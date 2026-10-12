import os
import re
import time
import json
import base64
import hashlib
import random
import secrets
from datetime import date
from urllib.request import Request, urlopen

import streamlit as st
from PIL import Image

try:
    import numpy as np
except Exception:
    np = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from google import genai
except Exception:
    genai = None

try:
    from supabase import create_client
except Exception:
    create_client = None


# ============================================================
# NEUROLENS
# Explore cognition, behavior & the brain
# Creator: Ayna Jaffri
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"
AI_SESSION_LIMIT = 20


# ============================================================
# CONFIGURATION & SECRETS
# ============================================================

def secret(name, default=""):
    try:
        value = st.secrets.get(
            name,
            os.getenv(name, default),
        )
    except Exception:
        value = os.getenv(name, default)

    return str(
        value if value is not None else default
    ).strip()


GEMINI_API_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

SUPABASE_URL = secret("SUPABASE_URL")
SUPABASE_KEY = secret("SUPABASE_KEY")

EASYPAISA_NAME = secret(
    "EASYPAISA_NAME",
    CREATOR,
)
EASYPAISA_NUMBER = secret("EASYPAISA_NUMBER")
INTERNATIONAL_PAYMENT_URL = secret(
    "INTERNATIONAL_PAYMENT_URL"
)
PAYMENT_ADMIN_KEY = secret("PAYMENT_ADMIN_KEY")

GEMINI = None

if genai and GEMINI_API_KEY:
    try:
        GEMINI = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception:
        GEMINI = None


# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource(show_spinner=False)
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    if create_client is None:
        return None

    try:
        return create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception:
        return None


SUPABASE = get_supabase()


def save_supabase(table, data):
    if SUPABASE is None:
        return False

    try:
        SUPABASE.table(table).insert(
            data
        ).execute()
        return True
    except Exception:
        return False


# ============================================================
# ASSET PATHS
# ============================================================

ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

ASSETS = os.path.join(
    ROOT,
    "assets",
)


def find_asset(*names):
    for name in names:
        candidates = [
            os.path.join(ASSETS, name),
            os.path.join(ROOT, name),
        ]

        for path in candidates:
            if os.path.isfile(path):
                return path

    return None


BRAIN_IMAGE = find_asset(
    "brain.png",
    "brain.jpg",
    "brain.jpeg",
)

AYNA_ROBOT = find_asset(
    "ayna_robot.png",
    "ayna_robot.jpg",
    "ayna_robot.jpeg",
)

REBOOT_VIDEO = find_asset(
    "ayna_reboot_voiced.mp4",
    "ayna_reboot_voiced_faster_louder.mp4",
    "ayna_reboot.mp4",
)

LAB_VIDEO = find_asset(
    "cognitive_lab_brain.mp4",
)

BRAIN_ANIMATION = find_asset(
    "brain_animation.mp4",
)


def image_to_base64(path):
    if not path or not os.path.isfile(path):
        return ""

    try:
        with open(path, "rb") as file:
            return base64.b64encode(
                file.read()
            ).decode("utf-8")
    except Exception:
        return ""


# ============================================================
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(40,110,170,0.35),
            transparent 32%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(80,60,180,0.22),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #050b14 0%,
            #081625 48%,
            #07101d 100%
        );
}

.block-container {
    max-width: 1450px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    letter-spacing: -0.02em;
}

.nl-hero {
    padding: 28px;
    border-radius: 26px;
    border: 1px solid rgba(120,180,230,0.28);
    background:
        linear-gradient(
            135deg,
            rgba(19,55,88,0.94),
            rgba(13,25,47,0.96)
        );
    margin-bottom: 20px;
}

.nl-hero p {
    color: #b9d7ef;
    font-size: 1.05rem;
}

.nl-card {
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(110,165,210,0.22);
    background: rgba(12,31,52,0.82);
    margin: 10px 0;
}

