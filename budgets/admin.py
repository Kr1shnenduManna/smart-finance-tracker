from django.contrib import admin
from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'period', 'start_date', 'end_date', 'is_active', 'alert_threshold']
    list_filter = ['period', 'is_active', 'category']
    search_fields = ['user__username', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
