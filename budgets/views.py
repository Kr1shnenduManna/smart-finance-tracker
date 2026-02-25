from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta
from .models import Budget
from .serializers import BudgetSerializer
from ml_features.ml_utils import get_budget_predictor
from transactions.models import Transaction
from django.db.models import Sum, Avg
import numpy as np


class BudgetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for budgets
    """

    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter budgets by current user"""
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user and predict budget when creating"""
        budget = serializer.save(user=self.request.user)

        # Try to predict optimal budget amount
        self._predict_budget(budget)

    def _predict_budget(self, budget):
        """Predict optimal budget amount using ML, with fallback to averaging."""
        from collections import defaultdict

        # Get historical spending for this category
        three_months_ago = datetime.now().date() - timedelta(days=90)

        historical_transactions = Transaction.objects.filter(
            user=budget.user,
            category=budget.category,
            transaction_type="expense",
            date__gte=three_months_ago,
        )

        if historical_transactions.count() < 5:
            return  # Not enough data

        # --- Try ML predictor first ---
        try:
            predictor = get_budget_predictor()
            if predictor.is_trained:
                # Build the same feature vector the model was trained on
                monthly_spending = defaultdict(float)
                monthly_counts = defaultdict(int)

                for txn in historical_transactions:
                    mk = txn.date.strftime("%Y-%m")
                    monthly_spending[mk] += float(txn.amount)
                    monthly_counts[mk] += 1

                sorted_months = sorted(monthly_spending.keys())
                if sorted_months:
                    latest_month = sorted_months[-1]
                    month_num = int(latest_month.split("-")[1])
                    count = monthly_counts[latest_month]
                    prev_amounts = [
                        monthly_spending[m] for m in sorted_months[:-1]
                    ] or [0]
                    hist_avg = float(np.mean(prev_amounts))
                    idx = len(sorted_months) - 1

                    features = [month_num, budget.category_id, hist_avg, count, idx]
                    predicted = predictor.predict(features)

                    if predicted is not None and predicted > 0:
                        budget.predicted_amount = round(predicted, 2)
                        budget.save()
                        return
        except Exception:
            pass  # Fall through to simple averaging

        # --- Fallback: simple historical average ---
        monthly_avg = historical_transactions.aggregate(avg=Avg("amount"))["avg"] or 0

        if budget.period == "monthly":
            budget.predicted_amount = monthly_avg * historical_transactions.count() / 3
        elif budget.period == "weekly":
            budget.predicted_amount = monthly_avg / 4
        elif budget.period == "daily":
            budget.predicted_amount = monthly_avg / 30
        elif budget.period == "yearly":
            budget.predicted_amount = monthly_avg * 12

        budget.save()

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get active budgets"""
        budgets = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(budgets, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def alerts(self, request):
        """Get budgets that have exceeded alert threshold"""
        budgets = self.get_queryset().filter(is_active=True)
        alerts = []

        for budget in budgets:
            spent_pct = budget.get_spent_percentage()
            if spent_pct >= budget.alert_threshold:
                alerts.append(
                    {
                        "budget_id": budget.id,
                        "category": budget.category.name,
                        "amount": float(budget.amount),
                        "spent": float(budget.get_spent_amount()),
                        "percentage": round(spent_pct, 2),
                        "period": budget.period,
                    }
                )

        return Response(alerts)
