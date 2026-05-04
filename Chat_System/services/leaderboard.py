"""Persistent Whack-a-Mole leaderboard."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from services.config import RUNTIME_DIR


class Leaderboard:
    def __init__(self, path: Path | None = None):
        self.path = Path(path or (RUNTIME_DIR / "leaderboard.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.entries = self._load()

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise RuntimeError(f"Invalid leaderboard file: {self.path}")
        return data

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self.entries, handle, indent=2)

    def submit(self, player: str, score: int) -> list[dict]:
        if not player:
            raise ValueError("Player name is required")
        score = int(score)
        if score < 0:
            raise ValueError("Score cannot be negative")
        self.entries.append(
            {
                "player": player,
                "score": score,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        self.entries = sorted(self.entries, key=lambda entry: entry["score"], reverse=True)[:25]
        self._save()
        return self.top()

    def top(self, limit: int = 10) -> list[dict]:
        ranked = []
        for index, entry in enumerate(self.entries[:limit], start=1):
            item = dict(entry)
            item["rank"] = index
            ranked.append(item)
        return ranked
