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

st.set_page_config(page_title="NEUROLENS", page_icon="🧠", layout="wide")

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

# Ayna reboot video
REBOOT_VIDEO = find_video(
    "ayna_reboot.mp4",
    "ayna_welcome.mp4",
    "reboot.mp4",
    "welcome.mp4",
    keywords=("ayna", "reboot", "welcome")
)


st.markdown(
    """
<style>
.stApp{
    background:
    radial-gradient(circle at 15% 5%,#183c63,transparent 30%),
    linear-gradient(135deg,#06101d,#0b1b2d)
}

.block-container{
    max-width:1400px;
    padding-top:1rem
}

.hero{
    padding:28px;
    border-radius:24px;
    background:linear-gradient(135deg,#122c49,#111a32);
    border:1px solid #45617d;
    margin-bottom:18px
}

.card{
    padding:18px;
    border-radius:18px;
    background:#0d2035;
    border:1px solid #294560;
    margin:8px 0
}

.lab{
    min-height:320px;
    border-radius:24px;
    position:relative;
    overflow:hidden;
    background:
    radial-gradient(circle,#285b88 0,#0b1930 28%,#07111f 72%);
    border:1px solid #36536d
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
    animation:p 2.3s infinite
}

@keyframes p{
    50%{
        transform:scale(1.1)
    }
}

.small{
    opacity:.78;
    font-size:.9rem
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
    overflow:hidden
}

.neuron{
    font-size:5rem;
    animation:p 1.5s infinite
}

.signal{
    font-size:3rem;
    animation:move 2s linear infinite
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
    animation:p .9s infinite
}
</style>
""",
    unsafe_allow_html=True
)


# ---------------- STATE ----------------

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
    "progress": fresh_progress(),
    "ai_requests": 0,
    "ai_cache": {},
    "last_experiment": None,
    "experiment_history": [],
    "puzzle_history": [],
    "research_history": []
}


