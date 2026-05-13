from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """Stores conversation sessions"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    """Stores individual messages in a conversation"""

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"{self.session.id} - {self.role}"


class ChatAction(models.Model):
    """Tracks actions performed by the chatbot"""

    ACTION_TYPES = [
        ("create_goal", "Create Savings Goal"),
        ("create_budget", "Create Budget"),
        ("analyze_spending", "Analyze Spending"),
        ("get_suggestion", "Get Suggestion"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="actions"
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    parameters = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chat Action"
        verbose_name_plural = "Chat Actions"

    def __str__(self):
        return f"{self.session.id} - {self.action_type}"


class ChatInsight(models.Model):
    """Stores generated insights and recommendations"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_insights"
    )
    category = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chat Insight"
        verbose_name_plural = "Chat Insights"

    def __str__(self):
        return f"{self.user.username} - {self.title}"
