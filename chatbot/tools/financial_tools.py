"""Financial analysis and retrieval tools for the chatbot"""

from accounts.models import User, CURRENCY_SYMBOLS
from django.db.models import Sum
from datetime import datetime, timedelta
from decimal import Decimal


class FinancialDataRetriever:
    """Retrieve and analyze user's financial data"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = User.objects.get(id=user_id)

    def get_financial_summary(self) -> dict:
        """Get complete financial snapshot"""
        try:
            from accounts.models import Account
            from transactions.models import Transaction

            accounts = Account.objects.filter(user_id=self.user_id)
            total_balance = accounts.aggregate(Sum("balance"))["balance__sum"] or 0

            # Last 30 days transactions
            last_30_days = datetime.now() - timedelta(days=30)
            recent_transactions = Transaction.objects.filter(
                user_id=self.user_id, date__gte=last_30_days
            )

            income = (
                recent_transactions.filter(transaction_type="income").aggregate(
                    Sum("amount")
                )["amount__sum"]
                or 0
            )

            expenses = (
                recent_transactions.filter(transaction_type="expense").aggregate(
                    Sum("amount")
                )["amount__sum"]
                or 0
            )

            return {
                "total_balance": float(total_balance),
                "monthly_income": float(income),
                "monthly_expenses": float(expenses),
                "net_monthly": float(income - expenses),
                "accounts_count": accounts.count(),
                "transactions_count": recent_transactions.count(),
                "currency": getattr(self.user, "preferred_currency", "USD"),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_spending_by_category(self) -> dict:
        """Get spending breakdown by category"""
        try:
            from transactions.models import Transaction

            last_30_days = datetime.now() - timedelta(days=30)
            spending = (
                Transaction.objects.filter(
                    user_id=self.user_id,
                    transaction_type="expense",
                    date__gte=last_30_days,
                )
                .values("category__name")
                .annotate(total=Sum("amount"))
                .order_by("-total")
            )

            return {item["category__name"]: float(item["total"]) for item in spending}
        except Exception as e:
            return {"error": str(e)}

    def get_budget_status(self) -> dict:
        """Get current budget status"""
        try:
            from budgets.models import Budget

            budgets = Budget.objects.filter(user_id=self.user_id, is_active=True)
            budget_status = {}

            for budget in budgets:
                spent = budget.get_spent_amount()
                remaining = budget.amount - spent
                percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0

                budget_status[budget.category.name] = {
                    "budget": float(budget.amount),
                    "spent": float(spent),
                    "remaining": float(remaining),
                    "percentage": round(percentage, 2),
                    "period": budget.period,
                    "status": "on_track"
                    if percentage <= 80
                    else "at_risk"
                    if percentage <= 100
                    else "exceeded",
                }

            return budget_status
        except Exception as e:
            return {"error": str(e)}

    def get_savings_goals_status(self) -> dict:
        """Get all savings goals"""
        try:
            from goals.models import SavingsGoal

            goals = SavingsGoal.objects.filter(user_id=self.user_id, is_active=True)
            goals_status = {}

            for goal in goals:
                progress = (
                    (goal.current_amount / goal.target_amount * 100)
                    if goal.target_amount > 0
                    else 0
                )

                # Calculate days remaining
                days_remaining = (goal.target_date - datetime.now().date()).days

                goals_status[goal.name] = {
                    "target": float(goal.target_amount),
                    "current": float(goal.current_amount),
                    "progress": round(progress, 2),
                    "target_date": goal.target_date.isoformat(),
                    "days_remaining": max(0, days_remaining),
                    "category": goal.category,
                    "status": "completed"
                    if progress >= 100
                    else "on_track"
                    if progress >= 80
                    else "behind",
                }

            return goals_status
        except Exception as e:
            return {"error": str(e)}

    def get_context_prompt(self) -> str:
        """Generate context prompt for the agent"""
        summary = self.get_financial_summary()
        spending = self.get_spending_by_category()
        budgets = self.get_budget_status()
        goals = self.get_savings_goals_status()

        sym = CURRENCY_SYMBOLS.get(summary.get('currency', 'USD'), '$')
        context = f"""
# User Financial Context

## Summary
- Total Balance: {sym}{summary.get('total_balance', 0):.2f}
- Monthly Income: {sym}{summary.get('monthly_income', 0):.2f}
- Monthly Expenses: {sym}{summary.get('monthly_expenses', 0):.2f}
- Net Monthly: {sym}{summary.get('net_monthly', 0):.2f}
- Currency: {summary.get('currency', 'USD')}

## Top Spending Categories (Last 30 days)
"""
        for category, amount in sorted(
            spending.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            context += f"- {category}: {sym}{amount:.2f}\n"

        context += "\n## Budget Status\n"
        for category, budget_info in budgets.items():
            context += f"- {category}: {sym}{budget_info['spent']:.2f}/{sym}{budget_info['budget']:.2f} ({budget_info['percentage']:.0f}%) - {budget_info['status']}\n"

        context += "\n## Savings Goals\n"
        for goal_name, goal_info in goals.items():
            context += f"- {goal_name}: {sym}{goal_info['current']:.2f}/{sym}{goal_info['target']:.2f} ({goal_info['progress']:.0f}%) - {goal_info['days_remaining']} days left\n"

        return context
