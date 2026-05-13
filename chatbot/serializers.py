from rest_framework import serializers
from .models import ChatSession, ChatMessage, ChatAction, ChatInsight


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "session", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChatActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatAction
        fields = [
            "id",
            "session",
            "action_type",
            "description",
            "parameters",
            "result",
            "status",
            "created_at",
            "completed_at",
        ]
        read_only_fields = ["id", "created_at", "completed_at", "result"]


class ChatInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInsight
        fields = [
            "id",
            "user",
            "category",
            "title",
            "content",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "title",
            "created_at",
            "updated_at",
            "is_active",
            "messages",
            "message_count",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "messages"]

    def get_message_count(self, obj):
        return obj.messages.count()
