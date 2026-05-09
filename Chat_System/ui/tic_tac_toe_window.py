"""Graphical multiplayer Tic-Tac-Toe client window."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk


COLORS = {
    "bg": "#f7faff",
    "card": "#ffffff",
    "border": "#dbe4f4",
    "text": "#111827",
    "muted": "#66728a",
    "purple": "#5b4dff",
    "blue": "#2563eb",
    "green": "#12b76a",
    "red": "#dc2626",
}


class TicTacToeWindow:
    def __init__(self, master, username, send_payload, on_close=None):
        self.master = master
        self.username = username
        self.send_payload = send_payload
        self.on_close = on_close
        self.room_id = None
        self.symbol = "-"
        self.state = None
        self.closed = False

        self.window = ctk.CTkToplevel(master)
        self.window.title("Multiplayer Tic-Tac-Toe")
        self.window.geometry("430x540")
        self.window.resizable(False, False)
        self.window.configure(fg_color=COLORS["bg"])
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.transient(master)
        self.window.lift()
        self.window.focus_force()

        self.cells = []
        self._build()
        self._set_status("Click Join Game to enter matchmaking.")
        self._set_board_enabled(False)

    def _build(self):
        wrapper = ctk.CTkFrame(self.window, fg_color=COLORS["card"], corner_radius=16, border_width=1, border_color=COLORS["border"])
        wrapper.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(wrapper, text="Multiplayer Tic-Tac-Toe", text_color=COLORS["text"], font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(18, 4))
        ctk.CTkLabel(wrapper, text="Play with another connected client", text_color=COLORS["muted"], font=ctk.CTkFont(size=13)).pack(pady=(0, 14))

        meta = ctk.CTkFrame(wrapper, fg_color="#f3f6ff", corner_radius=12)
        meta.pack(fill="x", padx=20, pady=(0, 14))
        self.room_label = self._meta_label(meta, "Room: Not joined")
        self.symbol_label = self._meta_label(meta, "You are: -")
        self.turn_label = self._meta_label(meta, "Turn: -")

        board = ctk.CTkFrame(wrapper, fg_color="transparent")
        board.pack(pady=(2, 12))
        for row in range(3):
            board.grid_rowconfigure(row, weight=1)
            values = []
            for col in range(3):
                button = ctk.CTkButton(
                    board,
                    text="",
                    width=108,
                    height=88,
                    corner_radius=12,
                    fg_color="#ffffff",
                    hover_color="#eef2ff",
                    border_width=2,
                    border_color="#cfd8f6",
                    text_color=COLORS["purple"],
                    font=ctk.CTkFont(size=34, weight="bold"),
                    command=lambda r=row, c=col: self.make_move(r, c),
                )
                button.grid(row=row, column=col, padx=5, pady=5)
                values.append(button)
            self.cells.append(values)

        self.status_label = ctk.CTkLabel(wrapper, text="", wraplength=350, text_color=COLORS["text"], font=ctk.CTkFont(size=13, weight="bold"))
        self.status_label.pack(fill="x", padx=22, pady=(0, 12))

        actions = ctk.CTkFrame(wrapper, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkButton(actions, text="Join Game", height=38, corner_radius=10, fg_color=COLORS["purple"], hover_color="#4338ca", command=self.join_game).pack(side="left", expand=True, fill="x", padx=(0, 8))
        ctk.CTkButton(actions, text="Restart", height=38, corner_radius=10, fg_color="#eef2ff", hover_color="#dfe6ff", text_color=COLORS["purple"], command=self.restart).pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkButton(actions, text="Close", height=38, corner_radius=10, fg_color="#f1f5f9", hover_color="#e2e8f0", text_color=COLORS["text"], command=self.close).pack(side="left", expand=True, fill="x", padx=(8, 0))

    def _meta_label(self, master, text):
        label = ctk.CTkLabel(master, text=text, anchor="w", text_color=COLORS["text"], font=ctk.CTkFont(size=12, weight="bold"))
        label.pack(fill="x", padx=14, pady=(8 if text.startswith("Room") else 2, 8 if text.startswith("Turn") else 2))
        return label

    def join_game(self):
        self.send_payload({"action": "ttt_join", "type": "ttt_join", "username": self.username})
        self._set_status("Joining Tic-Tac-Toe matchmaking...")

    def restart(self):
        if not self.room_id:
            self._set_status("Join a room before requesting restart.")
            return
        self.send_payload({"action": "ttt_restart", "type": "ttt_restart", "room_id": self.room_id, "username": self.username})
        self._set_status("Restart requested. Waiting for the other player.")

    def make_move(self, row, col):
        if not self.room_id:
            return
        self.send_payload(
            {
                "action": "ttt_move",
                "type": "ttt_move",
                "room_id": self.room_id,
                "username": self.username,
                "row": row,
                "col": col,
            }
        )

    def handle_message(self, payload):
        action = payload.get("action") or payload.get("type")
        if action == "ttt_waiting":
            self.room_id = payload.get("room_id")
            self.room_label.configure(text=f"Room: {self.room_id}")
            self.symbol_label.configure(text="You are: X")
            self.turn_label.configure(text="Turn: Waiting")
            self._set_status(payload.get("message") or "Waiting for opponent...")
            self._set_board_enabled(False)
        elif action == "ttt_state":
            self.apply_state(payload)
        elif action == "ttt_error":
            message = payload.get("message") or "Tic-Tac-Toe error."
            self._set_status(message, error=True)
            try:
                messagebox.showwarning("Tic-Tac-Toe", message, parent=self.window)
            except tk.TclError:
                pass

    def apply_state(self, state):
        self.state = state
        self.room_id = state.get("room_id")
        board = state.get("board") or [["", "", ""], ["", "", ""], ["", "", ""]]
        symbols = state.get("symbols") or {}
        self.symbol = symbols.get(self.username, "-")
        turn = state.get("turn")
        status = state.get("status")
        winner = state.get("winner")

        self.room_label.configure(text=f"Room: {self.room_id or 'Not joined'}")
        self.symbol_label.configure(text=f"You are: {self.symbol}")
        self.turn_label.configure(text=f"Turn: {turn or '-'}")

        for row in range(3):
            for col in range(3):
                value = board[row][col]
                self.cells[row][col].configure(
                    text=value,
                    text_color=COLORS["blue"] if value == "X" else COLORS["red"] if value == "O" else COLORS["purple"],
                )

        if status == "playing":
            if turn == self.username:
                self._set_status("Your turn.")
                self._set_board_enabled(True, board)
            else:
                self._set_status(f"{turn}'s turn.")
                self._set_board_enabled(False)
        elif status == "finished":
            if winner == self.username:
                self._set_status("You won!")
            elif winner:
                self._set_status("You lost!")
            else:
                self._set_status(state.get("message") or "Game finished.")
            self._set_board_enabled(False)
        elif status == "draw":
            self._set_status("Draw!")
            self._set_board_enabled(False)
        elif status == "closed":
            self._set_status(state.get("message") or "Opponent left the room.")
            self._set_board_enabled(False)
        else:
            self._set_status(state.get("message") or "Waiting for opponent...")
            self._set_board_enabled(False)

    def _set_board_enabled(self, enabled, board=None):
        board = board or [["", "", ""], ["", "", ""], ["", "", ""]]
        for row in range(3):
            for col in range(3):
                state = "normal" if enabled and not board[row][col] else "disabled"
                self.cells[row][col].configure(state=state)

    def _set_status(self, text, error=False):
        self.status_label.configure(text=text, text_color=COLORS["red"] if error else COLORS["text"])

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.room_id:
            self.send_payload({"action": "ttt_leave", "type": "ttt_leave", "room_id": self.room_id, "username": self.username})
        if self.on_close:
            self.on_close()
        try:
            self.window.destroy()
        except tk.TclError:
            pass