.nl-world {
    min-height: 390px;
    border-radius: 30px;
    overflow: hidden;
    position: relative;
    border: 1px solid rgba(130,190,240,0.30);
    background:
        radial-gradient(
            circle at 50% 42%,
            rgba(77,170,255,0.24),
            transparent 25%
        ),
        linear-gradient(
            135deg,
            #081a2b,
            #0b1225 50%,
            #100d26
        );
}

.nl-world-title {
    position: absolute;
    top: 22px;
    left: 25px;
    font-weight: 700;
    font-size: 1.05rem;
}

.nl-brain {
    position: absolute;
    left: 50%;
    top: 45%;
    transform: translate(-50%, -50%);
    font-size: 8rem;
    filter: drop-shadow(
        0 0 25px rgba(100,200,255,0.65)
    );
    animation: nlFloat 3s ease-in-out infinite;
}

.nl-robot {
    position: absolute;
    right: 12%;
    bottom: 25px;
    font-size: 5rem;
    filter: drop-shadow(
        0 0 18px rgba(180,150,255,0.55)
    );
}

@keyframes nlFloat {
    0%, 100% {
        transform: translate(-50%, -50%);
    }
    50% {
        transform: translate(-50%, -56%);
    }
}

.nl-orb {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    margin: 25px auto;
    background:
        radial-gradient(
            circle at 35% 30%,
            #ffffff,
            #8bdcff 18%,
            #6075ff 52%,
            #332267 100%
        );
    box-shadow:
        0 0 30px rgba(105,190,255,0.65),
        0 0 80px rgba(90,100,255,0.25);
}

.nl-stage {
    min-height: 230px;
    border-radius: 22px;
    border: 1px solid rgba(100,170,220,0.25);
    background:
        radial-gradient(
            circle,
            rgba(50,110,160,0.35),
            rgba(5,15,28,0.96)
        );
    display: flex;
    align-items: center;
    justify-content: center;
}

.nl-small {
    color: #9eb8ce;
    font-size: 0.9rem;
}

.nl-label {
    font-size: 0.78rem;
    color: #8fb4d0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.nl-stat {
    text-align: center;
    padding: 14px;
    border-radius: 16px;
    background: rgba(12,29,48,0.8);
    border: 1px solid rgba(110,165,210,0.20);
}

