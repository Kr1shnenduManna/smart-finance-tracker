from django.contrib import admin
from .models import Bill, BillPayment, BillNotification


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ["name", "amount", "frequency", "status", "next_due_date", "user"]
    list_filter = ["status", "frequency", "is_active", "created_at"]
    search_fields = ["name", "user__email"]
    readonly_fields = ["last_paid_date", "created_at", "updated_at"]


@admin.register(BillPayment)
class BillPaymentAdmin(admin.ModelAdmin):
    list_display = ["bill", "paid_date", "amount_paid", "transaction_id"]
    list_filter = ["paid_date", "bill"]
    search_fields = ["bill__name", "transaction_id"]


@admin.register(BillNotification)
class BillNotificationAdmin(admin.ModelAdmin):
    list_display = ["bill", "user", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["bill__name", "user__email"]
