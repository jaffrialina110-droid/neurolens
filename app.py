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

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

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
    layout="wide"
)


# =========================================================
# PATHS / ASSETS
# =========================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset_path(name):
    p = os.path.join(ASSETS, name)

    if os.path.exists(p):
        return p

    return os.path.join(ROOT, name)


def find_video(*names, keywords=()):
    for name in names:
        p = asset_path(name)

        if os.path.exists(p):
            return p

    for folder in (ASSETS, ROOT):

        if not os.path.isdir(folder):
            continue

        for name in os.listdir(folder):

            low = name.lower()

            if (
                low.endswith((".mp4", ".webm", ".mov"))
                and any(k in low for k in keywords)
            ):
                return os.path.join(folder, name)

    return None


BRAIN_PATH = asset_path("brain.png")

JOURNEY_VIDEO = find_video(
    "brain_animation.mp4",
    keywords=("brain", "journey")
)

LAB_VIDEO = find_video(
    "cognitive_lab_brain.mp4",
    keywords=("lab", "cognitive")
)

# Voiced reboot video first
REBOOT_VIDEO = find_video(
    "ayna_reboot_voiced.mp4",
    "ayna_reboot.mp4",
    "ayna_welcome.mp4",
    "reboot.mp4",
    "welcome.mp4",
    keywords=("ayna", "reboot", "welcome")
)


# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(
            circle at 15% 5%,
            #183c63,
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #06101d,
            #0b1b2d
        );
}

.block-container {
    max-width: 1400px;
    padding-top: 1rem;
}

.hero {
    padding: 28px;
    border-radius: 24px;
    background:
        linear-gradient(
            135deg,
            #122c49,
            #111a32
        );
    border: 1px solid #45617d;
    margin-bottom: 18px;
}

.card {
    padding: 18px;
    border-radius: 18px;
    background: #0d2035;
    border: 1px solid #294560;
    margin: 8px 0;
}

.lab {
    min-height: 320px;
    border-radius: 24px;
    position: relative;
    overflow: hidden;

    background:
        radial-gradient(
            circle,
            #285b88 0,
            #0b1930 28%,
            #07111f 72%
        );

    border: 1px solid #36536d;
}

.orb {
    position: absolute;
    width: 92px;
    height: 92px;

    border-radius: 50%;

    left: calc(50% - 46px);
    top: calc(50% - 46px);

    background:
        radial-gradient(
            circle,
            #fff,
            #8ed1ff 20%,
            #536bff 55%,
            #342a7d
        );

    box-shadow: 0 0 45px #71bfff;

    animation: pulse 2.3s infinite;
}

@keyframes pulse {

    50% {
        transform: scale(1.1);
    }

}

.small {
    opacity: .78;
    font-size: .9rem;
}

.stage {
    height: 210px;
    border-radius: 22px;

    background:
        radial-gradient(
            circle,
            #153d63,
            #081321
        );

    border: 1px solid #38536e;

    display: flex;
    align-items: center;
    justify-content: center;

    overflow: hidden;
}

.neuron {
    font-size: 5rem;
    animation: pulse 1.5s infinite;
}

.signal {
    font-size: 3rem;
    animation: signalMove 2s linear infinite;
}

@keyframes signalMove {

    0% {
        transform: translateX(-170px);
    }

    100% {
        transform: translateX(170px);
    }

}

