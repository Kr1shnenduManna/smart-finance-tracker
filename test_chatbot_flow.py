#!/usr/bin/env python
"""
Test script to verify chatbot end-to-end flow
Tests LLM integration and fallback handler
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finance_tracker.settings")
django.setup()

from django.contrib.auth import get_user_model
from chatbot.agents.ai_agent import AIFinancialAgent
from chatbot.llm.gemini_client import gemini_client
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

User = get_user_model()


def test_chatbot():
    """Test chatbot with various prompts"""

    # Get or create test user
    user, _ = User.objects.get_or_create(
        username="testuser",
        defaults={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    print(f"\n{'=' * 60}")
    print(f"Testing Chatbot with User: {user.username}")
    print(f"{'=' * 60}\n")

    # Initialize agent with user ID
    agent = AIFinancialAgent(user.id)

    # Check LLM availability
    print(f"📡 Gemini Enabled: {gemini_client.enabled}")
    print(f"📡 Gemini Available: {gemini_client.is_available()}")
    print(
        f"📡 LLM Mode: {'AI (LLM)' if gemini_client.enabled and gemini_client.is_available() else 'Fallback'}\n"
    )

    # Test cases
    test_prompts = [
        "Hi, how are you?",
        "Show my savings goals",
        "Create a goal to save 5000 for a bike",
        "Add 500 to bike funds",
        "What's my spending breakdown?",
        "Show my income vs expenses",
        "Get my financial summary",
        "What's my budget status?",
        "Can you give me spending insights?",
    ]

    print("Testing various prompts:\n")

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{i}. User: {prompt}")
        print("-" * 40)

        try:
            result = agent.process_message(prompt)

            if result.get("success"):
                response = result.get("response", "No response")
                # Show first 200 chars of response
                display_text = (
                    response[:200] + "..." if len(response) > 200 else response
                )
                print(f"✅ Response: {display_text}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")

    print(f"\n{'=' * 60}")
    print("✅ Chatbot flow test completed")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    test_chatbot()
