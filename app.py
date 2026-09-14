import os
import time
import random
import hashlib
import json
import base64
from pathlib import Path

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
    import plotly.graph_objects as go
except Exception:
    go = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(45,212,191,.10), transparent 28%),
            radial-gradient(circle at top right, rgba(59,130,246,.10), transparent 28%),
            #07111f;
        color: #eef6ff;
    }

    [data-testid="stSidebar"] {
        background: #091625;
    }

    .hero {
        padding: 30px;
        border-radius: 24px;
        background: linear-gradient(135deg,#0d2337,#102c46);
        border: 1px solid rgba(120,190,255,.18);
        margin-bottom: 22px;
    }

    .hero h1 {
        font-size: 3rem;
        margin-bottom: 5px;
    }

    .hero p {
        color: #b9d5ea;
        font-size: 1.05rem;
    }

    .card {
        padding: 22px;
        border-radius: 20px;
        background: rgba(13,31,49,.82);
        border: 1px solid rgba(130,190,255,.14);
        margin: 10px 0;
    }

    .small-card {
        padding: 15px;
        border-radius: 16px;
        background: #0d2032;
        border: 1px solid rgba(130,190,255,.12);
        margin: 7px 0;
    }

    .tag {
        display: inline-block;
        padding: 7px 12px;
        margin: 4px;
        border-radius: 999px;
        background: #12314a;
        color: #cde9ff;
        font-size: .85rem;
    }

    .mood-box {
        text-align: center;
        padding: 25px;
        border-radius: 24px;
        background: linear-gradient(145deg,#102a40,#0c1b2b);
        border: 1px solid rgba(120,190,255,.2);
        margin: 15px 0;
    }

    .mood-emoji {
        font-size: 5rem;
    }

    .mood-name {
        font-size: 2rem;
        font-weight: 700;
    }

    .lab-screen {
        padding: 20px;
        border-radius: 22px;
        background: linear-gradient(145deg,#081c2c,#102e43);
        border: 1px solid rgba(95,190,255,.2);
        margin-top: 15px;
    }

    .lab-machine {
        min-height: 180px;
        padding: 25px;
        border-radius: 20px;
        background: #071522;
        border: 1px solid rgba(100,190,255,.15);
        text-align: center;
        margin-top: 15px;
    }

    .machine-icon {
        font-size: 4rem;
    }

    .pulse {
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(1); opacity: .7; }
        50% { transform: scale(1.08); opacity: 1; }
        100% { transform: scale(1); opacity: .7; }
    }

    .brain-stage {
        padding: 20px;
        border-radius: 20px;
        background: #0c1f31;
        border: 1px solid rgba(120,190,255,.14);
    }

    .success {
        padding: 15px;
        border-radius: 15px;
        background: rgba(34,197,94,.12);
        border: 1px solid rgba(34,197,94,.25);
    }

    .warning {
        padding: 15px;
        border-radius: 15px;
        background: rgba(245,158,11,.12);
        border: 1px solid rgba(245,158,11,.25);
    }

    .footer {
        text-align:center;
        color:#7891a7;
        padding:30px 0;
    }

    div.stButton > button {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ASSET HELPERS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


def find_asset(*names):
    locations = [
        BASE_DIR,
        BASE_DIR / "assets",
    ]

    for folder in locations:
        for name in names:
            p = folder / name
            if p.exists():
                return p

    return None


BRAIN_IMAGE = find_asset(
    "brain.png",
    "brain.jpg",
    "brain.jpeg",
)

LAB_VIDEO = find_asset(
    "cognitive_lab_brain.mp4",
)

BRAIN_ANIMATION = find_asset(
    "brain_animation.mp4",
    "assets/brain_animation.mp4",
)

REBOOT_VIDEO = find_asset(
    "ayna_reboot_voiced_faster_louder.mp4",
    "ayna_reboot_voiced_louder.mp4",
    "ayna_reboot_voiced.mp4",
)

ROBOT_IMAGE = find_asset(
    "ayna_robot.png",
)

JOURNEY_VIDEO = find_asset(
    "brain_journey.mp4",
    "journey.mp4",
)


def file_bytes(path):
    if path and path.exists():
        return path.read_bytes()
    return None


def image_base64(path):
    data = file_bytes(path)
    if not data:
        return None

    ext = path.suffix.lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"

    return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Welcome Reboot",
    "language": "English",

    "messages": [],
    "private_messages": [],

    "private_pin_hash": None,
    "private_unlocked": False,

    "ai_requests": 0,

    "lab_character": "Mira",
    "lab_equipment": "EEG Scanner",
    "lab_experiment": "Attention Gate",
    "lab_video": "Full Cognitive Lab",
    "lab_running": False,
    "lab_result": None,

    "voice_mood": None,
    "voice_analysis": None,
    "behaviour_text": "",
    "behaviour_emojis": "",

    "progress": {
        "puzzles": 0,
        "experiments": 0,
        "brain_topics": 0,
        "questions": 0,
    },

    "journey_stage": "Prefrontal Cortex",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GEMINI
# ============================================================

def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


API_KEY = get_api_key()

client = None

if genai and API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception:
        client = None


def ask_gemini(prompt, audio_bytes=None, mime_type="audio/wav"):
    if not client:
        return (
            "AI connection is not available right now. "
            "Please check GEMINI_API_KEY in Streamlit Secrets."
        )

    try:
        contents = [prompt]

        if audio_bytes and types:
            contents.append(
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type,
                )
            )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )

        st.session_state.ai_requests += 1

        return response.text

    except Exception as e:
        return f"AI response error: {str(e)}"


def ask_gemini_json(prompt, audio_bytes=None, mime_type="audio/wav"):
    raw = ask_gemini(prompt, audio_bytes, mime_type)

    try:
        cleaned = raw.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start >= 0 and end >= 0:
            cleaned = cleaned[start:end + 1]

        return json.loads(cleaned)

    except Exception:
        return None


# ============================================================
# TEXT TO SPEECH
# ============================================================

def browser_speak(text):
    safe = json.dumps(text)

    components.html(
        f"""
        <script>
        const text = {safe};
        if ("speechSynthesis" in window) {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.rate = 0.92;
            u.pitch = 1.0;
            window.speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=0,
    )


# ============================================================
# DATA
# ============================================================

CHARACTERS = {
    "Mira": {
        "emoji": "👩‍🔬",
        "role": "Attention subject",
        "description": "Used for attention and cognitive-control experiments.",
    },
    "Nova": {
        "emoji": "👩‍🔬",
        "role": "Memory subject",
        "description": "Used for working-memory and retrieval experiments.",
    },
    "Ray": {
        "emoji": "👩‍🔬",
        "role": "Decision subject",
        "description": "Used for reward and decision-making experiments.",
    },
    "Zara": {
        "emoji": "👩‍🔬",
        "role": "Behaviour subject",
        "description": "Used for behaviour and emotion-related experiments.",
    },
}


EQUIPMENT = {
    "EEG Scanner": {
        "icon": "⚡",
        "purpose": "Tracks electrical brain activity patterns.",
    },
    "Eye Tracker": {
        "icon": "👁️",
        "purpose": "Tracks visual attention and gaze behaviour.",
    },
    "Reaction-Time Monitor": {
        "icon": "⏱️",
        "purpose": "Measures response speed in cognitive tasks.",
    },
    "Cognitive Task Screen": {
        "icon": "🖥️",
        "purpose": "Displays controlled cognitive stimuli.",
    },
    "Auditory Attention Station": {
        "icon": "🎧",
        "purpose": "Presents controlled auditory attention tasks.",
    },
    "Behaviour Observation Station": {
        "icon": "🔎",
        "purpose": "Observes behavioural responses during tasks.",
    },
    "Emotion Recognition Display": {
        "icon": "😊",
        "purpose": "Presents emotion-related visual stimuli.",
    },
}


EXPERIMENTS = {
    "Attention Gate": {
        "icon": "🎯",
        "description": "Selective attention under competing visual information.",
    },
    "Working Memory Sprint": {
        "icon": "🧠",
        "description": "Short-term information holding and updating.",
    },
    "Decision Under Delay": {
        "icon": "⏳",
        "description": "Immediate versus delayed reward decision-making.",
    },
    "Inhibition Challenge": {
        "icon": "🛑",
        "description": "Response inhibition and cognitive control.",
    },
    "Cognitive Flexibility": {
        "icon": "🔄",
        "description": "Switching between changing rules and task demands.",
    },
    "Memory Retrieval": {
        "icon": "💭",
        "description": "Retrieval of previously presented information.",
    },
}


BRAIN_SYSTEMS = {
    "Prefrontal Cortex": {
        "icon": "🧠",
        "description": "Supports planning, cognitive control, working memory and decision-making.",
    },
    "Hippocampus": {
        "icon": "🧠",
        "description": "Important for memory formation, retrieval and spatial representation.",
    },
    "Striatum": {
        "icon": "🧠",
        "description": "Part of the basal ganglia involved in action selection, reward and learning.",
    },
    "Anterior Cingulate Cortex": {
        "icon": "🧠",
        "description": "Associated with conflict monitoring, error processing and cognitive control.",
    },
    "Attention Networks": {
        "icon": "👁️",
        "description": "Distributed systems that help select and maintain relevant information.",
    },
    "Amygdala": {
        "icon": "🧠",
        "description": "Involved in processing emotionally relevant information and threat-related learning.",
    },
    "Thalamus": {
        "icon": "🧠",
        "description": "A major relay and integration structure connecting multiple brain systems.",
    },
}


JOURNEY_STAGES = {
    "Prefrontal Cortex": "Planning, cognitive control, working memory and decision-making.",
    "Anterior Cingulate Cortex": "Conflict monitoring, error processing and control.",
    "Thalamus": "Relay and integration of information across brain systems.",
    "Striatum": "Action selection, reward processing and reinforcement learning.",
    "Hippocampus": "Memory formation and retrieval.",
    "Amygdala": "Emotionally relevant processing and threat learning.",
}


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## 🧠 NEUROLENS")
st.sidebar.caption("Explore cognition, behaviour & the brain")

PAGES = [
    "Welcome Reboot",
    "Lab",
    "Brain Journey",
    "Explore Brain",
    "Brain Puzzle",
    "AI Mood & Behaviour",
    "Brain Exercises",
    "Daily Cognitive Experiment",
    "Research Book",
    "Ask Ayna",
    "Private Ask Ayna",
    "My Progress",
]

selected_page = st.sidebar.radio(
    "Navigate",
    PAGES,
    index=PAGES.index(st.session_state.page)
    if st.session_state.page in PAGES
    else 0,
)

st.session_state.page = selected_page

st.sidebar.divider()

st.session_state.language = st.sidebar.radio(
    "Ayna language",
    ["English", "Roman English"],
    index=0 if st.session_state.language == "English" else 1,
)

st.sidebar.markdown(
    """
    <div class="small-card">
    <b>Research mode</b><br>
    Educational cognitive neuroscience exploration.<br><br>
    Games and self-reports are not clinical or direct measurements of brain activity.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# WELCOME
# ============================================================

if st.session_state.page == "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">
            <h1>🧠 NEUROLENS</h1>
            <p>
            Explore cognition, behaviour, brain systems and
            AI-assisted cognitive experiments.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if REBOOT_VIDEO:
        st.video(str(REBOOT_VIDEO))

    st.markdown(
        """
        <div class="card">
        <h2>Welcome to NeuroLens</h2>
        <p>
        I’m <b>Ayna</b>. Let's explore the brain, behaviour,
        cognition and artificial intelligence together.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Brain systems", len(BRAIN_SYSTEMS))

    with c2:
        st.metric("Lab experiments", len(EXPERIMENTS))

    with c3:
        st.metric("Cognitive tools", "Interactive")

    if st.button("🚀 Enter NeuroLens", use_container_width=True):
        st.session_state.page = "Lab"
        st.rerun()


# ============================================================
# LAB
# ============================================================

elif st.session_state.page == "Lab":

    st.title("🔬 Cognitive Neuroscience Lab")
    st.caption(
        "You are the scientist. Select the subject, equipment and experiment, "
        "then run the live setup."
    )

    col1, col2 = st.columns(2)

    with col1:
        character_name = st.selectbox(
            "👩‍🔬 Select lab character / subject",
            list(CHARACTERS.keys()),
            index=list(CHARACTERS.keys()).index(
                st.session_state.lab_character
            ),
        )

        equipment_name = st.selectbox(
            "🧪 Select equipment",
            list(EQUIPMENT.keys()),
            index=list(EQUIPMENT.keys()).index(
                st.session_state.lab_equipment
            ),
        )

    with col2:
        experiment_name = st.selectbox(
            "🧠 Select experiment",
            list(EXPERIMENTS.keys()),
            index=list(EXPERIMENTS.keys()).index(
                st.session_state.lab_experiment
            ),
        )

        video_options = ["Full Cognitive Lab"]

        if LAB_VIDEO:
            video_options.append("Cognitive Lab Video")

        if BRAIN_ANIMATION:
            video_options.append("Brain Animation")

        if REBOOT_VIDEO:
            video_options.append("Ayna Reboot")

        video_name = st.selectbox(
            "🎬 Lab video",
            video_options,
        )

    st.session_state.lab_character = character_name
    st.session_state.lab_equipment = equipment_name
    st.session_state.lab_experiment = experiment_name
    st.session_state.lab_video = video_name

    character = CHARACTERS[character_name]
    equipment = EQUIPMENT[equipment_name]
    experiment = EXPERIMENTS[experiment_name]

    st.markdown(
        f"""
        <div class="card">
            <h2>
                {character["emoji"]} {character_name}
            </h2>
            <p><b>Role:</b> {character["role"]}</p>
            <p>{character["description"]}</p>

            <span class="tag">
                {equipment["icon"]} {equipment_name}
            </span>

            <span class="tag">
                {experiment["icon"]} {experiment_name}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎬 Lab overview video")

    selected_video = None

    if video_name in ["Full Cognitive Lab", "Cognitive Lab Video"]:
        selected_video = LAB_VIDEO
    elif video_name == "Brain Animation":
        selected_video = BRAIN_ANIMATION
    elif video_name == "Ayna Reboot":
        selected_video = REBOOT_VIDEO

    if selected_video:
        st.video(str(selected_video))
    else:
        st.info(
            "No lab video file found. The live dynamic lab setup below "
            "will still work."
        )

    st.markdown("### ⚡ Live experimental setup")

    if st.button(
        "▶️ Run Live Experiment",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.lab_running = True
        st.session_state.lab_result = None

    status = "RUNNING" if st.session_state.lab_running else "READY"
    status_icon = "🟢" if st.session_state.lab_running else "🟡"

    animation_class = "pulse" if st.session_state.lab_running else ""

    st.markdown(
        f"""
        <div class="lab-screen">
            <h2>{status_icon} LIVE LAB — {status}</h2>

            <div class="lab-machine">

                <div class="machine-icon {animation_class}">
                    {character["emoji"]}
                </div>

                <h2>{character_name}</h2>

                <p>
                    <b>{equipment["icon"]} {equipment_name}</b>
                </p>

                <p>
                    {experiment["icon"]}
                    <b>{experiment_name}</b>
                </p>

                <p>{equipment["purpose"]}</p>

                <div class="tag">
                    Experiment status: {status}
                </div>

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.lab_running:

        st.markdown("### 🧪 Experiment interaction")

        if experiment_name == "Attention Gate":
            target = random.choice(["X", "A", "K", "M"])

            st.write(
                f"Find the target stimulus: **{target}**"
            )

            answer = st.text_input(
                "Enter target",
                key="attention_answer",
            )

            if st.button("Submit Attention Response"):
                if answer.strip().upper() == target:
                    st.session_state.lab_result = "Correct attention response."
                    st.session_state.progress["experiments"] += 1
                else:
                    st.session_state.lab_result = (
                        "Response did not match the target."
                    )

        elif experiment_name == "Working Memory Sprint":

            sequence = "729418"

            st.write(
                "Remember this sequence for a few seconds:"
            )

            st.code(sequence)

            time.sleep(0.2)

            memory_answer = st.text_input(
                "Enter the sequence",
                key="memory_answer",
            )

            if st.button("Submit Memory Response"):
                if memory_answer.strip() == sequence:
                    st.session_state.lab_result = (
                        "Correct memory retrieval."
                    )
                    st.session_state.progress["experiments"] += 1
                else:
                    st.session_state.lab_result = (
                        "The recalled sequence did not match."
                    )

        elif experiment_name == "Decision Under Delay":

            st.write(
                "Choose one:"
            )

            decision = st.radio(
                "Reward choice",
                [
                    "Rs 1,000 today",
                    "Rs 1,500 after 30 days",
                ],
                key="decision_choice",
            )

            if st.button("Submit Decision"):
                st.session_state.lab_result = (
                    f"Recorded choice: {decision}. "
                    "This demonstrates a delay-discounting style decision task."
                )
                st.session_state.progress["experiments"] += 1

        elif experiment_name == "Inhibition Challenge":

            st.write(
                "Press only when the target is **GO**."
            )

            stimulus = random.choice(
                ["GO", "NO-GO"]
            )

            st.markdown(
                f"""
                <div class="mood-box">
                    <h1>{stimulus}</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )

            response = st.radio(
                "Your response",
                ["Press", "Do not press"],
                key="inhibition_response",
            )

            if st.button("Submit Inhibition Response"):
                correct = (
                    (stimulus == "GO" and response == "Press")
                    or
                    (stimulus == "NO-GO" and response == "Do not press")
                )

                if correct:
                    st.session_state.lab_result = "Correct inhibition response."
                    st.session_state.progress["experiments"] += 1
                else:
                    st.session_state.lab_result = "Response error."

        elif experiment_name == "Cognitive Flexibility":

            rule = random.choice(
                ["Respond by colour", "Respond by shape"]
            )

            st.write(f"Current rule: **{rule}**")

            answer = st.selectbox(
                "Select response",
                ["Red", "Blue", "Circle", "Square"],
                key="flex_response",
            )

            if st.button("Submit Flexibility Response"):
                st.session_state.lab_result = (
                    f"Recorded response: {answer}. "
                    "Cognitive flexibility involves adapting to changing task rules."
                )
                st.session_state.progress["experiments"] += 1

        elif experiment_name == "Memory Retrieval":

            words = [
                "attention",
                "reward",
                "memory",
                "emotion",
                "control",
            ]

            st.write(
                "Study these words:"
            )

            st.write(", ".join(words))

            answer = st.text_input(
                "Recall one word",
                key="retrieval_answer",
            )

            if st.button("Submit Retrieval"):
                if answer.strip().lower() in words:
                    st.session_state.lab_result = (
                        "Correct retrieval."
                    )
                    st.session_state.progress["experiments"] += 1
                else:
                    st.session_state.lab_result = (
                        "That word was not in the presented set."
                    )

    if st.session_state.lab_result:
        st.success(st.session_state.lab_result)

    st.divider()

    st.markdown("### 🤖 Ask Ayna about this experiment")

    language = st.radio(
        "Response language",
        ["English", "Roman English"],
        horizontal=True,
        key="lab_ai_language",
    )

    lab_question = st.text_input(
        "Ask Ayna about the current setup",
        placeholder="Why are we using this equipment?",
    )

    if st.button("🤖 Ask Ayna", key="lab_ask_ayna"):

        if language == "English":
            lang_instruction = "Answer in clear English."
        else:
            lang_instruction = (
                "Answer in simple Roman English / Roman Urdu."
            )

        prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

The user is currently acting as the scientist in a virtual laboratory.

Current subject:
{character_name}

Equipment:
{equipment_name}

Experiment:
{experiment_name}

Equipment purpose:
{equipment["purpose"]}

Experiment description:
{experiment["description"]}

Current result:
{st.session_state.lab_result}

Question:
{lab_question}

{lang_instruction}

Explain step-by-step.
Do not diagnose.
Do not claim this simple virtual experiment measures real brain activity.
Explain that the setup is educational/simulated where appropriate.
"""

        answer = ask_gemini(prompt)

        st.markdown(
            f"""
            <div class="card">
            <b>🤖 Ayna:</b><br><br>
            {html.escape(answer).replace(chr(10), "<br>")}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# BRAIN JOURNEY
# ============================================================

elif st.session_state.page == "Brain Journey":

    st.title("🧭 Brain Journey")
    st.caption(
        "Explore major brain systems step-by-step with Ayna."
    )

    stage = st.selectbox(
        "Choose a stage",
        list(JOURNEY_STAGES.keys()),
        index=list(JOURNEY_STAGES.keys()).index(
            st.session_state.journey_stage
        ),
    )

    st.session_state.journey_stage = stage

    if BRAIN_IMAGE:
        st.image(
            str(BRAIN_IMAGE),
            caption=f"Brain Journey — {stage}",
            use_container_width=True,
        )

    st.markdown(
        f"""
        <div class="brain-stage">
            <h2>🧠 {stage}</h2>
            <p>{JOURNEY_STAGES[stage]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🤖 Ayna Explain This Stage"):

        prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

Explain the brain journey stage:
{stage}

Give:
1. What it is
2. Main functions
3. Important connections
4. Relation to cognition or behaviour
5. One simple example

Use clear scientific language.
Do not diagnose.
"""

        answer = ask_gemini(prompt)

        st.session_state.progress["brain_topics"] += 1

        st.markdown(
            f"""
            <div class="card">
            <b>🤖 Ayna:</b><br><br>
            {html.escape(answer).replace(chr(10), "<br>")}
            </div>
            """,
            unsafe_allow_html=True,
        )

        browser_speak(answer)


# ============================================================
# EXPLORE BRAIN
# ============================================================

elif st.session_state.page == "Explore Brain":

    st.title("🧠 Explore Brain Systems")

    if BRAIN_IMAGE:
        st.image(
            str(BRAIN_IMAGE),
            caption="NeuroLens brain map",
            use_container_width=True,
        )

    system_name = st.selectbox(
        "Select a brain system",
        list(BRAIN_SYSTEMS.keys()),
    )

    system = BRAIN_SYSTEMS[system_name]

    st.markdown(
        f"""
        <div class="card">
            <h2>{system["icon"]} {system_name}</h2>
            <p>{system["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🤖 Explain with Ayna"):

        prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

Explain:
{system_name}

Description:
{system["description"]}

Explain in a scientifically responsible way:
- anatomy
- function
- cognitive relevance
- behaviour relevance
- important connections

Do not diagnose.
"""

        answer = ask_gemini(prompt)

        st.session_state.progress["brain_topics"] += 1

        st.write(answer)
        browser_speak(answer)


# ============================================================
# VISUAL TOUCH BRAIN PUZZLE
# ============================================================

elif st.session_state.page == "Brain Puzzle":

    st.title("🧩 Brain Image Puzzle")
    st.caption(
        "Drag the brain pieces with your finger and reconstruct the complete image."
    )

    if not BRAIN_IMAGE:
        st.error(
            "brain.png was not found. Put brain.png in the same folder as app.py."
        )

    else:

        level = st.selectbox(
            "Puzzle level",
            ["3 × 3", "4 × 4", "5 × 5", "6 × 6"],
        )

        size = int(level[0])

        img_data = image_base64(BRAIN_IMAGE)

        if img_data:

            puzzle_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0,
                  maximum-scale=1.0,user-scalable=no">

            <style>

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin:0;
                padding:10px;
                background:#071522;
                color:white;
                font-family:Arial,sans-serif;
                touch-action:none;
                user-select:none;
            }}

            .title {{
                text-align:center;
                font-size:20px;
                margin-bottom:10px;
            }}

            .board {{
                width:min(92vw,620px);
                margin:auto;
                display:grid;
                grid-template-columns:repeat({size},1fr);
                gap:3px;
                background:#18324a;
                padding:5px;
                border-radius:15px;
            }}

            .slot {{
                aspect-ratio:1/1;
                border:2px dashed #385a75;
                border-radius:5px;
                position:relative;
                overflow:hidden;
                background:#0a1a29;
            }}

            .piece {{
                position:absolute;
                inset:0;
                width:100%;
                height:100%;
                background-image:url("{img_data}");
                background-size:{size * 100}% {size * 100}%;
                border-radius:4px;
                touch-action:none;
            }}

            .piece.dragging {{
                opacity:.65;
                z-index:100;
            }}

            .message {{
                text-align:center;
                font-size:18px;
                font-weight:bold;
                padding:12px;
            }}

            .done {{
                color:#4ade80;
            }}

            </style>
            </head>

            <body>

            <div class="title">
                🧠 Drag each piece into its correct position
            </div>

            <div id="board" class="board"></div>

            <div id="message" class="message">
                Touch and drag the pieces.
            </div>

            <script>

            const N = {size};
            const board = document.getElementById("board");
            const message = document.getElementById("message");

            let order = [];

            for(let i=0;i<N*N;i++){{
                order.push(i);
            }}

            order.sort(() => Math.random() - 0.5);

            function row(i) {{
                return Math.floor(i/N);
            }}

            function col(i) {{
                return i % N;
            }}

            function createPiece(sourceIndex) {{

                const piece = document.createElement("div");

                piece.className = "piece";

                const r = row(sourceIndex);
                const c = col(sourceIndex);

                const x = N === 1 ? 0 : (c/(N-1))*100;
                const y = N === 1 ? 0 : (r/(N-1))*100;

                piece.style.backgroundPosition =
                    x + "% " + y + "%";

                piece.dataset.source = sourceIndex;

                return piece;
            }}

            for(let slotIndex=0;slotIndex<N*N;slotIndex++){{

                const slot = document.createElement("div");

                slot.className = "slot";

                slot.dataset.target = slotIndex;

                const piece = createPiece(order[slotIndex]);

                slot.appendChild(piece);

                board.appendChild(slot);
            }}

            let dragged = null;
            let ghost = null;
            let startParent = null;

            function startDrag(e) {{

                e.preventDefault();

                dragged = e.currentTarget;
                startParent = dragged.parentElement;

                dragged.classList.add("dragging");

                ghost = dragged.cloneNode(true);

                ghost.style.position = "fixed";
                ghost.style.width =
                    dragged.getBoundingClientRect().width + "px";

                ghost.style.height =
                    dragged.getBoundingClientRect().height + "px";

                ghost.style.pointerEvents = "none";
                ghost.style.zIndex = "9999";

                document.body.appendChild(ghost);

                moveGhost(e);
            }}

            function moveGhost(e) {{

                if(!ghost) return;

                const rect =
                    dragged.getBoundingClientRect();

                ghost.style.left =
                    (e.clientX - rect.width/2) + "px";

                ghost.style.top =
                    (e.clientY - rect.height/2) + "px";
            }}

            function endDrag(e) {{

                if(!dragged) return;

                e.preventDefault();

                const element =
                    document.elementFromPoint(
                        e.clientX,
                        e.clientY
                    );

                const targetSlot =
                    element
                    ? element.closest(".slot")
                    : null;

                if(targetSlot){{

                    const targetPiece =
                        targetSlot.querySelector(".piece");

                    const sourceSlot =
                        dragged.parentElement;

                    if(targetPiece &&
                       targetPiece !== dragged){{

                        sourceSlot.appendChild(targetPiece);
                    }}

                    targetSlot.appendChild(dragged);
                }}

                dragged.classList.remove("dragging");

                if(ghost){{
                    ghost.remove();
                }}

                dragged = null;
                ghost = null;

                checkSolved();
            }}

            function checkSolved() {{

                const slots =
                    document.querySelectorAll(".slot");

                let correct = 0;

                slots.forEach((slot,index)=>{{

                    const piece =
                        slot.querySelector(".piece");

                    if(piece &&
                       Number(piece.dataset.source) === index){{
                        correct++;
                    }}
                }});

                if(correct === N*N){{

                    message.innerHTML =
                        "🎉 Puzzle solved! Excellent reconstruction.";

                    message.className =
                        "message done";
                }} else {{

                    message.innerHTML =
                        correct + " / " + (N*N) +
                        " pieces are in the correct position.";
                }}
            }}

            document.addEventListener(
                "pointermove",
                moveGhost,
                {{passive:false}}
            );

            document.addEventListener(
                "pointerup",
                endDrag,
                {{passive:false}}
            );

            document.querySelectorAll(".piece")
                .forEach(piece => {{

                    piece.addEventListener(
                        "pointerdown",
                        startDrag,
                        {{passive:false}}
                    );

                }});

            checkSolved();

            </script>

            </body>
            </html>
            """

            components.html(
                puzzle_html,
                height=720,
                scrolling=False,
            )

            st.markdown(
                """
                <div class="warning">
                The puzzle runs as a real touch/drag interaction inside
                the browser component. The Streamlit button below records
                your completion in NeuroLens progress.
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "✅ I completed the puzzle",
                use_container_width=True,
            ):
                st.session_state.progress["puzzles"] += 1
                st.success("Puzzle completion recorded!")


# ============================================================
# AI MOOD & BEHAVIOUR
# ============================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.title("🎭 AI Mood & Behaviour")
    st.caption(
        "Voice-first educational analysis of apparent behavioural cues."
    )

    st.warning(
        "This is an AI-estimated cue from the provided voice/text/emoji. "
        "It cannot directly determine a person's true inner mood and is not a diagnosis."
    )

    st.markdown("### 🎙️ Step 1 — Voice")

    voice = st.audio_input(
        "Record your voice",
        key="mood_voice",
    )

    if st.button(
        "📤 Send Voice",
        use_container_width=True,
        key="send_mood_voice",
    ):

        if not voice:
            st.warning("Please record your voice first.")

        else:

            audio_bytes = voice.getvalue()

            prompt = """
You are Ayna, an educational cognitive neuroscience assistant.

Analyze the provided voice only for broad apparent affective/behavioural cues.

Return ONLY valid JSON:

{
  "mood": "Happy",
  "emoji": "😊",
  "confidence": "low|moderate|high",
  "cue": "brief description",
  "explanation": "brief scientific explanation"
}

Allowed mood labels:
Happy, Excited, Calm, Neutral, Worried, Sad, Frustrated, Tired.

Important:
- This is only an apparent AI estimate.
- Do not claim to know the person's true internal emotional state.
- Do not diagnose mental health conditions.
- Avoid certainty.
"""

            result = ask_gemini_json(
                prompt,
                audio_bytes,
                voice.type or "audio/wav",
            )

            if result:

                mood = result.get("mood", "Neutral")
                emoji = result.get("emoji", "😐")
                confidence = result.get(
                    "confidence",
                    "low",
                )
                cue = result.get(
                    "cue",
                    "",
                )
                explanation = result.get(
                    "explanation",
                    "",
                )

                st.session_state.voice_mood = mood
                st.session_state.voice_analysis = result

                st.markdown(
                    f"""
                    <div class="mood-box">
                        <div class="mood-emoji">{emoji}</div>
                        <div class="mood-name">{mood}</div>
                        <p>AI confidence: {confidence}</p>
                        <p>{cue}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write(explanation)

                browser_speak(
                    f"The apparent mood cue is {mood}. "
                    f"{explanation}"
                )

            else:
                st.warning(
                    "Ayna could not confidently structure the voice estimate. "
                    "Please try another recording."
                )

    st.divider()

    st.markdown("### ✍️ Step 2 — Add text")

    behaviour_text = st.text_area(
        "Write what you want Ayna to consider",
        value=st.session_state.behaviour_text,
        placeholder="Example: I have been thinking about my experiment all day.",
    )

    if st.button(
        "📤 Send Text",
        key="send_behaviour_text",
        use_container_width=True,
    ):

        st.session_state.behaviour_text = behaviour_text

        prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

User text:
{behaviour_text}

Previously estimated apparent voice mood:
{st.session_state.voice_mood}

Explain possible cognitive/behavioural cues.

Do not diagnose.
Do not claim certainty about the user's actual emotional state.
Use educational language.
"""

        answer = ask_gemini(prompt)

        st.write(answer)


    st.markdown("### 😊 Step 3 — Add emoji")

    emoji_options = [
        "😊 Happy",
        "🤩 Excited",
        "😌 Calm",
        "😐 Neutral",
        "😟 Worried",
        "😔 Sad",
        "😤 Frustrated",
        "😴 Tired",
    ]

    selected_emojis = st.multiselect(
        "Select the emoji that best represents what you want to add",
        emoji_options,
    )

    if st.button(
        "📤 Send Emoji",
        key="send_behaviour_emoji",
        use_container_width=True,
    ):

        emoji_text = ", ".join(selected_emojis)

        st.session_state.behaviour_emojis = emoji_text

        if emoji_text:
            prompt = f"""
You are Ayna.

The user selected:
{emoji_text}

Voice-estimated apparent mood:
{st.session_state.voice_mood}

Text:
{st.session_state.behaviour_text}

Explain how these inputs can be interpreted as behavioural/affective
cues without claiming that they reveal the person's true internal state.

Do not diagnose.
"""

            answer = ask_gemini(prompt)

            st.write(answer)

        else:
            st.info("Select at least one emoji first.")


    st.divider()

    st.markdown("### 🧠 Combined analysis")

    if st.button(
        "🧠 Analyze Voice + Text + Emoji",
        type="primary",
        use_container_width=True,
    ):

        if not voice:
            st.warning(
                "Please record and send a voice sample first."
            )

        else:

            combined_prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

Analyze the following multimodal information:

Voice-estimated apparent mood:
{st.session_state.voice_mood}

User text:
{st.session_state.behaviour_text}

Selected emojis:
{st.session_state.behaviour_emojis}

Provide:
1. Apparent mood cue
2. Cognitive/behavioural interpretation
3. What the voice may contribute
4. What the text may contribute
5. What the emoji may contribute
6. Important uncertainty

Never claim direct access to inner mental state.
Never diagnose.
Use scientific but simple language.
"""

            answer = ask_gemini(
                combined_prompt,
                voice.getvalue(),
                voice.type or "audio/wav",
            )

            st.markdown(
                f"""
                <div class="card">
                <h3>🧠 Ayna's combined analysis</h3>
                {html.escape(answer).replace(chr(10), "<br>")}
                </div>
                """,
                unsafe_allow_html=True,
            )

            browser_speak(answer)


# ============================================================
# BRAIN EXERCISES
# ============================================================

elif st.session_state.page == "Brain Exercises":

    st.title("🧠 Brain Exercises")

    exercise = st.selectbox(
        "Choose an exercise",
        [
            "Memory Sequence",
            "Attention Search",
            "Stroop Challenge",
            "Pattern Challenge",
            "Decision Challenge",
        ],
    )

    if exercise == "Memory Sequence":

        sequence = "729418"

        st.write("Memorize:")
        st.code(sequence)

        answer = st.text_input(
            "Enter the sequence"
        )

        if st.button("Check Memory"):

            if answer.strip() == sequence:
                st.success("Correct!")
                st.session_state.progress["puzzles"] += 1
            else:
                st.error("Not quite. Try again.")

    elif exercise == "Attention Search":

        st.write(
            "Find the letter **X**."
        )

        letters = [
            random.choice(
                ["A", "B", "C", "D", "E"]
            )
            for _ in range(12)
        ]

        position = random.randint(0, 11)
        letters[position] = "X"

        st.markdown(
            f"""
            <div class="card" style="font-size:2rem;text-align:center;">
            {" ".join(letters)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.text_input(
            "Which position contains X? Count from 1."
        )

        if st.button("Check Attention"):

            try:
                if int(answer) == position + 1:
                    st.success("Correct attention response!")
                    st.session_state.progress["puzzles"] += 1
                else:
                    st.error("Try again.")
            except Exception:
                st.warning("Enter a number.")

    elif exercise == "Stroop Challenge":

        word = random.choice(
            ["RED", "BLUE", "GREEN", "YELLOW"]
        )

        colour = random.choice(
            ["Red", "Blue", "Green", "Yellow"]
        )

        st.markdown(
            f"""
            <div class="mood-box">
                <h1>{word}</h1>
                <p>Ink cue: {colour}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.selectbox(
            "What colour is the ink cue?",
            ["Red", "Blue", "Green", "Yellow"],
        )

        if st.button("Submit Stroop"):

            if answer == colour:
                st.success("Correct.")
                st.session_state.progress["puzzles"] += 1
            else:
                st.error("Incorrect.")

    elif exercise == "Pattern Challenge":

        st.write("Continue the pattern:")

        st.code("2 → 4 → 8 → 16 → 32 → ?")

        answer = st.text_input("Answer")

        if st.button("Check Pattern"):

            if answer.strip() == "64":
                st.success("Correct!")
                st.session_state.progress["puzzles"] += 1
            else:
                st.error("Try again.")

    elif exercise == "Decision Challenge":

        st.write(
            "Which would you choose?"
        )

        choice = st.radio(
            "Reward",
            [
                "Rs 1,000 today",
                "Rs 1,500 after 30 days",
            ],
        )

        if st.button("Submit Decision"):

            st.success(
                f"Choice recorded: {choice}"
            )

            st.session_state.progress["puzzles"] += 1


# ============================================================
# DAILY COGNITIVE EXPERIMENT
# ============================================================

elif st.session_state.page == "Daily Cognitive Experiment":

    st.title("📅 Daily Cognitive Experiment")

    experiments = [
        (
            "Attention",
            "Count how many times the letter X appears in a paragraph."
        ),
        (
            "Memory",
            "Read five words and recall them after one minute."
        ),
        (
            "Decision-making",
            "Compare an immediate reward with a delayed larger reward."
        ),
        (
            "Cognitive flexibility",
            "Switch between two simple sorting rules."
        ),
    ]

    title, description = random.choice(experiments)

    st.markdown(
        f"""
        <div class="card">
            <h2>Today's focus: {title}</h2>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("✅ Mark experiment complete"):
        st.session_state.progress["experiments"] += 1
        st.success("Daily experiment recorded.")


# ============================================================
# RESEARCH BOOK
# ============================================================

elif st.session_state.page == "Research Book":

    st.title("📖 Research Book")

    st.markdown(
        """
        <div class="card">
        <h3>NEUROLENS Research Notes</h3>

        <p>
        Use this area to record concepts, questions, hypotheses,
        observations and literature notes.
        </p>

        <span class="tag">Cognitive Neuroscience</span>
        <span class="tag">Attention</span>
        <span class="tag">Memory</span>
        <span class="tag">Decision-making</span>
        <span class="tag">Behaviour</span>
        <span class="tag">AI</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    note = st.text_area(
        "Research note",
        placeholder="Write your research observation..."
    )

    if st.button("Save Research Note"):

        st.session_state["last_research_note"] = note

        st.success(
            "Research note saved for this session."
        )

    if "last_research_note" in st.session_state:

        st.markdown(
            f"""
            <div class="small-card">
            <b>Latest note</b><br><br>
            {html.escape(st.session_state["last_research_note"])}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# ASK AYNA
# ============================================================

elif st.session_state.page == "Ask Ayna":

    st.title("🤖 Ask Ayna")

    st.caption(
        "Educational cognitive neuroscience assistant."
    )

    language = st.radio(
        "Response language",
        ["English", "Roman English"],
        horizontal=True,
        key="main_ayna_language",
    )

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input(
        "Ask about memory, attention, learning, behaviour..."
    )

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        if language == "English":
            language_instruction = (
                "Answer in clear English."
            )
        else:
            language_instruction = (
                "Answer in simple Roman English / Roman Urdu."
            )

        system_prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

Topics:
- memory
- attention
- learning
- emotion
- decision-making
- reward
- perception
- cognitive control
- brain systems
- neuroplasticity
- behavioural neuroscience
- cognitive psychology
- AI and cognition

Rules:
- Do not diagnose.
- Do not claim a simple game measures brain activity.
- Distinguish self-report from objective neuroscience measurements.
- Explain scientific uncertainty.
- Be concise but useful.

{language_instruction}

User question:
{prompt}
"""

        answer = ask_gemini(system_prompt)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    st.title("🔐 Private Ask Ayna")

    st.warning(
        "Your Secret Key is hashed in this session. "
        "Do not use a password you use for important accounts."
    )

    if not st.session_state.private_pin_hash:

        st.subheader("Create your Secret Key")

        new_pin = st.text_input(
            "Secret Key / PIN",
            type="password",
        )

        if st.button("Create Secret Key"):

            if len(new_pin) < 4:
                st.error(
                    "Use at least 4 characters."
                )
            else:

                st.session_state.private_pin_hash = (
                    hashlib.sha256(
                        new_pin.encode()
                    ).hexdigest()
                )

                st.session_state.private_unlocked = True

                st.success(
                    "Secret Key created."
                )

                st.rerun()

    elif not st.session_state.private_unlocked:

        st.subheader("Unlock Private Ask Ayna")

        pin = st.text_input(
            "Enter Secret Key",
            type="password",
        )

        if st.button("🔓 Unlock"):

            hashed = hashlib.sha256(
                pin.encode()
            ).hexdigest()

            if hashed == st.session_state.private_pin_hash:

                st.session_state.private_unlocked = True

                st.success(
                    "Private area unlocked."
                )

                st.rerun()

            else:
                st.error(
                    "Incorrect Secret Key."
                )

    else:

        st.success(
            "🔓 Private Ask Ayna unlocked."
        )

        if st.button("🔒 Lock Private Chat"):

            st.session_state.private_unlocked = False

            st.rerun()

        for message in st.session_state.private_messages:

            with st.chat_message(message["role"]):
                st.write(message["content"])

        private_prompt = st.chat_input(
            "Write a private question..."
        )

        if private_prompt:

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "content": private_prompt,
                }
            )

            answer = ask_gemini(
                f"""
You are Ayna.

This is a private educational conversation.

Answer this question:
{private_prompt}

Do not diagnose.
Do not claim certainty where scientific evidence is uncertain.
"""
            )

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            st.rerun()


# ============================================================
# MY PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    st.title("📊 My Progress")

    progress = st.session_state.progress

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Puzzle completions",
            progress["puzzles"],
        )

    with c2:
        st.metric(
            "Experiments",
            progress["experiments"],
        )

    with c3:
        st.metric(
            "Brain topics",
            progress["brain_topics"],
        )

    with c4:
        st.metric(
            "Ayna AI questions",
            st.session_state.ai_requests,
        )

    if go:

        labels = [
            "Puzzles",
            "Experiments",
            "Brain Topics",
            "AI Questions",
        ]

        values = [
            progress["puzzles"],
            progress["experiments"],
            progress["brain_topics"],
            st.session_state.ai_requests,
        ]

        fig = go.Figure(
            go.Bar(
                x=labels,
                y=values,
                text=values,
                textposition="auto",
            )
        )

        fig.update_layout(
            title="NEUROLENS Activity",
            template="plotly_dark",
            height=420,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="card">
        <h3>🧠 NeuroLens learning note</h3>
        <p>
        These progress numbers represent interaction with the app.
        They are not measurements of intelligence, brain activity,
        mental health or cognitive ability.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🧠 NEUROLENS — Explore cognition, behaviour & the brain<br>
        Created by Ayna Jaffri
    </div>
    """,
    unsafe_allow_html=True,
)
