#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reference-style chat bubbles and media cards for the desktop client."""

from __future__ import annotations

import io
import os
import threading
import tkinter as tk
import urllib.request

import customtkinter as ctk
from PIL import Image

COLORS = {
    "text": "#101828",
    "muted": "#667085",
    "border": "#dde5f0",
    "incoming": "#f6f7fb",
    "outgoing": "#edf3ff",
    "bot": "#f4efff",
    "purple": "#5b4dff",
    "purple_soft": "#eee8ff",
    "pink": "#5b4dff",
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


def _text_height(text: str, wrap_chars: int) -> int:
    lines = 0
    for part in (text or " ").splitlines() or [" "]:
        lines += max(1, (len(part) // wrap_chars) + 1)
    return min(max(lines, 1), 10)


class SelectableText(tk.Text):
    def __init__(self, master, text, bg, fg, wrap_chars=64, font_size=13, width=64):
        super().__init__(
            master,
            height=_text_height(text, wrap_chars),
            width=width,
            wrap="word",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            bg=bg,
            fg=fg,
            insertbackground=fg,
            selectbackground="#c7d2fe",
            selectforeground="#111827",
            font=("Helvetica", font_size),
            cursor="xterm",
            padx=0,
            pady=0,
        )
        self.insert("1.0", text or "")
        self.configure(state="disabled")
        self.bind("<Control-a>", self._select_all)
        self.bind("<Control-A>", self._select_all)

    def _select_all(self, _event=None):
        self.tag_add("sel", "1.0", "end-1c")
        return "break"


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
        emoji = {"Positive": "😊", "Neutral": "😐", "Negative": "😡"}.get(sentiment, "")
        super().__init__(
            master,
            text=f"{sentiment} {emoji}".strip(),
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
        row.grid(row=0, column=0, sticky="e" if outgoing else "w", padx=0, pady=4)

        bubble = self._bubble(row, sender, timestamp, text, sentiment, outgoing)
        if outgoing:
            bubble.pack(side="right", padx=(0, 4))
        else:
            avatar = Avatar(row, sender, size=38)
            avatar.pack(side="left", padx=(2, 9), anchor="n")
            bubble.pack(side="left")

    def _bubble(self, master, sender, timestamp, text, sentiment, outgoing):
        bubble = ctk.CTkFrame(
            master,
            fg_color=COLORS["outgoing"] if outgoing else COLORS["incoming"],
            border_color="#dce6ff" if outgoing else "#edf0f6",
            border_width=1,
            corner_radius=10,
        )
        bubble.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(bubble, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(7, 0))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=sender,
            text_color=COLORS["pink"] if outgoing else "#315bff",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=timestamp,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=1, sticky="e", padx=(12, 0))

        SelectableText(
            bubble,
            text=text,
            bg=COLORS["outgoing"] if outgoing else COLORS["incoming"],
            fg=COLORS["text"],
            wrap_chars=66 if outgoing else 64,
            width=66 if outgoing else 64,
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(5, 7))

        chip_row = ctk.CTkFrame(bubble, fg_color="transparent")
        chip_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 7))
        chip_row.grid_columnconfigure(0, weight=1)
        SentimentChip(chip_row, sentiment).grid(row=0, column=1, sticky="e")
        return bubble


class BotCard(ctk.CTkFrame):
    def __init__(self, master, title, timestamp, text):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", pady=4)
        Avatar(row, "ICDS Bot", size=38, color="#7c8cff").pack(side="left", padx=(2, 9), anchor="n")

        bubble = ctk.CTkFrame(
            row,
            fg_color=COLORS["bot"],
            border_color="#d7e6ff",
            border_width=1,
            corner_radius=10,
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

        SelectableText(
            bubble,
            text=text,
            bg=COLORS["bot"],
            fg=COLORS["text"],
            wrap_chars=66,
            width=66,
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

        bubble = ctk.CTkFrame(row, fg_color="#f6f7fb", corner_radius=10, border_width=1, border_color=COLORS["border"])
        bubble.pack(side="left")
        bubble.grid_columnconfigure(0, weight=1)

        prompt = payload.get("prompt") or payload.get("message") or "AI image"
        ctk.CTkLabel(
            bubble,
            text=f"AI Picture · {timestamp}",
            text_color="#e11d8a",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 2))
        SelectableText(
            bubble,
            text=prompt,
            bg="#f6f7fb",
            fg=COLORS["text"],
            wrap_chars=54,
            font_size=12,
            width=54,
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        self.image_label = ctk.CTkLabel(
            bubble,
            text="Loading preview...",
            width=420,
            height=190,
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
        image.thumbnail((420, 190))
        self._image_ref = ctk.CTkImage(light_image=image.copy(), dark_image=image.copy(), size=image.size)
        self.image_label.configure(image=self._image_ref, text="")
