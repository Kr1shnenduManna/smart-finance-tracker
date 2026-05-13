from django.contrib import admin
from .models import ChatSession, ChatMessage, ChatAction, ChatInsight


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created_at", "is_active"]
    list_filter = ["created_at", "is_active"]
    search_fields = ["user__username", "title"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "role", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["session__id", "content"]
    readonly_fields = ["created_at"]


@admin.register(ChatAction)
class ChatActionAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "action_type", "status", "created_at"]
    list_filter = ["action_type", "status", "created_at"]
    search_fields = ["session__id", "description"]
    readonly_fields = ["created_at"]


@admin.register(ChatInsight)
class ChatInsightAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "category", "title", "created_at"]
    list_filter = ["category", "created_at"]
    search_fields = ["user__username", "title", "content"]
    readonly_fields = ["created_at"]
