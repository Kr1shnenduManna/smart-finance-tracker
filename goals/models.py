from django.db import models
from django.utils import timezone
from decimal import Decimal
from accounts.models import User, Account


class SavingsGoal(models.Model):
    """Savings Goal model for tracking financial goals"""

    GOAL_CATEGORIES = [
        ("emergency", "Emergency Fund"),
        ("vacation", "Vacation"),
        ("car", "Car"),
        ("home", "Home"),
        ("education", "Education"),
        ("retirement", "Retirement"),
        ("investment", "Investment"),
        ("debt_payoff", "Debt Payoff"),
        ("other", "Other"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="savings_goals"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="savings_goals",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=GOAL_CATEGORIES, default="other")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )

    # Financial details
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Timeline
    start_date = models.DateField(auto_now_add=True)
    target_date = models.DateField()

    # Tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "savings_goals"
        ordering = ["-priority", "target_date"]
        verbose_name_plural = "Savings Goals"

    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"

    def get_progress_percentage(self):
        """Calculate progress as percentage"""
        if self.target_amount == 0:
            return 0
        progress = (self.current_amount / self.target_amount) * 100
        return min(progress, 100)

    def get_remaining_amount(self):
        """Get remaining amount needed"""
        return max(self.target_amount - self.current_amount, 0)

    def get_days_remaining(self):
        """Get days until target date"""
        delta = self.target_date - timezone.now().date()
        return max(delta.days, 0)

    def get_suggested_monthly_savings(self):
        """Calculate suggested monthly savings to reach goal"""
        from dateutil.relativedelta import relativedelta

        remaining = self.get_remaining_amount()
        target_date = self.target_date
        today = timezone.now().date()

        months_remaining = (target_date.year - today.year) * 12 + (
            target_date.month - today.month
        )

        if months_remaining <= 0:
            return remaining

        return Decimal(remaining) / Decimal(months_remaining)

    def add_contribution(self, amount):
        """Add contribution to the goal"""
        self.current_amount += amount
        if self.current_amount >= self.target_amount:
            self.is_active = False
            self.completed_at = timezone.now().date()
        self.save()
        return self

    def is_on_track(self):
        """Check if goal is on track based on time and progress"""
        progress_needed = (
            100
            * (timezone.now().date() - self.start_date).days
            / (self.target_date - self.start_date).days
        )
        current_progress = self.get_progress_percentage()
        return current_progress >= progress_needed * 0.8  # 20% buffer


class GoalContribution(models.Model):
    """Track contributions to savings goals"""

    goal = models.ForeignKey(
        SavingsGoal, on_delete=models.CASCADE, related_name="contributions"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    contribution_date = models.DateField()
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source of contribution (e.g., salary, bonus)",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "goal_contributions"
        ordering = ["-contribution_date"]

    def __str__(self):
        return f"{self.goal.name} - {self.amount} on {self.contribution_date}"


class GoalMilestone(models.Model):
    """Milestones for savings goals"""

    goal = models.ForeignKey(
        SavingsGoal, on_delete=models.CASCADE, related_name="milestones"
    )
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    target_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "goal_milestones"
        ordering = ["target_amount"]

    def __str__(self):
        return f"{self.goal.name} - {self.name} ({self.target_amount})"
