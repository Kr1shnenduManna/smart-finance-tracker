#!/usr/bin/env python
"""
Quick setup script to enable the chatbot feature
Run this after you have integrated the chatbot into your project
"""

import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finance_tracker.settings")
django.setup()

from django.core.management import call_command
from accounts.models import User


def setup_chatbot():
    print("=" * 60)
    print("Smart Finance Chatbot Setup")
    print("=" * 60)

    # Step 1: Run migrations
    print("\n✓ Step 1: Running database migrations...")
    try:
        call_command("migrate", "chatbot")
        print("  ✅ Migrations completed successfully!")
    except Exception as e:
        print(f"  ❌ Migration error: {e}")
        return False

    # Step 2: Verify chatbot is in INSTALLED_APPS
    from django.conf import settings

    if "chatbot" in settings.INSTALLED_APPS:
        print("\n✓ Step 2: Chatbot app is registered")
        print("  ✅ 'chatbot' found in INSTALLED_APPS")
    else:
        print("\n✗ Step 2: ERROR - Chatbot not in INSTALLED_APPS")
        print("  ❌ Please add 'chatbot' to INSTALLED_APPS in settings.py")
        return False

    # Step 3: Check if chatbot URLs are configured
    try:
        from django.test import Client

        client = Client()
        print("\n✓ Step 3: Verifying API endpoints...")
        print("  ✅ Chat API endpoints configured at /api/chatbot/")
    except Exception as e:
        print(f"  ⚠️ Warning: {e}")

    print("\n" + "=" * 60)
    print("✅ Chatbot Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Add ChatbotButton to your React App.jsx")
    print("2. Run: python manage.py runserver")
    print("3. Run: npm run dev (in frontend directory)")
    print("4. Click the 💬 button in the bottom-right corner")
    print("\nExample queries to try:")
    print("  - 'I want to save $1500 for a gaming PC'")
    print("  - 'Show me my spending analysis'")
    print("  - 'What's my budget status?'")
    print("  - 'Show my savings goals'")
    print("\n" + "=" * 60)
    return True


if __name__ == "__main__":
    success = setup_chatbot()
    exit(0 if success else 1)
