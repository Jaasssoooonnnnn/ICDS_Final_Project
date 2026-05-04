import argparse
import socket
import sys

import client_state_machine as csm
from chat_utils import CHAT_PORT, SERVER, myrecv, mysend


class GUIClient:
    def __init__(self, args):
        self.args = args
        self.socket = None
        self.closed = False

    def init_chat(self):
        try:
            from GUI import GUI
        except ModuleNotFoundError as exc:
            if exc.name == "_tkinter":
                sys.exit(
                    "This Python does not include Tkinter. On macOS, try:\n"
                    "/usr/bin/python3 chat_gui_client.py"
                )
            raise

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        svr = SERVER if self.args.d is None else (self.args.d, CHAT_PORT)
        self.socket.connect(svr)
        self.sm = csm.ClientSM(self.socket)
        self.gui = GUI(self.send, self.recv, self.sm, self.socket, self.quit)

    def send(self, msg):
        mysend(self.socket, msg)

    def recv(self):
        return myrecv(self.socket)

    def quit(self):
        if self.closed or self.socket is None:
            return
        self.closed = True
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.socket.close()

    def run_chat(self):
        self.init_chat()
        self.gui.run()


def main():
    parser = argparse.ArgumentParser(description="chat GUI client argument")
    parser.add_argument("-d", type=str, default=None, help="server IP addr")
    args = parser.parse_args()

    client = GUIClient(args)
    client.run_chat()


if __name__ == "__main__":
    main()
