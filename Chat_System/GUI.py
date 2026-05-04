#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

        self.chat_scroll = None
        self.entryMsg = None
        self.status_pill = None
        self.online_list = None
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

        card = ctk.CTkFrame(self.login_window, fg_color="#ffffff", corner_radius=18)
        card.pack(fill="both", expand=True, padx=34, pady=34)

        ctk.CTkLabel(
            card,
            text="ICDS Chat",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#20233a",
        ).pack(pady=(36, 6))
        ctk.CTkLabel(
            card,
            text="Sign in to your project workspace",
            font=ctk.CTkFont(size=14),
            text_color="#67708a",
        ).pack(pady=(0, 26))

        self.entryName = ctk.CTkEntry(
            card,
            height=44,
            corner_radius=12,
            placeholder_text="Display name",
            border_color="#d9def0",
            fg_color="#f8f9fd",
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
            fg_color="#635bff",
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
            self._set_status("Connected", "#16a34a")
            self._request_online_users()
            self._request_leaderboard()
            self.Window.after(int(CHAT_WAIT * 1000), self.proc)
        elif response.get("status") == "duplicate":
            self.statusLabel.configure(text="Duplicate username, try another.")
        else:
            self.statusLabel.configure(text="Login failed, try again.")

    def layout(self, name):
        self.Window.deiconify()
        self.Window.title("ICDS Chat Workspace")
        self.Window.geometry("1180x760")
        self.Window.minsize(980, 660)
        self.Window.configure(fg_color="#eef2f8")
        self.Window.protocol("WM_DELETE_WINDOW", self.close)

        self.Window.grid_columnconfigure(0, minsize=236, weight=0)
        self.Window.grid_columnconfigure(1, weight=1)
        self.Window.grid_columnconfigure(2, minsize=300, weight=0)
        self.Window.grid_rowconfigure(0, weight=1)

        self._build_sidebar(name)
        self._build_chat_column()
        self._build_right_panel()
        self.add_bot_card(
            "Welcome to ICDS Chat. Use @bot, /summary, /keywords, or /aipic: your prompt when you are ready.",
            title="ICDS Bot",
        )

    def _build_sidebar(self, name):
        sidebar = ctk.CTkFrame(self.Window, fg_color="#192033", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="ICDS",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#ffffff",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(30, 4))
        ctk.CTkLabel(
            sidebar,
            text="Final Project Chat",
            font=ctk.CTkFont(size=13),
            text_color="#aeb7d5",
        ).grid(row=1, column=0, sticky="w", padx=24)

        user_card = ctk.CTkFrame(sidebar, fg_color="#242d46", corner_radius=14)
        user_card.grid(row=2, column=0, sticky="ew", padx=18, pady=(28, 16))
        ctk.CTkLabel(
            user_card,
            text=name[:1].upper() or "U",
            width=42,
            height=42,
            corner_radius=21,
            fg_color="#7668ff",
            text_color="#ffffff",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=14, pady=14)
        ctk.CTkLabel(
            user_card,
            text=name,
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        self.status_pill = ctk.CTkLabel(
            sidebar,
            text="Connecting",
            height=28,
            corner_radius=14,
            fg_color="#3b425a",
            text_color="#ffffff",
        )
        self.status_pill.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 22))

        ctk.CTkLabel(
            sidebar,
            text="Online Users",
            text_color="#dce3ff",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=4, column=0, sticky="w", padx=24, pady=(2, 8))
        self.online_list = ctk.CTkTextbox(
            sidebar,
            height=220,
            fg_color="#151b2c",
            text_color="#dce3ff",
            border_width=0,
            corner_radius=12,
        )
        self.online_list.grid(row=5, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.online_list.insert("1.0", "Loading...")
        self.online_list.configure(state="disabled")

        ctk.CTkButton(
            sidebar,
            text="Refresh Users",
            height=38,
            corner_radius=10,
            fg_color="#384261",
            hover_color="#465274",
            command=self._request_online_users,
        ).grid(row=6, column=0, sticky="ew", padx=18, pady=(0, 18))

    def _build_chat_column(self):
        center = ctk.CTkFrame(self.Window, fg_color="#f7f8fc", corner_radius=0)
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(center, fg_color="#ffffff", corner_radius=0, height=76)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Group Conversation",
            text_color="#20233a",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(18, 0))
        ctk.CTkLabel(
            header,
            text="Shared room with Gemini bot, image cards, insights, and game scores",
            text_color="#67708a",
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 16))

        self.chat_scroll = ctk.CTkScrollableFrame(center, fg_color="#f7f8fc")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        self.chat_scroll.grid_columnconfigure(0, weight=1)

        composer = ctk.CTkFrame(center, fg_color="#ffffff", corner_radius=18)
        composer.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        composer.grid_columnconfigure(0, weight=1)
        self.entryMsg = ctk.CTkEntry(
            composer,
            height=46,
            corner_radius=13,
            border_color="#dce2f2",
            fg_color="#f8f9fd",
            placeholder_text="Type a message, @bot question, /summary, /keywords, or /aipic: prompt",
        )
        self.entryMsg.grid(row=0, column=0, sticky="ew", padx=(16, 10), pady=14)
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
        ctk.CTkButton(
            composer,
            text="Send",
            width=96,
            height=44,
            corner_radius=12,
            fg_color="#635bff",
            hover_color="#5148e5",
            command=lambda: self.sendButton(self.entryMsg.get()),
        ).grid(row=0, column=1, padx=(0, 16), pady=14)

    def _build_right_panel(self):
        panel = ctk.CTkScrollableFrame(self.Window, fg_color="#ffffff", corner_radius=0)
        panel.grid(row=0, column=2, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="Quick Actions",
            text_color="#20233a",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(28, 12))

        actions = ctk.CTkFrame(panel, fg_color="#f4f6fb", corner_radius=14)
        actions.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 20))
        actions.grid_columnconfigure((0, 1), weight=1)
        buttons = [
            ("Game", self.open_game),
            ("Summary", self.request_summary),
            ("Keywords", self.request_keywords),
            ("AI Pic", self.prompt_image),
        ]
        for index, (label, command) in enumerate(buttons):
            ctk.CTkButton(
                actions,
                text=label,
                height=40,
                corner_radius=10,
                fg_color="#ffffff",
                text_color="#31384f",
                border_width=1,
                border_color="#dfe4f2",
                hover_color="#edf0fb",
                command=command,
            ).grid(row=index // 2, column=index % 2, sticky="ew", padx=8, pady=8)

        ctk.CTkLabel(
            panel,
            text="Sentiment",
            text_color="#20233a",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=2, column=0, sticky="w", padx=22, pady=(0, 10))
        sentiments = ctk.CTkFrame(panel, fg_color="#f4f6fb", corner_radius=14)
        sentiments.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 20))
        sentiments.grid_columnconfigure((0, 1, 2), weight=1)
        for col, label in enumerate(("Positive", "Neutral", "Negative")):
            box = ctk.CTkFrame(sentiments, fg_color="#ffffff", corner_radius=12)
            box.grid(row=0, column=col, sticky="ew", padx=6, pady=10)
            self.insight_labels[label] = ctk.CTkLabel(
                box,
                text="0",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#20233a",
            )
            self.insight_labels[label].pack(pady=(10, 0))
            ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=10), text_color="#67708a").pack(pady=(0, 10))

        ctk.CTkLabel(
            panel,
            text="Insights",
            text_color="#20233a",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=4, column=0, sticky="w", padx=22, pady=(0, 10))
        insight_card = ctk.CTkFrame(panel, fg_color="#f4f6fb", corner_radius=14)
        insight_card.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 20))
        self.summary_label = ctk.CTkLabel(
            insight_card,
            text=self.last_summary,
            wraplength=238,
            justify="left",
            text_color="#31384f",
        )
        self.summary_label.pack(fill="x", padx=14, pady=(14, 8))
        self.keyword_label = ctk.CTkLabel(
            insight_card,
            text="Tags will appear here.",
            wraplength=238,
            justify="left",
            text_color="#635bff",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.keyword_label.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkLabel(
            panel,
            text="Leaderboard",
            text_color="#20233a",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=6, column=0, sticky="w", padx=22, pady=(0, 10))
        self.leaderboard_frame = ctk.CTkFrame(panel, fg_color="#f4f6fb", corner_radius=14)
        self.leaderboard_frame.grid(row=7, column=0, sticky="ew", padx=18, pady=(0, 28))
        self._render_leaderboard()

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
        ).pack(fill="x", padx=8, pady=7, anchor="e" if outgoing else "w")
        self._scroll_to_bottom()

    def add_bot_card(self, text, title="ICDS Bot"):
        BotCard(self.chat_scroll, title=title, timestamp=self._timestamp(), text=text).pack(fill="x", padx=8, pady=7)
        self._scroll_to_bottom()

    def add_image_card(self, payload):
        ImageCard(self.chat_scroll, payload=payload, timestamp=self._timestamp()).pack(fill="x", padx=8, pady=7)
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
        if self.online_list is None:
            return
        self.online_list.configure(state="normal")
        self.online_list.delete("1.0", "end")
        self.online_list.insert("1.0", "\n".join(users) if users else "No users listed.")
        self.online_list.configure(state="disabled")

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
                wraplength=230,
                text_color="#67708a",
            ).pack(fill="x", padx=14, pady=16)
            return
        for index, row in enumerate(rows, start=1):
            player = row.get("player") or row.get("name") or "Player" if isinstance(row, dict) else str(row)
            score = row.get("score", "") if isinstance(row, dict) else ""
            ctk.CTkLabel(
                self.leaderboard_frame,
                text=f"{index}. {player}  {score}",
                anchor="w",
                text_color="#31384f",
                font=ctk.CTkFont(size=13, weight="bold" if index == 1 else "normal"),
            ).pack(fill="x", padx=14, pady=(10 if index == 1 else 4, 6))

    def _set_status(self, text, color):
        if self.status_pill is not None:
            self.status_pill.configure(text=text, fg_color=color)

    def _timestamp(self):
        return datetime.now().strftime("%H:%M")

    def _scroll_to_bottom(self):
        self.Window.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

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
