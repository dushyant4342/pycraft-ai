import asyncio
import logging
from datetime import datetime, timedelta

import streamlit as st

from auth import login_ui
from components import (
    render_editor, render_header, render_history_tab, render_progress,
    render_question, render_result, render_start_screen, render_stats_strip,
)
from llm import review_code
from session import (
    _COOKIE_NAME, _get_cookie_manager, init_session,
    load_next_question, try_restore_session,
)
from styles import inject_css
from tracker import get_all_topic_stats, init_db, save_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pycraft")

st.set_page_config(page_title="PyCraft AI", layout="wide", page_icon="⚡")


def main() -> None:
    inject_css()
    init_db()

    cookie_manager = _get_cookie_manager()

    pending = st.session_state.pop("_pending_token", None)
    if pending:
        cookie_manager.set(
            _COOKIE_NAME, pending,
            expires_at=datetime.now() + timedelta(days=30),
            key="set_session_cookie",
        )

    try_restore_session(cookie_manager)

    if not st.session_state.get("user_id"):
        login_ui()
        st.stop()

    if not st.session_state.get("_logged_in_logged"):
        log.info("user session started: user_id=%s", st.session_state.user_id)
        st.session_state["_logged_in_logged"] = True

    init_session()
    render_header(cookie_manager)

    user_id = st.session_state.user_id
    stats = asyncio.run(get_all_topic_stats(user_id=user_id))
    render_stats_strip(stats)

    left_col, center_col = st.columns([5, 7], gap="large")

    with left_col:
        progress_tab, history_tab = st.tabs(["Progress", "History"])
        with progress_tab:
            render_progress(stats)
        with history_tab:
            render_history_tab()

    with center_col:
        if st.session_state.question is None:
            render_start_screen()
        else:
            render_question()
            code = render_editor()
            st.session_state["_last_code"] = code

            st.markdown("<br>", unsafe_allow_html=True)
            col_submit, col_skip = st.columns([3, 1])
            with col_submit:
                attempt = st.session_state.get("attempt", 1)
                submit_label = f"Re-submit (Attempt {attempt})" if attempt > 1 else "Submit Solution"
                submit = st.button(
                    submit_label,
                    use_container_width=True,
                    disabled=st.session_state.submitted,
                    type="primary",
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


if __name__ == "__main__":
    main()
