# tests/test_custom_topic.py
#
# Tests for the custom-topic feature:
#   - Expanded TOPICS list in session.py and llm.py (16 topics)
#   - custom_topic overrides pill selection in load_next_question()
#   - custom_topic / topic_locked state after load_next_question() completes
#   - init_session() default for custom_topic
#   - _DIFF_DESCRIPTORS existence and completeness in llm.py
#   - TOPICS parity between session.py and llm.py

import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Resolve src/ without importing app.py or components.py
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import llm
import session
import tracker

# ---------------------------------------------------------------------------
# Expected full topic list (single source of truth for tests)
# ---------------------------------------------------------------------------

_EXPECTED_TOPICS = [
    "strings",
    "lists",
    "dicts",
    "functions",
    "OOP",
    "comprehensions",
    "async",
    "linked lists",
    "hash tables",
    "stacks & queues",
    "trees & BST",
    "heaps",
    "graphs",
    "sorting algorithms",
    "recursion",
    "dynamic programming",
]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db(tmp_path: Path):
    """Isolated SQLite DB; patches tracker.DB_PATH for the test duration."""
    db_path = tmp_path / "test.db"
    with patch.object(tracker, "DB_PATH", db_path):
        tracker.init_db()
        user_id = tracker.create_user("test@example.com", "dummy_hash")
        yield db_path, user_id


@pytest.fixture()
def session_state():
    """
    Provide a plain dict that acts as st.session_state for the duration
    of one test.  Patches streamlit.session_state on the already-imported
    session module so session.py's attribute lookups hit our dict.
    """
    state: dict = {}

    class _StateProxy:
        """Minimal proxy: attribute and item access/assignment delegate to the dict."""

        def __getattr__(self, key: str):
            try:
                return state[key]
            except KeyError:
                raise AttributeError(key)

        def __setattr__(self, key: str, value):
            state[key] = value

        def __getitem__(self, key: str):
            return state[key]

        def __setitem__(self, key: str, value):
            state[key] = value

        def __contains__(self, key: str) -> bool:
            return key in state

        def get(self, key: str, default=None):
            return state.get(key, default)

        def update(self, mapping: dict):
            state.update(mapping)

    proxy = _StateProxy()
    # Patch st.session_state in the session module's namespace
    with patch.object(session.st, "session_state", proxy):
        yield state


@pytest.fixture()
def loaded_state(session_state: dict, db):
    """
    session_state pre-populated with the minimum keys load_next_question()
    reads, plus a real user_id from the isolated DB.  LLM and DB async
    calls are mocked so no real I/O happens.
    """
    _, user_id = db
    session_state["user_id"] = user_id
    session_state["topic"] = "lists"
    session_state["custom_topic"] = ""
    session_state["difficulty"] = 1
    return session_state


# ---------------------------------------------------------------------------
# 1. Expanded TOPICS list - session.py
# ---------------------------------------------------------------------------


class TestSessionTopics:
    def test_topics_has_exactly_16_items(self):
        assert len(session.TOPICS) == 16

    def test_topics_contains_all_original_seven(self):
        original = {"strings", "lists", "dicts", "functions", "OOP", "comprehensions", "async"}
        assert original.issubset(set(session.TOPICS))

    @pytest.mark.parametrize(
        "topic",
        [
            "linked lists",
            "hash tables",
            "stacks & queues",
            "trees & BST",
            "heaps",
            "graphs",
            "sorting algorithms",
            "recursion",
            "dynamic programming",
        ],
    )
    def test_topics_contains_new_ds_topic(self, topic: str):
        assert topic in session.TOPICS

    def test_topics_is_a_list(self):
        assert isinstance(session.TOPICS, list)

    def test_topics_has_no_duplicates(self):
        assert len(session.TOPICS) == len(set(session.TOPICS))


# ---------------------------------------------------------------------------
# 2. Custom topic overrides pill selection in load_next_question()
# ---------------------------------------------------------------------------


