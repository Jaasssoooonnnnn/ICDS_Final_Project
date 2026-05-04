"""Manual external API smoke test for the ICDS chat server.

This script is intentionally not named test_*.py because it calls Gemini and
Pollinations.ai. Run it before presentation when network/API quota is available:

    /opt/anaconda3/envs/chat_system/bin/python Chat_System/tests/external_smoke.py
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

CHAT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/opt/anaconda3/envs/chat_system/bin/python"
PORT = int(os.getenv("ICDS_EXTERNAL_SMOKE_PORT", "19114"))
SIZE_SPEC = 5


def send_json(sock, payload):
    body = json.dumps(payload)
    frame = (("0" * SIZE_SPEC + str(len(body)))[-SIZE_SPEC:] + body).encode()
    sock.sendall(frame)


def recv_json(sock, timeout=8.0):
    sock.settimeout(timeout)
    size = b""
    while len(size) < SIZE_SPEC:
        chunk = sock.recv(SIZE_SPEC - len(size))
        if not chunk:
            raise ConnectionError("socket closed while reading frame size")
        size += chunk
    body = b""
    length = int(size.decode())
    while len(body) < length:
        chunk = sock.recv(length - len(body))
        if not chunk:
            raise ConnectionError("socket closed while reading frame body")
        body += chunk
    return json.loads(body.decode())


def recv_until(sock, predicate, label, timeout=60.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            msg = recv_json(sock, timeout=max(0.2, deadline - time.time()))
        except socket.timeout:
            break
        last = msg
        if msg.get("action") == "error":
            raise RuntimeError("server error: " + msg.get("error", "unknown"))
        if predicate(msg):
            return msg
    raise TimeoutError(f"did not receive {label}; last message was {last}")


def login(name):
    sock = socket.create_connection(("127.0.0.1", PORT), timeout=4)
    send_json(sock, {"action": "login", "name": name})
    response = recv_until(sock, lambda msg: msg.get("action") == "login", "login")
    if response.get("status") != "ok":
        raise RuntimeError(f"login failed for {name}: {response}")
    return sock


def main():
    env = os.environ.copy()
    env["CHAT_HOST"] = "127.0.0.1"
    env["CHAT_PORT"] = str(PORT)
    server = subprocess.Popen(
        [PYTHON, "chat_server.py"],
        cwd=CHAT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("server did not start")

        suffix = str(int(time.time() * 1000))
        alice_name = "ApiAlice" + suffix
        bob_name = "ApiBob" + suffix
        alice = login(alice_name)
        bob = login(bob_name)
        try:
            send_json(alice, {"action": "exchange", "message": "We need slides, testing notes, and a demo plan."})
            recv_until(bob, lambda msg: msg.get("action") == "exchange", "peer exchange")

            send_json(alice, {"action": "exchange", "message": "@bot Give one short action item."})
            bot = recv_until(bob, lambda msg: msg.get("action") == "bot_response", "Gemini bot response")
            if bot.get("status") != "ok" or not bot.get("message"):
                raise RuntimeError("bot_response failed: " + json.dumps(bot))

            send_json(alice, {"action": "summary_request"})
            summary = recv_until(alice, lambda msg: msg.get("action") == "summary_response", "Gemini summary")
            if summary.get("status") != "ok" or not summary.get("message"):
                raise RuntimeError("summary_response failed: " + json.dumps(summary))

            send_json(alice, {"action": "keywords_request"})
            keywords = recv_until(alice, lambda msg: msg.get("action") == "keywords_response", "Gemini keywords")
            if keywords.get("status") != "ok" or not keywords.get("keywords"):
                raise RuntimeError("keywords_response failed: " + json.dumps(keywords))

            send_json(alice, {"action": "image_request", "prompt": "small purple ICDS chat bubble smoke test"})
            image = recv_until(bob, lambda msg: msg.get("action") == "image_response", "Pollinations image")
            if image.get("status") != "ok" or not Path(image.get("path", "")).exists():
                raise RuntimeError("image_response failed: " + json.dumps(image))

            print("external smoke ok")
            print("bot chars:", len(bot["message"]))
            print("summary chars:", len(summary["message"]))
            print("keywords:", ", ".join(keywords["keywords"]))
            print("image path:", image["path"])
        finally:
            alice.close()
            bob.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
        if server.returncode not in (0, -15, None):
            output = server.stdout.read() if server.stdout else ""
            print(output, file=sys.stderr)


if __name__ == "__main__":
    main()
