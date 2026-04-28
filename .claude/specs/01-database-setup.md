# Spec 01: Database Setup

## Goal
Persist user sessions and performance history using SQLite. No server required.

## File
`pycraft.db` -- auto-created on first run via `tracker.py`.

## Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT    NOT NULL,
    topic     TEXT    NOT NULL,
    difficulty INTEGER NOT NULL,
    question  TEXT    NOT NULL,
    code      TEXT    NOT NULL,
    score     INTEGER NOT NULL,  -- 0-10
    feedback  TEXT    NOT NULL
);
```

## Functions in `tracker.py`

| Function | Signature | Returns |
|---|---|---|
| `init_db()` | `() -> None` | Creates DB + table if not exists |
| `save_session()` | `(topic, difficulty, question, code, score, feedback) -> None` | Inserts one row |
| `get_recent_scores()` | `(topic, limit=5) -> list[int]` | Last N scores for a topic |

## Constraints
- All SQL in `tracker.py` only -- no inline queries elsewhere
- `timestamp` stored as ISO 8601 string
- `score` validated as int in range 0-10 before insert
- DB path resolved relative to project root: `Path(__file__).parent.parent / "pycraft.db"`

## Acceptance Criteria
- `init_db()` is idempotent (safe to call on every app start)
- `get_recent_scores("lists", 5)` returns up to 5 most recent scores for that topic, newest first
- All functions work without a running server
