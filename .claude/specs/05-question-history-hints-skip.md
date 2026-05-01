# Spec 05: Question History, Difficulty Picker, Skip, and Hints

## Goal
Give users control over their practice session and visibility into past work. Four additions:
1. **History tab** - browse previous submissions (code, score, feedback) per topic.
2. **Difficulty picker** - let users override the auto-computed difficulty at session start.
3. **Skip question** - discard the current question and load a new one without recording a score.
4. **Hint button** - request an incremental hint from the LLM without revealing the full solution.

## Files
- `src/app.py` - history tab UI, difficulty picker on start screen, skip button, hint button, hint state.
- `src/llm.py` - add `get_hint()` async function.
- `src/tracker.py` - add `get_session_history()` query function.

## Design

### History Tab
Add a second tab alongside the main practice area using `st.tabs(["Practice", "History"])`.

**History tab layout:**
- Topic filter: selectbox over the 7 topics + "All".
- Table rendered with `st.dataframe` showing columns: `date`, `topic`, `difficulty`, `score`, `code` (truncated to 120 chars), `feedback` (truncated to 200 chars).
- Clicking a row expands an `st.expander` with full code (via `streamlit-ace` in read-only mode) and full feedback.
- Rows sorted by `submitted_at` descending; limited to last 50 rows per query.

**DB query:** reads `sessions` table joined with `users` to filter by `user_id`.

### Difficulty Picker
On the start screen (before a question loads), render a difficulty slider `st.select_slider` from 1 to 5 next to the topic picker.

- Default value: seeded from `get_topic_stats(topic, user_id)["last_difficulty"]` when a topic is selected, else 3.
- Stores selection in `st.session_state.difficulty`.
- Label shows the current level name: `{1: "Beginner", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert"}`.
- Hidden once `topic_locked = True` (same flag from spec 04).
- Auto-adaptation still runs after each submission and updates `st.session_state.difficulty` for the next question.

### Skip Question
A "Skip" button rendered below the code editor, alongside the existing "Submit" button.

- On click: increments `st.session_state.skip_count` (persists in session only, not DB), calls `load_next_question()`, then `st.rerun()`.
- No score is written to DB.
- Skip count shown as a small `st.caption` next to the button: "Skipped: N this session".
- Session state key: `skip_count: int = 0` added to `init_session()`.

### Hint System
A "Get Hint" button rendered below the question card.

**State:**
- `hint_level: int = 0` in session state (reset to 0 each new question).
- `hints: list[str] = []` in session state (reset each new question).
- Max 3 hints per question (button disabled after 3).

**UX flow:**
1. User clicks "Get Hint"; `hint_level` increments.
2. `asyncio.run(get_hint(question, code_so_far, hint_level))` is called.
3. Hint text appended to `hints` and all hints rendered in an `st.expander("Hints")` that auto-opens.
4. Button label updates: "Get Hint (1/3)", "Get Hint (2/3)", "Get Hint (3/3)" then disabled.

**Hint progression (enforced in prompt):**
- Level 1: conceptual nudge only, no code.
- Level 2: pseudocode or algorithm outline.
- Level 3: partial code snippet (not the full solution).

## Functions / Classes

| Name | Signature | Returns | Notes |
|------|-----------|---------|-------|
| `get_session_history` | `(user_id: int, topic: str \| None, limit: int = 50) -> list[dict]` | List of session dicts | `tracker.py`; topic=None returns all topics |
| `get_hint` | `(question: str, code: str, hint_level: int) -> str` | Hint text string | `llm.py`; async; system prompt enforces level-appropriate hints |
| `render_history_tab` | `() -> None` | None | `app.py`; renders full history tab content |
| `render_difficulty_picker` | `(topic: str) -> None` | None | `app.py`; select_slider + difficulty label |
| `init_session` | `() -> None` (modified) | None | Adds `skip_count`, `hint_level`, `hints` to defaults |
| `load_next_question` | `() -> None` (modified) | None | Resets `hint_level` and `hints` on each new question |

## Constraints
- All DB ops via `tracker.py` only; no raw `sqlite3` in `app.py`.
- All LLM calls async; `asyncio.run()` at Streamlit call site.
- `get_hint()` must never reveal the complete solution; enforced via system prompt instruction.
- Max hints per question: 3 (hard limit, button disabled in UI and ignored in backend if exceeded).
- Skip does not write any row to the `sessions` table.
- History tab only shows sessions for the currently logged-in `user_id`.
- No sidebar; all UI in main column.
- Score and difficulty invariants unchanged (score 0-10, difficulty 1-5).
- Topic list unchanged: `strings`, `lists`, `dicts`, `functions`, `OOP`, `comprehensions`, `async`.
- Difficulty picker hidden while a question is active (`topic_locked = True`).

## Acceptance Criteria
- History tab displays past sessions for the logged-in user, sorted newest first.
- Filtering by topic shows only rows for that topic.
- Clicking a history row expands the full code and feedback.
- Difficulty slider appears on the start screen; default seeds from last known difficulty for the selected topic.
- Selected difficulty is used as the starting point for `next_question()`.
- Auto-adaptation still runs after submission and updates difficulty for the next round.
- "Skip" button loads a new question without writing a session row.
- Skip counter increments and displays correctly each skip.
- "Get Hint" button appears below the question card and is disabled after 3 clicks.
- Hint 1 contains no code; hint 2 contains pseudocode; hint 3 contains a partial snippet.
- Hints persist in the expander while the current question is active; reset on next question.
- All new UI elements match the existing dark theme and accent colors.
