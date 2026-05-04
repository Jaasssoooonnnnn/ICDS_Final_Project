#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reference-aligned CustomTkinter desktop client."""

from __future__ import annotations

import ast
import json
import select
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from chat_utils import CHAT_WAIT, S_LOGGEDIN, S_OFFLINE

try:
    from textblob import TextBlob
except ImportError:  # pragma: no cover - dependency is documented for runtime.
    TextBlob = None

try:
    from ui.game_window import WhackAMoleWindow
    from ui.message_widgets import BotCard, ImageCard, MessageCard
except ImportError:
    from Chat_System.ui.game_window import WhackAMoleWindow
    from Chat_System.ui.message_widgets import BotCard, ImageCard, MessageCard


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLORS = {
    "app_bg": "#ffffff",
    "sidebar": "#f8faff",
    "center": "#ffffff",
    "chat_bg": "#fbfcff",
    "right": "#ffffff",
    "border": "#e3e8f4",
    "soft": "#f4f6fb",
    "soft2": "#f8f9fd",
    "text": "#172033",
    "muted": "#71809c",
    "purple": "#635bff",
    "purple2": "#7b61ff",
    "green": "#22c55e",
    "blue": "#2f80ed",
    "pink": "#ec4899",
    "teal": "#14b8a6",
    "orange": "#f59e0b",
}

FONT = "Helvetica"
SPACE = 18

NAV_ITEMS = [
    ("Chats", "chat"),
    ("Bot", "bot"),
    ("Game", "game"),
    ("AI Image", "image"),
    ("Summary", "summary"),
]

ACTION_META = [
    ("Start Game", "Play a quick team game", "Game", "#635bff"),
    ("/summary", "Get summary of this chat", "Summary", "#2f80ed"),
    ("/keywords", "Extract important keywords", "Keywords", "#14b8a6"),
    ("/aipic", "Generate AI image from prompt", "AI Pic", "#ec4899"),
]


