#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os
import threading
import urllib.request

import customtkinter as ctk
from PIL import Image


SENTIMENT_STYLES = {
    "Positive": ("#e8f7ef", "#16834a"),
    "Neutral": ("#eef2ff", "#4b5cb8"),
    "Negative": ("#fdecec", "#c24141"),
}


class MessageCard(ctk.CTkFrame):
    def __init__(self, master, sender, timestamp, text, sentiment, outgoing=False):
        bg = "#eef2ff" if outgoing else "#ffffff"
        super().__init__(master, fg_color=bg, corner_radius=16, border_width=1, border_color="#dde3f0")
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=sender,
            text_color="#20233a",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text=timestamp, text_color="#8a93aa", font=ctk.CTkFont(size=11)).grid(row=0, column=1)

        ctk.CTkLabel(
            self,
            text=text,
            justify="left",
            wraplength=560,
            text_color="#31384f",
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

        chip_bg, chip_text = SENTIMENT_STYLES.get(sentiment, SENTIMENT_STYLES["Neutral"])
        ctk.CTkLabel(
            self,
            text=sentiment,
            height=24,
            corner_radius=12,
            fg_color=chip_bg,
            text_color=chip_text,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))


class BotCard(ctk.CTkFrame):
    def __init__(self, master, title, timestamp, text):
        super().__init__(master, fg_color="#f4f0ff", corner_radius=16, border_width=1, border_color="#d9ceff")
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            self,
            text="AI",
            width=40,
            height=40,
            corner_radius=20,
            fg_color="#635bff",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, rowspan=2, padx=14, pady=14, sticky="n")
        ctk.CTkLabel(
            self,
            text=f"{title} · {timestamp}",
            text_color="#4f46a5",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=(0, 14), pady=(14, 2))
        ctk.CTkLabel(
            self,
            text=text,
            justify="left",
            wraplength=560,
            text_color="#2f2d4f",
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=1, sticky="w", padx=(0, 14), pady=(0, 14))


class ImageCard(ctk.CTkFrame):
    def __init__(self, master, payload, timestamp):
        super().__init__(master, fg_color="#ffffff", corner_radius=16, border_width=1, border_color="#dde3f0")
        self.payload = payload
        self.image_label = None
        self._image_ref = None
        self.grid_columnconfigure(0, weight=1)

        prompt = payload.get("prompt") or payload.get("message") or "AI image"
        ctk.CTkLabel(
            self,
            text=f"AI Picture · {timestamp}",
            text_color="#635bff",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 2))
        ctk.CTkLabel(
            self,
            text=prompt,
            justify="left",
            wraplength=560,
            text_color="#31384f",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

        self.image_label = ctk.CTkLabel(
            self,
            text="Loading preview...",
            height=210,
            corner_radius=14,
            fg_color="#f3f5fb",
            text_color="#67708a",
        )
        self.image_label.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
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
        image.thumbnail((560, 260))
        self._image_ref = ctk.CTkImage(light_image=image.copy(), dark_image=image.copy(), size=image.size)
        self.image_label.configure(image=self._image_ref, text="")
