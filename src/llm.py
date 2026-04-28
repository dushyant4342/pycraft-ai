import json
import anthropic

MODEL = "claude-sonnet-4-6"
TOPICS = ["strings", "lists", "dicts", "functions", "OOP", "comprehensions", "async"]

_client = anthropic.AsyncAnthropic()


async def next_question(topic: str, difficulty: int, history: list[int]) -> dict:
    """Return {question, topic, difficulty} for the next practice prompt."""
    history_note = f"Recent scores: {history}." if history else "No prior scores."

    message = await _client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=(
            "You are a Python coding tutor. Generate a single focused Python practice question. "
            "Respond with JSON only: {\"question\": \"...\", \"topic\": \"...\", \"difficulty\": <int 1-5>}. "
            f"Valid topics: {TOPICS}."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}. Difficulty: {difficulty}/5. {history_note} "
                    "Generate one coding question appropriate for this level. "
                    "Do not include the solution."
                ),
            }
        ],
    )

    raw = message.content[0].text.strip()
    data = json.loads(raw)
    return {
        "question": data["question"],
        "topic": data.get("topic", topic),
        "difficulty": int(data.get("difficulty", difficulty)),
    }


async def review_code(question: str, code: str) -> dict:
    """Return {score: int 0-10, feedback: str} for the submitted solution."""
    message = await _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a strict but fair Python code reviewer. "
            "Evaluate the solution for correctness, style, and efficiency. "
            "Respond with JSON only: {\"score\": <int 0-10>, \"feedback\": \"...\"}."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\nStudent code:\n```python\n{code}\n```\n\n"
                    "Score 0-10 and give concise, actionable feedback."
                ),
            }
        ],
    )

    raw = message.content[0].text.strip()
    data = json.loads(raw)
    score = max(0, min(10, int(data["score"])))
    return {"score": score, "feedback": data["feedback"]}
