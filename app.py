import os
import re
import io
import json
import time
import base64
import hashlib
import hmac
import secrets
import random
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
    ImageDraw,
    ImageFont
)

# ============================================================
# NEUROLENS — OFFICIAL BRAND CONFIGURATION
# ============================================================

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"
TAGLINE = "Explore cognition, behavior & the brain"

APP_DIR = Path(__file__).resolve().parent

# Use the exact logo supplied by the creator.
LOGO_PATH = APP_DIR / "neurolens_logo.png"

if not LOGO_PATH.exists():
    raise FileNotFoundError(
        "Official NeuroLens logo missing. "
        "Upload neurolens_logo.png beside app.py."
    )

APP_LOGO = Image.open(LOGO_PATH).convert("RGBA")

st.set_page_config(
    page_title="NEUROLENS",
    page_icon=APP_LOGO,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# OPTIONAL INTEGRATIONS
# ============================================================

try:
    from supabase import create_client
except ImportError:
    create_client = None

try:
    from google import genai
except ImportError:
    genai = None

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    import numpy as np
except ImportError:
    np = None

# ============================================================
# CONFIGURATION AND SECRETS
# ============================================================

def get_secret(key, default=""):
    try:
        value = st.secrets.get(key, os.getenv(key, default))
    except Exception:
        value = os.getenv(key, default)

    return str(value or default).strip()


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

EASYPAISA_NAME = get_secret(
    "EASYPAISA_NAME",
    CREATOR
)

EASYPAISA_NUMBER = get_secret("EASYPAISA_NUMBER")
CONSULTATION_FEE = get_secret("CONSULTATION_FEE")
INTERNATIONAL_PAYMENT_URL = get_secret(
    "INTERNATIONAL_PAYMENT_URL"
)

# Never hardcode payment credentials or private API keys.

supabase = None
supabase_error = None

if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
    except Exception as exc:
        supabase_error = str(exc)


def database_connected():
    return supabase is not None


# ============================================================
# FEATURE FLAGS
# ============================================================

FEATURES = {
    "accounts": True,
    "brain_explorer": True,
    "cstc_learning": True,
    "ayna_ai": True,
    "personal_healing": True,
    "private_journal": True,
    "brain_puzzle": True,
    "cognitive_challenges": True,
    "research_library": True,
    "personal_ebook": True,
    "photo_studio": True,
    "progress_dashboard": True,
    "appointments": True,
    "owner_control_center": True,
    "staff_workspace": True,

    # Advanced Stage — separate extensions.
    "advanced_neurosocial": False,
    "advanced_brain_lab": False,
    "behaviour_decoding": False,
    "advanced_photo_studio": False,
    "research_engine_pro": False,
    "hardware_integrations": False,
}


def feature_enabled(name):
    return bool(FEATURES.get(name, False))


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "page": "Welcome",
    "language": "English",
    "authenticated": False,
    "user": None,
    "user_id": None,
    "ai_messages": [],
    "ai_requests_today": 0,
    "ai_request_date": str(date.today()),
    "private_unlocked": False,
    "private_last_activity": None,
    "private_failed_attempts": 0,
    "private_lock_until": None,
    "journal_entries": [],
    "ebook_chapters": [],
    "research_bookmarks": [],
    "challenge_results": [],
    "lab_results": [],
    "photo_original": None,
    "photo_edited": None,
    "appointment_requests": [],
    "owner_authenticated": False,
    "staff_authenticated": False,
}


