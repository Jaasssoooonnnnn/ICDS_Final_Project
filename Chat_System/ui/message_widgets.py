#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reference-style chat bubbles and media cards for the desktop client."""

from __future__ import annotations

import io
import os
import threading
import urllib.request

import customtkinter as ctk
from PIL import Image

COLORS = {
    "text": "#172033",
    "muted": "#7a849b",
    "border": "#e2e7f2",
    "incoming": "#ffffff",
    "outgoing": "#f7f4ff",
    "bot": "#f8fbff",
    "purple": "#635bff",
    "purple_soft": "#ece9ff",
    "pink": "#ec4899",
}

SENTIMENT_STYLES = {
    "Positive": ("#dcfce7", "#16834a"),
    "Neutral": ("#fff4d7", "#a96b00"),
    "Negative": ("#fee2e2", "#dc2626"),
}

NAME_COLORS = ["#4f46e5", "#0f8f8a", "#e11d8a", "#0f6ccf", "#7c3aed"]


def _name_color(name: str) -> str:
    if name == "ICDS Bot":
        return COLORS["purple"]
    return NAME_COLORS[sum(ord(ch) for ch in name) % len(NAME_COLORS)]


def _avatar_text(name: str) -> str:
    stripped = (name or "?").strip()
    if stripped == "ICDS Bot":
        return "AI"
    return stripped[:1].upper() or "?"


class Avatar(ctk.CTkLabel):
    def __init__(self, master, name, size=36, color=None):
        super().__init__(
            master,
            text=_avatar_text(name),
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=color or _name_color(name),
            text_color="#ffffff",
            font=ctk.CTkFont(size=max(11, size // 3), weight="bold"),
        )


class SentimentChip(ctk.CTkLabel):
    def __init__(self, master, sentiment):
        bg, fg = SENTIMENT_STYLES.get(sentiment, SENTIMENT_STYLES["Neutral"])
        super().__init__(
            master,
            text=sentiment,
            height=22,
            corner_radius=11,
            fg_color=bg,
            text_color=fg,
            font=ctk.CTkFont(size=10, weight="bold"),
        )


class MessageCard(ctk.CTkFrame):
    def __init__(self, master, sender, timestamp, text, sentiment, outgoing=False):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.grid_columnconfigure(0, weight=1)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=0, column=0, sticky="e" if outgoing else "w", padx=0, pady=3)

        bubble = self._bubble(row, sender, timestamp, text, sentiment, outgoing)
        avatar = Avatar(row, sender, size=38, color="#2f80ed" if outgoing else None)
        if outgoing:
            bubble.pack(side="right", padx=(0, 9))
            avatar.pack(side="right", padx=(0, 2), anchor="n")
        else:
            avatar.pack(side="left", padx=(2, 9), anchor="n")
            bubble.pack(side="left")

    def _bubble(self, master, sender, timestamp, text, sentiment, outgoing):
        bubble = ctk.CTkFrame(
            master,
            fg_color=COLORS["outgoing"] if outgoing else COLORS["incoming"],
            border_color="#cfc8ff" if outgoing else COLORS["border"],
            border_width=1,
            corner_radius=12,
        )
        bubble.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(bubble, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(9, 0))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=sender,
            text_color=COLORS["pink"] if outgoing else _name_color(sender),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=timestamp,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10),
        ).grid(row=0, column=1, sticky="e", padx=(12, 0))

        ctk.CTkLabel(
            bubble,
            text=text,
            justify="left",
            wraplength=360,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(5, 7))

        chip_row = ctk.CTkFrame(bubble, fg_color="transparent")
        chip_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 9))
        chip_row.grid_columnconfigure(0, weight=1)
        SentimentChip(chip_row, sentiment).grid(row=0, column=1, sticky="e")
        return bubble


class BotCard(ctk.CTkFrame):
    def __init__(self, master, title, timestamp, text):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", pady=3)
        Avatar(row, "ICDS Bot", size=38, color="#7c8cff").pack(side="left", padx=(2, 9), anchor="n")

        bubble = ctk.CTkFrame(
            row,
            fg_color=COLORS["bot"],
            border_color="#d7e6ff",
            border_width=1,
            corner_radius=12,
        )
        bubble.pack(side="left")

        header = ctk.CTkFrame(bubble, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(9, 2))
        ctk.CTkLabel(
            header,
            text=title,
            text_color=COLORS["purple"],
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="BOT",
            height=18,
            corner_radius=5,
            fg_color="#eef4ff",
            text_color=COLORS["purple"],
            font=ctk.CTkFont(size=9, weight="bold"),
        ).pack(side="left", padx=(8, 8))
        ctk.CTkLabel(header, text=timestamp, text_color=COLORS["muted"], font=ctk.CTkFont(size=10)).pack(side="left")

        ctk.CTkLabel(
            bubble,
            text=text,
            justify="left",
            wraplength=430,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 11))


class ImageCard(ctk.CTkFrame):
    def __init__(self, master, payload, timestamp):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.payload = payload
        self.image_label = None
        self._image_ref = None

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", pady=3)
        Avatar(row, payload.get("from") or "AI Image", size=38, color=COLORS["pink"]).pack(side="left", padx=(2, 9), anchor="n")

        bubble = ctk.CTkFrame(row, fg_color="#ffffff", corner_radius=12, border_width=1, border_color=COLORS["border"])
        bubble.pack(side="left")
        bubble.grid_columnconfigure(0, weight=1)

        prompt = payload.get("prompt") or payload.get("message") or "AI image"
        ctk.CTkLabel(
            bubble,
            text=f"AI Picture · {timestamp}",
            text_color="#e11d8a",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            bubble,
            text=prompt,
            justify="left",
            wraplength=450,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        self.image_label = ctk.CTkLabel(
            bubble,
            text="Loading preview...",
            width=450,
            height=240,
            corner_radius=10,
            fg_color="#f3f5fb",
            text_color=COLORS["muted"],
        )
        self.image_label.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        self._load_preview()

    def _load_preview(self):
        source = (
            self.payload.get("local_path")
            or self.payload.get("path")
            or self.payload.get("file_path")
            or self.payload.get("url")
            or self.payload.get("image_url")
        )
        if not source:
            self.image_label.configure(text="No preview path or URL returned.")
            return
        if os.path.exists(source):
            self._set_image_from_path(source)
            return
        if source.startswith(("http://", "https://")):
            threading.Thread(target=self._download_preview, args=(source,), daemon=True).start()
            return
        self.image_label.configure(text=source)

    def _set_image_from_path(self, path):
        try:
            image = Image.open(path)
            self._set_image(image)
        except OSError as exc:
            self.image_label.configure(text=f"Preview failed: {exc}")

    def _download_preview(self, url):
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                data = response.read()
            image = Image.open(io.BytesIO(data))
            image.load()
        except OSError as exc:
            self.after(0, lambda: self.image_label.configure(text=f"Preview failed: {exc}"))
            return
        self.after(0, lambda: self._set_image(image))

    def _set_image(self, image):
        image.thumbnail((450, 250))
        self._image_ref = ctk.CTkImage(light_image=image.copy(), dark_image=image.copy(), size=image.size)
        self.image_label.configure(image=self._image_ref, text="")
