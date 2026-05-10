"""Create screenshots for manual UI comparison against reference mockups."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageGrab

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from GUI import GUI  # noqa: E402
from chat_utils import S_LOGGEDIN  # noqa: E402
from ui.tic_tac_toe_window import TicTacToeWindow  # noqa: E402
from ui.game_window import WhackAMoleWindow  # noqa: E402


class FakeSM:
    def __init__(self):
        self.state = S_LOGGEDIN

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.name = name


def capture_window(window, path):
    window.update_idletasks()
    window.update()
    window.lift()
    try:
        window.attributes("-topmost", True)
    except Exception:
        pass
    time.sleep(0.6)
    x = window.winfo_rootx()
    y = window.winfo_rooty()
    w = window.winfo_width()
    h = window.winfo_height()
    full_path = path.with_name(path.stem + "_full.png")
    try:
        subprocess.run(["screencapture", "-x", str(full_path)], check=True)
        full = Image.open(full_path)
        scale = full.width / max(1, window.winfo_screenwidth())
        crop = (
            int(x * scale),
            int(y * scale),
            int((x + w) * scale),
            int((y + h) * scale),
        )
        full.crop(crop).save(path)
    except Exception:
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(path)
    try:
        window.attributes("-topmost", False)
    except Exception:
        pass


def main():
    out_dir = Path("tmp/ui_refactor")
    out_dir.mkdir(parents=True, exist_ok=True)
    sent = []
    gui = GUI(lambda msg: sent.append(json.loads(msg)), lambda: "", FakeSM(), socket.socket())
    gui.show_splash(start_mainloop=False, auto_finish=False)
    gui.splash_window.update()
    capture_window(gui.splash_window, out_dir / "splash_refactor.png")
    gui.splash_frame.destroy()
    gui.Window.overrideredirect(False)
    gui.splash_window = None
    gui.splash_frame = None

    gui.name = "Arjun Mehta"
    gui.layout("Arjun Mehta")
    gui.Window.geometry("1560x900+60+60")
    gui._set_status("Connected", "#22c55e")
    gui._update_online_users(["Priya Sharma", "Rohan Verma", "Nikita Singh", "Karan Gupta", "Sneha Iyer", "Meera Joshi"])
    gui.add_message("Priya Sharma", "Great work on the prototype! The new GUI looks clean and modern.", "Positive", False)
    gui.add_message("Rohan Verma", "I integrated the sockets module. Real-time updates are working as expected.", "Positive", False)
    gui.add_message("Nikita Singh", "I found a bug when the leaderboard loads slowly on weak networks.", "Negative", False)
    gui.add_message("Arjun Mehta", "@bot what are the action items?", "Neutral", True)
    gui.add_bot_card("Here are the action items: finish UI polish, test the leaderboard, and rehearse the demo.", "ICDS Bot")
    gui._handle_ai_response("summary_response", {"message": "The team reviewed UI polish, socket behavior, and leaderboard testing."})
    gui._handle_ai_response("keywords_response", {"keywords": ["GUI", "sockets", "leaderboard", "chatbot", "testing"]})
    gui._update_leaderboard({"entries": [{"player": "Priya Sharma", "score": 48}, {"player": "Arjun Mehta", "score": 23}, {"player": "Rohan Verma", "score": 21}]})
    gui.Window.update()
    gui.chat_scroll._parent_canvas.yview_moveto(0.0)
    gui.Window.update()
    capture_window(gui.Window, out_dir / "main_chat_refactor.png")

    game = WhackAMoleWindow(gui.Window, "Arjun Mehta", lambda score: sent.append({"score": score}), duration=5)
    game.window.geometry("1040x700+120+120")
    game.canvas.delete("mole")
    x, y = game.holes[3]
    game.canvas.create_image(x, y, image=game.images["mole"], anchor="s", tags=("mole",))
    capture_window(game.window, out_dir / "game_live_refactor.png")
    game.score = 23
    game._finish()
    capture_window(game.window, out_dir / "game_result_refactor.png")
    game.close()

    ttt = TicTacToeWindow(gui.Window, "Arjun Mehta", lambda payload: sent.append(payload))
    ttt.window.geometry("430x640+140+80")
    ttt.handle_message(
        {
            "action": "ttt_state",
            "room_id": "ttt_demo",
            "players": ["Arjun Mehta", "Priya Sharma"],
            "symbols": {"Arjun Mehta": "X", "Priya Sharma": "O"},
            "board": [["X", "O", ""], ["", "X", ""], ["O", "", ""]],
            "turn": "Arjun Mehta",
            "status": "playing",
            "winner": None,
            "message": "Arjun Mehta's turn.",
        }
    )
    capture_window(ttt.window, out_dir / "tic_tac_toe_refactor.png")
    ttt.close()
    gui.close()
    print(out_dir / "splash_refactor.png")
    print(out_dir / "main_chat_refactor.png")
    print(out_dir / "game_live_refactor.png")
    print(out_dir / "game_result_refactor.png")
    print(out_dir / "tic_tac_toe_refactor.png")


if __name__ == "__main__":
    main()
