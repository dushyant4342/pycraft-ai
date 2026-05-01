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
    """Return {score: int 0-10, feedback: str} for the submitted solution."""
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
                    "Respond with JSON only: {\"score\": <int 0-10>, \"feedback\": \"...\"}."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\nStudent code:\n```python\n{code}\n```\n\n"
                    "Score 0-10 and give concise, actionable feedback."
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    score = max(0, min(10, int(data["score"])))
    return {"score": score, "feedback": data["feedback"]}
