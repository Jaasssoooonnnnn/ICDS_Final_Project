"""Provider selection for project chatbot, summary, and keyword features."""

from __future__ import annotations

from services.config import env_value, load_project_env
from services.gemini_client import GeminiClient
from services.openai_client import OpenAIClient


def _usable_key(value: str) -> bool:
    value = (value or "").strip()
    return bool(value) and not value.lower().startswith("replace-with-")


class LLMClient:
    """Use OpenAI when configured, otherwise fall back to Gemini.

    The project originally used Gemini, but the final demo environment may only
    have an OpenAI key. Prefer OpenAI so an invalid old Gemini key cannot block
    the valid configured provider.
    """

    def __init__(self):
        load_project_env()
        preferred = env_value("AI_PROVIDER", "").lower()
        gemini_key = env_value("GEMINI_API_KEY")
        openai_key = env_value("OPENAI_API_KEY")

        self.fallback_provider = None
        self.fallback_client = None
        if preferred == "gemini" and _usable_key(gemini_key):
            self.provider = "Gemini"
            self.client = GeminiClient(api_key=gemini_key)
            if _usable_key(openai_key):
                self.fallback_provider = "OpenAI"
                self.fallback_client = OpenAIClient(api_key=openai_key)
        elif preferred == "openai" and _usable_key(openai_key):
            self.provider = "OpenAI"
            self.client = OpenAIClient(api_key=openai_key)
            if _usable_key(gemini_key):
                self.fallback_provider = "Gemini"
                self.fallback_client = GeminiClient(api_key=gemini_key)
        elif _usable_key(openai_key):
            self.provider = "OpenAI"
            self.client = OpenAIClient(api_key=openai_key)
            if _usable_key(gemini_key):
                self.fallback_provider = "Gemini"
                self.fallback_client = GeminiClient(api_key=gemini_key)
        elif _usable_key(gemini_key):
            self.provider = "Gemini"
            self.client = GeminiClient(api_key=gemini_key)
        else:
            raise RuntimeError("Missing AI API key: set GEMINI_API_KEY or OPENAI_API_KEY in .env")

    def bot_reply(self, user_message: str, context: str, personality: str = "concise helpful teammate") -> str:
        return self._call("bot_reply", user_message, context, personality)

    def summarize(self, context: str) -> str:
        return self._call("summarize", context)

    def keywords(self, context: str) -> list[str]:
        return self._call("keywords", context)

    def _call(self, method_name: str, *args):
        try:
            return getattr(self.client, method_name)(*args)
        except Exception as primary_error:
            if self.fallback_client is None:
                raise
            try:
                result = getattr(self.fallback_client, method_name)(*args)
                self.provider, self.fallback_provider = self.fallback_provider, self.provider
                self.client, self.fallback_client = self.fallback_client, self.client
                return result
            except Exception as fallback_error:
                raise RuntimeError(
                    f"{self.provider} failed: {primary_error}; "
                    f"{self.fallback_provider} failed: {fallback_error}"
                ) from fallback_error
