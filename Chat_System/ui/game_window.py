#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Whack-a-Mole game window using imagegen-produced artwork."""

from __future__ import annotations

import random
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageChops, ImageTk

ASSET_SHEET = Path(__file__).resolve().parents[1] / "assets" / "whack_mole_sheet.png"

GAME = {
    "cream": "#fff6dc",
    "cream2": "#fffaf0",
    "purple": "#635bff",
    "purple2": "#8b76ff",
    "text": "#3a2414",
    "green": "#22c55e",
    "red": "#ef4444",
    "blue": "#2563eb",
    "gold": "#f59e0b",
    "border": "#7a4a20",
}


class WhackAMoleWindow:
    def __init__(self, master, player_name, submit_callback, duration=30):
        self.master = master
        self.player_name = player_name
        self.submit_callback = submit_callback
        self.duration = duration
        self.time_left = duration
        self.score = 0
        self.best_score = 0
        self.active_hole = None
        self.running = True
        self.submitted = False
        self.after_ids = []
        self.images = {}

        self.window = tk.Toplevel(master)
        self.window.title("Whack-a-Mole")
        self.window.geometry("1040x700")
        self.window.resizable(False, False)
        self.window.configure(bg="#dff7ff")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.transient(master)
        self.window.lift()
        self.window.focus_force()

        self.canvas = tk.Canvas(self.window, width=1040, height=700, bg="#dff7ff", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.holes = [
            (230, 292),
            (520, 292),
            (810, 292),
            (230, 468),
            (520, 468),
            (810, 468),
        ]

        self._load_assets()
        self._draw_scene()
        self._spawn_mole()
        self._tick()

    def _load_assets(self):
        if not ASSET_SHEET.exists():
            raise FileNotFoundError(f"Missing game asset sheet: {ASSET_SHEET}")
        sheet = Image.open(ASSET_SHEET).convert("RGBA")

        field = sheet.crop((470, 58, 1454, 505)).resize((980, 446), Image.Resampling.LANCZOS)
        self.images["field"] = ImageTk.PhotoImage(field)

        mole = sheet.crop((10, 220, 420, 710)).convert("RGBA")
        bg = Image.new("RGBA", mole.size, (255, 255, 255, 255))
        diff = ImageChops.difference(mole, bg).convert("L")
        alpha = diff.point(lambda p: 0 if p < 88 else 255)
        mole.putalpha(alpha)
        mole = mole.crop(mole.getbbox()).resize((118, 142), Image.Resampling.LANCZOS)
        self.images["mole"] = ImageTk.PhotoImage(mole)

        result = sheet.crop((485, 540, 1448, 932)).resize((560, 230), Image.Resampling.LANCZOS)
        self.images["result"] = ImageTk.PhotoImage(result)

    def _draw_scene(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, 1040, 700, fill="#dff7ff", outline="")
        self._draw_status_cards()
        self.canvas.create_image(520, 390, image=self.images["field"])
        self._draw_instruction()
        self._draw_footer()
        self._draw_quit_button()

    def _draw_status_cards(self):
        self.timer_value = self._status_card(140, 42, 260, "TIME LEFT", f"00:{self.time_left:02d}", GAME["gold"])
        self.score_value = self._status_card(420, 42, 220, "SCORE", str(self.score), GAME["green"])
        self.best_value = self._status_card(660, 42, 250, "BEST SCORE", str(self.best_score), GAME["blue"])

    def _status_card(self, x, y, w, label, value, value_color):
        self._rounded_rect(x, y, x + w, y + 78, 18, GAME["cream"], GAME["border"], width=3)
        self.canvas.create_text(x + 18, y + 26, text=label, anchor="w", fill=GAME["text"], font=("Helvetica", 13, "bold"))
        return self.canvas.create_text(x + w - 22, y + 51, text=value, anchor="e", fill=value_color, font=("Helvetica", 28, "bold"))

    def _draw_quit_button(self):
        self._rounded_rect(928, 42, 1000, 120, 18, GAME["red"], "#b91c1c", width=2, tags=("quit",))
        self.canvas.create_text(964, 70, text="X", fill="#ffffff", font=("Helvetica", 24, "bold"), tags=("quit",))
        self.canvas.create_text(964, 98, text="QUIT", fill="#ffffff", font=("Helvetica", 12, "bold"), tags=("quit",))
        self.canvas.tag_bind("quit", "<Button-1>", lambda _event: self.close())

    def _draw_instruction(self):
        self._rounded_rect(330, 142, 710, 184, 10, "#c98a45", "#794719", width=3)
        self.canvas.create_text(520, 163, text="Click the moles to earn points!", fill=GAME["text"], font=("Helvetica", 18, "bold"))

    def _draw_footer(self):
        self._rounded_rect(205, 632, 835, 670, 12, GAME["cream2"], "#bd8634", width=2)
        self.canvas.create_text(300, 651, text="+1 for each mole!", fill=GAME["text"], font=("Helvetica", 13, "bold"))
        self.canvas.create_line(445, 640, 445, 662, fill="#d9ad69", width=2)
        self.canvas.create_text(590, 651, text="Moles hide faster as time goes on.", fill=GAME["text"], font=("Helvetica", 13, "bold"))
        self.canvas.create_line(748, 640, 748, 662, fill="#d9ad69", width=2)
        self.canvas.create_text(790, 651, text="Have fun!", fill=GAME["text"], font=("Helvetica", 13, "bold"))

    def _spawn_mole(self):
        if not self.running:
            return
        self.canvas.delete("mole")
        self.active_hole = random.randrange(len(self.holes))
        x, y = self.holes[self.active_hole]
        self.canvas.create_image(x, y - 58, image=self.images["mole"], tags=("mole",))
        self.canvas.tag_bind("mole", "<Button-1>", self._hit_mole)
        delay = max(420, 900 - (self.duration - self.time_left) * 14)
        self.after_ids.append(self.window.after(delay, self._spawn_mole))

    def _hit_mole(self, _event):
        if not self.running:
            return
        self.score += 1
        self.best_score = max(self.best_score, self.score)
        self.canvas.itemconfigure(self.score_value, text=str(self.score))
        self.canvas.itemconfigure(self.best_value, text=str(self.best_score))
        self.canvas.delete("mole")
        self.active_hole = None

    def _tick(self):
        if not self.running:
            return
        self.canvas.itemconfigure(self.timer_value, text=f"00:{self.time_left:02d}")
        if self.time_left <= 0:
            self._finish()
            return
        self.time_left -= 1
        self.after_ids.append(self.window.after(1000, self._tick))

    def _finish(self):
        self.running = False
        self.canvas.delete("mole")
        self._cancel_timers()
        self._result_modal()

    def _result_modal(self):
        self.canvas.create_rectangle(0, 0, 1040, 700, fill="#eef6ff", stipple="gray25", outline="", tags=("result",))
        self.canvas.create_image(520, 360, image=self.images["result"], tags=("result",))
        self._rounded_rect(355, 244, 685, 486, 18, "#ffffff", "#d9def0", width=2, tags=("result_panel", "result"))
        self.canvas.create_text(520, 280, text="Game finished!", fill=GAME["text"], font=("Helvetica", 24, "bold"), tags=("result",))
        self.canvas.create_text(520, 320, text="Your score", fill="#697386", font=("Helvetica", 14), tags=("result",))
        self.canvas.create_text(520, 368, text=str(self.score), fill=GAME["purple"], font=("Helvetica", 42, "bold"), tags=("result",))
        self.canvas.create_text(520, 405, text=f"Great job, {self.player_name}!", fill=GAME["green"], font=("Helvetica", 14, "bold"), tags=("result",))
        self._rounded_rect(385, 436, 510, 470, 9, "#ffffff", "#d7def0", width=2, tags=("play_again", "result"))
        self._rounded_rect(532, 436, 655, 470, 9, GAME["purple"], GAME["purple"], width=2, tags=("submit", "result"))
        self.canvas.create_text(448, 453, text="Play Again", fill="#374151", font=("Helvetica", 12, "bold"), tags=("play_again", "result"))
        self.canvas.create_text(594, 453, text="Submit Score", fill="#ffffff", font=("Helvetica", 12, "bold"), tags=("submit", "result"))
        self.canvas.tag_bind("play_again", "<Button-1>", lambda _event: self.restart())
        self.canvas.tag_bind("submit", "<Button-1>", lambda _event: self.submit_score())

    def restart(self):
        self.time_left = self.duration
        self.score = 0
        self.running = True
        self.submitted = False
        self.after_ids = []
        self._draw_scene()
        self._spawn_mole()
        self._tick()

    def submit_score(self):
        if self.submitted:
            return
        self.submitted = True
        self.canvas.itemconfigure("submit", fill="#c7d2fe")
        self.submit_callback(self.score)

    def _cancel_timers(self):
        for after_id in self.after_ids:
            try:
                self.window.after_cancel(after_id)
            except tk.TclError:
                pass
        self.after_ids = []

    def _rounded_rect(self, x1, y1, x2, y2, radius, fill, outline, width=1, tags=()):
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, fill=fill, outline=outline, width=width, tags=tags)

    def close(self):
        self.running = False
        self._cancel_timers()
        try:
            self.window.destroy()
        except tk.TclError:
            pass
