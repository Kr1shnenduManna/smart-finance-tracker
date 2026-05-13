"""Gemini API client for LLM integration"""

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for communicating with Google Gemini API"""

    def __init__(self):
        self.api_key = settings.GEMINI_CONFIG.get("api_key", "")
        self.model_name = settings.GEMINI_CONFIG.get("model", "gemini-1.5-flash")
        self.enabled = settings.GEMINI_CONFIG.get("enabled", False) and GEMINI_AVAILABLE
        self.temperature = settings.GEMINI_CONFIG.get("temperature", 0.7)

        if self.enabled and self.api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")
                self.enabled = False

    def is_available(self) -> bool:
        """Check if Gemini API is configured and accessible"""
        if not self.enabled or not self.api_key or not GEMINI_AVAILABLE:
            return False

        try:
            # Test the API by getting model info
            genai.get_model(self.model_name)
            return True
        except Exception as e:
            logger.warning(f"Gemini API not available: {e}")
            return False

    def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate response from Gemini model

        Args:
            prompt: User message/prompt
            context: Additional context (financial data, conversation history)
            system_prompt: System instructions for the model

        Returns:
            Generated response or None if failed
        """
        if not self.enabled or not self.api_key or not GEMINI_AVAILABLE:
            return None

        if not self.is_available():
            logger.warning(
                "Gemini API is not available. Falling back to intent matching."
            )
            return None

        try:
            # Build the full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nUser: {prompt}"
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\n{full_prompt}"

            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt
                or "You are a helpful financial assistant. Provide clear, concise, and actionable financial advice.",
            )

            # Generate response
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                ),
            )

            if response.text:
                return response.text.strip()
            else:
                logger.error("Gemini returned empty response")
                return None

        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            return None

    def generate_financial_response(
        self,
        user_message: str,
        financial_context: str,
        conversation_history: Optional[list] = None,
    ) -> Optional[str]:
        """
        Generate financially-aware response from Gemini

        Args:
            user_message: User's message
            financial_context: User's financial data context
            conversation_history: Previous conversation messages

        Returns:
            Generated response or None if failed
        """
        if not self.enabled or not self.api_key or not GEMINI_AVAILABLE:
            return None

        if not self.is_available():
            return None

        try:
            # Build conversation context
            conversation_text = ""
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    conversation_text += f"{role}: {content}\n"

            system_prompt = f"""You are an intelligent financial assistant helping users manage their personal finances. 
You have access to the user's financial data and should provide personalized, actionable advice.

User's Financial Context:
{financial_context}

Conversation History:
{conversation_text}

Guidelines:
- Be helpful, clear, and concise
- Provide actionable financial advice
- Consider the user's current financial situation
- Suggest improvements when appropriate
- Use emojis for better readability (e.g., 💰, 📊, ✅, ⚠️)
"""

            model = genai.GenerativeModel(
                self.model_name, system_instruction=system_prompt
            )

            response = model.generate_content(
                user_message,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                ),
            )

            if response.text:
                return response.text.strip()
            else:
                logger.error("Gemini returned empty financial response")
                return None

        except Exception as e:
            logger.error(f"Error generating financial response from Gemini: {e}")
            return None


# Global instance
gemini_client = GeminiClient()
