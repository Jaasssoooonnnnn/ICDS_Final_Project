"""Pollinations.ai image generation client."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import requests

from services.config import RUNTIME_DIR, env_value, load_project_env


class PollinationsClient:
    def __init__(self, base_url: str | None = None, output_dir: Path | None = None):
        load_project_env()
        self.base_url = (base_url or env_value("POLLINATIONS_IMAGE_BASE_URL", "https://image.pollinations.ai/prompt")).rstrip("/")
        self.output_dir = Path(output_dir or (RUNTIME_DIR / "images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def image_url(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Image prompt cannot be empty")
        encoded = quote(prompt.strip())
        return f"{self.base_url}/{encoded}?width=768&height=512&nologo=true&enhance=true"

    def generate(self, prompt: str) -> dict:
        url = self.image_url(prompt)
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type.lower():
            raise RuntimeError(f"Pollinations returned non-image content-type: {content_type}")
        image_path = self.output_dir / f"aipic-{uuid4().hex[:12]}.jpg"
        image_path.write_bytes(response.content)
        return {
            "prompt": prompt.strip(),
            "url": url,
            "path": str(image_path),
        }
