from django.core.management.base import BaseCommand
from transactions.models import Category


class Command(BaseCommand):
    help = "Populate database with default categories"

    def handle(self, *args, **options):
        # Income categories
        income_categories = [
            {"name": "Salary", "icon": "banknote", "color": "#4CAF50"},
            {"name": "Freelance", "icon": "briefcase", "color": "#8BC34A"},
            {"name": "Investment", "icon": "trending-up", "color": "#009688"},
            {"name": "Business", "icon": "building", "color": "#00BCD4"},
            {"name": "Rental Income", "icon": "home", "color": "#03A9F4"},
            {"name": "Gift", "icon": "gift", "color": "#2196F3"},
            {"name": "Other Income", "icon": "plus", "color": "#607D8B"},
        ]

        # Expense categories
        expense_categories = [
            {"name": "Food & Drinks", "icon": "utensils", "color": "#FF5722"},
            {"name": "Groceries", "icon": "shopping-cart", "color": "#FF9800"},
            {"name": "Transport", "icon": "car", "color": "#FFC107"},
            {"name": "Rent", "icon": "home", "color": "#795548"},
            {"name": "Utilities", "icon": "zap", "color": "#CDDC39"},
            {"name": "Healthcare", "icon": "heart-pulse", "color": "#8BC34A"},
            {"name": "Entertainment", "icon": "film", "color": "#4CAF50"},
            {"name": "Shopping", "icon": "shopping-bag", "color": "#009688"},
            {"name": "Education", "icon": "book-open", "color": "#00BCD4"},
            {"name": "Personal Care", "icon": "scissors", "color": "#03A9F4"},
            {"name": "Travel", "icon": "plane", "color": "#2196F3"},
            {"name": "Insurance", "icon": "shield", "color": "#3F51B5"},
            {"name": "EMI & Loans", "icon": "credit-card", "color": "#9C27B0"},
            {"name": "Subscriptions", "icon": "repeat", "color": "#673AB7"},
            {"name": "Recharge & Bills", "icon": "smartphone", "color": "#E91E63"},
            {"name": "Other Expense", "icon": "minus-circle", "color": "#607D8B"},
        ]

        # Create income categories
        for cat_data in income_categories:
            Category.objects.get_or_create(
                name=cat_data["name"],
                category_type="income",
                defaults={
                    "icon": cat_data["icon"],
                    "color": cat_data["color"],
                    "is_system": True,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created income category: {cat_data['name']}")
            )

        # Create expense categories
        for cat_data in expense_categories:
            Category.objects.get_or_create(
                name=cat_data["name"],
                category_type="expense",
                defaults={
                    "icon": cat_data["icon"],
                    "color": cat_data["color"],
                    "is_system": True,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created expense category: {cat_data['name']}")
            )

        self.stdout.write(self.style.SUCCESS("Successfully populated categories"))