.syn {
    font-size: 3rem;
    animation: pulse .9s infinite;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

def fresh_progress():

    return {
        "experiments": 0,
        "puzzles": 0,
        "games": 0,
        "research": 0,
        "streak": 1,
        "accuracy": 0,
        "reaction_time": None
    }


defaults = {

    "page": "Welcome Reboot",

    "language": "English",

    "character": "Nova",

    "equipment": "EEG Scanner",

    "journey_stage": "brain",

    "journey_region": "Prefrontal Cortex",

    "messages": [],

    "private_messages": [],

    "private_unlocked": False,

    # NEW:
    # User-created PIN is stored only as a hash
    "private_pin_hash": None,

    "progress": fresh_progress(),

    "ai_requests": 0,

    "ai_cache": {},

    "last_experiment": None,

    "experiment_history": [],

    "puzzle_history": [],

    "research_history": [],

    "research_results": [],

    "lab_started": False,

    "active_lab_experiment": None,

    "lab_result": None,

    "inhib_word": None
}


for key, value in defaults.items():

    if key not in st.session_state:

        if isinstance(value, dict):
            st.session_state[key] = value.copy()

        elif isinstance(value, list):
            st.session_state[key] = value.copy()

        else:
            st.session_state[key] = value


# =========================================================
# NAVIGATION
# =========================================================

PAGES = [

    "Welcome Reboot",

    "Lab",

    "Explore Brain",

    "Brain Puzzle",

    "AI Mood & Behaviour",

    "Brain Exercises",

    # NEW DEDICATED PAGE
    "Daily Cognitive Experiment",

    "Research Book",

    "Ask Ayna",

    "Private Ask Ayna",

    "My Progress"
]


# =========================================================
# BRAIN DATABASE
# =========================================================

BRAIN = {

    "Prefrontal Cortex": (
        "Supports planning, working memory, cognitive control "
        "and goal-directed behaviour.",
        "Planning, decision-making and inhibition.",
        "Prefrontal cortex ↔ basal ganglia ↔ thalamus ↔ cortex"
    ),

    "Hippocampus": (
        "Important for episodic memory formation "
        "and spatial representation.",
        "Learning, memory and navigation.",
        "Hippocampus ↔ entorhinal cortex ↔ cortex"
    ),

    "Amygdala": (
        "Processes emotionally significant information "
        "and contributes to emotional learning.",
        "Threat processing, salience and emotional learning.",
        "Amygdala ↔ hypothalamus ↔ brainstem/cortex"
    ),

    "Striatum": (
        "Contributes to action selection, reward learning "
        "and habits.",
        "Reward learning, action selection and habits.",
        "Cortex → striatum → pallidal pathways → thalamus → cortex"
    ),

    "Anterior Cingulate Cortex": (
        "Contributes to performance monitoring, "
        "conflict processing and control.",
        "Conflict, error processing and effort-related control.",
        "ACC ↔ prefrontal ↔ striatal networks"
    ),

    "Cerebellum": (
        "Supports coordination, timing and motor learning "
        "and also contributes to cognition.",
        "Timing, balance, coordination and motor learning.",
        "Cerebellum → deep nuclei → thalamus → cortex"
    )
}


# =========================================================
# NEUROTRANSMITTERS
# =========================================================

NT = {

    "Dopamine":
        "Involved in reward learning, motivation, movement "
        "and several cognitive processes.",

    "Serotonin":
        "Involved in mood-related processes, sleep, appetite "
        "and many physiological functions.",

    "GABA":
        "A major inhibitory neurotransmitter "
        "in the central nervous system.",

    "Glutamate":
        "A major excitatory neurotransmitter important "
        "for learning and plasticity.",

    "Acetylcholine":
        "Contributes to attention, learning, memory "
        "and neuromuscular communication."
}


# =========================================================
# RESEARCH BOOK TOPICS
# =========================================================

BOOK = {

    "Brain & Behaviour": (
        "Behaviour emerges from interacting brain networks, "
        "body systems and environment.",

        "Cognitive neuroscience links behaviour to distributed "
        "neural systems. Separate correlation, causation, "
        "computational models and clinical observations."
    ),

    "Memory": (
        "Memory includes encoding, consolidation, "
        "retrieval and reconsolidation.",

        "Episodic, semantic, working and procedural memory "
        "involve partly distinct but interacting systems."
    ),

    "Attention": (
        "Attention changes which information receives "
        "processing priority.",

        "Attention involves selection, enhancement and "
        "suppression interacting with sensory and control networks."
    ),

    "Perception": (
        "Perception is the brain's construction of meaningful "
        "representations from sensory input.",

        "Perception reflects interactions among sensory evidence, "
        "prior knowledge, attention and context."
    ),

    "Emotion": (
        "Emotion involves interacting brain, body "
        "and cognitive processes.",

        "Contemporary models emphasize distributed networks, "
        "appraisal, interoception, learning and context."
    ),

    "Decision Making": (
        "Decisions combine goals, rewards, uncertainty, "
        "memory and control.",

        "Decision neuroscience examines valuation, learning, "
        "uncertainty, evidence accumulation and cognitive control."
    ),

    "Cognitive Control": (
        "Control helps maintain goals and adjust behaviour.",

        "Prefrontal, cingulate, parietal and striatal systems "
        "interact in task-dependent control."
    ),

    "Neuroplasticity": (
        "The nervous system can change with development, "
        "learning and experience.",

        "Plasticity includes synaptic, circuit and systems-level "
        "changes influenced by learning and context."
    )
}


# =========================================================
# LAB EQUIPMENT
# =========================================================

EQUIPMENT = {

    "EEG Scanner":
        "Illustrates measurement of electrical activity at "
        "the scalp; educational simulation only.",

    "Eye Tracker":
        "Illustrates measurement of gaze position "
        "and fixation patterns.",

    "Reaction-Time Monitor":
        "Measures response latency in a simple cognitive task.",

    "Auditory Attention Station":
        "Presents competing sounds to explore selective attention.",

    "Cognitive Task Screen":
        "Runs structured memory, attention and decision tasks.",

    "Physiological Monitor":
        "Illustrates non-neural physiological signals such as "
        "pulse or skin conductance; not a diagnosis."
}


# =========================================================
# EXPERIMENT BANK
# =========================================================

EXPERIMENTS = [

    ("Attention Gate", "Attention"),

    ("Working Memory Sprint", "Working Memory"),

    ("Decision Under Delay", "Decision Making"),

    ("Inhibition Challenge", "Inhibitory Control"),

    ("Cognitive Flexibility", "Cognitive Flexibility"),

    ("Memory Retrieval", "Memory")
]


MOODS = {

    "Positive": "😊",

    "Calm": "😌",

    "Neutral": "😐",

    "Worried": "😟",

    "Low": "😔",

    "Frustrated": "😤",

    "Tired": "😴"
}


# =========================================================
# LOAD BRAIN IMAGE
# =========================================================

@st.cache_data(show_spinner=False)
def load_brain():

    try:

        if os.path.exists(BRAIN_PATH):

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
def make_client(key):

    if genai is None or not key:
        return None

    try:
        return genai.Client(api_key=key)

    except Exception:
        return None


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

AI_LIMIT = 140


def ask_ai(prompt, context="", max_tokens=450):

    cache_key = hashlib.sha256(
        (prompt + "\n" + context)
        .encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()


    if cache_key in st.session_state.ai_cache:

        return (
            st.session_state.ai_cache[cache_key],
            "cache"
        )


    if st.session_state.ai_requests >= AI_LIMIT:

        return (
            "AI session limit reached. "
            "Local NEUROLENS activities are still available.",
            "limit"
        )


    client = make_client(get_api_key())


    if client is None:

        return (
            "Ask Ayna is unavailable. "
            "Add GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )


    prompt = f"""
You are Ayna, the AI assistant inside NEUROLENS,
an educational cognitive neuroscience platform.

Be accurate, concise, friendly and scientifically cautious.

Never diagnose a medical or psychiatric condition.

Do not claim that games, voice estimates or self-report
scores directly measure brain activity.

Distinguish evidence from hypotheses.

Language preference may be English or Roman English.

Avoid pretending to be a doctor or therapist.

Context:
{context[-4500:]}

Task:
{prompt}
"""


    try:

        st.session_state.ai_requests += 1

        if types:

            config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_tokens
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=config
            )

        else:

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )


        text = (
            getattr(response, "text", None)
            or "Ayna returned no text."
        ).strip()


        st.session_state.ai_cache[cache_key] = text

        return text, "ai"
    except Exception:

        return (
            "Ayna could not complete that request right now. "
            "You can continue with the local tools.",
            "error"
        )
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

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

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
    layout="wide"
)


# =========================================================
# PATHS / ASSETS
# =========================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset_path(name):
    p = os.path.join(ASSETS, name)

    if os.path.exists(p):
        return p

    return os.path.join(ROOT, name)


def find_video(*names, keywords=()):
    for name in names:
        p = asset_path(name)

        if os.path.exists(p):
            return p

    for folder in (ASSETS, ROOT):

        if not os.path.isdir(folder):
            continue

        for name in os.listdir(folder):

            low = name.lower()

            if (
                low.endswith((".mp4", ".webm", ".mov"))
                and any(k in low for k in keywords)
            ):
                return os.path.join(folder, name)

    return None


BRAIN_PATH = asset_path("brain.png")

JOURNEY_VIDEO = find_video(
    "brain_animation.mp4",
    keywords=("brain", "journey")
)

LAB_VIDEO = find_video(
    "cognitive_lab_brain.mp4",
    keywords=("lab", "cognitive")
)

# Voiced reboot video first
REBOOT_VIDEO = find_video(
    "ayna_reboot_voiced.mp4",
    "ayna_reboot.mp4",
    "ayna_welcome.mp4",
    "reboot.mp4",
    "welcome.mp4",
    keywords=("ayna", "reboot", "welcome")
)


# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(
            circle at 15% 5%,
            #183c63,
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #06101d,
            #0b1b2d
        );
}

.block-container {
    max-width: 1400px;
    padding-top: 1rem;
}

.hero {
    padding: 28px;
    border-radius: 24px;
    background:
        linear-gradient(
            135deg,
            #122c49,
            #111a32
        );
    border: 1px solid #45617d;
    margin-bottom: 18px;
}

.card {
    padding: 18px;
    border-radius: 18px;
    background: #0d2035;
    border: 1px solid #294560;
    margin: 8px 0;
}

.lab {
    min-height: 320px;
    border-radius: 24px;
    position: relative;
    overflow: hidden;

    background:
        radial-gradient(
            circle,
            #285b88 0,
            #0b1930 28%,
            #07111f 72%
        );

    border: 1px solid #36536d;
}

.orb {
    position: absolute;
    width: 92px;
    height: 92px;

    border-radius: 50%;

    left: calc(50% - 46px);
    top: calc(50% - 46px);

    background:
        radial-gradient(
            circle,
            #fff,
            #8ed1ff 20%,
            #536bff 55%,
            #342a7d
        );

    box-shadow: 0 0 45px #71bfff;

    animation: pulse 2.3s infinite;
}

@keyframes pulse {

    50% {
        transform: scale(1.1);
    }

}

.small {
    opacity: .78;
    font-size: .9rem;
}

.stage {
    height: 210px;
    border-radius: 22px;

    background:
        radial-gradient(
            circle,
            #153d63,
            #081321
        );

    border: 1px solid #38536e;

    display: flex;
    align-items: center;
    justify-content: center;

    overflow: hidden;
}

.neuron {
    font-size: 5rem;
    animation: pulse 1.5s infinite;
}

.signal {
    font-size: 3rem;
    animation: signalMove 2s linear infinite;
}

@keyframes signalMove {

    0% {
        transform: translateX(-170px);
    }

    100% {
        transform: translateX(170px);
    }

}

