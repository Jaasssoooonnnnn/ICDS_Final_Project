#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Compact chat cards styled to match the reference desktop mockups."""

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
    "outgoing": "#f5f2ff",
    "bot": "#f8fbff",
    "purple": "#635bff",
    "purple_soft": "#ece9ff",
}

SENTIMENT_STYLES = {
    "Positive": ("#dcfce7", "#16834a"),
    "Neutral": ("#fff4d7", "#b57900"),
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
    def __init__(self, master, name, size=34, color=None):
        super().__init__(
            master,
            text=_avatar_text(name),
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=color or _name_color(name),
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
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
            padx=9,
        )


class MessageCard(ctk.CTkFrame):
    def __init__(self, master, sender, timestamp, text, sentiment, outgoing=False):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        bubble_color = COLORS["outgoing"] if outgoing else COLORS["incoming"]
        bubble_border = "#cfc8ff" if outgoing else COLORS["border"]
        avatar_col = 2 if outgoing else 0
        bubble_col = 1
        sticky = "e" if outgoing else "w"

        if outgoing:
            Avatar(self, sender, size=34, color="#2f80ed").grid(row=0, column=avatar_col, padx=(8, 4), pady=4, sticky="n")
        else:
            Avatar(self, sender, size=34).grid(row=0, column=avatar_col, padx=(4, 8), pady=4, sticky="n")

        bubble = ctk.CTkFrame(
            self,
            fg_color=bubble_color,
            border_color=bubble_border,
            border_width=1,
            corner_radius=12,
        )
        bubble.grid(row=0, column=bubble_col, sticky=sticky, pady=4)
        bubble.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(bubble, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(9, 0))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=sender,
            text_color=_name_color(sender),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=timestamp,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10),
        ).grid(row=0, column=1, sticky="e", padx=(14, 0))

        ctk.CTkLabel(
            bubble,
            text=text,
            justify="left",
            wraplength=360,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 6))

        chip_row = ctk.CTkFrame(bubble, fg_color="transparent")
        chip_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 9))
        chip_row.grid_columnconfigure(0, weight=1)
        SentimentChip(chip_row, sentiment).grid(row=0, column=1, sticky="e")


class BotCard(ctk.CTkFrame):
    def __init__(self, master, title, timestamp, text):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.grid_columnconfigure(1, weight=1)
        Avatar(self, "ICDS Bot", size=36, color="#7c8cff").grid(row=0, column=0, padx=(4, 8), pady=5, sticky="n")

        bubble = ctk.CTkFrame(
            self,
            fg_color=COLORS["bot"],
            border_color="#d7e6ff",
            border_width=1,
            corner_radius=12,
        )
        bubble.grid(row=0, column=1, sticky="w", pady=5)
        bubble.grid_columnconfigure(0, weight=1)

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
            wraplength=410,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 11))


class ImageCard(ctk.CTkFrame):
    def __init__(self, master, payload, timestamp):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.payload = payload
        self.image_label = None
        self._image_ref = None
        self.grid_columnconfigure(1, weight=1)

        Avatar(self, payload.get("from") or "AI Image", size=36, color="#ec4899").grid(
            row=0, column=0, padx=(4, 8), pady=5, sticky="n"
        )
        bubble = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12, border_width=1, border_color=COLORS["border"])
        bubble.grid(row=0, column=1, sticky="w", pady=5)
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
            wraplength=410,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        self.image_label = ctk.CTkLabel(
            bubble,
            text="Loading preview...",
            width=420,
            height=230,
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
        image.thumbnail((420, 240))
        self._image_ref = ctk.CTkImage(light_image=image.copy(), dark_image=image.copy(), size=image.size)
        self.image_label.configure(image=self._image_ref, text="")
