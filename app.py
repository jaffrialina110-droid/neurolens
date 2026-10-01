import os
import time
import json
import base64
import random
from datetime import date
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

try:
    from supabase import create_client
except Exception:
    create_client = None

try:
    from google import genai
except Exception:
    genai = None

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# ============================================================
# NEUROLENS
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"
AI_LIMIT = 20


# ============================================================
# SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, os.getenv(name, default))
    except Exception:
        value = os.getenv(name, default)

    return str(value if value is not None else default).strip()


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret("GEMINI_MODEL", "gemini-2.5-flash")

EASYPAISA_NUMBER = get_secret("EASYPAISA_NUMBER")
INTERNATIONAL_PAYMENT_URL = get_secret("INTERNATIONAL_PAYMENT_URL")


# ============================================================
# SUPABASE
# ============================================================

supabase = None
SUPABASE_ERROR = ""

if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception as exc:
        SUPABASE_ERROR = str(exc)


def supabase_connected():
    return supabase is not None


def db_insert(table, data):
    if not supabase_connected():
        return None

    try:
        return supabase.table(table).insert(data).execute()
    except Exception as exc:
        st.session_state.last_error = str(exc)
        return None


def db_select(table, columns="*", filters=None, limit=100):
    if not supabase_connected():
        return []

    try:
        query = supabase.table(table).select(columns)

        for key, value in (filters or {}).items():
            query = query.eq(key, value)

        result = query.limit(limit).execute()
        return result.data or []

    except Exception as exc:
        st.session_state.last_error = str(exc)
        return []


def db_update(table, data, filters):
    if not supabase_connected():
        return None

    try:
        query = supabase.table(table).update(data)

        for key, value in filters.items():
            query = query.eq(key, value)

        return query.execute()

    except Exception as exc:
        st.session_state.last_error = str(exc)
        return None


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "NeuroWorld",

    "user": None,
    "access_token": "",

    "ai_requests": 0,
    "ai_date": date.today().isoformat(),
    "ai_history": [],

    "lab_score": 0,
    "lab_completed": 0,

    "exercise_scores": [],

    "puzzle_moves": 0,
    "puzzle_start": 0,
    "puzzle_done": False,

    "journey_index": 0,

    "mood_result": None,

    "private_unlocked": False,
    "private_pin": "",

    "research_results": [],
    "research_notes": [],

    "friends": [],
    "messages": [],

    "last_error": "",
}


for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: Inter, Arial, sans-serif;
}

.main {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(70,130,255,.12),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(160,80,255,.10),
            transparent 30%
        );
}

.neuro-title {
    font-size: 50px;
    font-weight: 900;
    letter-spacing: 3px;
}

.subtitle {
    font-size: 18px;
    opacity: .75;
}

.creator {
    font-size: 13px;
    opacity: .55;
}

.card {
    padding: 22px;
    border-radius: 22px;
    border: 1px solid rgba(140,160,200,.22);
    background: rgba(100,120,160,.07);
    margin-bottom: 18px;
}

.world {
    padding: 30px;
    border-radius: 28px;
    border: 1px solid rgba(100,160,255,.28);
    background:
        radial-gradient(
            circle at 50% 35%,
            rgba(90,150,255,.20),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            rgba(5,15,35,.96),
            rgba(20,25,60,.96)
        );
}

.brain-character {
    font-size: 130px;
    text-align: center;
    animation: floatBrain 3s ease-in-out infinite;
}

.robot-character {
    font-size: 100px;
    text-align: center;
    animation: floatRobot 2.5s ease-in-out infinite;
}

@keyframes floatBrain {
    0% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
    100% { transform: translateY(0); }
}

@keyframes floatRobot {
    0% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
    100% { transform: translateY(0); }
}

.portal {
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(120,160,255,.25);
    background: rgba(80,110,180,.08);
    min-height: 130px;
}

.success {
    padding: 18px;
    border-radius: 18px;
    background: rgba(50,180,100,.10);
    border: 1px solid rgba(50,180,100,.25);
}

.warning {
    padding: 18px;
    border-radius: 18px;
    background: rgba(240,170,50,.10);
    border: 1px solid rgba(240,170,50,.25);
}

.small {
    opacity: .65;
    font-size: 13px;
}

