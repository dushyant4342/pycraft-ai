import asyncio
import logging
import random
from datetime import datetime, timedelta

import extra_streamlit_components as stx
import streamlit as st
from streamlit_ace import st_ace

from auth import login_ui
from llm import review_code, next_question, get_hint
from tracker import (
    init_db, save_session, get_recent_scores, get_recent_questions,
    compute_next_difficulty, get_all_topic_stats, get_topic_stats,
    get_user_by_token, delete_auth_token, get_session_history,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pycraft")

st.set_page_config(page_title="PyCraft AI", layout="wide", page_icon="⚡")

TOPIC_ICONS = {
    "strings": "🔤",
    "lists": "📋",
    "dicts": "🗂️",
    "functions": "⚙️",
    "OOP": "🧩",
    "comprehensions": "🔁",
    "async": "⚡",
}

TOPICS = ["strings", "lists", "dicts", "functions", "OOP", "comprehensions", "async"]


def inject_css() -> None:
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* ── Base ──────────────────────────────────────── */
        html, body, [data-testid="stAppViewContainer"] {
            background: #0d0f18 !important;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stMain"] { background: #0d0f18 !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        #MainMenu, footer, header { visibility: hidden; }
        [data-testid="stToolbar"] { display: none; }
        [data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 2rem !important; max-width: 900px !important; }

        /* ── Typography ────────────────────────────────── */
        h1, h2, h3 { font-family: 'Inter', sans-serif; }
        p, li, span { font-family: 'Inter', sans-serif; }

        /* ── Gradient title ────────────────────────────── */
        .app-title {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #7c6af7 0%, #4f9eff 50%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
            margin: 0;
        }
        .app-subtitle {
            color: #64748b;
            font-size: 0.88rem;
            margin-top: 0.3rem;
            font-weight: 400;
        }

        /* ── Cards ─────────────────────────────────────── */
        .ui-card {
            background: #161925;
            border: 1px solid #252840;
            border-radius: 14px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.25rem;
        }
        .ui-card-accent {
            background: linear-gradient(135deg, #1a1d35 0%, #161925 100%);
            border: 1px solid #7c6af730;
            border-radius: 14px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.25rem;
        }

        /* ── Metric cards ──────────────────────────────── */
        .metric-card {
            background: #161925;
            border: 1px solid #252840;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            text-align: center;
        }
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.6rem;
            font-weight: 700;
            color: #e2e8f0;
            line-height: 1.2;
        }
        .metric-label {
            font-size: 0.72rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 0.3rem;
        }

        /* ── Topic progress rows ───────────────────────── */
        .topic-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.65rem 0;
            border-bottom: 1px solid #1e2235;
        }
        .topic-row:last-child { border-bottom: none; }
        .topic-name {
            font-weight: 600;
            font-size: 0.9rem;
            color: #cbd5e1;
        }
        .topic-meta {
            font-size: 0.78rem;
            color: #64748b;
            margin-top: 0.1rem;
        }
        .topic-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }

        /* ── Score badge ───────────────────────────────── */
        .score-wrap { display: flex; align-items: center; gap: 1rem; margin: 0.75rem 0; }
        .score-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.8rem;
            font-weight: 700;
            padding: 0.3rem 1rem;
            border-radius: 12px;
            letter-spacing: -1px;
        }
        .score-high { background: #052e16; color: #4ade80; border: 1px solid #166534; }
        .score-mid  { background: #1c1500; color: #fbbf24; border: 1px solid #92400e; }
        .score-low  { background: #1c0606; color: #f87171; border: 1px solid #991b1b; }

        /* ── Inline alert ──────────────────────────────── */
        .alert {
            border-radius: 10px;
            padding: 0.85rem 1.1rem;
            font-size: 0.9rem;
            font-weight: 500;
            line-height: 1.55;
            margin: 0.5rem 0;
        }
        .alert-success { background: #052e16; color: #86efac; border: 1px solid #166534; }
        .alert-warning { background: #1c1500; color: #fde68a; border: 1px solid #92400e; }
        .alert-error   { background: #1c0606; color: #fca5a5; border: 1px solid #991b1b; }
        .alert-info    { background: #0d1f3c; color: #93c5fd; border: 1px solid #1e40af; }

        /* ── Tags / pills ──────────────────────────────── */
        .tag {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            margin-right: 0.4rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .tag-topic    { background: #2e1065; color: #c4b5fd; }
        .tag-diff-1   { background: #052e16; color: #4ade80; }
        .tag-diff-2   { background: #1a2e16; color: #86efac; }
        .tag-diff-3   { background: #1c1500; color: #fbbf24; }
        .tag-diff-4   { background: #1c0d00; color: #fb923c; }
        .tag-diff-5   { background: #1c0606; color: #f87171; }

        /* ── Question text ─────────────────────────────── */
        .question-text {
            font-size: 1.05rem;
            line-height: 1.7;
            color: #e2e8f0;
            font-weight: 400;
        }
        .question-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: #7c6af7;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.5rem;
        }

        /* ── Buttons ───────────────────────────────────── */
        .stButton > button {
            background: linear-gradient(135deg, #7c6af7 0%, #6657d4 100%) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 0.6rem 1.6rem !important;
            transition: all 0.18s ease !important;
            box-shadow: 0 2px 12px #7c6af740 !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #6657d4 0%, #5548b8 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 18px #7c6af760 !important;
        }
        .stButton > button:active { transform: translateY(0) !important; }
        .stButton > button:disabled {
            background: #252840 !important;
            color: #475569 !important;
            box-shadow: none !important;
        }

        /* ── Ace editor ────────────────────────────────── */
        .ace_editor { border-radius: 10px !important; border: 1px solid #252840 !important; }

        /* ── Selectbox / input ─────────────────────────── */
        .stSelectbox > div > div,
        .stTextInput > div > div > input {
            background: #161925 !important;
            border: 1px solid #252840 !important;
            border-radius: 8px !important;
            color: #e2e8f0 !important;
        }

        /* ── Tabs ──────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background: #161925;
            border-radius: 10px;
            padding: 0.25rem;
            border: 1px solid #252840;
            gap: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px !important;
            color: #64748b !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
        }
        .stTabs [aria-selected="true"] {
            background: #7c6af7 !important;
            color: #fff !important;
        }

        /* ── Divider ───────────────────────────────────── */
        hr { border-color: #252840 !important; margin: 1.25rem 0 !important; }

        /* ── Spinner ───────────────────────────────────── */
        .stSpinner > div { color: #7c6af7 !important; }

        /* ── Header greeting ───────────────────────────── */
        .app-greeting {
            font-size: 0.88rem;
            margin-top: 0.35rem;
            font-weight: 400;
        }
        .greeting-name {
            color: #a78bfa;
            font-weight: 700;
        }
        .greeting-sep { color: #252840; margin: 0 0.5rem; }
        .greeting-sub { color: #475569; }

        /* ── Sign-out chip (sibling selector targeting) ─ */
        div:has(.signout-anchor) ~ div .stButton > button {
            background: transparent !important;
            color: #475569 !important;
            border: 1px solid #1e2235 !important;
            border-radius: 999px !important;
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            padding: 0.2rem 0.75rem !important;
            height: auto !important;
            box-shadow: none !important;
            letter-spacing: 0.02em !important;
            white-space: nowrap !important;
            margin-top: 1.4rem !important;
        }
        div:has(.signout-anchor) ~ div .stButton > button:hover {
            color: #fca5a5 !important;
            border-color: #450a0a !important;
            background: #1c06061a !important;
            transform: none !important;
            box-shadow: none !important;
        }

        /* ── Topic picker radio pills ──────────────────── */
        div[data-testid="stRadioGroup"] { justify-content: center; }
        div[data-testid="stRadioGroup"] [role="radiogroup"] {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            justify-content: center;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] label {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            background: #161925;
            border: 1.5px solid #252840;
            border-radius: 9999px;
            padding: 0.32rem 0.95rem;
            cursor: pointer;
            white-space: nowrap;
            font-size: 0.82rem;
            font-weight: 500;
            color: #94a3b8;
            transition: border-color 0.15s, color 0.15s, background 0.15s;
            user-select: none;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] label:hover {
            border-color: #6366f1;
            color: #c4b5fd;
            background: #1a1d2e;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, #6366f1, #818cf8);
            border-color: transparent;
            color: #fff;
            font-weight: 700;
            box-shadow: 0 2px 12px #6366f145;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] input[type="radio"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)


def card(html: str, accent: bool = False) -> None:
    cls = "ui-card-accent" if accent else "ui-card"
    st.markdown(f'<div class="{cls}">{html}</div>', unsafe_allow_html=True)


def score_badge(score: float) -> str:
    cls = "score-high" if score >= 7 else ("score-mid" if score >= 4 else "score-low")
    label = "Excellent" if score >= 8 else ("Good" if score >= 6 else ("Fair" if score >= 4 else "Needs work"))
    display = f"{score:.1f}"
    return (
        f'<div class="score-wrap">'
        f'<span class="score-badge {cls}">{display}/10</span>'
        f'<span style="color:#94a3b8;font-size:0.9rem;font-weight:500;">{label}</span>'
        f'</div>'
    )


def alert(message: str, kind: str = "info") -> None:
    st.markdown(f'<div class="alert alert-{kind}">{message}</div>', unsafe_allow_html=True)


def diff_tag(level: int) -> str:
    labels = {1: "Easy", 2: "Medium-Easy", 3: "Medium", 4: "Hard", 5: "Expert"}
    return f'<span class="tag tag-diff-{level}">{labels.get(level, str(level))}</span>'


def topic_tag(topic: str) -> str:
    icon = TOPIC_ICONS.get(topic, "📌")
    return f'<span class="tag tag-topic">{icon} {topic}</span>'


def avg_color(avg: float) -> str:
    if avg is None:
        return "#64748b"
    if avg >= 7:
        return "#4ade80"
    if avg >= 4:
        return "#fbbf24"
    return "#f87171"


def init_session() -> None:
    defaults = {
        "question": None,
        "topic": "lists",
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
    topic = st.session_state.topic
    if not topic:
        topic = random.choice(TOPICS)
        st.session_state.topic = topic
        log.info("random topic selected: %s", topic)
    stats = asyncio.run(get_topic_stats(topic, user_id=user_id))
    if stats["count"] > 0:
        st.session_state.difficulty = stats["last_difficulty"]
        log.info("difficulty seeded from history: topic=%s difficulty=%d (sessions=%d)", topic, stats["last_difficulty"], stats["count"])
    history = get_recent_scores(st.session_state.topic, limit=5, user_id=user_id)
    past_questions = get_recent_questions(st.session_state.topic, limit=10, user_id=user_id)
    st.session_state.difficulty = compute_next_difficulty(history, st.session_state.difficulty)
    log.info("generating question: topic=%s difficulty=%d history=%s past_q_count=%d", st.session_state.topic, st.session_state.difficulty, history, len(past_questions))
    result = asyncio.run(
        next_question(st.session_state.topic, st.session_state.difficulty, history, past_questions)
    )
    st.session_state.question = result["question"]
    st.session_state.topic = result["topic"]
    st.session_state.difficulty = result["difficulty"]
    log.info("question ready: topic=%s difficulty=%d", result["topic"], result["difficulty"])
    st.session_state.feedback = None
    st.session_state.score = None
    st.session_state.submitted = False
    st.session_state.topic_locked = True
    st.session_state.hint_level = 0
    st.session_state.hints = []
    st.session_state.attempt = 1


_COOKIE_NAME = "pycraft_session"


def _get_cookie_manager() -> stx.CookieManager:
    return stx.CookieManager(key="pycraft_cookie_mgr")


def try_restore_session(cookie_manager: stx.CookieManager) -> None:
    """Restore user_id/email from session cookie on page refresh."""
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
    """Extract capitalized first name from email username, stripping trailing digits."""
    username = email.split("@")[0].split(".")[0]
    name = username.rstrip("0123456789")
    return (name or username).capitalize()


def render_header(cookie_manager: stx.CookieManager) -> None:
    first_name = _first_name(st.session_state.user_email)
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.markdown(
            f'<p class="app-title">⚡ PyCraft AI</p>'
            f'<p class="app-subtitle">Hello, {first_name} &nbsp;·&nbsp; Adaptive Python practice, powered by AI</p>',
            unsafe_allow_html=True,
        )
    with col_logout:
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("Sign out", key="logout_btn"):
            log.info("user logged out: user_id=%s", st.session_state.get("user_id"))
            token = cookie_manager.get(_COOKIE_NAME)
            if token:
                delete_auth_token(token)
                cookie_manager.delete(_COOKIE_NAME, key="del_session_logout")
            st.session_state.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)


def render_progress(stats: list[dict]) -> None:
    if not stats:
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
            f'<div class="topic-meta">{row["count"]} sessions &nbsp;&middot;&nbsp; Level {row["last_difficulty"]}/5</div>'
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
        "text-transform:uppercase;font-weight:6001;margin-bottom:0.5rem;'>Choose a topic</p>",
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


DIFF_LABELS = {1: "Beginner", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert"}


def render_difficulty_picker(topic: str) -> None:
    user_id = st.session_state.get("user_id")
    default = st.session_state.get("difficulty", 1)
    if topic and user_id:
        stats = asyncio.run(get_topic_stats(topic, user_id=user_id))
        if stats["count"] > 0 and stats["last_difficulty"]:
            default = stats["last_difficulty"]
    st.markdown(
        "<p style='text-align:center;color:#475569;font-size:0.75rem;letter-spacing:0.07em;"
        "text-transform:uppercase;font-weight:600;margin:0.75rem 0 0.5rem;'>Difficulty</p>",
        unsafe_allow_html=True,
    )
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        chosen = st.select_slider(
            "difficulty_picker",
            options=[1, 2, 3, 4, 5],
            value=default,
            format_func=lambda v: f"{v} - {DIFF_LABELS[v]}",
            label_visibility="collapsed",
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
    topic_options = ["All"] + TOPICS
    topic_filter = st.selectbox("Filter by topic", topic_options, key="history_topic_filter")
    selected_topic = None if topic_filter == "All" else topic_filter
    rows = asyncio.run(get_session_history(user_id, topic=selected_topic, limit=50))
    if not rows:
        st.caption("No submissions yet.")
        return
    import pandas as pd
    df = pd.DataFrame([
        {
            "Date": r["timestamp"][:10],
            "Topic": r["topic"],
            "Diff": r["difficulty"],
            "Score": r["score"],
            "Code": (r["code"][:120] + "..." if len(r["code"]) > 120 else r["code"]),
            "Feedback": (r["feedback"][:200] + "..." if len(r["feedback"]) > 200 else r["feedback"]),
        }
        for r in rows
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")
    for row in rows:
        with st.expander(f"#{row['id']} · {row['topic']} · score {row['score']}/10 · {row['timestamp'][:10]}"):
            st.markdown(f"**Question:** {row['question']}")
            st_ace(
                value=row["code"],
                language="python",
                theme="tomorrow_night",
                font_size=13,
                height=200,
                readonly=True,
                auto_update=True,
                key=f"history_ace_{row['id']}",
                show_gutter=True,
                show_print_margin=False,
            )
            kind = "success" if row["score"] >= 7 else ("warning" if row["score"] >= 4 else "error")
            alert(row["feedback"], kind=kind)


def render_start_screen() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    card(
        '<p style="text-align:center;font-size:2.5rem;margin:0;">🚀</p>'
        '<p style="text-align:center;font-size:1.2rem;font-weight:600;color:#e2e8f0;margin:0.5rem 0 0.25rem;">Ready to practice?</p>'
        '<p style="text-align:center;color:#64748b;font-size:0.9rem;margin:0;">Pick a topic or let AI choose for you.</p>',
        accent=True,
    )
    if not st.session_state.get("topic_locked", False):
        render_topic_picker()
        render_difficulty_picker(st.session_state.get("topic", "lists"))
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("Start Practicing", use_container_width=True):
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
            new_level = hint_level + 1
            code_so_far = st.session_state.get("_last_code", "")
            with st.spinner("Generating hint..."):
                hint_text = asyncio.run(
                    get_hint(st.session_state.question, code_so_far, new_level)
                )
            st.session_state.hint_level = new_level
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
    col_a, col_retry, col_next, col_c = st.columns([1, 1.5, 1.5, 1])
    with col_retry:
        if st.button("Try Again", use_container_width=True):
            st.session_state.submitted = False
            st.session_state.feedback = None
            st.session_state.score = None
            st.session_state.attempt = attempt + 1
            st.rerun()
    with col_next:
        if st.button("Next Question →", use_container_width=True):
            st.session_state.question = None
            st.session_state.topic_locked = False
            st.session_state.feedback = None
            st.session_state.score = None
            st.session_state.submitted = False
            st.session_state.attempt = 1
            st.rerun()


def main() -> None:
    inject_css()
    init_db()

    cookie_manager = _get_cookie_manager()

    # Commit pending login token to cookie (set by auth.py after rerun)
    pending = st.session_state.pop("_pending_token", None)
    if pending:
        expires = datetime.now() + timedelta(days=30)
        cookie_manager.set(_COOKIE_NAME, pending, expires_at=expires, key="set_session_cookie")

    try_restore_session(cookie_manager)

    if not st.session_state.get("user_id"):
        login_ui()
        st.stop()

    if not st.session_state.get("_logged_in_logged"):
        log.info("user session started: user_id=%s", st.session_state.user_id)
        st.session_state["_logged_in_logged"] = True

    init_session()
    render_header(cookie_manager)

    practice_tab, history_tab = st.tabs(["Practice", "History"])

    with practice_tab:
        user_id = st.session_state.user_id
        stats = asyncio.run(get_all_topic_stats(user_id=user_id))
        render_progress(stats)

        if st.session_state.question is None:
            render_start_screen()
        else:
            render_question()
            code = render_editor()
            st.session_state["_last_code"] = code

            st.markdown("<br>", unsafe_allow_html=True)
            col_a, col_b, col_skip, col_c = st.columns([1, 2, 1, 1])
            with col_b:
                attempt = st.session_state.get("attempt", 1)
                submit_label = f"Re-submit (Attempt {attempt})" if attempt > 1 else "Submit Solution"
                submit = st.button(
                    submit_label,
                    use_container_width=True,
                    disabled=st.session_state.submitted,
                )
            with col_skip:
                if st.button("Skip", use_container_width=True, disabled=st.session_state.submitted):
                    st.session_state.skip_count = st.session_state.get("skip_count", 0) + 1
                    load_next_question()
                    st.rerun()
            skip_count = st.session_state.get("skip_count", 0)
            if skip_count > 0:
                st.caption(f"Skipped: {skip_count} this session")

            if submit and code.strip():
                log.info("code submitted: topic=%s difficulty=%d", st.session_state.topic, st.session_state.difficulty)
                with st.spinner("AI is reviewing your code..."):
                    result = asyncio.run(review_code(st.session_state.question, code))
                st.session_state.score = result["score"]
                st.session_state.feedback = result["feedback"]
                st.session_state.submitted = True
                log.info("review complete: score=%d/10 topic=%s", result["score"], st.session_state.topic)
                save_session(
                    topic=st.session_state.topic,
                    difficulty=st.session_state.difficulty,
                    question=st.session_state.question,
                    code=code,
                    score=result["score"],
                    feedback=result["feedback"],
                    user_id=user_id,
                )
                st.rerun()

            if st.session_state.submitted:
                st.markdown("<hr>", unsafe_allow_html=True)
                render_result()

    with history_tab:
        render_history_tab()


if __name__ == "__main__":
    main()
