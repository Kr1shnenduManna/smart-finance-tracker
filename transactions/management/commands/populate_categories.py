from django.core.management.base import BaseCommand
from transactions.models import Category


class Command(BaseCommand):
    help = 'Populate database with default categories'

    def handle(self, *args, **options):
        # Income categories
        income_categories = [
            {'name': 'Salary', 'icon': 'money', 'color': '#4CAF50'},
            {'name': 'Freelance', 'icon': 'briefcase', 'color': '#8BC34A'},
            {'name': 'Investment', 'icon': 'trending-up', 'color': '#009688'},
            {'name': 'Business', 'icon': 'business', 'color': '#00BCD4'},
            {'name': 'Gift', 'icon': 'gift', 'color': '#03A9F4'},
            {'name': 'Other Income', 'icon': 'plus', 'color': '#2196F3'},
        ]
        
        # Expense categories
        expense_categories = [
            {'name': 'Food & Dining', 'icon': 'restaurant', 'color': '#FF5722'},
            {'name': 'Groceries', 'icon': 'shopping-cart', 'color': '#FF9800'},
            {'name': 'Transportation', 'icon': 'car', 'color': '#FFC107'},
            {'name': 'Housing', 'icon': 'home', 'color': '#FFEB3B'},
            {'name': 'Utilities', 'icon': 'flash', 'color': '#CDDC39'},
            {'name': 'Healthcare', 'icon': 'medkit', 'color': '#8BC34A'},
            {'name': 'Entertainment', 'icon': 'film', 'color': '#4CAF50'},
            {'name': 'Shopping', 'icon': 'cart', 'color': '#009688'},
            {'name': 'Education', 'icon': 'book', 'color': '#00BCD4'},
            {'name': 'Personal Care', 'icon': 'cut', 'color': '#03A9F4'},
            {'name': 'Travel', 'icon': 'airplane', 'color': '#2196F3'},
            {'name': 'Insurance', 'icon': 'shield', 'color': '#3F51B5'},
            {'name': 'Savings', 'icon': 'piggy-bank', 'color': '#673AB7'},
            {'name': 'Debt Payment', 'icon': 'credit-card', 'color': '#9C27B0'},
            {'name': 'Other Expense', 'icon': 'minus', 'color': '#E91E63'},
        ]
        
        # Create income categories
        for cat_data in income_categories:
            Category.objects.get_or_create(
                name=cat_data['name'],
                category_type='income',
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_system': True,
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Created income category: {cat_data["name"]}'))
        
        # Create expense categories
        for cat_data in expense_categories:
            Category.objects.get_or_create(
                name=cat_data['name'],
                category_type='expense',
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_system': True,
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Created expense category: {cat_data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully populated categories'))
