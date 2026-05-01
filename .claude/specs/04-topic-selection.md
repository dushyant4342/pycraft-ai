# Spec 04: Topic Selection

## Goal
Expose topic selection in the UI so users can deliberately choose which Python topic to practice. Currently `topic` is hardcoded to `"lists"` in `init_session()` and never surfaced as a user control. The start screen already hints at this ("Pick a topic or let AI choose for you") but provides no mechanism to do it.

## Files
- `src/app.py` — add topic picker to the start screen; wire selection into `load_next_question()`.

No other files change; `tracker.py`, `llm.py`, and `auth.py` are untouched.

## Design

**Topic picker placement:** Render a pill-grid of topic buttons on the start screen (before a question is loaded). One extra pill labelled "Random" lets the LLM choose freely. Selection sets `st.session_state.topic`; clicking "Start" then calls `load_next_question()` as today.

**Session state:**
- Add `"topic_locked": False` to `init_session()` defaults. Set to `True` once a question is loaded; reset to `False` on "Next Question".
- While `topic_locked` is `True`, hide the picker so mid-session topic switching is prevented.

**"Random" mode:** When the user picks Random, `st.session_state.topic` is set to `""`. `load_next_question()` already passes `topic` to `next_question()`; update that call to pass `None` (or `""`) and update the system prompt in `llm.py` to pick freely when topic is empty. After the LLM returns, set `st.session_state.topic` from `result["topic"]` as today.

**Difficulty carry-over:** When the user switches to a topic they have history in, seed difficulty from `get_topic_stats(topic, user_id)["last_difficulty"]` instead of resetting to 1.

## Functions / Classes

| Name | Signature | Returns | Notes |
|------|-----------|---------|-------|
| `render_topic_picker` | `() -> None` | None | Renders pill-grid in `app.py`; sets `st.session_state.topic` on click |
| `load_next_question` | `() -> None` (modified) | None | Seeds difficulty from topic history before calling LLM |
| `init_session` | `() -> None` (modified) | None | Adds `topic_locked: False` to defaults |
| `next_question` | `(topic: str \| None, difficulty: int, history: list) -> dict` (modified) | dict | Treats `None`/`""` topic as free-choice in system prompt |

## Constraints
- TOPICS list stays exactly: `strings`, `lists`, `dicts`, `functions`, `OOP`, `comprehensions`, `async`.
- No sidebar; picker renders in main column only.
- All DB ops via `tracker.py` only.
- All LLM calls remain async; `asyncio.run()` at call site.
- Picker is hidden once a question is active (`topic_locked = True`).
- Score and difficulty invariants unchanged (score 0-10, difficulty 1-5).
- `get_topic_stats()` call is async; wrap with `asyncio.run()`.

## Acceptance Criteria
- Start screen shows a pill for each of the 7 topics plus a "Random" pill.
- Selecting a topic pill highlights it and updates `st.session_state.topic`.
- Clicking "Start" loads a question for the selected topic.
- "Random" generates a question for a topic chosen by the LLM.
- When switching to a topic with prior history, difficulty is seeded from last known level, not reset to 1.
- Topic picker is not visible while a question is displayed.
- Topic picker reappears after the user clicks "Next Question".
- Existing session flow (submit, score, feedback, next) is unaffected.