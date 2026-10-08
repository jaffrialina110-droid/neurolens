import os
import random
import time
import hashlib
import secrets
import html
from io import BytesIO

import streamlit as st
from PIL import Image

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

try:
    import requests
except Exception:
    requests = None

try:
    from supabase import create_client
except Exception:
    create_client = None


# ============================================================
# NEUROLENS
# Explore cognition, behavior & the brain
# Created by Ayna Jaffri
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS & ASSETS
# ============================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset_path(filename):
    paths = [
        os.path.join(ASSETS, filename),
        os.path.join(ROOT, filename),
    ]

    for path in paths:
        if os.path.exists(path):
            return path

    return None


def find_asset(*names):
    for name in names:
        path = asset_path(name)
        if path:
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
    "ayna_reboot_voiced_louder.mp4",
    "ayna_reboot.mp4",
)

BRAIN_ANIMATION = find_asset(
    "brain_animation.mp4",
)

LAB_VIDEO = find_asset(
    "cognitive_lab_brain.mp4",
)


# ============================================================
# GLOBAL STYLE
# IMPORTANT: ALL HTML MUST USE unsafe_allow_html=True
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

.nl-hero h1 {
    margin-bottom: 4px;
}

.nl-hero p {
    color: #b9d7ef;
    font-size: 1.05rem;
    margin-bottom: 5px;
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
    filter: drop-shadow(0 0 25px rgba(100,200,255,0.65));
    animation: nlFloat 3s ease-in-out infinite;
}

.nl-robot {
    position: absolute;
    right: 12%;
    bottom: 25px;
    font-size: 5rem;
    filter: drop-shadow(0 0 18px rgba(180,150,255,0.55));
    animation: nlFloat 3.5s ease-in-out infinite;
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
    animation: nlPulse 2.2s ease-in-out infinite;
}

@keyframes nlPulse {
    50% {
        transform: scale(1.08);
    }
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
    overflow: hidden;
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

.nl-selected {
    border: 1px solid rgba(110,205,255,0.55);
    background: rgba(35,100,145,0.24);
}

.nl-stat {
    text-align: center;
    padding: 14px;
    border-radius: 16px;
    background: rgba(12,29,48,0.8);
    border: 1px solid rgba(110,165,210,0.20);
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SAFE HTML HELPER
# ============================================================

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
# SESSION STATE
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


DEFAULT_STATE = {
    "page": "NeuroWorld",
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

    "lab_character": "Researcher",
    "lab_equipment": "EEG Simulator",
    "lab_experiment": "Attention",
    "lab_phase": "setup",
    "lab_result": None,

    "journey_index": 0,

    "puzzle_size": 3,
    "puzzle_board": [],
    "puzzle_solution": [],
    "puzzle_moves": 0,
    "puzzle_started": False,
    "puzzle_start_time": None,
    "puzzle_completed": False,

    "mood_text_result": None,
    "mood_voice_result": None,
    "mood_camera_result": None,

    "private_pin_hash": None,
    "private_pin_salt": None,
    "private_unlocked": False,

    "consultation_status": "Not started",
    "consultation_method": None,
    "consultation_data": None,
    "consultation_messages": [],

    "settings_model": "gemini-2.5-flash",
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        if isinstance(value, dict):
            st.session_state[key] = value.copy()

        elif isinstance(value, list):
            st.session_state[key] = value.copy()

        else:
            st.session_state[key] = value


# ============================================================
# NAVIGATION
# ============================================================

PAGES = [
    "NeuroWorld",
    "Cognitive Lab",
    "Explore Brain",
    "Brain Puzzle",
    "Brain Challenges",
    "AI Mood & Behaviour",
    "Research World",
    "Ask Ayna",
    "Private Ask Ayna",
    "Behaviour Decoding",
    "My Progress",
    "Security & Privacy",
    "Settings",
]


def navigate(page):
    st.session_state.page = page
    st.rerun()


# ============================================================
# SECRETS
# ============================================================

def secret_value(name, default=""):

    try:
        value = st.secrets.get(name)

        if value is not None:
            value = str(value).strip()

            if value:
                return value

    except Exception:
        pass

    value = os.getenv(name, "").strip()

    return value if value else default


GEMINI_API_KEY = secret_value("GEMINI_API_KEY")

GEMINI_MODEL = secret_value(
    "GEMINI_MODEL",
    st.session_state.get(
        "settings_model",
        "gemini-2.5-flash",
    ),
)

SUPABASE_URL = secret_value("SUPABASE_URL")
SUPABASE_KEY = secret_value("SUPABASE_KEY")

EASYPAISA_NAME = secret_value(
    "EASYPAISA_NAME",
    "Ayna Jaffri",
)

EASYPAISA_NUMBER = secret_value(
    "EASYPAISA_NUMBER",
    "",
)

INTERNATIONAL_PAYMENT_URL = secret_value(
    "INTERNATIONAL_PAYMENT_URL",
    "",
)

PAYMENT_ADMIN_KEY = secret_value(
    "PAYMENT_ADMIN_KEY",
    "",
)


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource(show_spinner=False)
def get_supabase():

    if not SUPABASE_URL:
        return None

    if not SUPABASE_KEY:
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
        SUPABASE.table(table).insert(data).execute()
        return True
    except Exception:
        return False


# ============================================================
# GEMINI
# ============================================================

@st.cache_resource(show_spinner=False)
def get_gemini_client(api_key):

    if not api_key:
        return None

    if genai is None:
        return None

    try:
        return genai.Client(
            api_key=api_key
        )
    except Exception:
        return None


GEMINI = get_gemini_client(
    GEMINI_API_KEY
)


AI_SESSION_LIMIT = 20


def ask_ai(
    prompt,
    context="",
    max_tokens=500,
):

    cache_key = hashlib.sha256(
        (
            prompt
            + "\n"
            + context
        ).encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()

    if cache_key in st.session_state.ai_cache:
        return (
            st.session_state.ai_cache[cache_key],
            "cache",
        )

    if st.session_state.ai_requests >= AI_SESSION_LIMIT:

        return (
            "AI session limit reached. "
            "You can continue using the local "
            "NeuroLens experiments and brain activities.",
            "limit",
        )

    if GEMINI is None:

        return (
            "Ayna AI is currently offline. "
            "Please add GEMINI_API_KEY to Streamlit Secrets.",
            "offline",
        )

    system_prompt = """
You are Ayna, the AI cognitive-neuroscience assistant
inside NEUROLENS.

Your role:
- explain cognitive neuroscience clearly
- discuss brain, behaviour, learning, attention,
  memory, decision-making and consciousness
- distinguish established evidence from hypotheses
- be scientifically cautious
- use concise language

Important safety rules:
- Do not diagnose mental or neurological disorders.
- Do not claim that a game measures brain activity.
- Do not claim that voice or facial analysis can read someone's mind.
- Do not infer sensitive traits such as identity, race,
  religion, sexuality or political beliefs.
- Voice and face outputs are AI-assisted estimates only.
- Self-report results are not clinical measurements.
- Encourage professional help for serious health concerns.

User language:
%s
""" % st.session_state.get(
        "language",
        "English",
    )

    full_prompt = (
        system_prompt
        + "\n\nContext:\n"
        + context[-5000:]
        + "\n\nUser request:\n"
        + prompt
    )

    try:

        st.session_state.ai_requests += 1

        config = None

        if types is not None:
            config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_tokens,
            )

        response = GEMINI.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=config,
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

        st.session_state.progress[
            "ai_requests"
        ] = st.session_state.ai_requests

        return answer, "ai"

    except Exception:

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

    if types is None:
        return (
            "Voice processing is unavailable "
            "in this environment.",
            "offline",
        )

    if st.session_state.ai_requests >= AI_SESSION_LIMIT:
        return (
            "AI session limit reached.",
            "limit",
        )

    try:

        st.session_state.ai_requests += 1

        audio_bytes = audio_file.getvalue()

        mime_type = (
            getattr(
                audio_file,
                "type",
                None,
            )
            or "audio/wav"
        )

        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type,
        )

        response = GEMINI.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                audio_part,
                instruction,
            ],
        )

        answer = (
            getattr(response, "text", None)
            or "No voice interpretation was returned."
        ).strip()

        st.session_state.progress[
            "ai_requests"
        ] = st.session_state.ai_requests

        return answer, "ai"

    except Exception:

        return (
            "Ayna could not process this voice "
            "recording right now.",
            "error",
        )


# ============================================================
# BRAIN DATA
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
        "image": [
            "hippocampus.png",
            "hippocampus.jpg",
        ],
        "description": (
            "The hippocampus is strongly involved "
            "in episodic memory and spatial "
            "representation."
        ),
        "focus": "Memory and navigation",
    },
    {
        "name": "Striatum",
        "emoji": "🔄",
        "image": [
            "striatum.png",
            "striatum.jpg",
        ],
        "description": (
            "The striatum contributes to action "
            "selection, reward learning and habit "
            "formation."
        ),
        "focus": "Reward and action selection",
    },
    {
        "name": "Anterior Cingulate Cortex",
        "emoji": "⚖️",
        "image": [
            "acc.png",
            "acc.jpg",
            "anterior_cingulate_cortex.png",
        ],
        "description": (
            "The anterior cingulate cortex contributes "
            "to performance monitoring, conflict "
            "processing and cognitive control."
        ),
        "focus": "Conflict and performance monitoring",
    },
    {
        "name": "Attention Networks",
        "emoji": "👁️",
        "image": [
            "attention_network.png",
            "attention_network.jpg",
            "attention_network.gif",
        ],
        "description": (
            "Attention depends on interacting neural "
            "systems that help select, prioritize and "
            "sustain information processing."
        ),
        "focus": "Selection and cognitive priority",
    },
]


