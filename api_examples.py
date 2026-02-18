#!/usr/bin/env python
"""
Example script demonstrating Smart Finance Tracker API usage
"""
import os
import django
import requests
from requests.auth import HTTPBasicAuth

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_tracker.settings')
django.setup()

BASE_URL = 'http://localhost:8000/api'
AUTH = HTTPBasicAuth('admin', 'admin123')

def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def example_1_list_categories():
    """Example 1: List all transaction categories"""
    print_section("Example 1: List Transaction Categories")
    
    response = requests.get(f'{BASE_URL}/transactions/categories/', auth=AUTH)
    
    if response.status_code == 200:
        categories = response.json()
        print(f"Found {len(categories)} categories:\n")
        
        income = [c for c in categories if c['category_type'] == 'income']
        expense = [c for c in categories if c['category_type'] == 'expense']
        
        print(f"Income Categories ({len(income)}):")
        for cat in income[:3]:
            print(f"  • {cat['name']} ({cat['color']})")
        
        print(f"\nExpense Categories ({len(expense)}):")
        for cat in expense[:5]:
            print(f"  • {cat['name']} ({cat['color']})")
    else:
        print(f"Error: {response.status_code}")

def example_2_create_account():
    """Example 2: Create a new financial account"""
    print_section("Example 2: Create Financial Account")
    
    data = {
        'name': 'My Savings Account',
        'account_type': 'savings',
        'currency': 'USD',
        'description': 'Personal savings account'
    }
    
    response = requests.post(f'{BASE_URL}/accounts/accounts/', json=data, auth=AUTH)
    
    if response.status_code == 201:
        account = response.json()
        print(f"✓ Created account: {account['name']}")
        print(f"  Type: {account['account_type']}")
        print(f"  Balance: ${account['balance']}")
        print(f"  ID: {account['id']}")
        return account['id']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def example_3_create_transaction(account_id):
    """Example 3: Create a new transaction"""
    print_section("Example 3: Create Transaction")
    
    # Get a category first
    categories = requests.get(f'{BASE_URL}/transactions/categories/', auth=AUTH).json()
    expense_category = next((c for c in categories if c['category_type'] == 'expense'), None)
    
    if not expense_category:
        print("No expense category found!")
        return
    
    from datetime import date
    
    data = {
        'account': account_id,
        'category': expense_category['id'],
        'transaction_type': 'expense',
        'amount': '75.50',
        'description': 'Dinner at restaurant',
        'date': str(date.today()),
        'notes': 'Team dinner'
    }
    
    response = requests.post(f'{BASE_URL}/transactions/transactions/', json=data, auth=AUTH)
    
    if response.status_code == 201:
        transaction = response.json()
        print(f"✓ Created transaction:")
        print(f"  Amount: ${transaction['amount']}")
        print(f"  Type: {transaction['transaction_type']}")
        print(f"  Category: {transaction['category_name']}")
        print(f"  Date: {transaction['date']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def example_4_create_budget():
    """Example 4: Create a budget"""
    print_section("Example 4: Create Budget")
    
    # Get a category
    categories = requests.get(f'{BASE_URL}/transactions/categories/', auth=AUTH).json()
    expense_category = next((c for c in categories if c['category_type'] == 'expense'), None)
    
    from datetime import date, timedelta
    
    today = date.today()
    start = today.replace(day=1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    data = {
        'category': expense_category['id'],
        'amount': '500.00',
        'period': 'monthly',
        'start_date': str(start),
        'end_date': str(end),
        'alert_threshold': 80,
        'is_active': True
    }
    
    response = requests.post(f'{BASE_URL}/budgets/budgets/', json=data, auth=AUTH)
    
    if response.status_code == 201:
        budget = response.json()
        print(f"✓ Created budget:")
        print(f"  Category: {budget['category_name']}")
        print(f"  Amount: ${budget['amount']}")
        print(f"  Period: {budget['period']}")
        print(f"  Spent: ${budget['spent_amount']} ({budget['spent_percentage']}%)")
        print(f"  Remaining: ${budget['remaining_amount']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def example_5_get_summary():
    """Example 5: Get transaction summary"""
    print_section("Example 5: Transaction Summary")
    
    response = requests.get(f'{BASE_URL}/transactions/transactions/summary/', auth=AUTH)
    
    if response.status_code == 200:
        summary = response.json()
        print(f"Income:")
        print(f"  Total: ${summary['income']['total']}")
        print(f"  Count: {summary['income']['count']}")
        
        print(f"\nExpenses:")
        print(f"  Total: ${summary['expense']['total']}")
        print(f"  Count: {summary['expense']['count']}")
        
        print(f"\nNet: ${summary['net']}")
    else:
        print(f"Error: {response.status_code}")

def main():
    print("\n" + "=" * 60)
    print("  Smart Finance Tracker - API Usage Examples")
    print("=" * 60)
    print("\nNote: Make sure the Django server is running on localhost:8000")
    
    try:
        # Example 1: List categories
        example_1_list_categories()
        
        # Example 2: Create account
        account_id = example_2_create_account()
        
        if account_id:
            # Example 3: Create transaction
            example_3_create_transaction(account_id)
            
            # Example 4: Create budget
            example_4_create_budget()
        
        # Example 5: Get summary
        example_5_get_summary()
        
        print("\n" + "=" * 60)
        print("  ✓ Examples completed successfully!")
        print("=" * 60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the server.")
        print("Please make sure the Django server is running:")
        print("  python manage.py runserver\n")

if __name__ == '__main__':
    main()
