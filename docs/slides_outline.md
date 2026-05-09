# Slides Outline

## Slide 1: ICDS Final Project Chat System

- Distributed socket chat system with modern desktop GUI.
- Built on the original server and multi-client chat framework.

## Slide 2: Project Goals

- Replace terminal interaction with a complete GUI.
- Add AI assistant features.
- Add bonus NLP and image generation features.
- Add a playable game with shared leaderboard.

## Slide 3: System Architecture

- Socket server: `chat_server.py`.
- GUI clients: `chat_gui_client.py` and `GUI.py`.
- Protocol actions: `protocol.py`.
- Service layer: Gemini/OpenAI, Pollinations, sentiment, history, leaderboard.

## Slide 4: GUI Design

- Login window.
- Left sidebar with navigation and online users.
- Central chat stream with message cards.
- Right panel for quick actions, insights, sentiment, and leaderboard.

## Slide 5: Chatbot

- `ICDS Bot` uses Gemini or OpenAI through the provider selector.
- `/bot` for direct bot interaction.
- `@bot` for group interaction.
- Recent chat history is included as context.
- `/personality:` changes bot behavior.

## Slide 6: Bonus AI Features

- `/summary` generates a concise recent-chat summary.
- `/keywords` extracts important topic tags.
- `/aipic:` generates an image through Pollinations.ai.

## Slide 7: Sentiment Analysis

- Uses local TextBlob.
- Labels each user message as Positive, Neutral, or Negative.
- Displays visible tags and aggregate counts in the insight panel.

## Slide 8: Whack-a-Mole Game

- Tkinter `Toplevel` and `Canvas`.
- Player clicks moles before the timer ends.
- Final score is submitted to the server.
- Server returns sorted leaderboard rankings.

## Slide 9: Testing

- Python compilation checks.
- Unit tests for services and protocol validation.
- Socket smoke test for two-client login, chat, sentiment, and leaderboard.
- Optional external smoke test for Gemini/OpenAI and Pollinations.

## Slide 10: pi-mono Usage

- Requirement breakdown.
- Code generation and refactoring assistance.
- Debugging and testing support.
- Progress documentation.

## Slide 11: Challenges

- Preserving the original socket architecture.
- Handling real API failures clearly.
- Keeping GUI updates responsive.
- Integrating game results into the chat server.

## Slide 12: Conclusion

- GUI requirement completed.
- Chatbot selective topic completed.
- Game selective topic completed.
- Bonus features completed: group bot, AI image, summary/keywords, sentiment,
  and multiplayer Tic-Tac-Toe.