div.stButton > button {
    border-radius: 12px;
    min-height: 44px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# ASSETS
# ============================================================

def find_asset(filename):
    locations = [
        filename,
        os.path.join("assets", filename),
        os.path.join(".", filename),
        os.path.join(".", "assets", filename),
    ]

    for path in locations:
        if os.path.exists(path):
            return path

    return None


def image_base64(path):
    if not path:
        return ""

    try:
        with open(path, "rb") as file:
            return base64.b64encode(file.read()).decode()
    except Exception:
        return ""


# ============================================================
# HEADER
# ============================================================

def header():
    st.markdown(
        f"""
        <div class="card">
            <div class="neuro-title">🧠 {APP_NAME}</div>
            <div class="subtitle">
                Explore cognition, behavior & the brain
            </div>
            <div class="creator">
                Independent cognitive neuroscience research project by
                {CREATOR}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BROWSER VOICE
# ============================================================

def speak_button(text, label="🔊 Speak"):
    safe_text = json.dumps(str(text))

    components.html(
        f"""
        <button
            onclick="speakAyna()"
            style="
                width:100%;
                padding:12px;
                border-radius:12px;
                border:1px solid rgba(120,150,220,.3);
                background:rgba(80,120,220,.12);
                color:inherit;
                font-size:15px;
            "
        >
            {label}
        </button>

        <script>
        function speakAyna() {{
            const text = {safe_text};

            if (!("speechSynthesis" in window)) {{
                alert("Browser voice is not supported.");
                return;
            }}

            window.speechSynthesis.cancel();

            const speech =
                new SpeechSynthesisUtterance(text);

            speech.rate = 0.95;
            speech.pitch = 1.05;

            window.speechSynthesis.speak(speech);
        }}
        </script>
        """,
        height=65,
    )


# ============================================================
# AI
# ============================================================

def reset_ai_counter():
    today = date.today().isoformat()

    if st.session_state.ai_date != today:
        st.session_state.ai_date = today
        st.session_state.ai_requests = 0


reset_ai_counter()


def ai_available():
    return bool(
        GEMINI_API_KEY
        and genai is not None
    )


def ask_ayna(prompt, context=""):
    if st.session_state.ai_requests >= AI_LIMIT:
        return (
            "Ayna AI session limit reached. "
            "You can continue using the other NEUROLENS features."
        )

    if not ai_available():
        return (
            "Ask Ayna is not connected yet. "
            "Please add GEMINI_API_KEY in Streamlit Secrets."
        )

    system_prompt = f"""
You are Ask Ayna inside NEUROLENS.

Creator:
Ayna Jaffri

Role:
Educational cognitive neuroscience and behavior assistant.

Topics:
attention, memory, learning, emotion,
decision-making, reward, cognitive control,
perception, behavior, brain systems,
neuroplasticity and consciousness.

Rules:
- Do not diagnose.
- Do not claim to read someone's mind.
- Do not claim games measure brain activity.
- Do not infer psychiatric conditions from text,
  voice or performance.
- Clearly distinguish behavioral observations
  from direct neural measurements.
- Explain uncertainty.
- Do not invent studies or data.
- Encourage professional help for health concerns.
- Use the user's selected language.

Language:
{st.session_state.get("language", "English")}

Additional context:
{context}

User:
{prompt}
"""

    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=system_prompt,
        )

        answer = getattr(response, "text", None)

        if not answer:
            return "Ayna could not generate a response right now."

        st.session_state.ai_requests += 1

        st.session_state.ai_history.append(
            {
                "prompt": prompt,
                "response": answer,
                "time": time.time(),
            }
        )

        return answer

    except Exception:
        return (
            "Ayna is temporarily unavailable. "
            "Please check the Gemini configuration."
        )


# ============================================================
# NEUROWORLD
# ============================================================

def page_neuroworld():

    header()

    brain_path = find_asset("brain.png")
    robot_path = find_asset("ayna_robot.png")

    brain_b64 = image_base64(brain_path)
    robot_b64 = image_base64(robot_path)

    if brain_b64:
        brain_visual = f"""
        <img
            src="data:image/png;base64,{brain_b64}"
            style="
                width:220px;
                height:220px;
                object-fit:contain;
                animation:floatBrain 3s ease-in-out infinite;
            "
        >
        """
    else:
        brain_visual = """
        <div class="brain-character">🧠</div>
        """

    if robot_b64:
        robot_visual = f"""
        <img
            src="data:image/png;base64,{robot_b64}"
            style="
                width:180px;
                height:180px;
                object-fit:contain;
            "
        >
        """
    else:
        robot_visual = """
        <div class="robot-character">🤖</div>
        """

    st.markdown(
        f"""
        <div class="world">

            <div style="text-align:center;">
                {brain_visual}

                <h1>Hi, I am NeuroLens.</h1>

                <p style="font-size:20px;">
                    Come with me — I'll show you what you can explore.
                </p>
            </div>

            <hr>

            <div style="text-align:center;">
                {robot_visual}

                <h3>Meet Ayna</h3>

                <p>
                    Your AI research companion inside the NeuroLens world.
                </p>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    speak_button(
        "Hi, I am NeuroLens. Come with me. "
        "I'll show you what you can explore.",
        "🔊 NeuroLens speaks",
    )

    st.markdown("### 🌌 Enter a NeuroLens world")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="portal">
            🧪 <b>Cognitive Lab</b><br>
            Run interactive behavioral experiments.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Enter Lab", use_container_width=True):
            st.session_state.page = "Cognitive Lab"
            st.rerun()

    with c2:
        st.markdown(
            """
            <div class="portal">
            🧠 <b>Brain Journey</b><br>
            Explore neurons, synapses and brain systems.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Explore Brain", use_container_width=True):
            st.session_state.page = "Brain Journey"
            st.rerun()

    with c3:
        st.markdown(
            """
            <div class="portal">
            🎮 <b>Brain Challenges</b><br>
            Test attention, memory and reasoning.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Brain Challenges", use_container_width=True):
            st.session_state.page = "Brain Challenges"
            st.rerun()

    c4, c5, c6 = st.columns(3)

    with c4:
        st.markdown(
            """
            <div class="portal">
            🤖 <b>Ask Ayna</b><br>
            Talk with the cognitive neuroscience AI.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Talk to Ayna", use_container_width=True):
            st.session_state.page = "Ask Ayna"
            st.rerun()

    with c5:
        st.markdown(
            """
            <div class="portal">
            🔬 <b>Research World</b><br>
            Search scientific literature.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Research", use_container_width=True):
            st.session_state.page = "Research Book"
            st.rerun()

    with c6:
        st.markdown(
            """
            <div class="portal">
            💬 <b>NeuroSocial</b><br>
            Connect and communicate.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("NeuroSocial", use_container_width=True):
            st.session_state.page = "NeuroSocial"
            st.rerun()


# ============================================================
# COGNITIVE LAB
# ============================================================

def page_lab():

    header()

    st.header("🧪 Cognitive Neuroscience Lab")

    st.write(
        "Choose an experiment and complete the behavioral task."
    )

    character = st.selectbox(
        "👤 Research role",
        [
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent",
        ],
    )

    equipment = st.selectbox(
        "🔬 Equipment",
        [
            "EEG Simulator",
            "Eye Tracker",
            "Reaction-Time System",
            "Cognitive Task Monitor",
            "Physiological Sensor",
        ],
    )

    experiment = st.selectbox(
        "🧪 Experiment",
        [
            "Attention",
            "Memory",
            "Decision & Reward",
            "Stroop Cognitive Control",
            "Pattern Recognition",
        ],
    )

    st.info(
        f"Role: {character} | Equipment: {equipment} | "
        f"Experiment: {experiment}"
    )

    st.markdown("### 🌐 Live Lab")

    if experiment == "Attention":

        st.subheader("🎯 Attention Task")

        target = st.session_state.get(
            "attention_target",
            random.choice(["X", "O", "K"]),
        )

        grid = [
            "O O O O O",
            "O O O O O",
            f"O O {target} O O",
            "O O O O O",
            "O O O O O",
        ]

        st.code("\n".join(grid))

        answer = st.text_input(
            "Which target did you see?",
            key="attention_answer",
        )

        if st.button("Check Attention"):

            if answer.strip().upper() == target:

                st.session_state.lab_score += 1
                st.session_state.lab_completed += 1

                db_insert(
                    "lab_results",
                    {
                        "experiment": "Attention",
                        "score": 1,
                    },
                )

                st.success(
                    "Correct. This demonstrates a simple "
                    "selective-attention behavioral task."
                )

            else:
                st.info(
                    f"The target was {target}. "
                    "This is a behavioral demonstration, "
                    "not a direct neural measurement."
                )

    elif experiment == "Memory":

        st.subheader("🧠 Working Memory")

        sequence = "729418"

        st.code(sequence)

        if st.button("Hide Sequence"):
            st.session_state.memory_hidden = True

        if st.session_state.get("memory_hidden"):

            st.success("Sequence hidden.")

            answer = st.text_input(
                "Enter the sequence",
                key="memory_answer",
            )

            if st.button("Check Memory"):

                if answer.strip() == sequence:

                    st.session_state.lab_score += 1
                    st.session_state.lab_completed += 1

                    st.success(
                        "Excellent recall. "
                        "This is a behavioral memory task."
                    )

                else:

                    st.info(
                        "The original sequence was "
                        f"{sequence}."
                    )

    elif experiment == "Decision & Reward":

        st.subheader("💰 Decision & Reward")

        choice = st.radio(
            "Choose one:",
            [
                "PKR 1,000 today",
                "PKR 1,500 after 30 days",
            ],
        )

        if st.button("Submit Decision"):

            st.session_state.lab_completed += 1

            st.success(
                f"You selected: {choice}"
            )

            st.write(
                "This illustrates intertemporal choice "
                "and reward valuation."
            )

    elif experiment == "Stroop Cognitive Control":

        st.subheader("🎨 Stroop Task")

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:48px;
                font-weight:900;
                padding:30px;
            ">
            BLUE
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.selectbox(
            "What is the ink color?",
            [
                "BLUE",
                "RED",
                "GREEN",
                "YELLOW",
            ],
        )

        if st.button("Submit Stroop"):

            if answer == "BLUE":

                st.session_state.lab_score += 1
                st.session_state.lab_completed += 1

                st.success(
                    "Correct. This demonstrates "
                    "cognitive interference."
                )

            else:

                st.info(
                    "The ink color was BLUE."
                )

    else:

        st.subheader("🔢 Pattern Recognition")

        pattern = "2 → 4 → 8 → 16 → 32 → ?"

        st.markdown(
            f"""
            <div class="card"
            style="text-align:center;font-size:28px;">
            {pattern}
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.text_input(
            "What comes next?",
            key="pattern_answer",
        )

        if st.button("Check Pattern"):

            if answer.strip() == "64":

                st.session_state.lab_score += 1
                st.session_state.lab_completed += 1

                st.success(
                    "Correct. The sequence doubles each time."
                )

            else:

                st.info(
                    "The next value is 64."
                )

    st.markdown("### 📊 Lab Progress")

    st.metric(
        "Completed experiments",
        st.session_state.lab_completed,
    )

    st.metric(
        "Correct responses",
        st.session_state.lab_score,
    )

    st.caption(
        "These tasks demonstrate behavior and cognition. "
        "They do not measure EEG, fMRI or actual neural activity."
    )


# ============================================================
# BRAIN JOURNEY
# ============================================================

JOURNEY = [
    (
        "Neuron",
        "Neurons are specialized cells that receive, "
        "integrate and transmit information.",
        "neuron.png",
    ),
    (
        "Synapse",
        "A synapse is a communication junction between neurons.",
        "synapse.png",
    ),
    (
        "Neural Signaling",
        "Neural communication involves electrical and "
        "chemical processes.",
        "neural_signaling.gif",
    ),
    (
        "Prefrontal Cortex",
        "The prefrontal cortex contributes to cognitive "
        "control, planning and working memory.",
        "prefrontal_cortex.png",
    ),
    (
        "Hippocampus",
        "The hippocampus is important for memory formation "
        "and spatial processing.",
        "hippocampus.png",
    ),
    (
        "Striatum",
        "The striatum participates in action selection, "
        "reward-related learning and movement.",
        "striatum.png",
    ),
    (
        "Anterior Cingulate Cortex",
        "The anterior cingulate cortex is associated with "
        "conflict and performance monitoring.",
        "acc.png",
    ),
    (
        "Attention Networks",
        "Attention depends on distributed neural systems "
        "that help select relevant information.",
        "attention_network.png",
    ),
]


def page_brain_journey():

    header()

    st.header("🧠 Visual Brain Journey")

    index = (
        st.session_state.journey_index
        % len(JOURNEY)
    )

    title, description, image_name = JOURNEY[index]

    st.progress(
        (index + 1) / len(JOURNEY)
    )

    st.markdown(
        f"""
        <div class="card">
            <h2>{title}</h2>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    visual = find_asset(image_name)

    if visual:
        try:
            st.image(
                visual,
                use_container_width=True,
            )
        except Exception:
            st.info(
                "Visual could not be displayed."
            )
    else:
        brain = find_asset("brain.png")

        if brain and Image:
            st.image(
                Image.open(brain),
                use_container_width=True,
            )
        else:
            st.info(
                f"Add {image_name} to the assets folder "
                "for the concept visual."
            )

    a, b, c = st.columns(3)

    with a:
        if st.button(
            "⬅ Previous",
            use_container_width=True,
        ):
            st.session_state.journey_index = max(
                0,
                st.session_state.journey_index - 1,
            )
            st.rerun()

    with b:
        if st.button(
            "🔄 Restart",
            use_container_width=True,
        ):
            st.session_state.journey_index = 0
            st.rerun()

    with c:
        if st.button(
            "Next ➡",
            use_container_width=True,
        ):
            st.session_state.journey_index += 1
            st.rerun()


# ============================================================
# BRAIN CHALLENGES
# ============================================================

def page_challenges():

    header()

    st.header("🎮 Brain Challenges")

    challenge = st.selectbox(
        "Choose challenge",
        [
            "Working Memory",
            "Attention Hunt",
            "Reaction Challenge",
            "Pattern Lock",
            "Decision Challenge",
        ],
    )

    if challenge == "Working Memory":

        st.subheader("🧠 Working Memory")

        numbers = "481729"

        st.code(numbers)

        answer = st.text_input(
            "Remember and enter the sequence"
        )

        if st.button("Check Memory"):

            if answer.strip() == numbers:

                st.success("Correct!")
st.session_state.exercise_scores.append(
    {
        "exercise": challenge,
        "score": 1
    }
)
                
                        "exercise": challenge,
                        "score":