# ============================================================
# RESEARCH TOPICS
# ============================================================

RESEARCH_TOPICS = {
    "Consciousness": (
        "Consciousness concerns subjective experience "
        "and awareness. Neuroscience studies associated "
        "brain processes, but explaining why neural "
        "activity is accompanied by subjective experience "
        "remains an open scientific problem."
    ),
    "Memory": (
        "Memory includes processes such as encoding, "
        "consolidation and retrieval. Different forms "
        "of memory rely on partly overlapping neural "
        "systems."
    ),
    "Attention": (
        "Attention changes which information receives "
        "greater processing priority. It involves "
        "interacting sensory and control networks."
    ),
    "Decision Making": (
        "Decision-making integrates reward, goals, "
        "uncertainty, memory and cognitive control."
    ),
    "Neuroplasticity": (
        "Neuroplasticity refers to changes in nervous "
        "system structure or function associated with "
        "development, learning, experience and other "
        "conditions."
    ),
    "Emotion": (
        "Emotion emerges from interactions among brain, "
        "body, learning, appraisal, interoception and "
        "context."
    ),
    "Addiction & Consciousness": (
        "Addiction research examines interactions among "
        "reward learning, motivation, habits, control "
        "systems and environmental context. Questions "
        "about consciousness remain complex and should "
        "not be reduced to one brain region."
    ),
    "CSTC Circuits": (
        "Cortico-striato-thalamo-cortical circuits form "
        "interacting loops involving cortex, striatum, "
        "pallidal structures, subthalamic nucleus and "
        "thalamus. Their functional organization is "
        "context-dependent."
    ),
}


# ============================================================
# LAB DATA
# ============================================================

LAB_CHARACTERS = {
    "Researcher": {
        "emoji": "🧑‍🔬",
        "description": "Research-focused exploration",
    },
    "Student": {
        "emoji": "🎓",
        "description": "Learning-focused exploration",
    },
    "Lab Assistant": {
        "emoji": "👩‍🔬",
        "description": "Experiment support",
    },
    "AI Research Agent": {
        "emoji": "🤖",
        "description": "AI-assisted research exploration",
    },
}


LAB_EQUIPMENT = {
    "EEG Simulator": (
        "Conceptual simulated neural-signal display. "
        "This is not real EEG."
    ),
    "Eye Tracker": (
        "Conceptual gaze and attention measurement "
        "simulation."
    ),
    "Reaction-Time System": (
        "Measures response time for a simple "
        "computer-based task."
    ),
    "Cognitive Task Monitor": (
        "Displays structured cognitive experiments."
    ),
    "Physiological Sensor": (
        "Conceptual physiological signal display. "
        "It is not a medical device."
    ),
}


LAB_EXPERIMENTS = [
    "Attention",
    "Memory",
    "Decision & Reward",
    "Stroop-Cognitive Control",
    "Pattern Recognition",
]


# ============================================================
# MOOD LABELS
# ============================================================

MOOD_EMOJIS = {
    "Happy": "😊",
    "Excited": "🤩",
    "Calm": "😌",
    "Neutral": "😐",
    "Worried": "😟",
    "Sad": "😔",
    "Frustrated": "😤",
    "Tired": "😴",
}


# ============================================================
# LOAD BRAIN IMAGE
# ============================================================

@st.cache_data(show_spinner=False)
def load_brain_image(path):

    if not path:
        return None

    try:
        return Image.open(path).convert("RGB")
    except Exception:
        return None


brain_image = load_brain_image(
    BRAIN_IMAGE
)


# ============================================================
# TEXT-TO-SPEECH BUTTON
# ============================================================

