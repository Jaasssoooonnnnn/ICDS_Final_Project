"""
Socket chat server for the ICDS final project.

The original JSON-over-socket framing is preserved in chat_utils.py. This
server extends the old switchboard with explicit project actions for LLM chat,
Pollinations image generation, local sentiment, and the game leaderboard.
"""

from __future__ import annotations

import json
import pickle as pkl
import select
import socket
import time
from pathlib import Path

import chat_group as grp
import indexer
from chat_utils import SERVER, myrecv, mysend, text_proc
from protocol import (
    ACTION_BOT_REQUEST,
    ACTION_BOT_RESPONSE,
    ACTION_CONNECT,
    ACTION_DISCONNECT,
    ACTION_ERROR,
    ACTION_EXCHANGE,
    ACTION_IMAGE_REQUEST,
    ACTION_IMAGE_RESPONSE,
    ACTION_KEYWORDS_REQUEST,
    ACTION_KEYWORDS_RESPONSE,
    ACTION_LEADERBOARD,
    ACTION_LIST,
    ACTION_LOGIN,
    ACTION_POEM,
    ACTION_SCORE_SUBMIT,
    ACTION_SEARCH,
    ACTION_SUMMARY_REQUEST,
    ACTION_SUMMARY_RESPONSE,
    ACTION_TTT_ERROR,
    ACTION_TTT_JOIN,
    ACTION_TTT_LEAVE,
    ACTION_TTT_MOVE,
    ACTION_TTT_RESTART,
    ACTION_TTT_STATE,
    ACTION_TTT_WAITING,
    ACTION_TIME,
    BOT_NAME,
    require_fields,
)
from services.chat_history import ChatHistory
from services.leaderboard import Leaderboard
from services.llm_client import LLMClient
from services.pollinations_client import PollinationsClient
from services.sentiment import analyze_sentiment
from services.tic_tac_toe import TicTacToeRoom

BASE_DIR = Path(__file__).resolve().parent


