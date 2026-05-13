from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import ChatSession, ChatMessage, ChatAction, ChatInsight
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    ChatActionSerializer,
    ChatInsightSerializer,
)
from .agents.ai_agent import AIFinancialAgent


class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Send a message to the chatbot and get a response"""
        session = self.get_object()
        user_message = request.data.get("message", "").strip()

        if not user_message:
            return Response(
                {"error": "Message cannot be empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        if len(user_message) > 2000:
            return Response(
                {"error": "Message is too long (max 2000 characters)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Save user message
            user_msg_obj = ChatMessage.objects.create(
                session=session, role="user", content=user_message
            )

            # Initialize agent
            agent = AIFinancialAgent(request.user.id)

            # Process message with agent
            result = agent.process_message(user_message)

            if result["success"]:
                response_text = result["response"]

                # Save assistant response
                assistant_msg = ChatMessage.objects.create(
                    session=session, role="assistant", content=response_text
                )

                # Update session's updated_at
                session.updated_at = timezone.now()
                session.save(update_fields=["updated_at"])

                return Response(
                    {
                        "success": True,
                        "message_id": assistant_msg.id,
                        "response": response_text,
                        "user_message_id": user_msg_obj.id,
                        "timestamp": assistant_msg.created_at.isoformat(),
                    }
                )
            else:
                return Response(
                    {"error": result.get("error", "Failed to process message")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {"error": f"Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def get_financial_context(self, request):
        """Get user's complete financial context"""
        try:
            agent = AIFinancialAgent(request.user.id)

            return Response(
                {
                    "success": True,
                    "summary": agent.tools.get_financial_summary(),
                    "spending": agent.tools.get_spending_breakdown(),
                    "budgets": agent.tools.get_budget_status(),
                    "goals": agent.tools.get_all_goals(),
                }
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def clear_sessions(self, request):
        """Clear all chat sessions for the user"""
        ChatSession.objects.filter(user=request.user).delete()
        return Response({"message": "All chat sessions cleared"})


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.request.query_params.get("session_id")
        if session_id:
            return ChatMessage.objects.filter(
                session__user=self.request.user, session_id=session_id
            )
        return ChatMessage.objects.filter(session__user=self.request.user)


class ChatActionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatActionSerializer

    def get_queryset(self):
        return ChatAction.objects.filter(session__user=self.request.user)


class ChatInsightViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatInsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatInsight.objects.filter(user=self.request.user)
