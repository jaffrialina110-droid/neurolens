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

# =========================
# PART 3 — INTERACTIVE NEUROSCIENCE LAB
# =========================

EXPERIMENTS = {
    "Attention & Response": {
        "description": "Find the target letter as quickly and accurately as possible.",
        "purpose": "This task explores visual attention and response selection."
    },
    "Memory Sequence": {
        "description": "Remember the sequence and reproduce it.",
        "purpose": "This task explores short-term sequence recall."
    },
    "Decision & Reward": {
        "description": "Choose between a smaller immediate reward and a larger delayed reward.",
        "purpose": "This task explores choices involving delay and reward."
    },
    "Stroop Control": {
        "description": "Identify the displayed word's ink colour, not the word itself.",
        "purpose": "This task explores interference and response control."
    },
    "Reaction Time": {
        "description": "Respond when the target appears.",
        "purpose": "This task records your response time in this simple task."
    }
}


def page_interactive_lab():
    show_hero(
        "Interactive Neuroscience Lab",
        "Explore attention, memory, decision-making and response behaviour."
    )

    characters = ["Ayna", "Nova", "Mira", "Ray", "Zara"]
    equipment = [
        "Neural Scanner — educational simulation",
        "Reaction Console",
        "Memory Chamber",
        "Attention Monitor",
        "Decision & Reward Console"
    ]

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.lab_character = st.selectbox(
            "Choose your lab guide",
            characters,
            index=(
                characters.index(st.session_state.lab_character)
                if st.session_state.lab_character in characters else 0
            ),
            key="lab_character_select"
        )

    with col2:
        st.session_state.lab_equipment = st.selectbox(
            "Choose equipment",
            equipment,
            key="lab_equipment_select"
        )

    st.markdown(
        f"### 🧑‍🔬 Guide: {safe_text(st.session_state.lab_character)}"
    )
    st.caption(
        "Educational simulation only. No brain activity is measured by these tasks."
    )

    experiment_names = list(EXPERIMENTS.keys())

    selected = st.selectbox(
        "Select an experiment",
        experiment_names,
        index=(
            experiment_names.index(st.session_state.lab_experiment)
            if st.session_state.lab_experiment in experiment_names else 0
        ),
        key="lab_experiment_select"
    )

    st.session_state.lab_experiment = selected
    details = EXPERIMENTS[selected]

    html_card(
        selected,
        details["description"],
        "LAB EXPERIMENT"
    )

    st.write("**What this task explores:**", details["purpose"])

    if selected == "Attention & Response":
        run_attention_experiment()

    elif selected == "Memory Sequence":
        run_memory_experiment()

    elif selected == "Decision & Reward":
        run_decision_experiment()

    elif selected == "Stroop Control":
        run_stroop_experiment()

    elif selected == "Reaction Time":
        run_reaction_experiment()

    st.divider()
    st.subheader("Recent experiment history")

    history = st.session_state.experiment_history

    if history:
        for item in reversed(history[-5:]):
            st.write(
                f"• {item.get('experiment', 'Experiment')} — "
                f"{item.get('result', 'Completed')}"
            )
    else:
        st.info("Complete an experiment to start your history.")


