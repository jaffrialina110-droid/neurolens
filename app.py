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