for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = (
            v.copy()
            if isinstance(v, dict)
            else (v.copy() if isinstance(v, list) else v)
        )


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
    "My Progress"
]


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
        "Cognitive neuroscience links behaviour to distributed neural systems. "
        "Separate correlation, causation, computational models and clinical observations."
    ),

    "Memory": (
        "Memory includes encoding, consolidation, retrieval and reconsolidation.",
        "Episodic, semantic, working and procedural memory involve partly distinct "
        "but interacting systems."
    ),

    "Attention": (
        "Attention changes which information receives processing priority.",
        "Attention involves selection, enhancement and suppression interacting "
        "with sensory and control networks."
    ),

    "Perception": (
        "Perception is the brain's construction of meaningful representations from sensory input.",
        "Perception reflects interactions among sensory evidence, prior knowledge, "
        "attention and context."
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


@st.cache_data(show_spinner=False)
def load_brain():
    try:
        if os.path.exists(BRAIN_PATH):
            return Image.open(BRAIN_PATH).convert("RGB")
    except Exception:
        pass

    return None


brain = load_brain()


# ---------------- AI ----------------

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


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

AI_LIMIT = 140


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
                color:white
            "
        >
            🔊 Play Ayna
        </button>

        <script>
        function speak(){{
            window.speechSynthesis.cancel();

            let u = new SpeechSynthesisUtterance(
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
                <b style="
                    position:absolute;
                    top:15px;
                    left:20px
                ">
                    AYNA • NEUROSCIENCE LAB
                </b>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.info(
        "👋 Ayna is ready. Tap the button below "
        "if your browser blocks automatic voice playback."
    )

    voice_button(
        text,
        "reboot_voice"
    )


# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    lang = st.radio(
        "Language",
        ["English", "Roman English"],
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

    for i, p in enumerate(PAGES):

        if st.button(
            ("● " if p == st.session_state.page else "○ ") + p,
            key=f"nav_{i}",
            use_container_width=True
        ):
            go_to(p)

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


# ---------------- HEADER ----------------

if st.session_state.page != "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">
            <h1>🧠 NEUROLENS</h1>
            <p>Explore cognition, behaviour & the brain</p>
            <small>
                Interactive Cognitive Neuroscience Lab •
                Created by Ayna Jaffri
            </small>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------- WELCOME REBOOT ----------------

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
                <b style="
                    position:absolute;
                    top:15px;
                    left:20px
                ">
                    AYNA • NEUROSCIENCE LAB
                </b>
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.session_state.get(
        "language",
        "English"
    ) == "Roman English":

        welcome_text = (
            "Welcome to NeuroLens! Main Ayna hoon, "
            "aap ki cognitive neuroscience lab assistant. "
            "Aaj hum brain, behaviour aur cognition ko explore karenge."
        )

    else:

        welcome_text = (
            "Welcome to NeuroLens! I'm Ayna, your cognitive neuroscience "
            "lab assistant. Let's explore the brain, behaviour, and cognition together."
        )

    st.markdown("### 🤖 Ayna")

    st.write(welcome_text)

    voice_button(
        welcome_text,
        "welcome_reboot_voice"
    )

    st.info(
        "Agar video mein voice nahi hai, Play Ayna button browser "
        "speech se Ayna ki voice chalata hai. Lip-sync aur browser "
        "voice frame-perfect synchronized nahi hoti."
    )

    if st.button(
        "🚀 Enter NeuroLens",
        use_container_width=True,
        type="primary",
        key="enter_neurolens"
    ):
        go_to("Lab")


# ---------------- LAB ----------------

if st.session_state.page == "Lab":

    st.subheader(
        "🔬 Interactive Cognitive Neuroscience Lab"
    )

    ayna_reboot_welcome()

    st.divider()

    left, right = st.columns([1.35, 1])

    with left:

        if LAB_VIDEO:

            st.video(LAB_VIDEO)

        else:

            st.markdown(
                """
                <div class="lab">
                    <div class="orb"></div>
                    <div style="
                        position:absolute;
                        top:16px;
                        left:20px
                    ">
                        LIVE NEURAL ACTIVITY • SIMULATION
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            "### Today's laboratory setup"
        )

        equipment = st.selectbox(
            "🧪 Choose equipment",
            list(EQUIPMENT),
            key="equipment_select"
        )

        st.info(
            EQUIPMENT[equipment]
        )

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

        st.success(
            f"🧑‍🔬 {char} is ready with the {equipment}."
        )

        exp_index = (
            (time.gmtime().tm_yday - 1)
            % len(EXPERIMENTS)
        )

        title, domain = EXPERIMENTS[exp_index]

        st.markdown(
            f"### 🧠 Today's experiment: {title}"
        )

        st.caption(
            f"Domain: {domain}"
        )

        if st.button(
            "▶️ Enter experiment",
            use_container_width=True,
            key="enter_today"
        ):

            st.session_state.last_experiment = title

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

    st.markdown("### Lab flow")

    st.write(
        "**Choose character → equipment → experiment → "
        "perform task → Ayna explanation → follow-up challenge → research note.**"
    )

    st.caption(
        "Educational simulations are not automatically scientifically "
        "validated research protocols. Publishable research requires "
        "literature-based methods, predefined outcomes, consent and "
        "ethics review where applicable."
        # ---------------- EXPLORE BRAIN / BRAIN JOURNEY ----------------

if st.session_state.page == "Explore Brain":

    st.subheader("🧠 Brain Journey")

    stages = [
        ("brain", "🧠 Whole Brain",
         "The brain is a complex biological network containing interacting regions and circuits."),

        ("region", "🔵 Brain Region",
         "Different regions contribute to different functions, but most cognitive functions depend on distributed networks."),

        ("circuit", "🔗 Neural Circuit",
         "Information is processed through interconnected neural circuits. Some pathways contain bidirectional communication."),

        ("neuron", "🧬 Neuron",
         "Neurons are specialized cells that communicate through electrical and chemical signals."),

        ("dendrites", "🌿 Dendrites",
         "Dendrites receive synaptic inputs from other neurons."),

        ("axon", "➖ Axon",
         "The axon carries electrical signals away from the cell body toward other neurons or target cells."),

        ("myelin", "⚡ Myelin",
         "Myelin increases the efficiency and speed of electrical signal propagation along many axons."),

        ("signal", "⚡ Electrical Signal",
         "Changes in membrane potential allow neurons to generate and propagate electrical signals."),

        ("synapse", "🔗 Synapse",
         "A synapse is a communication junction between neurons or between a neuron and another target cell."),

        ("neurotransmitter", "🧪 Neurotransmitter",
         "Neurotransmitters are chemical messengers released at many synapses."),

        ("function", "🧠 Cognitive Function",
         "Neural systems contribute to attention, memory, decision-making, emotion and behaviour.")
    ]

    labels = [x[1] for x in stages]

    current = st.session_state.get(
        "journey_stage",
        "brain"
    )

    current_index = next(
        (
            i for i, x in enumerate(stages)
            if x[0] == current
        ),
        0
    )

    stage_key, stage_name, explanation = stages[current_index]

    st.markdown(
        f"""
        <div class="card">
            <h2>{stage_name}</h2>
            <p>{explanation}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Visual animation for each stage
    if stage_key == "brain":

        if brain:
            st.image(
                brain,
                use_container_width=True
            )
        else:
            st.markdown(
                '<div class="stage"><div class="neuron">🧠</div></div>',
                unsafe_allow_html=True
            )

    elif stage_key == "region":

        region = st.selectbox(
            "Choose a brain region",
            list(BRAIN.keys()),
            key="journey_region_select"
        )

        info, function, pathway = BRAIN[region]

        st.markdown(
            f"""
            <div class="stage">
                <div style="text-align:center">
                    <div class="neuron">🔵</div>
                    <b>{html.escape(region)}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.info(info)
        st.write(f"**Main contribution:** {function}")
        st.write(f"**Example network:** {pathway}")

    elif stage_key == "circuit":

        st.markdown(
            """
            <div class="stage">
                <div style="
                    font-size:2.4rem;
                    letter-spacing:16px
                ">
                    🧠 → 🔵 → ⚫ → 🟣 → 🧠
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(
            "Neural circuits are networks of connected neurons and brain regions. "
            "Information flow can be one-way in some connections and reciprocal in others."
        )

    elif stage_key == "neuron":

        st.markdown(
            """
            <div class="stage">
                <div class="neuron">🧬</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif stage_key == "dendrites":

        st.markdown(
            """
            <div class="stage">
                <div style="font-size:5rem">
                    🌿
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif stage_key == "axon":

        st.markdown(
            """
            <div class="stage">
                <div style="
                    font-size:4rem;
                    animation:move 2s linear infinite
                ">
                    🟢━━━━━━━⚡
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif stage_key == "myelin":

        st.markdown(
            """
            <div class="stage">
                <div style="
                    font-size:2.6rem;
                    letter-spacing:5px
                ">
                    🟢🔵🔵🔵🔵🔵⚡
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif stage_key == "signal":

        st.markdown(
            """
            <div class="stage">
                <div class="signal">
                    ⚡
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif stage_key == "synapse":

        st.markdown(
            """
            <div class="stage">
                <div class="syn">
                    🧠 〰️ 🧠
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif stage_key == "neurotransmitter":

        nt = st.selectbox(
            "Choose neurotransmitter",
            list(NT.keys()),
            key="nt_select"
        )

        st.markdown(
            """
            <div class="stage">
                <div style="
                    font-size:3.5rem;
                    animation:p 1s infinite
                ">
                    🧪 • • • 🧠
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.info(NT[nt])

    elif stage_key == "function":

        st.markdown(
            """
            <div class="stage">
                <div style="
                    font-size:3.5rem;
                    animation:p 1.5s infinite
                ">
                    🧠 → 💭 → 🎯
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(
            "Cognition and behaviour emerge from interactions among "
            "distributed neural systems, body signals and environmental context."
        )

    st.markdown("### 🤖 Ayna explains")

    if st.session_state.language == "Roman English":

        ayna_text = (
            f"Is stage mein hum {stage_name} ko explore kar rahe hain. "
            f"Yaad rakhein ke brain functions aksar multiple connected "
            f"regions aur networks mil kar perform karte hain."
        )

    else:

        ayna_text = (
            f"In this stage we are exploring {stage_name}. "
            "Remember that cognitive functions usually depend on "
            "interacting regions and distributed networks."
        )

    st.write(ayna_text)

    voice_button(
        ayna_text,
        f"journey_voice_{current_index}"
    )

    st.divider()

    b1, b2, b3 = st.columns(3)

    with b1:

        if current_index > 0:

            if st.button(
                "⬅️ Previous",
                use_container_width=True,
                key="journey_previous"
            ):

                st.session_state.journey_stage = stages[
                    current_index - 1
                ][0]

                st.rerun()

    with b2:

        st.write(
            f"**Stage {current_index + 1} / {len(stages)}**"
        )

    with b3:

        if current_index < len(stages) - 1:

            if st.button(
                "Next ➡️",
                use_container_width=True,
                key="journey_next"
            ):

                st.session_state.journey_stage = stages[
                    current_index + 1
                ][0]

                st.rerun()

    st.divider()

    st.markdown("### 💬 Ask Ayna about this stage")

    question = st.text_input(
        "Your question",
        placeholder="Why is this stage important?",
        key="journey_question"
    )

    if st.button(
        "Ask Ayna",
        key="journey_ask"
    ) and question.strip():

        answer, source = ask_ai(
            question,
            context=(
                f"Current Brain Journey stage: {stage_name}\n"
                f"Explanation: {explanation}"
            )
        )

        st.write(answer)

        voice_button(
            answer,
            "journey_answer_voice"
        )


# ---------------- BRAIN PUZZLE ----------------

if st.session_state.page == "Brain Puzzle":

    st.subheader("🧩 Brain Puzzle")

    st.write(
        "Arrange the numbered tiles in the correct order. "
        "This is an educational cognitive game, not a clinical assessment."
    )

    size = st.selectbox(
        "Puzzle size",
        [3, 4, 5],
        key="puzzle_size"
    )

    total = size * size

    if (
        "puzzle_board" not in st.session_state
        or st.session_state.get("puzzle_board_size") != size
    ):

        board = list(range(1, total + 1))

        while True:

            shuffled = board.copy()
            random.shuffle(shuffled)

            if shuffled != board:
                break

        st.session_state.puzzle_board = shuffled
        st.session_state.puzzle_board_size = size
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_start = time.time()
        st.session_state.puzzle_done = False

    board = st.session_state.puzzle_board

    if not st.session_state.puzzle_done:

        st.markdown(
            f"**Moves:** {st.session_state.puzzle_moves}"
        )

        elapsed = int(
            time.time()
            - st.session_state.puzzle_start
        )

        st.markdown(
            f"**Timer:** {elapsed} seconds"
        )

        cols = st.columns(size)

        for i, value in enumerate(board):

            with cols[i % size]:

                if st.button(
                    str(value),
                    use_container_width=True,
                    key=f"puzzle_tile_{i}_{value}"
                ):

                    # Simple adjacent swap interaction
                    if i > 0:

                        board[i], board[i - 1] = (
                            board[i - 1],
                            board[i]
                        )

                        st.session_state.puzzle_moves += 1

                    st.session_state.puzzle_board = board

                    if board == list(range(1, total + 1)):

                        st.session_state.puzzle_done = True

                        record(
                            "puzzles"
                        )

                        record(
                            "games"
                        )

                        st.session_state.puzzle_history.append(
                            {
                                "size": size,
                                "moves":
                                    st.session_state.puzzle_moves,
                                "time": elapsed
                            }
                        )

                    st.rerun()

    if st.session_state.puzzle_done:

        elapsed = int(
            time.time()
            - st.session_state.puzzle_start
        )

        st.success(
            f"🎉 Puzzle completed! "
            f"{st.session_state.puzzle_moves} moves "
            f"in {elapsed} seconds."
        )

        st.balloons()

        if st.button(
            "🔄 New Puzzle",
            key="new_puzzle"
        ):

            st.session_state.pop(
                "puzzle_board",
                None
            )

            st.session_state.pop(
                "puzzle_board_size",
                None
            )

            st.session_state.puzzle_done = False

            st.rerun()


# ---------------- AI MOOD & BEHAVIOUR ----------------

if st.session_state.page == "AI Mood & Behaviour":

    st.subheader("🎙️ AI Mood & Behaviour")

    st.warning(
        "Educational exploration only. This tool does not diagnose "
        "mental-health conditions or determine a person's clinical state."
    )

    tab_voice, tab_text = st.tabs(
        ["🎙️ Voice", "⌨️ Text"]
    )

    with tab_voice:

        st.write(
            "Record a short description of how you feel."
        )

        audio = st.audio_input(
            "Record your voice",
            key="mood_audio"
        )

        if audio:

            if st.button(
                "📤 Send Voice",
                key="send_mood_voice"
            ):

                prompt = """
Analyze this recording for broad communication/emotional cues.

Return:
1. A broad non-clinical mood label.
2. A short explanation.
3. One supportive but non-therapeutic suggestion.

Do not diagnose.
Do not infer hidden mental illness.
Do not claim voice can reliably determine a person's true emotional state.
"""

                result, source = ask_ai_audio(
                    audio,
                    prompt
                )

                st.markdown("### 🤖 Ayna")

                st.write(result)

                voice_button(
                    result,
                    "mood_result_voice"
                )

    with tab_text:

        mood_text = st.text_area(
            "How are you feeling?",
            placeholder=(
                "Example: I feel tired because I had a busy day."
            ),
            key="mood_text"
        )

        if st.button(
            "📤 Send Text",
            key="send_mood_text"
        ) and mood_text.strip():

            prompt = f"""
Analyze this self-report for a broad, non-clinical mood category.

Possible labels:
Positive, Calm, Neutral, Worried, Low, Frustrated, Tired.

Return the best broad label and a short explanation.

Text:
{mood_text}

Do not diagnose.
"""

            result, source = ask_ai(
                prompt
            )

            st.markdown("### 🤖 Ayna")

            st.write(result)

            voice_button(
                result,
                "mood_text_result_voice"
            )

    st.divider()

    st.markdown("### 🌈 Mood map")

    cols = st.columns(
        len(MOODS)
    )

    for col, (name, emoji) in zip(
        cols,
        MOODS.items()
    ):

        with col:

            st.markdown(
                f"""
                <div class="card"
                     style="text-align:center">
                    <div style="font-size:2rem">
                        {emoji}
                    </div>
                    <b>{name}</b>
                </div>
                """,
                unsafe_allow_html=True
            )


# ---------------- BRAIN EXERCISES ----------------

if st.session_state.page == "Brain Exercises":

    st.subheader(
        "🎯 Daily Cognitive Experiments"
    )

    exp_index = (
        (time.gmtime().tm_yday - 1)
        % len(EXPERIMENTS)
    )

    title, domain = EXPERIMENTS[exp_index]

    st.markdown(
        f"""
        <div class="card">
            <h2>{title}</h2>
            <p>Domain: {domain}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if domain == "Working Memory":

        sequence = [7, 2, 9, 4, 1, 8]

        if "memory_answer" not in st.session_state:

            st.info(
                "Memorize this sequence, then enter it below."
            )

            st.markdown(
                f"## {' '.join(map(str, sequence))}"
            )

            st.session_state.memory_sequence = sequence

        answer = st.text_input(
            "Enter the sequence",
            key="memory_answer"
        )

        if st.button(
            "Check Memory",
            key="check_memory"
        ):

            correct = answer.replace(
                " ",
                ""
            ) == "".join(
                map(str, sequence)
            )

            if correct:

                st.success(
                    "Correct! Excellent working-memory performance."
                )

            else:

                st.error(
                    "Not quite. Try again and focus on the sequence."
                )

            record(
                "experiments"
            )

    elif domain == "Attention":

        target = st.selectbox(
            "Select the target letter",
            ["X", "O", "K", "M"],
            key="attention_target"
        )

        letters = [
            random.choice(
                ["X", "O", "K", "M"]
            )
            for _ in range(12)
        ]

        st.markdown(
            "### Target array"
        )

        st.write(
            " ".join(letters)
        )

        selected = st.text_input(
            "How many targets did you see?",
            key="attention_count"
        )

        if st.button(
            "Check Attention",
            key="check_attention"
        ):

            actual = letters.count(
                target
            )

            try:
                val = int(selected)

                if val == actual:
                    st.success("Correct!")
                else:
                    st.info(
                        f"The target appeared {actual} times."
                    )

            except Exception:

                st.info(
                    f"The target appeared {actual} times."
                )

            record(
                "experiments"
            )

    elif domain == "Decision Making":

        st.write(
            "Which option would you choose?"
        )

        choice = st.radio(
            "Choose one",
            [
                "Receive Rs 1,000 now",
                "Receive Rs 1,500 in 30 days"
            ],
            key="decision_choice"
        )

        if st.button(
            "Submit Decision",
            key="submit_decision"
        ):

            st.success(
                f"You selected: {choice}"
            )

            st.write(
                "This task illustrates temporal discounting "
                "and decision-making. One choice does not indicate "
                "a personality type or clinical characteristic."
            )

            record(
                "experiments"
            )

    elif domain == "Inhibitory Control":

        st.write(
            "Press the button only when you see GO."
        )

        cue = random.choice(
            ["GO", "STOP"]
        )

        st.markdown(
            f"## {cue}"
        )

        if st.button(
            "RESPOND",
            key="inhibition_respond"
        ):

            if cue == "GO":

                st.success(
                    "Response recorded."
                )

            else:

                st.error(
                    "This was a STOP trial."
                )

            record(
                "experiments"
            )

    elif domain == "Cognitive Flexibility":

        mode = st.radio(
            "Switch rule",
            [
                "Respond by number",
                "Respond by parity"
            ],
            key="flex_mode"
        )

        value = random.randint(
            1,
            9
        )

        st.markdown(
            f"## {value}"
        )

        response = st.text_input(
            "Your response",
            key="flex_response"
        )

        if st.button(
            "Submit",
            key="flex_submit"
        ):

            if mode == "Respond by number":

                expected = str(value)

            else:

                expected = (
                    "Even"
                    if value % 2 == 0
                    else "Odd"
                )

            if response.strip().lower() == expected.lower():

                st.success("Correct.")

            else:

                st.info(
                    f"Expected: {expected}"
                )

            record(
                "experiments"
            )

    else:

        words = [
            "memory",
            "attention",
            "brain",
            "learning",
            "decision"
        ]

        target_word = random.choice(
            words
        )

        st.write(
            "Read the word and recall it after a few seconds."
        )

        st.markdown(
            f"## {target_word}"
        )

        recall = st.text_input(
            "Recall the word",
            key="recall_word"
        )

        if st.button(
            "Check Recall",
            key="check_recall"
        ):

            if recall.strip().lower() == target_word:

                st.success(
                    "Correct recall."
                )

            else:

                st.info(
                    f"The word was {target_word}."
                )

            record(
                "experiments"
            )

    st.divider()

    st.markdown(
        "### 🤖 Ayna's research note"
    )

    note = (
        f"Today's activity targets {domain}. "
        "Performance on a short educational task can vary "
        "with attention, fatigue, practice and context. "
        "It should not be interpreted as a diagnosis or "
        "a direct measurement of brain activity."
    )

    st.write(note)

    voice_button(
        note,
        "experiment_note_voice"
    )


# ---------------- RESEARCH BOOK ----------------

if st.session_state.page == "Research Book":

    st.subheader(
        "📖 Research Book"
    )

    st.write(
        "Choose a neuroscience topic to explore."
    )

    topic = st.selectbox(
        "Research topic",
        list(BOOK.keys()),
        key="research_topic"
    )

    summary, explanation = BOOK[topic]

    st.markdown(
        f"""
        <div class="card">
            <h2>{topic}</h2>
            <p>{summary}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "### Key explanation"
    )

    st.write(explanation)

    if st.button(
        "🤖 Ask Ayna for a deeper explanation",
        key="research_ai"
    ):

        answer, source = ask_ai(
            f"""
Explain the topic '{topic}' for an educated general audience.

Cover:
- core neuroscience concept
- major brain systems
- what evidence supports
- important limitations
- one interesting research question

Do not invent citations.
""",
            context=explanation
        )

        st.write(answer)

        voice_button(
            answer,
            "research_answer_voice"
        )

        record(
            "research"
        )

    st.divider()

    st.markdown(
        "### 🔎 Research search"
    )

    research_query = st.text_input(
        "What research question do you want to explore?",
        placeholder="Example: working memory and prefrontal cortex",
        key="research_query"
    )

    if st.button(
        "Search research topic",
        key="research_search"
    ) and research_query.strip():

        answer, source = ask_ai(
            f"""
Help me formulate a research search strategy for:

{research_query}

Give:
1. Key concepts.
2. Synonyms.
3. Suggested PubMed/Europe PMC search terms.
4. Important variables.
5. A possible research gap.

Do not invent papers or citations.
""",
            context=research_query
        )

        st.write(answer)

        st.info(
            "For actual papers, verify the title, authors, "
            "abstract, DOI and source directly in PubMed or Europe PMC."
        )

        st.session_state.research_history.append(
            research_query
        )


# ---------------- ASK AYNA ----------------

if st.session_state.page == "Ask Ayna":

    st.subheader(
        "💬 Ask Ayna"
    )

    st.write(
        "Ask about cognition, neuroscience, behaviour, "
        "decision-making, learning or the brain."
    )

    for msg in st.session_state.messages:

        with st.chat_message(
            msg["role"]
        ):

            st.write(
                msg["content"]
            )

    user_prompt = st.chat_input(
        "Ask Ayna anything about neuroscience..."
    )

    if user_prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_prompt
            }
        )

        context = "\n".join(
            [
                f'{m["role"]}: {m["content"]}'
                for m in st.session_state.messages[-8:]
            ]
        )

        answer, source = ask_ai(
            user_prompt,
            context=context
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.rerun()

    if st.session_state.messages:

        last_answer = next(
            (
                m["content"]
                for m in reversed(
                    st.session_state.messages
                )
                if m["role"] == "assistant"
            ),
            None
        )

        if last_answer:

            voice_button(
                last_answer,
                "ask_ayna_last_voice"
            )

    if st.button(
        "🗑️ Clear Ask Ayna",
        key="clear_ask"
    ):

        st.session_state.messages = []

        st.rerun()


# ---------------- PRIVATE ASK AYNA ----------------

if st.session_state.page == "Private Ask Ayna":

    st.subheader(
        "🔐 Private Ask Ayna"
    )

    st.caption(
        "Private session access"
    )

    if not st.session_state.private_unlocked:

        pin = st.text_input(
            "Enter PIN",
            type="password",
            key="private_pin"
        )

        if st.button(
            "Unlock",
            key="private_unlock"
        ):

            valid = False

            try:

                from modules.security import verify_pin

                valid = verify_pin(pin)

            except Exception:

                # Demo fallback for this educational app
                valid = pin == "2026"

            if valid:

                st.session_state.private_unlocked = True

                st.success(
                    "Private Ask Ayna unlocked."
                )

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )

    else:

        st.success(
            "🔓 Private session unlocked"
        )

        for msg in st.session_state.private_messages:

            with st.chat_message(
                msg["role"]
            ):

                st.write(
                    msg["content"]
                )

        private_prompt = st.chat_input(
            "Private question for Ayna..."
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
                    f'{m["role"]}: {m["content"]}'
                    for m in st.session_state.private_messages[-8:]
                ]
            )

            answer, source = ask_ai(
                private_prompt,
                context=(
                    "This is a private educational session. "
                    + context
                )
            )

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()

        if st.session_state.private_messages:

            last = next(
                (
                    m["content"]
                    for m in reversed(
                        st.session_state.private_messages
                    )
                    if m["role"] == "assistant"
                ),
                None
            )

            if last:

                voice_button(
                    last,
                    "private_voice"
                )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "🗑️ Clear private chat",
                key="clear_private"
            ):

                st.session_state.private_messages = []

                st.rerun()

        with c2:

            if st.button(
                "🔒 Lock",
                key="lock_private"
            ):

                st.session_state.private_unlocked = False

                st.rerun()

        st.warning(
            "Important: this PIN is a session-level access gate. "
            "It is not equivalent to end-to-end encryption or "
            "a secure medical/private data system."
        )


# ---------------- PROGRESS ----------------

if st.session_state.page == "My Progress":

    st.subheader(
        "📊 My Progress"
    )

    p = st.session_state.progress

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Experiments",
            p.get("experiments", 0)
        )

    with c2:

        st.metric(
            "Puzzles",
            p.get("puzzles", 0)
        )

    with c3:

        st.metric(
            "Games",
            p.get("games", 0)
        )

    with c4:

        st.metric(
            "Research topics",
            p.get("research", 0)
        )

    st.divider()

    st.markdown(
        "### 🧠 Activity overview"
    )

    if plotly_go:

        labels = [
            "Experiments",
            "Puzzles",
            "Games",
            "Research"
        ]

        values = [
            p.get("experiments", 0),
            p.get("puzzles", 0),
            p.get("games", 0),
            p.get("research", 0)
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
            title="NEUROLENS activity",
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        for label, value in zip(
            [
                "Experiments",
                "Puzzles",
                "Games",
                "Research"
            ],
            [
                p.get("experiments", 0),
                p.get("puzzles", 0),
                p.get("games", 0),
                p.get("research", 0)
            ]
        ):

            st.write(
                f"**{label}:** {value}"
            )

    st.divider()

    st.markdown(
        "### 🧩 Puzzle history"
    )

    if st.session_state.puzzle_history:

        for item in reversed(
            st.session_state.puzzle_history[-10:]
        ):

            st.write(
                f'{item["size"]}×{item["size"]} — '
                f'{item["moves"]} moves — '
                f'{item["time"]} sec'
            )

    else:

        st.caption(
            "No completed puzzles yet."
        )

    st.divider()

    st.markdown(
        "### 📚 Research history"
    )

    if st.session_state.research_history:

        for item in reversed(
            st.session_state.research_history[-10:]
        ):

            st.write(
                f"• {item}"
            )

    else:

        st.caption(
            "No research searches yet."
        )

    st.divider()

    st.info(
        "Progress currently lives in the active session. "
        "Permanent cross-device history would require a database/backend."
    )


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience • "
    "Educational interactive platform • Created by Ayna Jaffri"
)
    )
