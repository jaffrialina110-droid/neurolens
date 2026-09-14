import os
import io
import json
import hashlib
import random
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# Gemini
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False


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
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #f7fbff 0%, #eef7ff 100%);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 2rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #dff3ff, #f5fbff);
        border: 1px solid #c8e8fa;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        font-size: 3rem;
        margin-bottom: .3rem;
        color: #12344d;
    }

    .hero p {
        font-size: 1.1rem;
        color: #456;
    }

    .card {
        padding: 1.2rem;
        border-radius: 18px;
        background: white;
        border: 1px solid #dcecf5;
        box-shadow: 0 5px 20px rgba(30, 80, 110, .06);
        margin-bottom: 1rem;
    }

    .section-title {
        color: #12344d;
        margin-top: 1rem;
    }

    .small-note {
        color: #667781;
        font-size: .9rem;
    }

    .success-box {
        padding: 1rem;
        border-radius: 15px;
        background: #edf9f1;
        border: 1px solid #ccebd5;
    }

    .warning-box {
        padding: 1rem;
        border-radius: 15px;
        background: #fff8e7;
        border: 1px solid #f2dfaa;
    }

    .brain-card {
        padding: 1rem;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #dcecf5;
        height: 100%;
    }

    .metric-box {
        padding: 1rem;
        border-radius: 16px;
        background: #f5fbff;
        border: 1px solid #d9edf9;
        text-align: center;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULT_PAGE = "Welcome Reboot"

if "page" not in st.session_state:
    st.session_state.page = DEFAULT_PAGE

if "ayna_messages" not in st.session_state:
    st.session_state.ayna_messages = []

if "private_messages" not in st.session_state:
    st.session_state.private_messages = []

if "progress" not in st.session_state:
    st.session_state.progress = {
        "games": 0,
        "experiments": 0,
        "research_reads": 0,
        "ai_questions": 0,
        "behaviour_tasks": 0,
    }

if "private_unlocked" not in st.session_state:
    st.session_state.private_unlocked = False

if "private_pin_hash" not in st.session_state:
    st.session_state.private_pin_hash = None

if "selected_equipment" not in st.session_state:
    st.session_state.selected_equipment = "EEG Scanner"

if "selected_brain_system" not in st.session_state:
    st.session_state.selected_brain_system = "Prefrontal Cortex"

if "last_experiment" not in st.session_state:
    st.session_state.last_experiment = None


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
    "My Progress",
]


def go_to(page):
    st.session_state.page = page
    st.rerun()


# =========================================================
# ASSET HELPERS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent


def find_asset(filename):
    possible = [
        BASE_DIR / filename,
        BASE_DIR / "assets" / filename,
    ]

    for path in possible:
        if path.exists():
            return path

    return None


def find_video(keyword):
    search_dirs = [
        BASE_DIR,
        BASE_DIR / "assets",
    ]

    for directory in search_dirs:
        if not directory.exists():
            continue

        for file in directory.iterdir():
            if file.is_file() and file.suffix.lower() in [".mp4", ".webm", ".mov"]:
                if keyword.lower() in file.name.lower():
                    return file

    return None


def display_video(path):
    if path is None or not path.exists():
        return False

    try:
        with open(path, "rb") as video_file:
            video_bytes = video_file.read()

        st.video(video_bytes, format="video/mp4")
        return True

    except Exception:
        try:
            st.video(str(path))
            return True
        except Exception:
            return False


# =========================================================
# BRAIN DATABASE
# =========================================================

BRAIN_SYSTEMS = {
    "Prefrontal Cortex": {
        "function": "Planning, decision-making, working memory and cognitive control.",
        "keywords": ["planning", "control", "decision-making", "working memory"],
        "related": "Executive control networks",
    },
    "Hippocampus": {
        "function": "Memory formation, spatial representation and contextual learning.",
        "keywords": ["memory", "learning", "navigation", "context"],
        "related": "Medial temporal lobe",
    },
    "Striatum": {
        "function": "Reward processing, action selection, habit learning and motor control.",
        "keywords": ["reward", "habit", "action selection", "motivation"],
        "related": "Basal ganglia",
    },
    "Anterior Cingulate Cortex": {
        "function": "Conflict monitoring, cognitive control, motivation and error processing.",
        "keywords": ["conflict", "error", "control", "motivation"],
        "related": "Cingulo-opercular and control networks",
    },
    "Attention Networks": {
        "function": "Coordinate selective attention and allocation of cognitive resources.",
        "keywords": ["attention", "selection", "focus", "orientation"],
        "related": "Frontoparietal and dorsal attention systems",
    },
}


