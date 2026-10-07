# ============================================================
# NEUROLENS
# Explore cognition, behavior & the brain
#
# FRESH REBUILD — PART 1
# ============================================================

import os
import re
import json
import time
import base64
import random
import hashlib
import hmac
from pathlib import Path
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# PAGE CONFIG
# IMPORTANT: This must be the first Streamlit command.
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# OPTIONAL LIBRARIES
# ============================================================

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import numpy as np
except Exception:
    np = None

try:
    import plotly.express as px
except Exception:
    px = None

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    from supabase import create_client
except Exception:
    create_client = None

try:
    from google import genai
except Exception:
    genai = None


# ============================================================
# APP IDENTITY
# ============================================================

APP_NAME = "NEUROLENS"
APP_TAGLINE = "Explore cognition, behavior & the brain"
CREATOR_NAME = "Ayna Jaffri"
PROFESSIONAL_ROLE = "Independent cognitive neuroscience researcher"


# ============================================================
# SAFE SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value is None:
            return default
        return str(value)
    except Exception:
        return default


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

EASYPAISA_NUMBER = get_secret(
    "EASYPAISA_NUMBER"
)

INTERNATIONAL_PAYMENT_URL = get_secret(
    "INTERNATIONAL_PAYMENT_URL"
)

PAYMENT_ADMIN_KEY = get_secret(
    "PAYMENT_ADMIN_KEY"
)


# ============================================================
# SUPABASE
# ============================================================

supabase = None

if (
    create_client is not None
    and SUPABASE_URL
    and SUPABASE_KEY
):

    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception:
        supabase = None


# ============================================================
# GEMINI
# ============================================================

gemini_client = None

if genai is not None and GEMINI_API_KEY:

    try:
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception:
        gemini_client = None


# ============================================================
# SESSION DEFAULTS
# ============================================================

DEFAULTS = {
    "page": "NeuroWorld",
    "authenticated": False,
    "user": None,

    # NeuroWorld
    "world_stage": "welcome",

    # Identity
    "display_name": "Ayna Jaffri",
    "profile_bio": PROFESSIONAL_ROLE,

    # AI
    "ai_requests": 0,
    "ai_request_times": [],
    "ai_request_history": [],
    "ayna_messages": [],

    # Voice / face
    "voice_result": None,
    "face_result": None,

    # Lab
    "lab_results": [],
    "lab_history": [],
    "lab_experiment": "Attention",
    "lab_character": "Researcher",
    "lab_started": False,
    "lab_completed": False,
    "lab_result": None,

    # Brain Journey
    "brain_journey_index": 0,

    # Puzzle
    "puzzle_grid": 3,
    "puzzle_board": [],
    "puzzle_solution": [],
    "puzzle_started": False,
    "puzzle_completed": False,
    "puzzle_moves": 0,
    "puzzle_start_time": None,
    "puzzle_elapsed": 0,

    # Challenges
    "exercise_scores": [],
    "wm_sequence": "",
    "wm_show": False,
    "wm_score": None,
    "attention_target": "",
    "attention_options": [],
    "attention_correct": None,
    "pattern_question": None,
    "stroop_item": None,
    "reaction_started": False,
    "reaction_start_time": None,

    # Research
    "research_results": [],
    "research_notes": [],

    # Private Ayna
    "private_pin_hash": None,
    "private_pin_salt": None,
    "private_unlocked": False,
    "private_messages": [],

    # Social
    "social_posts": [],
    "social_notifications": [],

    # Consultation
    "consultation_requests": [],

    # Settings
    "interface_language": "English",

    # Errors
    "last_error": "",
}


for key, value in DEFAULTS.items():

    if key not in st.session_state:

        if isinstance(value, list):
            st.session_state[key] = []

        elif isinstance(value, dict):
            st.session_state[key] = {}

        else:
            st.session_state[key] = value


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value, max_length=2000):

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\x00", "")

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value[:max_length]


def current_user_id():

    user = st.session_state.get(
        "user"
    )

    if not user:
        return None

    return user.get("id")


def current_user_email():

    user = st.session_state.get(
        "user"
    )

    if not user:
        return ""

    return user.get(
        "email",
        "",
    )


def safe_json(value):

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
        )
    except Exception:
        return "{}"


# ============================================================
# DATABASE HELPERS
# ============================================================

def db_insert(table, payload):

    if supabase is None:
        return None

    try:

        response = (
            supabase
            .table(table)
            .insert(payload)
            .execute()
        )

        return response

    except Exception as exc:

        st.session_state.last_error = str(
            exc
        )

        return None


def db_select(
    table,
    filters=None,
    limit=50,
):

    if supabase is None:
        return []

    try:

        query = supabase.table(
            table
        ).select("*")

        filters = filters or {}

        for column, value in filters.items():

            query = query.eq(
                column,
                value,
            )

        response = (
            query
            .limit(limit)
            .execute()
        )

        return response.data or []

    except Exception as exc:

        st.session_state.last_error = str(
            exc
        )

        return []


# ============================================================
# ASSET SYSTEM
# ============================================================

APP_DIR = Path(__file__).resolve().parent

ASSETS_DIR = APP_DIR / "assets"


def find_asset(filename):

    possible_paths = [
        APP_DIR / filename,
        ASSETS_DIR / filename,
    ]

    for path in possible_paths:

        if path.exists():
            return path

    return None


def image_exists(filename):

    return find_asset(filename) is not None


def show_asset(
    filename,
    width=None,
    caption=None,
):

    path = find_asset(filename)

    if path is None:

        return False

    try:

        st.image(
            str(path),
            width=width,
            caption=caption,
        )

        return True

    except Exception:

        return False


def asset_data_uri(filename):

    path = find_asset(filename)

    if path is None:
        return None

    try:

        suffix = path.suffix.lower()

        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(
            suffix,
            "application/octet-stream",
        )

        encoded = base64.b64encode(
            path.read_bytes()
        ).decode("utf-8")

        return f"data:{mime};base64,{encoded}"

    except Exception:

        return None


# ============================================================
# AI HELPERS
# ============================================================

def ai_available():

    return (
        gemini_client is not None
        and bool(GEMINI_API_KEY)
    )


def ai_limit_reached():

    now = time.time()

    recent = [
        timestamp
        for timestamp in st.session_state.ai_request_times
        if now - timestamp < 60
    ]

    st.session_state.ai_request_times = recent

    return len(recent) >= 10


def register_ai_request():

    now = time.time()

    st.session_state.ai_request_times.append(
        now
    )

    st.session_state.ai_requests += 1

    st.session_state.ai_request_history.append(
        {
            "time": now,
        }
    )


def ai_generate(
    prompt,
    max_output_tokens=1200,
):

    if not ai_available():

        return (
            "Gemini AI is not connected. "
            "Please add GEMINI_API_KEY to Streamlit Secrets."
        )

    if ai_limit_reached():

        return (
            "AI request limit reached temporarily. "
            "Please wait a moment and try again."
        )

    try:

        register_ai_request()

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "max_output_tokens": max_output_tokens,
            },
        )

        text = getattr(
            response,
            "text",
            "",
        )

        return (
            text.strip()
            if text
            else "No AI response was returned."
        )

    except Exception as exc:

        st.session_state.last_error = str(
            exc
        )

        return (
            "I could not generate a reliable AI response right now."
        )


# ============================================================
# BROWSER TEXT-TO-SPEECH
# ============================================================

