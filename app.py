import os
import re
import time
import json
import base64
import hashlib
import secrets
import random
from datetime import date
from urllib.parse import urlencode

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFont

try:
    import numpy as np
except Exception:
    np = None

try:
    from streamlit_dnd import dnd
except Exception:
    dnd = None

try:
    from streamlit_webrtc import (
        webrtc_streamer,
        VideoProcessorBase,
    )
    import av
    import cv2
    import mediapipe as mp
except Exception:
    webrtc_streamer = None
    VideoProcessorBase = object
    av = None
    cv2 = None
    mp = None

try:
    from brainflow.board_shim import (
        BoardShim,
        BrainFlowInputParams,
        BoardIds,
    )
except Exception:
    BoardShim = None
    BrainFlowInputParams = None
    BoardIds = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"
TAGLINE = "Explore cognition, behavior & the brain"
AI_SESSION_LIMIT = 20


# ============================================================
# SECRETS
# ============================================================

def secret(name, default=""):
    try:
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)

    if value is None:
        return default

    return str(value).strip()


GEMINI_API_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret("GEMINI_MODEL", "gemini-2.5-flash")

EASYPAISA_NUMBER = secret("EASYPAISA_NUMBER")
EASYPAISA_NAME = secret("EASYPAISA_NAME", CREATOR)

INTERNATIONAL_PAYMENT_URL = secret(
    "INTERNATIONAL_PAYMENT_URL"
)

PAYMENT_ADMIN_KEY = secret("PAYMENT_ADMIN_KEY")


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: Inter, Arial, sans-serif;
}

.main {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(60,140,255,.10),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(120,80,255,.08),
            transparent 25%
        );
}

.neuro-title {
    font-size: 52px;
    font-weight: 800;
    letter-spacing: 3px;
    margin-bottom: 0;
}

.neuro-subtitle {
    font-size: 19px;
    opacity: .78;
    margin-top: 0;
}

.creator {
    font-size: 14px;
    opacity: .65;
}

.hero,
.card,
.small-card,
.social-card,
.story-card,
.challenge-card,
.game-card,
.result-card {
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,.20);
    background: rgba(128,128,128,.06);
}

.hero {
    padding: 32px;
    background:
        linear-gradient(
            135deg,
            rgba(50,120,255,.13),
            rgba(100,80,255,.08)
        );
    margin-bottom: 20px;
}

.card {
    padding: 22px;
    margin-bottom: 18px;
}

.small-card {
    padding: 15px;
    margin-bottom: 12px;
}

.social-card {
    padding: 18px;
    margin-bottom: 12px;
}

.story-card {
    padding: 15px;
    margin-bottom: 15px;
}

.challenge-card {
    padding: 20px;
    margin-bottom: 15px;
}

.game-card {
    padding: 20px;
}

.result-card {
    padding: 20px;
}

.muted {
    opacity: .65;
}

.center {
    text-align: center;
}

.big-emoji {
    font-size: 70px;
}

.friend-online {
    color: #2ecc71;
}

.streak {
    font-size: 24px;
    font-weight: 700;
}

.chat-header {
    padding: 18px;
    border-radius: 16px;
    background: rgba(70,120,255,.10);
    margin-bottom: 15px;
}

.scene {
    position: relative;
    height: 360px;
    border-radius: 22px;
    overflow: hidden;
    background:
        radial-gradient(
            circle at 50% 35%,
            rgba(70,130,255,.20),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #07101f,
            #111e38,
            #07101f
        );
    border: 1px solid rgba(130,170,255,.30);
}

.floor {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 80px;
    background: rgba(0,0,0,.25);
}

.robot {
    position: absolute;
    left: 12%;
    bottom: 50px;
    text-align: center;
    width: 190px;
}

.machine {
    position: absolute;
    right: 13%;
    bottom: 55px;
    font-size: 100px;
}

.beam {
    position: absolute;
    top: 70px;
    height: 3px;
    width: 35%;
    background: rgba(100,180,255,.9);
    box-shadow: 0 0 18px rgba(100,180,255,.9);
    animation: scan 2.2s linear infinite;
}

@keyframes scan {
    0% {
        left: 5%;
        opacity: .1;
    }
    50% {
        left: 80%;
        opacity: 1;
    }
    100% {
        left: 5%;
        opacity: .1;
    }
}

@keyframes pulse {
    0% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.08);
    }
    100% {
        transform: scale(1);
    }
}

@keyframes floatRobot {
    0% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-12px);
    }
    100% {
        transform: translateY(0);
    }
}

button {
    border-radius: 12px !important;
}