class Server:
    def __init__(self):
        self.new_clients = []
        self.logged_name2sock = {}
        self.logged_sock2name = {}
        self.all_sockets = []
        self.group = grp.Group()
        self.indices = {}
        self.history = ChatHistory()
        self.leaderboard = Leaderboard()
        self.pollinations = PollinationsClient()
        self._llm = None
        self.bot_personality = "concise helpful teammate"
        self.ttt_rooms = {}
        self.ttt_waiting_room_id = None
        self.ttt_counter = 0
        self.ttt_scores_awarded = set()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        self.sonnet = indexer.PIndex(str(BASE_DIR / "AllSonnets.txt"))

    @property
    def llm(self):
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    def send_json(self, sock, payload):
        mysend(sock, json.dumps(payload))

    def broadcast(self, payload, include_sender=True, sender_sock=None):
        failed = []
        for sock in list(self.logged_sock2name.keys()):
            if not include_sender and sock is sender_sock:
                continue
            try:
                self.send_json(sock, payload)
            except OSError:
                failed.append(sock)
        for sock in failed:
            self.drop_logged_client(sock)

    def broadcast_to_ttt_room(self, room, payload):
        for player in room.players:
            sock = self.logged_name2sock.get(player)
            if sock is not None:
                try:
                    self.send_json(sock, payload)
                except OSError:
                    self.drop_logged_client(sock)

    def broadcast_system_message(self, message):
        payload = {
            "action": ACTION_BOT_RESPONSE,
            "status": "ok",
            "from": BOT_NAME,
            "sender": BOT_NAME,
            "message": message,
            "timestamp": time.strftime("%H:%M", time.localtime()),
        }
        self.broadcast(payload)

    def online_payload(self):
        users = sorted(self.logged_name2sock.keys())
        return {
            "action": ACTION_LIST,
            "users": users,
            "results": self.group.list_all(),
            "online_count": len(users),
        }

    def broadcast_online_list(self):
        if self.logged_sock2name:
            self.broadcast(self.online_payload())

    def error_payload(self, message):
        return {"action": ACTION_ERROR, "status": "error", "error": str(message)}

    def new_client(self, sock):
        print("new client...")
        sock.setblocking(False)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        try:
            raw = myrecv(sock)
        except OSError:
            self.drop_new_client(sock)
            return
        if not raw:
            self.drop_new_client(sock)
            return
        try:
            msg = json.loads(raw)
            require_fields(msg, ["action", "name"])
            if msg["action"] != ACTION_LOGIN:
                raise ValueError("Expected login action")
            name = msg["name"].strip()
            if not name:
                raise ValueError("Login name cannot be empty")
            if self.group.is_member(name):
                self.send_json(sock, {"action": ACTION_LOGIN, "status": "duplicate"})
                print(name + " duplicate login attempt")
                return

            self.new_clients.remove(sock)
            self.logged_name2sock[name] = sock
            self.logged_sock2name[sock] = name
            self.indices[name] = self.load_index(name)
            self.group.join(name)
            print(name + " logged in")
            self.send_json(sock, {"action": ACTION_LOGIN, "status": "ok", "name": name})
            self.broadcast_online_list()
        except Exception as exc:
            self.send_json(sock, self.error_payload(exc))
            self.drop_new_client(sock)

    def load_index(self, name):
        index_path = BASE_DIR / f"{name}.idx"
        try:
            with index_path.open("rb") as handle:
                return pkl.load(handle)
        except (IOError, EOFError, pkl.UnpicklingError):
            return indexer.Index(str(BASE_DIR / name))

    def save_index(self, name):
        index = self.indices.get(name)
        if index is None:
            return
        with (BASE_DIR / f"{name}.idx").open("wb") as handle:
            pkl.dump(index, handle)

    def drop_new_client(self, sock):
        if sock in self.new_clients:
            self.new_clients.remove(sock)
        if sock in self.all_sockets:
            self.all_sockets.remove(sock)
        sock.close()

    def drop_logged_client(self, sock):
        name = self.logged_sock2name.pop(sock, None)
        if name is not None:
            self.save_index(name)
            self.indices.pop(name, None)
            self.logged_name2sock.pop(name, None)
            self.group.leave(name)
            self.handle_ttt_disconnect(name)
        if sock in self.all_sockets:
            self.all_sockets.remove(sock)
        try:
            sock.close()
        except OSError:
            pass

    def logout(self, sock):
        name = self.logged_sock2name.get(sock)
        if name is None:
            self.drop_new_client(sock)
            return
        self.handle_ttt_disconnect(name)
        print(name + " logged out")
        self.drop_logged_client(sock)
        self.broadcast_online_list()

    def next_ttt_room_id(self):
        self.ttt_counter += 1
        return f"ttt_{self.ttt_counter}"

    def ttt_error(self, from_sock, message, room_id=None):
        self.send_json(
            from_sock,
            {
                "action": ACTION_TTT_ERROR,
                "type": ACTION_TTT_ERROR,
                "room_id": room_id,
                "message": str(message),
            },
        )

    def handle_ttt_join(self, from_sock, msg):
        username = msg.get("username") or self.logged_sock2name[from_sock]
        if username != self.logged_sock2name[from_sock]:
            raise ValueError("Tic-Tac-Toe username does not match the logged-in client.")

        for existing in self.ttt_rooms.values():
            if username in existing.players and existing.status in {"waiting", "playing", "finished", "draw"}:
                if existing.status == "waiting":
                    self.send_json(
                        from_sock,
                        {
                            "action": ACTION_TTT_WAITING,
                            "type": ACTION_TTT_WAITING,
                            "room_id": existing.room_id,
                            "message": "Waiting for another player...",
                        },
                    )
                else:
                    self.send_json(from_sock, existing.to_state_message())
                return

        room = None
        waiting_candidates = []
        if self.ttt_waiting_room_id:
            waiting_candidates.append(self.ttt_rooms.get(self.ttt_waiting_room_id))
        waiting_candidates.extend(
            candidate
            for candidate in self.ttt_rooms.values()
            if candidate and candidate.room_id != self.ttt_waiting_room_id
        )
        for candidate in waiting_candidates:
            if candidate and candidate.status == "waiting" and username not in candidate.players:
                room = candidate
                break

        if room is None:
            room_id = self.next_ttt_room_id()
            room = TicTacToeRoom(room_id)
            self.ttt_rooms[room_id] = room
            self.ttt_waiting_room_id = room_id

        symbol = room.add_player(username)
        self.broadcast_system_message(f"{username} joined Tic-Tac-Toe room {room.room_id} as {symbol}.")

        if room.status == "waiting":
            self.send_json(
                from_sock,
                {
                    "action": ACTION_TTT_WAITING,
                    "type": ACTION_TTT_WAITING,
                    "room_id": room.room_id,
                    "message": "Waiting for another player...",
                },
            )
        else:
            self.ttt_waiting_room_id = None
            self.broadcast_system_message("Tic-Tac-Toe game started.")
            self.broadcast_to_ttt_room(room, room.to_state_message())

    def handle_ttt_move(self, from_sock, msg):
        require_fields(msg, ["room_id", "row", "col"])
        username = msg.get("username") or self.logged_sock2name[from_sock]
        room_id = msg["room_id"]
        room = self.ttt_rooms.get(room_id)
        if room is None:
            raise ValueError("Tic-Tac-Toe room does not exist.")
        room.make_move(username, int(msg["row"]), int(msg["col"]))
        state = room.to_state_message()
        self.broadcast_to_ttt_room(room, state)
        self.handle_ttt_score(room)
        if room.status == "finished":
            self.broadcast_system_message(f"{room.winner} won the Tic-Tac-Toe game.")
        elif room.status == "draw":
            self.broadcast_system_message("The Tic-Tac-Toe game ended in a draw.")

    def handle_ttt_restart(self, from_sock, msg):
        require_fields(msg, ["room_id"])
        username = msg.get("username") or self.logged_sock2name[from_sock]
        room = self.ttt_rooms.get(msg["room_id"])
        if room is None:
            raise ValueError("Tic-Tac-Toe room does not exist.")
        restarted = room.vote_restart(username)
        if restarted:
            self.ttt_scores_awarded.discard(room.room_id)
            self.broadcast_system_message(f"Tic-Tac-Toe room {room.room_id} restarted.")
            self.broadcast_to_ttt_room(room, room.to_state_message())
        else:
            payload = room.to_state_message()
            payload["message"] = f"{username} requested a restart. Waiting for the other player."
            self.broadcast_to_ttt_room(room, payload)

    def handle_ttt_leave(self, from_sock, msg):
        username = msg.get("username") or self.logged_sock2name[from_sock]
        room_id = msg.get("room_id")
        if not room_id:
            return
        room = self.ttt_rooms.get(room_id)
        if room is None:
            return
        peers = [player for player in room.players if player != username]
        room.remove_player(username)
        if self.ttt_waiting_room_id == room_id:
            self.ttt_waiting_room_id = None
        for peer in peers:
            sock = self.logged_name2sock.get(peer)
            if sock is not None:
                try:
                    self.send_json(sock, room.to_state_message())
                except OSError:
                    self.drop_logged_client(sock)
        self.broadcast_system_message(f"{username} left Tic-Tac-Toe room {room_id}.")

    def handle_ttt_disconnect(self, username):
        for room in list(self.ttt_rooms.values()):
            if username in room.players:
                fake_msg = {"room_id": room.room_id, "username": username}
                sock = self.logged_name2sock.get(username)
                if sock is not None:
                    self.handle_ttt_leave(sock, fake_msg)

    def handle_ttt_score(self, room):
        if room.status not in {"finished", "draw"} or room.room_id in self.ttt_scores_awarded:
            return
        self.ttt_scores_awarded.add(room.room_id)
        if room.status == "draw":
            for player in room.players:
                self.leaderboard.submit(player, 30)
        else:
            for player in room.players:
                self.leaderboard.submit(player, 100 if player == room.winner else 10)
        self.broadcast({"action": ACTION_LEADERBOARD, "entries": self.leaderboard.top()})

    def handle_exchange(self, from_sock, msg):
        require_fields(msg, ["message"])
        from_name = self.logged_sock2name[from_sock]
        message = msg["message"].strip()
        if not message:
            raise ValueError("Message cannot be empty")
        lowered = message.lower()
        if lowered.startswith("/aipic:"):
            self.handle_image(from_sock, {"action": ACTION_IMAGE_REQUEST, "prompt": message})
            return
        if lowered == "/summary":
            self.handle_summary(from_sock)
            return
        if lowered == "/keywords":
            self.handle_keywords(from_sock)
            return
        if lowered.startswith("/personality:") or lowered.startswith("/botpersona:"):
            self.handle_personality(from_sock, message)
            return
        if lowered.startswith("/bot"):
            prompt = message[4:].strip() or "Please help with this discussion."
            self.handle_bot(prompt, from_sock, broadcast=False)
            return

        sentiment = analyze_sentiment(message)
        record = self.history.add(from_name, message, sentiment)
        said = text_proc(message, from_name)
        for name, index in self.indices.items():
            index.add_msg_and_index(said)

        payload = {
            "action": ACTION_EXCHANGE,
            "from": from_name,
            "sender": from_name,
            "message": message,
            "timestamp": record.timestamp,
            "sentiment": sentiment,
            "insights": self.history.insights(),
        }
        self.broadcast(payload, include_sender=False, sender_sock=from_sock)

        if lowered.startswith("@bot"):
            prompt = message[4:].strip() or "Please help with this discussion."
            self.handle_bot(prompt, from_sock, broadcast=True)

    def handle_bot(self, prompt, from_sock, broadcast=False):
        from_name = self.logged_sock2name[from_sock]
        try:
            reply = self.llm.bot_reply(prompt, self.history.context(), self.bot_personality)
            record = self.history.add(BOT_NAME, reply, kind="bot")
            payload = {
                "action": ACTION_BOT_RESPONSE,
                "status": "ok",
                "from": BOT_NAME,
                "sender": BOT_NAME,
                "message": reply,
                "timestamp": record.timestamp,
                "requester": from_name,
            }
        except Exception as exc:
            payload = {
                "action": ACTION_BOT_RESPONSE,
                "status": "error",
                "from": BOT_NAME,
                "sender": BOT_NAME,
                "message": f"AI error: {exc}",
                "error": str(exc),
                "timestamp": time.strftime("%H:%M", time.localtime()),
                "requester": from_name,
            }
        if broadcast:
            self.broadcast(payload)
        else:
            self.send_json(from_sock, payload)

    def handle_personality(self, from_sock, msg):
        separator = ":" if ":" in msg else " "
        personality = msg.split(separator, 1)[1].strip()
        if not personality:
            raise ValueError("Bot personality is required after /personality:")
        if len(personality) > 180:
            raise ValueError("Bot personality must be 180 characters or fewer")
        self.bot_personality = personality
        from_name = self.logged_sock2name[from_sock]
        payload = {
            "action": ACTION_BOT_RESPONSE,
            "status": "ok",
            "from": BOT_NAME,
            "sender": BOT_NAME,
            "message": f"ICDS Bot personality updated to: {personality}",
            "timestamp": time.strftime("%H:%M", time.localtime()),
            "requester": from_name,
        }
        self.broadcast(payload)

    def handle_summary(self, from_sock):
        try:
            summary = self.llm.summarize(self.history.context())
            record = self.history.add(BOT_NAME, summary, kind="summary")
            payload = {
                "action": ACTION_SUMMARY_RESPONSE,
                "status": "ok",
                "from": BOT_NAME,
                "message": summary,
                "timestamp": record.timestamp,
            }
        except Exception as exc:
            payload = {
                "action": ACTION_SUMMARY_RESPONSE,
                "status": "error",
                "from": BOT_NAME,
                "message": f"AI summary error: {exc}",
                "error": str(exc),
                "timestamp": time.strftime("%H:%M", time.localtime()),
            }
        self.send_json(from_sock, payload)

    def handle_keywords(self, from_sock):
        try:
            keywords = self.llm.keywords(self.history.context())
            text = ", ".join(keywords)
            record = self.history.add(BOT_NAME, text, kind="keywords")
            payload = {
                "action": ACTION_KEYWORDS_RESPONSE,
                "status": "ok",
                "from": BOT_NAME,
                "message": text,
                "keywords": keywords,
                "timestamp": record.timestamp,
            }
        except Exception as exc:
            payload = {
                "action": ACTION_KEYWORDS_RESPONSE,
                "status": "error",
                "from": BOT_NAME,
                "message": f"AI keywords error: {exc}",
                "error": str(exc),
                "timestamp": time.strftime("%H:%M", time.localtime()),
            }
        self.send_json(from_sock, payload)

    def handle_image(self, from_sock, msg):
        prompt = (msg.get("prompt") or msg.get("message") or "").strip()
        if prompt.lower().startswith("/aipic:"):
            prompt = prompt.split(":", 1)[1].strip()
        if not prompt:
            raise ValueError("Image prompt is required after /aipic:")
        try:
            image = self.pollinations.generate(prompt)
            from_name = self.logged_sock2name[from_sock]
            record = self.history.add(from_name, "/aipic: " + prompt, kind="image")
            payload = {
                "action": ACTION_IMAGE_RESPONSE,
                "status": "ok",
                "from": from_name,
                "sender": from_name,
                "prompt": image["prompt"],
                "url": image["url"],
                "path": image["path"],
                "timestamp": record.timestamp,
            }
        except Exception as exc:
            payload = {
                "action": ACTION_IMAGE_RESPONSE,
                "status": "error",
                "from": "Pollinations.ai",
                "message": f"Pollinations error: {exc}",
                "error": str(exc),
                "timestamp": time.strftime("%H:%M", time.localtime()),
            }
        self.broadcast(payload)

    def handle_msg(self, from_sock):
        try:
            raw = myrecv(from_sock)
        except OSError:
            self.logout(from_sock)
            return
        if not raw:
            self.logout(from_sock)
            return

        try:
            msg = json.loads(raw)
            action = msg.get("action") or msg.get("type")
            if not action:
                raise ValueError("Malformed payload; missing action")
            if action == ACTION_CONNECT:
                self.handle_connect(from_sock, msg)
            elif action == ACTION_EXCHANGE:
                self.handle_exchange(from_sock, msg)
            elif action == ACTION_LIST:
                self.send_json(from_sock, self.online_payload())
            elif action == ACTION_POEM:
                poem = self.sonnet.get_poem(int(msg["target"]))
                self.send_json(from_sock, {"action": ACTION_POEM, "results": "\n".join(poem).strip()})
            elif action == ACTION_TIME:
                ctime = time.strftime("%d.%m.%y,%H:%M", time.localtime())
                self.send_json(from_sock, {"action": ACTION_TIME, "results": ctime})
            elif action == ACTION_SEARCH:
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                search_rslt = "\n".join([x[-1] for x in self.indices[from_name].search(term)])
                self.send_json(from_sock, {"action": ACTION_SEARCH, "results": search_rslt})
            elif action == ACTION_DISCONNECT:
                self.handle_disconnect(from_sock)
            elif action == ACTION_BOT_REQUEST:
                self.handle_bot(msg.get("message", ""), from_sock, broadcast=msg.get("scope") == "group")
            elif action == ACTION_SUMMARY_REQUEST:
                self.handle_summary(from_sock)
            elif action == ACTION_KEYWORDS_REQUEST:
                self.handle_keywords(from_sock)
            elif action == ACTION_IMAGE_REQUEST:
                self.handle_image(from_sock, msg)
            elif action == ACTION_SCORE_SUBMIT:
                require_fields(msg, ["score"])
                player = msg.get("player") or self.logged_sock2name[from_sock]
                ranking = self.leaderboard.submit(player, msg["score"])
                self.broadcast({"action": ACTION_LEADERBOARD, "entries": ranking})
            elif action == ACTION_LEADERBOARD:
                self.send_json(from_sock, {"action": ACTION_LEADERBOARD, "entries": self.leaderboard.top()})
            elif action == ACTION_TTT_JOIN:
                self.handle_ttt_join(from_sock, msg)
            elif action == ACTION_TTT_MOVE:
                self.handle_ttt_move(from_sock, msg)
            elif action == ACTION_TTT_RESTART:
                self.handle_ttt_restart(from_sock, msg)
            elif action == ACTION_TTT_LEAVE:
                self.handle_ttt_leave(from_sock, msg)
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as exc:
            try:
                action = msg.get("action") or msg.get("type")
                room_id = msg.get("room_id")
            except Exception:
                action = None
                room_id = None
            if action in {ACTION_TTT_JOIN, ACTION_TTT_MOVE, ACTION_TTT_RESTART, ACTION_TTT_LEAVE}:
                self.ttt_error(from_sock, exc, room_id=room_id)
            else:
                self.send_json(from_sock, self.error_payload(exc))

    def handle_connect(self, from_sock, msg):
        require_fields(msg, ["target"])
        to_name = msg["target"]
        from_name = self.logged_sock2name[from_sock]
        if to_name == from_name:
            response = {"action": ACTION_CONNECT, "status": "self"}
        elif self.group.is_member(to_name):
            self.group.connect(from_name, to_name)
            response = {"action": ACTION_CONNECT, "status": "success"}
            for peer in self.group.list_me(from_name)[1:]:
                peer_sock = self.logged_name2sock[peer]
                self.send_json(peer_sock, {"action": ACTION_CONNECT, "status": "request", "from": from_name})
        else:
            response = {"action": ACTION_CONNECT, "status": "no-user"}
        self.send_json(from_sock, response)

    def handle_disconnect(self, from_sock):
        from_name = self.logged_sock2name[from_sock]
        peers = self.group.list_me(from_name)
        self.group.disconnect(from_name)
        peers.remove(from_name)
        if len(peers) == 1:
            peer = peers.pop()
            self.send_json(self.logged_name2sock[peer], {"action": ACTION_DISCONNECT})

    def run(self):
        print("starting server on " + repr(SERVER) + "...")
        while True:
            read, write, error = select.select(self.all_sockets, [], [])
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            if self.server in read:
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
