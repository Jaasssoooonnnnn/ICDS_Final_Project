"""Recent chat history and insight counters."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque

from services.sentiment import NEGATIVE, NEUTRAL, POSITIVE


@dataclass
class ChatRecord:
    sender: str
    text: str
    timestamp: str
    sentiment: str = NEUTRAL
    kind: str = "message"


@dataclass
class ChatHistory:
    limit: int = 80
    records: Deque[ChatRecord] = field(default_factory=deque)
    sentiment_counts: Counter = field(default_factory=Counter)

    def add(self, sender: str, text: str, sentiment: str = NEUTRAL, kind: str = "message") -> ChatRecord:
        timestamp = datetime.now().strftime("%H:%M")
        record = ChatRecord(sender=sender, text=text, timestamp=timestamp, sentiment=sentiment, kind=kind)
        self.records.append(record)
        if kind == "message":
            self.sentiment_counts[sentiment] += 1
        while len(self.records) > self.limit:
            removed = self.records.popleft()
            if removed.kind == "message":
                self.sentiment_counts[removed.sentiment] -= 1
        return record

    def context(self, max_items: int = 12) -> str:
        recent = list(self.records)[-max_items:]
        if not recent:
            return "No recent chat history."
        return "\n".join(f"{r.timestamp} {r.sender}: {r.text}" for r in recent)

    def insights(self) -> dict:
        return {
            POSITIVE: max(0, self.sentiment_counts[POSITIVE]),
            NEUTRAL: max(0, self.sentiment_counts[NEUTRAL]),
            NEGATIVE: max(0, self.sentiment_counts[NEGATIVE]),
        }
