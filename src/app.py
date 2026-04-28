import asyncio
import streamlit as st
from streamlit_ace import st_ace

from llm import review_code, next_question
from tracker import init_db, save_session, get_recent_scores, compute_next_difficulty, get_all_topic_stats

st.set_page_config(page_title="PyCraft AI", layout="wide")


def init_session():
    if "question" not in st.session_state:
        st.session_state.question = None
    if "topic" not in st.session_state:
        st.session_state.topic = "lists"
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = 1
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "score" not in st.session_state:
        st.session_state.score = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False


def load_next_question():
    history = get_recent_scores(st.session_state.topic, limit=5)
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


def main():
    init_db()
    init_session()

    st.title("PyCraft AI")
    st.caption(f"Topic: `{st.session_state.topic}` | Difficulty: {st.session_state.difficulty}/5")

    stats = asyncio.run(get_all_topic_stats())
    if stats:
        st.subheader("Progress")
        for row in stats:
            st.markdown(
                f"**{row['topic']}** — {row['count']} sessions | avg {row['avg_score']}/10 | difficulty {row['last_difficulty']}/5"
            )

    st.divider()

    if st.session_state.question is None:
        if st.button("Start"):
            load_next_question()
            st.rerun()
        return

    st.markdown(f"**Question:** {st.session_state.question}")
    st.write("")

    code = st_ace(
        language="python",
        theme="monokai",
        font_size=14,
        height=300,
        key="code_editor",
        placeholder="# Write your Python solution here...",
        auto_update=True,
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        submit = st.button("Submit", type="primary", disabled=st.session_state.submitted)

    if submit and code.strip():
        with st.spinner("Reviewing..."):
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
        )
        st.rerun()

    if st.session_state.submitted:
        score = st.session_state.score
        color = "green" if score >= 7 else "orange" if score >= 4 else "red"
        st.markdown(f"**Score:** :{color}[{score}/10]")
        st.markdown(f"**Feedback:** {st.session_state.feedback}")

        if st.button("Next Question"):
            load_next_question()
            st.rerun()


if __name__ == "__main__":
    main()
