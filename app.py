import os
import random
import time
import hashlib
import base64
import html
import urllib.parse
import urllib.request
import json
from datetime import datetime
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

st.markdown(
    """
<style>

.stApp{
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

.block-container{
    max-width:1400px;
    padding-top:1rem;
}

.hero{
    padding:28px;
    border-radius:24px;
    background:
        linear-gradient(
            135deg,
            #122c49,
            #111a32
        );
    border:1px solid #45617d;
    margin-bottom:18px;
}

.card{
    padding:18px;
    border-radius:18px;
    background:#0d2035;
    border:1px solid #294560;
    margin:8px 0;
}

.lab{
    min-height:320px;
    border-radius:24px;
    position:relative;
    overflow:hidden;
    background:
        radial-gradient(
            circle,
            #285b88 0,
            #0b1930 28%,
            #07111f 72%
        );
    border:1px solid #36536d;
}

.orb{
    position:absolute;
    width:92px;
    height:92px;
    border-radius:50%;
    left:calc(50% - 46px);
    top:calc(50% - 46px);
    background:
        radial-gradient(
            circle,
            #fff,
            #8ed1ff 20%,
            #536bff 55%,
            #342a7d
        );
    box-shadow:0 0 45px #71bfff;
    animation:p 2.3s infinite;
}

@keyframes p{
    50%{
        transform:scale(1.1);
    }
}

.small{
    opacity:.78;
    font-size:.9rem;
}

.stage{
    height:210px;
    border-radius:22px;
    background:
        radial-gradient(
            circle,
            #153d63,
            #081321
        );
    border:1px solid #38536e;
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
}

.neuron{
    font-size:5rem;
    animation:p 1.5s infinite;
}

.signal{
    font-size:3rem;
    animation:move 2s linear infinite;
}

@keyframes move{
    0%{
        transform:translateX(-170px);
    }

    100%{
        transform:translateX(170px);
    }
}

.syn{
    font-size:3rem;
    animation:p .9s infinite;
}

</style>
""",
    unsafe_allow_html=True
)


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

    "messages": [],
    "private_messages": [],

    "private_unlocked": False,
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
    "lab_start_time": None,

    "lab_sequence": None,
    "attention_target": None,
    "attention_stimuli": [],
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
        "Contributes to performance monitoring, conflict "
        "processing and control.",
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
# RESEARCH BOOK
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
        "pulse or skin conductance; not a diagnosis.",

    "Behaviour Observation Station":
        "Educational simulation for observing behavioural "
        "responses during structured tasks.",

    "Behaviour Task Screen":
        "Runs simple behavioural decision-making and "
        "response-pattern tasks.",

    "Social Interaction Simulator":
        "Educational simulation of social interaction, "
        "communication and behavioural responses.",

    "Emotion Recognition Display":
        "Educational simulation exploring interpretation "
        "of facial and emotional cues; not a clinical emotion detector."
}


BEHAVIOUR_EQUIPMENT = [
    "Behaviour Observation Station",
    "Behaviour Task Screen",
    "Social Interaction Simulator",
    "Emotion Recognition Display"
]


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


