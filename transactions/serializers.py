from rest_framework import serializers
from .models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'description', 'icon', 'color', 
                  'is_system', 'created_at']
        read_only_fields = ['id', 'is_system', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    account_name = serializers.ReadOnlyField(source='account.name')
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'account', 'account_name', 'category', 'category_name',
                  'transaction_type', 'amount', 'description', 'date', 'notes', 
                  'receipt', 'is_recurring', 'auto_categorized', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'auto_categorized', 'created_at', 'updated_at']


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['account', 'category', 'transaction_type', 'amount', 'description', 
                  'date', 'notes', 'receipt', 'is_recurring']
