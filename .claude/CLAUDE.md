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

# Run tests
pytest

# Run a single test file
pytest tests/test_history_date_filter.py

# Required env var (in .env at repo root)
OPENAI_API_KEY=sk-...
```

## Stack

- **UI**: Streamlit + streamlit-ace (code editor), no sidebar, dark theme via injected CSS
- **LLM**: OpenAI `gpt-4o-mini` via `AsyncOpenAI` (all LLM calls are async, wrapped with `asyncio.run` at Streamlit call sites)
- **DB**: SQLite (`pycraft.db` at repo root) via `sqlite3`, accessed only through `tracker.py`
- **Auth**: bcrypt password hashing in `auth.py`; persistent login via `extra_streamlit_components.CookieManager` (cookie name: `pycraft_session`); user identity stored in `st.session_state.user_id`

## Architecture

```
src/
  app.py          — Streamlit entry point: tab layout (Practice / History), orchestrates render calls
  auth.py         — Login/register UI + bcrypt helpers; sets session_state.user_id on success
  session.py      — Cookie-based session restore (try_restore_session), session state defaults (init_session),
                    and question-loading logic (load_next_question)
  llm.py          — Three async functions: next_question(), review_code(), get_hint(); all return dicts
  tracker.py      — All DB reads/writes: users, auth_tokens, sessions tables; difficulty logic
  components.py   — All Streamlit render functions (render_header, render_question, render_editor,
                    render_history_tab, render_result, render_start_screen, etc.)
  styles.py       — inject_css(): injects full dark-theme CSS via st.markdown(unsafe_allow_html=True)
```

**Request flow:** `app.py` calls `session.load_next_question()`, which calls `asyncio.run(next_question(...))`, renders a streamlit-ace editor via `components.render_editor()`, then calls `asyncio.run(review_code(...))` on submit. Score + feedback are saved via `tracker.save_session()`, then `st.rerun()` refreshes the UI.

**Difficulty adaptation:** `compute_next_difficulty()` in `tracker.py` reads the last 5 scores for the active topic. avg >= 8 bumps difficulty, avg < 5 drops it, fewer than 3 scores = no change.

**Hints:** `get_hint(question, code, hint_level)` in `llm.py` returns a progressive hint string. Max 3 hints per question; `hint_level` tracks how many have been shown.

## Tests

Tests live in `tests/`. `pytest.ini` sets `testpaths = tests` and `asyncio_mode = auto`. Fixtures use `unittest.mock.patch.object(tracker, "DB_PATH", tmp_path)` to isolate each test against a temporary SQLite file; `tracker.init_db()` is called inside the fixture to set up the schema.

## Invariants

- All DB ops go through `tracker.py` only; never `sqlite3` directly in other files
- All LLM calls must be `async`; use `asyncio.run()` at the Streamlit call site
- Score is always `int` in range `[0, 10]`
- Topics: `strings`, `lists`, `dicts`, `functions`, `OOP`, `comprehensions`, `async`
- Difficulty: `int` in range `[1, 5]`
- No sidebar; all UI stays in the main column
- CSS lives entirely in `styles.inject_css()`; do not add inline styles to other files beyond the existing pattern