def ask_ai(
    prompt,
    context="",
    max_tokens=450,
    system_extra=""
):

    cache_key = hashlib.sha256(
        (
            prompt
            + "\n"
            + context
            + "\n"
            + system_extra
        ).encode(
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

    client = make_client(
        get_api_key()
    )

    if client is None:

        return (
            "Ask Ayna is unavailable. "
            "Add GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    full_prompt = f"""
You are Ayna, the AI assistant inside NEUROLENS,
an educational cognitive neuroscience platform.

Be accurate, concise, friendly and scientifically cautious.

Never diagnose a medical or psychiatric condition.

Do not claim that games, voice estimates or self-report
scores directly measure brain activity.

Distinguish evidence from hypotheses.

Language preference may be English or Roman English.

Avoid pretending to be a doctor or therapist.

{system_extra}

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
                contents=full_prompt,
                config=config
            )

        else:

            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt
            )

        text = (
            getattr(
                response,
                "text",
                None
            )
            or "Ayna returned no text."
        ).strip()

        st.session_state.ai_cache[cache_key] = text

        return text, "ai"

    except Exception as error:

        return (
            "Ayna could not complete that request right now. "
            "You can continue with the local tools.",
            "error"
        )


def ask_ai_audio(
    audio,
    prompt
):

    client = make_client(
        get_api_key()
    )

    if client is None:

        return (
            "Voice AI needs GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    if types is None:

        return (
            "Voice input support is unavailable in this environment.",
            "offline"
        )

    if st.session_state.ai_requests >= AI_LIMIT:

        return (
            "AI session limit reached.",
            "limit"
        )

    try:

        st.session_state.ai_requests += 1

        part = types.Part.from_bytes(
            data=audio.getvalue(),
            mime_type=audio.type or "audio/wav"
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                part,
                prompt
            ]
        )

        return (
            getattr(
                response,
                "text",
                None
            )
            or "No voice result returned."
        ).strip(), "ai"

    except Exception:

        return (
            "Ayna could not process the voice recording right now.",
            "error"
        )


# =========================================================
# HELPERS
# =========================================================

def go_to(page):

    st.session_state.page = page
    st.rerun()


def record(name, amount=1):

    st.session_state.progress[name] = (
        st.session_state.progress.get(
            name,
            0
        )
        + amount
    )


def voice_button(
    text,
    key,
    language="en-US"
):

    safe = (
        html.escape(
            str(text)
        )
        .replace(
            "`",
            "\\`"
        )
    )

    components.html(
        f"""
        <button
            onclick="speakText()"
            style="
                padding:9px 15px;
                border-radius:10px;
                border:1px solid #789;
                background:#173b5f;
                color:white;
                cursor:pointer;
            "
        >
            🔊 Play Ayna
        </button>

        <script>
        function speakText(){{
            window.speechSynthesis.cancel();

            const text =
                `{safe}`;

            const u =
                new SpeechSynthesisUtterance(text);

            u.lang = '{language}';
            u.rate = 0.92;
            u.pitch = 1.03;

            window.speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=52
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    lang = st.radio(
        "Language",
        [
            "English",
            "Roman English"
        ],
        index=(
            0
            if st.session_state.get(
                "language",
                "English"
            ) == "English"
            else 1
        ),
        key="language_choice"
    )

    st.session_state.language = lang

    st.divider()

    for i, page in enumerate(PAGES):

        if st.button(
            (
                "● "
                if page == st.session_state.page
                else "○ "
            ) + page,
            key=f"nav_{i}",
            use_container_width=True
        ):
            go_to(page)

    st.divider()

    st.caption(
        f"AI requests: "
        f"{st.session_state.ai_requests}/{AI_LIMIT}"
    )

    st.progress(
        min(
            st.session_state.ai_requests / AI_LIMIT,
            1.0
        )
    )

    st.caption(
        "Local-first design: games, visuals and "
        "educational notes do not require AI."
    )


# =========================================================
# HEADER
# =========================================================

if st.session_state.page != "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">
            <h1>🧠 NEUROLENS</h1>
            <p>Explore cognition, behaviour & the brain</p>
            <small>
                Interactive Cognitive Neuroscience Lab
                • Created by Ayna Jaffri
            </small>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# WELCOME REBOOT
# =========================================================

if st.session_state.page == "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">
            <h1>🧠 NEUROLENS</h1>
            <p>Welcome Reboot</p>
            <small>
                Initializing Ayna Cognitive Neuroscience System...
            </small>
        </div>
        """,
        unsafe_allow_html=True
    )

    if REBOOT_VIDEO:

        st.video(REBOOT_VIDEO)

    elif brain:

        st.image(
            brain,
            use_container_width=True
        )

    else:

        st.markdown(
            """
            <div class="lab">
                <div class="orb"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    welcome_text = (
        "Welcome to NeuroLens! Main Ayna hoon, "
        "aap ki cognitive neuroscience lab assistant. "
        "Aaj hum brain, behaviour aur cognition ko explore karenge."
        if st.session_state.language == "Roman English"
        else
        "Welcome to NeuroLens! I'm Ayna, your cognitive "
        "neuroscience lab assistant. Let's explore the brain, "
        "behaviour, and cognition together."
    )

    st.markdown("### 🤖 Ayna")

    st.write(welcome_text)

    voice_button(
        welcome_text,
        "welcome_reboot_voice"
    )

    st.info(
        "Agar video mein voice nahi hai, Play Ayna button "
        "browser speech se Ayna ki voice chalata hai."
    )

    if st.button(
        "🚀 Enter NeuroLens",
        use_container_width=True,
        type="primary",
        key="enter_neurolens"
    ):

        go_to("Lab")


# =========================================================
# LAB
# =========================================================

elif st.session_state.page == "Lab":

    st.subheader(
        "🔬 Interactive Cognitive Neuroscience Lab"
    )

    st.caption(
        "Character → equipment → experiment → perform → "
        "Ayna analysis → follow-up"
    )

    left, right = st.columns(
        [1.35, 1]
    )

    with left:

        if LAB_VIDEO:
            st.video(LAB_VIDEO)

        else:

            st.markdown(
                """
                <div class="lab">
                    <div class="orb"></div>
                </div>
                """,
                unsafe_allow_html=True
            )

        equipment = st.selectbox(
            "Choose equipment",
            list(EQUIPMENT),
            index=list(EQUIPMENT).index(
                st.session_state.equipment
            )
            if st.session_state.equipment in EQUIPMENT
            else 0,
            key="lab_equipment_main"
        )

        st.session_state.equipment = equipment

        characters = [
            "Nova",
            "Mira",
            "Ray",
            "Zara"
        ]

        character = st.selectbox(
            "👤 Choose lab character",
            characters,
            index=characters.index(
                st.session_state.character
            ),
            key="lab_character_main"
        )

        st.session_state.character = character

        st.success(
            f"🧑‍🔬 {character} is ready with "
            f"the {equipment}."
        )

        st.info(
            EQUIPMENT[equipment]
        )

        st.markdown("### 🧪 Behaviour Lab")

        st.write(
            "Explore educational behaviour-focused simulations "
            "separately from the main neuroscience lab."
        )

        if st.button(
            "🧠 Open Behaviour Lab",
            use_container_width=True,
            key="open_behaviour_lab"
        ):

            go_to("AI Mood & Behaviour")

    with right:

        st.markdown("### 🧪 Select Experiment")

        LAB_TASKS = {

            "Attention Gate": (
                "Attention",
                "Find X in: A X K M X T P X R B X Q",
                "4"
            ),

            "Working Memory Sprint": (
                "Working Memory",
                "Memorize: 7 2 9 4 1 8",
                "729418"
            ),

            "Decision Under Delay": (
                "Decision Making",
                "A: Rs 1,000 today | B: Rs 1,500 after 30 days",
                "B"
            ),

            "Inhibition Challenge": (
                "Inhibitory Control",
                "Respond with the colour shown by the target.",
                "BLUE"
            ),

            "Cognitive Flexibility": (
                "Cognitive Flexibility",
                "Continue: Circle → Square → Circle → Square → ?",
                "Circle"
            ),

            "Memory Retrieval": (
                "Memory",
                "Earlier sequence: 3 8 1 6 4 9. Which target number was present?",
                "6"
            )
        }

        selected = st.selectbox(
            "Experiment",
            list(LAB_TASKS),
            key="lab_selected_experiment"
        )

        domain, instruction, correct_answer = LAB_TASKS[
            selected
        ]

        st.markdown(
            f"""
            <div class="card">
                <b>Domain:</b> {domain}<br>
                <b>Task:</b> {instruction}
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "▶️ Start Experiment",
            type="primary",
            use_container_width=True,
            key="lab_start"
        ):

            st.session_state.lab_started = True
            st.session_state.active_lab_experiment = selected
            st.session_state.lab_result = None
            st.session_state.lab_start_time = time.time()

            st.session_state.lab_sequence = "729418"
            st.session_state.attention_target = "X"
            st.session_state.inhib_word = "BLUE"

            st.rerun()

    if st.session_state.lab_started:

        active = st.session_state.active_lab_experiment

        st.divider()

        st.markdown(
            f"## 🧠 Active Experiment: {active}"
        )

        response = None

        if active == "Attention Gate":

            st.markdown(
                """
                <div class="card"
                style="text-align:center;font-size:30px;">
                A&nbsp;&nbsp;X&nbsp;&nbsp;K&nbsp;&nbsp;M&nbsp;&nbsp;
                X&nbsp;&nbsp;T&nbsp;&nbsp;P&nbsp;&nbsp;X&nbsp;&nbsp;
                R&nbsp;&nbsp;B&nbsp;&nbsp;X&nbsp;&nbsp;Q
                </div>
                """,
                unsafe_allow_html=True
            )

            response = st.text_input(
                "How many X characters did you find?",
                key="lab_attention_response"
            )

        elif active == "Working Memory Sprint":

            st.info(
                "Memorize this sequence: 7 2 9 4 1 8"
            )

            response = st.text_input(
                "Enter the sequence",
                key="lab_memory_response"
            )

        elif active == "Decision Under Delay":

            response = st.radio(
                "Choose one:",
                [
                    "A — Rs 1,000 today",
                    "B — Rs 1,500 after 30 days"
                ],
                key="lab_decision_response"
            )

        elif active == "Inhibition Challenge":

            st.markdown(
                """
                <div class="card"
                style="text-align:center;font-size:36px;">
                BLUE
                </div>
                """,
                unsafe_allow_html=True
            )

            response = st.selectbox(
                "Your response",
                [
                    "RED",
                    "BLUE",
                    "GREEN",
                    "YELLOW"
                ],
                key="lab_inhibition_response"
            )

        elif active == "Cognitive Flexibility":

            response = st.radio(
                "What comes next?",
                [
                    "Circle",
                    "Square"
                ],
                key="lab_flex_response"
            )

        elif active == "Memory Retrieval":

            st.info(
                "Recall: 3 8 1 6 4 9"
            )

            response = st.text_input(
                "Which target number was present?",
                key="lab_recall_response"
            )

        if st.button(
            "✅ Submit Experiment",
            type="primary",
            key="lab_submit"
        ):

            elapsed = (
                time.time()
                - (
                    st.session_state.lab_start_time
                    or time.time()
                )
            )

            correct = False

            if active == "Attention Gate":
                correct = str(response).strip() == "4"

            elif active == "Working Memory Sprint":
                correct = (
                    str(response).replace(" ", "")
                    == "729418"
                )

            elif active == "Decision Under Delay":
                correct = str(response).startswith("B")

            elif active == "Inhibition Challenge":
                correct = response == "BLUE"

            elif active == "Cognitive Flexibility":
                correct = response == "Circle"

            elif active == "Memory Retrieval":
                correct = str(response).strip() == "6"

            result = {
                "experiment": active,
                "correct": correct,
                "time": round(elapsed, 2)
            }

            st.session_state.lab_result = result

            record("experiments")
            record("games")

            st.session_state.experiment_history.append(
                result
            )

            st.rerun()

    if st.session_state.lab_result:

        result = st.session_state.lab_result

        if result["correct"]:

            st.success(
                f"🎉 Correct! Response time: "
                f"{result['time']} seconds."
            )

        else:

            st.warning(
                "Not quite. Treat this as a learning "
                "exercise, not a diagnostic score."
            )

        if st.button(
            "🤖 Ask Ayna for follow-up",
            key="lab_followup"
        ):

            answer_text, source = ask_ai(
                f"""
Give one short educational follow-up challenge
for the cognitive domain of
{result['experiment']}.
Do not diagnose.
""",
                max_tokens=250
            )

            st.write(answer_text)
            st.caption(source)

            voice_button(
                answer_text,
                "lab_followup_voice"
            )


# =========================================================
# EXPLORE BRAIN
# =========================================================

elif st.session_state.page == "Explore Brain":

    st.subheader(
        "🧠 Explore Brain Systems"
    )

    st.caption(
        "Explore regions, circuits, neurotransmitters "
        "and cognition."
    )

    region = st.selectbox(
        "Select brain region",
        list(BRAIN),
        key="brain_region"
    )

    description, function, circuit = BRAIN[
        region
    ]

    col1, col2 = st.columns(
        [1.1, 1]
    )

    with col1:

        if JOURNEY_VIDEO:

            st.video(JOURNEY_VIDEO)

        elif brain:

            st.image(
                brain,
                use_container_width=True
            )

        else:

            st.markdown(
                """
                <div class="stage">
                    <div class="neuron">🧠</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with col2:

        st.markdown(
            f"""
            <div class="card">
                <h2>{region}</h2>
                <p>{description}</p>

                <b>Main functions</b>
                <p>{function}</p>

                <b>Example circuit</b>
                <p>{circuit}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "### 🧪 Neurotransmitter context"
    )

    nt = st.selectbox(
        "Select neurotransmitter",
        list(NT),
        key="brain_nt"
    )

    st.info(
        f"**{nt}:** {NT[nt]}"
    )

    st.markdown(
        "### 💬 Ask Ayna about this region"
    )

    question = st.text_input(
        "Question",
        key="brain_question",
        placeholder="e.g. How does this region support memory?"
    )

    if st.button(
        "Ask Ayna",
        key="brain_ask"
    ) and question:

        answer, source = ask_ai(
            question,
            context=(
                f"Brain region: {region}\n"
                f"Description: {description}\n"
                f"Function: {function}\n"
                f"Circuit: {circuit}"
            ),
            max_tokens=450
        )

        st.write(answer)
        st.caption(source)

        voice_button(
            answer,
            "brain_region_voice"
        )


# =========================================================
# BRAIN PICTURE PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    st.subheader(
        "🧩 Brain Picture Puzzle"
    )

    st.caption(
        "Drag pieces with mouse or touch and place them "
        "into the correct positions."
    )

    if not brain:

        st.warning(
            "brain.png is required for the picture puzzle."
        )

    else:

        difficulty = st.select_slider(
            "Difficulty",
            [
                "3 × 3",
                "4 × 4",
                "5 × 5"
            ],
            value="3 × 3",
            key="picture_puzzle_difficulty"
        )

        n = int(difficulty[0])

        buffer = BytesIO()

        brain.save(
            buffer,
            format="PNG"
        )

        image_data = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        puzzle_html = """
        <div style="font-family:Arial,sans-serif;color:white;">

            <button
                id="newPuzzle"
                style="
                    padding:9px 15px;
                    border-radius:10px;
                    border:1px solid #789;
                    background:#173b5f;
                    color:white;
                    cursor:pointer;
                "
            >
                🔀 New Puzzle
            </button>

            <span
                id="stats"
                style="margin-left:12px;"
            ></span>

            <div id="board"></div>

            <h3 id="complete"></h3>

        </div>

        <style>

        #board {
            display:grid;
            grid-template-columns:repeat(__N__,1fr);
            gap:6px;
            max-width:800px;
            margin:14px auto;
        }

        .slot {
            aspect-ratio:1;
            border:2px dashed #9fb1c8;
            border-radius:10px;
            overflow:hidden;
            background:#102235;
        }

        .piece {
            width:100%;
            height:100%;
            background-image:url(
                data:image/png;base64,__IMAGE__
            );
            background-size:__SIZE__% __SIZE__%;
            cursor:grab;
            touch-action:none;
            border-radius:8px;
        }

        .correct {
            outline:3px solid #4caf78;
            cursor:default;
        }

        </style>

        <script>

        (() => {

            const N = __N__;

            const board =
                document.getElementById("board");

            const stats =
                document.getElementById("stats");

            const complete =
                document.getElementById("complete");

            let moves = 0;

            let start = Date.now();

            let dragging = null;


            function shuffle(array) {

                for (
                    let i = array.length - 1;
                    i > 0;
                    i--
                ) {

                    const j =
                        Math.floor(
                            Math.random() * (i + 1)
                        );

                    [
                        array[i],
                        array[j]
                    ] =
                    [
                        array[j],
                        array[i]
                    ];
                }
            }


            function updateStats() {

                const correct =
                    document.querySelectorAll(
                        ".piece.correct"
                    ).length;

                const seconds =
                    Math.floor(
                        (Date.now() - start) / 1000
                    );

                stats.textContent =
                    "Moves: "
                    + moves
                    + " • Correct: "
                    + correct
                    + "/"
                    + (N * N)
                    + " • Time: "
                    + seconds
                    + "s";

                if (correct === N * N) {

                    complete.textContent =
                        "🎉 Puzzle solved!";
                }
            }


            function checkPieces() {

                document
                .querySelectorAll(".piece")
                .forEach(function(piece) {

                    const parent =
                        piece.parentElement;

                    const correct =
                        parent &&
                        Number(piece.dataset.id)
                        ===
                        Number(parent.dataset.slot);

                    piece.classList.toggle(
                        "correct",
                        correct
                    );
                });
            }


            function setup() {

                board.innerHTML = "";

                complete.textContent = "";

                moves = 0;

                start = Date.now();

                let ids =
                    Array.from(
                        {length:N * N},
                        function(_, i) {
                            return i;
                        }
                    );

                shuffle(ids);


                ids.forEach(function(id) {

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
                        : col / (N - 1) * 100;

                    const y =
                        N === 1
                        ? 0
                        : row / (N - 1) * 100;


                    piece.style.backgroundPosition =
                        x + "% " + y + "%";


                    piece.addEventListener(
                        "pointerdown",
                        function(event) {

                            if (
                                piece.classList.contains(
                                    "correct"
                                )
                            ) {
                                return;
                            }

                            dragging = piece;

                            try {

                                piece.setPointerCapture(
                                    event.pointerId
                                );

                            } catch(e) {}
                        }
                    );


                    piece.addEventListener(
                        "pointerup",
                        function(event) {

                            if (!dragging) {
                                return;
                            }

                            const target =
                                document.elementFromPoint(
                                    event.clientX,
                                    event.clientY
                                );

                            const targetSlot =
                                target
                                ? target.closest(".slot")
                                : null;


                            if (targetSlot) {

                                const other =
                                    targetSlot.querySelector(
                                        ".piece"
                                    );

                                const oldParent =
                                    piece.parentElement;


                                if (
                                    other &&
                                    other !== piece
                                ) {

                                    oldParent.appendChild(
                                        other
                                    );
                                }


                                targetSlot.appendChild(
                                    piece
                                );

                                moves++;

                                checkPieces();

                                updateStats();
                            }

                            dragging = null;
                        }
                    );


                    slot.appendChild(piece);

                    board.appendChild(slot);

                });

                updateStats();
            }


            document
            .getElementById("newPuzzle")
            .addEventListener(
                "click",
                setup
            );


            setInterval(
                updateStats,
                1000
            );


            setup();

        })();

        </script>
        """

        puzzle_html = (
            puzzle_html
            .replace("__N__", str(n))
            .replace("__IMAGE__", image_data)
            .replace("__SIZE__", str(n * 100))
        )

        components.html(
            puzzle_html,
            height=730
        )

        if st.button(
            "✅ Record puzzle completion",
            key="record_puzzle"
        ):

            record("puzzles")

            st.session_state.puzzle_history.append(
                {
                    "difficulty": difficulty,
                    "time": time.time()
                }
            )

            st.success(
                "Puzzle activity recorded."
            )


