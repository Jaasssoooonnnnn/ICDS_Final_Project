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
    "app_bg": "#edf3ff",
    "sidebar": "#f7faff",
    "center": "#ffffff",
    "chat_bg": "#ffffff",
    "right": "#f7faff",
    "border": "#dbe4f4",
    "soft": "#eef3ff",
    "soft2": "#f8faff",
    "text": "#111827",
    "muted": "#66728a",
    "purple": "#5b4dff",
    "purple2": "#8a62ff",
    "green": "#12b76a",
    "blue": "#3867ff",
    "pink": "#8b5cf6",
    "teal": "#20b26b",
    "orange": "#f5a524",
}

FONT = "Helvetica"
SPACE = 18

NAV_ITEMS = [
    ("💬", "Chat", "chat"),
    ("🤖", "Bot", "bot"),
    ("🎮", "Games", "game"),
    ("🖼️", "AI Images", "image"),
    ("📄", "Summary", "summary"),
    ("🏷️", "Keywords", "keywords"),
    ("⚙️", "Settings", "settings"),
]

ACTION_META = [
    ("📄", "/summary", "Generate chat summary", "Summary", "#3867ff"),
    ("🏷️", "/keywords", "Extract keywords", "Keywords", "#8b5cf6"),
    ("🖼️", "/aipic", "Generate AI image", "AI Pic", "#20b26b"),
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
        self.member_badge = None
        self.room_pinned = False
        self.notifications_enabled = True
        self.personality_var = tk.StringVar(value="Friendly")
        self.leaderboard_scope = tk.StringVar(value="This Week")
        self.leaderboard_tab_buttons = {}

        self.chat_scroll = None
        self.entryMsg = None
        self.status_pill = None
        self.member_count_label = None
        self.online_list_frame = None
        self.right_online_frame = None
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
        self.Window.title("ICDS Chat+")
        self.Window.geometry("1600x900")
        self.Window.minsize(1360, 780)
        self.Window.configure(fg_color=COLORS["app_bg"])
        self.Window.protocol("WM_DELETE_WINDOW", self.close)

        self.Window.grid_columnconfigure(0, minsize=280, weight=0)
        self.Window.grid_columnconfigure(1, weight=1)
        self.Window.grid_columnconfigure(2, minsize=500, weight=0)
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
        sidebar.grid_rowconfigure(4, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=30, pady=(28, 20))
        ctk.CTkLabel(
            brand,
            text="⌁",
            width=36,
            height=36,
            corner_radius=9,
            fg_color=COLORS["purple"],
            text_color="#ffffff",
            font=ctk.CTkFont(family=FONT, size=20, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            brand,
            text="ICDS Chat+",
            font=ctk.CTkFont(family=FONT, size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=(12, 0))

        user = ctk.CTkFrame(sidebar, width=226, height=176, fg_color="#eee8ff", corner_radius=15, border_width=1, border_color="#d9d4ff")
        user.grid_propagate(False)
        user.pack_propagate(False)
        user.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 26))
        self._avatar(user, name, size=58, color="#7c5cff").pack(pady=(12, 3))
        ctk.CTkLabel(user, text="Lv.5", height=24, corner_radius=12, fg_color=COLORS["purple"], text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold")).pack()
        info_row = ctk.CTkFrame(user, fg_color="transparent")
        info_row.pack(fill="x", padx=18, pady=(6, 0))
        ctk.CTkLabel(info_row, text=name, anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(user, text="Student ID: 2023123456", anchor="w", text_color=COLORS["muted"], font=ctk.CTkFont(size=11)).pack(fill="x", padx=18, pady=(1, 10))

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 16))
        for index, (icon, label, key) in enumerate(NAV_ITEMS):
            selected = index == 0
            btn = ctk.CTkButton(
                nav,
                text=(f"{icon}   {label}"),
                anchor="w",
                height=48,
                corner_radius=12,
                fg_color="#edf0ff" if selected else "transparent",
                hover_color="#edf0ff",
                text_color=COLORS["purple"] if selected else COLORS["text"],
                font=ctk.CTkFont(size=14, weight="bold" if selected else "normal"),
                command=self._nav_action(key),
            )
            btn.pack(fill="x", pady=4)
            self.nav_buttons[key] = btn

        footer = ctk.CTkFrame(sidebar, fg_color="#ffffff", corner_radius=16, border_width=1, border_color=COLORS["border"])
        footer.grid(row=5, column=0, sticky="ew", padx=30, pady=(0, 28))
        ctk.CTkLabel(footer, text="●", text_color=COLORS["green"], font=ctk.CTkFont(size=14)).pack(side="left", padx=(18, 8), pady=12)
        ctk.CTkLabel(footer, text="Connected", text_color=COLORS["text"], font=ctk.CTkFont(size=12)).pack(side="left")

    def _build_chat_column(self):
        center = ctk.CTkFrame(self.Window, fg_color=COLORS["center"], corner_radius=0)
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(center, fg_color="#ffffff", corner_radius=0, height=92)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="sw", padx=24, pady=(20, 0))
        ctk.CTkLabel(
            title_row,
            text="Distributed Chat Room",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")
        self.member_badge = ctk.CTkLabel(title_row, text="♙ 12", height=26, corner_radius=10, fg_color="#f0f3fb", text_color=COLORS["muted"], font=ctk.CTkFont(size=12))
        self.member_badge.pack(side="left", padx=(12, 0))
        self.member_count_label = ctk.CTkLabel(
            header,
            text="Final Project Demo",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
        )
        self.member_count_label.grid(row=1, column=0, sticky="nw", padx=24, pady=(0, 14))
        tools = ctk.CTkFrame(header, fg_color="transparent")
        tools.grid(row=0, column=2, rowspan=2, padx=(0, 22), pady=26)
        tool_actions = (
            ("⌕", self.open_search),
            ("⌖", self.toggle_pin),
            ("!", self.toggle_notifications),
            ("⋯", self.show_command_menu),
        )
        for symbol, command in tool_actions:
            ctk.CTkButton(
                tools,
                text=symbol,
                width=34,
                height=34,
                corner_radius=10,
                fg_color="transparent",
                hover_color="#edf0ff",
                text_color="#0f172a",
                font=ctk.CTkFont(size=18, weight="bold"),
                command=command,
            ).pack(side="left", padx=5)
        self.status_pill = ctk.CTkLabel(
            header,
            text="Connecting",
            height=30,
            corner_radius=12,
            fg_color="#ecfdf3",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.status_pill.grid_forget()

        ctk.CTkFrame(center, height=1, fg_color=COLORS["border"]).grid(row=0, column=0, sticky="sew")

        self.chat_scroll = ctk.CTkScrollableFrame(center, fg_color="#ffffff", scrollbar_button_color="#cbd5e1")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")
        self.chat_scroll.grid_columnconfigure(0, weight=1)
        self._date_divider()

        composer = ctk.CTkFrame(center, fg_color="#ffffff", corner_radius=0)
        composer.grid(row=2, column=0, sticky="ew")
        composer.grid_columnconfigure(1, weight=1)
        inner = ctk.CTkFrame(composer, fg_color="#ffffff", corner_radius=14, border_width=1, border_color="#aebcff")
        inner.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=16)
        inner.grid_columnconfigure(4, weight=1)
        self.entryMsg = ctk.CTkEntry(
            inner,
            height=42,
            corner_radius=10,
            border_width=0,
            fg_color="#ffffff",
            placeholder_text="Type a message...",
            text_color=COLORS["text"],
        )
        self.entryMsg.grid(row=0, column=0, columnspan=7, sticky="ew", padx=16, pady=(8, 2))
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
        composer_actions = (
            ("😊  Emoji", self.insert_emoji),
            ("📎  Files", self.show_file_notice),
            ("📄  Summary", self.request_summary),
            ("🏷️  Keywords", self.request_keywords),
        )
        for col, (label, command) in enumerate(composer_actions):
            ctk.CTkButton(
                inner,
                text=label,
                height=30,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#f0f3ff",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=12),
                command=command,
            ).grid(row=1, column=col, padx=(10 if col == 0 else 4, 4), pady=(0, 10))
        ctk.CTkLabel(inner, text="0/2000", text_color=COLORS["muted"], font=ctk.CTkFont(size=12)).grid(row=1, column=5, padx=8, pady=(0, 10), sticky="e")
        ctk.CTkButton(
            inner,
            text="➤  Send",
            width=108,
            height=46,
            corner_radius=12,
            fg_color=COLORS["purple"],
            hover_color="#4338ca",
            command=lambda: self.sendButton(self.entryMsg.get()),
        ).grid(row=1, column=6, padx=(6, 12), pady=(0, 10))

    def _build_right_panel(self):
        panel = ctk.CTkScrollableFrame(self.Window, fg_color=COLORS["right"], corner_radius=0, scrollbar_button_color="#cbd5e1")
        panel.grid(row=0, column=2, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        online = self._panel_card(panel, "Online Users", "♟")
        self.right_online_frame = ctk.CTkFrame(online, fg_color="transparent")
        self.right_online_frame.pack(fill="x", padx=16, pady=(0, 14))
        self._render_right_online_users()

        quick = self._panel_card(panel, "Quick Actions", "⚡")
        for icon, title, subtitle, action, color in ACTION_META:
            self._action_row(quick, icon, title, subtitle, action, color).pack(fill="x", padx=16, pady=5)

        settings = self._panel_card(panel, "ChatBot Settings", "▣")
        ctk.CTkLabel(settings, text="Choose ChatBot Personality", anchor="w", text_color=COLORS["muted"], font=ctk.CTkFont(size=12)).pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkOptionMenu(
            settings,
            variable=self.personality_var,
            values=["Friendly", "Humorous", "Serious"],
            height=38,
            corner_radius=10,
            fg_color="#f7f4ff",
            button_color=COLORS["purple"],
            button_hover_color="#4338ca",
            text_color=COLORS["purple"],
            dropdown_fg_color="#ffffff",
            dropdown_hover_color="#edf0ff",
            dropdown_text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.set_personality,
        ).pack(fill="x", padx=16, pady=(0, 16))

        leaderboard = self._panel_card(panel, "Leaderboard", "🏆")
        tabs = ctk.CTkFrame(leaderboard, fg_color="#edf1f8", corner_radius=12)
        tabs.pack(fill="x", padx=16, pady=(0, 12))
        for idx, tab in enumerate(("This Week", "This Month", "All Time")):
            tab_button = ctk.CTkButton(
                tabs,
                text=tab,
                height=32,
                corner_radius=10,
                border_width=0,
                fg_color=COLORS["purple"] if idx == 0 else "transparent",
                hover_color="#dfe6ff",
                text_color="#ffffff" if idx == 0 else COLORS["muted"],
                font=ctk.CTkFont(size=11, weight="bold" if idx == 0 else "normal"),
                command=lambda scope=tab: self.set_leaderboard_scope(scope),
            )
            tab_button.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            self.leaderboard_tab_buttons[tab] = tab_button
        self.leaderboard_frame = ctk.CTkFrame(leaderboard, fg_color="transparent")
        self.leaderboard_frame.pack(fill="x", padx=16, pady=(0, 16))
        self._render_leaderboard()

        insights = self._panel_card(panel, "Insights", "~")
        self.summary_label = ctk.CTkLabel(
            insights,
            text=self.last_summary,
            wraplength=300,
            justify="left",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
        )
        self.summary_label.pack(fill="x", padx=12, pady=(4, 10))
        self.keyword_label = ctk.CTkLabel(
            insights,
            text="Tags will appear here.",
            wraplength=300,
            justify="left",
            text_color=COLORS["purple"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.keyword_label.pack(fill="x", padx=12, pady=(0, 12))

        sentiment = self._panel_card(panel, "Sentiment Overview", "*")
        grid = ctk.CTkFrame(sentiment, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 14))
        grid.grid_columnconfigure(0, weight=1)
        for row_index, label in enumerate(("Positive", "Neutral", "Negative")):
            box = ctk.CTkFrame(grid, fg_color=COLORS["soft2"], corner_radius=10)
            box.grid(row=row_index, column=0, sticky="ew", pady=4)
            self.insight_labels[label] = ctk.CTkLabel(
                box,
                text=f"{label}  0",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["text"],
            )
            self.insight_labels[label].pack(side="left", padx=12, pady=8)

    def _panel_card(self, master, title, icon):
        card = ctk.CTkFrame(master, fg_color="#ffffff", corner_radius=14, border_width=1, border_color=COLORS["border"])
        card.grid(sticky="ew", padx=18, pady=(14, 0))
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(header, text=icon, width=30, height=30, corner_radius=10, fg_color="#eef2ff", text_color=COLORS["purple"], font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text=title, text_color=COLORS["text"], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(10, 0))
        return card

    def _action_row(self, master, icon_text, title, subtitle, action, color):
        row = ctk.CTkFrame(master, height=44, fg_color="#fbfcff", corner_radius=9, border_width=1, border_color=COLORS["border"])
        row.pack_propagate(False)
        icon = ctk.CTkLabel(row, text=icon_text, width=34, height=34, corner_radius=8, fg_color=color, text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"))
        icon.pack(side="left", padx=(10, 10), pady=5)
        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(side="left", fill="both", expand=True, pady=8, padx=(0, 8))
        ctk.CTkLabel(text, text=title, width=112, anchor="w", text_color=COLORS["purple"], font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkLabel(text, text=subtitle, anchor="e", text_color=COLORS["muted"], font=ctk.CTkFont(size=11)).pack(side="right")
        self._bind_click_recursive(row, lambda _event: self._run_quick_action(action))
        return row

    def _bind_click_recursive(self, widget, callback):
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click_recursive(child, callback)

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
        elif action == "AI Pic":
            self.prompt_image()
        elif action == "Bot":
            self.prompt_bot()
        elif action == "Settings":
            self.show_settings_help()
        else:
            self.show_chat_home()

    def show_chat_home(self):
        self.add_bot_card("You are already in the main group chat.", title="Chat")

    def prompt_bot(self):
        dialog = ctk.CTkInputDialog(text="Ask ICDS Bot", title="Bot")
        question = (dialog.get_input() or "").strip()
        if question:
            self._send_bot_request(question, direct=True)

    def show_settings_help(self):
        self.add_bot_card(
            "Use the ChatBot Settings dropdown on the right to switch between Friendly, Humorous, and Serious bot personalities.",
            title="Settings",
        )

    def insert_emoji(self):
        self.entryMsg.insert("end", "😊")
        self.entryMsg.focus()

    def show_file_notice(self):
        self.add_bot_card(
            "File upload is not part of the selected guideline/bonus scope. Use /aipic: for generated image sharing.",
            title="Files",
        )

    def set_leaderboard_scope(self, scope):
        self.leaderboard_scope.set(scope)
        for label, button in self.leaderboard_tab_buttons.items():
            active = label == scope
            button.configure(
                fg_color=COLORS["purple"] if active else "transparent",
                text_color="#ffffff" if active else COLORS["muted"],
                font=ctk.CTkFont(size=11, weight="bold" if active else "normal"),
            )
        self.add_bot_card(f"Leaderboard view changed to {scope}.", title="Leaderboard")

    def open_search(self):
        dialog = ctk.CTkInputDialog(text="Search your chat history", title="Search")
        term = (dialog.get_input() or "").strip()
        if not term:
            return
        self.add_bot_card(f"Searching local chat history for: {term}", title="Search")
        self._safe_send({"action": "search", "target": term})

    def toggle_pin(self):
        self.room_pinned = not self.room_pinned
        status = "pinned" if self.room_pinned else "unpinned"
        self.add_bot_card(f"Distributed Chat Room is now {status} for this session.", title="Pin")

    def toggle_notifications(self):
        self.notifications_enabled = not self.notifications_enabled
        status = "enabled" if self.notifications_enabled else "muted"
        self.add_bot_card(f"Room alerts are {status}.", title="Alerts")

    def show_command_menu(self):
        commands = (
            "Available commands:\n"
            "/bot your question - ask the AI assistant directly\n"
            "@bot your question - ask the AI assistant in chat\n"
            "/summary - summarize recent chat\n"
            "/keywords - extract important keywords\n"
            "/aipic: prompt - generate an AI image\n"
            "/personality: style - change bot personality"
        )
        self.add_bot_card(commands, title="Menu")

    def set_personality(self, choice):
        profiles = {
            "Friendly": "friendly and supportive teaching assistant",
            "Humorous": "lightly humorous but still concise project teammate",
            "Serious": "serious, concise, technical project reviewer",
        }
        personality = profiles.get(choice, profiles["Friendly"])
        self.add_bot_card(f"Setting bot personality to {choice}.", title="ChatBot Settings")
        self._safe_send({"action": "exchange", "sender": self.name, "message": f"/personality: {personality}"})

    def _nav_action(self, key):
        return lambda: self._run_quick_action(
            "Game"
            if key == "game"
            else "Bot"
            if key == "bot"
            else "Summary"
            if key == "summary"
            else "Keywords"
            if key == "keywords"
            else "AI Pic"
            if key == "image"
            else "Settings"
            if key == "settings"
            else "Chats"
        )

    def _date_divider(self):
        row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(18, 14))
        row.grid_columnconfigure((0, 2), weight=1)
        ctk.CTkFrame(row, height=1, fg_color=COLORS["border"]).grid(row=0, column=0, sticky="ew", padx=(120, 12))
        ctk.CTkLabel(row, text="Today", height=24, corner_radius=12, fg_color=COLORS["soft"], text_color="#525b70", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=1)
        ctk.CTkFrame(row, height=1, fg_color=COLORS["border"]).grid(row=0, column=2, sticky="ew", padx=(12, 120))

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
        if lower.startswith("/personality:") or lower.startswith("/botpersona:"):
            self.add_message(self.name, msg, sentiment="Neutral", outgoing=True)
            self._safe_send({"action": "exchange", "sender": self.name, "message": msg})
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
        elif action == "search":
            results = payload.get("results") or "No matching chat history found."
            self.add_bot_card(results, title="Search")
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
        ).pack(fill="x", padx=18, pady=2)
        self._scroll_to_bottom()

    def add_bot_card(self, text, title="ICDS Bot"):
        BotCard(self.chat_scroll, title=title, timestamp=self._timestamp(), text=text).pack(fill="x", padx=18, pady=3)
        self._scroll_to_bottom()

    def add_image_card(self, payload):
        ImageCard(self.chat_scroll, payload=payload, timestamp=self._timestamp()).pack(fill="x", padx=18, pady=3)
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
            emoji = {"Positive": "😊", "Neutral": "😐", "Negative": "😡"}.get(label, "")
            widget.configure(text=f"{label} {emoji}   {self.sentiment_counts.get(label, 0)}")

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
            self.member_count_label.configure(text="Final Project Demo")
            if self.member_badge is not None:
                self.member_badge.configure(text=f"♙ {count}")
        self._render_online_users()
        self._render_right_online_users()

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
            ctk.CTkLabel(row, text=user, anchor="w", text_color="#e2e8f0", font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(10, 4))
            ctk.CTkLabel(row, text="●", text_color=COLORS["green"], font=ctk.CTkFont(size=11)).pack(side="right")

    def _render_right_online_users(self):
        if self.right_online_frame is None:
            return
        for child in self.right_online_frame.winfo_children():
            child.destroy()
        users = self.online_users or [self.name or "Alex Zhang", "ChatBot"]
        shown = list(users[:4])
        if "ChatBot" not in shown:
            shown.append("ChatBot")
        for index, user in enumerate(shown[:4]):
            row = ctk.CTkFrame(self.right_online_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)
            self._avatar(row, user, size=32, color="#dbeafe" if user != "ChatBot" else "#e0e7ff").pack(side="left")
            label = str(user)
            if label == self.name:
                label += " (You)"
            ctk.CTkLabel(row, text=label, anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=13)).pack(side="left", fill="x", expand=True, padx=(10, 4))
            if index == 0 and label != "ChatBot":
                ctk.CTkLabel(row, text="♛", text_color=COLORS["orange"], font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 8))
            if user == "ChatBot":
                ctk.CTkLabel(row, text="Bot", height=20, corner_radius=6, fg_color="#eee8ff", text_color=COLORS["purple"], font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=(0, 8))
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
            rows = [
                {"player": "Alice", "score": 1280},
                {"player": "Bob", "score": 980},
                {"player": self.name or "Alex Zhang", "score": 760},
                {"player": "Carol", "score": 620},
                {"player": "Dave", "score": 510},
            ]
        for index, row in enumerate(rows, start=1):
            player = row.get("player") or row.get("name") or "Player" if isinstance(row, dict) else str(row)
            score = row.get("score", "") if isinstance(row, dict) else ""
            item = ctk.CTkFrame(self.leaderboard_frame, fg_color="#ffffff", corner_radius=8)
            item.pack(fill="x", pady=5)
            rank = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else str(index)
            ctk.CTkLabel(item, text=rank, width=28, text_color=COLORS["muted"], font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6), pady=3)
            self._avatar(item, str(player), size=26).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(item, text=f"{score} pts", width=72, anchor="e", text_color=COLORS["muted"], font=ctk.CTkFont(size=12)).pack(side="right")
            ctk.CTkLabel(item, text=str(player), anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True)

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
