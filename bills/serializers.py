from rest_framework import serializers
from .models import Bill, BillPayment, BillNotification


class BillPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillPayment
        fields = [
            "id",
            "paid_date",
            "amount_paid",
            "notes",
            "transaction_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BillSerializer(serializers.ModelSerializer):
    payments = BillPaymentSerializer(many=True, read_only=True)
    days_until_due = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    should_notify = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "name",
            "description",
            "amount",
            "frequency",
            "due_date",
            "is_automatic",
            "status",
            "next_due_date",
            "last_paid_date",
            "notify_days_before",
            "is_active",
            "account",
            "account_name",
            "category",
            "category_name",
            "payments",
            "days_until_due",
            "is_overdue",
            "should_notify",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_paid_date", "created_at", "updated_at"]

    def get_days_until_due(self, obj):
        return obj.days_until_due()

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    def get_should_notify(self, obj):
        return obj.should_notify()


class BillNotificationSerializer(serializers.ModelSerializer):
    bill_name = serializers.CharField(source="bill.name", read_only=True)
    bill_amount = serializers.DecimalField(
        source="bill.amount", read_only=True, max_digits=12, decimal_places=2
    )

    class Meta:
        model = BillNotification
        fields = [
            "id",
            "bill",
            "bill_name",
            "bill_amount",
            "notification_type",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
