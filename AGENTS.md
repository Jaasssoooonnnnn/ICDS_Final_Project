# ICDS Final Project PRD and Agent Operating Guide

This file is the source of truth for agents working in this repository.
Read it before touching code. The project starts from the base
`Chat_System` socket chat framework and must become a final-project-ready
desktop chat application.

## Project Mission

Build an ICDS final project chat system that demonstrates:

- A polished desktop GUI.
- A Gemini-powered chatbot.
- Gemini-powered group chatbot interaction.
- Pollinations.ai image generation through `/aipic`.
- Gemini-powered `/summary` and `/keywords`.
- Local TextBlob sentiment analysis.
- A single-player Whack-a-Mole game with a shared leaderboard.

The final app should feel visually close to the reference screenshots in:

`/Users/huxingyun/Desktop/课/ICDS/Final Project/演示图`

This is a Python desktop project. Do not convert it into a web app.

## Locked Decisions

- Repository root: `/Users/huxingyun/Desktop/课/ICDS/Final Project`
- Base framework: `Chat_System`
- Runtime Python: `/opt/anaconda3/envs/chat_system/bin/python`
- Primary GUI toolkit: `customtkinter`
- Game toolkit: Tkinter `Toplevel` plus `Canvas`
- Chatbot model: `gemini-3.1-flash-lite-preview`
- Summary/keywords model: `gemini-3.1-flash-lite-preview`
- AI image provider: Pollinations.ai
- Sentiment provider: local TextBlob
- Visual asset generation: Codex `imagegen` skill
- Collaboration model: use `spawn_agent` for independent workstreams when the
  user has authorized agent delegation.
- Git policy: after `git init`, every key feature must be tested, recorded in
  `progress.md`, and committed.

## Required Product Features

### 1. Modern GUI

Build a CustomTkinter desktop client with:

- Login window.
- Main app shell with left sidebar, central chat, and right action/insight
  panel.
- Clear display of both sent and received messages.
- Message cards with sender, timestamp, text, and sentiment tag.
- Bot response cards.
- AI image cards with generated image preview.
- Quick action buttons for game, summary, keywords, and AI image generation.
- Online user list.
- Connection status indicator.
- Clean visual polish matching the reference images.

### 2. Chatbot

Provide a Gemini chatbot reachable by client command and GUI action.

- Direct command: `@bot <message>` in a group chat.
- Optional direct command: `/bot <message>` for one-to-one bot interaction.
- Bot responses should preserve short conversation context.
- The bot should identify itself as `ICDS Bot`.
- Do not fake bot success if Gemini fails. Raise or display the actual error
  clearly enough to debug.

### 3. Chatbot Group Interaction

The bot must participate naturally in group chat:

- It responds when addressed with `@bot`.
- It should see recent group chat context.
- Its response is broadcast into the same group conversation.
- It should not respond to every ordinary message.

### 4. Whack-a-Mole Single-Player Leaderboard

Implement a Tkinter `Toplevel` game window using `Canvas`.

- The game is single-player.
- The player clicks moles to score points.
- The game has a countdown timer.
- At game end, the user can submit the score to the server.
- The server maintains a leaderboard.
- The GUI can show leaderboard rank, player score, and recent activity.
- Prefer generated visual assets from `imagegen` for the game banner,
  background, mole sprites, and result panel.

### 5. AI Picture Generation

Support:

```text
/aipic: prompt text
```

Implementation requirements:

- Use Pollinations.ai.
- Extract the prompt after `/aipic:`.
- Save generated images under a project runtime folder that is gitignored.
- Display the generated image in the chat GUI.
- Broadcast enough metadata for peers to see the image card if possible.
- Do not use Gemini or OpenAI image generation for this feature.

### 6. Summary and Keywords

Support:

```text
/summary
/keywords
```

Implementation requirements:

