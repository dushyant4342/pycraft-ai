import bcrypt
import streamlit as st

from tracker import create_auth_token, create_user, get_user_by_email


def hash_password(password: str) -> str:
    """Return bcrypt hash of password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Return True if password matches the bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _inject_auth_css() -> None:
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: #0d0f18 !important;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stMain"] { background: #0d0f18 !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        #MainMenu, footer, header { visibility: hidden; }
        [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
        .block-container {
            padding-top: 4rem !important;
            max-width: 460px !important;
        }
        .auth-logo {
            font-size: 3rem;
            text-align: center;
            margin-bottom: 0.25rem;
        }
        .auth-title {
            font-size: 2rem;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(135deg, #7c6af7 0%, #4f9eff 50%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
            margin: 0;
        }
        .auth-tagline {
            text-align: center;
            color: #64748b;
            font-size: 0.88rem;
            margin-top: 0.4rem;
            margin-bottom: 2rem;
        }
        /* Tabs */
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
            flex: 1;
            justify-content: center;
        }
        .stTabs [aria-selected="true"] {
            background: #7c6af7 !important;
            color: #fff !important;
        }
        /* Inputs */
        .stTextInput > div > div > input {
            background: #161925 !important;
            border: 1px solid #252840 !important;
            border-radius: 8px !important;
            color: #e2e8f0 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.9rem !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #7c6af7 !important;
            box-shadow: 0 0 0 2px #7c6af720 !important;
        }
        label { color: #94a3b8 !important; font-size: 0.82rem !important; font-weight: 500 !important; }
        /* Button */
        .stButton > button {
            background: linear-gradient(135deg, #7c6af7 0%, #6657d4 100%) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 0.6rem 1.6rem !important;
            width: 100% !important;
            box-shadow: 0 2px 12px #7c6af740 !important;
            transition: all 0.18s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #6657d4 0%, #5548b8 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 18px #7c6af760 !important;
        }
        /* Alert */
        .stAlert {
            background: #1c0606 !important;
            border: 1px solid #991b1b !important;
            border-radius: 8px !important;
            color: #fca5a5 !important;
        }
        .auth-divider {
            text-align: center;
            color: #252840;
            font-size: 0.78rem;
            margin: 0.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)


def login_ui() -> None:
    """Render centered login/register card. Sets session_state.user_id and user_email on success."""
    _inject_auth_css()

    st.markdown(
        '<div class="auth-logo">⚡</div>'
        '<p class="auth-title">PyCraft AI</p>'
        '<p class="auth-tagline">Adaptive Python practice, powered by AI</p>',
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        st.markdown("<br>", unsafe_allow_html=True)
        email = st.text_input("Email address", key="login_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign In", key="login_btn"):
            if not email or not password:
                st.error("Email and password are required.")
            else:
                user = get_user_by_email(email)
                if user and verify_password(password, user["password_hash"]):
                    st.session_state.user_id = user["id"]
                    st.session_state.user_email = user["email"]
                    st.session_state["_pending_token"] = create_auth_token(user["id"], user["email"])
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab_register:
        st.markdown("<br>", unsafe_allow_html=True)
        reg_email = st.text_input("Email address", key="reg_email", placeholder="you@example.com")
        reg_password = st.text_input("Password", type="password", key="reg_password", placeholder="Min 6 characters")
        reg_confirm = st.text_input("Confirm password", type="password", key="reg_confirm", placeholder="Repeat password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Create Account", key="reg_btn"):
            if not reg_email or not reg_password:
                st.error("Email and password are required.")
            elif reg_password != reg_confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    user_id = create_user(reg_email, hash_password(reg_password))
                    st.session_state.user_id = user_id
                    st.session_state.user_email = reg_email
                    st.session_state["_pending_token"] = create_auth_token(user_id, reg_email)
                    st.rerun()
                except ValueError:
                    st.error("An account with that email already exists.")
