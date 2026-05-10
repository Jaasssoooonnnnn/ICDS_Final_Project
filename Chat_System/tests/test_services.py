import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from protocol import ACTION_EXCHANGE, require_fields
from services.chat_history import ChatHistory
from services.gemini_client import GeminiClient
from services.leaderboard import Leaderboard
from services.llm_client import LLMClient
from services.openai_client import OpenAIClient
from services.pollinations_client import PollinationsClient
from services.sentiment import NEGATIVE, NEUTRAL, POSITIVE, analyze_sentiment
from services.tic_tac_toe import TicTacToeRoom


class ServiceTests(unittest.TestCase):
    def test_sentiment_labels(self):
        self.assertEqual(analyze_sentiment("I love this excellent project"), POSITIVE)
        self.assertEqual(analyze_sentiment("This is a message about class"), NEUTRAL)
        self.assertEqual(analyze_sentiment("I hate this terrible bug"), NEGATIVE)

    def test_chat_history_context_and_counts(self):
        history = ChatHistory(limit=3)
        history.add("Alice", "Great work", POSITIVE)
        history.add("Bob", "Okay", NEUTRAL)
        context = history.context()
        self.assertIn("Alice: Great work", context)
        self.assertEqual(history.insights()[POSITIVE], 1)
        self.assertEqual(history.insights()[NEUTRAL], 1)

    def test_leaderboard_sorts_scores(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            board = Leaderboard(Path(temp_dir) / "leaderboard.json")
            board.submit("low", 2)
            top = board.submit("high", 9)
            self.assertEqual(top[0]["player"], "high")
            self.assertEqual(top[0]["rank"], 1)

    def test_protocol_requires_fields(self):
        require_fields({"action": ACTION_EXCHANGE, "message": "hi"}, ["action", "message"])
        with self.assertRaises(ValueError):
            require_fields({"action": ACTION_EXCHANGE}, ["action", "message"])

    def test_gemini_missing_key_fails_clearly(self):
        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
            GeminiClient(api_key="")

    def test_gemini_prompt_includes_personality(self):
        client = GeminiClient.__new__(GeminiClient)
        prompts = []

        def fake_generate(prompt):
            prompts.append(prompt)
            return "ok"

        client._generate = fake_generate
        self.assertEqual(client.bot_reply("help", "Alice: hi", "warm project mentor"), "ok")
        self.assertIn("warm project mentor", prompts[0])

    def test_openai_response_text_parsing(self):
        client = OpenAIClient.__new__(OpenAIClient)
        data = {"output": [{"type": "message", "content": [{"type": "output_text", "text": "hello"}]}]}
        text = []

        def fake_urlopen(_request, timeout=45):
            class FakeResponse:
                def __enter__(self):
                    return self

                def __exit__(self, *_args):
                    return False

                def read(self):
                    return __import__("json").dumps(data).encode("utf-8")

            return FakeResponse()

        client.api_key = "test"
        client.model = "test-model"
        client.base_url = "https://api.openai.com/v1"
        import urllib.request

        original = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen
        try:
            text.append(client._generate("hi"))
        finally:
            urllib.request.urlopen = original
        self.assertEqual(text[0], "hello")

    def test_llm_client_uses_openai_when_gemini_placeholder(self):
        import os

        old_gemini = os.environ.get("GEMINI_API_KEY")
        old_openai = os.environ.get("OPENAI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "replace-with-your-gemini-api-key"
        os.environ["OPENAI_API_KEY"] = "sk-test"
        original_init = OpenAIClient.__init__
        try:
            OpenAIClient.__init__ = lambda self, api_key=None, model=None: setattr(self, "api_key", api_key or "sk-test")
            client = LLMClient()
            self.assertEqual(client.provider, "OpenAI")
        finally:
            OpenAIClient.__init__ = original_init
            if old_gemini is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = old_gemini
            if old_openai is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old_openai

    def test_llm_client_prefers_openai_over_gemini_by_default(self):
        import os

        old_provider = os.environ.get("AI_PROVIDER")
        old_gemini = os.environ.get("GEMINI_API_KEY")
        old_openai = os.environ.get("OPENAI_API_KEY")
        os.environ.pop("AI_PROVIDER", None)
        os.environ["GEMINI_API_KEY"] = "bad-gemini-key"
        os.environ["OPENAI_API_KEY"] = "sk-test"
        original_init = OpenAIClient.__init__
        try:
            OpenAIClient.__init__ = lambda self, api_key=None, model=None: setattr(self, "api_key", api_key or "sk-test")
            client = LLMClient()
            self.assertEqual(client.provider, "OpenAI")
        finally:
            OpenAIClient.__init__ = original_init
            if old_provider is None:
                os.environ.pop("AI_PROVIDER", None)
            else:
                os.environ["AI_PROVIDER"] = old_provider
            if old_gemini is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = old_gemini
            if old_openai is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old_openai

    def test_llm_client_falls_back_when_primary_fails(self):
        client = LLMClient.__new__(LLMClient)

        class BadPrimary:
            def summarize(self, _context):
                raise RuntimeError("bad primary")

        class GoodFallback:
            def summarize(self, _context):
                return "fallback summary"

        client.provider = "Gemini"
        client.client = BadPrimary()
        client.fallback_provider = "OpenAI"
        client.fallback_client = GoodFallback()
        self.assertEqual(client.summarize("Alice: hi"), "fallback summary")
        self.assertEqual(client.provider, "OpenAI")

    def test_pollinations_url_encodes_prompt(self):
        client = PollinationsClient(base_url="https://image.pollinations.ai/prompt", output_dir=Path(tempfile.gettempdir()))
        url = client.image_url("purple robot helper")
        self.assertIn("purple%20robot%20helper", url)
        self.assertIn("nologo=true", url)

    def test_pollinations_timeout_returns_local_fallback(self):
        import requests
        import services.pollinations_client as pollinations_module

        with tempfile.TemporaryDirectory() as temp_dir:
            client = PollinationsClient(base_url="https://image.pollinations.ai/prompt", output_dir=Path(temp_dir))
            original_get = pollinations_module.requests.get
            pollinations_module.requests.get = lambda *_args, **_kwargs: (_ for _ in ()).throw(requests.Timeout("slow"))
            try:
                result = client.generate("demo robot")
            finally:
                pollinations_module.requests.get = original_get

            self.assertTrue(result["fallback"])
            self.assertTrue(Path(result["path"]).exists())
            self.assertIn("demo%20robot", result["url"])

    def test_tic_tac_toe_detects_o_win_and_draw(self):
        room = TicTacToeRoom("room")
        room.add_player("Alice")
        room.add_player("Bob")
        for player, row, col in [
            ("Alice", 0, 0),
            ("Bob", 1, 0),
            ("Alice", 0, 1),
            ("Bob", 1, 1),
            ("Alice", 2, 2),
            ("Bob", 1, 2),
        ]:
            room.make_move(player, row, col)
        self.assertEqual(room.status, "finished")
        self.assertEqual(room.winner, "Bob")

        draw = TicTacToeRoom("draw")
        draw.add_player("Alice")
        draw.add_player("Bob")
        for player, row, col in [
            ("Alice", 0, 0),
            ("Bob", 0, 1),
            ("Alice", 0, 2),
            ("Bob", 1, 1),
            ("Alice", 1, 0),
            ("Bob", 1, 2),
            ("Alice", 2, 1),
            ("Bob", 2, 0),
            ("Alice", 2, 2),
        ]:
            draw.make_move(player, row, col)
        self.assertEqual(draw.status, "draw")
        self.assertIsNone(draw.winner)


if __name__ == "__main__":
    unittest.main()
