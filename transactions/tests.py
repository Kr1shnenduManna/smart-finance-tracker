from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from .models import Category, Transaction
from accounts.models import Account

User = get_user_model()


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            category_type='expense',
            icon='test-icon',
            color='#FF5733'
        )
    
    def test_category_creation(self):
        """Test category can be created"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.category_type, 'expense')
    
    def test_category_str(self):
        """Test category string representation"""
        self.assertEqual(str(self.category), 'Test Category (expense)')


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            account_type='checking',
            balance=Decimal('1000.00')
        )
        self.category = Category.objects.create(
            name='Test Category',
            category_type='expense'
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            transaction_type='expense',
            amount=Decimal('50.00'),
            description='Test transaction',
            date=date.today()
        )
    
    def test_transaction_creation(self):
        """Test transaction can be created"""
        self.assertEqual(self.transaction.user, self.user)
        self.assertEqual(self.transaction.amount, Decimal('50.00'))
        self.assertEqual(self.transaction.transaction_type, 'expense')
    
    def test_transaction_updates_account_balance(self):
        """Test transaction updates account balance"""
        # Account balance should have been decreased by transaction amount
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('950.00'))