# =========================================================
# AI MOOD & BEHAVIOUR / BEHAVIOUR LAB
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.subheader(
        "🧠 Behaviour Lab"
    )

    st.caption(
        "Educational behaviour and conversational simulations. "
        "These activities do not diagnose or directly measure brain activity."
    )

    st.markdown("### 🧪 Behaviour Lab Equipment")

    behaviour_equipment = st.selectbox(
        "Choose Behaviour Lab equipment",
        BEHAVIOUR_EQUIPMENT,
        key="behaviour_equipment"
    )

    st.info(
        EQUIPMENT[behaviour_equipment]
    )

    st.markdown("### 👤 Lab Character")

    behaviour_character = st.selectbox(
        "Choose character",
        [
            "Nova",
            "Mira",
            "Ray",
            "Zara"
        ],
        key="behaviour_character"
    )

    st.success(
        f"🧑‍🔬 {behaviour_character} is ready at the "
        f"{behaviour_equipment}."
    )

    st.divider()

    tab_voice, tab_text, tab_social = st.tabs(
        [
            "🎙️ Voice Behaviour",
            "⌨️ Text Behaviour",
            "🤝 Social Interaction"
        ]
    )

    # -----------------------------------------------------
    # VOICE
    # -----------------------------------------------------

    with tab_voice:

        st.markdown(
            "### 🎙️ Conversational Behaviour Input"
        )

        audio = None

        try:

            audio = st.audio_input(
                "Record your voice",
                key="mood_audio"
            )

        except Exception:

            st.info(
                "Voice recording is unavailable in this browser. "
                "Use the Text Behaviour tab instead."
            )

        context = st.text_input(
            "Optional context",
            key="mood_context"
        )

        if st.button(
            "🧠 Send Voice to Ayna",
            key="send_mood_voice"
        ):

            if audio:

                answer, source = ask_ai_audio(
                    audio,
                    f"""
You are analysing a short conversational sample
for an educational behaviour laboratory.

Give a cautious broad conversational estimate only.

Choose one primary broad state from:
{', '.join(MOODS)}

Return:
1. emoji
2. broad conversational state
3. confidence: Low / Medium / High
4. one short explanation

Do not diagnose.
Do not infer sensitive traits.
Do not claim to measure brain activity.

Context:
{context[:500]}
"""
                )

                st.success(
                    "Ayna's educational conversational estimate"
                )

                st.write(answer)
                st.caption(source)

                voice_button(
                    answer,
                    "mood_voice_result"
                )

            else:

                st.warning(
                    "No voice recording was detected. "
                    "Please record a voice message or use Text Behaviour."
                )

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    with tab_text:

        st.markdown(
            "### ⌨️ Behavioural Text Task"
        )

        behaviour_text = st.text_area(
            "Tell Ayna what you are thinking or feeling",
            height=130,
            key="mood_text"
        )

        if st.button(
            "✨ Analyse Behavioural Text",
            key="send_mood_text"
        ):

            if behaviour_text.strip():

                answer, source = ask_ai(
                    f"""
Give a cautious educational conversational analysis.

Return:
- one broad state
- one possible behavioural signal
- confidence
- one short explanation

User text:
{behaviour_text}

Do not diagnose.
Do not infer sensitive traits.
Do not claim that the response measures brain activity.
""",
                    max_tokens=300
                )

                st.info(answer)
                st.caption(source)

                voice_button(
                    answer,
                    "mood_text_result"
                )

            else:

                st.warning(
                    "Please enter some text first."
                )

    # -----------------------------------------------------
    # SOCIAL INTERACTION
    # -----------------------------------------------------

    with tab_social:

        st.markdown(
            "### 🤝 Social Interaction Simulator"
        )

        scenario = st.selectbox(
            "Choose scenario",
            [
                "Meeting a new person",
                "Receiving unexpected feedback",
                "Solving a disagreement",
                "Working in a team",
                "Making a difficult decision"
            ],
            key="social_scenario"
        )

        response_style = st.radio(
            "How would you respond?",
            [
                "Calm",
                "Direct",
                "Avoidant",
                "Curious",
                "Emotional"
            ],
            horizontal=True,
            key="social_response_style"
        )

        if st.button(
            "🧠 Run Behaviour Simulation",
            key="run_social_simulation"
        ):

            answer, source = ask_ai(
                f"""
You are running an educational social behaviour simulation.

Scenario:
{scenario}

Selected response style:
{response_style}

Explain:
1. what behavioural tendency the response may represent
2. one alternative response
3. one cognitive process that could be involved

Use cautious language.
Do not diagnose personality or mental illness.
""",
                max_tokens=350
            )

            record("experiments")

            st.success(
                "Behaviour simulation complete."
            )

            st.write(answer)
            st.caption(source)

            voice_button(
                answer,
                "social_result_voice"
            )

    st.divider()

    st.caption(
        "Behavioural responses are context-dependent. "
        "These simulations are educational and should not be "
        "treated as clinical, psychological or neurological diagnosis."
    )


