"""Environment configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is documented in AGENTS.md
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHAT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = CHAT_ROOT / "runtime"


def load_project_env() -> None:
    if load_dotenv is not None:
        load_dotenv(PROJECT_ROOT / ".env")


def env_value(name: str, default: str | None = None, required: bool = False) -> str:
    load_project_env()
    value = os.getenv(name, default)
    if isinstance(value, str):
        value = value.strip()
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or ""
