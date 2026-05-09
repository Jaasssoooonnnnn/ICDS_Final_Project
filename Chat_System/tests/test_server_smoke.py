import json
import os
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

CHAT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = os.environ.get("CHAT_TEST_PYTHON", sys.executable)
PORT = 19112
SIZE_SPEC = 5


def send_json(sock, payload):
    body = json.dumps(payload)
    data = (("0" * SIZE_SPEC + str(len(body)))[-SIZE_SPEC:] + body).encode()
    sock.sendall(data)


def recv_json(sock, timeout=2.0):
    sock.settimeout(timeout)
    size = b""
    while len(size) < SIZE_SPEC:
        chunk = sock.recv(SIZE_SPEC - len(size))
        if not chunk:
            raise ConnectionError("socket closed while reading frame size")
        size += chunk
    length = int(size.decode())
    body = b""
    while len(body) < length:
        chunk = sock.recv(length - len(body))
        if not chunk:
            raise ConnectionError("socket closed while reading frame body")
        body += chunk
    return json.loads(body.decode())


def recv_until(sock, action, timeout=4.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            msg = recv_json(sock, timeout=max(0.1, deadline - time.time()))
        except socket.timeout:
            break
        last = msg
        if msg.get("action") == action:
            return msg
    raise AssertionError(f"Did not receive action {action}; last message was {last}")


def recv_until_predicate(sock, predicate, label, timeout=4.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            msg = recv_json(sock, timeout=max(0.1, deadline - time.time()))
        except socket.timeout:
            break
        last = msg
        if predicate(msg):
            return msg
    raise AssertionError(f"Did not receive {label}; last message was {last}")


class ServerSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = os.environ.copy()
        env["CHAT_HOST"] = "127.0.0.1"
        env["CHAT_PORT"] = str(PORT)
        cls.server = subprocess.Popen(
            [PYTHON, "chat_server.py"],
            cwd=CHAT_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        deadline = time.time() + 8
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.1)
        output = cls.server.stdout.read() if cls.server.stdout else ""
        raise RuntimeError("server did not start\n" + output)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            cls.server.kill()

    def make_client(self, name):
        sock = socket.create_connection(("127.0.0.1", PORT), timeout=2)
        send_json(sock, {"action": "login", "name": name})
        response = recv_until(sock, "login")
        self.assertEqual(response["status"], "ok")
        return sock

    def test_login_exchange_sentiment_and_leaderboard(self):
        suffix = str(int(time.time() * 1000))
        alice_name = "AliceSmoke" + suffix
        bob_name = "BobSmoke" + suffix
        alice = self.make_client(alice_name)
        bob = self.make_client(bob_name)
        try:
            send_json(alice, {"action": "list"})
            listing = recv_until_predicate(
                alice,
                lambda msg: msg.get("action") == "list"
                and alice_name in msg.get("users", [])
                and bob_name in msg.get("users", []),
                "online list containing both smoke users",
            )
            self.assertIn(alice_name, listing["users"])

            send_json(alice, {"action": "exchange", "message": "I love this project"})
            exchange = recv_until(bob, "exchange")
            self.assertEqual(exchange["from"], alice_name)
            self.assertEqual(exchange["sentiment"], "Positive")

            send_json(alice, {"action": "score_submit", "score": 7})
            board = recv_until(alice, "leaderboard")
            self.assertGreaterEqual(board["entries"][0]["score"], 7)
        finally:
            alice.close()
            bob.close()

    def test_multiplayer_tic_tac_toe_state_sync_and_validation(self):
        suffix = str(int(time.time() * 1000))
        alice_name = "AliceTTT" + suffix
        bob_name = "BobTTT" + suffix
        alice = self.make_client(alice_name)
        bob = self.make_client(bob_name)
        try:
            send_json(alice, {"action": "ttt_join", "username": alice_name})
            waiting = recv_until(alice, "ttt_waiting")
            room_id = waiting["room_id"]

            send_json(bob, {"action": "ttt_join", "username": bob_name})
            alice_state = recv_until(alice, "ttt_state")
            bob_state = recv_until(bob, "ttt_state")
            self.assertEqual(alice_state["room_id"], room_id)
            self.assertEqual(alice_state["symbols"][alice_name], "X")
            self.assertEqual(bob_state["symbols"][bob_name], "O")
            self.assertEqual(alice_state["turn"], alice_name)

            send_json(bob, {"action": "ttt_move", "room_id": room_id, "username": bob_name, "row": 0, "col": 0})
            error = recv_until(bob, "ttt_error")
            self.assertIn("not your turn", error["message"])

            moves = [
                (alice, alice_name, 0, 0),
                (bob, bob_name, 1, 0),
                (alice, alice_name, 0, 1),
                (bob, bob_name, 1, 1),
                (alice, alice_name, 0, 2),
            ]
            final_state = None
            for sock, username, row, col in moves:
                send_json(sock, {"action": "ttt_move", "room_id": room_id, "username": username, "row": row, "col": col})
                final_state = recv_until_predicate(
                    alice,
                    lambda msg: msg.get("action") == "ttt_state" and msg.get("room_id") == room_id,
                    "Alice Tic-Tac-Toe state",
                )
                recv_until_predicate(
                    bob,
                    lambda msg: msg.get("action") == "ttt_state" and msg.get("room_id") == room_id,
                    "Bob Tic-Tac-Toe state",
                )

            self.assertEqual(final_state["status"], "finished")
            self.assertEqual(final_state["winner"], alice_name)
            leaderboard = recv_until(alice, "leaderboard")
            self.assertIsInstance(leaderboard["entries"], list)
        finally:
            alice.close()
            bob.close()


if __name__ == "__main__":
    unittest.main()
