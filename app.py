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
from urllib.request import Request, urlopen

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

try:
    import numpy as np
except Exception:
    np = None

try:
    from streamlit_dnd import dnd, apply_move
except Exception:
    dnd = None
    apply_move = None

try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
    import av
    import cv2
    import mediapipe as mp
except Exception:
    webrtc_streamer = None
    VideoProcessorBase = object
    RTCConfiguration = None
    av = None
    cv2 = None
    mp = None

try:
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
    from brainflow.data_filter import DataFilter, WindowOperations
except Exception:
    BoardShim = None
    BrainFlowInputParams = None
    BoardIds = None
    DataFilter = None
    WindowOperations = None

try:
    from google import genai
except Exception:
    genai = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


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
# SECRETS / CONFIG
# ============================================================

def secret(name, default=""):
    try:
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)
    return str(value if value is not None else default).strip()


try:
    from supabase import create_client
except Exception:
    create_client = None


GEMINI_API_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret("GEMINI_MODEL", "gemini-2.5-flash")

SUPABASE_URL = secret("SUPABASE_URL")
SUPABASE_KEY = secret("SUPABASE_KEY")

supabase = None
supabase_error = ""

if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception as exc:
        supabase_error = str(exc)


def supabase_available():
    return supabase is not None


def supabase_status():
    if supabase_available():
        return "🟢 Supabase Connected"

    if not create_client:
        return "🔴 Supabase package missing"

    if not SUPABASE_URL:
        return "🔴 SUPABASE_URL missing"

    if not SUPABASE_KEY:
        return "🔴 SUPABASE_KEY missing"

    return "🔴 Supabase connection failed"


EASYPAISA_NUMBER = secret("EASYPAISA_NUMBER")
EASYPAISA_NAME = secret(
    "EASYPAISA_NAME",
    CREATOR,
)

CONSULTATION_FEE = secret("CONSULTATION_FEE")

INTERNATIONAL_PAYMENT_URL = secret(
    "INTERNATIONAL_PAYMENT_URL"
)

PAYMENT_ADMIN_KEY = secret(
    "PAYMENT_ADMIN_KEY"
)


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

.card,
.small-card,
.hero,
.success-box,
.warning-box {
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,.20);
    background: rgba(128,128,128,.06);
}

.card {
    padding: 22px;
    margin-bottom: 18px;
}

.small-card {
    padding: 15px;
    margin-bottom: 12px;
}

.hero {
    padding: 32px;
    background:
        linear-gradient(
            135deg,
            rgba(50,120,255,.13),
            rgba(100,80,255,.08)
        );
}

.success-box {
    padding: 18px;
    border-color: rgba(50,180,100,.35);
    background: rgba(50,180,100,.08);
}

.warning-box {
    padding: 18px;
    border-color: rgba(240,170,40,.35);
    background: rgba(240,170,40,.08);
}

.muted {
    opacity: .65;
}

.lab-scene {
    border-radius: 22px;
    overflow: hidden;
    border: 1px solid rgba(128,128,128,.25);
}

div.stButton > button {
    border-radius: 12px;
}

