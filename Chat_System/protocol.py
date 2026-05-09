"""Shared JSON action names and payload helpers for the chat system."""

ACTION_LOGIN = "login"
ACTION_CONNECT = "connect"
ACTION_DISCONNECT = "disconnect"
ACTION_EXCHANGE = "exchange"
ACTION_LIST = "list"
ACTION_TIME = "time"
ACTION_SEARCH = "search"
ACTION_POEM = "poem"

ACTION_BOT_REQUEST = "bot_request"
ACTION_BOT_RESPONSE = "bot_response"
ACTION_SUMMARY_REQUEST = "summary_request"
ACTION_SUMMARY_RESPONSE = "summary_response"
ACTION_KEYWORDS_REQUEST = "keywords_request"
ACTION_KEYWORDS_RESPONSE = "keywords_response"
ACTION_IMAGE_REQUEST = "image_request"
ACTION_IMAGE_RESPONSE = "image_response"
ACTION_SCORE_SUBMIT = "score_submit"
ACTION_LEADERBOARD = "leaderboard"
ACTION_ERROR = "error"

ACTION_TTT_JOIN = "ttt_join"
ACTION_TTT_WAITING = "ttt_waiting"
ACTION_TTT_MOVE = "ttt_move"
ACTION_TTT_RESTART = "ttt_restart"
ACTION_TTT_LEAVE = "ttt_leave"
ACTION_TTT_STATE = "ttt_state"
ACTION_TTT_ERROR = "ttt_error"

BOT_NAME = "ICDS Bot"


def require_fields(payload, fields):
    """Raise ValueError when a JSON payload does not contain required fields."""
    missing = [field for field in fields if field not in payload]
    if missing:
        raise ValueError(
            "Malformed payload for action "
            + repr(payload.get("action"))
            + "; missing "
            + ", ".join(missing)
        )
