from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from .models import Budget
from transactions.models import Category, Transaction
from accounts.models import Account

User = get_user_model()


class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            category_type='expense'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            account_type='checking',
            balance=Decimal('1000.00')
        )
        
        today = date.today()
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('500.00'),
            period='monthly',
            start_date=today,
            end_date=today + timedelta(days=30),
            alert_threshold=80
        )
    
    def test_budget_creation(self):
        """Test budget can be created"""
        self.assertEqual(self.budget.user, self.user)
        self.assertEqual(self.budget.amount, Decimal('500.00'))
        self.assertEqual(self.budget.period, 'monthly')
    
    def test_budget_str(self):
        """Test budget string representation"""
        expected = f"Test Category - 500.00 (monthly)"
        self.assertEqual(str(self.budget), expected)
    
    def test_budget_spent_calculation(self):
        """Test budget spent amount calculation"""
        # Create a transaction within budget period
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            transaction_type='expense',
            amount=Decimal('100.00'),
            description='Test expense',
            date=date.today()
        )
        
        spent = self.budget.get_spent_amount()
        self.assertEqual(spent, Decimal('100.00'))
        
        remaining = self.budget.get_remaining_amount()
        self.assertEqual(remaining, Decimal('400.00'))
        
        percentage = self.budget.get_spent_percentage()
        self.assertEqual(percentage, 20.0)
