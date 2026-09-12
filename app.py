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
        transform:scale(1.1)
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
        transform:translateX(-170px)
    }
    100%{
        transform:translateX(170px)
    }
}

.syn{
    font-size:3rem;
    animation:p .9s infinite;
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

    "inhib_word": None,

    "brain_stage": 0
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
        .encode("utf-8", errors="ignore")
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

        response = client.models.generate_content(
            model=MODEL,
            contents=[part, prompt]
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


def go_to(page):

    st.session_state.page = page
    st.rerun()


def record(name, amount=1):

    st.session_state.progress[name] = (
        st.session_state.progress.get(name, 0)
        + amount
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

            let u =
                new SpeechSynthesisUtterance(
                    `{safe}`
                );

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
        "Welcome to NeuroLens! I'm Ayna, your cognitive "
        "neuroscience lab assistant. Let's explore the brain, "
        "behaviour, and cognition together."
    )

    if REBOOT_VIDEO:
        st.video(REBOOT_VIDEO)

    else:

        st.markdown(
            """
            <div class="lab">
                <div class="orb"></div>
                <b style="
                    position:absolute;
                    top:15px;
                    left:20px;
                ">
                    AYNA • NEUROSCIENCE LAB
                </b>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.info(
        "👋 Ayna is ready. Tap the button below if your "
        "browser blocks automatic voice playback."
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
            st.session_state.ai_requests
            / AI_LIMIT,
            1.0
        )
    )

    st.caption(
        "Local-first design: games, visuals and "
        "educational notes do not require AI."
    )


# =========================================================
# MAIN HEADER
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
        if st.session_state.get(
            "language",
            "English"
        ) == "Roman English"
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
        "browser speech se Ayna ki voice chalata hai. "
        "Lip-sync aur browser voice frame-perfect synchronized nahi hoti."
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

    st.markdown("## 🧪 Interactive Cognitive Neuroscience Lab")

    st.caption(
        "Choose a researcher character, laboratory equipment "
        "and a cognitive experiment."
    )

    # -----------------------------------------------------
    # CHARACTER
    # -----------------------------------------------------

    characters = {
        "Nova": "🧑‍🔬",
        "Mira": "👩‍🔬",
        "Ray": "🧑‍🚀",
        "Zara": "👩‍🚀"
    }

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 👩‍🔬 Researcher")

        selected_character = st.selectbox(
            "Choose your lab character",
            list(characters.keys()),
            index=list(characters.keys()).index(
                st.session_state.character
            ),
            key="lab_character"
        )

        st.session_state.character = selected_character

    with col2:

        st.markdown("### 🔬 Equipment")

        selected_equipment = st.selectbox(
            "Choose laboratory equipment",
            list(EQUIPMENT.keys()),
            index=list(EQUIPMENT.keys()).index(
                st.session_state.equipment
            ),
            key="lab_equipment"
        )

        st.session_state.equipment = selected_equipment

    # -----------------------------------------------------
    # LAB VISUAL
    # -----------------------------------------------------

    st.markdown(
        f"""
        <div class="lab">

            <div style="
                position:absolute;
                top:18px;
                left:20px;
                font-size:18px;
                font-weight:700;
            ">
                {characters[selected_character]}
                {selected_character}
            </div>

            <div class="orb"></div>

            <div style="
                position:absolute;
                bottom:18px;
                left:20px;
                right:20px;
                text-align:center;
                opacity:.85;
            ">
                🔬 {selected_equipment}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if LAB_VIDEO:

        st.markdown("### 🎥 Lab Animation")

        st.video(LAB_VIDEO)

    st.markdown("---")

    # -----------------------------------------------------
    # EQUIPMENT EXPLANATION
    # -----------------------------------------------------

    st.markdown("### 🔬 Equipment")

    st.info(
        EQUIPMENT[selected_equipment]
    )

    # -----------------------------------------------------
    # EXPERIMENT SELECTION
    # -----------------------------------------------------

    st.markdown("### 🧠 Today's Cognitive Experiment")

    experiment_names = [
        item[0]
        for item in EXPERIMENTS
    ]

    experiment_name = st.selectbox(
        "Choose an experiment",
        experiment_names,
        key="lab_experiment"
    )

    experiment_domain = dict(
        EXPERIMENTS
    )[experiment_name]

    st.markdown(
        f"""
        <div class="card">
            <b>Experiment:</b> {experiment_name}<br>
            <b>Cognitive domain:</b> {experiment_domain}
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # EXPERIMENT INSTRUCTIONS
    # -----------------------------------------------------

    experiment_instructions = {

        "Attention Gate":
            "Press the target letter X only when it appears. "
            "Ignore other letters.",

        "Working Memory Sprint":
            "Remember the sequence and enter it after it disappears.",

        "Decision Under Delay":
            "Choose between a smaller immediate reward "
            "and a larger delayed reward.",

        "Inhibition Challenge":
            "Respond to the target while inhibiting the "
            "automatic response.",

        "Cognitive Flexibility":
            "Identify the changing rule and adapt your response.",

        "Memory Retrieval":
            "Study the information briefly and then retrieve "
            "the requested item."
    }

    st.markdown("### 📋 Instructions")

    st.write(
        experiment_instructions.get(
            experiment_name,
            "Complete the task carefully."
        )
    )

    # -----------------------------------------------------
    # START EXPERIMENT
    # -----------------------------------------------------

    if st.button(
        "▶️ Start Experiment",
        type="primary",
        use_container_width=True,
        key="start_lab_experiment"
    ):

        st.session_state.lab_started = True

        st.session_state.active_lab_experiment = (
            experiment_name
        )

        st.session_state.lab_result = None

        st.session_state.lab_start_time = time.time()

        # Generate task data

        if experiment_name == "Working Memory Sprint":

            st.session_state.lab_sequence = "".join(
                str(random.randint(0, 9))
                for _ in range(6)
            )

        elif experiment_name == "Attention Gate":

            st.session_state.attention_target = (
                random.choice(
                    ["X", "K", "M", "R"]
                )
            )

            st.session_state.attention_stimuli = [
                random.choice(
                    ["X", "K", "M", "R", "T", "P"]
                )
                for _ in range(8)
            ]

        elif experiment_name == "Inhibition Challenge":

            st.session_state.inhib_word = random.choice(
                [
                    "RED",
                    "BLUE",
                    "GREEN",
                    "YELLOW"
                ]
            )

        st.rerun()

    # -----------------------------------------------------
    # ACTIVE EXPERIMENT
    # -----------------------------------------------------

    if st.session_state.lab_started:

        active = (
            st.session_state.active_lab_experiment
        )

        st.markdown("---")

        st.markdown(
            f"## 🧠 Active Task — {active}"
        )

        # -------------------------------------------------
        # ATTENTION
        # -------------------------------------------------

        if active == "Attention Gate":

            target = st.session_state.get(
                "attention_target",
                "X"
            )

            stimuli = st.session_state.get(
                "attention_stimuli",
                ["X", "K", "M", "R"]
            )

            st.markdown(
                f"""
                <div class="card"
                     style="text-align:center;font-size:30px;">
                    Target: <b>{target}</b><br><br>
                    {" ".join(stimuli)}
                </div>
                """,
                unsafe_allow_html=True
            )

            response = st.text_input(
                "Which target letter did you identify?",
                key="attention_response"
            )

        # -------------------------------------------------
        # WORKING MEMORY
        # -------------------------------------------------

        elif active == "Working Memory Sprint":

            sequence = st.session_state.get(
                "lab_sequence",
                "729418"
            )

            st.markdown(
                f"""
                <div class="card"
                     style="
                        text-align:center;
                        font-size:34px;
                     ">
                    Memorize:<br>
                    <b>{sequence}</b>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(
                "Try to remember the sequence before submitting."
            )

            response = st.text_input(
                "Enter the sequence",
                key="memory_response"
            )

        # -------------------------------------------------
        # DECISION
        # -------------------------------------------------

        elif active == "Decision Under Delay":

            decision = st.radio(
                "Choose one:",
                [
                    "Rs 1,000 today",
                    "Rs 1,500 after 30 days"
                ],
                key="decision_response"
            )

            response = decision

        # -------------------------------------------------
        # INHIBITION
        # -------------------------------------------------

        elif active == "Inhibition Challenge":

            word = st.session_state.get(
                "inhib_word",
                "RED"
            )

            st.markdown(
                f"""
                <div class="card"
                     style="
                        text-align:center;
                        font-size:35px;
                     ">
                    <b>{word}</b>
                </div>
                """,
                unsafe_allow_html=True
            )

            response = st.selectbox(
                "Select the word
        st.markdown("## 🧠 Cognition & Behaviour"); st.info(f"{region}: {BRAIN[region][1]}")
        st.write("Cognition and behaviour emerge from interacting neural systems, bodily states, learning history and environment. A single region or neurotransmitter rarely explains a complex behaviour by itself.")
        voice_button(f"The journey connects {region} with cognition and behaviour. Complex behaviour depends on interacting distributed systems.","function_voice")
        if st.button("🏠 Restart journey",key="restart_journey2",use_container_width=True): st.session_state.journey_stage="brain"; st.rerun()
    st.divider(); st.markdown("### 💬 Ask Ayna about this stage")
    q=st.text_input("Question",key="journey_q",placeholder="Ask about what you are seeing...")
    if st.button("Ask Ayna",key="journey_ask") and q:
        ans,src=ask_ai(q,f"Current stage: {labels[stage]}; brain region: {region}.")
        st.write(ans); st.caption(src); voice_button(ans,"journey_ans")

# ---------------- PUZZLE ----------------
elif st.session_state.page=="Brain Puzzle":
    st.subheader("🧩 Brain Picture Puzzle")
    st.caption("Drag pieces with mouse or touch and drop them onto slots. Correct pieces snap into place.")
    if not brain: st.warning("brain.png is required for the puzzle.")
    else:
        diff=st.select_slider("Difficulty",["3 × 3","4 × 4","5 × 5"],value="3 × 3",key="puzzle_diff"); n=int(diff[0])
        b=BytesIO(); brain.save(b,"PNG"); data=base64.b64encode(b.getvalue()).decode()
        html_p=f"""<div style='font-family:Arial'><button id='newp'>🔀 New Puzzle</button><span id='stats' style='margin-left:12px'></span><div id='board'></div><h3 id='done'></h3></div><style>#board{{display:grid;grid-template-columns:repeat({n},1fr);gap:6px;max-width:800px;margin:14px auto}}.slot{{aspect-ratio:1;border:2px dashed #9fb1c8;border-radius:10px;overflow:hidden;background:#102235}}.piece{{width:100%;height:100%;background-image:url(data:image/png;base64,{data});background-size:{n*100}% {n*100}%;cursor:grab;touch-action:none;border-radius:8px}}.correct{{outline:3px solid #4caf78;cursor:default}}</style><script>(()=>{{const N={n},board=document.getElementById('board'),stats=document.getElementById('stats'),done=document.getElementById('done');let moves=0,start=Date.now(),drag=null;function sh(a){{for(let i=a.length-1;i>0;i--){{let j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}}}}function update(){{let c=[...document.querySelectorAll('.piece.correct')].length;stats.textContent=`Moves: ${{moves}} • Correct: ${{c}}/${{N*N}} • Time: ${{Math.floor((Date.now()-start)/1000)}}s`;if(c===N*N)done.textContent='🎉 Puzzle solved!'}}function setup(){{board.innerHTML='';done.textContent='';moves=0;start=Date.now();let a=[...Array(N*N).keys()];sh(a);a.forEach(id=>{{let slot=document.createElement('div');slot.className='slot';slot.dataset.slot=id;let p=document.createElement('div');p.className='piece';p.dataset.id=id;let row=Math.floor(id/N),col=id%N;p.style.backgroundPosition=`${{col/(N-1)*100}}% ${{row/(N-1)*100}}%`;p.onpointerdown=e=>{{if(p.classList.contains('correct'))return;drag=p;p.setPointerCapture(e.pointerId)}};p.onpointerup=e=>{{if(!drag)return;let target=document.elementFromPoint(e.clientX,e.clientY)?.closest('.slot');if(target){{let other=target.querySelector('.piece'),old=p.parentElement;if(other&&other!==p)old.appendChild(other);target.appendChild(p);moves++;[...document.querySelectorAll('.piece')].forEach(x=>x.classList.toggle('correct',+x.dataset.id===+x.parentElement.dataset.slot));update()}}drag=null}};slot.appendChild(p);board.appendChild(slot)}});update()}}document.getElementById('newp').onclick=setup;setInterval(update,1000);setup()}})()</script>"""
        components.html(html_p,height=730)
        if st.button("✅ Record puzzle completion",key="record_puzzle2"): record("puzzles"); st.session_state.puzzle_history.append({"difficulty":diff,"time":time.time()}); st.success("Puzzle activity recorded.")

# ---------------- MOOD ----------------
elif st.session_state.page=="AI Mood & Behaviour":
    st.subheader("🎯 AI Mood & Behaviour")
    st.write("Use voice as the main input, or type. This is an educational conversational estimate, not a clinical assessment.")
    v,t=st.tabs(["🎙️ Voice","⌨️ Text"])
    with v:
        audio=None
        try: audio=st.audio_input("Record your voice",key="mood_audio")
        except Exception: st.info("Voice recording is unavailable in this browser. Use Text.")
        ctx=st.text_input("Optional context",key="mood_ctx")
        if st.button("🧠 Send Voice to Ayna",key="send_mood_voice") and audio:
            ans,src=ask_ai_audio(audio,f"Estimate broad conversational affect only. Choose one primary mood from {', '.join(MOODS)}. Give emoji, mood, confidence (Low/Medium/High), and one short explanation. Do not diagnose or infer sensitive traits. Context: {ctx[:500]}")
            st.success("Ayna's broad conversational estimate"); st.write(ans); st.caption(src); voice_button(ans,"mood_voice_result")
    with t:
        txt=st.text_area("Tell Ayna how you feel",height=130,key="mood_text")
        if st.button("✨ Send Text to Ayna",key="send_mood_text") and txt:
            ans,src=ask_ai(f"Give one emoji, one primary broad mood from {', '.join(MOODS)}, optional secondary signal, confidence and one friendly sentence for this text:\n{txt}",max_tokens=240)
            st.info(ans); st.caption(src); voice_button(ans,"mood_text_result")
    st.caption("Voice tone and text can be ambiguous and context-dependent. Results should not be treated as diagnosis, brain measurement or a definitive statement about a person's mental state.")

# ---------------- EXERCISES ----------------
elif st.session_state.page=="Brain Exercises":
    st.subheader("🧠 Brain Exercises")
    st.caption("Practice cognitive tasks at your own pace.")
    index=(time.gmtime().tm_yday-1)%len(EXPERIMENTS); title,domain=EXPERIMENTS[index]
    st.markdown(f"## {title}"); st.caption(f"Domain: {domain} • Equipment: {st.session_state.equipment}")
    if domain=="Attention":
        x=st.radio("Which sequence contains X?",["A B C D","A B X D","A B C E","A X C D"],key="ex_att"); submitted=st.button("Check",key="ex_att_submit"); correct=x=="A B X D"
    elif domain=="Working Memory":
        st.markdown("### Memorize: 7 2 9 4 1 8"); x=st.text_input("Enter sequence",key="ex_mem"); submitted=st.button("Check",key="ex_mem_submit"); correct=x.replace(" ","")=="729418"
    elif domain=="Decision Making":
        x=st.radio("Choose one",["Rs. 1,000 today","Rs. 1,500 after 30 days"],key="ex_dec"); submitted=st.button("Submit",key="ex_dec_submit"); correct=True
    elif domain=="Inhibitory Control":
        word=st.session_state.get("inhib_word")
        if not word: word=random.choice(["RED","BLUE","GREEN"]); st.session_state.inhib_word=word
        st.markdown(f"### {word}"); x=st.selectbox("Response",["RED","BLUE","GREEN"],key="ex_inhib"); submitted=st.button("Submit",key="ex_inhib_submit"); correct=x==word
    elif domain=="Cognitive Flexibility":
        rule=st.radio("Choose the rule",["Odd/even","Greater/less than 10"],key="ex_flex_rule"); num=st.number_input("Number",1,30,7,key="ex_flex_num"); submitted=st.button("Check",key="ex_flex_submit"); correct=True
    else:
        seq="7294"; x=st.text_input("Recall the sequence 7 2 9 4",key="ex_recall"); submitted=st.button("Check",key="ex_recall_submit"); correct=x.replace(" ","")==seq
    if submitted:
        if correct:
            st.success("🎉 Response recorded."); record("experiments"); record("games"); st.session_state.experiment_history.append({"title":title,"domain":domain,"correct":True})
        else:
            st.warning("Not quite. Treat the result as practice, not a diagnostic score."); st.session_state.experiment_history.append({"title":title,"domain":domain,"correct":False})
    st.info("Educational cognitive task only. A single task does not diagnose a condition or directly measure brain activity.")
    if st.button("💡 Ask Ayna for a follow-up challenge",key="follow_challenge"):
        ans,src=ask_ai(f"Give a short educational follow-up challenge for {title} in cognitive neuroscience. No diagnosis.")
        st.write(ans); voice_button(ans,"followup_voice")

# ---------------- DAILY COGNITIVE EXPERIMENT ----------------
elif st.session_state.page=="Daily Cognitive Experiment":
    st.subheader("🧪 Daily Cognitive Experiment")
    st.caption("One short educational task per day. Performance is not a clinical or brain-activity measurement.")
    index=(time.gmtime().tm_yday-1)%len(EXPERIMENTS)
    title,domain=EXPERIMENTS[index]
    st.markdown(f"## {title}")
    st.caption(f"Domain: {domain} • Equipment: {st.session_state.equipment}")

    if domain=="Attention":
        st.write("Find the X characters in: A  X  K  M  X  T  P  X  R  B  X  Q")
        response=st.text_input("How many Xs?",key="daily_attention")
        submitted=st.button("Check",key="daily_attention_submit")
        correct=response.strip()=="4"
    elif domain=="Working Memory":
        st.info("Memorize: 7 2 9 4 1 8")
        response=st.text_input("Enter the sequence",key="daily_memory")
        submitted=st.button("Check",key="daily_memory_submit")
        correct=response.replace(" ","")=="729418"
    elif domain=="Decision Making":
        response=st.radio("Which option would you choose?",["Rs. 1,000 today","Rs. 1,500 after 30 days"],key="daily_decision")
        submitted=st.button("Submit",key="daily_decision_submit")
        correct=True
    elif domain=="Inhibitory Control":
        if not st.session_state.inhib_word:
            st.session_state.inhib_word=random.choice(["RED","BLUE","GREEN"])
        target=st.session_state.inhib_word
        st.markdown(f"### Target: {target}")
        response=st.selectbox("Response",["RED","BLUE","GREEN"],key="daily_inhibition")
        submitted=st.button("Submit",key="daily_inhibition_submit")
        correct=response==target
    elif domain=="Cognitive Flexibility":
        st.write("Continue: Circle → Square → Circle → Square → ?")
        response=st.radio("Your answer",["Circle","Square"],key="daily_flex")
        submitted=st.button("Check",key="daily_flex_submit")
        correct=response=="Circle"
    else:
        st.info("Recall: 3 8 1 6 4 9. Which target number was present?")
        response=st.text_input("Enter the target number",key="daily_recall")
        submitted=st.button("Check",key="daily_recall_submit")
        correct=response.strip()=="6"

    if submitted:
        record("experiments")
        record("games")
        result={"title":title,"domain":domain,"correct":bool(correct),"time":time.time()}
        st.session_state.experiment_history.append(result)
        if correct:
            st.success("🎉 Correct. Keep going!")
        else:
            st.warning("Not quite. Treat this as practice, not a diagnosis.")

    if st.button("🤖 Ask Ayna for a Follow-up",key="daily_followup"):
        answer,src=ask_ai(f"Give one short educational follow-up challenge for {title} in {domain}. No diagnosis.",max_tokens=220)
        st.write(answer)
        st.caption(src)
        voice_button(answer,"daily_followup_voice")

# ---------------- RESEARCH BOOK ----------------
elif st.session_state.page=="Research Book":
    st.subheader("📖 Cognitive Neuroscience Research Book")
    st.caption("Search real literature through Europe PMC. Ayna explains records; she does not invent citations.")

    topic=st.text_input(
        "🔎 Search research papers",
        placeholder="e.g. working memory, attention, dopamine, neuroplasticity",
        key="real_research_topic"
    )
    c1,c2=st.columns(2)
    with c1:
        limit=st.selectbox("Number of papers",[5,10],key="real_research_limit")
    with c2:
        years=st.selectbox("Date filter",["All years","Last 5 years","Last 10 years"],key="real_research_years")

    if st.button("🔍 Search Research",use_container_width=True,key="real_research_search"):
        if not topic.strip():
            st.warning("Enter a research topic first.")
        else:
            import urllib.parse
            import urllib.request
            import json
            from datetime import datetime

            q=topic.strip()
            current_year=datetime.utcnow().year
            if years=="Last 5 years":
                q += f" AND FIRST_PDATE:[{current_year-5}-01-01 TO {current_year}-12-31]"
            elif years=="Last 10 years":
                q += f" AND FIRST_PDATE:[{current_year-10}-01-01 TO {current_year}-12-31]"

            url=(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
                f"?query={urllib.parse.quote_plus(q)}&format=json&pageSize={limit}"
            )
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"NEUROLENS Research Book/1.0"})
                with st.spinner("Searching Europe PMC..."):
                    with urllib.request.urlopen(req,timeout=20) as response:
                        data=json.loads(response.read().decode("utf-8"))
                results=data.get("resultList",{}).get("result",[])
                st.session_state.research_results=results
                if results:
                    record("research")
                    st.success(f"Found {len(results)} research record(s).")
                else:
                    st.info("No papers matched this search.")
            except Exception as e:
                st.error("Research search failed. Please try again.")
            for i,r in enumerate(st.session_state.research_results):
                title=r.get("title","Untitled paper")
                authors=r.get("authorString","Authors not listed")
                journal=r.get("journalTitle","Journal not listed")
                year=r.get("pubYear","Year n/a")
                doi=r.get("doi")
                pmid=r.get("pmid")
                pmcid=r.get("pmcid")
                abstract=r.get("abstractText","")
                st.markdown(f"### {i+1}. {title}")
                st.write(f"**Authors:** {authors}")
                st.write(f"**Journal:** {journal} • **Year:** {year}")
                if doi: st.write(f"**DOI:** {doi}")
                if pmid:
                    st.markdown(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
                if pmcid:
                    st.markdown(f"[Europe PMC full text](https://europepmc.org/articles/{pmcid})")
                if abstract:
                    with st.expander("📄 Abstract"):
                        st.write(abstract)
                st.divider()

# ---------------- ASK AYNA ----------------
elif st.session_state.page=="Ask Ayna":
    st.subheader("🤖 Ask Ayna")
    st.caption("Educational cognitive neuroscience assistant — not a diagnostic system.")

    if not st.session_state.messages:
        st.info("Ask about memory, attention, learning, emotion, decision-making, reward, perception, cognitive control, brain systems or neuroplasticity.")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    prompt=st.chat_input("Ask Ayna about the brain, cognition or behaviour...")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Ayna is thinking..."):
                answer,src=ask_ai(prompt,max_tokens=700)
            st.write(answer)
            st.caption(src)
            st.session_state.messages.append({"role":"assistant","content":answer})
            st.session_state.ai_requests+=1
            voice_button(answer,"ask_ayna_voice")

# ---------------- PRIVATE ASK AYNA ----------------
elif st.session_state.page=="Private Ask Ayna":
    st.subheader("🔐 Private Ask Ayna")
    st.caption("Create your own 4–6 digit session PIN. The PIN is hashed in the current session; it is not a permanent authentication system.")

    if st.session_state.private_pin_hash is None:
        st.info("Create your personal PIN to open your private research/chat space.")
        new_pin=st.text_input("Create PIN",type="password",max_chars=6,key="new_private_pin")
        confirm_pin=st.text_input("Confirm PIN",type="password",max_chars=6,key="confirm_private_pin")

        if st.button("🔒 Create Private PIN",key="create_private_pin"):
            if not new_pin.isdigit() or not 4<=len(new_pin)<=6:
                st.error("PIN must contain only 4–6 digits.")
            elif new_pin!=confirm_pin:
                st.error("PINs do not match.")
            else:
                st.session_state.private_pin_hash=hashlib.sha256(new_pin.encode()).hexdigest()
                st.session_state.private_unlocked=True
                st.success("Private PIN created for this session.")
                st.rerun()

    elif not st.session_state.private_unlocked:
        pin=st.text_input("Enter your PIN",type="password",max_chars=6,key="private_unlock_pin")
        if st.button("🔓 Unlock",key="unlock_private"):
            if hashlib.sha256(pin.encode()).hexdigest()==st.session_state.private_pin_hash:
                st.session_state.private_unlocked=True
                st.success("Unlocked.")
                st.rerun()
            else:
                st.error("Incorrect PIN.")

    else:
        st.success("🔓 Private space unlocked.")

        if st.session_state.private_messages:
            for m in st.session_state.private_messages:
                with st.chat_message(m["role"]):
                    st.write(m["content"])

        private_prompt=st.chat_input("Private Ask Ayna...",key="private_chat_input")

        if private_prompt:
            st.session_state.private_messages.append({"role":"user","content":private_prompt})

            with st.chat_message("user"):
                st.write(private_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Ayna is thinking..."):
                    answer,src=ask_ai(
                        private_prompt,
                        system_extra="This is a private research workspace. Be scientifically cautious. Do not diagnose. Do not invent references.",
                        max_tokens=700
                    )
                st.write(answer)
                st.caption(src)
                st.session_state.private_messages.append({"role":"assistant","content":answer})
                voice_button(answer,"private_voice")

        st.divider()

        c1,c2=st.columns(2)

        with c1:
            if st.button("🔒 Lock Private Space",key="lock_private"):
                st.session_state.private_unlocked=False
                st.rerun()

        with c2:
            if st.button("🗑️ Delete Private Session",key="delete_private"):
                st.session_state.private_messages=[]
                st.session_state.private_pin_hash=None
                st.session_state.private_unlocked=False
                st.success("Private session deleted.")
                st.rerun()

# ---------------- PROGRESS ----------------
elif st.session_state.page=="My Progress":
    st.subheader("📊 My Progress")

    p=st.session_state.progress

    c1,c2,c3,c4=st.columns(4)

    c1.metric("🧪 Experiments",p.get("experiments",0))
    c2.metric("🎮 Games",p.get("games",0))
    c3.metric("🧩 Puzzles",p.get("puzzles",0))
    c4.metric("📚 Research",p.get("research",0))

    st.divider()

    st.markdown("### Your NeuroLens activity")

    chart_data={
        "Activity":["Experiments","Games","Puzzles","Research","AI Requests"],
        "Count":[
            p.get("experiments",0),
            p.get("games",0),
            p.get("puzzles",0),
            p.get("research",0),
            st.session_state.ai_requests
        ]
    }

    try:
        import plotly.graph_objects as plotly_go

        fig=plotly_go.Figure(
            data=[
                plotly_go.Bar(
                    x=chart_data["Activity"],
                    y=chart_data["Count"]
                )
            ]
        )

        fig.update_layout(
            title="NeuroLens Activity",
            height=400,
            margin=dict(l=20,r=20,t=60,b=20)
        )

        st.plotly_chart(fig,use_container_width=True)

    except Exception:
        st.write(chart_data)

    st.info(
        "Progress is session-based in this version. "
        "It records activities completed during the current app session."
    )

    if st.session_state.experiment_history:
        st.markdown("### 🧪 Recent experiment activity")

        for item in reversed(st.session_state.experiment_history[-10:]):
            status="✅ Correct" if item.get("correct") else "❌ Practice"
            st.write(
                f"**{item.get('title','Experiment')}** — "
                f"{item.get('domain','Cognition')} — {status}"
            )

    if st.session_state.research_results:
        st.markdown("### 📚 Current research results")

        st.write(
            f"{len(st.session_state.research_results)} "
            "research record(s) currently loaded."
        )

# ---------------- FOOTER ----------------
st.divider()

st.caption(
    "NEUROLENS — Explore cognition, behavior & the brain"
)

st.caption(
    "Educational research and cognitive exploration platform. "
    "Games, self-reports and conversational outputs are not clinical diagnoses "
    "and do not directly measure brain activity."
)

st.caption(
    "Creator: Ayna Jaffri • Independent cognitive neuroscience researcher"
)


