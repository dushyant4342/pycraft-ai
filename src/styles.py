import streamlit as st


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
        .block-container {
            padding-top: 2rem !important;
            max-width: 1280px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* ── Typography ────────────────────────────────── */
        h1, h2, h3, p, li, span { font-family: 'Inter', sans-serif; }

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
        .greeting-name { color: #a78bfa; font-weight: 700; }

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

        /* ── Stats strip ───────────────────────────────── */
        .stats-strip {
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1.25rem;
        }
        .stat-chip {
            background: #161925;
            border: 1px solid #252840;
            border-radius: 10px;
            padding: 0.65rem 1rem;
            text-align: center;
            flex: 1;
        }
        .stat-chip-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.25rem;
            font-weight: 700;
            color: #e2e8f0;
            line-height: 1.2;
        }
        .stat-chip-label {
            font-size: 0.65rem;
            font-weight: 600;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 0.25rem;
        }

        /* ── Metric cards ──────────────────────────────── */
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
        .topic-name { font-weight: 600; font-size: 0.9rem; color: #cbd5e1; }
        .topic-meta { font-size: 0.78rem; color: #64748b; margin-top: 0.1rem; }

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
        .tag-topic  { background: #2e1065; color: #c4b5fd; }
        .tag-diff-1 { background: #052e16; color: #4ade80; }
        .tag-diff-2 { background: #1a2e16; color: #86efac; }
        .tag-diff-3 { background: #1c1500; color: #fbbf24; }
        .tag-diff-4 { background: #1c0d00; color: #fb923c; }
        .tag-diff-5 { background: #1c0606; color: #f87171; }

        /* ── Question text ─────────────────────────────── */
        .question-text { font-size: 1.05rem; line-height: 1.7; color: #e2e8f0; font-weight: 400; }
        .question-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: #7c6af7;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.5rem;
        }

        /* ── Buttons ───────────────────────────────────── */
        div[data-testid="stVerticalBlock"] .stButton > button,
        .stButton > button {
            background: linear-gradient(135deg, #7c6af7 0%, #6657d4 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 0.7rem 1.6rem !important;
            box-shadow: 0 2px 18px #7c6af750 !important;
            letter-spacing: 0.02em !important;
            width: 100% !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #6657d4 0%, #5548b8 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 22px #7c6af760 !important;
        }
        .stButton > button:disabled {
            background: #252840 !important;
            color: #475569 !important;
            box-shadow: none !important;
            transform: none !important;
        }
        /* Sign-out ghost chip */
        div:has(.signout-anchor) ~ div .stButton > button {
            background: transparent !important;
            border: 1px solid #252840 !important;
            color: #64748b !important;
            box-shadow: none !important;
            width: auto !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            border-radius: 999px !important;
            padding: 0.3rem 1rem !important;
        }
        div:has(.signout-anchor) ~ div .stButton > button:hover {
            color: #fca5a5 !important;
            border-color: #7f1d1d !important;
            background: #1c06061a !important;
            transform: none !important;
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
        .stSelectbox label {
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            color: #64748b !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
        }

        /* ── Tabs ──────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background: #161925;
            border-radius: 10px;
            padding: 0.25rem;
            border: 1px solid #252840;
            gap: 0.25rem;
            width: 100%;
            display: flex;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px !important;
            color: #64748b !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            flex: 1 1 0 !important;
            text-align: center !important;
            justify-content: center !important;
        }
        .stTabs [aria-selected="true"] { background: #7c6af7 !important; color: #fff !important; }
        .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
        .stTabs [data-baseweb="tab-border"]    { display: none !important; }

        /* ── Expander (history rows) ───────────────────── */
        .streamlit-expanderHeader {
            background: #161925 !important;
            border: 1px solid #252840 !important;
            border-radius: 10px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.82rem !important;
            color: #cbd5e1 !important;
            padding: 0.5rem 0.9rem !important;
        }
        .streamlit-expanderHeader:hover {
            border-color: #7c6af7 !important;
            color: #e2e8f0 !important;
        }
        .streamlit-expanderContent {
            background: #0d1120 !important;
            border: 1px solid #252840 !important;
            border-top: none !important;
            border-bottom-left-radius: 10px !important;
            border-bottom-right-radius: 10px !important;
            padding: 0.75rem !important;
        }
        /* Hints expander */
        details[data-testid="stExpander"] summary p { font-weight: 600 !important; }

        /* ── Topic picker radio pills ──────────────────── */
        div[data-testid="stRadioGroup"] { justify-content: center; }
        div[data-testid="stRadioGroup"] [role="radiogroup"] {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.45rem !important;
            justify-content: center !important;
            padding: 0 !important;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] label {
            display: flex !important;
            align-items: center !important;
            gap: 0.3rem !important;
            background: #161925 !important;
            border: 1.5px solid #252840 !important;
            border-radius: 9999px !important;
            padding: 0.32rem 0.95rem !important;
            cursor: pointer !important;
            white-space: nowrap !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: #94a3b8 !important;
            transition: border-color 0.15s, color 0.15s, background 0.15s !important;
            user-select: none !important;
            line-height: 1.4 !important;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] label:hover {
            border-color: #6366f1 !important;
            color: #c4b5fd !important;
            background: #1a1d2e !important;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, #6366f1, #818cf8) !important;
            border-color: transparent !important;
            color: #fff !important;
            font-weight: 700 !important;
            box-shadow: 0 2px 12px #6366f145 !important;
        }
        div[data-testid="stRadioGroup"] [role="radiogroup"] input[type="radio"],
        div[data-testid="stRadioGroup"] [role="radiogroup"] label > div { display: none !important; }
        div[data-testid="stRadioGroup"] [role="radiogroup"] label > p {
            margin: 0 !important;
            font-size: 0.82rem !important;
            color: inherit !important;
        }

        /* ── Slider ────────────────────────────────────── */
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background: #7c6af7 !important;
            border-color: #7c6af7 !important;
        }

        /* ── Misc ──────────────────────────────────────── */
        hr { border-color: #252840 !important; margin: 1.25rem 0 !important; }
        .stSpinner > div { color: #7c6af7 !important; }
    </style>
    """, unsafe_allow_html=True)