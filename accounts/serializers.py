from rest_framework import serializers
from .models import User, Account


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                  'profile_picture', 'created_at']
        read_only_fields = ['id', 'created_at']


class AccountSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Account
        fields = ['id', 'user', 'name', 'account_type', 'balance', 'currency', 
                  'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'balance', 'created_at', 'updated_at']
