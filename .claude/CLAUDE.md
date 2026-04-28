# PyCraft AI

Adaptive Python coding practice app. One question at a time, Claude reviews code, SQLite tracks performance.

## Stack
- Streamlit + streamlit-ace (UI + code editor)
- Anthropic SDK, model: claude-sonnet-4-6 (async)
- SQLite via sqlite3 (pycraft.db)
- Python 3.11+


## Rules
- All DB ops via tracker.py only
- All Claude calls async
- Score always int 0-10
- Topics: strings, lists, dicts, functions, OOP, comprehensions, async
- Difficulty 1-5; avg >= 8 => bump, avg < 5 => drop (rolling last 5)
- no sidebar clutter, runs locally only
