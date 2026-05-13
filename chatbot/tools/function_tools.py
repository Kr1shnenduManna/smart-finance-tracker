"""
Dynamic function tools for the chatbot
These tools can be called by the LLM to perform various financial operations
"""

import json
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any, Dict, List

from accounts.models import User
from accounts.models import CURRENCY_SYMBOLS
from transactions.models import Transaction
from goals.models import SavingsGoal
from budgets.models import Budget
from accounts.models import Account
from bills.models import Bill, BillPayment
import logging

logger = logging.getLogger(__name__)


class ChatbotTools:
    """Collection of tools that the chatbot can invoke"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        try:
            self.user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError(f"User with id {user_id} not found")

    def _curr_sym(self) -> str:
        """Return the currency symbol for the user's preferred currency."""
        return CURRENCY_SYMBOLS.get(getattr(self.user, 'preferred_currency', 'USD'), '$')

    # ============= GOAL FUNCTIONS =============

    def create_savings_goal(
        self,
        goal_name: str,
        target_amount: float,
        target_date: str = None,
        category: str = "other",
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a new savings goal"""
        try:
            if target_date is None:
                target_date = (datetime.now() + timedelta(days=120)).strftime(
                    "%Y-%m-%d"
                )

            goal_date = datetime.strptime(target_date, "%Y-%m-%d").date()

            goal = SavingsGoal.objects.create(
                user=self.user,
                name=goal_name,
                target_amount=Decimal(str(target_amount)),
                target_date=goal_date,
                category=category,
                description=description,
                is_active=True,
            )

            return {
                "success": True,
                "message": f"✅ Savings goal '{goal.name}' created successfully!",
                "goal_id": goal.id,
                "goal_name": goal.name,
                "target_amount": float(goal.target_amount),
                "target_date": goal.target_date.isoformat(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_goal_contribution(self, amount: float, goal_id: int = None, goal_name: str = None) -> Dict[str, Any]:
        """Add money to a savings goal and record a transaction.
        Provide either goal_id (int) or goal_name (str, case-insensitive partial match).
        """
        try:
            from goals.models import GoalContribution
            from transactions.models import Category as TransCategory
            from django.utils import timezone as tz

            # --- Resolve goal by ID or by name ---
            goal = None
            if goal_id:
                try:
                    goal = SavingsGoal.objects.get(id=goal_id, user=self.user)
                except SavingsGoal.DoesNotExist:
                    pass

            if goal is None and goal_name:
                # Case-insensitive partial match
                matches = SavingsGoal.objects.filter(
                    user=self.user, is_active=True, name__icontains=goal_name.strip()
                )
                if matches.exists():
                    goal = matches.first()
                else:
                    # Broader word-by-word search
                    for word in goal_name.strip().split():
                        if len(word) > 2:
                            m = SavingsGoal.objects.filter(
                                user=self.user, is_active=True, name__icontains=word
                            )
                            if m.exists():
                                goal = m.first()
                                break

            if goal is None:
                all_goals = SavingsGoal.objects.filter(user=self.user, is_active=True)
                names = [g.name for g in all_goals]
                return {
                    "success": False,
                    "error": f"Could not find goal matching '{goal_name or goal_id}'. Active goals: {names}"
                }

            contrib_amount = Decimal(str(amount))

            # Find or create a Savings expense category
            category, _ = TransCategory.objects.get_or_create(
                name="Savings",
                category_type="expense",
                defaults={"is_system": True}
            )

            # Use goal's account or fall back to user's primary account
            account = goal.account or Account.objects.filter(user=self.user).first()

            # Create Transaction (post_save signal auto-deducts balance)
            transaction = None
            if account:
                transaction = Transaction.objects.create(
                    user=self.user,
                    account=account,
                    category=category,
                    transaction_type="expense",
                    amount=contrib_amount,
                    description=f"Savings contribution: {goal.name}",
                    date=datetime.now().date(),
                    notes="Contributed via Finance Assistant",
                )

            # Record the GoalContribution
            GoalContribution.objects.create(
                goal=goal,
                amount=contrib_amount,
                contribution_date=datetime.now().date(),
                source="Finance Assistant",
                notes="Via chatbot",
            )

            # Update goal current_amount
            goal.current_amount += contrib_amount
            if goal.current_amount >= goal.target_amount:
                goal.is_active = False
                goal.completed_at = tz.now().date()
            goal.save()

            total_progress = float(
                (goal.current_amount / goal.target_amount * 100)
                if goal.target_amount > 0
                else 0
            )

            return {
                "success": True,
                "message": f"\u2705 Added {self._curr_sym()}{amount:.2f} to goal '{goal.name}'. A transaction has been recorded.",
                "goal_name": goal.name,
                "new_total": float(goal.current_amount),
                "progress": round(total_progress, 1),
                "transaction_id": transaction.id if transaction else None,
            }
        except Exception as e:
            logger.error(f"Error in add_goal_contribution: {e}")
            return {"success": False, "error": str(e)}

    def get_all_goals(self) -> Dict[str, Any]:

        """Get all active savings goals"""
        try:
            goals = SavingsGoal.objects.filter(user=self.user, is_active=True)
            goals_list = []

            for goal in goals:
                progress = float(
                    (goal.current_amount / goal.target_amount * 100)
                    if goal.target_amount > 0
                    else 0
                )
                days_remaining = (goal.target_date - datetime.now().date()).days

                goals_list.append(
                    {
                        "id": goal.id,
                        "name": goal.name,
                        "target_amount": float(goal.target_amount),
                        "current_amount": float(goal.current_amount),
                        "progress": round(progress, 2),
                        "target_date": goal.target_date.isoformat(),
                        "days_remaining": max(0, days_remaining),
                        "category": goal.category,
                    }
                )

            return {"success": True, "goals": goals_list}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_goal(self, goal_id: int) -> Dict[str, Any]:
        """Delete/deactivate a savings goal"""
        try:
            goal = SavingsGoal.objects.get(id=goal_id, user=self.user)
            goal.is_active = False
            goal.save()
            return {
                "success": True,
                "message": f"✅ Goal '{goal.name}' has been deleted",
            }
        except SavingsGoal.DoesNotExist:
            return {"success": False, "error": "Goal not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============= TRANSACTION FUNCTIONS =============

    def add_transaction(self, amount: float, transaction_type: str, category_name: str = "Uncategorized", date: str = None, description: str = "") -> Dict[str, Any]:
        """Add a new income or expense transaction"""
        try:
            from transactions.models import Category
            
            # Find primary account or create default
            account = Account.objects.filter(user=self.user).first()
            if not account:
                account = Account.objects.create(user=self.user, name="Cash", account_type="cash", balance=0)
                
            # Handle Category
            category_name = category_name.title()
            category, _ = Category.objects.get_or_create(
                name=category_name, 
                defaults={"category_type": transaction_type}
            )
            
            # Date
            trans_date = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.now().date()
            
            # Create transaction
            t = Transaction.objects.create(
                user=self.user,
                account=account,
                category=category,
                transaction_type=transaction_type,
                amount=Decimal(str(amount)),
                date=trans_date,
                description=description
            )
            
            # Update balance
            if transaction_type == "income":
                account.balance += Decimal(str(amount))
            else:
                account.balance -= Decimal(str(amount))
            account.save()
            
            return {
                "success": True, 
                "message": f"✅ Successfully added {transaction_type} of {self._curr_sym()}{amount} to '{account.name}' under category '{category_name}'.",
                "transaction_id": t.id
            }
        except Exception as e:
            logger.error(f"Error in add_transaction: {e}")
            return {"success": False, "error": str(e)}

    def get_transactions(self, limit: int = 10, days: int = 30) -> Dict[str, Any]:
        """Get recent transactions"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            transactions = Transaction.objects.filter(
                user=self.user, date__gte=start_date
            ).order_by("-date")[:limit]

            trans_list = []
            for t in transactions:
                trans_list.append(
                    {
                        "id": t.id,
                        "date": t.date.isoformat(),
                        "amount": float(t.amount),
                        "type": t.transaction_type,
                        "category": t.category.name if t.category else "Uncategorized",
                        "description": t.description or "",
                    }
                )

            return {"success": True, "transactions": trans_list}
        except Exception as e:
            logger.error(f"Error in get_transactions: {e}")
            return {"success": False, "error": str(e)}

    def get_spending_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Get spending by category"""
        try:
            from django.db.models import Sum

            start_date = datetime.now() - timedelta(days=days)
            spending_data = {}

            categories = (
                Transaction.objects.filter(
                    user=self.user,
                    transaction_type="expense",
                    date__gte=start_date,
                )
                .values("category__name")
                .annotate(total=Sum("amount"))
                .order_by("-total")
            )

            for item in categories:
                if item["category__name"]:
                    spending_data[item["category__name"]] = float(item["total"] or 0)

            return {"success": True, "spending": spending_data}
        except Exception as e:
            logger.error(f"Error in get_spending_breakdown: {e}")
            return {"success": False, "error": str(e)}

    def get_income_vs_expenses(self, days: int = 30) -> Dict[str, Any]:
        """Get income vs expenses for period"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            from django.db.models import Sum

            income = (
                Transaction.objects.filter(
                    user=self.user, transaction_type="income", date__gte=start_date
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            expenses = (
                Transaction.objects.filter(
                    user=self.user, transaction_type="expense", date__gte=start_date
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            return {
                "success": True,
                "income": float(income),
                "expenses": float(expenses),
                "net": float(income - expenses),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============= ACCOUNT FUNCTIONS =============

    def get_accounts(self) -> Dict[str, Any]:
        """Get all user accounts and balances"""
        try:
            accounts = Account.objects.filter(user=self.user)
            accounts_list = []
            total_balance = Decimal("0")

            for account in accounts:
                accounts_list.append(
                    {
                        "id": account.id,
                        "name": account.name,
                        "type": account.account_type,
                        "balance": float(account.balance),
                        "currency": account.currency,
                    }
                )
                total_balance += account.balance

            return {
                "success": True,
                "accounts": accounts_list,
                "total_balance": float(total_balance),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============= BILL FUNCTIONS =============

    def create_bill(self, name: str, amount: float, frequency: str = "monthly", due_date: int = None, next_due_date: str = None) -> Dict[str, Any]:
        """Create a new bill reminder"""
        try:
            # If due_date is not provided but next_due_date is, extract the day
            if due_date is None:
                if next_due_date:
                    due_date = datetime.strptime(next_due_date, "%Y-%m-%d").day
                else:
                    due_date = datetime.now().day

            # Determine next_due_date if not explicitly given
            if next_due_date:
                next_date = datetime.strptime(next_due_date, "%Y-%m-%d").date()
            else:
                today = datetime.now().date()
                try:
                    next_date = today.replace(day=due_date)
                    if next_date < today:
                        if today.month == 12:
                            next_date = next_date.replace(year=today.year + 1, month=1)
                        else:
                            next_date = next_date.replace(month=today.month + 1)
                except ValueError:
                    # Handle cases like Feb 30th -> move to next month or end of month
                    if today.month == 12:
                        next_date = today.replace(year=today.year + 1, month=1, day=1)
                    else:
                        next_date = today.replace(month=today.month + 1, day=1)

            # Map common LLM frequency words to models FREQUENCY_CHOICES
            freq_map = {
                "one-time": "once",
                "one time": "once",
                "weekly": "weekly",
                "biweekly": "biweekly",
                "bi-weekly": "biweekly",
                "monthly": "monthly",
                "quarterly": "quarterly",
                "yearly": "yearly",
                "annual": "yearly",
                "annually": "yearly"
            }
            mapped_frequency = freq_map.get(frequency.lower(), "monthly")

            bill = Bill.objects.create(
                user=self.user,
                name=name.title(),
                amount=Decimal(str(amount)),
                frequency=mapped_frequency,
                due_date=due_date,
                next_due_date=next_date,
                status="pending"
            )
            return {
                "success": True,
                "message": f"✅ Bill reminder for '{bill.name}' of {self._curr_sym()}{bill.amount} created successfully. It is due on {bill.next_due_date}.",
                "bill_id": bill.id
            }
        except Exception as e:
            logger.error(f"Error in create_bill: {e}")
            return {"success": False, "error": str(e)}

    def get_bills(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Get upcoming and pending bills"""
        try:
            end_date = datetime.now().date() + timedelta(days=days_ahead)
            bills = Bill.objects.filter(
                user=self.user, 
                is_active=True,
                status__in=["pending", "overdue"]
            ).order_by("next_due_date")

            bills_list = []
            for b in bills:
                # only show if due date is within our window or overdue
                if b.next_due_date <= end_date or b.status == "overdue":
                    bills_list.append(
                        {
                            "id": b.id,
                            "name": b.name,
                            "amount": float(b.amount),
                            "frequency": b.frequency,
                            "next_due_date": b.next_due_date.isoformat(),
                            "status": b.status,
                            "days_until_due": b.days_until_due(),
                        }
                    )

            return {"success": True, "bills": bills_list}
        except Exception as e:
            logger.error(f"Error in get_bills: {e}")
            return {"success": False, "error": str(e)}

    def pay_bill(self, bill_id: int, amount: float = None) -> Dict[str, Any]:
        """Mark a bill as paid, create a transaction, and update account balance"""
        try:
            from transactions.models import Category as TransCategory

            bill = Bill.objects.get(id=bill_id, user=self.user)
            pay_amount = Decimal(str(amount)) if amount is not None else bill.amount

            # --- Find or create a category for this bill ---
            category = bill.category
            if not category:
                category_name = bill.name.title()
                category, _ = TransCategory.objects.get_or_create(
                    name=category_name,
                    defaults={"category_type": "expense"}
                )

            # --- Find or use primary account ---
            account = bill.account or Account.objects.filter(user=self.user).first()

            # --- Create Transaction so it appears in the Transactions section ---
            # Note: the post_save signal on Transaction auto-deducts from account balance
            transaction = None
            if account:
                transaction = Transaction.objects.create(
                    user=self.user,
                    account=account,
                    category=category,
                    transaction_type="expense",
                    amount=pay_amount,
                    description=f"Bill payment: {bill.name}",
                    date=datetime.now().date(),
                    notes="Paid via Finance Assistant",
                    is_recurring=bill.frequency != "once",
                )

            # --- Record the BillPayment ---
            payment = BillPayment.objects.create(
                bill=bill,
                paid_date=datetime.now().date(),
                amount_paid=pay_amount,
                notes="Paid via Finance Assistant",
                transaction_id=str(transaction.id) if transaction else "",
            )

            # --- Update bill status ---
            bill.status = "paid"
            bill.last_paid_date = payment.paid_date

            # If recurring, advance to next cycle
            if bill.frequency != "once":
                bill.next_due_date = bill.get_next_due_date()
                bill.status = "pending"

            bill.save()

            return {
                "success": True,
                "message": f"\u2705 Successfully paid {self._curr_sym()}{pay_amount} for '{bill.name}'. A transaction has been recorded.",
                "bill_name": bill.name,
                "amount_paid": float(pay_amount),
                "transaction_id": transaction.id if transaction else None,
                "next_due_date": bill.next_due_date.isoformat() if bill.frequency != "once" else None
            }
        except Bill.DoesNotExist:
            return {"success": False, "error": "Bill not found"}
        except Exception as e:
            logger.error(f"Error in pay_bill: {e}")
            return {"success": False, "error": str(e)}


    # ============= BUDGET FUNCTIONS =============

    def get_budget_status(self) -> Dict[str, Any]:
        """Get status of all active budgets"""
        try:
            budgets = Budget.objects.filter(user=self.user, is_active=True)
            budget_status = {}

            for budget in budgets:
                spent = budget.get_spent_amount()
                remaining = budget.amount - spent
                percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0

                status = (
                    "on_track"
                    if percentage <= 80
                    else "at_risk"
                    if percentage <= 100
                    else "exceeded"
                )

                budget_status[budget.category.name] = {
                    "budget": float(budget.amount),
                    "spent": float(spent),
                    "remaining": float(remaining),
                    "percentage": round(percentage, 2),
                    "period": budget.period,
                    "status": status,
                }

            return {"success": True, "budgets": budget_status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_budget(
        self, amount: float, category_name: str = None, category_id: int = None, period: str = "monthly"
    ) -> Dict[str, Any]:
        """Create a new budget for a category.
        Looks up the category by name (case-insensitive) or creates it if missing.
        Auto-calculates start_date and end_date from the period.
        """
        try:
            from transactions.models import Category
            from datetime import date
            from dateutil.relativedelta import relativedelta

            # --- Resolve category ---
            category = None

            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    pass

            if category is None and category_name:
                # Try exact match first, then case-insensitive partial
                category = (
                    Category.objects.filter(name__iexact=category_name.strip()).first()
                    or Category.objects.filter(name__icontains=category_name.strip()).first()
                )
                if category is None:
                    # Create it as an expense category
                    category = Category.objects.create(
                        name=category_name.strip().title(),
                        category_type="expense",
                    )
                    logger.info(f"[create_budget] Created new category: {category.name}")

            if category is None:
                all_cats = list(Category.objects.filter(category_type="expense").values_list("name", flat=True))
                return {
                    "success": False,
                    "error": f"Could not resolve category. Available expense categories: {all_cats}"
                }

            # --- Check if budget already exists and update it ---
            today = date.today()
            if period == "daily":
                start, end = today, today
            elif period == "weekly":
                start = today - timedelta(days=today.weekday())
                end = start + timedelta(days=6)
            elif period == "yearly":
                start = date(today.year, 1, 1)
                end = date(today.year, 12, 31)
            else:  # monthly (default)
                start = date(today.year, today.month, 1)
                end = start + relativedelta(months=1) - timedelta(days=1)

            existing = Budget.objects.filter(
                user=self.user, category=category, is_active=True
            ).first()

            if existing:
                # Update existing budget amount
                existing.amount = Decimal(str(amount))
                existing.period = period
                existing.start_date = start
                existing.end_date = end
                existing.save()
                return {
                    "success": True,
                    "message": f"\u2705 Updated budget for '{category.name}' to {self._curr_sym()}{amount:.2f}/{period}",
                    "budget_id": existing.id,
                    "category": category.name,
                    "amount": amount,
                    "period": period,
                }

            budget = Budget.objects.create(
                user=self.user,
                category=category,
                amount=Decimal(str(amount)),
                period=period,
                start_date=start,
                end_date=end,
                is_active=True,
            )

            return {
                "success": True,
                "message": f"\u2705 Budget of {self._curr_sym()}{amount:.2f}/{period} set for '{category.name}'",
                "budget_id": budget.id,
                "category": category.name,
                "amount": amount,
                "period": period,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in create_budget: {e}")
            return {"success": False, "error": str(e)}

    # ============= SUMMARY & ANALYTICS =============

    def get_financial_summary(self) -> Dict[str, Any]:
        """Get complete financial overview"""
        try:
            from django.db.models import Sum

            # Get accounts
            accounts = Account.objects.filter(user=self.user)
            total_balance = accounts.aggregate(Sum("balance"))["balance__sum"] or 0

            # Last 30 days transactions
            start_date = datetime.now() - timedelta(days=30)
            recent_transactions = Transaction.objects.filter(
                user=self.user, date__gte=start_date
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
                "success": True,
                "total_balance": float(total_balance),
                "monthly_income": float(income),
                "monthly_expenses": float(expenses),
                "net_monthly": float(income - expenses),
                "accounts_count": accounts.count(),
                "transactions_count": recent_transactions.count(),
                "savings_rate": round(
                    (float(income - expenses) / float(income) * 100)
                    if income > 0
                    else 0,
                    2,
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_spending_insights(self) -> Dict[str, Any]:
        """Get personalized spending insights and recommendations"""
        try:
            summary = self.get_financial_summary()
            if not summary["success"]:
                return summary

            insights = []

            monthly_income = summary["monthly_income"]
            monthly_expenses = summary["monthly_expenses"]
            net = summary["net_monthly"]

            # Analyze spending patterns
            if monthly_expenses > monthly_income:
                insights.append(
                    "⚠️ Your expenses exceed your income! Consider cutting back on spending."
                )

            savings_rate = summary["savings_rate"]
            if savings_rate > 30:
                insights.append(
                    f"✅ Excellent! You're saving {savings_rate}% of your income - keep it up!"
                )
            elif savings_rate > 15:
                insights.append(
                    f"📈 Good job! You're saving {savings_rate}%. Try to increase this to 20%+ for financial security."
                )
            elif savings_rate > 0:
                insights.append(
                    f"💡 You're saving {savings_rate}% of income. Aim for at least 15-20% for long-term financial health."
                )
            else:
                insights.append(
                    "🚨 You're not saving anything. Make saving a priority!"
                )

            # Check budgets
            budgets = Budget.objects.filter(user=self.user, is_active=True)
            exceeded_count = 0
            for budget in budgets:
                spent = budget.get_spent_amount()
                if spent > budget.amount:
                    exceeded_count += 1

            if exceeded_count > 0:
                insights.append(
                    f"⚠️ You've exceeded {exceeded_count} budget(s) this month."
                )

            return {"success": True, "insights": insights}
        except Exception as e:
            logger.error(f"Error in get_spending_insights: {e}")
            return {"success": False, "error": str(e)}

    # ============= TOOL REGISTRY =============

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools for the LLM"""
        return [
            {
                "name": "create_savings_goal",
                "description": "Create a new savings goal",
                "parameters": {
                    "goal_name": "str - Name of the goal (e.g., 'Bike', 'Vacation')",
                    "target_amount": "float - Target amount to save",
                    "target_date": "str - Target date in YYYY-MM-DD format (optional)",
                    "category": "str - Category like 'travel', 'purchase', 'emergency', 'other' (default: 'other')",
                    "description": "str - Additional description (optional)",
                },
            },
            {
                "name": "add_goal_contribution",
                "description": "Add money to a savings goal by name or ID",
                "parameters": {
                    "amount": "float - Amount to add (REQUIRED)",
                    "goal_name": "str - Name of the goal (e.g. 'PC', 'bike'). Use this instead of goal_id when the user mentions a name.",
                    "goal_id": "int - ID of the goal (optional, use goal_name instead)",
                },
            },
            {
                "name": "get_all_goals",
                "description": "Retrieve all active savings goals",
                "parameters": {},
            },
            {
                "name": "delete_goal",
                "description": "Delete/deactivate a savings goal",
                "parameters": {"goal_id": "int - ID of the goal"},
            },
            {
                "name": "add_transaction",
                "description": "Add a new income or expense transaction",
                "parameters": {
                    "amount": "float - The amount of the transaction",
                    "transaction_type": "str - Either 'income' or 'expense'",
                    "category_name": "str - Category of transaction (default: 'Uncategorized')",
                    "date": "str - Date in YYYY-MM-DD format (optional, defaults to today)",
                    "description": "str - Optional description of the transaction"
                },
            },
            {
                "name": "get_transactions",
                "description": "Get recent transactions",
                "parameters": {
                    "limit": "int - Number of transactions (default: 10)",
                    "days": "int - How many days back (default: 30)",
                },
            },
            {
                "name": "get_spending_breakdown",
                "description": "Get spending analysis by category",
                "parameters": {"days": "int - How many days back (default: 30)"},
            },
            {
                "name": "get_income_vs_expenses",
                "description": "Get income vs expenses comparison",
                "parameters": {"days": "int - How many days back (default: 30)"},
            },
            {
                "name": "get_accounts",
                "description": "Get all user accounts and total balance",
                "parameters": {},
            },
            {
                "name": "get_bills",
                "description": "Get upcoming and pending bills",
                "parameters": {"days_ahead": "int - How many days ahead to look (default: 30)"},
            },
            {
                "name": "create_bill",
                "description": "Set a new bill reminder",
                "parameters": {
                    "name": "str - Name of the bill (e.g., 'Internet', 'Rent')",
                    "amount": "float - The amount of the bill",
                    "frequency": "str - 'once', 'weekly', 'biweekly', 'monthly', 'quarterly', 'yearly' (default: 'monthly')",
                    "due_date": "int - Day of the month it's due (1-31, optional)",
                    "next_due_date": "str - Exact date it is next due in YYYY-MM-DD format (optional)"
                },
            },
            {
                "name": "pay_bill",
                "description": "Mark a bill as paid",
                "parameters": {
                    "bill_id": "int - ID of the bill",
                    "amount": "float - Optional custom amount, defaults to bill amount",
                },
            },
            {
                "name": "get_budget_status",
                "description": "Get status of all active budgets",
                "parameters": {},
            },
            {
                "name": "create_budget",
                "description": "Create or update a budget for a spending category. Always use category_name — never guess a category_id.",
                "parameters": {
                    "amount": "float - Budget amount (REQUIRED)",
                    "category_name": "str - Category name e.g. 'Food', 'Transport', 'Entertainment'. Will be looked up in DB or created if missing. (REQUIRED)",
                    "period": "str - 'daily', 'weekly', 'monthly' (default), or 'yearly'",
                },
            },
            {
                "name": "get_financial_summary",
                "description": "Get complete financial overview",
                "parameters": {},
            },
            {
                "name": "get_spending_insights",
                "description": "Get personalized spending insights and recommendations",
                "parameters": {},
            },
        ]

    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically call a tool by name"""
        if hasattr(self, tool_name):
            try:
                method = getattr(self, tool_name)
                return method(**parameters)
            except TypeError as e:
                return {"success": False, "error": f"Invalid parameters: {str(e)}"}
        else:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
