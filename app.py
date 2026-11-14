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
# ============================================================
# PART 4 — BRAIN EXPLORER
# ============================================================

BRAIN_REGIONS = {
    "Prefrontal Cortex": {
        "location": "Frontal lobe",
        "functions": [
            "Planning",
            "Working memory",
            "Decision-making",
            "Cognitive control",
            "Goal-directed behavior"
        ],
        "explanation": (
            "The prefrontal cortex contributes to executive "
            "functions, including planning, working memory, "
            "decision-making and cognitive control."
        ),
        "connection": (
            "It interacts with other cortical and subcortical "
            "regions, including the basal ganglia and thalamus."
        )
    },

    "Hippocampus": {
        "location": "Medial temporal lobe",
        "functions": [
            "Episodic memory",
            "Memory consolidation",
            "Spatial navigation",
            "Contextual learning"
        ],
        "explanation": (
            "The hippocampus is important for forming and "
            "retrieving episodic memories and for spatial "
            "and contextual learning."
        ),
        "connection": (
            "It interacts with cortical areas and other "
            "limbic structures."
        )
    },

    "Striatum": {
        "location": "Basal ganglia",
        "functions": [
            "Action selection",
            "Reward learning",
            "Habit formation",
            "Motor and cognitive loops"
        ],
        "explanation": (
            "The striatum receives cortical and thalamic input "
            "and participates in selecting and learning actions."
        ),
        "connection": (
            "It is a major input structure of the basal ganglia "
            "and participates in CSTC circuits."
        )
    },

    "Anterior Cingulate Cortex": {
        "location": "Medial frontal cortex",
        "functions": [
            "Conflict monitoring",
            "Error processing",
            "Effort allocation",
            "Motivational control"
        ],
        "explanation": (
            "The anterior cingulate cortex contributes to "
            "monitoring actions, detecting conflict and "
            "evaluating the need for control."
        ),
        "connection": (
            "It interacts with prefrontal, limbic and "
            "subcortical networks."
        )
    },

    "Amygdala": {
        "location": "Medial temporal lobe",
        "functions": [
            "Emotional learning",
            "Threat processing",
            "Emotional salience",
            "Associative learning"
        ],
        "explanation": (
            "The amygdala contributes to emotional learning "
            "and the processing of biologically relevant stimuli."
        ),
        "connection": (
            "It interacts with hippocampal, prefrontal and "
            "hypothalamic systems."
        )
    },

    "Thalamus": {
        "location": "Diencephalon",
        "functions": [
            "Information relay",
            "Sensory processing",
            "Cortical communication",
            "Motor circuit integration"
        ],
        "explanation": (
            "The thalamus is a major relay and integration "
            "structure connecting multiple brain networks."
        ),
        "connection": (
            "Basal ganglia output reaches motor and other "
            "cortical areas through thalamic nuclei."
        )
    }
}


