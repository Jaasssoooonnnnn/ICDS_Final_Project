#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

ASSET_SHEET = Path(__file__).resolve().parents[1] / "assets" / "whack_mole_sheet.png"


class WhackAMoleWindow:
    def __init__(self, master, player_name, submit_callback, duration=30):
        self.master = master
        self.player_name = player_name
        self.submit_callback = submit_callback
        self.duration = duration
        self.time_left = duration
        self.score = 0
        self.active_hole = None
        self.running = True
        self.submitted = False
        self.banner_image = None
        self.result_image = None

        self.window = tk.Toplevel(master)
        self.window.title("Whack-a-Mole")
        self.window.geometry("620x560")
        self.window.resizable(False, False)
        self.window.configure(bg="#eef2f8")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas = tk.Canvas(self.window, width=620, height=500, bg="#eef2f8", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.footer = tk.Frame(self.window, bg="#ffffff", height=60)
        self.footer.pack(fill="x")

        self.submit_button = tk.Button(
            self.footer,
            text="Submit Score",
            command=self.submit_score,
            state="disabled",
            bg="#635bff",
            fg="#ffffff",
            activebackground="#5148e5",
            relief="flat",
            font=("Helvetica", 13, "bold"),
            padx=18,
            pady=8,
        )
        self.submit_button.pack(side="right", padx=18, pady=10)

        tk.Label(
            self.footer,
            text="Click the mole before it dives away.",
            bg="#ffffff",
            fg="#4b5563",
            font=("Helvetica", 12),
        ).pack(side="left", padx=18)

        self.holes = [(120, 190), (310, 190), (500, 190), (120, 340), (310, 340), (500, 340)]
        self._load_assets()
        self._draw_static_scene()
        self._spawn_mole()
        self._tick()

    def _load_assets(self):
        if not ASSET_SHEET.exists():
            return
        try:
            sheet = Image.open(ASSET_SHEET)
            banner = sheet.crop((470, 65, 1450, 505)).resize((620, 278))
            result = sheet.crop((485, 540, 1445, 930)).resize((430, 175))
        except OSError:
            return
        self.banner_image = ImageTk.PhotoImage(banner)
        self.result_image = ImageTk.PhotoImage(result)

    def _draw_static_scene(self):
        self.canvas.create_rectangle(0, 0, 620, 500, fill="#eef2f8", outline="")
        self.canvas.create_rectangle(0, 0, 620, 92, fill="#192033", outline="")
        self.canvas.create_text(
            30,
            28,
            text="Whack-a-Mole",
            anchor="w",
            fill="#ffffff",
            font=("Helvetica", 26, "bold"),
        )
        self.timer_text = self.canvas.create_text(
            500,
            30,
            text=f"Time {self.time_left}s",
            anchor="w",
            fill="#cbd5ff",
            font=("Helvetica", 16, "bold"),
        )
        self.score_text = self.canvas.create_text(
            500,
            58,
            text=f"Score {self.score}",
            anchor="w",
            fill="#ffffff",
            font=("Helvetica", 16, "bold"),
        )
        self.canvas.create_rectangle(0, 92, 620, 500, fill="#dff5dc", outline="")
        if self.banner_image is not None:
            self.canvas.create_image(310, 232, image=self.banner_image)
        for x, y in self.holes:
            self.canvas.create_oval(x - 58, y + 20, x + 58, y + 58, fill="#8d6e63", outline="#6d4c41", width=3)
            self.canvas.create_oval(x - 44, y + 29, x + 44, y + 51, fill="#5d4037", outline="")

    def _spawn_mole(self):
        if not self.running:
            return
        self.canvas.delete("mole")
        self.active_hole = random.randrange(len(self.holes))
        x, y = self.holes[self.active_hole]
        self.canvas.create_oval(x - 34, y - 42, x + 34, y + 42, fill="#9b6a45", outline="#6d4428", width=3, tags=("mole",))
        self.canvas.create_oval(x - 18, y - 18, x - 7, y - 7, fill="#111827", outline="", tags=("mole",))
        self.canvas.create_oval(x + 7, y - 18, x + 18, y - 7, fill="#111827", outline="", tags=("mole",))
        self.canvas.create_oval(x - 7, y - 4, x + 7, y + 8, fill="#f2a7a7", outline="", tags=("mole",))
        self.canvas.create_arc(x - 17, y + 8, x + 17, y + 28, start=200, extent=140, style="arc", width=3, outline="#3b2418", tags=("mole",))
        self.canvas.tag_bind("mole", "<Button-1>", self._hit_mole)
        self.window.after(820, self._spawn_mole)

    def _hit_mole(self, _event):
        if not self.running:
            return
        self.score += 1
        self.canvas.itemconfigure(self.score_text, text=f"Score {self.score}")
        self.canvas.delete("mole")
        self.active_hole = None

    def _tick(self):
        if not self.running:
            return
        self.canvas.itemconfigure(self.timer_text, text=f"Time {self.time_left}s")
        if self.time_left <= 0:
            self._finish()
            return
        self.time_left -= 1
        self.window.after(1000, self._tick)

    def _finish(self):
        self.running = False
        self.canvas.delete("mole")
        if self.result_image is not None:
            self.canvas.create_image(310, 270, image=self.result_image, tags=("result",))
        else:
            self.canvas.create_rectangle(95, 150, 525, 390, fill="#ffffff", outline="#d9def0", width=2, tags=("result",))
        self.canvas.create_text(310, 210, text="Time!", fill="#20233a", font=("Helvetica", 30, "bold"), tags=("result",))
        self.canvas.create_text(
            310,
            266,
            text=f"{self.player_name}, your score is {self.score}.",
            fill="#4b5563",
            font=("Helvetica", 16),
            tags=("result",),
        )
        self.canvas.create_text(
            310,
            315,
            text="Submit it to refresh the shared leaderboard.",
            fill="#635bff",
            font=("Helvetica", 14, "bold"),
            tags=("result",),
        )
        self.submit_button.configure(state="normal")

    def submit_score(self):
        if self.submitted:
            return
        self.submitted = True
        self.submit_button.configure(text="Submitted", state="disabled")
        self.submit_callback(self.score)

    def close(self):
        self.running = False
        self.window.destroy()
