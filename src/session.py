import asyncio
import logging
import random
import re

_SAFE_TOPIC_RE = re.compile(r"^[A-Za-z0-9 &_\-/()]+$")
_TOPIC_MAX_LEN = 60


def _sanitize_custom_topic(raw: str) -> str | None:
    topic = raw.strip()[:_TOPIC_MAX_LEN]
    return topic if topic and _SAFE_TOPIC_RE.match(topic) else None

import extra_streamlit_components as stx
import streamlit as st

from llm import next_question
from tracker import (
    compute_next_difficulty,
    delete_auth_token,
    get_recent_questions,
    get_recent_scores,
    get_topic_stats,
    get_user_by_token,
)

log = logging.getLogger("pycraft")

TOPICS = [
    "strings", "lists", "dicts", "functions", "OOP", "comprehensions", "async",
    "linked lists", "hash tables", "stacks & queues", "trees & BST", "heaps",
    "graphs", "sorting algorithms", "recursion", "dynamic programming",
]
_COOKIE_NAME = "pycraft_session"


def _get_cookie_manager() -> stx.CookieManager:
    return stx.CookieManager(key="pycraft_cookie_mgr")


def try_restore_session(cookie_manager: stx.CookieManager) -> None:
    if st.session_state.get("user_id"):
        return
    token = cookie_manager.get(_COOKIE_NAME)
    if not token:
        return
    user = get_user_by_token(token)
    if user:
        st.session_state.user_id = user["id"]
        st.session_state.user_email = user["email"]
    else:
        cookie_manager.delete(_COOKIE_NAME, key="del_stale_cookie")


def _first_name(email: str) -> str:
    username = email.split("@")[0].split(".")[0]
    name = username.rstrip("0123456789")
    return (name or username).capitalize()


def init_session() -> None:
    defaults = {
        "question": None,
        "topic": "lists",
        "custom_topic": "",
        "difficulty": 1,
        "feedback": None,
        "score": None,
        "submitted": False,
        "topic_locked": False,
        "skip_count": 0,
        "hint_level": 0,
        "hints": [],
        "attempt": 1,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def load_next_question() -> None:
    user_id = st.session_state.user_id
    custom_raw = st.session_state.get("custom_topic", "").strip()
    custom = _sanitize_custom_topic(custom_raw) if custom_raw else None
    topic = custom if custom else st.session_state.get("topic", "")
    if not topic:
        topic = random.choice(TOPICS)
        st.session_state.topic = topic
        log.info("random topic selected: %s", topic)
    stats = asyncio.run(get_topic_stats(topic, user_id=user_id))
    if stats["count"] > 0:
        st.session_state.difficulty = stats["last_difficulty"]
        log.info(
            "difficulty seeded from history: topic=%s difficulty=%d (sessions=%d)",
            topic, stats["last_difficulty"], stats["count"],
        )
    history = get_recent_scores(topic, limit=5, user_id=user_id)
    past_questions = get_recent_questions(topic, limit=10, user_id=user_id)
    st.session_state.difficulty = compute_next_difficulty(history, st.session_state.difficulty)
    log.info(
        "generating question: topic=%s difficulty=%d history=%s past_q_count=%d",
        topic, st.session_state.difficulty, history, len(past_questions),
    )
    result = asyncio.run(
        next_question(topic, st.session_state.difficulty, history, past_questions)
    )
    st.session_state.question = result["question"]
    st.session_state.topic = result["topic"]
    st.session_state.difficulty = result["difficulty"]
    log.info("question ready: topic=%s difficulty=%d", result["topic"], result["difficulty"])
    st.session_state.update({
        "feedback": None,
        "score": None,
        "submitted": False,
        "topic_locked": True,
        "hint_level": 0,
        "hints": [],
        "attempt": 1,
        "custom_topic": "",
    })