# =========================================================
# BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    st.subheader(
        "🧠 Brain Exercises"
    )

    st.caption(
        "Practice cognitive tasks at your own pace."
    )

    index = (
        time.gmtime().tm_yday - 1
    ) % len(EXPERIMENTS)

    title, domain = EXPERIMENTS[index]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {domain} • "
        f"Equipment: {st.session_state.equipment}"
    )

    submitted = False
    correct = False

    if domain == "Attention":

        response = st.radio(
            "Which sequence contains X?",
            [
                "A B C D",
                "A B X D",
                "A B C E",
                "A X C D"
            ],
            key="exercise_attention"
        )

        submitted = st.button(
            "Check",
            key="exercise_attention_submit"
        )

        correct = (
            response == "A B X D"
        )

    elif domain == "Working Memory":

        st.markdown(
            "### Memorize: 7 2 9 4 1 8"
        )

        response = st.text_input(
            "Enter sequence",
            key="exercise_memory"
        )

        submitted = st.button(
            "Check",
            key="exercise_memory_submit"
        )

        correct = (
            response.replace(
                " ",
                ""
            ) == "729418"
        )

    elif domain == "Decision Making":

        response = st.radio(
            "Choose one",
            [
                "Rs. 1,000 today",
                "Rs. 1,500 after 30 days"
            ],
            key="exercise_decision"
        )

        submitted = st.button(
            "Submit",
            key="exercise_decision_submit"
        )

        correct = True

    elif domain == "Inhibitory Control":

        if not st.session_state.inhib_word:

            st.session_state.inhib_word = random.choice(
                [
                    "RED",
                    "BLUE",
                    "GREEN"
                ]
            )

        word = st.session_state.inhib_word

        st.markdown(
            f"### {word}"
        )

        response = st.selectbox(
            "Response",
            [
                "RED",
                "BLUE",
                "GREEN"
            ],
            key="exercise_inhibition"
        )

        submitted = st.button(
            "Submit",
            key="exercise_inhibition_submit"
        )

        correct = (
            response == word
        )

    elif domain == "Cognitive Flexibility":

        st.write(
            "Continue: Circle → Square → Circle → Square → ?"
        )

        response = st.radio(
            "Your answer",
            [
                "Circle",
                "Square"
            ],
            key="exercise_flexibility"
        )

        submitted = st.button(
            "Check",
            key="exercise_flexibility_submit"
        )

        correct = (
            response == "Circle"
        )

    else:

        st.info(
            "Recall: 3 8 1 6 4 9. "
            "Which target number was present?"
        )

        response = st.text_input(
            "Enter target number",
            key="exercise_recall"
        )

        submitted = st.button(
            "Check",
            key="exercise_recall_submit"
        )

        correct = (
            response.strip() == "6"
        )

    if submitted:

        record("experiments")
        record("games")

        st.session_state.experiment_history.append(
            {
                "title": title,
                "domain": domain,
                "correct": correct
            }
        )

        if correct:

            st.success(
                "🎉 Response recorded."
            )

        else:

            st.warning(
                "Not quite. Treat the result as practice, "
                "not a diagnostic score."
            )

    st.info(
        "Educational cognitive task only. "
        "A single task does not diagnose a condition "
        "or directly measure brain activity."
    )

    if st.button(
        "💡 Ask Ayna for a follow-up challenge",
        key="exercise_followup"
    ):

        answer, source = ask_ai(
            f"""
Give a short educational follow-up challenge
for {title} in cognitive neuroscience.
No diagnosis.
""",
            max_tokens=220
        )

        st.write(answer)
        st.caption(source)

        voice_button(
            answer,
            "exercise_followup_voice"
        )


