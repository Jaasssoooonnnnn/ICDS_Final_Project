"""Local TextBlob sentiment labels."""

from textblob import TextBlob

POSITIVE = "Positive"
NEUTRAL = "Neutral"
NEGATIVE = "Negative"


def analyze_sentiment(text: str) -> str:
    polarity = TextBlob(text or "").sentiment.polarity
    if polarity > 0.1:
        return POSITIVE
    if polarity < -0.1:
        return NEGATIVE
    return NEUTRAL