for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# PREMIUM NEUROLENS VISUAL DESIGN
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --neuro-purple: #8057F5;
        --neuro-blue: #38BDF8;
        --neuro-dark: #101329;
        --neuro-glass: rgba(128, 87, 245, 0.10);
    }

    .stApp {
        background:
            radial-gradient(
                circle at 12% 8%,
                rgba(128,87,245,.13),
                transparent 30%
            ),
            radial-gradient(
                circle at 90% 20%,
                rgba(56,189,248,.10),
                transparent 28%
            );
    }

    .neuro-title {
        font-size: clamp(34px, 5vw, 58px);
        font-weight: 850;
        letter-spacing: 3px;
        margin-bottom: 0;
        background: linear-gradient(
            90deg,
            #A78BFA,
            #38BDF8
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .neuro-subtitle {
        font-size: 17px;
        opacity: .78;
    }

    .neuro-card {
        padding: 22px;
        border-radius: 20px;
        border: 1px solid rgba(150,150,255,.22);
        background: rgba(128,87,245,.07);
        margin-bottom: 14px;
    }

    .neuro-hero {
        padding: 30px;
        border-radius: 24px;
        border: 1px solid rgba(150,150,255,.25);
        background: linear-gradient(
            135deg,
            rgba(128,87,245,.15),
            rgba(56,189,248,.08)
        );
    }

    div.stButton > button {
        border-radius: 12px;
        min-height: 42px;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(150,150,255,.15);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# BRAND HEADER
# ============================================================

def render_brand_header():
    left, right = st.columns([1, 5])

    with left:
        st.image(APP_LOGO, width=105)

    with right:
        st.markdown(
            f'<div class="neuro-title">{APP_NAME}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="neuro-subtitle">{TAGLINE}</div>',
            unsafe_allow_html=True
        )

        st.caption(f"Created by {CREATOR}")


# ============================================================
# SECURITY HELPERS
# ============================================================

def hash_secret(value, salt=None):
    if salt is None:
        salt = secrets.token_bytes(32)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt,
        310000
    )

    return salt.hex(), digest.hex()


def verify_secret(value, salt_hex, expected_hex):
    try:
        salt = bytes.fromhex(salt_hex)
        _, actual = hash_secret(value, salt)

        return hmac.compare_digest(
            actual,
            expected_hex
        )
    except Exception:
        return False


def clear_private_session():
    st.session_state.private_unlocked = False
    st.session_state.private_last_activity = None


def private_session_active(timeout_minutes=10):
    last = st.session_state.private_last_activity

    if not st.session_state.private_unlocked or not last:
        return False

    elapsed = (
        datetime.now() - last
    ).total_seconds()
    if elapsed > timeout_minutes * 60:
        clear_private_session()
        return False

    st.session_state.private_last_activity = datetime.now()
    return True
# ============================================================
# NEUROLENS — DATABASE FOUNDATION
# ============================================================

DB_PATH = APP_DIR / "neurolens_data.db"


def get_local_db():
    connection = sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_local_db()
    cursor = connection.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS user_settings (
        user_id TEXT PRIMARY KEY,
        language TEXT DEFAULT 'English',
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS ai_conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ai_messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(conversation_id)
            REFERENCES ai_conversations(id),
        FOREIGN KEY(user_id)
            REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS challenge_results (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        challenge_type TEXT NOT NULL,
        score REAL DEFAULT 0,
        details TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS journal_entries (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        encrypted_content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS research_bookmarks (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        article_url TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS appointment_requests (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        purpose TEXT NOT NULL,
        preferred_date TEXT,
        preferred_time TEXT,
        contact_method TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        action TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    connection.commit()
    connection.close()


initialize_database()


# ============================================================
# DATABASE HELPERS
# ============================================================

def db_execute(query, values=()):
    connection = get_local_db()

    try:
        connection.execute(query, values)
        connection.commit()
        return True
    except sqlite3.Error as exc:
        st.error(f"Database operation failed: {exc}")
        return False
    finally:
        connection.close()


def db_fetch_one(query, values=()):
    connection = get_local_db()

    try:
        result = connection.execute(
            query,
            values
        ).fetchone()

        return dict(result) if result else None
    finally:
        connection.close()


def db_fetch_all(query, values=()):
    connection = get_local_db()

    try:
        results = connection.execute(
            query,
            values
        ).fetchall()

        return [dict(row) for row in results]
    finally:
        connection.close()


def create_audit_log(user_id, action):
    db_execute(
        """
        INSERT INTO audit_logs
        (id, user_id, action, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            secrets.token_hex(16),
            user_id,
            action,
            datetime.now().isoformat()
        )
    )


# ============================================================
# ACCOUNT VALIDATION
# ============================================================

def valid_email(email):
    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email.strip()
        )
    )


def valid_password(password):
    return (
        len(password) >= 10
        and any(c.isupper() for c in password)
        and any(c.islower() for c in password)
        and any(c.isdigit() for c in password)
    )


# ============================================================
# ACCOUNT REGISTRATION
# ============================================================

def register_user(username, email, password, display_name):
    username = username.strip()
    email = email.strip().lower()
    display_name = display_name.strip()

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if not valid_email(email):
        return False, "Enter a valid email address."

    if not valid_password(password):
        return False, (
            "Password must contain at least 10 characters, "
            "uppercase, lowercase and a number."
        )

    if len(display_name) < 2:
        return False, "Enter your display name."

    existing = db_fetch_one(
        """
        SELECT id FROM users
        WHERE username = ? OR email = ?
        """,
        (username, email)
    )

    if existing:
        return False, "Username or email is already registered."

    user_id = secrets.token_hex(16)
    salt, password_hash = hash_secret(password)
    now = datetime.now().isoformat()

    success = db_execute(
        """
        INSERT INTO users (
            id, username, email,
            password_hash, password_salt,
            display_name, role, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'user', ?)
        """,
        (
            user_id,
            username,
            email,
            password_hash,
            salt,
            display_name,
            now
        )
    )

    if not success:
        return False, "Account could not be created."

    db_execute(
        """
        INSERT INTO user_settings
        (user_id, language, created_at)
        VALUES (?, 'English', ?)
        """,
        (user_id, now)
    )

    create_audit_log(user_id, "account_created")

    return True, "Account created successfully."


# ============================================================
# ACCOUNT LOGIN
# ============================================================

def authenticate_user(identifier, password):
    identifier = identifier.strip().lower()

    user = db_fetch_one(
        """
        SELECT * FROM users
        WHERE lower(username) = ?
           OR lower(email) = ?
        """,
        (identifier, identifier)
    )

    if not user:
        return None

    if not user["active"]:
        return None

    valid = verify_secret(
        password,
        user["password_salt"],
        user["password_hash"]
    )

    if not valid:
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "display_name": user["display_name"],
        "role": user["role"]
    }


# ============================================================
# CURRENT USER ACCESS
# ============================================================

def current_user():
    if not st.session_state.authenticated:
        return None

    return {
        "id": st.session_state.user_id,
        **(st.session_state.user or {})
    }


def require_login():
    if not st.session_state.authenticated:
        st.warning("Please login to access this feature.")
        return False

    return True


def user_data_query(table, columns="*"):
    allowed_tables = {
        "challenge_results",
        "journal_entries",
        "research_bookmarks",
        "appointment_requests"
    }

    if table not in allowed_tables:
        raise ValueError("Table is not permitted.")

    if not require_login():
        return []

    user_id = st.session_state.user_id

    return db_fetch_all(
        f"""
        SELECT {columns}
        FROM {table}
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    )


# ============================================================
# ACCOUNT LOGIN / SIGNUP PAGE
# ============================================================

def page_account():
    render_brand_header()

    st.title("Your NeuroLens Account")

    if st.session_state.authenticated:
        user = current_user()

        st.success(
            f"Welcome, {user['display_name']}!"
        )

        st.write(f"Username: {user['username']}")
        st.write(f"Email: {user['email']}")
        st.write(f"Account role: {user['role']}")

        if st.button("Logout", use_container_width=True):
            create_audit_log(
                st.session_state.user_id,
                "logout"
            )

            clear_private_session()

            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.user_id = None

            st.session_state.ai_messages = []

            st.rerun()

        return

    login_tab, signup_tab = st.tabs([
        "Login",
        "Create Account"
    ])

    with login_tab:
        st.subheader("Login to NeuroLens")

        identifier = st.text_input(
            "Username or email",
            key="account_login_identifier"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="account_login_password"
        )

        if st.button(
            "Login",
            key="account_login_button",
            use_container_width=True
        ):
            user = authenticate_user(
                identifier,
                password
            )

            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.user_id = user["id"]

                create_audit_log(
                    user["id"],
                    "login"
                )

                st.success("Login successful.")
                st.rerun()
            else:
                st.error(
                    "Login failed. Check your details."
                )

    with signup_tab:
        st.subheader("Create your account")

        display_name = st.text_input(
            "Display name",
            key="signup_display_name"
        )

        username = st.text_input(
            "Username",
            key="signup_username"
        )

        email = st.text_input(
            "Email address",
            key="signup_email"
        )

        new_password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="signup_confirm_password"
        )

        st.caption(
            "Use at least 10 characters with uppercase, "
            "lowercase and a number."
        )

        if st.button(
            "Create Account",
            key="signup_button",
            use_container_width=True
        ):
            if new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                success, message = register_user(
                    username,
                    email,
                    new_password,
                    display_name
                )

                if success:
                    st.success(message)
                    st.info(
                        "You can now login using your username "
                        "or email."
                    )
                else:
                    st.error(message)


# ============================================================
# USER-SPECIFIC ACTIVITY STORAGE
# ============================================================

def save_challenge_result(
    challenge_type,
    score,
    details=None
):
    if not require_login():
        return False

    return db_execute(
        """
        INSERT INTO challenge_results (
            id,
            user_id,
            challenge_type,
            score,
            details,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            secrets.token_hex(16),
            st.session_state.user_id,
            challenge_type,
            float(score),
            json.dumps(details or {}),
            datetime.now().isoformat()
        )
    )


def save_research_bookmark(title, article_url=""):
    if not require_login():
        return False

    return db_execute(
        """
        INSERT INTO research_bookmarks (
            id,
            user_id,
            title,
            article_url,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            secrets.token_hex(16),
            st.session_state.user_id,
            title,
            article_url,
            datetime.now().isoformat()
        )
    )


# ============================================================
# ACCOUNT STATUS
# ============================================================

def account_status():
    if not st.session_state.authenticated:
        return "Guest"

    user = current_user()

    return user["display_name"]
# ============================================================
# NEUROLENS — WELCOME DASHBOARD
# ============================================================

def render_neural_animation():
    components.html(
        """
        <div class="neural-stage">
            <div class="neural-orbit orbit-one"></div>
            <div class="neural-orbit orbit-two"></div>
            <div class="neural-orbit orbit-three"></div>

            <div class="neural-brain">
                <div class="brain-core">N</div>
                <div class="brain-pulse"></div>
            </div>
        </div>

        <style>
        .neural-stage {
            height: 280px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .neural-brain {
            width: 125px;
            height: 125px;
            border-radius: 48% 52% 45% 55%;
            background: linear-gradient(
                135deg,
                #8057F5,
                #38BDF8
            );
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow:
                0 0 35px rgba(128,87,245,.65),
                0 0 75px rgba(56,189,248,.25);
            animation: brainFloat 3s ease-in-out infinite;
            position: relative;
            z-index: 2;
        }

        .brain-core {
            color: white;
            font-size: 48px;
            font-weight: 900;
            font-family: Arial;
        }

        .brain-pulse {
            position: absolute;
            inset: -15px;
            border: 2px solid #38BDF8;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .neural-orbit {
            position: absolute;
            border: 1px solid rgba(56,189,248,.45);
            border-radius: 50%;
            animation: rotateOrbit 12s linear infinite;
        }

        .orbit-one {
            width: 190px;
            height: 190px;
        }

        .orbit-two {
            width: 235px;
            height: 235px;
            animation-duration: 18s;
        }

        .orbit-three {
            width: 275px;
            height: 275px;
            animation-duration: 25s;
        }

        @keyframes brainFloat {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-12px);
            }
        }

        @keyframes pulse {
            0% {
                transform: scale(.85);
                opacity: .9;
            }
            100% {
                transform: scale(1.45);
                opacity: 0;
            }
        }

        @keyframes rotateOrbit {
            from {
                transform: rotate(0deg);
            }
            to {
                transform: rotate(360deg);
            }
        }
        </style>
        """,
        height=290
    )


# ============================================================
# FEATURE NAVIGATION
# ============================================================

INITIAL_STAGE_PAGES = [
    "Welcome",
    "Account",
    "Brain Explorer",
    "CSTC Learning",
    "Interactive Lab",
    "Brain Puzzle",
    "Cognitive Challenges",
    "Personal Healing",
    "Private Journal",
    "Research Library",
    "Personal eBook",
    "Photo Studio",
    "Progress Dashboard",
    "Appointments",
    "Ask Ayna AI",
    "Owner Control Center",
    "Staff Workspace",
    "Advanced Stage Preview",
    "Settings",
]


def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()


# ============================================================
# FEATURE CARD
# ============================================================

def feature_card(title, description, page_name):
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(description)

        if st.button(
            "Open",
            key=f"open_{page_name.replace(' ', '_')}",
            use_container_width=True
        ):
            navigate_to(page_name)


# ============================================================
# WELCOME DASHBOARD
# ============================================================

def page_welcome():
    render_brand_header()

    st.markdown(
        """
        <div class="neuro-hero">
            <h1>Welcome to NeuroLens</h1>
            <h3>Explore the science behind your mind.</h3>
            <p>
                Discover cognition, behavior, brain circuits,
                learning, memory and artificial intelligence
                through interactive neuroscience experiences.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    left, right = st.columns([1.1, 1])

    with left:
        render_neural_animation()

    with right:
        st.markdown("### Meet Ayna AI")

        st.write(
            "Hello! I am Ayna, your NeuroLens AI learning "
            "companion. Let's explore the brain, behavior "
            "and cognition together."
        )

        st.caption(
            "Educational AI assistant — not a medical professional."
        )

        if st.button(
            "Start Exploring",
            use_container_width=True,
            type="primary"
        ):
            navigate_to("Brain Explorer")

        if st.button(
            "Talk to Ayna AI",
            use_container_width=True
        ):
            navigate_to("Ask Ayna AI")

    st.divider()

    st.markdown("## Explore NeuroLens")

    feature_data = [
        (
            "Brain Explorer",
            "Explore brain regions and their cognitive functions."
        ),
        (
            "CSTC Learning",
            "Learn direct, indirect and hyperdirect pathways."
        ),
        (
            "Interactive Lab",
            "Try cognitive experiments and learning activities."
        ),
        (
            "Brain Puzzle",
            "Reconstruct brain images using interactive puzzles."
        ),
        (
            "Cognitive Challenges",
            "Practice memory, attention, Stroop and decision tasks."
        ),
        (
            "Personal Healing",
            "Explore reflection and evidence-informed coping tools."
        ),
        (
            "Private Journal",
            "Keep personal reflections in a protected space."
        ),
        (
            "Research Library",
            "Discover neuroscience and research publications."
        ),
        (
            "Personal eBook",
            "Write and organize your own chapters and stories."
        ),
        (
            "Photo Studio",
            "Create portraits, effects and downloadable edits."
        ),
        (
            "Progress Dashboard",
            "Review your learning activity and self-reports."
        ),
        (
            "Appointments",
            "Submit a request for a discussion with the creator."
        ),
    ]

    columns = st.columns(3)

    for index, item in enumerate(feature_data):
        with columns[index % 3]:
            feature_card(
                item[0],
                item[1],
                item[0]
            )

    st.divider()

    st.markdown("## Your Learning Journey")

    journey_steps = [
        "Discover the brain",
        "Understand neural circuits",
        "Explore cognitive processes",
        "Practice interactive challenges",
        "Read scientific research",
        "Track your learning progress"
    ]

    for index, step in enumerate(journey_steps, 1):
        st.markdown(f"**{index}.** {step}")

    st.divider()

    st.markdown(
        """
        <div class="neuro-card">
            <h3>Advanced Stage</h3>
            <p>
                Future extensions will include advanced
                NeuroSocial, 3D brain simulations, hardware
                integrations, research tools and expanded
                Ayna AI capabilities.
            </p>
            <p><b>Status: Planned / Preview</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        "NeuroLens | Created by Ayna Jaffri | "
        "Explore cognition, behavior & the brain"
    )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.image(APP_LOGO, width=115)

        st.markdown("## NEUROLENS")
        st.caption(TAGLINE)

        if st.session_state.authenticated:
            user = current_user()
            st.success(
                f"Welcome, {user['display_name']}"
            )
        else:
            st.info("Guest access")

        st.divider()

        st.markdown("### Initial Stage")

        for page_name in INITIAL_STAGE_PAGES:
            if st.button(
                page_name,
                key=f"sidebar_{page_name}",
                use_container_width=True
            ):
                st.session_state.page = page_name
                st.rerun()

        st.divider()

        st.markdown("### Advanced Stage")

        st.caption("Planned extensions")

        advanced_pages = [
            "NeuroSocial Advanced",
            "Behaviour Decoding",
            "Advanced Brain Lab",
            "Research Engine Pro",
            "Hardware Hub"
        ]

        for page_name in advanced_pages:
            st.button(
                page_name,
                key=f"advanced_{page_name}",
                disabled=True,
                use_container_width=True
            )

        st.divider()

        st.caption(
            "NeuroLens © Ayna Jaffri"
        )


# ============================================================
# PAGE ROUTER
# ============================================================

def render_current_page():
    page = st.session_state.page

    if page == "Welcome":
        page_welcome()

    elif page == "Account":
        page_account()

    else:
        st.info(
            f"{page} module will be connected in its "
            "respective implementation section."
        )

        if st.button("Back to Welcome"):
            navigate_to("Welcome")


# ============================================================
# MAIN APPLICATION ENTRY
# ============================================================

def run_neurolens():
    render_sidebar()
    render_current_page()


if __name__ == "__main__":
    run_neurolens()
