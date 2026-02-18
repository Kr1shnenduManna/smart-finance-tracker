from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer, TransactionCreateSerializer
from ml_features.ml_utils import get_categorizer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transaction categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def income(self, request):
        """Get income categories"""
        categories = Category.objects.filter(category_type='income')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expense(self, request):
        """Get expense categories"""
        categories = Category.objects.filter(category_type='expense')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transactions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions by current user"""
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('type', None)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve"""
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """Set user and auto-categorize when creating transaction"""
        transaction = serializer.save(user=self.request.user)
        
        # Try to auto-categorize if no category provided
        if not transaction.category and transaction.description:
            categorizer = get_categorizer()
            predicted_category, confidence = categorizer.predict(transaction.description)
            
            if predicted_category and confidence > 0.6:
                try:
                    category = Category.objects.get(name=predicted_category)
                    transaction.category = category
                    transaction.auto_categorized = True
                    transaction.save()
                except Category.DoesNotExist:
                    pass
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary statistics"""
        queryset = self.get_queryset()
        
        income = queryset.filter(transaction_type='income').aggregate(
            total=Sum('amount'), count=Count('id')
        )
        expense = queryset.filter(transaction_type='expense').aggregate(
            total=Sum('amount'), count=Count('id')
        )
        
        return Response({
            'income': {
                'total': income['total'] or 0,
                'count': income['count']
            },
            'expense': {
                'total': expense['total'] or 0,
                'count': expense['count']
            },
            'net': (income['total'] or 0) - (expense['total'] or 0)
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get transactions grouped by category"""
        queryset = self.get_queryset()
        
        # Group by category
        categories_data = queryset.values(
            'category__name', 'transaction_type'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return Response(list(categories_data))
