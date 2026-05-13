from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import Bill, BillPayment, BillNotification
from .serializers import (
    BillSerializer,
    BillPaymentSerializer,
    BillNotificationSerializer,
)
from transactions.models import Transaction, Category


class BillViewSet(viewsets.ModelViewSet):
    """Viewset for managing bills"""

    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bill.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        """Mark a bill as paid — creates a transaction and updates account balance"""
        bill = self.get_object()
        amount_paid = Decimal(str(request.data.get("amount_paid", bill.amount)))
        notes = request.data.get("notes", "")

        # Use the bill's linked account, or fall back to user's primary account
        from accounts.models import Account as UserAccount
        account = bill.account or UserAccount.objects.filter(
            user=request.user, is_active=True
        ).first()

        # Try to use the bill's category, fall back to a generic "Bills" category
        category = bill.category
        if not category:
            category = Category.objects.filter(
                name="Bills", category_type="expense"
            ).first()
            if not category:
                category = Category.objects.create(
                    name="Bills", category_type="expense", is_system=True
                )

        # Always create a transaction (signal handles balance deduction automatically)
        transaction = None
        if account:
            transaction = Transaction.objects.create(
                user=request.user,
                account=account,
                category=category,
                transaction_type="expense",
                amount=amount_paid,
                description=f"Bill payment: {bill.name}",
                date=timezone.now().date(),
                notes=notes or f"Payment for bill: {bill.name}",
                is_recurring=bill.frequency != "once",
            )

        payment = BillPayment.objects.create(
            bill=bill,
            paid_date=timezone.now().date(),
            amount_paid=amount_paid,
            notes=notes,
            transaction_id=str(transaction.id) if transaction else "",
        )

        bill.status = "paid"
        bill.last_paid_date = timezone.now().date()

        # Advance next_due_date for recurring bills
        if bill.frequency != "once":
            bill.next_due_date = bill.get_next_due_date()
            bill.status = "pending"  # Reset to pending for next cycle

        bill.save()

        # Create notification
        BillNotification.objects.create(
            bill=bill, user=request.user, notification_type="paid"
        )

        return Response(
            {
                "message": "Bill marked as paid",
                "payment": BillPaymentSerializer(payment).data,
                "transaction_id": transaction.id if transaction else None,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a bill"""
        bill = self.get_object()
        bill.status = "cancelled"
        bill.is_active = False
        bill.save()

        return Response({"message": "Bill cancelled"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming bills (next 30 days)"""
        today = timezone.now().date()
        from datetime import timedelta

        thirty_days_later = today + timedelta(days=30)

        bills = Bill.objects.filter(
            user=request.user,
            is_active=True,
            status="pending",
            next_due_date__gte=today,
            next_due_date__lte=thirty_days_later,
        ).order_by("next_due_date")

        serializer = self.get_serializer(bills, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get overdue bills"""
        today = timezone.now().date()
        bills = Bill.objects.filter(
            user=request.user, is_active=True, status="pending", next_due_date__lt=today
        ).order_by("next_due_date")

        serializer = self.get_serializer(bills, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get bills summary"""
        # Process any due auto-pay bills first
        self._process_autopay(request.user)

        bills = self.get_queryset()
        total_bills = bills.count()
        active_bills = bills.filter(is_active=True).count()
        pending_bills = bills.filter(status="pending").count()
        total_monthly = sum(
            b.amount for b in bills.filter(frequency="monthly", is_active=True)
        )

        today = timezone.now().date()
        overdue_bills = bills.filter(status="pending", next_due_date__lt=today).count()

        return Response(
            {
                "total_bills": total_bills,
                "active_bills": active_bills,
                "pending_bills": pending_bills,
                "overdue_bills": overdue_bills,
                "total_monthly_amount": str(total_monthly),
            }
        )

    @action(detail=False, methods=["post"])
    def process_autopay(self, request):
        """Manually trigger auto-pay processing for due bills"""
        paid_bills = self._process_autopay(request.user)
        return Response(
            {
                "message": f"Processed {len(paid_bills)} auto-pay bill(s)",
                "paid_bills": [
                    {"id": b.id, "name": b.name, "amount": str(b.amount)}
                    for b in paid_bills
                ],
            },
            status=status.HTTP_200_OK,
        )

    def _process_autopay(self, user):
        """Internal: auto-pay all bills that are due and have is_automatic=True"""
        today = timezone.now().date()
        due_bills = Bill.objects.filter(
            user=user,
            is_active=True,
            is_automatic=True,
            status="pending",
            next_due_date__lte=today,
            account__isnull=False,  # Must have a linked account
        )

        paid_bills = []
        for bill in due_bills:
            # Check account has sufficient funds (skip credit cards)
            if (
                bill.account.account_type != "credit_card"
                and bill.account.balance < bill.amount
            ):
                # Insufficient funds — create overdue notification instead
                BillNotification.objects.create(
                    bill=bill,
                    user=user,
                    notification_type="overdue",
                )
                continue

            # Find or create category
            category = bill.category
            if not category:
                category = Category.objects.filter(
                    name="Bills", category_type="expense"
                ).first()
                if not category:
                    category = Category.objects.create(
                        name="Bills", category_type="expense", is_system=True
                    )

            # Create transaction (signal handles account balance)
            transaction = Transaction.objects.create(
                user=user,
                account=bill.account,
                category=category,
                transaction_type="expense",
                amount=bill.amount,
                description=f"Auto-pay: {bill.name}",
                date=today,
                notes=f"Automatic payment for {bill.name}",
                is_recurring=bill.frequency != "once",
            )

            # Record payment
            BillPayment.objects.create(
                bill=bill,
                paid_date=today,
                amount_paid=bill.amount,
                notes="Auto-pay",
                transaction_id=str(transaction.id),
            )

            bill.status = "paid"
            bill.last_paid_date = today

            # Advance to next due date for recurring bills
            if bill.frequency != "once":
                bill.next_due_date = bill.get_next_due_date()
                bill.status = "pending"

            bill.save()

            BillNotification.objects.create(
                bill=bill, user=user, notification_type="paid"
            )
            paid_bills.append(bill)

        return paid_bills

    def list(self, request, *args, **kwargs):
        """Override list to auto-pay due bills before returning"""
        self._process_autopay(request.user)
        return super().list(request, *args, **kwargs)


class BillPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for viewing bill payments"""

    serializer_class = BillPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BillPayment.objects.filter(bill__user=self.request.user)


class BillNotificationViewSet(viewsets.ModelViewSet):
    """Viewset for managing bill notifications"""

    serializer_class = BillNotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return BillNotification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"message": f"{count} notifications marked as read"})
