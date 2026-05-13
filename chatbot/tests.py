from django.test import TestCase
from accounts.models import User
from .models import ChatSession, ChatMessage


class ChatSessionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_chat_session(self):
        """Test creating a chat session"""
        session = ChatSession.objects.create(user=self.user, title="Test Chat")
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.title, "Test Chat")
        self.assertTrue(session.is_active)

    def test_create_chat_message(self):
        """Test creating a chat message"""
        session = ChatSession.objects.create(user=self.user, title="Test Chat")

        message = ChatMessage.objects.create(
            session=session, role="user", content="Hello chatbot!"
        )

        self.assertEqual(message.session, session)
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello chatbot!")
