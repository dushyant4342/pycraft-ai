---
name: ui-design
description: Redesign or modernize the PyCraft AI Streamlit UI with polished fonts, clear visual hierarchy, interactive feedback, and a cohesive dark-first theme. Use when the user asks to improve, refresh, or redesign the app UI.
---

# UI Design Skill: PyCraft AI

## Goals
- Modern dark-first aesthetic with a clean accent color system
- Typography clarity via Google Fonts injected through `st.markdown`
- Interactive feedback: loading states, score animations, toast-style alerts
- Zero sidebar clutter (per project rules); all navigation stays in main column

---

## Design Tokens

```python
COLORS = {
    "bg":        "#0f1117",   # page background
    "surface":   "#1a1d27",   # card / container background
    "border":    "#2e3147",   # subtle dividers
    "accent":    "#7c6af7",   # primary CTA (purple-indigo)
    "accent_alt":"#4f9eff",   # secondary highlight (blue)
    "success":   "#22c55e",
    "warning":   "#f59e0b",
    "error":     "#ef4444",
    "text":      "#e2e8f0",   # body text
    "muted":     "#64748b",   # labels, captions
}

FONTS = {
    "heading": "Inter",       # clean geometric sans — headings
    "body":    "Inter",       # consistent with heading
    "mono":    "JetBrains Mono",  # code editor and snippets
}
```

---

## CSS Injection Pattern

Inject once at the top of `app.py` via `st.markdown(..., unsafe_allow_html=True)`:

```python
def inject_global_css() -> None:
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* ── Base ─────────────────────────────────────── */
        html, body, [data-testid="stAppViewContainer"] {
            background: #0f1117;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }

        /* ── Hide Streamlit chrome ────────────────────── */
        #MainMenu, footer, header { visibility: hidden; }
        [data-testid="stToolbar"] { display: none; }

        /* ── Typography ───────────────────────────────── */
        h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; color: #e2e8f0; }
        h2 { font-size: 1.35rem; font-weight: 600; color: #e2e8f0; }
        h3 { font-size: 1.1rem; font-weight: 500; color: #cbd5e1; }
        p, li { font-size: 0.95rem; line-height: 1.65; color: #cbd5e1; }

        /* ── Card / surface ───────────────────────────── */
        .ui-card {
            background: #1a1d27;
            border: 1px solid #2e3147;
            border-radius: 12px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.25rem;
        }

        /* ── Score badge ──────────────────────────────── */
        .score-badge {
            display: inline-block;
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.5rem;
            font-weight: 700;
            padding: 0.4rem 1.2rem;
            border-radius: 10px;
            letter-spacing: -1px;
        }
        .score-high  { background: #14532d; color: #22c55e; }
        .score-mid   { background: #451a03; color: #f59e0b; }
        .score-low   { background: #450a0a; color: #ef4444; }

        /* ── Accent button ────────────────────────────── */
        .stButton > button {
            background: #7c6af7;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.55rem 1.4rem;
            transition: background 0.18s ease, transform 0.12s ease;
        }
        .stButton > button:hover {
            background: #6657d4;
            transform: translateY(-1px);
        }
        .stButton > button:active { transform: translateY(0); }

        /* ── Code editor (streamlit-ace) ──────────────── */
        .ace_editor { border-radius: 8px !important; }

        /* ── Selectbox / input ────────────────────────── */
        .stSelectbox > div > div,
        .stTextInput > div > div > input {
            background: #1a1d27 !important;
            border: 1px solid #2e3147 !important;
            border-radius: 8px !important;
            color: #e2e8f0 !important;
        }

        /* ── Progress bar ─────────────────────────────── */
        .stProgress > div > div > div { background: #7c6af7; border-radius: 999px; }

        /* ── Divider ──────────────────────────────────── */
        hr { border-color: #2e3147; margin: 1.5rem 0; }

        /* ── Spinner text ─────────────────────────────── */
        .stSpinner > div { color: #7c6af7 !important; }

        /* ── Tag pill ─────────────────────────────────── */
        .tag-pill {
            display: inline-block;
            background: #2e3147;
            color: #94a3b8;
            font-size: 0.75rem;
            font-weight: 500;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            margin: 0.15rem;
        }
    </style>
    """, unsafe_allow_html=True)
```

