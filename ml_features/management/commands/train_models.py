"""
Management command to train ML models for the finance tracker.
Trains both the TransactionCategorizer and BudgetPredictor using
existing user transaction data.
"""

import numpy as np
from django.core.management.base import BaseCommand
from transactions.models import Transaction, Category
from ml_features.ml_utils import TransactionCategorizer, BudgetPredictor
from ml_features.models import MLModel
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from collections import defaultdict


class Command(BaseCommand):
    help = "Train ML models using existing transaction data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            choices=["categorizer", "budget", "all"],
            default="all",
            help="Which model to train (default: all)",
        )
        parser.add_argument(
            "--min-samples",
            type=int,
            default=5,
            help="Minimum number of samples required for training (default: 5)",
        )

    def handle(self, *args, **options):
        model_choice = options["model"]
        min_samples = options["min_samples"]

        if model_choice in ("categorizer", "all"):
            self._train_categorizer(min_samples)

        if model_choice in ("budget", "all"):
            self._train_budget_predictor(min_samples)

    def _train_categorizer(self, min_samples):
        """Train the transaction categorizer on existing labeled transactions."""
        self.stdout.write("Training TransactionCategorizer...")

        # Get transactions with both description and category
        transactions = (
            Transaction.objects.filter(
                description__isnull=False,
                category__isnull=False,
            )
            .exclude(description="")
            .select_related("category")
        )

        if transactions.count() < min_samples:
            self.stdout.write(
                self.style.WARNING(
                    f"Not enough labeled transactions ({transactions.count()}/{min_samples}). "
                    f"Need at least {min_samples} to train."
                )
            )
            return

        descriptions = list(transactions.values_list("description", flat=True))
        categories = list(transactions.values_list("category__name", flat=True))

        categorizer = TransactionCategorizer()
        success = categorizer.train(descriptions, categories)

        if success:
            model_path = "ml_models/categorizer.pkl"
            categorizer.save_model(model_path)

            # Calculate accuracy via simple train-set evaluation
            correct = sum(
                1
                for desc, cat in zip(descriptions, categories)
                if categorizer.predict(desc)[0] == cat
            )
            accuracy = correct / len(descriptions)

            # Save/update model metadata in DB
            MLModel.objects.update_or_create(
                model_type="categorization",
                is_active=True,
                defaults={
                    "name": "Transaction Categorizer",
                    "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "accuracy": round(accuracy, 4),
                    "file_path": model_path,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Categorizer trained on {len(descriptions)} samples. "
                    f"Train accuracy: {accuracy:.2%}"
                )
            )
        else:
            self.stdout.write(self.style.ERROR("Categorizer training failed."))

    def _train_budget_predictor(self, min_samples):
        """Train the budget predictor on historical spending patterns."""
        self.stdout.write("Training BudgetPredictor...")

        # Build feature vectors from monthly spending per category per user
        # Features: [month_number, day_of_week_avg, category_id, historical_avg, transaction_count]
        expense_transactions = Transaction.objects.filter(
            transaction_type="expense",
            category__isnull=False,
        ).select_related("category")

        if expense_transactions.count() < min_samples:
            self.stdout.write(
                self.style.WARNING(
                    f"Not enough expense transactions ({expense_transactions.count()}/{min_samples}). "
                    f"Need at least {min_samples} to train."
                )
            )
            return

        # Group by user + category + month to build training samples
        monthly_spending = defaultdict(lambda: defaultdict(float))
        monthly_counts = defaultdict(lambda: defaultdict(int))

        for txn in expense_transactions:
            key = (txn.user_id, txn.category_id)
            month_key = txn.date.strftime("%Y-%m")
            monthly_spending[key][month_key] += float(txn.amount)
            monthly_counts[key][month_key] += 1

        features = []
        amounts = []

        for (user_id, category_id), months in monthly_spending.items():
            sorted_months = sorted(months.keys())
            for i, month_key in enumerate(sorted_months):
                month_num = int(month_key.split("-")[1])
                count = monthly_counts[(user_id, category_id)][month_key]
                # Historical average up to this point
                prev_amounts = [months[m] for m in sorted_months[:i]] if i > 0 else [0]
                hist_avg = np.mean(prev_amounts)

                features.append([month_num, category_id, hist_avg, count, i])
                amounts.append(months[month_key])

        if len(features) < min_samples:
            self.stdout.write(
                self.style.WARNING(
                    f"Not enough monthly aggregates ({len(features)}/{min_samples}). "
                    f"Need at least {min_samples} to train."
                )
            )
            return

        features = np.array(features)
        amounts = np.array(amounts)

        predictor = BudgetPredictor()
        success = predictor.train(features, amounts)

        if success:
            model_path = "ml_models/budget_predictor.pkl"
            predictor.save_model(model_path)

            # Simple R² score on training data
            predictions = [predictor.predict(f) for f in features]
            ss_res = np.sum((amounts - predictions) ** 2)
            ss_tot = np.sum((amounts - np.mean(amounts)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            MLModel.objects.update_or_create(
                model_type="prediction",
                is_active=True,
                defaults={
                    "name": "Budget Predictor",
                    "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "accuracy": round(r2, 4),
                    "file_path": model_path,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Budget predictor trained on {len(features)} samples. "
                    f"Train R²: {r2:.4f}"
                )
            )
        else:
            self.stdout.write(self.style.ERROR("Budget predictor training failed."))
