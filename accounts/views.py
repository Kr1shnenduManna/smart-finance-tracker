from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import login
from .models import User, Account, CURRENCY_CHOICES, CURRENCY_SYMBOLS
from .serializers import UserSerializer, AccountSerializer, RegisterSerializer
from .currency_utils import convert_currency, get_exchange_rate, fetch_exchange_rates


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


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def currency_list(request):
    """List all supported currencies with symbols."""
    currencies = [
        {"code": code, "name": name, "symbol": CURRENCY_SYMBOLS.get(code, code)}
        for code, name in CURRENCY_CHOICES
    ]
    return Response(currencies)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def exchange_rate(request):
    """
    Get exchange rate between two currencies.
    """
    from_curr = request.query_params.get("from", "USD")
    to_curr = request.query_params.get("to", "INR")
    amount = request.query_params.get("amount")

    try:
        rate = get_exchange_rate(from_curr, to_curr)
        result = {"from": from_curr, "to": to_curr, "rate": str(rate)}

        if amount:
            converted, _ = convert_currency(float(amount), from_curr, to_curr)
            result["amount"] = amount
            result["converted"] = str(converted)

        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def all_exchange_rates(request):
    """Get all exchange rates (base USD). Useful for client-side conversion."""
    rates = fetch_exchange_rates("USD")
    return Response({"base": "USD", "rates": rates})


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
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True
            )
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