def store_experiment(name, result, accuracy=None, reaction_ms=None):
    entry = {
        "experiment": name,
        "result": str(result),
        "accuracy": accuracy,
        "reaction_ms": reaction_ms,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    st.session_state.experiment_history.append(entry)
    record_progress("experiments")

    if accuracy is not None:
        st.session_state.progress["accuracy"] = accuracy

    if reaction_ms is not None:
        current = st.session_state.progress.get("best_reaction_ms")
        if current is None or reaction_ms < current:
            st.session_state.progress["best_reaction_ms"] = reaction_ms

    st.session_state.behaviour_records.append(entry.copy())

    save_supabase("experiment_results", {
        "experiment_name": name,
        "result_text": str(result),
        "accuracy": accuracy,
        "reaction_ms": reaction_ms
    })


def run_attention_experiment():
    st.markdown("#### 🔎 Find the target")

    if "attention_target" not in st.session_state:
        st.session_state.attention_target = random.choice(["X", "K", "M", "T"])
        st.session_state.attention_options = random.sample(
            ["X", "K", "M", "T", "A", "R", "P", "S"],
            4
        )
        if st.session_state.attention_target not in st.session_state.attention_options:
            st.session_state.attention_options[
                random.randrange(4)
            ] = st.session_state.attention_target

    target = st.session_state.attention_target
    options = st.session_state.attention_options

    st.markdown(f"### Target: **{target}**")

    answer = st.radio(
        "Which option matches the target?",
        options,
        horizontal=True,
        key="attention_answer"
    )

    if st.button("Check attention answer", key="check_attention"):
        if st.session_state.get("attention_done"):
            st.info("This round is already complete. Start a new round.")
        else:
            correct = answer == target
            result = "Correct" if correct else "Incorrect"

            store_experiment(
                "Attention & Response",
                result,
                accuracy=100 if correct else 0
            )

            st.session_state.attention_done = True

            if correct:
                st.success("Correct selection!")
            else:
                st.warning(f"The target was {target}.")

            st.caption(
                "One short task cannot establish your general attention ability."
            )

    if st.button("New attention round", key="new_attention"):
        st.session_state.attention_target = random.choice(["X", "K", "M", "T"])
        st.session_state.attention_options = random.sample(
            ["X", "K", "M", "T", "A", "R", "P", "S"],
            4
        )
        if st.session_state.attention_target not in st.session_state.attention_options:
            st.session_state.attention_options[0] = st.session_state.attention_target

        st.session_state.attention_done = False
        st.rerun()


def run_memory_experiment():
    st.markdown("#### 🧠 Memory sequence")

    if "memory_sequence" not in st.session_state:
        st.session_state.memory_sequence = "".join(
            str(random.randint(1, 9)) for _ in range(5)
        )

    if not st.session_state.get("memory_started"):
        st.info(
            "Study this sequence, then enter it below. "
            "For a fair challenge, look away before submitting."
        )
        st.code(st.session_state.memory_sequence)

        if st.button("Hide sequence and begin", key="hide_memory"):
            st.session_state.memory_started = True
            st.rerun()

    else:
        answer = st.text_input(
            "Enter the sequence",
            max_chars=10,
            key="memory_answer"
        )

        if st.button("Check memory answer", key="check_memory"):
            if st.session_state.get("memory_done"):
                st.info("This round is already complete.")
            else:
                correct = (
                    answer.strip() == st.session_state.memory_sequence
                )

                store_experiment(
                    "Memory Sequence",
                    "Correct recall" if correct else "Incorrect recall",
                    accuracy=100 if correct else 0
                )

                st.session_state.memory_done = True

                if correct:
                    st.success("Sequence recalled correctly!")
                else:
                    st.warning(
                        "The sequence did not match. "
                        "This single result is not a memory diagnosis."
                    )

    if st.button("Generate new memory sequence", key="new_memory"):
        st.session_state.memory_sequence = "".join(
            str(random.randint(1, 9)) for _ in range(5)
        )
        st.session_state.memory_started = False
        st.session_state.memory_done = False
        st.rerun()


def run_decision_experiment():
    st.markdown("#### 💰 Decision & reward")

    st.write("Choose one option:")

    choice = st.radio(
        "Which reward would you choose?",
        [
            "Receive Rs 1,000 today",
            "Receive Rs 1,500 after 30 days"
        ],
        key="decision_choice"
    )

    reason = st.text_area(
        "Optional: Why did you choose it?",
        key="decision_reason",
        max_chars=500
    )

    if st.button("Save decision", key="save_decision"):
        if st.session_state.get("decision_done"):
            st.info("This decision has already been saved.")
        else:
            st.session_state.decision_done = True

            store_experiment(
                "Decision & Reward",
                choice
            )

            st.session_state.behaviour_records.append({
                "experiment": "Decision explanation",
                "result": reason.strip() or "No explanation provided",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })

            st.success("Decision recorded.")

            st.write(
                "Reflection: immediate needs, trust, uncertainty, "
                "and personal priorities can all influence choices. "
                "One answer does not define your personality."
            )

    if st.button("Reset decision", key="reset_decision"):
        st.session_state.decision_done = False
        st.rerun()


def run_stroop_experiment():
    st.markdown("#### 🎨 Stroop control task")

    colours = {
        "RED": "#ff4d4d",
        "BLUE": "#4d9dff",
        "GREEN": "#39c878",
        "YELLOW": "#f4d35e"
    }

    if "stroop_word" not in st.session_state:
        word = random.choice(list(colours.keys()))
        ink = random.choice([c for c in colours if c != word])
        st.session_state.stroop_word = word
        st.session_state.stroop_ink = ink

    word = st.session_state.stroop_word
    ink = st.session_state.stroop_ink

    st.markdown(
        f'<div style="font-size:42px;font-weight:800;'
        f'color:{colours[ink]};text-align:center;padding:18px">'
        f'{safe_text(word)}</div>',
        unsafe_allow_html=True
    )

    answer = st.radio(
        "What is the ink colour?",
        list(colours.keys()),
        horizontal=True,
        key="stroop_answer"
    )

    if st.button("Check ink colour", key="check_stroop"):
        if st.session_state.get("stroop_done"):
            st.info("This round is already complete.")
        else:
            correct = answer == ink

            store_experiment(
                "Stroop Control",
                "Correct" if correct else "Incorrect",
                accuracy=100 if correct else 0
            )

            st.session_state.stroop_done = True

            if correct:
                st.success("Correct — you identified the ink colour.")
            else:
                st.warning(f"The ink colour was {ink}.")

            st.caption(
                "This is a simplified educational task, "
                "not a clinical executive-function assessment."
            )

    if st.button("New Stroop round", key="new_stroop"):
        word = random.choice(list(colours.keys()))
        ink = random.choice([c for c in colours if c != word])
        st.session_state.stroop_word = word
        st.session_state.stroop_ink = ink
        st.session_state.stroop_done = False
        st.rerun()


def run_reaction_experiment():
    st.markdown("#### ⚡ Reaction time")

    st.write(
        "Press the button when you are ready. "
        "Then start a round and respond when the target appears."
    )

    if "reaction_ready" not in st.session_state:
        st.session_state.reaction_ready = False

    if "reaction_start_time" not in st.session_state:
        st.session_state.reaction_start_time = None

    if not st.session_state.reaction_ready:
        if st.button("Start reaction round", key="start_reaction"):
            st.session_state.reaction_start_time = time.perf_counter()
            st.session_state.reaction_ready = True
            st.rerun()

    else:
        st.success("TARGET! Press the response button now.")

        if st.button("RESPOND", key="respond_reaction"):
            start = st.session_state.reaction_start_time

            if start is not None:
                elapsed_ms = round((time.perf_counter() - start) * 1000)

                store_experiment(
                    "Reaction Time",
                    f"{elapsed_ms} ms",
                    reaction_ms=elapsed_ms
                )

                st.success(f"Recorded response: {elapsed_ms} ms")

                st.caption(
                    "This measures the time between the app's start "
                    "event and your click. It is not a laboratory-grade "
                    "reaction-time measurement."
                )

            st.session_state.reaction_ready = False
            st.session_state.reaction_start_time = None
            st.rerun()


# =========================
# BEHAVIOUR DECODING
# =========================

def page_behaviour_decoding():
    show_hero(
        "Behaviour Decoding",
        "Explore recorded task results and reflect on everyday patterns."
    )

    st.info(
        "Recorded task outcomes and AI-generated interpretations are "
        "different things. This module does not diagnose conditions "
        "or determine hidden motives."
    )

    records = st.session_state.behaviour_records

    st.subheader("1. Your recorded task results")

    if not records:
        st.write(
            "No task results recorded yet. Complete an experiment "
            "in the Interactive Neuroscience Lab first."
        )
    else:
        for index, record in enumerate(reversed(records[-20:])):
            with st.expander(
                f"{record.get('experiment', 'Task')} — "
                f"{record.get('timestamp', '')}"
            ):
                st.write("Result:", record.get("result", "Not recorded"))

                if record.get("accuracy") is not None:
                    st.write("Task accuracy:", f"{record['accuracy']}%")

                if record.get("reaction_ms") is not None:
                    st.write(
                        "Recorded click response:",
                        f"{record['reaction_ms']} ms"
                    )

    st.divider()
    st.subheader("2. Reflect on an everyday pattern")

    situation = st.text_area(
        "Situation: What happened?",
        max_chars=1200,
        key="behaviour_situation"
    )

    response = st.text_area(
        "Your response: What did you think, feel or do?",
        max_chars=1200,
        key="behaviour_response"
    )

    outcome = st.text_area(
        "Outcome: What happened afterwards?",
        max_chars=1200,
        key="behaviour_outcome"
    )

    if st.button("Save behaviour reflection", key="save_behaviour"):
        if not situation.strip() or not response.strip():
            st.warning("Please enter the situation and your response.")
        else:
            item = {
                "experiment": "Everyday behaviour reflection",
                "situation": situation.strip(),
                "response": response.strip(),
                "outcome": outcome.strip(),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            st.session_state.behaviour_records.append(item)

            save_supabase("behaviour_reflections", item)

            st.success("Reflection saved in this session.")

    st.divider()
    st.subheader("3. Explore possible patterns")

    if st.button("Generate a careful reflection", key="decode_behaviour"):
        if not situation.strip() or not response.strip():
            st.warning("Enter a situation and response first.")
        else:
            prompt = f"""
Help the user reflect on an everyday situation without diagnosing them.

Situation:
{situation.strip()}

Response:
{response.strip()}

Outcome:
{outcome.strip()}

Please:
1. Summarize the situation neutrally.
2. Separate what the user reported from possible interpretations.
3. Offer up to two possible explanations, clearly labelled as hypotheses.
4. Ask one gentle question that could help the user reflect.
5. Suggest one small, safe next step.

Do not infer a disorder, personality type, hidden motive, or trauma.
Do not claim that one example proves a recurring pattern.
"""

            result = ask_ai(prompt)

            st.markdown("### Reflection")
            st.write(result)

    st.caption(
        "Only information you choose to enter is considered. "
        "A pattern should be explored across multiple real-life examples, "
        "not concluded from a single task."
    )


# END OF PART 3

# =========================
# PART 4 — BRAIN JOURNEY
# BRAIN EXPLORER
# HEALING & PERSONAL INSIGHT
# =========================

BRAIN_JOURNEY_STEPS = [
    {
        "title": "1. Brain Regions",
        "description": (
            "Different brain regions contribute to different functions. "
            "Complex behaviours usually involve interacting brain regions."
        ),
        "details": (
            "The prefrontal cortex contributes to planning and control. "
            "The hippocampus is important for forming many kinds of memories. "
            "The striatum contributes to action selection, learning and reward."
        )
    },
    {
        "title": "2. Neural Circuits",
        "description": (
            "Brain regions communicate through networks of connected neurons."
        ),
        "details": (
            "A circuit can include multiple brain regions and pathways. "
            "Its effects depend on the connections, activity patterns and context."
        )
    },
    {
        "title": "3. Neurons",
        "description": (
            "Neurons are specialized cells that receive, process and transmit signals."
        ),
        "details": (
            "Dendrites receive many incoming signals, the cell body integrates "
            "cellular activity, and the axon carries electrical signals toward "
            "other cells."
        )
    },
    {
        "title": "4. Synapses",
        "description": (
            "Synapses are communication junctions between neurons or other cells."
        ),
        "details": (
            "At chemical synapses, neurotransmitters can be released and bind "
            "to receptors on a target cell. Their effects depend on the receptor "
            "and biological context."
        )
    },
    {
        "title": "5. Behaviour and Experience",
        "description": (
            "Neural activity participates in perception, memory, decisions, "
            "emotion and action."
        ),
        "details": (
            "Behaviour is also shaped by learning, sleep, stress, environment "
            "and social context. A single behaviour cannot reveal one specific "
            "brain mechanism with certainty."
        )
    }
]


def page_brain_journey():
    show_hero(
        "Brain Journey",
        "Explore how brain regions, circuits, neurons and synapses "
        "contribute to cognition and behaviour."
    )

    st.markdown("### Follow the biological pathway")

    step_titles = [item["title"] for item in BRAIN_JOURNEY_STEPS]

    selected_title = st.selectbox(
        "Choose a stage",
        step_titles,
        key="brain_journey_step"
    )

    selected_step = next(
        item for item in BRAIN_JOURNEY_STEPS
        if item["title"] == selected_title
    )

    html_card(
        selected_step["title"],
        selected_step["description"],
        "BRAIN JOURNEY"
    )

    st.write(selected_step["details"])

    st.markdown("### How the stages connect")
    st.markdown(
        """
        **Brain regions**
        ↓
        **Connected neural circuits**
        ↓
        **Neurons and electrical activity**
        ↓
        **Synaptic communication**
        ↓
        **Cognition, experience and behaviour**
        """
    )

    st.caption(
        "This is a simplified learning sequence, not one universal "
        "one-way pathway. Neural systems are interconnected and often "
        "operate through recurrent feedback."
    )

    st.divider()
    st.subheader("Explore a brain concept")

    concept_names = [item["name"] for item in BRAIN_CONCEPTS]

    selected_concept_name = st.selectbox(
        "Choose a concept",
        concept_names,
        key="journey_concept"
    )

    concept = next(
        item for item in BRAIN_CONCEPTS
        if item["name"] == selected_concept_name
    )

    st.markdown(f"### {safe_text(concept['name'])}")
    st.write(concept.get("description", ""))

    concept_image = get_asset_image(concept.get("image", ""))

    if concept_image is not None:
        st.image(concept_image, use_container_width=True)
    else:
        st.info(
            "No matching concept image was found in the current assets. "
            "The written explanation is still available."
        )

    if st.button(
        "Ask Ayna to explain this concept",
        key="explain_concept"
    ):
        prompt = f"""
Explain this neuroscience concept for a curious learner.

Concept: {concept.get('name', '')}
Description: {concept.get('description', '')}

Include:
- A clear definition
- How it relates to cognition or behaviour
- One everyday example
- One important scientific limitation

Do not invent research findings or claim that one brain region
fully determines a complex behaviour.
"""
        st.markdown("### Ayna's explanation")
        st.write(ask_ai(prompt))


# =========================
# BRAIN EXPLORER
# =========================

BRAIN_REGIONS = {
    "Prefrontal Cortex": {
        "function": (
            "Contributes to planning, working memory, flexible thinking "
            "and goal-directed control."
        ),
        "limitation": (
            "These functions involve distributed networks and are not "
            "exclusive to one region."
        )
    },
    "Hippocampus": {
        "function": (
            "Important for forming and organizing many kinds of memories "
            "and for aspects of spatial navigation."
        ),
        "limitation": (
            "Memory depends on several interacting brain systems."
        )
    },
    "Striatum": {
        "function": (
            "Participates in action selection, reinforcement learning "
            "and reward-related processes."
        ),
        "limitation": (
            "Different striatal circuits support different functions."
        )
    },
    "Anterior Cingulate Cortex": {
        "function": (
            "Participates in monitoring, control, motivation and "
            "processing information relevant to behaviour."
        ),
        "limitation": (
            "Its functions depend on subregion, network and task."
        )
    },
    "Amygdala": {
        "function": (
            "Contributes to learning about biologically relevant events "
            "and to aspects of emotional processing."
        ),
        "limitation": (
            "It is not simply a fear centre; its role is broader."
        )
    },
    "Thalamus": {
        "function": (
            "Supports communication between many brain systems and "
            "contributes to sensory processing and attention."
        ),
        "limitation": (
            "Different thalamic nuclei have distinct connections and roles."
        )
    }
}


def page_brain_explorer():
    show_hero(
        "Brain Explorer",
        "Explore selected brain regions and their known contributions."
    )

    region_name = st.selectbox(
        "Choose a region",
        list(BRAIN_REGIONS.keys()),
        key="brain_explorer_region"
    )

    region = BRAIN_REGIONS[region_name]

    html_card(
        region_name,
        region["function"],
        "BRAIN REGION"
    )

    st.markdown("### Scientific context")
    st.write(region["limitation"])

    st.divider()
    st.subheader("3D brain view")

    if go is not None and plotly is not None:
        import numpy as np

        u = np.linspace(0, 2 * np.pi, 45)
        v = np.linspace(0, np.pi, 30)

        x = 1.35 * np.outer(np.cos(u), np.sin(v))
        y = 1.00 * np.outer(np.sin(u), np.sin(v))
        z = 1.15 * np.outer(np.ones_like(u), np.cos(v))

        fig = go.Figure(
            data=[
                go.Surface(
                    x=x,
                    y=y,
                    z=z,
                    colorscale="Viridis",
                    showscale=False,
                    opacity=0.85
                )
            ]
        )

        fig.update_layout(
            title=(
                "Illustrative 3D shape — "
                "not an anatomical reconstruction"
            ),
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                aspectmode="data"
            ),
            margin=dict(l=0, r=0, t=50, b=0),
            height=420
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key="illustrative_brain_3d"
        )

        st.caption(
            "Rotate the shape with touch or mouse. This is a visual "
            "placeholder, not a scientifically accurate brain scan."
        )
    else:
        if BRAIN_IMAGE:
            st.image(
                BRAIN_IMAGE,
                caption="Available brain image asset",
                use_container_width=True
            )
        else:
            st.info(
                "A 3D viewer requires Plotly. Add plotly to "
                "requirements.txt to enable the illustrative 3D shape."
            )

    st.divider()
    st.subheader("Compare brain regions")

    first_region = st.selectbox(
        "First region",
        list(BRAIN_REGIONS.keys()),
        index=0,
        key="compare_region_a"
    )

    second_region = st.selectbox(
        "Second region",
        list(BRAIN_REGIONS.keys()),
        index=1,
        key="compare_region_b"
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"**{first_region}**")
        st.write(BRAIN_REGIONS[first_region]["function"])

    with col_b:
        st.markdown(f"**{second_region}**")
        st.write(BRAIN_REGIONS[second_region]["function"])

    if st.button(
        "Explain the comparison",
        key="brain_region_compare"
    ):
        prompt = f"""
Compare these two brain regions for educational purposes:

1. {first_region}: {BRAIN_REGIONS[first_region]['function']}
2. {second_region}: {BRAIN_REGIONS[second_region]['function']}

Explain their main differences, possible interactions and limitations.
Do not claim that either region works in isolation.
Do not invent specific anatomical connections if uncertain.
"""
        st.write(ask_ai(prompt))


# =========================
# HEALING & PERSONAL INSIGHT
# =========================

def page_healing_insight():
    show_hero(
        "Healing & Personal Insight",
        "A space for reflection, personal goals and small next steps."
    )

    st.info(
        "This is a self-reflection tool, not psychotherapy or a diagnostic "
        "service. Share only what you feel comfortable recording."
    )

    tab_journal, tab_timeline, tab_goals, tab_map = st.tabs(
        [
            "Personal Journal",
            "Life Timeline",
            "Goals & Progress",
            "Memory Map"
        ]
    )

    # PERSONAL JOURNAL
    with tab_journal:
        st.subheader("Personal Story Journal")

        journal_title = st.text_input(
            "Entry title",
            key="healing_journal_title",
            max_chars=120
        )

        journal_text = st.text_area(
            "Write what you would like to reflect on",
            key="healing_journal_text",
            height=180,
            max_chars=5000
        )

        journal_feeling = st.selectbox(
            "How would you describe your current feeling?",
            [
                "Not sure",
                "Calm",
                "Hopeful",
                "Sad",
                "Worried",
                "Frustrated",
                "Overwhelmed",
                "Mixed feelings"
            ],
            key="healing_journal_feeling"
        )

        if st.button(
            "Save journal entry",
            key="save_healing_journal"
        ):
            if not journal_text.strip():
                st.warning("Write something before saving.")
            else:
                entry = {
                    "title": (
                        journal_title.strip()
                        or "Personal reflection"
                    ),
                    "text": journal_text.strip(),
                    "feeling": journal_feeling,
                    "timestamp": time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }

                st.session_state.healing_entries.append(entry)

                save_supabase(
                    "healing_journal",
                    {
                        "title": entry["title"],
                        "entry_text": entry["text"],
                        "feeling": entry["feeling"]
                    }
                )

                st.success("Entry added to this session.")

        st.divider()
        st.subheader("Saved entries in this session")

        if st.session_state.healing_entries:
            for entry in reversed(st.session_state.healing_entries):
                with st.expander(
                    f"{entry.get('title', 'Reflection')} — "
                    f"{entry.get('timestamp', '')}"
                ):
                    st.write(
                        "Feeling:",
                        entry.get("feeling", "Not recorded")
                    )
                    st.write(entry.get("text", ""))
        else:
            st.caption(
                "Your saved journal entries will appear here."
            )

        st.caption(
            "Session storage alone is not permanent. Verify database "
            "access and privacy protections before storing sensitive "
            "personal information."
        )

    # LIFE TIMELINE
    with tab_timeline:
        st.subheader("Past → Present → Next Step")

        past = st.text_area(
            "Past: What experience would you like to reflect on?",
            key="timeline_past",
            max_chars=1500
        )

        present = st.text_area(
            "Present: What challenge matters now?",
            key="timeline_present",
            max_chars=1500
        )

        future = st.text_area(
            "Next: What would you like to work toward?",
            key="timeline_future",
            max_chars=1500
        )

        if st.button(
            "Build my reflection timeline",
            key="build_timeline"
        ):
            timeline = {
                "past": past.strip(),
                "present": present.strip(),
                "future": future.strip(),
                "timestamp": time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            st.session_state.memory_map_items.append(timeline)

            st.markdown("### Your timeline")

            col_past, col_now, col_next = st.columns(3)

            with col_past:
                html_card(
                    "PAST",
                    timeline["past"] or "Not entered",
                    "REFLECTION"
                )

            with col_now:
                html_card(
                    "PRESENT",
                    timeline["present"] or "Not entered",
                    "REFLECTION"
                )

            with col_next:
                html_card(
                    "NEXT STEP",
                    timeline["future"] or "Not entered",
                    "REFLECTION"
                )

            st.caption(
                "This timeline organizes what you entered. It does not "
                "prove that past events caused your current experience."
            )

    # GOALS & PROGRESS
    with tab_goals:
        st.subheader("Personal Goals")

        goal_text = st.text_input(
            "A small goal you want to work toward",
            key="healing_goal_text",
            max_chars=250
        )

        goal_deadline = st.date_input(
            "Target date",
            key="healing_goal_date"
        )

        if st.button("Add goal", key="add_healing_goal"):
            if not goal_text.strip():
                st.warning("Enter a goal first.")
            else:
                goal = {
                    "goal": goal_text.strip(),
                    "target_date": str(goal_deadline),
                    "completed": False,
                    "timestamp": time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }

                st.session_state.healing_goals.append(goal)

                save_supabase(
                    "healing_goals",
                    {
                        "goal_text": goal["goal"],
                        "target_date": goal["target_date"],
                        "completed": False
                    }
                )

                st.success("Goal added.")

        st.divider()
        st.subheader("Goal tracker")

        if not st.session_state.healing_goals:
            st.caption(
                "Add a small goal to start tracking progress."
            )
        else:
            for index, goal in enumerate(
                st.session_state.healing_goals
            ):
                st.write(
                    f"**{goal['goal']}** — "
                    f"target: {goal['target_date']}"
                )

                completed = st.checkbox(
                    "Mark as completed",
                    value=goal.get("completed", False),
                    key=f"goal_completed_{index}"
                )

                st.session_state.healing_goals[index][
                    "completed"
                ] = completed

        total_goals = len(st.session_state.healing_goals)

        completed_goals = sum(
            1 for goal in st.session_state.healing_goals
            if goal.get("completed", False)
        )

        if total_goals:
            st.progress(completed_goals / total_goals)
            st.write(
                f"Completed {completed_goals} of {total_goals} goals."
            )

        st.caption(
            "This progress reflects the goals you entered. It is not "
            "a clinical measure of recovery or mental health."
        )

    # MEMORY MAP
    with tab_map:
        st.subheader("Visual Memory Map")

        st.write(
            "Map experiences, current challenges and hopes. "
            "Add only details you want to keep."
        )

        map_label = st.text_input(
            "Map item label",
            key="memory_map_label",
            max_chars=100
        )

        map_category = st.selectbox(
            "Category",
            [
                "Important experience",
                "Current challenge",
                "Support system",
                "Personal strength",
                "Future hope"
            ],
            key="memory_map_category"
        )

        map_note = st.text_area(
            "Short note",
            key="memory_map_note",
            max_chars=1000
        )

        if st.button(
            "Add to memory map",
            key="add_memory_map"
        ):
            if not map_label.strip():
                st.warning("Add a label first.")
            else:
                item = {
                    "label": map_label.strip(),
                    "category": map_category,
                    "note": map_note.strip(),
                    "timestamp": time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }

                st.session_state.memory_map_items.append(item)
                st.success("Added to your session memory map.")

        st.divider()
        st.subheader("Your map")

        map_items = st.session_state.memory_map_items

        if not map_items:
            st.caption(
                "Your map is empty. Add an item above."
            )
        else:
            for item in map_items:
                html_card(
                    item.get(
                        "label",
                        item.get("present", "Untitled")
                    ),
                    (
                        item.get("category", "Reflection")
                        + "\n\n"
                        + item.get(
                            "note",
                            item.get("present", "")
                        )
                    ),
                    "MEMORY MAP"
                )

    # GUIDED REFLECTION
    st.divider()
    st.subheader("Guided Reflection: Why do I feel stuck?")

    stuck_context = st.text_area(
        "Describe the situation in your own words",
        key="why_stuck_context",
        max_chars=2000
    )

    if st.button(
        "Explore possible next steps",
        key="why_stuck_button"
    ):
        if not stuck_context.strip():
            st.warning("Describe the situation first.")
        else:
            reflection_prompt = f"""
Offer a gentle, non-clinical reflection on this situation:

{stuck_context.strip()}

Please:
- Acknowledge the situation without exaggerating it.
- Separate what the user said from what remains unknown.
- Offer up to three possible factors as hypotheses, not facts.
- Suggest two small, practical and safe next steps.
- Include one optional journaling question.
- Respect that the user may not be ready to act immediately.

Do not diagnose the user.
Do not claim to discover repressed memories or hidden trauma.
Do not promise healing or guaranteed outcomes.
Do not blame the user.
"""
            st.markdown("### Your reflection")
            st.write(ask_ai(reflection_prompt))


# END OF PART 4

# =========================
# PART 5 — BRAIN PUZZLE
# COGNITIVE CHALLENGES
# PROGRESS & ACHIEVEMENTS
# =========================

import math
import time
import random


# -------------------------
# BRAIN PUZZLE HELPERS
# -------------------------

def create_puzzle(size):
    """Create a shuffled numbered-tile puzzle."""
    total = size * size
    tiles = list(range(1, total)) + [0]

    # Shuffle until the puzzle is solvable.
    while True:
        random.shuffle(tiles)
        if puzzle_is_solvable(tiles, size):
            break

    return tiles


def puzzle_is_solvable(tiles, size):
    """Check solvability of a sliding puzzle."""
    values = [value for value in tiles if value != 0]
    inversions = 0

    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] > values[j]:
                inversions += 1

    if size % 2 == 1:
        return inversions % 2 == 0

    blank_row_from_bottom = size - (tiles.index(0) // size)

    if blank_row_from_bottom % 2 == 0:
        return inversions % 2 == 1

    return inversions % 2 == 0


def puzzle_is_solved(tiles):
    """Check whether all tiles are in their target positions."""
    expected = list(range(1, len(tiles))) + [0]
    return tiles == expected


def puzzle_move(tiles, size, source, destination):
    """Move a tile only when it is adjacent to the blank."""
    if source < 0 or source >= len(tiles):
        return tiles, False

    if destination < 0 or destination >= len(tiles):
        return tiles, False

    if tiles[source] == 0:
        return tiles, False

    source_row, source_col = divmod(source, size)
    dest_row, dest_col = divmod(destination, size)

    adjacent = (
        abs(source_row - dest_row)
        + abs(source_col - dest_col)
        == 1
    )

    if not adjacent or tiles[destination] != 0:
        return tiles, False

    updated = tiles.copy()
    updated[source], updated[destination] = (
        updated[destination],
        updated[source]
    )

    return updated, True


def initialise_puzzle(size):
    st.session_state.puzzle_grid = size
    st.session_state.puzzle_tiles = create_puzzle(size)
    st.session_state.puzzle_moves = 0
    st.session_state.puzzle_completed = False
    st.session_state.puzzle_started_at = time.time()
    st.session_state.puzzle_selected_tile = None


# -------------------------
# BRAIN PUZZLE PAGE
# -------------------------

def page_brain_puzzle():
    show_hero(
        "Brain Puzzle",
        "Solve the sliding-tile challenge using planning and spatial reasoning."
    )

    st.info(
        "This version uses tile selection and adjacent moves. "
        "It does not provide drag-and-drop movement."
    )

    size = st.selectbox(
        "Puzzle size",
        [3, 4, 5],
        index=(
            [3, 4, 5].index(st.session_state.puzzle_grid)
            if st.session_state.puzzle_grid in [3, 4, 5]
            else 0
        ),
        format_func=lambda n: f"{n} × {n}",
        key="puzzle_size_select"
    )

    if (
        not st.session_state.puzzle_tiles
        or len(st.session_state.puzzle_tiles) != size * size
    ):
        initialise_puzzle(size)

    if st.button("Start / Restart puzzle", key="restart_puzzle"):
        initialise_puzzle(size)
        st.rerun()

    tiles = st.session_state.puzzle_tiles

    elapsed = 0
    if st.session_state.puzzle_started_at:
        elapsed = int(
            time.time() - st.session_state.puzzle_started_at
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Moves", st.session_state.puzzle_moves)

    with col2:
        st.metric("Time", f"{elapsed} sec")

    with col3:
        st.metric("Tiles", f"{size * size - 1}")

    st.markdown("### Arrange the tiles in order")

    selected_tile = st.session_state.puzzle_selected_tile

    for row_index in range(size):
        columns = st.columns(size)

        for col_index in range(size):
            index = row_index * size + col_index
            value = tiles[index]

            with columns[col_index]:
                if value == 0:
                    st.button(
                        "⬜",
                        key=f"puzzle_blank_{index}",
                        disabled=True,
                        use_container_width=True
                    )
                else:
                    label = str(value)

                    if selected_tile == index:
                        label = f"✓ {value}"

                    if st.button(
                        label,
                        key=f"puzzle_tile_{index}",
                        use_container_width=True,
                        disabled=st.session_state.puzzle_completed
                    ):
                        st.session_state.puzzle_selected_tile = index
                        st.rerun()

    if selected_tile is not None:
        if selected_tile < len(tiles) and tiles[selected_tile] != 0:
            st.write(
                f"Selected tile: **{tiles[selected_tile]}**"
            )

            blank_index = tiles.index(0)
            blank_row, blank_col = divmod(blank_index, size)

            possible_targets = []

            for index in range(len(tiles)):
                row, col = divmod(index, size)

                if (
                    abs(row - blank_row)
                    + abs(col - blank_col)
                    == 1
                ):
                    possible_targets.append(index)

            if selected_tile in possible_targets:
                if st.button(
                    "Move selected tile into the empty space",
                    key="confirm_puzzle_move"
                ):
                    updated, moved = puzzle_move(
                        tiles,
                        size,
                        selected_tile,
                        blank_index
                    )

                    if moved:
                        st.session_state.puzzle_tiles = updated
                        st.session_state.puzzle_moves += 1
                        st.session_state.puzzle_selected_tile = None

                        if puzzle_is_solved(updated):
                            st.session_state.puzzle_completed = True

                            moves = st.session_state.puzzle_moves

                            score = max(
                                100,
                                1000 - moves * 5 - elapsed
                            )

                            st.session_state.puzzle_history.append({
                                "size": size,
                                "moves": moves,
                                "seconds": elapsed,
                                "score": score
                            })

                            record_progress("puzzles")
                            add_achievement("Puzzle Solver")

                        st.rerun()
                    else:
                        st.warning("That move is not allowed.")
            else:
                st.caption(
                    "The selected tile is not next to the empty space. "
                    "Choose a tile beside the empty space."
                )

            if st.button(
                "Cancel selection",
                key="cancel_puzzle_selection"
            ):
                st.session_state.puzzle_selected_tile = None
                st.rerun()

    if st.session_state.puzzle_completed:
        st.success("Puzzle completed!")

        st.write(
            f"Moves: {st.session_state.puzzle_moves}"
        )

        st.write(f"Time: {elapsed} seconds")

        st.caption(
            "Puzzle performance is a game result, not a clinical "
            "measure of intelligence or brain health."
        )


# =========================
# COGNITIVE CHALLENGES
# =========================

COGNITIVE_CHALLENGES = [
    {
        "name": "Number Pattern",
        "question": "What number comes next: 2, 4, 8, 16, __?",
        "options": ["18", "24", "32", "30"],
        "answer": "32",
        "explanation": (
            "Each number is twice the previous number."
        )
    },
    {
        "name": "Working Memory",
        "question": "Remember this code: 729418. What was the code?",
        "options": ["729418", "724918", "792418", "729481"],
        "answer": "729418",
        "explanation": (
            "The task checks whether you can reproduce the displayed sequence."
        )
    },
    {
        "name": "Logical Reasoning",
        "question": (
            "All roses in a garden are flowers. "
            "A plant is a rose. What follows?"
        ),
        "options": [
            "It is a flower",
            "It is a tree",
            "It is not a flower",
            "There is not enough information"
        ],
        "answer": "It is a flower",
        "explanation": (
            "The conclusion follows from the two statements provided."
        )
    },
    {
        "name": "Attention to Detail",
        "question": "Which option is different from the others?",
        "options": ["ABCD", "ABCD", "ABDC", "ABCD"],
        "answer": "ABDC",
        "explanation": (
            "The third option changes the order of the last two letters."
        )
    }
]


def page_cognitive_challenges():
    show_hero(
        "Cognitive Challenges",
        "Try short exercises involving reasoning, attention and memory."
    )

    st.caption(
        "These are informal educational challenges, not validated "
        "neuropsychological tests."
    )

    names = [
        challenge["name"]
        for challenge in COGNITIVE_CHALLENGES
    ]

    selected_name = st.selectbox(
        "Choose a challenge",
        names,
        key="challenge_select"
    )

    challenge = next(
        item for item in COGNITIVE_CHALLENGES
        if item["name"] == selected_name
    )

    html_card(
        challenge["name"],
        challenge["question"],
        "COGNITIVE CHALLENGE"
    )

    answer = st.radio(
        "Choose your answer",
        challenge["options"],
        key=f"challenge_answer_{selected_name}"
    )

    if st.button(
        "Submit answer",
        key=f"submit_challenge_{selected_name}"
    ):
        submitted_key = f"challenge_submitted_{selected_name}"

        if st.session_state.get(submitted_key, False):
            st.info(
                "You have already submitted this challenge in this session."
            )
        else:
            correct = answer == challenge["answer"]

            result = {
                "name": challenge["name"],
                "answer": answer,
                "correct": correct,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            st.session_state.challenge_history.append(result)
            st.session_state[submitted_key] = True

            record_progress("challenges")

            if correct:
                add_achievement("Challenge Completed")
                st.success("Correct answer!")
            else:
                st.warning("Not quite. Review the explanation below.")

            st.write("**Explanation:**", challenge["explanation"])

    if st.button(
        "Reset this challenge",
        key=f"reset_challenge_{selected_name}"
    ):
        st.session_state[
            f"challenge_submitted_{selected_name}"
        ] = False

        st.rerun()

    st.divider()
    st.subheader("Challenge history")

    history = st.session_state.challenge_history

    if history:
        for item in reversed(history[-10:]):
            status = "Correct" if item["correct"] else "Incorrect"
            st.write(
                f"• {item['name']}: {status} "
                f"({item['timestamp']})"
            )
    else:
        st.caption("Complete a challenge to see your history.")


# =========================
# PROGRESS & ACHIEVEMENTS
# =========================

def page_progress():
    show_hero(
        "Progress & Achievements",
        "Review the learning activities you have completed in this session."
    )

    progress = st.session_state.progress

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Experiments",
            progress.get("experiments", 0)
        )

        st.metric(
            "Puzzles completed",
            progress.get("puzzles", 0)
        )

        st.metric(
            "Challenges",
            progress.get("challenges", 0)
        )

    with col2:
        st.metric(
            "Research activities",
            progress.get("research", 0)
        )

        st.metric(
            "AI requests",
            st.session_state.get("ai_requests", 0)
        )

        best = progress.get("best_reaction_ms")

        st.metric(
            "Best recorded reaction",
            f"{best} ms" if best is not None else "Not recorded"
        )

    st.divider()
    st.subheader("Achievements")

    achievements = st.session_state.achievements

    if achievements:
        for achievement in achievements:
            st.write(f"🏅 {achievement}")
    else:
        st.info(
            "No achievements yet. Complete an experiment, puzzle "
            "or challenge to earn one."
        )

    st.divider()
    st.subheader("Recent activity")

    activity_items = []

    activity_items.extend(
        st.session_state.experiment_history[-5:]
    )

    activity_items.extend(
        st.session_state.challenge_history[-5:]
    )

    activity_items.extend(
        st.session_state.puzzle_history[-5:]
    )

    activity_items.sort(
        key=lambda item: item.get("timestamp", ""),
        reverse=True
    )

    if activity_items:
        for item in activity_items[:10]:
            st.write(item)
    else:
        st.caption("Your recent activities will appear here.")

    st.caption(
        "These totals represent activities recorded by the app. "
        "They are not measurements of intelligence, mental health "
        "or brain activity."
    )


# END OF PART 5

