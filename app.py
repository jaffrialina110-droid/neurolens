import os
import random
import time
import hashlib
import base64
import html
from io import BytesIO

import streamlit as st
from PIL import Image
import streamlit.components.v1 as components

# =========================================================
# OPTIONAL AI
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


def find_reboot_video():
    candidates = [
        "ayna_reboot.mp4",
        "ayna_welcome.mp4",
        "ayna_3d_reboot.mp4",
        "reboot.mp4",
        "welcome.mp4",
        "ayna.mp4",
    ]

    for name in candidates:
        path = asset_path(name)
        if path:
            return path

    if os.path.isdir(ASSETS):
        for name in os.listdir(ASSETS):
            low = name.lower()
            if low.endswith(".mp4") and (
                "reboot" in low
                or "welcome" in low
                or "ayna" in low
            ):
                return os.path.join(ASSETS, name)

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
        radial-gradient(circle at 10% 0%, #173c63, transparent 30%),
        radial-gradient(circle at 90% 20%, #162d4a, transparent 30%),
        linear-gradient(135deg, #050c15, #0a1727 55%, #06101c);
}

.block-container {
    max-width: 1450px;
    padding-top: 1rem;
}

.hero {
    padding: 28px;
    border-radius: 24px;
    background: linear-gradient(135deg, #102d4c, #111a31);
    border: 1px solid #3c5d7c;
    margin-bottom: 18px;
}

.card {
    padding: 18px;
    border-radius: 18px;
    background: rgba(13, 32, 53, .92);
    border: 1px solid #294560;
    margin: 8px 0;
}

.lab-card {
    padding: 20px;
    border-radius: 22px;
    background:
        radial-gradient(circle at center, #1e537e, #0a1729 65%);
    border: 1px solid #365978;
}

.equipment {
    padding: 15px;
    border-radius: 15px;
    background: #0d2035;
    border: 1px solid #294560;
    min-height: 100px;
}

.stage {
    padding: 18px;
    border-radius: 18px;
    background: #0d2035;
    border: 1px solid #294560;
    text-align: center;
}

.small {
    opacity: .78;
    font-size: .9rem;
}

.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: #173b5f;
    border: 1px solid #416789;
    margin-right: 6px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "page": "Lab",
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
        "streak": 1,
        "accuracy": 0,
    },

    "experiment_history": [],
    "research_history": [],

    "ai_requests": 0,
    "ai_cache": {},

    "puzzle_score": 0,

    "lab_started": False,
    "lab_experiment": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        if isinstance(value, dict):
            st.session_state[key] = value.copy()
        elif isinstance(value, list):
            st.session_state[key] = []
        else:
            st.session_state[key] = value


# =========================================================
# NAVIGATION
# =========================================================
PAGES = [
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


def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()


# =========================================================
# LANGUAGE
# =========================================================
def lang_label():
    return st.session_state.get("language", "English")


def roman_or_english(english, roman):
    if lang_label() == "Roman English":
        return roman
    return english


# =========================================================
# BRAIN DATA
# =========================================================
BRAIN = {
    "Prefrontal Cortex": {
        "description": (
            "Supports planning, working memory, cognitive control "
            "and goal-directed behaviour."
        ),
        "behaviour": "Planning, decision-making and inhibition.",
        "circuit": "Prefrontal cortex ↔ basal ganglia ↔ thalamus ↔ cortex",
        "emoji": "🧠",
    },

    "Hippocampus": {
        "description": (
            "Important for episodic memory formation and spatial "
            "representation."
        ),
        "behaviour": "Learning, memory and navigation.",
        "circuit": "Hippocampus ↔ entorhinal cortex ↔ cortex",
        "emoji": "🗺️",
    },

    "Amygdala": {
        "description": (
            "Processes emotionally significant information and "
            "contributes to emotional learning."
        ),
        "behaviour": "Threat processing, salience and emotional learning.",
        "circuit": "Amygdala ↔ hypothalamus ↔ brainstem/cortex",
        "emoji": "❤️",
    },

    "Striatum": {
        "description": (
            "Contributes to action selection, reward learning and habits."
        ),
        "behaviour": "Reward learning, action selection and habits.",
        "circuit": (
            "Cortex → striatum → pallidal pathways → "
            "thalamus → cortex"
        ),
        "emoji": "🎯",
    },

    "Anterior Cingulate Cortex": {
        "description": (
            "Contributes to performance monitoring, conflict processing "
            "and cognitive control."
        ),
        "behaviour": "Conflict, error processing and effort-related control.",
        "circuit": "ACC ↔ prefrontal ↔ striatal networks",
        "emoji": "⚡",
    },

    "Cerebellum": {
        "description": (
            "Supports coordination, timing and motor learning and also "
            "contributes to cognition."
        ),
        "behaviour": "Timing, balance, coordination and motor learning.",
        "circuit": "Cerebellum → deep nuclei → thalamus → cortex",
        "emoji": "⚙️",
    },
}


# =========================================================
# NEUROTRANSMITTERS
# =========================================================
NT = {
    "Dopamine": (
        "Involved in reward learning, motivation, movement and "
        "several cognitive processes."
    ),
    "Serotonin": (
        "Involved in mood-related processes, sleep, appetite and "
        "many physiological functions."
    ),
    "GABA": (
        "A major inhibitory neurotransmitter in the central nervous system."
    ),
    "Glutamate": (
        "A major excitatory neurotransmitter important for learning "
        "and plasticity."
    ),
    "Acetylcholine": (
        "Contributes to attention, learning, memory and neuromuscular "
        "communication."
    ),
}


# =========================================================
# RESEARCH BOOK
# =========================================================
BOOK = {
    "Brain & Behaviour": (
        "Behaviour emerges from interacting brain networks, body systems "
        "and environment.",
        "Cognitive neuroscience links behaviour to distributed neural systems. "
        "Correlation, causation, computational models and clinical observations "
        "must be distinguished."
    ),

    "Memory": (
        "Memory includes encoding, consolidation, retrieval and reconsolidation.",
        "Episodic, semantic, working and procedural memory involve partly "
        "distinct but interacting systems."
    ),

    "Attention": (
        "Attention changes which information receives processing priority.",
        "Attention involves selection, enhancement and suppression interacting "
        "with sensory and control networks."
    ),

    "Perception": (
        "Perception is the brain's construction of meaningful representations "
        "from sensory input.",
        "Perception reflects interactions among sensory evidence, prior "
        "knowledge, attention and context."
    ),

    "Emotion": (
        "Emotion involves interacting brain, body and cognitive processes.",
        "Contemporary models emphasize distributed networks, appraisal, "
        "interoception, learning and context."
    ),

    "Decision Making": (
        "Decisions combine goals, rewards, uncertainty, memory and control.",
        "Decision neuroscience examines valuation, learning, uncertainty, "
        "evidence accumulation and cognitive control."
    ),

    "Cognitive Control": (
        "Control helps maintain goals and adjust behaviour.",
        "Prefrontal, cingulate, parietal and striatal systems interact "
        "in task-dependent control."
    ),

    "Neuroplasticity": (
        "The nervous system can change with development, learning and experience.",
        "Plasticity includes synaptic, circuit and systems-level changes "
        "influenced by learning and context."
    ),
}


# =========================================================
# EQUIPMENT
# =========================================================
EQUIPMENT = {
    "EEG Scanner": (
        "Visual educational simulation of neural electrical activity.",
        "🧠"
    ),
    "Eye Tracker": (
        "Explores visual attention and gaze behaviour.",
        "👁️"
    ),
    "Reaction-Time Monitor": (
        "Measures response time during a cognitive task.",
        "⚡"
    ),
    "Auditory Attention Station": (
        "Explores selective attention to competing sounds.",
        "🎧"
    ),
    "Cognitive Task Screen": (
        "Displays controlled cognitive tasks and challenges.",
        "🖥️"
    ),
    "Physiological Monitor": (
        "Educational display for broad physiological signals.",
        "❤️"
    ),
}


# =========================================================
# EXPERIMENT BANK
# =========================================================
EXPERIMENTS = [
    {
        "title": "Working Memory Sprint",
        "domain": "Working Memory",
        "description": "Remember and reproduce a short sequence.",
    },
    {
        "title": "Attention Gate",
        "domain": "Attention",
        "description": "Identify the target embedded in distractors.",
    },
    {
        "title": "Decision Under Delay",
        "domain": "Decision Making",
        "description": "Explore choices involving immediate versus delayed rewards.",
    },
    {
        "title": "Inhibition Challenge",
        "domain": "Inhibitory Control",
        "description": "Respond selectively while ignoring a competing response.",
    },
    {
        "title": "Cognitive Flexibility",
        "domain": "Cognitive Flexibility",
        "description": "Switch between changing rules.",
    },
    {
        "title": "Memory Retrieval",
        "domain": "Memory",
        "description": "Retrieve information after a short delay.",
    },
]


# =========================================================
# BRAIN IMAGE
# =========================================================
@st.cache_data(show_spinner=False)
def load_brain():
    if BRAIN_PATH:
        try:
            return Image.open(BRAIN_PATH).convert("RGB")
        except Exception:
            pass
    return None


brain = load_brain()


# =========================================================
# GEMINI
# =========================================================
def get_api_key():
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):

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
    "gemini-2.5-flash"
)

AI_LIMIT = 140


def ask_ai(prompt, context="", max_tokens=450):

    st.session_state.setdefault("ai_cache", {})
    st.session_state.setdefault("ai_requests", 0)

    cache_key = hashlib.sha256(
        (prompt + "\n" + context).encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()

    if cache_key in st.session_state.ai_cache:
        return st.session_state.ai_cache[cache_key], "cache"

    if st.session_state.ai_requests >= AI_LIMIT:
        return (
            "Ayna's session AI limit has been reached. "
            "You can still use the local NEUROLENS tools.",
            "limit"
        )

    client = make_client(get_api_key())

    if client is None:
        return (
            "Ask Ayna AI is unavailable right now. "
            "Please check GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    language_instruction = (
        "Respond in Roman English."
        if lang_label() == "Roman English"
        else "Respond in clear English."
    )

    short_context = "\n".join(
        context[-4000:].splitlines()[-10:]
    )

    full_prompt = f"""
You are Ayna, the AI assistant inside NEUROLENS,
an educational cognitive neuroscience platform.

{language_instruction}

Be scientifically cautious, concise and friendly.

Rules:
- Never diagnose medical or psychiatric conditions.
- Never claim a game directly measures brain activity.
- Never claim voice mood estimates are clinical diagnoses.
- Distinguish evidence from hypotheses.
- Do not invent research citations.
- Explain neuroscience in an understandable way.

Context:
{short_context}

User task:
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

        text = getattr(response, "text", None)

        if not text:
            return (
                "Ayna returned no text. Please try again.",
                "empty"
            )

        text = text.strip()

        st.session_state.ai_cache[cache_key] = text

        return text, "ai"

    except Exception as exc:

        return (
            "Ayna could not complete that AI request right now. "
            "You can continue using the local NEUROLENS tools.",
            "error"
        )


# =========================================================
# VOICE
# =========================================================
def voice_button(text, key, language=None):

    if not text:
        return

    language = language or (
        "en-US"
        if lang_label() == "English"
        else "en-US"
    )

    safe_text = json_escape_for_js(text)

    components.html(
        f"""
        <div style="text-align:center;margin:8px 0;">
            <button
                onclick="speakAyna()"
                style="
                    padding:10px 18px;
                    border-radius:12px;
                    border:1px solid #5f7f9e;
                    background:#173b5f;
                    color:white;
                    font-size:15px;
                    cursor:pointer;
                "
            >
                🔊 Play Ayna
            </button>
        </div>

        <script>
        function speakAyna() {{
            try {{
                window.speechSynthesis.cancel();

                const utterance =
                    new SpeechSynthesisUtterance({safe_text});

                utterance.lang = "{language}";
                utterance.rate = 0.92;
                utterance.pitch = 1.04;
                utterance.volume = 1.0;

                window.speechSynthesis.speak(utterance);
            }} catch(e) {{
                console.log(e);
            }}
        }}
        </script>
        """,
        height=65,
    )


def json_escape_for_js(text):

    return (
        '"' +
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        + '"'
    )


# =========================================================
# RECORD PROGRESS
# =========================================================
def record(name, amount=1):

    if name not in st.session_state.progress:
        st.session_state.progress[name] = 0

    st.session_state.progress[name] += amount


# =========================================================
# AYNА REBOOT / WELCOME
# =========================================================
def ayna_reboot_welcome():

    st.markdown(
        """
        <div class="card">
            <h2>🤖 Meet Ayna</h2>
            <p>
            Your cognitive neuroscience lab assistant.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if AYNA_REBOOT_VIDEO:

        st.video(
            AYNA_REBOOT_VIDEO,
            autoplay=False,
            loop=True,
            muted=False,
        )

    else:

        st.info(
            "Ayna reboot video not found. "
            "Place your 3D reboot MP4 inside the assets folder."
        )

    english = (
        "Welcome to NeuroLens! I'm Ayna, your cognitive neuroscience "
        "lab assistant. Let's explore the brain, behaviour, and cognition together."
    )

    roman = (
        "Welcome to NeuroLens! Main Ayna hoon, tumhari cognitive "
        "neuroscience lab assistant. Chalo brain, behaviour aur cognition ko explore karte hain."
    )

    text = roman_or_english(english, roman)

    st.markdown(
        f"""
        <div class="card">
            <h3>👋 {text}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    voice_button(
        text,
        "ayna_reboot_voice",
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

    st.session_state.language = language

    st.divider()

    st.caption("Navigate")

    for i, page_name in enumerate(PAGES):

        label = (
            "● "
            if page_name == st.session_state.page
            else "○ "
        ) + page_name

        if st.button(
            label,
            key=f"nav_btn_{i}",
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
            st.session_state.ai_requests / AI_LIMIT,
            1.0,
        )
    )


# =========================================================
# HEADER
# =========================================================
st.markdown(
    """
    <div class="hero">
        <h1>🧠 NEUROLENS</h1>
        <p>Explore cognition, behaviour & the brain</p>
        <small>
        Interactive Cognitive Neuroscience Platform • Created by Ayna Jaffri
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LAB
# =========================================================
if st.session_state.page == "Lab":

    st.subheader("🔬 Interactive Cognitive Neuroscience Lab")

    # -----------------------------------------------------
    # Ayna welcome
    # -----------------------------------------------------
    ayna_reboot_welcome()

    st.divider()

    # -----------------------------------------------------
    # Character + equipment
    # -----------------------------------------------------
    left, right = st.columns(2)

    with left:

        st.markdown("### 👤 Choose your lab character")

        characters = [
            "Nova",
            "Mira",
            "Ray",
            "Zara",
        ]

        character = st.selectbox(
            "Character",
            characters,
            index=characters.index(
                st.session_state.character
            ),
            key="lab_character_select",
        )

        st.session_state.character = character

        st.info(
            f"🧑‍🔬 {character} is ready for the lab."
        )

    with right:

        st.markdown("### 🧪 Choose equipment")

        equipment = st.selectbox(
            "Equipment",
            list(EQUIPMENT.keys()),
            index=list(EQUIPMENT.keys()).index(
                st.session_state.equipment
            ),
            key="lab_equipment_select",
        )

        st.session_state.equipment = equipment

        emoji = EQUIPMENT[equipment][1]
        description = EQUIPMENT[equipment][0]

        st.success(
            f"{emoji} {equipment}\n\n{description}"
        )

    st.divider()

    # -----------------------------------------------------
    # Lab visual
    # -----------------------------------------------------
    if LAB_VIDEO:

        st.video(
            LAB_VIDEO,
            autoplay=False,
            loop=True,
            muted=True,
        )

    else:

        st.markdown(
            """
            <div class="lab-card">
                <h2>🧠 LIVE NEURAL ACTIVITY</h2>
                <p>
                Cognitive laboratory environment
                </p>

                <div style="
                    text-align:center;
                    font-size:75px;
                    padding:40px;
                ">
                    🧠 ⚡ 🧠
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # -----------------------------------------------------
    # Today's experiment
    # -----------------------------------------------------
    day_index = (
        time.gmtime().tm_yday - 1
    ) % len(EXPERIMENTS)

    experiment = EXPERIMENTS[day_index]

    st.markdown("### 🧪 Today's Experiment")

    st.markdown(
        f"""
        <div class="card">
            <h2>{experiment["title"]}</h2>
            <p>
            <b>Domain:</b> {experiment["domain"]}
            </p>
            <p>
            {experiment["description"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🚀 Enter Lab & Start Experiment",
        use_container_width=True,
        key="enter_lab_experiment",
    ):

        st.session_state.lab_started = True
        st.session_state.lab_experiment = experiment
        go_to("Brain Exercises")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button(
            "🧠 Brain Journey",
            use_container_width=True,
            key="lab_brain_journey",
        ):
            st.session_state.journey_stage = "brain"
            go_to("Explore Brain")

    with c2:
        if st.button(
            "🧩 Puzzle",
            use_container_width=True,
            key="lab_puzzle",
        ):
            go_to("Brain Puzzle")

    with c3:
        if st.button(
            "🎯 Mood & Behaviour",
            use_container_width=True,
            key="lab_mood",
        ):
            go_to("AI Mood & Behaviour")

    with c4:
        if st.button(
            "💬 Ask Ayna",
            use_container_width=True,
            key="lab_ask",
        ):
            go_to("Ask Ayna")


# =========================================================
# EXPLORE BRAIN
# =========================================================
elif st.session_state.page == "Explore Brain":

    st.subheader("🧠 Brain Journey")

    stages = [
        ("brain", "Whole Brain"),
        ("region", "Brain Region"),
        ("circuit", "Neural Circuit"),
        ("neuron", "Neuron"),
        ("dendrites", "Dendrites"),
        ("axon", "Axon"),
        ("myelin", "Myelin"),
        ("signal", "Electrical Signal"),
        ("synapse", "Synapse"),
        ("nt", "Neurotransmitter"),
        ("function", "Cognition & Behaviour"),
    ]

    current = st.session_state.journey_stage

    st.markdown(
        " → ".join(
            name for _, name in stages
        )
    )

    st.divider()

    # -----------------------------------------------------
    # WHOLE BRAIN
    # -----------------------------------------------------
    if current == "brain":

        st.markdown("## 🧠 Whole Brain")

        if JOURNEY_VIDEO:

            st.video(
                JOURNEY_VIDEO,
                autoplay=False,
                loop=True,
                muted=True,
            )

        elif brain:

            st.image(
                brain,
                use_container_width=True,
            )

        else:

            st.warning(
                "brain.png or brain_animation.mp4 not found."
            )

        region = st.selectbox(
            "Choose a brain region",
            list(BRAIN.keys()),
            index=list(BRAIN.keys()).index(
                st.session_state.journey_region
            ),
            key="journey_region_choice",
        )

        if st.button(
            "🚀 Enter this region",
            use_container_width=True,
            key="journey_enter_region",
        ):

            st.session_state.journey_region = region
            st.session_state.journey_stage = "region"
            st.rerun()

    # -----------------------------------------------------
    # REGION
    # -----------------------------------------------------
    elif current == "region":

        region = st.session_state.journey_region
        info = BRAIN[region]

        st.markdown(
            f"## {info['emoji']} {region}"
        )

        a, b = st.columns(2)

        with a:

            st.info(info["description"])

            st.markdown(
                f"**Behavioural relevance:** "
                f"{info['behaviour']}"
            )

        with b:

            st.markdown("### 🔗 Network / Circuit")

            st.code(
                info["circuit"]
            )

        text = roman_or_english(
            f"Welcome inside the {region}. "
            f"This system contributes to cognition and behaviour.",
            f"{region} ke andar welcome. "
            f"Yeh system cognition aur behaviour mein contribute karta hai."
        )

        voice_button(
            text,
            "region_voice",
        )

        if st.button(
            "🔗 Explore neural circuit",
            use_container_width=True,
            key="region_to_circuit",
        ):

            st.session_state.journey_stage = "circuit"
            st.rerun()

        if st.button(
            "🔙 Back to whole brain",
            use_container_width=True,
            key="region_back",
        ):

            st.session_state.journey_stage = "brain"
            st.rerun()

    # -----------------------------------------------------
    # CIRCUIT
    # -----------------------------------------------------
    elif current == "circuit":

        region = st.session_state.journey_region
        info = BRAIN[region]

        st.markdown(
            f"## 🔗 {region} Circuit"
        )

        st.markdown(
            f"""
            <div class="stage">
                <h2>🧠 Cortex</h2>
                <h2>↓</h2>
                <h2>🟣 Striatum</h2>
                <h2>↓</h2>
                <h2>⚙️ Pallidal / Subthalamic Network</h2>
                <h2>↓</h2>
                <h2>🔵 Thalamus</h2>
                <h2>↓</h2>
                <h2>🧠 Cortex</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.code(
            info["circuit"]
        )

        voice_button(
            "Now we are following information through a neural circuit.",
            "circuit_voice",
        )

        if st.button(
            "🧬 Enter neuron",
            use_container_width=True,
            key="circuit_neuron",
        ):

            st.session_state.journey_stage = "neuron"
            st.rerun()

    # -----------------------------------------------------
    # NEURON
    # -----------------------------------------------------
    elif current == "neuron":

        st.markdown("## 🧬 Neuron")

        st.markdown(
            """
            <div class="stage">
                🌿 Dendrites
                <br>↓
                🟣 Cell Body / Soma
                <br>↓
                ⚡ Axon
                <br>↓
                🔵 Axon Terminal
            </div>
            """,
            unsafe_allow_html=True,
        )

        part = st.selectbox(
            "Explore neuron structure",
            [
                "Dendrites",
                "Cell Body",
                "Axon",
                "Axon Terminal",
            ],
            key="neuron_part",
        )

        descriptions = {
            "Dendrites":
                "Dendrites receive many synaptic inputs.",
            "Cell Body":
                "The soma supports cellular metabolism and contains the nucleus.",
            "Axon":
                "The axon conducts electrical signals toward terminals.",
            "Axon Terminal":
                "Axon terminals participate in communication with other cells.",
        }

        st.info(
            descriptions[part]
        )

        voice_button(
            descriptions[part],
            "neuron_voice",
        )

        if st.button(
            "🌿 Explore dendrites",
            use_container_width=True,
            key="neuron_dendrites",
        ):

            st.session_state.journey_stage = "dendrites"
            st.rerun()

    # -----------------------------------------------------
    # DENDRITES
    # -----------------------------------------------------
    elif current == "dendrites":

        st.markdown("## 🌿 Dendrites")

        st.markdown(
            """
            <div class="stage">
                🌿 ─── 🌿 ─── 🌿
                <br>
                ↓
                <br>
                🟣
                <br>
                Dendritic branches receive inputs
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "Dendrites are specialized neuronal structures "
            "that receive synaptic inputs."
        )

        if st.button(
            "⚡ Follow the axon",
            use_container_width=True,
            key="dendrites_axon",
        ):

            st.session_state.journey_stage = "axon"
            st.rerun()

    # -----------------------------------------------------
    # AXON
    # -----------------------------------------------------
    elif current == "axon":

        st.markdown("## ⚡ Axon")

        components.html(
            """
            <div style="
                height:160px;
                border-radius:20px;
                background:#eef4fb;
                position:relative;
                overflow:hidden;
            ">

                <div style="
                    position:absolute;
                    top:70px;
                    left:5%;
                    right:5%;
                    height:15px;
                    background:#8c6a4d;
                    border-radius:20px;
                "></div>

                <div style="
                    position:absolute;
                    top:35px;
                    left:5%;
                    font-size:35px;
                    animation:moveSignal 3s linear infinite;
                ">
                    ⚡
                </div>

            </div>

            <style>
            @keyframes moveSignal {
                from { left:5%; }
                to { left:88%; }
            }
            </style>
            """,
            height=180,
        )

        st.info(
            "The axon conducts electrical signals toward the axon terminals."
        )

        if st.button(
            "🛡️ Explore myelin",
            use_container_width=True,
            key="axon_myelin",
        ):

            st.session_state.journey_stage = "myelin"
            st.rerun()

    # -----------------------------------------------------
    # MYELIN
    # -----------------------------------------------------
    elif current == "myelin":

        st.markdown("## 🛡️ Myelin")

        st.markdown(
            """
            <div class="stage">
                🟡 🟡 🟡
                <br>
                ═══════════════
                <br>
                ⚡ AXON ⚡
                <br>
                ═══════════════
                <br>
                🟡 🟡 🟡
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "Myelin insulates many axons and supports rapid "
            "saltatory conduction."
        )

        if st.button(
            "⚡ Follow electrical signal",
            use_container_width=True,
            key="myelin_signal",
        ):

            st.session_state.journey_stage = "signal"
            st.rerun()

    # -----------------------------------------------------
    # ELECTRICAL SIGNAL
    # -----------------------------------------------------
    elif current == "signal":

        st.markdown("## ⚡ Electrical Signal")

        components.html(
            """
            <div style="
                height:130px;
                border-radius:20px;
                background:#071522;
                position:relative;
                overflow:hidden;
            ">

            <div style="
                position:absolute;
                top:55px;
                left:5%;
                right:5%;
                height:4px;
                background:#65cfff;
            "></div>

            <div style="
                position:absolute;
                top:28px;
                left:5%;
                font-size:35px;
                animation:signalMove 2s linear infinite;
            ">
            ⚡
            </div>

            </div>

            <style>
            @keyframes signalMove {
                from { left:5%; }
                to { left:88%; }
            }
            </style>
            """,
            height=150,
        )

        st.info(
            "Electrical activity along an axon can carry information "
            "toward synaptic terminals."
        )

        if st.button(
            "🔗 Enter synapse",
            use_container_width=True,
            key="signal_synapse",
        ):

            st.session_state.journey_stage = "synapse"
            st.rerun()

    # -----------------------------------------------------
    # SYNAPSE
    # -----------------------------------------------------
    elif current == "synapse":

        st.markdown("## 🔗 Synapse")

        st.markdown(
            """
            <div class="stage">
                🟣 Sending neuron
                <br>
                • • • • •
                <br>
                🔵 Receiving neuron
            </div>
            """,
            unsafe_allow_html=True,
        )

        synapse_part = st.selectbox(
            "Explore",
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
                "The sending side of a chemical synapse.",
            "Synaptic Vesicles":
                "Vesicles store neurotransmitters before release.",
            "Synaptic Cleft":
                "The extracellular space between communicating cells.",
            "Postsynaptic Membrane":
                "The receiving membrane contains signaling machinery.",
            "Receptors":
                "Receptors detect signaling molecules.",
        }

        st.info(
            synapse_info[synapse_part]
        )

        if st.button(
            "🧪 Follow neurotransmitter",
            use_container_width=True,
            key="synapse_nt",
        ):

            st.session_state.journey_stage = "nt"
            st.rerun()

    # -----------------------------------------------------
    # NEUROTRANSMITTER
    # -----------------------------------------------------
    elif current == "nt":

        st.markdown("## 🧪 Neurotransmitter Explorer")

        neurotransmitter = st.selectbox(
            "Choose neurotransmitter",
            list(NT.keys()),
            key="journey_nt_select",
        )

        st.success(
            NT[neurotransmitter]
        )

        components.html(
            """
            <div style="
                text-align:center;
                font-size:42px;
                padding:25px;
                animation:ntPulse 1.5s infinite;
            ">
                🟣 🟣 🟣 🟣 🟣
            </div>

            <style>
            @keyframes ntPulse {
                50% { transform:scale(1.15); }
            }
            </style>
            """,
            height=110,
        )

        if st.button(
            "🧠 Connect to cognition & behaviour",
            use_container_width=True,
            key="nt_function",
        ):

            st.session_state.journey_stage = "function"
            st.rerun()

    # -----------------------------------------------------
    # FUNCTION
    # -----------------------------------------------------
    elif current == "function":

        st.markdown(
            "## 🧠 Cognition & Behaviour"
        )

        st.markdown(
            """
            <div class="stage">

            🧠 Neural systems

            ↓

            ⚡ Neural signalling

            ↓

            🔗 Networks and circuits

            ↓

            🧩 Cognitive processes

            ↓

            🎯 Behaviour

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "Cognitive neuroscience studies how neural systems "
            "interact with cognition and behaviour. Behaviour is "
            "not explained by one brain region alone."
        )

        voice_button(
            "Cognitive neuroscience connects neural systems with cognition and behaviour.",
            "function_voice",
        )

        if st.button(
            "🏠 Restart Brain Journey",
            use_container_width=True,
            key="restart_brain",
        ):

            st.session_state.journey_stage = "brain"
            st.rerun()

    st.divider()

    # -----------------------------------------------------
    # CONTEXTUAL ASK AYNA
    # -----------------------------------------------------
    st.markdown(
        "### 💬 Ask Ayna about this stage"
    )

    stage_question = st.text_input(
        "Question",
        placeholder="Ask about what you are seeing...",
        key="journey_question",
    )

    if st.button(
        "Ask Ayna",
        key="journey_ask",
    ) and stage_question:

        answer, source = ask_ai(
            stage_question,
            f"""
            Current brain journey stage: {current}
            Current region: {st.session_state.journey_region}
            """,
        )

        st.write(answer)
        st.caption(source)

        voice_button(
            answer,
            "journey_answer_voice",
        )


# =========================================================
# BRAIN PUZZLE
# =========================================================
elif st.session_state.page == "Brain Puzzle":

    st.subheader("🧩 Brain Picture Puzzle")

    st.caption(
        "Drag pieces with your finger or mouse. "
        "Drop them onto another slot to rearrange them."
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

        N = int(difficulty[0])

        buffer = BytesIO()

        brain.save(
            buffer,
            format="PNG",
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode()

        puzzle_html = f"""
        <div
            id="puzzle-root"
            style="font-family:Arial,sans-serif;"
        >

            <div style="
                display:flex;
                gap:10px;
                flex-wrap:wrap;
                align-items:center;
                margin-bottom:12px;
            ">

                <button
                    id="newPuzzle"
                    style="
                        padding:10px 14px;
                        border-radius:10px;
                        border:1px solid #789;
                        cursor:pointer;
                    "
                >
                    🔀 New Puzzle
                </button>

                <span id="stats"></span>

            </div>

            <div id="board"></div>

            <h3 id="message"></h3>

        </div>

        <style>

        #board {{
            display:grid;
            grid-template-columns:repeat({N}, 1fr);
            gap:6px;
            max-width:900px;
            margin:12px auto;
        }}

        .slot {{
            aspect-ratio:1;
            border:2px dashed #8298ae;
            border-radius:10px;
            overflow:hidden;
            background:#102235;
        }}

        .piece {{
            width:100%;
            height:100%;
            background-image:url(
                data:image/png;base64,{encoded}
            );
            background-size:{N * 100}% {N * 100}%;
            cursor:grab;
            touch-action:none;
            border-radius:8px;
        }}

        .correct {{
            outline:3px solid #54d18a;
            cursor:default;
        }}

        </style>

        <script>

        (() => {{

            const N = {N};

            const board =
                document.getElementById("board");

            const stats =
                document.getElementById("stats");

            const message =
                document.getElementById("message");

            let moves = 0;
            let startTime = Date.now();
            let dragging = null;

            function shuffle(array) {{

                for (
                    let i = array.length - 1;
                    i > 0;
                    i--
                ) {{

                    const j =
                        Math.floor(
                            Math.random() * (i + 1)
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

                const pieces =
                    [
                        ...document.querySelectorAll(
                            ".piece"
                        )
                    ];

                const correct =
                    pieces.filter(
                        p =>
                            Number(p.dataset.id) ===
                            Number(
                                p.parentElement.dataset.slot
                            )
                    ).length;

                const seconds =
                    Math.floor(
                        (Date.now() - startTime) / 1000
                    );

                stats.textContent =
                    "Moves: " + moves +
                    " • Correct: " +
                    correct +
                    "/" + (N * N) +
                    " • Time: " +
                    seconds + "s";

                if (correct === N * N) {{

                    message.textContent =
                        "🎉 Puzzle solved!";

                }} else {{

                    message.textContent = "";

                }}

            }}

            function setup() {{

                board.innerHTML = "";

                message.textContent = "";

                moves = 0;

                startTime = Date.now();

                const order =
                    [...Array(N * N).keys()];

                shuffle(order);

                order.forEach(id => {{

                    const slot =
                        document.createElement("div");

                    slot.className = "slot";

                    slot.dataset.slot = id;

                    const piece =
                        document.createElement("div");

                    piece.className = "piece";

                    piece.dataset.id = id;

                    const row =
                        Math.floor(id / N);

                    const col =
                        id % N;

                    const x =
                        N === 1
                        ? 0
                        : (col / (N - 1)) * 100;

                    const y =
                        N === 1
                        ? 0
                        : (row / (N - 1)) * 100;

                    piece.style.backgroundPosition =
                        x + "% " + y + "%";

                    piece.addEventListener(
                        "pointerdown",
                        event => {{

                            if (
                                piece.classList.contains(
                                    "correct"
                                )
                            ) {{
                                return;
                            }}

                            dragging = piece;

                            try {{
                                piece.setPointerCapture(
                                    event.pointerId
                                );
                            }} catch(e) {{}}

                        }}
                    );

                    piece.addEventListener(
                        "pointerup",
                        event => {{

                            if (!dragging) {{
                                return;
                            }}

                            const target =
                                document.elementFromPoint(
                                    event.clientX,
                                    event.clientY
                                );

                            const targetSlot =
                                target
                                ? target.closest(".slot")
                                : null;

                            if (targetSlot) {{

                                const other =
                                    targetSlot.querySelector(
                                        ".piece"
                                    );

                                const oldParent =
                                    piece.parentElement;

                                if (
                                    other &&
                                    other !== piece
                                ) {{

                                    oldParent.appendChild(
                                        other
                                    );

                                }}

                                targetSlot.appendChild(
                                    piece
                                );

                                moves++;

                                document
                                    .querySelectorAll(
                                        ".piece"
                                    )
                                    .forEach(p => {{

                                        const isCorrect =
                                            Number(
                                                p.dataset.id
                                            ) ===
                                            Number(
                                                p.parentElement
                                                    .dataset.slot
                                            );

                                        p.classList.toggle(
                                            "correct",
                                            isCorrect
                                        );

                                    }});

                                update();

                            }}

                            dragging = null;

                        }}
                    );

                    slot.appendChild(piece);

                    board.appendChild(slot);

                }});

                update();

            }}

            document
                .getElementById("newPuzzle")
                .addEventListener(
                    "click",
                    setup
                );

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
            "✅ Record Puzzle Activity",
            key="record_puzzle_activity",
        ):

            record("puzzles")

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
        roman_or_english(
            "Speak naturally to Ayna or type a message. "
            "The result is a broad conversational estimate, "
            "not a clinical diagnosis.",
            "Ayna se naturally baat karo ya text likho. "
            "Result sirf broad conversational estimate hai, "
            "clinical diagnosis nahi."
        )
    )

    st.info(
        "⚠️ Voice and text estimates do not directly measure brain activity "
        "and should not be treated as medical or psychiatric diagnoses."
    )

    tab_voice, tab_text = st.tabs(
        [
            "🎙️ Voice",
            "⌨️ Text",
        ]
    )

    # -----------------------------------------------------
    # VOICE
    # -----------------------------------------------------
    with tab_voice:

        audio = None

        try:

            audio = st.audio_input(
                "🎙️ Record your voice",
                key="mood_voice_input",
            )

        except Exception:

            st.warning(
                "Voice recording is not available in this browser."
            )

        context = st.text_input(
            "Optional context",
            placeholder="Anything you want Ayna to consider?",
            key="mood_context",
        )

        if st.button(
            "🧠 Send Voice to Ayna",
            use_container_width=True,
            key="send_mood_voice",
        ):

            if not audio:

                st.warning(
                    "Please record a voice sample first."
                )

            else:

                client = make_client(
                    get_api_key()
                )

                if client is None:

                    st.error(
                        "Gemini AI is unavailable. "
                        "Check GEMINI_API_KEY in Streamlit Secrets."
                    )

                elif st.session_state.ai_requests >= AI_LIMIT:

                    st.warning(
                        "AI session limit reached."
                    )

                else:

                    try:

                        st.session_state.ai_requests += 1

                        prompt = f"""
Analyze this voice sample only for broad conversational affect.

Return:
1. Primary mood from:
Positive, Calm, Neutral, Worried, Low, Frustrated, Tired

2. Optional secondary signal.

3. Confidence:
Low, Medium or High.

4. One short friendly explanation.

Do not diagnose.
Do not infer sensitive traits.
Do not claim certainty.
Context:
{context[:500]}
"""

                        response = client.models.generate_content(
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

                        result = (
                            getattr(
                                response,
                                "text",
                                None
                            )
                            or "No result returned."
                        )

                        st.success(
                            "😊 Ayna's broad estimate"
                        )

                        st.write(result)

                        voice_button(
                            result,
                            "mood_voice_result",
                        )

                    except Exception:

                        st.error(
                            "Voice analysis is temporarily unavailable. "
                            "You can still use the Text tab."
                        )

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------
    with tab_text:

        text = st.text_area(
            "Tell Ayna how you feel",
            height=140,
            placeholder=(
                "Example: I feel tired and distracted today..."
            ),
            key="mood_text",
        )

        if st.button(
            "✨ Send Text to Ayna",
            use_container_width=True,
            key="send_mood_text",
        ):

            if not text.strip():

                st.warning(
                    "Please write something first."
                )

            else:

                prompt = f"""
Give:
- one suitable emoji
- primary broad mood
- optional secondary signal
- one friendly sentence

User text:
{text}
"""

                answer, source = ask_ai(
                    prompt,
                    max_tokens=220,
                )

                st.info(answer)

                st.caption(source)

                voice_button(
                    answer,
                    "mood_text_result",
                )


# =========================================================
# BRAIN EXERCISES
# =========================================================
elif st.session_state.page == "Brain Exercises":

    st.subheader(
        "🧪 Cognitive Neuroscience Experiment"
    )

    experiment = st.session_state.get(
        "lab_experiment"
    )

    if experiment is None:

        index = (
            time.gmtime().tm_yday - 1
        ) % len(EXPERIMENTS)

        experiment = EXPERIMENTS[index]

    title = experiment["title"]
    domain = experiment["domain"]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {domain}"
    )

    st.markdown(
        f"""
        <div class="card">
            <b>Educational experiment:</b>
            This task demonstrates a cognitive process.
            It is not a diagnostic test and does not directly
            measure brain activity.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # WORKING MEMORY
    # -----------------------------------------------------
    if domain
