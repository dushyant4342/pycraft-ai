import asyncio
import streamlit as st
from streamlit_ace import st_ace

from auth import login_ui
from llm import review_code, next_question
from tracker import init_db, save_session, get_recent_scores, compute_next_difficulty, get_all_topic_stats

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

        /* ── Logout btn override ───────────────────────── */
        .logout-btn > button {
            background: transparent !important;
            color: #64748b !important;
            border: 1px solid #252840 !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            font-size: 0.82rem !important;
            padding: 0.4rem 0.9rem !important;
        }
        .logout-btn > button:hover {
            color: #f87171 !important;
            border-color: #991b1b !important;
            transform: none !important;
            box-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)


def card(html: str, accent: bool = False) -> None:
    cls = "ui-card-accent" if accent else "ui-card"
    st.markdown(f'<div class="{cls}">{html}</div>', unsafe_allow_html=True)


def score_badge(score: int) -> str:
    cls = "score-high" if score >= 7 else ("score-mid" if score >= 4 else "score-low")
    label = "Excellent" if score >= 8 else ("Good" if score >= 6 else ("Fair" if score >= 4 else "Needs work"))
    return (
        f'<div class="score-wrap">'
        f'<span class="score-badge {cls}">{score}/10</span>'
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def load_next_question() -> None:
    user_id = st.session_state.user_id
    history = get_recent_scores(st.session_state.topic, limit=5, user_id=user_id)
    st.session_state.difficulty = compute_next_difficulty(history, st.session_state.difficulty)
    result = asyncio.run(
        next_question(st.session_state.topic, st.session_state.difficulty, history)
    )
    st.session_state.question = result["question"]
    st.session_state.topic = result["topic"]
    st.session_state.difficulty = result["difficulty"]
    st.session_state.feedback = None
    st.session_state.score = None
    st.session_state.submitted = False


def render_header() -> None:
    col_title, col_logout = st.columns([7, 1])
    with col_title:
        st.markdown(
            f'<p class="app-title">⚡ PyCraft AI</p>'
            f'<p class="app-subtitle">Adaptive Python practice, powered by AI &nbsp;·&nbsp; {st.session_state.user_email}</p>',
            unsafe_allow_html=True,
        )
    with col_logout:
        st.write("")
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("Logout", key="logout_btn"):
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
        rows_html += f"""
        <div class="topic-row">
            <div>
                <div class="topic-name">{icon} {row['topic']}</div>
                <div class="topic-meta">{row['count']} sessions &nbsp;·&nbsp; Level {row['last_difficulty']}/5</div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:{color};font-size:1rem;">
                    {avg}/10
                </div>
                <div style="width:80px;height:4px;background:#252840;border-radius:999px;margin-top:4px;">
                    <div style="width:{bar_pct}%;height:100%;background:{color};border-radius:999px;"></div>
                </div>
            </div>
        </div>
        """
    card(rows_html)


def render_start_screen() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    card(
        '<p style="text-align:center;font-size:2.5rem;margin:0;">🚀</p>'
        '<p style="text-align:center;font-size:1.2rem;font-weight:600;color:#e2e8f0;margin:0.5rem 0 0.25rem;">Ready to practice?</p>'
        '<p style="text-align:center;color:#64748b;font-size:0.9rem;margin:0;">Pick a topic or let AI choose for you.</p>',
        accent=True,
    )
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

    kind = "success" if score >= 7 else ("warning" if score >= 4 else "error")
    st.markdown(score_badge(score), unsafe_allow_html=True)
    alert(feedback, kind=kind)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("Next Question →", use_container_width=True):
            with st.spinner("Generating next question..."):
                load_next_question()
            st.rerun()


def main() -> None:
    inject_css()
    init_db()

    if not st.session_state.get("user_id"):
        login_ui()
        st.stop()

    init_session()
    render_header()

    user_id = st.session_state.user_id
    stats = asyncio.run(get_all_topic_stats(user_id=user_id))
    render_progress(stats)

    if st.session_state.question is None:
        render_start_screen()
        return

    render_question()
    code = render_editor()

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        submit = st.button(
            "Submit Solution",
            use_container_width=True,
            disabled=st.session_state.submitted,
        )

    if submit and code.strip():
        with st.spinner("AI is reviewing your code..."):
            result = asyncio.run(review_code(st.session_state.question, code))
        st.session_state.score = result["score"]
        st.session_state.feedback = result["feedback"]
        st.session_state.submitted = True
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


if __name__ == "__main__":
    main()
