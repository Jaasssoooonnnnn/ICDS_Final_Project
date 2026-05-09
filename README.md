# ICDS Final Project Chat System

This project extends the original socket-based chat system into a desktop chat
application with a polished CustomTkinter GUI, Gemini/OpenAI chatbot features,
Pollinations.ai image generation, TextBlob sentiment analysis, Gemini/OpenAI
summary and keyword extraction, a single-player Whack-a-Mole game, and a
graphical multiplayer Tic-Tac-Toe game with server-authoritative state.

## Features

- Multi-client socket chat with login and online user list.
- Modern desktop GUI with left navigation, central chat stream, and right
  insight/action panel.
- Sent and received message cards with sender, timestamp, and sentiment tags.
- Gemini/OpenAI-powered `ICDS Bot` through `/bot` and group `@bot` mentions.
- Bot personality setting with `/personality: friendly project mentor`.
- Gemini/OpenAI-powered `/summary` and `/keywords` over real recent chat
  history.
- Pollinations.ai image generation with `/aipic: prompt text`.
- Image cards with preview rendering in the chat stream.
- Local TextBlob sentiment analysis: `Positive`, `Neutral`, `Negative`.
- Tkinter `Canvas` Whack-a-Mole game with score submission and ranked
  leaderboard.
- Multiplayer Tic-Tac-Toe between two GUI clients, synchronized and validated
  by the server.

## Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and fill in either a Gemini key or an OpenAI
key:

```text
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
GEMINI_MODEL=gemini-3.1-flash-lite-preview
POLLINATIONS_IMAGE_BASE_URL=https://image.pollinations.ai/prompt
CHAT_HOST=127.0.0.1
CHAT_PORT=1112
```

`.env` is intentionally ignored by Git. The server uses Gemini when
`GEMINI_API_KEY` is configured; otherwise it falls back to OpenAI when
`OPENAI_API_KEY` is configured.

## Run

Start the server in one terminal:

```powershell
cd Chat_System
python chat_server.py
```

Start one or more GUI clients in separate terminals:

```powershell
cd Chat_System
python chat_gui_client.py
```

For a two-client demo, open two GUI clients, log in with different names, and
send messages from both windows.

## Demo Commands

- Normal chat: type any message and click `Send`.
- Group bot: `@bot help us plan the final presentation`.
- Direct bot: `/bot explain our architecture in two sentences`.
- Personality: `/personality: upbeat teaching assistant`.
- Summary: `/summary`.
- Keywords: `/keywords`.
- AI image: `/aipic: a futuristic classroom chat app dashboard`.
- Multiplayer game: click `Games` or Quick Actions `Tic-Tac-Toe` in two
  clients, click `Join Game`, then take turns on the graphical board.
- Solo game: click Quick Actions `Whack-a-Mole`, play briefly, then submit the
  score.

## Verification

Compile all Python files:

```powershell
$files = Get-ChildItem -Path Chat_System -Recurse -Filter *.py | ForEach-Object { $_.FullName }
python -m py_compile @files
```

Run automated tests:

```powershell
python -m unittest discover -s Chat_System\tests -v
```

Optional real external API smoke test, requiring a valid `.env`:

```powershell
python Chat_System\tests\external_smoke.py
```

## Requirement Coverage

| Guideline requirement | Implementation |
| --- | --- |
| GUI display window, input, send button, real-time updates | `Chat_System/GUI.py` |
| Display both sent and received messages | `MessageCard` usage in `GUI.py` |
| Login and online users | GUI login plus server `login` and `list` actions |
| Chatbot | Gemini/OpenAI LLM client and `@bot` or `/bot` commands |
| Chatbot context | `services/chat_history.py` passed into LLM prompts |
| Chatbot personality | `/personality:` command |
| Group chatbot interaction bonus | `@bot` broadcast response in group chat |
| Single-player game with ranked scores | `ui/game_window.py` and `services/leaderboard.py` |
| Interactive multiplayer gaming bonus | `services/tic_tac_toe.py`, `ui/tic_tac_toe_window.py`, and `ttt_*` server actions |
| AI picture bonus | Pollinations `/aipic:` flow |
| Summary / keywords bonus | Gemini/OpenAI `/summary` and `/keywords` |
| Sentiment bonus | Local TextBlob analysis and visible tags |
| pi-mono usage demonstration | See `docs/presentation_script.md` |

## Notes

Generated runtime images and score data are saved under `Chat_System/runtime/`,
which is ignored by Git. No real API keys should be committed.
