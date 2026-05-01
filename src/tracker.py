import asyncio
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "pycraft.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_users_table(conn: sqlite3.Connection) -> None:
    """Create users table, auth_tokens table, and add user_id column to sessions if missing."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token      TEXT    PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            email      TEXT    NOT NULL,
            expires_at TEXT    NOT NULL
        )
    """)
    existing = {row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
    if "user_id" not in existing:
        conn.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id)")


def init_db() -> None:
    """Create DB tables and run migrations if needed."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT    NOT NULL,
                topic      TEXT    NOT NULL,
                difficulty INTEGER NOT NULL,
                question   TEXT    NOT NULL,
                code       TEXT    NOT NULL,
                score      INTEGER NOT NULL,
                feedback   TEXT    NOT NULL
            )
        """)
        init_users_table(conn)


def create_user(email: str, password_hash: str) -> int:
    """Insert a new user and return their id. Raises ValueError on duplicate email."""
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        with _connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, password_hash, created_at),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Email already registered: {email}")


def create_auth_token(user_id: int, email: str) -> str:
    """Generate a 30-day session token, store it, and return it."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO auth_tokens (token, user_id, email, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, email, expires_at),
        )
    return token


def get_user_by_token(token: str) -> dict | None:
    """Return {id, email} for a valid, unexpired token, or None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT user_id, email FROM auth_tokens WHERE token = ? AND expires_at > ?",
            (token, datetime.now(timezone.utc).isoformat()),
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "email": row[1]}


def delete_auth_token(token: str) -> None:
    """Remove a session token (logout)."""
    with _connect() as conn:
        conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))


def get_user_by_email(email: str) -> dict | None:
    """Return {id, email, password_hash} for the user or None if not found."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "email": row[1], "password_hash": row[2]}


def save_session(
    topic: str,
    difficulty: int,
    question: str,
    code: str,
    score: int,
    feedback: str,
    user_id: int | None = None,
) -> None:
    """Insert one completed session row."""
    if not (0 <= score <= 10):
        raise ValueError(f"score must be 0-10, got {score}")

    timestamp = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (timestamp, topic, difficulty, question, code, score, feedback, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, topic, difficulty, question, code, score, feedback, user_id),
        )


def get_recent_questions(topic: str, limit: int = 10, user_id: int | None = None) -> list[str]:
    """Return the last `limit` question texts for a topic, newest first."""
    with _connect() as conn:
        if user_id is not None:
            rows = conn.execute(
                "SELECT question FROM sessions WHERE topic = ? AND user_id = ? ORDER BY id DESC LIMIT ?",
                (topic, user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT question FROM sessions WHERE topic = ? ORDER BY id DESC LIMIT ?",
                (topic, limit),
            ).fetchall()
    return [row[0] for row in rows]


def get_recent_scores(topic: str, limit: int = 5, user_id: int | None = None) -> list[int]:
    """Return the last `limit` scores for a topic, newest first."""
    with _connect() as conn:
        if user_id is not None:
            rows = conn.execute(
                "SELECT score FROM sessions WHERE topic = ? AND user_id = ? ORDER BY id DESC LIMIT ?",
                (topic, user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT score FROM sessions WHERE topic = ? ORDER BY id DESC LIMIT ?",
                (topic, limit),
            ).fetchall()
    return [row[0] for row in rows]


def compute_next_difficulty(scores: list[int], current: int) -> int:
    """Return adjusted difficulty based on rolling avg of scores; no change if fewer than 3 scores."""
    if len(scores) < 3:
        return current
    avg = sum(scores) / len(scores)
    if avg >= 8:
        return min(current + 1, 5)
    if avg < 5:
        return max(current - 1, 1)
    return current


def _fetch_topic_stats(topic: str, user_id: int | None = None) -> dict:
    with _connect() as conn:
        if user_id is not None:
            row = conn.execute(
                """
                SELECT COUNT(*), ROUND(AVG(score), 1), difficulty
                FROM sessions
                WHERE topic = ? AND user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (topic, user_id),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT COUNT(*), ROUND(AVG(score), 1), difficulty
                FROM sessions
                WHERE topic = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (topic,),
            ).fetchone()
    count, avg_score, last_difficulty = row
    return {"topic": topic, "count": count, "avg_score": avg_score, "last_difficulty": last_difficulty}


def _fetch_all_topic_stats(user_id: int | None = None) -> list[dict]:
    with _connect() as conn:
        if user_id is not None:
            rows = conn.execute(
                """
                SELECT s.topic,
                       COUNT(*) as count,
                       ROUND(AVG(s.score), 1) as avg_score,
                       (SELECT difficulty FROM sessions WHERE topic = s.topic AND user_id = ? ORDER BY id DESC LIMIT 1) as last_difficulty
                FROM sessions s
                WHERE s.user_id = ?
                GROUP BY s.topic
                ORDER BY s.topic
                """,
                (user_id, user_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT s.topic,
                       COUNT(*) as count,
                       ROUND(AVG(s.score), 1) as avg_score,
                       (SELECT difficulty FROM sessions WHERE topic = s.topic ORDER BY id DESC LIMIT 1) as last_difficulty
                FROM sessions s
                GROUP BY s.topic
                ORDER BY s.topic
                """
            ).fetchall()
    return [
        {"topic": r[0], "count": r[1], "avg_score": r[2], "last_difficulty": r[3]}
        for r in rows
    ]


async def get_topic_stats(topic: str, user_id: int | None = None) -> dict:
    """Return {topic, count, avg_score, last_difficulty} for a single topic."""
    return await asyncio.to_thread(_fetch_topic_stats, topic, user_id)


async def get_all_topic_stats(user_id: int | None = None) -> list[dict]:
    """Return per-topic stats for all topics that have at least one session."""
    return await asyncio.to_thread(_fetch_all_topic_stats, user_id)