class TestCustomTopicOverrides:
    def _mock_llm_result(self, topic: str, difficulty: int) -> dict:
        return {"question": "Write a function.", "topic": topic, "difficulty": difficulty}

    def test_custom_topic_overrides_pill_selection(self, loaded_state: dict, db):
        """When custom_topic is set, load_next_question passes it to next_question(), not session topic."""
        loaded_state["custom_topic"] = "recursion"
        loaded_state["topic"] = "lists"  # pill selection; should be ignored

        captured: list[str] = []

        async def fake_next_question(topic, difficulty, history, past_questions=None):
            captured.append(topic)
            return {"question": "Q", "topic": topic, "difficulty": difficulty}

        async def fake_get_topic_stats(topic, user_id=None):
            return {"count": 0, "last_difficulty": 1, "avg_score": None, "topic": topic}

        with (
            patch.object(session, "next_question", fake_next_question),
            patch.object(session, "get_topic_stats", fake_get_topic_stats),
            patch.object(session, "get_recent_scores", return_value=[]),
            patch.object(session, "get_recent_questions", return_value=[]),
            patch.object(session, "compute_next_difficulty", return_value=1),
        ):
            session.load_next_question()

        assert captured == ["recursion"], (
            "load_next_question should pass custom_topic to the LLM, not the pill topic"
        )

    def test_pill_topic_used_when_custom_topic_empty(self, loaded_state: dict, db):
        """When custom_topic is empty, load_next_question uses st.session_state.topic."""
        loaded_state["custom_topic"] = ""
        loaded_state["topic"] = "dicts"

        captured: list[str] = []

        async def fake_next_question(topic, difficulty, history, past_questions=None):
            captured.append(topic)
            return {"question": "Q", "topic": topic, "difficulty": difficulty}

        async def fake_get_topic_stats(topic, user_id=None):
            return {"count": 0, "last_difficulty": 1, "avg_score": None, "topic": topic}

        with (
            patch.object(session, "next_question", fake_next_question),
            patch.object(session, "get_topic_stats", fake_get_topic_stats),
            patch.object(session, "get_recent_scores", return_value=[]),
            patch.object(session, "get_recent_questions", return_value=[]),
            patch.object(session, "compute_next_difficulty", return_value=1),
        ):
            session.load_next_question()

        assert captured == ["dicts"]

    def test_whitespace_only_custom_topic_falls_back_to_pill(self, loaded_state: dict, db):
        """Whitespace in custom_topic must not be treated as a valid custom topic."""
        loaded_state["custom_topic"] = "   "
        loaded_state["topic"] = "functions"

        captured: list[str] = []

        async def fake_next_question(topic, difficulty, history, past_questions=None):
            captured.append(topic)
            return {"question": "Q", "topic": topic, "difficulty": difficulty}

        async def fake_get_topic_stats(topic, user_id=None):
            return {"count": 0, "last_difficulty": 1, "avg_score": None, "topic": topic}

        with (
            patch.object(session, "next_question", fake_next_question),
            patch.object(session, "get_topic_stats", fake_get_topic_stats),
            patch.object(session, "get_recent_scores", return_value=[]),
            patch.object(session, "get_recent_questions", return_value=[]),
            patch.object(session, "compute_next_difficulty", return_value=1),
        ):
            session.load_next_question()

        assert captured == ["functions"], (
            "Whitespace-only custom_topic must be treated as empty; pill topic should be used"
        )


# ---------------------------------------------------------------------------
# 3. State after load_next_question() completes
# ---------------------------------------------------------------------------


class TestStateAfterLoadNextQuestion:
    def _run_load(self, loaded_state: dict, custom_topic: str = ""):
        """Helper: run load_next_question() with all external calls mocked."""
        loaded_state["custom_topic"] = custom_topic

        async def fake_next_question(topic, difficulty, history, past_questions=None):
            return {"question": "Q", "topic": topic, "difficulty": difficulty}

        async def fake_get_topic_stats(topic, user_id=None):
            return {"count": 0, "last_difficulty": 1, "avg_score": None, "topic": topic}

        with (
            patch.object(session, "next_question", fake_next_question),
            patch.object(session, "get_topic_stats", fake_get_topic_stats),
            patch.object(session, "get_recent_scores", return_value=[]),
            patch.object(session, "get_recent_questions", return_value=[]),
            patch.object(session, "compute_next_difficulty", return_value=1),
        ):
            session.load_next_question()

    def test_custom_topic_cleared_after_load(self, loaded_state: dict, db):
        """custom_topic must be reset to '' once the question is loaded."""
        self._run_load(loaded_state, custom_topic="heaps")
        assert loaded_state.get("custom_topic") == "", (
            "custom_topic should be cleared to '' after load_next_question()"
        )

    def test_topic_locked_is_true_after_load(self, loaded_state: dict, db):
        """topic_locked must be True after load_next_question() completes."""
        loaded_state["topic_locked"] = False
        self._run_load(loaded_state)
        assert loaded_state.get("topic_locked") is True

    def test_custom_topic_cleared_even_when_it_was_empty(self, loaded_state: dict, db):
        """custom_topic must remain '' (not become None or be missing) when it was already empty."""
        self._run_load(loaded_state, custom_topic="")
        assert loaded_state.get("custom_topic") == ""


