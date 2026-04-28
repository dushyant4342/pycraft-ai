# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PyCraft AI

Adaptive Python coding practice app. One question at a time, an LLM reviews submitted code, SQLite tracks performance and adjusts difficulty automatically.

## Commands

```bash
# Run the app
streamlit run src/app.py

# Install dependencies
pip install -r requirements.txt

# Required env var (in .env at repo root)
OPENAI_API_KEY=sk-...
```

## Stack

- **UI**: Streamlit + streamlit-ace (code editor), no sidebar, dark theme via injected CSS
- **LLM**: OpenAI `gpt-4o-mini` via `AsyncOpenAI` (all calls are async, wrapped with `asyncio.run` at Streamlit call sites)
- **DB**: SQLite (`pycraft.db` at repo root) via `sqlite3`, accessed only through `tracker.py`
- **Auth**: bcrypt password hashing in `auth.py`; user identity stored in `st.session_state.user_id`

## Architecture

```
src/
  app.py       — Streamlit entry point: session state, UI rendering, page flow
  auth.py      — Login/register UI + bcrypt helpers; sets session_state.user_id on success
  llm.py       — Two async functions: next_question(), review_code(); both return dicts
  tracker.py   — All DB reads/writes: users table, sessions table, difficulty logic
```

**Request flow:** `app.py` calls `asyncio.run(next_question(...))` to get a question, renders a streamlit-ace editor, then calls `asyncio.run(review_code(...))` on submit. Score + feedback are saved via `tracker.save_session()`, then `st.rerun()` refreshes the UI.

**Difficulty adaptation:** `compute_next_difficulty()` in `tracker.py` reads the last 5 scores for the active topic. avg >= 8 bumps difficulty, avg < 5 drops it, fewer than 3 scores = no change.

## Invariants

- All DB ops go through `tracker.py` only — never `sqlite3` directly in other files
- All LLM calls must be `async`; use `asyncio.run()` at the Streamlit call site
- Score is always `int` in range `[0, 10]`
- Topics: `strings`, `lists`, `dicts`, `functions`, `OOP`, `comprehensions`, `async`
- Difficulty: `int` in range `[1, 5]`
- No sidebar — all UI stays in the main column
- CSS is injected via `st.markdown(..., unsafe_allow_html=True)` in `inject_css()` at the top of `main()`
