"""Authoritative server-side Tic-Tac-Toe room state."""

from __future__ import annotations


class TicTacToeRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: list[str] = []
        self.symbols: dict[str, str] = {}
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.turn: str | None = None
        self.status = "waiting"
        self.winner: str | None = None
        self.restart_votes: set[str] = set()

    def add_player(self, username: str) -> str:
        if username in self.players:
            return self.symbols[username]
        if len(self.players) >= 2:
            raise ValueError("Tic-Tac-Toe room is full")
        symbol = "X" if not self.players else "O"
        self.players.append(username)
        self.symbols[username] = symbol
        if len(self.players) == 2:
            self.status = "playing"
            self.turn = self.players[0]
        return symbol

    def make_move(self, username: str, row: int, col: int) -> None:
        if self.status != "playing":
            raise ValueError("The game is not active.")
        if username not in self.players:
            raise ValueError("You are not in this Tic-Tac-Toe room.")
        if username != self.turn:
            raise ValueError("It is not your turn.")
        if row not in range(3) or col not in range(3):
            raise ValueError("Move must be inside the 3x3 board.")
        if self.board[row][col]:
            raise ValueError("That cell is already occupied.")

        self.board[row][col] = self.symbols[username]
        if self.check_winner():
            self.status = "finished"
            self.winner = username
            self.turn = None
        elif self.is_draw():
            self.status = "draw"
            self.winner = None
            self.turn = None
        else:
            self.turn = self.players[1] if username == self.players[0] else self.players[0]

    def vote_restart(self, username: str) -> bool:
        if username not in self.players:
            raise ValueError("You are not in this Tic-Tac-Toe room.")
        self.restart_votes.add(username)
        if len(self.restart_votes) == len(self.players):
            self.reset()
            return True
        return False

    def reset(self) -> None:
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.turn = self.players[0] if len(self.players) == 2 else None
        self.status = "playing" if len(self.players) == 2 else "waiting"
        self.winner = None
        self.restart_votes.clear()

    def remove_player(self, username: str) -> None:
        if username not in self.players:
            return
        self.players.remove(username)
        self.symbols.pop(username, None)
        self.restart_votes.discard(username)
        self.status = "closed"
        self.turn = None

    def check_winner(self) -> bool:
        lines = []
        lines.extend(self.board)
        lines.extend([[self.board[row][col] for row in range(3)] for col in range(3)])
        lines.append([self.board[i][i] for i in range(3)])
        lines.append([self.board[i][2 - i] for i in range(3)])
        return any(line[0] and line.count(line[0]) == 3 for line in lines)

    def is_draw(self) -> bool:
        return all(cell for row in self.board for cell in row)

    def message(self) -> str:
        if self.status == "waiting":
            return "Waiting for another player..."
        if self.status == "playing":
            return f"Game started. {self.turn}'s turn."
        if self.status == "finished":
            return f"{self.winner} wins!"
        if self.status == "draw":
            return "Draw!"
        return "Tic-Tac-Toe room closed."

    def to_state_message(self) -> dict:
        return {
            "action": "ttt_state",
            "type": "ttt_state",
            "room_id": self.room_id,
            "players": list(self.players),
            "symbols": dict(self.symbols),
            "board": [row[:] for row in self.board],
            "turn": self.turn,
            "status": self.status,
            "winner": self.winner,
            "message": self.message(),
        }