- Use Gemini API.
- Use actual recent chat history, not fixed sample text.
- `/summary` returns a concise discussion summary.
- `/keywords` returns important topics as short tags.
- Show results in bot-style cards and in the right insight panel.

### 7. Sentiment Analysis

Analyze each user chat message locally with TextBlob.

Requirements:

- Labels: `Positive`, `Neutral`, `Negative`.
- Display visible sentiment tags in the message card.
- Keep the analysis local. Do not call Gemini for sentiment.
- The right insight panel should show counts for positive, neutral, and
  negative messages.

## Architecture

Preserve the existing socket server/client structure. Extend it cleanly instead
of replacing it.

Recommended module boundaries:

- `services/gemini_client.py`: Gemini API wrapper for bot, summary, keywords.
- `services/pollinations_client.py`: image generation URL/download client.
- `services/sentiment.py`: TextBlob sentiment labels.
- `services/chat_history.py`: recent message history and insight helpers.
- `services/leaderboard.py`: score storage, sorting, and persistence.
- `ui/modern_gui.py`: CustomTkinter app shell.
- `ui/message_widgets.py`: reusable message/image/bot card widgets.
- `ui/game_window.py`: Whack-a-Mole `Toplevel` game.
- `protocol.py`: shared action names and payload conventions if the existing
  protocol grows beyond simple inline JSON dictionaries.

These names are recommendations, not mandatory filenames. The important rule is
to avoid growing one giant GUI file or one giant server switchboard.

## Protocol Expectations

Keep the current JSON-over-socket framing from `chat_utils.py` unless there is
a concrete reason to change it.

New behavior should use explicit `action` values. Recommended actions:

- `exchange`: normal chat message.
- `bot_request` / `bot_response`: Gemini chatbot interaction.
- `summary_request` / `summary_response`: Gemini summary.
- `keywords_request` / `keywords_response`: Gemini keywords.
- `image_request` / `image_response`: Pollinations image generation.
- `score_submit` / `leaderboard`: game score and rankings.

Fail fast on malformed payloads. Do not silently ignore missing required keys.

## Environment and Dependencies

Use this Python for all app runs and tests:

```bash
/opt/anaconda3/envs/chat_system/bin/python
```

Known dependencies:

```bash
customtkinter
pillow
requests
textblob
nltk
google-genai
python-dotenv
```

If an agent discovers a missing package, it may install the package into
`/opt/anaconda3/envs/chat_system`, but it must also update dependency
documentation such as `requirements.txt` or a clearly named environment section.

## Secrets and Configuration

Local secrets live in `.env`. Never commit `.env`.

Required environment variables:

```bash
GEMINI_API_KEY=<local secret>
GEMINI_MODEL=gemini-3.1-flash-lite-preview
POLLINATIONS_IMAGE_BASE_URL=https://image.pollinations.ai/prompt
CHAT_HOST=127.0.0.1
CHAT_PORT=1112
```

Commit `.env.example` with placeholders only.

Do not put real API keys in:

- Source files.
- `AGENTS.md`.
- `progress.md`.
- Commit messages.
- Test snapshots.

## Design Philosophy

Match the visual direction of the screenshots, but keep the app implementable
inside the course project constraints.

UI principles:

- Light modern workspace.
- Purple/blue accent color.
- Left sidebar for navigation and online users.
- Center column for chat messages.
- Right panel for quick actions, room info, image controls, insights, and
  leaderboard cards.
- Rounded cards, soft borders, restrained shadows.
- Sentiment tags must be visually obvious.
- Bot and AI image output should look intentionally designed, not dumped text.
- Use generated bitmap assets from `imagegen` where visuals matter.

Do not spend time on decorative complexity that harms stability.

## Imagegen Usage

Use the `imagegen` skill for:

- App avatar placeholders.
- Bot icon or bot avatar.
- Whack-a-Mole banner.
- Mole sprites.
- Game background.
- Empty-state or result panel artwork.
- UI mockups when visual direction is uncertain.

