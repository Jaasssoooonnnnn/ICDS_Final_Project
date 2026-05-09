"""Small fail-fast Gemini wrapper for bot, summary, and keywords."""

from __future__ import annotations

from services.config import env_value, load_project_env


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        load_project_env()
        self.api_key = (api_key if api_key is not None else env_value("GEMINI_API_KEY", required=True)).strip()
        if not self.api_key:
            raise RuntimeError("Missing required environment variable: GEMINI_API_KEY")
        self.model = model or env_value("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("google-genai is required for Gemini features") from exc
        self.client = genai.Client(api_key=self.api_key)

    def _generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text.strip()

    def bot_reply(self, user_message: str, context: str, personality: str = "concise helpful teammate") -> str:
        prompt = (
            "You are ICDS Bot, a concise helpful chatbot inside a group chat.\n"
            f"Current personality: {personality}.\n"
            "Use the recent chat context when it helps. Identify yourself naturally as ICDS Bot.\n\n"
            f"Recent context:\n{context}\n\n"
            f"User request:\n{user_message}\n\n"
            "Reply in a friendly, useful way. Keep it under 180 words unless asked otherwise."
        )
        return self._generate(prompt)

    def summarize(self, context: str) -> str:
        prompt = (
            "Summarize the actual recent chat history below in 3 concise bullets. "
            "Do not invent details.\n\n"
            f"{context}"
        )
        return self._generate(prompt)

    def keywords(self, context: str) -> list[str]:
        prompt = (
            "Extract 5 to 8 important topic keywords from the actual recent chat history. "
            "Return only short comma-separated tags, no preamble.\n\n"
            f"{context}"
        )
        text = self._generate(prompt)
        tags = [part.strip().lstrip("#") for part in text.replace("\n", ",").split(",")]
        return [tag for tag in tags if tag][:8]
