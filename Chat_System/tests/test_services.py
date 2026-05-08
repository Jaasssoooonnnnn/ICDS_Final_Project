import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from protocol import ACTION_EXCHANGE, require_fields
from services.chat_history import ChatHistory
from services.gemini_client import GeminiClient
from services.leaderboard import Leaderboard
from services.pollinations_client import PollinationsClient
from services.sentiment import NEGATIVE, NEUTRAL, POSITIVE, analyze_sentiment


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

    def test_pollinations_url_encodes_prompt(self):
        client = PollinationsClient(base_url="https://image.pollinations.ai/prompt", output_dir=Path(tempfile.gettempdir()))
        url = client.image_url("purple robot helper")
        self.assertIn("purple%20robot%20helper", url)
        self.assertIn("nologo=true", url)


if __name__ == "__main__":
    unittest.main()