# =========================================================
# DAILY COGNITIVE EXPERIMENT
# =========================================================

elif st.session_state.page == "Daily Cognitive Experiment":

    st.subheader(
        "🧪 Daily Cognitive Experiment"
    )

    st.caption(
        "One short educational task per day. "
        "Performance is not a clinical or brain-activity measurement."
    )

    index = (
        time.gmtime().tm_yday - 1
    ) % len(EXPERIMENTS)

    title, domain = EXPERIMENTS[index]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {domain} • "
        f"Equipment: {st.session_state.equipment}"
    )

    submitted = False
    correct = False

    if domain == "Attention":

        st.write(
            "Find the X characters in:"
        )

        st.markdown(
            """
            **A X K M X T P X R B X Q**
            """
        )

        response = st.text_input(
            "How many Xs?",
            key="daily_attention"
        )

        submitted = st.button(
            "Check",
            key="daily_attention_submit"
        )

        correct = (
            response.strip() == "4"
        )

    elif domain == "Working Memory":

        st.info(
            "Memorize: 7 2 9 4 1 8"
        )

        response = st.text_input(
            "Enter the sequence",
            key="daily_memory"
        )

        submitted = st.button(
            "Check",
            key="daily_memory_submit"
        )

        correct = (
            response.replace(
                " ",
                ""
            ) == "729418"
        )

    elif domain == "Decision Making":

        response = st.radio(
            "Which option would you choose?",
            [
                "Rs. 1,000 today",
                "Rs. 1,500 after 30 days"
            ],
            key="daily_decision"
        )

        submitted = st.button(
            "Submit",
            key="daily_decision_submit"
        )

        correct = True

    elif domain == "Inhibitory Control":

        if not st.session_state.inhib_word:

            st.session_state.inhib_word = random.choice(
                [
                    "RED",
                    "BLUE",
                    "GREEN"
                ]
            )

        target = st.session_state.inhib_word

        st.markdown(
            f"### Target: {target}"
        )

        response = st.selectbox(
            "Response",
            [
                "RED",
                "BLUE",
                "GREEN"
            ],
            key="daily_inhibition"
        )

        submitted = st.button(
            "Submit",
            key="daily_inhibition_submit"
        )

        correct = (
            response == target
        )

    elif domain == "Cognitive Flexibility":

        st.write(
            "Continue: Circle → Square → Circle → Square → ?"
        )

        response = st.radio(
            "Your answer",
            [
                "Circle",
                "Square"
            ],
            key="daily_flexibility"
        )

        submitted = st.button(
            "Check",
            key="daily_flexibility_submit"
        )

        correct = (
            response == "Circle"
        )

    else:

        st.info(
            "Recall: 3 8 1 6 4 9. "
            "Which target number was present?"
        )

        response = st.text_input(
            "Enter the target number",
            key="daily_recall"
        )

        submitted = st.button(
            "Check",
            key="daily_recall_submit"
        )

        correct = (
            response.strip() == "6"
        )

    if submitted:

        record("experiments")
        record("games")

        result = {
            "title": title,
            "domain": domain,
            "correct": bool(correct),
            "time": time.time()
        }

        st.session_state.experiment_history.append(
            result
        )

        if correct:

            st.success(
                "🎉 Correct. Keep going!"
            )

        else:

            st.warning(
                "Not quite. Treat this as practice, "
                "not a diagnosis."
            )

    if st.button(
        "🤖 Ask Ayna for a Follow-up",
        key="daily_followup"
    ):

        answer, source = ask_ai(
            f"""
Give one short educational follow-up challenge
for {title} in {domain}.
No diagnosis.
""",
            max_tokens=220
        )

        st.write(answer)
        st.caption(source)

        voice_button(
            answer,
            "daily_followup_voice"
        )


# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    st.subheader(
        "📖 Cognitive Neuroscience Research Book"
    )

    st.caption(
        "Search real literature through Europe PMC. "
        "Ayna explains records; she does not invent citations."
    )

    topic = st.text_input(
        "🔎 Search research papers",
        placeholder=(
            "e.g. working memory, attention, dopamine, neuroplasticity"
        ),
        key="research_topic"
    )

    col1, col2 = st.columns(2)

    with col1:

        limit = st.selectbox(
            "Number of papers",
            [
                5,
                10
            ],
            key="research_limit"
        )

    with col2:

        years = st.selectbox(
            "Date filter",
            [
                "All years",
                "Last 5 years",
                "Last 10 years"
            ],
            key="research_years"
        )

    if st.button(
        "🔍 Search Research",
        use_container_width=True,
        key="research_search"
    ):

        if not topic.strip():

            st.warning(
                "Enter a research topic first."
            )

        else:

            query = topic.strip()

            current_year = datetime.utcnow().year

            if years == "Last 5 years":

                query += (
                    f" AND FIRST_PDATE:"
                    f"[{current_year - 5}-01-01 TO "
                    f"{current_year}-12-31]"
                )

            elif years == "Last 10 years":

                query += (
                    f" AND FIRST_PDATE:"
                    f"[{current_year - 10}-01-01 TO "
                    f"{current_year}-12-31]"
                )
            url = (
                "                "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
                "?query="
                + urllib.parse.quote(query)
                + f"&format=json&pageSize={limit}"
            )

            try:

                with urllib.request.urlopen(
                    url,
                    timeout=15
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
                st.session_state.research_history.append(
                    {
                        "topic": topic,
                        "count": len(results)
                    }
                )

                record("research")

            except Exception as error:

                st.error(
                    "Research search could not be completed right now."
                )

                results = []

            if results:

                st.success(
                    f"Found {len(results)} research records."
                )

                for i, paper in enumerate(results):

                    title = (
                        paper.get(
                            "title"
                        )
                        or "Untitled research record"
                    )

                    authors = (
                        paper.get(
                            "authorString"
                        )
                        or "Authors not listed"
                    )

                    journal = (
                        paper.get(
                            "journalTitle"
                        )
                        or "Journal not listed"
                    )

                    year = (
                        paper.get(
                            "pubYear"
                        )
                        or "Year not listed"
                    )

                    doi = paper.get(
                        "doi"
                    )

                    pmid = paper.get(
                        "pmid"
                    )

                    pmcid = paper.get(
                        "pmcid"
                    )

                    abstract = (
                        paper.get(
                            "abstractText"
                        )
                        or "Abstract not available."
                    )

                    with st.expander(
                        f"📄 {i + 1}. {title}"
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

                        if doi:

                            st.write(
                                f"**DOI:** {doi}"
                            )

                        if pmid:

                            st.write(
                                f"**PMID:** {pmid}"
                            )

                        if pmcid:

                            st.write(
                                f"**PMCID:** {pmcid}"
                            )

                        st.markdown(
                            "**Abstract**"
                        )

                        st.write(
                            abstract
                        )

                        if doi:

                            doi_url = (
                                "https://doi.org/"
                                + urllib.parse.quote(
                                    doi,
                                    safe="/"
                                )
                            )

                            st.link_button(
                                "🔗 Open DOI",
                                doi_url
                            )

                        elif pmid:

                            st.link_button(
                                "🔗 Open PubMed",
                                "https://pubmed.ncbi.nlm.nih.gov/"
                                + str(pmid)
                                + "/"
                            )

            else:

                if topic.strip():

                    st.info(
                        "No research records were found "
                        "for this search."
                    )

    st.divider()

    st.markdown(
        "### 🧠 Research Topic Notes"
    )

    book_topic = st.selectbox(
        "Choose a topic",
        list(BOOK),
        key="book_topic"
    )

    overview, research_note = BOOK[
        book_topic
    ]

    st.markdown(
        f"""
        <div class="card">
            <h3>{book_topic}</h3>
            <p>{overview}</p>
            <b>Research note</b>
            <p>{research_note}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    book_question = st.text_input(
        "Ask Ayna about this research topic",
        key="book_question",
        placeholder="Ask a cognitive neuroscience question..."
    )

    if st.button(
        "🤖 Ask Ayna",
        key="book_ask"
    ) and book_question:

        answer, source = ask_ai(
            book_question,
            context=(
                f"Research topic: {book_topic}\n"
                f"Overview: {overview}\n"
                f"Research note: {research_note}"
            ),
            max_tokens=450
        )

        st.write(answer)
        st.caption(source)

        voice_button(
            answer,
            "book_answer_voice"
        )


# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    st.subheader(
        "🤖 Ask Ayna"
    )

    st.caption(
        "Your educational cognitive neuroscience assistant."
    )

    if not st.session_state.messages:

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! I'm Ayna. Ask me about memory, "
                    "attention, learning, emotion, decision-making, "
                    "reward, perception, cognitive control, "
                    "brain systems or neuroplasticity."
                )
            }
        ]

    for i, message in enumerate(
        st.session_state.messages
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
                    f"ask_ayna_voice_{i}"
                )

    try:

        audio = st.audio_input(
            "🎙️ Optional voice message",
            key="public_voice"
        )

    except Exception:

        audio = None

        st.caption(
            "Voice recording is unavailable in this browser. "
            "You can use the text box below."
        )

    if audio:

        if st.button(
            "🎙️ Send Voice",
            key="send_public_voice"
        ):

            answer, source = ask_ai_audio(
                audio,
                """
You are Ayna, an educational cognitive neuroscience assistant.

Listen to the user's voice and answer their question.

Use scientifically cautious language.
Do not diagnose.
Do not claim simple tasks measure brain activity.
Keep the answer concise and useful.
"""
            )

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": "🎙️ Voice message"
                }
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()

    prompt = st.chat_input(
        "Ask Ayna about the brain, behaviour or cognition..."
    )

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        previous = "\n".join(
            [
                f"{m['role']}: {m['content']}"
                for m in st.session_state.messages[-8:]
            ]
        )

        answer, source = ask_ai(
            prompt,
            context=previous,
            max_tokens=500
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.rerun()


# =========================================================
# PRIVATE ASK AYNA
# =========================================================

elif st.session_state.page == "Private Ask Ayna":

    st.subheader(
        "🔐 Private Ask Ayna"
    )

    st.caption(
        "A private educational space for your own research notes."
    )

    if not st.session_state.private_unlocked:

        st.info(
            "Create a PIN for this session or enter your existing PIN."
        )

        pin = st.text_input(
            "PIN",
            type="password",
            max_chars=12,
            key="private_pin_input"
        )

        if st.button(
            "🔓 Unlock Private Ayna",
            type="primary",
            key="private_unlock"
        ):

            if not pin.strip():

                st.warning(
                    "Please enter a PIN."
                )

            elif st.session_state.private_pin_hash is None:

                st.session_state.private_pin_hash = hashlib.sha256(
                    pin.encode(
                        "utf-8"
                    )
                ).hexdigest()

                st.session_state.private_unlocked = True

                st.success(
                    "Private Ask Ayna unlocked for this session."
                )

                st.rerun()

            else:

                entered_hash = hashlib.sha256(
                    pin.encode(
                        "utf-8"
                    )
                ).hexdigest()

                if (
                    entered_hash
                    ==
                    st.session_state.private_pin_hash
                ):

                    st.session_state.private_unlocked = True

                    st.success(
                        "Unlocked."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Incorrect PIN."
                    )

    else:

        st.success(
            "🔓 Private session unlocked."
        )

        if st.button(
            "🔒 Lock Private Session",
            key="lock_private"
        ):

            st.session_state.private_unlocked = False
            st.rerun()

        for i, message in enumerate(
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
                        f"private_voice_{i}"
                    )

        private_prompt = st.chat_input(
            "Ask Ayna privately..."
        )

        if private_prompt:

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "content": private_prompt
                }
            )

            context = "\n".join(
                [
                    f"{m['role']}: {m['content']}"
                    for m in st.session_state.private_messages[-8:]
                ]
            )

            answer, source = ask_ai(
                private_prompt,
                context=(
                    "This is a private research-notes session.\n"
                    + context
                ),
                max_tokens=500
            )

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()


# =========================================================
# MY PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.subheader(
        "📊 My Progress"
    )

    progress = st.session_state.progress

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Experiments",
            progress.get(
                "experiments",
                0
            )
        )

    with col2:

        st.metric(
            "Puzzles",
            progress.get(
                "puzzles",
                0
            )
        )

    with col3:

        st.metric(
            "Games",
            progress.get(
                "games",
                0
            )
        )

    with col4:

        st.metric(
            "Research",
            progress.get(
                "research",
                0
            )
        )

    st.divider()

    st.markdown(
        "### 🧠 Activity Overview"
    )

    if plotly_go:

        labels = [
            "Experiments",
            "Puzzles",
            "Games",
            "Research"
        ]

        values = [
            progress.get(
                "experiments",
                0
            ),
            progress.get(
                "puzzles",
                0
            ),
            progress.get(
                "games",
                0
            ),
            progress.get(
                "research",
                0
            )
        ]

        fig = plotly_go.Figure(
            data=[
                plotly_go.Bar(
                    x=labels,
                    y=values
                )
            ]
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="white"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.write(
            {
                "Experiments": progress.get(
                    "experiments",
                    0
                ),
                "Puzzles": progress.get(
                    "puzzles",
                    0
                ),
                "Games": progress.get(
                    "games",
                    0
                ),
                "Research": progress.get(
                    "research",
                    0
                )
            }
        )

    st.divider()

    st.markdown(
        "### 🧪 Recent Experiments"
    )

    history = st.session_state.experiment_history

    if history:

        for item in reversed(
            history[-10:]
        ):

            if isinstance(item, dict):

                title = (
                    item.get(
                        "title"
                    )
                    or item.get(
                        "experiment"
                    )
                    or "Experiment"
                )

                correct = item.get(
                    "correct"
                )

                if correct is True:

                    status = "✅ Correct"

                elif correct is False:

                    status = "⚪ Practice"

                else:

                    status = "🧪 Completed"

                st.write(
                    f"**{title}** — {status}"
                )

            else:

                st.write(
                    f"🧪 {item}"
                )

    else:

        st.info(
            "No experiments recorded yet."
        )

    st.divider()

    st.markdown(
        "### 📚 Research Searches"
    )

    if st.session_state.research_history:

        for item in reversed(
            st.session_state.research_history[-10:]
        ):

            st.write(
                f"🔎 {item.get('topic', 'Research')} "
                f"— {item.get('count', 0)} records"
            )

    else:

        st.info(
            "No research searches yet."
        )

    st.divider()

    st.markdown(
        "### 🧩 Puzzle History"
    )

    if st.session_state.puzzle_history:

        for item in reversed(
            st.session_state.puzzle_history[-10:]
        ):

            st.write(
                f"🧩 {item.get('difficulty', 'Puzzle')}"
            )

    else:

        st.info(
            "No puzzle activity recorded yet."
        )

    st.caption(
        "Progress reflects activity inside this session. "
        "It is not a medical or cognitive assessment."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience • "
    "Educational simulation • Created by Ayna Jaffri"
)

st.caption(
    "Important: NEUROLENS activities are educational. "
    "They do not diagnose medical or psychiatric conditions "
    "and simple games do not directly measure brain activity."
)
            
