from django.contrib import admin
from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'icon', 'color', 'is_system']
    list_filter = ['category_type', 'is_system']
    search_fields = ['name', 'description']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'account', 'transaction_type', 'amount', 'category', 'auto_categorized']
    list_filter = ['transaction_type', 'date', 'category', 'is_recurring', 'auto_categorized']
    search_fields = ['description', 'notes', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