def speak_text(text):

    text = clean_text(
        text,
        5000,
    )

    if not text:
        return

    safe_text = json.dumps(
        text,
        ensure_ascii=False,
    )

    html = f"""
    <script>
    const text = {safe_text};

    if ("speechSynthesis" in window) {{
        window.speechSynthesis.cancel();

        const utterance =
            new SpeechSynthesisUtterance(text);

        utterance.rate = 0.95;
        utterance.pitch = 1.0;

        window.speechSynthesis.speak(
            utterance
        );
    }}
    </script>
    """

    components.html(
        html,
        height=0,
    )


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 20% 10%,
                rgba(79, 70, 229, .10),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #050816,
                #081126
            );
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .nl-card {
        padding: 22px;
        border-radius: 22px;
        border: 1px solid rgba(148,163,184,.18);
        background: rgba(15,23,42,.72);
        margin: 10px 0;
    }

    .nl-hero {
        padding: 32px;
        border-radius: 30px;
        border: 1px solid rgba(129,140,248,.25);
        background:
            radial-gradient(
                circle at 20% 20%,
                rgba(99,102,241,.28),
                transparent 35%
            ),
            linear-gradient(
                135deg,
                #111a46,
                #07101f
            );
        text-align: center;
        margin-bottom: 20px;
    }

    .nl-hero-title {
        font-size: clamp(28px, 5vw, 52px);
        font-weight: 900;
        margin: 8px 0;
    }

    .nl-hero-subtitle {
        color: #c7d2fe;
        font-size: 16px;
        line-height: 1.7;
    }

    .brain-character {
        font-size: 88px;
        line-height: 1;
        margin: 8px;
    }

    .robot-character {
        font-size: 64px;
        line-height: 1;
    }

    .feature-grid {
        display: grid;
        grid-template-columns:
            repeat(
                auto-fit,
                minmax(220px, 1fr)
            );
        gap: 16px;
        margin-top: 18px;
    }

    .feature-card {
        padding: 20px;
        border-radius: 22px;
        background: rgba(255,255,255,.045);
        border: 1px solid rgba(255,255,255,.09);
        min-height: 150px;
    }

    .feature-icon {
        font-size: 42px;
        margin-bottom: 8px;
    }

    .feature-title {
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .feature-text {
        color: #aebbd4;
        font-size: 14px;
        line-height: 1.55;
    }

    .small-muted {
        color: #94a3b8;
        font-size: 13px;
    }

    @media (max-width: 700px) {

        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .nl-hero {
            padding: 22px 16px;
        }

        .brain-character {
            font-size: 70px;
        }

        .robot-character {
            font-size: 52px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AUTH
# ============================================================

def logout():

    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.page = "NeuroWorld"

    st.rerun()


def page_auth():

    st.title("👤 NEUROLENS Account")

    st.caption(
        "Create an account or continue exploring as a guest."
    )

    if supabase is None:

        st.info(
            "Supabase is not connected. Guest mode is available."
        )

        if st.button(
            "Continue as Guest",
            type="primary",
            use_container_width=True,
            key="guest_mode",
        ):

            st.session_state.authenticated = False
            st.session_state.page = "NeuroWorld"
            st.rerun()

        return

    tab_login, tab_signup = st.tabs(
        [
            "Login",
            "Create Account",
        ]
    )

    with tab_login:

        email = st.text_input(
            "Email",
            key="login_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
            key="login_button",
        ):

            if not email or not password:

                st.error(
                    "Enter your email and password."
                )

            else:

                try:

                    response = (
                        supabase.auth.sign_in_with_password(
                            {
                                "email": email.strip(),
                                "password": password,
                            }
                        )
                    )

                    if response.user:

                        st.session_state.user = {
                            "id": response.user.id,
                            "email": response.user.email,
                        }

                        st.session_state.authenticated = True
                        st.session_state.page = "NeuroWorld"

                        st.success(
                            "Login successful."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Login could not be completed."
                        )

                except Exception:

                    st.error(
                        "Login failed. Check your email and password."
                    )

    with tab_signup:

        signup_email = st.text_input(
            "Email",
            key="signup_email",
        )

        signup_password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
        )

        if st.button(
            "Create Account",
            type="primary",
            use_container_width=True,
            key="signup_button",
        ):

            if not signup_email or not signup_password:

                st.error(
                    "Enter an email and password."
                )

            elif len(signup_password) < 6:

                st.error(
                    "Password should contain at least 6 characters."
                )

            else:

                try:

                    response = (
                        supabase.auth.sign_up(
                            {
                                "email": signup_email.strip(),
                                "password": signup_password,
                            }
                        )
                    )

                    if response.user:

                        if response.session:

                            st.session_state.user = {
                                "id": response.user.id,
                                "email": response.user.email,
                            }

                            st.session_state.authenticated = True
                            st.session_state.page = "NeuroWorld"

                            st.success(
                                "Account created."
                            )

                            st.rerun()

                        else:

                            st.success(
                                "Account created. "
                                "Please check your email if confirmation is required."
                            )

                    else:

                        st.error(
                            "Account could not be created."
                        )

                except Exception:

                    st.error(
                        "Account creation failed."
                    )


# ============================================================
# NEUROWORLD
# ============================================================

def page_neuroworld():

    stage = st.session_state.get(
        "world_stage",
        "welcome",
    )

    # --------------------------------------------------------
    # WELCOME
    # --------------------------------------------------------

    if stage == "welcome":

        st.markdown(
            """
            <div class="nl-hero">

                <div class="brain-character">
                    🧠
                </div>

                <div class="nl-hero-title">
                    NEUROLENS
                </div>

                <div class="nl-hero-subtitle">
                    Explore cognition, behavior & the brain
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="nl-card" style="text-align:center;">

                <div style="font-size:52px;">
                    🧠
                </div>

                <h2>
                    Welcome to your NeuroWorld
                </h2>

                <p>
                    A space where neuroscience, cognition,
                    AI and interactive learning come together.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "✨ Meet NeuroLens",
            type="primary",
            use_container_width=True,
            key="meet_neurolens",
        ):

            st.session_state.world_stage = "intro"

            st.rerun()

        return

    # --------------------------------------------------------
    # INTRO
    # --------------------------------------------------------

    if stage == "intro":

        st.markdown(
            """
            <div class="nl-hero">

                <div class="brain-character">
                    🧠
                </div>

                <div class="nl-hero-title">
                    Hi, I am NeuroLens.
                </div>

                <div class="nl-hero-subtitle">
                    Come with me — I'll show you
                    what you can explore.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        robot_asset = find_asset(
            "ayna_robot.png"
        )

        if robot_asset:

            col1, col2 = st.columns(
                [1, 2]
            )

            with col1:

                st.image(
                    str(robot_asset),
                    use_container_width=True,
                )

            with col2:

                st.markdown(
                    """
                    <div class="nl-card">

                        <div style="font-size:48px;">
                            🤖
                        </div>

                        <h2>
                            Meet Ayna
                        </h2>

                        <p>
                            Your female AI research companion
                            inside NeuroLens.
                        </p>

                        <p>
                            Together we can explore the brain,
                            run cognitive experiments,
                            solve challenges, explore research
                            and ask neuroscience questions.
                        </p>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="nl-card" style="text-align:center;">

                    <div class="robot-character">
                        🤖
                    </div>

                    <h2>
                        Meet Ayna
                    </h2>

                    <p>
                        Your female AI research companion
                        inside NeuroLens.
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "### 🌌 What can we explore?"
        )

        st.markdown(
            """
            <div class="feature-grid">

                <div class="feature-card">
                    <div class="feature-icon">🧪</div>
                    <div class="feature-title">
                        Cognitive Lab
                    </div>
                    <div class="feature-text">
                        Interactive attention, memory,
                        decision and cognitive-control experiments.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">
                        Brain Journey
                    </div>
                    <div class="feature-text">
                        Explore neurons, synapses and
                        major cognitive brain systems.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">🧩</div>
                    <div class="feature-title">
                        Brain Challenges
                    </div>
                    <div class="feature-text">
                        Test memory, attention, pattern
                        recognition and reaction.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">🔬</div>
                    <div class="feature-title">
                        Research World
                    </div>
                    <div class="feature-text">
                        Search biomedical literature
                        and build research notes.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">
                        Ask Ayna
                    </div>
                    <div class="feature-text">
                        Discuss cognition, neuroscience,
                        behaviour and AI.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">🌐</div>
                    <div class="feature-title">
                        NeuroSocial
                    </div>
                    <div class="feature-text">
                        Share ideas, research interests
                        and cognitive challenges.
                    </div>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 🚀 Ready?")

        if st.button(
            "🚀 Enter NEUROLENS",
            type="primary",
            use_container_width=True,
            key="enter_neurolens",
        ):

            st.session_state.world_stage = "world"

            st.session_state.page = "Cognitive Lab"

            st.rerun()

        return

    # --------------------------------------------------------
    # WORLD HOME
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="nl-hero">

            <div class="brain-character">
                🧠
            </div>

            <div class="nl-hero-title">
                NeuroWorld
            </div>

            <div class="nl-hero-subtitle">
                Your interactive neuroscience environment
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🧪 Enter Cognitive Lab",
        type="primary",
        use_container_width=True,
        key="world_enter_lab",
    ):

        st.session_state.page = "Cognitive Lab"

        st.rerun()

    st.markdown(
        """
        <div class="feature-grid">

            <div class="feature-card">
                <div class="feature-icon">🧪</div>
                <div class="feature-title">
                    Cognitive Lab
                </div>
                <div class="feature-text">
                    Run interactive cognitive experiments.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <div class="feature-title">
                    Brain Journey
                </div>
                <div class="feature-text">
                    Travel through major brain systems.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🧩</div>
                <div class="feature-title">
                    Brain Puzzle
                </div>
                <div class="feature-text">
                    Reconstruct the brain image through
                    interactive puzzle challenges.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <div class="feature-title">
                    Brain Challenges
                </div>
                <div class="feature-text">
                    Work on memory, attention and
                    decision-making tasks.
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PART 1 END
# ============================================================
# ============================================================
# NEUROLENS — PART 2
# COGNITIVE LAB + BRAIN JOURNEY + BRAIN PUZZLE
# ============================================================


# ============================================================
# COGNITIVE LAB
# ============================================================

LAB_EXPERIMENTS = {
    "Attention": {
        "icon": "👁️",
        "description": (
            "Test selective attention by finding a target "
            "among competing visual information."
        ),
    },
    "Memory": {
        "icon": "🧠",
        "description": (
            "Test short-term working-memory performance "
            "with a temporary sequence."
        ),
    },
    "Decision & Reward": {
        "icon": "💰",
        "description": (
            "Explore a simplified reward-delay decision."
        ),
    },
    "Stroop Cognitive Control": {
        "icon": "🎨",
        "description": (
            "Test response control when word meaning "
            "and colour information conflict."
        ),
    },
    "Pattern Recognition": {
        "icon": "🔢",
        "description": (
            "Identify a numerical pattern and predict "
            "the next element."
        ),
    },
}


def lab_save_result(
    experiment,
    score,
    observations,
    extra=None,
):

    result = {
        "experiment": experiment,
        "score": float(score),
        "observations": observations,
        "extra": extra or {},
        "timestamp": time.time(),
    }

    st.session_state.lab_results.append(
        result
    )

    st.session_state.lab_history.append(
        result
    )

    user_id = current_user_id()

    if user_id:

        db_insert(
            "lab_results",
            {
                "user_id": user_id,
                "experiment": experiment,
                "score": float(score),
                "result_data": result,
            },
        )


def run_attention_lab():

    st.markdown(
        """
        <div class="nl-card">
            <h3>👁️ Attention Experiment</h3>
            <p>
                Find the target letter as quickly as possible.
                This is a behavioural simulation and does not
                measure actual neural activity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "lab_attention_target" not in st.session_state:

        st.session_state.lab_attention_target = None
        st.session_state.lab_attention_options = []
        st.session_state.lab_attention_correct = None
        st.session_state.lab_attention_start = None

    if st.session_state.lab_attention_target is None:

        if st.button(
            "▶ Start Attention Experiment",
            type="primary",
            use_container_width=True,
            key="lab_attention_start",
        ):

            target = random.choice(
                ["X", "K", "M", "R", "A"]
            )

            options = [
                random.choice(
                    ["X", "K", "M", "R", "A"]
                )
                for _ in range(20)
            ]

            correct = random.randint(
                0,
                len(options) - 1,
            )

            options[correct] = target

            st.session_state.lab_attention_target = target
            st.session_state.lab_attention_options = options
            st.session_state.lab_attention_correct = correct
            st.session_state.lab_attention_start = time.time()

            st.rerun()

        return

    target = st.session_state.lab_attention_target

    st.markdown(
        f"""
        <div class="nl-card" style="text-align:center;">
            <div class="small-muted">
                Find this target:
            </div>
            <div style="
                font-size:48px;
                font-weight:900;
                margin-top:8px;
            ">
                {target}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)

    for index, value in enumerate(
        st.session_state.lab_attention_options
    ):

        with cols[index % 5]:

            if st.button(
                value,
                key=f"lab_attention_item_{index}",
                use_container_width=True,
            ):

                elapsed = (
                    time.time()
                    - st.session_state.lab_attention_start
                )

                correct = (
                    index
                    == st.session_state.lab_attention_correct
                )

                if correct:

                    score = max(
                        0,
                        min(
                            100,
                            int(
                                100
                                - elapsed * 12
                            ),
                        ),
                    )

                    observations = (
                        "The target was identified correctly. "
                        "Performance reflects task accuracy and "
                        "interaction speed in this simulation."
                    )

                    st.success(
                        "🎯 Target identified correctly."
                    )

                else:

                    score = 0

                    observations = (
                        "The selected item was not the target. "
                        "This task is only an educational attention "
                        "exercise."
                    )

                    st.error(
                        "Not the target."
                    )

                lab_save_result(
                    "Attention",
                    score,
                    observations,
                    {
                        "reaction_time_seconds": elapsed,
                        "correct": correct,
                    },
                )

                st.session_state.lab_result = {
                    "score": score,
                    "observations": observations,
                }

                st.session_state.lab_completed = True

                st.session_state.lab_attention_target = None

                st.rerun()


def run_memory_lab():

    st.markdown(
        """
        <div class="nl-card">
            <h3>🧠 Memory Experiment</h3>
            <p>
                Memorize the displayed sequence and reproduce it.
                This is a simple working-memory simulation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    difficulty = st.selectbox(
        "Difficulty",
        [
            "Easy",
            "Medium",
            "Hard",
        ],
        key="lab_memory_difficulty",
    )

    lengths = {
        "Easy": 4,
        "Medium": 6,
        "Hard": 8,
    }

    length = lengths[difficulty]

    if "lab_memory_sequence" not in st.session_state:

        st.session_state.lab_memory_sequence = None
        st.session_state.lab_memory_show = False

    if st.session_state.lab_memory_sequence is None:

        if st.button(
            "▶ Start Memory Experiment",
            type="primary",
            use_container_width=True,
            key="lab_memory_start",
        ):

            sequence = "".join(
                str(
                    random.randint(
                        0,
                        9,
                    )
                )
                for _ in range(length)
            )

            st.session_state.lab_memory_sequence = sequence
            st.session_state.lab_memory_show = True

            st.rerun()

        return

    sequence = st.session_state.lab_memory_sequence

    if st.session_state.lab_memory_show:

        st.markdown(
            f"""
            <div class="nl-card" style="
                text-align:center;
                padding:30px;
            ">

                <div class="small-muted">
                    Memorize this sequence
                </div>

                <div style="
                    font-size:40px;
                    font-weight:900;
                    letter-spacing:8px;
                    margin-top:15px;
                ">
                    {sequence}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "I Memorized It",
            type="primary",
            use_container_width=True,
            key="memory_hide",
        ):

            st.session_state.lab_memory_show = False
            st.rerun()

        return

    answer = st.text_input(
        "Enter the sequence",
        max_chars=20,
        key="lab_memory_answer",
    )

    if st.button(
        "Check Memory",
        type="primary",
        use_container_width=True,
        key="memory_check",
    ):

        correct = (
            answer.strip()
            == sequence
        )

        score = 100 if correct else 0

        if correct:

            observations = (
                "The sequence was reproduced correctly "
                "in this working-memory task."
            )

            st.success(
                "✅ Correct."
            )

        else:

            observations = (
                "The sequence was not reproduced correctly. "
                "This does not by itself indicate a cognitive problem."
            )

            st.error(
                "❌ Incorrect."
            )

        lab_save_result(
            "Memory",
            score,
            observations,
            {
                "difficulty": difficulty,
                "correct": correct,
            },
        )

        st.session_state.lab_result = {
            "score": score,
            "observations": observations,
        }

        st.session_state.lab_completed = True

        st.session_state.lab_memory_sequence = None
        st.session_state.lab_memory_show = False

        st.rerun()


def run_decision_lab():

    st.markdown(
        """
        <div class="nl-card">
            <h3>💰 Decision & Reward Experiment</h3>

            <p>
                Imagine you can choose between:
            </p>

            <ul>
                <li><b>PKR 1,000 today</b></li>
                <li><b>PKR 1,500 after 30 days</b></li>
            </ul>

            <p>
                Your choice is recorded as a decision preference
                within this educational simulation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Which would you choose?",
        [
            "PKR 1,000 today",
            "PKR 1,500 after 30 days",
        ],
        key="lab_decision_choice",
    )

    if st.button(
        "Submit Decision",
        type="primary",
        use_container_width=True,
        key="lab_decision_submit",
    ):

        if "30 days" in choice:

            observation = (
                "You selected the delayed larger reward. "
                "This choice prioritizes a larger future payoff "
                "over immediate availability."
            )

        else:

            observation = (
                "You selected the immediate reward. "
                "This choice prioritizes immediate availability."
            )

        st.success(
            "Decision recorded."
        )

        st.info(
            observation
        )

        lab_save_result(
            "Decision & Reward",
            100,
            observation,
            {
                "choice": choice,
            },
        )

        st.session_state.lab_result = {
            "score": 100,
            "observations": observation,
        }

        st.session_state.lab_completed = True


def run_stroop_lab():

    st.markdown(
        """
        <div class="nl-card">
            <h3>🎨 Stroop Cognitive Control</h3>

            <p>
                Identify the ink colour rather than the written word.
                This demonstrates response conflict in a simplified
                educational task.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if (
        st.session_state.stroop_item
        is None
    ):

        st.session_state.stroop_item = random.choice(
            [
                ("RED", "blue"),
                ("BLUE", "red"),
                ("GREEN", "yellow"),
                ("YELLOW", "green"),
            ]
        )

    word, colour = (
        st.session_state.stroop_item
    )

    st.markdown(
        f"""
        <div class="nl-card" style="
            text-align:center;
        ">

            <div class="small-muted">
                Select the ink colour
            </div>

            <div style="
                font-size:46px;
                font-weight:900;
                color:{colour};
                margin-top:12px;
            ">
                {word}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.radio(
        "Ink colour",
        [
            "red",
            "blue",
            "green",
            "yellow",
        ],
        horizontal=True,
        key="lab_stroop_answer",
    )

    if st.button(
        "Check Response",
        type="primary",
        use_container_width=True,
        key="lab_stroop_check",
    ):

        correct = (
            answer == colour
        )

        score = 100 if correct else 0

        if correct:

            observation = (
                "Correct response in the simplified Stroop task."
            )

            st.success(
                "✅ Correct."
            )

        else:

            observation = (
                "The response conflicted with the ink colour."
            )

            st.error(
                "❌ Incorrect."
            )

        lab_save_result(
            "Stroop Cognitive Control",
            score,
            observation,
            {
                "word": word,
                "ink_colour": colour,
                "answer": answer,
            },
        )

        st.session_state.lab_result = {
            "score": score,
            "observations": observation,
        }

        st.session_state.lab_completed = True

        st.session_state.stroop_item = None

        st.rerun()


def run_pattern_lab():

    st.markdown(
        """
        <div class="nl-card">
            <h3>🔢 Pattern Recognition</h3>
            <p>
                Identify the rule and predict the missing number.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    patterns = [
        (
            ["2", "4", "8", "16", "?"],
            "32",
        ),
        (
            ["3", "6", "12", "24", "?"],
            "48",
        ),
        (
            ["5", "10", "20", "40", "?"],
            "80",
        ),
        (
            ["1", "4", "9", "16", "?"],
            "25",
        ),
    ]

    if st.session_state.pattern_question is None:

        st.session_state.pattern_question = random.choice(
            patterns
        )

    sequence, answer = (
        st.session_state.pattern_question
    )

    st.markdown(
        f"""
        <div class="nl-card" style="
            text-align:center;
        ">

            <div style="
                font-size:30px;
                font-weight:900;
            ">
                {" → ".join(sequence)}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    response = st.text_input(
        "Your answer",
        max_chars=20,
        key="lab_pattern_answer",
    )

    if st.button(
        "Check Pattern",
        type="primary",
        use_container_width=True,
        key="lab_pattern_check",
    ):

        correct = (
            response.strip()
            == answer
        )

        score = 100 if correct else 0

        if correct:

            observation = (
                "The numerical pattern was identified correctly."
            )

            st.success(
                "🎯 Correct."
            )

        else:

            observation = (
                "The predicted value did not match the "
                "pattern used in this task."
            )

            st.error(
                f"Incorrect. Expected {answer}."
            )

        lab_save_result(
            "Pattern Recognition",
            score,
            observation,
            {
                "sequence": sequence,
                "answer": response,
            },
        )

        st.session_state.lab_result = {
            "score": score,
            "observations": observation,
        }

        st.session_state.lab_completed = True

        st.session_state.pattern_question = None

        st.rerun()


def page_lab():

    st.title("🧪 Cognitive Neuroscience Lab")

    st.caption(
        "Interactive behavioural simulations for exploring cognition."
    )

    st.warning(
        "Lab tasks are educational simulations. "
        "They do not record real EEG/fMRI signals and "
        "do not provide clinical measurements."
    )

    st.subheader("👤 Choose your role")

    character = st.selectbox(
        "Research role",
        [
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent",
        ],
        key="lab_character_selector",
    )

    st.session_state.lab_character = character

    st.subheader("🧰 Virtual Equipment")

    equipment = st.multiselect(
        "Select equipment",
        [
            "EEG Simulator",
            "Eye Tracker",
            "Reaction-Time System",
            "Cognitive Task Monitor",
            "Physiological Sensor",
        ],
        default=[
            "Cognitive Task Monitor",
        ],
        key="lab_equipment",
    )

    if equipment:

        st.caption(
            "Selected: "
            + ", ".join(equipment)
        )

    st.divider()

    st.subheader("🧠 Select Experiment")

    experiment = st.selectbox(
        "Experiment",
        list(LAB_EXPERIMENTS.keys()),
        key="lab_experiment_selector",
    )

    info = LAB_EXPERIMENTS[
        experiment
    ]

    st.markdown(
        f"""
        <div class="nl-card">

            <div style="font-size:45px;">
                {info["icon"]}
            </div>

            <h3>
                {experiment}
            </h3>

            <p>
                {info["description"]}
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if experiment == "Attention":

        run_attention_lab()

    elif experiment == "Memory":

        run_memory_lab()

    elif experiment == "Decision & Reward":

        run_decision_lab()

    elif experiment == "Stroop Cognitive Control":

        run_stroop_lab()

    elif experiment == "Pattern Recognition":

        run_pattern_lab()

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    if st.session_state.lab_result:

        result = st.session_state.lab_result

        st.divider()

        st.subheader("📊 Experiment Result")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Performance",
                f"{result.get('score', 0)}/100",
            )

        with col2:

            st.metric(
                "Role",
                st.session_state.lab_character,
            )

        st.info(
            result.get(
                "observations",
                "",
            )
        )

        st.caption(
            "Interpretation is limited to performance in this "
            "specific simulation and should not be treated as "
            "a diagnosis or measurement of brain activity."
        )


# ============================================================
# BRAIN JOURNEY
# ============================================================

BRAIN_SYSTEMS = [
    {
        "name": "Neuron",
        "icon": "⚡",
        "asset": "neuron.png",
        "description": (
            "Neurons are specialized cells that communicate "
            "information through electrical and chemical signalling."
        ),
    },
    {
        "name": "Synapse",
        "icon": "🔗",
        "asset": "synapse.png",
        "description": (
            "A synapse is a communication junction where "
            "signals can pass from one neuron to another."
        ),
    },
    {
        "name": "Neural Signaling",
        "icon": "⚡",
        "asset": "neural_signaling.gif",
        "description": (
            "Neural signalling involves coordinated electrical "
            "and chemical processes that allow neural systems "
            "to transmit information."
        ),
    },
    {
        "name": "Prefrontal Cortex",
        "icon": "🧠",
        "asset": "prefrontal_cortex.png",
        "description": (
            "The prefrontal cortex contributes to planning, "
            "working memory, cognitive control and decision-making."
        ),
    },
    {
        "name": "Hippocampus",
        "icon": "🧠",
        "asset": "hippocampus.png",
        "description": (
            "The hippocampus is strongly involved in memory "
            "formation and spatial/contextual processing."
        ),
    },
    {
        "name": "Striatum",
        "icon": "🧠",
        "asset": "striatum.png",
        "description": (
            "The striatum is part of the basal-ganglia circuitry "
            "involved in action selection, reward and learning."
        ),
    },
    {
        "name": "Anterior Cingulate Cortex",
        "icon": "🧠",
        "asset": "acc.png",
        "description": (
            "The anterior cingulate cortex participates in "
            "monitoring, cognitive control, motivation and "
            "processing of competing information."
        ),
    },
    {
        "name": "Attention Networks",
        "icon": "👁️",
        "asset": "attention_network.png",
        "description": (
            "Attention networks coordinate selection and "
            "prioritization of information relevant to behaviour."
        ),
    },
]


def ask_ayna_about_system(system):

    question = (
        "Explain this neuroscience concept in simple terms: "
        + system["name"]
        + ". "
        + system["description"]
    )

    answer = ai_generate(
        f"""
You are Ayna, an educational cognitive-neuroscience AI guide.

Explain the following concept clearly for a general learner.

Concept:
{question}

Rules:
- Be scientifically cautious.
- Do not diagnose.
- Do not invent facts.
- Keep it concise.
"""
    )

    st.session_state["brain_system_answer"] = answer


def page_brain_journey():

    st.title("🧠 Visual Brain Journey")

    st.caption(
        "Explore neural systems one concept at a time."
    )

    index = st.session_state.brain_journey_index

    system = BRAIN_SYSTEMS[
        index
    ]

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    st.progress(
        (index + 1)
        / len(BRAIN_SYSTEMS)
    )

    st.caption(
        f"Concept {index + 1} of {len(BRAIN_SYSTEMS)}"
    )

    # --------------------------------------------------------
    # CONCEPT VISUAL
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="nl-card" style="
            text-align:center;
        ">

            <div style="
                font-size:48px;
            ">
                {system["icon"]}
            </div>

            <h2>
                {system["name"]}
            </h2>

        </div>
        """,
        unsafe_allow_html=True,
    )

    asset = find_asset(
        system["asset"]
    )

    if asset:

        st.image(
            str(asset),
            use_container_width=True,
        )

    else:

        st.markdown(
            f"""
            <div class="nl-card" style="
                text-align:center;
                padding:55px 20px;
            ">

                <div style="font-size:70px;">
                    {system["icon"]}
                </div>

                <p class="small-muted">
                    Add {system["asset"]}
                    to your assets folder for the
                    dedicated visual.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="nl-card">

            <h3>
                🔬 What are we exploring?
            </h3>

            <p>
                {system["description"]}
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # AI EXPLANATION
    # --------------------------------------------------------

    if st.button(
        "🤖 Ask Ayna About This System",
        use_container_width=True,
        key=f"ask_system_{index}",
    ):

        with st.spinner(
            "Ayna is preparing an explanation..."
        ):

            ask_ayna_about_system(
                system
            )

        st.rerun()

    if st.session_state.get(
        "brain_system_answer"
    ):

        st.markdown(
            """
            <div class="nl-card">
                <h3>🤖 Ayna's Explanation</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(
            st.session_state.brain_system_answer
        )

        if st.button(
            "🔊 Speak Explanation",
            key=f"speak_system_{index}",
        ):

            speak_text(
                st.session_state.brain_system_answer
            )

    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    st.divider()

    previous_col, restart_col, next_col = (
        st.columns(3)
    )

    with previous_col:

        if st.button(
            "⬅ Previous",
            use_container_width=True,
            disabled=index == 0,
            key="brain_previous",
        ):

            st.session_state.brain_journey_index = max(
                0,
                index - 1,
            )

            st.session_state.brain_system_answer = ""

            st.rerun()

    with restart_col:

        if st.button(
            "🔄 Restart",
            use_container_width=True,
            key="brain_restart",
        ):

            st.session_state.brain_journey_index = 0
            st.session_state.brain_system_answer = ""

            st.rerun()

    with next_col:

        if st.button(
            "Next ➡",
            use_container_width=True,
            disabled=index == len(BRAIN_SYSTEMS) - 1,
            key="brain_next",
        ):

            st.session_state.brain_journey_index = min(
                len(BRAIN_SYSTEMS) - 1,
                index + 1,
            )

            st.session_state.brain_system_answer = ""

            st.rerun()


# ============================================================
# BRAIN PUZZLE
# ============================================================

def puzzle_make_solution(grid):

    return list(
        range(
            grid * grid
        )
    )


def puzzle_shuffle(solution):

    board = solution.copy()

    random.shuffle(
        board
    )

    # Prevent an already-completed puzzle.
    if board == solution:

        random.shuffle(
            board
        )

    return board


def puzzle_new_round(grid):

    solution = puzzle_make_solution(
        grid
    )

    board = puzzle_shuffle(
        solution
    )

    st.session_state.puzzle_grid = grid
    st.session_state.puzzle_solution = solution
    st.session_state.puzzle_board = board
    st.session_state.puzzle_started = True
    st.session_state.puzzle_completed = False
    st.session_state.puzzle_moves = 0
    st.session_state.puzzle_start_time = time.time()
    st.session_state.puzzle_elapsed = 0


def puzzle_swap(
    first,
    second,
):

    board = st.session_state.puzzle_board

    if (
        first < 0
        or second < 0
        or first >= len(board)
        or second >= len(board)
    ):
        return

    board[first], board[second] = (
        board[second],
        board[first],
    )

    st.session_state.puzzle_moves += 1


def puzzle_check():

    board = st.session_state.puzzle_board

    solution = st.session_state.puzzle_solution

    if board == solution:

        st.session_state.puzzle_completed = True

        if st.session_state.puzzle_start_time:

            st.session_state.puzzle_elapsed = (
                time.time()
                - st.session_state.puzzle_start_time
            )

        return True

    return False


def page_puzzle():

    st.title("🧩 Brain Puzzle")

    st.caption(
        "Reconstruct the brain image by arranging the puzzle pieces."
    )

    st.info(
        "Puzzle uses the brain.png asset. "
        "If brain.png is missing, add it to the project root."
    )

    # --------------------------------------------------------
    # CONTROLS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        grid_choice = st.selectbox(
            "Puzzle size",
            [
                "3 × 3 — 9 pieces",
                "3 × 4 — 12 pieces",
                "4 × 4 — 16 pieces",
                "5 × 5 — 25 pieces",
            ],
            key="puzzle_size_choice",
        )

    with col2:

        challenge_mode = st.selectbox(
            "Challenge mode",
            [
                "Standard",
                "Speed Challenge",
                "Minimum Moves",
                "Memory Mode",
            ],
            key="puzzle_challenge_mode",
        )

    with col3:

        st.metric(
            "Moves",
            st.session_state.puzzle_moves,
        )

    grid_map = {
        "3 × 3 — 9 pieces": 3,
        "3 × 4 — 12 pieces": 4,
        "4 × 4 — 16 pieces": 4,
        "5 × 5 — 25 pieces": 5,
    }

    # 3x4 means 12 pieces but the board is represented
    # as 3 rows x 4 columns.
    if grid_choice == "3 × 4 — 12 pieces":

        rows = 3
        cols = 4

    else:

        rows = grid_map[
            grid_choice
        ]

        cols = rows

    total = rows * cols

    if st.button(
        "🎮 New Puzzle",
        type="primary",
        use_container_width=True,
        key="new_brain_puzzle",
    ):

        puzzle_new_round(
            total
        )

        st.session_state.puzzle_rows = rows
        st.session_state.puzzle_cols = cols

        st.rerun()

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    brain_path = find_asset(
        "brain.png"
    )

    if brain_path:

        st.markdown(
            "### 🧠 Source Brain Image"
        )

        st.image(
            str(brain_path),
            use_container_width=True,
        )

    else:

        st.warning(
            "brain.png was not found. "
            "Please upload brain.png to your project."
        )

    # --------------------------------------------------------
    # START PUZZLE
    # --------------------------------------------------------

    if not st.session_state.puzzle_started:

        st.markdown(
            """
            <div class="nl-card" style="
                text-align:center;
            ">

                <div style="font-size:65px;">
                    🧩
                </div>

                <h3>
                    Your puzzle is ready.
                </h3>

                <p>
                    Choose the puzzle size and press
                    <b>New Puzzle</b>.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    # --------------------------------------------------------
    # PUZZLE STATE
    # --------------------------------------------------------

    board = st.session_state.puzzle_board

    if not board:

        puzzle_new_round(
            total
        )

        board = st.session_state.puzzle_board

    rows = st.session_state.get(
        "puzzle_rows",
        rows,
    )

    cols = st.session_state.get(
        "puzzle_cols",
        cols,
    )

    # --------------------------------------------------------
    # IMAGE TILE BOARD
    #
    # This is a reliable Streamlit-native interaction:
    # select one tile, then select another tile to swap them.
    # It works on phone, tablet and laptop.
    #
    # The next upgrade can replace this with a true browser
    # pointer-drag component once a state-returning component
    # is connected.
    # --------------------------------------------------------

    st.markdown(
        "### 🧩 Arrange the Pieces"
    )

    st.caption(
        "Tap one piece and then tap another piece to swap them."
    )

    selected = st.session_state.get(
        "puzzle_selected",
        None,
    )

    # --------------------------------------------------------
    # TILE GRID
    # --------------------------------------------------------

    for row in range(rows):

        columns = st.columns(
            cols
        )

        for col in range(cols):

            index = (
                row * cols
                + col
            )

            if index >= len(board):
                continue

            tile_id = board[index]

            with columns[col]:

                # Source image available:
                # show cropped-looking numbered tiles using
                # CSS background positioning.
                if brain_path:

                    image_uri = asset_data_uri(
                        "brain.png"
                    )

                    if image_uri:

                        x = tile_id % cols
                        y = tile_id // rows

                        # Use tile number visually so every
                        # piece remains identifiable.
                        st.markdown(
                            f"""
                            <div style="
                                width:100%;
                                aspect-ratio:1;
                                border-radius:12px;
                                background-image:url('{image_uri}');
                                background-size:
                                    {cols * 100}%
                                    {rows * 100}%;
                                background-position:
                                    {x * 100 / max(cols - 1, 1)}%
                                    {y * 100 / max(rows - 1, 1)}%;
                                border:
                                    2px solid
                                    rgba(255,255,255,.15);
                                overflow:hidden;
                                margin-bottom:5px;
                            "></div>
                            """,
                            unsafe_allow_html=True,
                        )

                else:

                    st.markdown(
                        f"""
                        <div class="nl-card"
                             style="
                                text-align:center;
                                padding:25px;
                             ">
                            🧩
                            <br>
                            Piece {tile_id + 1}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                label = (
                    f"Selected {tile_id + 1}"
                    if selected == index
                    else f"Piece {tile_id + 1}"
                )

                if st.button(
                    label,
                    use_container_width=True,
                    key=f"puzzle_tile_{index}",
                ):

                    if selected is None:

                        st.session_state.puzzle_selected = index

                    elif selected == index:

                        st.session_state.puzzle_selected = None

                    else:

                        puzzle_swap(
                            selected,
                            index,
                        )

                        st.session_state.puzzle_selected = None

                    st.rerun()

    # --------------------------------------------------------
    # CHECK
    # --------------------------------------------------------

    st.divider()

    if st.button(
        "✅ Check Puzzle",
        type="primary",
        use_container_width=True,
        key="check_brain_puzzle",
    ):

        if puzzle_check():

            st.success(
                "🎉 Puzzle completed!"
            )

            st.balloons()

            score = max(
                0,
                100
                - (
                    st.session_state.puzzle_moves
                    * 2
                ),
            )

            st.metric(
                "Puzzle Score",
                f"{score}/100",
            )

            user_id = current_user_id()

            if user_id:

                db_insert(
                    "brain_puzzle_results",
                    {
                        "user_id": user_id,
                        "grid_size": total,
                        "moves": st.session_state.puzzle_moves,
                        "score": score,
                        "challenge_mode": challenge_mode,
                    },
                )

        else:

            correct_positions = sum(
                1
                for a, b in zip(
                    board,
                    st.session_state.puzzle_solution,
                )
                if a == b
            )

            st.warning(
                f"Not complete yet. "
                f"{correct_positions}/{total} pieces "
                f"are currently in the correct position."
            )

    if st.session_state.puzzle_completed:

        if st.button(
            "🔄 Play Again",
            use_container_width=True,
            key="puzzle_play_again",
        ):

            puzzle_new_round(
                total
            )

            st.session_state.puzzle_rows = rows
            st.session_state.puzzle_cols = cols
            st.session_state.puzzle_selected = None

            st.rerun()

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    if st.button(
        "↩ Reset Puzzle",
        use_container_width=True,
        key="reset_brain_puzzle",
    ):

        puzzle_new_round(
            total
        )

        st.session_state.puzzle_rows = rows
        st.session_state.puzzle_cols = cols
        st.session_state.puzzle_selected = None

        st.rerun()

    # --------------------------------------------------------
    # SIMULATION NOTICE
    # --------------------------------------------------------

    st.caption(
        "Puzzle performance reflects this interactive task only; "
        "it is not a measure of intelligence or brain function."
    )


# ============================================================
# PART 2 END
# ============================================================
# ============================================================
# NEUROLENS — PART 3
# BRAIN CHALLENGES + ASK AYNA + AI MOOD/BEHAVIOUR + RESEARCH
# ============================================================


# ============================================================
# BRAIN CHALLENGES
# ============================================================

def save_exercise_result(
    exercise,
    score,
    details=None,
):

    result = {
        "exercise": exercise,
        "score": float(score),
        "details": details or {},
        "timestamp": time.time(),
    }

    st.session_state.exercise_scores.append(
        result
    )

    user_id = current_user_id()

    if user_id:

        db_insert(
            "exercise_results",
            {
                "user_id": user_id,
                "exercise": exercise,
                "score": float(score),
                "result_data": result,
            },
        )


def working_memory_challenge():

    st.markdown(
        """
        <div class="nl-card">
            <h3>🧠 Working Memory</h3>
            <p>
                Memorize the sequence and reproduce it after
                it disappears.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "challenge_memory_sequence" not in st.session_state:
        st.session_state.challenge_memory_sequence = None

    if "challenge_memory_visible" not in st.session_state:
        st.session_state.challenge_memory_visible = False

    if st.session_state.challenge_memory_sequence is None:

        length = st.select_slider(
            "Sequence length",
            options=[4, 5, 6, 7, 8],
            value=5,
            key="memory_challenge_length",
        )

        if st.button(
            "▶ Start Memory Challenge",
            type="primary",
            use_container_width=True,
            key="start_memory_challenge",
        ):

            sequence = "".join(
                str(
                    random.randint(0, 9)
                )
                for _ in range(length)
            )

            st.session_state.challenge_memory_sequence = sequence
            st.session_state.challenge_memory_visible = True

            st.rerun()

        return

    sequence = (
        st.session_state.challenge_memory_sequence
    )

    if st.session_state.challenge_memory_visible:

        st.markdown(
            f"""
            <div class="nl-card" style="
                text-align:center;
                padding:35px;
            ">

                <div class="small-muted">
                    Memorize
                </div>

                <div style="
                    font-size:44px;
                    font-weight:900;
                    letter-spacing:8px;
                    margin-top:15px;
                ">
                    {sequence}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Hide Sequence",
            type="primary",
            use_container_width=True,
            key="hide_memory_challenge",
        ):

            st.session_state.challenge_memory_visible = False

            st.rerun()

        return

    answer = st.text_input(
        "Enter the sequence",
        max_chars=30,
        key="memory_challenge_answer",
    )

    if st.button(
        "Check Memory",
        type="primary",
        use_container_width=True,
        key="check_memory_challenge",
    ):

        correct = (
            answer.strip()
            == sequence
        )

        score = 100 if correct else 0

        if correct:

            st.success(
                "🎯 Excellent memory."
            )

        else:

            st.error(
                "The sequence did not match."
            )

        save_exercise_result(
            "Working Memory",
            score,
            {
                "correct": correct,
                "sequence_length": len(sequence),
            },
        )

        st.session_state.challenge_memory_sequence = None
        st.session_state.challenge_memory_visible = False

        st.rerun()


def attention_challenge():

    st.markdown(
        """
        <div class="nl-card">
            <h3>👁️ Attention Challenge</h3>
            <p>
                Find the target symbol among distractors.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "attention_challenge_data" not in st.session_state:

        st.session_state.attention_challenge_data = None

    if st.session_state.attention_challenge_data is None:

        if st.button(
            "▶ Start Attention Challenge",
            type="primary",
            use_container_width=True,
            key="start_attention_challenge",
        ):

            target = random.choice(
                ["X", "K", "M", "R"]
            )

            options = [
                random.choice(
                    ["X", "K", "M", "R", "A", "B"]
                )
                for _ in range(24)
            ]

            correct_index = random.randrange(
                len(options)
            )

            options[correct_index] = target

            st.session_state.attention_challenge_data = {
                "target": target,
                "options": options,
                "correct": correct_index,
                "started": time.time(),
            }

            st.rerun()

        return

    data = (
        st.session_state.attention_challenge_data
    )

    st.markdown(
        f"""
        <div class="nl-card" style="
            text-align:center;
        ">

            <div class="small-muted">
                Find
            </div>

            <div style="
                font-size:48px;
                font-weight:900;
            ">
                {data["target"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(6)

    for index, value in enumerate(
        data["options"]
    ):

        with cols[index % 6]:

            if st.button(
                value,
                key=f"attention_challenge_{index}",
                use_container_width=True,
            ):

                elapsed = (
                    time.time()
                    - data["started"]
                )

                correct = (
                    index
                    == data["correct"]
                )

                if correct:

                    score = max(
                        0,
                        min(
                            100,
                            int(
                                100
                                - elapsed * 10
                            ),
                        ),
                    )

                    st.success(
                        "🎯 Correct target."
                    )

                else:

                    score = 0

                    st.error(
                        "Not the target."
                    )

                save_exercise_result(
                    "Attention",
                    score,
                    {
                        "correct": correct,
                        "reaction_time": elapsed,
                    },
                )

                st.session_state.attention_challenge_data = None

                st.rerun()


def pattern_challenge():

    st.markdown(
        """
        <div class="nl-card">
            <h3>🔢 Pattern Recognition</h3>
            <p>
                Find the next number in the sequence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    patterns = [
        (["2", "4", "8", "16", "?"], "32"),
        (["3", "6", "12", "24", "?"], "48"),
        (["5", "10", "20", "40", "?"], "80"),
        (["1", "4", "9", "16", "?"], "25"),
    ]

    if "pattern_challenge_data" not in st.session_state:

        st.session_state.pattern_challenge_data = random.choice(
            patterns
        )

    sequence, answer = (
        st.session_state.pattern_challenge_data
    )

    st.markdown(
        f"""
        <div class="nl-card" style="
            text-align:center;
        ">

            <div style="
                font-size:30px;
                font-weight:900;
            ">
                {" → ".join(sequence)}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    response = st.text_input(
        "Next value",
        key="pattern_challenge_answer",
    )

    if st.button(
        "Check Pattern",
        type="primary",
        use_container_width=True,
        key="check_pattern_challenge",
    ):

        correct = (
            response.strip()
            == answer
        )

        score = 100 if correct else 0

        if correct:

            st.success(
                "🧠 Correct pattern."
            )

        else:

            st.error(
                f"Not quite. The expected value was {answer}."
            )

        save_exercise_result(
            "Pattern Recognition",
            score,
            {
                "correct": correct,
            },
        )

        st.session_state.pattern_challenge_data = None

        st.rerun()


def decision_challenge():

    st.markdown(
        """
        <div class="nl-card">
            <h3>💰 Decision Challenge</h3>

            <p>
                Choose between an immediate smaller reward
                and a delayed larger reward.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Your choice",
        [
            "PKR 1,000 today",
            "PKR 1,500 after 30 days",
        ],
        key="decision_challenge_choice",
    )

    if st.button(
        "Submit Decision",
        type="primary",
        use_container_width=True,
        key="submit_decision_challenge",
    ):

        if "30 days" in choice:

            observation = (
                "You selected the delayed larger reward."
            )

        else:

            observation = (
                "You selected the immediate reward."
            )

        st.success(
            "Decision recorded."
        )

        st.info(
            observation
        )

        save_exercise_result(
            "Decision Challenge",
            100,
            {
                "choice": choice,
            },
        )


def reaction_challenge():

    st.markdown(
        """
        <div class="nl-card">
            <h3>⚡ Quick Reaction</h3>
            <p>
                Start the task and react when the signal appears.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "reaction_ready" not in st.session_state:
        st.session_state.reaction_ready = False

    if "reaction_waiting" not in st.session_state:
        st.session_state.reaction_waiting = False

    if "reaction_start" not in st.session_state:
        st.session_state.reaction_start = None

    if not st.session_state.reaction_waiting:

        if st.button(
            "▶ Start Reaction Test",
            type="primary",
            use_container_width=True,
            key="start_reaction_test",
        ):

            st.session_state.reaction_waiting = True
            st.session_state.reaction_ready = False

            delay = random.uniform(
                1.0,
                3.0,
            )

            time.sleep(
                delay
            )

            st.session_state.reaction_ready = True
            st.session_state.reaction_start = time.time()

            st.rerun()

        return

    if not st.session_state.reaction_ready:

        st.warning(
            "Wait for the signal..."
        )

        return

    if st.button(
        "🟢 TAP NOW!",
        type="primary",
        use_container_width=True,
        key="reaction_now",
    ):

        reaction_time = (
            time.time()
            - st.session_state.reaction_start
        )

        score = max(
            0,
            min(
                100,
                int(
                    100
                    - reaction_time * 100
                ),
            ),
        )

        st.success(
            f"Reaction time: {reaction_time:.3f} seconds"
        )

        save_exercise_result(
            "Quick Reaction",
            score,
            {
                "reaction_time": reaction_time,
            },
        )

        st.session_state.reaction_waiting = False
        st.session_state.reaction_ready = False
        st.session_state.reaction_start = None


def stroop_challenge():

    st.markdown(
        """
        <div class="nl-card">
            <h3>🎨 Stroop Challenge</h3>
            <p>
                Select the colour of the text, not the written word.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "challenge_stroop" not in st.session_state:
        st.session_state.challenge_stroop = None

    if st.session_state.challenge_stroop is None:

        items = [
            ("RED", "blue"),
            ("BLUE", "red"),
            ("GREEN", "yellow"),
            ("YELLOW", "green"),
        ]

        st.session_state.challenge_stroop = random.choice(
            items
        )

    word, colour = (
        st.session_state.challenge_stroop
    )

    st.markdown(
        f"""
        <div class="nl-card" style="
            text-align:center;
        ">

            <div style="
                color:{colour};
                font-size:50px;
                font-weight:900;
            ">
                {word}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.radio(
        "Ink colour",
        [
            "red",
            "blue",
            "green",
            "yellow",
        ],
        horizontal=True,
        key="challenge_stroop_answer",
    )

    if st.button(
        "Submit",
        type="primary",
        use_container_width=True,
        key="submit_stroop_challenge",
    ):

        correct = (
            answer == colour
        )

        score = 100 if correct else 0

        if correct:
            st.success("🎯 Correct.")
        else:
            st.error("❌ Incorrect.")

        save_exercise_result(
            "Stroop Cognitive Control",
            score,
            {
                "correct": correct,
            },
        )

        st.session_state.challenge_stroop = None

        st.rerun()


def page_challenges():

    st.title("🎯 Brain Challenges")

    st.caption(
        "Short interactive cognitive exercises."
    )

    st.warning(
        "These are educational behavioural tasks. "
        "They are not diagnostic tests and do not measure "
        "actual brain activity."
    )

    challenge = st.selectbox(
        "Choose a challenge",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
            "Quick Reaction",
            "Stroop Cognitive Control",
        ],
        key="brain_challenge_selector",
    )

    st.divider()

    if challenge == "Working Memory":

        working_memory_challenge()

    elif challenge == "Attention":

        attention_challenge()

    elif challenge == "Pattern Recognition":

        pattern_challenge()

    elif challenge == "Decision Challenge":

        decision_challenge()

    elif challenge == "Quick Reaction":

        reaction_challenge()

    elif challenge == "Stroop Cognitive Control":

        stroop_challenge()


# ============================================================
# ASK AYNA
# ============================================================

def ask_ayna_prompt(
    user_message
):

    message = clean_text(
        user_message,
        4000,
    )

    if not message:
        return

    prompt = f"""
You are Ayna, the AI research companion inside NEUROLENS.

Your role:
- Explain cognitive neuroscience, brain systems,
  behaviour, AI and research concepts.
- Help users learn.
- Be scientifically cautious.
- Clearly distinguish established evidence from uncertainty.
- Never diagnose a person.
- Never claim to read someone's mind.
- Never claim that a game, voice recording, facial image,
  or self-report can directly measure brain activity.
- Do not present AI guesses as facts.
- If a health issue is raised, encourage appropriate
  professional support when relevant.

User message:
{message}

Give a clear, useful response.
"""

    answer = ai_generate(
        prompt,
        max_output_tokens=1500,
    )

    st.session_state.ayna_messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    st.session_state.ayna_messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    user_id = current_user_id()

    if user_id:

        db_insert(
            "ai_requests",
            {
                "user_id": user_id,
                "request_text": message,
                "response_text": answer,
                "request_type": "ask_ayna",
            },
        )


def page_ask_ayna():

    st.title("🤖 Ask Ayna")

    st.caption(
        "Ask Ayna about cognition, neuroscience, behaviour, AI or research."
    )

    if not ai_available():

        st.info(
            "Add GEMINI_API_KEY to Streamlit Secrets "
            "to activate Ask Ayna."
        )

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    for message in st.session_state.get(
        "ayna_messages",
        [],
    ):

        role = message.get(
            "role"
        )

        content = message.get(
            "content",
            "",
        )

        if role == "user":

            with st.chat_message(
                "user"
            ):

                st.write(
                    content
                )

        else:

            with st.chat_message(
                "assistant"
            ):

                st.write(
                    content
                )

                if st.button(
                    "🔊 Speak Ayna",
                    key=f"speak_{hash(content)}",
                ):

                    speak_text(
                        content
                    )

    # --------------------------------------------------------
    # INPUT
    # --------------------------------------------------------

    prompt = st.chat_input(
        "Ask Ayna..."
    )

    if prompt:

        with st.spinner(
            "Ayna is thinking..."
        ):

            ask_ayna_prompt(
                prompt
            )

        st.rerun()

    # --------------------------------------------------------
    # QUICK PROMPTS
    # --------------------------------------------------------

    st.markdown(
        "### 💡 Try asking"
    )

    quick_prompts = [
        "What is working memory?",
        "How does attention work?",
        "Explain the CSTC loop simply.",
        "What is neuroplasticity?",
        "How does reward affect decision-making?",
        "What is the difference between AI and human cognition?",
    ]

    quick_cols = st.columns(2)

    for index, question in enumerate(
        quick_prompts
    ):

        with quick_cols[index % 2]:

            if st.button(
                question,
                use_container_width=True,
                key=f"quick_ayna_{index}",
            ):

                with st.spinner(
                    "Ayna is thinking..."
                ):

                    ask_ayna_prompt(
                        question
                    )

                st.rerun()


# ============================================================
# AI VOICE + FACE MOOD/BEHAVIOUR
# ============================================================

def parse_ai_json(
    text,
    fallback=None,
):

    fallback = fallback or {}

    if not text:
        return fallback

    cleaned = re.sub(
        r"```(?:json)?",
        "",
        text,
        flags=re.I,
    )

    cleaned = cleaned.replace(
        "```",
        "",
    ).strip()

    try:

        return json.loads(
            cleaned
        )

    except Exception:

        match = re.search(
            r"\{.*\}",
            cleaned,
            flags=re.S,
        )

        if match:

            try:

                return json.loads(
                    match.group(0)
                )

            except Exception:
                pass

    return fallback


def analyse_voice_with_ai(
    audio_bytes,
    mime_type="audio/wav",
):

    if not ai_available():

        return {
            "transcript": "",
            "emoji": "🧩",
            "vibe_label": "AI unavailable",
            "explanation": (
                "Gemini is not connected."
            ),
        }

    if ai_limit_reached():

        return {
            "transcript": "",
            "emoji": "⏳",
            "vibe_label": "Temporarily limited",
            "explanation": (
                "Please wait before making another AI request."
            ),
        }

    try:

        from google.genai import types

        register_ai_request()

        prompt = """
Return ONLY valid JSON with these keys:

transcript
emoji
vibe_label
explanation

vibe_label must describe only observable
communication/acoustic characteristics, such as:

Positive/energetic-sounding
Calm-sounding
Neutral/mixed
Tense-sounding
Low-energy-sounding
Uncertain/mixed

Important:
- Do not claim certainty about hidden emotions.
- Do not diagnose.
- Do not infer personality.
- Do not infer mental health.
- Do not claim to read the person's mind.
- Explain that the result is an AI-assisted interpretation.
"""

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type,
                ),
            ],
        )

        result = parse_ai_json(
            getattr(
                response,
                "text",
                "",
            ),
            {
                "transcript": "",
                "emoji": "🧩",
                "vibe_label": "Uncertain/mixed",
                "explanation": (
                    "The AI could not provide a reliable structured interpretation."
                ),
            },
        )

        return result

    except Exception as exc:

        st.session_state.last_error = str(
            exc
        )

        return {
            "transcript": "",
            "emoji": "⚠️",
            "vibe_label": "Unavailable",
            "explanation": (
                "Voice analysis could not be completed safely."
            ),
        }


def analyse_face_with_ai(
    image_bytes,
    mime_type="image/jpeg",
):

    if not ai_available():

        return {
            "emoji": "🧩",
            "expression": "AI unavailable",
            "explanation": (
                "Gemini is not connected."
            ),
        }

    if ai_limit_reached():

        return {
            "emoji": "⏳",
            "expression": "Temporarily limited",
            "explanation": (
                "Please wait before making another AI request."
            ),
        }

    try:

        from google.genai import types

        register_ai_request()

        prompt = """
Return ONLY valid JSON with:

emoji
expression
explanation

Describe only visible facial expression cues.

Examples:
smiling
neutral
focused-looking
surprised-looking
frowning
uncertain

Rules:
- Do not identify the person.
- Do not infer personality.
- Do not infer hidden emotions with certainty.
- Do not diagnose.
- Do not infer mental health.
- Do not claim to know what the person is thinking.
- Clearly describe the result as an AI-assisted visual estimate.
"""

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
            ],
        )

        return parse_ai_json(
            getattr(
                response,
                "text",
                "",
            ),
            {
                "emoji": "🧩",
                "expression": "Uncertain",
                "explanation": (
                    "The visual interpretation could not be structured reliably."
                ),
            },
        )

    except Exception as exc:

        st.session_state.last_error = str(
            exc
        )

        return {
            "emoji": "⚠️",
            "expression": "Unavailable",
            "explanation": (
                "Face interpretation could not be completed."
            ),
        }


def page_mood():

    st.title("🎭 AI Mood & Behaviour")

    st.caption(
        "AI-assisted interpretation of observable voice and facial-expression cues."
    )

    st.warning(
        "This feature does not read minds, measure brain activity, "
        "diagnose mental health, or determine a person's true "
        "emotional state. Results are probabilistic AI estimates."
    )

    tab_voice, tab_face, tab_combined = st.tabs(
        [
            "🎙️ Voice",
            "📷 Face",
            "🔗 Combined",
        ]
    )

    # ========================================================
    # VOICE
    # ========================================================

    with tab_voice:

        st.subheader(
            "🎙️ Voice Interpretation"
        )

        voice = st.audio_input(
            "Record your voice",
            key="mood_voice_input",
        )

        if voice:

            if st.button(
                "📤 SEND VOICE",
                type="primary",
                use_container_width=True,
                key="send_mood_voice",
            ):

                with st.spinner(
                    "Ayna is analysing the voice..."
                ):

                    result = analyse_voice_with_ai(
                        voice.getvalue(),
                        voice.type or "audio/wav",
                    )

                st.session_state.voice_result = result

                user_id = current_user_id()

                if user_id:

                    db_insert(
                        "voice_mood_results",
                        {
                            "user_id": user_id,
                            "result_data": result,
                            "source_type": "voice",
                        },
                    )

                st.rerun()

        if st.session_state.voice_result:

            result = (
                st.session_state.voice_result
            )

            st.markdown(
                f"""
                <div class="nl-card">

                    <div style="
                        font-size:48px;
                    ">
                        {result.get("emoji", "🧩")}
                    </div>

                    <h3>
                        {result.get(
                            "vibe_label",
                            "Uncertain/mixed"
                        )}
                    </h3>

                    <p>
                        {result.get(
                            "explanation",
                            ""
                        )}
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "### 📝 Transcript"
            )

            st.write(
                result.get(
                    "transcript",
                    "",
                )
            )

            st.caption(
                "AI-assisted voice-vibe interpretation based on "
                "observable communication/acoustic cues."
            )

    # ========================================================
    # FACE
    # ========================================================

    with tab_face:

        st.subheader(
            "📷 Facial Expression Interpretation"
        )

        camera_image = st.camera_input(
            "Take a photo",
            key="mood_face_camera",
        )

        if camera_image:

            st.image(
                camera_image,
                caption="Captured image",
                use_container_width=True,
            )

            if st.button(
                "🔎 Analyse Expression",
                type="primary",
                use_container_width=True,
                key="analyse_face",
            ):

                with st.spinner(
                    "Ayna is analysing visible expression cues..."
                ):

                    result = analyse_face_with_ai(
                        camera_image.getvalue(),
                        camera_image.type or "image/jpeg",
                    )

                st.session_state.face_result = result

                user_id = current_user_id()

                if user_id:

                    db_insert(
                        "voice_mood_results",
                        {
                            "user_id": user_id,
                            "result_data": result,
                            "source_type": "face",
                        },
                    )

                st.rerun()

        if st.session_state.face_result:

            result = (
                st.session_state.face_result
            )

            st.markdown(
                f"""
                <div class="nl-card">

                    <div style="
                        font-size:48px;
                    ">
                        {result.get("emoji", "🧩")}
                    </div>

                    <h3>
                        {result.get(
                            "expression",
                            "Uncertain"
                        )}
                    </h3>

                    <p>
                        {result.get(
                            "explanation",
                            ""
                        )}
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # ========================================================
    # COMBINED
    # ========================================================

    with tab_combined:

        st.subheader(
            "🔗 Combined Voice + Face"
        )

        st.write(
            "Record a voice sample and capture a facial image. "
            "The two AI estimates can then be compared."
        )

        voice_combined = st.audio_input(
            "Voice sample",
            key="combined_voice",
        )

        face_combined = st.camera_input(
            "Facial image",
            key="combined_face",
        )

        if st.button(
            "🔗 Run Combined Interpretation",
            type="primary",
            use_container_width=True,
            key="run_combined_mood",
        ):

            if not voice_combined and not face_combined:

                st.error(
                    "Provide at least a voice sample or facial image."
                )

            else:

                voice_result = None
                face_result = None

                if voice_combined:

                    with st.spinner(
                        "Analysing voice..."
                    ):

                        voice_result = analyse_voice_with_ai(
                            voice_combined.getvalue(),
                            voice_combined.type or "audio/wav",
                        )

                if face_combined:

                    with st.spinner(
                        "Analysing visible expression..."
                    ):

                        face_result = analyse_face_with_ai(
                            face_combined.getvalue(),
                            face_combined.type or "image/jpeg",
                        )

                st.session_state.voice_result = (
                    voice_result
                )

                st.session_state.face_result = (
                    face_result
                )

                st.success(
                    "Combined analysis completed."
                )

                if voice_result:

                    st.markdown(
                        f"""
                        <div class="nl-card">

                            <h4>
                                🎙️ Voice
                            </h4>

                            <div style="
                                font-size:32px;
                            ">
                                {voice_result.get(
                                    "emoji",
                                    "🧩"
                                )}
                            </div>

                            <p>
                                {voice_result.get(
                                    "vibe_label",
                                    "Uncertain"
                                )}
                            </p>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if face_result:

                    st.markdown(
                        f"""
                        <div class="nl-card">

                            <h4>
                                📷 Face
                            </h4>

                            <div style="
                                font-size:32px;
                            ">
                                {face_result.get(
                                    "emoji",
                                    "🧩"
                                )}
                            </div>

                            <p>
                                {face_result.get(
                                    "expression",
                                    "Uncertain"
                                )}
                            </p>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.caption(
                    "If the two signals differ, that does not mean "
                    "the person is hiding an emotion. Different "
                    "modalities can simply provide different cues."
                )


# ============================================================
# RESEARCH WORLD
# ============================================================

def europe_pmc_search(
    query,
    page_size=10,
):

    if requests is None:

        return []

    query = clean_text(
        query,
        500,
    )

    if not query:
        return []

    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/"
        "rest/search"
    )

    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "resultList",
            {}
        ).get(
            "result",
            [],
        )

    except Exception as exc:

        st.session_state.last_error = str(
            exc
        )

        return []


def research_ai_summary(
    title,
    abstract,
):

    prompt = f"""
You are Ayna, a cautious research assistant.

Summarize this scientific paper for a cognitive-neuroscience
researcher.

Title:
{clean_text(title, 1000)}

Abstract:
{clean_text(abstract, 5000)}

Provide:
1. Main question
2. Main finding
3. Possible relevance
4. One limitation or caution

Do not invent information not present in the supplied text.
"""

    return ai_generate(
        prompt,
        max_output_tokens=1000,
    )


def save_research_note(
    title,
    note,
    paper_url="",
):

    payload = {
        "title": clean_text(
            title,
            500,
        ),
        "note": clean_text(
            note,
            5000,
        ),
        "paper_url": clean_text(
            paper_url,
            1000,
        ),
        "timestamp": time.time(),
    }

    st.session_state.research_notes.append(
        payload
    )

    user_id = current_user_id()

    if user_id:

        db_insert(
            "research_notes",
            {
                "user_id": user_id,
                "title": payload["title"],
                "note": payload["note"],
                "paper_url": payload["paper_url"],
            },
        )


def page_research():

    st.title("🔬 Research World")

    st.caption(
        "Search biomedical literature through Europe PMC and build research notes."
    )

    query = st.text_input(
        "Research topic",
        placeholder=(
            "e.g. attention and reward learning"
        ),
        key="research_query",
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔎 Search Europe PMC",
            type="primary",
            use_container_width=True,
            key="search_research",
        ):

            if not query.strip():

                st.warning(
                    "Enter a research topic first."
                )

            else:

                with st.spinner(
                    "Searching biomedical literature..."
                ):

                    results = europe_pmc_search(
                        query,
                        page_size=10,
                    )

                st.session_state.research_results = results

                if not results:

                    st.info(
                        "No results found."
                    )

    with col2:

        if st.button(
            "🗑 Clear Results",
            use_container_width=True,
            key="clear_research",
        ):

            st.session_state.research_results = []

            st.rerun()

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    results = st.session_state.get(
        "research_results",
        [],
    )

    if results:

        st.divider()

        st.subheader(
            f"📚 {len(results)} Research Results"
        )

        for index, paper in enumerate(
            results
        ):

            title = paper.get(
                "title",
                "Untitled paper",
            )

            abstract = paper.get(
                "abstractText",
                "",
            )

            journal = paper.get(
                "journalTitle",
                "",
            )

            year = paper.get(
                "pubYear",
                "",
            )

            pmid = paper.get(
                "pmid",
                "",
            )

            doi = paper.get(
                "doi",
                "",
            )

            if pmid:

                paper_url = (
                    "https://pubmed.ncbi.nlm.nih.gov/"
                    + str(pmid)
                    + "/"
                )

            elif doi:

                paper_url = (
                    "https://doi.org/"
                    + str(doi)
                )

            else:

                paper_url = ""

            with st.expander(
                f"{index + 1}. {title}"
            ):

                if journal or year:

                    st.caption(
                        f"{journal} {year}".strip()
                    )

                if abstract:

                    st.write(
                        abstract
                    )

                else:

                    st.info(
                        "No abstract was available from the result."
                    )

                if paper_url:

                    st.markdown(
                        f"[📄 Open paper record]({paper_url})"
                    )

                st.divider()

                if st.button(
                    "🤖 Summarize with Ayna",
                    key=f"research_summary_{index}",
                ):

                    with st.spinner(
                        "Preparing research summary..."
                    ):

                        summary = research_ai_summary(
                            title,
                            abstract,
                        )

                    st.session_state[
                        f"research_summary_{index}"
                    ] = summary

                    st.rerun()

                summary = st.session_state.get(
                    f"research_summary_{index}",
                    "",
                )

                if summary:

                    st.markdown(
                        "### 🤖 Ayna's Research Summary"
                    )

                    st.write(
                        summary
                    )

                    note = st.text_area(
                        "Research note",
                        key=f"research_note_{index}",
                        placeholder=(
                            "Write your own research observation..."
                        ),
                    )

                    if st.button(
                        "💾 Save Research Note",
                        key=f"save_research_note_{index}",
                    ):

                        if not note.strip():

                            st.warning(
                                "Write a note first."
                            )

                        else:

                            save_research_note(
                                title,
                                note,
                                paper_url,
                            )

                            st.success(
                                "Research note saved."
                            )

    # --------------------------------------------------------
    # SAVED NOTES
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "📓 My Research Notes"
    )

    notes = st.session_state.get(
        "research_notes",
        [],
    )

    if not notes:

        st.caption(
            "No research notes saved in this session yet."
        )

    else:

        for note in reversed(
            notes[-20:]
        ):

            with st.expander(
                note.get(
                    "title",
                    "Research note",
                )
            ):

                st.write(
                    note.get(
                        "note",
                        "",
                    )
                )

                if note.get(
                    "paper_url"
                ):

                    st.markdown(
                        f"[Open source paper]({note['paper_url']})"
                    )


# ============================================================
# PART 3 END
# ============================================================
# ============================================================
# NEUROLENS — PART 4
# PRIVATE AYNA + NEUROSOCIAL + CONSULTATION
# PROGRESS + SECURITY + SETTINGS + ACCOUNT + FINAL ROUTER
# ============================================================


# ============================================================
# PRIVATE AYNA
# ============================================================

def hash_private_pin(pin):

    pin = clean_text(
        pin,
        20,
    )

    if not pin.isdigit():
        return ""

    if len(pin) < 4 or len(pin) > 6:
        return ""

    salt = os.urandom(16)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        120000,
    )

    return (
        base64.b64encode(salt).decode()
        + ":"
        + base64.b64encode(derived).decode()
    )


def verify_private_pin(
    pin,
    stored_hash,
):

    try:

        salt_b64, hash_b64 = stored_hash.split(
            ":",
            1,
        )

        salt = base64.b64decode(
            salt_b64
        )

        expected = base64.b64decode(
            hash_b64
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            120000,
        )

        return hmac.compare_digest(
            actual,
            expected,
        )

    except Exception:

        return False


def page_private():

    st.title("🔐 Private Ayna")

    st.caption(
        "A private session area for personal notes and conversations."
    )

    if not st.session_state.private_unlocked:

        st.markdown(
            """
            <div class="nl-card">

                <h3>🔒 Private Space</h3>

                <p>
                    Create a 4–6 digit PIN for this browser session.
                    The PIN is processed using salted PBKDF2-HMAC-SHA256.
                </p>

                <p class="small-muted">
                    Do not use a PIN that you use for banking,
                    Easypaisa, email or another important account.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        pin = st.text_input(
            "Enter PIN",
            type="password",
            max_chars=6,
            key="private_pin_input",
        )

        if st.button(
            "🔓 Unlock Private Ayna",
            type="primary",
            use_container_width=True,
            key="unlock_private",
        ):

            if (
                pin.isdigit()
                and 4 <= len(pin) <= 6
            ):

                if not st.session_state.private_pin_hash:

                    st.session_state.private_pin_hash = (
                        hash_private_pin(
                            pin
                        )
                    )

                    st.session_state.private_unlocked = True

                    st.success(
                        "Private Ayna unlocked for this session."
                    )

                    st.rerun()

                else:

                    if verify_private_pin(
                        pin,
                        st.session_state.private_pin_hash,
                    ):

                        st.session_state.private_unlocked = True

                        st.success(
                            "Private Ayna unlocked."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Incorrect PIN."
                        )

            else:

                st.error(
                    "PIN must contain 4–6 digits."
                )

        st.info(
            "This session PIN is stored in Streamlit session state. "
            "For long-term account security, use your main account "
            "authentication as the primary protection."
        )

        return

    # --------------------------------------------------------
    # UNLOCKED
    # --------------------------------------------------------

    top1, top2 = st.columns(2)

    with top1:

        st.success(
            "🔓 Private Ayna is unlocked."
        )

    with top2:

        if st.button(
            "🔒 Lock",
            use_container_width=True,
            key="lock_private",
        ):

            st.session_state.private_unlocked = False
            st.rerun()

    st.divider()

    message = st.text_area(
        "Private message",
        height=130,
        max_chars=4000,
        placeholder=(
            "Write a private thought, research idea or question..."
        ),
        key="private_message_input",
    )

    if st.button(
        "💾 Save Private Message",
        type="primary",
        use_container_width=True,
        key="save_private_message",
    ):

        if not message.strip():

            st.warning(
                "Write something first."
            )

        else:

            item = {
                "role": "user",
                "content": clean_text(
                    message,
                    4000,
                ),
                "timestamp": time.time(),
            }

            st.session_state.private_messages.append(
                item
            )

            user_id = current_user_id()

            if user_id:

                db_insert(
                    "private_ayna_messages",
                    {
                        "user_id": user_id,
                        "message": item["content"],
                        "role": "user",
                    },
                )

            st.success(
                "Private message saved for this session."
            )

    if st.session_state.private_messages:

        st.divider()

        st.subheader(
            "📓 Private Session Notes"
        )

        for item in reversed(
            st.session_state.private_messages[-20:]
        ):

            st.markdown(
                f"""
                <div class="nl-card">
                    <p>
                        {item.get("content", "")}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# NEUROSOCIAL
# ============================================================

def page_social():

    st.title("🌐 NeuroSocial")

    st.caption(
        "A simple space for neuroscience learning, sharing and collaboration."
    )

    if not current_user_id():

        st.info(
            "Sign in to use account-based social features."
        )

        return

    tab_feed, tab_profile, tab_invite = st.tabs(
        [
            "📰 Feed",
            "👤 My Profile",
            "🤝 Invitations",
        ]
    )

    # --------------------------------------------------------
    # FEED
    # --------------------------------------------------------

    with tab_feed:

        st.subheader(
            "🧠 Research & Brain Ideas"
        )

        post_text = st.text_area(
            "Share an idea",
            max_chars=1500,
            placeholder=(
                "Share a neuroscience observation, research idea "
                "or learning insight..."
            ),
            key="social_post_text",
        )

        if st.button(
            "📤 Publish",
            type="primary",
            use_container_width=True,
            key="publish_social_post",
        ):

            if not post_text.strip():

                st.warning(
                    "Write something first."
                )

            else:

                user_id = current_user_id()

                db_insert(
                    "stories",
                    {
                        "user_id": user_id,
                        "content": clean_text(
                            post_text,
                            1500,
                        ),
                    },
                )

                st.success(
                    "Your post was submitted."
                )

        st.divider()

        try:

            feed = db_select(
                "stories",
                limit=20,
            )

        except Exception:

            feed = []

        if not feed:

            st.caption(
                "No public posts are available yet."
            )

        else:

            for post in feed:

                content = post.get(
                    "content",
                    "",
                )

                if not content:
                    continue

                st.markdown(
                    f"""
                    <div class="nl-card">

                        <div style="
                            font-size:24px;
                            margin-bottom:8px;
                        ">
                            🧠
                        </div>

                        <p>
                            {content}
                        </p>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    with tab_profile:

        st.subheader(
            "👤 Profile"
        )

        name = st.text_input(
            "Display name",
            value=st.session_state.profile_name,
            max_chars=80,
            key="social_profile_name",
        )

        bio = st.text_area(
            "Bio",
            value=st.session_state.profile_bio,
            max_chars=500,
            key="social_profile_bio",
        )

        if st.button(
            "💾 Save Profile",
            type="primary",
            use_container_width=True,
            key="save_social_profile",
        ):

            st.session_state.profile_name = clean_text(
                name,
                80,
            )

            st.session_state.profile_bio = clean_text(
                bio,
                500,
            )

            user_id = current_user_id()

            if user_id:

                db_insert(
                    "profiles",
                    {
                        "id": user_id,
                        "display_name": st.session_state.profile_name,
                        "bio": st.session_state.profile_bio,
                    },
                )

            st.success(
                "Profile information saved."
            )

    # --------------------------------------------------------
    # INVITATIONS
    # --------------------------------------------------------

    with tab_invite:

        st.subheader(
            "🤝 Collaboration Invitation"
        )

        email = st.text_input(
            "Person's email",
            key="social_invite_email",
        )

        message = st.text_area(
            "Invitation message",
            max_chars=1000,
            key="social_invite_message",
        )

        if st.button(
            "📨 Send Invitation",
            type="primary",
            use_container_width=True,
            key="send_social_invitation",
        ):

            if not email.strip():

                st.warning(
                    "Enter an email address."
                )

            else:

                user_id = current_user_id()

                db_insert(
                    "invitations",
                    {
                        "sender_id": user_id,
                        "email": clean_text(
                            email,
                            200,
                        ),
                        "message": clean_text(
                            message,
                            1000,
                        ),
                    },
                )

                st.success(
                    "Invitation request submitted."
                )


# ============================================================
# BEHAVIOUR DECODING / CONSULTATION
# ============================================================

CONSULTATION_PRICES = {
    "20 min": {
        "PKR": "1,000",
        "USD": "8",
    },
    "30 min": {
        "PKR": "1,500",
        "USD": "10",
    },
    "45 min": {
        "PKR": "2,000",
        "USD": "12",
    },
    "Advice / Consultation": {
        "PKR": "1,500",
        "USD": "10",
    },
}


def page_consultation():

    st.title("🧩 Behaviour Decoding")

    st.caption(
        "Book a structured educational consultation about behaviour, cognition and research."
    )

    st.warning(
        "This is not a medical diagnosis or emergency mental-health service."
    )

    st.subheader(
        "💳 Consultation Options"
    )

    for duration, price in CONSULTATION_PRICES.items():

        st.markdown(
            f"""
            <div class="nl-card">

                <h3>
                    {duration}
                </h3>

                <p>
                    🇵🇰 PKR {price["PKR"]}
                    &nbsp; | &nbsp;
                    🌍 ${price["USD"]}
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    selected = st.selectbox(
        "Choose consultation",
        list(
            CONSULTATION_PRICES.keys()
        ),
        key="consultation_duration",
    )

    name = st.text_input(
        "Your name",
        max_chars=100,
        key="consultation_name",
    )

    contact = st.text_input(
        "Email / preferred contact",
        max_chars=200,
        key="consultation_contact",
    )

    topic = st.text_area(
        "Topic / question",
        max_chars=2000,
        placeholder=(
            "Briefly describe what you want to discuss..."
        ),
        key="consultation_topic",
    )

    payment_method = st.selectbox(
        "Payment method",
        [
            "Easypaisa",
            "International Payment",
            "Other / To be discussed",
        ],
        key="consultation_payment_method",
    )

    payment_reference = st.text_input(
        "Payment reference / transaction ID",
        max_chars=200,
        key="consultation_payment_reference",
    )

    if payment_method == "Easypaisa":

        if EASYPAISA_NUMBER:

            st.info(
                f"Easypaisa payment number: {EASYPAISA_NUMBER}"
            )

        else:

            st.info(
                "Easypaisa payment details will appear here "
                "after official merchant/API configuration."
            )

    elif payment_method == "International Payment":

        if INTERNATIONAL_PAYMENT_URL:

            st.markdown(
                f"[🌍 Open International Payment Page]({INTERNATIONAL_PAYMENT_URL})"
            )

        else:

            st.info(
                "International payment link is not configured yet."
            )

    st.divider()

    if st.button(
        "📩 Submit Consultation Request",
        type="primary",
        use_container_width=True,
        key="submit_consultation_request",
    ):

        if not name.strip():

            st.error(
                "Please enter your name."
            )

        elif not contact.strip():

            st.error(
                "Please enter your contact information."
            )

        elif not topic.strip():

            st.error(
                "Please enter the consultation topic."
            )

        else:

            user_id = current_user_id()

            payload = {
                "user_id": user_id,
                "name": clean_text(
                    name,
                    100,
                ),
                "contact": clean_text(
                    contact,
                    200,
                ),
                "topic": clean_text(
                    topic,
                    2000,
                ),
                "duration": selected,
                "payment_method": payment_method,
                "payment_reference": clean_text(
                    payment_reference,
                    200,
                ),
                "payment_status": "Pending verification",
            }

            db_insert(
                "consultation_requests",
                payload,
            )

            st.success(
                "Consultation request submitted. "
                "Payment status is pending verification."
            )

            st.info(
                "Automatic Easypaisa verification requires an "
                "official merchant/API integration. Do not treat "
                "a manually entered transaction ID as proof of payment."
            )


# ============================================================
# PROGRESS
# ============================================================

def page_progress():

    st.title("📈 My Progress")

    st.caption(
        "Your NEUROLENS learning and interaction overview."
    )

    lab_results = (
        st.session_state.get(
            "lab_results",
            [],
        )
    )

    exercise_results = (
        st.session_state.get(
            "exercise_scores",
            [],
        )
    )

    puzzle_moves = (
        st.session_state.get(
            "puzzle_moves",
            0,
        )
    )

    ai_count = (
        st.session_state.get(
            "ai_requests",
            0,
        )
    )

    research_notes = (
        st.session_state.get(
            "research_notes",
            [],
        )
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Lab Experiments",
            len(lab_results),
        )

    with col2:

        st.metric(
            "Brain Exercises",
            len(exercise_results),
        )

    with col3:

        st.metric(
            "AI Requests",
            ai_count,
        )

    with col4:

        st.metric(
            "Research Notes",
            len(research_notes),
        )

    st.divider()

    # --------------------------------------------------------
    # SCORES
    # --------------------------------------------------------

    if exercise_results:

        st.subheader(
            "🎯 Exercise Scores"
        )

        if pd is not None:

            df = pd.DataFrame(
                exercise_results
            )

            if (
                "exercise" in df.columns
                and "score" in df.columns
            ):

                if px is not None:

                    fig = px.bar(
                        df,
                        x="exercise",
                        y="score",
                        title="Recent Exercise Performance",
                    )

                    fig.update_layout(
                        yaxis_range=[
                            0,
                            100,
                        ]
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                    )

    # --------------------------------------------------------
    # LAB RESULTS
    # --------------------------------------------------------

    if lab_results:

        st.subheader(
            "🧪 Lab History"
        )

        for result in reversed(
            lab_results[-10:]
        ):

            st.markdown(
                f"""
                <div class="nl-card">

                    <b>
                        {result.get("experiment", "Experiment")}
                    </b>

                    <br>

                    Score:
                    {result.get("score", 0):.0f}/100

                    <br>

                    <span class="small-muted">
                        {result.get("observations", "")}
                    </span>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # ACHIEVEMENTS
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🏆 Achievements"
    )

    achievements = []

    if len(lab_results) >= 1:

        achievements.append(
            "🧪 First Lab Experiment"
        )

    if len(exercise_results) >= 1:

        achievements.append(
            "🎯 First Brain Challenge"
        )

    if len(research_notes) >= 1:

        achievements.append(
            "🔬 First Research Note"
        )

    if ai_count >= 5:

        achievements.append(
            "🤖 AI Explorer"
        )

    if st.session_state.get(
        "puzzle_completed",
        False,
    ):

        achievements.append(
            "🧩 Puzzle Solver"
        )

    if achievements:

        for achievement in achievements:

            st.success(
                achievement
            )

    else:

        st.info(
            "Complete activities to unlock achievements."
        )


# ============================================================
# SECURITY & PRIVACY CENTER
# ============================================================

def page_security():

    st.title("🛡️ Security & Privacy Center")

    st.caption(
        "How NEUROLENS handles security, AI and user data."
    )

    sections = {
        "🔑 API Key Protection": [
            "Gemini API credentials should be stored only in Streamlit Secrets.",
            "Never paste your API key into public GitHub code.",
            "Do not place service-role Supabase keys in frontend code.",
        ],
        "🧼 Input Protection": [
            "User text is length-limited before being sent to AI or storage.",
            "AI prompts explicitly restrict unsupported claims.",
            "User-generated content should be treated as untrusted input.",
        ],
        "🤖 AI Safety": [
            "AI output can be incorrect.",
            "AI mood/face/voice features are probabilistic estimates.",
            "NEUROLENS does not claim to read minds.",
            "AI features do not diagnose medical or psychiatric conditions.",
        ],
        "🔐 Private Ayna": [
            "Private session PINs use salted PBKDF2-HMAC-SHA256.",
            "Never reuse a banking or payment PIN.",
            "Session privacy depends on the security of the device and account.",
        ],
        "💳 Payment Security": [
            "Payment references are treated as unverified until confirmed.",
            "Automatic Easypaisa verification requires official merchant/API integration.",
            "Never ask users to send passwords, OTPs or banking PINs.",
        ],
        "🧠 Research Data": [
            "Educational tasks should not be presented as clinical measurements.",
            "Simulated EEG/neural visualizations are conceptual unless real validated hardware/data is explicitly connected.",
        ],
    }

    for title, bullets in sections.items():

        with st.expander(
            title,
            expanded=False,
        ):

            for bullet in bullets:

                st.write(
                    "• " + bullet
                )

    st.divider()

    st.subheader(
        "⚠️ Important Limitations"
    )

    st.write(
        """
        NEUROLENS is an educational and research-oriented
        interactive platform. AI-generated interpretations,
        behavioural tasks and self-reported information should
        not be treated as definitive measurements of cognition,
        personality, emotion, mental health or brain activity.
        """
    )


# ============================================================
# SETTINGS
# ============================================================

def page_settings():

    st.title("⚙️ Settings")

    st.caption(
        "Configure your NEUROLENS experience."
    )

    st.subheader(
        "🌐 Language"
    )

    st.selectbox(
        "Interface language",
        [
            "English",
        ],
        key="settings_language",
    )

    st.subheader(
        "🤖 AI Model"
    )

    st.selectbox(
        "Gemini model",
        [
            GEMINI_MODEL,
        ],
        key="settings_ai_model",
    )

    st.caption(
        "Current configured model: "
        + GEMINI_MODEL
    )

    st.subheader(
        "📊 AI Usage"
    )

    st.metric(
        "AI requests this session",
        st.session_state.ai_requests,
    )

    st.caption(
        f"Session AI limit: {AI_SESSION_LIMIT}"
    )

    st.subheader(
        "💳 Payment Configuration"
    )

    if EASYPAISA_NUMBER:

        st.success(
            "Easypaisa configuration detected."
        )

    else:

        st.info(
            "Easypaisa merchant configuration is not active."
        )

    if INTERNATIONAL_PAYMENT_URL:

        st.success(
            "International payment link detected."
        )

    else:

        st.info(
            "International payment link is not configured."
        )

    st.divider()

    st.subheader(
        "🧹 Reset Session Progress"
    )

    if st.button(
        "Reset Local Progress",
        use_container_width=True,
        key="reset_local_progress",
    ):

        keys_to_reset = [
            "lab_results",
            "lab_history",
            "exercise_scores",
            "research_notes",
            "ayna_messages",
            "private_messages",
            "voice_result",
            "face_result",
            "lab_result",
            "brain_system_answer",
        ]

        for key in keys_to_reset:

            if key in st.session_state:

                if isinstance(
                    st.session_state[key],
                    list,
                ):

                    st.session_state[key] = []

                elif isinstance(
                    st.session_state[key],
                    str,
                ):

                    st.session_state[key] = ""

                else:

                    st.session_state[key] = None

        st.session_state.ai_requests = 0

        st.success(
            "Local session progress reset."
        )

        st.rerun()


# ============================================================
# ACCOUNT
# ============================================================

def page_account():

    st.title("👤 Account")

    user = (
        st.session_state.get(
            "user",
            None,
        )
    )

    if not user:

        st.info(
            "You are currently using NEUROLENS without a signed-in account."
        )

        if st.button(
            "🔐 Go to Account Login",
            type="primary",
            use_container_width=True,
            key="account_go_login",
        ):

            st.session_state.page = "Account"

            st.rerun()

        return

    email = ""

    try:

        email = user.email or ""

    except Exception:

        email = ""

    st.markdown(
        f"""
        <div class="nl-card">

            <h3>
                👋 Welcome
            </h3>

            <p>
                {email}
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader(
        "👤 Profile"
    )

    name = st.text_input(
        "Display name",
        value=st.session_state.profile_name,
        max_chars=80,
        key="account_name",
    )

    bio = st.text_area(
        "Bio",
        value=st.session_state.profile_bio,
        max_chars=500,
        key="account_bio",
    )

    if st.button(
        "💾 Save Account Profile",
        type="primary",
        use_container_width=True,
        key="save_account_profile",
    ):

        st.session_state.profile_name = clean_text(
            name,
            80,
        )

        st.session_state.profile_bio = clean_text(
            bio,
            500,
        )

        user_id = current_user_id()

        if user_id:

            db_insert(
                "profiles",
                {
                    "id": user_id,
                    "display_name": st.session_state.profile_name,
                    "bio": st.session_state.profile_bio,
                },
            )

        st.success(
            "Profile updated."
        )

    st.divider()

    if st.button(
        "🚪 Log Out",
        use_container_width=True,
        key="account_logout",
    ):

        logout_user()


# ============================================================
# FINAL NAVIGATION
# ============================================================

def render_main_navigation():

    page = st.session_state.get(
        "page",
        "NeuroWorld",
    )

    if page == "NeuroWorld":

        page_neuroworld()

    elif page == "Welcome":

        page_welcome()

    elif page == "Cognitive Lab":

        page_lab()

    elif page == "Brain Journey":

        page_brain_journey()

    elif page == "Brain Puzzle":

        page_puzzle()

    elif page == "Brain Challenges":

        page_challenges()

    elif page == "Ask Ayna":

        page_ask_ayna()

    elif page == "AI Mood & Behaviour":

        page_mood()

    elif page == "Research World":

        page_research()

    elif page == "Private Ayna":

        page_private()

    elif page == "NeuroSocial":

        page_social()

    elif page == "Behaviour Decoding":

        page_consultation()

    elif page == "My Progress":

        page_progress()

    elif page == "Security & Privacy":

        page_security()

    elif page == "Settings":

        page_settings()

    elif page == "Account":

        page_account()

    else:

        st.session_state.page = "NeuroWorld"

        page_neuroworld()


# ============================================================
# FINAL SIDEBAR
# ============================================================

def render_sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:10px 0 18px 0;
            ">

                <div style="
                    font-size:42px;
                ">
                    🧠
                </div>

                <h2 style="
                    margin:0;
                ">
                    NEUROLENS
                </h2>

                <div class="small-muted">
                    Explore cognition, behavior & the brain
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        navigation = [
            (
                "🌍",
                "NeuroWorld",
            ),
            (
                "🧪",
                "Cognitive Lab",
            ),
            (
                "🧠",
                "Brain Journey",
            ),
            (
                "🧩",
                "Brain Puzzle",
            ),
            (
                "🎯",
                "Brain Challenges",
            ),
            (
                "🤖",
                "Ask Ayna",
            ),
            (
                "🎭",
                "AI Mood & Behaviour",
            ),
            (
                "🔬",
                "Research World",
            ),
            (
                "🔐",
                "Private Ayna",
            ),
            (
                "🌐",
                "NeuroSocial",
            ),
            (
                "🧩",
                "Behaviour Decoding",
            ),
            (
                "📈",
                "My Progress",
            ),
            (
                "🛡️",
                "Security & Privacy",
            ),
            (
                "⚙️",
                "Settings",
            ),
            (
                "👤",
                "Account",
            ),
        ]

        for icon, label in navigation:

            if st.button(
                f"{icon} {label}",
                use_container_width=True,
                key=f"nav_{label}",
            ):

                st.session_state.page = label

                st.rerun()

        st.divider()

        if current_user_id():

            st.success(
                "🟢 Account connected"
            )

        else:

            st.info(
                "🔵 Guest mode"
            )

        st.caption(
            "NEUROLENS is an educational cognitive-neuroscience platform."
        )


# ============================================================
# FINAL APP ENTRY
# ============================================================

def main():

    # Safety initialization.
    if "page" not in st.session_state:

        st.session_state.page = "NeuroWorld"

    render_sidebar()

    render_main_navigation()


# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":

    main()


# ============================================================
# NEUROLENS — END OF APP
# ============================================================

