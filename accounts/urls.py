from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AccountViewSet, register

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"accounts", AccountViewSet, basename="account")

urlpatterns = [
    path("register/", register, name="register"),
    path("", include(router.urls)),
]
