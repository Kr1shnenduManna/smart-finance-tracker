from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Account
from transactions.models import Category


class Bill(models.Model):
    """Bill model for tracking recurring and one-time bills"""

    FREQUENCY_CHOICES = [
        ("once", "One-time"),
        ("weekly", "Weekly"),
        ("biweekly", "Bi-weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bills")
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="bills"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )

    name = models.CharField(
        max_length=255, help_text="e.g., Electric Bill, Internet, Rent"
    )
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default="monthly"
    )
    due_date = models.IntegerField(help_text="Day of month for recurring bills (1-31)")
    is_automatic = models.BooleanField(default=False, help_text="Auto-pay from account")

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    next_due_date = models.DateField()
    last_paid_date = models.DateField(null=True, blank=True)

    # Notification settings
    notify_days_before = models.IntegerField(
        default=3, help_text="Days before due date to notify"
    )

    # Activity tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bills"
        ordering = ["next_due_date"]
        verbose_name_plural = "Bills"

    def __str__(self):
        return f"{self.name} - {self.amount} ({self.frequency})"

    def is_overdue(self):
        """Check if bill is overdue"""
        return self.status == "pending" and self.next_due_date < timezone.now().date()

    def days_until_due(self):
        """Returns days until due date"""
        delta = self.next_due_date - timezone.now().date()
        return delta.days

    def should_notify(self):
        """Check if user should be notified about bill"""
        days_until = self.days_until_due()
        return 0 <= days_until <= self.notify_days_before

    def get_next_due_date(self):
        """Calculate the next due date based on frequency"""
        from dateutil.relativedelta import relativedelta

        current = self.next_due_date
        today = timezone.now().date()

        frequency_map = {
            "weekly": relativedelta(weeks=1),
            "biweekly": relativedelta(weeks=2),
            "monthly": relativedelta(months=1),
            "quarterly": relativedelta(months=3),
            "yearly": relativedelta(years=1),
        }

        delta = frequency_map.get(self.frequency)
        if delta is None:
            return current  # one-time bills don't advance

        next_date = current + delta
        # If the calculated date is still in the past, keep advancing
        while next_date <= today:
            next_date += delta
        return next_date


class BillPayment(models.Model):
    """Payment history for bills"""

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="payments")
    paid_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    transaction_id = models.CharField(
        max_length=100, blank=True, help_text="Reference to transaction"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bill_payments"
        ordering = ["-paid_date"]

    def __str__(self):
        return f"{self.bill.name} - {self.amount_paid} on {self.paid_date}"


class BillNotification(models.Model):
    """Track bill notifications sent to user"""

    NOTIFICATION_TYPES = [
        ("due_soon", "Bill Due Soon"),
        ("overdue", "Bill Overdue"),
        ("paid", "Bill Paid"),
    ]

    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name="notifications"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bill_notifications"
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bill_notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} - {self.bill.name}"
