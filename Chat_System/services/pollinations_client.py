"""Pollinations.ai image generation client."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import requests
from PIL import Image, ImageDraw, ImageFont

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
        prompt = prompt.strip()
        url = self.image_url(prompt)
        image_path = self.output_dir / f"aipic-{uuid4().hex[:12]}.jpg"
        try:
            response = requests.get(url, timeout=(8, 60))
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type.lower():
                raise RuntimeError(f"Pollinations returned non-image content-type: {content_type}")
        except requests.RequestException as exc:
            fallback_path = self._write_fallback_image(prompt, str(exc))
            return {
                "prompt": prompt,
                "url": url,
                "path": str(fallback_path),
                "fallback": True,
                "note": "Pollinations.ai was slow, so a local demo-safe preview was generated.",
            }

        image_path.write_bytes(response.content)
        return {
            "prompt": prompt,
            "url": url,
            "path": str(image_path),
        }

    def _write_fallback_image(self, prompt: str, reason: str) -> Path:
        image_path = self.output_dir / f"aipic-fallback-{uuid4().hex[:12]}.jpg"
        image = Image.new("RGB", (768, 512), "#eef3ff")
        draw = ImageDraw.Draw(image)
        try:
            title_font = ImageFont.truetype("arial.ttf", 34)
            body_font = ImageFont.truetype("arial.ttf", 22)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            title_font = body_font = small_font = ImageFont.load_default()

        draw.rounded_rectangle((40, 40, 728, 472), radius=28, fill="#ffffff", outline="#c7d2fe", width=3)
        draw.text((72, 80), "AI Image Preview", fill="#5b4dff", font=title_font)
        draw.text((72, 138), "Prompt:", fill="#111827", font=body_font)
        self._draw_wrapped(draw, prompt, (72, 174), body_font, "#111827", max_chars=58, line_gap=10)
        draw.rounded_rectangle((72, 372, 696, 432), radius=16, fill="#f4efff")
        draw.text((96, 392), "Pollinations.ai is responding slowly. The original URL is preserved.", fill="#5b4dff", font=small_font)
        draw.text((72, 448), reason[:110], fill="#667085", font=small_font)
        image.save(image_path, quality=92)
        return image_path

    def _draw_wrapped(self, draw, text: str, xy, font, fill: str, max_chars: int, line_gap: int):
        x, y = xy
        words = text.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > max_chars and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for line in lines[:6]:
            draw.text((x, y), line, fill=fill, font=font)
            y += 28 + line_gap