@media (max-width: 700px) {

    .neuro-title {
        font-size: 34px;
    }

    .neuro-subtitle {
        font-size: 16px;
    }

    .scene {
        height: 300px;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {

    "page": "Welcome",

    "language": "English",

    # ---------------- LAB ----------------
    "character": "Ayna",
    "equipment": "Neural Scanner",
    "experiment": "Attention & Response",
    "experiment_started": False,
    "experiment_completed": False,
    "lab_result": None,
    "lab_completed": 0,
    "lab_followup": False,

    # ---------------- AI ----------------
    "ai_requests": 0,
    "ai_date": date.today().isoformat(),
    "ai_history": [],
    "ayna_messages": [],

    # ---------------- PRIVATE ----------------
    "private_unlocked": False,
    "private_pin_hash": "",
    "private_pin_salt": "",
    "private_messages": [],

    # ---------------- MOOD ----------------
    "voice_result": None,
    "mood_result": None,
    "behaviour_result": None,

    # ---------------- RESEARCH ----------------
    "research_results": [],
    "research_notes": [],
    "research_completed": 0,

    # ---------------- JOURNEY ----------------
    "journey_index": 0,

    # ---------------- PUZZLE ----------------
    "puzzle_grid": 3,
    "puzzle_tiles": [],
    "puzzle_blank": None,
    "puzzle_moves": 0,
    "puzzle_started_at": 0,
    "puzzle_elapsed": 0,
    "puzzle_completed": False,
    "puzzle_best_time": None,
    "puzzle_best_moves": None,
    "puzzle_round": 1,
    "puzzle_challenge": "Time Challenge",

    # ---------------- EXERCISES ----------------
    "games_completed": 0,
    "achievements": [],

    # ---------------- HARDWARE ----------------
    "eye_samples": [],
    "eeg_history": [],

    # ---------------- SOCIAL ----------------
    "social_username": "",
    "social_bio": "",
    "social_avatar": "🧠",

    "social_search": "",
    "social_target": "",

    "friends": [],
    "incoming_requests": [],
    "sent_requests": [],

    "social_messages": [],

    "friend_streaks": {},

    "stories": [],

    "story_draft_image": None,
    "story_draft_filter": "Original",
    "story_draft_emoji": "🧠",
    "story_draft_text": "",

    "social_challenges": [],
    "active_challenge": None,

    "social_game": None,

    # ---------------- PROGRESS ----------------
    "achievements": [],
    "activity_log": [],

    # ---------------- CONSULTATION ----------------
    "forum_status": "Not started",
    "forum_name": "",
    "forum_phone": "",
    "forum_problem": "",
    "forum_slot": "",
    "forum_payment_method": "",
    "forum_payment_status": "Not submitted",
    "forum_transaction_id": "",
    "forum_messages": [],

    # ---------------- SYSTEM ----------------
    "health_log": [],
    "heal_attempts": 0,
    "heal_recovered": 0,
    "last_error": "",
}


for key, value in DEFAULTS.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# GENERAL HELPERS
# ============================================================

def add_activity(name, detail=""):

    st.session_state.activity_log.append(
        {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "activity": name,
            "detail": detail,
        }
    )


def add_achievement(name):

    if name not in st.session_state.achievements:

        st.session_state.achievements.append(name)


def find_asset(filename):

    candidates = [
        filename,
        os.path.join(".", filename),
        os.path.join("assets", filename),
        os.path.join(".", "assets", filename),
    ]

    for path in candidates:

        if os.path.exists(path):

            return path

    return None


def image_to_base64(path):

    if not path or not os.path.exists(path):
        return ""

    try:

        with open(path, "rb") as f:

            return base64.b64encode(
                f.read()
            ).decode("utf-8")

    except Exception:

        return ""


def safe_html(text):

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


# ============================================================
# HEADER
# ============================================================

def render_header():

    st.markdown(
        f"""
        <div class="hero">

            <div class="neuro-title">
                🧠 {APP_NAME}
            </div>

            <div class="neuro-subtitle">
                {TAGLINE}
            </div>

            <div class="creator">
                Independent cognitive neuroscience research project
                · {CREATOR}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BROWSER VOICE
# ============================================================

def browser_speech_button(
    text,
    label="🔊 Speak Ayna",
):

    payload = json.dumps(str(text))

    components.html(
        f"""
        <button
            onclick="speakAyna()"
            style="
                width:100%;
                padding:12px;
                border-radius:12px;
                border:1px solid rgba(128,128,128,.35);
                background:rgba(70,120,255,.12);
                color:inherit;
                cursor:pointer;
                font-size:15px;
            "
        >
            {safe_html(label)}
        </button>

        <script>

        function speakAyna() {{

            const text = {payload};

            if (!("speechSynthesis" in window)) {{

                alert(
                    "Your browser does not support speech synthesis."
                );

                return;
            }}

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
        """,
        height=60,
    )


# ============================================================
# AI
# ============================================================

def reset_ai_counter():

    today = date.today().isoformat()

    if st.session_state.ai_date != today:

        st.session_state.ai_date = today
        st.session_state.ai_requests = 0


reset_ai_counter()


def ai_available():

    return bool(
        GEMINI_API_KEY
        and genai is not None
    )


def ask_ai(
    prompt,
    context="",
):

    reset_ai_counter()

    if st.session_state.ai_requests >= AI_SESSION_LIMIT:

        return (
            "Ayna AI daily/session limit reached. "
            "You can continue using the non-AI features."
        )

    if not ai_available():

        return (
            "Ayna AI is not connected yet. "
            "Please add GEMINI_API_KEY to Streamlit Secrets."
        )

    system_prompt = f"""
You are Ask Ayna inside NEUROLENS.

Creator:
Ayna Jaffri

Focus:
cognitive neuroscience, cognition, attention, memory,
learning, emotion, reward, decision-making, perception,
cognitive control, neuroplasticity, behaviour and consciousness.

Rules:

- Educational explanations only.
- Do not diagnose.
- Do not claim games measure brain activity.
- Do not claim voice analysis proves hidden emotion.
- Do not infer personality from a short recording.
- Do not invent scientific studies.
- Distinguish evidence from hypothesis.
- Explain uncertainty.
- Do not pretend to know private mental states.
- If health concerns arise, recommend an appropriate professional.
- Keep answers understandable.

Language:
{st.session_state.language}

Additional context:
{context}

User:
{prompt}
"""

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=system_prompt,
        )

        answer = getattr(
            response,
            "text",
            None,
        )

        if not answer:

            return (
                "Ayna could not generate a response "
                "right now."
            )

        st.session_state.ai_requests += 1

        st.session_state.ai_history.append(
            {
                "time": time.time(),
                "prompt": prompt,
                "response": answer,
            }
        )

        return answer

    except Exception:

        return (
            "Ayna is temporarily unavailable. "
            "Please check your Gemini configuration."
        )


# ============================================================
# WELCOME
# ============================================================

def page_welcome():

    st.header("🧠 Welcome to NEUROLENS")

    video = find_asset(
        "ayna_reboot_voiced.mp4"
    )

    if not video:

        video = find_asset(
            "ayna_reboot_voiced_faster_louder.mp4"
        )

    if video:

        st.video(video)

    else:

        st.markdown(
            """
            <div class="card center">

                <div class="big-emoji">
                    🧠
                </div>

                <h2>
                    Welcome to NeuroLens
                </h2>

                <p>
                    I’m Ayna. Let's explore the brain,
                    behaviour, and cognition together.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="card">

        <h3>
        Explore. Experiment. Understand.
        </h3>

        <p>
        NEUROLENS combines cognitive neuroscience
        education, interactive behavioural tasks,
        AI-assisted learning and a social cognitive
        challenge environment.
        </p>

        <p class="muted">
        Interactive tasks are educational demonstrations.
        They are not clinical tests and do not directly
        measure brain activity.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.language = st.selectbox(
        "🌐 Language",
        [
            "English",
            "Roman Urdu",
        ],
        index=[
            "English",
            "Roman Urdu",
        ].index(
            st.session_state.language
        ),
    )

    if st.button(
        "🚀 ENTER NEUROLENS",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.page = "Lab"

        add_activity(
            "Entered NEUROLENS"
        )

        st.rerun()


# ============================================================
# LAB
# ============================================================

CHARACTERS = {

    "Ayna":
        ("🧑‍🔬", "Researcher"),

    "Student":
        ("🧑‍🎓", "Student"),

    "Lab Assistant":
        ("🧑‍💻", "Lab Assistant"),

    "AI Research Agent":
        ("🤖", "AI Research Agent"),
}


EQUIPMENT = {

    "EEG Simulator":
        "🧠",

    "Eye Tracker":
        "👁️",

    "Reaction-Time System":
        "⚡",

    "Cognitive Task Monitor":
        "📊",

    "Physiological Sensor":
        "❤️",
}


EXPERIMENTS = {

    "Attention":
        "Selective attention and target detection.",

    "Memory":
        "Short-term sequence memory.",

    "Decision & Reward":
        "Immediate versus delayed reward.",

    "Stroop-Cognitive Control":
        "Cognitive interference and control.",

    "Pattern Recognition":
        "Detect a sequence or rule.",
}


def lab_scene():

    character_icon = CHARACTERS[
        st.session_state.character
    ][0]

    equipment_icon = EQUIPMENT[
        st.session_state.equipment
    ]

    robot_path = find_asset(
        "ayna_robot.png"
    )

    robot_b64 = image_to_base64(
        robot_path
    )

    if robot_b64:

        character_html = (
            f"""
            <img
                src="data:image/png;base64,{robot_b64}"
                style="
                    width:150px;
                    height:150px;
                    object-fit:contain;
                    animation:floatRobot 2s
                    ease-in-out infinite;
                "
            >
            """
        )

    else:

        character_html = f"""
        <div
            style="
                font-size:100px;
                animation:floatRobot 2s
                ease-in-out infinite;
            "
        >
            {character_icon}
        </div>
        """

    st.markdown(
        f"""
        <div class="scene">

            <div
                style="
                    position:absolute;
                    top:20px;
                    left:25px;
                    font-weight:700;
                "
            >
                🧪
                {safe_html(
                    st.session_state.experiment
                )}
            </div>

            <div class="beam"></div>

            <div class="robot">

                {character_html}

                <div>
                    {safe_html(
                        st.session_state.character
                    )}
                </div>

            </div>

            <div class="machine">

                {equipment_icon}

            </div>

            <div class="floor"></div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def finish_lab(result):

    st.session_state.lab_result = result
    st.session_state.experiment_completed = True
    st.session_state.lab_completed += 1

    add_achievement(
        "Cognitive Lab Explorer"
    )

    add_activity(
        "Completed Lab",
        st.session_state.experiment,
    )


def lab_attention():

    st.subheader(
        "🎯 Attention Challenge"
    )

    st.write(
        "Find the target X."
    )

    st.markdown(
        """
        <div class="card center"
             style="font-size:32px;letter-spacing:14px">

        O O O O O<br>
        O O O O O<br>
        O O X O O<br>
        O O O O O<br>
        O O O O O

        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.text_input(
        "What was the target?",
        key="lab_attention",
    )

    if st.button(
        "Check Attention",
        use_container_width=True,
    ):

        if answer.strip().upper() == "X":

            finish_lab(
                "Correct. You identified the target. "
                "This is a simple behavioural attention task."
            )

        else:

            finish_lab(
                "The target was X. "
                "Selective attention helps prioritize "
                "relevant information among distractors."
            )

        st.rerun()


def lab_memory():

    sequence = "729418"

    st.subheader(
        "🧠 Memory Mission"
    )

    if not st.session_state.get(
        "memory_hidden",
        False,
    ):

        st.code(sequence)

        if st.button(
            "Hide Sequence",
            use_container_width=True,
        ):

            st.session_state.memory_hidden = True
            st.rerun()

    else:

        st.success(
            "Sequence hidden."
        )

        answer = st.text_input(
            "Enter what you remember",
            key="lab_memory",
        )

        if st.button(
            "Check Memory",
            use_container_width=True,
        ):

            if answer.strip() == sequence:

                finish_lab(
                    "Excellent recall. "
                    "The sequence was reproduced accurately."
                )

            else:

                finish_lab(
                    "The sequence was 729418. "
                    "Working-memory performance can vary "
                    "with attention and interference."
                )

            st.session_state.memory_hidden = False

            st.rerun()


def lab_decision():

    st.subheader(
        "💰 Decision & Reward"
    )

    choice = st.radio(
        "Choose one:",
        [
            "Rs 1,000 today",
            "Rs 1,500 after 30 days",
        ],
    )

    if st.button(
        "Submit Decision",
        use_container_width=True,
    ):

        finish_lab(
            f"You selected: {choice}. "
            "This illustrates intertemporal choice, "
            "where immediate and delayed rewards are compared."
        )

        st.rerun()


def lab_stroop():

    st.subheader(
        "🎨 Stroop Cognitive Control"
    )

    st.write(
        "Identify the INK COLOR, not the word."
    )

    st.markdown(
        """
        <div
            style="
                text-align:center;
                font-size:52px;
                font-weight:800;
                padding:25px;
            "
        >
            <span style="color:#2468d8">
                RED
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.selectbox(
        "Ink color:",
        [
            "BLUE",
            "RED",
            "GREEN",
            "YELLOW",
        ],
    )

    if st.button(
        "Submit Stroop",
        use_container_width=True,
    ):

        if answer == "BLUE":

            finish_lab(
                "Correct. The word and ink colour conflicted, "
                "creating a simple interference condition."
            )

        else:

            finish_lab(
                "The ink colour was BLUE. "
                "This demonstrates how conflicting information "
                "can influence response selection."
            )

        st.rerun()


def lab_pattern():

    st.subheader(
        "🔢 Pattern Recognition"
    )

    st.markdown(
        """
        <div class="card center"
             style="font-size:30px">

        2 → 4 → 8 → 16 → 32 → ?

        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.number_input(
        "Next number",
        min_value=0,
        step=1,
    )

    if st.button(
        "Check Pattern",
        use_container_width=True,
    ):

        if answer == 64:

            finish_lab(
                "Correct. The pattern doubles each time."
            )

        else:

            finish_lab(
                "The expected next number is 64."
            )

        st.rerun()


def page_lab():

    st.header(
        "🔬 Interactive Cognitive Neuroscience Lab"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.session_state.character = st.selectbox(
            "👤 Character",
            list(CHARACTERS.keys()),
        )

    with c2:

        st.session_state.equipment = st.selectbox(
            "🔬 Equipment",
            list(EQUIPMENT.keys()),
        )

    with c3:

        st.session_state.experiment = st.selectbox(
            "🧪 Experiment",
            list(EXPERIMENTS.keys()),
        )

    st.info(
        EXPERIMENTS[
            st.session_state.experiment
        ]
    )

    if st.button(
        "⚙️ APPLY LAB SETUP",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.experiment_started = True
        st.session_state.experiment_completed = False
        st.session_state.lab_result = None
        st.session_state.lab_followup = False

        st.rerun()

    if not st.session_state.experiment_started:

        return

    lab_scene()

    if not st.session_state.experiment_completed:

        if st.session_state.experiment == "Attention":

            lab_attention()

        elif st.session_state.experiment == "Memory":

            lab_memory()

        elif st.session_state.experiment == "Decision & Reward":

            lab_decision()

        elif st.session_state.experiment == "Stroop-Cognitive Control":

            lab_stroop()

        elif st.session_state.experiment == "Pattern Recognition":

            lab_pattern()

    else:

        st.markdown(
            """
            <div class="result-card">

            <h3>
            🤖 Ayna's Scientific Explanation
            </h3>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(
            st.session_state.lab_result
        )

        browser_speech_button(
            st.session_state.lab_result,
            "🔊 Play Ayna Explanation",
        )

        if st.button(
            "🧩 Follow-up Challenge",
            use_container_width=True,
        ):

            st.session_state.lab_followup = True

        if st.session_state.lab_followup:

            st.info(
                "Try increasing difficulty, "
                "adding distractors or increasing memory load."
            )


# ============================================================
# BRAIN JOURNEY
# ============================================================

JOURNEY = [

    (
        "Whole Brain",
        "The brain contains interacting regions and networks.",
        "brain",
    ),

    (
        "Neuron",
        "Neurons receive, integrate and transmit information.",
        "neuron",
    ),

    (
        "Electrical Signal",
        "Electrical activity can propagate along neuronal axons.",
        "signal",
    ),

    (
        "Synapse",
        "Neurons communicate across synaptic junctions.",
        "synapse",
    ),

    (
        "Neurotransmitters",
        "Chemical messengers participate in synaptic communication.",
        "chemical",
    ),

    (
        "Prefrontal Cortex",
        "Important for cognitive control, planning and working memory.",
        "pfc",
    ),

    (
        "Hippocampus",
        "Important for memory formation and spatial processing.",
        "hippocampus",
    ),

    (
        "Striatum",
        "Involved in action selection and reward-related learning.",
        "striatum",
    ),

    (
        "Anterior Cingulate Cortex",
        "Associated with conflict and performance monitoring.",
        "acc",
    ),

    (
        "Attention Networks",
        "Distributed systems help select relevant information.",
        "attention",
    ),
]


def concept_visual(kind):

    asset_map = {

        "brain":
            [
                "brain_animation.mp4",
                "cognitive_lab_brain.mp4",
            ],

        "pfc":
            [
                "pfc.png",
                "prefrontal_cortex.png",
            ],

        "hippocampus":
            [
                "hippocampus.png",
            ],

        "striatum":
            [
                "striatum.png",
            ],

        "acc":
            [
                "acc.png",
                "anterior_cingulate.png",
            ],

        "attention":
            [
                "attention_network.png",
                "attention.png",
            ],

        "neuron":
            [
                "neuron.gif",
                "neuron.png",
                "neuron.mp4",
            ],

        "synapse":
            [
                "synapse.gif",
                "synapse.png",
                "synapse.mp4",
            ],
    }

    if kind in asset_map:

        for name in asset_map[kind]:

            path = find_asset(name)

            if path:

                if path.lower().endswith(
                    (".mp4", ".webm")
                ):

                    st.video(path)

                else:

                    st.image(
                        path,
                        use_container_width=True,
                    )

                return True

    return False


def fallback_concept_visual(kind):

    if kind == "neuron":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:40px">

            🌿 → 🟢 → ━━━━━━━ → ●

            <br>

            <small>
            Dendrites → soma → axon
            </small>

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "synapse":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:38px">

            🧠 🟠🟠🟠 🧠

            <br>

            <small>
            Conceptual synaptic communication
            </small>

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "signal":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:36px">

            🧠 → ⚡ → ⚡ → ⚡ → 🧠

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "chemical":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:36px">

            🧠 → 🟠 🟠 🟠 → 🧠

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "pfc":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:50px">

            🧠
            <br>
            🔵

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "hippocampus":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:50px">

            🧠
            <br>
            🟣

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "striatum":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:50px">

            🧠
            <br>
            🟢

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "acc":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:50px">

            🧠
            <br>
            🟠

            </div>
            """,
            unsafe_allow_html=True,
        )

    elif kind == "attention":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:34px">

            👀 → 🎯

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        brain = find_asset(
            "brain.png"
        )

        if brain:

            st.image(
                brain,
                use_container_width=True,
            )

        else:

            st.markdown(
                """
                <div class="card center"
                     style="font-size:70px">

                🧠

                </div>
                """,
                unsafe_allow_html=True,
            )


def page_brain_journey():

    st.header(
        "🧠 Visual Brain Journey"
    )

    index = (
        st.session_state.journey_index
        % len(JOURNEY)
    )

    title, description, kind = JOURNEY[index]

    st.progress(
        (index + 1) / len(JOURNEY)
    )

    st.markdown(
        f"## {title}"
    )

    st.write(
        description
    )

    if not concept_visual(kind):

        fallback_concept_visual(kind)

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "⬅ Previous",
            disabled=index == 0,
            use_container_width=True,
        ):

            st.session_state.journey_index -= 1
            st.rerun()

    with c2:

        if st.button(
            "🔄 Restart",
            use_container_width=True,
        ):

            st.session_state.journey_index = 0
            st.rerun()

    with c3:

        if st.button(
            "Next ➡",
            disabled=index == len(JOURNEY) - 1,
            use_container_width=True,
        ):

            st.session_state.journey_index += 1
            st.rerun()


# ============================================================
# EXPLORE BRAIN
# ============================================================

BRAIN_SYSTEMS = {

    "Prefrontal Cortex":
        "Cognitive control, planning, working memory and goal-directed behaviour.",

    "Hippocampus":
        "Memory formation and spatial processing.",

    "Striatum":
        "Action selection, reward-related learning and movement.",

    "Anterior Cingulate Cortex":
        "Conflict monitoring and performance monitoring.",

    "Attention Networks":
        "Distributed systems supporting selection of relevant information.",

}


def page_explore_brain():

    st.header(
        "🧠 Explore Brain Systems"
    )

    system = st.selectbox(
        "Select a concept",
        list(BRAIN_SYSTEMS.keys()),
    )

    visual_map = {

        "Prefrontal Cortex":
            "pfc",

        "Hippocampus":
            "hippocampus",

        "Striatum":
            "striatum",

        "Anterior Cingulate Cortex":
            "acc",

        "Attention Networks":
            "attention",
    }

    kind = visual_map[
        system
    ]

    if not concept_visual(kind):

        fallback_concept_visual(kind)

    st.markdown(
        f"""
        <div class="card">

        <h2>
        {safe_html(system)}
        </h2>

        <p>
        {safe_html(
            BRAIN_SYSTEMS[system]
        )}
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🤖 Ask Ayna",
        use_container_width=True,
    ):

        answer = ask_ai(
            f"Explain the role of {system} "
            "in cognitive neuroscience."
        )

        st.write(answer)

        browser_speech_button(
            answer
        )


# ============================================================
# BRAIN PUZZLE
# ============================================================

def puzzle_image():

    path = find_asset(
        "brain.png"
    )

    if not path:

        return None

    try:

        return Image.open(
            path
        ).convert("RGB")

    except Exception:

        return None


def make_puzzle(n):

    tiles = list(
        range(n * n)
    )

    blank = n * n - 1

    shuffled = tiles[:]

    for _ in range(
        max(80, n * n * 30)
    ):

        blank_index = shuffled.index(
            blank
        )

        r, c = divmod(
            blank_index,
            n
        )

        choices = []

        if r > 0:
            choices.append(
                blank_index - n
            )

        if r < n - 1:
            choices.append(
                blank_index + n
            )

        if c > 0:
            choices.append(
                blank_index - 1
            )

        if c < n - 1:
            choices.append(
                blank_index + 1
            )

        target = random.choice(
            choices
        )

        shuffled[
            blank_index
        ], shuffled[
            target
        ] = (
            shuffled[target],
            shuffled[blank_index],
        )

    return shuffled


def tile_image(
    image,
    tile_id,
    n,
):

    width, height = image.size

    row, col = divmod(
        tile_id,
        n
    )

    return image.crop(
        (
            int(col * width / n),
            int(row * height / n),
            int((col + 1) * width / n),
            int((row + 1) * height / n),
        )
    )


def page_brain_puzzle():

    st.header(
        "🧩 Brain Puzzle"
    )

    st.write(
        "Arrange the brain pieces. "
        "Only legal adjacent moves are accepted."
    )

    image = puzzle_image()

    if image is None:

        st.error(
            "Please add brain.png "
            "to the project root or assets/."
        )

        return

    n = st.selectbox(
        "Puzzle grid",
        [3, 4, 5],
        index=0,
        format_func=lambda x:
        f"{x} × {x}",
    )

    if (
        st.session_state.puzzle_grid != n
        or not st.session_state.puzzle_tiles
    ):

        st.session_state.puzzle_grid = n

        st.session_state.puzzle_tiles = (
            make_puzzle(n)
        )

        st.session_state.puzzle_moves = 0

        st.session_state.puzzle_completed = False

        st.session_state.puzzle_started_at = time.time()

    if st.button(
        "🆕 New Puzzle",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.puzzle_grid = n

        st.session_state.puzzle_tiles = (
            make_puzzle(n)
        )

        st.session_state.puzzle_moves = 0

        st.session_state.puzzle_completed = False

        st.session_state.puzzle_started_at = time.time()

        st.rerun()

    elapsed = (
        time.time()
        - st.session_state.puzzle_started_at
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "⏱️ Time",
        f"{elapsed:.1f}s",
    )

    c2.metric(
        "Moves",
        st.session_state.puzzle_moves,
    )

    c3.metric(
        "Round",
        st.session_state.puzzle_round,
    )

    st.divider()

    tiles = st.session_state.puzzle_tiles

    target = list(
        range(n * n)
    )

    blank = n * n - 1

    # --------------------------------------------------------
    # Native DND mode
    # --------------------------------------------------------

    if dnd is not None:

        st.info(
            "Drag a piece toward the empty position. "
            "Touch drag behaviour depends on the browser/device."
        )

        with st.container(
            border=True
        ):

            for position, tile_id in enumerate(
                tiles
            ):

                col1, col2, col3 = st.columns(
                    [1, 1, 1]
                )

                target_col = [
                    col1,
                    col2,
                    col3,
                ][position % 3]

                with target_col:

                    if tile_id == blank:

                        st.markdown(
                            """
                            <div
                                style="
                                    height:120px;
                                    display:flex;
                                    align-items:center;
                                    justify-content:center;
                                    border:2px dashed #777;
                                    border-radius:12px;
                                    font-size:28px;
                                "
                            >
                                ⬜
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    else:

                        st.image(
                            tile_image(
                                image,
                                tile_id,
                                n,
                            ),
                            use_container_width=True,
                        )

        st.caption(
            "For a guaranteed two-dimensional finger puzzle "
            "on every mobile browser, a custom JS pointer-event "
            "component is preferable to Streamlit's generic DND."
        )

    # --------------------------------------------------------
    # Reliable tap-to-move fallback
    # --------------------------------------------------------

    st.subheader(
        "📱 Touch-friendly Move Control"
    )

    st.caption(
        "Tap a piece next to the empty slot. "
        "This works reliably on phones/tablets."
    )

    cols = st.columns(n)

    for index, tile_id in enumerate(
        tiles
    ):

        with cols[
            index % n
        ]:

            if tile_id == blank:

                st.markdown(
                    """
                    <div
                        style="
                            height:70px;
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            border:2px dashed #777;
                            border-radius:10px;
                            font-size:24px;
                        "
                    >
                    ⬜
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                if st.button(
                    f"Piece {tile_id + 1}",
                    key=f"puzzle_piece_{index}_{tile_id}",
                    use_container_width=True,
                ):

                    blank_index = tiles.index(
                        blank
                    )

                    r1, c1 = divmod(
                        index,
                        n
                    )

                    r2, c2 = divmod(
                        blank_index,
                        n
                    )

                    if (
                        abs(r1 - r2)
                        + abs(c1 - c2)
                        == 1
                    ):

                        new_tiles = tiles[:]

                        new_tiles[
                            index
                        ], new_tiles[
                            blank_index
                        ] = (
                            new_tiles[
                                blank_index
                            ],
                            new_tiles[
                                index
                            ],
                        )

                        st.session_state.puzzle_tiles = (
                            new_tiles
                        )

                        st.session_state.puzzle_moves += 1

                        if (
                            new_tiles
                            == target
                        ):

                            st.session_state.puzzle_completed = True

                            st.session_state.puzzle_elapsed = (
                                time.time()
                                - st.session_state.puzzle_started_at
                            )

                            st.session_state.games_completed += 1

                            add_achievement(
                                "Brain Puzzle Master"
                            )

                            add_activity(
                                "Completed Brain Puzzle"
                            )

                            st.balloons()

                        st.rerun()

                    else:

                        st.warning(
                            "Wrong position. "
                            "The piece snaps back."
                        )


    if st.session_state.puzzle_completed:

        st.success(
            f"""
            🎉 Puzzle completed!

            Time:
            {st.session_state.puzzle_elapsed:.1f}s

            Moves:
            {st.session_state.puzzle_moves}
            """
        )

        if st.button(
            "➡️ Next Round",
            use_container_width=True,
        ):

            st.session_state.puzzle_round += 1

            next_grid = min(
                5,
                3
                + (
                    (
                        st.session_state.puzzle_round
                        - 1
                    )
                    // 2
                ),
            )

            st.session_state.puzzle_grid = (
                next_grid
            )

            st.session_state.puzzle_tiles = (
                make_puzzle(next_grid)
            )

            st.session_state.puzzle_moves = 0

            st.session_state.puzzle_completed = False

            st.session_state.puzzle_started_at = time.time()

            st.rerun()


# ============================================================
# VOICE MOOD
# ============================================================

def analyze_voice(audio):

    if not audio:

        return None

    if not ai_available():

        return {
            "transcript":
                "",
            "emoji":
                "⚪",
            "vibe":
                "AI unavailable",
            "explanation":
                "Connect Gemini to analyze the recording.",
        }

    try:

        audio_bytes = audio.getvalue()

        prompt = """
Analyze this user-provided voice recording.

Return JSON with:

{
  "transcript": "...",
  "emoji": "...",
  "vibe": "...",
  "explanation": "..."
}

Vibe must describe broad observable communication/acoustic
features only.

Possible labels:

Positive/energetic-sounding
Calm-sounding
Neutral/mixed
Tense/stressed-sounding
Low-energy-sounding
Uncertain/mixed

Do NOT diagnose.

Do NOT claim to know the person's hidden emotional state.

Do NOT infer personality.

State that this is an AI-assisted acoustic interpretation.
"""

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=(
                        audio.type
                        or "audio/wav"
                    ),
                ),
            ],
        )

        text = (
            getattr(
                response,
                "text",
                "",
            )
            or ""
        )

        st.session_state.ai_requests += 1

        cleaned = re.sub(
            r"```json|```",
            "",
            text,
            flags=re.I,
        ).strip()

        try:

            return json.loads(
                cleaned
            )

        except Exception:

            return {
                "transcript":
                    text,
                "emoji":
                    "🧩",
                "vibe":
                    "Uncertain/mixed",
                "explanation":
                    "The response could not be structured reliably.",
            }

    except Exception:

        return {
            "transcript":
                "",
            "emoji":
                "⚠️",
            "vibe":
                "Unavailable",
            "explanation":
                "Voice analysis failed safely. Please try again.",
        }


def page_voice_mood():

    st.header(
        "🎙️ AI Voice Mood & Behaviour"
    )

    st.caption(
        "Voice interpretation is an AI-assisted estimate "
        "of observable acoustic/communication cues. "
        "It cannot reliably reveal hidden emotion or diagnose."
    )

    voice = st.audio_input(
        "🎤 Record your voice",
        sample_rate=16000,
        key="voice_mood_input",
    )

    if voice:

        st.audio(
            voice
        )

        if st.button(
            "📤 SEND VOICE",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "Ayna is listening..."
            ):

                result = analyze_voice(
                    voice
                )

            st.session_state.voice_result = result

            st.rerun()

    result = st.session_state.voice_result

    if result:

        st.markdown(
            f"""
            <div class="result-card center">

                <div class="big-emoji">
                    {safe_html(
                        result.get(
                            "emoji",
                            "🧩"
                        )
                    )}
                </div>

                <h2>
                    {safe_html(
                        result.get(
                            "vibe",
                            "Uncertain"
                        )
                    )}
                </h2>

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

        st.markdown(
            "### 💬 Voice-vibe interpretation"
        )

        st.write(
            result.get(
                "explanation",
                "",
            )
        )

        st.caption(
            "AI-assisted interpretation only. "
            "Voice cannot reliably prove a person's true "
            "internal emotional state, personality or diagnosis."
        )


# ============================================================
# MOOD & BEHAVIOUR
# ============================================================

def page_mood():

    st.header(
        "💭 Mood & Feelings"
    )

    mood = st.select_slider(
        "Current mood",
        [
            "Very low",
            "Low",
            "Neutral",
            "Good",
            "Very good",
        ],
        value="Neutral",
    )

    stress = st.slider(
        "Stress",
        0,
        10,
        5,
    )

    energy = st.slider(
        "Energy",
        0,
        10,
        5,
    )

    attention = st.slider(
        "Attention",
        0,
        10,
        5,
    )

    sleep = st.slider(
        "Sleep quality",
        0,
        10,
        5,
    )

    feelings = st.text_area(
        "How are you feeling?"
    )

    if st.button(
        "🤖 Ask Ayna to Reflect",
        type="primary",
        use_container_width=True,
    ):

        answer = ask_ai(
            f"""
Mood: {mood}

Stress:
{stress}/10

Energy:
{energy}/10

Attention:
{attention}/10

Sleep quality:
{sleep}/10

Self-described feelings:
{feelings}

Give an educational reflection.
Do not diagnose.
""",
        )

        st.session_state.mood_result = answer

        st.rerun()

    if st.session_state.mood_result:

        st.markdown(
            st.session_state.mood_result
        )

        browser_speech_button(
            st.session_state.mood_result,
            "🔊 Play Ayna",
        )


# ============================================================
# BRAIN EXERCISES
# ============================================================

def page_exercises():

    st.header(
        "🎮 Brain Exercises"
    )

    exercise = st.selectbox(
        "Choose exercise",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
            "Quick Reaction",
        ],
    )

    if exercise == "Working Memory":

        sequence = "729418"

        if not st.session_state.get(
            "exercise_memory_hidden",
            False,
        ):

            st.code(sequence)

            if st.button(
                "Hide",
                use_container_width=True,
            ):

                st.session_state.exercise_memory_hidden = True
                st.rerun()

        else:

            answer = st.text_input(
                "Enter sequence"
            )

            if st.button(
                "Check",
                use_container_width=True,
            ):

                if answer.strip() == sequence:

                    st.success(
                        "Correct!"
                    )

                    st.session_state.games_completed += 1

                    add_achievement(
                        "Memory Practice"
                    )

                else:

                    st.warning(
                        "Try again."
                    )

    elif exercise == "Attention":

        st.markdown(
            """
            <div class="card center"
                 style="font-size:30px">

            O O O O O<br>
            O O X O O<br>
            O O O O O

            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.text_input(
            "Target"
        )

        if st.button(
            "Check",
            use_container_width=True,
        ):

            if answer.strip().upper() == "X":

                st.success(
                    "Correct!"
                )

                st.session_state.games_completed += 1

                add_achievement(
                    "Attention Practice"
                )

            else:

                st.error(
                    "Target was X."
                )

    elif exercise == "Pattern Recognition":

        st.markdown(
            """
            ###

            2 → 4 → 8 → 16 → 32 → ?

            """
        )

        answer = st.number_input(
            "Answer",
            min_value=0,
            step=1,
        )

        if st.button(
            "Check",
            use_container_width=True,
        ):

            if answer == 64:

                st.success(
                    "Correct!"
                )

                st.session_state.games_completed += 1

                add_achievement(
                    "Pattern Practice"
                )

            else:

                st.warning(
                    "Expected: 64"
                )

    elif exercise == "Decision Challenge":

        choice = st.radio(
            "Choose:",
            [
                "Rs 1,000 today",
                "Rs 1,500 after 30 days",
            ],
        )

        if st.button(
            "Submit",
            use_container_width=True,
        ):

            st.info(
                f"You selected {choice}."
            )

            st.session_state.games_completed += 1

    else:

        st.subheader(
            "⚡ Quick Reaction"
        )

        st.write(
            "Press the button when you are ready."
        )

        if st.button(
            "START",
            use_container_width=True,
        ):

            st.session_state.reaction_started = time.time()

            st.success(
                "STARTED — press STOP!"
            )

        if st.button(
            "STOP",
            use_container_width=True,
        ):

            if hasattr(
                st.session_state,
                "reaction_started",
            ):

                reaction = (
                    time.time()
                    - st.session_state.reaction_started
                )

                st.metric(
                    "Reaction time",
                    f"{reaction:.3f} sec",
                )

                st.session_state.games_completed += 1

                add_achievement(
                    "Reaction Practice"
                )


# ============================================================
# ASK AYNA
# ============================================================

def page_ask_ayna():

    st.header(
        "🤖 Ask Ayna"
    )

    st.caption(
        "Ask questions about cognition, brain science, "
        "behaviour and AI."
    )

    for message in st.session_state.ayna_messages:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    question = st.chat_input(
        "Ask Ayna..."
    )

    if question:

        st.session_state.ayna_messages.append(
            {
                "role":
                    "user",
                "content":
                    question,
            }
        )

        answer = ask_ai(
            question
        )

        st.session_state.ayna_messages.append(
            {
                "role":
                    "assistant",
                "content":
                    answer,
            }
        )

        st.rerun()

    st.divider()

    st.subheader(
        "🎙️ Ask by Voice"
    )

    voice = st.audio_input(
        "Record question",
        sample_rate=16000,
        key="ayna_voice_question",
    )

    if voice:

        st.audio(
            voice
        )

        if st.button(
            "📤 SEND VOICE QUESTION",
            use_container_width=True,
        ):

            if not ai_available():

                st.error(
                    "Gemini is not connected."
                )

            else:

                try:

                    prompt = """
Listen to the user's voice.

First provide a concise transcript.

Then answer the spoken question using
cognitive neuroscience knowledge.

Do not invent unclear words.

Do not diagnose.
"""

                    client = genai.Client(
                        api_key=GEMINI_API_KEY
                    )

                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=[
                            prompt,
                            types.Part.from_bytes(
                                data=voice.getvalue(),
                                mime_type=(
                                    voice.type
                                    or "audio/wav"
                                ),
                            ),
                        ],
                    )

                    answer = getattr(
                        response,
                        "text",
                        "",
                    )

                    st.session_state.ai_requests += 1

                    st.session_state.ayna_messages.append(
                        {
                            "role":
                                "user",
                            "content":
                                "[Voice question]",
                        }
                    )

                    st.session_state.ayna_messages.append(
                        {
                            "role":
                                "assistant",
                            "content":
                                answer,
                        }
                    )

                    st.rerun()

                except Exception:

                    st.error(
                        "Voice question could not be processed."
                    )


# ============================================================
# PRIVATE AYNA
# ============================================================

def pin_hash(
    pin,
    salt,
):

    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt.encode(),
        200000,
    ).hex()


def page_private():

    st.header(
        "🔐 Private Ask Ayna"
    )

    if not st.session_state.private_pin_hash:

        st.subheader(
            "Create Private PIN"
        )

        pin = st.text_input(
            "4–6 digit PIN",
            type="password",
            max_chars=6,
        )

        confirm = st.text_input(
            "Confirm PIN",
            type="password",
            max_chars=6,
        )

        if st.button(
            "Create PIN",
            use_container_width=True,
        ):

            if not re.fullmatch(
                r"\d{4,6}",
                pin or "",
            ):

                st.error(
                    "PIN must contain 4–6 digits."
                )

            elif pin != confirm:

                st.error(
                    "PINs do not match."
                )

            else:

                salt = secrets.token_hex(16)

                st.session_state.private_pin_salt = salt

                st.session_state.private_pin_hash = (
                    pin_hash(
                        pin,
                        salt,
                    )
                )

                st.session_state.private_unlocked = True

                st.success(
                    "Private mode created."
                )

        return

    if not st.session_state.private_unlocked:

        pin = st.text_input(
            "Enter PIN",
            type="password",
            max_chars=6,
        )

        if st.button(
            "Unlock",
            use_container_width=True,
        ):

            if secrets.compare_digest(
                pin_hash(
                    pin,
                    st.session_state.private_pin_salt,
                ),
                st.session_state.private_pin_hash,
            ):

                st.session_state.private_unlocked = True

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )

        return

    st.success(
        "Private mode unlocked."
    )

    question = st.text_area(
        "Private question"
    )

    if st.button(
        "SEND PRIVATE QUESTION",
        use_container_width=True,
    ):

        answer = ask_ai(
            question,
            context="Private Ask Ayna area.",
        )

        st.session_state.private_messages.append(
            {
                "question":
                    question,
                "answer":
                    answer,
            }
        )

        st.rerun()

    for item in st.session_state.private_messages:

        st.markdown(
            "### You"
        )

        st.write(
            item["question"]
        )

        st.markdown(
            "### Ayna"
        )

        st.write(
            item["answer"]
        )

    if st.button(
        "🔒 Lock",
        use_container_width=True,
    ):

        st.session_state.private_unlocked = False

        st.rerun()


# ============================================================
# RESEARCH BOOK
# ============================================================

def page_research():

    st.header(
        "📚 Research Book"
    )

    query = st.text_input(
        "Search Europe PMC",
        placeholder="e.g. attention cognitive neuroscience",
    )

    if st.button(
        "🔎 Search Research",
        use_container_width=True,
    ):

        if not query.strip():

            st.warning(
                "Enter a research topic."
            )

        else:

            import urllib.request
            import urllib.parse

            url = (
                "https://www.ebi.ac.uk/europepmc/webservices/"
                "rest/search?"
                + urllib.parse.urlencode(
                    {
                        "query":
                            query,
                        "format":
                            "json",
                        "pageSize":
                            10,
                    }
                )
            )

            try:

                with urllib.request.urlopen(
                    url,
                    timeout=15,
                ) as response:

                    data = json.loads(
                        response.read().decode()
                    )

                results = data.get(
                    "resultList",
                    {}
                ).get(
                    "result",
                    []
                )

                st.session_state.research_results = results

                st.session_state.research_completed += 1

            except Exception:

                st.error(
                    "Research search failed."
                )

    for paper in st.session_state.research_results:

        title = paper.get(
            "title",
            "Untitled",
        )

        year = paper.get(
            "pubYear",
            "",
        )

        pmid = paper.get(
            "pmid",
            "",
        )

        st.markdown(
            f"""
            <div class="card">

            <h4>
            {safe_html(title)}
            </h4>

            <p>
            Year: {safe_html(year)}
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if pmid:

            st.link_button(
                "Open paper",
                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            )

    st.divider()

    st.subheader(
        "📝 Research Notes"
    )

    note = st.text_area(
        "Write research note"
    )

    if st.button(
        "Save Research Note",
        use_container_width=True,
    ):

        if note.strip():

            st.session_state.research_notes.append(
                {
                    "time":
                        time.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    "note":
                        note.strip(),
                }
            )

            st.success(
                "Note saved."
            )


# ============================================================
# NEUROSOCIAL PROFILE
# ============================================================

def save_username():

    username = re.sub(
        r"[^A-Za-z0-9_.-]",
        "",
        st.session_state.social_username.strip(),
    )

    st.session_state.social_username = (
        username[:30]
    )


def page_social_profile():

    st.subheader(
        "👤 My NeuroSocial Profile"
    )

    st.session_state.social_username = st.text_input(
        "Username",
        value=st.session_state.social_username,
    )

    st.session_state.social_bio = st.text_area(
        "Bio",
        value=st.session_state.social_bio,
        placeholder="Cognitive neuroscience • AI • Brain research",
    )

    st.session_state.social_avatar = st.selectbox(
        "Avatar",
        [
            "🧠",
            "🧑‍🔬",
            "🤖",
            "🔬",
            "👁️",
            "🧬",
        ],
        index=[
            "🧠",
            "🧑‍🔬",
            "🤖",
            "🔬",
            "👁️",
            "🧬",
        ].index(
            st.session_state.social_avatar
        ),
    )

    if st.button(
        "💾 Save Profile",
        use_container_width=True,
    ):

        save_username()

        st.success(
            f"Profile saved as @{st.session_state.social_username}"
        )


# ============================================================
# FIND USERS
# ============================================================

DEMO_USERS = [

    {
        "username":
            "Sarah",
        "avatar":
            "🧑‍🔬",
        "bio":
            "Neuroscience learner",
    },

    {
        "username":
            "NeuroStudent",
        "avatar":
            "🧑‍🎓",
        "bio":
            "Cognition enthusiast",
    },

    {
        "username":
            "BrainExplorer",
        "avatar":
            "🧠",
        "bio":
            "Brain & behaviour",
    },

    {
        "username":
            "AIResearcher",
        "avatar":
            "🤖",
        "bio":
            "AI + neuroscience",
    },

]


def page_find_users():

    st.subheader(
        "🔎 Find People"
    )

    search = st.text_input(
        "Search username",
        value=st.session_state.social_search,
    )

    st.session_state.social_search = search

    if not search:

        users = DEMO_USERS

    else:

        users = [
            u
            for u in DEMO_USERS
            if search.lower()
            in u["username"].lower()
        ]

    for user in users:

        if (
            user["username"]
            == st.session_state.social_username
        ):

            continue

        st.markdown(
            f"""
            <div class="social-card">

            <h3>
            {user["avatar"]}
            @{safe_html(user["username"])}
            </h3>

            <p>
            {safe_html(user["bio"])}
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if user["username"] in st.session_state.friends:

            st.success(
                "Already friends"
            )

        else:

            if st.button(
                f"➕ Send Friend Invite · @{user['username']}",
                key=f"invite_{user['username']}",
                use_container_width=True,
            ):

                if (
                    user["username"]
                    not in st.session_state.sent_requests
                ):

                    st.session_state.sent_requests.append(
                        user["username"]
                    )

                    st.success(
                        f"Friend request sent to @{user['username']}"
                    )


# ============================================================
# FRIEND REQUESTS
# ============================================================

def page_friend_requests():

    st.subheader(
        "🤝 Friend Requests"
    )

    if not st.session_state.incoming_requests:

        st.info(
            "No incoming requests."
        )

    for username in st.session_state.incoming_requests:

        st.markdown(
            f"""
            <div class="social-card">

            <h3>
            🤝 @{safe_html(username)}
            </h3>

            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "✅ Accept",
                key=f"accept_{username}",
                use_container_width=True,
            ):

                if username not in st.session_state.friends:

                    st.session_state.friends.append(
                        username
                    )

                st.session_state.incoming_requests.remove(
                    username
                )

                st.rerun()

        with c2:

            if st.button(
                "❌ Decline",
                key=f"decline_{username}",
                use_container_width=True,
            ):

                st.session_state.incoming_requests.remove(
                    username
                )

                st.rerun()

    st.divider()

    st.subheader(
        "📤 Sent Requests"
    )

    if not st.session_state.sent_requests:

        st.info(
            "No pending sent requests."
        )

    for username in st.session_state.sent_requests:

        st.write(
            f"@{username} · Pending"
        )


# ============================================================
# FRIENDS
# ============================================================

def page_friends():

    st.subheader(
        "👥 My Friends"
    )

    if not st.session_state.friends:

        st.info(
            "Your friends will appear here."
        )

        return

    for friend in st.session_state.friends:

        streak = st.session_state.friend_streaks.get(
            friend,
            0,
        )

        st.markdown(
            f"""
            <div class="social-card">

            <h3>
            🧑‍🤝‍🧑 @{safe_html(friend)}
            </h3>

            <div class="streak">
            🔥 {streak} day streak
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            f"💬 Chat with @{friend}",
            key=f"chat_friend_{friend}",
            use_container_width=True,
        ):

            st.session_state.social_target = friend

            st.session_state.social_social_tab = (
                "Chat"
            )

            st.rerun()


# ============================================================
# FRIEND CHAT
# ============================================================

def friend_message_allowed():

    return bool(
        st.session_state.social_username
        and st.session_state.social_target
    )


def page_friend_chat():

    target = st.session_state.social_target

    if not target:

        st.info(
            "Select a friend first."
        )

        return

    streak = st.session_state.friend_streaks.get(
        target,
        0,
    )

    st.markdown(
        f"""
        <div class="chat-header">

        <h2>
        🧑‍🤝‍🧑 Chat with @{safe_html(target)}
        </h2>

        <div>
        🟢 Online
        &nbsp;&nbsp;
        🔥 {streak}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    messages = [

        m
        for m in st.session_state.social_messages

        if {
            m.get("from"),
            m.get("to"),
        }
        == {
            st.session_state.social_username,
            target,
        }

    ]

    for message in messages:

        is_me = (
            message["from"]
            == st.session_state.social_username
        )

        with st.chat_message(
            "user" if is_me else "assistant"
        ):

            if message.get(
                "type"
            ) == "voice":

                st.audio(
                    message["audio"]
                )

            elif message.get(
                "type"
            ) == "story":

                st.write(
                    "📸 Story"
                )

            elif message.get(
                "type"
            ) == "challenge":

                st.write(
                    "🧠 Challenge invitation"
                )

            else:

                st.write(
                    message.get(
                        "text",
                        "",
                    )
                )

    st.divider()

    text = st.chat_input(
        f"Message @{target}"
    )

    if text:

        st.session_state.social_messages.append(
            {
                "from":
                    st.session_state.social_username,
                "to":
                    target,
                "text":
                    text,
                "type":
                    "text",
                "time":
                    time.time(),
            }
        )

        st.session_state.friend_streaks[
            target
        ] = (
            st.session_state.friend_streaks.get(
                target,
                0,
            )
            + 1
        )

        add_activity(
            "Sent social message",
            f"To @{target}",
        )

        st.rerun()

    st.subheader(
        "🎙️ Voice Message"
    )

    voice = st.audio_input(
        "Record voice message",
        sample_rate=16000,
        key=f"friend_voice_{target}",
    )

    if voice:

        st.audio(
            voice
        )

        if st.button(
            f"🎙️ Send Voice to @{target}",
            use_container_width=True,
        ):

            # Session-level demonstration.
            # Production requires persistent media storage.

            st.session_state.social_messages.append(
                {
                    "from":
                        st.session_state.social_username,
                    "to":
                        target,
                    "type":
                        "voice",
                    "audio":
                        voice.getvalue(),
                    "mime":
                        voice.type
                        or "audio/wav",
                    "time":
                        time.time(),
                }
            )

            st.session_state.friend_streaks[
                target
            ] = (
                st.session_state.friend_streaks.get(
                    target,
                    0,
                )
                + 1
            )

            st.success(
                "Voice message added to this session."
            )

            st.rerun()


# ============================================================
# STORY EDITOR
# ============================================================

def apply_filter(
    image,
    filter_name,
):

    if filter_name == "Original":

        return image

    if filter_name == "Grayscale":

        return ImageOps.grayscale(
            image
        ).convert("RGB")

    if filter_name == "Contrast":

        return ImageEnhance.Contrast(
            image
        ).enhance(1.6)

    if filter_name == "Bright":

        return ImageEnhance.Brightness(
            image
        ).enhance(1.35)

    if filter_name == "Sharp":

        return ImageEnhance.Sharpness(
            image
        ).enhance(2.0)

    return image


def page_story_creator():

    st.subheader(
        "📸 Create Story / Streak"
    )

    image = st.camera_input(
        "Take a picture",
        key="story_camera",
    )

    uploaded = st.file_uploader(
        "Or upload an image",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
    )

    if uploaded:

        image = uploaded

    if image:

        try:

            img = Image.open(
                image
            ).convert("RGB")

            filter_name = st.selectbox(
                "✨ Filter",
                [
                    "Original",
                    "Grayscale",
                    "Contrast",
                    "Bright",
                    "Sharp",
                ],
            )

            edited = apply_filter(
                img,
                filter_name,
            )

            emoji = st.selectbox(
                "Sticker",
                [
                    "🧠",
                    "🔥",
                    "❤️",
                    "😂",
                    "👀",
                    "🤯",
                    "🎯",
                    "🧪",
                ],
            )

            text = st.text_input(
                "Add text"
            )

            st.image(
                edited,
                use_container_width=True,
            )

            st.markdown(
                f"""
                <div class="card center"
                     style="font-size:40px">

                {emoji}

                <br>

                <b>
                {safe_html(text)}
                </b>

                </div>
                """,
                unsafe_allow_html=True,
            )

            target = st.text_input(
                "Send story/streak to friend"
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "📸 Post Story",
                    use_container_width=True,
                ):

                    st.session_state.stories.append(
                        {
                            "owner":
                                st.session_state.social_username,
                            "emoji":
                                emoji,
                            "text":
                                text,
                            "image":
                                edited,
                            "time":
                                time.time(),
                            "reactions":
                                [],
                            "replies":
                                [],
                        }
                    )

                    st.success(
                        "Story created for this session."
                    )

            with c2:

                if st.button(
                    "🔥 Send as Streak",
                    use_container_width=True,
                ):

                    if not target.strip():

                        st.warning(
                            "Enter a friend username."
                        )

                    else:

                        st.session_state.social_messages.append(
                            {
                                "from":
                                    st.session_state.social_username,
                                "to":
                                    target.strip(),
                                "type":
                                    "story",
                                "image":
                                    edited,
                                "emoji":
                                    emoji,
                                "text":
                                    text,
                                "time":
                                    time.time(),
                            }
                        )

                        st.session_state.friend_streaks[
                            target.strip()
                        ] = (
                            st.session_state.friend_streaks.get(
                                target.strip(),
                                0,
                            )
                            + 1
                        )

                        st.success(
                            f"🔥 Sent to @{target}"
                        )

        except Exception:

            st.error(
                "Image could not be processed."
            )


# ============================================================
# STORIES
# ============================================================

def page_stories():

    st.subheader(
        "📸 Stories"
    )

    if not st.session_state.stories:

        st.info(
            "No stories yet."
        )

    for index, story in enumerate(
        reversed(
            st.session_state.stories
        )
    ):

        st.markdown(
            f"""
            <div class="story-card">

            <h3>
            {safe_html(
                story.get(
                    "emoji",
                    "📸"
                )
            )}
            @{safe_html(
                story.get(
                    "owner",
                    "user"
                )
            )}
            </h3>

            <p>
            {safe_html(
                story.get(
                    "text",
                    ""
                )
            )}
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if story.get(
            "image"
        ) is not None:

            st.image(
                story["image"],
                use_container_width=True,
            )

        reaction = st.selectbox(
            "React",
            [
                "❤️",
                "🔥",
                "😂",
                "🤯",
                "👏",
            ],
            key=f"story_reaction_{index}",
        )

        if st.button(
            "React",
            key=f"story_react_{index}",
        ):

            story.setdefault(
                "reactions",
                []
            ).append(
                reaction
            )

            st.success(
                f"Reacted {reaction}"
            )

        reply = st.text_input(
            "Reply",
            key=f"story_reply_{index}",
        )

        if st.button(
            "Send Reply",
            key=f"story_reply_button_{index}",
        ):

            if reply.strip():

                story.setdefault(
                    "replies",
                    []
                ).append(
                    reply.strip()
                )

                st.success(
                    "Reply added."
                )


# ============================================================
# CHALLENGES
# ============================================================

CHALLENGES = {

    "Attention Hunt":
        "Busy scene → identify target signal → solve attention puzzle.",

    "Memory Mission":
        "View objects briefly → remember them → solve recall puzzle.",

    "Reaction Race":
        "Respond to a changing target as quickly as possible.",

    "Pattern Lock":
        "Discover the sequence → unlock the pattern.",

    "Decision & Reward":
        "Make a reward decision → solve the related decision puzzle.",

    "Mystery Case":
        "Inspect clues → select relevant evidence → solve the puzzle.",

    "Stroop Challenge":
        "Resolve word/colour conflict → complete cognitive-control puzzle.",

    "Logic Puzzle":
        "Interpret the situation → solve the logical puzzle.",
}


def page_challenges():

    st.subheader(
        "🧠 Neuro Challenges"
    )

    target = st.text_input(
        "Friend username",
        value=st.session_state.social_target,
    )

    challenge = st.selectbox(
        "Challenge type",
        list(CHALLENGES.keys()),
    )

    st.markdown(
        f"""
        <div class="challenge-card">

        <h3>
        {safe_html(challenge)}
        </h3>

        <p>
        {safe_html(
            CHALLENGES[challenge]
        )}
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    situation = st.text_area(
        "Situation for your friend",
        placeholder=(
            "Example: You enter a busy room. "
            "Several objects and signals appear. "
            "Find the relevant target."
        ),
    )

    if st.button(
        "📤 Send Challenge",
        type="primary",
        use_container_width=True,
    ):

        if not target.strip():

            st.warning(
                "Enter friend username."
            )

        else:

            challenge_data = {

                "id":
                    secrets.token_hex(6),

                "from":
                    st.session_state.social_username,

                "to":
                    target.strip(),

                "type":
                    challenge,

                "situation":
                    situation.strip(),

                "status":
                    "Pending",

                "score":
                    None,

                "time":
                    time.time(),
            }

            st.session_state.social_challenges.append(
                challenge_data
            )

            st.success(
                f"Challenge sent to @{target}"
            )

    st.divider()

    st.subheader(
        "📥 Challenge Invitations"
    )

    for challenge_data in (
        st.session_state.social_challenges
    ):

        if (
            challenge_data["to"]
            != st.session_state.social_username
        ):

            continue

        if challenge_data["status"] != "Pending":

            continue

        st.markdown(
            f"""
            <div class="challenge-card">

            <h3>
            🧠 {safe_html(
                challenge_data["type"]
            )}
            </h3>

            <p>
            From:
            @{safe_html(
                challenge_data["from"]
            )}
            </p>

            <p>
            {safe_html(
                challenge_data["situation"]
            )}
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "✅ Accept",
                key=f"challenge_accept_{challenge_data['id']}",
                use_container_width=True,
            ):

                challenge_data["status"] = "Accepted"

                st.session_state.active_challenge = (
                    challenge_data
                )

                st.rerun()

        with c2:

            if st.button(
                "❌ Decline",
                key=f"challenge_decline_{challenge_data['id']}",
                use_container_width=True,
            ):

                challenge_data["status"] = "Declined"

                st.rerun()

    if st.session_state.active_challenge:

        run_active_challenge()


def run_active_challenge():

    challenge = (
        st.session_state.active_challenge
    )

    st.divider()

    st.subheader(
        f"🎮 {challenge['type']}"
    )

    st.markdown(
        f"""
        <div class="challenge-card">

        <h3>
        Situation
        </h3>

        <p>
        {safe_html(
            challenge["situation"]
        )}
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "### ❓ Question / Decision"
    )

    if challenge["type"] == "Attention Hunt":

        answer = st.radio(
            "Which signal should you follow?",
            [
                "Target X",
                "Distractor O",
                "Ignore everything",
            ],
        )

        correct = (
            answer
            == "Target X"
        )

    elif challenge["type"] == "Memory Mission":

        st.code(
            "🧠 🔴 ⭐ 🟢 🔺"
        )

        answer = st.text_input(
            "Which symbol appeared after the red circle?"
        )

        correct = (
            answer.strip()
            == "⭐"
        )

    elif challenge["type"] == "Decision & Reward":

        answer = st.radio(
            "Which option has the delayed reward?",
            [
                "Rs 1,000 now",
                "Rs 1,500 later",
            ],
        )

        correct = (
            answer
            == "Rs 1,500 later"
        )

    elif challenge["type"] == "Pattern Lock":

        answer = st.number_input(
            "2 → 4 → 8 → 16 → ?",
            min_value=0,
            step=1,
        )

        correct = (
            answer == 32
        )

    elif challenge["type"] == "Stroop Challenge":

        answer = st.radio(
            "The word says RED but the ink is BLUE. "
            "What should you report?",
            [
                "RED",
                "BLUE",
            ],
        )

        correct = (
            answer == "BLUE"
        )

    elif challenge["type"] == "Reaction Race":

        answer = st.radio(
            "Target appears. What should you do?",
            [
                "Press immediately",
                "Wait",
            ],
        )

        correct = (
            answer
            == "Press immediately"
        )

    elif challenge["type"] == "Mystery Case":

        answer = st.radio(
            "Which clue is directly relevant?",
            [
                "The unusual signal",
                "Wall colour",
                "Background music",
            ],
        )

        correct = (
            answer
            == "The unusual signal"
        )

    else:

        answer = st.radio(
            "Which rule solves the sequence?",
            [
                "Double each number",
                "Subtract 2",
                "Random pattern",
            ],
        )

        correct = (
            answer
            == "Double each number"
        )

    if st.button(
        "🧩 SUBMIT PUZZLE",
        type="primary",
        use_container_width=True,
    ):

        score = 100 if correct else 50

        challenge["score"] = score

        challenge["status"] = "Completed"

        st.success(
            f"Challenge complete — score: {score}"
        )

        st.info(
            "Score reflects this task only. "
            "It does not determine intelligence or "
            "overall cognitive ability."
        )

        if st.button(
            "🔁 Rematch",
            use_container_width=True,
        ):

            challenge["status"] = "Pending"

            challenge["score"] = None

            st.session_state.active_challenge = None

            st.rerun()


# ============================================================
# CHESS
# ============================================================

def initial_chess_board():

    return [

        list("♜♞♝♛♚♝♞♜"),

        list("♟♟♟♟♟♟♟♟"),

        [""] * 8,

        [""] * 8,

        [""] * 8,

        [""] * 8,

        list("♙♙♙♙♙♙♙♙"),

        list("♖♘♗♕♔♗♘♖"),

    ]


def page_chess():

    st.subheader(
        "♟️ Chess"
    )

    st.caption(
        "Interactive board prototype. "
        "Persistent realtime multiplayer requires backend game-state sync."
    )

    if (
        not st.session_state.social_game
        or st.session_state.social_game.get(
            "type"
        ) != "chess"
    ):

        st.session_state.social_game = {
            "type":
                "chess",
            "board":
                initial_chess_board(),
            "turn":
                "white",
        }

    board = st.session_state.social_game[
        "board"
    ]

    for row in range(8):

        cols = st.columns(8)

        for col in range(8):

            piece = board[row][col]

            with cols[col]:

                if st.button(
                    piece or "·",
                    key=f"chess_{row}_{col}",
                    use_container_width=True,
                ):

                    st.session_state.chess_selected = (
                        row,
                        col,
                    )

    selected = st.session_state.get(
        "chess_selected"
    )

    if selected:

        st.info(
            f"Selected square: "
            f"{selected[0] + 1}, "
            f"{selected[1] + 1}"
        )

        st.write(
            "Select another square to define "
            "a move in the UI prototype."
        )

        if st.button(
            "Clear Selection",
            use_container_width=True,
        ):

            st.session_state.chess_selected = None

            st.rerun()


# ============================================================
# LUDO
# ============================================================

def page_ludo():

    st.subheader(
        "🎲 Ludo-style Game"
    )

    if (
        not st.session_state.social_game
        or st.session_state.social_game.get(
            "type"
        ) != "ludo"
    ):

        st.session_state.social_game = {
            "type":
                "ludo",
            "position":
                0,
        }

    st.markdown(
        """
        <div class="game-card center">

        🔴 🟢 🔵 🟡

        <br><br>

        🏠 ─── 🎯

        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🎲 Roll Dice",
        type="primary",
        use_container_width=True,
    ):

        roll = random.randint(
            1,
            6,
        )

        st.session_state.social_game[
            "position"
        ] += roll

        st.success(
            f"You rolled {roll}."
        )

    st.metric(
        "Your position",
        st.session_state.social_game[
            "position"
        ],
    )


# ============================================================
# EXTERNAL INVITE
# ============================================================

def page_external_invite():

    st.subheader(
        "📨 Invite Friends"
    )

    username = (
        st.session_state.social_username
        or "yourusername"
    )

    invite_url = (
        "https://neuro-lens-ayna.streamlit.app/"
        "?join=1&ref="
        + username
    )

    message = (
        f"Join me on NEUROLENS — "
        f"explore cognition, play brain challenges "
        f"and connect with friends!\n\n"
        f"{invite_url}"
    )

    st.text_area(
        "Your personal invite message",
        value=message,
        height=130,
    )

    st.markdown(
        "### Share"
    )

    encoded = (
        urlencode(
            {
                "text":
                    message
            }
        )
    )

    whatsapp = (
        "https://wa.me/?"
        + encoded
    )

    telegram = (
        "https://t.me/share/url?"
        + urlencode(
            {
                "url":
                    invite_url,
                "text":
                    message,
            }
        )
    )

    email = (
        "mailto:?"
        + urlencode(
            {
                "subject":
                    "Join NEUROLENS",
                "body":
                    message,
            }
        )
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.link_button(
            "WhatsApp",
            whatsapp,
            use_container_width=True,
        )

    with c2:

        st.link_button(
            "Telegram",
            telegram,
            use_container_width=True,
        )

    with c3:

        st.link_button(
            "Email",
            email,
            use_container_width=True,
        )

    st.link_button(
        "📸 Instagram",
        "https://www.instagram.com/",
        use_container_width=True,
    )

    st.link_button(
        "👻 Snapchat",
        "https://www.snapchat.com/",
        use_container_width=True,
    )

    st.link_button(
        "💬 SMS",
        "sms:?body="
        + message.replace(
            " ",
            "%20",
        ),
        use_container_width=True,
    )

    components.html(
        f"""
        <button
            onclick="
                navigator.clipboard.writeText(
                    {json.dumps(invite_url)}
                );
                alert('Invite link copied');
            "
            style="
                width:100%;
                padding:12px;
                border-radius:12px;
                border:1px solid #777;
                background:transparent;
                color:inherit;
            "
        >
            📋 Copy Invite Link
        </button>
        """,
        height=60,
    )

    components.html(
        f"""
        <button
            onclick="
                if (navigator.share) {{
                    navigator.share({{
                        title:'NEUROLENS',
                        text:{json.dumps(message)},
                        url:{json.dumps(invite_url)}
                    }});
                }} else {{
                    navigator.clipboard.writeText(
                        {json.dumps(invite_url)}
                    );
                    alert('Link copied');
                }}
            "
            style="
                width:100%;
                padding:12px;
                border-radius:12px;
                border:1px solid #777;
                background:rgba(70,120,255,.12);
                color:inherit;
            "
        >
            📤 Native Share
        </button>
        """,
        height=60,
    )

    st.caption(
        "NEUROLENS can generate/share an invitation link. "
        "It cannot automatically send a private DM inside "
        "Instagram, Snapchat or WhatsApp without the "
        "platform's permitted API."
    )


# ============================================================
# NEUROSOCIAL MAIN
# ============================================================

def page_neurosocial():

    st.header(
        "👥 NeuroSocial"
    )

    if not st.session_state.social_username:

        st.info(
            "Create your NeuroSocial profile first."
        )

        page_social_profile()

        return

    tabs = st.tabs(
        [
            "👤 Profile",
            "🔎 Find People",
            "🤝 Requests",
            "👥 Friends",
            "💬 Chat",
            "📸 Stories",
            "🧠 Challenges",
            "♟️ Chess",
            "🎲 Ludo",
            "📨 Invite",
        ]
    )

    with tabs[0]:

        page_social_profile()

    with tabs[1]:

        page_find_users()

    with tabs[2]:

        page_friend_requests()

    with tabs[3]:

        page_friends()

    with tabs[4]:

        if st.session_state.friends:

            selected = st.selectbox(
                "Choose friend",
                st.session_state.friends,
                index=(
                    st.session_state.friends.index(
                        st.session_state.social_target
                    )
                    if st.session_state.social_target
                    in st.session_state.friends
                    else 0
                ),
            )

            st.session_state.social_target = selected

            page_friend_chat()

        else:

            st.info(
                "Add a friend to start chatting."
            )

    with tabs[5]:

        page_story_creator()

        st.divider()

        page_stories()

    with tabs[6]:

        page_challenges()

    with tabs[7]:

        page_chess()

    with tabs[8]:

        page_ludo()

    with tabs[9]:

        page_external_invite()


# ============================================================
# EYE TRACKING
# ============================================================

def page_eye_tracking():

    st.header(
        "👁️ Eye Tracking Lab"
    )

    st.caption(
        "Webcam-based gaze estimation. "
        "This is not research-grade eye tracking."
    )

    if (
        webrtc_streamer is None
        or mp is None
        or cv2 is None
        or av is None
    ):

        st.warning(
            "Camera dependencies are not installed."
        )

        return

    class GazeProcessor(
        VideoProcessorBase
    ):

        def __init__(self):

            self.samples = []

            self.mesh = (
                mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
            )

        def recv(self, frame):

            img = frame.to_ndarray(
                format="bgr24"
            )

            rgb = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2RGB,
            )

            result = self.mesh.process(
                rgb
            )

            if result.multi_face_landmarks:

                landmarks = (
                    result
                    .multi_face_landmarks[0]
                    .landmark
                )

                ids = [
                    468,
                    469,
                    470,
                    471,
                    472,
                    473,
                    474,
                    475,
                    476,
                    477,
                ]

                points = [
                    (
                        landmarks[i].x,
                        landmarks[i].y,
                    )
                    for i in ids
                    if i < len(landmarks)
                ]

                if points:

                    x = sum(
                        p[0]
                        for p in points
                    ) / len(points)

                    y = sum(
                        p[1]
                        for p in points
                    ) / len(points)

                    self.samples.append(
                        (
                            time.time(),
                            x,
                            y,
                        )
                    )

                    self.samples = (
                        self.samples[-300:]
                    )

            return av.VideoFrame.from_ndarray(
                img,
                format="bgr24",
            )

    context = webrtc_streamer(
        key="neurolens_eye",
        video_processor_factory=GazeProcessor,
        media_stream_constraints={
            "video": True,
            "audio": False,
        },
        async_processing=True,
    )

    if context and context.video_processor:

        samples = list(
            context.video_processor.samples
        )

        st.metric(
            "Gaze samples",
            len(samples),
        )

        if samples and go:

            start = samples[0][0]

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=[
                        s[0] - start
                        for s in samples
                    ],
                    y=[
                        s[1]
                        for s in samples
                    ],
                    name="Gaze X",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=[
                        s[0] - start
                        for s in samples
                    ],
                    y=[
                        s[2]
                        for s in samples
                    ],
                    name="Gaze Y",
                )
            )

            fig.update_layout(
                height=320,
                title="Normalized webcam gaze",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# ============================================================
# EEG / BIOSIGNAL
# ============================================================

def synthetic_eeg():

    if (
        BoardShim is None
        or BoardIds is None
    ):

        return None

    try:

        params = BrainFlowInputParams()

        board_id = (
            BoardIds.SYNTHETIC_BOARD.value
        )

        board = BoardShim(
            board_id,
            params,
        )

        board.prepare_session()

        board.start_stream()

        time.sleep(2)

        data = board.get_current_board_data(
            512
        )

        board.stop_stream()

        board.release_session()

        return data

    except Exception:

        return None


def page_eeg():

    st.header(
        "🧠 EEG / Biosignal Lab"
    )

    st.warning(
        "Synthetic EEG is for education/development. "
        "It is NOT your brain activity."
    )

    if st.button(
        "▶️ Generate Synthetic EEG",
        use_container_width=True,
    ):

        data = synthetic_eeg()

        if data is None:

            st.error(
                "BrainFlow is unavailable."
            )

        else:

            st.success(
                "Synthetic EEG generated."
            )

            if go:

                channel = data[0]

                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        y=channel[
                            -500:
                        ],
                        mode="lines",
                    )
                )

                fig.update_layout(
                    height=300,
                    title="Synthetic EEG waveform",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )


# ============================================================
# PROGRESS
# ============================================================

def page_progress():

    st.header(
        "📊 My Progress"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Games",
        st.session_state.games_completed,
    )

    c2.metric(
        "Lab",
        st.session_state.lab_completed,
    )

    c3.metric(
        "Research",
        st.session_state.research_completed,
    )

    c4.metric(
        "AI Requests",
        st.session_state.ai_requests,
    )

    st.divider()

    st.subheader(
        "🏆 Achievements"
    )

    if not st.session_state.achievements:

        st.info(
            "Complete activities to unlock achievements."
        )

    for achievement in (
        st.session_state.achievements
    ):

        st.success(
            f"🏆 {achievement}"
        )

    st.divider()

    if go:

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=[
                    "Games",
                    "Lab",
                    "Research",
                    "AI",
                ],
                y=[
                    st.session_state.games_completed,
                    st.session_state.lab_completed,
                    st.session_state.research_completed,
                    st.session_state.ai_requests,
                ],
            )
        )

        fig.update_layout(
            title="NEUROLENS Activity",
            height=350,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.subheader(
        "📝 Activity History"
    )

    if st.session_state.activity_log:

        st.dataframe(
            st.session_state.activity_log,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No activity yet."
        )


# ============================================================
# CONSULTATION / BEHAVIOUR DECODING
# ============================================================

PRICES = [

    (
        "20 minutes",
        1000,
        8,
    ),

    (
        "30 minutes",
        1500,
        10,
    ),

    (
        "45 minutes",
        2000,
        12,
    ),

    (
        "Advice / Consultation",
        1500,
        10,
    ),

]


def valid_phone(
    phone
):

    return bool(
        re.fullmatch(
            r"[+]?[0-9][0-9\s\-]{7,17}",
            phone.strip(),
        )
    )


def page_consultation():

    st.header(
        "🧠 Behaviour Decoding · 1-to-1"
    )

    st.markdown(
        """
        <div class="card">

        <h3>
        Session Pricing
        </h3>

        <p>
        These are introductory consultation prices.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    for label, pkr, usd in PRICES:

        st.write(
            f"**{label}:** "
            f"PKR {pkr:,} · "
            f"International ${usd}"
        )

    st.divider()

    with st.form(
        "consultation_form"
    ):

        name = st.text_input(
            "Name"
        )

        phone = st.text_input(
            "Contact number"
        )

        topic = st.text_area(
            "Discussion topic"
        )

        slot = st.selectbox(
            "Preferred slot",
            [
                "Morning",
                "Afternoon",
                "Evening",
            ],
        )

        submitted = st.form_submit_button(
            "📋 Submit Request",
            use_container_width=True,
        )

    if submitted:

        if not name.strip():

            st.error(
                "Enter your name."
            )

        elif not valid_phone(
            phone
        ):

            st.error(
                "Enter a valid contact number."
            )

        elif not topic.strip():

            st.error(
                "Enter discussion topic."
            )

        else:

            st.session_state.forum_name = name

            st.session_state.forum_phone = phone

            st.session_state.forum_problem = topic

            st.session_state.forum_slot = slot

            st.session_state.forum_status = (
                "Request submitted"
            )

            st.success(
                "Request saved."
            )

    if (
        st.session_state.forum_status
        == "Not started"
    ):

        return

    st.divider()

    st.subheader(
        "💳 Payment"
    )

    method = st.radio(
        "Payment method",
        [
            "🇵🇰 Easypaisa",
            "🌍 International Payment",
        ],
    )

    if method == "🇵🇰 Easypaisa":

        if EASYPAISA_NUMBER:

            st.write(
                "Easypaisa account:"
            )

            st.code(
                EASYPAISA_NUMBER
            )

            st.write(
                f"Account name: "
                f"{EASYPAISA_NAME}"
            )

        else:

            st.warning(
                "Easypaisa is not configured."
            )

        reference = st.text_input(
            "Transaction/reference ID"
        )

        if st.button(
            "Submit Payment Reference",
            use_container_width=True,
        ):

            if reference.strip():

                st.session_state.forum_transaction_id = (
                    reference.strip()
                )

                st.session_state.forum_payment_status = (
                    "Pending verification"
                )

                st.success(
                    "Payment reference submitted."
                )

            else:

                st.error(
                    "Enter reference ID."
                )

    else:

        if INTERNATIONAL_PAYMENT_URL:

            st.link_button(
                "💳 Open International Payment",
                INTERNATIONAL_PAYMENT_URL,
                use_container_width=True,
            )

        else:

            st.warning(
                "International payment URL is not configured."
            )

        reference = st.text_input(
            "International payment reference"
        )

        if st.button(
            "Submit International Reference",
            use_container_width=True,
        ):

            if reference.strip():

                st.session_state.forum_transaction_id = (
                    reference.strip()
                )

                st.session_state.forum_payment_status = (
                    "Pending verification"
                )

                st.success(
                    "Reference submitted."
                )

            else:

                st.error(
                    "Enter reference."
                )

    st.divider()

    status = (
        st.session_state.forum_payment_status
    )

    st.write(
        f"Payment status: **{status}**"
    )

    st.caption(
        "A reference ID does not itself verify payment. "
        "Automatic verification requires an official "
        "payment-provider API/webhook."
    )


# ============================================================
# PAYMENT DEVELOPMENT PAGE
# ============================================================

def page_payment_demo():

    st.header(
        "🧾 Payment Verification · Development"
    )

    if not PAYMENT_ADMIN_KEY:

        st.info(
            "PAYMENT_ADMIN_KEY is not configured."
        )

        return

    key = st.text_input(
        "Developer key",
        type="password",
    )

    if not secrets.compare_digest(
        key or "",
        PAYMENT_ADMIN_KEY,
    ):

        return

    if st.button(
        "🧪 Mark Latest Payment Verified",
        use_container_width=True,
    ):

        if (
            st.session_state.forum_transaction_id
        ):

            st.session_state.forum_payment_status = (
                "Verified"
            )

            st.success(
                "Development verification applied."
            )

        else:

            st.warning(
                "No payment reference."
            )


# ============================================================
# SECURITY
# ============================================================

def page_security():

    st.header(
        "🛡️ Security & Privacy Center"
    )

    st.markdown(
        """
        <div class="card">

        <h3>🔑 API Key Protection</h3>

        <p>
        Gemini API keys should be stored in Streamlit
        Secrets and never hard-coded in the source code.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card">

        <h3>🔐 Private PIN</h3>

        <p>
        The Private Ask Ayna PIN uses salted PBKDF2-HMAC-SHA256
        hashing in the current session.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card">

        <h3>🤖 AI Safety</h3>

        <p>
        AI responses are educational. Voice and game results
        are not clinical measurements and should not be used
        as diagnoses.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card">

        <h3>👥 Social Privacy</h3>

        <p>
        The current social prototype stores messages in
        Streamlit session state. Production deployment should
        use authenticated users, encrypted transport,
        persistent database storage and secure media storage.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card">

        <h3>💳 Payment Security</h3>

        <p>
        Never treat a user-entered transaction ID as proof
        of payment. Production payment access should use
        provider-side verification/webhooks.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SYSTEM HEALTH
# ============================================================

def page_system_health():

    st.header(
        "🛠️ System Health"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Errors",
        len(st.session_state.health_log),
    )

    c2.metric(
        "Recovery attempts",
        st.session_state.heal_attempts,
    )

    c3.metric(
        "Recovered",
        st.session_state.heal_recovered,
    )

    checks = [

        (
            "Gemini AI",
            ai_available(),
        ),

        (
            "Brain image",
            bool(
                find_asset(
                    "brain.png"
                )
            ),
        ),

        (
            "DND package",
            dnd is not None,
        ),

        (
            "Camera stack",
            webrtc_streamer is not None,
        ),

        (
            "BrainFlow",
            BoardShim is not None,
        ),

    ]

    for name, available in checks:

        st.write(
            (
                "🟢"
                if available
                else "🟡"
            ),
            name,
        )

    if st.session_state.last_error:

        st.warning(
            st.session_state.last_error
        )


# ============================================================
# SETTINGS
# ============================================================

def page_settings():

    st.header(
        "⚙️ Settings"
    )

    st.session_state.language = st.selectbox(
        "Language",
        [
            "English",
            "Roman Urdu",
        ],
        index=[
            "English",
            "Roman Urdu",
        ].index(
            st.session_state.language
        ),
    )

    st.write(
        "Gemini AI:",
        (
            "🟢 Connected"
            if ai_available()
            else
            "🟡 Not connected"
        ),
    )

    st.write(
        f"AI usage: "
        f"{st.session_state.ai_requests}/"
        f"{AI_SESSION_LIMIT}"
    )

    st.divider()

    st.subheader(
        "💳 Payment Configuration"
    )

    st.write(
        "Easypaisa configured:",
        bool(EASYPAISA_NUMBER),
    )

    st.write(
        "International payment configured:",
        bool(
            INTERNATIONAL_PAYMENT_URL
        ),
    )

    st.divider()

    st.subheader(
        "📁 Assets"
    )

    assets = [

        "brain.png",

        "brain_animation.mp4",

        "cognitive_lab_brain.mp4",

        "ayna_robot.png",

        "ayna_reboot_voiced.mp4",

        "neuron.png",

        "synapse.png",

        "pfc.png",

        "hippocampus.png",

        "striatum.png",

        "acc.png",

        "attention_network.png",

    ]

    for asset in assets:

        st.write(
            (
                "✅"
                if find_asset(asset)
                else
                "⚪"
            ),
            asset,
        )

    st.divider()

    if st.button(
        "♻️ Reset Session Progress",
        use_container_width=True,
    ):

        keep = {
            "page",
            "language",
            "social_username",
            "social_bio",
            "social_avatar",
        }

        for key in list(
            st.session_state.keys()
        ):

            if key not in keep:

                del st.session_state[key]

        st.success(
            "Session progress reset."
        )

        st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

render_header()

with st.sidebar:

    st.markdown(
        f"""
        <div style="text-align:center;padding:10px">

        <div style="font-size:45px">
        🧠
        </div>

        <h2>
        {APP_NAME}
        </h2>

        <div class="muted">
        {CREATOR}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    pages = [

        "Welcome",

        "Lab",

        "Brain Journey",

        "Explore Brain",

        "Brain Puzzle",

        "AI Mood & Behaviour",

        "Brain Exercises",

        "Eye Tracking",

        "EEG / Biosignal Lab",

        "NeuroSocial",

        "Ask Ayna",

        "Private Ask Ayna",

        "Research Book",

        "Behaviour Decoding",

        "Payment Demo",

        "My Progress",

        "Security & Privacy",

        "System Health",

        "Settings",

    ]

    selected = st.radio(
        "Navigate",
        pages,
        index=pages.index(
            st.session_state.page
        ),
    )

    if selected != st.session_state.page:

        st.session_state.page = selected

        st.rerun()

    st.divider()

    if st.session_state.social_username:

        st.caption(
            f"👤 @{st.session_state.social_username}"
        )

    st.caption(
        "Explore cognition, behaviour & the brain."
    )


# ============================================================
# ROUTER
# ============================================================

page = st.session_state.page

try:

    if page == "Welcome":

        page_welcome()

    elif page == "Lab":

        page_lab()

    elif page == "Brain Journey":

        page_brain_journey()

    elif page == "Explore Brain":

        page_explore_brain()

    elif page == "Brain Puzzle":

        page_brain_puzzle()

    elif page == "AI Mood & Behaviour":

        tabs = st.tabs(
            [
                "🎙️ Voice Mood",
                "💭 Mood",
                "🧠 Behaviour",
            ]
        )

        with tabs[0]:

            page_voice_mood()

        with tabs[1]:

            page_mood()

        with tabs[2]:

            st.subheader(
                "🧠 Behaviour Snapshot"
            )

            if st.button(
                "Generate Behaviour Snapshot",
                use_container_width=True,
            ):

                answer = ask_ai(
                    """
                    Give a cautious educational summary
                    of cognitive-task behaviour.

                    Discuss attention, memory, reaction and
                    decision behaviour only when supported.

                    Do not diagnose.
                    """
                )

                st.session_state.behaviour_result = answer

            if st.session_state.behaviour_result:

                st.write(
                    st.session_state.behaviour_result
                )

    elif page == "Brain Exercises":

        page_exercises()

    elif page == "Eye Tracking":

        page_eye_tracking()

    elif page == "EEG / Biosignal Lab":

        page_eeg()

    elif page == "NeuroSocial":

        page_neurosocial()

    elif page == "Ask Ayna":

        page_ask_ayna()

    elif page == "Private Ask Ayna":

        page_private()

    elif page == "Research Book":

        page_research()

    elif page == "Behaviour Decoding":

        page_consultation()

    elif page == "Payment Demo":

        page_payment_demo()

    elif page == "My Progress":

        page_progress()

    elif page == "Security & Privacy":

        page_security()

    elif page == "System Health":

        page_system_health()

    elif page == "Settings":

        page_settings()


except Exception as exc:

    st.session_state.heal_attempts += 1

    st.session_state.heal_recovered += 1

    st.session_state.last_error = (
        f"{type(exc).__name__}: {str(exc)}"
    )

    st.session_state.health_log.append(
        {
            "time":
                time.strftime(
                    "%H:%M:%S"
                ),
            "feature":
                page,
            "error":
                str(exc)[:500],
        }
    )

    st.error(
        "This feature encountered an error. "
        "NEUROLENS kept the rest of the application available."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    f"""
    <div
        style="
            text-align:center;
            opacity:.55;
            font-size:13px;
            padding:20px;
        "
    >

    🧠 {APP_NAME}

    <br>

    {TAGLINE}

    <br>

    Created by {CREATOR}

    </div>
    """,
    unsafe_allow_html=True,
)