Project-bound generated assets must be copied into the workspace, under a
clear asset folder, and referenced by code from there. Do not leave app assets
only in Codex's generated image cache.

## Agent Collaboration Workflow

Use `spawn_agent` when tasks are independent and can proceed in parallel.

Good split examples:

- Agent A: server protocol and leaderboard actions.
- Agent B: Gemini client and bot/summary/keywords service.
- Agent C: Pollinations image flow and image card display.
- Agent D: CustomTkinter app shell and message widgets.
- Agent E: Whack-a-Mole game window and score submission.

Rules:

- Define each subagent's file ownership before spawning.
- Do not assign overlapping write scopes to parallel workers.
- Tell workers they are not alone in the codebase and must not revert edits
  made by others.
- Main agent integrates and tests the final behavior.
- Do not spawn agents for trivial one-file edits.

## Progress Discipline

Maintain `progress.md` at the repo root.

Before starting work:

- Read `AGENTS.md`.
- Read `progress.md`.
- Inspect current git status after `git init`.
- Identify user changes and do not revert them.

After every meaningful chunk:

- Update `progress.md`.
- Record what changed.
- Record tests run and results.
- Record bugs found or decisions made.
- Record commit hash after committing.
- Leave next-agent notes.

## Commit Discipline

Git is intentionally not initialized until the user approves this PRD.

After `git init`:

- Make small focused commits.
- Each required feature should have at least one commit.
- Before each commit, run relevant tests or manual verification.
- Update `progress.md` before committing.
- Do not commit `.env`, runtime images, caches, `.idx`, or `.DS_Store`.

Suggested commit sequence:

1. `project setup and PRD`
2. `modernize chat GUI shell`
3. `add sentiment analysis`
4. `add Gemini chatbot`
5. `add group bot interaction`
6. `add summary and keyword commands`
7. `add Pollinations image generation`
8. `add whack-a-mole leaderboard`
9. `polish UI and presentation readiness`

## Testing Discipline

Every feature must be tested. Prefer automated smoke tests for services and
protocol behavior, plus documented manual GUI checks where automation is hard.

Required checks:

- `python -m py_compile` for changed Python files.
- Server/client login smoke test.
- Normal chat send/receive test.
- Sentiment label test for positive, neutral, and negative messages.
- Gemini client configuration test that fails clearly when the key is missing.
- Bot command test with a real Gemini call when network/API quota allows.
- Summary/keywords test using real recent chat history.
- Pollinations URL/download test.
- Game scoring test for timer, hit detection, score submit, and leaderboard
  ordering.
- GUI manual verification with screenshots after major UI changes.

If an external API is unavailable, record the exact failure in `progress.md`.
Do not replace it with fake success.

## Fail-Fast Coding Rules

Prefer clear failures over hidden behavior.

Do not:

- Add broad `except Exception: pass`.
- Swallow socket/API/config errors silently.
- Invent fake bot, image, or summary responses in production code.
- Add fallback API keys.
- Add hidden offline behavior unless it is explicitly named test mode.
- Mix unrelated feature logic into one large file.
- Commit generated caches or runtime artifacts.

Do:

- Validate required environment variables at startup of the service that uses
  them.
- Raise specific errors with useful messages.
- Keep API clients small and testable.
- Keep UI rendering separate from network/service logic.
- Keep protocol payloads explicit.
- Make manual verification steps reproducible.

## Acceptance Criteria

The project is ready for final presentation when:

- Two or more clients can login through the GUI.
- Sent and received messages display correctly.
- Sentiment tags appear for normal user messages.
- `@bot` works in a group chat.
- `/summary` and `/keywords` use real chat history.
- `/aipic:` generates and displays an image.
- Whack-a-Mole can be played and submits a ranked score.
- Leaderboard is visible in the GUI.
- The app visually resembles the reference screenshots.
- `progress.md` documents all milestones, tests, and commits.
- No real secrets are committed.