@media (max-width: 700px) {

    .neuro-title {
        font-size: 34px;
    }

    .neuro-subtitle {
        font-size: 16px;
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

    # --------------------------------------------------------
    # LAB
    # --------------------------------------------------------

    "character": "Ayna",
    "equipment": "Neural Scanner",
    "experiment": "Attention & Response",

    "experiment_started": False,
    "experiment_completed": False,

    "lab_result": None,
    "lab_followup": False,
    "lab_completed": 0,

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    "ai_requests": 0,
    "ai_history": [],
    "ayna_messages": [],

    # --------------------------------------------------------
    # PRIVATE MODE
    # --------------------------------------------------------

    "private_unlocked": False,
    "private_pin_hash": "",
    "private_pin_salt": "",

    # --------------------------------------------------------
    # FORUM
    # --------------------------------------------------------

    "forum_status": "Not started",
    "forum_payment_method": "",
    "forum_payment_status": "Not submitted",
    "forum_transaction_id": "",

    "forum_name": "",
    "forum_phone": "",
    "forum_problem": "",
    "forum_slot": "",

    "forum_messages": [],

    # --------------------------------------------------------
    # RESEARCH
    # --------------------------------------------------------

    "research_results": [],
    "research_notes": [],
    "research_completed": 0,

    # --------------------------------------------------------
    # MOOD
    # --------------------------------------------------------

    "mood_result": None,

    # --------------------------------------------------------
    # PUZZLE
    # --------------------------------------------------------

    "puzzle_completed": False,
    "puzzle_moves": 0,
    "puzzle_grid": 3,
    "puzzle_tiles": [],
    "puzzle_started_at": 0.0,
    "puzzle_elapsed": 0.0,

    "puzzle_best_time": None,
    "puzzle_best_moves": None,

    "puzzle_round": 1,
    "puzzle_difficulty": "Easy",
    "puzzle_challenge": "Time Challenge",

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    "voice_result": None,
    "eye_samples": [],
    "eeg_history": [],

    # --------------------------------------------------------
    # GENERAL PROGRESS
    # --------------------------------------------------------

    "games_completed": 0,
    "achievements": [],

    "health_log": [],
    "heal_attempts": 0,
    "heal_recovered": 0,
    "last_error": "",

    # --------------------------------------------------------
    # SOCIAL
    # --------------------------------------------------------

    "social_username": "",
    "social_target": "",
    "social_streak": 0,
    "social_last_day": "",

    # --------------------------------------------------------
    # BRAIN JOURNEY
    # --------------------------------------------------------

    "journey_index": 0,

    # --------------------------------------------------------
    # PUZZLE
    # --------------------------------------------------------

    "puzzle_blank": None,
}


for key, value in DEFAULTS.items():

    if key not in st.session_state:
        st.session_state[key] = value


def add_achievement(name):

    if name not in st.session_state.achievements:
        st.session_state.achievements.append(name)


# ============================================================
# ASSET HELPERS
# ============================================================

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


def safe_html_text(text):

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


# ============================================================
# HEADER / VOICE
# ============================================================

def render_header():

    st.markdown(
        f"""
        <div class="hero">

            <div class="neuro-title">
                🧠 {APP_NAME}
            </div>

            <div class="neuro-subtitle">
                Explore cognition, behavior & the brain
            </div>

            <div class="creator">
                Independent cognitive neuroscience research
                project by {CREATOR}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def browser_speech_button(
    text,
    label="🔊 Play Ayna",
):

    safe_text = json.dumps(
        str(text)
    )

    components.html(
        f"""
        <button
            onclick='speakText()'
            style="
                width:100%;
                padding:12px 18px;
                border-radius:12px;
                border:1px solid rgba(128,128,128,.35);
                background:rgba(70,120,255,.12);
                color:inherit;
                cursor:pointer;
                font-size:15px;
            "
        >
            {safe_html_text(label)}
        </button>

        <script>

        function speakText() {{

            const text = {safe_text};

            if (!("speechSynthesis" in window)) {{

                alert(
                    "Browser voice is not supported."
                );

                return;
            }}

            window.speechSynthesis.cancel();

            const u =
                new SpeechSynthesisUtterance(text);

            u.rate = 0.95;
            u.pitch = 1.0;

            window.speechSynthesis.speak(u);
        }}

        </script>
        """,
        height=60,
    )


# ============================================================
# AI ENGINE
# ============================================================

def reset_ai_counter_if_new_day():

    today = date.today().isoformat()

    if "ai_date" not in st.session_state:

        st.session_state.ai_date = today

    if st.session_state.ai_date != today:

        st.session_state.ai_date = today
        st.session_state.ai_requests = 0


reset_ai_counter_if_new_day()


def ai_available():

    return bool(
        GEMINI_API_KEY
        and genai is not None
    )


def ask_ai(
    prompt,
    system_context="",
):

    if (
        st.session_state.ai_requests
        >= AI_SESSION_LIMIT
    ):

        return (
            "AI request limit reached for "
            "today/session. You can continue "
            "using the non-AI features of "
            "NEUROLENS."
        )

    if not ai_available():

        return (
            "Ask Ayna AI is not connected yet. "
            "Add GEMINI_API_KEY to Streamlit "
            "Secrets."
        )

    full_prompt = f"""

You are Ask Ayna, an educational
cognitive neuroscience assistant
inside NEUROLENS.

Creator: Ayna Jaffri.

Topics:

cognitive neuroscience,
attention,
memory,
learning,
emotion,
decision-making,
reward,
perception,
cognitive control,
brain systems,
neuroplasticity,
behavioral neuroscience,
and consciousness.

Rules:

1. Give scientifically grounded
   educational explanations.

2. Do not diagnose medical or
   psychiatric conditions.

3. Do not claim a simple game
   measures brain activity.

4. Distinguish behavioral observations
   from neural measurements.

5. Mention uncertainty where appropriate.

6. Use clear language.

7. Do not invent studies,
   citations or data.

8. Do not pretend to know the user's
   private mental state.

9. Do not infer a diagnosis from
   voice, text or game performance.

10. If a health concern is raised,
    encourage appropriate professional
    advice.

11. If discussing research,
    distinguish established evidence
    from hypotheses.

Preferred language:

{st.session_state.language}

Additional context:

{system_context}

User request:

{prompt}

"""

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
        )

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:

            return (
                "Ayna could not generate "
                "a response right now."
            )

        st.session_state.ai_requests += 1

        st.session_state.ai_history.append(
            {
                "prompt": prompt,
                "response": text,
                "time": time.time(),
            }
        )

        return text

    except Exception:

        return (
            "Ayna is temporarily unavailable. "
            "Please check the Gemini API "
            "key/model configuration and "
            "try again later."
        )
        # ============================================================
# WELCOME / Ayna INTRO
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

        try:
            st.video(video)
        except Exception:
            st.warning(
                "Ayna intro video could not be displayed."
            )

    else:

        st.markdown(
            """
            <div class="hero">

                <h2>👋 Welcome to NeuroLens</h2>

                <p>
                I’m Ayna. Let's explore the brain,
                behaviour, and cognition together.
                </p>

                <p class="muted">
                Add the Ayna reboot video inside
                <b>assets/</b> to enable the intro animation.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="card">

            <h2>Explore the brain interactively</h2>

            <p>
            NEUROLENS combines cognitive tasks,
            neuroscience education, AI-assisted
            explanations and research exploration.
            </p>

            <p>
            You can explore attention, memory,
            decision-making, cognitive control,
            neural signaling and brain systems.
            </p>

            <p class="muted">
            Educational simulations are not clinical
            assessments and do not directly measure
            brain activity.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    language_options = [
        "English",
        "Roman Urdu",
    ]

    current_language = (
        st.session_state.language
        if st.session_state.language in language_options
        else "English"
    )

    selected_language = st.selectbox(
        "🌐 Interface / AI language",
        language_options,
        index=language_options.index(
            current_language
        ),
    )

    st.session_state.language = selected_language

    st.markdown("### 🚀 Ready?")

    if st.button(
        "🚀 Enter NEUROLENS",
        use_container_width=True,
    ):

        st.session_state.page = "Lab"

        st.rerun()


# ============================================================
# COGNITIVE LAB
# ============================================================

LAB_CHARACTERS = {

    "Researcher": {
        "emoji": "🧑‍🔬",
        "description":
            "Runs and interprets cognitive experiments.",
    },

    "Student": {
        "emoji": "🎓",
        "description":
            "Learns through interactive experiments.",
    },

    "Lab Assistant": {
        "emoji": "🧪",
        "description":
            "Monitors experimental tasks and observations.",
    },

    "AI Research Agent": {
        "emoji": "🤖",
        "description":
            "Provides AI-assisted explanations.",
    },

}


LAB_EQUIPMENT = {

    "EEG Simulator":
        "🧠 Conceptual neural-signal visualization",

    "Eye Tracker":
        "👁️ Visual attention demonstration",

    "Reaction-Time System":
        "⚡ Behavioral reaction-time task",

    "Cognitive Task Monitor":
        "🖥️ Cognitive task interface",

    "Physiological Sensor":
        "❤️ Educational physiological-signal concept",

}


LAB_EXPERIMENTS = {

    "Attention": {
        "emoji": "🎯",
        "description":
            "Selective attention and target detection.",
    },

    "Memory": {
        "emoji": "🧠",
        "description":
            "Short-term sequence memory.",
    },

    "Decision & Reward": {
        "emoji": "💰",
        "description":
            "Immediate versus delayed reward.",
    },

    "Stroop-Cognitive Control": {
        "emoji": "🎨",
        "description":
            "Interference and cognitive control.",
    },

    "Pattern Recognition": {
        "emoji": "🔢",
        "description":
            "Detect a rule in a changing sequence.",
    },

}


def lab_visual():

    character = st.session_state.character
    equipment = st.session_state.equipment
    experiment = st.session_state.experiment

    character_data = LAB_CHARACTERS.get(
        character,
        LAB_CHARACTERS["Researcher"],
    )

    equipment_text = LAB_EQUIPMENT.get(
        equipment,
        "",
    )

    experiment_data = LAB_EXPERIMENTS.get(
        experiment,
        {},
    )

    st.markdown(
        f"""
        <div class="card">

            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:20px;
                flex-wrap:wrap;
            ">

                <div>

                    <div style="font-size:70px;">
                        {character_data["emoji"]}
                    </div>

                    <h3>
                        {safe_html_text(character)}
                    </h3>

                    <p class="muted">
                        {safe_html_text(
                            character_data["description"]
                        )}
                    </p>

                </div>

                <div style="
                    text-align:center;
                    min-width:150px;
                ">

                    <div style="font-size:70px;">
                        {experiment_data.get(
                            "emoji",
                            "🧪"
                        )}
                    </div>

                    <strong>
                        {safe_html_text(experiment)}
                    </strong>

                </div>

                <div>

                    <div style="
                        font-size:55px;
                        text-align:center;
                    ">
                        🔬
                    </div>

                    <strong>
                        {safe_html_text(equipment)}
                    </strong>

                    <p class="muted">
                        {safe_html_text(
                            equipment_text
                        )}
                    </p>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def reset_lab():

    st.session_state.experiment_started = False
    st.session_state.experiment_completed = False
    st.session_state.lab_result = None
    st.session_state.lab_followup = False

    st.session_state.memory_reveal_hidden = False

    st.session_state.lab_answer = ""

    st.session_state.pattern_answer = ""

    st.session_state.stroop_answer = ""

    st.session_state.decision_answer = ""


def finish_lab(result):

    st.session_state.lab_result = result
    st.session_state.experiment_completed = True
    st.session_state.lab_completed += 1

    add_achievement(
        "Cognitive Lab Explorer"
    )


def attention_experiment():

    st.subheader(
        "🎯 Attention & Response"
    )

    st.write(
        "Find the target X among distractors."
    )

    grid = [
        ["O", "O", "O", "O", "O"],
        ["O", "O", "O", "O", "O"],
        ["O", "O", "X", "O", "O"],
        ["O", "O", "O", "O", "O"],
        ["O", "O", "O", "O", "O"],
    ]

    grid_text = "\n".join(
        " ".join(row)
        for row in grid
    )

    st.code(grid_text)

    answer = st.text_input(
        "What was the target?",
        key="lab_answer",
    )

    if st.button(
        "Check Attention",
        key="lab_check_attention",
        use_container_width=True,
    ):

        if answer.strip().upper() == "X":

            finish_lab(
                "Correct. You identified the target X. "
                "This demonstrates a simple form of "
                "selective visual attention."
            )

        else:

            finish_lab(
                "The target was X. The task demonstrates "
                "how attention can prioritize relevant "
                "information among distractors."
            )

        st.rerun()


def memory_experiment():

    st.subheader(
        "🧠 Memory Sequence"
    )

    sequence = "729418"

    if not st.session_state.memory_reveal_hidden:

        st.write(
            "Study the sequence carefully."
        )

        st.code(
            sequence
        )

        if st.button(
            "🙈 Hide Sequence",
            key="hide_memory_sequence",
            use_container_width=True,
        ):

            st.session_state.memory_reveal_hidden = True

            st.session_state.memory_started_at = (
                time.time()
            )

            st.rerun()

    else:

        st.success(
            "Sequence hidden. Now reproduce it."
        )

        answer = st.text_input(
            "Enter the sequence from memory",
            key="memory_recall_answer",
        )

        if st.button(
            "Check Memory",
            key="check_memory_sequence",
            use_container_width=True,
        ):

            if answer.strip() == sequence:

                finish_lab(
                    "Accurate recall. You reproduced "
                    "the sequence correctly. This is a "
                    "behavioral memory demonstration, "
                    "not a direct measurement of neural activity."
                )

            else:

                finish_lab(
                    "The target sequence was 729418. "
                    "Working-memory performance can be "
                    "affected by attention, interference "
                    "and task demands."
                )

            st.session_state.memory_reveal_hidden = False

            st.rerun()


def decision_experiment():

    st.subheader(
        "💰 Decision & Reward"
    )

    st.write(
        "Choose between an immediate and delayed reward."
    )

    choice = st.radio(
        "Your choice:",
        [
            "Rs 1,000 today",
            "Rs 1,500 after 30 days",
        ],
        key="decision_answer",
    )

    if st.button(
        "Submit Decision",
        key="submit_decision",
        use_container_width=True,
    ):

        finish_lab(
            f"You selected **{choice}**. "
            "This task illustrates intertemporal choice, "
            "where immediate and delayed rewards are compared."
        )

        st.rerun()


def stroop_experiment():

    st.subheader(
        "🎨 Stroop Cognitive Control"
    )

    st.write(
        "Identify the ink colour, not the written word."
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:28px;
            border-radius:18px;
            border:1px solid rgba(128,128,128,.25);
            margin:15px 0;
        ">

            <div style="
                font-size:46px;
                font-weight:800;
                color:#246BCE;
            ">
                RED
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.selectbox(
        "Ink colour:",
        [
            "BLUE",
            "RED",
            "GREEN",
            "YELLOW",
        ],
        key="stroop_answer",
    )

    if st.button(
        "Submit Stroop",
        key="submit_stroop",
        use_container_width=True,
    ):

        if answer == "BLUE":

            finish_lab(
                "Correct. The ink colour was BLUE. "
                "The mismatch between the written word "
                "and ink colour creates interference."
            )

        else:

            finish_lab(
                "The ink colour was BLUE. "
                "This task demonstrates cognitive interference "
                "and the need for cognitive control."
            )

        st.rerun()


def pattern_experiment():

    st.subheader(
        "🔢 Pattern Recognition"
    )

    st.write(
        "Identify the next number in the sequence."
    )

    st.code(
        "2 → 4 → 8 → 16 → 32 → ?"
    )

    answer = st.text_input(
        "Next number:",
        key="pattern_answer",
    )

    if st.button(
        "Check Pattern",
        key="check_pattern",
        use_container_width=True,
    ):

        if answer.strip() == "64":

            finish_lab(
                "Correct. Each value doubles. "
                "This demonstrates simple rule-based pattern recognition."
            )

        else:

            finish_lab(
                "The next value is 64 because the sequence "
                "doubles at every step."
            )

        st.rerun()


def show_lab_result():

    if not st.session_state.lab_result:
        return

    st.markdown(
        f"""
        <div class="success-box">

            <h3>🤖 Ayna's Scientific Explanation</h3>

            <p>
                {safe_html_text(
                    st.session_state.lab_result
                )}
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    browser_speech_button(
        st.session_state.lab_result,
        "🔊 Speak Ayna's Explanation",
    )

    st.markdown(
        "### 🧩 Follow-up"
    )

    followup = st.radio(
        "What would you like to do next?",
        [
            "Increase difficulty",
            "Try another experiment",
            "Explore the related brain system",
        ],
        key="lab_followup_choice",
    )

    if followup == "Increase difficulty":

        st.info(
            "A harder version can increase the number "
            "of distractors, memory load or decision complexity."
        )

    elif followup == "Try another experiment":

        if st.button(
            "🧪 Reset Lab",
            key="reset_lab_after_result",
            use_container_width=True,
        ):

            reset_lab()
            st.rerun()

    else:

        st.info(
            "Use Brain Journey or Explore Brain to study "
            "the relevant neuroscience concepts."
        )


def page_lab():

    st.header(
        "🧪 Interactive Cognitive Neuroscience Lab"
    )

    st.write(
        "Choose your research setup and run an "
        "interactive behavioral experiment."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        character_names = list(
            LAB_CHARACTERS.keys()
        )

        if st.session_state.character not in character_names:
            st.session_state.character = character_names[0]

        st.session_state.character = st.selectbox(
            "👤 Character",
            character_names,
            index=character_names.index(
                st.session_state.character
            ),
            key="lab_character_selector",
        )

    with col2:

        equipment_names = list(
            LAB_EQUIPMENT.keys()
        )

        if st.session_state.equipment not in equipment_names:
            st.session_state.equipment = equipment_names[0]

        st.session_state.equipment = st.selectbox(
            "🔬 Equipment",
            equipment_names,
            index=equipment_names.index(
                st.session_state.equipment
            ),
            key="lab_equipment_selector",
        )

    with col3:

        experiment_names = list(
            LAB_EXPERIMENTS.keys()
        )

        if st.session_state.experiment not in experiment_names:
            st.session_state.experiment = experiment_names[0]

        st.session_state.experiment = st.selectbox(
            "🧪 Experiment",
            experiment_names,
            index=experiment_names.index(
                st.session_state.experiment
            ),
            key="lab_experiment_selector",
        )

    experiment_description = LAB_EXPERIMENTS[
        st.session_state.experiment
    ]["description"]

    st.info(
        experiment_description
    )

    if not st.session_state.experiment_started:

        if st.button(
            "🚀 Start Experiment",
            use_container_width=True,
        ):

            st.session_state.experiment_started = True
            st.session_state.experiment_completed = False
            st.session_state.lab_result = None
            st.session_state.lab_followup = False

            st.rerun()

    if st.session_state.experiment_started:

        lab_visual()

        st.divider()

        if not st.session_state.experiment_completed:

            experiment_name = (
                st.session_state.experiment
            )

            if experiment_name == "Attention":

                attention_experiment()

            elif experiment_name == "Memory":

                memory_experiment()

            elif experiment_name == "Decision & Reward":

                decision_experiment()

            elif experiment_name == "Stroop-Cognitive Control":

                stroop_experiment()

            elif experiment_name == "Pattern Recognition":

                pattern_experiment()

        else:

            show_lab_result()

        st.divider()

        if st.button(
            "🔄 Reset Current Experiment",
            use_container_width=True,
        ):

            reset_lab()
            st.rerun()


# ============================================================
# BRAIN JOURNEY
# ============================================================

BRAIN_JOURNEY = [

    {
        "title": "Whole Brain",
        "description":
            "The brain contains interacting regions and "
            "networks that support perception, movement, "
            "memory, attention, emotion and decision-making.",
        "assets": [
            "brain.png",
            "brain_animation.mp4",
        ],
    },

    {
        "title": "Neuron",
        "description":
            "A neuron is a specialized cell that receives, "
            "integrates and transmits information.",
        "assets": [
            "neuron.png",
            "neuron.gif",
        ],
    },

    {
        "title": "Neural Signaling",
        "description":
            "Neural information can involve electrical "
            "activity within neurons and chemical signaling "
            "between connected cells.",
        "assets": [
            "neural_signaling.gif",
        ],
    },

    {
        "title": "Synapse",
        "description":
            "A synapse is a communication junction where "
            "signals can pass from one neuron to another.",
        "assets": [
            "synapse.png",
            "synapse.gif",
        ],
    },

    {
        "title": "Prefrontal Cortex",
        "description":
            "The prefrontal cortex is involved in several "
            "higher-order functions including planning, "
            "working memory and cognitive control.",
        "assets": [
            "prefrontal_cortex.png",
        ],
    },

    {
        "title": "Hippocampus",
        "description":
            "The hippocampus is strongly associated with "
            "memory formation and spatial/contextual processing.",
        "assets": [
            "hippocampus.png",
        ],
    },

    {
        "title": "Striatum",
        "description":
            "The striatum is part of the basal ganglia and "
            "participates in action selection, learning and reward-related circuits.",
        "assets": [
            "striatum.png",
        ],
    },

    {
        "title": "Anterior Cingulate Cortex",
        "description":
            "The anterior cingulate cortex participates in "
            "monitoring, control, conflict processing and several "
            "forms of cognitive and affective processing.",
        "assets": [
            "acc.png",
        ],
    },

    {
        "title": "Attention Networks",
        "description":
            "Attention depends on distributed neural systems "
            "that help select and prioritize information.",
        "assets": [
            "attention_network.png",
        ],
    },

]


def find_first_available_asset(
    assets
):

    for filename in assets:

        path = find_asset(
            filename
        )

        if path:
            return path

    return None


def brain_journey_visual(step):

    asset = find_first_available_asset(
        step["assets"]
    )

    if not asset:

        brain = find_asset(
            "brain.png"
        )

        if brain:
            st.image(
                brain,
                use_container_width=True,
            )

        st.info(
            "Concept-specific visual not found. "
            "Add the requested asset to the assets folder."
        )

        return

    extension = os.path.splitext(
        asset
    )[1].lower()

    if extension in [
        ".mp4",
        ".webm",
        ".mov",
    ]:

        try:
            st.video(
                asset
            )
        except Exception:

            st.info(
                "The concept animation could not be displayed."
            )

    elif extension in [
        ".gif",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    ]:

        try:
            st.image(
                asset,
                use_container_width=True,
            )
        except Exception:

            st.info(
                "The concept image could not be displayed."
            )


def page_brain_journey():

    st.header(
        "🧠 Visual Brain Journey"
    )

    total = len(
        BRAIN_JOURNEY
    )

    index = int(
        st.session_state.journey_index
    ) % total

    step = BRAIN_JOURNEY[index]

    st.progress(
        (index + 1) / total
    )

    st.caption(
        f"Concept {index + 1} of {total}"
    )

    st.markdown(
        f"## {step['title']}"
    )

    st.write(
        step["description"]
    )

    brain_journey_visual(
        step
    )

    st.markdown(
        """
        <div class="card">

        <strong>Research note</strong>

        <p class="muted">
        This visual journey is educational.
        A region or network should not be interpreted
        as having one isolated function; brain functions
        usually depend on interacting systems.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "⬅️ Previous",
            use_container_width=True,
        ):

            st.session_state.journey_index = (
                index - 1
            ) % total

            st.rerun()

    with col2:

        if st.button(
            "🔄 Restart",
            use_container_width=True,
        ):

            st.session_state.journey_index = 0

            st.rerun()

    with col3:

        if st.button(
            "Next ➡️",
            use_container_width=True,
        ):

            st.session_state.journey_index = (
                index + 1
            ) % total 
            st.rerun()


# ============================================================
# END OF PART 2
# ============================================================
# ============================================================
# EXPLORE BRAIN
# ============================================================

BRAIN_REGIONS = {

    "Prefrontal Cortex": {
        "emoji": "🧠",
        "description": (
            "The prefrontal cortex is involved in several "
            "higher-order processes including planning, "
            "working memory, cognitive control and decision-making."
        ),
        "asset": "prefrontal_cortex.png",
    },

    "Hippocampus": {
        "emoji": "🧠",
        "description": (
            "The hippocampus is strongly associated with "
            "memory formation and contextual and spatial processing."
        ),
        "asset": "hippocampus.png",
    },

    "Striatum": {
        "emoji": "🔄",
        "description": (
            "The striatum is part of the basal ganglia and "
            "participates in action selection, learning and "
            "reward-related circuits."
        ),
        "asset": "striatum.png",
    },

    "Anterior Cingulate Cortex": {
        "emoji": "🎯",
        "description": (
            "The anterior cingulate cortex participates in "
            "monitoring, conflict processing and cognitive control."
        ),
        "asset": "acc.png",
    },

    "Attention Networks": {
        "emoji": "👁️",
        "description": (
            "Attention depends on distributed neural networks "
            "that help select and prioritize information."
        ),
        "asset": "attention_network.png",
    },

    "Neuron": {
        "emoji": "⚡",
        "description": (
            "Neurons are specialized cells that receive, "
            "integrate and transmit information."
        ),
        "asset": "neuron.png",
    },

    "Synapse": {
        "emoji": "🔗",
        "description": (
            "A synapse is a communication junction between "
            "neurons where chemical or electrical signaling can occur."
        ),
        "asset": "synapse.png",
    },

    "Neural Signaling": {
        "emoji": "⚡",
        "description": (
            "Neural communication involves electrical activity "
            "within neurons and chemical signaling between many "
            "connected neurons."
        ),
        "asset": "neural_signaling.gif",
    },

}


def page_explore_brain():

    st.header(
        "🔬 Explore Brain"
    )

    st.write(
        "Select a brain concept to explore its role "
        "within distributed neural systems."
    )

    names = list(
        BRAIN_REGIONS.keys()
    )

    selected = st.selectbox(
        "Select concept",
        names,
        key="explore_brain_region",
    )

    info = BRAIN_REGIONS[
        selected
    ]

    st.markdown(
        f"""
        <div class="card">

            <div style="
                font-size:55px;
            ">
                {info["emoji"]}
            </div>

            <h2>
                {safe_html_text(selected)}
            </h2>

            <p>
                {safe_html_text(info["description"])}
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    asset = find_asset(
        info["asset"]
    )

    if asset:

        extension = os.path.splitext(
            asset
        )[1].lower()

        if extension in [
            ".gif",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        ]:

            st.image(
                asset,
                use_container_width=True,
            )

        elif extension in [
            ".mp4",
            ".webm",
            ".mov",
        ]:

            st.video(
                asset
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

        st.info(
            f"Concept visual not found for {selected}. "
            f"Add assets/{info['asset']} to show the dedicated visual."
        )

    st.markdown(
        """
        <div class="warning-box">

            <strong>Important neuroscience note</strong>

            <p>
            Brain regions do not normally operate as isolated
            single-function modules. Most cognitive functions
            emerge from interactions between multiple regions
            and networks.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BRAIN PUZZLE
# ============================================================

def puzzle_make_tiles(
    image,
    grid_size,
):

    try:

        image = image.convert(
            "RGB"
        )

        width, height = image.size

        size = min(
            width,
            height,
        )

        left = (
            width - size
        ) // 2

        top = (
            height - size
        ) // 2

        image = image.crop(
            (
                left,
                top,
                left + size,
                top + size,
            )
        )

        tile_size = size // grid_size

        tiles = []

        for row in range(
            grid_size
        ):

            for col in range(
                grid_size
            ):

                tile = image.crop(
                    (
                        col * tile_size,
                        row * tile_size,
                        (col + 1) * tile_size,
                        (row + 1) * tile_size,
                    )
                )

                tiles.append(
                    tile
                )

        return tiles

    except Exception:

        return []


def puzzle_tile_data_url(
    image,
):

    try:

        from io import BytesIO

        buffer = BytesIO()

        image.save(
            buffer,
            format="PNG",
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode(
            "utf-8"
        )

        return (
            "data:image/png;base64,"
            + encoded
        )

    except Exception:

        return ""


def puzzle_create_state(
    grid_size,
):

    brain_path = find_asset(
        "brain.png"
    )

    if not brain_path:

        return False

    try:

        image = Image.open(
            brain_path
        )

    except Exception:

        return False

    tiles = puzzle_make_tiles(
        image,
        grid_size,
    )

    if not tiles:

        return False

    total = grid_size * grid_size

    order = list(
        range(total)
    )

    random.shuffle(
        order
    )

    # Avoid accidentally starting solved.
    if order == list(
        range(total)
    ):

        order.reverse()

    st.session_state.puzzle_grid = (
        grid_size
    )

    st.session_state.puzzle_tiles = [
        {
            "id": index,
            "image": puzzle_tile_data_url(
                tiles[index]
            ),
            "target": index,
        }
        for index in range(total)
    ]

    st.session_state.puzzle_order = order

    st.session_state.puzzle_moves = 0

    st.session_state.puzzle_completed = False

    st.session_state.puzzle_started_at = (
        time.time()
    )

    st.session_state.puzzle_elapsed = 0

    st.session_state.puzzle_blank = (
        total - 1
    )

    return True


def puzzle_current_order():

    order = st.session_state.get(
        "puzzle_order",
        [],
    )

    return list(
        order
    )


def puzzle_is_solved():

    order = puzzle_current_order()

    if not order:
        return False

    return order == list(
        range(
            len(order)
        )
    )


def puzzle_move_piece(
    position,
):

    order = puzzle_current_order()

    if not order:
        return False

    grid = int(
        st.session_state.puzzle_grid
    )

    total = grid * grid

    if position < 0 or position >= total:
        return False

    blank = order.index(
        total - 1
    )

    row1 = blank // grid
    col1 = blank % grid

    row2 = position // grid
    col2 = position % grid

    distance = (
        abs(row1 - row2)
        +
        abs(col1 - col2)
    )

    if distance != 1:
        return False

    order[blank], order[position] = (
        order[position],
        order[blank],
    )

    st.session_state.puzzle_order = (
        order
    )

    st.session_state.puzzle_moves += 1

    return True


def puzzle_finish():

    if puzzle_is_solved():

        if not st.session_state.puzzle_completed:

            elapsed = (
                time.time()
                -
                st.session_state.puzzle_started_at
            )

            st.session_state.puzzle_elapsed = (
                elapsed
            )

            st.session_state.puzzle_completed = True

            st.session_state.games_completed += 1

            add_achievement(
                "Brain Puzzle Completed"
            )

            previous_time = (
                st.session_state.puzzle_best_time
            )

            if (
                previous_time is None
                or elapsed < previous_time
            ):

                st.session_state.puzzle_best_time = (
                    elapsed
                )

            previous_moves = (
                st.session_state.puzzle_best_moves
            )

            moves = (
                st.session_state.puzzle_moves
            )

            if (
                previous_moves is None
                or moves < previous_moves
            ):

                st.session_state.puzzle_best_moves = (
                    moves
                )

            return True

    return False


def puzzle_grid_html():

    order = puzzle_current_order()

    if not order:
        return ""

    grid = int(
        st.session_state.puzzle_grid
    )

    tiles = {
        item["id"]: item
        for item in st.session_state.puzzle_tiles
    }

    cells = []

    for position, tile_id in enumerate(
        order
    ):

        if tile_id == grid * grid - 1:

            cells.append(
                """
                <div style="
                    aspect-ratio:1;
                    border-radius:10px;
                    border:1px dashed rgba(128,128,128,.25);
                    background:rgba(128,128,128,.05);
                ">
                </div>
                """
            )

            continue

        tile = tiles.get(
            tile_id
        )

        if not tile:
            continue

        cells.append(
            f"""
            <div
                style="
                    aspect-ratio:1;
                    border-radius:10px;
                    overflow:hidden;
                    border:1px solid rgba(128,128,128,.25);
                    background-image:url('{tile["image"]}');
                    background-size:100% 100%;
                    background-repeat:no-repeat;
                "
            ></div>
            """
        )

    return "\n".join(
        cells
    )


def page_brain_puzzle():

    st.header(
        "🧩 Brain Puzzle"
    )

    st.write(
        "Reconstruct the brain image by moving adjacent "
        "pieces into the empty position."
    )

    st.caption(
        "This is a visual puzzle. It does not measure intelligence "
        "or diagnose cognitive ability."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        grid_options = [
            3,
            4,
            5,
        ]

        selected_grid = st.selectbox(
            "Grid",
            grid_options,
            index=(
                grid_options.index(
                    st.session_state.puzzle_grid
                )
                if st.session_state.puzzle_grid
                in grid_options
                else 0
            ),
        )

    with col2:

        challenge_options = [
            "Time Challenge",
            "Minimum Moves",
            "Speed Mode",
            "Memory Mode",
        ]

        st.session_state.puzzle_challenge = st.selectbox(
            "Challenge Mode",
            challenge_options,
            index=challenge_options.index(
                st.session_state.puzzle_challenge
            ),
        )

    with col3:

        st.metric(
            "Round",
            st.session_state.puzzle_round,
        )

    if st.button(
        "🆕 New Puzzle",
        use_container_width=True,
    ):

        st.session_state.puzzle_grid = (
            selected_grid
        )

        puzzle_create_state(
            selected_grid
        )

        st.rerun()

    if not st.session_state.puzzle_order:

        st.info(
            "Press New Puzzle to start."
        )

        brain_path = find_asset(
            "brain.png"
        )

        if brain_path:

            st.image(
                brain_path,
                use_container_width=True,
            )

        return

    elapsed = (
        st.session_state.puzzle_elapsed
        if st.session_state.puzzle_completed
        else (
            time.time()
            -
            st.session_state.puzzle_started_at
        )
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Moves",
            st.session_state.puzzle_moves,
        )

    with col2:

        st.metric(
            "Time",
            f"{elapsed:.1f}s",
        )

    with col3:

        st.metric(
            "Best Time",
            (
                f"{st.session_state.puzzle_best_time:.1f}s"
                if st.session_state.puzzle_best_time
                is not None
                else "-"
            ),
        )

    with col4:

        st.metric(
            "Best Moves",
            (
                st.session_state.puzzle_best_moves
                if st.session_state.puzzle_best_moves
                is not None
                else "-"
            ),
        )

    # --------------------------------------------------------
    # Puzzle board
    # --------------------------------------------------------

    grid_html = puzzle_grid_html()

    st.markdown(
        f"""
        <div
            style="
                display:grid;
                grid-template-columns:
                    repeat({st.session_state.puzzle_grid},1fr);
                gap:6px;
                max-width:650px;
                margin:auto;
                padding:10px;
                border-radius:18px;
                border:1px solid rgba(128,128,128,.25);
                background:rgba(128,128,128,.04);
            "
        >
            {grid_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "For the full touch-drag version, the custom "
        "component layer can be enabled in the connected build. "
        "The current board also supports adjacent-piece movement."
    )

    # --------------------------------------------------------
    # Keyboard/mobile-friendly move controls
    # --------------------------------------------------------

    st.markdown(
        "### 🎮 Move a Piece"
    )

    order = puzzle_current_order()

    if order:

        grid = int(
            st.session_state.puzzle_grid
        )

        blank = order.index(
            grid * grid - 1
        )

        valid_positions = []

        row = blank // grid
        col = blank % grid

        candidates = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]

        for r, c in candidates:

            if (
                0 <= r < grid
                and
                0 <= c < grid
            ):

                valid_positions.append(
                    r * grid + c
                )

        buttons = st.columns(
            max(
                1,
                min(
                    4,
                    len(valid_positions)
                )
            )
        )

        for index, position in enumerate(
            valid_positions
        ):

            tile_id = order[
                position
            ]

            with buttons[
                index % len(buttons)
            ]:

                if st.button(
                    f"Move piece {tile_id + 1}",
                    key=f"move_piece_{position}",
                    use_container_width=True,
                ):

                    puzzle_move_piece(
                        position
                    )

                    if puzzle_finish():

                        st.balloons()

                    st.rerun()

    if st.session_state.puzzle_completed:

        score = max(
            0,
            int(
                10000
                /
                max(
                    1,
                    st.session_state.puzzle_moves
                )
            )
        )

        st.markdown(
            f"""
            <div class="success-box">

                <h2>🎉 Puzzle Complete!</h2>

                <p>
                Time:
                <strong>
                    {st.session_state.puzzle_elapsed:.1f}s
                </strong>
                </p>

                <p>
                Moves:
                <strong>
                    {st.session_state.puzzle_moves}
                </strong>
                </p>

                <p>
                Puzzle score:
                <strong>
                    {score}
                </strong>
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "➡️ Next Round",
            use_container_width=True,
        ):

            next_grid = min(
                5,
                st.session_state.puzzle_grid + 1
            )

            st.session_state.puzzle_round += 1

            puzzle_create_state(
                next_grid
            )

            st.rerun()

    if st.button(
        "🔄 Reset Puzzle",
        use_container_width=True,
    ):

        puzzle_create_state(
            st.session_state.puzzle_grid
        )

        st.rerun()


# ============================================================
# GEMINI AUDIO ANALYSIS
# ============================================================

def analyze_audio_with_gemini(
    audio_bytes,
    mime_type="audio/wav",
):

    if not ai_available():

        return {
            "transcript": "",
            "emoji": "❔",
            "vibe": "AI unavailable",
            "explanation":
                "Gemini is not connected.",
        }

    if not audio_bytes:

        return {
            "transcript": "",
            "emoji": "❔",
            "vibe": "No audio",
            "explanation":
                "No audio recording was provided.",
        }

    prompt = """
You are analyzing a short user voice recording
for an educational interface.

Return JSON only with:

{
  "transcript": "...",
  "emoji": "...",
  "vibe": "...",
  "explanation": "..."
}

The transcript should represent what was said
as accurately as possible.

The vibe should describe observable vocal
characteristics such as:

- energetic
- calm
- tense
- low-energy
- excited
- frustrated
- neutral
- uncertain

Do NOT claim that you know the person's
true internal emotional state.

Do NOT diagnose.

Treat emotion/vibe as an AI-assisted
probabilistic interpretation of the recording.

Keep explanation short.

"""

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(
                            audio_bytes
                        ).decode("utf-8"),
                    }
                },
            ],
        )

        raw = getattr(
            response,
            "text",
            "",
        )

        raw = raw.strip()

        if raw.startswith(
            "```"
        ):

            raw = re.sub(
                r"^```(?:json)?",
                "",
                raw,
                flags=re.I,
            )

            raw = re.sub(
                r"```$",
                "",
                raw,
            )

        parsed = json.loads(
            raw
        )

        return {
            "transcript":
                str(
                    parsed.get(
                        "transcript",
                        "",
                    )
                ),

            "emoji":
                str(
                    parsed.get(
                        "emoji",
                        "🎙️",
                    )
                ),

            "vibe":
                str(
                    parsed.get(
                        "vibe",
                        "Uncertain",
                    )
                ),

            "explanation":
                str(
                    parsed.get(
                        "explanation",
                        "",
                    )
                ),
        }

    except Exception:

        return {
            "transcript": "",
            "emoji": "❔",
            "vibe": "Uncertain",
            "explanation":
                "The voice analysis could not be completed. "
                "Try recording a clearer sample.",
        }


# ============================================================
# VOICE MOOD
# ============================================================

def page_voice_mood():

    st.header(
        "🎙️ AI Voice Mood & Behaviour"
    )

    st.write(
        "Record your voice and let Gemini provide an "
        "AI-assisted interpretation of the vocal characteristics."
    )

    st.markdown(
        """
        <div class="warning-box">

        <strong>Important</strong>

        <p>
        Voice analysis cannot directly read your mind
        or determine your true internal emotional state.
        The result is an AI-assisted interpretation of
        observable characteristics in the recording.
        It is not a medical or psychological diagnosis.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    audio = st.audio_input(
        "🎙️ Record your voice"
    )

    if audio is not None:

        st.audio(
            audio
        )

        if st.button(
            "🧠 Analyze Voice",
            use_container_width=True,
        ):

            audio_bytes = audio.getvalue()

            with st.spinner(
                "Ayna is analyzing the voice..."
            ):

                result = analyze_audio_with_gemini(
                    audio_bytes,
                    getattr(
                        audio,
                        "type",
                        "audio/wav",
                    )
                    or "audio/wav",
                )

            st.session_state.voice_result = (
                result
            )

            st.rerun()

    result = st.session_state.voice_result

    if result:

        st.divider()

        st.subheader(
            "🎭 Voice Interpretation"
        )

        col1, col2 = st.columns(
            [1, 3]
        )

        with col1:

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    font-size:80px;
                ">
                    {safe_html_text(
                        result.get(
                            "emoji",
                            "🎙️"
                        )
                    )}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            st.markdown(
                f"""
                <div class="card">

                    <h3>
                    Vocal vibe
                    </h3>

                    <p style="
                        font-size:24px;
                        font-weight:700;
                    ">
                    {safe_html_text(
                        result.get(
                            "vibe",
                            "Uncertain"
                        )
                    )}
                    </p>

                    <p>
                    {safe_html_text(
                        result.get(
                            "explanation",
                            ""
                        )
                    )}
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader(
            "📝 Transcript"
        )

        transcript = result.get(
            "transcript",
            "",
        )

        if transcript:

            st.write(
                transcript
            )

        else:

            st.info(
                "No reliable transcript was returned."
            )


# ============================================================
# GEMINI IMAGE ANALYSIS
# ============================================================

def analyze_face_with_gemini(
    image_bytes,
    mime_type="image/jpeg",
):

    if not ai_available():

        return {
            "emoji": "❔",
            "expression": "AI unavailable",
            "explanation":
                "Gemini is not connected.",
        }

    prompt = """
Analyze the visible facial expression in this image.

Return JSON only:

{
  "emoji": "...",
  "expression": "...",
  "explanation": "..."
}

Describe only visible expression-related
characteristics.

Examples:

neutral,
smiling,
serious,
surprised,
tensed,
frowning,
relaxed,
uncertain.

Do NOT claim to know the person's hidden
emotional state.

Do NOT diagnose mental health conditions.

A facial expression is not equivalent to
a person's actual internal mood.

Keep the explanation short.
"""

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        encoded = base64.b64encode(
            image_bytes
        ).decode(
            "utf-8"
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded,
                    }
                },
            ],
        )

        raw = getattr(
            response,
            "text",
            "",
        ).strip()

        if raw.startswith(
            "```"
        ):

            raw = re.sub(
                r"^```(?:json)?",
                "",
                raw,
                flags=re.I,
            )

            raw = re.sub(
                r"```$",
                "",
                raw,
            )

        data = json.loads(
            raw
        )

        return {
            "emoji":
                str(
                    data.get(
                        "emoji",
                        "🙂",
                    )
                ),

            "expression":
                str(
                    data.get(
                        "expression",
                        "Uncertain",
                    )
                ),

            "explanation":
                str(
                    data.get(
                        "explanation",
                        "",
                    )
                ),
        }

    except Exception:

        return {
            "emoji": "❔",
            "expression": "Uncertain",
            "explanation":
                "The visible-expression analysis could not be completed.",
        }


# ============================================================
# FACE SCAN
# ============================================================

def page_face_scan():

    st.header(
        "📷 Face Expression Scan"
    )

    st.write(
        "Capture a selfie and let AI describe the "
        "visible facial expression."
    )

    st.markdown(
        """
        <div class="warning-box">

        <strong>Privacy & interpretation note</strong>

        <p>
        The camera is activated only when you choose
        the camera control. The result describes visible
        facial expression and should not be treated as
        definitive evidence of internal mood, personality,
        mental health or hidden thoughts.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    photo = st.camera_input(
        "📸 Take a selfie"
    )

    if photo is not None:

        st.image(
            photo,
            caption="Captured image",
            use_container_width=True,
        )

        if st.button(
            "🧠 Analyze Facial Expression",
            use_container_width=True,
        ):

            with st.spinner(
                "Ayna is analyzing the visible expression..."
            ):

                result = analyze_face_with_gemini(
                    photo.getvalue(),
                    getattr(
                        photo,
                        "type",
                        "image/jpeg",
                    )
                    or "image/jpeg",
                )

            st.session_state.face_result = (
                result
            )

            st.rerun()

    result = st.session_state.get(
        "face_result"
    )

    if result:

        st.divider()

        st.subheader(
            "🙂 Visible Expression"
        )

        st.markdown(
            f"""
            <div class="card">

                <div style="
                    font-size:80px;
                    text-align:center;
                ">
                    {safe_html_text(
                        result.get(
                            "emoji",
                            "🙂"
                        )
                    )}
                </div>

                <h3 style="text-align:center;">
                    {safe_html_text(
                        result.get(
                            "expression",
                            "Uncertain"
                        )
                    )}
                </h3>

                <p>
                    {safe_html_text(
                        result.get(
                            "explanation",
                            ""
                        )
                    )}
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# COMBINED EMOTION / EXPRESSION SCAN
# ============================================================

def page_mood_behaviour():

    st.header(
        "🎭 Emotion & Expression Lab"
    )

    st.write(
        "Explore voice-based and camera-based "
        "AI-assisted expression analysis."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🎙️ Voice Scan",
            "📷 Face Scan",
            "🧠 Combined Scan",
        ]
    )

    with tab1:

        page_voice_mood()

    with tab2:

        page_face_scan()

    with tab3:

        st.subheader(
            "🧠 Combined Voice + Face"
        )

        st.write(
            "Record your voice and capture a selfie. "
            "The two signals are analyzed separately."
        )

        audio = st.audio_input(
            "🎙️ Record voice",
            key="combined_voice_input",
        )

        photo = st.camera_input(
            "📷 Capture face",
            key="combined_face_input",
        )

        if st.button(
            "🔬 Run Combined Scan",
            use_container_width=True,
        ):

            if audio is None or photo is None:

                st.warning(
                    "Please provide both a voice recording "
                    "and a camera image."
                )

            else:

                with st.spinner(
                    "Analyzing voice and visible expression..."
                ):

                    voice_result = (
                        analyze_audio_with_gemini(
                            audio.getvalue(),
                            getattr(
                                audio,
                                "type",
                                "audio/wav",
                            )
                            or "audio/wav",
                        )
                    )

                    face_result = (
                        analyze_face_with_gemini(
                            photo.getvalue(),
                            getattr(
                                photo,
                                "type",
                                "image/jpeg",
                            )
                            or "image/jpeg",
                        )
                    )

                st.session_state.combined_result = {
                    "voice": voice_result,
                    "face": face_result,
                }

                st.rerun()

        combined = st.session_state.get(
            "combined_result"
        )

        if combined:

            voice = combined["voice"]
            face = combined["face"]

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    f"""
                    <div class="card">

                        <h3>
                        🎙️ Voice
                        </h3>

                        <div style="
                            font-size:55px;
                        ">
                            {safe_html_text(
                                voice.get(
                                    "emoji",
                                    "🎙️"
                                )
                            )}
                        </div>

                        <strong>
                            {safe_html_text(
                                voice.get(
                                    "vibe",
                                    "Uncertain"
                                )
                            )}
                        </strong>

                        <p>
                            {safe_html_text(
                                voice.get(
                                    "explanation",
                                    ""
                                )
                            )}
                        </p>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:

                st.markdown(
                    f"""
                    <div class="card">

                        <h3>
                        📷 Face
                        </h3>

                        <div style="
                            font-size:55px;
                        ">
                            {safe_html_text(
                                face.get(
                                    "emoji",
                                    "🙂"
                                )
                            )}
                        </div>

                        <strong>
                            {safe_html_text(
                                face.get(
                                    "expression",
                                    "Uncertain"
                                )
                            )}
                        </strong>

                        <p>
                            {safe_html_text(
                                face.get(
                                    "explanation",
                                    ""
                                )
                            )}
                        </p>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.info(
                "Voice and facial expression are separate "
                "observable signals. If they differ, that "
                "does not mean one of them is 'wrong' or "
                "that the person's internal mood has been identified."
            )


# ============================================================
# END OF PART 3
# ============================================================
# ============================================================
# PART 4 — SUPABASE + NEUROSOCIAL + CHAT + STORIES + GAMES
# ============================================================

# ------------------------------------------------------------
# SUPABASE DATABASE HELPERS
# ------------------------------------------------------------

def db_select(table, filters=None, limit=100, order=None, descending=True):
    if not supabase_available():
        return []

    try:
        query = supabase.table(table).select("*")

        if filters:
            for key, value in filters.items():
                if value is None:
                    query = query.is_(key, "null")
                else:
                    query = query.eq(key, value)

        if order:
            query = query.order(order, desc=descending)

        query = query.limit(limit)
        response = query.execute()

        return response.data or []

    except Exception as exc:
        st.warning(f"Database read error: {exc}")
        return []


def db_insert_safe(table, payload):
    if not supabase_available():
        return None

    try:
        response = supabase.table(table).insert(payload).execute()
        data = response.data or []
        return data[0] if data else None
    except Exception as exc:
        st.warning(f"Database insert error: {exc}")
        return None


def db_update_safe(table, payload, filters):
    if not supabase_available():
        return None

    try:
        query = supabase.table(table).update(payload)

        for key, value in filters.items():
            query = query.eq(key, value)

        response = query.execute()
        return response.data or []
    except Exception as exc:
        st.warning(f"Database update error: {exc}")
        return []


def db_delete_safe(table, filters):
    if not supabase_available():
        return False

    try:
        query = supabase.table(table).delete()

        for key, value in filters.items():
            query = query.eq(key, value)

        query.execute()
        return True

    except Exception as exc:
        st.warning(f"Database delete error: {exc}")
        return False


# ------------------------------------------------------------
# AUTH HELPERS
# ------------------------------------------------------------

def auth_session_user():
    if not supabase_available():
        return None

    try:
        response = supabase.auth.get_user()
        return response.user if response else None
    except Exception:
        return None


def auth_user_id():
    user = auth_session_user()

    if user is None:
        return None

    return getattr(user, "id", None)


def auth_email():
    user = auth_session_user()

    if user is None:
        return ""

    return getattr(user, "email", "") or ""


def safe_username(value):
    value = str(value or "").strip().lower()

    allowed = []

    for char in value:
        if char.isalnum() or char in "._-":
            allowed.append(char)

    result = "".join(allowed)

    return result[:30]


def profile_username(user_id):
    if not user_id:
        return "user"

    rows = db_select(
        "profiles",
        filters={"id": user_id},
        limit=1
    )

    if rows:
        return rows[0].get("username") or "user"

    return "user"


def load_my_profile():
    uid = auth_user_id()

    if not uid:
        return None

    rows = db_select(
        "profiles",
        filters={"id": uid},
        limit=1
    )

    return rows[0] if rows else None


def social_require_auth():
    if not supabase_available():
        st.error(
            "Supabase is not connected. "
            "Add SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets."
        )
        return False

    uid = auth_user_id()

    if not uid:
        st.warning(
            "Please create an account or sign in before using NeuroSocial."
        )
        return False

    return True


# ------------------------------------------------------------
# ACCOUNT PAGE
# ------------------------------------------------------------

def page_account():
    st.header("👤 My Account")

    if not supabase_available():
        st.error("Supabase is not connected.")
        return

    user = auth_session_user()

    if not user:
        st.subheader("Create your NEUROLENS account")

        mode = st.radio(
            "Choose",
            ["Sign In", "Create Account"],
            horizontal=True
        )

        email = st.text_input(
            "Email",
            key="account_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="account_password"
        )

        if mode == "Create Account":
            username = st.text_input(
                "Username",
                placeholder="e.g. ayna_neuro"
            )

            display_name = st.text_input(
                "Display name",
                placeholder="Ayna"
            )

            bio = st.text_area(
                "Bio",
                placeholder="Cognitive neuroscience • AI • Brain research"
            )

            if st.button(
                "Create Account",
                type="primary",
                use_container_width=True
            ):
                username = safe_username(username)

                if not email or not password:
                    st.error("Email and password are required.")

                elif len(password) < 8:
                    st.error(
                        "Password should contain at least 8 characters."
                    )

                elif not username:
                    st.error("Please choose a valid username.")

                else:
                    try:
                        result = supabase.auth.sign_up(
                            {
                                "email": email.strip(),
                                "password": password,
                                "options": {
                                    "data": {
                                        "username": username,
                                        "display_name": display_name.strip(),
                                        "bio": bio.strip()
                                    }
                                }
                            }
                        )

                        if result.user:
                            st.success(
                                "Account created. "
                                "Check your email if email confirmation is enabled."
                            )
                            st.rerun()

                    except Exception as exc:
                        st.error(str(exc))

        else:

            if st.button(
                "Sign In",
                type="primary",
                use_container_width=True
            ):
                if not email or not password:
                    st.error("Email and password are required.")

                else:
                    try:
                        result = supabase.auth.sign_in_with_password(
                            {
                                "email": email.strip(),
                                "password": password
                            }
                        )

                        if result.user:
                            st.success("Signed in successfully.")
                            st.rerun()

                    except Exception as exc:
                        st.error(str(exc))

        return

    uid = auth_user_id()
    profile = load_my_profile() or {}

    st.success("🟢 You are signed in.")

    st.markdown(
        f"### @{profile.get('username', 'user')}"
    )

    st.write(
        f"**Email:** {auth_email()}"
    )

    display_name = st.text_input(
        "Display name",
        value=profile.get("display_name") or "",
        key="account_display_name"
    )

    bio = st.text_area(
        "Bio",
        value=profile.get("bio") or "",
        key="account_bio"
    )

    if st.button(
        "Save Profile",
        type="primary",
        use_container_width=True
    ):
        db_update_safe(
            "profiles",
            {
                "display_name": display_name.strip(),
                "bio": bio.strip()
            },
            {"id": uid}
        )

        st.success("Profile updated.")
        st.rerun()

    st.divider()

    if st.button(
        "🔐 Sign Out",
        use_container_width=True
    ):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.pop("social_selected_friend", None)

        st.success("Signed out.")
        st.rerun()


# ------------------------------------------------------------
# FRIEND SYSTEM
# ------------------------------------------------------------

def are_friends(user_a, user_b):
    if not user_a or not user_b:
        return False

    rows1 = db_select(
        "friendships",
        filters={
            "user_id": user_a,
            "friend_id": user_b
        },
        limit=1
    )

    if rows1:
        return True

    rows2 = db_select(
        "friendships",
        filters={
            "user_id": user_b,
            "friend_id": user_a
        },
        limit=1
    )

    return bool(rows2)


def send_friend_request(sender_id, receiver_id):
    if not sender_id or not receiver_id:
        return False, "Invalid users."

    if sender_id == receiver_id:
        return False, "You cannot add yourself."

    if are_friends(sender_id, receiver_id):
        return False, "You are already friends."

    existing = db_select(
        "friend_requests",
        filters={
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "status": "pending"
        },
        limit=1
    )

    if existing:
        return False, "Friend request already sent."

    reverse = db_select(
        "friend_requests",
        filters={
            "sender_id": receiver_id,
            "receiver_id": sender_id,
            "status": "pending"
        },
        limit=1
    )

    if reverse:
        return False, "This user already sent you a request."

    result = db_insert_safe(
        "friend_requests",
        {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "status": "pending"
        }
    )

    if result:
        return True, "Friend request sent."

    return False, "Could not send request."


def accept_friend_request(request_id, sender_id, receiver_id):
    if not request_id:
        return False

    updated = db_update_safe(
        "friend_requests",
        {"status": "accepted"},
        {"id": request_id}
    )

    if not updated:
        return False

    db_insert_safe(
        "friendships",
        {
            "user_id": sender_id,
            "friend_id": receiver_id
        }
    )

    db_insert_safe(
        "friendships",
        {
            "user_id": receiver_id,
            "friend_id": sender_id
        }
    )

    return True


def friend_rows(uid):
    if not uid:
        return []

    rows = db_select(
        "friendships",
        filters={"user_id": uid},
        limit=100
    )

    friends = []

    for row in rows:
        fid = row.get("friend_id")

        if not fid:
            continue

        profile = db_select(
            "profiles",
            filters={"id": fid},
            limit=1
        )

        if profile:
            friends.append(profile[0])

    return friends


# ------------------------------------------------------------
# CONVERSATION SYSTEM
# ------------------------------------------------------------

def get_or_create_conversation(user_a, user_b):
    if not user_a or not user_b:
        return None

    conversations = db_select(
        "conversations",
        limit=200,
        order="created_at",
        descending=True
    )

    for conversation in conversations:

        member_ids = conversation.get("member_ids")

        if isinstance(member_ids, list):
            normalized = set(str(x) for x in member_ids)

            if normalized == {
                str(user_a),
                str(user_b)
            }:
                return conversation

        participants = conversation.get("participants")

        if isinstance(participants, list):
            normalized = set(str(x) for x in participants)

            if normalized == {
                str(user_a),
                str(user_b)
            }:
                return conversation

    payload = {
        "member_ids": [user_a, user_b]
    }

    return db_insert_safe(
        "conversations",
        payload
    )


def conversation_messages(conversation_id):
    if not conversation_id:
        return []

    return db_select(
        "messages",
        filters={"conversation_id": conversation_id},
        limit=200,
        order="created_at",
        descending=False
    )


def render_messages(conversation_id):
    messages = conversation_messages(conversation_id)

    if not messages:
        st.info("No messages yet. Start the conversation.")
        return

    for message in messages:

        sender_id = message.get("sender_id")
        content = message.get("content") or ""

        sender_name = profile_username(sender_id)

        if sender_id == auth_user_id():
            label = "You"
        else:
            label = f"@{sender_name}"

        with st.chat_message(
            "user" if sender_id == auth_user_id() else "assistant"
        ):
            st.markdown(f"**{label}**")
            st.write(content)


def send_text_message(conversation_id, sender_id, content):
    if not conversation_id or not sender_id:
        return None

    content = str(content or "").strip()

    if not content:
        return None

    content = content[:4000]

    return db_insert_safe(
        "messages",
        {
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": "text"
        }
    )


# ------------------------------------------------------------
# VOICE MESSAGE STORAGE
# ------------------------------------------------------------

def upload_voice_message(file_obj, user_id):
    if not file_obj or not user_id or not supabase_available():
        return None

    try:
        filename = (
            f"{user_id}/"
            f"{int(time.time())}_"
            f"{secrets.token_hex(5)}.wav"
        )

        data = file_obj.getvalue()

        supabase.storage.from_(
            "voice-messages"
        ).upload(
            filename,
            data,
            {
                "content-type": "audio/wav",
                "upsert": False
            }
        )

        return filename

    except Exception as exc:
        st.warning(f"Voice upload failed: {exc}")
        return None


def create_voice_message(
    conversation_id,
    sender_id,
    storage_path,
    duration_seconds=None
):
    if not conversation_id or not sender_id or not storage_path:
        return None

    return db_insert_safe(
        "voice_messages",
        {
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "storage_path": storage_path,
            "duration_seconds": duration_seconds
        }
    )


def get_voice_messages(conversation_id):
    if not conversation_id:
        return []

    return db_select(
        "voice_messages",
        filters={"conversation_id": conversation_id},
        limit=100,
        order="created_at",
        descending=False
    )


# ------------------------------------------------------------
# STORAGE URL
# ------------------------------------------------------------

def create_signed_url(bucket, path, expires=3600):
    if not supabase_available() or not path:
        return None

    try:
        result = supabase.storage.from_(bucket).create_signed_url(
            path,
            expires
        )

        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl")

        return getattr(
            result,
            "signedURL",
            None
        ) or getattr(
            result,
            "signedUrl",
            None
        )

    except Exception:
        return None


# ------------------------------------------------------------
# STORIES
# ------------------------------------------------------------

def upload_story_media(file_obj, user_id):
    if not file_obj or not user_id:
        return None

    try:
        extension = "jpg"

        mime = getattr(file_obj, "type", "") or ""

        if "png" in mime:
            extension = "png"

        elif "webp" in mime:
            extension = "webp"

        filename = (
            f"{user_id}/"
            f"{int(time.time())}_"
            f"{secrets.token_hex(5)}."
            f"{extension}"
        )

        supabase.storage.from_(
            "stories"
        ).upload(
            filename,
            file_obj.getvalue(),
            {
                "content-type": mime or "image/jpeg",
                "upsert": False
            }
        )

        return filename

    except Exception as exc:
        st.warning(f"Story upload failed: {exc}")
        return None


def create_story(
    user_id,
    storage_path,
    caption="",
    filter_name="Original"
):
    if not user_id or not storage_path:
        return None

    return db_insert_safe(
        "stories",
        {
            "user_id": user_id,
            "media_path": storage_path,
            "caption": caption[:500],
            "filter_name": filter_name
        }
    )


def friend_stories(uid):
    friends = friend_rows(uid)

    friend_ids = [
        f.get("id")
        for f in friends
        if f.get("id")
    ]

    friend_ids.append(uid)

    all_stories = db_select(
        "stories",
        limit=200,
        order="created_at",
        descending=True
    )

    return [
        story
        for story in all_stories
        if story.get("user_id") in friend_ids
    ]


# ------------------------------------------------------------
# FRIEND STREAKS
# ------------------------------------------------------------

def get_streak(uid, friend_id):
    rows = db_select(
        "friend_streaks",
        limit=10
    )

    for row in rows:

        a = row.get("user_id")
        b = row.get("friend_id")

        if (
            (a == uid and b == friend_id)
            or
            (a == friend_id and b == uid)
        ):
            return row

    return None


def update_friend_streak(uid, friend_id):
    if not uid or not friend_id:
        return

    existing = get_streak(uid, friend_id)

    today = date.today().isoformat()

    if not existing:

        db_insert_safe(
            "friend_streaks",
            {
                "user_id": uid,
                "friend_id": friend_id,
                "current_streak": 1,
                "last_interaction_date": today
            }
        )

        return

    last_date = existing.get(
        "last_interaction_date"
    )

    current = int(
        existing.get("current_streak") or 0
    )

    if last_date == today:
        return

    try:
        previous = date.fromisoformat(
            str(last_date)
        )

        gap = (
            date.today() - previous
        ).days

    except Exception:
        gap = 999

    if gap == 1:
        current += 1

    else:
        current = 1

    db_update_safe(
        "friend_streaks",
        {
            "current_streak": current,
            "last_interaction_date": today
        },
        {
            "id": existing.get("id")
        }
    )


# ------------------------------------------------------------
# CHALLENGES
# ------------------------------------------------------------

CHALLENGE_TYPES = {
    "Attention Hunt": {
        "emoji": "👀",
        "description": "Find the correct target among distractors."
    },
    "Memory Mission": {
        "emoji": "🧠",
        "description": "Remember a short sequence."
    },
    "Reaction Race": {
        "emoji": "⚡",
        "description": "Respond as quickly as possible."
    },
    "Pattern Lock": {
        "emoji": "🔐",
        "description": "Solve the hidden sequence."
    },
    "Decision & Reward": {
        "emoji": "💰",
        "description": "Choose between immediate and delayed rewards."
    },
    "Mystery Case": {
        "emoji": "🕵️",
        "description": "Interpret a situation and identify relevant clues."
    },
    "Stroop Control": {
        "emoji": "🎨",
        "description": "Test cognitive control under interference."
    },
    "Logic Puzzle": {
        "emoji": "🧩",
        "description": "Solve a short reasoning puzzle."
    }
}


def create_challenge(
    sender_id,
    receiver_id,
    challenge_type,
    title,
    situation,
    question,
    puzzle_data=None,
    media_path=None
):
    return db_insert_safe(
        "challenges",
        {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "challenge_type": challenge_type,
            "title": title[:200],
            "situation": situation[:2000],
            "question": question[:1000],
            "puzzle_data": puzzle_data or {},
            "media_path": media_path,
            "status": "pending"
        }
    )


def challenge_rows_for_user(uid):
    if not uid:
        return []

    rows = db_select(
        "challenges",
        limit=200,
        order="created_at",
        descending=True
    )

    return [
        row
        for row in rows
        if uid in {
            row.get("sender_id"),
            row.get("receiver_id")
        }
    ]


# ------------------------------------------------------------
# CHALLENGE VISUAL PUZZLE
# ------------------------------------------------------------

def render_attention_challenge():
    st.markdown("### 👀 Attention Hunt")

    target = "🔺"

    options = [
        "⚪",
        "🔵",
        "🟢",
        "🟡",
        "🔺",
        "🟣",
        "🟠",
        "⚫"
    ]

    random.shuffle(options)

    choice = st.radio(
        "Find the target:",
        options,
        horizontal=True,
        key="attention_challenge_choice"
    )

    return choice == target


def render_memory_challenge():
    st.markdown("### 🧠 Memory Mission")

    if "memory_challenge_sequence" not in st.session_state:
        st.session_state.memory_challenge_sequence = (
            str(random.randint(100000, 999999))
        )

    if not st.session_state.get(
        "memory_challenge_revealed"
    ):
        st.info(
            "Memorize the sequence shown below. "
            "It will disappear when you start the answer."
        )

        st.markdown(
            f"# {st.session_state.memory_challenge_sequence}"
        )

        if st.button(
            "I memorized it",
            key="memory_hide"
        ):
            st.session_state.memory_challenge_revealed = True
            st.rerun()

        return None

    answer = st.text_input(
        "Enter the sequence you remember",
        key="memory_challenge_answer"
    )

    if st.button(
        "Check Memory",
        key="memory_check"
    ):
        return (
            answer.strip()
            ==
            st.session_state.memory_challenge_sequence
        )

    return None


def render_decision_challenge():
    st.markdown("### 💰 Decision & Reward")

    st.write(
        "Situation: You can receive PKR 1,000 today "
        "or PKR 1,500 after 30 days."
    )

    choice = st.radio(
        "What would you choose?",
        [
            "PKR 1,000 today",
            "PKR 1,500 after 30 days"
        ],
        key="decision_challenge_choice"
    )

    if st.button(
        "Submit Decision",
        key="decision_submit"
    ):
        return {
            "answer": choice,
            "reasoning": (
                "This challenge explores "
                "intertemporal choice and reward valuation."
            )
        }

    return None


def render_pattern_challenge():
    st.markdown("### 🔐 Pattern Lock")

    sequence = [2, 4, 8, 16, 32]

    st.write(
        " → ".join(str(x) for x in sequence)
    )

    answer = st.number_input(
        "What comes next?",
        min_value=0,
        max_value=1000,
        value=64,
        step=1,
        key="pattern_challenge_answer"
    )

    if st.button(
        "Check Pattern",
        key="pattern_challenge_check"
    ):
        return int(answer) == 64

    return None


# ------------------------------------------------------------
# CHALLENGE VISUAL UPLOAD
# ------------------------------------------------------------

def upload_challenge_visual(file_obj, uid):
    if not file_obj or not uid:
        return None

    try:
        mime = file_obj.type or "image/png"

        extension = "png"

        if "jpeg" in mime or "jpg" in mime:
            extension = "jpg"

        elif "webp" in mime:
            extension = "webp"

        path = (
            f"{uid}/"
            f"{int(time.time())}_"
            f"{secrets.token_hex(5)}."
            f"{extension}"
        )

        supabase.storage.from_(
            "challenge-media"
        ).upload(
            path,
            file_obj.getvalue(),
            {
                "content-type": mime,
                "upsert": False
            }
        )

        return path

    except Exception as exc:
        st.warning(
            f"Challenge visual upload failed: {exc}"
        )

        return None


# ------------------------------------------------------------
# INVITE SYSTEM
# ------------------------------------------------------------

def make_invite_link(username):
    username = safe_username(username)

    base_url = (
        st.get_option(
            "browser.serverAddress"
        )
        or "https://neuro-lens-ayna.streamlit.app"
    )

    return (
        base_url
        + "/?ref="
        + urllib.parse.quote(username)
    )


def render_invite_buttons(link):
    st.markdown("### 📨 Invite Friends")

    st.code(link)

    col1, col2 = st.columns(2)

    with col1:
        st.link_button(
            "💬 WhatsApp",
            "https://wa.me/?text="
            + urllib.parse.quote(
                "Join me on NEUROLENS: " + link
            ),
            use_container_width=True
        )

    with col2:
        st.link_button(
            "✈️ Telegram",
            "https://t.me/share/url?url="
            + urllib.parse.quote(link)
            + "&text="
            + urllib.parse.quote(
                "Join me on NEUROLENS"
            ),
            use_container_width=True
        )

    col3, col4 = st.columns(2)

    with col3:
        st.link_button(
            "📧 Email",
            "mailto:?subject="
            + urllib.parse.quote(
                "Join me on NEUROLENS"
            )
            + "&body="
            + urllib.parse.quote(
                "Join me here: " + link
            ),
            use_container_width=True
        )

    with col4:
        st.link_button(
            "📱 SMS",
            "sms:?body="
            + urllib.parse.quote(
                "Join me on NEUROLENS: " + link
            ),
            use_container_width=True
        )

    st.caption(
        "Instagram/Snapchat sharing depends on the "
        "device/app share system. NEUROLENS cannot "
        "send private messages through those apps "
        "without their official APIs."
    )


# ------------------------------------------------------------
# STORIES UI
# ------------------------------------------------------------

def render_stories(uid):
    st.subheader("📖 Stories")

    tab1, tab2 = st.tabs(
        [
            "➕ Create Story",
            "👀 View Stories"
        ]
    )

    with tab1:

        image = st.camera_input(
            "Take a picture",
            key="story_camera"
        )

        upload = st.file_uploader(
            "Or upload an image",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            key="story_upload"
        )

        selected = image or upload

        caption = st.text_input(
            "Story text",
            placeholder="Add a caption..."
        )

        filter_name = st.selectbox(
            "Filter",
            [
                "Original",
                "Soft",
                "Warm",
                "Cool",
                "High Contrast",
                "Black & White"
            ]
        )

        emoji = st.selectbox(
            "Emoji sticker",
            [
                "",
                "🧠",
                "🔥",
                "❤️",
                "😂",
                "😎",
                "✨",
                "👀",
                "🧩"
            ]
        )

        if selected:
            st.image(
                selected,
                use_container_width=True
            )

        if st.button(
            "📤 Post Story",
            type="primary",
            disabled=selected is None,
            use_container_width=True
        ):
            path = upload_story_media(
                selected,
                uid
            )

            if path:

                final_caption = (
                    emoji + " " + caption
                ).strip()

                result = create_story(
                    uid,
                    path,
                    final_caption,
                    filter_name
                )

                if result:
                    st.success(
                        "Story posted successfully."
                    )
                    st.rerun()

    with tab2:

        stories = friend_stories(uid)

        if not stories:
            st.info(
                "No stories yet. Create the first one."
            )

        for story in stories:

            path = story.get("media_path")

            url = create_signed_url(
                "stories",
                path
            )

            owner = profile_username(
                story.get("user_id")
            )

            st.markdown(
                f"### @{owner}"
            )

            if url:
                st.image(
                    url,
                    use_container_width=True
                )

            if story.get("caption"):
                st.write(
                    story.get("caption")
                )

            st.divider()


# ------------------------------------------------------------
# NEUROSOCIAL PAGE
# ------------------------------------------------------------

def page_neurosocial():

    st.header("👥 NeuroSocial")

    st.caption(
        "Connect with friends, chat, share voice messages, "
        "stories and brain challenges."
    )

    if not social_require_auth():
        return

    uid = auth_user_id()

    tabs = st.tabs(
        [
            "👤 Profile",
            "🤝 Friends",
            "💬 Chat",
            "📖 Stories",
            "🧠 Challenges",
            "♟️ Chess",
            "🎲 Ludo",
            "📨 Invite"
        ]
    )

    # ========================================================
    # PROFILE
    # ========================================================

    with tabs[0]:

        profile = load_my_profile() or {}

        st.markdown(
            f"# @{profile.get('username', 'user')}"
        )

        st.write(
            profile.get("display_name")
            or profile.get("username")
            or "NEUROLENS User"
        )

        st.write(
            profile.get("bio")
            or "No bio added yet."
        )

        st.info(
            "Edit your profile from the Account page."
        )

    # ========================================================
    # FRIENDS
    # ========================================================

    with tabs[1]:

        st.subheader("🔎 Find Users")

        search = st.text_input(
            "Search username",
            key="social_user_search"
        )

        if search.strip():

            profiles = db_select(
                "profiles",
                limit=100
            )

            query = search.strip().lower()

            matches = [
                p for p in profiles
                if query in (
                    p.get("username")
                    or ""
                ).lower()
            ]

            if not matches:
                st.info(
                    "No matching users found."
                )

            for person in matches:

                pid = person.get("id")

                if pid == uid:
                    continue

                username = (
                    person.get("username")
                    or "user"
                )

                display = (
                    person.get("display_name")
                    or username
                )

                st.markdown(
                    f"### {display}"
                )

                st.caption(
                    f"@{username}"
                )

                if are_friends(uid, pid):

                    st.success(
                        "🟢 Friends"
                    )

                else:

                    if st.button(
                        f"🤝 Add @{username}",
                        key=f"send_friend_{pid}",
                        use_container_width=True
                    ):

                        ok, message = (
                            send_friend_request(
                                uid,
                                pid
                            )
                        )

                        if ok:
                            st.success(message)

                        else:
                            st.warning(message)

                        st.rerun()

                st.divider()

        # ----------------------------------------------------
        # RECEIVED REQUESTS
        # ----------------------------------------------------

        st.subheader(
            "📥 Received Friend Requests"
        )

        incoming = db_select(
            "friend_requests",
            filters={
                "receiver_id": uid,
                "status": "pending"
            },
            limit=100,
            order="created_at",
            descending=True
        )

        if not incoming:
            st.caption(
                "No pending requests."
            )

        for request in incoming:

            sender_id = request.get(
                "sender_id"
            )

            sender_name = profile_username(
                sender_id
            )

            c1, c2, c3 = st.columns(
                [3, 1, 1]
            )

            with c1:
                st.write(
                    f"@{sender_name}"
                )

            with c2:

                if st.button(
                    "Accept",
                    key=f"accept_{request.get('id')}"
                ):

                    if accept_friend_request(
                        request.get("id"),
                        sender_id,
                        uid
                    ):
                        st.success(
                            "Friend added."
                        )
                        st.rerun()

            with c3:

                if st.button(
                    "Decline",
                    key=f"decline_{request.get('id')}"
                ):

                    db_update_safe(
                        "friend_requests",
                        {"status": "declined"},
                        {"id": request.get("id")}
                    )

                    st.rerun()

        # ----------------------------------------------------
        # SENT REQUESTS
        # ----------------------------------------------------

        st.subheader(
            "📤 Sent Requests"
        )

        sent = db_select(
            "friend_requests",
            filters={
                "sender_id": uid
            },
            limit=100,
            order="created_at",
            descending=True
        )

        for request in sent:

            receiver = profile_username(
                request.get("receiver_id")
            )

            st.write(
                f"@{receiver} — "
                f"{request.get('status', 'pending')}"
            )

        # ----------------------------------------------------
        # FRIEND LIST
        # ----------------------------------------------------

        st.subheader(
            "👥 My Friends"
        )

        friends = friend_rows(uid)

        if not friends:
            st.info(
                "You don't have any friends yet."
            )

        for friend in friends:

            st.write(
                f"• @{friend.get('username', 'user')}"
            )

    # ========================================================
    # CHAT
    # ========================================================

    with tabs[2]:

        friends = friend_rows(uid)

        if not friends:

            st.info(
                "Add a friend first to start chatting."
            )

        else:

            labels = [
                "@"
                + (
                    f.get("username")
                    or "user"
                )
                for f in friends
            ]

            choice = st.selectbox(
                "Choose friend",
                range(len(friends)),
                format_func=lambda i: labels[i],
                key="chat_friend_selector"
            )

            friend = friends[choice]

            friend_id = friend.get("id")

            friend_username = (
                friend.get("username")
                or "user"
            )

            conversation = (
                get_or_create_conversation(
                    uid,
                    friend_id
                )
            )

            if conversation:

                conversation_id = (
                    conversation.get("id")
                )

                # IMPORTANT:
                # Clear specific chat identity.

                st.markdown(
                    f"# 💬 Chat with @{friend_username}"
                )

                st.caption(
                    f"Private 1-to-1 conversation with "
                    f"@{friend_username}"
                )

                st.divider()

                render_messages(
                    conversation_id
                )

                # ------------------------------------------------
                # TEXT MESSAGE
                # ------------------------------------------------

                message = st.chat_input(
                    f"Message @{friend_username}...",
                    key=f"chat_input_{friend_id}"
                )

                if message:

                    result = send_text_message(
                        conversation_id,
                        uid,
                        message
                    )

                    if result:

                        update_friend_streak(
                            uid,
                            friend_id
                        )

                        st.rerun()

                # ------------------------------------------------
                # VOICE MESSAGE
                # ------------------------------------------------

                st.markdown(
                    "### 🎙️ Voice Message"
                )

                voice = st.audio_input(
                    f"Record voice for @{friend_username}",
                    key=f"voice_message_{friend_id}"
                )

                if voice:

                    if st.button(
                        "📤 Send Voice Message",
                        key=f"send_voice_{friend_id}",
                        type="primary",
                        use_container_width=True
                    ):

                        path = upload_voice_message(
                            voice,
                            uid
                        )

                        if path:

                            created = create_voice_message(
                                conversation_id,
                                uid,
                                path
                            )

                            if created:

                                update_friend_streak(
                                    uid,
                                    friend_id
                                )

                                st.success(
                                    "Voice message sent."
                                )

                                st.rerun()

                # ------------------------------------------------
                # VOICE MESSAGE HISTORY
                # ------------------------------------------------

                voice_messages = (
                    get_voice_messages(
                        conversation_id
                    )
                )

                if voice_messages:

                    st.markdown(
                        "### 🔊 Voice Messages"
                    )

                    for vm in voice_messages:

                        sender = profile_username(
                            vm.get("sender_id")
                        )

                        url = create_signed_url(
                            "voice-messages",
                            vm.get("storage_path")
                        )

                        st.caption(
                            f"@{sender}"
                        )

                        if url:
                            st.audio(url)

                        st.divider()

    # ========================================================
    # STORIES
    # ========================================================

    with tabs[3]:

        render_stories(uid)

    # ========================================================
    # CHALLENGES
    # ========================================================

    with tabs[4]:

        st.subheader(
            "🧠 Friend Brain Challenges"
        )

        friends = friend_rows(uid)

        if not friends:

            st.info(
                "Add a friend first."
            )

        else:

            friend_index = st.selectbox(
                "Challenge friend",
                range(len(friends)),
                format_func=lambda i:
                    "@"
                    + (
                        friends[i].get("username")
                        or "user"
                    ),
                key="challenge_friend"
            )

            target_friend = friends[
                friend_index
            ]

            target_id = target_friend.get(
                "id"
            )

            challenge_type = st.selectbox(
                "Challenge type",
                list(CHALLENGE_TYPES.keys()),
                key="challenge_type"
            )

            st.info(
                CHALLENGE_TYPES[
                    challenge_type
                ]["description"]
            )

            title = st.text_input(
                "Challenge title",
                value=challenge_type
            )

            situation = st.text_area(
                "Situation",
                placeholder=(
                    "Example: You enter a busy room. "
                    "Several objects are moving and one "
                    "target signal appears briefly."
                ),
                key="challenge_situation"
            )

            question = st.text_area(
                "Question / decision",
                placeholder=(
                    "What would you do first?"
                ),
                key="challenge_question"
            )

            challenge_visual = st.file_uploader(
                "Optional challenge visual",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp"
                ],
                key="challenge_visual"
            )

            uploaded_path = None

            if challenge_visual:

                st.image(
                    challenge_visual,
                    caption="Challenge visual preview",
                    use_container_width=True
                )

                if st.button(
                    "Upload Challenge Visual",
                    key="upload_challenge_visual",
                    use_container_width=True
                ):

                    uploaded_path = (
                        upload_challenge_visual(
                            challenge_visual,
                            uid
                        )
                    )

                    if uploaded_path:
                        st.session_state[
                            "last_challenge_media"
                        ] = uploaded_path

                        st.success(
                            "Challenge visual uploaded."
                        )

            uploaded_path = (
                st.session_state.get(
                    "last_challenge_media"
                )
            )

            if st.button(
                "🚀 Send Challenge",
                type="primary",
                use_container_width=True
            ):

                if not situation.strip():
                    st.error(
                        "Add a situation first."
                    )

                elif not question.strip():
                    st.error(
                        "Add a question first."
                    )

                else:

                    challenge = create_challenge(
                        uid,
                        target_id,
                        challenge_type,
                        title,
                        situation,
                        question,
                        {
                            "challenge_type":
                                challenge_type
                        },
                        uploaded_path
                    )

                    if challenge:

                        st.success(
                            f"Challenge sent to "
                            f"@{target_friend.get('username', 'user')}."
                        )

                        st.rerun()

        # ----------------------------------------------------
        # RECEIVED / SENT CHALLENGES
        # ----------------------------------------------------

        st.divider()

        challenges = challenge_rows_for_user(
            uid
        )

        for challenge in challenges:

            sender = profile_username(
                challenge.get("sender_id")
            )

            receiver = profile_username(
                challenge.get("receiver_id")
            )

            st.markdown(
                f"### "
                f"{CHALLENGE_TYPES.get(challenge.get('challenge_type'), {}).get('emoji', '🧠')} "
                f"{challenge.get('title', 'Brain Challenge')}"
            )

            st.caption(
                f"From @{sender} → @{receiver}"
            )

            st.write(
                challenge.get("situation")
                or ""
            )

            st.markdown(
                "**Question:** "
                + (
                    challenge.get("question")
                    or ""
                )
            )

            media_path = challenge.get(
                "media_path"
            )

            if media_path:

                media_url = create_signed_url(
                    "challenge-media",
                    media_path
                )

                if media_url:
                    st.image(
                        media_url,
                        use_container_width=True
                    )

            status = challenge.get(
                "status"
            )

            if (
                challenge.get("receiver_id") == uid
                and status == "pending"
            ):

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "Accept",
                        key=f"challenge_accept_{challenge.get('id')}",
                        use_container_width=True
                    ):

                        db_update_safe(
                            "challenges",
                            {"status": "accepted"},
                            {"id": challenge.get("id")}
                        )

                        st.rerun()

                with c2:

                    if st.button(
                        "Decline",
                        key=f"challenge_decline_{challenge.get('id')}",
                        use_container_width=True
                    ):

                        db_update_safe(
                            "challenges",
                            {"status": "declined"},
                            {"id": challenge.get("id")}
                        )

                        st.rerun()

            elif status == "accepted":

                st.markdown(
                    "#### 🎮 Play Challenge"
                )

                result = None

                ctype = challenge.get(
                    "challenge_type"
                )

                if ctype == "Attention Hunt":

                    result = (
                        render_attention_challenge()
                    )

                elif ctype == "Memory Mission":

                    result = (
                        render_memory_challenge()
                    )

                elif ctype == "Decision & Reward":

                    result = (
                        render_decision_challenge()
                    )

                elif ctype == "Pattern Lock":

                    result = (
                        render_pattern_challenge()
                    )

                else:

                    answer = st.text_area(
                        "Your response",
                        key=f"generic_answer_{challenge.get('id')}"
                    )

                    if st.button(
                        "Submit Challenge",
                        key=f"submit_generic_{challenge.get('id')}"
                    ):

                        result = {
                            "answer": answer,
                            "correct": None
                        }

                if result is not None:

                    if isinstance(
                        result,
                        dict
                    ):
                        answer_data = result
                        correct = result.get(
                            "correct"
                        )

                    else:
                        answer_data = {
                            "answer": result
                        }

                        correct = bool(
                            result
                        )

                    if correct is True:
                        score = 100

                    elif correct is False:
                        score = 0

                    else:
                        score = 50

                    db_insert_safe(
                        "challenge_results",
                        {
                            "challenge_id":
                                challenge.get("id"),
                            "user_id": uid,
                            "score": score,
                            "result_data":
                                answer_data
                        }
                    )

                    db_update_safe(
                        "challenges",
                        {
                            "status":
                                "completed"
                        },
                        {
                            "id":
                                challenge.get("id")
                        }
                    )

                    st.success(
                        f"Challenge completed — Score: {score}/100"
                    )

                    st.rerun()

            st.divider()

    # ========================================================
    # CHESS
    # ========================================================

    with tabs[5]:

        st.subheader(
            "♟️ Friend Chess Room"
        )

        st.caption(
            "Turn-based friend chess room. "
            "The game state is stored in Supabase."
        )

        friends = friend_rows(uid)

        if not friends:

            st.info(
                "Add a friend to start a chess game."
            )

        else:

            friend_index = st.selectbox(
                "Play against",
                range(len(friends)),
                format_func=lambda i:
                    "@"
                    + (
                        friends[i].get("username")
                        or "user"
                    ),
                key="chess_friend_select"
            )

            opponent = friends[
                friend_index
            ]

            opponent_id = opponent.get(
                "id"
            )

            if st.button(
                "♟️ Create Chess Game",
                type="primary",
                use_container_width=True
            ):

                db_insert_safe(
                    "chess_games",
                    {
                        "challenger_id": uid,
                        "opponent_id": opponent_id,
                        "board_state": {
                            "moves": []
                        },
                        "turn_user_id": uid,
                        "status": "active"
                    }
                )

                st.success(
                    "Chess game created."
                )

                st.rerun()

            games = db_select(
                "chess_games",
                limit=100,
                order="created_at",
                descending=True
            )

            for game in games:

                players = {
                    game.get("challenger_id"),
                    game.get("opponent_id")
                }

                if uid not in players:
                    continue

                st.markdown(
                    "### ♟️ Chess Match"
                )

                opponent_name = profile_username(
                    game.get("opponent_id")
                    if game.get("challenger_id") == uid
                    else game.get("challenger_id")
                )

                st.caption(
                    f"Opponent: @{opponent_name}"
                )

                turn = game.get(
                    "turn_user_id"
                )

                if turn == uid:
                    st.success(
                        "🟢 Your turn"
                    )
                else:
                    st.info(
                        f"⏳ Waiting for @{profile_username(turn)}"
                    )

                board_state = (
                    game.get("board_state")
                    or {}
                )

                moves = (
                    board_state.get("moves")
                    or []
                )

                st.markdown(
                    "#### Move history"
                )

                if moves:
                    for index, move in enumerate(
                        moves[-20:],
                        start=max(
                            1,
                            len(moves) - 19
                        )
                    ):
                        st.write(
                            f"{index}. {move}"
                        )
                else:
                    st.caption(
                        "No moves yet."
                    )

                move = st.text_input(
                    "Enter move, e.g. e2-e4",
                    key=f"chess_move_{game.get('id')}"
                )

                if st.button(
                    "Play Move",
                    key=f"chess_play_{game.get('id')}",
                    use_container_width=True
                ):

                    if turn != uid:

                        st.warning(
                            "It is not your turn."
                        )

                    elif not move.strip():

                        st.warning(
                            "Enter a move first."
                        )

                    else:

                        updated_moves = (
                            list(moves)
                        )

                        updated_moves.append(
                            move.strip()[:30]
                        )

                        opponent_id = (
                            game.get("opponent_id")
                            if game.get("challenger_id") == uid
                            else game.get("challenger_id")
                        )

                        db_update_safe(
                            "chess_games",
                            {
                                "board_state": {
                                    "moves":
                                        updated_moves
                                },
                                "turn_user_id":
                                    opponent_id
                            },
                            {
                                "id":
                                    game.get("id")
                            }
                        )

                        st.rerun()

                st.divider()

    # ========================================================
    # LUDO
    # ========================================================

    with tabs[6]:

        st.subheader(
            "🎲 Friend Ludo Room"
        )

        friends = friend_rows(uid)

        if not friends:

            st.info(
                "Add a friend to start Ludo."
            )

        else:

            friend_index = st.selectbox(
                "Play against",
                range(len(friends)),
                format_func=lambda i:
                    "@"
                    + (
                        friends[i].get("username")
                        or "user"
                    ),
                key="ludo_friend_select"
            )

            opponent = friends[
                friend_index
            ]

            opponent_id = opponent.get(
                "id"
            )

            if st.button(
                "🎲 Create Ludo Game",
                type="primary",
                use_container_width=True
            ):

                db_insert_safe(
                    "ludo_games",
                    {
                        "player1_id": uid,
                        "player2_id": opponent_id,
                        "game_state": {
                            "p1": 0,
                            "p2": 0,
                            "turn": uid,
                            "winner": None
                        },
                        "status": "active"
                    }
                )

                st.success(
                    "Ludo game created."
                )

                st.rerun()

            games = db_select(
                "ludo_games",
                limit=100,
                order="created_at",
                descending=True
            )

            for game in games:

                players = {
                    game.get("player1_id"),
                    game.get("player2_id")
                }

                if uid not in players:
                    continue

                state = (
                    game.get("game_state")
                    or {}
                )

                st.markdown(
                    "### 🎲 Ludo Match"
                )

                p1 = state.get(
                    "p1",
                    0
                )

                p2 = state.get(
                    "p2",
                    0
                )

                turn = state.get(
                    "turn"
                )

                st.write(
                    f"Your position: "
                    f"{p1 if game.get('player1_id') == uid else p2}"
                )

                st.write(
                    f"Opponent position: "
                    f"{p2 if game.get('player1_id') == uid else p1}"
                )

                if turn == uid:

                    st.success(
                        "🟢 Your turn"
                    )

                    if st.button(
                        "🎲 Roll Dice",
                        key=f"ludo_roll_{game.get('id')}",
                        use_container_width=True
                    ):

                        dice = random.randint(
                            1,
                            6
                        )

                        if game.get(
                            "player1_id"
                        ) == uid:

                            p1 += dice

                            if p1 >= 30:
                                winner = uid
                            else:
                                winner = None

                        else:

                            p2 += dice

                            if p2 >= 30:
                                winner = uid
                            else:
                                winner = None

                        next_turn = (
                            game.get("player2_id")
                            if game.get("player1_id") == uid
                            else game.get("player1_id")
                        )

                        new_state = {
                            "p1": p1,
                            "p2": p2,
                            "turn": next_turn,
                            "winner": winner
                        }

                        db_update_safe(
                            "ludo_games",
                            {
                                "game_state":
                                    new_state,
                                "status":
                                    "completed"
                                    if winner
                                    else "active"
                            },
                            {
                                "id":
                                    game.get("id")
                            }
                        )

                        st.success(
                            f"You rolled {dice}."
                        )

                        st.rerun()

                else:

                    st.info(
                        "Waiting for your friend."
                    )

                if state.get("winner"):

                    if state.get("winner") == uid:
                        st.success(
                            "🎉 Game completed."
                        )
                    else:
                        st.info(
                            "Game completed."
                        )

                st.divider()

    # ========================================================
    # INVITE
    # ========================================================

    with tabs[7]:

        profile = load_my_profile() or {}

        username = (
            profile.get("username")
            or "user"
        )

        link = make_invite_link(
            username
        )

        render_invite_buttons(
            link
        )


# ============================================================
# FINAL SIDEBAR
# ============================================================

def render_sidebar():

    with st.sidebar:

        st.markdown(
            "# 🧠 NEUROLENS"
        )

        st.caption(
            "Explore cognition, behavior & the brain"
        )

        st.divider()

        page = st.radio(
            "Navigate",
            [
                "🏠 Home",
                "🧠 Brain Journey",
                "🔬 Cognitive Lab",
                "🧩 Brain Puzzle",
                "🎙️ Voice Mood",
                "😊 Mood & Feelings",
                "🎮 Cognitive Games",
                "👥 NeuroSocial",
                "👤 Account",
                "🔐 Private Ayna",
                "🤖 Ask Ayna",
                "📚 Research Book",
                "💬 1-to-1 Session",
                "📊 My Progress",
                "🛡️ Security & Privacy",
                "⚙️ Settings"
            ],
            key="main_navigation"
        )

        st.divider()

        uid = auth_user_id()

        if uid:

            st.success(
                f"Signed in as "
                f"@{profile_username(uid)}"
            )

        else:

            st.warning(
                "Not signed in"
            )

        if supabase_available():

            st.caption(
                "🟢 Supabase connected"
            )

        else:

            st.caption(
                "🔴 Supabase not connected"
            )

        st.divider()

        st.caption(
            "NEUROLENS is an educational/research "
            "exploration tool. Simulated experiments "
            "and AI interpretations are not clinical "
            "diagnosis or direct measurement of brain activity."
        )

    return page


# ============================================================
# FINAL ROUTER
# ============================================================

selected_page = render_sidebar()


if selected_page == "🏠 Home":

    page_welcome()


elif selected_page == "🧠 Brain Journey":

    page_brain_journey()


elif selected_page == "🔬 Cognitive Lab":

    page_lab()


elif selected_page == "🧩 Brain Puzzle":

    page_brain_puzzle()


elif selected_page == "🎙️ Voice Mood":

    page_voice_mood()


elif selected_page == "😊 Mood & Feelings":

    page_mood_feelings()


elif selected_page == "🎮 Cognitive Games":

    page_cognitive_games()


elif selected_page == "👥 NeuroSocial":

    page_neurosocial()


elif selected_page == "👤 Account":

    page_account()


elif selected_page == "🔐 Private Ayna":

    page_private_ayna()


elif selected_page == "🤖 Ask Ayna":

    page_ask_ayna()


elif selected_page == "📚 Research Book":

    page_research_book()


elif selected_page == "💬 1-to-1 Session":

    page_one_to_one()


elif selected_page == "📊 My Progress":

    page_my_progress()


elif selected_page == "🛡️ Security & Privacy":

    page_security_privacy()


elif selected_page == "⚙️ Settings":

    page_settings()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        padding:20px 5px;
        opacity:0.75;
    ">
        <strong>NEUROLENS</strong><br>
        Explore cognition, behavior & the brain<br><br>
        Built by <strong>Ayna Jaffri</strong><br>
        Independent Cognitive Neuroscience Researcher
    </div>
    """,
    unsafe_allow_html=True
)
            


