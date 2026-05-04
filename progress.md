# ICDS Final Project Progress

Original prompt:

Build from the base `Chat_System` framework into a polished ICDS final project
desktop chat app matching `/Users/huxingyun/Desktop/课/ICDS/Final Project/演示图`.
Required points: GUI, Chatbot, single-player Whack-a-Mole leaderboard.
Bonus points: AI Picture Generation, Summary / Keywords, Sentiment Analysis,
Chatbot Group Interaction. Use Pollinations.ai for images, Google Gemini API
with `gemini-3.1-flash-lite-preview` for chatbot/summary/keywords, and local
TextBlob for sentiment. Use `/opt/anaconda3/envs/chat_system` as the runtime.
Agents should use subagents for independent work, update this file, test each
feature, and commit after each key point once git is initialized.

## Current Status

- [x] PRD approved by user.
- [x] `AGENTS.md` created as project PRD and agent operating guide.
- [x] Local `.env` created with Gemini/Pollinations/runtime configuration.
- [x] `.env.example` created with placeholders.
- [x] `.gitignore` created to exclude secrets and runtime artifacts.
- [x] Git repository initialized.
- [x] Baseline project prepared for first commit.
- [x] Core service layer and server protocol actions implemented.

## Feature Milestones

- [x] GUI: CustomTkinter desktop shell matching the reference screenshots.
- [ ] Chatbot: Gemini-powered bot for direct client interaction.
- [x] Game: Tkinter Whack-a-Mole with single-player score submission.
- [ ] AI Picture Generation: Pollinations.ai `/aipic:` flow.
- [ ] Summary / Keywords: Gemini `/summary` and `/keywords` over real history.
- [x] Sentiment Analysis: local TextBlob labels and insight counts.
- [ ] Chatbot Group Interaction: `@bot` responds inside group chat context.

## Decisions

- Use Python desktop UI, not web.
- Use `customtkinter` for the main app and Tkinter `Canvas` for the game.
- Use `gemini-3.1-flash-lite-preview` as requested by the user.
- Do not commit `.env`.
- Do not initialize git until after PRD approval.
- Prefer fail-fast implementation over hidden fallback behavior.

## Tests and Validation Log

- 2026-05-04: Confirmed required Python packages import successfully in
  `/opt/anaconda3/envs/chat_system`: `tkinter`, `PIL`, `customtkinter`,
  `requests`, `textblob`, `google.genai`, `nltk`.
- 2026-05-04: Created PRD/config/progress files only. No `Chat_System` source
  files modified.
- 2026-05-04: Initialized git repository and prepared the first baseline commit
  with project source, reference docs, reference screenshots, PRD/config
  templates, and progress tracking. `.env`, `.DS_Store`, caches, and runtime
  indexes are ignored.
- 2026-05-04: Added explicit protocol constants plus services for environment
  loading, Gemini, Pollinations.ai, TextBlob sentiment, recent chat history, and
  persistent game leaderboard. Reworked `chat_server.py` to broadcast normal
  messages, attach sentiment labels, respond to `@bot`, `/bot`, `/summary`,
  `/keywords`, `/aipic:`, score submission, leaderboard, and online-list
  actions with clear error payloads instead of silent fallbacks.
- 2026-05-04: Ran
  `/opt/anaconda3/envs/chat_system/bin/python -m py_compile` for changed core
  Python files: passed.
- 2026-05-04: Ran
  `/opt/anaconda3/envs/chat_system/bin/python -m unittest discover -s Chat_System/tests -v`:
  6 service/protocol tests passed, including sentiment labels, missing Gemini
  key failure, Pollinations URL construction, chat history, and leaderboard
  ordering.
- 2026-05-04: Commit `d477c4d` recorded the core chat services and protocol
  actions.
- 2026-05-04: Replaced the legacy Tk text GUI with a CustomTkinter desktop
  workspace: login window, left online-user sidebar, central message/bot/image
  cards, right quick actions, sentiment insights, summary/keyword panel, and
  leaderboard card.
- 2026-05-04: Added `ui/game_window.py` with a Tkinter `Toplevel` +
  `Canvas` Whack-a-Mole game, countdown timer, hit detection, result panel, and
  score submission callback.
- 2026-05-04: Used Codex `imagegen` to create
  `Chat_System/assets/whack_mole_sheet.png`; the game window loads it for the
  game banner/background and result-panel art.
- 2026-05-04: Installed missing `python-dotenv` into
  `/opt/anaconda3/envs/chat_system` and kept it documented in
  `requirements.txt`.
- 2026-05-04: Added a real socket smoke test that starts the server on a test
  port, logs in two clients, verifies online list behavior, sends a normal chat
  message with `Positive` sentiment, submits a game score, and verifies
  leaderboard response. The first sandbox run could not bind localhost; rerun
  with approved local socket permissions passed.
- 2026-05-04: Hardened user chat index loading so empty/corrupt ignored runtime
  `.idx` files are rebuilt instead of closing the login socket with a pickle
  EOF error.
- 2026-05-04: Ran
  `/opt/anaconda3/envs/chat_system/bin/python -m py_compile` for server, GUI,
  UI, game, state machine, and smoke-test files: passed.
- 2026-05-04: Ran
  `/opt/anaconda3/envs/chat_system/bin/python -m unittest discover -s Chat_System/tests -v`:
  7 tests passed, including real socket server/client smoke.
- 2026-05-04: Ran real Gemini smoke calls for bot reply, summary, and keywords
  using the configured local `.env` key: passed. No secret was printed.
- 2026-05-04: Ran real Pollinations.ai smoke generation; image saved under the
  gitignored runtime folder `Chat_System/runtime/images/`: passed.
- 2026-05-04: Ran a brief Tk/CustomTkinter GUI construction smoke that created
  the main workspace and game window in the target Python environment: passed.

## Next Agent Notes

- First implementation step after this setup should inspect `git status --short`
  and continue from the baseline commit.
- Before changing code, read `AGENTS.md` and this file.
- Keep `.env` local only. Never print or commit the real Gemini key.
- Consider starting with protocol/data boundaries before GUI polish so feature
  integration stays clean.
- Next step: finish final audit against every AGENTS.md acceptance item, then
  commit this GUI/game/smoke-test chunk.
