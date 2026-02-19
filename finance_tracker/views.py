from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from transactions.models import Transaction, Category
from budgets.models import Budget
from accounts.models import Account


@login_required
def dashboard(request):
    """Main dashboard view"""
    user = request.user
    
    # Get date range (default to current month)
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Get all user accounts
    accounts = Account.objects.filter(user=user, is_active=True)
    total_balance = sum(float(acc.balance) for acc in accounts)
    
    # Get transactions for current month
    transactions = Transaction.objects.filter(
        user=user,
        date__gte=start_of_month,
        date__lte=today
    )
    
    # Calculate income and expenses
    income = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    expenses = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get active budgets
    active_budgets = Budget.objects.filter(
        user=user,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )
    
    # Budget alerts
    budget_alerts = []
    for budget in active_budgets:
        spent_pct = budget.get_spent_percentage()
        if spent_pct >= budget.alert_threshold:
            budget_alerts.append({
                'budget': budget,
                'percentage': round(spent_pct, 1)
            })
    
    # Recent transactions
    recent_transactions = Transaction.objects.filter(user=user).order_by('-date', '-created_at')[:10]
    
    # Expense by category
    expense_by_category = transactions.filter(
        transaction_type='expense'
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    
    context = {
        'total_balance': total_balance,
        'income': income,
        'expenses': expenses,
        'net': income - expenses,
        'accounts': accounts,
        'recent_transactions': recent_transactions,
        'budget_alerts': budget_alerts,
        'expense_by_category': expense_by_category,
    }
    
    return render(request, 'dashboard/index.html', context)