# ---------------------------------------------------------------------------
# 4. init_session() defaults
# ---------------------------------------------------------------------------


class TestInitSessionDefaults:
    def test_init_session_sets_custom_topic_default(self, session_state: dict):
        """init_session must add custom_topic='' when it is absent."""
        # Ensure key is absent before calling
        session_state.pop("custom_topic", None)
        session.init_session()
        assert "custom_topic" in session_state
        assert session_state["custom_topic"] == ""

    def test_init_session_does_not_overwrite_existing_custom_topic(self, session_state: dict):
        """init_session must not clobber a custom_topic the caller already set."""
        session_state["custom_topic"] = "graphs"
        session.init_session()
        assert session_state["custom_topic"] == "graphs"

    def test_init_session_sets_remaining_defaults_when_state_empty(self, session_state: dict):
        """Smoke-check: other defaults should also be applied on a fresh state."""
        session.init_session()
        assert session_state.get("topic") == "lists"
        assert session_state.get("difficulty") == 1
        assert session_state.get("topic_locked") is False

    def test_init_session_does_not_overwrite_existing_topic(self, session_state: dict):
        """Pre-existing session keys must not be overwritten by init_session()."""
        session_state["topic"] = "OOP"
        session.init_session()
        assert session_state["topic"] == "OOP"


# ---------------------------------------------------------------------------
# 5. _DIFF_DESCRIPTORS in llm.py
# ---------------------------------------------------------------------------


class TestDiffDescriptors:
    def test_diff_descriptors_exists(self):
        assert hasattr(llm, "_DIFF_DESCRIPTORS"), "_DIFF_DESCRIPTORS must exist in llm.py"

    def test_diff_descriptors_has_keys_1_to_5(self):
        assert set(llm._DIFF_DESCRIPTORS.keys()) == {1, 2, 3, 4, 5}

    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
    def test_diff_descriptor_is_non_empty_string(self, level: int):
        desc = llm._DIFF_DESCRIPTORS[level]
        assert isinstance(desc, str) and len(desc.strip()) > 0, (
            f"Descriptor for difficulty {level} must be a non-empty string"
        )

    def test_diff_descriptors_is_a_dict(self):
        assert isinstance(llm._DIFF_DESCRIPTORS, dict)


# ---------------------------------------------------------------------------
# 6. TOPICS parity between session.py and llm.py
# ---------------------------------------------------------------------------


class TestTopicsParity:
    def test_llm_topics_has_exactly_16_items(self):
        assert len(llm.TOPICS) == 16

    def test_llm_and_session_topics_contain_same_items(self):
        """Order may differ; the set of topics must be identical."""
        assert set(llm.TOPICS) == set(session.TOPICS), (
            "llm.TOPICS and session.TOPICS must contain the same 16 topics"
        )

    def test_llm_topics_contains_all_expected_topics(self):
        assert set(llm.TOPICS) == set(_EXPECTED_TOPICS)

    def test_session_topics_contains_all_expected_topics(self):
        assert set(session.TOPICS) == set(_EXPECTED_TOPICS)

    @pytest.mark.parametrize("topic", _EXPECTED_TOPICS)
    def test_each_expected_topic_in_both_modules(self, topic: str):
        assert topic in llm.TOPICS, f"'{topic}' missing from llm.TOPICS"
        assert topic in session.TOPICS, f"'{topic}' missing from session.TOPICS"