---

## Reusable HTML Components

### Card wrapper
```python
def card(content_html: str) -> None:
    st.markdown(f'<div class="ui-card">{content_html}</div>', unsafe_allow_html=True)
```

### Score badge
```python
def score_badge(score: int) -> str:
    css_class = "score-high" if score >= 8 else ("score-mid" if score >= 5 else "score-low")
    return f'<span class="score-badge {css_class}">{score}/10</span>'
```

### Tag pills (topic, difficulty)
```python
def tag_pill(label: str) -> str:
    return f'<span class="tag-pill">{label}</span>'
```

### Toast-style inline alert
```python
def inline_alert(message: str, kind: str = "success") -> None:
    colors = {
        "success": ("#14532d", "#22c55e"),
        "warning": ("#451a03", "#f59e0b"),
        "error":   ("#450a0a", "#ef4444"),
        "info":    ("#1e3a5f", "#4f9eff"),
    }
    bg, fg = colors.get(kind, colors["info"])
    st.markdown(
        f'<div style="background:{bg};color:{fg};border-radius:8px;padding:0.75rem 1rem;'
        f'font-size:0.9rem;font-weight:500;margin:0.5rem 0;">{message}</div>',
        unsafe_allow_html=True,
    )
```

---

## Page Header Pattern

```python
def render_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div style="padding: 1.5rem 0 0.5rem 0;">
            <h1 style="margin:0;">{title}</h1>
            {"<p style='color:#64748b;margin:0.25rem 0 0 0;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        <hr>
        """,
        unsafe_allow_html=True,
    )
```

---

## Streamlit-ace Editor Config

```python
from streamlit_ace import st_ace

def code_editor(default: str = "", height: int = 300) -> str:
    return st_ace(
        value=default,
        language="python",
        theme="tomorrow_night",          # dark, high-contrast
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        auto_update=False,
        height=height,
        key="code_editor",
    )
```

---

## Difficulty Indicator

```python
def difficulty_bar(level: int, max_level: int = 5) -> None:
    filled = "█" * level
    empty  = "░" * (max_level - level)
    color  = "#22c55e" if level <= 2 else ("#f59e0b" if level <= 3 else "#ef4444")
    st.markdown(
        f'<p style="font-family:\'JetBrains Mono\',monospace;color:{color};'
        f'font-size:1.1rem;letter-spacing:2px;margin:0;">{filled}{empty} {level}/{max_level}</p>',
        unsafe_allow_html=True,
    )
```

---

## Layout Rules

1. **Single column** for main content; use `st.columns` only for metrics row.
2. Wrap every major section in `card()` so surfaces stay visually grouped.
3. CTA buttons always full-width via `use_container_width=True`.
4. Loading states: wrap Claude calls with `st.spinner("Reviewing your code...")`.
5. After score is shown, render `inline_alert()` with motivational feedback.
6. Metrics row (score, streak, difficulty) at top using `st.columns(3)`.

### Metrics row example
```python
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Last Score", f"{last_score}/10")
with col2:
    st.metric("Streak", f"{streak} correct")
with col3:
    st.metric("Difficulty", f"Level {difficulty}/5")
```

---

## Do / Don't

| Do | Don't |
|----|-------|
| Use `#7c6af7` accent consistently | Mix multiple accent hues |
| JetBrains Mono for all code/numbers | Use system monospace fonts |
| Wrap sections in `ui-card` divs | Use raw `st.write` for structured content |
| Show spinner during LLM calls | Let UI freeze silently |
| Use `inline_alert` for score feedback | Use `st.success/error` (breaks theme) |
| Keep sidebar empty | Add nav or filters to sidebar |
