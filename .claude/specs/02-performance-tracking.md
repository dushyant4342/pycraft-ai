# Spec 02: Performance Tracking

## Goal
Expose per-topic and overall performance analytics from SQLite so the app can drive adaptive difficulty and show progress to the user.

## Files
- `tracker.py` — add analytics query functions (no schema changes needed; builds on Spec 01 sessions table)
- `app.py` — call analytics functions to render a lightweight progress view and drive difficulty adjustment

## Design

All reads hit the `sessions` table from Spec 01. No new tables required.

**Adaptive difficulty logic** (called after every submission):
1. Fetch last 5 scores for the current topic via `get_recent_scores(topic, 5)`.
2. If `len(scores) >= 3` and `avg >= 8`: bump difficulty (cap at 5).
3. If `len(scores) >= 3` and `avg < 5`: drop difficulty (floor at 1).
4. Otherwise: keep current difficulty.

**Progress view** (rendered in main area, not sidebar):
- Per-topic row: topic name, sessions count, avg score, current difficulty.
- Only topics with at least one session are shown.

## Functions / Classes

| Name | Signature | Returns | Notes |
|------|-----------|---------|-------|
| `get_topic_stats` | `(topic: str) -> dict` | `{count, avg_score, last_difficulty}` | Async; single query with AVG + COUNT |
| `get_all_topic_stats` | `() -> list[dict]` | List of stat dicts per topic | Async; one query across all topics |
| `compute_next_difficulty` | `(scores: list[int], current: int) -> int` | Next difficulty int 1-5 | Pure function, no DB access |

## Constraints
- All DB queries in `tracker.py` only; `app.py` calls functions, never raw SQL.
- `compute_next_difficulty` requires at least 3 scores before adjusting; returns `current` otherwise.
- `avg_score` rounded to one decimal place.
- Difficulty always clamped to `[1, 5]`; score always `int` in `[0, 10]`.
- No sidebar widgets; progress view renders inline in the main Streamlit area.

## Acceptance Criteria
- `compute_next_difficulty([9,8,9,8,9], 3)` returns `4`.
- `compute_next_difficulty([3,4,3], 2)` returns `1`.
- `compute_next_difficulty([7,8], 2)` returns `2` (fewer than 3 scores, no change).
- `get_all_topic_stats()` returns only topics present in the sessions table.
- Progress view displays without error when the DB is empty.