NEUROTRANSMITTERS = {
    "Dopamine": "Reward learning, motivation, movement and action selection.",
    "Serotonin": "Modulates mood, cognition, sleep and several regulatory processes.",
    "Acetylcholine": "Important for attention, learning, memory and neuromuscular signaling.",
    "Glutamate": "Major excitatory neurotransmitter involved in learning and plasticity.",
    "GABA": "Major inhibitory neurotransmitter that regulates neural activity.",
    "Norepinephrine": "Supports arousal, attention and responses to salient events.",
}


EQUIPMENT = {
    "EEG Scanner": {
        "purpose": "Records electrical activity at the scalp with high temporal resolution.",
        "measure": "Electrophysiological activity",
    },
    "Eye Tracker": {
        "purpose": "Tracks gaze position and eye movements during cognitive tasks.",
        "measure": "Visual attention and eye movements",
    },
    "Reaction-Time Monitor": {
        "purpose": "Measures response latency during controlled tasks.",
        "measure": "Behavioural response time",
    },
    "Auditory Attention Station": {
        "purpose": "Tests attention to competing or target auditory information.",
        "measure": "Auditory attention",
    },
    "Cognitive Task Screen": {
        "purpose": "Presents controlled cognitive stimuli and records responses.",
        "measure": "Task performance",
    },
    "Physiological Monitor": {
        "purpose": "Can monitor physiological signals relevant to cognitive experiments.",
        "measure": "Physiological responses",
    },
    "Behaviour Observation Station": {
        "purpose": "Structured observation of behaviour during controlled activities.",
        "measure": "Observable behaviour",
    },
    "Behaviour Task Screen": {
        "purpose": "Presents behavioural decision and reaction tasks.",
        "measure": "Behavioural responses",
    },
    "Social Interaction Simulator": {
        "purpose": "Creates controlled social interaction scenarios for behavioural research.",
        "measure": "Social behaviour",
    },
    "Emotion Recognition Display": {
        "purpose": "Presents emotional stimuli for perception and behaviour tasks.",
        "measure": "Emotion-related responses",
    },
}


EXPERIMENTS = [
    {
        "name": "Delayed Reward",
        "question": "Would you choose Rs 1,000 today or Rs 1,500 after 30 days?",
        "concept": "Delay discounting and reward-based decision-making.",
    },
    {
        "name": "Memory Sequence",
        "question": "Remember: 7 2 9 4 1 8",
        "concept": "Working memory and short-term information maintenance.",
    },
    {
        "name": "Attention X",
        "question": "Find the letter X among distractors.",
        "concept": "Selective attention.",
    },
    {
        "name": "Stroop Challenge",
        "question": "Identify the ink colour while ignoring conflicting word information.",
        "concept": "Cognitive control and interference.",
    },
    {
        "name": "Pattern Challenge",
        "question": "Complete: 2 → 4 → 8 → 16 → 32 → ?",
        "concept": "Pattern detection and reasoning.",
    },
]


MOODS = [
    "Calm",
    "Focused",
    "Curious",
    "Stressed",
    "Tired",
    "Motivated",
    "Distracted",
    "Happy",
]


# =========================================================
# GEMINI
# =========================================================

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
AI_LIMIT = 140


def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", None)
        if key:
            return str(key).strip()
    except Exception:
        pass

    key = os.getenv("GEMINI_API_KEY", "")
    return key.strip()


