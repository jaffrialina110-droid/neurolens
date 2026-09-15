import os, random, time, hashlib, base64, html
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
    return p if os.path.exists(p) else os.path.join(ROOT, name)


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
    "ayna_reboot_voiced_faster_louder.mp4",
    "ayna_reboot_voiced_louder.mp4",
    "ayna_reboot.mp4",
    "ayna_welcome.mp4",
    "reboot.mp4",
    "welcome.mp4",
    keywords=("ayna", "reboot", "welcome")
)


# Available lab videos
LAB_VIDEOS = {}

for _name, _label in [
    ("cognitive_lab_brain.mp4", "Cognitive Lab Overview"),
    ("brain_animation.mp4", "Brain Animation"),
]:
    _vp = asset_path(_name)

    if os.path.exists(_vp):
        LAB_VIDEOS[_label] = _vp


# =========================================================
# CSS
# =========================================================
st.markdown(
    """
<style>

.stApp{
    background:
        radial-gradient(circle at 15% 5%,#183c63,transparent 30%),
        linear-gradient(135deg,#06101d,#0b1b2d);
}

.block-container{
    max-width:1400px;
    padding-top:1rem;
}

.hero{
    padding:28px;
    border-radius:24px;
    background:linear-gradient(135deg,#122c49,#111a32);
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
        radial-gradient(circle,#285b88 0,#0b1930 28%,#07111f 72%);
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
        radial-gradient(circle,#fff,#8ed1ff 20%,#536bff 55%,#342a7d);
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
        radial-gradient(circle,#153d63,#081321);
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

    "journey_stage": "brain",
    "journey_region": "Prefrontal Cortex",

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

    "lab_running": False,
    "lab_animation": False,
    "lab_setup_applied": False,
    "lab_trial": None,

    "mood_voice_result": None,
    "mood_text_result": None,
    "mood_emoji": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        if isinstance(v, dict):
            st.session_state[k] = v.copy()
        elif isinstance(v, list):
            st.session_state[k] = v.copy()
        else:
            st.session_state[k] = v


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
# BRAIN KNOWLEDGE
# =========================================================
BRAIN = {
    "Prefrontal Cortex": (
        "Supports planning, working memory, cognitive control and goal-directed behaviour.",
        "Planning, decision-making and inhibition.",
        "Prefrontal cortex ↔ basal ganglia ↔ thalamus ↔ cortex"
    ),

    "Hippocampus": (
        "Important for episodic memory formation and spatial representation.",
        "Learning, memory and navigation.",
        "Hippocampus ↔ entorhinal cortex ↔ cortex"
    ),

    "Amygdala": (
        "Processes emotionally significant information and contributes to emotional learning.",
        "Threat processing, salience and emotional learning.",
        "Amygdala ↔ hypothalamus ↔ brainstem/cortex"
    ),

    "Striatum": (
        "Contributes to action selection, reward learning and habits.",
        "Reward learning, action selection and habits.",
        "Cortex → striatum → pallidal pathways → thalamus → cortex"
    ),

    "Anterior Cingulate Cortex": (
        "Contributes to performance monitoring, conflict processing and control.",
        "Conflict, error processing and effort-related control.",
        "ACC ↔ prefrontal ↔ striatal networks"
    ),

    "Cerebellum": (
        "Supports coordination, timing and motor learning and also contributes to cognition.",
        "Timing, balance, coordination and motor learning.",
        "Cerebellum → deep nuclei → thalamus → cortex"
    )
}


NT = {
    "Dopamine":
        "Involved in reward learning, motivation, movement and several cognitive processes.",

    "Serotonin":
        "Involved in mood-related processes, sleep, appetite and many physiological functions.",

    "GABA":
        "A major inhibitory neurotransmitter in the central nervous system.",

    "Glutamate":
        "A major excitatory neurotransmitter important for learning and plasticity.",

    "Acetylcholine":
        "Contributes to attention, learning, memory and neuromuscular communication."
}


BOOK = {
    "Brain & Behaviour": (
        "Behaviour emerges from interacting brain networks, body systems and environment.",
        "Cognitive neuroscience links behaviour to distributed neural systems. Separate correlation, causation, computational models and clinical observations."
    ),

    "Memory": (
        "Memory includes encoding, consolidation, retrieval and reconsolidation.",
        "Episodic, semantic, working and procedural memory involve partly distinct but interacting systems."
    ),

    "Attention": (
        "Attention changes which information receives processing priority.",
        "Attention involves selection, enhancement and suppression interacting with sensory and control networks."
    ),

    "Perception": (
        "Perception is the brain's construction of meaningful representations from sensory input.",
        "Perception reflects interactions among sensory evidence, prior knowledge, attention and context."
    ),

    "Emotion": (
        "Emotion involves interacting brain, body and cognitive processes.",
        "Contemporary models emphasize distributed networks, appraisal, interoception, learning and context."
    ),

    "Decision Making": (
        "Decisions combine goals, rewards, uncertainty, memory and control.",
        "Decision neuroscience examines valuation, learning, uncertainty, evidence accumulation and cognitive control."
    ),

    "Cognitive Control": (
        "Control helps maintain goals and adjust behaviour.",
        "Prefrontal, cingulate, parietal and striatal systems interact in task-dependent control."
    ),

    "Neuroplasticity": (
        "The nervous system can change with development, learning and experience.",
        "Plasticity includes synaptic, circuit and systems-level changes influenced by learning and context."
    )
}


EQUIPMENT = {
    "EEG Scanner":
        "Illustrates measurement of electrical activity at the scalp; educational simulation only.",

    "Eye Tracker":
        "Illustrates measurement of gaze position and fixation patterns.",

    "Reaction-Time Monitor":
        "Measures response latency in a simple cognitive task.",

    "Auditory Attention Station":
        "Presents competing sounds to explore selective attention.",

    "Cognitive Task Screen":
        "Runs structured memory, attention and decision tasks.",

    "Physiological Monitor":
        "Illustrates non-neural physiological signals such as pulse or skin conductance; not a diagnosis."
}


EXPERIMENTS = [
    ("Attention Gate", "Attention"),
    ("Working Memory Sprint", "Working Memory"),
    ("Decision Under Delay", "Decision Making"),
    ("Inhibition Challenge", "Inhibitory Control"),
    ("Cognitive Flexibility", "Cognitive Flexibility"),
    ("Memory Retrieval", "Memory"),
]


MOODS = {
    "Happy": "😊",
    "Excited": "🤩",
    "Calm": "😌",
    "Neutral": "😐",
    "Worried": "😟",
    "Sad": "😔",
    "Frustrated": "😤",
    "Tired": "😴",
}


# =========================================================
# BRAIN IMAGE
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
            v = st.secrets.get(name)

            if v:
                return str(v).strip()

        except Exception:
            pass

        v = os.getenv(name)

        if v:
            return v.strip()

    return None


@st.cache_resource(show_spinner=False)
def make_client(key):
    if genai is None or not key:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


MODEL = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.6-flash"

if MODEL == "gemini-2.5-flash":
    MODEL = "gemini-3.6-flash"


# 10 AI questions per session/day-style usage
AI_LIMIT = 10


def ask_ai(prompt, context="", max_tokens=450):

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
            "Ayna's AI question limit has been reached for this session. "
            "You can continue using the local NEUROLENS activities.",
            "limit"
        )

    client = make_client(get_api_key())

    if client is None:
        return (
            "Ask Ayna is unavailable. Add GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    prompt = f"""
You are Ayna, the AI assistant inside NEUROLENS,
an educational cognitive neuroscience platform.

Be accurate, concise, friendly and scientifically cautious.

Never diagnose a medical or psychiatric condition.

Do not claim that games, voice estimates or self-report scores
directly measure brain activity.

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

            cfg = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_tokens
            )

            r = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=cfg
            )

        else:

            r = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

        text = (
            getattr(r, "text", None)
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


def ask_ai_audio(audio, prompt):

    client = make_client(get_api_key())

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
        return "AI session limit reached.", "limit"

    try:

        st.session_state.ai_requests += 1

        part = types.Part.from_bytes(
            data=audio.getvalue(),
            mime_type=audio.type or "audio/wav"
        )

        r = client.models.generate_content(
            model=MODEL,
            contents=[part, prompt]
        )

        return (
            getattr(r, "text", None)
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
        st.session_state.progress.get(name, 0) + amount
    )


def voice_button(text, key, language="en-US"):

    safe = html.escape(text).replace("`", "\\`")

    components.html(
        f"""
        <button
            onclick="speak()"
            style="
                padding:9px 15px;
                border-radius:10px;
                border:1px solid #789;
                background:#173b5f;
                color:white;
            "
        >
        🔊 Play Ayna
        </button>

        <script>
        function speak(){{
            window.speechSynthesis.cancel();

            let u = new SpeechSynthesisUtterance(`{safe}`);

            u.lang = '{language}';
            u.rate = .92;
            u.pitch = 1.03;

            window.speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=52
    )


def ayna_reboot_welcome():

    text = (
        "Welcome to NeuroLens! I'm Ayna, your cognitive neuroscience "
        "lab assistant. Let's explore the brain, behaviour, and cognition together."
    )

    if REBOOT_VIDEO:
        st.video(REBOOT_VIDEO)

    else:
        st.markdown(
            """
            <div class="lab">
                <div class="orb"></div>
                <b style="position:absolute;top:15px;left:20px">
                    AYNA • NEUROSCIENCE LAB
                </b>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.info(
        "👋 Ayna is ready. Tap the button below if your browser blocks automatic voice playback."
    )

    voice_button(
        text,
        "reboot_voice"
    )


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    lang = st.radio(
        "Language",
        ["English", "Roman English"],
        index=(
            0
            if st.session_state.get("language", "English") == "English"
            else 1
        ),
        key="language_choice"
    )

    st.session_state.language = lang

    st.divider()

    for i, p in enumerate(PAGES):

        if st.button(
            ("● " if p == st.session_state.page else "○ ") + p,
            key=f"nav_{i}",
            use_container_width=True
        ):
            go_to(p)

    st.divider()

    st.caption(
        f"AI requests: {st.session_state.ai_requests}/{AI_LIMIT}"
    )

    st.progress(
        min(
            st.session_state.ai_requests / AI_LIMIT,
            1.0
        )
    )

    st.caption(
        "Local-first design: games, visuals and educational notes do not require AI."
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
                Interactive Cognitive Neuroscience Lab • Created by Ayna Jaffri
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
                <b style="position:absolute;top:15px;left:20px">
                    AYNA • NEUROSCIENCE LAB
                </b>
            </div>
            """,
            unsafe_allow_html=True
        )

    welcome_text = (
        "Welcome to NeuroLens! Main Ayna hoon, aap ki cognitive neuroscience "
        "lab assistant. Aaj hum brain, behaviour aur cognition ko explore karenge."
        if st.session_state.get("language", "English") == "Roman English"
        else
        "Welcome to NeuroLens! I'm Ayna, your cognitive neuroscience lab assistant. "
        "Let's explore the brain, behaviour, and cognition together."
    )

    st.markdown("### 🤖 Ayna")

    st.write(welcome_text)

    voice_button(
        welcome_text,
        "welcome_reboot_voice"
    )

    st.info(
        "Agar video mein voice nahi hai, Play Ayna button browser speech se "
        "Ayna ki voice chalata hai."
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
        "Character → equipment → experiment → apply setup → "
        "run live simulation → perform task → Ayna analysis"
    )

    ayna_reboot_welcome()

    st.divider()

    left, right = st.columns([1.35, 1])

    # -----------------------------------------------------
    # LAB VIDEO + EQUIPMENT
    # -----------------------------------------------------
    with left:

        if LAB_VIDEOS:

            video_label = st.selectbox(
                "🎬 Lab video",
                list(LAB_VIDEOS),
                key="lab_video_select"
            )

            st.video(
                LAB_VIDEOS[video_label]
            )

        elif LAB_VIDEO:

            st.video(LAB_VIDEO)

        else:

            st.markdown(
                """
                <div class="lab">
                    <div class="orb"></div>
                    <div style="position:absolute;top:16px;left:20px">
                        LIVE NEURAL ACTIVITY • SIMULATION
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("### Today's laboratory setup")

        equipment = st.selectbox(
            "🧪 Choose equipment",
            list(EQUIPMENT),
            key="equipment_select"
        )

        st.session_state.equipment = equipment

        st.info(EQUIPMENT[equipment])

        equip_icon = {
            "EEG Scanner": "🧠〰️〰️",
            "Eye Tracker": "👁️↔️",
            "Reaction-Time Monitor": "⚡⏱️",
            "Auditory Attention Station": "🔊👂",
            "Cognitive Task Screen": "🖥️🧠",
            "Physiological Monitor": "❤️📈"
        }[equipment]

        if st.button(
            "👀 Watch Equipment Animation",
            use_container_width=True,
            key="watch_equipment"
        ):
            st.session_state.lab_animation = True

        if st.session_state.lab_animation:

            equipment_html = f"""
            <div style="
                height:170px;
                border-radius:20px;
                background:radial-gradient(circle,#183e63,#07111f);
                display:flex;
                align-items:center;
                justify-content:center;
                color:white;
                font:700 42px Arial;
            ">
                <div style="
                    animation:p 1.2s infinite;
                ">
                    {equip_icon}
                </div>
            </div>

            <style>
            @keyframes p {{
                50% {{
                    transform:scale(1.16);
                    filter:drop-shadow(0 0 18px #70c8ff);
                }}
            }}
            </style>
            """

            components.html(
                equipment_html,
                height=185
            )

    # -----------------------------------------------------
    # CHARACTER + EXPERIMENT
    # -----------------------------------------------------
    with right:

        chars = [
            "Nova",
            "Mira",
            "Ray",
            "Zara"
        ]

        char = st.selectbox(
            "👤 Choose your lab character",
            chars,
            index=chars.index(
                st.session_state.character
            ),
            key="lab_char"
        )

        st.session_state.character = char

        exp_index = (
            (time.gmtime().tm_yday - 1)
            % len(EXPERIMENTS)
        )

        selected_exp = st.selectbox(
            "🧠 Choose experiment",
            [x[0] for x in EXPERIMENTS],
            index=exp_index,
            key="lab_exp_select"
        )

        domain = dict(EXPERIMENTS)[selected_exp]

        st.markdown(
            f"### 🧠 Experiment: {selected_exp}"
        )

        st.caption(
            f"Domain: {domain}"
        )

        if st.button(
            "🧪 Apply Experiment Setup",
            use_container_width=True,
            key="apply_lab_setup",
            type="primary"
        ):

            st.session_state.last_experiment = selected_exp
            st.session_state.lab_setup_applied = True
            st.session_state.lab_running = False
            st.session_state.lab_trial = None

            st.rerun()

        if st.session_state.lab_setup_applied:

            st.success(
                f"👩‍🔬 {char} + {equipment} + "
                f"{selected_exp} setup applied."
            )

        if st.button(
            "▶️ Run Equipment / Experiment",
            use_container_width=True,
            key="run_lab_experiment"
        ):

            st.session_state.lab_running = True
            st.session_state.lab_setup_applied = True
            st.session_state.last_experiment = selected_exp
            st.session_state.lab_trial = None

            st.rerun()

        if st.button(
            "⏹️ Stop Experiment",
            use_container_width=True,
            key="stop_lab_experiment"
        ):

            st.session_state.lab_running = False

            st.rerun()

        if st.button(
            "▶️ Enter experiment",
            use_container_width=True,
            key="enter_today"
        ):

            st.session_state.last_experiment = selected_exp

            go_to("Brain Exercises")

        if st.button(
            "🧠 Enter Brain Journey",
            use_container_width=True,
            key="lab_journey"
        ):

            st.session_state.journey_stage = "brain"

            go_to("Explore Brain")

        if st.button(
            "🧩 Brain Puzzle",
            use_container_width=True,
            key="lab_puzzle"
        ):
            go_to("Brain Puzzle")

        if st.button(
            "🎯 AI Mood & Behaviour",
            use_container_width=True,
            key="lab_mood"
        ):
            go_to("AI Mood & Behaviour")

        if st.button(
            "💬 Ask Ayna",
            use_container_width=True,
            key="lab_ask"
        ):
            go_to("Ask Ayna")

    # -----------------------------------------------------
    # LIVE LAB
    # -----------------------------------------------------
    if st.session_state.lab_running:

        machine_icon = {
            "EEG Scanner": "🧠〰️",
            "Eye Tracker": "👁️🔎",
            "Reaction-Time Monitor": "⚡⏱️",
            "Auditory Attention Station": "🔊👂",
            "Cognitive Task Screen": "🖥️🧠",
            "Physiological Monitor": "❤️📈"
        }[equipment]

        st.markdown(
            "### 🔴 LIVE EXPERIMENT RUNNING"
        )

        live_html = f"""
        <div style="
            height:210px;
            border-radius:22px;
            background:linear-gradient(135deg,#081321,#153d63);
            position:relative;
            overflow:hidden;
            color:white;
            font-family:Arial;
        ">

            <div style="
                position:absolute;
                top:14px;
                left:18px;
                font-weight:700;
            ">
                👩‍🔬 {html.escape(char)}
                • {html.escape(selected_exp)}
            </div>

            <div style="
                position:absolute;
                left:50%;
                top:55%;
                transform:translate(-50%,-50%);
                font-size:62px;
                animation:p 1.1s infinite;
            ">
                {machine_icon}
            </div>

            <div style="
                position:absolute;
                bottom:14px;
                left:18px;
                right:18px;
                height:5px;
                background:#17324b;
                border-radius:9px;
                overflow:hidden;
            ">
                <div style="
                    height:100%;
                    width:55%;
                    background:#70c8ff;
                    animation:scan 1.5s linear infinite;
                ">
                </div>
            </div>
        </div>

        <style>
        @keyframes p {{
            50% {{
                transform:translate(-50%,-50%) scale(1.12);
                filter:drop-shadow(0 0 20px #73c8ff);
            }}
        }}

        @keyframes scan {{
            from {{
                transform:translateX(-110%);
            }}
            to {{
                transform:translateX(210%);
            }}
        }}
        </style>
        """

        components.html(
            live_html,
            height=225
        )

        st.caption(
            "Live scene is a visual simulation; the selected character, "
            "equipment and experiment are reflected in the animated overlay."
        )

        # -------------------------------------------------
        # ATTENTION
        # -------------------------------------------------
        if selected_exp == "Attention Gate":

            if st.session_state.lab_trial is None:

                target = random.choice(
                    ["X", "K", "M", "A"]
                )

                grid = [
                    random.choice("XKMABC")
                    for _ in range(12)
                ]

                grid[
                    random.randrange(12)
                ] = target

                st.session_state.lab_trial = {
                    "target": target,
                    "grid": grid
                }

            tr = st.session_state.lab_trial

            st.write(
                f"**Find target: {tr['target']}**"
            )

            st.code(
                " ".join(tr["grid"])
            )

            ans = st.selectbox(
                "Your answer",
                [
                    "Target present",
                    "Target absent"
                ],
                key="lab_att_ans"
            )

            if st.button(
                "🔵 Submit Attention Result",
                key="lab_att_submit"
            ):

                ok = (
                    tr["target"] in tr["grid"]
                ) == (
                    ans == "Target present"
                )

                st.success(
                    "Correct response recorded."
                    if ok
                    else
                    "Response recorded for practice."
                )

                if ok:
                    record("experiments")

        # -------------------------------------------------
        # WORKING MEMORY
        # -------------------------------------------------
        elif selected_exp == "Working Memory Sprint":

            st.info(
                "Memorize: 7 2 9 4 1 8"
            )

            ans = st.text_input(
                "Recall sequence",
                key="lab_mem_ans"
            )

            if st.button(
                "🔵 Submit Memory Result",
                key="lab_mem_submit"
            ):

                ok = (
                    ans.replace(" ", "")
                    == "729418"
                )

                st.success(
                    "Correct."
                    if ok
                    else
                    "Not quite."
                )

                if ok:
                    record("experiments")

        # -------------------------------------------------
        # DECISION MAKING
        # -------------------------------------------------
        elif selected_exp == "Decision Under Delay":

            ans = st.radio(
                "Choose",
                [
                    "Rs. 1,000 today",
                    "Rs. 1,500 after 30 days"
                ],
                key="lab_dec_ans"
            )

            if st.button(
                "🔵 Submit Decision",
                key="lab_dec_submit"
            ):

                st.success(
                    "Choice recorded. This task explores delay discounting; "
                    "there is no single diagnostic answer."
                )

                record("experiments")

        # -------------------------------------------------
        # INHIBITION
        # -------------------------------------------------
        elif selected_exp == "Inhibition Challenge":

            if st.session_state.lab_trial is None:

                st.session_state.lab_trial = {
                    "colour": random.choice(
                        ["RED", "BLUE", "GREEN"]
                    )
                }

            colour = st.session_state.lab_trial["colour"]

            st.write(
                f"**Stimulus colour: {colour}**"
            )

            ans = st.selectbox(
                "Choose a response",
                ["RED", "BLUE", "GREEN"],
                key="lab_inhib_ans"
            )

            if st.button(
                "🔵 Submit Inhibition Result",
                key="lab_inhib_submit"
            ):

                ok = ans == colour

                st.success(
                    "Correct inhibition response."
                    if ok
                    else
                    "Response recorded as practice."
                )

                if ok:
                    record("experiments")

        # -------------------------------------------------
        # FLEXIBILITY
        # -------------------------------------------------
        elif selected_exp == "Cognitive Flexibility":

            rule = st.radio(
                "Rule",
                [
                    "Odd/even",
                    "Greater/less than 10"
                ],
                key="lab_flex_rule"
            )

            num = st.number_input(
                "Number",
                1,
                30,
                7,
                key="lab_flex_num"
            )

            if st.button(
                "🔵 Submit Flexibility Result",
                key="lab_flex_submit"
            ):

                st.success(
                    f"Rule '{rule}' applied to {num}. "
                    "Result recorded."
                )

                record("experiments")

        # -------------------------------------------------
        # MEMORY RETRIEVAL
        # -------------------------------------------------
        else:

            if st.session_state.lab_trial is None:

                st.session_state.lab_trial = {
                    "word": random.choice(
                        [
                            "planet",
                            "window",
                            "memory",
                            "network",
                            "attention"
                        ]
                    )
                }

            word = st.session_state.lab_trial["word"]

            st.write(
                f"Remember this word: **{word}**"
            )

            ans = st.text_input(
                "Recall word",
                key="lab_recall_ans"
            )

            if st.button(
                "🔵 Submit Retrieval Result",
                key="lab_recall_submit"
            ):

                ok = (
                    ans.strip().lower()
                    == word
                )

                st.success(
                    "Correct."
                    if ok
                    else
                    "Not quite."
                )

                if ok:
                    record("experiments")

    st.markdown("### Lab flow")

    st.write(
        "**Choose character → equipment → experiment → apply setup → "
        "run live simulation → perform task → Ayna explanation → follow-up challenge → research note.**"
    )

    st.caption(
        "Educational simulations are not automatically scientifically validated "
        "research protocols. Publishable research requires literature-based methods, "
        "predefined outcomes, consent and ethics review where applicable."
    )


# =========================================================
# BRAIN JOURNEY
# =========================================================
elif st.session_state.page == "Explore Brain":

    st.subheader("🧠 Brain Journey")

    labels = {
        "brain": "Whole Brain",
        "region": "Brain Region",
        "circuit": "Neural Circuit",
        "neuron": "Neuron",
        "dendrite": "Dendrites",
        "axon": "Axon & Myelin",
        "signal": "Electrical Signal",
        "synapse": "Synapse",
        "nt": "Neurotransmitter",
        "function": "Cognition & Behaviour"
    }

    stage = st.session_state.journey_stage
    region = st.session_state.journey_region

    st.caption(
        " → ".join(labels.values())
    )

    if stage == "brain":

        if JOURNEY_VIDEO:
            st.video(JOURNEY_VIDEO)

        elif brain:
            st.image(
                brain,
                use_container_width=True
            )

        else:
            st.warning(
                "brain.png not found."
            )

        r = st.selectbox(
            "🔎 Choose a brain region",
            list(BRAIN),
            index=list(BRAIN).index(region),
            key="journey_region_select"
        )

        if st.button(
            "🚀 Travel inside this region",
            key="travel_region",
            use_container_width=True
        ):

            st.session_state.journey_region = r
            st.session_state.journey_stage = "region"

            st.rerun()

    elif stage == "region":

        info = BRAIN[region]

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                f"## 🔬 {region}"
            )

            st.info(info[0])

            st.write(
                "**Behavioural relevance:**",
                info[1]
            )

        with c2:

            st.markdown(
                "## 🔗 Circuit context"
            )

            st.code(info[2])

        components.html(
            '<div class="stage"><div class="neuron">🧠</div></div>',
            height=220
        )

        voice_button(
            f"Welcome inside the {region}. "
            "This region contributes to cognition and behaviour "
            "in context with distributed neural systems.",
            "region_voice"
        )

        if st.button(
            "🔗 Enter neural circuit",
            key="enter_circuit",
            use_container_width=True
        ):

            st.session_state.journey_stage = "circuit"

            st.rerun()

    elif stage == "circuit":

        st.markdown(
            f"## 🔗 {region} neural pathway"
        )

        st.code(
            BRAIN[region][2]
        )

        components.html(
            '<div class="stage"><div style="font-size:2.2rem;animation:p 1s infinite">🧠 → ⚙️ → 🔵 → 🧠</div></div>',
            height=220
        )

        st.info(
            "Circuit diagrams represent information flow schematically; "
            "real networks are recurrent, distributed and context-dependent."
        )

        if st.button(
            "🧬 Enter neuron",
            key="enter_neuron2",
            use_container_width=True
        ):

            st.session_state.journey_stage = "neuron"

            st.rerun()

    elif stage == "neuron":

        st.markdown(
            f"## 🧬 Neuron inside {region}"
        )

        components.html(
            '<div class="stage"><div class="neuron">🌳</div></div>',
            height=220
        )

        st.write(
            "A neuron receives inputs through dendrites, integrates "
            "signals in the cell body and can propagate electrical "
            "activity along its axon."
        )

        if st.button(
            "🌿 Explore dendrites",
            key="enter_dendrite",
            use_container_width=True
        ):

            st.session_state.journey_stage = "dendrite"

            st.rerun()

    elif stage == "dendrite":

        st.markdown("## 🌿 Dendrites")

        components.html(
            '<div class="stage"><div style="font-size:5rem;animation:p 1.2s infinite">🌿</div></div>',
            height=220
        )

        st.info(
            "Dendrites receive many synaptic inputs. "
            "Their structure can influence how signals are integrated."
        )

        if st.button(
            "⚡ Follow the axon",
            key="enter_axon",
            use_container_width=True
        ):

            st.session_state.journey_stage = "axon"

            st.rerun()

    elif stage == "axon":

        st.markdown("## ⚡ Axon & Myelin")

        components.html(
            '<div class="stage"><div style="font-size:4rem">🟤━🔵━🔵━🟤</div></div>',
            height=220
        )

        st.info(
            "Myelin insulates many axons and supports rapid saltatory conduction."
        )

        if st.button(
            "⚡ Watch electrical signal",
            key="enter_signal",
            use_container_width=True
        ):

            st.session_state.journey_stage = "signal"

            st.rerun()

    elif stage == "signal":

        st.markdown("## ⚡ Electrical Signal")

        components.html(
            '<div class="stage"><div class="signal">⚡</div></div>',
            height=220
        )

        st.info(
            "An action potential is a rapid change in membrane potential "
            "that propagates along an excitable membrane."
        )

        if st.button(
            "🔗 Enter synapse",
            key="enter_synapse2",
            use_container_width=True
        ):

            st.session_state.journey_stage = "synapse"

            st.rerun()

    elif stage == "synapse":

        st.markdown("## 🔗 Synapse Explorer")

        components.html(
            '<div class="stage"><div class="syn">🟣 • • • • • 🔵</div></div>',
            height=220
        )

        part = st.selectbox(
            "Explore",
            [
                "Presynaptic terminal",
                "Synaptic vesicles",
                "Synaptic cleft",
                "Postsynaptic membrane",
                "Receptors"
            ],
            key="syn_part"
        )

        details = {
            "Presynaptic terminal":
                "Sending side of a chemical synapse.",

            "Synaptic vesicles":
                "Store neurotransmitter for release.",

            "Synaptic cleft":
                "Extracellular space between communicating cells.",

            "Postsynaptic membrane":
                "Receiving membrane containing signalling machinery.",

            "Receptors":
                "Proteins that detect signalling molecules."
        }

        st.info(
            details[part]
        )

        if st.button(
            "🧪 Follow neurotransmitter",
            key="follow_nt2",
            use_container_width=True
        ):

            st.session_state.journey_stage = "nt"

            st.rerun()

    elif stage == "nt":

        st.markdown(
            "## 🧪 Neurotransmitter Explorer"
        )

        n = st.selectbox(
            "Choose neurotransmitter",
            list(NT),
            key="nt2"
        )

        st.success(NT[n])

        components.html(
            '<div class="stage"><div class="syn">🟣 🟣 🟣</div></div>',
            height=220
        )

        if st.button(
            "🧠 Connect to cognition & behaviour",
            key="enter_function",
            use_container_width=True
        ):

            st.session_state.journey_stage = "function"

            st.rerun()

    elif stage == "function":

        st.markdown(
            "## 🧠 Cognition & Behaviour"
        )

        st.info(
            f"{region}: {BRAIN[region][1]}"
        )

        st.write(
            "Cognition and behaviour emerge from interacting neural systems, "
            "bodily states, learning history and environment. A single region "
            "or neurotransmitter rarely explains a complex behaviour by itself."
        )

        voice_button(
            f"The journey connects {region} with cognition and behaviour. "
            "Complex behaviour depends on interacting distributed systems.",
            "function_voice"
        )

        if st.button(
            "🏠 Restart journey",
            key="restart_journey2",
            use_container_width=True
        ):

            st.session_state.journey_stage = "brain"

            st.rerun()

    st.divider()

    st.markdown(
        "### 💬 Ask Ayna about this stage"
    )

    q = st.text_input(
        "Question",
        key="journey_q",
        placeholder="Ask about what you are seeing..."
    )

    if st.button(
        "Ask Ayna",
        key="journey_ask"
    ) and q:

        ans, src = ask_ai(
            q,
            f"Current stage: {labels[stage]}; brain region: {region}."
        )

        st.write(ans)
        st.caption(src)

        voice_button(
            ans,
            "journey_ans"
        )


# =========================================================
# BRAIN PUZZLE
# =========================================================
elif st.session_state.page == "Brain Puzzle":

    st.subheader(
        "🧩 Brain Picture Puzzle"
    )

    st.caption(
        "Drag pieces with mouse or touch and drop them onto slots. "
        "Correct pieces snap into place."
    )

    if not brain:

        st.warning(
            "brain.png is required for the puzzle."
        )

    else:

        diff = st.select_slider(
            "Difficulty",
            [
                "3 × 3",
                "4 × 4",
                "5 × 5"
            ],
            value="3 × 3",
            key="puzzle_diff"
        )

        n = int(diff[0])

        b = BytesIO()

        brain.save(
            b,
            "PNG"
        )

        data = base64.b64encode(
            b.getvalue()
        ).decode()

        html_p = f"""
        <div style='font-family:Arial'>

            <button id='newp'>
                🔀 New Puzzle
            </button>

            <span
                id='stats'
                style='margin-left:12px'
            >
            </span>

            <div id='board'></div>

            <h3 id='done'></h3>

        </div>

        <style>

        #board{{
            display:grid;
            grid-template-columns:repeat({n},1fr);
            gap:6px;
            max-width:800px;
            margin:14px auto;
        }}

        .slot{{
            aspect-ratio:1;
            border:2px dashed #9fb1c8;
            border-radius:10px;
            overflow:hidden;
            background:#102235;
        }}

        .piece{{
            width:100%;
            height:100%;
            background-image:url(data:image/png;base64,{data});
            background-size:{n*100}% {n*100}%;
            cursor:grab;
            touch-action:none;
            border-radius:8px;
        }}

        .correct{{
            outline:3px solid #4caf78;
            cursor:default;
        }}

        </style>

        <script>

        (() => {{

            const N = {n};

            const board =
                document.getElementById('board');

            const stats =
                document.getElementById('stats');

            const done =
                document.getElementById('done');

            let moves = 0;
            let start = Date.now();
            let drag = null;


            function sh(a){{

                for(
                    let i=a.length-1;
                    i>0;
                    i--
                ){{

                    let j =
                        Math.floor(
                            Math.random()*(i+1)
                        );

                    [a[i],a[j]] =
                        [a[j],a[i]];
                }}
            }}


            function update(){{

                let c =
                    [
                        ...document.querySelectorAll(
                            '.piece.correct'
                        )
                    ].length;

                stats.textContent =
                    `Moves: ${{moves}} • Correct: ${{c}}/${{N*N}} • Time: ${{Math.floor((Date.now()-start)/1000)}}s`;

                if(c === N*N){{
                    done.textContent =
                        '🎉 Puzzle solved!';
                }}
            }}


            function setup(){{

                board.innerHTML='';
                done.textContent='';

                moves=0;
                start=Date.now();

                let a =
                    [...Array(N*N).keys()];

                sh(a);

                a.forEach(id => {{

                    let slot =
                        document.createElement(
                            'div'
                        );

                    slot.className='slot';
                    slot.dataset.slot=id;

                    let p =
                        document.createElement(
                            'div'
                        );

                    p.className='piece';
                    p.dataset.id=id;

                    let row =
                        Math.floor(id/N);

                    let col =
                        id%N;

                    p.style.backgroundPosition =
                        `${{col/(N-1)*100}}% ${{row/(N-1)*100}}%`;


                    p.onpointerdown = e => {{

                        if(
                            p.classList.contains(
                                'correct'
                            )
                        ) return;

                        drag=p;

                        p.setPointerCapture(
                            e.pointerId
                        );
                    }};


                    p.onpointerup = e => {{

                        if(!drag) return;

                        let target =
                            document
                                .elementFromPoint(
                                    e.clientX,
                                    e.clientY
                                )
                                ?.closest('.slot');

                        if(target){{

                            let other =
                                target.querySelector(
                                    '.piece'
                                );

                            let old =
                                p.parentElement;

                            if(
                                other &&
                                other!==p
                            ){{
                                old.appendChild(
                                    other
                                );
                            }}

                            target.appendChild(p);

                            moves++;

                            [
                                ...document.querySelectorAll(
                                    '.piece'
                                )
                            ].forEach(x =>

                                x.classList.toggle(
                                    'correct',
                                    +x.dataset.id ===
                                    +x.parentElement.dataset.slot
                                )

                            );

                            update();
                        }}

                        drag=null;
                    }};

                    slot.appendChild(p);

                    board.appendChild(slot);

                }});

                update();
            }}


            document
                .getElementById('newp')
                .onclick=setup;

            setInterval(
                update,
                1000
            );

            setup();

        }})();

        </script>
        """

        components.html(
            html_p,
            height=730
        )

        if st.button(
            "✅ Record puzzle completion",
            key="record_puzzle2"
        ):

            record("puzzles")

            st.session_state.puzzle_history.append(
                {
                    "difficulty": diff,
                    "time": time.time()
                }
            )

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
        "Use voice as the main input, or type. "
        "Ayna provides a broad conversational estimate."
    )

    v, t = st.tabs(
        [
            "🎙️ Voice",
            "⌨️ Text"
        ]
    )

    # -----------------------------------------------------
    # VOICE
    # -----------------------------------------------------
    with v:

        audio = None

        try:

            audio = st.audio_input(
                "Record your voice",
                key="mood_audio"
            )

        except Exception:

            st.info(
                "Voice recording is unavailable in this browser. Use Text."
            )

        ctx = st.text_input(
            "Optional context",
            key="mood_ctx"
        )

        if st.button(
            "🔵 Send Voice",
            key="send_mood_voice"
        ) and audio:

            ans, src = ask_ai_audio(
                audio,
                f"""
Estimate broad conversational affect only.

Choose one primary mood from:
{', '.join(MOODS.keys())}

Give:
- emoji
- mood
- confidence: Low / Medium / High
- one short explanation

Do not diagnose or infer sensitive traits.

Context:
{ctx[:500]}
"""
            )

            st.session_state.mood_voice_result = ans

            st.success(
                "Ayna's broad conversational estimate"
            )

            st.write(ans)

            st.caption(src)

            voice_button(
                ans,
                "mood_voice_result"
            )

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------
    with t:

        txt = st.text_area(
            "Tell Ayna how you feel",
            height=130,
            key="mood_text"
        )

        emoji = st.selectbox(
            "Choose an emoji that best represents your current state",
            [
                "😊 Happy",
                "🤩 Excited",
                "😌 Calm",
                "😐 Neutral",
                "😟 Worried",
                "😔 Sad",
                "😤 Frustrated",
                "😴 Tired"
            ],
            key="mood_emoji_select"
        )

        if st.button(
            "🔵 Send Text",
            key="send_mood_text"
        ) and txt:

            ans, src = ask_ai(
                f"""
Give:
- one emoji
- one primary broad mood
- optional secondary signal
- confidence
- one friendly sentence

User-selected emoji:
{emoji}

Text:
{txt}
""",
                max_tokens=240
            )

            st.session_state.mood_text_result = ans
            st.session_state.mood_emoji = emoji

            st.info(ans)

            st.caption(src)

            voice_button(
                ans,
                "mood_text_result"
            )

    # -----------------------------------------------------
    # COMBINED ANALYSIS
    # -----------------------------------------------------
    st.divider()

    st.markdown(
        "### 🧠 Combined Behaviour Analysis"
    )

    st.caption(
        "Ayna combines the available voice estimate, written text "
        "and selected emoji into one contextual summary."
    )

    if st.button(
        "🧠 Analyse Voice + Text + Emoji",
        key="combined_mood_analysis"
    ):

        combined_context = f"""
VOICE RESULT:
{st.session_state.get("mood_voice_result") or "No voice result supplied."}

TEXT RESULT:
{st.session_state.get("mood_text_result") or "No text result supplied."}

SELECTED EMOJI:
{st.session_state.get("mood_emoji") or "No emoji supplied."}

Original text:
{st.session_state.get("mood_text","")}
"""

        ans, src = ask_ai(
            """
Combine the available inputs into a concise behavioural summary.

Return:
1. apparent broad mood
2. strongest conversational cues
3. how voice, text and emoji agree or differ
4. confidence level
5. one short observation

Do not diagnose.
Do not infer sensitive traits.
Do not claim certainty about the person's internal state.
""",
            combined_context,
            max_tokens=350
        )

        st.success(
            "Combined analysis"
        )

        st.write(ans)

        st.caption(src)

        voice_button(
            ans,
            "combined_mood_voice"
        )

    st.caption(
        "Voice tone, text and emoji can be ambiguous and context-dependent. "
        "Results should not be treated as diagnosis, brain measurement or a "
        "definitive statement about a person's mental state."
    )


# =========================================================
# BRAIN EXERCISES
# =========================================================
elif st.session_state.page == "Brain Exercises":

    st.subheader(
        "🧪 Daily Cognitive Experiment"
    )

    if st.session_state.get("last_experiment"):

        selected_title = st.session_state.last_experiment

        domain = dict(EXPERIMENTS).get(
            selected_title,
            "Cognitive Task"
        )

        title = selected_title

    else:

        index = (
            (time.gmtime().tm_yday - 1)
            % len(EXPERIMENTS)
        )

        title, domain = EXPERIMENTS[index]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {domain} • Equipment: "
        f"{st.session_state.equipment}"
    )

    # -----------------------------------------------------
    # ATTENTION
    # -----------------------------------------------------
    if domain == "Attention":

        x = st.radio(
            "Which sequence contains X?",
            [
                "A B C D",
                "A B X D",
                "A B C E",
                "A X C D"
            ],
            key="ex_att"
        )

        submitted = st.button(
            "Check",
            key="ex_att_submit"
        )

        correct = x == "A B X D"

    # -----------------------------------------------------
    # WORKING MEMORY
    # -----------------------------------------------------
    elif domain == "Working Memory":

        st.markdown(
            "### Memorize: 7 2 9 4 1 8"
        )

        x = st.text_input(
            "Enter sequence",
            key="ex_mem"
        )

        submitted = st.button(
            "Check",
            key="ex_mem_submit"
        )

        correct = (
            x.replace(" ", "")
            == "729418"
        )

    # -----------------------------------------------------
    # DECISION
    # -----------------------------------------------------
    elif domain == "Decision Making":

        x = st.radio(
            "Choose one",
            [
                "Rs. 1,000 today",
                "Rs. 1,500 after 30 days"
            ],
            key="ex_dec"
        )

        submitted = st.button(
            "Submit",
            key="ex_dec_submit"
        )

        correct = True

    # -----------------------------------------------------
    # INHIBITION
    # -----------------------------------------------------
    elif domain == "Inhibitory Control":

        word = st.session_state.get(
            "inhib_word"
        )

        if not word:

            word = random.choice(
                [
                    "RED",
                    "BLUE",
                    "GREEN"
                ]
            )

            st.session_state.inhib_word = word

        st.markdown(
            f"### {word}"
        )

        x = st.selectbox(
            "Response",
            [
                "RED",
                "BLUE",
                "GREEN"
            ],
            key="ex_inhib"
        )

        submitted = st.button(
            "Submit",
            key="ex_inhib_submit"
        )

        correct = x == word

    # -----------------------------------------------------
    # FLEXIBILITY
    # -----------------------------------------------------
    elif domain == "Cognitive Flexibility":

        rule = st.radio(
            "Choose the rule",
            [
                "Odd/even",
                "Greater/less than 10"
            ],
            key="ex_flex_rule"
        )

        num = st.number_input(
            "Number",
            1,
            30,
            7,
            key="ex_flex_num"
        )

        submitted = st.button(
            "Check",
            key="ex_flex_submit"
        )

        correct = True

    # -----------------------------------------------------
    # MEMORY
    # -----------------------------------------------------
    else:

        seq = "7294"

        x = st.text_input(
            "Recall the sequence 7 2 9 4",
            key="ex_recall"
        )

        submitted = st.button(
            "Check",
            key="ex_recall_submit"
        )

        correct = (
            x.replace(" ", "")
            == seq
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------
    if submitted:

        if correct:

            st.success(
                "🎉 Response recorded."
            )

            record("experiments")
            record("games")

            st.session_state.experiment_history.append(
                {
                    "title": title,
                    "domain": domain,
                    "correct": True
                }
            )

        else:

            st.warning(
                "Not quite. Treat the result as practice, "
                "not a diagnostic score."
            )

            st.session_state.experiment_history.append(
                {
                    "title": title,
                    "domain": domain,
                    "correct": False
                }
            )

    st.info(
        "Educational cognitive task only. A single task does not "
        "diagnose a condition or directly measure brain activity."
    )

    if st.button(
        "💡 Ask Ayna for a follow-up challenge",
        key="follow_challenge"
    ):

        ans, src = ask_ai(
            f"""
Give a short educational follow-up challenge
for {title} in cognitive neuroscience.

No diagnosis.
""",
            max_tokens=300
        )

        st.write(ans)

        voice_button(
            ans,
            "followup_voice"
        )


# =========================================================
# RESEARCH BOOK
# =========================================================
elif st.session_state.page == "Research Book":

    st.subheader(
        "📖 Cognitive Neuroscience Research Book"
    )

    mode = st.radio(
        "Mode",
        [
            "Simple Mode",
            "Research Mode"
        ],
        horizontal=True,
        key="book_mode"
    )

    topic = st.selectbox(
        "Topic",
        list(BOOK),
        key="book_topic"
    )

    simple, research = BOOK[topic]

    if mode == "Simple Mode":

        st.info(simple)

        voice_button(
            simple,
            "book_simple_voice"
        )

    else:

        st.info(research)

        st.markdown(
            "### 🔎 Research note"
        )

        st.write(
            "Interpret findings in terms of study design, "
            "measurement, effect size, uncertainty and replication."
        )

        st.markdown(
            "### 📚 Suggested source types"
        )

        st.write(
            "• PubMed-indexed research"
            "\n• peer-reviewed reviews"
            "\n• systematic reviews/meta-analyses"
            "\n• primary articles"
        )

        if st.button(
            "📝 Mark topic explored",
            key="mark_research"
        ):

            record("research")

            st.session_state.research_history.append(
                topic
            )

            st.success(
                "Research topic recorded."
            )

        st.caption(
            "This starter book is an educational research guide. "
            "Use primary papers, systematic reviews and indexed databases "
            "for formal literature review."
        )


# =========================================================
# ASK AYNA
# =========================================================
elif st.session_state.page == "Ask Ayna":

    st.subheader(
        "💬 Ask Ayna"
    )

    st.caption(
        "English | Roman English • Text + voice"
    )

    for m in st.session_state.messages:

        with st.chat_message(
            m["role"]
        ):
            st.markdown(
                m["content"]
            )

    try:

        audio = st.audio_input(
            "🎙️ Optional voice message",
            key="public_voice"
        )

    except Exception:

        audio = None

    if st.button(
        "🔵 Send Voice",
        key="public_voice_send"
    ) and audio:

        language_instruction = (
            "Respond in Roman English."
            if st.session_state.language == "Roman English"
            else
            "Respond in English."
        )

        ans, src = ask_ai_audio(
            audio,
            f"""
Transcribe and answer this user's request.

You are Ayna, an educational cognitive neuroscience assistant.

{language_instruction}

Be concise and scientifically cautious.
"""
        )

        st.session_state.messages += [
            {
                "role": "user",
                "content": "🎙️ Voice message"
            },
            {
                "role": "assistant",
                "content": ans
            }
        ]

        st.rerun()

    q = st.chat_input(
        "Ask Ayna...",
        key="public_chat"
    )

    if q:

        ctx = "\n".join(
            f"{m['role']}: {m['content'][:600]}"
            for m in st.session_state.messages[-6:]
        )

        language_instruction = (
            "Respond in Roman English."
            if st.session_state.language == "Roman English"
            else
            "Respond in English."
        )

        ans, src = ask_ai(
            f"""
{language_instruction}

User question:
{q}
""",
            ctx
        )

        st.session_state.messages += [
            {
                "role": "user",
                "content": q
            },
            {
                "role": "assistant",
                "content": ans
            }
        ]

        st.rerun()

    if st.session_state.messages:

        last = st.session_state.messages[-1]["content"]

        voice_button(
            last,
            "public_last_voice"
        )

        if st.button(
            "🗑️ Clear chat",
            key="clear_public2"
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

    # -----------------------------------------------------
    # FIRST-TIME PIN CREATION
    # -----------------------------------------------------
    if (
        st.session_state.get("private_pin_hash")
        is None
    ):

        st.info(
            "Create your own 4–6 digit Secret PIN for this session."
        )

        new_pin = st.text_input(
            "Create Secret PIN",
            type="password",
            max_chars=6,
            key="create_private_pin"
        )

        confirm_pin = st.text_input(
            "Confirm Secret PIN",
            type="password",
            max_chars=6,
            key="confirm_private_pin"
        )

        if st.button(
            "🔐 Create Private Lock",
            key="create_private_lock"
        ):

            if (
                not new_pin.isdigit()
                or not 4 <= len(new_pin) <= 6
            ):

                st.error(
                    "PIN must contain 4–6 digits."
                )

            elif new_pin != confirm_pin:

                st.error(
                    "PINs do not match."
                )

            else:

                st.session_state.private_pin_hash = (
                    hashlib.sha256(
                        new_pin.encode("utf-8")
                    ).hexdigest()
                )

                st.session_state.private_unlocked = True

                st.success(
                    "Private Ask Ayna lock created."
                )

                st.rerun()

    # -----------------------------------------------------
    # UNLOCK
    # -----------------------------------------------------
    elif not st.session_state.private_unlocked:

        st.write(
            "Enter your Secret PIN to unlock Private Ask Ayna."
        )

        pin = st.text_input(
            "Secret PIN",
            type="password",
            max_chars=6,
            key="private_pin"
        )

        if st.button(
            "🔓 Unlock",
            key="unlock_private"
        ):

            pin_hash = hashlib.sha256(
                pin.encode("utf-8")
            ).hexdigest()

            if (
                pin_hash
                == st.session_state.private_pin_hash
            ):

                st.session_state.private_unlocked = True

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )

        st.caption(
            "The PIN hash is kept in the current session. "
            "This is a session lock, not permanent encrypted storage."
        )

    # -----------------------------------------------------
    # PRIVATE CHAT
    # -----------------------------------------------------
    else:

        st.success(
            "🔓 Private Ask Ayna unlocked"
        )

        for m in st.session_state.private_messages:

            with st.chat_message(
                m["role"]
            ):
                st.markdown(
                    m["content"]
                )

        try:

            pv = st.audio_input(
                "🎙️ Private voice message",
                key="private_voice"
            )

        except Exception:

            pv = None

        if st.button(
            "🔵 Send Voice",
            key="private_voice_send"
        ) and pv:

            ans, src = ask_ai_audio(
                pv,
                """
Answer the user's private message as Ayna.
Be concise, educational and non-clinical.
"""
            )

            st.session_state.private_messages += [
                {
                    "role": "user",
                    "content": "🎙️ Voice message"
                },
                {
                    "role": "assistant",
                    "content": ans
                }
            ]

            st.rerun()

        pq = st.chat_input(
            "Private message to Ayna...",
            key="private_chat"
        )

        if pq:

            ctx = "\n".join(
                f"{m['role']}: {m['content'][:600]}"
                for m in st.session_state.private_messages[-6:]
            )

            ans, _ = ask_ai(
                pq,
                ctx
            )

            st.session_state.private_messages += [
                {
                    "role": "user",
                    "content": pq
                },
                {
                    "role": "assistant",
                    "content": ans
                }
            ]

            st.rerun()

        if st.session_state.private_messages:

            voice_button(
                st.session_state.private_messages[-1]["content"],
                "private_last_voice"
            )

        if st.button(
            "🔒 Lock Private Ask Ayna",
            key="lock_private"
        ):

            st.session_state.private_unlocked = False

            st.rerun()

        if st.button(
            "🗑️ Delete private session",
            key="delete_private2"
        ):

            st.session_state.private_messages = []
            st.session_state.private_unlocked = False
            st.session_state.private_pin_hash = None

            st.rerun()


# =========================================================
# MY PROGRESS
# =========================================================
elif st.session_state.page == "My Progress":

    st.subheader(
        "📊 My Progress"
    )

    p = st.session_state.progress

    cols = st.columns(5)

    for c, (name, key) in zip(
        cols,
        [
            ("Experiments", "experiments"),
            ("Puzzles", "puzzles"),
            ("Games", "games"),
            ("Research", "research"),
            ("Streak", "streak")
        ]
    ):

        c.metric(
            name,
            p.get(key, 0)
        )

    if plotly_go:

        fig = plotly_go.Figure(
            plotly_go.Bar(
                x=[
                    "Experiments",
                    "Puzzles",
                    "Games",
                    "Research"
                ],
                y=[
                    p.get("experiments", 0),
                    p.get("puzzles", 0),
                    p.get("games", 0),
                    p.get("research", 0)
                ]
            )
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown(
        "### 📚 History"
    )

    if st.session_state.experiment_history:

        st.write(
            st.session_state.experiment_history[-10:]
        )

    if st.session_state.research_history:

        st.write(
            "Research topics:",
            st.session_state.research_history[-10:]
        )

    st.info(
        "Progress is session-based in this build. "
        "Permanent accounts/history require authenticated backend storage."
    )


# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • Created by Ayna Jaffri"
)
