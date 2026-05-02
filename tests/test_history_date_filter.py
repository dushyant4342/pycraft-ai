# tests/test_history_date_filter.py
#
# Tests for the date-filter feature added to _fetch_session_history /
# get_session_history in src/tracker.py (spec 06).
#
# Strategy: patch tracker.DB_PATH to a tmp_path-scoped SQLite file, initialise
# the schema via init_db(), insert rows directly via sqlite3 with explicit ISO-8601
# timestamps, then call the public async get_session_history() to verify SQL
# filtering is correct.  No real pycraft.db is touched.

import asyncio
import sqlite3
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

# Make `import tracker` resolve to src/tracker.py
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import tracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SESSION_DEFAULTS = dict(
    difficulty=1,
    question="What is a list?",
    code="x = []",
    score=5,
    feedback="OK",
)


def _insert_session(
    conn: sqlite3.Connection,
    user_id: int,
    timestamp: str,
    topic: str = "lists",
    **overrides,
) -> None:
    """Insert one session row with an explicit timestamp string."""
    d = {**_SESSION_DEFAULTS, **overrides, "topic": topic}
    conn.execute(
        """
        INSERT INTO sessions
            (timestamp, topic, difficulty, question, code, score, feedback, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            d["topic"],
            d["difficulty"],
            d["question"],
            d["code"],
            d["score"],
            d["feedback"],
            user_id,
        ),
    )
    conn.commit()


def _run(coro):
    """Thin wrapper so tests stay readable without async def boilerplate."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(tmp_path: Path):
    """
    Yield a (db_path, user_id) tuple backed by an isolated SQLite file.

    Patches tracker.DB_PATH for the duration of the test so every tracker
    function in this process talks to the temp file, not pycraft.db.
    """
    db_path = tmp_path / "pycraft_test.db"
    with patch.object(tracker, "DB_PATH", db_path):
        tracker.init_db()
        user_id = tracker.create_user("test@example.com", "dummy_hash")
        yield db_path, user_id


# ---------------------------------------------------------------------------
# Acceptance criteria tests
# ---------------------------------------------------------------------------

class TestNoDateFilter:
    """AC-1: no date params returns all sessions (backward-compatible)."""

    def test_returns_all_sessions_when_no_date_params(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-03-01T10:00:00+00:00")
            _insert_session(conn, user_id, "2026-04-15T12:00:00+00:00")
            _insert_session(conn, user_id, "2026-05-01T08:00:00+00:00")

        result = _run(tracker.get_session_history(user_id))
        assert len(result) == 3

    def test_returns_empty_list_for_user_with_no_sessions(self, db):
        _, user_id = db
        result = _run(tracker.get_session_history(user_id))
        assert result == []


class TestStartDateFilter:
    """AC-2: start_date excludes sessions before that date."""

    def test_excludes_sessions_before_start_date(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-03-31T23:59:59+00:00")  # before
            _insert_session(conn, user_id, "2026-04-01T00:00:00+00:00")  # on boundary
            _insert_session(conn, user_id, "2026-04-10T10:00:00+00:00")  # after

        result = _run(
            tracker.get_session_history(user_id, start_date=date(2026, 4, 1))
        )
        timestamps = [r["timestamp"] for r in result]
        assert all("2026-03-31" not in ts for ts in timestamps)
        assert len(result) == 2

    def test_start_date_boundary_is_inclusive(self, db):
        """A session exactly on start_date must be included (closed interval)."""
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-01T00:00:00+00:00")

        result = _run(
            tracker.get_session_history(user_id, start_date=date(2026, 4, 1))
        )
        assert len(result) == 1


class TestEndDateFilter:
    """AC-3: end_date excludes sessions after that date."""

    def test_excludes_sessions_after_end_date(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-10T10:00:00+00:00")  # before
            _insert_session(conn, user_id, "2026-04-20T23:59:59+00:00")  # on boundary
            _insert_session(conn, user_id, "2026-04-21T00:00:00+00:00")  # after

        result = _run(
            tracker.get_session_history(user_id, end_date=date(2026, 4, 20))
        )
        timestamps = [r["timestamp"] for r in result]
        assert all("2026-04-21" not in ts for ts in timestamps)
        assert len(result) == 2

    def test_end_date_boundary_is_inclusive(self, db):
        """A session exactly on end_date must be included (closed interval)."""
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-20T23:59:59+00:00")

        result = _run(
            tracker.get_session_history(user_id, end_date=date(2026, 4, 20))
        )
        assert len(result) == 1


class TestCombinedDateRange:
    """AC-4: start_date + end_date together return only the closed range."""

    def test_returns_only_sessions_in_range(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-03-31T10:00:00+00:00")  # before
            _insert_session(conn, user_id, "2026-04-01T00:00:00+00:00")  # start boundary
            _insert_session(conn, user_id, "2026-04-10T12:00:00+00:00")  # inside
            _insert_session(conn, user_id, "2026-04-30T23:59:59+00:00")  # end boundary
            _insert_session(conn, user_id, "2026-05-01T00:00:01+00:00")  # after

        result = _run(
            tracker.get_session_history(
                user_id,
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
            )
        )
        assert len(result) == 3
        for row in result:
            day = row["timestamp"][:10]
            assert "2026-04-01" <= day <= "2026-04-30"

    def test_both_boundaries_inclusive(self, db):
        """Sessions on exactly start_date and end_date both appear in results."""
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-01T00:00:00+00:00")
            _insert_session(conn, user_id, "2026-04-30T23:59:59+00:00")

        result = _run(
            tracker.get_session_history(
                user_id,
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
            )
        )
        assert len(result) == 2

    def test_single_day_range(self, db):
        """start_date == end_date returns only sessions from that one day."""
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-15T08:00:00+00:00")
            _insert_session(conn, user_id, "2026-04-15T20:00:00+00:00")
            _insert_session(conn, user_id, "2026-04-14T23:59:59+00:00")
            _insert_session(conn, user_id, "2026-04-16T00:00:00+00:00")

        result = _run(
            tracker.get_session_history(
                user_id,
                start_date=date(2026, 4, 15),
                end_date=date(2026, 4, 15),
            )
        )
        assert len(result) == 2
        assert all(r["timestamp"].startswith("2026-04-15") for r in result)


class TestDateRangeWithTopicFilter:
    """AC-5: date range combined with topic filter returns rows matching both."""

    def test_topic_and_date_range_combined(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            # matching: correct topic + inside range
            _insert_session(conn, user_id, "2026-04-10T10:00:00+00:00", topic="lists")
            # wrong topic, inside range
            _insert_session(conn, user_id, "2026-04-10T11:00:00+00:00", topic="dicts")
            # correct topic, outside range
            _insert_session(conn, user_id, "2026-03-01T10:00:00+00:00", topic="lists")

        result = _run(
            tracker.get_session_history(
                user_id,
                topic="lists",
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
            )
        )
        assert len(result) == 1
        assert result[0]["topic"] == "lists"
        assert result[0]["timestamp"].startswith("2026-04-10")

    def test_no_match_when_topic_outside_range(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-03-01T10:00:00+00:00", topic="async")

        result = _run(
            tracker.get_session_history(
                user_id,
                topic="async",
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
            )
        )
        assert result == []


class TestLimitEnforcement:
    """AC-6: limit is respected after date filters are applied."""

    def test_limit_caps_results_within_date_range(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            for day in range(1, 11):  # 10 sessions in April
                ts = f"2026-04-{day:02d}T10:00:00+00:00"
                _insert_session(conn, user_id, ts)

        result = _run(
            tracker.get_session_history(
                user_id,
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
                limit=3,
            )
        )
        assert len(result) == 3

    def test_default_limit_is_50(self, db):
        """Default limit=50: inserting 60 rows returns at most 50."""
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            for i in range(60):
                ts = f"2026-04-01T{i % 24:02d}:00:00+00:00"
                _insert_session(conn, user_id, ts)

        result = _run(tracker.get_session_history(user_id))
        assert len(result) == 50

    def test_limit_with_no_date_filter(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            for day in range(1, 11):
                _insert_session(conn, user_id, f"2026-04-{day:02d}T10:00:00+00:00")

        result = _run(tracker.get_session_history(user_id, limit=5))
        assert len(result) == 5


class TestEmptyResult:
    """AC-7: empty list when no sessions fall in the date range."""

    def test_empty_when_all_sessions_before_start_date(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-01-15T10:00:00+00:00")
            _insert_session(conn, user_id, "2026-02-20T10:00:00+00:00")

        result = _run(
            tracker.get_session_history(user_id, start_date=date(2026, 4, 1))
        )
        assert result == []

    def test_empty_when_all_sessions_after_end_date(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-05-01T10:00:00+00:00")
            _insert_session(conn, user_id, "2026-06-01T10:00:00+00:00")

        result = _run(
            tracker.get_session_history(user_id, end_date=date(2026, 4, 30))
        )
        assert result == []

    def test_empty_when_no_sessions_at_all(self, db):
        _, user_id = db
        result = _run(
            tracker.get_session_history(
                user_id,
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
            )
        )
        assert result == []

    def test_empty_for_wrong_user(self, db):
        """Sessions belonging to a different user must not be returned."""
        db_path, user_id = db
        other_user_id = tracker.create_user("other@example.com", "hash2")
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, other_user_id, "2026-04-10T10:00:00+00:00")

        result = _run(
            tracker.get_session_history(
                user_id,
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 30),
            )
        )
        assert result == []


class TestResultShape:
    """Sanity-check that returned dicts contain the expected keys."""

    def test_result_dict_has_required_keys(self, db):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-10T10:00:00+00:00", topic="OOP", score=7)

        result = _run(tracker.get_session_history(user_id))
        assert len(result) == 1
        row = result[0]
        expected_keys = {"id", "timestamp", "topic", "difficulty", "score", "code", "feedback", "question"}
        assert expected_keys == set(row.keys())

    def test_results_ordered_newest_first(self, db):
        """ORDER BY id DESC: the most recently inserted row comes first."""
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-01T10:00:00+00:00")
            _insert_session(conn, user_id, "2026-04-10T10:00:00+00:00")
            _insert_session(conn, user_id, "2026-04-20T10:00:00+00:00")

        result = _run(tracker.get_session_history(user_id))
        timestamps = [r["timestamp"][:10] for r in result]
        assert timestamps == sorted(timestamps, reverse=True)


class TestAllTopics:
    """Verify the feature works across every valid topic value."""

    @pytest.mark.parametrize("topic", [
        "strings", "lists", "dicts", "functions", "OOP", "comprehensions", "async"
    ])
    def test_date_filter_works_for_each_topic(self, db, topic: str):
        db_path, user_id = db
        with sqlite3.connect(db_path) as conn:
            _insert_session(conn, user_id, "2026-04-10T10:00:00+00:00", topic=topic)
            _insert_session(conn, user_id, "2026-03-01T10:00:00+00:00", topic=topic)

        result = _run(
            tracker.get_session_history(
                user_id,
                topic=topic,
                start_date=date(2026, 4, 1),
            )
        )
        assert len(result) == 1
        assert result[0]["topic"] == topic
