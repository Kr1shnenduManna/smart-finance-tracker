"""
Machine Learning utilities for Smart Finance Tracker
"""
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
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=100)),
            ('classifier', MultinomialNB())
        ])
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


def get_categorizer():
    """Get or create a transaction categorizer instance"""
    categorizer = TransactionCategorizer()
    model_path = 'ml_models/categorizer.pkl'
    categorizer.load_model(model_path)
    return categorizer


def get_budget_predictor():
    """Get or create a budget predictor instance"""
    predictor = BudgetPredictor()
    model_path = 'ml_models/budget_predictor.pkl'
    predictor.load_model(model_path)
    return predictor
