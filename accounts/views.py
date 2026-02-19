from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Account
from .serializers import UserSerializer, AccountSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for users (read-only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class AccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for financial accounts
    """
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter accounts by current user"""
        return Account.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user to current user when creating account"""
        serializer.save(user=self.request.user)
