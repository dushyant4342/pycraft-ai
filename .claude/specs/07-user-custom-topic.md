# Spec 07: User Custom Topic + Expanded Topic List + Difficulty Calibration

## Goal
Three related UX improvements to the Practice tab:
1. Let users type a free-form custom topic (e.g. "Linked Lists", "Tries") instead of being limited to the preset pill buttons.
2. Expand the preset topic list with common CS/DS topics so users don't need to type common ones.
3. Shrink the difficulty slider width to half and re-calibrate the LLM difficulty prompt so levels 3-5 actually produce hard/expert questions (currently level 3-4 feel easy).

## Files
- `src/session.py` — extend `TOPICS` list; handle custom topic in `load_next_question()`.
- `src/llm.py` — extend `TOPICS` constant; strengthen difficulty calibration in system prompt; accept free-form topic string.
- `src/components.py` — add custom topic text input below pill grid; narrow slider via column layout; update `DIFF_LABELS` descriptions.
- `src/styles.py` — no changes required (slider width controlled via column layout in `components.py`).

## Design

### Extended Topic List
Replace the 7-item `TOPICS` constant in both `session.py` and `llm.py` with a shared import from a single source of truth in `session.py`:

```python
TOPICS = [
    "strings", "lists", "dicts", "functions", "OOP",
    "comprehensions", "async",
    "linked lists", "hash tables", "stacks & queues",
    "trees & BST", "heaps", "graphs", "sorting algorithms",
    "recursion", "dynamic programming",
]
```

`llm.py` imports `TOPICS` from `session.py` instead of defining its own copy.

### Custom Topic Input
In `render_start_screen()` (via `components.py`), render a `st.text_input` below the topic pill grid with placeholder `"or type a custom topic..."`. Logic:
- If text input is non-empty, it overrides the pill selection: `st.session_state.topic = custom_value.strip().lower()`.
- If text input is empty, the pill selection applies as today.
- Clear the text input on "Next Question" by resetting session state key.

Custom topics are passed verbatim to `next_question()`; the LLM system prompt already accepts free-form topics since the topic string is interpolated directly.

### Difficulty Slider Width
Wrap `render_difficulty_picker()` in a 3-column layout `[1, 2, 1]` and render the slider only in the centre column. This halves its visual width without CSS changes.

### Difficulty Calibration
Rewrite the difficulty descriptor in the LLM user-message to be explicit about expected complexity at each level:

| Level | Label | LLM instruction |
|-------|-------|-----------------|
| 1 | Beginner | Single concept, no edge cases, 5-10 lines max |
| 2 | Easy | 1-2 concepts, basic edge case, 10-20 lines |
| 3 | Medium | Multiple concepts, handle edge cases, algorithm awareness |
| 4 | Hard | Optimised solution required, O(n) analysis expected, non-trivial logic |
| 5 | Expert | Advanced DS/algo, time+space complexity, production-level constraints |

Update the user-message in `next_question()` to pass this descriptor string alongside the numeric level so the model calibrates correctly.

## Functions / Classes

| Name | Signature | Returns | Notes |
|------|-----------|---------|-------|
| `render_topic_picker` | `() -> None` (modified) | None | `components.py`; adds `st.text_input` for custom topic below pills |
| `render_difficulty_picker` | `(topic: str) -> None` (modified) | None | `components.py`; wraps slider in `st.columns([1, 2, 1])` to halve width |
| `next_question` | `(topic: str, difficulty: int, history: list, past_questions: list \| None) -> dict` (modified) | dict | `llm.py`; appends difficulty descriptor string to user message; imports TOPICS from session |
| `TOPICS` | constant | list[str] | Defined once in `session.py`; imported by `llm.py` and `components.py` |

## Constraints
- `TOPICS` defined only in `session.py`; `llm.py` and `components.py` import it — no duplicate definitions.
- Custom topic input is additive: it does not remove or replace the pill grid.
- Custom topic value is passed as-is to `next_question()`; no server-side validation or whitelist.
- All DB ops via `tracker.py` only; `topic` column in `sessions` table is TEXT with no constraint, so custom topics store fine.
- Difficulty range stays `[1, 5]`; score range stays `[0, 10]`.
- No sidebar; all UI in main column.
- Slider width reduction must use column layout only; no new CSS injection.
- All LLM calls remain async; `asyncio.run()` at call sites.

## Acceptance Criteria
- Start screen shows all 16 preset topic pills plus a text input below them.
- Typing a custom topic and clicking "Start" generates a question on that topic.
- If both a pill and text input are active, text input takes precedence.
- Text input clears when "Next Question" is clicked.
- Difficulty slider is visually half the width of the current slider.
- At level 3, the LLM generates questions requiring multi-concept solutions and edge-case handling.
- At level 4-5, the LLM generates questions requiring algorithmic optimisation or advanced DS knowledge.
- `TOPICS` import works correctly in `llm.py` and `components.py` with no circular import.
- Existing session flow (submit, score, hint, skip, history) is unaffected.