@media (max-width: 700px) {
    .nl-hero {
        padding: 18px;
    }
    .nl-brain {
        font-size: 5rem;
    }
    .nl-robot {
        font-size: 3rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SAFE HTML HELPERS
# ============================================================

import html


def safe_text(value):
    return html.escape(str(value))


def html_card(title, body):
    return f"""
    <div class="nl-card">
        <h3>{safe_text(title)}</h3>
        <div>{body}</div>
    </div>
    """


# ============================================================
# PROGRESS
# ============================================================

def fresh_progress():
    return {
        "experiments": 0,
        "puzzles": 0,
        "challenges": 0,
        "research": 0,
        "ai_requests": 0,
        "accuracy": 0,
        "best_reaction_ms": None,
    }


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "page": "Welcome",
    "language": "English",

    "messages": [],
    "private_messages": [],

    "ai_requests": 0,
    "ai_cache": {},

    "progress": fresh_progress(),

    "experiment_history": [],
    "puzzle_history": [],
    "challenge_history": [],
    "research_history": [],

    "lab_character": "Ayna",
    "lab_equipment": "Neural Scanner",
    "lab_experiment": "Attention & Response",

    "games_completed": 0,
    "achievements": [],

    "mood_result": None,
    "voice_result": None,

    "healing_entries": [],
    "healing_goals": [],
    "memory_map_items": [],
    "behaviour_records": [],

    "puzzle_grid": 3,
    "puzzle_moves": 0,
    "puzzle_completed": False,
    "puzzle_tiles": [],

    "research_results": [],
    "research_notes": [],

    "private_unlocked": False,
    "private_pin_hash": "",

    "social_username": "",
    "social_target": "",
    "social_streak": 0,

    "eye_samples": [],
    "eeg_history": [],

    "last_error": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def add_achievement(name):
    if name not in st.session_state.achievements:
        st.session_state.achievements.append(name)


# ============================================================
# BRAIN CONCEPTS
# ============================================================

BRAIN_CONCEPTS = [
    {
        "name": "Neuron",
        "emoji": "🧠",
        "image": [
            "neuron.png",
            "neuron.jpg",
            "neuron.gif",
        ],
        "description": (
            "A neuron is a specialized cell that "
            "receives, integrates and communicates "
            "information through electrical and "
            "chemical signalling."
        ),
        "focus": "Cellular communication",
    },
    {
        "name": "Synapse",
        "emoji": "🔗",
        "image": [
            "synapse.png",
            "synapse.jpg",
            "synapse.gif",
        ],
        "description": (
            "A synapse is a communication point "
            "where one neuron influences another "
            "neuron or target cell."
        ),
        "focus": "Neuron-to-neuron communication",
    },
    {
        "name": "Neural Signaling",
        "emoji": "⚡",
        "image": [
            "neural_signaling.gif",
            "neural_signaling.png",
            "neural_signaling.mp4",
        ],
        "description": (
            "Neural signalling involves coordinated "
            "electrical and chemical processes that "
            "allow information to move through neural "
            "circuits."
        ),
        "focus": "Information transmission",
    },
    {
        "name": "Prefrontal Cortex",
        "emoji": "🎯",
        "image": [
            "prefrontal_cortex.png",
            "prefrontal_cortex.jpg",
        ],
        "description": (
            "The prefrontal cortex participates in "
            "planning, working memory, cognitive "
            "control and goal-directed behaviour."
        ),
        "focus": "Planning and cognitive control",
    },
    {
        "name": "Hippocampus",
        "emoji": "🧩",
        "image": ["hippocampus.png", "hippocampus.jpg"],
        "description": (
            "The hippocampus supports the formation "
            "and organization of episodic memories "
            "and spatial learning."
        ),
        "focus": "Memory and spatial learning",
    },
    {
        "name": "Striatum",
        "emoji": "🔄",
        "image": ["striatum.png", "striatum.jpg"],
        "description": (
            "The striatum participates in action "
            "selection, reinforcement learning and "
            "habit-related processes."
        ),
        "focus": "Action and reward learning",
    },
    {
        "name": "Anterior Cingulate Cortex",
        "emoji": "🧭",
        "image": ["acc.png", "acc.jpg"],
        "description": (
            "The anterior cingulate cortex contributes "
            "to conflict monitoring, effort allocation "
            "and aspects of emotion and cognition."
        ),
        "focus": "Monitoring and control",
    },
]


# ============================================================
# END OF PART 1
# ============================================================

# ============================================================
# PART 2 — CORE HELPERS, AI & NEUROLENS WORLD
# ============================================================

# ------------------------------------------------------------
# SAFE SESSION HELPERS
# ------------------------------------------------------------

def ensure_list(key):
    value = st.session_state.get(key)

    if not isinstance(value, list):
        value = []
        st.session_state[key] = value

    return value


def record_progress(category, details=None):
    progress = st.session_state.progress

    if category in progress:
        progress[category] = (
            int(progress.get(category, 0)) + 1
        )

    history_key = {
        "experiments": "experiment_history",
        "puzzles": "puzzle_history",
        "challenges": "challenge_history",
        "research": "research_history",
    }.get(category)

    if history_key:
        ensure_list(history_key).append({
            "date": str(date.today()),
            "details": details or {},
        })


def save_health_event(event, status, details=""):
    ensure_list("health_log").append({
        "date": str(date.today()),
        "event": str(event),
        "status": str(status),
        "details": str(details),
    })


def get_asset_image(*names):
    path = find_asset(*names)

    if path:
        try:
            st.image(path, use_container_width=True)
            return True
        except Exception:
            pass

    return False


def show_hero(title, subtitle, emoji="🧠"):
    st.markdown(
        f"""
        <div class="nl-hero">
            <div style="font-size:2.2rem">
                {emoji}
            </div>
            <h1>{safe_text(title)}</h1>
            <p>{safe_text(subtitle)}</p>
            <div class="nl-small">
                Explore cognition, behavior & the brain
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_notice(message, kind="info"):
    if kind == "success":
        st.success(message)
    elif kind == "warning":
        st.warning(message)
    elif kind == "error":
        st.error(message)
    else:
        st.info(message)


# ------------------------------------------------------------
# AI CONNECTION
# ------------------------------------------------------------

AI_SYSTEM_PROMPT = """
You are Ayna, the AI guide inside NEUROLENS.

Your focus is cognitive neuroscience, learning, attention,
memory, decision-making, behavior and brain science.

Rules:
- Explain scientific concepts in clear, accessible language.
- Distinguish established evidence from hypotheses.
- Never diagnose mental or neurological disorders.
- Never claim that a game measures actual brain activity.
- Treat self-reports as self-reports, not clinical measurements.
- Never claim to detect hidden emotions with certainty.
- Treat voice-based mood interpretation as an uncertain estimate.
- Do not claim to recover forgotten memories or verify memories.
- For distress, respond supportively and suggest appropriate
  professional or trusted-person support when needed.
- Never present a simulation as a real EEG recording.
- Never invent citations or research findings.
- Protect personal information and encourage privacy.
- Do not claim to be a human researcher or therapist.
"""


def ask_ai(prompt, system_prompt=None):
    prompt = str(prompt or "").strip()

    if not prompt:
        return (
            "Please enter a question so Ayna can help.",
            "empty",
        )

    if st.session_state.ai_requests >= AI_SESSION_LIMIT:
        return (
            "Your AI session limit has been reached. "
            "You can continue using the local NEUROLENS tools.",
            "limit",
        )

    if GEMINI is None:
        return (
            "Ayna AI is not connected yet. Add GEMINI_API_KEY "
            "to Streamlit Secrets. Local experiments and "
            "learning tools can still be used.",
            "offline",
        )

    cache_key = hashlib.sha256(
        (
            str(system_prompt or AI_SYSTEM_PROMPT)
            + prompt
        ).encode("utf-8")
    ).hexdigest()

    cached = st.session_state.ai_cache.get(cache_key)

    if cached:
        return cached, "cache"

    try:
        st.session_state.ai_requests += 1

        response = GEMINI.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                (system_prompt or AI_SYSTEM_PROMPT)
                + "\n\nUser request:\n"
                + prompt
            ),
        )

        answer = (
            getattr(response, "text", None)
            or ""
        ).strip()

        if not answer:
            answer = (
                "Ayna could not generate a response "
                "for that request."
            )

        st.session_state.ai_cache[cache_key] = answer

        st.session_state.progress["ai_requests"] = (
            st.session_state.ai_requests
        )

        return answer, "ai"

    except Exception as exc:
        st.session_state.last_error = str(exc)

        return (
            "Ayna could not complete the AI request "
            "right now. You can continue using the "
            "local NEUROLENS tools.",
            "error",
        )


def ask_ai_audio(audio_file, instruction):
    if GEMINI is None:
        return (
            "Voice AI requires GEMINI_API_KEY "
            "in Streamlit Secrets.",
            "offline",
        )

    if st.session_state.ai_requests >= AI_SESSION_LIMIT:
        return "AI session limit reached.", "limit"

    try:
        audio_bytes = audio_file.getvalue()

        if not audio_bytes:
            return "The audio recording is empty.", "empty"

        # Use the actual MIME type where available.
        mime_type = (
            getattr(audio_file, "type", None)
            or "audio/wav"
        )

        st.session_state.ai_requests += 1

        response = GEMINI.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(
                            audio_bytes
                        ).decode("utf-8"),
                    }
                },
                AI_SYSTEM_PROMPT
                + "\n\n"
                + str(instruction),
            ],
        )

        answer = (
            getattr(response, "text", None)
            or "No voice interpretation was returned."
        ).strip()

        st.session_state.progress["ai_requests"] = (
            st.session_state.ai_requests
        )

        return answer, "ai"

    except Exception as exc:
        st.session_state.last_error = str(exc)

        return (
            "Ayna could not process this voice "
            "recording right now.",
            "error",
        )


# ------------------------------------------------------------
# NEUROLENS WORLD VISUAL
# ------------------------------------------------------------

def neuro_world_visual():
    brain_visual = "🧠"

    if BRAIN_IMAGE:
        brain_visual = (
            '<img src="data:image/png;base64,'
            + image_to_base64(BRAIN_IMAGE)
            + '" alt="Brain illustration" '
            + 'style="max-width:240px;'
            + 'max-height:220px;object-fit:contain;">'
        )

    if AYNA_ROBOT:
        extension = os.path.splitext(AYNA_ROBOT)[1].lower()

        if extension in (".jpg", ".jpeg"):
            mime = "image/jpeg"
        else:
            mime = "image/png"

        robot_visual = (
            '<img src="data:'
            + mime
            + ';base64,'
            + image_to_base64(AYNA_ROBOT)
            + '" alt="Ayna robot" '
            + 'style="max-width:150px;'
            + 'max-height:180px;object-fit:contain;">'
        )
    else:
        robot_visual = "🤖"

    st.markdown(
        f"""
        <div class="nl-world">
            <div class="nl-world-title">
                NEUROLENS WORLD
            </div>

            <div class="nl-brain">
                {brain_visual}
            </div>

            <div class="nl-robot">
                {robot_visual}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# WELCOME / REBOOT
# ------------------------------------------------------------

def page_welcome():
    show_hero(
        "Welcome to NEUROLENS",
        "Explore cognition, behavior & the brain.",
        "🧠",
    )

    if REBOOT_VIDEO:
        st.video(REBOOT_VIDEO)
    else:
        st.markdown(
            """
            <div class="nl-stage">
                <div style="text-align:center;padding:24px">
                    <div class="nl-orb"></div>
                    <h2>Meet Ayna</h2>
                    <p>Your guide to the world of cognition.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write(
        "Welcome to NeuroLens! I'm Ayna. "
        "Let's explore the brain, behaviour, and cognition together."
    )

    language = st.selectbox(
        "Choose your language",
        ["English", "Roman English"],
        key="language",
    )

    if st.button(
        "🚀 Enter NeuroLens",
        use_container_width=True,
    ):
        st.session_state.page = "NeuroWorld"
        st.rerun()


# ------------------------------------------------------------
# NEUROLENS WORLD PAGE
# ------------------------------------------------------------

def page_neuroworld():
    show_hero(
        "NeuroLens World",
        "A space to explore cognition, learning and behavior.",
        "🌌",
    )

    neuro_world_visual()

    st.markdown(
        """
        <div class="nl-card">
            <h3>🧭 Explore the Lab</h3>
            <p>
                Run cognitive tasks, explore brain concepts,
                reflect on your experiences and build a
                personal learning history.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)

    shortcuts = [
        ("🧪 Cognitive Lab", "Interactive Lab"),
        ("🧠 Brain Journey", "Brain Journey"),
        ("🧩 Brain Puzzle", "Brain Puzzle"),
        ("💬 Ask Ayna", "Ask Ayna"),
        ("💜 Healing", "Healing & Insight"),
        ("📚 Research", "Research Book"),
    ]

    for index, (label, destination) in enumerate(shortcuts):
        with cols[index % 3]:
            if st.button(
                label,
                key=f"world_shortcut_{index}",
                use_container_width=True,
            ):
                st.session_state.page = destination
                st.rerun()


# ------------------------------------------------------------
# END OF PART 2
# ------------------------------------------------------------

