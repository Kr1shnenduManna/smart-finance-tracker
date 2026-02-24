
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import joblib


class TransactionCategorizer:
    """
    ML model for automatic transaction categorization
    Uses TF-IDF and Naive Bayes for text classification
    """

    def __init__(self):
        self.model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(max_features=100)),
                ("classifier", MultinomialNB()),
            ]
        )
        self.is_trained = False

    def train(self, descriptions, categories):
        """
        Train the categorization model

        Args:
            descriptions: List of transaction descriptions
            categories: List of category labels
        """
        if len(descriptions) < 5:
            # Not enough data to train
            return False

        self.model.fit(descriptions, categories)
        self.is_trained = True
        return True

    def predict(self, description):
        """
        Predict category for a transaction description

        Args:
            description: Transaction description text

        Returns:
            Tuple of (predicted_category, confidence)
        """
        if not self.is_trained:
            return None, 0.0

        prediction = self.model.predict([description])[0]
        probabilities = self.model.predict_proba([description])[0]
        confidence = max(probabilities)

        return prediction, confidence

    def save_model(self, filepath):
        """Save the trained model to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.model, filepath)

    def load_model(self, filepath):
        """Load a trained model from disk"""
        if os.path.exists(filepath):
            self.model = joblib.load(filepath)
            self.is_trained = True
            return True
        return False


class BudgetPredictor:
    """
    ML model for predictive budgeting
    Uses Random Forest for regression
    """

    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False

    def train(self, features, amounts):
        """
        Train the budget prediction model

        Args:
            features: Array of feature vectors (e.g., historical spending patterns)
            amounts: Array of actual spending amounts
        """
        if len(features) < 5:
            # Not enough data to train
            return False

        self.model.fit(features, amounts)
        self.is_trained = True
        return True

    def predict(self, features):
        """
        Predict budget amount

        Args:
            features: Feature vector for prediction

        Returns:
            Predicted budget amount
        """
        if not self.is_trained:
            return None

        prediction = self.model.predict([features])[0]
        return max(0, prediction)  # Ensure non-negative

    def save_model(self, filepath):
        """Save the trained model to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.model, filepath)

    def load_model(self, filepath):
        """Load a trained model from disk"""
        if os.path.exists(filepath):
            self.model = joblib.load(filepath)
            self.is_trained = True
            return True
        return False


CATEGORIZER_MODEL_PATH = "ml_models/categorizer.pkl"
BUDGET_MODEL_PATH = "ml_models/budget_predictor.pkl"

# Module-level caches so the model is loaded only once per process
_categorizer_instance = None
_budget_predictor_instance = None


def get_categorizer():
    """Get or create a cached transaction categorizer instance"""
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = TransactionCategorizer()
        _categorizer_instance.load_model(CATEGORIZER_MODEL_PATH)
    return _categorizer_instance


def get_budget_predictor():
    """Get or create a cached budget predictor instance"""
    global _budget_predictor_instance
    if _budget_predictor_instance is None:
        _budget_predictor_instance = BudgetPredictor()
        _budget_predictor_instance.load_model(BUDGET_MODEL_PATH)
    return _budget_predictor_instance


def retrain_categorizer_if_ready(min_samples=10):
    """
    Retrain the categorizer using all labeled transactions.
    Called automatically when enough manual categorizations exist.
    Returns True if training succeeded.
    """
    global _categorizer_instance
    from transactions.models import Transaction  # avoid circular import

    transactions = (
        Transaction.objects.filter(
            description__isnull=False,
            category__isnull=False,
        )
        .exclude(description="")
        .select_related("category")
    )

    if transactions.count() < min_samples:
        return False

    descriptions = list(transactions.values_list("description", flat=True))
    categories = list(transactions.values_list("category__name", flat=True))

    categorizer = TransactionCategorizer()
    success = categorizer.train(descriptions, categories)

    if success:
        categorizer.save_model(CATEGORIZER_MODEL_PATH)
        # Refresh the cached instance
        _categorizer_instance = categorizer
        return True
    return False


def retrain_budget_predictor_if_ready(min_samples=10):
    """
    Retrain the budget predictor using all expense transactions.
    Returns True if training succeeded.
    """
    global _budget_predictor_instance
    from transactions.models import Transaction  # avoid circular import
    from collections import defaultdict

    expense_txns = Transaction.objects.filter(
        transaction_type="expense",
        category__isnull=False,
    ).select_related("category")

    if expense_txns.count() < min_samples:
        return False

    monthly_spending = defaultdict(lambda: defaultdict(float))
    monthly_counts = defaultdict(lambda: defaultdict(int))

    for txn in expense_txns:
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
            prev_amounts = [months[m] for m in sorted_months[:i]] if i > 0 else [0]
            hist_avg = np.mean(prev_amounts)
            features.append([month_num, category_id, hist_avg, count, i])
            amounts.append(months[month_key])

    if len(features) < min_samples:
        return False

    features_arr = np.array(features)
    amounts_arr = np.array(amounts)

    predictor = BudgetPredictor()
    success = predictor.train(features_arr, amounts_arr)

    if success:
        predictor.save_model(BUDGET_MODEL_PATH)
        _budget_predictor_instance = predictor
        return True
    return False