@st.cache_resource
def make_client(api_key):
    if not GEMINI_AVAILABLE or not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def ask_ai(prompt, context="", system_extra=""):
    api_key = get_api_key()

    if not GEMINI_AVAILABLE:
        return "Gemini library is not available. Please check requirements.txt."

    if not api_key:
        return (
            "Gemini API key is not configured yet. "
            "Add GEMINI_API_KEY to Streamlit Secrets."
        )

    client = make_client(api_key)

    if client is None:
        return "I could not connect to the AI service right now."

    system_instruction = """
You are Ayna, an educational cognitive neuroscience assistant inside NEUROLENS.

Focus on:
- cognitive neuroscience
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

Rules:
1. Give scientifically responsible educational answers.
2. Do not diagnose medical or psychiatric conditions.
3. Do not claim that simple games measure brain activity directly.
4. Clearly distinguish behavioural performance from neural measurement.
5. Mention uncertainty when scientific evidence is mixed.
6. Do not invent research findings.
7. Keep answers understandable.
"""

    if system_extra:
        system_instruction += "\n" + system_extra

    full_prompt = (
        system_instruction
        + "\n\nContext:\n"
        + str(context)
        + "\n\nUser question:\n"
        + str(prompt)
    )

    cache_key = hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()

    if "ai_cache" not in st.session_state:
        st.session_state.ai_cache = {}

    if cache_key in st.session_state.ai_cache:
        return st.session_state.ai_cache[cache_key]

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
        )

        answer = getattr(response, "text", None)

        if not answer:
            answer = "I could not generate a response."

        answer = str(answer)[:AI_LIMIT * 20]

        st.session_state.ai_cache[cache_key] = answer
        return answer

    except Exception as e:
        error_text = str(e)

        if "401" in error_text or "API key" in error_text:
            return "Gemini API key is invalid or unavailable."

        if "429" in error_text:
            return "AI usage limit reached. Please try again later."

        return "The AI service is temporarily unavailable."


# =========================================================
# GENERAL HELPERS
# =========================================================

def record_progress(key):
    st.session_state.progress[key] = (
        st.session_state.progress.get(key, 0) + 1
    )


