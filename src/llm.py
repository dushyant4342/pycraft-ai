import json
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

MODEL = "gpt-4o-mini"
TOPICS = ["strings", "lists", "dicts", "functions", "OOP", "comprehensions", "async"]

_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])


async def next_question(
    topic: str,
    difficulty: int,
    history: list[int],
    past_questions: list[str] | None = None,
) -> dict:
    """Return {question, topic, difficulty} for the next practice prompt."""
    history_note = f"Recent scores: {history}." if history else "No prior scores."
    avoid_block = ""
    if past_questions:
        bullets = "\n".join(f"- {q[:120]}" for q in past_questions)
        avoid_block = f"\n\nDo NOT repeat or closely resemble any of these previously asked questions:\n{bullets}"

    response = await _client.chat.completions.create(
        model=MODEL,
        max_tokens=512,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Python coding tutor. Generate a single focused Python practice question with sample input & output. "
                    "Respond with JSON only: {\"question\": \"...\", \"topic\": \"...\", \"difficulty\": <int 1-5>}. "
                    f"Valid topics: {TOPICS}."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}. Difficulty: {difficulty}/5. {history_note} "
                    "Generate one coding question appropriate for this level. "
                    f"Do not include the solution.{avoid_block}"
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return {
        "question": data["question"],
        "topic": data.get("topic", topic),
        "difficulty": int(data.get("difficulty", difficulty)),
    }


async def review_code(question: str, code: str) -> dict:
    """Return {score: float 0-10 with one decimal, feedback: str} for the submitted solution."""
    response = await _client.chat.completions.create(
        model=MODEL,
        max_tokens=512,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict but fair Python code reviewer. "
                    "Evaluate the solution for correctness, style, and efficiency. "
                    "Respond with JSON only: {\"score\": <decimal 0.0-10.0 with one decimal place>, \"feedback\": \"...\"}."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\nStudent code:\n```python\n{code}\n```\n\n"
                    "Score 0.0-10.0 (one decimal, e.g. 7.5) and give concise, actionable feedback."
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    score = round(max(0.0, min(10.0, float(data["score"]))), 1)
    return {"score": score, "feedback": data["feedback"]}


_HINT_GUIDANCE = {
    1: (
        "Give a conceptual nudge only. Explain the general approach or which Python concept applies. "
        "Do NOT write any code, pseudocode, or variable names."
    ),
    2: (
        "Give a pseudocode or algorithm outline. Use plain English steps. "
        "You may mention built-in function names but do NOT write actual Python syntax."
    ),
    3: (
        "Give a partial code snippet (at most 5 lines) that covers one sub-problem. "
        "Do NOT reveal the complete solution."
    ),
}


async def get_hint(question: str, code: str, hint_level: int) -> str:
    """Return a level-gated hint string. hint_level must be 1, 2, or 3."""
    if hint_level not in _HINT_GUIDANCE:
        raise ValueError(f"hint_level must be 1-3, got {hint_level}")
    guidance = _HINT_GUIDANCE[hint_level]
    response = await _client.chat.completions.create(
        model=MODEL,
        max_tokens=256,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a Python tutor giving a level-{hint_level} hint. {guidance} "
                    "Never reveal the full solution."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Student's current code:\n```python\n{code or '# (nothing yet)'}\n```\n\n"
                    f"Give a level-{hint_level} hint."
                ),
            },
        ],
    )
    return response.choices[0].message.content.strip()
