from django.db import models
from accounts.models import User, Account, CURRENCY_CHOICES


class Category(models.Model):
    """Category model for transaction categorization"""

    CATEGORY_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#000000")
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category_type})"

    class Meta:
        db_table = "categories"
        verbose_name_plural = "Categories"
        ordering = ["name"]


class Transaction(models.Model):
    """Transaction model for income and expenses"""

    TRANSACTION_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="INR")
    original_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount in original currency before conversion",
    )
    original_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        null=True,
        blank=True,
        help_text="Original currency if different from user preferred currency",
    )
    exchange_rate = models.DecimalField(
        max_digits=14,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Exchange rate used for conversion",
    )
    description = models.TextField(blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    receipt = models.ImageField(upload_to="receipts/", blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    auto_categorized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.date}"

    class Meta:
        db_table = "transactions"
        ordering = ["-date", "-created_at"]
