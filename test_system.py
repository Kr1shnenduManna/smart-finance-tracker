#!/usr/bin/env python
"""
Test script to verify Smart Finance Tracker functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_tracker.settings')
django.setup()

from accounts.models import User, Account
from transactions.models import Category, Transaction
from budgets.models import Budget
from datetime import date, timedelta
from decimal import Decimal

def main():
    print("=" * 60)
    print("Smart Finance Tracker - System Verification")
    print("=" * 60)
    
    # 1. Check User
    print("\n1. Checking Users...")
    user = User.objects.first()
    if user:
        print(f"   ✓ User found: {user.username}")
    else:
        print("   ✗ No users found")
        return
    
    # 2. Check Categories
    print("\n2. Checking Categories...")
    categories = Category.objects.all()
    print(f"   ✓ Total categories: {categories.count()}")
    income_cats = categories.filter(category_type='income').count()
    expense_cats = categories.filter(category_type='expense').count()
    print(f"   ✓ Income categories: {income_cats}")
    print(f"   ✓ Expense categories: {expense_cats}")
    
    # 3. Create Test Account
    print("\n3. Creating Test Account...")
    account, created = Account.objects.get_or_create(
        user=user,
        name='Test Checking Account',
        defaults={
            'account_type': 'checking',
            'balance': Decimal('1000.00'),
            'currency': 'USD',
            'description': 'Test account for verification'
        }
    )
    if created:
        print(f"   ✓ Created account: {account.name} with balance ${account.balance}")
    else:
        print(f"   ✓ Found existing account: {account.name} with balance ${account.balance}")
    
    # 4. Create Test Transaction
    print("\n4. Creating Test Transaction...")
    category = Category.objects.filter(category_type='expense').first()
    today = date.today()
    
    transaction, created = Transaction.objects.get_or_create(
        user=user,
        account=account,
        date=today,
        description='Test grocery purchase',
        defaults={
            'category': category,
            'transaction_type': 'expense',
            'amount': Decimal('50.00'),
            'notes': 'Test transaction for verification'
        }
    )
    if created:
        print(f"   ✓ Created transaction: ${transaction.amount} - {transaction.description}")
    else:
        print(f"   ✓ Found existing transaction: ${transaction.amount} - {transaction.description}")
    
    # 5. Create Test Budget
    print("\n5. Creating Test Budget...")
    start_date = today.replace(day=1)
    if today.month == 12:
        end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    budget, created = Budget.objects.get_or_create(
        user=user,
        category=category,
        period='monthly',
        start_date=start_date,
        defaults={
            'amount': Decimal('500.00'),
            'end_date': end_date,
            'alert_threshold': 80,
            'is_active': True
        }
    )
    if created:
        print(f"   ✓ Created budget: ${budget.amount} for {budget.category.name}")
    else:
        print(f"   ✓ Found existing budget: ${budget.amount} for {budget.category.name}")
    
    spent = budget.get_spent_amount()
    remaining = budget.get_remaining_amount()
    pct = budget.get_spent_percentage()
    print(f"   ✓ Budget status: Spent ${spent}, Remaining ${remaining} ({pct:.1f}%)")
    
    # 6. Summary
    print("\n6. System Summary...")
    total_accounts = Account.objects.filter(user=user).count()
    total_transactions = Transaction.objects.filter(user=user).count()
    total_budgets = Budget.objects.filter(user=user).count()
    
    print(f"   ✓ Total accounts: {total_accounts}")
    print(f"   ✓ Total transactions: {total_transactions}")
    print(f"   ✓ Total budgets: {total_budgets}")
    
    # 7. ML Features
    print("\n7. Checking ML Features...")
    from ml_features.ml_utils import get_categorizer, get_budget_predictor
    
    categorizer = get_categorizer()
    print(f"   ✓ Transaction categorizer initialized")
    
    predictor = get_budget_predictor()
    print(f"   ✓ Budget predictor initialized")
    
    print("\n" + "=" * 60)
    print("✓ All systems operational!")
    print("=" * 60)
    
    print("\n📊 API Endpoints Available:")
    print("   - Accounts: http://localhost:8000/api/accounts/")
    print("   - Transactions: http://localhost:8000/api/transactions/")
    print("   - Budgets: http://localhost:8000/api/budgets/")
    print("   - Admin: http://localhost:8000/admin/")
    print("\n🔐 Demo credentials: username=admin, password=admin123")
    print("   Note: Change these credentials in production!")

if __name__ == '__main__':
    main()
