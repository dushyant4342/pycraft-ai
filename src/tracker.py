import asyncio
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


def _fetch_topic_stats(topic: str) -> dict:
    with _connect() as conn:
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


def _fetch_all_topic_stats() -> list[dict]:
    with _connect() as conn:
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


async def get_topic_stats(topic: str) -> dict:
    """Return {topic, count, avg_score, last_difficulty} for a single topic."""
    return await asyncio.to_thread(_fetch_topic_stats, topic)


async def get_all_topic_stats() -> list[dict]:
    """Return per-topic stats for all topics that have at least one session."""
    return await asyncio.to_thread(_fetch_all_topic_stats)
