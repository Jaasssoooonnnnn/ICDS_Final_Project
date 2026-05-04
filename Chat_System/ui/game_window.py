#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Bright 3x3 Whack-a-Mole game window."""

from __future__ import annotations

import random
import tkinter as tk

GAME = {
    "sky": "#72d7ff",
    "grass": "#82cf39",
    "grass_dark": "#55a628",
    "wood": "#c7833a",
    "wood_dark": "#74451f",
    "cream": "#fff4cf",
    "purple": "#635bff",
    "text": "#3a2414",
    "green": "#22c55e",
    "red": "#ef4444",
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

        self.window = tk.Toplevel(master)
        self.window.title("Whack-a-Mole")
        self.window.geometry("960x640")
        self.window.resizable(False, False)
        self.window.configure(bg=GAME["sky"])
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.transient(master)
        self.window.lift()
        self.window.focus_force()

        self.canvas = tk.Canvas(self.window, width=960, height=640, bg=GAME["sky"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.holes = [
            (230, 295),
            (480, 295),
            (730, 295),
            (230, 420),
            (480, 420),
            (730, 420),
            (230, 545),
            (480, 545),
            (730, 545),
        ]

        self._draw_scene()
        self._spawn_mole()
        self._tick()

    def _draw_scene(self):
        self.canvas.delete("all")
        self._draw_background()
        self._draw_status_cards()
        self._draw_instruction()
        self._draw_holes()
        self._draw_footer()

    def _draw_background(self):
        self.canvas.create_rectangle(0, 0, 960, 640, fill=GAME["sky"], outline="")
        self.canvas.create_oval(-120, 55, 210, 270, fill="#55b764", outline="")
        self.canvas.create_oval(780, 65, 1060, 280, fill="#55b764", outline="")
        for x, y, w in [(110, 82, 70), (190, 60, 92), (710, 72, 84), (790, 54, 110)]:
            self.canvas.create_oval(x, y, x + w, y + w // 2, fill="#ffffff", outline="")
        self.canvas.create_polygon(0, 240, 210, 150, 390, 245, fill="#9ad86a", outline="")
        self.canvas.create_polygon(260, 245, 540, 125, 780, 246, fill="#a8dd72", outline="")
        self.canvas.create_polygon(610, 245, 870, 150, 960, 210, 960, 640, 0, 640, 0, 245, fill=GAME["grass"], outline="")
        for x in range(0, 980, 52):
            self.canvas.create_arc(x, 575, x + 80, 650, start=30, extent=120, outline=GAME["grass_dark"], width=3)
        for x, y in [(80, 530), (860, 500), (70, 360), (890, 340)]:
            self._flower(x, y)

    def _draw_status_cards(self):
        self.timer_value = self._status_card(135, 48, 250, 78, "TIME LEFT", f"00:{self.time_left:02d}", "#f59e0b")
        self.score_value = self._status_card(405, 48, 210, 78, "SCORE", str(self.score), "#16a34a")
        self.best_value = self._status_card(640, 48, 230, 78, "BEST SCORE", str(self.best_score), "#2563eb")
        self.quit_button = self._rounded_rect(875, 43, 940, 126, 18, GAME["red"], "#b91c1c")
        self.canvas.create_text(907, 75, text="X", fill="#ffffff", font=("Helvetica", 24, "bold"), tags=("quit",))
        self.canvas.create_text(907, 103, text="QUIT", fill="#ffffff", font=("Helvetica", 12, "bold"), tags=("quit",))
        self.canvas.tag_bind("quit", "<Button-1>", lambda _event: self.close())

    def _status_card(self, x, y, w, h, label, value, color):
        self._rounded_rect(x, y, x + w, y + h, 20, "#fff8dc", "#84511f", width=3)
        self.canvas.create_text(x + 18, y + 24, text=label, anchor="w", fill=GAME["text"], font=("Helvetica", 13, "bold"))
        return self.canvas.create_text(x + w - 22, y + 50, text=value, anchor="e", fill=color, font=("Helvetica", 27, "bold"))

    def _draw_instruction(self):
        self._rounded_rect(300, 150, 660, 192, 10, GAME["wood"], GAME["wood_dark"], width=3)
        self.canvas.create_text(480, 171, text="Click the moles to earn points!", fill=GAME["text"], font=("Helvetica", 18, "bold"))

    def _draw_holes(self):
        for x, y in self.holes:
            self._draw_hole(x, y)

    def _draw_hole(self, x, y):
        self.canvas.create_oval(x - 78, y - 28, x + 78, y + 30, fill="#7a4c36", outline="#593423", width=4, tags=("hole",))
        self.canvas.create_oval(x - 60, y - 17, x + 60, y + 18, fill="#2b1b16", outline="", tags=("hole",))
        self.canvas.create_arc(x - 78, y - 28, x + 78, y + 30, start=0, extent=180, outline="#b78652", width=10, tags=("hole",))

    def _draw_footer(self):
        self._rounded_rect(165, 590, 795, 625, 12, GAME["cream"], "#b7792b", width=2)
        self.canvas.create_text(265, 607, text="+1 for each mole!", fill=GAME["text"], font=("Helvetica", 13, "bold"))
        self.canvas.create_line(405, 596, 405, 620, fill="#d9ad69", width=2)
        self.canvas.create_text(545, 607, text="Moles hide faster as time goes on.", fill=GAME["text"], font=("Helvetica", 13, "bold"))
        self.canvas.create_line(705, 596, 705, 620, fill="#d9ad69", width=2)
        self.canvas.create_text(750, 607, text="Have fun!", fill=GAME["text"], font=("Helvetica", 13, "bold"))

    def _flower(self, x, y):
        for dx, dy in [(-7, 0), (7, 0), (0, -7), (0, 7)]:
            self.canvas.create_oval(x + dx - 5, y + dy - 5, x + dx + 5, y + dy + 5, fill="#ffffff", outline="")
        self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#facc15", outline="")

    def _spawn_mole(self):
        if not self.running:
            return
        self.canvas.delete("mole")
        self.active_hole = random.randrange(len(self.holes))
        x, y = self.holes[self.active_hole]
        self._draw_mole(x, y - 18)
        delay = max(420, 900 - (self.duration - self.time_left) * 14)
        self.after_ids.append(self.window.after(delay, self._spawn_mole))

    def _draw_mole(self, x, y):
        self.canvas.create_oval(x - 44, y - 64, x + 44, y + 32, fill="#9b6a45", outline="#603b22", width=4, tags=("mole",))
        self.canvas.create_oval(x - 30, y - 42, x - 14, y - 26, fill="#111827", outline="", tags=("mole",))
        self.canvas.create_oval(x + 14, y - 42, x + 30, y - 26, fill="#111827", outline="", tags=("mole",))
        self.canvas.create_oval(x - 11, y - 20, x + 11, y + 2, fill="#f3a0a8", outline="", tags=("mole",))
        self.canvas.create_arc(x - 24, y - 5, x + 24, y + 25, start=200, extent=140, style="arc", width=4, outline="#2b1b16", tags=("mole",))
        self.canvas.create_polygon(x - 24, y - 64, x - 6, y - 92, x + 10, y - 64, fill="#facc15", outline="#9a5b12", width=2, tags=("mole",))
        self.canvas.tag_bind("mole", "<Button-1>", self._hit_mole)

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
        for after_id in self.after_ids:
            try:
                self.window.after_cancel(after_id)
            except tk.TclError:
                pass
        self._result_modal()

    def _result_modal(self):
        self.canvas.create_rectangle(0, 0, 960, 640, fill="#eff7ff", stipple="gray25", outline="", tags=("result",))
        self._rounded_rect(300, 190, 660, 430, 20, "#ffffff", "#d7def0", width=2, tags=("result",))
        self.canvas.create_oval(335, 220, 415, 300, fill="#f2efff", outline="", tags=("result",))
        self.canvas.create_text(375, 260, text="*", fill=GAME["purple"], font=("Helvetica", 42, "bold"), tags=("result",))
        self.canvas.create_text(480, 232, text="Game finished!", fill=GAME["text"], font=("Helvetica", 21, "bold"), tags=("result",))
        self.canvas.create_text(480, 272, text="Your score", fill="#6b7280", font=("Helvetica", 13), tags=("result",))
        self.canvas.create_text(480, 315, text=str(self.score), fill=GAME["purple"], font=("Helvetica", 38, "bold"), tags=("result",))
        self.canvas.create_text(480, 350, text=f"Great job, {self.player_name}!", fill=GAME["green"], font=("Helvetica", 13, "bold"), tags=("result",))
        self.play_again_rect = self._rounded_rect(330, 382, 470, 417, 10, "#ffffff", "#d7def0", width=2, tags=("play_again", "result"))
        self.submit_rect = self._rounded_rect(490, 382, 630, 417, 10, GAME["purple"], GAME["purple"], width=2, tags=("submit", "result"))
        self.canvas.create_text(400, 399, text="Play Again", fill="#374151", font=("Helvetica", 12, "bold"), tags=("play_again", "result"))
        self.canvas.create_text(560, 399, text="Submit Score", fill="#ffffff", font=("Helvetica", 12, "bold"), tags=("submit", "result"))
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
        for after_id in self.after_ids:
            try:
                self.window.after_cancel(after_id)
            except tk.TclError:
                pass
        try:
            self.window.destroy()
        except tk.TclError:
            pass