def current_time():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def render_header(title, subtitle=""):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.image(
        str(find_asset("brain.png"))
        if find_asset("brain.png")
        else "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?auto=format&fit=crop&w=600&q=80",
        use_container_width=True,
    )

    st.markdown("## 🧠 NEUROLENS")
    st.caption("Explore cognition, behaviour & the brain")

    st.divider()

    for index, page_name in enumerate(PAGES):
        if st.button(
            page_name,
            key=f"nav_{index}",
            use_container_width=True,
        ):
            go_to(page_name)

    st.divider()

    st.markdown("### 🔬 Research Mode")
    st.caption("Educational cognitive neuroscience environment.")

    st.markdown(
        """
        <div class="small-note">
        Created by Ayna Jaffri<br>
        Independent cognitive neuroscience research project
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PAGE 1 — WELCOME REBOOT
# =========================================================

if st.session_state.page == "Welcome Reboot":

    render_header(
        "Welcome to NEUROLENS 🧠",
        "Explore cognition, behaviour and the brain through interactive learning.",
    )

    reboot_video = find_video("reboot")

    if reboot_video:
        display_video(reboot_video)
    else:
        brain_video = find_video("brain")
        if brain_video:
            display_video(brain_video)

    st.markdown(
        """
        <div class="card">
        <h2>Welcome to the Cognitive Lab</h2>
        <p>
        NEUROLENS is an educational interactive environment designed to
        explore cognitive neuroscience concepts through games,
        experiments, behavioural tasks and AI-assisted explanations.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Brain Systems", len(BRAIN_SYSTEMS))

    with col2:
        st.metric("Lab Equipment", len(EQUIPMENT))

    with col3:
        st.metric("Experiments", len(EXPERIMENTS))

    st.markdown("### 🚀 Start Exploring")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🧪 Open Lab", use_container_width=True):
            go_to("Lab")

    with c2:
        if st.button("🧠 Explore Brain", use_container_width=True):
            go_to("Explore Brain")

    with c3:
        if st.button("🤖 Ask Ayna", use_container_width=True):
            go_to("Ask Ayna")


# =========================================================
# PAGE 2 — LAB
# =========================================================

elif st.session_state.page == "Lab":

    render_header(
        "🧪 Cognitive Neuroscience Lab",
        "Explore research equipment, behavioural stations and experimental tasks.",
    )

    lab_video = find_video("cognitive_lab")

    if lab_video:
        display_video(lab_video)

    st.markdown("## 🔬 Laboratory Equipment")

    equipment_names = list(EQUIPMENT.keys())

    selected = st.selectbox(
        "Select equipment",
        equipment_names,
        index=equipment_names.index(
            st.session_state.selected_equipment
        ),
    )

    st.session_state.selected_equipment = selected

    equipment = EQUIPMENT[selected]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="card">
            <h3>🔬 {selected}</h3>
            <p>{equipment["purpose"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="card">
            <h3>📊 Research Measure</h3>
            <p>{equipment["measure"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## 🧠 Research Stations")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "🧠 Cognitive Testing",
            use_container_width=True,
        ):
            go_to("Brain Exercises")

    with c2:
        if st.button(
            "🧪 Open Behaviour Lab",
            use_container_width=True,
        ):
            go_to("AI Mood & Behaviour")

    with c3:
        if st.button(
            "🔬 Daily Experiment",
            use_container_width=True,
        ):
            go_to("Daily Cognitive Experiment")

    st.markdown("## 🧪 Behaviour Lab Equipment")

    behaviour_equipment = [
        "Behaviour Observation Station",
        "Behaviour Task Screen",
        "Social Interaction Simulator",
        "Emotion Recognition Display",
    ]

    behaviour_choice = st.selectbox(
        "Select a behaviour research station",
        behaviour_equipment,
    )

    selected_info = EQUIPMENT[behaviour_choice]

    st.info(
        f"{behaviour_choice}: {selected_info['purpose']} "
        f"Measure: {selected_info['measure']}."
    )

    st.success(
        "Lab status: Character ready. "
        f"Selected equipment: {behaviour_choice}."
    )


# =========================================================
# PAGE 3 — EXPLORE BRAIN
# =========================================================

elif st.session_state.page == "Explore Brain":

    render_header(
        "🧠 Explore Brain Systems",
        "Learn how major cognitive systems contribute to behaviour.",
    )

    selected_system = st.selectbox(
        "Choose a brain system",
        list(BRAIN_SYSTEMS.keys()),
    )

    st.session_state.selected_brain_system = selected_system

    info = BRAIN_SYSTEMS[selected_system]

    st.markdown(
        f"""
        <div class="card">
        <h2>{selected_system}</h2>
        <p><b>Function:</b> {info["function"]}</p>
        <p><b>Related systems:</b> {info["related"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🔗 Key Concepts")

    cols = st.columns(len(info["keywords"]))

    for col, keyword in zip(cols, info["keywords"]):
        with col:
            st.markdown(
                f"""
                <div class="metric-box">
                <b>{keyword}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("## 🧬 Neurotransmitters")

    selected_nt = st.selectbox(
        "Explore a neurotransmitter",
        list(NEUROTRANSMITTERS.keys()),
    )

    st.info(NEUROTRANSMITTERS[selected_nt])

    st.warning(
        "Neurotransmitters do not have one simple psychological function. "
        "Their effects depend on receptors, circuits, brain regions and context."
    )


# =========================================================
# PAGE 4 — BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    render_header(
        "🧩 Brain Puzzle",
        "A visual challenge for attention, memory and pattern processing.",
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["3 × 3", "4 × 4", "5 × 5"],
    )

    size = int(difficulty[0])

    if "puzzle_board" not in st.session_state:
        st.session_state.puzzle_board = list(range(1, size * size + 1))
        random.shuffle(st.session_state.puzzle_board)

    if st.session_state.get("puzzle_size") != size:
        st.session_state.puzzle_size = size
        st.session_state.puzzle_board = list(
            range(1, size * size + 1)
        )
        random.shuffle(st.session_state.puzzle_board)

    board = st.session_state.puzzle_board

    st.markdown(
        """
        <div class="card">
        <p>
        Arrange or inspect the numbered tiles as a simple cognitive puzzle.
        This is an educational game and not a clinical or direct measure of
        brain activity.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(size)

    for i, value in enumerate(board):
        with cols[i % size]:
            if st.button(
                str(value),
                key=f"puzzle_{size}_{i}_{value}",
                use_container_width=True,
            ):
                st.session_state.puzzle_board[i] = (
                    st.session_state.puzzle_board[i]
                    + 1
                )

    if st.button("🔄 New Puzzle", use_container_width=True):
        st.session_state.puzzle_board = list(
            range(1, size * size + 1)
        )
        random.shuffle(st.session_state.puzzle_board)
        record_progress("games")
        st.rerun()


# =========================================================
# PAGE 5 — AI MOOD & BEHAVIOUR
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    render_header(
        "🧪 AI Mood & Behaviour Lab",
        "Explore self-reported mood and observable behavioural patterns.",
    )

    st.markdown(
        """
        <div class="warning-box">
        <b>Important:</b> These tasks are educational. A mood selection
        or behavioural response does not diagnose a mental-health condition
        and does not directly measure brain activity.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🎙️ Voice Behaviour",
            "💬 Text Behaviour",
            "🤝 Social Interaction",
        ]
    )

    with tab1:
        st.subheader("Voice Behaviour")

        voice_text = st.text_area(
            "Write a short sentence that you might say aloud.",
            placeholder="Example: I feel focused today.",
        )

        if st.button("Analyse Voice-Style Text"):
            if voice_text.strip():
                answer = ask_ai(
                    f"Give an educational behavioural analysis of this text "
                    f"as if it were a spoken statement: {voice_text}",
                    system_extra=(
                        "Do not infer medical conditions, personality disorders, "
                        "or diagnoses from one sentence. Discuss only observable "
                        "linguistic or behavioural possibilities."
                    ),
                )

                st.write(answer)
                record_progress("behaviour_tasks")

    with tab2:
        st.subheader("Text Behaviour")

        text_input = st.text_area(
            "Write a short response to a hypothetical situation.",
            placeholder="Example: Someone cancels a meeting at the last minute.",
        )

        if st.button("Analyse Text Behaviour"):
            if text_input.strip():
                answer = ask_ai(
                    f"Analyse possible cognitive and behavioural processes "
                    f"in this response: {text_input}",
                    system_extra=(
                        "Do not diagnose the person. Discuss possibilities such "
                        "as attention, interpretation, decision-making, emotion "
                        "regulation or cognitive control."
                    ),
                )

                st.write(answer)
                record_progress("behaviour_tasks")

    with tab3:
        st.subheader("Social Interaction Simulator")

        scenario = st.selectbox(
            "Choose a scenario",
            [
                "A friend disagrees with your idea.",
                "A colleague gives unexpected feedback.",
                "Someone does not reply to your message.",
                "A group asks you to make a quick decision.",
            ],
        )

        response = st.text_area(
            "How would you respond?",
        )

        if st.button("Explore Cognitive Processes"):
            if response.strip():
                answer = ask_ai(
                    f"""
                    Scenario:
                    {scenario}

                    Response:
                    {response}

                    Explain possible cognitive processes involved.
                    """,
                    system_extra=(
                        "Keep the analysis educational. Do not label the user "
                        "with a disorder or make a clinical diagnosis."
                    ),
                )

                st.write(answer)
                record_progress("behaviour_tasks")


# =========================================================
# PAGE 6 — BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    render_header(
        "🧠 Brain Exercises",
        "Short educational challenges involving memory, attention and reasoning.",
    )

    exercise = st.selectbox(
        "Choose an exercise",
        [
            "Memory Challenge",
            "Attention Challenge",
            "Stroop Challenge",
            "Pattern Challenge",
            "Decision Challenge",
        ],
    )

    if exercise == "Memory Challenge":

        st.markdown("### 🧠 Memory Challenge")

        sequence = "729418"

        st.write("Remember this sequence:")
        st.code("7 2 9 4 1 8")

        answer = st.text_input(
            "Enter the sequence from memory"
        )

        if st.button("Check Memory"):
            if answer.replace(" ", "") == sequence:
                st.success("Sequence matched.")
            else:
                st.error("Sequence did not match.")

            record_progress("games")

    elif exercise == "Attention Challenge":

        st.markdown("### 👁️ Attention Challenge")

        grid = [
            ["O", "O", "O", "O", "O"],
            ["O", "O", "X", "O", "O"],
            ["O", "O", "O", "O", "O"],
            ["O", "O", "O", "O", "O"],
            ["O", "O", "O", "O", "O"],
        ]

        for row in grid:
            st.write("   ".join(row))

        choice = st.text_input(
            "Where is X? Example: row 2, column 3"
        )

        if st.button("Check Attention"):
            if "2" in choice and "3" in choice:
                st.success("Correct target location.")
            else:
                st.error("Try again.")

            record_progress("games")

    elif exercise == "Stroop Challenge":

        st.markdown("### 🎨 Stroop Challenge")

        st.write(
            "Read the ink colour, not the word meaning."
        )

        colour = random.choice(
            ["RED", "BLUE", "GREEN", "YELLOW"]
        )

        st.markdown(
            f"<h1>{colour}</h1>",
            unsafe_allow_html=True,
        )

        selected_colour = st.selectbox(
            "Choose the colour",
            ["RED", "BLUE", "GREEN", "YELLOW"],
        )

        st.button("Record Response")
        record_progress("games")

        st.info(
            "In a real Stroop task, stimulus timing and response accuracy "
            "can be measured experimentally."
        )

    elif exercise == "Pattern Challenge":

        st.markdown("### 🔢 Pattern Challenge")

        st.write(
            "2 → 4 → 8 → 16 → 32 → ?"
        )

        answer = st.text_input("Next number")

        if st.button("Check Pattern"):
            if answer.strip() == "64":
                st.success("Correct.")
            else:
                st.error("Try again.")

            record_progress("games")

    elif exercise == "Decision Challenge":

        st.markdown("### 💰 Decision Challenge")

        option = st.radio(
            "Which would you choose?",
            [
                "Rs 1,000 today",
                "Rs 1,500 after 30 days",
            ],
        )

        if st.button("Record Decision"):
            st.success(
                f"Your response: {option}"
            )

            st.info(
                "This illustrates delay discounting and reward-based "
                "decision-making. There is no universally correct choice."
            )

            record_progress("games")


# =========================================================
# PAGE 7 — DAILY COGNITIVE EXPERIMENT
# =========================================================

elif st.session_state.page == "Daily Cognitive Experiment":

    render_header(
        "🧪 Daily Cognitive Experiment",
        "Run one small educational behavioural experiment.",
    )

    experiment_names = [
        experiment["name"]
        for experiment in EXPERIMENTS
    ]

    selected_name = st.selectbox(
        "Choose today's experiment",
        experiment_names,
    )

    experiment = next(
        item
        for item in EXPERIMENTS
        if item["name"] == selected_name
    )

    st.markdown(
        f"""
        <div class="card">
        <h3>{experiment["name"]}</h3>
        <p><b>Concept:</b> {experiment["concept"]}</p>
        <p><b>Task:</b> {experiment["question"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    response = st.text_input(
        "Your response"
    )

    if st.button("Run Experiment"):

        st.session_state.last_experiment = {
            "name": experiment["name"],
            "response": response,
            "time": current_time(),
        }

        record_progress("experiments")

        st.success("Response recorded.")

        st.info(
            "This is a behavioural learning task. "
            "It does not directly measure neural activity."
        )

    if st.session_state.last_experiment:

        st.markdown("### 📋 Last Recorded Experiment")

        result = st.session_state.last_experiment

        st.write(
            f"**Experiment:** {result['name']}"
        )
        st.write(
            f"**Response:** {result['response']}"
        )
        st.write(
            f"**Time:** {result['time']}"
        )


# =========================================================
# PAGE 8 — RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    render_header(
        "📚 Research Book",
        "Search scientific literature through Europe PMC.",
    )

    query = st.text_input(
        "Search scientific literature",
        placeholder="Example: cognitive neuroscience attention",
    )

    limit = st.slider(
        "Number of results",
        min_value=1,
        max_value=10,
        value=5,
    )

    if st.button("🔎 Search Literature"):

        if not query.strip():
            st.warning("Enter a research topic first.")
        else:

            try:
                encoded_query = urllib.parse.quote(
                    query.strip()
                )

                url = (
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
                    "?query="
                    + encoded_query
                    + f"&format=json&pageSize={limit}"
                )

                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "NEUROLENS/1.0"
                    },
                )

                with urllib.request.urlopen(
                    request,
                    timeout=15,
                ) as response:

                    data = json.loads(
                        response.read().decode("utf-8")
                    )

                results = data.get("resultList", {}).get(
                    "result",
                    []
                )

                if not results:
                    st.info("No results found.")
                else:

                    record_progress("research_reads")

                    for result in results:

                        title = result.get(
                            "title",
                            "Untitled research article",
                        )

                        authors = result.get(
                            "authorString",
                            "Authors not listed",
                        )

                        journal = result.get(
                            "journalTitle",
                            "Journal not listed",
                        )

                        year = result.get(
                            "pubYear",
                            "Year not listed",
                        )

                        abstract = result.get(
                            "abstractText",
                            "",
                        )

                        pmid = result.get(
                            "pmid",
                            "",
                        )

                        st.markdown(
                            f"""
                            <div class="card">
                            <h3>{title}</h3>
                            <p><b>Authors:</b> {authors}</p>
                            <p><b>Journal:</b> {journal}</p>
                            <p><b>Year:</b> {year}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if abstract:
                            with st.expander(
                                "Abstract"
                            ):
                                st.write(abstract)

                        if pmid:
                            st.markdown(
                                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            )

            except Exception as e:

                st.error(
                    "Literature search could not be completed."
                )

                st.caption(
                    f"Technical detail: {e}"
                )


# =========================================================
# PAGE 9 — ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    render_header(
        "🤖 Ask Ayna",
        "Ask questions about cognition, behaviour and the brain.",
    )

    st.markdown(
        """
        <div class="card">
        <p>
        Ask Ayna is an educational cognitive neuroscience assistant.
        It can explain concepts related to memory, attention, learning,
        emotion, decision-making, reward, cognitive control and brain systems.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for message in st.session_state.ayna_messages:

        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

    user_prompt = st.chat_input(
        "Ask Ayna about the brain..."
    )

    if user_prompt:

        st.session_state.ayna_messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            with st.spinner(
                "Ayna is thinking..."
            ):

                answer = ask_ai(
                    user_prompt
                )

            st.markdown(answer)

        st.session_state.ayna_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        record_progress("ai_questions")


# =========================================================
# PAGE 10 — PRIVATE ASK AYNA
# =========================================================

elif st.session_state.page == "Private Ask Ayna":

    render_header(
        "🔐 Private Ask Ayna",
        "A session-only private research notes area.",
    )

    if not st.session_state.private_unlocked:

        st.info(
            "Create a temporary PIN for this browser session."
        )

        pin = st.text_input(
            "Enter PIN",
            type="password",
        )

        if st.button("Unlock Private Mode"):

            if pin.strip():

                st.session_state.private_pin_hash = hashlib.sha256(
                    pin.encode("utf-8")
                ).hexdigest()

                st.session_state.private_unlocked = True

                st.success(
                    "Private mode unlocked for this session."
                )

                st.rerun()

            else:
                st.warning(
                    "Enter a PIN."
                )

    else:

        st.success(
            "Private mode is active for this session."
        )

        for message in st.session_state.private_messages:

            with st.chat_message(
                message["role"]
            ):
                st.markdown(
                    message["content"]
                )

        private_prompt = st.chat_input(
            "Ask Ayna privately..."
        )

        if private_prompt:

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "content": private_prompt,
                }
            )

            with st.chat_message("user"):
                st.markdown(private_prompt)

            with st.chat_message("assistant"):

                with st.spinner(
                    "Ayna is thinking..."
                ):

                    answer = ask_ai(
                        private_prompt,
                        system_extra=(
                            "Treat this as a private educational research note. "
                            "Do not diagnose the user."
                        ),
                    )

                st.markdown(answer)

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

        if st.button(
            "🔒 Lock Private Mode"
        ):

            st.session_state.private_unlocked = False
            st.session_state.private_messages = []
            st.session_state.private_pin_hash = None

            st.rerun()


# =========================================================
# PAGE 11 — MY PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    render_header(
        "📊 My Progress",
        "Your current NEUROLENS activity during this session.",
    )

    progress = st.session_state.progress

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "Games",
            progress["games"],
        )

    with c2:
        st.metric(
            "Experiments",
            progress["experiments"],
        )

    with c3:
        st.metric(
            "Research Reads",
            progress["research_reads"],
        )

    with c4:
        st.metric(
            "AI Questions",
            progress["ai_questions"],
        )

    with c5:
        st.metric(
            "Behaviour Tasks",
            progress["behaviour_tasks"],
        )

    data = {
        "Activity": [
            "Games",
            "Experiments",
            "Research Reads",
            "AI Questions",
            "Behaviour Tasks",
        ],
        "Count": [
            progress["games"],
            progress["experiments"],
            progress["research_reads"],
            progress["ai_questions"],
            progress["behaviour_tasks"],
        ],
    }

    fig = px.bar(
        data,
        x="Activity",
        y="Count",
        title="NEUROLENS Session Activity",
    )

    fig.update_layout(
        xaxis_title="Activity",
        yaxis_title="Count",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.info(
        "Progress is session-based. It is not a clinical assessment "
        "and does not represent brain activity."
    )

    if st.button(
        "🔄 Reset Progress"
    ):

        st.session_state.progress = {
            "games": 0,
            "experiments": 0,
            "research_reads": 0,
            "ai_questions": 0,
            "behaviour_tasks": 0,
        }

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#6b7c86;">
    <b>🧠 NEUROLENS</b><br>
    Explore cognition, behaviour & the brain<br><br>
    Educational cognitive neuroscience project by Ayna Jaffri.
    <br><br>
    NEUROLENS is for education and research exploration.
    Simple cognitive games and self-reports do not directly measure
    brain activity and should not be used for diagnosis.
    </div>
    """,
    unsafe_allow_html=True,
)