def speak_button(text, key="speak"):

    clean = str(text)

    encoded = (
        clean
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    components_code = f"""
    <button
        id="btn_{key}"
        style="
            padding:10px 16px;
            border-radius:10px;
            border:1px solid #6d91ad;
            background:#163b5d;
            color:white;
            cursor:pointer;
            font-size:15px;
        "
    >
        🔊 Speak Ayna
    </button>

    <script>
    const btn = document.getElementById("btn_{key}");

    if (btn) {{
        btn.addEventListener("click", function() {{
            if ("speechSynthesis" in window) {{
                window.speechSynthesis.cancel();

                const utterance =
                    new SpeechSynthesisUtterance(`{encoded}`);

                utterance.lang = "en-US";
                utterance.rate = 0.92;
                utterance.pitch = 1.02;

                window.speechSynthesis.speak(
                    utterance
                );
            }}
        }});
    }}
    </script>
    """

    import streamlit.components.v1 as components

    components.html(
        components_code,
        height=55,
    )


# ============================================================
# COMMON HEADER
# ============================================================

def page_header(
    title,
    subtitle="",
):

    st.markdown(
        f"""
        <div class="nl-hero">
            <h1>{safe_text(title)}</h1>
            <p>{safe_text(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# WORLD CHARACTER VISUAL
# ============================================================

def neuro_world_visual():

    brain_visual = "🧠"

    if AYNA_ROBOT:
        robot_visual = (
            '<img src="'
            + AYNA_ROBOT
            + '" '
            + 'style="max-width:150px;'
            + 'max-height:180px;'
            + 'object-fit:contain;">'
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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    st.caption(
        "Explore cognition, behavior & the brain"
    )

    language_options = [
        "English",
        "Roman English",
    ]

    selected_language = st.radio(
        "Language",
        language_options,
        index=(
            0
            if st.session_state.language == "English"
            else 1
        ),
        key="sidebar_language",
    )

    st.session_state.language = selected_language

    st.divider()

    st.markdown("### 🌐 NeuroWorld")

    for index, page in enumerate(PAGES):

        label = (
            "● "
            if st.session_state.page == page
            else "○ "
        ) + page

        if st.button(
            label,
            key=f"sidebar_{index}",
            use_container_width=True,
        ):
            navigate(page)

    st.divider()

    st.caption(
        f"AI requests: "
        f"{st.session_state.ai_requests}/"
        f"{AI_SESSION_LIMIT}"
    )

    st.progress(
        min(
            st.session_state.ai_requests
            / AI_SESSION_LIMIT,
            1.0,
        )
    )

    st.caption(
        "AI features require GEMINI_API_KEY. "
        "Local cognitive activities can run "
        "without AI."
    )


# ============================================================
# MAIN WORLD ROUTER STARTS IN PART 2
# ============================================================
# ============================================================
# PART 2 — NEUROWORLD + COGNITIVE LAB + BRAIN JOURNEY
# ============================================================


# ============================================================
# NEUROWORLD
# ============================================================

if st.session_state.page == "NeuroWorld":

    page_header(
        "🧠 NeuroWorld",
        "Enter the NEUROLENS world and choose where you want to explore."
    )

    neuro_world_visual()

    st.markdown(
        """
        <div class="nl-card">
            <h2>🧠 Hi, I am NeuroLens.</h2>
            <p>
                Come with me — I'll show you what you can explore.
            </p>
            <p class="nl-small">
                Your brain guide and Ayna's AI research environment
                are ready for exploration.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    world_text = (
        "Hi, I am NeuroLens. Come with me — "
        "I'll show you what you can explore."
    )

    speak_button(
        world_text,
        "world_intro_voice",
    )

    st.markdown("### 🌌 Choose your destination")

    destinations = [
        (
            "🔬 Cognitive Lab",
            "Run interactive cognitive experiments.",
            "Cognitive Lab",
        ),
        (
            "🧠 Explore Brain",
            "Travel through neurons, synapses and brain systems.",
            "Explore Brain",
        ),
        (
            "🧩 Brain Puzzle",
            "Reconstruct a brain image through a cognitive puzzle.",
            "Brain Puzzle",
        ),
        (
            "🎯 Brain Challenges",
            "Test attention, memory, inhibition and patterns.",
            "Brain Challenges",
        ),
        (
            "🤖 Ask Ayna",
            "Ask the AI cognitive-neuroscience assistant.",
            "Ask Ayna",
        ),
        (
            "🌍 Research World",
            "Explore research topics and scientific literature.",
            "Research World",
        ),
    ]

    cols = st.columns(3)

    for index, item in enumerate(destinations):

        title, description, target = item

        with cols[index % 3]:

            st.markdown(
                html_card(
                    title,
                    (
                        f"<p>{safe_text(description)}</p>"
                        f"<span class='nl-small'>"
                        f"NEUROLENS exploration"
                        f"</span>"
                    ),
                ),
                unsafe_allow_html=True,
            )

            if st.button(
                f"Enter → {title}",
                key=f"world_destination_{index}",
                use_container_width=True,
            ):
                navigate(target)

    st.divider()

    st.markdown("### 🤖 Ayna's guidance")

    st.info(
        "The NeuroWorld interface is designed as an educational "
        "environment. Simulated signals, cognitive tasks and AI "
        "interpretations are not clinical measurements."
    )


# ============================================================
# COGNITIVE LAB
# ============================================================

elif st.session_state.page == "Cognitive Lab":

    page_header(
        "🔬 Cognitive Neuroscience Lab",
        "Run a simulated cognitive experiment and examine the result."
    )

    if LAB_VIDEO:
        st.video(LAB_VIDEO)

    left, right = st.columns([1, 1.35])

    with left:

        st.markdown("### 1️⃣ Choose your character")

        character_names = list(
            LAB_CHARACTERS.keys()
        )

        current_character = (
            st.session_state.lab_character
        )

        character = st.selectbox(
            "Lab role",
            character_names,
            index=character_names.index(
                current_character
            ),
            key="lab_character_select",
        )

        st.session_state.lab_character = character

        character_data = LAB_CHARACTERS[
            character
        ]

        st.markdown(
            html_card(
                character_data["emoji"]
                + " "
                + character,
                character_data["description"],
            ),
            unsafe_allow_html=True,
        )

        st.markdown("### 2️⃣ Choose equipment")

        equipment_names = list(
            LAB_EQUIPMENT.keys()
        )

        equipment = st.selectbox(
            "Equipment",
            equipment_names,
            index=equipment_names.index(
                st.session_state.lab_equipment
            ),
            key="lab_equipment_select",
        )

        st.session_state.lab_equipment = equipment

        st.info(
            LAB_EQUIPMENT[equipment]
        )

        st.markdown("### 3️⃣ Choose experiment")

        experiment = st.selectbox(
            "Experiment",
            LAB_EXPERIMENTS,
            index=LAB_EXPERIMENTS.index(
                st.session_state.lab_experiment
            ),
            key="lab_experiment_select",
        )

        st.session_state.lab_experiment = experiment

        st.markdown(
            f"""
            <div class="nl-card">
                <div class="nl-label">
                    Current experiment
                </div>
                <h3>{safe_text(experiment)}</h3>
                <p>
                    Character:
                    {safe_text(character)}
                </p>
                <p>
                    Equipment:
                    {safe_text(equipment)}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "⚙️ Apply Lab Setup",
            key="apply_lab_setup",
            use_container_width=True,
            type="primary",
        ):

            st.session_state.lab_phase = "ready"

            st.session_state.lab_result = None

            st.success(
                "Lab setup applied. The experiment is ready."
            )

    with right:

        st.markdown("### 🧪 Experiment Chamber")

        st.markdown(
            """
            <div class="nl-stage">
                <div>
                    <div class="nl-orb"></div>
                    <div style="
                        text-align:center;
                        color:#b8d7ee;
                    ">
                        NEUROLENS SIMULATION CORE
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Conceptual laboratory simulation — "
            "not real EEG, fMRI or physiological measurement."
        )

        if st.session_state.lab_phase != "ready":

            st.warning(
                "Apply the lab setup first."
            )

        else:

            st.markdown(
                "### ▶️ Start experiment"
            )

            if st.button(
                "🚀 Start Live Experiment",
                key="start_lab_experiment",
                use_container_width=True,
                type="primary",
            ):

                st.session_state.lab_phase = "running"

                st.session_state.lab_result = None

                st.rerun()

        if st.session_state.lab_phase == "running":

            st.divider()

            st.markdown(
                f"### 🧠 {safe_text(experiment)}"
            )

            # ------------------------------------------------
            # ATTENTION
            # ------------------------------------------------

            if experiment == "Attention":

                st.write(
                    "Find the target letter X."
                )

                options = [
                    "A B C D",
                    "A B X D",
                    "A C D E",
                    "A B C E",
                ]

                selected = st.radio(
                    "Which sequence contains X?",
                    options,
                    key="lab_attention_answer",
                )

                if st.button(
                    "Submit Attention Response",
                    key="submit_lab_attention",
                    use_container_width=True,
                ):

                    correct = (
                        selected == "A B X D"
                    )

                    score = 100 if correct else 0

                    st.session_state.lab_result = {
                        "score": score,
                        "accuracy": score,
                        "observation": (
                            "Target detection was successful."
                            if correct
                            else
                            "The target was missed in this trial."
                        ),
                    }

                    st.session_state.lab_phase = "result"

            # ------------------------------------------------
            # MEMORY
            # ------------------------------------------------

            elif experiment == "Memory":

                st.write(
                    "Memorize the sequence before entering it."
                )

                memory_sequence = (
                    "7 2 9 4 1 8"
                )

                st.markdown(
                    f"""
                    <div class="nl-card"
                         style="text-align:center;">
                        <h2>
                            {memory_sequence}
                        </h2>
                        <p>
                            Try to remember it.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                memory_answer = st.text_input(
                    "Enter the sequence",
                    key="lab_memory_answer",
                )

                if st.button(
                    "Submit Memory Response",
                    key="submit_lab_memory",
                    use_container_width=True,
                ):

                    normalized = (
                        memory_answer
                        .replace(" ", "")
                        .strip()
                    )

                    correct = (
                        normalized == "729418"
                    )

                    score = 100 if correct else 0

                    st.session_state.lab_result = {
                        "score": score,
                        "accuracy": score,
                        "observation": (
                            "The sequence was recalled correctly."
                            if correct
                            else
                            "The sequence was not recalled completely."
                        ),
                    }

                    st.session_state.lab_phase = "result"

            # ------------------------------------------------
            # DECISION & REWARD
            # ------------------------------------------------

            elif experiment == "Decision & Reward":

                st.write(
                    "Choose between an immediate reward "
                    "and a delayed larger reward."
                )

                decision = st.radio(
                    "Your choice",
                    [
                        "PKR 1,000 today",
                        "PKR 1,500 after 30 days",
                    ],
                    key="lab_decision_answer",
                )

                if st.button(
                    "Submit Decision",
                    key="submit_lab_decision",
                    use_container_width=True,
                ):

                    st.session_state.lab_result = {
                        "score": 100,
                        "accuracy": 100,
                        "observation": (
                            "Choice recorded. "
                            "This task illustrates delay discounting "
                            "and reward preference; it does not "
                            "diagnose personality or decision ability."
                        ),
                        "choice": decision,
                    }

                    st.session_state.lab_phase = "result"

            # ------------------------------------------------
            # STROOP
            # ------------------------------------------------

            elif experiment == "Stroop-Cognitive Control":

                st.write(
                    "Select the INK COLOR, not the written word."
                )

                stroop_trials = [
                    ("RED", "BLUE"),
                    ("GREEN", "RED"),
                    ("BLUE", "GREEN"),
                    ("YELLOW", "BLUE"),
                ]

                trial_index = (
                    st.session_state.get(
                        "stroop_trial_index",
                        0,
                    )
                    % len(stroop_trials)
                )

                word, ink_color = (
                    stroop_trials[trial_index]
                )

                st.markdown(
                    f"""
                    <div class="nl-card"
                         style="text-align:center;">
                        <div class="nl-label">
                            Word stimulus
                        </div>
                        <h1>{safe_text(word)}</h1>
                        <p>
                            Ink color:
                            <strong>
                                {safe_text(ink_color)}
                            </strong>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                answer = st.selectbox(
                    "What was the ink color?",
                    [
                        "RED",
                        "GREEN",
                        "BLUE",
                        "YELLOW",
                    ],
                    key="lab_stroop_answer",
                )

                if st.button(
                    "Submit Stroop Response",
                    key="submit_lab_stroop",
                    use_container_width=True,
                ):

                    correct = (
                        answer == ink_color
                    )

                    score = 100 if correct else 0

                    st.session_state.lab_result = {
                        "score": score,
                        "accuracy": score,
                        "observation": (
                            "The response followed the ink-color rule."
                            if correct
                            else
                            "The response followed the wrong feature "
                            "for this trial."
                        ),
                    }

                    st.session_state.lab_phase = "result"

            # ------------------------------------------------
            # PATTERN
            # ------------------------------------------------

            elif experiment == "Pattern Recognition":

                st.write(
                    "Identify the next item in the sequence."
                )

                st.markdown(
                    """
                    <div class="nl-card"
                         style="text-align:center;">
                        <h2>
                            2 → 4 → 8 → 16 → 32 → ?
                        </h2>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                pattern_answer = st.number_input(
                    "Next number",
                    min_value=0,
                    max_value=1000,
                    value=64,
                    step=1,
                    key="lab_pattern_answer",
                )

                if st.button(
                    "Submit Pattern Response",
                    key="submit_lab_pattern",
                    use_container_width=True,
                ):

                    correct = (
                        pattern_answer == 64
                    )

                    score = 100 if correct else 0

                    st.session_state.lab_result = {
                        "score": score,
                        "accuracy": score,
                        "observation": (
                            "The doubling rule was identified."
                            if correct
                            else
                            "The expected doubling pattern "
                            "was not selected."
                        ),
                    }

                    st.session_state.lab_phase = "result"

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        if (
            st.session_state.lab_phase
            == "result"
            and st.session_state.lab_result
        ):

            result = (
                st.session_state.lab_result
            )

            st.divider()

            st.markdown(
                "### 📊 Experiment Result"
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Score",
                    f"{result['score']}%",
                )

            with c2:
                st.metric(
                    "Accuracy",
                    f"{result['accuracy']}%",
                )

            with c3:
                st.metric(
                    "Trials",
                    1,
                )

            st.success(
                result["observation"]
            )

            st.markdown(
                "### 📡 Simulated signal"
            )

            signal = [
                random.uniform(
                    -1,
                    1,
                )
                for _ in range(80)
            ]

            if go:

                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        y=signal,
                        mode="lines",
                        name="Simulated signal",
                    )
                )

                fig.update_layout(
                    height=260,
                    margin=dict(
                        l=20,
                        r=20,
                        t=20,
                        b=20,
                    ),
                    xaxis_title="Sample",
                    yaxis_title="Amplitude",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            else:

                st.line_chart(
                    signal
                )

            st.caption(
                "Illustrative simulated signal only. "
                "This is not a real neural recording."
            )

            # Save result only once.
            if not st.session_state.get(
                "lab_result_saved",
                False,
            ):

                st.session_state.progress[
                    "experiments"
                ] += 1

                st.session_state.experiment_history.append(
                    {
                        "experiment": experiment,
                        "character": character,
                        "equipment": equipment,
                        "score": result["score"],
                        "time": time.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    }
                )

                st.session_state.lab_result_saved = True

                save_supabase(
                    "lab_results",
                    {
                        "experiment_name": experiment,
                        "score": result["score"],
                    },
                )

            st.markdown(
                "### 🤖 Ayna's observation"
            )

            if st.button(
                "💡 Ask Ayna to explain this result",
                key="ask_lab_result",
                use_container_width=True,
            ):

                result_prompt = f"""
Explain this educational cognitive experiment
result in simple scientific language.

Experiment:
{experiment}

Score:
{result['score']}%

Observation:
{result['observation']}

Explain what cognitive process the task was designed
to illustrate. Do not diagnose the user and do not
claim the score directly measures brain activity.
"""

                answer, _ = ask_ai(
                    result_prompt,
                    max_tokens=350,
                )

                st.write(answer)

                speak_button(
                    answer,
                    "lab_result_voice",
                )

            st.divider()

            if st.button(
                "🔄 Run Another Lab Trial",
                key="restart_lab",
                use_container_width=True,
            ):

                st.session_state.lab_phase = "ready"
                st.session_state.lab_result = None
                st.session_state.lab_result_saved = False
                st.rerun()


# ============================================================
# EXPLORE BRAIN / BRAIN JOURNEY
# ============================================================

elif st.session_state.page == "Explore Brain":

    page_header(
        "🧠 Explore Brain",
        "Take a visual journey from neurons and synapses to distributed brain systems."
    )

    if BRAIN_ANIMATION:
        st.video(BRAIN_ANIMATION)

    concept_count = len(
        BRAIN_CONCEPTS
    )

    if "journey_index" not in st.session_state:
        st.session_state.journey_index = 0

    index = max(
        0,
        min(
            st.session_state.journey_index,
            concept_count - 1,
        ),
    )

    concept = BRAIN_CONCEPTS[index]

    st.markdown(
        f"""
        <div class="nl-card">
            <div class="nl-label">
                Brain Journey • Stage {index + 1} of {concept_count}
            </div>
            <h2>
                {safe_text(concept["emoji"])}
                {safe_text(concept["name"])}
            </h2>
            <p>
                {safe_text(concept["description"])}
            </p>
            <p class="nl-small">
                Focus:
                {safe_text(concept["focus"])}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Find the concept-specific visual.
    concept_image = find_asset(
        *concept["image"]
    )

    concept_video = None

    for name in concept["image"]:

        if name.lower().endswith(
            (
                ".mp4",
                ".webm",
                ".mov",
            )
        ):

            concept_video = asset_path(
                name
            )

            if concept_video:
                break

    if concept_video:

        st.video(
            concept_video
        )

    elif concept_image:

        st.image(
            concept_image,
            use_container_width=True,
        )

    else:

        st.markdown(
            f"""
            <div class="nl-stage">
                <div style="
                    text-align:center;
                    font-size:5rem;
                ">
                    {safe_text(concept["emoji"])}
                    <div style="
                        font-size:1rem;
                        color:#a8c6dc;
                        margin-top:10px;
                    ">
                        Concept visual not uploaded yet
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        "The visual above is an educational representation. "
        "Brain functions are distributed and context-dependent; "
        "a single region should not be treated as a complete explanation "
        "of a complex behaviour."
    )

    st.markdown(
        "### 🧭 Journey controls"
    )

    b1, b2, b3 = st.columns(3)

    with b1:

        if st.button(
            "⬅️ Previous",
            key="journey_previous",
            use_container_width=True,
            disabled=index == 0,
        ):

            st.session_state.journey_index = (
                index - 1
            )

            st.rerun()

    with b2:

        if st.button(
            "🔄 Restart Journey",
            key="journey_restart",
            use_container_width=True,
        ):

            st.session_state.journey_index = 0
            st.rerun()

    with b3:

        if st.button(
            "Next ➡️",
            key="journey_next",
            use_container_width=True,
            disabled=index == concept_count - 1,
        ):

            st.session_state.journey_index = (
                index + 1
            )

            st.rerun()

    st.progress(
        (index + 1) / concept_count
    )

    st.markdown(
        "### 🔬 What should you notice?"
    )

    observation, _ = ask_ai(
        f"""
Give one short educational observation about
{concept['name']} for a cognitive neuroscience
learner. Avoid diagnosis and avoid saying that
this region alone determines behaviour.
""",
        max_tokens=180,
    )
    st.write(
        observation
    )
    speak_button(
        observation,
        "journey_observation_voice",
    )
elif st.session_state.page == "Brain Puzzle":
    page_header(
        "Brain Puzzle",
        "Reconstruct the brain image and challenge your visual-spatial processing."
    )

    if brain_image is None:
        st.warning("brain.png not found. Please place brain.png in the main app folder.")
    else:
        # -----------------------------
        # PUZZLE SETTINGS
        # -----------------------------
        puzzle_size = st.selectbox(
            "Puzzle difficulty",
            [3, 4, 5],
            index=0,
            format_func=lambda x: f"{x} × {x}"
        )

        total_tiles = puzzle_size * puzzle_size

        if (
            st.session_state.get("puzzle_size") != puzzle_size
            or "puzzle_tiles" not in st.session_state
            or len(st.session_state.puzzle_tiles) != total_tiles
        ):
            st.session_state.puzzle_size = puzzle_size
            st.session_state.puzzle_tiles = list(range(total_tiles))
            st.session_state.puzzle_target = list(range(total_tiles))
            st.session_state.puzzle_moves = 0
            st.session_state.puzzle_started = False
            st.session_state.puzzle_completed = False
            st.session_state.puzzle_start_time = None
            st.session_state.puzzle_round = 1

        st.markdown(
            """
            <div class="nl-card">
                <b>How to play</b><br>
                Tap one tile and then tap another tile to swap them.
                Reconstruct the complete brain image.
                </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Round", st.session_state.puzzle_round)

        with col2:
            st.metric("Moves", st.session_state.puzzle_moves)

        with col3:
            if st.session_state.puzzle_completed:
                elapsed = (
                    time.perf_counter() - st.session_state.puzzle_start_time
                    if st.session_state.puzzle_start_time
                    else 0
                )
                st.metric("Time", f"{elapsed:.1f}s")
            else:
                st.metric("Time", "Running" if st.session_state.puzzle_started else "Ready")

        with col4:
            score_preview = max(
                0,
                1000
                - (st.session_state.puzzle_moves * 20)
            )
            st.metric("Score", score_preview)

        # -----------------------------
        # IMAGE PREPARATION
        # -----------------------------
        puzzle_img = brain_image.convert("RGB")

        width, height = puzzle_img.size
        side = min(width, height)

        left = (width - side) // 2
        top = (height - side) // 2

        puzzle_img = puzzle_img.crop(
            (left, top, left + side, top + side)
        )

        tile_w = side // puzzle_size

        tiles = []

        for row in range(puzzle_size):
            for col in range(puzzle_size):
                x1 = col * tile_w
                y1 = row * tile_w
                x2 = x1 + tile_w
                y2 = y1 + tile_w

                tile = puzzle_img.crop((x1, y1, x2, y2))
                tiles.append(tile)

        # -----------------------------
        # START / RESET
        # -----------------------------
        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("Start Puzzle", use_container_width=True):
                st.session_state.puzzle_started = True
                st.session_state.puzzle_completed = False
                st.session_state.puzzle_moves = 0
                st.session_state.puzzle_start_time = time.perf_counter()

                shuffled = list(range(total_tiles))

                # Make sure puzzle is not accidentally already solved.
                while shuffled == list(range(total_tiles)):
                    random.shuffle(shuffled)

                st.session_state.puzzle_tiles = shuffled
                st.rerun()

        with c2:
            if st.button("Reset Puzzle", use_container_width=True):
                st.session_state.puzzle_tiles = list(range(total_tiles))
                st.session_state.puzzle_moves = 0
                st.session_state.puzzle_started = False
                st.session_state.puzzle_completed = False
                st.session_state.puzzle_start_time = None
                st.rerun()

        with c3:
            if st.button("New Round", use_container_width=True):
                st.session_state.puzzle_round += 1

                shuffled = list(range(total_tiles))
                while shuffled == list(range(total_tiles)):
                    random.shuffle(shuffled)

                st.session_state.puzzle_tiles = shuffled
                st.session_state.puzzle_moves = 0
                st.session_state.puzzle_started = True
                st.session_state.puzzle_completed = False
                st.session_state.puzzle_start_time = time.perf_counter()

                st.rerun()

        # -----------------------------
        # TILE SELECTION
        # -----------------------------
        if "puzzle_selected" not in st.session_state:
            st.session_state.puzzle_selected = None

        selected = st.session_state.puzzle_selected

        st.markdown(
            "<div style='height:10px'></div>",
            unsafe_allow_html=True
        )

        # -----------------------------
        # PUZZLE GRID
        # -----------------------------
        for row in range(puzzle_size):

            cols = st.columns(puzzle_size)

            for col in range(puzzle_size):

                display_index = row * puzzle_size + col
                tile_index = st.session_state.puzzle_tiles[display_index]

                with cols[col]:

                    tile_buffer = BytesIO()
                    tiles[tile_index].save(tile_buffer, format="PNG")

                    st.image(
                        tile_buffer.getvalue(),
                        use_container_width=True
                    )

                    button_label = f"Tile {display_index + 1}"

                    if selected == display_index:
                        button_label = "✓ Selected"

                    if st.button(
                        button_label,
                        key=f"puzzle_tile_{puzzle_size}_{display_index}",
                        use_container_width=True
                    ):

                        if not st.session_state.puzzle_started:
                            st.info("Press Start Puzzle first.")
                        elif st.session_state.puzzle_completed:
                            st.info("Puzzle completed. Start a new round.")
                        else:

                            if st.session_state.puzzle_selected is None:

                                st.session_state.puzzle_selected = display_index
                                st.rerun()

                            else:

                                first = st.session_state.puzzle_selected
                                second = display_index

                                if first != second:

                                    puzzle_list = st.session_state.puzzle_tiles

                                    puzzle_list[first], puzzle_list[second] = (
                                        puzzle_list[second],
                                        puzzle_list[first]
                                    )

                                    st.session_state.puzzle_moves += 1

                                st.session_state.puzzle_selected = None

                                # Check completion
                                if (
                                    st.session_state.puzzle_tiles
                                    == st.session_state.puzzle_target
                                ):
                                    st.session_state.puzzle_completed = True

                                    elapsed = (
                                        time.perf_counter()
                                        - st.session_state.puzzle_start_time
                                        if st.session_state.puzzle_start_time
                                        else 0
                                    )

                                    final_score = max(
                                        100,
                                        int(
                                            1200
                                            - st.session_state.puzzle_moves * 20
                                            - elapsed * 3
                                        )
                                    )

                                    st.session_state.puzzle_last_score = final_score

                                    save_supabase(
                                        "brain_puzzle_results",
                                        {
                                            "moves": int(
                                                st.session_state.puzzle_moves
                                            ),
                                            "score": int(final_score),
                                            "grid_size": int(puzzle_size),
                                            "duration_seconds": float(elapsed)
                                        }
                                    )

                                st.rerun()

        # -----------------------------
        # COMPLETION
        # -----------------------------
        if st.session_state.puzzle_completed:

            final_score = st.session_state.get(
                "puzzle_last_score",
                100
            )

            st.success("🎉 Puzzle completed!")

            st.markdown(
                f"""
                <div class="nl-card">
                    <h3>🧠 Brain Puzzle Complete</h3>
                    <p><b>Round:</b> {st.session_state.puzzle_round}</p>
                    <p><b>Moves:</b> {st.session_state.puzzle_moves}</p>
                    <p><b>Score:</b> {final_score}</p>
                    <p>Your visual-spatial challenge has been completed.</p>
                    <small>
                    This is a cognitive exercise and does not diagnose
                    neurological function.
                    </small>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Next Round",
                use_container_width=True
            ):
                st.session_state.puzzle_round += 1

                shuffled = list(range(total_tiles))

                while shuffled == list(range(total_tiles)):
                    random.shuffle(shuffled)

                st.session_state.puzzle_tiles = shuffled
                st.session_state.puzzle_moves = 0
                st.session_state.puzzle_started = True
                st.session_state.puzzle_completed = False
                st.session_state.puzzle_start_time = time.perf_counter()
                st.session_state.puzzle_selected = None

                st.rerun()


# ============================================================
# BRAIN CHALLENGES
# ============================================================

elif st.session_state.page == "Brain Challenges":

    page_header(
        "Brain Challenges",
        "Short cognitive exercises designed for attention, memory, decision-making and pattern recognition."
    )

    challenge_type = st.selectbox(
        "Choose a challenge",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
            "Quick Reaction"
        ]
    )

    # --------------------------------------------------------
    # WORKING MEMORY
    # --------------------------------------------------------
    if challenge_type == "Working Memory":

        st.subheader("🧠 Working Memory")

        if "memory_challenge_sequence" not in st.session_state:
            st.session_state.memory_challenge_sequence = (
                "7 2 9 4 1 8"
            )

        sequence = st.session_state.memory_challenge_sequence

        if not st.session_state.get("memory_show", False):

            st.info(
                "Memorize the sequence, then press Hide Sequence."
            )

            st.markdown(
                f"""
                <div class="nl-card" style="text-align:center;">
                    <div style="font-size:38px;font-weight:700;">
                    {sequence}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Hide Sequence",
                use_container_width=True
            ):
                st.session_state.memory_show = True
                st.rerun()

        else:

            st.write("Enter the sequence from memory:")

            answer = st.text_input(
                "Your answer",
                key="memory_answer"
            )

            if st.button(
                "Check Memory",
                use_container_width=True
            ):

                clean_answer = answer.replace(
                    " ",
                    ""
                ).strip()

                correct_answer = sequence.replace(
                    " ",
                    ""
                )

                if clean_answer == correct_answer:

                    st.success(
                        "Correct! Excellent working-memory performance."
                    )

                    memory_score = 100

                else:

                    st.error(
                        f"Not quite. The target sequence was {sequence}."
                    )

                    memory_score = 0

                save_supabase(
                    "exercise_results",
                    {
                        "exercise_name": "Working Memory",
                        "score": memory_score
                    }
                )

                st.session_state.memory_show = False

                st.session_state.memory_challenge_sequence = (
                    " ".join(
                        random.sample(
                            list("0123456789"),
                            6
                        )
                    )
                )


    # --------------------------------------------------------
    # ATTENTION
    # --------------------------------------------------------
    elif challenge_type == "Attention":

        st.subheader("🎯 Attention Challenge")

        st.write(
            "Find the letter X as quickly as possible."
        )

        if "attention_grid" not in st.session_state:

            letters = []

            for _ in range(24):
                letters.append(
                    random.choice(
                        ["O", "0", "Q", "C"]
                    )
                )

            target_position = random.randint(
                0,
                23
            )

            letters[target_position] = "X"

            st.session_state.attention_grid = letters
            st.session_state.attention_target = target_position

        grid = st.session_state.attention_grid

        cols = st.columns(6)

        for i, value in enumerate(grid):

            with cols[i % 6]:

                if st.button(
                    value,
                    key=f"attention_{i}",
                    use_container_width=True
                ):

                    if value == "X":

                        st.success(
                            "Correct! You detected the target."
                        )

                        score = 100

                    else:

                        st.error(
                            "That was a distractor."
                        )

                        score = 0

                    save_supabase(
                        "exercise_results",
                        {
                            "exercise_name": "Attention",
                            "score": score
                        }
                    )

                    # Create new grid
                    letters = [
                        random.choice(
                            ["O", "0", "Q", "C"]
                        )
                        for _ in range(24)
                    ]

                    target_position = random.randint(
                        0,
                        23
                    )

                    letters[target_position] = "X"

                    st.session_state.attention_grid = letters
                    st.session_state.attention_target = target_position

                    st.rerun()


    # --------------------------------------------------------
    # PATTERN
    # --------------------------------------------------------
    elif challenge_type == "Pattern Recognition":

        st.subheader("🔢 Pattern Recognition")

        st.markdown(
            """
            <div class="nl-card">
                <h3>2 → 4 → 8 → 16 → 32 → ?</h3>
                <p>Identify the next value.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        answer = st.text_input(
            "Your answer",
            key="pattern_answer"
        )

        if st.button(
            "Check Pattern",
            use_container_width=True
        ):

            if answer.strip() == "64":

                st.success(
                    "Correct! The sequence doubles each time."
                )

                score = 100

            else:

                st.error(
                    "Try again. Look at how each value changes."
                )

                score = 0

            save_supabase(
                "exercise_results",
                {
                    "exercise_name": "Pattern Recognition",
                    "score": score
                }
            )


    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------
    elif challenge_type == "Decision Challenge":

        st.subheader("💰 Decision & Reward")

        st.markdown(
            """
            <div class="nl-card">
                <h3>Choose one:</h3>
                <p>💵 <b>PKR 1,000 today</b></p>
                <p>⏳ <b>PKR 1,500 after 30 days</b></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        decision = st.radio(
            "Your choice",
            [
                "PKR 1,000 today",
                "PKR 1,500 after 30 days"
            ]
        )

        if st.button(
            "Submit Decision",
            use_container_width=True
        ):

            st.success(
                "Decision recorded."
            )

            st.info(
                "This challenge explores delay discounting and reward preference. "
                "A single choice does not diagnose personality or financial behaviour."
            )

            save_supabase(
                "exercise_results",
                {
                    "exercise_name": "Decision Challenge",
                    "score": 100,
                    "choice": decision
                }
            )


    # --------------------------------------------------------
    # QUICK REACTION
    # --------------------------------------------------------
    elif challenge_type == "Quick Reaction":

        st.subheader("⚡ Quick Reaction")

        st.write(
            "Press Start. When the signal appears, press React."
        )

        if "reaction_waiting" not in st.session_state:
            st.session_state.reaction_waiting = False

        if "reaction_signal" not in st.session_state:
            st.session_state.reaction_signal = False

        if "reaction_start" not in st.session_state:
            st.session_state.reaction_start = None

        if not st.session_state.reaction_waiting:

            if st.button(
                "Start Reaction Test",
                use_container_width=True
            ):

                delay = random.uniform(
                    1.0,
                    3.0
                )

                st.session_state.reaction_waiting = True
                st.session_state.reaction_signal = False
                st.session_state.reaction_delay = delay
                st.session_state.reaction_start = time.perf_counter()

                st.rerun()

        else:

            elapsed = (
                time.perf_counter()
                - st.session_state.reaction_start
            )

            delay = st.session_state.reaction_delay

            if not st.session_state.reaction_signal:

                if elapsed >= delay:

                    st.session_state.reaction_signal = True
                    st.session_state.reaction_signal_time = (
                        time.perf_counter()
                    )

                    st.rerun()

                else:

                    st.warning(
                        "Wait for the signal..."
                    )

                    if st.button(
                        "I Reacted Early",
                        use_container_width=True
                    ):

                        st.error(
                            "Too early! Wait for the signal."
                        )

                        st.session_state.reaction_waiting = False
                        st.session_state.reaction_signal = False

                        st.rerun()

                    time.sleep(0.15)
                    st.rerun()

            else:

                st.success("🟢 REACT NOW!")

                if st.button(
                    "React",
                    use_container_width=True
                ):

                    reaction_time = (
                        time.perf_counter()
                        - st.session_state.reaction_signal_time
                    )

                    reaction_ms = int(
                        reaction_time * 1000
                    )

                    score = max(
                        0,
                        min(
                            100,
                            int(
                                100
                                - reaction_ms / 5
                            )
                        )
                    )

                    st.metric(
                        "Reaction Time",
                        f"{reaction_ms} ms"
                    )

                    st.metric(
                        "Score",
                        score
                    )

                    save_supabase(
                        "exercise_results",
                        {
                            "exercise_name": "Quick Reaction",
                            "score": score,
                            "reaction_time_ms": reaction_ms
                        }
                    )

                    st.session_state.reaction_waiting = False
                    st.session_state.reaction_signal = False
                    st.session_state.reaction_start = None


# ============================================================
# AI MOOD & BEHAVIOUR
# ============================================================

elif st.session_state.page == "AI Mood & Behaviour":

    page_header(
        "AI Mood & Behaviour",
        "Use text, voice or camera input for an AI-assisted interpretation of visible cues."
    )

    st.warning(
        "Important: these are AI-assisted estimates, not mind-reading, "
        "medical diagnosis, personality diagnosis, or clinical assessment."
    )

    mode = st.radio(
        "Choose input",
        [
            "Text",
            "Voice",
            "Camera"
        ],
        horizontal=True
    )

    # --------------------------------------------------------
    # TEXT MOOD
    # --------------------------------------------------------
    if mode == "Text":

        mood_text = st.text_area(
            "Describe how you feel or what is happening",
            height=140,
            placeholder="Example: I feel distracted and tired today."
        )

        if st.button(
            "Analyze Text",
            use_container_width=True
        ):

            if not mood_text.strip():

                st.warning(
                    "Please enter some text first."
                )

            else:

                prompt = f"""
You are Ayna, an AI cognitive-neuroscience assistant.

Analyze the following user-written text.

Return:
1. One suitable emoji.
2. A short description of the emotional/behavioural cue.
3. A cautious interpretation.
4. One supportive suggestion.

Do NOT diagnose.
Do NOT claim certainty about the person's internal mental state.
Do NOT claim to measure brain activity.

User text:
{safe_text(mood_text)}
"""

                answer = ask_ai(
                    prompt,
                    "I can provide a cautious AI-assisted interpretation."
                )

                st.markdown(
                    answer
                )

                save_supabase(
                    "voice_mood_results",
                    {
                        "input_type": "text",
                        "interpretation": answer
                    }
                )


    # --------------------------------------------------------
    # VOICE
    # --------------------------------------------------------
    elif mode == "Voice":

        st.write(
            "Record a short voice sample."
        )

        audio = st.audio_input(
            "Record voice"
        )

        if audio is not None:

            st.audio(
                audio
            )

            if st.button(
                "Analyze Voice",
                use_container_width=True
            ):

                audio_bytes = audio.getvalue()

                answer = ask_ai_audio(
                    audio_bytes,
                    """
Analyze this voice recording conservatively.

Return:
- one emoji representing the apparent communication vibe
- possible observable vocal cues
- a cautious interpretation
- one supportive suggestion

Do not claim to know the person's true emotions.
Do not diagnose mental health conditions.
Do not identify the person.
Do not claim to measure brain activity.
"""
                )

                st.markdown(
                    answer
                )

                save_supabase(
                    "voice_mood_results",
                    {
                        "input_type": "voice",
                        "interpretation": answer
                    }
                )


    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------
    elif mode == "Camera":

        st.write(
            "Capture an image for a non-identifying visual expression interpretation."
        )

        camera_image = st.camera_input(
            "Take a photo"
        )

        if camera_image is not None:

            st.image(
                camera_image,
                caption="Captured image"
            )

            if st.button(
                "Analyze Visible Expression",
                use_container_width=True
            ):

                image_bytes = camera_image.getvalue()

                answer = ask_ai_audio(
                    image_bytes,
                    """
Analyze the uploaded image for visible facial-expression cues only.

Return:
- one emoji representing the apparent visible expression
- observable facial-expression cues
- a cautious interpretation

Rules:
- Do not identify the person.
- Do not infer identity.
- Do not infer private attributes.
- Do not diagnose mental health.
- Do not claim to know the person's true feelings.
- Do not claim to read thoughts.
- Do not claim to measure brain activity.
- Make it clear that this is only an AI-assisted visual interpretation.
"""
                )

                st.markdown(
                    answer
                )

                save_supabase(
                    "voice_mood_results",
                    {
                        "input_type": "camera",
                        "interpretation": answer
                    }
                )

    st.markdown(
        """
        <div class="nl-card">
            <b>Scientific limitation</b><br>
            Facial expressions and vocal characteristics can provide observable
            behavioural cues, but they cannot reliably reveal a person's complete
            internal emotional or cognitive state.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# RESEARCH WORLD
# ============================================================

elif st.session_state.page == "Research World":

    page_header(
        "Research World",
        "Explore biomedical literature and turn papers into structured research notes."
    )

    topic = st.selectbox(
        "Research topic",
        RESEARCH_TOPICS
    )

    custom_query = st.text_input(
        "Or enter your own search query",
        placeholder="Example: cognitive control addiction consciousness"
    )

    query = custom_query.strip() or topic

    col1, col2 = st.columns(2)

    with col1:

        max_results = st.slider(
            "Number of papers",
            3,
            10,
            5
        )

    with col2:

        if st.button(
            "Search Europe PMC",
            use_container_width=True
        ):

            st.session_state.research_query = query

            try:

                params = {
                    "query": query,
                    "format": "json",
                    "pageSize": max_results,
                    "resultType": "core"
                }

                response = requests.get(
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                    params=params,
                    timeout=20
                )

                response.raise_for_status()

                data = response.json()

                st.session_state.research_results = (
                    data.get("resultList", {}).get("result", [])
                )

            except Exception as e:

                st.error(
                    f"Research search failed: {e}"
                )

    results = st.session_state.get(
        "research_results",
        []
    )

    if results:

        st.success(
            f"Found {len(results)} papers."
        )

        for i, paper in enumerate(results):

            title = paper.get(
                "title",
                "Untitled paper"
            )

            authors = paper.get(
                "authorString",
                "Authors not listed"
            )

            journal = paper.get(
                "journalTitle",
                "Journal not listed"
            )

            year = paper.get(
                "pubYear",
                ""
            )

            abstract = paper.get(
                "abstractText",
                ""
            )

            pmid = paper.get(
                "pmid",
                ""
            )

            doi = paper.get(
                "doi",
                ""
            )

            with st.expander(
                f"{i + 1}. {title}"
            ):

                st.write(
                    f"**Authors:** {authors}"
                )

                st.write(
                    f"**Journal:** {journal}"
                )

                st.write(
                    f"**Year:** {year}"
                )

                if abstract:

                    st.write(
                        abstract[:3000]
                    )

                if pmid:

                    st.markdown(
                        f"[View on PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
                    )

                if doi:

                    st.markdown(
                        f"[DOI](https://doi.org/{doi})"
                    )

                # AI summary
                if st.button(
                    "AI Summary",
                    key=f"research_ai_{i}"
                ):

                    summary_prompt = f"""
You are Ayna, a cognitive neuroscience research assistant.

Summarize this scientific paper for a researcher.

Include:
- research question
- methodology
- major findings
- limitations
- possible research gap

Do not invent information.

Title:
{safe_text(title)}

Abstract:
{safe_text(abstract)}
"""

                    summary = ask_ai(
                        summary_prompt,
                        "No AI summary available."
                    )

                    st.markdown(
                        summary
                    )

                    st.session_state[
                        f"research_summary_{i}"
                    ] = summary

                if st.button(
                    "Save Research Note",
                    key=f"research_save_{i}"
                ):

                    summary_text = st.session_state.get(
                        f"research_summary_{i}",
                        ""
                    )

                    save_supabase(
                        "research_notes",
                        {
                            "title": title,
                            "notes": (
                                summary_text
                                if summary_text
                                else abstract[:4000]
                            ),
                            "source_url": (
                                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                                if pmid
                                else ""
                            )
                        }
                    )

                    st.success(
                        "Research note saved."
                    )

    else:

        st.info(
            "Choose a topic and search Europe PMC to begin."
        )

    st.markdown(
        """
        <div class="nl-card">
            <b>Research workflow</b><br>
            Literature search → paper screening → AI-assisted summary →
            limitations → research gap → research note.
            <br><br>
            AI summaries should always be checked against the original paper.
        </div>
        """,
        unsafe_allow_html=True
    )
# ============================================================
# PRIVATE ASK AYNA
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    page_header(
        "Private Ask Ayna",
        "A private session for personal conversations."
    )

    st.info(
        "Your private conversation is protected by a local session PIN. "
        "Do not use this feature for emergencies or clinical diagnosis."
    )

    # --------------------------------------------------------
    # PRIVATE PIN HELPERS
    # --------------------------------------------------------

    def make_pin_hash(pin, salt=None):
        if salt is None:
            salt = secrets.token_bytes(16)

        derived = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            120000
        )

        return (
            base64.b64encode(salt).decode("utf-8"),
            base64.b64encode(derived).decode("utf-8")
        )


    def verify_pin(pin, salt_b64, stored_hash):

        try:
            salt = base64.b64decode(
                salt_b64.encode("utf-8")
            )

            derived = hashlib.pbkdf2_hmac(
                "sha256",
                pin.encode("utf-8"),
                salt,
                120000
            )

            calculated = base64.b64encode(
                derived
            ).decode("utf-8")

            return secrets.compare_digest(
                calculated,
                stored_hash
            )

        except Exception:
            return False


    # --------------------------------------------------------
    # CREATE PIN
    # --------------------------------------------------------

    if not st.session_state.get(
        "private_pin_configured",
        False
    ):

        st.subheader("Create Private PIN")

        new_pin = st.text_input(
            "Create a 4–6 digit PIN",
            type="password",
            max_chars=6
        )

        confirm_pin = st.text_input(
            "Confirm PIN",
            type="password",
            max_chars=6
        )

        if st.button(
            "Create Private PIN",
            use_container_width=True
        ):

            if (
                not new_pin.isdigit()
                or len(new_pin) < 4
                or len(new_pin) > 6
            ):

                st.error(
                    "PIN must contain 4–6 digits."
                )

            elif new_pin != confirm_pin:

                st.error(
                    "PINs do not match."
                )

            else:

                salt_b64, hash_b64 = make_pin_hash(
                    new_pin
                )

                st.session_state.private_pin_salt = salt_b64
                st.session_state.private_pin_hash = hash_b64
                st.session_state.private_pin_configured = True
                st.session_state.private_unlocked = True
                st.session_state.private_messages = []

                st.success(
                    "Private PIN created."
                )

                st.rerun()


    # --------------------------------------------------------
    # UNLOCK
    # --------------------------------------------------------

    elif not st.session_state.get(
        "private_unlocked",
        False
    ):

        st.subheader("🔐 Unlock Private Ask Ayna")

        pin = st.text_input(
            "Enter PIN",
            type="password",
            max_chars=6
        )

        if st.button(
            "Unlock",
            use_container_width=True
        ):

            if verify_pin(
                pin,
                st.session_state.private_pin_salt,
                st.session_state.private_pin_hash
            ):

                st.session_state.private_unlocked = True

                st.success(
                    "Private session unlocked."
                )

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )


    # --------------------------------------------------------
    # PRIVATE CHAT
    # --------------------------------------------------------

    else:

        top1, top2 = st.columns(2)

        with top1:
            st.success("🔓 Private session unlocked.")

        with top2:

            if st.button(
                "🔒 Lock Session",
                use_container_width=True
            ):

                st.session_state.private_unlocked = False
                st.rerun()


        if "private_messages" not in st.session_state:

            st.session_state.private_messages = []


        for message in st.session_state.private_messages:

            role = message.get(
                "role",
                "assistant"
            )

            content = message.get(
                "content",
                ""
            )

            with st.chat_message(role):

                st.markdown(
                    content
                )


        private_text = st.text_area(
            "Private message",
            height=120,
            placeholder="Write something privately..."
        )

        if st.button(
            "SEND",
            use_container_width=True
        ):

            if private_text.strip():

                user_text = safe_text(
                    private_text.strip()
                )

                st.session_state.private_messages.append(
                    {
                        "role": "user",
                        "content": user_text
                    }
                )

                private_prompt = f"""
You are Ayna, a supportive AI cognitive-neuroscience assistant.

This is a private conversation.

Respond with empathy and respect.
Do not diagnose.
Do not claim certainty about emotions or mental health.
Do not pretend to be a therapist.
If the user describes an emergency or immediate danger,
encourage them to contact local emergency services or a trusted person.

User:
{user_text}
"""

                response = ask_ai(
                    private_prompt,
                    "I’m here to listen. Please tell me what is on your mind."
                )

                st.session_state.private_messages.append(
                    {
                        "role": "assistant",
                        "content": response
                    }
                )

                save_supabase(
                    "private_ayna_messages",
                    {
                        "role": "user",
                        "content": user_text
                    }
                )

                st.rerun()


# ============================================================
# BEHAVIOUR DECODING
# ============================================================

elif st.session_state.page == "Behaviour Decoding":

    page_header(
        "Behaviour Decoding",
        "Request a structured one-to-one discussion about cognition, behaviour or research."
    )

    st.warning(
        "Behaviour Decoding is an educational discussion service. "
        "It is not a medical, psychiatric or emergency service."
    )

    # --------------------------------------------------------
    # PRICING
    # --------------------------------------------------------

    st.subheader("Session Options")

    pricing = {
        "20 minutes": {
            "PKR": 1000,
            "USD": 8
        },
        "30 minutes": {
            "PKR": 1500,
            "USD": 10
        },
        "45 minutes": {
            "PKR": 2000,
            "USD": 12
        },
        "Advice / Consultation": {
            "PKR": 1500,
            "USD": 10
        }
    }

    price_cols = st.columns(4)

    for i, (name, values) in enumerate(
        pricing.items()
    ):

        with price_cols[i]:

            st.markdown(
                f"""
                <div class="nl-card">
                    <h4>{name}</h4>
                    <p><b>PKR {values["PKR"]:,}</b></p>
                    <p>International: <b>${values["USD"]}</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )


    # --------------------------------------------------------
    # REQUEST FORM
    # --------------------------------------------------------

    st.subheader("Request a Session")

    client_name = st.text_input(
        "Name"
    )

    contact = st.text_input(
        "Email / Contact"
    )

    topic = st.text_area(
        "Topic / Question",
        height=120,
        placeholder="Describe the topic you want to discuss."
    )

    session_length = st.selectbox(
        "Session",
        list(pricing.keys())
    )

    payment_method = st.selectbox(
        "Payment Method",
        [
            "Easypaisa",
            "International Payment"
        ]
    )

    payment_reference = st.text_input(
        "Payment Reference / Transaction ID",
        placeholder="Enter your payment reference after payment."
    )


    # --------------------------------------------------------
    # PAYMENT INFORMATION
    # --------------------------------------------------------

    if payment_method == "Easypaisa":

        easypaisa_name = st.session_state.get(
            "easypaisa_name",
            ""
        )

        easypaisa_number = st.session_state.get(
            "easypaisa_number",
            ""
        )

        if easypaisa_number:

            st.info(
                f"Easypaisa: {easypaisa_name} — {easypaisa_number}"
            )

        else:

            st.info(
                "Easypaisa payment details will appear here "
                "after they are configured in Streamlit Secrets."
            )

    else:

        international_url = st.session_state.get(
            "international_payment_url",
            ""
        )

        if international_url:

            st.markdown(
                f"[Open International Payment Page]({international_url})"
            )

        else:

            st.info(
                "International payment link is not configured yet."
            )


    # --------------------------------------------------------
    # SUBMIT REQUEST
    # --------------------------------------------------------

    if st.button(
        "Submit Consultation Request",
        use_container_width=True
    ):

        if not client_name.strip():

            st.error(
                "Please enter your name."
            )

        elif not contact.strip():

            st.error(
                "Please enter your contact information."
            )

        elif not topic.strip():

            st.error(
                "Please describe your topic."
            )

        elif not payment_reference.strip():

            st.error(
                "Please enter your payment reference."
            )

        else:

            selected_price = pricing[
                session_length
            ]

            request_data = {
                "name": safe_text(client_name),
                "contact": safe_text(contact),
                "topic": safe_text(topic),
                "session_length": session_length,
                "payment_method": payment_method,
                "payment_reference": safe_text(
                    payment_reference
                ),
                "amount_pkr": selected_price["PKR"],
                "amount_usd": selected_price["USD"],
                "payment_status": "pending"
            }

            save_supabase(
                "consultation_requests",
                request_data
            )

            st.session_state.consultation_submitted = True

            st.success(
                "Consultation request submitted."
            )

            st.info(
                "Payment verification is required before the discussion is unlocked."
            )


    # --------------------------------------------------------
    # PAYMENT VERIFICATION
    # --------------------------------------------------------

    st.divider()

    st.subheader("Payment Verification")

    st.write(
        "Current status:"
    )

    if st.session_state.get(
        "consultation_submitted",
        False
    ):

        st.warning(
            "Pending verification"
        )

    else:

        st.info(
            "No consultation request submitted in this session."
        )

    st.markdown(
        """
        <div class="nl-card">
            <b>Payment security</b><br>
            Payment verification should be performed using an official
            payment-provider/API workflow. Do not place a private
            payment-provider secret key in frontend code.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# MY PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    page_header(
        "My Progress",
        "Track your NeuroLens learning, cognitive exercises and research activity."
    )

    # --------------------------------------------------------
    # SESSION METRICS
    # --------------------------------------------------------

    lab_count = st.session_state.get(
        "lab_completed",
        0
    )

    ai_count = st.session_state.get(
        "ai_request_count",
        0
    )

    puzzle_score = st.session_state.get(
        "puzzle_last_score",
        0
    )

    exercise_scores = st.session_state.get(
        "exercise_scores",
        []
    )

    if not isinstance(
        exercise_scores,
        list
    ):
        exercise_scores = []


    total_exercises = len(
        exercise_scores
    )

    average_score = (
        sum(exercise_scores)
        / len(exercise_scores)
        if exercise_scores
        else 0
    )


    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Lab Sessions",
            lab_count
        )

    with col2:
        st.metric(
            "Exercises",
            total_exercises
        )

    with col3:
        st.metric(
            "Average Score",
            f"{average_score:.0f}"
        )

    with col4:
        st.metric(
            "AI Requests",
            ai_count
        )


    # --------------------------------------------------------
    # PROGRESS CHART
    # --------------------------------------------------------

    if exercise_scores:

        try:

            import plotly.graph_objects as go

            chart = go.Figure()

            chart.add_trace(
                go.Scatter(
                    y=exercise_scores,
                    x=list(
                        range(
                            1,
                            len(exercise_scores) + 1
                        )
                    ),
                    mode="lines+markers",
                    name="Exercise Score"
                )
            )

            chart.update_layout(
                title="Exercise Performance",
                xaxis_title="Attempt",
                yaxis_title="Score",
                yaxis_range=[0, 100]
            )

            st.plotly_chart(
                chart,
                use_container_width=True
            )

        except Exception:

            st.write(
                exercise_scores
            )

    else:

        st.info(
            "Complete cognitive exercises to build your progress history."
        )


    # --------------------------------------------------------
    # ACHIEVEMENTS
    # --------------------------------------------------------

    st.subheader("Achievements")

    achievements = []

    if lab_count >= 1:
        achievements.append(
            "🧪 First Cognitive Lab"
        )

    if total_exercises >= 1:
        achievements.append(
            "🧠 First Brain Exercise"
        )

    if puzzle_score > 0:
        achievements.append(
            "🧩 Brain Puzzle Completed"
        )

    if ai_count >= 5:
        achievements.append(
            "🤖 AI Explorer"
        )

    if len(achievements) == 0:

        st.info(
            "Your first achievement is waiting."
        )

    else:

        for achievement in achievements:

            st.success(
                achievement
            )


    # --------------------------------------------------------
    # RESEARCH
    # --------------------------------------------------------

    research_results = st.session_state.get(
        "research_results",
        []
    )

    st.subheader("Research Activity")

    st.write(
        f"Research papers viewed in the current session: "
        f"{len(research_results)}"
    )

    st.markdown(
        """
        <div class="nl-card">
            <b>Progress note</b><br>
            NeuroLens progress is designed for learning and self-reflection.
            Exercise scores are not clinical or neurological measurements.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SECURITY & PRIVACY
# ============================================================

elif st.session_state.page == "Security & Privacy":

    page_header(
        "Security & Privacy",
        "Understand how NeuroLens handles AI, private information and user inputs."
    )

    st.subheader("🔐 API Key Protection")

    st.write(
        "Gemini and Supabase credentials should be stored in "
        "Streamlit Secrets rather than inside public source code."
    )

    st.subheader("🧹 Input Sanitization")

    st.write(
        "User-generated text is passed through basic sanitization "
        "before being inserted into AI prompts or HTML-rendered areas."
    )

    st.subheader("🤖 AI Safety")

    st.write(
        "NeuroLens uses AI-assisted interpretation and educational "
        "responses. AI output can be incorrect and should be checked."
    )

    st.subheader("🧠 No Mind Reading")

    st.write(
        "Voice and facial-expression features provide cautious interpretations "
        "of observable cues. They cannot reliably determine a person's "
        "private thoughts or complete emotional state."
    )

    st.subheader("🧪 Simulated Neuroscience")

    st.write(
        "Any EEG-like or neural-signal visualizations inside NeuroLens "
        "are simulated/conceptual unless explicitly connected to validated hardware."
    )

    st.subheader("🔑 Private PIN")

    st.write(
        "Private Ask Ayna uses a salted PBKDF2-HMAC-SHA256 PIN derivation "
        "rather than storing the raw PIN."
    )

    st.subheader("💳 Payment Security")

    st.write(
        "Payment verification should use official payment-provider APIs "
        "or a secure server-side verification workflow."
    )

    st.subheader("⚠️ Important Limitation")

    st.write(
        "NeuroLens is an educational/research-oriented prototype. "
        "It is not a substitute for a doctor, psychologist, psychiatrist, "
        "neurologist, emergency service or other qualified professional."
    )


# ============================================================
# SETTINGS
# ============================================================

elif st.session_state.page == "Settings":

    page_header(
        "Settings",
        "Configure NeuroLens for your preferred experience."
    )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = st.selectbox(
        "Interface language",
        [
            "English",
            "Roman English"
        ],
        index=0
    )

    st.session_state.interface_language = language


    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model_options = [
        "gemini-2.5-flash",
        "gemini-2.0-flash"
    ]

    current_model = st.session_state.get(
        "selected_model",
        "gemini-2.5-flash"
    )

    if current_model not in model_options:
        current_model = model_options[0]

    selected_model = st.selectbox(
        "AI Model",
        model_options,
        index=model_options.index(
            current_model
        )
    )

    st.session_state.selected_model = selected_model


    # --------------------------------------------------------
    # PAYMENT STATUS
    # --------------------------------------------------------

    st.subheader("Payment Configuration")

    easypaisa_configured = bool(
        st.session_state.get(
            "easypaisa_number",
            ""
        )
    )

    international_configured = bool(
        st.session_state.get(
            "international_payment_url",
            ""
        )
    )

    st.write(
        f"Easypaisa: "
        f"{'Configured' if easypaisa_configured else 'Not configured'}"
    )

    st.write(
        f"International payment: "
        f"{'Configured' if international_configured else 'Not configured'}"
    )


    # --------------------------------------------------------
    # USAGE
    # --------------------------------------------------------

    st.subheader("AI Usage")

    st.write(
        f"AI requests this session: "
        f"{st.session_state.get('ai_request_count', 0)}"
    )

    st.write(
        f"Session AI limit: "
        f"{AI_SESSION_LIMIT}"
    )


    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    st.subheader("Reset Session")

    st.warning(
        "This resets local NeuroLens session progress."
    )

    if st.button(
        "Reset Session Progress",
        use_container_width=True
    ):

        keep_keys = {
            "page",
            "selected_model",
            "interface_language"
        }

        for key in list(
            st.session_state.keys()
        ):

            if key not in keep_keys:

                del st.session_state[key]

        st.success(
            "Session progress reset."
        )

        st.rerun()


# ============================================================
# FINAL FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        padding:30px 10px 15px 10px;
        color:#8b96a8;
        font-size:13px;
    ">
        <b>NEUROLENS</b><br>
        Explore cognition, behavior &amp; the brain.<br>
        Created by Ayna Jaffri
    </div>
    """,
    unsafe_allow_html=True
)

