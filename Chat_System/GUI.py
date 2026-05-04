#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import select
from tkinter import *

from chat_utils import CHAT_WAIT, S_LOGGEDIN, S_OFFLINE, menu


class GUI:
    def __init__(self, send, recv, sm, s, on_close=None):
        self.Window = Tk()
        self.Window.withdraw()

        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.on_close = on_close

        self.my_msg = ""
        self.closed = False
        self.textCons = None

    def login(self):
        self.login_window = Toplevel()
        self.login_window.title("Login")
        self.login_window.resizable(width=False, height=False)
        self.login_window.configure(width=400, height=300)
        self.login_window.protocol("WM_DELETE_WINDOW", self.close)

        self.pls = Label(
            self.login_window,
            text="Please login to continue",
            justify=CENTER,
            font="Helvetica 14 bold",
        )
        self.pls.place(relheight=0.15, relx=0.2, rely=0.07)

        self.labelName = Label(
            self.login_window,
            text="Name: ",
            font="Helvetica 12",
        )
        self.labelName.place(relheight=0.2, relx=0.1, rely=0.2)

        self.entryName = Entry(self.login_window, font="Helvetica 14")
        self.entryName.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.2)
        self.entryName.focus()
        self.entryName.bind("<Return>", lambda event: self.goAhead(self.entryName.get()))

        self.statusLabel = Label(
            self.login_window,
            text="",
            fg="#B03A2E",
            font="Helvetica 11",
        )
        self.statusLabel.place(relwidth=0.8, relheight=0.1, relx=0.1, rely=0.42)

        self.go = Button(
            self.login_window,
            text="CONTINUE",
            font="Helvetica 14 bold",
            command=lambda: self.goAhead(self.entryName.get()),
        )
        self.go.place(relx=0.4, rely=0.55)

        self.Window.mainloop()

    def goAhead(self, name):
        name = name.strip()
        if len(name) == 0:
            self.statusLabel.config(text="Please enter a name.")
            return

        msg = json.dumps({"action": "login", "name": name})
        self.send(msg)
        response = json.loads(self.recv())
        if response["status"] == "ok":
            self.login_window.destroy()
            self.sm.set_state(S_LOGGEDIN)
            self.sm.set_myname(name)
            self.layout(name)
            self.append_text(menu)
            self.Window.after(int(CHAT_WAIT * 1000), self.proc)
        elif response["status"] == "duplicate":
            self.statusLabel.config(text="Duplicate username, try again.")
        else:
            self.statusLabel.config(text="Login failed, try again.")

    def layout(self, name):
        self.name = name
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=False, height=False)
        self.Window.configure(width=470, height=550, bg="#17202A")
        self.Window.protocol("WM_DELETE_WINDOW", self.close)

        self.labelHead = Label(
            self.Window,
            bg="#17202A",
            fg="#EAECEE",
            text=self.name,
            font="Helvetica 13 bold",
            pady=5,
        )
        self.labelHead.place(relwidth=1)

        self.line = Label(self.Window, width=450, bg="#ABB2B9")
        self.line.place(relwidth=1, rely=0.07, relheight=0.012)

        self.textCons = Text(
            self.Window,
            width=20,
            height=2,
            bg="#17202A",
            fg="#EAECEE",
            font="Helvetica 14",
            padx=5,
            pady=5,
        )
        self.textCons.place(relheight=0.745, relwidth=1, rely=0.08)

        self.labelBottom = Label(self.Window, bg="#ABB2B9", height=80)
        self.labelBottom.place(relwidth=1, rely=0.825)

        self.entryMsg = Entry(
            self.labelBottom,
            bg="#2C3E50",
            fg="#EAECEE",
            font="Helvetica 13",
        )
        self.entryMsg.place(relwidth=0.74, relheight=0.06, rely=0.008, relx=0.011)
        self.entryMsg.focus()
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))

        self.buttonMsg = Button(
            self.labelBottom,
            text="Send",
            font="Helvetica 10 bold",
            width=20,
            bg="#ABB2B9",
            command=lambda: self.sendButton(self.entryMsg.get()),
        )
        self.buttonMsg.place(relx=0.77, rely=0.008, relheight=0.06, relwidth=0.22)

        self.textCons.config(cursor="arrow")
        scrollbar = Scrollbar(self.textCons)
        scrollbar.place(relheight=1, relx=0.974)
        scrollbar.config(command=self.textCons.yview)
        self.textCons.config(yscrollcommand=scrollbar.set)
        self.textCons.config(state=DISABLED)

    def sendButton(self, msg):
        msg = msg.strip()
        if len(msg) == 0:
            return
        self.my_msg = msg
        self.entryMsg.delete(0, END)

    def append_text(self, msg):
        if not msg or self.textCons is None:
            return
        self.textCons.config(state=NORMAL)
        self.textCons.insert(END, msg + "\n\n")
        self.textCons.config(state=DISABLED)
        self.textCons.see(END)

    def proc(self):
        if self.closed:
            return

        read, write, error = select.select([self.socket], [], [], 0)
        peer_msg = ""
        if self.socket in read:
            peer_msg = self.recv()

        if len(self.my_msg) > 0 or len(peer_msg) > 0:
            system_msg = self.sm.proc(self.my_msg, peer_msg)
            self.my_msg = ""
            self.append_text(system_msg)

        if self.sm.get_state() == S_OFFLINE:
            self.close()
            return

        self.Window.after(int(CHAT_WAIT * 1000), self.proc)

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.sm.get_state() != S_OFFLINE:
            self.sm.set_state(S_OFFLINE)
        if self.on_close is not None:
            self.on_close()
        self.Window.destroy()

    def run(self):
        self.login()
