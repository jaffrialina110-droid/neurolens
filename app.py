import os
import random
import time
import hashlib
import base64
from io import BytesIO

import streamlit as st
from PIL import Image
import streamlit.components.v1 as components

# =========================================================
# OPTIONAL AI IMPORT
# =========================================================

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

# =========================================================
# OPTIONAL PLOTLY
# =========================================================

try:
    import plotly.graph_objects as plotly_go
except Exception:
    plotly_go = None

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# PATHS
# =========================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset_path(name):
    paths = [
        os.path.join(ASSETS, name),
        os.path.join(ROOT, name),
    ]

    for path in paths:
        if os.path.exists(path):
            return path

    return None


BRAIN_PATH = asset_path("brain.png")
JOURNEY_VIDEO = asset_path("brain_animation.mp4")
LAB_VIDEO = asset_path("cognitive_lab_brain.mp4")
AYNA_ROBOT = asset_path("ayna_robot.png")


def find_reboot_video():
    preferred = [
        "ayna_reboot.mp4",
        "ayna_welcome.mp4",
        "ayna_3d_reboot.mp4",
        "reboot.mp4",
        "welcome.mp4",
        "ayna.mp4",
    ]

    for name in preferred:
        path = asset_path(name)
        if path:
            return path

    search_dirs = [ROOT, ASSETS]

    for directory in search_dirs:
        if not directory or not os.path.exists(directory):
            continue

        try:
            for name in os.listdir(directory):
                if not name.lower().endswith(".mp4"):
                    continue

                low = name.lower()

                if any(
                    word in low
                    for word in ["reboot", "welcome", "ayna"]
                ):
                    return os.path.join(directory, name)

        except Exception:
            pass

    return None


AYNA_REBOOT_VIDEO = find_reboot_video()

# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 0%, #173d63 0%, transparent 30%),
        radial-gradient(circle at 90% 10%, #172c55 0%, transparent 25%),
        linear-gradient(135deg, #050b14, #0a1727 55%, #07111d);
    color: #eef6ff;
}

.block-container {
    max-width: 1450px;
    padding-top: 1rem;
}

.hero {
    padding: 28px;
    margin-bottom: 20px;
    border-radius: 24px;
    background:
        linear-gradient(135deg, rgba(20,55,88,.95), rgba(12,24,44,.95));
    border: 1px solid #355878;
    box-shadow: 0 12px 40px rgba(0,0,0,.25);
}

.hero h1 {
    margin-bottom: 4px;
}

.card {
    padding: 18px;
    margin: 10px 0;
    border-radius: 18px;
    background: rgba(13,32,53,.92);
    border: 1px solid #294963;
}

.lab-card {
    min-height: 330px;
    border-radius: 24px;
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at center, #285b88 0%, #0b1930 32%, #06101e 75%);
    border: 1px solid #36536d;
}

.neural-orb {
    position: absolute;
    width: 105px;
    height: 105px;
    border-radius: 50%;
    left: calc(50% - 52px);
    top: calc(50% - 52px);
    background:
        radial-gradient(
            circle,
            white 0%,
            #8ed1ff 20%,
            #536bff 55%,
            #342a7d 100%
        );
    box-shadow:
        0 0 25px #72c5ff,
        0 0 60px rgba(83,107,255,.8);
    animation: pulseBrain 2.2s infinite;
}

.neural-line {
    position: absolute;
    height: 2px;
    background: #75c9ff88;
    transform-origin: left;
}

.nl1 {
    left: 12%;
    top: 34%;
    width: 40%;
    transform: rotate(18deg);
}

.nl2 {
    left: 52%;
    top: 55%;
    width: 34%;
    transform: rotate(-24deg);
}

.nl3 {
    left: 26%;
    top: 72%;
    width: 43%;
    transform: rotate(-17deg);
}

@keyframes pulseBrain {
    50% {
        transform: scale(1.12);
    }
}

.stage-card {
    min-height: 230px;
    padding: 25px;
    border-radius: 22px;
    background:
        radial-gradient(circle, #173c61, #081525 70%);
    border: 1px solid #355777;
    text-align: center;
}

.neuron {
    font-size: 70px;
    animation: neuronPulse 1.7s infinite;
}

@keyframes neuronPulse {
    50% {
        transform: scale(1.08);
    }
}

.signal-track {
    height: 100px;
    border-radius: 18px;
    position: relative;
    overflow: hidden;
    background: #edf4fb;
    margin: 15px 0;
}

.signal-axon {
    position: absolute;
    top: 45px;
    left: 6%;
    right: 6%;
    height: 12px;
    border-radius: 10px;
    background: #8c6a4d;
}

.signal-pulse {
    position: absolute;
    top: 25px;
    left: 5%;
    font-size: 34px;
    animation: signalMove 2.2s linear infinite;
}

@keyframes signalMove {
    from {
        left: 5%;
    }
    to {
        left: 88%;
    }
}

.synapse {
    font-size: 42px;
    padding: 30px;
    border-radius: 18px;
    background: #08182b;
    animation: synapsePulse 1.5s infinite;
}

@keyframes synapsePulse {
    50% {
        box-shadow: 0 0 35px rgba(83,177,255,.5);
    }
}

.reboot-box {
    padding: 25px;
    border-radius: 25px;
    background:
        radial-gradient(circle at center, #193e66, #07111f 70%);
    border: 1px solid #365b7c;
    text-align: center;
}

.small-note {
    opacity: .78;
    font-size: .9rem;
}

.metric-card {
    padding: 18px;
    border-radius: 18px;
    background: #0d2035;
    border: 1px solid #294963;
    text-align: center;
}

.equipment {
    padding: 15px;
    border-radius: 16px;
    background: #0b1c30;
    border: 1px solid #294963;
    margin-bottom: 8px;
}

</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "Welcome Reboot",
    "welcome_seen": False,

    "language": "English",

    "character": "Nova",
    "equipment": "EEG Scanner",

    "journey_stage": "brain",
    "journey_region": "Prefrontal Cortex",

    "messages": [],
    "private_messages": [],
    "private_unlocked": False,

    "progress": {
        "experiments": 0,
        "puzzles": 0,
        "games": 0,
        "research": 0,
        "journey": 0,
        "mood_checks": 0,
        "streak": 1,
    },

    "ai_requests": 0,
    "ai_cache": {},

    "last_mood_result": "",
    "last_experiment_result": "",

    "puzzle_completed": False,
    "puzzle_score": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        if isinstance(value, dict):
            st.session_state[key] = value.copy()
        else:
            st.session_state[key] = value

# =========================================================
# PAGES
# =========================================================

PAGES = [
    "Welcome Reboot",
    "Lab",
    "Explore Brain",
    "Brain Puzzle",
    "AI Mood & Behaviour",
    "Brain Exercises",
    "Research Book",
    "Ask Ayna",
    "Private Ask Ayna",
    "My Progress",
]

# =========================================================
# DATA
# =========================================================

BRAIN = {
    "Prefrontal Cortex": (
        "Supports planning, working memory, cognitive control and goal-directed behaviour.",
        "Planning, decision-making, inhibition and cognitive control.",
        "Cortex ↔ Striatum ↔ Pallidum ↔ Thalamus ↔ Cortex",
    ),

    "Hippocampus": (
        "Important for memory formation, spatial representation and contextual learning.",
        "Learning, episodic memory and navigation.",
        "Hippocampus ↔ Entorhinal Cortex ↔ Cortex",
    ),

    "Amygdala": (
        "Processes emotionally significant information and contributes to emotional learning.",
        "Threat processing, salience and emotional learning.",
        "Amygdala ↔ Hypothalamus ↔ Brainstem/Cortex",
    ),

    "Striatum": (
        "Contributes to action selection, reward learning and habit-related processes.",
        "Reward learning, action selection and habits.",
        "Cortex → Striatum → Pallidal Pathways → Thalamus → Cortex",
    ),

    "Anterior Cingulate Cortex": (
        "Contributes to performance monitoring, conflict processing and control.",
        "Conflict monitoring, error processing and effort-related control.",
        "ACC ↔ Prefrontal ↔ Striatal Networks",
    ),

    "Cerebellum": (
        "Supports coordination, timing and motor learning and also contributes to cognition.",
        "Timing, coordination, balance and motor learning.",
        "Cerebellum → Deep Nuclei → Thalamus → Cortex",
    ),
}

NT = {
    "Dopamine": "Involved in reward learning, motivation, movement and several cognitive processes.",
    "Serotonin": "Involved in mood-related processes, sleep, appetite and many physiological functions.",
    "GABA": "A major inhibitory neurotransmitter in the central nervous system.",
    "Glutamate": "A major excitatory neurotransmitter important for learning and plasticity.",
    "Acetylcholine": "Contributes to attention, learning, memory and neuromuscular communication.",
}

BOOK = {
    "Brain & Behaviour": (
        "Behaviour emerges from interactions among brain networks, body systems and environment.",
        "Cognitive neuroscience examines how distributed neural systems contribute to behaviour. Correlation, causation, computational models and experimental design must be distinguished.",
    ),

    "Memory": (
        "Memory includes encoding, consolidation and retrieval.",
        "Different forms of memory involve partly distinct but interacting neural systems, including working, episodic, semantic and procedural memory.",
    ),

    "Attention": (
        "Attention changes which information receives processing priority.",
        "Attention involves selection, enhancement and suppression interacting with sensory and cognitive-control networks.",
    ),

    "Perception": (
        "Perception is the brain's construction of meaningful representations from sensory input.",
        "Perception reflects interactions among sensory evidence, prior knowledge, attention and context.",
    ),

    "Emotion": (
        "Emotion involves interacting brain, body and cognitive processes.",
        "Modern models emphasize distributed networks, appraisal, interoception, learning and context rather than a single emotion centre.",
    ),

    "Decision Making": (
        "Decisions combine goals, rewards, uncertainty, memory and control.",
        "Decision neuroscience examines valuation, learning, uncertainty, evidence accumulation and cognitive control.",
    ),

    "Cognitive Control": (
        "Cognitive control helps maintain goals and adjust behaviour.",
        "Prefrontal, cingulate, parietal and striatal systems interact in task-dependent control.",
    ),

    "Neuroplasticity": (
        "The nervous system can change with development, learning and experience.",
        "Plasticity can occur at synaptic, circuit and systems levels and is influenced by learning and context.",
    ),
}

EQUIPMENT = [
    "EEG Scanner",
    "Eye Tracker",
    "Reaction-Time Monitor",
    "Auditory Attention Station",
    "Cognitive Task Screen",
    "Physiological Monitor",
]

EXPERIMENTS = [
    ("Attention Gate", "Attention"),
    ("Working Memory Sprint", "Working Memory"),
    ("Decision Under Delay", "Decision Making"),
    ("Inhibition Challenge", "Inhibitory Control"),
    ("Cognitive Flexibility", "Cognitive Flexibility"),
    ("Memory Retrieval", "Memory"),
]

# =========================================================
# HELPERS
# =========================================================


@st.cache_data(show_spinner=False)
def load_brain():
    if not BRAIN_PATH:
        return None

    try:
        return Image.open(BRAIN_PATH).convert("RGB")
    except Exception:
        return None


brain = load_brain()


def get_api_key():
    names = [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ]

    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass

        value = os.getenv(name)

        if value:
            return value.strip()

    return None


@st.cache_resource(show_spinner=False)
def make_client(api_key):
    if genai is None or not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

AI_LIMIT = 140


def ask_ai(prompt, context="", max_tokens=450):
    st.session_state.setdefault("ai_cache", {})
    st.session_state.setdefault("ai_requests", 0)

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

    if st.session_state.ai_requests >= AI_LIMIT:
        return (
            "AI session limit reached. Local NEUROLENS tools are still available.",
            "limit",
        )

    client = make_client(get_api_key())

    if client is None:
        return (
            "Ask Ayna AI is unavailable right now. Please check GEMINI_API_KEY in Streamlit Secrets.",
            "offline",
        )

    short_context = "\n".join(
        context[-4000:].splitlines()[-12:]
    )

    full_prompt = f"""
You are Ayna, the AI cognitive neuroscience assistant inside NEUROLENS.

Rules:
- Be scientifically cautious.
- Use simple language when possible.
- Do not diagnose medical or psychiatric conditions.
- Do not claim that a game directly measures brain activity.
- Do not claim that a voice sample provides a clinical diagnosis.
- Distinguish evidence from hypothesis.
- Do not pretend to be a doctor or therapist.
- If discussing research, mention uncertainty and study limitations.
- You can answer in English or Roman English.

Context:
{short_context}

User request:
{prompt}
"""

    try:
        st.session_state.ai_requests += 1

        if types is not None:
            config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_tokens,
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
                config=config,
            )

        else:
            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
            )

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:
            return (
                "Ayna returned no text. Please try again.",
                "empty",
            )

        text = text.strip()

        st.session_state.ai_cache[cache_key] = text

        return text, "ai"

    except Exception as exc:
        return (
            "Ayna could not complete that AI request right now. "
            "You can continue using the local NEUROLENS tools.",
            "error",
        )


def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()


def record(name, amount=1):
    st.session_state.progress[name] = (
        st.session_state.progress.get(name, 0)
        + amount
    )


def voice_button(text, key, language=None):
    if language is None:
        language = (
            "en-US"
            if st.session_state.language == "English"
            else "en-US"
        )

    safe = (
        str(text)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", " ")
        .replace("\r", " ")
    )

    components.html(
        f"""
        <button
            style="
                padding:9px 15px;
                border-radius:11px;
                border:1px solid #789;
                background:#173b5f;
                color:white;
                cursor:pointer;
                font-size:14px;
            "
            onclick="speakAyna()"
        >
        🔊 Play Ayna
        </button>

        <script>
        function speakAyna() {{
            const u =
                new SpeechSynthesisUtterance('{safe}');

            u.lang = '{language}';

            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=55,
    )


def reboot_voice_text():
    if st.session_state.language == "Roman English":
        return (
            "Welcome to NeuroLens! "
            "Main Ayna hoon, aap ki cognitive neuroscience lab assistant. "
            "Aaj hum brain, behaviour aur cognition ko explore karenge."
        )

    return (
        "Welcome to NeuroLens! "
        "I'm Ayna, your cognitive neuroscience lab assistant. "
        "Let's explore the brain, behaviour, and cognition together."
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    language = st.radio(
        "Language",
        [
            "English",
            "Roman English",
        ],
        index=(
            0
            if st.session_state.language == "English"
            else 1
        ),
        key="language_selector",
    )

    if language != st.session_state.language:
        st.session_state.language = language

    st.divider()

    st.caption("Navigate")

    for i, page_name in enumerate(PAGES):

        prefix = (
            "● "
            if page_name == st.session_state.page
            else "○ "
        )

        if st.button(
            prefix + page_name,
            key=f"navigation_button_{i}",
            use_container_width=True,
        ):
            go_to(page_name)

    st.divider()

    st.caption(
        f"AI requests: "
        f"{st.session_state.ai_requests}/{AI_LIMIT}"
    )

    st.progress(
        min(
            st.session_state.ai_requests
            / AI_LIMIT,
            1.0,
        )
    )

    st.caption(
        "Local experiments and puzzle functions "
        "do not require AI."
    )

# =========================================================
# HEADER
# =========================================================

if st.session_state.page != "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">
            <h1>🧠 NEUROLENS</h1>
            <p>
                Explore cognition, behaviour & the brain
            </p>
            <small>
                Interactive Cognitive Neuroscience Platform
                • Created by Ayna Jaffri
            </small>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# WELCOME REBOOT
# =========================================================

if st.session_state.page == "Welcome Reboot":

    st.markdown(
        """
        <div class="reboot-box">
            <h1>🧠 NEUROLENS</h1>
            <h2>Welcome Reboot</h2>
            <p>
                Initializing Ayna Cognitive Neuroscience System...
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    if AYNA_REBOOT_VIDEO:

        st.video(
            AYNA_REBOOT_VIDEO
        )

    elif AYNA_ROBOT:

        st.image(
            AYNA_ROBOT,
            use_container_width=True,
        )

    else:

        st.markdown(
            """
            <div class="lab-card">
                <div class="neural-line nl1"></div>
                <div class="neural-line nl2"></div>
                <div class="neural-line nl3"></div>
                <div class="neural-orb"></div>

                <div style="
                    position:absolute;
                    top:18px;
                    left:20px;
                    font-weight:bold;
                ">
                    AYNA SYSTEM ONLINE
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 🤖 Ayna")

    st.write(
        reboot_voice_text()
    )

    voice_button(
        reboot_voice_text(),
        "welcome_reboot_voice",
    )

    st.info(
        "Ayna's voice is generated through browser speech synthesis. "
        "Your reboot video can remain silent and the voice will play separately."
    )

    if st.button(
        "🚀 Enter NeuroLens",
        type="primary",
        use_container_width=True,
        key="enter_neurolens",
    ):

        st.session_state.welcome_seen = True
        st.session_state.page = "Lab"

        st.rerun()

# =========================================================
# LAB
# =========================================================

elif st.session_state.page == "Lab":

    st.subheader(
        "🔬 Cognitive Neuroscience Lab"
    )

    left, right = st.columns(
        [1.55, 1]
    )

    with left:

        if LAB_VIDEO:

            st.video(
                LAB_VIDEO
            )

        else:

            st.markdown(
                """
                <div class="lab-card">

                    <div class="neural-line nl1"></div>
                    <div class="neural-line nl2"></div>
                    <div class="neural-line nl3"></div>

                    <div class="neural-orb"></div>

                    <div style="
                        position:absolute;
                        top:15px;
                        left:20px;
                        font-weight:bold;
                    ">
                        LIVE NEURAL ACTIVITY
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:

        st.markdown("### 👩‍🔬 Lab Setup")

        characters = [
            "Nova",
            "Mira",
            "Ray",
            "Zara",
        ]

        char = st.selectbox(
            "Choose your lab character",
            characters,
            index=characters.index(
                st.session_state.character
            ),
            key="lab_character",
        )

        st.session_state.character = char

        equipment = st.selectbox(
            "Choose equipment",
            EQUIPMENT,
            index=EQUIPMENT.index(
                st.session_state.equipment
            ),
            key="lab_equipment",
        )

        st.session_state.equipment = equipment

        st.info(
            f"🧑‍🔬 {char} is ready with "
            f"{equipment}."
        )

        if st.button(
            "🧪 Start Today's Experiment",
            use_container_width=True,
            key="lab_start_experiment",
        ):

            go_to("Brain Exercises")

        if st.button(
            "🧠 Enter Brain Journey",
            use_container_width=True,
            key="lab_brain_journey",
        ):

            st.session_state.journey_stage = "brain"

            go_to("Explore Brain")

        if st.button(
            "🧩 Open Brain Puzzle",
            use_container_width=True,
            key="lab_puzzle",
        ):

            go_to("Brain Puzzle")

        if st.button(
            "🎯 AI Mood & Behaviour",
            use_container_width=True,
            key="lab_mood",
        ):

            go_to("AI Mood & Behaviour")

        if st.button(
            "💬 Ask Ayna",
            use_container_width=True,
            key="lab_ask_ayna",
        ):

            go_to("Ask Ayna")

    st.divider()

    st.markdown(
        "### 🧪 Today's Lab Pathway"
    )

    pathway = [
        ("👤", "Choose Character"),
        ("🔬", "Choose Equipment"),
        ("🧠", "Run Experiment"),
        ("🤖", "Ayna Analysis"),
    ]

    cols = st.columns(4)

    for col, item in zip(
        cols,
        pathway,
    ):

        with col:

            st.markdown(
                f"""
                <div class="card">
                    <h2>{item[0]}</h2>
                    <b>{item[1]}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 🧰 Available Equipment")

    eq_cols = st.columns(3)

    for i, equipment_name in enumerate(
        EQUIPMENT
    ):

        with eq_cols[i % 3]:

            st.markdown(
                f"""
                <div class="equipment">
                    🔬 <b>{equipment_name}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =========================================================
# EXPLORE BRAIN
# =========================================================

elif st.session_state.page == "Explore Brain":

    st.subheader(
        "🧠 Inside-Brain Journey"
    )

    stage_labels = {
        "brain": "Whole Brain",
        "region": "Brain Region",
        "neuron": "Neuron",
        "axon": "Axon & Myelin",
        "synapse": "Synapse",
        "nt": "Neurotransmitter",
    }

    stage = st.session_state.journey_stage
    region = st.session_state.journey_region

    st.caption(
        " → ".join(
            stage_labels.values()
        )
    )

    # -----------------------------------------------------
    # WHOLE BRAIN
    # -----------------------------------------------------

    if stage == "brain":

        if JOURNEY_VIDEO:

            st.video(
                JOURNEY_VIDEO
            )

        elif brain:

            st.image(
                brain,
                use_container_width=True,
            )

        else:

            st.markdown(
                """
                <div class="stage-card">
                    <div style="font-size:70px">
                        🧠
                    </div>
                    <h2>Whole Brain</h2>
                    <p>
                        Explore the major systems
                        of the human brain.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        region_choice = st.selectbox(
            "🔎 Choose a brain region",
            list(BRAIN.keys()),
            index=list(BRAIN.keys()).index(
                region
            ),
            key="brain_region_selector",
        )

        if st.button(
            "🚀 Travel Inside This Region",
            use_container_width=True,
            key="travel_region",
        ):

            st.session_state.journey_region = region_choice
            st.session_state.journey_stage = "region"

            record("journey")

            st.rerun()

    # -----------------------------------------------------
    # REGION
    # -----------------------------------------------------

    elif stage == "region":

        info = BRAIN[region]

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"## 🔬 {region}"
            )

            st.info(
                info[0]
            )

            st.markdown(
                "**Behavioural / cognitive relevance:**"
            )

            st.write(
                info[1]
            )

        with col2:

            st.markdown(
                "## 🔗 Circuit"
            )

            st.code(
                info[2]
            )

        voice_button(
            (
                f"Welcome inside the {region}. "
                "Let's explore how this neural system "
                "contributes to cognition and behaviour."
            ),
            "region_voice",
        )

        if st.button(
            "🧬 Enter Neuron",
            use_container_width=True,
            key="enter_neuron",
        ):

            st.session_state.journey_stage = "neuron"
            st.rerun()

        if st.button(
            "🔙 Back to Whole Brain",
            use_container_width=True,
            key="back_to_brain",
        ):

            st.session_state.journey_stage = "brain"
            st.rerun()

    # -----------------------------------------------------
    # NEURON
    # -----------------------------------------------------

    elif stage == "neuron":

        st.markdown(
            f"## 🧬 Neuron inside {region}"
        )

        st.markdown(
            """
            <div class="stage-card">
                <div class="neuron">
                    🌳
                </div>

                <h3>
                    Dendrites →
                    Soma →
                    Axon →
                    Terminals
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        part = st.selectbox(
            "Explore neuron",
            [
                "Dendrites",
                "Cell Body",
                "Axon",
                "Axon Terminal",
            ],
            key="neuron_part",
        )

        neuron_info = {
            "Dendrites":
                "Receive many synaptic inputs from other neurons.",

            "Cell Body":
                "Contains the nucleus and supports cellular metabolism.",

            "Axon":
                "Carries electrical signals toward the axon terminals.",

            "Axon Terminal":
                "Specialized region involved in communication with another cell.",
        }

        st.info(
            neuron_info[part]
        )

        if st.button(
            "⚡ Follow Electrical Signal",
            use_container_width=True,
            key="follow_signal",
        ):

            st.session_state.journey_stage = "axon"
            st.rerun()

    # -----------------------------------------------------
    # AXON
    # -----------------------------------------------------

    elif stage == "axon":

        st.markdown(
            "## ⚡ Axon & Myelin"
        )

        st.info(
            "Myelin insulates many axons and supports "
            "rapid saltatory conduction."
        )

        components.html(
            """
            <div class="signal-track">

                <div class="signal-axon"></div>

                <div class="signal-pulse">
                    ⚡
                </div>

            </div>
            """,
            height=130,
        )

        if st.button(
            "🔗 Enter Synapse",
            use_container_width=True,
            key="enter_synapse",
        ):

            st.session_state.journey_stage = "synapse"
            st.rerun()

    # -----------------------------------------------------
    # SYNAPSE
    # -----------------------------------------------------

    elif stage == "synapse":

        st.markdown(
            "## 🔗 Synapse Explorer"
        )

        st.markdown(
            """
            <div class="synapse">
                🟣 • • • • • 🔵
            </div>
            """,
            unsafe_allow_html=True,
        )

        synapse_part = st.selectbox(
            "Explore synapse",
            [
                "Presynaptic Terminal",
                "Synaptic Vesicles",
                "Synaptic Cleft",
                "Postsynaptic Membrane",
                "Receptors",
            ],
            key="synapse_part",
        )

        synapse_info = {

            "Presynaptic Terminal":
                "Sending side of a chemical synapse.",

            "Synaptic Vesicles":
                "Small membrane-bound structures that store neurotransmitter.",

            "Synaptic Cleft":
                "The extracellular space between communicating cells.",

            "Postsynaptic Membrane":
                "Receiving membrane containing signalling machinery.",

            "Receptors":
                "Proteins that detect signalling molecules.",
        }

        st.info(
            synapse_info[synapse_part]
        )

        if st.button(
            "🧪 Follow Neurotransmitter",
            use_container_width=True,
            key="follow_neurotransmitter",
        ):

            st.session_state.journey_stage = "nt"
            st.rerun()

    # -----------------------------------------------------
    # NEUROTRANSMITTER
    # -----------------------------------------------------

    elif stage == "nt":

        st.markdown(
            "## 🧪 Neurotransmitter Explorer"
        )

        neurotransmitter = st.selectbox(
            "Choose neurotransmitter",
            list(NT.keys()),
            key="neurotransmitter_selector",
        )

        st.success(
            NT[neurotransmitter]
        )

        st.markdown(
            """
            <div class="stage-card">
                <div style="
                    font-size:40px;
                    animation:neuronPulse 1.3s infinite;
                ">
                    🟣 🟣 🟣 🟣 🟣
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        voice_button(
            (
                f"The selected neurotransmitter is "
                f"{neurotransmitter}. "
                f"{NT[neurotransmitter]}"
            ),
            "nt_voice",
        )

        if st.button(
            "🏠 Restart Brain Journey",
            use_container_width=True,
            key="restart_journey",
        ):

            st.session_state.journey_stage = "brain"
            st.rerun()

    # -----------------------------------------------------
    # ASK AYNA ABOUT CURRENT STAGE
    # -----------------------------------------------------

    st.divider()

    st.markdown(
        "### 💬 Ask Ayna About This Stage"
    )

    stage_question = st.text_input(
        "Question",
        key="journey_question",
        placeholder="Ask about what you are seeing...",
    )

    if st.button(
        "Ask Ayna",
        key="journey_ask",
    ) and stage_question:

        answer, source = ask_ai(
            stage_question,
            (
                f"Current stage: "
                f"{stage_labels[stage]}. "
                f"Brain region: {region}."
            ),
        )

        st.write(
            answer
        )

        st.caption(
            f"Source mode: {source}"
        )

        voice_button(
            answer,
            "journey_answer_voice",
        )

# =========================================================
# BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    st.subheader(
        "🧩 Brain Picture Puzzle"
    )

    st.caption(
        "Drag with mouse or touch. "
        "Drop a piece onto another slot."
    )

    if not brain:

        st.warning(
            "brain.png is required for the puzzle."
        )

    else:

        difficulty = st.select_slider(
            "Difficulty",
            [
                "3 × 3",
                "4 × 4",
                "5 × 5",
            ],
            value="3 × 3",
            key="puzzle_difficulty",
        )

        N = int(
            difficulty[0]
        )

        buffer = BytesIO()

        brain.save(
            buffer,
            format="PNG",
        )

        image_b64 = base64.b64encode(
            buffer.getvalue()
        ).decode()

        puzzle_html = f"""
        <div style="
            font-family:Arial;
            color:#111;
        ">

            <button
                id="newPuzzle"
                style="
                    padding:10px 14px;
                    border-radius:10px;
                    border:1px solid #777;
                    cursor:pointer;
                "
            >
                🔀 New Puzzle
            </button>

            <span
                id="stats"
                style="margin-left:15px;"
            ></span>

            <div
                id="board"
                style="
                    display:grid;
                    grid-template-columns:
                        repeat({N},1fr);
                    gap:6px;
                    max-width:850px;
                    margin:16px auto;
                "
            ></div>

            <h3 id="message"></h3>

        </div>

        <style>

        .slot {{
            aspect-ratio:1;
            border:2px dashed #8da0b5;
            border-radius:10px;
            overflow:hidden;
            background:#f4f7fa;
        }}

        .piece {{
            width:100%;
            height:100%;
            background-image:
                url(data:image/png;base64,{image_b64});
            background-size:
                {N*100}% {N*100}%;
            cursor:grab;
            touch-action:none;
            border-radius:8px;
        }}

        .piece.correct {{
            outline:3px solid #35a86a;
            cursor:default;
        }}

        </style>

        <script>

        (() => {{

            const N = {N};

            const board =
                document.getElementById(
                    "board"
                );

            const stats =
                document.getElementById(
                    "stats"
                );

            const message =
                document.getElementById(
                    "message"
                );

            let moves = 0;

            let startTime =
                Date.now();

            let dragPiece = null;

            function shuffle(array) {{

                for (
                    let i = array.length - 1;
                    i > 0;
                    i--
                ) {{

                    const j =
                        Math.floor(
                            Math.random() *
                            (i + 1)
                        );

                    [
                        array[i],
                        array[j]
                    ] = [
                        array[j],
                        array[i]
                    ];
                }}
            }}

            function update() {{

                const correct =
                    [
                        ...document
                            .querySelectorAll(
                                ".piece.correct"
                            )
                    ].length;

                const seconds =
                    Math.floor(
                        (
                            Date.now()
                            - startTime
                        ) / 1000
                    );

                stats.textContent =
                    "Moves: "
                    + moves
                    + " • Correct: "
                    + correct
                    + "/"
                    + (N*N)
                    + " • Time: "
                    + seconds
                    + "s";

                if (
                    correct === N*N
                ) {{

                    message.textContent =
                        "🎉 Puzzle solved!";

                }}

            }}

            function setup() {{

                board.innerHTML = "";

                message.textContent = "";

                moves = 0;

                startTime =
                    Date.now();

                const pieces =
                    [
                        ...Array(
                            N*N
                        ).keys()
                    ];

                shuffle(
                    pieces
                );

                pieces.forEach(
                    (id) => {{

                        const slot =
                            document
                                .createElement(
                                    "div"
                                );

                        slot.className =
                            "slot";

                        slot.dataset.slot =
                            id;

                        const piece =
                            document
                                .createElement(
                                    "div"
                                );

                        piece.className =
                            "piece";

                        piece.dataset.id =
                            id;

                        const row =
                            Math.floor(
                                id / N
                            );

                        const col =
                            id % N;

                        const x =
                            N === 1
                            ? 0
                            : (
                                col /
                                (N-1)
                            ) * 100;

                        const y =
                            N === 1
                            ? 0
                            : (
                                row /
                                (N-1)
                            ) * 100;

                        piece.style
                            .backgroundPosition =
                            x + "% " + y + "%";

                        piece.addEventListener(
                            "pointerdown",
                            (event) => {{

                                if (
                                    piece
                                        .classList
                                        .contains(
                                            "correct"
                                        )
                                ) {{
                                    return;
                                }}

                                dragPiece =
                                    piece;

                                try {{
                                    piece.setPointerCapture(
                                        event.pointerId
                                    );
                                }} catch(e) {{}}
                            }}
                        );

                        piece.addEventListener(
                            "pointerup",
                            (event) => {{

                                if (
                                    !dragPiece
                                ) {{
                                    return;
                                }}

                                const target =
                                    document
                                        .elementFromPoint(
                                            event.clientX,
                                            event.clientY
                                        )
                                        ?.closest(
                                            ".slot"
                                        );

                                if (
                                    target
                                ) {{

                                    const other =
                                        target
                                            .querySelector(
                                                ".piece"
                                            );

                                    const oldParent =
                                        piece.parentElement;

                                    if (
                                        other
                                        &&
                                        other !== piece
                                    ) {{

                                        oldParent
                                            .appendChild(
                                                other
                                            );

                                        target
                                            .appendChild(
                                                piece
                                            );

                                    }} else {{

                                        target
                                            .appendChild(
                                                piece
                                            );
                                    }}

                                    moves++;

                                    document
                                        .querySelectorAll(
                                            ".piece"
                                        )
                                        .forEach(
                                            (p) => {{

                                                const isCorrect =
                                                    Number(
                                                        p.dataset.id
                                                    )
                                                    ===
                                                    Number(
                                                        p.parentElement
                                                            .dataset
                                                            .slot
                                                    );

                                                p.classList
                                                    .toggle(
                                                        "correct",
                                                        isCorrect
                                                    );
                                            }}
                                        );

                                    update();
                                }}

                                dragPiece =
                                    null;
                            }}
                        );

                        slot.appendChild(
                            piece
                        );

                        board.appendChild(
                            slot
                        );
                    }
                );

                update();
            }}

            document
                .getElementById(
                    "newPuzzle"
                )
                .onclick = setup;

            setInterval(
                update,
                1000
            );

            setup();

        }})();

        </script>
        """

        components.html(
            puzzle_html,
            height=760,
        )

        if st.button(
            "✅ Record Puzzle Completion",
            key="record_puzzle_completion",
        ):

            record("puzzles")

            st.session_state.puzzle_completed = True

            st.success(
                "Puzzle activity recorded."
            )

# =========================================================
# AI MOOD & BEHAVIOUR
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.subheader(
        "🎯 AI Mood & Behaviour"
    )

    st.write(
        "Speak naturally to Ayna or type a message. "
        "The result is an educational conversational estimate, "
        "not a clinical assessment."
    )

    st.warning(
        "This feature does not diagnose mental-health conditions "
        "and should not be treated as a medical assessment."
    )

    voice_tab, text_tab = st.tabs(
        [
            "🎙️ Voice",
            "⌨️ Text",
        ]
    )

    # -----------------------------------------------------
    # VOICE
    # -----------------------------------------------------

    with voice_tab:

        audio = None

        try:

            audio = st.audio_input(
                "Record your voice",
                key="behaviour_audio",
            )

        except Exception:

            st.info(
                "Voice recording is not available "
                "in this browser. Use the Text tab."
            )

        context = st.text_input(
            "Optional context",
            key="behaviour_context",
            placeholder="Anything you want Ayna to consider?",
        )

        if st.button(
            "🧠 Send Voice",
            key="send_behaviour_voice",
        ):

            if not audio:

                st.warning(
                    "Please record your voice first."
                )

            else:

                client = make_client(
                    get_api_key()
                )

                if client is None:

                    st.error(
                        "Voice AI needs GEMINI_API_KEY "
                        "in Streamlit Secrets."
                    )

                elif (
                    st.session_state.ai_requests
                    >= AI_LIMIT
                ):

                    st.warning(
                        "AI session limit reached."
                    )

                else:

                    try:

                        st.session_state.ai_requests += 1

                        prompt = f"""
Analyze this voice sample only for broad conversational affect.

Return:
1. Emoji
2. One broad mood:
   Positive/Happy
   Calm
   Neutral
   Worried
   Low/Sad
   Frustrated
   Tired
3. Optional secondary signal
4. Confidence: Low, Medium or High
5. One short friendly explanation

Do not diagnose.
Do not infer sensitive traits.
Do not claim this measures brain activity.

Context:
{context[:500]}
"""

                        if types is not None:

                            response = (
                                client.models.generate_content(
                                    model=MODEL,
                                    contents=[
                                        types.Part.from_bytes(
                                            data=audio.getvalue(),
                                            mime_type=(
                                                audio.type
                                                or "audio/wav"
                                            ),
                                        ),
                                        prompt,
                                    ],
                                )
                            )

                        else:

                            response = (
                                client.models.generate_content(
                                    model=MODEL,
                                    contents=[
                                        prompt
                                    ],
                                )
                            )

                        result = (
                            getattr(
                                response,
                                "text",
                                None,
                            )
                            or
                            "No result returned."
                        )

                        st.session_state.last_mood_result = result

                        record(
                            "mood_checks"
                        )

                        st.success(
                            "😊 Ayna's conversational estimate"
                        )

                        st.write(
                            result
                        )

                        voice_button(
                            result,
                            "mood_voice_result",
                        )

                    except Exception:

                        st.error(
                            "Voice analysis is temporarily "
                            "unavailable. You can still use "
                            "text analysis."
                        )

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    with text_tab:

        mood_text = st.text_area(
            "Tell Ayna how you feel",
            height=130,
            key="mood_text_input",
            placeholder=(
                "Example: I feel a little tired "
                "but I'm excited about my work."
            ),
        )

        if st.button(
            "✨ Send Text",
            key="send_mood_text",
        ):

            if not mood_text.strip():

                st.warning(
                    "Please enter some text first."
                )

            else:

                answer, source = ask_ai(
                    f"""
Give an educational conversational affect estimate.

Return:
- one suitable emoji
- primary broad mood
- optional secondary signal
- confidence
- one friendly sentence

Text:
{mood_text}
""",
                    max_tokens=250,
                )

                st.session_state.last_mood_result = answer

                record(
                    "mood_checks"
                )

                st.info(
                    answer
                )

                st.caption(
                    f"Source mode: {source}"
                )

                voice_button(
                    answer,
                    "mood_text_voice",
                )

# =========================================================
# BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    st.subheader(
        "🧪 Today's Cognitive Neuroscience Experiment"
    )

    day_index = (
        time.gmtime().tm_yday - 1
    ) % len(EXPERIMENTS)

    title, domain = EXPERIMENTS[
        day_index
    ]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {domain}"
    )

    # -----------------------------------------------------
    # ATTENTION
    # -----------------------------------------------------

    if domain == "Attention":

        choice = st.radio(
            "Which sequence contains X?",
            [
                "A B C D",
                "A B X D",
                "A B C E",
                "A X C D",
            ],
            key="attention_choice",
        )

        submitted = st.button(
            "Check",
            key="attention_check",
        )

        correct = (
            choice == "A B X D"
        )

    # -----------------------------------------------------
    # WORKING MEMORY
    # -----------------------------------------------------

    elif domain == "Working Memory":

        st.markdown(
            "### Memorize:"
        )

        st.markdown(
            "## **7 2 9 4 1 8**"
        )

        memory_answer = st.text_input(
            "Enter the sequence",
            key="memory_answer",
        )

        submitted = st.button(
            "Check",
            key="memory_check",
        )

        correct = (
            memory_answer
            .replace(" ", "")
            == "729418"
        )

    # -----------------------------------------------------
    # DECISION MAKING
    # -----------------------------------------------------

    elif domain == "Decision Making":

        decision = st.radio(
            "Which would you choose?",
            [
                "Rs. 1,000 today",
                "Rs. 1,500 after 30 days",
            ],
            key="decision_choice",
        )

        submitted = st.button(
            "Submit Decision",
            key="decision_submit",
        )

        correct = True

        if submitted:

            st.info(
                "There is no universally correct answer. "
                "This task explores delay discounting and individual choice."
            )

    # -----------------------------------------------------
    # INHIBITORY CONTROL
    # -----------------------------------------------------

    elif domain == "Inhibitory Control":

        if "inhibition_target" not in st.session_state:

            st.session_state.inhibition_target = random.choice(
                [
                    "RED",
                    "BLUE",
                    "GREEN",
                ]
            )

        target = st.session_state.inhibition_target

        st.markdown(
            f"## {target}"
        )

        response = st.selectbox(
            "Response",
            [
                "RED",
                "BLUE",
                "GREEN",
            ],
            key="inhibition_response",
        )

        submitted = st.button(
            "Submit",
            key="inhibition_submit",
        )

        correct = (
            response == target
        )

    # -----------------------------------------------------
    # FLEXIBILITY
    # -----------------------------------------------------

    elif domain == "Cognitive Flexibility":

        rule = st.selectbox(
            "Current rule",
            [
                "Choose the larger number",
                "Choose the smaller number",
                "Choose the even number",
            ],
            key="flexibility_rule",
        )

        a, b = random.sample(
            range(1, 20),
            2,
        )

        st.write(
            f"Numbers: **{a}** and **{b}**"
        )

        if rule == "Choose the larger number":

            answer = st.radio(
                "Your answer",
                [
                    str(a),
                    str(b),
                ],
                key="flex_answer_large",
            )

            correct = (
                int(answer)
                == max(a, b)
            )

        elif rule == "Choose the smaller number":

            answer = st.radio(
                "Your answer",
                [
                    str(a),
                    str(b),
                ],
                key="flex_answer_small",
            )

            correct = (
                int(answer)
                == min(a, b)
            )

        else:

            even_options = [
                x
                for x in [a, b]
                if x % 2 == 0
            ]

            if even_options:

                options = [
                    str(x)
                    for x in [a, b]
                ]

                answer = st.radio(
                    "Your answer",
                    options,
                    key="flex_answer_even",
                )

                correct = (
                    int(answer)
                    in even_options
                )

            else:

                st.info(
                    "Neither option is even. "
                    "This trial has no valid response."
                )

                answer = None
                correct = False

        submitted = st.button(
            "Submit",
            key="flex_submit",
        )

    # -----------------------------------------------------
    # MEMORY RETRIEVAL / FALLBACK
    # -----------------------------------------------------

    else:

        number = st.session_state.get(
            "retrieval_number"
        )

        if number is None:

            number = random.randint(
                10,
                40,
            )

            st.session_state.retrieval_number = number

        answer = st.number_input(
            f"{number} + 7 = ?",
            step=1,
            key="retrieval_answer",
        )

        submitted = st.button(
            "Check",
            key="retrieval_check",
        )

        correct = (
            answer
            == number + 7
        )

    if submitted:

        if correct:

            st.success(
                "🎉 Correct response recorded!"
            )

            record(
                "experiments"
            )

            record(
                "games"
            )

            st.session_state.last_experiment_result = (
                f"{title}: correct"
            )

        else:

            st.warning(
                "Not quite. Treat this as practice "
                "rather than a clinical or diagnostic result."
            )

            st.session_state.last_experiment_result = (
                f"{title}: incorrect"
            )

    st.divider()

    st.info(
        "Educational task only. A single cognitive task "
        "cannot diagnose a condition or directly measure "
        "brain activity."
    )

    st.markdown(
        "### 🤖 Ayna's Lab Note"
    )

    lab_note = (
        f"Today's task explores {domain}. "
        "Performance can be influenced by attention, "
        "practice, fatigue, strategy and many other factors."
    )

    st.write(
        lab_note
    )

    voice_button(
        lab_note,
        "experiment_lab_voice",
    )

# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    st.subheader(
        "📖 Cognitive Neuroscience Research Book"
    )

    mode = st.radio(
        "Reading Mode",
        [
            "Simple Mode",
            "Research Mode",
        ],
        horizontal=True,
        key="research_mode",
    )

    topic = st.selectbox(
        "Choose topic",
        list(BOOK.keys()),
        key="research_topic",
    )

    simple_text, research_text = BOOK[
        topic
    ]

    if mode == "Simple Mode":

        st.info(
            simple_text
        )

        voice_button(
            simple_text,
            "research_simple_voice",
        )

    else:

        st.info(
            research_text
        )

        st.markdown(
            "### 🔎 Research Note"
        )

        st.write(
            "When interpreting scientific findings, "
            "consider study design, sample size, measurement, "
            "effect size, uncertainty, replication and alternative explanations."
        )

        st.markdown(
            "### 📚 Research Sources"
        )

        st.write(
            "• Peer-reviewed review articles"
        )

        st.write(
            "• PubMed-indexed research"
        )

        st.write(
            "• Systematic reviews and meta-analyses"
        )

        st.write(
            "• Primary experimental studies"
        )

        st.info(
            "Research Book content is educational. "
            "For publication-grade work, verify the original paper "
            "and citation before using a claim."
        )

        if st.button(
            "🔎 Ask Ayna to Explain This Topic",
            key="research_ai_explain",
        ):

            answer, source = ask_ai(
                (
                    f"Explain {topic} in cognitive neuroscience "
                    "for a researcher. Include important concepts, "
                    "measurement issues and limitations."
                ),
                max_tokens=450,
            )

            st.write(
                answer
            )

            st.caption(
                source
            )

            voice_button(
                answer,
                "research_ai_voice",
            )

# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    st.subheader(
        "💬 Ask Ayna"
    )

    st.caption(
        "Ask about neuroscience, cognition, behaviour, "
        "AI, learning, decision-making and general questions."
    )

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

            if (
                message["role"]
                == "assistant"
            ):

                voice_button(
                    message["content"],
                    (
                        "ask_ayna_voice_"
                        + hashlib.sha256(
                            message["content"].encode(
                                "utf-8",
                                errors="ignore",
                            )
                        ).hexdigest()[:12]
                    ),
                )

    question = st.chat_input(
        "Ask Ayna...",
        key="public_chat",
    )

    if question:

        context = "\n".join(
            (
                f"{m['role']}: "
                f"{m['content'][:700]}"
            )
            for m in st.session_state.messages[-6:]
        )

        answer, source = ask_ai(
            question,
            context,
        )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    if st.session_state.messages:

        if st.button(
            "🗑️ Clear Chat",
            key="clear_public_chat",
        ):

            st.session_state.messages = []

            st.rerun()

# =========================================================
# PRIVATE ASK AYNA
# =========================================================

elif st.session_state.page == "Private Ask Ayna":

    st.subheader(
        "🔐 Private Ask Ayna"
    )

    st.caption(
        "Session-level private chat."
    )

    if not st.session_state.private_unlocked:

        st.write(
            "Enter your private session PIN."
        )

        pin = st.text_input(
            "PIN",
            type="password",
            max_chars=12,
            key="private_pin",
        )

        st.caption(
            "Default demo PIN: 1234. "
            "For real private data, use authenticated encrypted storage."
        )

        if st.button(
            "🔓 Unlock",
            key="private_unlock_button",
        ):

            expected_pin = os.getenv(
                "NEUROLENS_PRIVATE_PIN",
                "1234",
            )

            if pin == expected_pin:

                st.session_state.private_unlocked = True

                st.success(
                    "Private session unlocked."
                )

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )

    else:

        for message in st.session_state.private_messages:

            with st.chat_message(
                message["role"]
            ):

                st.markdown(
                    message["content"]
                )

                if (
                    message["role"]
                    == "assistant"
                ):

                    voice_button(
                        message["content"],
                        (
                            "private_voice_"
                            + hashlib.sha256(
                                message["content"].encode(
                                    "utf-8",
                                    errors="ignore",
                                )
                            ).hexdigest()[:12]
                        ),
                    )

        private_question = st.chat_input(
            "Private message to Ayna...",
            key="private_chat",
        )

        if private_question:

            context = "\n".join(
                (
                    f"{m['role']}: "
                    f"{m['content'][:700]}"
                )
                for m in st.session_state.private_messages[-6:]
            )

            answer, _ = ask_ai(
                private_question,
                context,
            )

            st.session_state.private_messages.extend(
                [
                    {
                        "role": "user",
                        "content": private_question,
                    },
                    {
                        "role": "assistant",
                        "content": answer,
                    },
                ]
            )

            st.rerun()

        if st.button(
            "🗑️ Delete Private Session",
            key="delete_private_session",
        ):

            st.session_state.private_messages = []

            st.session_state.private_unlocked = False

            st.rerun()

# =========================================================
# MY PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.subheader(
        "📊 My Progress"
    )

    p = st.session_state.progress

    metrics = [
        (
            "Experiments",
            p.get("experiments", 0),
        ),
        (
            "Puzzles",
            p.get("puzzles", 0),
        ),
        (
            "Games",
            p.get("games", 0),
        ),
        (
            "Research",
            p.get("research", 0),
        ),
        (
            "Journey",
            p.get("journey", 0),
        ),
        (
            "Mood Checks",
            p.get("mood_checks", 0),
        ),
    ]

    cols = st.columns(
        len(metrics)
    )

    for col, (name, value) in zip(
        cols,
        metrics,
    ):

        with col:

            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>{name}</h3>
                    <h1>{value}</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    if plotly_go:

        fig = plotly_go.Figure(
            plotly_go.Bar(
                x=[
                    "Experiments",
                    "Puzzles",
                    "Games",
                    "Research",
                    "Journey",
                    "Mood",
                ],
                y=[
                    p.get(
                        "experiments",
                        0,
                    ),
                    p.get(
                        "puzzles",
                        0,
                    ),
                    p.get(
                        "games",
                        0,
                    ),
                    p.get(
                        "research",
                        0,
                    ),
                    p.get(
                        "journey",
                        0,
                    ),
                    p.get(
                        "mood_checks",
                        0,
                    ),
                ],
            )
        )

        fig.update_layout(
            height=380,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.markdown(
        "### 🔬 Current Lab Status"
    )

    st.write(
        f"Character: **{st.session_state.character}**"
    )

    st.write(
        f"Equipment: **{st.session_state.equipment}**"
    )

    if st.session_state.last_experiment_result:

        st.write(
            "Last experiment: "
            + st.session_state.last_experiment_result
        )

    if st.session_state.last_mood_result:

        st.write(
            "Last mood interaction completed."
        )

    st.info(
        "Progress in this build is session-based. "
        "Permanent history requires an authenticated backend/database."
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NEUROLENS • Interactive Cognitive Neuroscience • Created by Ayna Jaffri"
)
