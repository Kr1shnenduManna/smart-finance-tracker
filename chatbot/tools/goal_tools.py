"""Tools for creating and managing savings goals"""

from accounts.models import User, CURRENCY_SYMBOLS
from datetime import datetime
from decimal import Decimal
import json


def create_savings_goal(user_id: int, goal_data: dict) -> dict:
    """Create a new savings goal for the user

    Args:
        user_id: User ID
        goal_data: Dictionary with keys:
            - name (str): Goal name
            - target_amount (float): Target amount
            - target_date (str): Target date (YYYY-MM-DD)
            - category (str): Goal category
            - description (str, optional): Goal description

    Returns:
        Dictionary with success/error information
    """
    try:
        from goals.models import SavingsGoal

        user = User.objects.get(id=user_id)

        goal = SavingsGoal.objects.create(
            user=user,
            name=goal_data.get("name", "Unnamed Goal"),
            target_amount=Decimal(str(goal_data.get("target_amount", 0))),
            target_date=datetime.strptime(
                goal_data.get("target_date", ""), "%Y-%m-%d"
            ).date(),
            category=goal_data.get("category", "other"),
            description=goal_data.get("description", ""),
            is_active=True,
        )

        # Format the response
        return {
            "success": True,
            "message": f"✅ Savings goal '{goal.name}' created successfully!",
            "goal_id": goal.id,
            "goal_name": goal.name,
            "target_amount": float(goal.target_amount),
            "target_date": goal.target_date.isoformat(),
            "category": goal.category,
        }

    except ValueError as ve:
        return {"success": False, "error": f"Invalid input: {str(ve)}"}
    except User.DoesNotExist:
        return {"success": False, "error": "User not found"}
    except Exception as e:
        return {"success": False, "error": f"Failed to create goal: {str(e)}"}


def get_savings_goals(user_id: int) -> dict:
    """Get all active savings goals for the user

    Args:
        user_id: User ID

    Returns:
        Dictionary with list of goals
    """
    try:
        from goals.models import SavingsGoal

        goals = SavingsGoal.objects.filter(user_id=user_id, is_active=True)

        if not goals:
            return {
                "success": True,
                "message": "You don't have any active savings goals.",
                "goals": [],
            }

        goals_list = []
        for goal in goals:
            progress = (
                (goal.current_amount / goal.target_amount * 100)
                if goal.target_amount > 0
                else 0
            )
            days_remaining = (goal.target_date - datetime.now().date()).days

            goals_list.append(
                {
                    "id": goal.id,
                    "name": goal.name,
                    "current_amount": float(goal.current_amount),
                    "target_amount": float(goal.target_amount),
                    "progress": round(progress, 2),
                    "target_date": goal.target_date.isoformat(),
                    "days_remaining": max(0, days_remaining),
                    "category": goal.category,
                }
            )

        return {
            "success": True,
            "message": f"You have {len(goals_list)} active savings goal(s).",
            "goals": goals_list,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "goals": []}


def add_goal_contribution(user_id: int, goal_id: int, amount: float) -> dict:
    """Add a contribution to a savings goal

    Args:
        user_id: User ID
        goal_id: Goal ID
        amount: Amount to contribute

    Returns:
        Dictionary with success/error information
    """
    try:
        from goals.models import SavingsGoal, GoalContribution

        goal = SavingsGoal.objects.get(id=goal_id, user_id=user_id)

        # Create contribution
        contribution = GoalContribution.objects.create(
            goal=goal, amount=Decimal(str(amount))
        )

        # Update goal's current amount
        goal.current_amount += Decimal(str(amount))
        goal.save()

        progress = (
            (goal.current_amount / goal.target_amount * 100)
            if goal.target_amount > 0
            else 0
        )

        user = User.objects.get(id=user_id)
        sym = CURRENCY_SYMBOLS.get(getattr(user, 'preferred_currency', 'USD'), '$')
        return {
            "success": True,
            "message": f"✅ Added {sym}{amount:.2f} to '{goal.name}'",
            "goal_name": goal.name,
            "amount_added": amount,
            "new_total": float(goal.current_amount),
            "target_amount": float(goal.target_amount),
            "progress": round(progress, 2),
        }

    except SavingsGoal.DoesNotExist:
        return {"success": False, "error": "Goal not found"}
    except Exception as e:
        return {"success": False, "error": f"Failed to add contribution: {str(e)}"}


def estimate_monthly_savings_needed(user_id: int, goal_name: str) -> dict:
    """Calculate how much needs to be saved monthly to reach a goal

    Args:
        user_id: User ID
        goal_name: Name of the goal

    Returns:
        Dictionary with savings estimate
    """
    try:
        from goals.models import SavingsGoal

        goal = SavingsGoal.objects.filter(
            user_id=user_id, name=goal_name, is_active=True
        ).first()

        if not goal:
            return {"success": False, "error": f"Goal '{goal_name}' not found"}

        remaining_amount = goal.target_amount - goal.current_amount
        days_remaining = (goal.target_date - datetime.now().date()).days
        months_remaining = max(1, days_remaining / 30)

        required_monthly = (
            remaining_amount / months_remaining
            if months_remaining > 0
            else remaining_amount
        )

        user = User.objects.get(id=user_id)
        sym = CURRENCY_SYMBOLS.get(getattr(user, 'preferred_currency', 'USD'), '$')
        message = f"📈 Budget Analysis for '{goal_name}':\n"
        message += f"Remaining to save: {sym}{remaining_amount:.2f}\n"
        message += f"Time remaining: {months_remaining:.1f} months\n"
        message += f"Required monthly: {sym}{required_monthly:.2f}\n"

        return {
            "success": True,
            "message": message,
            "goal_name": goal.name,
            "remaining_amount": float(remaining_amount),
            "months_remaining": round(months_remaining, 1),
            "required_monthly": float(required_monthly),
            "current_amount": float(goal.current_amount),
            "target_amount": float(goal.target_amount),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
