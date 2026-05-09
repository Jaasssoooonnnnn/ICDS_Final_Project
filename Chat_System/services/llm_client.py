"""Provider selection for project chatbot, summary, and keyword features."""

from __future__ import annotations

from services.config import env_value, load_project_env
from services.gemini_client import GeminiClient
from services.openai_client import OpenAIClient


def _usable_key(value: str) -> bool:
    value = (value or "").strip()
    return bool(value) and not value.lower().startswith("replace-with-")


class LLMClient:
    """Use Gemini when configured, otherwise fall back to OpenAI."""

    def __init__(self):
        load_project_env()
        gemini_key = env_value("GEMINI_API_KEY")
        openai_key = env_value("OPENAI_API_KEY")
        if _usable_key(gemini_key):
            self.provider = "Gemini"
            self.client = GeminiClient(api_key=gemini_key)
        elif _usable_key(openai_key):
            self.provider = "OpenAI"
            self.client = OpenAIClient(api_key=openai_key)
        else:
            raise RuntimeError("Missing AI API key: set GEMINI_API_KEY or OPENAI_API_KEY in .env")

    def bot_reply(self, user_message: str, context: str, personality: str = "concise helpful teammate") -> str:
        return self.client.bot_reply(user_message, context, personality)

    def summarize(self, context: str) -> str:
        return self.client.summarize(context)

    def keywords(self, context: str) -> list[str]:
        return self.client.keywords(context)
