"""Small OpenAI Responses API wrapper for bot, summary, and keywords."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from services.config import env_value, load_project_env


class OpenAIClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        load_project_env()
        self.api_key = (api_key if api_key is not None else env_value("OPENAI_API_KEY")).strip()
        if not self.api_key:
            raise RuntimeError("Missing required environment variable: OPENAI_API_KEY")
        self.model = model or env_value("OPENAI_MODEL", "gpt-4.1-mini")
        self.base_url = env_value("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    def _generate(self, prompt: str, instructions: str = "") -> str:
        payload = {
            "model": self.model,
            "input": prompt,
        }
        if instructions:
            payload["instructions"] = instructions
        request = urllib.request.Request(
            self.base_url + "/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            details = details.replace(self.api_key, "<redacted>")
            raise RuntimeError(f"OpenAI API error {exc.code}: {details}") from exc
        except (urllib.error.URLError, ValueError) as exc:
            details = str(exc).replace(self.api_key, "<redacted>")
            raise RuntimeError(f"OpenAI connection error: {details}") from exc

        text = data.get("output_text")
        if text:
            return str(text).strip()
        parts = []
        for item in data.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    parts.append(content["text"])
        if parts:
            return "\n".join(parts).strip()
        raise RuntimeError("OpenAI returned an empty response")

    def bot_reply(self, user_message: str, context: str, personality: str = "concise helpful teammate") -> str:
        instructions = (
            "You are ICDS Bot, a concise helpful chatbot inside a group chat. "
            f"Current personality: {personality}. "
            "Use recent chat context when useful. Keep replies under 180 words unless asked otherwise."
        )
        prompt = f"Recent context:\n{context}\n\nUser request:\n{user_message}"
        return self._generate(prompt, instructions=instructions)

    def summarize(self, context: str) -> str:
        return self._generate(
            "Summarize the actual recent chat history in 3 concise bullets. Do not invent details.\n\n" + context
        )

    def keywords(self, context: str) -> list[str]:
        text = self._generate(
            "Extract 5 to 8 important topic keywords from the actual recent chat history. "
            "Return only short comma-separated tags, no preamble.\n\n"
            + context
        )
        tags = [part.strip().lstrip("#") for part in text.replace("\n", ",").split(",")]
        return [tag for tag in tags if tag][:8]
