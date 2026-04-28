# Spec 03: User Authentication

## Goal
Add email/password login so multiple users can share one PyCraft AI instance with isolated session history. Each user's performance data is scoped to their account.

## Files
- `tracker.py` — add `users` table DDL and user CRUD functions.
- `src/auth.py` — new module: password hashing, login/register logic.
- `src/app.py` — gate main UI behind login; store `user_id` in session state.
- `pycraft.db` — gains a `users` table and a `user_id` FK on `sessions`.

## Design

**Auth flow:**
1. App starts, checks `st.session_state.user_id`.
2. If not set, render login/register form (email + password, no sidebar).
3. On login: hash submitted password, compare against `users.password_hash`, set `session_state.user_id`.
4. On register: validate email uniqueness, hash password, insert user, set `session_state.user_id`.
5. All subsequent DB calls pass `user_id` to scope data.

**Password hashing:** `bcrypt` via `bcrypt` library. No plaintext storage.

**Schema changes:**

```sql
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL  -- ISO 8601
);

-- Add user_id FK to sessions (new installs only; migration note below)
ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id);
```

> Migration: existing rows get `user_id = NULL`; app handles NULL as legacy/anonymous data.

## Functions / Classes

| Name | Signature | Returns | Notes |
|------|-----------|---------|-------|
| `init_users_table` | `() -> None` | None | Called from `init_db()`; idempotent |
| `create_user` | `(email: str, password_hash: str) -> int` | New `user_id` | Raises `ValueError` on duplicate email |
| `get_user_by_email` | `(email: str) -> dict \| None` | `{id, email, password_hash}` or None | |
| `hash_password` | `(password: str) -> str` | bcrypt hash string | In `auth.py` |
| `verify_password` | `(password: str, hash: str) -> bool` | bool | In `auth.py` |
| `login_ui` | `() -> None` | None | Renders login/register form in `app.py`; sets `st.session_state.user_id` on success |

## Constraints
- All DB ops (including user queries) via `tracker.py` only.
- Passwords hashed with `bcrypt`; never stored or logged in plaintext.
- `user_id` added to all `save_session()` calls; `get_recent_scores()` and stats functions filter by `user_id`.
- No sidebar widgets; login form renders inline in the main area.
- No JWT, no session tokens, no external auth providers; Streamlit session state is the auth boundary (local use).
- `bcrypt` added to `requirements.txt`.

## Acceptance Criteria
- Registering with a new email creates a user and lands on the main app.
- Registering with a duplicate email shows an error, no crash.
- Correct password logs in and sets `session_state.user_id`.
- Wrong password shows an error and does not set `user_id`.
- Two users have fully independent progress stats.
- Existing sessions with `user_id = NULL` do not break the app.
- `init_db()` remains idempotent on fresh and pre-existing databases.
