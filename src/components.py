import asyncio
from datetime import date, timedelta

import streamlit as st
from streamlit_ace import st_ace

from llm import get_hint
from session import TOPICS, _COOKIE_NAME, _first_name, load_next_question
from tracker import delete_auth_token, get_session_history, get_topic_stats

TOPIC_ICONS = {
    "strings": "🔤",
    "lists": "📋",
    "dicts": "🗂️",
    "functions": "⚙️",
    "OOP": "🧩",
    "comprehensions": "🔁",
    "async": "⚡",
    "linked lists": "🔗",
    "hash tables": "🗃️",
    "stacks & queues": "📚",
    "trees & BST": "🌳",
    "heaps": "⛰️",
    "graphs": "🕸️",
    "sorting algorithms": "🔀",
    "recursion": "🔄",
    "dynamic programming": "🧠",
}

DIFF_LABELS = {1: "Beginner", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert"}


# ── UI primitives ────────────────────────────────────────────────────────────

def card(html: str, accent: bool = False) -> None:
    cls = "ui-card-accent" if accent else "ui-card"
    st.markdown(f'<div class="{cls}">{html}</div>', unsafe_allow_html=True)


def alert(message: str, kind: str = "info") -> None:
    st.markdown(f'<div class="alert alert-{kind}">{message}</div>', unsafe_allow_html=True)


def score_badge(score: float) -> str:
    cls = "score-high" if score >= 7 else ("score-mid" if score >= 4 else "score-low")
    label = "Excellent" if score >= 8 else ("Good" if score >= 6 else ("Fair" if score >= 4 else "Needs work"))
    return (
        f'<div class="score-wrap">'
        f'<span class="score-badge {cls}">{score:.1f}/10</span>'
        f'<span style="color:#94a3b8;font-size:0.9rem;font-weight:500;">{label}</span>'
        f'</div>'
    )


def diff_tag(level: int) -> str:
    labels = {1: "Easy", 2: "Medium-Easy", 3: "Medium", 4: "Hard", 5: "Expert"}
    return f'<span class="tag tag-diff-{level}">{labels.get(level, str(level))}</span>'


def topic_tag(topic: str) -> str:
    icon = TOPIC_ICONS.get(topic, "📌")
    return f'<span class="tag tag-topic">{icon} {topic}</span>'


def avg_color(avg: float | None) -> str:
    if avg is None:
        return "#64748b"
    if avg >= 7:
        return "#4ade80"
    if avg >= 4:
        return "#fbbf24"
    return "#f87171"


# ── Render functions ─────────────────────────────────────────────────────────

def render_header(cookie_manager) -> None:
    first_name = _first_name(st.session_state.user_email)
    col_title, col_logout = st.columns([6, 1])
    with col_title:
        st.markdown(
            f'<p class="app-title">⚡ PyCraft AI</p>'
            f'<p class="app-subtitle" style="margin-bottom:0.1rem;">'
            f'Welcome back, <span class="greeting-name">{first_name}</span>'
            f'</p>'
            f'<p class="app-subtitle" style="margin-top:0.15rem;">'
            f'<span style="color:#475569;">Your AI-powered Python coach is ready 🚀</span>'
            f'</p>',
            unsafe_allow_html=True,
        )
    with col_logout:
        st.markdown('<div class="signout-anchor"></div>', unsafe_allow_html=True)
        if st.button("Sign out", key="logout_btn"):
            token = cookie_manager.get(_COOKIE_NAME)
            if token:
                delete_auth_token(token)
                cookie_manager.delete(_COOKIE_NAME, key="del_session_logout")
            st.session_state.clear()
            st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)