class GUI:
    def __init__(self, send, recv, sm, s, on_close=None):
        self.Window = ctk.CTk()
        self.Window.withdraw()

        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.on_close = on_close

        self.closed = False
        self.name = ""
        self.last_summary = "No summary yet."
        self.last_keywords = []
        self.sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        self.leaderboard_rows = []
        self.online_users = []
        self.nav_buttons = {}

        self.chat_scroll = None
        self.entryMsg = None
        self.status_pill = None
        self.member_count_label = None
        self.online_list_frame = None
        self.insight_labels = {}
        self.summary_label = None
        self.keyword_label = None
        self.leaderboard_frame = None

    def run(self):
        self.login()

    def login(self):
        self.login_window = ctk.CTkToplevel(self.Window)
        self.login_window.title("ICDS Chat Login")
        self.login_window.geometry("460x380")
        self.login_window.resizable(False, False)
        self.login_window.configure(fg_color="#f5f7fb")
        self.login_window.protocol("WM_DELETE_WINDOW", self.close)
        self.login_window.grab_set()

        card = ctk.CTkFrame(self.login_window, fg_color="#ffffff", corner_radius=16, border_width=1, border_color=COLORS["border"])
        card.pack(fill="both", expand=True, padx=34, pady=34)

        ctk.CTkLabel(
            card,
            text="ICDS Chat",
            font=ctk.CTkFont(family=FONT, size=30, weight="bold"),
            text_color=COLORS["text"],
        ).pack(pady=(38, 6))
        ctk.CTkLabel(
            card,
            text="Sign in to your project workspace",
            font=ctk.CTkFont(family=FONT, size=14),
            text_color=COLORS["muted"],
        ).pack(pady=(0, 26))

        self.entryName = ctk.CTkEntry(
            card,
            height=44,
            corner_radius=12,
            placeholder_text="Display name",
            border_color="#d9def0",
            fg_color="#f8f9fd",
            text_color=COLORS["text"],
        )
        self.entryName.pack(fill="x", padx=34)
        self.entryName.focus()
        self.entryName.bind("<Return>", lambda event: self.goAhead(self.entryName.get()))

        self.statusLabel = ctk.CTkLabel(card, text="", text_color="#d64545")
        self.statusLabel.pack(pady=(10, 4))

        ctk.CTkButton(
            card,
            height=44,
            corner_radius=12,
            text="Continue",
            fg_color=COLORS["purple"],
            hover_color="#5148e5",
            command=lambda: self.goAhead(self.entryName.get()),
        ).pack(fill="x", padx=34, pady=(12, 0))

        self.Window.mainloop()

    def goAhead(self, name):
        name = name.strip()
        if not name:
            self.statusLabel.configure(text="Please enter a name.")
            return

        self._safe_send({"action": "login", "name": name})
        try:
            response = json.loads(self.recv())
        except (json.JSONDecodeError, OSError) as exc:
            self.statusLabel.configure(text=f"Login failed: {exc}")
            return

        if response.get("status") == "ok":
            self.login_window.destroy()
            self.name = name
            self.sm.set_state(S_LOGGEDIN)
            self.sm.set_myname(name)
            self.layout(name)
            self._set_status("Connected", COLORS["green"])
            self._request_online_users()
            self._request_leaderboard()
            self.Window.after(int(CHAT_WAIT * 1000), self.proc)
        elif response.get("status") == "duplicate":
            self.statusLabel.configure(text="Duplicate username, try another.")
        else:
            self.statusLabel.configure(text=response.get("error") or "Login failed, try again.")

    def layout(self, name):
        self.Window.deiconify()
        self.Window.title("ICDS Chat")
        self.Window.geometry("1220x780")
        self.Window.minsize(1060, 680)
        self.Window.configure(fg_color=COLORS["app_bg"])
        self.Window.protocol("WM_DELETE_WINDOW", self.close)

        self.Window.grid_columnconfigure(0, minsize=250, weight=0)
        self.Window.grid_columnconfigure(1, weight=1)
        self.Window.grid_columnconfigure(2, minsize=292, weight=0)
        self.Window.grid_rowconfigure(0, weight=1)

        self._build_sidebar(name)
        self._build_chat_column()
        self._build_right_panel()
        self.add_bot_card(
            "Welcome to ICDS Chat. Use @bot, /summary, /keywords, or /aipic: your prompt when you are ready.",
            title="ICDS Bot",
        )

    def _build_sidebar(self, name):
        sidebar = ctk.CTkFrame(self.Window, fg_color=COLORS["sidebar"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(5, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 16))
        ctk.CTkLabel(
            brand,
            text="...",
            width=32,
            height=30,
            corner_radius=9,
            fg_color=COLORS["purple"],
            text_color="#ffffff",
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            brand,
            text="ICDS Chat",
            font=ctk.CTkFont(family=FONT, size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=(12, 0))

        user = ctk.CTkFrame(sidebar, fg_color="transparent")
        user.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self._avatar(user, name, size=48, color="#2f80ed").pack(side="left")
        info = ctk.CTkFrame(user, fg_color="transparent")
        info.pack(side="left", padx=(12, 0), fill="x", expand=True)
        ctk.CTkLabel(info, text=name, anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x")
        ctk.CTkLabel(info, text="Online", anchor="w", text_color=COLORS["muted"], font=ctk.CTkFont(size=11)).pack(fill="x")
        ctk.CTkLabel(user, text="v", text_color=COLORS["muted"], font=ctk.CTkFont(size=13)).pack(side="right")

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))
        for index, (label, key) in enumerate(NAV_ITEMS):
            selected = index == 0
            btn = ctk.CTkButton(
                nav,
                text=("  " + label),
                anchor="w",
                height=44,
                corner_radius=10,
                fg_color=COLORS["purple"] if selected else "transparent",
                hover_color="#ebe9ff",
                text_color="#ffffff" if selected else "#26324d",
                font=ctk.CTkFont(size=13, weight="bold" if selected else "normal"),
                command=self._nav_action(key),
            )
            btn.pack(fill="x", pady=4)
            self.nav_buttons[key] = btn

        ctk.CTkFrame(sidebar, height=1, fg_color=COLORS["border"]).grid(row=3, column=0, sticky="ew", padx=20, pady=(2, 14))

        users_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        users_header.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 8))
        ctk.CTkLabel(users_header, text="ONLINE USERS", text_color=COLORS["muted"], font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(users_header, text="●", text_color=COLORS["green"], font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 7))

        self.online_list_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", scrollbar_button_color="#d7deec")
        self.online_list_frame.grid(row=5, column=0, sticky="nsew", padx=18, pady=(0, 16))
        self._render_online_users()

        ctk.CTkButton(
            sidebar,
            text="Refresh Users",
            height=36,
            corner_radius=10,
            fg_color="#ffffff",
            text_color="#26324d",
            border_width=1,
            border_color=COLORS["border"],
            hover_color="#edf0fb",
            command=self._request_online_users,
        ).grid(row=6, column=0, sticky="ew", padx=18, pady=(0, 16))

    def _build_chat_column(self):
        center = ctk.CTkFrame(self.Window, fg_color=COLORS["center"], corner_radius=0)
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(center, fg_color="#ffffff", corner_radius=0, height=76)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header,
            text="grp",
            width=44,
            height=44,
            corner_radius=22,
            fg_color=COLORS["purple"],
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, rowspan=2, padx=(22, 12), pady=16)
        ctk.CTkLabel(
            header,
            text="General Group Chat",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1, sticky="sw", pady=(17, 0))
        self.member_count_label = ctk.CTkLabel(
            header,
            text="●  connected room",
            text_color=COLORS["green"],
            font=ctk.CTkFont(size=12),
        )
        self.member_count_label.grid(row=1, column=1, sticky="nw", pady=(0, 15))
        self.status_pill = ctk.CTkLabel(
            header,
            text="Connecting",
            height=30,
            corner_radius=9,
            fg_color=COLORS["soft2"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.status_pill.grid(row=0, column=2, rowspan=2, padx=(8, 18), pady=22)

        ctk.CTkFrame(center, height=1, fg_color=COLORS["border"]).grid(row=0, column=0, sticky="sew")

        self.chat_scroll = ctk.CTkScrollableFrame(center, fg_color=COLORS["chat_bg"], scrollbar_button_color="#d7deec")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")
        self.chat_scroll.grid_columnconfigure(0, weight=1)
        self._date_divider()

        composer = ctk.CTkFrame(center, fg_color="#ffffff", corner_radius=0)
        composer.grid(row=2, column=0, sticky="ew")
        composer.grid_columnconfigure(1, weight=1)
        inner = ctk.CTkFrame(composer, fg_color="#ffffff", corner_radius=13, border_width=1, border_color=COLORS["border"])
        inner.grid(row=0, column=0, columnspan=3, sticky="ew", padx=22, pady=14)
        inner.grid_columnconfigure(2, weight=1)
        ctk.CTkButton(inner, text=":)", width=38, height=38, corner_radius=10, fg_color="transparent", hover_color="#edf0fb", text_color="#52617d").grid(row=0, column=0, padx=(8, 0), pady=8)
        ctk.CTkButton(inner, text="+", width=38, height=38, corner_radius=10, fg_color="transparent", hover_color="#edf0fb", text_color="#52617d").grid(row=0, column=1, padx=(0, 4), pady=8)
        self.entryMsg = ctk.CTkEntry(
            inner,
            height=42,
            corner_radius=9,
            border_width=0,
            fg_color="#ffffff",
            placeholder_text="Type a message...",
            text_color=COLORS["text"],
        )
        self.entryMsg.grid(row=0, column=2, sticky="ew", padx=(0, 8), pady=8)
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
        ctk.CTkButton(
            inner,
            text="Send",
            width=96,
            height=42,
            corner_radius=9,
            fg_color=COLORS["purple"],
            hover_color="#5148e5",
            command=lambda: self.sendButton(self.entryMsg.get()),
        ).grid(row=0, column=3, padx=(0, 8), pady=8)

    def _build_right_panel(self):
        panel = ctk.CTkScrollableFrame(self.Window, fg_color=COLORS["right"], corner_radius=0, scrollbar_button_color="#d7deec")
        panel.grid(row=0, column=2, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        quick = self._panel_card(panel, "Quick Actions", "!")
        for title, subtitle, action, color in ACTION_META:
            self._action_row(quick, title, subtitle, action, color).pack(fill="x", padx=10, pady=6)

        room = self._panel_card(panel, "Room Info", "i")
        self._info_line(room, "Room Name", "General Group Chat")
        self._info_line(room, "Created By", self.name or "You")
        self._info_line(room, "Members", str(max(len(self.online_users), 1)))

        insights = self._panel_card(panel, "Insights", "~")
        self.summary_label = ctk.CTkLabel(
            insights,
            text=self.last_summary,
            wraplength=218,
            justify="left",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
        )
        self.summary_label.pack(fill="x", padx=12, pady=(4, 10))
        self.keyword_label = ctk.CTkLabel(
            insights,
            text="Tags will appear here.",
            wraplength=218,
            justify="left",
            text_color=COLORS["purple"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.keyword_label.pack(fill="x", padx=12, pady=(0, 12))

        sentiment = self._panel_card(panel, "Sentiment Overview", "*")
        grid = ctk.CTkFrame(sentiment, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 10))
        grid.grid_columnconfigure((0, 1, 2), weight=1)
        for col, label in enumerate(("Positive", "Neutral", "Negative")):
            box = ctk.CTkFrame(grid, fg_color=COLORS["soft2"], corner_radius=10)
            box.grid(row=0, column=col, sticky="ew", padx=4)
            self.insight_labels[label] = ctk.CTkLabel(
                box,
                text="0",
                font=ctk.CTkFont(size=21, weight="bold"),
                text_color=COLORS["text"],
            )
            self.insight_labels[label].pack(pady=(9, 0))
            ctk.CTkLabel(box, text=label[:3], font=ctk.CTkFont(size=9), text_color=COLORS["muted"]).pack(pady=(0, 9))

        leaderboard = self._panel_card(panel, "Leaderboard", "cup")
        self.leaderboard_frame = ctk.CTkFrame(leaderboard, fg_color="transparent")
        self.leaderboard_frame.pack(fill="x", padx=8, pady=(0, 8))
        self._render_leaderboard()

    def _panel_card(self, master, title, icon):
        card = ctk.CTkFrame(master, fg_color="#ffffff", corner_radius=13, border_width=1, border_color=COLORS["border"])
        card.grid(sticky="ew", padx=16, pady=(18, 0))
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=icon, width=24, height=24, corner_radius=12, fg_color=COLORS["soft2"], text_color=COLORS["purple"], font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text=title, text_color=COLORS["text"], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(9, 0))
        return card

    def _action_row(self, master, title, subtitle, action, color):
        row = ctk.CTkFrame(master, fg_color="#ffffff", corner_radius=10, border_width=1, border_color=COLORS["border"])
        icon = ctk.CTkLabel(row, text=action[:2], width=42, height=42, corner_radius=11, fg_color=color, text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"))
        icon.pack(side="left", padx=10, pady=10)
        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(side="left", fill="both", expand=True, pady=8)
        ctk.CTkLabel(text, text=title, anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=12, weight="bold")).pack(fill="x")
        ctk.CTkLabel(text, text=subtitle, anchor="w", text_color=COLORS["muted"], font=ctk.CTkFont(size=10)).pack(fill="x")
        row.bind("<Button-1>", lambda _event: self._run_quick_action(action))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda _event: self._run_quick_action(action))
        return row

    def _info_line(self, master, label, value):
        ctk.CTkLabel(master, text=label, anchor="w", text_color=COLORS["muted"], font=ctk.CTkFont(size=10)).pack(fill="x", padx=12, pady=(0, 1))
        ctk.CTkLabel(master, text=value, anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=12)).pack(fill="x", padx=12, pady=(0, 9))

    def _run_quick_action(self, action):
        if action == "Game":
            self.open_game()
        elif action == "Summary":
            self.request_summary()
        elif action == "Keywords":
            self.request_keywords()
        else:
            self.prompt_image()

    def _nav_action(self, key):
        return lambda: self._run_quick_action("Game" if key == "game" else "Summary" if key == "summary" else "AI Pic" if key == "image" else "Bot" if key == "bot" else "Chats")

    def _date_divider(self):
        row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(14, 10))
        row.grid_columnconfigure((0, 2), weight=1)
        ctk.CTkFrame(row, height=1, fg_color=COLORS["border"]).grid(row=0, column=0, sticky="ew", padx=(80, 12))
        ctk.CTkLabel(row, text="Today", height=24, corner_radius=12, fg_color=COLORS["soft"], text_color="#525b70", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=1)
        ctk.CTkFrame(row, height=1, fg_color=COLORS["border"]).grid(row=0, column=2, sticky="ew", padx=(12, 80))

    def sendButton(self, msg):
        msg = msg.strip()
        if not msg:
            return
        self.entryMsg.delete(0, "end")

        lower = msg.lower()
        if lower == "/summary":
            self.request_summary()
            return
        if lower == "/keywords":
            self.request_keywords()
            return
        if lower.startswith("/aipic:"):
            self.request_image(msg.split(":", 1)[1].strip())
            return
        if lower.startswith("/bot "):
            self._send_bot_request(msg[5:].strip(), direct=True)
            return
        if lower.startswith("@bot"):
            self.add_message(self.name, msg, outgoing=True)
            self._safe_send(
                {
                    "action": "exchange",
                    "from": f"[{self.name}]",
                    "message": msg,
                    "sender": self.name,
                    "sentiment": "Neutral",
                    "timestamp": self._timestamp(),
                }
            )
            return

        sentiment = self._label_sentiment(msg)
        self.add_message(self.name, msg, sentiment=sentiment, outgoing=True)
        self._safe_send(
            {
                "action": "exchange",
                "from": f"[{self.name}]",
                "message": msg,
                "sender": self.name,
                "sentiment": sentiment,
                "timestamp": self._timestamp(),
            }
        )

    def proc(self):
        if self.closed:
            return
        try:
            read, _write, _error = select.select([self.socket], [], [], 0)
        except (OSError, ValueError):
            self._set_status("Disconnected", "#dc2626")
            self.close()
            return

        while self.socket in read:
            try:
                raw_msg = self.recv()
            except OSError as exc:
                self.add_bot_card(f"Socket receive failed: {exc}", title="Connection Error")
                self._set_status("Disconnected", "#dc2626")
                break
            if not raw_msg:
                self._set_status("Disconnected", "#dc2626")
                break
            self._handle_payload(raw_msg)
            read, _write, _error = select.select([self.socket], [], [], 0)

        if self.sm.get_state() == S_OFFLINE:
            self.close()
            return
        self.Window.after(int(CHAT_WAIT * 1000), self.proc)

    def _handle_payload(self, raw_msg):
        try:
            payload = json.loads(raw_msg)
        except json.JSONDecodeError:
            self.add_bot_card(raw_msg, title="Server")
            return

        action = payload.get("action")
        if action == "exchange":
            sender = payload.get("sender") or payload.get("from") or "Peer"
            sender = str(sender).strip("[]") or "Peer"
            text = payload.get("message", "")
            sentiment = payload.get("sentiment") or self._label_sentiment(text)
            self.add_message(sender, text, sentiment=sentiment, outgoing=sender == self.name)
        elif action in {"bot_response", "summary_response", "keywords_response"}:
            self._handle_ai_response(action, payload)
        elif action == "image_response":
            self.add_image_card(payload)
        elif action in {"leaderboard", "leaderboard_list"}:
            self._update_leaderboard(payload)
        elif action == "list":
            self._update_online_users(payload.get("users") or payload.get("results") or "")
        elif action == "connect":
            self.add_bot_card(f"{payload.get('from', 'A peer')} joined the chat.", title="Room")
        elif action == "disconnect":
            self.add_bot_card("A peer disconnected.", title="Room")
        elif action == "error":
            self.add_bot_card(payload.get("message") or payload.get("error") or "Unknown server error.", title="Error")
        else:
            self.add_bot_card(json.dumps(payload, indent=2), title="Server")

    def _handle_ai_response(self, action, payload):
        text = payload.get("message") or payload.get("response") or payload.get("summary") or payload.get("keywords") or ""
        if isinstance(text, list):
            text = ", ".join(str(item) for item in text)
        title = "ICDS Bot"
        if action == "summary_response":
            title = "Summary"
            self.last_summary = text or "No summary returned."
            self.summary_label.configure(text=self.last_summary)
        elif action == "keywords_response":
            title = "Keywords"
            keywords = payload.get("keywords", text)
            if isinstance(keywords, str):
                self.last_keywords = [part.strip() for part in keywords.replace("\n", ",").split(",") if part.strip()]
            else:
                self.last_keywords = [str(part) for part in keywords]
            self.keyword_label.configure(text=", ".join(f"#{tag.lstrip('#')}" for tag in self.last_keywords) or "No tags returned.")
            text = self.keyword_label.cget("text")
        self.add_bot_card(text or "No response text returned.", title=title)

    def add_message(self, sender, text, sentiment=None, outgoing=False):
        sentiment = sentiment or self._label_sentiment(text)
        self.sentiment_counts[sentiment] = self.sentiment_counts.get(sentiment, 0) + 1
        self._render_sentiments()
        MessageCard(
            self.chat_scroll,
            sender=sender,
            timestamp=self._timestamp(),
            text=text,
            sentiment=sentiment,
            outgoing=outgoing,
        ).pack(fill="x", padx=20, pady=2)
        self._scroll_to_bottom()

    def add_bot_card(self, text, title="ICDS Bot"):
        BotCard(self.chat_scroll, title=title, timestamp=self._timestamp(), text=text).pack(fill="x", padx=20, pady=3)
        self._scroll_to_bottom()

    def add_image_card(self, payload):
        ImageCard(self.chat_scroll, payload=payload, timestamp=self._timestamp()).pack(fill="x", padx=20, pady=3)
        self._scroll_to_bottom()

    def request_summary(self):
        self.add_bot_card("Requesting a concise summary from recent chat history...", title="Summary")
        self._safe_send({"action": "summary_request", "sender": self.name})

    def request_keywords(self):
        self.add_bot_card("Requesting keyword tags from recent chat history...", title="Keywords")
        self._safe_send({"action": "keywords_request", "sender": self.name})

    def prompt_image(self):
        dialog = ctk.CTkInputDialog(text="Describe the image for Pollinations.ai", title="AI Picture")
        prompt = (dialog.get_input() or "").strip()
        if prompt:
            self.request_image(prompt)

    def request_image(self, prompt):
        if not prompt:
            self.add_bot_card("Please include a prompt after /aipic:.", title="AI Picture")
            return
        self.add_bot_card(f"Generating image: {prompt}", title="AI Picture")
        self._safe_send({"action": "image_request", "sender": self.name, "prompt": prompt})

    def open_game(self):
        WhackAMoleWindow(self.Window, player_name=self.name, submit_callback=self.submit_score)

    def submit_score(self, score):
        self.add_bot_card(f"Submitting Whack-a-Mole score: {score}", title="Game")
        self._safe_send({"action": "score_submit", "player": self.name, "score": int(score), "timestamp": self._timestamp()})
        self._request_leaderboard()

    def _send_bot_request(self, text, direct=False):
        if not text:
            self.add_bot_card("Ask ICDS Bot a question after @bot or /bot.", title="ICDS Bot")
            return
        if direct:
            self.add_message(self.name, f"/bot {text}", outgoing=True)
        self._safe_send({"action": "bot_request", "sender": self.name, "message": text, "scope": "direct" if direct else "group"})

    def _request_online_users(self):
        self._safe_send({"action": "list"})

    def _request_leaderboard(self):
        self._safe_send({"action": "leaderboard", "sender": self.name})

    def _safe_send(self, payload):
        try:
            self.send(json.dumps(payload))
        except OSError as exc:
            self._set_status("Send failed", "#dc2626")
            self.add_bot_card(f"Send failed: {exc}", title="Connection Error")

    def _label_sentiment(self, text):
        if TextBlob is None or not text.strip():
            return "Neutral"
        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.12:
            return "Positive"
        if polarity < -0.12:
            return "Negative"
        return "Neutral"

    def _render_sentiments(self):
        for label, widget in self.insight_labels.items():
            widget.configure(text=str(self.sentiment_counts.get(label, 0)))

    def _update_online_users(self, data):
        users = []
        if isinstance(data, list):
            users = [str(item) for item in data]
        elif isinstance(data, dict):
            users = [str(key) for key in data.keys()]
        elif isinstance(data, str):
            parsed = self._extract_users_from_legacy_list(data)
            users = parsed if parsed else [line.strip() for line in data.splitlines() if line.strip()]
        self.online_users = users
        if self.member_count_label is not None:
            count = len(users) if users else 1
            self.member_count_label.configure(text=f"●  {count} members online")
        self._render_online_users()

    def _render_online_users(self):
        if self.online_list_frame is None:
            return
        for child in self.online_list_frame.winfo_children():
            child.destroy()
        users = self.online_users or [self.name or "You"]
        for user in users[:10]:
            row = ctk.CTkFrame(self.online_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            self._avatar(row, user, size=36).pack(side="left")
            ctk.CTkLabel(row, text=user, anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(10, 4))
            ctk.CTkLabel(row, text="●", text_color=COLORS["green"], font=ctk.CTkFont(size=11)).pack(side="right")

    def _extract_users_from_legacy_list(self, text):
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = ast.literal_eval(line)
                except (SyntaxError, ValueError):
                    continue
                if isinstance(data, dict):
                    return list(data.keys())
        return []

    def _update_leaderboard(self, payload):
        rows = payload.get("entries") or payload.get("leaderboard") or payload.get("results") or []
        if isinstance(rows, str):
            try:
                rows = json.loads(rows)
            except json.JSONDecodeError:
                rows = [{"player": line, "score": ""} for line in rows.splitlines() if line.strip()]
        self.leaderboard_rows = rows if isinstance(rows, list) else []
        self._render_leaderboard()

    def _render_leaderboard(self):
        if self.leaderboard_frame is None:
            return
        for child in self.leaderboard_frame.winfo_children():
            child.destroy()
        rows = self.leaderboard_rows[:5]
        if not rows:
            ctk.CTkLabel(
                self.leaderboard_frame,
                text="Play Whack-a-Mole to claim the board.",
                wraplength=220,
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=12),
            ).pack(fill="x", padx=8, pady=10)
            return
        for index, row in enumerate(rows, start=1):
            player = row.get("player") or row.get("name") or "Player" if isinstance(row, dict) else str(row)
            score = row.get("score", "") if isinstance(row, dict) else ""
            item = ctk.CTkFrame(self.leaderboard_frame, fg_color=COLORS["soft2"] if index == 1 else "#ffffff", corner_radius=8)
            item.pack(fill="x", pady=3)
            ctk.CTkLabel(item, text=str(index), width=24, text_color=COLORS["purple"], font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(8, 4), pady=7)
            ctk.CTkLabel(item, text=str(player), anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(item, text=f"{score} pts", text_color=COLORS["purple"], font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=8)

    def _set_status(self, text, color):
        if self.status_pill is not None:
            self.status_pill.configure(text=text, text_color=COLORS["text"], fg_color="#f3fbf6")

    def _timestamp(self):
        return datetime.now().strftime("%H:%M")

    def _scroll_to_bottom(self):
        if self.chat_scroll is not None:
            self.Window.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def _avatar(self, master, name, size=36, color=None):
        palette = ["#2f80ed", "#0f8f8a", "#e11d8a", "#7c3aed", "#f59e0b"]
        chosen = color or palette[sum(ord(ch) for ch in (name or "?")) % len(palette)]
        return ctk.CTkLabel(
            master,
            text=(name or "?")[:1].upper(),
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=chosen,
            text_color="#ffffff",
            font=ctk.CTkFont(size=max(11, size // 3), weight="bold"),
        )

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.sm.get_state() != S_OFFLINE:
            self.sm.set_state(S_OFFLINE)
        if self.on_close is not None:
            self.on_close()
        try:
            self.Window.destroy()
        except tk.TclError:
            pass
