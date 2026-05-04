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

- [ ] GUI: CustomTkinter desktop shell matching the reference screenshots.
- [ ] Chatbot: Gemini-powered bot for direct client interaction.
- [ ] Game: Tkinter Whack-a-Mole with single-player score submission.
- [ ] AI Picture Generation: Pollinations.ai `/aipic:` flow.
- [ ] Summary / Keywords: Gemini `/summary` and `/keywords` over real history.
- [ ] Sentiment Analysis: local TextBlob labels and insight counts.
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

## Next Agent Notes

- First implementation step after this setup should inspect `git status --short`
  and continue from the baseline commit.
- Before changing code, read `AGENTS.md` and this file.
- Keep `.env` local only. Never print or commit the real Gemini key.
- Consider starting with protocol/data boundaries before GUI polish so feature
  integration stays clean.
- Next step: integrate the CustomTkinter GUI/game layer, then run socket smoke
  tests with real server/client processes.
