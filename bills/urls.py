from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BillViewSet, BillPaymentViewSet, BillNotificationViewSet

router = DefaultRouter()
router.register(r"bills", BillViewSet, basename="bill")
router.register(r"payments", BillPaymentViewSet, basename="bill-payment")
router.register(r"notifications", BillNotificationViewSet, basename="bill-notification")

urlpatterns = [
    path("", include(router.urls)),
]
