from django.db import models
from django.contrib.auth.models import AbstractUser


CURRENCY_CHOICES = [
    ("INR", "Indian Rupee"),
    ("USD", "US Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
    ("CAD", "Canadian Dollar"),
    ("AUD", "Australian Dollar"),
    ("CNY", "Chinese Yuan"),
    ("CHF", "Swiss Franc"),
    ("SGD", "Singapore Dollar"),
    ("AED", "UAE Dirham"),
    ("BDT", "Bangladeshi Taka"),
    ("BRL", "Brazilian Real"),
    ("KRW", "South Korean Won"),
    ("MYR", "Malaysian Ringgit"),
    ("THB", "Thai Baht"),
    ("ZAR", "South African Rand"),
    ("SEK", "Swedish Krona"),
    ("NOK", "Norwegian Krone"),
    ("NZD", "New Zealand Dollar"),
]

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "C$",
    "AUD": "A$",
    "CNY": "¥",
    "CHF": "CHF",
    "SGD": "S$",
    "AED": "د.إ",
    "BDT": "৳",
    "BRL": "R$",
    "KRW": "₩",
    "MYR": "RM",
    "THB": "฿",
    "ZAR": "R",
    "SEK": "kr",
    "NOK": "kr",
    "NZD": "NZ$",
}


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    preferred_currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default="INR"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "users"


class Account(models.Model):
    """Financial Account model for tracking multiple accounts per user"""

    ACCOUNT_TYPES = [
        ("checking", "Checking Account"),
        ("savings", "Savings Account"),
        ("credit_card", "Credit Card"),
        ("cash", "Cash"),
        ("investment", "Investment Account"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="INR")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    class Meta:
        db_table = "accounts"
        ordering = ["-created_at"]
