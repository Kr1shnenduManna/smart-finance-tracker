from rest_framework import serializers
from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    spent_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    spent_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = ['id', 'user', 'category', 'category_name', 'amount', 'period', 
                  'start_date', 'end_date', 'is_active', 'alert_threshold', 
                  'predicted_amount', 'spent_amount', 'remaining_amount', 
                  'spent_percentage', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'predicted_amount', 'created_at', 'updated_at']
    
    def get_spent_amount(self, obj):
        return float(obj.get_spent_amount())
    
    def get_remaining_amount(self, obj):
        return float(obj.get_remaining_amount())
    
    def get_spent_percentage(self, obj):
        return round(obj.get_spent_percentage(), 2)
