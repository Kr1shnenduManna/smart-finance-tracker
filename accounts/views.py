from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import login
from .models import User, Account
from .serializers import UserSerializer, AccountSerializer, RegisterSerializer


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    """Create a new user account and log them in immediately."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Auto-login after registration
        login(request, user)
        return Response(
            {"detail": "Account created successfully.", "username": user.username},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for users (read-only)
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Get or update current user information"""
        if request.method == "PATCH":
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
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
