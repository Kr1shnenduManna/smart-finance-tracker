from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatSessionViewSet,
    ChatMessageViewSet,
    ChatActionViewSet,
    ChatInsightViewSet,
)

router = DefaultRouter()
router.register(r"sessions", ChatSessionViewSet, basename="chat-session")
router.register(r"messages", ChatMessageViewSet, basename="chat-message")
router.register(r"actions", ChatActionViewSet, basename="chat-action")
router.register(r"insights", ChatInsightViewSet, basename="chat-insight")

urlpatterns = [
    path("", include(router.urls)),
]
