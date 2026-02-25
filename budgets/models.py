from django.db import models
from django.db.models import Sum
from accounts.models import User
from transactions.models import Category


class Budget(models.Model):
    """Budget model for managing spending limits"""
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    alert_threshold = models.IntegerField(default=80, help_text="Alert when spending reaches this percentage")
    predicted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category.name} - {self.amount} ({self.period})"
    
    class Meta:
        db_table = 'budgets'
        ordering = ['-created_at']
    
    def get_spent_amount(self):
        """Calculate total spent in this budget period"""
        from transactions.models import Transaction
        spent = Transaction.objects.filter(
            user=self.user,
            category=self.category,
            transaction_type='expense',
            date__gte=self.start_date,
            date__lte=self.end_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        return spent
    
    def get_remaining_amount(self):
        """Calculate remaining budget amount"""
        return self.amount - self.get_spent_amount()
    
    def get_spent_percentage(self):
        """Calculate percentage of budget spent"""
        if self.amount > 0:
            return (self.get_spent_amount() / self.amount) * 100
        return 0