.syn {
    font-size: 3rem;
    animation: pulse .9s infinite;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

def fresh_progress():

    return {
        "experiments": 0,
        "puzzles": 0,
        "games": 0,
        "research": 0,
        "streak": 1,
        "accuracy": 0,
        "reaction_time": None
    }


defaults = {

    "page": "Welcome Reboot",

    "language": "English",

    "character": "Nova",

    "equipment": "EEG Scanner",

    "journey_stage": "brain",

    "journey_region": "Prefrontal Cortex",

    "messages": [],

    "private_messages": [],

    "private_unlocked": False,

    # NEW:
    # User-created PIN is stored only as a hash
    "private_pin_hash": None,

    "progress": fresh_progress(),

    "ai_requests": 0,

    "ai_cache": {},

    "last_experiment": None,

    "experiment_history": [],

    "puzzle_history": [],

    "research_history": [],

    "research_results": [],

    "lab_started": False,

    "active_lab_experiment": None,

    "lab_result": None,

    "inhib_word": None
}


for key, value in defaults.items():

    if key not in st.session_state:

        if isinstance(value, dict):
            st.session_state[key] = value.copy()

        elif isinstance(value, list):
            st.session_state[key] = value.copy()

        else:
            st.session_state[key] = value


# =========================================================
# NAVIGATION
# =========================================================

PAGES = [

    "Welcome Reboot",

    "Lab",

    "Explore Brain",

    "Brain Puzzle",

    "AI Mood & Behaviour",

    "Brain Exercises",

    # NEW DEDICATED PAGE
    "Daily Cognitive Experiment",

    "Research Book",

    "Ask Ayna",

    "Private Ask Ayna",

    "My Progress"
]


# =========================================================
# BRAIN DATABASE
# =========================================================

BRAIN = {

    "Prefrontal Cortex": (
        "Supports planning, working memory, cognitive control "
        "and goal-directed behaviour.",
        "Planning, decision-making and inhibition.",
        "Prefrontal cortex ↔ basal ganglia ↔ thalamus ↔ cortex"
    ),

    "Hippocampus": (
        "Important for episodic memory formation "
        "and spatial representation.",
        "Learning, memory and navigation.",
        "Hippocampus ↔ entorhinal cortex ↔ cortex"
    ),

    "Amygdala": (
        "Processes emotionally significant information "
        "and contributes to emotional learning.",
        "Threat processing, salience and emotional learning.",
        "Amygdala ↔ hypothalamus ↔ brainstem/cortex"
    ),

    "Striatum": (
        "Contributes to action selection, reward learning "
        "and habits.",
        "Reward learning, action selection and habits.",
        "Cortex → striatum → pallidal pathways → thalamus → cortex"
    ),

    "Anterior Cingulate Cortex": (
        "Contributes to performance monitoring, "
        "conflict processing and control.",
        "Conflict, error processing and effort-related control.",
        "ACC ↔ prefrontal ↔ striatal networks"
    ),

    "Cerebellum": (
        "Supports coordination, timing and motor learning "
        "and also contributes to cognition.",
        "Timing, balance, coordination and motor learning.",
        "Cerebellum → deep nuclei → thalamus → cortex"
    )
}


# =========================================================
# NEUROTRANSMITTERS
# =========================================================

NT = {

    "Dopamine":
        "Involved in reward learning, motivation, movement "
        "and several cognitive processes.",

    "Serotonin":
        "Involved in mood-related processes, sleep, appetite "
        "and many physiological functions.",

    "GABA":
        "A major inhibitory neurotransmitter "
        "in the central nervous system.",

    "Glutamate":
        "A major excitatory neurotransmitter important "
        "for learning and plasticity.",

    "Acetylcholine":
        "Contributes to attention, learning, memory "
        "and neuromuscular communication."
}


# =========================================================
# RESEARCH BOOK TOPICS
# =========================================================

BOOK = {

    "Brain & Behaviour": (
        "Behaviour emerges from interacting brain networks, "
        "body systems and environment.",

        "Cognitive neuroscience links behaviour to distributed "
        "neural systems. Separate correlation, causation, "
        "computational models and clinical observations."
    ),

    "Memory": (
        "Memory includes encoding, consolidation, "
        "retrieval and reconsolidation.",

        "Episodic, semantic, working and procedural memory "
        "involve partly distinct but interacting systems."
    ),

    "Attention": (
        "Attention changes which information receives "
        "processing priority.",

        "Attention involves selection, enhancement and "
        "suppression interacting with sensory and control networks."
    ),

    "Perception": (
        "Perception is the brain's construction of meaningful "
        "representations from sensory input.",

        "Perception reflects interactions among sensory evidence, "
        "prior knowledge, attention and context."
    ),

    "Emotion": (
        "Emotion involves interacting brain, body "
        "and cognitive processes.",

        "Contemporary models emphasize distributed networks, "
        "appraisal, interoception, learning and context."
    ),

    "Decision Making": (
        "Decisions combine goals, rewards, uncertainty, "
        "memory and control.",

        "Decision neuroscience examines valuation, learning, "
        "uncertainty, evidence accumulation and cognitive control."
    ),

    "Cognitive Control": (
        "Control helps maintain goals and adjust behaviour.",

        "Prefrontal, cingulate, parietal and striatal systems "
        "interact in task-dependent control."
    ),

    "Neuroplasticity": (
        "The nervous system can change with development, "
        "learning and experience.",

        "Plasticity includes synaptic, circuit and systems-level "
        "changes influenced by learning and context."
    )
}


# =========================================================
# LAB EQUIPMENT
# =========================================================

EQUIPMENT = {

    "EEG Scanner":
        "Illustrates measurement of electrical activity at "
        "the scalp; educational simulation only.",

    "Eye Tracker":
        "Illustrates measurement of gaze position "
        "and fixation patterns.",

    "Reaction-Time Monitor":
        "Measures response latency in a simple cognitive task.",

    "Auditory Attention Station":
        "Presents competing sounds to explore selective attention.",

    "Cognitive Task Screen":
        "Runs structured memory, attention and decision tasks.",

    "Physiological Monitor":
        "Illustrates non-neural physiological signals such as "
        "pulse or skin conductance; not a diagnosis."
}


# =========================================================
# EXPERIMENT BANK
# =========================================================

EXPERIMENTS = [

    ("Attention Gate", "Attention"),

    ("Working Memory Sprint", "Working Memory"),

    ("Decision Under Delay", "Decision Making"),

    ("Inhibition Challenge", "Inhibitory Control"),

    ("Cognitive Flexibility", "Cognitive Flexibility"),

    ("Memory Retrieval", "Memory")
]


MOODS = {

    "Positive": "😊",

    "Calm": "😌",

    "Neutral": "😐",

    "Worried": "😟",

    "Low": "😔",

    "Frustrated": "😤",

    "Tired": "😴"
}


# =========================================================
# LOAD BRAIN IMAGE
# =========================================================

@st.cache_data(show_spinner=False)
def load_brain():

    try:

        if os.path.exists(BRAIN_PATH):

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
def make_client(key):

    if genai is None or not key:
        return None

    try:
        return genai.Client(api_key=key)

    except Exception:
        return None


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

AI_LIMIT = 140


def ask_ai(prompt, context="", max_tokens=450):

    cache_key = hashlib.sha256(
        (prompt + "\n" + context)
        .encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()


    if cache_key in st.session_state.ai_cache:

        return (
            st.session_state.ai_cache[cache_key],
            "cache"
        )


    if st.session_state.ai_requests >= AI_LIMIT:

        return (
            "AI session limit reached. "
            "Local NEUROLENS activities are still available.",
            "limit"
        )


    client = make_client(get_api_key())


    if client is None:

        return (
            "Ask Ayna is unavailable. "
            "Add GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )


    prompt = f"""
You are Ayna, the AI assistant inside NEUROLENS,
an educational cognitive neuroscience platform.

Be accurate, concise, friendly and scientifically cautious.

Never diagnose a medical or psychiatric condition.

Do not claim that games, voice estimates or self-report
scores directly measure brain activity.

Distinguish evidence from hypotheses.

Language preference may be English or Roman English.

Avoid pretending to be a doctor or therapist.

Context:
{context[-4500:]}

Task:
{prompt}
"""


    try:

        st.session_state.ai_requests += 1

        if types:

            config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_tokens
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=config
            )

        else:

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )


        text = (
            getattr(response, "text", None)
            or "Ayna returned no text."
        ).strip()


        st.session_state.ai_cache[cache_key] = text

        return text, "ai"

    except Exception:

        return (
            "Ayna could not complete that request right now. "
            "You can continue with the local tools.",
            "error"
        )
        # ============================================================
# PART 3 — BRAIN JOURNEY + BRAIN PUZZLE
# ============================================================

elif st.session_state.page == "Explore Brain":

    st.markdown("## 🧠 Brain Journey")
    st.caption(
        "Explore the brain from large-scale systems to neurons, "
        "signals, synapses and cognition."
    )

    stages = [
        {
            "title": "🧠 Whole Brain",
            "text": (
                "The brain is a highly interconnected biological system. "
                "Different regions and networks work together to support "
                "perception, memory, attention, emotion and decision-making."
            ),
            "color": "#8ecae6"
        },
        {
            "title": "🔬 Brain Regions",
            "text": (
                "Different brain regions have specialised roles, but "
                "they rarely work alone. For example, the prefrontal "
                "cortex contributes to planning, cognitive control and "
                "decision-making."
            ),
            "color": "#90dbf4"
        },
        {
            "title": "🔗 Neural Pathways",
            "text": (
                "Information travels through networks of connected "
                "brain regions. These pathways allow different systems "
                "to coordinate behaviour and cognition."
            ),
            "color": "#a3c4f3"
        },
        {
            "title": "🧬 Neuron",
            "text": (
                "Neurons are specialised cells that communicate "
                "information through electrical and chemical signals."
            ),
            "color": "#bdb2ff"
        },
        {
            "title": "🌿 Dendrites",
            "text": (
                "Dendrites receive signals from other neurons and "
                "help integrate incoming information."
            ),
            "color": "#ffc8dd"
        },
        {
            "title": "⚡ Axon",
            "text": (
                "The axon carries electrical signals away from the "
                "neuron's cell body toward other cells."
            ),
            "color": "#ffafcc"
        },
        {
            "title": "🛡️ Myelin",
            "text": (
                "Myelin forms an insulating layer around many axons "
                "and supports faster and more efficient signal conduction."
            ),
            "color": "#caffbf"
        },
        {
            "title": "⚡ Electrical Signal",
            "text": (
                "An action potential is an electrical event that "
                "propagates along the axon when a neuron reaches "
                "the required threshold."
            ),
            "color": "#9bf6ff"
        },
        {
            "title": "🔄 Synapse",
            "text": (
                "At synapses, neurons communicate with other neurons "
                "or target cells. Chemical neurotransmitters are one "
                "important mechanism of communication."
            ),
            "color": "#ffd6a5"
        },
        {
            "title": "🧪 Neurotransmitters",
            "text": (
                "Neurotransmitters are chemical messengers released "
                "at many synapses. Examples include dopamine, serotonin, "
                "GABA and glutamate."
            ),
            "color": "#fdffb6"
        },
        {
            "title": "🎯 Cognition & Behaviour",
            "text": (
                "Large-scale brain networks and cellular communication "
                "ultimately support functions such as attention, memory, "
                "learning, emotion and decision-making."
            ),
            "color": "#b9fbc0"
        }
    ]

    if "brain_stage" not in st.session_state:
        st.session_state.brain_stage = 0

    stage_index = st.session_state.brain_stage
    stage = stages[stage_index]

    st.markdown(
        f"""
        <div style="
            padding:30px;
            border-radius:25px;
            text-align:center;
            background:linear-gradient(
                135deg,
                rgba(255,255,255,.10),
                rgba(255,255,255,.03)
            );
            border:1px solid rgba(255,255,255,.15);
            margin-top:20px;
        ">
            <div style="font-size:72px;">🧠</div>
            <h2>{stage["title"]}</h2>
            <p style="font-size:18px;line-height:1.7;">
                {stage["text"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(
        (stage_index + 1) / len(stages),
        text=f"Stage {stage_index + 1} / {len(stages)}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "⬅️ Previous",
            disabled=stage_index == 0,
            use_container_width=True,
            key="brain_previous"
        ):
            st.session_state.brain_stage -= 1
            st.rerun()

    with col2:
        if st.button(
            "🔊 Explain",
            use_container_width=True,
            key=f"brain_explain_{stage_index}"
        ):
            explanation = (
                stage["title"].replace("🧠", "")
                .replace("🔬", "")
                .replace("🔗", "")
                .replace("🧬", "")
                .replace("🌿", "")
                .replace("⚡", "")
                .replace("🛡️", "")
                .replace("🔄", "")
                .replace("🧪", "")
                .replace("🎯", "")
            )

            if st.session_state.language == "🇵🇰 Roman English":
                explanation = (
                    "Ayna explains: "
                    + stage["text"]
                )

            voice_button(
                explanation,
                key=f"brain_voice_{stage_index}"
            )

    with col3:
        if st.button(
            "Next ➡️",
            disabled=stage_index == len(stages) - 1,
            use_container_width=True,
            key="brain_next"
        ):
            st.session_state.brain_stage += 1
            st.rerun()

    st.markdown("---")

    st.markdown("### 🔍 Ask Ayna About This Stage")

    brain_question = st.text_input(
        "Your question",
        placeholder="e.g. Why is this stage important?",
        key=f"brain_question_{stage_index}"
    )

    if st.button(
        "Ask Ayna 🧠",
        key=f"brain_ask_{stage_index}"
    ):
        if brain_question.strip():

            context = (
                f"""
                We are currently exploring:
                {stage["title"]}

                Scientific explanation:
                {stage["text"]}

                User question:
                {brain_question}
                """
            )

            answer = ask_ai(context)

            st.markdown("### 🤖 Ayna")
            st.write(answer)

            voice_button(
                answer,
                key=f"brain_answer_voice_{stage_index}"
            )


# ============================================================
# BRAIN PUZZLE
# ============================================================

elif st.session_state.page == "Brain Puzzle":

    st.markdown("## 🧩 Brain Puzzle")
    st.caption(
        "Drag the numbered tiles into the correct order. "
        "Designed for mouse, touch and tablet interaction."
    )

    puzzle_size = st.selectbox(
        "Puzzle size",
        [3, 4, 5],
        format_func=lambda x: f"{x} × {x}",
        key="puzzle_size"
    )

    total_tiles = puzzle_size * puzzle_size

    if "puzzle_started" not in st.session_state:
        st.session_state.puzzle_started = False

    if "puzzle_moves" not in st.session_state:
        st.session_state.puzzle_moves = 0

    if "puzzle_start_time" not in st.session_state:
        st.session_state.puzzle_start_time = None

    if "puzzle_correct" not in st.session_state:
        st.session_state.puzzle_correct = 0

    if "puzzle_order" not in st.session_state:
        st.session_state.puzzle_order = list(range(1, total_tiles + 1))

    if (
        len(st.session_state.puzzle_order)
        != total_tiles
    ):
        st.session_state.puzzle_order = list(
            range(1, total_tiles + 1)
        )
        random.shuffle(st.session_state.puzzle_order)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Moves",
            st.session_state.puzzle_moves
        )

    with col2:
        if st.session_state.puzzle_started:
            elapsed = int(
                time.time()
                - st.session_state.puzzle_start_time
            )
        else:
            elapsed = 0

        st.metric(
            "Time",
            f"{elapsed}s"
        )

    with col3:
        st.metric(
            "Correct",
            st.session_state.puzzle_correct
        )

    with col4:
        if st.button(
            "🔄 New Puzzle",
            use_container_width=True,
            key="new_puzzle"
        ):
            st.session_state.puzzle_order = list(
                range(1, total_tiles + 1)
            )

            random.shuffle(
                st.session_state.puzzle_order
            )

            st.session_state.puzzle_moves = 0
            st.session_state.puzzle_correct = 0
            st.session_state.puzzle_started = True
            st.session_state.puzzle_start_time = time.time()

            st.rerun()

    if not st.session_state.puzzle_started:

        if st.button(
            "▶️ Start Puzzle",
            use_container_width=True,
            key="start_puzzle"
        ):
            st.session_state.puzzle_order = list(
                range(1, total_tiles + 1)
            )

            random.shuffle(
                st.session_state.puzzle_order
            )

            st.session_state.puzzle_moves = 0
            st.session_state.puzzle_correct = 0
            st.session_state.puzzle_started = True
            st.session_state.puzzle_start_time = time.time()

            st.rerun()

    else:

        # ----------------------------------------------------
        # Interactive HTML / JavaScript puzzle
        # ----------------------------------------------------

        puzzle_values = ",".join(
            str(x)
            for x in st.session_state.puzzle_order
        )

        correct_values = ",".join(
            str(x)
            for x in range(1, total_tiles + 1)
        )

        puzzle_html = f"""
        <div id="brain-puzzle"
             style="
                 max-width:520px;
                 margin:20px auto;
                 font-family:Arial,sans-serif;
             ">

            <div style="
                display:grid;
                grid-template-columns:
                repeat({puzzle_size}, 1fr);
                gap:8px;
                touch-action:none;
                user-select:none;
            "
            id="puzzle-grid">

        """

        for value in st.session_state.puzzle_order:

            puzzle_html += f"""
                <div
                    class="tile"
                    draggable="true"
                    data-value="{value}"
                    style="
                        aspect-ratio:1;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        border-radius:16px;
                        background:
                            linear-gradient(
                                135deg,
                                #8ecae6,
                                #219ebc
                            );
                        color:white;
                        font-size:
                            {max(20, 42 - puzzle_size * 4)}px;
                        font-weight:800;
                        cursor:grab;
                        box-shadow:
                            0 5px 15px
                            rgba(0,0,0,.18);
                    "
                >
                    {value}
                </div>
            """

        puzzle_html += f"""
            </div>

            <div style="
                margin-top:16px;
                text-align:center;
                font-size:14px;
                opacity:.8;
            ">
                Drag a tile and drop it on another tile.
                <br>
                Touch devices are supported.
            </div>

            <div id="puzzle-status"
                 style="
                    text-align:center;
                    margin-top:12px;
                    font-weight:700;
                 ">
            </div>

        </div>

        <script>

        const grid =
            document.getElementById("puzzle-grid");

        const status =
            document.getElementById("puzzle-status");

        let dragged = null;

        function tiles() {{
            return Array.from(
                grid.querySelectorAll(".tile")
            );
        }}

        function currentOrder() {{
            return tiles().map(
                tile => Number(tile.dataset.value)
            );
        }}

        function checkPuzzle() {{

            const order = currentOrder();

            const correct = [
                {correct_values}
            ];

            const isCorrect =
                order.every(
                    (value, index) =>
                    value === correct[index]
                );

            if (isCorrect) {{
                status.innerHTML =
                    "🎉 Correct! Brain puzzle completed.";

                status.style.color =
                    "#4ade80";
            }} else {{
                status.innerHTML =
                    "Keep going — rearrange the tiles.";

                status.style.color =
                    "inherit";
            }}
        }}

        function swapTiles(a, b) {{

            const parent = grid;

            const children =
                Array.from(parent.children);

            const ai = children.indexOf(a);
            const bi = children.indexOf(b);

            if (ai < bi) {{
                parent.insertBefore(
                    b,
                    a
                );
            }} else {{
                parent.insertBefore(
                    a,
                    b
                );
            }}
        }}

        tiles().forEach(tile => {{

            tile.addEventListener(
                "dragstart",
                function(event) {{
                    dragged = tile;
                    event.dataTransfer
                        .setData(
                            "text/plain",
                            tile.dataset.value
                        );
                }}
            );

            tile.addEventListener(
                "dragover",
                function(event) {{
                    event.preventDefault();
                }}
            );

            tile.addEventListener(
                "drop",
                function(event) {{

                    event.preventDefault();

                    if (
                        dragged &&
                        dragged !== tile
                    ) {{
                        swapTiles(
                            dragged,
                            tile
                        );

                        checkPuzzle();
                    }}
                }}
            );

            tile.addEventListener(
                "touchstart",
                function() {{
                    dragged = tile;
                }},
                {{passive:true}}
            );

            tile.addEventListener(
                "touchend",
                function(event) {{

                    const touch =
                        event.changedTouches[0];

                    const target =
                        document.elementFromPoint(
                            touch.clientX,
                            touch.clientY
                        );

                    if (
                        target &&
                        target.classList.contains("tile") &&
                        dragged &&
                        dragged !== target
                    ) {{

                        swapTiles(
                            dragged,
                            target
                        );

                        checkPuzzle();
                    }}

                    dragged = null;
                }}
            );

        }});

        checkPuzzle();

        </script>
        """

        components.html(
            puzzle_html,
            height=max(
                500,
                puzzle_size * 125
            )
        )

        st.markdown("---")

        st.info(
            "🧠 This puzzle is an educational cognitive task. "
            "Its score should not be interpreted as a clinical "
            "measurement of brain function."
        )

        if st.button(
            "💾 Record Puzzle Result",
            key="record_puzzle"
        ):

            if st.session_state.puzzle_start_time:
                final_time = int(
                    time.time()
                    - st.session_state.puzzle_start_time
                )
            else:
                final_time = 0

            record(
                "Brain Puzzle",
                {
                    "size": f"{puzzle_size}x{puzzle_size}",
                    "moves": st.session_state.puzzle_moves,
                    "time_seconds": final_time
                }
            )

            st.success(
                "Puzzle result recorded in your session progress."
            )
            # ============================================================
# PART 4 — RESEARCH BOOK + ASK AYNA + PRIVATE CHAT + PROGRESS
# ============================================================

elif st.session_state.page == "Research Book":

    st.markdown("## 📚 Research Book")
    st.caption(
        "Search real biomedical and neuroscience literature. "
        "Ayna explains research papers but does not invent citations."
    )

    topic = st.text_input(
        "🔎 Search research papers",
        placeholder="e.g. attention, working memory, dopamine, neuroplasticity",
        key="research_search"
    )

    col1, col2 = st.columns(2)

    with col1:
        max_results = st.selectbox(
            "Number of papers",
            [5, 10],
            index=0,
            key="research_limit"
        )

    with col2:
        year_filter = st.selectbox(
            "Publication period",
            [
                "All years",
                "Last 5 years",
                "Last 10 years"
            ],
            key="research_year"
        )

    if st.button(
        "🔍 Search Research",
        use_container_width=True,
        key="search_research"
    ):

        if not topic.strip():
            st.warning("Please enter a research topic.")

        else:

            import urllib.parse
            import urllib.request
            import json

            query = topic.strip()

            if year_filter == "Last 5 years":
                query += " FIRST_PDATE:[2021-01-01 TO 2030-12-31]"

            elif year_filter == "Last 10 years":
                query += " FIRST_PDATE:[2016-01-01 TO 2030-12-31]"

            encoded_query = urllib.parse.quote_plus(query)

            api_url = (
                "https://www.ebi.ac.uk/"
                "europepmc/webservices/rest/search"
                f"?query={encoded_query}"
                f"&format=json&pageSize={max_results}"
            )

            try:

                with st.spinner(
                    "Searching Europe PMC research literature..."
                ):

                    request = urllib.request.Request(
                        api_url,
                        headers={
                            "User-Agent":
                            "NEUROLENS/1.0 Research Book"
                        }
                    )

                    with urllib.request.urlopen(
                        request,
                        timeout=20
                    ) as response:

                        data = json.loads(
                            response.read().decode(
                                "utf-8"
                            )
                        )

                results = data.get(
                    "resultList",
                    {}
                ).get(
                    "result",
                    []
                )

                st.session_state.research_results = results

                if results:
                    st.success(
                        f"Found {len(results)} research records."
                    )
                else:
                    st.info(
                        "No papers found for this search."
                    )

            except Exception as e:

                st.error(
                    "Research search could not be completed."
                )

                st.caption(
                    f"Technical detail: {str(e)}"
                )

    results = st.session_state.get(
        "research_results",
        []
    )

    if results:

        st.markdown("### 📑 Research Results")

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
                ""
            )

            pub_year = paper.get(
                "pubYear",
                ""
            )

            doi = paper.get(
                "doi",
                ""
            )

            pmid = paper.get(
                "pmid",
                ""
            )

            pmcid = paper.get(
                "pmcid",
                ""
            )

            abstract = paper.get(
                "abstractText",
                ""
            )

            is_open_access = paper.get(
                "isOpenAccess",
                False
            )

            with st.expander(
                f"📄 {i + 1}. {title}"
            ):

                st.markdown(
                    f"**Authors:** {authors}"
                )

                if journal:
                    st.markdown(
                        f"**Journal:** {journal}"
                    )

                if pub_year:
                    st.markdown(
                        f"**Year:** {pub_year}"
                    )

                if doi:
                    st.markdown(
                        f"**DOI:** `{doi}`"
                    )

                if pmid:
                    st.markdown(
                        f"**PMID:** `{pmid}`"
                    )

                if pmcid:
                    st.markdown(
                        f"**PMCID:** `{pmcid}`"
                    )

                if abstract:

                    st.markdown("### Abstract")

                    st.write(abstract)

                else:

                    st.info(
                        "Abstract is not available "
                        "through this record."
                    )

                st.markdown("---")

                # --------------------------------------------
                # ORIGINAL SOURCE
                # --------------------------------------------

                if pmid:

                    pubmed_url = (
                        "https://pubmed.ncbi.nlm.nih.gov/"
                        + str(pmid)
                        + "/"
                    )

                    st.link_button(
                        "🔗 View PubMed",
                        pubmed_url
                    )

                if pmcid:

                    europe_url = (
                        "https://europepmc.org/articles/"
                        + str(pmcid)
                    )

                    st.link_button(
                        "📖 View Full Text",
                        europe_url
                    )

                # --------------------------------------------
                # OPEN ACCESS PDF
                # --------------------------------------------

                pdf_url = None

                full_text_links = paper.get(
                    "fullTextUrlList",
                    {}
                )

                full_text_links = full_text_links.get(
                    "fullTextUrl",
                    []
                )

                for link in full_text_links:

                    link_url = link.get(
                        "url",
                        ""
                    )

                    document_style = link.get(
                        "documentStyle",
                        ""
                    )

                    if (
                        document_style.lower()
                        == "pdf"
                    ):

                        pdf_url = link_url
                        break

                    if link_url.lower().endswith(
                        ".pdf"
                    ):

                        pdf_url = link_url
                        break

                if (
                    not pdf_url
                    and pmcid
                    and is_open_access
                ):

                    pdf_url = (
                        "https://europepmc.org/"
                        "articles/"
                        f"{pmcid}?pdf=render"
                    )

                if pdf_url:

                    st.link_button(
                        "⬇️ Open / Download Open-Access PDF",
                        pdf_url
                    )

                    st.caption(
                        "PDF access is provided only when "
                        "an open/full-text route is available."
                    )

                else:

                    st.caption(
                        "No direct open-access PDF was detected. "
                        "Use the original source link to check "
                        "your lawful access."
                    )

                # --------------------------------------------
                # AYNA PAPER EXPLANATION
                # --------------------------------------------

                if st.button(
                    "🤖 Explain This Paper with Ayna",
                    key=f"explain_paper_{i}"
                ):

                    paper_context = f"""
                    Explain this research paper for an
                    educational cognitive neuroscience platform.

                    Title:
                    {title}

                    Authors:
                    {authors}

                    Journal:
                    {journal}

                    Year:
                    {pub_year}

                    DOI:
                    {doi}

                    Abstract:
                    {abstract}

                    Explain:
                    1. What question the researchers studied.
                    2. Why the question matters.
                    3. What methods were used if stated.
                    4. Main findings.
                    5. Limitations or uncertainty.
                    6. Why the findings matter for cognition,
                       behaviour or neuroscience.

                    Do not invent information that is not
                    present in the paper record.
                    """

                    explanation = ask_ai(
                        paper_context
                    )

                    st.markdown(
                        "### 🧠 Ayna's Explanation"
                    )

                    st.write(
                        explanation
                    )

                    voice_button(
                        explanation,
                        key=f"paper_voice_{i}"
                    )


# ============================================================
# ASK AYNA
# ============================================================

elif st.session_state.page == "Ask Ayna":

    st.markdown("## 🤖 Ask Ayna")

    st.caption(
        "Your cognitive neuroscience AI assistant."
    )

    st.info(
        "Ask about memory, attention, learning, emotion, "
        "decision-making, reward, perception, brain systems, "
        "behaviour and consciousness."
    )

    if "ayna_messages" not in st.session_state:

        st.session_state.ayna_messages = [
            {
                "role": "assistant",
                "content":
                "Hi! I'm Ayna. Ask me anything about "
                "cognition, behaviour and the brain."
            }
        ]

    for message_index, message in enumerate(
        st.session_state.ayna_messages
    ):

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

            if message["role"] == "assistant":

                voice_button(
                    message["content"],
                    key=f"ask_ayna_voice_{message_index}"
                )

    user_question = st.chat_input(
        "Ask Ayna a neuroscience question..."
    )

    if user_question:

        st.session_state.ayna_messages.append(
            {
                "role": "user",
                "content": user_question
            }
        )

        with st.chat_message("user"):
            st.write(user_question)

        history_text = "\n".join(
            [
                f'{m["role"]}: {m["content"]}'
                for m in
                st.session_state.ayna_messages[-8:]
            ]
        )

        language_instruction = (
            "Answer in clear English."
            if st.session_state.language
            == "🇬🇧 English"
            else
            "Answer in simple Roman English."
        )

        prompt = f"""
        You are Ayna, an educational cognitive neuroscience
        assistant inside NEUROLENS.

        {language_instruction}

        Areas:
        - cognitive neuroscience
        - attention
        - memory
        - learning
        - emotion
        - reward
        - decision-making
        - perception
        - cognitive control
        - neuroplasticity
        - brain systems
        - behaviour
        - consciousness

        Rules:
        - Be scientifically careful.
        - Do not diagnose mental or neurological disorders.
        - Do not claim a simple game measures brain activity.
        - Clearly mention uncertainty when evidence is limited.
        - Do not pretend to be a doctor or therapist.
        - Use understandable explanations.

        Conversation:
        {history_text}

        User's latest question:
        {user_question}
        """

        with st.chat_message("assistant"):

            with st.spinner(
                "Ayna is thinking..."
            ):

                answer = ask_ai(
                    prompt
                )

            st.write(answer)

            voice_button(
                answer,
                key="latest_ask_ayna_voice"
            )

        st.session_state.ayna_messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


# ============================================================
# PRIVATE ASK AYNA
# USER CREATES THEIR OWN 4–6 DIGIT PIN
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    st.markdown("## 🔐 Private Ask Ayna")

    st.caption(
        "Create your own 4–6 digit session PIN."
    )

    if (
        "private_pin_hash"
        not in st.session_state
    ):
        st.session_state.private_pin_hash = None

    if (
        "private_unlocked"
        not in st.session_state
    ):
        st.session_state.private_unlocked = False

    # --------------------------------------------------------
    # CREATE PIN
    # --------------------------------------------------------

    if (
        st.session_state.private_pin_hash
        is None
    ):

        st.info(
            "This is your first time using Private Ask Ayna. "
            "Create a PIN that you will remember."
        )

        new_pin = st.text_input(
            "Create PIN",
            type="password",
            max_chars=6,
            key="create_private_pin"
        )

        confirm_pin = st.text_input(
            "Confirm PIN",
            type="password",
            max_chars=6,
            key="confirm_private_pin"
        )

        if st.button(
            "🔐 Create Private PIN",
            use_container_width=True,
            key="create_pin_button"
        ):

            if not new_pin.isdigit():

                st.error(
                    "PIN must contain digits only."
                )

            elif not (
                4 <= len(new_pin) <= 6
            ):

                st.error(
                    "PIN must contain 4 to 6 digits."
                )

            elif new_pin != confirm_pin:

                st.error(
                    "PIN confirmation does not match."
                )

            else:

                st.session_state.private_pin_hash = (
                    hashlib.sha256(
                        new_pin.encode("utf-8")
                    ).hexdigest()
                )

                st.session_state.private_unlocked = True

                st.success(
                    "Private PIN created successfully."
                )

                st.rerun()

    # --------------------------------------------------------
    # UNLOCK
    # --------------------------------------------------------

    elif not st.session_state.private_unlocked:

        st.warning(
            "Private Ask Ayna is locked."
        )

        entered_pin = st.text_input(
            "Enter your PIN",
            type="password",
            max_chars=6,
            key="private_unlock_pin"
        )

        if st.button(
            "🔓 Unlock",
            use_container_width=True,
            key="private_unlock_button"
        ):

            entered_hash = hashlib.sha256(
                entered_pin.encode("utf-8")
            ).hexdigest()

            if (
                entered_hash
                == st.session_state.private_pin_hash
            ):

                st.session_state.private_unlocked = True

                st.success(
                    "Private chat unlocked."
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

        st.success(
            "🔓 Private Ask Ayna unlocked for this session."
        )

        if (
            "private_messages"
            not in st.session_state
        ):

            st.session_state.private_messages = [
                {
                    "role": "assistant",
                    "content":
                    "Private Ask Ayna is ready. "
                    "You can write your question here."
                }
            ]

        for message_index, message in enumerate(
            st.session_state.private_messages
        ):

            with st.chat_message(
                message["role"]
            ):

                st.write(
                    message["content"]
                )

                if message["role"] == "assistant":

                    voice_button(
                        message["content"],
                        key=f"private_voice_{message_index}"
                    )

        private_question = st.chat_input(
            "Ask Ayna privately..."
        )

        if private_question:

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "content": private_question
                }
            )

            private_history = "\n".join(
                [
                    f'{m["role"]}: {m["content"]}'
                    for m in
                    st.session_state.private_messages[-8:]
                ]
            )

            private_prompt = f"""
            You are Ayna, an educational cognitive
            neuroscience assistant.

            This is a private session.

            Answer carefully and clearly.

            Do not:
            - diagnose
            - act as a therapist
            - claim certainty where evidence is uncertain
            - expose private conversation content

            Conversation:
            {private_history}

            Latest user message:
            {private_question}
            """

            with st.chat_message("assistant"):

                with st.spinner(
                    "Ayna is thinking privately..."
                ):

                    private_answer = ask_ai(
                        private_prompt
                    )

                st.write(
                    private_answer
                )

                voice_button(
                    private_answer,
                    key="private_latest_voice"
                )

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": private_answer
                }
            )

        st.markdown("---")

        st.caption(
            "⚠️ This PIN is a session-level lock. "
            "It is not a replacement for encrypted storage, "
            "authentication or a secure clinical system."
        )

        if st.button(
            "🔒 Lock Private Chat",
            key="lock_private_chat"
        ):

            st.session_state.private_unlocked = False

            st.rerun()


# ============================================================
# MY PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    st.markdown("## 📊 My Progress")

    history = st.session_state.get(
        "history",
        []
    )

    if not history:

        st.info(
            "No activity recorded yet. "
            "Complete an experiment or puzzle first."
        )

    else:

        st.success(
            f"{len(history)} activity record(s) "
            "in this session."
        )

        for index, item in enumerate(
            reversed(history)
        ):

            with st.expander(
                f"📌 {item['activity']} — {item['time']}"
            ):

                st.write(
                    item["details"]
                )

        # ----------------------------------------------------
        # SIMPLE ACTIVITY CHART
        # ----------------------------------------------------

        activity_counts = {}

        for item in history:

            activity = item["activity"]

            activity_counts[activity] = (
                activity_counts.get(
                    activity,
                    0
                ) + 1
            )

        try:

            import plotly.graph_objects as plotly_go

            chart = plotly_go.Figure(
                data=[
                    plotly_go.Bar(
                        x=list(
                            activity_counts.keys()
                        ),
                        y=list(
                            activity_counts.values()
                        )
                    )
                ]
            )

            chart.update_layout(
                title="Activities Completed",
                xaxis_title="Activity",
                yaxis_title="Count",
                height=400
            )

            st.plotly_chart(
                chart,
                use_container_width=True
            )

        except Exception:

            st.bar_chart(
                activity_counts
            )

        # ----------------------------------------------------
        # CLEAR SESSION PROGRESS
        # ----------------------------------------------------

        if st.button(
            "🗑️ Clear Session Progress",
            key="clear_progress"
        ):

            st.session_state.history = []

            st.success(
                "Session progress cleared."
            )

            st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        opacity:.7;
        padding:15px;
    ">
        🧠 <b>NEUROLENS</b><br>
        Explore cognition, behaviour & the brain<br>
        <small>Created by Ayna Jaffri</small>
    </div>
    """,
    unsafe_allow_html=True
)

            
