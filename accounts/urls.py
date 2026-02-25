from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    AccountViewSet,
    register,
    currency_list,
    exchange_rate,
    all_exchange_rates,
)

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"accounts", AccountViewSet, basename="account")

urlpatterns = [
    path("register/", register, name="register"),
    path("currencies/", currency_list, name="currency-list"),
    path("exchange-rate/", exchange_rate, name="exchange-rate"),
    path("exchange-rates/", all_exchange_rates, name="all-exchange-rates"),
    path("", include(router.urls)),
]
