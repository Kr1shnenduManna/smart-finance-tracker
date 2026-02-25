from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Account

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test user can be created"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'testuser')


class AccountModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='Test Checking',
            account_type='checking',
            balance=Decimal('1000.00'),
            currency='USD'
        )
    
    def test_account_creation(self):
        """Test account can be created"""
        self.assertEqual(self.account.name, 'Test Checking')
        self.assertEqual(self.account.user, self.user)
        self.assertEqual(self.account.balance, Decimal('1000.00'))
    
    def test_account_str(self):
        """Test account string representation"""
        self.assertEqual(str(self.account), 'Test Checking (testuser)')
    
    def test_account_active_by_default(self):
        """Test account is active by default"""
        self.assertTrue(self.account.is_active)
