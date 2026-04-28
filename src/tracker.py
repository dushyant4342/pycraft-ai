import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "pycraft.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create DB and sessions table if they don't exist."""
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


def save_session(
    topic: str,
    difficulty: int,
    question: str,
    code: str,
    score: int,
    feedback: str,
) -> None:
    """Insert one completed session row."""
    if not (0 <= score <= 10):
        raise ValueError(f"score must be 0-10, got {score}")

    timestamp = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (timestamp, topic, difficulty, question, code, score, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, topic, difficulty, question, code, score, feedback),
        )


def get_recent_scores(topic: str, limit: int = 5) -> list[int]:
    """Return the last `limit` scores for a topic, newest first."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT score FROM sessions
            WHERE topic = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (topic, limit),
        ).fetchall()
    return [row[0] for row in rows]