def render_stats_strip(stats: list[dict]) -> None:
    """Aggregate metrics bar shown below the header."""
    if not stats:
        return
    total = sum(s["count"] for s in stats)
    avgs = [s["avg_score"] for s in stats if s["avg_score"] is not None]
    overall_avg = round(sum(avgs) / len(avgs), 1) if avgs else None
    topics_count = len(stats)
    best = max(stats, key=lambda s: s["avg_score"] or 0) if avgs else None

    avg_display = f"{overall_avg}" if overall_avg is not None else "—"
    avg_col = avg_color(overall_avg)
    best_label = f"{TOPIC_ICONS.get(best['topic'], '📌')} {best['topic']}" if best else "—"

    st.markdown(
        f"""
        <div class="stats-strip">
            <div class="stat-chip">
                <div class="stat-chip-value">{total}</div>
                <div class="stat-chip-label">Sessions</div>
            </div>
            <div class="stat-chip">
                <div class="stat-chip-value" style="color:{avg_col};">{avg_display}/10</div>
                <div class="stat-chip-label">Avg Score</div>
            </div>
            <div class="stat-chip">
                <div class="stat-chip-value">{topics_count}<span style="color:#475569;font-size:0.85rem;">/7</span></div>
                <div class="stat-chip-label">Topics</div>
            </div>
            <div class="stat-chip">
                <div class="stat-chip-value" style="font-size:1rem;">{best_label}</div>
                <div class="stat-chip-label">Best Topic</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress(stats: list[dict]) -> None:
    if not stats:
        st.markdown(
            '<p style="color:#475569;font-size:0.85rem;text-align:center;padding:2rem 0;">'
            'No sessions yet.<br>Start practicing to see your progress!</p>',
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:700;color:#7c6af7;text-transform:uppercase;'
        'letter-spacing:0.1em;margin-bottom:0.75rem;">Your Progress</p>',
        unsafe_allow_html=True,
    )
    rows_html = ""
    for row in stats:
        avg = row["avg_score"]
        color = avg_color(avg)
        icon = TOPIC_ICONS.get(row["topic"], "📌")
        bar_pct = int((avg or 0) / 10 * 100)
        rows_html += (
            f'<div class="topic-row">'
            f'<div>'
            f'<div class="topic-name">{icon} {row["topic"]}</div>'
            f'<div class="topic-meta">{row["count"]} sessions &middot; Level {row["last_difficulty"]}/5</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-weight:700;color:{color};font-size:1rem;">{avg}/10</div>'
            f'<div style="width:80px;height:4px;background:#252840;border-radius:999px;margin-top:4px;">'
            f'<div style="width:{bar_pct}%;height:100%;background:{color};border-radius:999px;"></div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
    card(rows_html)


def render_topic_picker() -> None:
    current = st.session_state.get("topic", "lists")
    all_options = TOPICS + [""]
    labels = {t: f"{TOPIC_ICONS.get(t, '')} {t}" for t in TOPICS}
    labels[""] = "🎲 Random"
    idx = TOPICS.index(current) if current in TOPICS else len(TOPICS)
    st.markdown(
        "<p style='text-align:center;color:#475569;font-size:0.75rem;letter-spacing:0.07em;"
        "text-transform:uppercase;font-weight:600;margin-bottom:0.5rem;'>Choose a topic</p>",
        unsafe_allow_html=True,
    )
    selected = st.radio(
        "topic",
        options=all_options,
        format_func=lambda t: labels[t],
        index=idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected != current:
        st.session_state.topic = selected
        st.rerun()
    st.text_input(
        "custom_topic",
        placeholder="or type a custom topic (e.g. Linked Lists, Binary Search)...",
        key="custom_topic",
        label_visibility="collapsed",
        max_chars=60,
    )


def render_difficulty_picker(topic: str) -> None:
    user_id = st.session_state.get("user_id")
    default = st.session_state.get("difficulty", 1)
    if topic and user_id:
        stats = asyncio.run(get_topic_stats(topic, user_id=user_id))
        if stats["count"] > 0 and stats["last_difficulty"]:
            default = stats["last_difficulty"]

    diff_colors = {1: "#4ade80", 2: "#86efac", 3: "#fbbf24", 4: "#fb923c", 5: "#f87171"}

    st.markdown(
        "<p style='text-align:center;color:#475569;font-size:0.75rem;letter-spacing:0.07em;"
        "text-transform:uppercase;font-weight:600;margin:0.75rem 0;'>Difficulty</p>",
        unsafe_allow_html=True,
    )
    _, mid_col, _ = st.columns([1, 2, 1])
    with mid_col:
        chosen = st.select_slider(
            "difficulty_picker",
            options=[1, 2, 3, 4, 5],
            value=default,
            format_func=lambda v: f"{v} - {DIFF_LABELS[v]}",
            label_visibility="collapsed",
        )
    color = diff_colors.get(chosen, "#7c6af7")
    st.markdown(
        f"<p style='text-align:center;color:{color};font-family:\"JetBrains Mono\",monospace;"
        f"font-weight:700;font-size:0.88rem;margin-top:0.25rem;'>{chosen} — {DIFF_LABELS[chosen]}</p>",
        unsafe_allow_html=True,
    )
    if chosen != st.session_state.get("difficulty"):
        st.session_state.difficulty = chosen


def render_history_tab() -> None:
    user_id = st.session_state.get("user_id")
    if not user_id:
        return

    st.markdown(
        "<p style='font-size:0.72rem;font-weight:700;color:#7c6af7;text-transform:uppercase;"
        "letter-spacing:0.1em;margin-bottom:0.75rem;'>Past Submissions</p>",
        unsafe_allow_html=True,
    )

    today = date.today()
    col_from, col_to = st.columns([1, 1])
    with col_from:
        start_date = st.date_input("From", value=today - timedelta(days=30), key="history_start_date")
    with col_to:
        end_date = st.date_input("To", value=today, key="history_end_date")

    if start_date > end_date:
        st.warning("Start date must be before end date.")
        return

    topic_options = ["All"] + TOPICS
    selected_filter = st.selectbox(
        "Filter by topic",
        options=topic_options,
        format_func=lambda t: f"{TOPIC_ICONS.get(t, '')} {t}" if t != "All" else "🗂 All topics",
        key="history_topic_filter",
        label_visibility="collapsed",
    )
    selected_topic = None if selected_filter == "All" else selected_filter

    rows = asyncio.run(
        get_session_history(user_id, topic=selected_topic, limit=50,
                            start_date=start_date, end_date=end_date)
    )
    if not rows:
        st.info("No sessions found for the selected filters.")
        return

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    for row in rows:
        score = row["score"]
        icon = TOPIC_ICONS.get(row["topic"], "📌")
        kind = "success" if score >= 7 else ("warning" if score >= 4 else "error")
        score_color = "#4ade80" if score >= 7 else ("#fbbf24" if score >= 4 else "#f87171")

        label = f"{icon} {row['topic']}  ·  {row['timestamp'][:10]}  ·  {score:.1f}/10"
        with st.expander(label):
            st.markdown(
                f"<p style='color:#94a3b8;font-size:0.82rem;font-style:italic;"
                f"margin:0 0 0.5rem;line-height:1.5;'>{row['question']}</p>",
                unsafe_allow_html=True,
            )
            st_ace(
                value=row["code"],
                language="python",
                theme="tomorrow_night",
                font_size=13,
                height=150,
                readonly=True,
                auto_update=True,
                key=f"history_ace_{row['id']}",
                show_gutter=True,
                show_print_margin=False,
            )
            alert(row["feedback"], kind=kind)


def render_start_screen() -> None:
    card(
        '<div style="text-align:center;padding:1rem 0 0.75rem;">'
        '<p style="font-size:1.25rem;font-weight:700;color:#e2e8f0;margin:0 0 0.3rem;letter-spacing:-0.01em;">Ready to practice?</p>'
        '<p style="color:#64748b;font-size:0.88rem;margin:0;">Pick a topic, set difficulty, or let AI choose for you.</p>'
        '</div>',
        accent=True,
    )
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    if not st.session_state.get("topic_locked", False):
        render_topic_picker()
        render_difficulty_picker(st.session_state.get("topic", "lists"))
    if st.button("Start Practicing", use_container_width=True, type="primary"):
        with st.spinner("Generating your first question..."):
            load_next_question()
        st.rerun()


def render_question() -> None:
    topic = st.session_state.topic
    diff = st.session_state.difficulty
    card(
        f'<div class="question-label">Challenge</div>'
        f'{topic_tag(topic)}{diff_tag(diff)}'
        f'<div style="margin-top:0.85rem;" class="question-text">{st.session_state.question}</div>',
        accent=True,
    )

    hint_level = st.session_state.get("hint_level", 0)
    hints = st.session_state.get("hints", [])
    max_hints = 3

    if hint_level < max_hints and not st.session_state.get("submitted", False):
        btn_label = f"Get Hint ({hint_level + 1}/{max_hints})" if hint_level > 0 else "Get Hint"
        if st.button(btn_label, key="hint_btn"):
            with st.spinner("Generating hint..."):
                hint_text = asyncio.run(
                    get_hint(st.session_state.question, st.session_state.get("_last_code", ""), hint_level + 1)
                )
            st.session_state.hint_level = hint_level + 1
            st.session_state.hints = hints + [hint_text]
            st.rerun()
    elif hint_level >= max_hints:
        st.button("Get Hint (3/3)", key="hint_btn_disabled", disabled=True)

    if st.session_state.get("hints"):
        with st.expander("Hints", expanded=True):
            for i, h in enumerate(st.session_state.hints, 1):
                st.markdown(f"**Hint {i}:** {h}")


def render_editor() -> str:
    return st_ace(
        language="python",
        theme="tomorrow_night",
        font_size=14,
        tab_size=4,
        height=300,
        key="code_editor",
        placeholder="# Write your Python solution here...",
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        auto_update=False,
    )


def render_result() -> None:
    score = st.session_state.score
    feedback = st.session_state.feedback
    attempt = st.session_state.get("attempt", 1)

    kind = "success" if score >= 7 else ("warning" if score >= 4 else "error")
    st.markdown(score_badge(score), unsafe_allow_html=True)
    if attempt > 1:
        st.caption(f"Attempt {attempt}")
    alert(feedback, kind=kind)

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_retry, col_next, _ = st.columns([1, 1.5, 1.5, 1])
    with col_retry:
        if st.button("Try Again", use_container_width=True, type="primary"):
            st.session_state.update({
                "submitted": False,
                "feedback": None,
                "score": None,
                "attempt": attempt + 1,
            })
            st.rerun()
    with col_next:
        if st.button("Next Question →", use_container_width=True, type="primary"):
            st.session_state.update({
                "question": None,
                "topic_locked": False,
                "feedback": None,
                "score": None,
                "submitted": False,
                "attempt": 1,
            })
            st.rerun()
