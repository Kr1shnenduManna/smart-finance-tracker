"""Ollama client for LLM integration"""

import requests
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for communicating with Ollama LLM"""

    def __init__(self):
        self.base_url = settings.OLLAMA_CONFIG.get("base_url", "http://localhost:11434")
        self.model = settings.OLLAMA_CONFIG.get("model", "mistral")
        self.timeout = settings.OLLAMA_CONFIG.get("timeout", 120)
        self.enabled = settings.OLLAMA_CONFIG.get("enabled", False)

    def is_available(self) -> bool:
        """Check if Ollama server is running and accessible"""
        if not self.enabled:
            return False

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama server not available: {e}")
            return False

    def get_available_models(self) -> list:
        """Get list of available models on Ollama"""
        if not self.is_available():
            return []

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")

        return []

    def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate response from Ollama model

        Args:
            prompt: User message/prompt
            context: Additional context (financial data, conversation history)
            system_prompt: System instructions for the model

        Returns:
            Generated response or None if failed
        """
        if not self.enabled:
            return None

        if not self.is_available():
            logger.warning(
                "Ollama server is not running. Falling back to intent matching."
            )
            return None

        try:
            # Build the full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"{context}\n\nUser: {prompt}"
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{full_prompt}"

            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                },
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                logger.error(
                    f"Ollama returned status {response.status_code}: {response.text}"
                )
                return None

        except requests.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None

    def generate_financial_response(
        self, user_message: str, financial_context: str, conversation_history: list
    ) -> Optional[str]:
        """
        Generate a financial advice response using Ollama

        Args:
            user_message: User's query
            financial_context: User's financial summary
            conversation_history: Previous messages in conversation

        Returns:
            Generated response or None
        """
        if not self.enabled:
            return None

        # Build system prompt for financial advisor
        system_prompt = """You are a helpful financial advisor integrated into a personal finance tracker app.
You have access to the user's financial data and transaction history.
Provide practical, actionable financial advice based on their situation.
Be concise and friendly. Format responses with clear sections using markdown.
If the user asks to create a goal or perform an action, explain what you would do.
Always be encouraging but realistic about their financial situation."""

        # Build conversation context
        history_context = ""
        if conversation_history:
            history_context = "\n\nRecent conversation:\n"
            for msg in conversation_history[-4:]:  # Last 4 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                history_context += f"{role}: {msg['content']}\n"

        # Combine all context
        full_context = f"{financial_context}{history_context}"

        return self.generate_response(
            user_message, context=full_context, system_prompt=system_prompt
        )


# Create singleton instance
ollama_client = OllamaClient()