def page_brain_explorer():

    render_brand_header()

    st.title("Interactive Brain Explorer")

    st.write(
        "Explore selected brain structures, their functions "
        "and their connections with cognitive processes."
    )

    selected_region = st.selectbox(
        "Select a brain region",
        list(BRAIN_REGIONS.keys())
    )

    data = BRAIN_REGIONS[selected_region]

    st.markdown(
        f"""
        <div class="neuro-card">
            <h2>{selected_region}</h2>
            <p><b>Location:</b> {data['location']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Main functions")

        for function in data["functions"]:
            st.markdown(f"- {function}")

    with right:
        st.subheader("Scientific explanation")
        st.write(data["explanation"])

        st.subheader("Neural connections")
        st.write(data["connection"])

    st.divider()

    st.subheader("Explore cognitive roles")

    for function in data["functions"]:
        with st.expander(function):
            st.write(
                f"{function} is one of the processes "
                f"associated with the {selected_region}. "
                "Its performance depends on distributed "
                "brain networks rather than one isolated region."
            )

    st.caption(
        "Educational overview. Brain functions are distributed "
        "and should not be interpreted as one-region-one-function."
    )


# ============================================================
# PART 4 — CSTC CIRCUIT LEARNING
# ============================================================

CSTC_PATHWAYS = {

    "Direct Pathway": {
        "summary": (
            "The direct pathway is commonly described as "
            "facilitating selected actions through reduced "
            "inhibitory output from basal ganglia output nuclei."
        ),

        "steps": [
            ("Cortex", "Excitatory glutamatergic input"),
            ("Striatum D1", "Inhibitory GABAergic projection"),
            ("GPi / SNr", "Reduced inhibitory output"),
            ("Thalamus", "Disinhibition"),
            ("Cortex", "Increased facilitation of selected activity")
        ],

        "direction": (
            "Cortex → Striatum D1 → GPi/SNr → Thalamus → Cortex"
        )
    },

    "Indirect Pathway": {
        "summary": (
            "The indirect pathway contributes to suppressing "
            "competing or unwanted actions through a sequence "
            "of inhibitory and excitatory connections."
        ),

        "steps": [
            ("Cortex", "Excitatory glutamatergic input"),
            ("Striatum D2", "Inhibitory GABAergic projection"),
            ("GPe", "Reduced inhibitory output"),
            ("STN", "Increased excitatory drive"),
            ("GPi / SNr", "Increased inhibitory output"),
            ("Thalamus", "Greater inhibition"),
            ("Cortex", "Reduced facilitation")
        ],

        "direction": (
            "Cortex → Striatum D2 → GPe → STN → GPi/SNr "
            "→ Thalamus → Cortex"
        )
    },

    "Hyperdirect Pathway": {
        "summary": (
            "The hyperdirect pathway provides a relatively "
            "rapid route from cortex to the subthalamic nucleus, "
            "which can increase basal ganglia output inhibition."
        ),

        "steps": [
            ("Cortex", "Excitatory glutamatergic projection"),
            ("STN", "Excitatory glutamatergic projection"),
            ("GPi / SNr", "Increased inhibitory output"),
            ("Thalamus", "Increased inhibition"),
            ("Cortex", "Reduced thalamocortical facilitation")
        ],

        "direction": (
            "Cortex → STN → GPi/SNr → Thalamus → Cortex"
        )
    }
}


def render_cstc_pathway(pathway_name):

    pathway = CSTC_PATHWAYS[pathway_name]

    st.markdown(f"### {pathway_name}")

    st.write(pathway["summary"])

    st.markdown("**Circuit direction:**")

    st.code(
        pathway["direction"],
        language="text"
    )

    st.markdown("**Step-by-step circuit nodes:**")

    for index, step in enumerate(pathway["steps"]):

        node, explanation = step

        st.markdown(
            f"""
            <div class="neuro-card">
                <h4>{index + 1}. {node}</h4>
                <p>{explanation}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if index < len(pathway["steps"]) - 1:
            st.markdown(
                "<div style='text-align:center;"
                "font-size:24px;color:#38BDF8'>↓</div>",
                unsafe_allow_html=True
            )


def page_cstc_learning():

    render_brand_header()

    st.title("CSTC Circuit Learning")

    st.write(
        "Cortico-Striato-Thalamo-Cortical circuits "
        "connect cortical regions, basal ganglia structures "
        "and thalamic nuclei."
    )

    st.info(
        "This section focuses on structural circuit organization. "
        "Functional and molecular explanations can be explored "
        "as separate learning layers."
    )

    selected_pathway = st.radio(
        "Choose a circuit",
        [
            "Direct Pathway",
            "Indirect Pathway",
            "Hyperdirect Pathway"
        ],
        horizontal=False
    )

    render_cstc_pathway(selected_pathway)

    st.divider()

    st.subheader("Important structures")

    structures = {
        "Striatum": (
            "Includes caudate nucleus and putamen in the "
            "dorsal striatum. D1 and D2 describe receptor "
            "populations, not completely separate anatomical organs."
        ),

        "GPe": (
            "External segment of globus pallidus. "
            "A key node in the indirect pathway."
        ),

        "STN": (
            "Subthalamic nucleus. Provides excitatory "
            "glutamatergic input to basal ganglia output nuclei."
        ),

        "GPi": (
            "Internal segment of globus pallidus. "
            "A major inhibitory output structure."
        ),

        "SNr": (
            "Substantia nigra pars reticulata. "
            "Another important basal ganglia output structure."
        ),

        "SNc": (
            "Substantia nigra pars compacta. "
            "Provides dopaminergic modulation of striatal circuits."
        ),

        "Thalamus": (
            "Relevant motor loop relays include VA and VL nuclei. "
            "Different CSTC loops involve different thalamic regions."
        )
    }

    for structure, description in structures.items():

        with st.expander(structure):

            st.write(description)

    st.warning(
        "Simplified teaching diagrams do not represent every "
        "collateral projection, feedback connection or "
        "cell-type-specific pathway."
    )
# ============================================================
# REGISTER PART 4 PAGES
# ============================================================

# These functions are now available to the main router.
# ============================================================
# PART 5 — INTERACTIVE NEUROSCIENCE LAB
# ============================================================

def save_experiment_result(name, score, details=None):
    if st.session_state.authenticated:
        return save_challenge_result(
            name,
            score,
            details or {}
        )

    st.session_state.challenge_results.append({
        "challenge": name,
        "score": score,
        "details": details or {},
        "date": datetime.now().isoformat()
    })

    return True


def page_lab():

    render_brand_header()

    st.title("Interactive Neuroscience Lab")

    st.write(
        "Welcome to your interactive cognitive learning lab. "
        "Choose an experiment and explore your task performance."
    )

    st.markdown(
        """
        <div class="neuro-card">
            <h3>Neuroscience Learning Environment</h3>
            <p>
                These experiments measure task performance,
                such as response accuracy and completion time.
                They do not directly measure brain activity.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    experiment = st.selectbox(
        "Select your experiment",
        [
            "Memory Sequence",
            "Attention Detection",
            "Stroop Control",
            "Decision and Reward",
            "Pattern Recognition"
        ]
    )

    st.divider()

    if experiment == "Memory Sequence":
        memory_experiment()

    elif experiment == "Attention Detection":
        attention_experiment()

    elif experiment == "Stroop Control":
        stroop_experiment()

    elif experiment == "Decision and Reward":
        decision_experiment()

    elif experiment == "Pattern Recognition":
        pattern_experiment()


# ============================================================
# MEMORY EXPERIMENT
# ============================================================

def memory_experiment():

    st.subheader("Memory Sequence")

    if "memory_sequence" not in st.session_state:
        st.session_state.memory_sequence = None

    if "memory_started" not in st.session_state:
        st.session_state.memory_started = False

    if "memory_submitted" not in st.session_state:
        st.session_state.memory_submitted = False

    if st.button("Start Memory Experiment"):

        sequence = [
            random.randint(0, 9)
            for _ in range(6)
        ]

        st.session_state.memory_sequence = sequence
        st.session_state.memory_started = True
        st.session_state.memory_submitted = False
        st.rerun()

    if st.session_state.memory_started:

        st.info(
            "Memorize this sequence. When you are ready, "
            "press Hide Sequence."
        )

        if not st.session_state.memory_submitted:
            st.markdown(
                "### " + "  —  ".join(
                    map(
                        str,
                        st.session_state.memory_sequence
                    )
                )
            )

            if st.button("Hide Sequence"):
                st.session_state.memory_submitted = True
                st.rerun()

        else:
            answer = st.text_input(
                "Enter the six digits in the same order",
                max_chars=6
            )

            if st.button("Submit Memory Answer"):

                correct = "".join(
                    map(
                        str,
                        st.session_state.memory_sequence
                    )
                )

                submitted = answer.strip()

                if len(submitted) != 6 or not submitted.isdigit():
                    st.error("Enter exactly six digits.")

                else:
                    score = sum(
                        a == b
                        for a, b in zip(correct, submitted)
                    )

                    percentage = score / 6 * 100

                    save_experiment_result(
                        "Memory Sequence",
                        percentage,
                        {
                            "correct_positions": score,
                            "total_positions": 6
                        }
                    )

                    st.success(
                        f"Correct positions: {score}/6"
                    )

                    st.metric(
                        "Position accuracy",
                        f"{percentage:.1f}%"
                    )

                    st.session_state.memory_started = False
                    st.session_state.memory_submitted = False
                    st.session_state.memory_sequence = None


# ============================================================
# ATTENTION EXPERIMENT
# ============================================================

def attention_experiment():

    st.subheader("Attention Detection")

    st.write(
        "Find the target letter X among distractors."
    )

    if "attention_grid" not in st.session_state:
        st.session_state.attention_grid = None

    if "attention_target" not in st.session_state:
        st.session_state.attention_target = None

    if st.button("Generate Attention Task"):

        letters = [
            random.choice(["O", "Q", "C", "G"])
            for _ in range(24)
        ]

        target_index = random.randint(0, 23)
        letters[target_index] = "X"

        st.session_state.attention_grid = letters
        st.session_state.attention_target = target_index

    if st.session_state.attention_grid is not None:

        st.markdown("### Find X")

        grid = st.columns(6)

        for index, letter in enumerate(
            st.session_state.attention_grid
        ):

            with grid[index % 6]:

                st.markdown(
                    f"<div class='neuro-card' "
                    f"style='text-align:center'>"
                    f"<h2>{letter}</h2></div>",
                    unsafe_allow_html=True
                )

        selected = st.number_input(
            "Enter the position of X (1–24)",
            min_value=1,
            max_value=24,
            step=1
        )

        if st.button("Check Attention Answer"):

            correct = (
                selected - 1
                == st.session_state.attention_target
            )

            score = 100 if correct else 0

            save_experiment_result(
                "Attention Detection",
                score,
                {
                    "correct": correct,
                    "target_position":
                        st.session_state.attention_target + 1
                }
            )

            if correct:
                st.success("Correct target detected!")

            else:
                st.error(
                    "Not quite. The target was at position "
                    f"{st.session_state.attention_target + 1}."
                )

            st.session_state.attention_grid = None
            st.session_state.attention_target = None


# ============================================================
# STROOP CONTROL EXPERIMENT
# ============================================================

def stroop_experiment():

    st.subheader("Stroop Control Task")

    st.write(
        "Select the ink color, not the written word."
    )

    colors = {
        "RED": "#FF3333",
        "BLUE": "#3399FF",
        "GREEN": "#20C878",
        "YELLOW": "#E6C229"
    }

    if "stroop_word" not in st.session_state:
        st.session_state.stroop_word = None

    if "stroop_ink" not in st.session_state:
        st.session_state.stroop_ink = None

    if st.button("Start Stroop Trial"):

        word = random.choice(list(colors.keys()))
        ink = random.choice(list(colors.keys()))

        st.session_state.stroop_word = word
        st.session_state.stroop_ink = ink

    if st.session_state.stroop_word:

        st.markdown(
            f"""
            <div style="
                padding:35px;
                text-align:center;
                font-size:44px;
                font-weight:900;
                color:{colors[st.session_state.stroop_ink]};
            ">
                {st.session_state.stroop_word}
            </div>
            """,
            unsafe_allow_html=True
        )

        answer = st.radio(
            "What is the ink color?",
            list(colors.keys()),
            horizontal=True
        )

        if st.button("Submit Stroop Answer"):

            correct = (
                answer == st.session_state.stroop_ink
            )

            score = 100 if correct else 0

            save_experiment_result(
                "Stroop Control",
                score,
                {
                    "correct": correct,
                    "word": st.session_state.stroop_word,
                    "ink": st.session_state.stroop_ink
                }
            )

            if correct:
                st.success("Correct ink color!")

            else:
                st.error(
                    "Incorrect. The ink color was "
                    f"{st.session_state.stroop_ink}."
                )

            st.session_state.stroop_word = None
            st.session_state.stroop_ink = None


# ============================================================
# DECISION AND REWARD EXPERIMENT
# ============================================================

def decision_experiment():

    st.subheader("Decision and Reward")

    st.write(
        "Choose between two hypothetical reward options."
    )

    st.markdown(
        """
        <div class="neuro-card">
            <h3>Option A</h3>
            <p>Receive Rs. 1,000 today.</p>
        </div>

        <div class="neuro-card">
            <h3>Option B</h3>
            <p>Receive Rs. 1,500 after 30 days.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    choice = st.radio(
        "Which option would you choose?",
        [
            "Option A — Rs. 1,000 today",
            "Option B — Rs. 1,500 after 30 days"
        ]
    )

    reason = st.text_area(
        "Why did you choose this option?",
        max_chars=500
    )

    if st.button("Save My Decision"):

        save_experiment_result(
            "Decision and Reward",
            0,
            {
                "choice": choice,
                "reason": reason
            }
        )

        st.success("Your decision has been recorded.")

        st.info(
            "Reflection: Your choice may involve time "
            "preference, perceived uncertainty, immediate "
            "reward and future value. One choice cannot "
            "identify your personality or brain activity."
        )


# ============================================================
# PATTERN RECOGNITION EXPERIMENT
# ============================================================

def pattern_experiment():

    st.subheader("Pattern Recognition")

    patterns = [
        {
            "sequence": [2, 4, 8, 16, 32],
            "answer": 64,
            "explanation": "Each number doubles."
        },
        {
            "sequence": [3, 6, 9, 12, 15],
            "answer": 18,
            "explanation": "Add 3 each time."
        },
        {
            "sequence": [1, 4, 9, 16, 25],
            "answer": 36,
            "explanation": "These are consecutive square numbers."
        },
        {
            "sequence": [5, 10, 20, 40, 80],
            "answer": 160,
            "explanation": "Each number doubles."
        }
    ]

    if "pattern_task" not in st.session_state:
        st.session_state.pattern_task = None

    if st.button("Generate Pattern"):

        st.session_state.pattern_task = random.choice(
            patterns
        )

    if st.session_state.pattern_task:

        task = st.session_state.pattern_task

        sequence_text = " → ".join(
            map(str, task["sequence"])
        )

        st.markdown(
            f"### {sequence_text} → ?"
        )

        answer = st.number_input(
            "Enter the next number",
            min_value=0,
            max_value=10000,
            step=1
        )

        if st.button("Check Pattern"):

            correct = answer == task["answer"]

            score = 100 if correct else 0

            save_experiment_result(
                "Pattern Recognition",
                score,
                {
                    "correct": correct,
                    "answer": task["answer"]
                }
            )

            if correct:
                st.success("Correct pattern!")

            else:
                st.error(
                    f"The correct answer was {task['answer']}."
                )

            st.info(task["explanation"])

            st.session_state.pattern_task = None


# ============================================================
# COGNITIVE CHALLENGES PAGE
# ============================================================

def page_cognitive_challenges():

    render_brand_header()

    st.title("Cognitive Challenges")

    st.write(
        "Practice five cognitive task categories and "
        "review your task performance."
    )

    st.markdown(
        """
        <div class="neuro-card">
            <h3>Learning and Self-Observation</h3>
            <p>
                Results describe performance on these specific
                tasks only. They are not clinical assessments,
                IQ tests or direct measurements of brain activity.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    challenge_names = [
        "Memory Sequence",
        "Attention Detection",
        "Stroop Control",
        "Decision and Reward",
        "Pattern Recognition"
    ]

    selected = st.selectbox(
        "Choose a cognitive challenge",
        challenge_names
    )

    if selected == "Memory Sequence":
        memory_experiment()

    elif selected == "Attention Detection":
        attention_experiment()

    elif selected == "Stroop Control":
        stroop_experiment()

    elif selected == "Decision and Reward":
        decision_experiment()

    elif selected == "Pattern Recognition":
        pattern_experiment()


# ============================================================
# PART 5 PAGE REGISTRATION
# ============================================================

# page_lab() and page_cognitive_challenges()
# are now available for the final application router.

# ============================================================
# PART 6 — PERSONAL HEALING + PRIVATE JOURNAL
# ============================================================

import base64

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None
    InvalidToken = Exception


# ============================================================
# PRIVATE JOURNAL DATABASE EXTENSION
# ============================================================

def initialize_private_journal():

    connection = get_local_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS journal_vault (
            user_id TEXT PRIMARY KEY,
            pin_salt TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            recovery_salt TEXT NOT NULL,
            recovery_hash TEXT NOT NULL,
            pin_wrapped_key TEXT NOT NULL,
            recovery_wrapped_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


initialize_private_journal()


# ============================================================
# ENCRYPTION HELPERS
# ============================================================

def derive_encryption_key(secret, salt_hex):

    salt = bytes.fromhex(salt_hex)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt,
        480000,
        dklen=32
    )

    return base64.urlsafe_b64encode(derived)


def encrypt_private_data(data, master_key):

    if Fernet is None:
        raise RuntimeError(
            "Install cryptography to enable private encryption."
        )

    cipher = Fernet(master_key)

    return cipher.encrypt(
        data.encode("utf-8")
    ).decode("utf-8")


def decrypt_private_data(encrypted_data, master_key):

    if Fernet is None:
        raise RuntimeError(
            "Install cryptography to enable private encryption."
        )

    cipher = Fernet(master_key)

    return cipher.decrypt(
        encrypted_data.encode("utf-8")
    ).decode("utf-8")


# ============================================================
# CREATE PRIVATE JOURNAL VAULT
# ============================================================

def create_private_vault(pin):

    if not require_login():
        return False, "Please login first.", None

    if Fernet is None:
        return (
            False,
            "Encryption library is not installed.",
            None
        )

    if not pin.isdigit() or not 6 <= len(pin) <= 12:
        return (
            False,
            "PIN must contain 6 to 12 digits.",
            None
        )

    user_id = st.session_state.user_id

    existing = db_fetch_one(
        """
        SELECT user_id FROM journal_vault
        WHERE user_id = ?
        """,
        (user_id,)
    )

    if existing:
        return (
            False,
            "A private vault already exists.",
            None
        )

    pin_salt, pin_hash = hash_secret(pin)

    recovery_code = secrets.token_urlsafe(24)

    recovery_salt, recovery_hash = hash_secret(
        recovery_code
    )

    master_key = Fernet.generate_key()

    pin_key = derive_encryption_key(
        pin,
        pin_salt
    )

    recovery_key = derive_encryption_key(
        recovery_code,
        recovery_salt
    )

    pin_wrapped_key = Fernet(
        pin_key
    ).encrypt(master_key).decode("utf-8")

    recovery_wrapped_key = Fernet(
        recovery_key
    ).encrypt(master_key).decode("utf-8")

    connection = get_local_db()

    try:
        connection.execute(
            """
            INSERT INTO journal_vault (
                user_id,
                pin_salt,
                pin_hash,
                recovery_salt,
                recovery_hash,
                pin_wrapped_key,
                recovery_wrapped_key,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                pin_salt,
                pin_hash,
                recovery_salt,
                recovery_hash,
                pin_wrapped_key,
                recovery_wrapped_key,
                datetime.now().isoformat()
            )
        )

        connection.commit()

    except sqlite3.Error as exc:
        return False, str(exc), None

    finally:
        connection.close()

    create_audit_log(
        user_id,
        "private_vault_created"
    )

    return (
        True,
        "Private journal created.",
        recovery_code
    )


# ============================================================
# LOAD MASTER KEY USING PIN
# ============================================================

def unlock_private_vault(pin):

    if not require_login():
        return False

    if Fernet is None:
        st.error("Encryption library is unavailable.")
        return False

    user_id = st.session_state.user_id

    lock_until = st.session_state.private_lock_until

    if lock_until:
        if datetime.now() < lock_until:
            st.error(
                "Too many attempts. Please wait before trying again."
            )
            return False

        st.session_state.private_lock_until = None
        st.session_state.private_failed_attempts = 0

    vault = db_fetch_one(
        """
        SELECT * FROM journal_vault
        WHERE user_id = ?
        """,
        (user_id,)
    )

    if not vault:
        st.error("Create your private journal first.")
        return False

    if not verify_secret(
        pin,
        vault["pin_salt"],
        vault["pin_hash"]
    ):

        st.session_state.private_failed_attempts += 1

        if st.session_state.private_failed_attempts >= 5:

            st.session_state.private_lock_until = (
                datetime.now() + timedelta(minutes=5)
            )

            st.error(
                "Five incorrect attempts. Vault locked for 5 minutes."
            )

        else:
            st.error("Incorrect PIN.")

        return False

    pin_key = derive_encryption_key(
        pin,
        vault["pin_salt"]
    )

    try:
        master_key = Fernet(
            pin_key
        ).decrypt(
            vault["pin_wrapped_key"].encode("utf-8")
        )

    except Exception:
        st.error("Vault could not be unlocked.")
        return False

    st.session_state.private_master_key = (
        base64.urlsafe_b64encode(master_key).decode("utf-8")
    )

    st.session_state.private_unlocked = True
    st.session_state.private_last_activity = datetime.now()
    st.session_state.private_failed_attempts = 0

    create_audit_log(
        user_id,
        "private_vault_unlocked"
    )

    return True


# ============================================================
# RECOVER VAULT USING RECOVERY CODE
# ============================================================

def recover_private_vault(recovery_code, new_pin):

    if not require_login():
        return False, "Please login first."

    if Fernet is None:
        return False, "Encryption library is unavailable."

    if not new_pin.isdigit() or not 6 <= len(new_pin) <= 12:
        return False, "New PIN must contain 6 to 12 digits."

    user_id = st.session_state.user_id

    vault = db_fetch_one(
        """
        SELECT * FROM journal_vault
        WHERE user_id = ?
        """,
        (user_id,)
    )

    if not vault:
        return False, "Private vault does not exist."

    if not verify_secret(
        recovery_code,
        vault["recovery_salt"],
        vault["recovery_hash"]
    ):
        return False, "Incorrect recovery code."

    recovery_key = derive_encryption_key(
        recovery_code,
        vault["recovery_salt"]
    )

    try:
        master_key = Fernet(
            recovery_key
        ).decrypt(
            vault["recovery_wrapped_key"].encode("utf-8")
        )

    except Exception:
        return False, "Recovery failed."

    new_salt, new_hash = hash_secret(new_pin)

    new_key = derive_encryption_key(
        new_pin,
        new_salt
    )

    wrapped_key = Fernet(
        new_key
    ).encrypt(master_key).decode("utf-8")

    db_execute(
        """
        UPDATE journal_vault
        SET pin_salt = ?,
            pin_hash = ?,
            pin_wrapped_key = ?
        WHERE user_id = ?
        """,
        (
            new_salt,
            new_hash,
            wrapped_key,
            user_id
        )
    )

    clear_private_session()

    create_audit_log(
        user_id,
        "private_vault_pin_recovered"
    )

    return True, "PIN changed successfully."


# ============================================================
# SAVE ENCRYPTED JOURNAL ENTRY
# ============================================================

def save_private_journal_entry(content):

    if not require_login():
        return False

    if not private_session_active():
        st.error("Unlock your journal first.")
        return False

    content = content.strip()

    if not content:
        st.warning("Write something before saving.")
        return False

    master_key = base64.urlsafe_b64decode(
        st.session_state.private_master_key
    )

    encrypted = encrypt_private_data(
        content,
        master_key
    )

    entry_id = secrets.token_hex(16)

    now = datetime.now().isoformat()

    success = db_execute(
        """
        INSERT INTO journal_entries (
            id,
            user_id,
            encrypted_content,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            st.session_state.user_id,
            encrypted,
            now,
            now
        )
    )

    if success:
        create_audit_log(
            st.session_state.user_id,
            "private_journal_entry_saved"
        )

    return success


# ============================================================
# READ PRIVATE JOURNAL ENTRIES
# ============================================================

def get_private_journal_entries():

    if not require_login():
        return []

    if not private_session_active():
        return []

    master_key = base64.urlsafe_b64decode(
        st.session_state.private_master_key
    )

    entries = db_fetch_all(
        """
        SELECT id, encrypted_content, created_at
        FROM journal_entries
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (st.session_state.user_id,)
    )

    decrypted_entries = []

    for entry in entries:

        try:
            content = decrypt_private_data(
                entry["encrypted_content"],
                master_key
            )

            decrypted_entries.append({
                "id": entry["id"],
                "content": content,
                "created_at": entry["created_at"]
            })

        except Exception:
            decrypted_entries.append({
                "id": entry["id"],
                "content": "[Unable to decrypt entry]",
                "created_at": entry["created_at"]
            })

    return decrypted_entries


# ============================================================
# DELETE PRIVATE JOURNAL ENTRY
# ============================================================

def delete_private_journal_entry(entry_id):

    if not require_login():
        return False

    if not private_session_active():
        return False

    success = db_execute(
        """
        DELETE FROM journal_entries
        WHERE id = ? AND user_id = ?
        """,
        (
            entry_id,
            st.session_state.user_id
        )
    )

    if success:
        create_audit_log(
            st.session_state.user_id,
            "private_journal_entry_deleted"
        )

    return success


# ============================================================
# PERSONAL JOURNAL PAGE
# ============================================================

def page_private_journal():

    render_brand_header()

    st.title("Private Journal")
    st.caption("Your personal space. Private by default.")

    if not require_login():
        return

    if Fernet is None:
        st.error(
            "Private encryption is unavailable. "
            "Install cryptography before using this feature."
        )
        return

    vault = db_fetch_one(
        """
        SELECT user_id FROM journal_vault
        WHERE user_id = ?
        """,
        (st.session_state.user_id,)
    )

    if not vault:

        st.subheader("Create your private vault")

        pin = st.text_input(
            "Create a 6–12 digit PIN",
            type="password",
            key="journal_new_pin"
        )

        confirm = st.text_input(
            "Confirm PIN",
            type="password",
            key="journal_confirm_pin"
        )

        if st.button("Create Private Journal"):

            if pin != confirm:
                st.error("PINs do not match.")

            else:
                success, message, recovery = (
                    create_private_vault(pin)
                )

                if success:

                    st.success(message)

                    st.warning(
                        "Save this recovery code somewhere safe. "
                        "It will not be shown again."
                    )

                    st.code(recovery)

                    st.info(
                        "After saving the recovery code, unlock "
                        "your journal using your PIN."
                    )

                else:
                    st.error(message)

        return

    if not private_session_active():

        st.subheader("Unlock Private Journal")

        pin = st.text_input(
            "Enter your PIN",
            type="password",
            key="journal_unlock_pin"
        )

        if st.button("Unlock Journal"):

            if unlock_private_vault(pin):
                st.success("Journal unlocked.")
                st.rerun()

        with st.expander("Forgot your PIN?"):

            recovery_code = st.text_input(
                "Recovery code",
                type="password",
                key="journal_recovery_code"
            )

            new_pin = st.text_input(
                "New PIN",
                type="password",
                key="journal_recovery_new_pin"
            )

            if st.button("Recover and Change PIN"):

                success, message = recover_private_vault(
                    recovery_code,
                    new_pin
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

        return

    st.success("Your private journal is unlocked.")

    st.subheader("Write a private entry")

    content = st.text_area(
        "Your thoughts",
        height=180,
        placeholder="Write your private reflection here..."
    )

    if st.button("Save Private Entry"):

        if save_private_journal_entry(content):
            st.success("Your encrypted entry has been saved.")
            st.rerun()

    st.divider()

    st.subheader("Your saved entries")

    entries = get_private_journal_entries()

    if not entries:
        st.info("No journal entries yet.")

    for entry in entries:

        with st.expander(
            entry["created_at"][:16]
        ):

            st.write(entry["content"])

            if st.button(
                "Delete this entry",
                key=f"delete_journal_{entry['id']}"
            ):

                if delete_private_journal_entry(
                    entry["id"]
                ):
                    st.success("Entry deleted.")
                    st.rerun()

    st.divider()

    if st.button("Lock My Journal"):

        clear_private_session()

        if "private_master_key" in st.session_state:
            del st.session_state["private_master_key"]

        st.rerun()


# ============================================================
# PERSONAL HEALING CONTENT
# ============================================================

HEALING_EXERCISES = {

    "Grounding Exercise": {
        "description": (
            "A short sensory grounding activity to help "
            "you reconnect with the present moment."
        ),
        "steps": [
            "Notice five things you can see.",
            "Notice four things you can physically feel.",
            "Listen for three sounds around you.",
            "Identify two smells, if possible.",
            "Notice one taste or take a gentle breath."
        ]
    },

    "Gentle Breathing": {
        "description": (
            "A gentle breathing practice. Keep your breathing "
            "comfortable; do not force or hold your breath."
        ),
        "steps": [
            "Sit comfortably.",
            "Relax your shoulders.",
            "Breathe in gently.",
            "Breathe out slowly.",
            "Repeat for a few comfortable cycles."
        ]
    },

    "Thought Reflection": {
        "description": (
            "A structured way to observe a thought without "
            "automatically treating it as a fact."
        ),
        "steps": [
            "What happened?",
            "What thought appeared?",
            "What emotion did you notice?",
            "What evidence supports this thought?",
            "What is another possible interpretation?"
        ]
    },

    "Small Next Step": {
        "description": (
            "Break an overwhelming task into one manageable action."
        ),
        "steps": [
            "Name one thing that feels difficult.",
            "Identify the smallest possible next action.",
            "Decide when you can try it.",
            "Notice what support might help.",
            "Recognize the effort, not just the outcome."
        ]
    }
}


# ============================================================
# PERSONAL HEALING PAGE
# ============================================================

def page_personal_healing():

    render_brand_header()

    st.title("Personal Healing Journey")

    st.write(
        "A supportive space for reflection, emotional "
        "awareness and gentle self-care."
    )

    st.info(
        "Ayna AI provides educational and supportive guidance. "
        "It is not a therapist, medical professional or "
        "replacement for mental-health treatment."
    )

    st.subheader("Personal check-in")

    mood = st.select_slider(
        "How are you feeling right now?",
        options=[
            "Very difficult",
            "Difficult",
            "Neutral",
            "Okay",
            "Good"
        ],
        value="Neutral"
    )

    energy = st.select_slider(
        "How is your energy?",
        options=[
            "Very low",
            "Low",
            "Moderate",
            "High",
            "Very high"
        ],
        value="Moderate"
    )

    reflection = st.text_area(
        "Would you like to write what is on your mind?",
        placeholder="Share only what you feel comfortable sharing."
    )

    if st.button("Save Check-in"):

        st.session_state.setdefault(
            "healing_checkins",
            []
        )

        st.session_state.healing_checkins.append({
            "mood": mood,
            "energy": energy,
            "reflection": reflection,
            "date": datetime.now().isoformat()
        })

        st.success("Your check-in is saved in this session.")

        st.caption(
            "This check-in is currently session-only, "
            "not permanently stored."
        )

    st.divider()

    st.subheader("Choose a supportive exercise")

    exercise_name = st.selectbox(
        "Select an exercise",
        list(HEALING_EXERCISES.keys())
    )

    exercise = HEALING_EXERCISES[exercise_name]

    st.write(exercise["description"])

    for index, step in enumerate(
        exercise["steps"],
        1
    ):
        st.markdown(f"**{index}.** {step}")

    st.divider()

    st.subheader("Reflection prompts")

    prompt = random.choice([
        "What is one thing you handled today?",
        "What would you say to a friend feeling this way?",
        "What is one small thing you can control today?",
        "What do you need more of right now?",
        "What helped you feel safe or supported recently?"
    ])

    st.markdown(
        f"<div class='neuro-card'><h3>{prompt}</h3></div>",
        unsafe_allow_html=True
    )

    answer = st.text_area(
        "Your reflection",
        key="healing_prompt_answer"
    )

    if st.button("Save Reflection"):

        st.session_state.setdefault(
            "healing_reflections",
            []
        )

        st.session_state.healing_reflections.append({
            "prompt": prompt,
            "answer": answer,
            "date": datetime.now().isoformat()
        })

        st.success(
            "Reflection saved in this session."
        )

    st.divider()

    st.subheader("Need additional support?")

    st.write(
        "If distress feels overwhelming, consider speaking "
        "with a trusted person or qualified mental-health "
        "professional. If you may hurt yourself or someone "
        "else, seek immediate local emergency support and "
        "stay with someone you trust."
    )


# ============================================================
# PART 6 PAGE REGISTRATION
# ============================================================

# page_private_journal()
# page_personal_healing()
# are ready for the final router.
# ============================================================
# PART 7A — RESEARCH LIBRARY
# ============================================================

def search_europe_pmc(query, page_size=10):

    query = query.strip()

    if not query:
        return []

    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    params = urlencode({
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "core"
    })

    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/"
        "rest/search?" + params
    )

    request = Request(
        url,
        headers={
            "User-Agent": "NeuroLens-Research-App/1.0"
        }
    )

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        return data.get("resultList", {}).get("result", [])

    except Exception as exc:
        st.error(f"Research search failed: {exc}")
        return []


def research_article_url(article):

    pmid = article.get("pmid")
    pmcid = article.get("pmcid")
    doi = article.get("doi")

    if pmcid:
        return f"https://europepmc.org/articles/{pmcid}"

    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    if doi:
        return f"https://doi.org/{doi}"

    return ""


def page_research_library():

    render_brand_header()

    st.title("NeuroLens Research Library")

    st.write(
        "Search scientific publications in neuroscience, "
        "mental health, cognition, behavior and related fields."
    )

    st.caption(
        "Research records are retrieved from Europe PMC. "
        "Full-text availability depends on publisher and access rights."
    )

    query = st.text_input(
        "Search research publications",
        placeholder=(
            "Example: cognitive neuroscience, CSTC circuits, "
            "consciousness, memory, addiction"
        )
    )

    max_results = st.selectbox(
        "Number of results",
        [5, 10, 20],
        index=1
    )

    if st.button("Search Research"):

        results = search_europe_pmc(
            query,
            max_results
        )

        st.session_state.research_results = results

    results = st.session_state.get(
        "research_results",
        []
    )

    if results:

        st.divider()

        for index, article in enumerate(results):

            title = article.get(
                "title",
                "Title unavailable"
            )

            authors = article.get(
                "authorString",
                "Authors unavailable"
            )

            journal = article.get(
                "journalTitle",
                "Journal unavailable"
            )

            year = article.get(
                "firstPublicationDate",
                article.get("pubYear", "Date unavailable")
            )

            doi = article.get(
                "doi",
                "Not available"
            )

            abstract = article.get(
                "abstractText",
                "Abstract not available in this record."
            )

            article_url = research_article_url(article)

            with st.expander(
                f"{index + 1}. {title}"
            ):

                st.write(f"**Authors:** {authors}")
                st.write(f"**Journal:** {journal}")
                st.write(f"**Publication date:** {year}")
                st.write(f"**DOI:** {doi}")

                st.markdown("**Abstract**")
                st.write(abstract)

                if article_url:
                    st.markdown(
                        f"[Open publication]({article_url})"
                    )

                if st.button(
                    "Bookmark Publication",
                    key=f"research_bookmark_{index}"
                ):

                    if require_login():

                        success = save_research_bookmark(
                            title,
                            article_url
                        )

                        if success:
                            st.success("Publication bookmarked.")

                if st.button(
                    "Prepare AI Summary",
                    key=f"research_summary_{index}"
                ):

                    st.session_state.research_summary_text = (
                        f"Title: {title}\n"
                        f"Authors: {authors}\n"
                        f"Journal: {journal}\n"
                        f"Date: {year}\n"
                        f"DOI: {doi}\n"
                        f"Abstract: {abstract}"
                    )

                    st.session_state.page = "Ask Ayna AI"
                    st.rerun()

    elif query:
        st.info(
            "No results loaded yet. Press Search Research."
        )

    st.divider()

    st.subheader("My Research Bookmarks")

    if require_login():

        bookmarks = user_data_query(
            "research_bookmarks"
        )

        if bookmarks:

            for item in bookmarks:

                st.markdown(
                    f"**{item['title']}**"
                )

                if item.get("article_url"):
                    st.markdown(
                        f"[Open article]({item['article_url']})"
                    )

                st.caption(item["created_at"])

        else:
            st.info("You have not saved any publications yet.")
# ============================================================
# PART 7B — PERSONAL EBOOK DATABASE
# ============================================================

def initialize_ebook_database():

    connection = get_local_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ebook_chapters (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            chapter_title TEXT NOT NULL,
            category TEXT DEFAULT 'Personal Writing',
            encrypted_content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


initialize_ebook_database()


# ============================================================
# SAVE PRIVATE EBOOK CHAPTER
# ============================================================

def save_ebook_chapter(title, category, content):

    if not require_login():
        return False

    if not private_session_active():
        return False

    title = title.strip()
    content = content.strip()

    if not title or not content:
        return False

    master_key = base64.urlsafe_b64decode(
        st.session_state.private_master_key
    )

    encrypted_content = encrypt_private_data(
        content,
        master_key
    )

    now = datetime.now().isoformat()

    return db_execute(
        """
        INSERT INTO ebook_chapters (
            id,
            user_id,
            chapter_title,
            category,
            encrypted_content,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            secrets.token_hex(16),
            st.session_state.user_id,
            title,
            category,
            encrypted_content,
            now,
            now
        )
    )


# ============================================================
# LOAD PRIVATE EBOOK CHAPTERS
# ============================================================

def load_ebook_chapters():

    if not require_login():
        return []

    if not private_session_active():
        return []

    master_key = base64.urlsafe_b64decode(
        st.session_state.private_master_key
    )

    chapters = db_fetch_all(
        """
        SELECT *
        FROM ebook_chapters
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (st.session_state.user_id,)
    )

    output = []

    for chapter in chapters:

        try:
            content = decrypt_private_data(
                chapter["encrypted_content"],
                master_key
            )

            output.append({
                "id": chapter["id"],
                "title": chapter["chapter_title"],
                "category": chapter["category"],
                "content": content,
                "created_at": chapter["created_at"]
            })

        except Exception:
            continue

    return output


# ============================================================
# DELETE EBOOK CHAPTER
# ============================================================

def delete_ebook_chapter(chapter_id):

    if not require_login():
        return False

    if not private_session_active():
        return False

    return db_execute(
        """
        DELETE FROM ebook_chapters
        WHERE id = ? AND user_id = ?
        """,
        (
            chapter_id,
            st.session_state.user_id
        )
    )


# ============================================================
# EBOOK EXPORT
# ============================================================

def create_ebook_pdf(title, chapters):

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            PageBreak
        )
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch

    except ImportError:
        return None

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch
    )

    styles = getSampleStyleSheet()

    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 20),
        Paragraph(
            f"Created in NeuroLens by "
            f"{st.session_state.user['display_name']}",
            styles["Normal"]
        ),
        Spacer(1, 30)
    ]

    for chapter in chapters:

        story.append(
            Paragraph(
                chapter["title"],
                styles["Heading1"]
            )
        )

        story.append(Spacer(1, 12))

        safe_content = (
            chapter["content"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

        story.append(
            Paragraph(
                safe_content,
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 25))

    document.build(story)

    output.seek(0)

    return output.getvalue()


# ============================================================
# PERSONAL EBOOK PAGE
# ============================================================

def page_personal_ebook():

    render_brand_header()

    st.title("Personal eBook Studio")

    st.write(
        "Create your own digital book with chapters, "
        "research notes, personal stories and reflections."
    )

    if not require_login():
        return

    if Fernet is None:
        st.error("Encryption library is required.")
        return

    vault = db_fetch_one(
        """
        SELECT user_id FROM journal_vault
        WHERE user_id = ?
        """,
        (st.session_state.user_id,)
    )

    if not vault:
        st.warning(
            "Create your Private Journal vault first."
        )
        return

    if not private_session_active():

        st.info(
            "Unlock your Private Journal to access "
            "your encrypted eBook."
        )

        pin = st.text_input(
            "Enter your private PIN",
            type="password",
            key="ebook_unlock_pin"
        )

        if st.button("Unlock eBook Studio"):

            if unlock_private_vault(pin):
                st.rerun()

        return

    st.subheader("Create a new chapter")

    title = st.text_input(
        "Chapter title",
        placeholder="My First Chapter"
    )

    category = st.selectbox(
        "Category",
        [
            "Personal Writing",
            "Research Notes",
            "Neuroscience",
            "Thoughts and Reflections",
            "Stories",
            "Learning Journal"
        ]
    )

    content = st.text_area(
        "Chapter content",
        height=260,
        placeholder="Start writing your chapter..."
    )

    if st.button("Save Chapter"):

        success = save_ebook_chapter(
            title,
            category,
            content
        )

        if success:
            st.success(
                "Chapter saved in encrypted form."
            )
            st.rerun()

        else:
            st.error("Chapter could not be saved.")

    st.divider()

    st.subheader("My eBook Chapters")

    chapters = load_ebook_chapters()

    if not chapters:

        st.info("Your eBook is currently empty.")

    for chapter in chapters:

        with st.expander(
            chapter["title"]
        ):

            st.caption(chapter["category"])
            st.write(chapter["content"])

            if st.button(
                "Delete Chapter",
                key=f"ebook_delete_{chapter['id']}"
            ):

                if delete_ebook_chapter(chapter["id"]):
                    st.success("Chapter deleted.")
                    st.rerun()

    st.divider()

    if chapters:

        ebook_title = st.text_input(
            "Your book title",
            value="My NeuroLens eBook"
        )

        if st.button("Prepare PDF eBook"):

            pdf_data = create_ebook_pdf(
                ebook_title,
                chapters
            )

            if pdf_data:

                st.download_button(
                    "Download My eBook PDF",
                    data=pdf_data,
                    file_name="my_neurolens_ebook.pdf",
                    mime="application/pdf"
                )

            else:
                st.error(
                    "PDF export unavailable. Install reportlab."
                )

    st.caption(
        "Your eBook chapters are encrypted at rest. "
        "PDF exports are downloaded as readable documents."
    )
# ============================================================
# PART 8 — NEUROLENS CUTE STUDIO / PHOTO STUDIO
# ============================================================

def apply_photo_filter(image, filter_name):
    """Apply a real Pillow-based visual effect."""
    img = image.convert("RGB")

    if filter_name == "Lavender Sparkle":
        img = ImageEnhance.Color(img).enhance(0.88)
        img = ImageEnhance.Brightness(img).enhance(1.08)
        img = ImageEnhance.Contrast(img).enhance(0.92)
        overlay = Image.new("RGB", img.size, (205, 180, 255))
        img = Image.blend(img, overlay, 0.12)

    elif filter_name == "Cute Cat":
        img = ImageEnhance.Color(img).enhance(1.18)
        img = ImageEnhance.Brightness(img).enhance(1.06)
        img = ImageEnhance.Contrast(img).enhance(1.04)

    elif filter_name == "Butterfly Dream":
        img = ImageEnhance.Color(img).enhance(0.82)
        img = ImageEnhance.Brightness(img).enhance(1.12)
        overlay = Image.new("RGB", img.size, (255, 190, 220))
        img = Image.blend(img, overlay, 0.13)

    elif filter_name == "Clean Portrait":
        img = ImageEnhance.Color(img).enhance(0.96)
        img = ImageEnhance.Contrast(img).enhance(1.04)
        img = ImageEnhance.Sharpness(img).enhance(1.12)
        img = ImageEnhance.Brightness(img).enhance(1.03)

    elif filter_name == "Blue Cyber":
        img = ImageEnhance.Color(img).enhance(0.90)
        blue_layer = Image.new("RGB", img.size, (45, 105, 190))
        img = Image.blend(img, blue_layer, 0.22)
        img = ImageEnhance.Contrast(img).enhance(1.18)

    elif filter_name == "Cinematic Vintage":
        img = ImageEnhance.Color(img).enhance(0.72)
        warm_layer = Image.new("RGB", img.size, (190, 125, 75))
        img = Image.blend(img, warm_layer, 0.16)
        img = ImageEnhance.Contrast(img).enhance(1.12)

    return img


def add_photo_text(image, text_value):
    """Add user-provided text to the image."""
    if not text_value:
        return image

    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", max(18, img.width // 22))
    except Exception:
        font = ImageFont.load_default()

    margin = max(12, img.width // 35)
    x = margin
    y = img.height - margin - max(25, img.width // 18)

    try:
        draw.text(
            (x + 2, y + 2),
            text_value,
            font=font,
            fill=(0, 0, 0, 150),
            stroke_width=1
        )
        draw.text(
            (x, y),
            text_value,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=1
        )
    except Exception:
        pass

    return img.convert("RGB")


def page_photo_studio():
    st.title("✨ Cute Studio")
    st.caption("Create your own photo aesthetic with NeuroLens.")

    st.info(
        "Photo filters are visual editing effects. "
        "They do not identify personality, emotions, or mental health."
    )

    uploaded = st.file_uploader(
        "Upload a photo from your device",
        type=["jpg", "jpeg", "png", "webp"],
        key="studio_photo_upload"
    )

    if uploaded is None:
        st.markdown("### Choose a photo to begin")
        st.write(
            "Upload a portrait, selfie, or any image. "
            "Your original image is kept unchanged in this editing session."
        )
        return

    try:
        original = Image.open(uploaded).convert("RGB")
    except Exception:
        st.error("Image open nahi ho saki. Please another image try karein.")
        return

    st.markdown("### 1. Choose your style")

    filter_names = [
        "Lavender Sparkle",
        "Cute Cat",
        "Butterfly Dream",
        "Clean Portrait",
        "Blue Cyber",
        "Cinematic Vintage"
    ]

    selected_filter = st.selectbox(
        "Photo filter",
        filter_names,
        key="studio_selected_filter"
    )

    st.markdown("### 2. Adjust your photo")

    brightness = st.slider(
        "Brightness",
        min_value=50,
        max_value=150,
        value=100,
        key="studio_brightness"
    )

    contrast = st.slider(
        "Contrast",
        min_value=50,
        max_value=150,
        value=100,
        key="studio_contrast"
    )

    text_overlay = st.text_input(
        "Add your own caption (optional)",
        max_chars=60,
        key="studio_text_overlay"
    )

    edited = apply_photo_filter(original, selected_filter)

    edited = ImageEnhance.Brightness(edited).enhance(
        brightness / 100
    )

    edited = ImageEnhance.Contrast(edited).enhance(
        contrast / 100
    )

    edited = add_photo_text(edited, text_overlay)

    st.markdown("### 3. Before and after")

    left, right = st.columns(2)

    with left:
        st.image(
            original,
            caption="Original photo",
            use_container_width=True
        )

    with right:
        st.image(
            edited,
            caption=selected_filter,
            use_container_width=True
        )

    st.markdown("### 4. Save your edited photo")

    output = io.BytesIO()
    edited.save(output, format="PNG")
    output.seek(0)

    st.download_button(
        "⬇️ Download edited photo",
        data=output.getvalue(),
        file_name="neurolens_photo.png",
        mime="image/png",
        use_container_width=True
    )

    st.caption(
        "Note: Cute Cat and Butterfly Dream currently apply color effects; "
        "automatic cat-ear placement, butterfly stickers, face tracking "
        "and background cutout are Advanced Stage features."
    )
# ============================================================
# PART 9 — NEUROLENS PROGRESS DASHBOARD
# ============================================================

def page_progress_dashboard():
    st.title("📊 My Progress")
    st.caption("Your learning journey and activity overview")

    user = st.session_state.get("user")

    if not user:
        st.info("Apni progress dekhne ke liye pehle login karein.")
        if st.button("Go to Account"):
            st.session_state.page = "Account"
            st.rerun()
        return

    user_id = user.get("id")

    st.markdown("### 🧠 Your NeuroLens Journey")

    try:
        challenge_rows = db_fetch_all(
            """
            SELECT *
            FROM challenge_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
    except Exception:
        challenge_rows = []

    try:
        bookmark_rows = db_fetch_all(
            """
            SELECT *
            FROM research_bookmarks
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
    except Exception:
        bookmark_rows = []

    try:
        journal_rows = db_fetch_all(
            """
            SELECT *
            FROM journal_entries
            WHERE user_id = ?
            """,
            (user_id,)
        )
    except Exception:
        journal_rows = []

    total_challenges = len(challenge_rows)
    total_bookmarks = len(bookmark_rows)
    total_journal_entries = len(journal_rows)

    col1, col2, col3 = st.columns(3)

    col1.metric("Challenges", total_challenges)
    col2.metric("Research Saved", total_bookmarks)
    col3.metric("Journal Entries", total_journal_entries)

    st.divider()

    st.markdown("### 🎯 Cognitive Challenge History")

    if challenge_rows:
        progress_data = []

        for item in challenge_rows:
            progress_data.append({
                "Challenge": item.get("challenge_name", "Challenge"),
                "Score": item.get("score", 0),
                "Date": item.get("created_at", "")
            })

        progress_df = pd.DataFrame(progress_data)

        st.dataframe(
            progress_df,
            use_container_width=True,
            hide_index=True
        )

        if "Score" in progress_df.columns:
            numeric_scores = pd.to_numeric(
                progress_df["Score"],
                errors="coerce"
            ).dropna()

            if not numeric_scores.empty:
                st.markdown("#### Score overview")
                st.line_chart(numeric_scores.reset_index(drop=True))

                st.metric(
                    "Average recorded score",
                    round(float(numeric_scores.mean()), 2)
                )

    else:
        st.info(
            "Abhi koi saved challenge result nahi hai. "
            "Interactive Lab ya Cognitive Challenges try karein."
        )

    st.divider()

    st.markdown("### 📚 Research Activity")

    if bookmark_rows:
        for item in bookmark_rows[:10]:
            title = item.get("title", "Saved research")
            st.write("•", title)
    else:
        st.write("Aapne abhi tak koi research article bookmark nahi kiya.")

    st.divider()

    st.markdown("### 🌱 Personal Journey")

    st.metric(
        "Saved journal entries",
        total_journal_entries
    )

    st.caption(
        "Private Journal content yahan display nahi hota. "
        "Dashboard sirf entry count dikhata hai."
    )

    st.divider()

    st.markdown("### 💜 Self-Reflection")

    st.write(
        "Aap apni daily experience ko reflect kar sakte hain. "
        "Yeh self-reported information hai, brain measurement nahi."
    )

    with st.form("neurolens_self_reflection"):
        sleep_quality = st.slider(
            "How was your sleep quality?",
            1, 10, 5
        )

        attention = st.slider(
            "How focused did you feel?",
            1, 10, 5
        )

        mental_load = st.slider(
            "How mentally overloaded did you feel?",
            1, 10, 5
        )

        memory_confidence = st.slider(
            "How confident did you feel about your memory?",
            1, 10, 5
        )

        submitted = st.form_submit_button(
            "Save reflection",
            use_container_width=True
        )

        if submitted:
            st.session_state["latest_self_reflection"] = {
                "sleep_quality": sleep_quality,
                "attention": attention,
                "mental_load": mental_load,
                "memory_confidence": memory_confidence,
                "saved_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
            }

            st.success("Your reflection is saved for this session.")

    reflection = st.session_state.get("latest_self_reflection")

    if reflection:
        st.markdown("#### Your latest self-reflection")

        reflection_df = pd.DataFrame({
            "Metric": [
                "Sleep quality",
                "Attention",
                "Mental load",
                "Memory confidence"
            ],
            "Self-reported rating": [
                reflection["sleep_quality"],
                reflection["attention"],
                reflection["mental_load"],
                reflection["memory_confidence"]
            ]
        })

        st.bar_chart(
            reflection_df.set_index("Metric")
        )

        st.caption(
            "Session-only data: this reflection is not yet stored "
            "permanently in your account."
        )

    st.divider()

    st.markdown("### 🚀 Keep Exploring")

    if st.button("Open Interactive Lab", use_container_width=True):
        st.session_state.page = "Interactive Lab"
        st.rerun()

    if st.button("Explore the Brain", use_container_width=True):
        st.session_state.page = "Explore Brain"
        st.rerun()
# ============================================================
# PART 7 PAGE REGISTRATION
# ============================================================

# page_research_library()
# page_personal_ebook()
# are ready for the final application router.
