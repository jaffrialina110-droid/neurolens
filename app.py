import os
import random
import time
import hashlib
import base64
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
# NEUROLENS
# Interactive Cognitive Neuroscience Lab
# Created by Ayna Jaffri
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# PATHS
# =========================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset_path(name):
    path = os.path.join(ASSETS, name)
    if os.path.exists(path):
        return path

    path = os.path.join(ROOT, name)
    if os.path.exists(path):
        return path

    return None


BRAIN_PATH = asset_path("brain.png")
JOURNEY_VIDEO = asset_path("brain_animation.mp4")
LAB_VIDEO = asset_path("cognitive_lab_brain.mp4")
AYNA_ROBOT = asset_path("ayna_robot.png")


# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at 15% 5%, #183c63, transparent 30%),
        linear-gradient(135deg, #06101d, #0b1b2d);
}

.block-container {
    max-width: 1400px;
    padding-top: 1rem;
}

.hero {
    padding: 28px;
    border-radius: 24px;
    background: linear-gradient(135deg,#122c49,#111a32);
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

.small-card {
    padding: 14px;
    border-radius: 15px;
    background: #0b1a2b;
    border: 1px solid #263e55;
}

.lab {
    min-height: 320px;
    border-radius: 24px;
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle,#285b88 0,#0b1930 28%,#07111f 72%);
    border: 1px solid #36536d;
}

.orb {
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

.line {
    position:absolute;
    height:2px;
    background:#75c9ff66;
    transform-origin:left;
}

.a {
    left:15%;
    top:35%;
    width:38%;
    transform:rotate(18deg);
}

.b {
    left:52%;
    top:55%;
    width:30%;
    transform:rotate(-25deg);
}

.c {
    left:28%;
    top:65%;
    width:48%;
    transform:rotate(5deg);
}

@keyframes p {
    0%,100% {transform:scale(1)}
    50% {transform:scale(1.12)}
}

.stage {
    padding:18px;
    border-radius:18px;
    background:#0d2136;
    border:1px solid #2c506e;
    min-height:130px;
}

.metric {
    padding:18px;
    border-radius:18px;
    background:#0b1b2d;
    border:1px solid #294560;
    text-align:center;
}

.ayna {
    padding:20px;
    border-radius:20px;
    background:linear-gradient(135deg,#122d49,#0b1829);
    border:1px solid #3c6584;
}

.warning {
    padding:14px;
    border-radius:14px;
    background:#281d0b;
    border:1px solid #74571c;
}

.success {
    padding:14px;
    border-radius:14px;
    background:#0d291e;
    border:1px solid #2f7954;
}

h1,h2,h3 {
    letter-spacing:.2px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "Lab",
    "language": "English",
    "character": "Nova",
    "journey_stage": "Whole Brain",
    "journey_region": "Prefrontal Cortex",
    "experiment": None,
    "experiment_started": False,
    "experiment_score": 0,
    "experiment_total": 0,
    "messages": [],
    "private_messages": [],
    "private_unlocked": False,
    "progress": {
        "experiments": 0,
        "puzzles": 0,
        "games": 0,
        "research": 0,
        "streak": 1,
        "accuracy": 0
    },
    "ai_requests": 0,
    "ai_cache": {},
    "puzzle_size": 3,
    "puzzle_moves": 0,
    "puzzle_start": None,
    "puzzle_score": 0,
    "mood_result": None,
    "mood_text": "",
    "research_topic": "Memory",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# DATA
# =========================================================

BRAIN = {
    "Prefrontal Cortex": {
        "role": "Planning, decision-making, working memory and cognitive control.",
        "behavior": "Helps you plan, inhibit responses and evaluate choices.",
        "question": "How does the prefrontal cortex contribute to decision-making?"
    },
    "Hippocampus": {
        "role": "Important for memory formation, spatial representation and contextual learning.",
        "behavior": "Supports formation and retrieval of many types of memories.",
        "question": "Why is the hippocampus important for memory?"
    },
    "Amygdala": {
        "role": "Processes emotionally significant information and contributes to threat learning.",
        "behavior": "Can influence attention, learning and defensive responses.",
        "question": "How can emotional information influence attention?"
    },
    "Striatum": {
        "role": "Part of the basal ganglia involved in action selection, reward learning and habit-related processes.",
        "behavior": "Helps integrate information relevant to selecting actions.",
        "question": "How is the striatum involved in reward learning?"
    },
    "ACC": {
        "role": "The anterior cingulate cortex contributes to conflict monitoring, effort and cognitive control.",
        "behavior": "Can signal when control or additional effort may be needed.",
        "question": "What happens when the brain detects response conflict?"
    },
    "Cerebellum": {
        "role": "Coordinates movement and also contributes to timing, learning and some cognitive processes.",
        "behavior": "Supports precise prediction and coordination.",
        "question": "Is the cerebellum only involved in movement?"
    }
}


NEUROTRANSMITTERS = {
    "Dopamine": "Important in reward learning, motivation, movement and reinforcement-related processes.",
    "Serotonin": "Involved in mood regulation, sleep, appetite and many other functions.",
    "GABA": "The major inhibitory neurotransmitter in the mature central nervous system.",
    "Glutamate": "The major excitatory neurotransmitter and important for learning and plasticity.",
    "Acetylcholine": "Important for attention, learning, memory and neuromuscular signaling."
}


BOOK = {
    "Brain & Behaviour": {
        "summary": "The brain continuously integrates internal states, sensory information, memories and goals to shape behaviour.",
        "key": "Behaviour emerges from interacting neural systems rather than a single isolated brain region."
    },
    "Memory": {
        "summary": "Memory involves encoding, consolidation, storage and retrieval, supported by distributed neural systems.",
        "key": "The hippocampus is especially important for many forms of episodic memory."
    },
    "Attention": {
        "summary": "Attention selects or prioritizes information for deeper processing.",
        "key": "Attention depends on interacting networks rather than a single attention centre."
    },
    "Perception": {
        "summary": "Perception is an active process in which the brain interprets sensory signals using context and prior information.",
        "key": "What we perceive is influenced by both incoming signals and prior expectations."
    },
    "Emotion": {
        "summary": "Emotion involves coordinated changes in brain activity, body state, attention, learning and behaviour.",
        "key": "Emotional processing is distributed across multiple interacting systems."
    },
    "Decision Making": {
        "summary": "Decision-making integrates values, goals, uncertainty, memory and contextual information.",
        "key": "Decisions can change when reward timing, probability and cognitive load change."
    },
    "Cognitive Control": {
        "summary": "Cognitive control helps maintain goals, resolve conflict and regulate behaviour.",
        "key": "Prefrontal and cingulate systems interact with other networks to support control."
    },
    "Neuroplasticity": {
        "summary": "Neuroplasticity refers to changes in neural structure or function associated with experience, learning and adaptation.",
        "key": "Learning can modify neural circuits over time."
    }
}


EXPERIMENTS = {
    "Working Memory Sprint": {
        "domain": "Working Memory",
        "instruction": "Remember the sequence and enter it after it disappears.",
        "items": ["7", "2", "9", "4", "1", "8"],
    },
    "Attention Gate": {
        "domain": "Attention",
        "instruction": "Identify the target while ignoring distracting information.",
        "items": ["TARGET"],
    },
    "Decision Under Delay": {
        "domain": "Decision Making",
        "instruction": "Choose between an immediate smaller reward and a delayed larger reward.",
        "items": [],
    },
    "Inhibition Challenge": {
        "domain": "Cognitive Control",
        "instruction": "Respond only when the target condition is satisfied.",
        "items": ["GO", "STOP", "GO", "GO"],
    },
    "Cognitive Flexibility": {
        "domain": "Cognitive Flexibility",
        "instruction": "Switch the rule used to classify information.",
        "items": [],
    },
    "Memory Retrieval": {
        "domain": "Memory",
        "instruction": "Retrieve previously presented information.",
        "items": [],
    }
}


# =========================================================
# HELPERS
# =========================================================

def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()


def encode_image(path):
    if not path or not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def image_data_uri(path):
    encoded = encode_image(path)

    if not encoded:
        return None

    ext = os.path.splitext(path)[1].lower()

    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp"
    }.get(ext, "image/png")

    return f"data:{mime};base64,{encoded}"


def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]

        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


@st.cache_resource
def make_client():
    key = get_api_key()

    if not key or genai is None:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def ask_ai(prompt):
    prompt = prompt.strip()

    if not prompt:
        return "Please enter a question."

    cache_key = hashlib.sha256(prompt.lower().encode()).hexdigest()

    if cache_key in st.session_state.ai_cache:
        return st.session_state.ai_cache[cache_key]

    if st.session_state.ai_requests >= 140:
        return (
            "Ayna's session AI limit has been reached. "
            "You can continue using the educational tools and return later."
        )

    client = make_client()

    if client is None:
        return (
            "Ayna AI is temporarily unavailable. "
            "Please check that GEMINI_API_KEY is configured in Streamlit Secrets."
        )

    system = """
You are Ayna, an educational cognitive neuroscience AI assistant inside NEUROLENS.

Rules:
- Explain neuroscience clearly.
- Do not diagnose mental illness.
- Do not claim that a simple app task measures clinical brain activity.
- Do not claim self-report scores are direct measurements of brain activity.
- Distinguish educational cognitive tasks from validated clinical or research instruments.
- Do not invent citations.
- If discussing research, explain uncertainty and limitations.
- You can respond in English or Roman English.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": system + "\n\nUser question:\n" + prompt}
                    ]
                }
            ]
        )

        answer = getattr(response, "text", None)

        if not answer:
            answer = "I couldn't generate an answer right now."

        st.session_state.ai_requests += 1
        st.session_state.ai_cache[cache_key] = answer

        return answer

    except Exception as e:
        return f"Ayna AI could not respond right now. Please try again."


def speak(text, button_key):
    safe_text = text.replace("\\", "\\\\").replace("`", "\\`")

    components.html(
        f"""
        <button
            onclick="window.speechSynthesis.speak(
                new SpeechSynthesisUtterance(`{safe_text}`)
            )"
            style="
                padding:10px 16px;
                border-radius:12px;
                border:1px solid #4d7394;
                background:#102a43;
                color:white;
                cursor:pointer;
                font-size:15px;
            "
        >
        🔊 Ayna Voice
        </button>
        """,
        height=55
    )


def language_instruction():
    if st.session_state.language == "Roman English":
        return "Roman English"

    return "English"


def record_experiment():
    st.session_state.progress["experiments"] += 1


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")
    st.caption("Interactive Cognitive Neuroscience")

    st.markdown("---")

    language = st.radio(
        "Language",
        ["English", "Roman English"],
        index=0 if st.session_state.language == "English" else 1
    )

    st.session_state.language = language

    st.markdown("---")

    pages = [
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

    for i, page in enumerate(pages):
        if st.button(
            page,
            key=f"nav_btn_{i}",
            use_container_width=True
        ):
            go_to(page)

    st.markdown("---")

    st.caption("Created by Ayna Jaffri")
    st.caption(f"AI requests: {st.session_state.ai_requests}/140")


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🧠 NEUROLENS</h1>
        <p style="font-size:18px;">
        Explore cognition, behaviour & the brain
        </p>
        <p style="opacity:.75;">
        Interactive Cognitive Neuroscience Lab
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LAB
# =========================================================

if st.session_state.page == "Lab":

    st.markdown("## 🔬 Interactive Cognitive Neuroscience Lab")

    st.write(
        "Enter the virtual lab, select a researcher character, "
        "choose equipment and perform an educational cognitive experiment."
    )

    if LAB_VIDEO:

        st.video(LAB_VIDEO)

    else:

        st.markdown(
            """
            <div class="lab">
                <div class="orb"></div>
                <div class="line a"></div>
                <div class="line b"></div>
                <div class="line c"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 1. Choose your researcher")

    character = st.selectbox(
        "Character",
        ["Nova", "Mira", "Ray", "Zara"],
        index=["Nova", "Mira", "Ray", "Zara"].index(
            st.session_state.character
        )
    )

    st.session_state.character = character

    st.markdown("### 2. Choose laboratory equipment")

    equipment = st.selectbox(
        "Equipment",
        [
            "EEG Scanner",
            "Eye Tracker",
            "Reaction-Time Monitor",
            "Auditory Attention Station",
            "Cognitive Task Screen",
            "Physiological Monitor"
        ]
    )

    st.markdown(
        f"""
        <div class="card">
        <b>Selected equipment:</b> {equipment}<br><br>
        <b>Researcher:</b> {character}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 3. Today's experiment")

    experiment_name = st.selectbox(
        "Experiment",
        list(EXPERIMENTS.keys())
    )

    experiment = EXPERIMENTS[experiment_name]

    st.markdown(
        f"""
        <div class="card">
        <h3>{experiment_name}</h3>
        <b>Domain:</b> {experiment["domain"]}<br>
        <b>Task:</b> {experiment["instruction"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🧪 Start Today's Experiment",
        use_container_width=True
    ):

        st.session_state.experiment = experiment_name
        st.session_state.experiment_started = True
        st.session_state.experiment_score = 0
        st.session_state.experiment_total = 0

        go_to("Brain Exercises")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "🧠 Enter Brain Journey",
            use_container_width=True
        ):
            go_to("Explore Brain")

    with c2:
        if st.button(
            "💭 AI Mood & Behaviour",
            use_container_width=True
        ):
            go_to("AI Mood & Behaviour")

    with c3:
        if st.button(
            "🤖 Ask Ayna",
            use_container_width=True
        ):
            go_to("Ask Ayna")


# =========================================================
# EXPLORE BRAIN
# =========================================================

elif st.session_state.page == "Explore Brain":

    st.markdown("## 🧠 Brain Journey")

    st.write(
        "Travel from the whole brain to neural circuits, neurons, "
        "synapses and behaviour."
    )

    stages = [
        "Whole Brain",
        "Brain Region",
        "Neural Pathway",
        "Neuron",
        "Dendrites",
        "Axon",
        "Myelin",
        "Electrical Signal",
        "Synapse",
        "Neurotransmitter",
        "Cognitive Function"
    ]

    selected_stage = st.selectbox(
        "Journey stage",
        stages,
        index=stages.index(st.session_state.journey_stage)
        if st.session_state.journey_stage in stages else 0
    )

    st.session_state.journey_stage = selected_stage

    st.markdown("---")

    if selected_stage == "Whole Brain":

        if JOURNEY_VIDEO:
            st.video(JOURNEY_VIDEO)

        else:
            st.markdown(
                """
                <div class="lab">
                    <div class="orb"></div>
                    <div class="line a"></div>
                    <div class="line b"></div>
                    <div class="line c"></div>
                </div>
                """,
                unsafe_allow_html=True
            )

        title = "The Whole Brain"

        explanation = (
            "The brain is a highly interconnected biological system. "
            "Different networks cooperate to support perception, memory, "
            "attention, emotion, movement and decision-making."
        )

    elif selected_stage == "Brain Region":

        region = st.selectbox(
            "Choose a region",
            list(BRAIN.keys())
        )

        st.session_state.journey_region = region

        info = BRAIN[region]

        title = region
        explanation = info["role"]

        st.markdown(
            f"""
            <div class="stage">
                <h2>🧠 {region}</h2>
                <p>{info["role"]}</p>
                <p><b>Behaviour:</b> {info["behavior"]}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif selected_stage == "Neural Pathway":

        title = "Neural Pathway / Circuit"

        explanation = (
            "Neural circuits are networks of connected neurons and brain "
            "regions. Information can move through multiple nodes, with "
            "feedback loops and bidirectional interactions depending on "
            "the circuit."
        )

        st.markdown(
            """
            <div class="lab">
                <div class="orb"></div>
                <div class="line a"></div>
                <div class="line b"></div>
                <div class="line c"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif selected_stage == "Neuron":

        title = "Neuron"

        explanation = (
            "A neuron is a specialized cell that receives, integrates "
            "and communicates information through electrical and chemical "
            "signalling."
        )

        st.markdown(
            """
            <div class="stage">
                <h2>⚡ Neuron</h2>
                <p>Input → integration → electrical signal → communication</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif selected_stage == "Dendrites":

        title = "Dendrites"

        explanation = (
            "Dendrites are branching neuronal structures that receive "
            "many synaptic inputs."
        )

    elif selected_stage == "Axon":

        title = "Axon"

        explanation = (
            "The axon carries electrical signals away from the neuron's "
            "cell body toward other neurons or target cells."
        )

    elif selected_stage == "Myelin":

        title = "Myelin"

        explanation = (
            "Myelin is a specialized insulating structure around many axons "
            "that supports rapid and efficient signal conduction."
        )

    elif selected_stage == "Electrical Signal":

        title = "Electrical Signal"

        explanation = (
            "Changes in membrane potential can generate action potentials, "
            "which propagate along the axon."
        )

    elif selected_stage == "Synapse":

        title = "Synapse"

        explanation = (
            "A synapse is a communication junction where one neuron "
            "influences another cell, often through chemical signalling."
        )

    elif selected_stage == "Neurotransmitter":

        transmitter = st.selectbox(
            "Choose neurotransmitter",
            list(NEUROTRANSMITTERS.keys())
        )

        title = transmitter
        explanation = NEUROTRANSMITTERS[transmitter]

    else:

        title = "Cognitive Function & Behaviour"

        explanation = (
            "Complex behaviour emerges from interactions among neural "
            "circuits, bodily states, learning, environment and context. "
            "A single brain region rarely explains a complex behaviour "
            "by itself."
        )

    st.markdown(
        f"""
        <div class="card">
            <h2>{title}</h2>
            <p>{explanation}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    speak(explanation, "journey_voice")

    st.markdown("### 💬 Ask Ayna about this stage")

    question = st.text_input(
        "Your question",
        key="journey_question"
    )

    if st.button("Ask Ayna", key="journey_ask"):

        if question:
            answer = ask_ai(
                f"""
                Current Brain Journey stage: {selected_stage}
                Current topic: {title}

                User question:
                {question}
                """
            )

            st.markdown(
                f"""
                <div class="ayna">
                🤖 <b>Ayna:</b><br><br>
                {answer}
                </div>
                """,
                unsafe_allow_html=True
            )

            speak(answer, "journey_answer")


# =========================================================
# BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    st.markdown("## 🧩 Brain Puzzle")

    st.write(
        "Arrange the brain image tiles using drag-and-drop. "
        "This is an educational puzzle, not a clinical assessment."
    )

    size = st.selectbox(
        "Puzzle level",
        [3, 4, 5],
        index=[3, 4, 5].index(st.session_state.puzzle_size)
    )

    st.session_state.puzzle_size = size

    if BRAIN_PATH:

        image = Image.open(BRAIN_PATH)

        st.image(
            image,
            caption=f"{size} × {size} Brain Puzzle",
            use_container_width=True
        )

    else:

        st.warning(
            "brain.png was not found. Keep brain.png in the repository "
            "or inside the assets folder."
        )

    st.markdown(
        """
        <div class="card">
        🖐️ <b>Drag & Drop:</b> use the puzzle interface to arrange tiles.<br>
        ⏱️ Timer: active during the puzzle.<br>
        🎯 Score: based on correct placements and completion.
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🧩 Start / New Puzzle",
        use_container_width=True
    ):

        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_start = time.time()

        st.info(
            "Puzzle initialized. Use the image above as the brain reference."
        )

    if st.session_state.puzzle_start:

        elapsed = int(
            time.time() - st.session_state.puzzle_start
        )

        st.metric("Time", f"{elapsed} sec")

    if st.button(
        "✅ Complete Puzzle",
        use_container_width=True
    ):

        st.session_state.progress["puzzles"] += 1

        score = max(
            0,
            100 - st.session_state.puzzle_moves * 2
        )

        st.session_state.puzzle_score = score

        st.success(
            f"Puzzle completed! Educational score: {score}/100"
        )


# =========================================================
# AI MOOD & BEHAVIOUR
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.markdown("## 💭 AI Mood & Behaviour")

    st.write(
        "Explore broad emotional or behavioural patterns from your "
        "self-described text or voice. This does not diagnose a "
        "mental-health condition."
    )

    tab_voice, tab_text = st.tabs(
        ["🎙️ Voice", "⌨️ Text"]
    )

    with tab_voice:

        st.markdown("### Record your voice")

        audio = st.audio_input(
            "Record a short message",
            key="mood_audio"
        )

        if st.button(
            "🧠 Send Voice to Ayna",
            key="send_voice"
        ):

            if audio is None:

                st.warning(
                    "Please record a voice message first."
                )

            else:

                client = make_client()

                if client is None:

                    st.error(
                        "Ayna AI is unavailable. Check GEMINI_API_KEY."
                    )

                else:

                    try:

                        audio_bytes = audio.getvalue()

                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[
                                types.Part.from_bytes(
                                    data=audio_bytes,
                                    mime_type="audio/wav"
                                ),
                                """
                                Analyze this short user voice message
                                educationally.

                                First summarize what the person said.
                                Then select ONE broad label:
                                Positive, Calm, Neutral, Worried,
                                Low, Frustrated, or Tired.

                                Do not diagnose.
                                Do not infer a psychiatric disorder.
                                Mention that voice/content interpretation
                                is approximate.
                                """
                            ]
                        )

                        answer = getattr(
                            response,
                            "text",
                            "I could not analyze the voice."
                        )

                        st.session_state.mood_result = answer

                        st.markdown(
                            f"""
                            <div class="ayna">
                            🤖 <b>Ayna:</b><br><br>
                            {answer}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        speak(answer, "voice_mood_answer")

                    except Exception:

                        st.error(
                            "Voice analysis could not be completed."
                        )

    with tab_text:

        text = st.text_area(
            "How are you feeling or what happened?",
            height=140,
            key="mood_text_input"
        )

        if st.button(
            "🧠 Send Text",
            key="send_text"
        ):

            if not text.strip():

                st.warning("Please enter some text.")

            else:

                answer = ask_ai(
                    f"""
                    Analyze this user-described experience
                    educationally.

                    Give:
                    1. A broad mood label from:
                       Positive, Calm, Neutral, Worried,
                       Low, Frustrated, Tired.
                    2. One short explanation.

                    Do not diagnose.

                    User:
                    {text}
                    """
                )

                st.session_state.mood_text = answer

                st.markdown(
                    f"""
                    <div class="ayna">
                    🤖 <b>Ayna:</b><br><br>
                    {answer}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                speak(answer, "text_mood_answer")

    st.markdown(
        """
        <div class="warning">
        ⚠️ <b>Scientific note:</b>
        This feature provides broad educational interpretation.
        It is not a medical, psychiatric or clinical assessment.
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    st.markdown("## 🧪 Brain Exercises")

    if st.session_state.experiment:

        experiment_name = st.session_state.experiment

    else:

        names = list(EXPERIMENTS.keys())

        experiment_name = names[
            (time.localtime().tm_yday) % len(names)
        ]

    experiment = EXPERIMENTS[experiment_name]

    st.markdown(
        f"""
        <div class="card">
        <h2>{experiment_name}</h2>
        <b>Domain:</b> {experiment["domain"]}<br><br>
        {experiment["instruction"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    if experiment_name == "Working Memory Sprint":

        sequence = "729418"

        st.info(
            "Study the sequence for a few seconds, then answer."
        )

        if st.button("Show Sequence"):

            st.session_state.memory_sequence = sequence
            st.session_state.memory_show_time = time.time()

        st.markdown(
            """
            <div class="stage">
            <h2>🧠 Working Memory</h2>
            <p>Remember the information and reproduce it.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        answer = st.text_input(
            "Enter the sequence",
            key="memory_answer"
        )

        if st.button("Check Memory"):

            st.session_state.experiment_total += 1

            if answer.strip() == sequence:

                st.session_state.experiment_score += 1
                st.session_state.progress["accuracy"] = 100

                st.success(
                    "Correct. Your response matched the target sequence."
                )

            else:

                st.warning(
                    "Not correct. Try again or start a new trial."
                )

    elif experiment_name == "Decision Under Delay":

        st.write(
            "Which option would you choose?"
        )

        choice = st.radio(
            "Reward choice",
            [
                "Rs 1,000 now",
                "Rs 1,500 in 30 days"
            ]
        )

        if st.button("Submit Decision"):

            st.session_state.experiment_total += 1
            st.session_state.experiment_score += 1

            st.success(
                f"You selected: {choice}"
            )

            st.info(
                "This task explores delay-related choice. "
                "One response cannot determine your personality "
                "or future financial behaviour."
            )

    elif experiment_name == "Attention Gate":

        st.write(
            "Find the target word."
        )

        options = [
            "DISTRACTOR",
            "DISTRACTOR",
            "TARGET",
            "DISTRACTOR"
        ]

        random.shuffle(options)

        selected = st.radio(
            "Which word is the target?",
            options
        )

        if st.button("Submit Attention Response"):

            st.session_state.experiment_total += 1

            if selected == "TARGET":

                st.session_state.experiment_score += 1
                st.success("Correct target detected.")

            else:

                st.warning("The target was TARGET.")

    elif experiment_name == "Inhibition Challenge":

        st.write(
            "Respond only when the word is GO."
        )

        word = random.choice(
            ["GO", "STOP"]
        )

        st.markdown(
            f"""
            <div class="stage">
            <h1>{word}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

        response = st.radio(
            "Your response",
            ["Respond", "Do not respond"]
        )

        if st.button("Submit Inhibition Trial"):

            st.session_state.experiment_total += 1

            correct = (
                (word == "GO" and response == "Respond")
                or
                (word == "STOP" and response == "Do not respond")
            )

            if correct:

                st.session_state.experiment_score += 1
                st.success("Correct.")

            else:

                st.warning("Incorrect.")

    elif experiment_name == "Cognitive Flexibility":

        rule = st.radio(
            "Current rule",
            [
                "Classify by colour",
                "Classify by shape"
            ]
        )

        answer = st.selectbox(
            "Choose an example",
            [
                "Red circle",
                "Blue square",
                "Green triangle"
            ]
        )

        if st.button("Switch Rule"):

            st.success(
                f"Rule switched to: {rule}"
            )

            st.info(
                "Cognitive flexibility involves adapting behaviour "
                "when task rules or goals change."
            )

    else:

        recall = st.text_input(
            "What do you remember from the previous task?"
        )

        if st.button("Submit Retrieval"):

            if recall.strip():

                st.session_state.experiment_score += 1
                st.session_state.experiment_total += 1

                st.success(
                    "Retrieval response recorded."
                )

            else:

                st.warning(
                    "Enter a response first."
                )

    st.markdown("---")

    total = st.session_state.experiment_total
    score = st.session_state.experiment_score

    if total:

        accuracy = round(
            (score / total) * 100
        )

    else:

        accuracy = 0

    st.markdown(
        f"""
        <div class="card">
        <b>Current score:</b> {score}/{total}<br>
        <b>Accuracy:</b> {accuracy}%
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "💡 Ask Ayna About This Experiment",
        use_container_width=True
    ):

        answer = ask_ai(
            f"""
            Explain the cognitive neuroscience behind:
            {experiment_name}

            Domain:
            {experiment["domain"]}
            """
        )

        st.markdown(
            f"""
            <div class="ayna">
            🤖 <b>Ayna:</b><br><br>
            {answer}
            </div>
            """,
            unsafe_allow_html=True
        )

        speak(answer, "exercise_voice")

    if st.button(
        "🏁 Record Experiment Completion",
        use_container_width=True
    ):

        record_experiment()

        st.session_state.progress["accuracy"] = accuracy

        st.success(
            "Experiment recorded in your current session."
        )

    st.markdown(
        """
        <div class="warning">
        These tasks are educational cognitive explorations.
        They should not be treated as scientifically validated
        diagnostic or publishable research protocols without
        appropriate literature review, predefined outcomes,
        consent and ethics procedures.
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    st.markdown("## 📚 Research Book")

    st.write(
        "Explore cognitive neuroscience topics and research concepts."
    )

    topic = st.selectbox(
        "Choose a topic",
        list(BOOK.keys()),
        index=list(BOOK.keys()).index(
            st.session_state.research_topic
        )
        if st.session_state.research_topic in BOOK else 0
    )

    st.session_state.research_topic = topic

    content = BOOK[topic]

    st.markdown(
        f"""
        <div class="card">
        <h2>📖 {topic}</h2>
        <p>{content["summary"]}</p>
        <hr>
        <b>Key concept:</b>
        <p>{content["key"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    mode = st.radio(
        "Reading mode",
        ["Simple Mode", "Research Mode"],
        horizontal=True
    )

    if mode == "Research Mode":

        st.markdown("### 🔬 Research explanation")

        question = st.text_input(
            "What would you like to understand about this topic?"
        )

        if st.button("Ask Ayna — Research Explanation"):

            if question:

                answer = ask_ai(
                    f"""
                    Topic: {topic}

                    Explain this question from a
                    cognitive neuroscience perspective:

                    {question}

                    Clearly distinguish established findings,
                    hypotheses and limitations.
                    Do not invent references.
                    """
                )

                st.markdown(
                    f"""
                    <div class="ayna">
                    🤖 <b>Ayna:</b><br><br>
                    {answer}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                speak(answer, "research_voice")

        st.markdown(
            """
            <div class="warning">
            📌 Real article retrieval is intentionally separated
            from AI explanation. When a literature database such
            as PubMed or Europe PMC is connected, article titles,
            authors, abstracts and DOI/source links should come
            from the database rather than being invented by AI.
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button(
        "📌 Mark Topic Read",
        use_container_width=True
    ):

        st.session_state.progress["research"] += 1

        st.success(
            f"{topic} added to your current research progress."
        )


# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    st.markdown("## 🤖 Ask Ayna")

    st.write(
        "Talk to Ayna about cognitive neuroscience, behaviour, "
        "learning, decisions, attention, memory and everyday questions."
    )

    for message in st.session_state.messages:

        role = message["role"]
        text = message["content"]

        if role == "user":

            st.markdown(
                f"""
                <div class="small-card">
                👤 <b>You:</b><br>{text}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div class="ayna">
                🤖 <b>Ayna:</b><br>{text}
                </div>
                """,
                unsafe_allow_html=True
            )

    user_input = st.chat_input(
        "Ask Ayna anything..."
    )

    if user_input:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        answer = ask_ai(
            f"""
            Respond as Ayna.

            Language:
            {language_instruction()}

            User:
            {user_input}
            """
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.rerun()

    if st.session_state.messages:

        if st.button("🔊 Voice Latest Ayna Response"):

            last_answer = None

            for m in reversed(
                st.session_state.messages
            ):

                if m["role"] == "assistant":

                    last_answer = m["content"]
                    break

            if last_answer:
                speak(last_answer, "ask_ayna_voice")

    if st.button("🗑️ Clear Chat"):

        st.session_state.messages = []
        st.rerun()


# =========================================================
# PRIVATE ASK AYNA
# =========================================================

elif st.session_state.page == "Private Ask Ayna":

    st.markdown("## 🔐 Private Ask Ayna")

    if not st.session_state.private_unlocked:

        st.write(
            "Enter your session PIN to open the private chat."
        )

        pin = st.text_input(
            "PIN",
            type="password"
        )

        if st.button(
            "🔓 Unlock Private Ayna"
        ):

            # Session-only lock.
            # For production security use authentication,
            # encrypted storage and a backend.

            if pin == "1234":

                st.session_state.private_unlocked = True
                st.rerun()

            else:

                st.error("Incorrect PIN.")

    else:

        st.success(
            "Private session unlocked."
        )

        st.caption(
            "This is a session-level lock, not permanent encrypted storage."
        )

        for message in st.session_state.private_messages:

            if message["role"] == "user":

                st.markdown(
                    f"""
                    <div class="small-card">
                    👤 <b>You:</b><br>{message["content"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div class="ayna">
                    🤖 <b>Ayna:</b><br>{message["content"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        private_input = st.chat_input(
            "Private message to Ayna..."
        )

        if private_input:

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "content": private_input
                }
            )

            answer = ask_ai(
                f"""
                This is a private educational conversation.

                Respond as Ayna in:
                {language_instruction()}

                User:
                {private_input}
                """
            )

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "🔒 Lock Session",
                use_container_width=True
            ):

                st.session_state.private_unlocked = False
                st.rerun()

        with c2:

            if st.button(
                "🗑️ Clear Private Chat",
                use_container_width=True
            ):

                st.session_state.private_messages = []
                st.rerun()


# =========================================================
# MY PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.markdown("## 📊 My Progress")

    progress = st.session_state.progress

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Experiments",
            progress["experiments"]
        )

    with c2:
        st.metric(
            "Puzzles",
            progress["puzzles"]
        )

    with c3:
        st.metric(
            "Research Topics",
            progress["research"]
        )

    with c4:
        st.metric(
            "Streak",
            progress["streak"]
        )

    st.markdown("---")

    st.markdown("### 🧠 Cognitive Activity")

    data = {
        "Experiments": progress["experiments"],
        "Puzzles": progress["puzzles"],
        "Research": progress["research"],
        "Games": progress["games"]
    }

    if plotly_go:

        fig = plotly_go.Figure(
            data=[
                plotly_go.Bar(
                    x=list(data.keys()),
                    y=list(data.values())
                )
            ]
        )

        fig.update_layout(
            title="Current Session Activity",
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.bar_chart(data)

    st.markdown("### 🎯 Accuracy")

    st.progress(
        min(
            max(progress["accuracy"], 0),
            100
        ) / 100
    )

    st.write(
        f"Current recorded accuracy: "
        f"{progress['accuracy']}%"
    )

    st.markdown(
        """
        <div class="warning">
        Progress shown here is session-based.
        Permanent history requires a database/backend.
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "NEUROLENS • Interactive Cognitive Neuroscience • "
    "Educational platform created by Ayna Jaffri"
)
