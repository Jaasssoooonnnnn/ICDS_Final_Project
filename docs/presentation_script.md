# Presentation Script

Target length: 10 to 15 minutes.

## 1. Introduction

Introduce the project as an enhanced distributed chat system. The goal is to
keep the original socket server and multi-client architecture while adding a
complete desktop experience and AI/game extensions.

Mention the core features:

- Modern GUI chat client.
- Gemini chatbot with context and configurable personality.
- Group bot interaction through `@bot`.
- AI image generation through Pollinations.ai.
- Summary and keyword extraction over real chat history.
- Local sentiment analysis with TextBlob.
- Whack-a-Mole game with server leaderboard.

## 2. pi-mono Usage Demo

Explain that pi-mono was used as an AI development assistant for:

- Turning the final project guideline into a project requirement checklist.
- Generating and refactoring service modules.
- Debugging socket smoke tests.
- Producing test coverage for sentiment, protocol validation, leaderboard, and
  server/client behavior.
- Summarizing implementation progress in `progress.md`.

In the video, show one concrete example: open `progress.md` and explain how
the assistant helped record milestones and test results, or show one test file
that was generated/refined with AI assistance.

## 3. Application Demo

Recommended order:

1. Start `python Chat_System/chat_server.py`.
2. Start two GUI clients with `python Chat_System/chat_gui_client.py`.
3. Log in as two different users.
4. Send a normal message from each client and point out sent and received
   cards.
5. Show sentiment tags and the sentiment counts in the right panel.
6. Send `@bot help us plan the demo` and show the group bot response.
7. Send `/personality: upbeat teaching assistant`, then ask `/bot introduce
   yourself`.
8. Send `/summary` and `/keywords`.
9. Send `/aipic: a futuristic classroom chat app dashboard` and show the image
   card.
10. Start Whack-a-Mole, play briefly, submit the score, and show the
    leaderboard.

## 4. Technical Discussion

Explain the architecture:

- `chat_server.py` remains the central socket server.
- `chat_utils.py` keeps the original JSON-over-socket framing.
- `protocol.py` defines explicit action names.
- `services/gemini_client.py` isolates Gemini calls.
- `services/pollinations_client.py` isolates image generation.
- `services/sentiment.py` keeps sentiment local.
- `services/chat_history.py` stores recent context for summary, keywords, and
  bot replies.
- `services/leaderboard.py` stores and ranks game scores.
- `GUI.py` and `ui/message_widgets.py` render the modern chat interface.
- `ui/game_window.py` implements the game in a `Toplevel` and `Canvas`.

## 5. Reflection

Discuss challenges:

- Keeping server protocol changes compatible with the original chat system.
- Making external API errors visible instead of silently faking success.
- Updating the GUI without blocking socket receive loops.
- Making the game independent while still submitting scores to the chat server.

Possible improvements:

- Add true two-player game synchronization.
- Add file transfer.
- Add richer profile avatars.
- Package the app into a one-click desktop executable.
