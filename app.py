import os
import re
import time
import json
import base64
import hashlib
import secrets
from io import BytesIO
from datetime import date
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

try:
    from google import genai
except Exception:
    genai = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# ============================================================
# NEUROLENS
# Explore cognition, behavior & the brain
# Creator: Ayna Jaffri
# ============================================================


st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"

AI_SESSION_LIMIT = 20

GEMINI_API_KEY = str(
    st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
).strip()

GEMINI_MODEL = str(
    st.secrets.get(
        "GEMINI_MODEL",
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
).strip()

EASYPAISA_NUMBER = str(
    st.secrets.get(
        "EASYPAISA_NUMBER",
        os.getenv("EASYPAISA_NUMBER", ""),
    )
).strip()

EASYPAISA_NAME = str(
    st.secrets.get(
        "EASYPAISA_NAME",
        os.getenv("EASYPAISA_NAME", CREATOR),
    )
).strip()

CONSULTATION_FEE = str(
    st.secrets.get(
        "CONSULTATION_FEE",
        os.getenv("CONSULTATION_FEE", ""),
    )
).strip()

INTERNATIONAL_PAYMENT_URL = str(
    st.secrets.get(
        "INTERNATIONAL_PAYMENT_URL",
        os.getenv("INTERNATIONAL_PAYMENT_URL", ""),
    )
).strip()


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
        radial-gradient(circle at 10% 10%, rgba(60,140,255,.10), transparent 30%),
        radial-gradient(circle at 90% 20%, rgba(120,80,255,.08), transparent 25%);
}

.neuro-title {
    font-size: 52px;
    font-weight: 800;
    letter-spacing: 3px;
    margin-bottom: 0;
}

.neuro-subtitle {
    font-size: 19px;
    opacity: .78;
    margin-top: 0;
}

.creator {
    font-size: 14px;
    opacity: .65;
}

.card {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,.20);
    background: rgba(128,128,128,.06);
    margin-bottom: 18px;
}

.small-card {
    padding: 15px;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,.18);
    background: rgba(128,128,128,.05);
}

.hero {
    padding: 32px;
    border-radius: 24px;
    border: 1px solid rgba(128,128,128,.20);
    background:
        linear-gradient(
            135deg,
            rgba(50,120,255,.13),
            rgba(100,80,255,.08)
        );
}

.metric {
    font-size: 30px;
    font-weight: 800;
}

.muted {
    opacity: .65;
}

.success-box {
    padding: 18px;
    border-radius: 15px;
    border: 1px solid rgba(50,180,100,.35);
    background: rgba(50,180,100,.08);
}

.warning-box {
    padding: 18px;
    border-radius: 15px;
    border: 1px solid rgba(240,170,40,.35);
    background: rgba(240,170,40,.08);
}

.lab-scene {
    border-radius: 22px;
    overflow: hidden;
    border: 1px solid rgba(128,128,128,.25);
    background:
        linear-gradient(
            135deg,
            #07101f,
            #101c34,
            #07101f
        );
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "Welcome",
    "language": "English",
    "character": "Ayna",
    "equipment": "Neural Scanner",
    "experiment": "Attention & Response",
    "experiment_started": False,
    "experiment_completed": False,
    "lab_result": None,
    "lab_followup": False,
    "ai_requests": 0,
    "ai_history": [],
    "ayna_messages": [],
    "private_unlocked": False,
    "private_pin_hash": "",
    "private_pin_salt": "",
    "forum_status": "Not started",
    "forum_payment_method": "",
    "forum_payment_status": "Not submitted",
    "forum_transaction_id": "",
    "forum_name": "",
    "forum_phone": "",
    "forum_problem": "",
    "forum_slot": "",
    "forum_messages": [],
    "research_results": [],
    "research_notes": [],
    "mood_result": None,
    "puzzle_completed": False,
    "games_completed": 0,
    "lab_completed": 0,
    "research_completed": 0,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# ASSET HELPERS
# ============================================================

def find_asset(filename):
    candidates = [
        filename,
        os.path.join("assets", filename),
        os.path.join(".", filename),
        os.path.join(".", "assets", filename),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def image_to_base64(path):
    if not path or not os.path.exists(path):
        return ""

    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def safe_html_text(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


# ============================================================
# HEADER
# ============================================================

def render_header():
    st.markdown(
        f"""
        <div class="hero">
            <div class="neuro-title">🧠 {APP_NAME}</div>
            <div class="neuro-subtitle">
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
# AI ENGINE
# ============================================================

def reset_ai_counter_if_new_day():
    today = date.today().isoformat()

    if "ai_date" not in st.session_state:
        st.session_state.ai_date = today

    if st.session_state.ai_date != today:
        st.session_state.ai_date = today
        st.session_state.ai_requests = 0


reset_ai_counter_if_new_day()


def ai_available():
    return bool(GEMINI_API_KEY and genai is not None)


def ask_ai(prompt, system_context=""):
    if st.session_state.ai_requests >= AI_SESSION_LIMIT:
        return (
            "AI request limit reached for this session. "
            "You can continue exploring the non-AI features of NEUROLENS."
        )

    if not ai_available():
        return (
            "Ask Ayna AI is not connected yet. "
            "Please add GEMINI_API_KEY to Streamlit Secrets."
        )

    full_prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience assistant
inside NEUROLENS.

Creator: Ayna Jaffri.

Topics include:
- cognitive neuroscience
- attention
- memory
- learning
- emotion
- decision-making
- reward
- perception
- cognitive control
- brain systems
- neuroplasticity
- behavioral neuroscience
- consciousness

Rules:
1. Give scientifically grounded educational explanations.
2. Do not diagnose medical or psychiatric conditions.
3. Do not claim a simple game measures brain activity.
4. Clearly distinguish behavioral observations from neural measurements.
5. Mention uncertainty where appropriate.
6. Use simple language when possible.
7. Do not invent studies, data or citations.
8. If the question is health-related, encourage appropriate professional advice.
9. Do not pretend to know the user's private mental state.
10. Do not make a diagnosis from voice, text or game performance.

Language:
{st.session_state.language}

Additional context:
{system_context}

User request:
{prompt}
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
        )

        text = getattr(response, "text", None)

        if not text:
            return "Ayna could not generate a response right now."

        st.session_state.ai_requests += 1

        st.session_state.ai_history.append(
            {
                "prompt": prompt,
                "response": text,
                "time": time.time(),
            }
        )

        return text

    except Exception as e:
        return (
            "Ayna is temporarily unavailable. "
            "Please check your Gemini API configuration."
        )


# ============================================================
# BROWSER VOICE
# ============================================================

def browser_speech_button(text, label="🔊 Play Ayna"):
    safe_text = json.dumps(str(text))

    components.html(
        f"""
        <html>
        <body style="margin:0;background:transparent;">
        <button
            onclick='speakText()'
            style="
                width:100%;
                padding:12px 18px;
                border-radius:12px;
                border:1px solid rgba(128,128,128,.35);
                background:rgba(70,120,255,.12);
                color:inherit;
                cursor:pointer;
                font-size:15px;
            "
        >
            {safe_html_text(label)}
        </button>

        <script>
        function speakText() {{
            const text = {safe_text};

            if (!("speechSynthesis" in window)) {{
                alert("Browser voice is not supported.");
                return;
            }}

            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.95;
            utterance.pitch = 1.0;

            window.speechSynthesis.speak(utterance);
        }}
        </script>
        </body>
        </html>
        """,
        height=60,
    )


# ============================================================
# WELCOME / REBOOT
# ============================================================

def page_welcome():
    st.header("🧠 Welcome to NEUROLENS")

    reboot_video = find_asset("ayna_reboot_voiced.mp4")

    if not reboot_video:
        reboot_video = find_asset("ayna_reboot_voiced_faster_louder.mp4")

    if reboot_video:
        st.video(reboot_video)

    st.markdown(
        """
        <div class="card">
        <h2>Welcome to NeuroLens</h2>
        <p>
        I’m Ayna. Let's explore the brain, behaviour, and cognition together.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚀 Enter NeuroLens", use_container_width=True):
        st.session_state.page = "Lab"
        st.rerun()


# ============================================================
# LAB
# ============================================================

CHARACTERS = {
    "Ayna": {
        "icon": "🧑‍🔬",
        "description": "Research assistant",
    },
    "NeuroBot": {
        "icon": "🤖",
        "description": "AI laboratory robot",
    },
    "Observer": {
        "icon": "👁️",
        "description": "Observation mode",
    },
}

EQUIPMENT = {
    "Neural Scanner": "🧠",
    "Reaction Console": "🎛️",
    "Memory Chamber": "🗃️",
    "Attention Monitor": "📡",
}

EXPERIMENTS = {
    "Attention & Response": {
        "description": "Test selective attention and response control.",
        "task": "attention",
    },
    "Memory Sequence": {
        "description": "Observe short-term sequence memory.",
        "task": "memory",
    },
    "Decision & Reward": {
        "description": "Explore immediate versus delayed reward.",
        "task": "decision",
    },
    "Stroop Control": {
        "description": "Explore interference and cognitive control.",
        "task": "stroop",
    },
}


def lab_scene():
    robot_path = find_asset("ayna_robot.png")
    robot_b64 = image_to_base64(robot_path)

    char = st.session_state.character
    equipment = st.session_state.equipment
    experiment = st.session_state.experiment

    icon = CHARACTERS.get(char, {}).get("icon", "🧑‍🔬")
    equipment_icon = EQUIPMENT.get(equipment, "🧠")

    if robot_b64:
        robot_html = f"""
        <img
            src="data:image/png;base64,{robot_b64}"
            style="
                width:150px;
                height:150px;
                object-fit:contain;
                animation:floatRobot 2s ease-in-out infinite;
            "
        >
        """
    else:
        robot_html = f"""
        <div style="
            font-size:110px;
            animation:floatRobot 2s ease-in-out infinite;
        ">
            {icon}
        </div>
        """

    st.markdown(
        f"""
        <style>
        @keyframes floatRobot {{
            0% {{ transform:translateY(0px); }}
            50% {{ transform:translateY(-12px); }}
            100% {{ transform:translateY(0px); }}
        }}

        @keyframes scan {{
            0% {{ left:5%; opacity:.1; }}
            50% {{ left:80%; opacity:1; }}
            100% {{ left:5%; opacity:.1; }}
        }}

        @keyframes pulse {{
            0% {{ transform:scale(1); }}
            50% {{ transform:scale(1.08); }}
            100% {{ transform:scale(1); }}
        }}

        .scene {{
            position:relative;
            height:370px;
            border-radius:22px;
            overflow:hidden;
            background:
                radial-gradient(circle at 50% 40%,
                    rgba(70,130,255,.20),
                    transparent 35%),
                linear-gradient(135deg,#07101f,#111e38,#07101f);
            border:1px solid rgba(130,170,255,.30);
        }}

        .floor {{
            position:absolute;
            bottom:0;
            left:0;
            width:100%;
            height:80px;
            background:rgba(0,0,0,.25);
        }}

        .robot {{
            position:absolute;
            left:13%;
            bottom:50px;
            text-align:center;
            width:190px;
        }}

        .machine {{
            position:absolute;
            right:13%;
            bottom:55px;
            font-size:100px;
            animation:pulse 1.7s ease-in-out infinite;
        }}

        .beam {{
            position:absolute;
            top:70px;
            height:3px;
            width:35%;
            background:rgba(100,180,255,.9);
            box-shadow:0 0 18px rgba(100,180,255,.9);
            animation:scan 2.2s linear infinite;
        }}

        .scene-title {{
            position:absolute;
            top:18px;
            left:25px;
            font-weight:700;
            font-size:18px;
        }}

        .scene-status {{
            position:absolute;
            top:45px;
            left:25px;
            opacity:.70;
            font-size:13px;
        }}

        </style>

        <div class="scene">
            <div class="scene-title">
                🧪 {safe_html_text(experiment)}
            </div>

            <div class="scene-status">
                Character: {safe_html_text(char)}
                &nbsp; | &nbsp;
                Equipment: {safe_html_text(equipment)}
            </div>

            <div class="beam"></div>

            <div class="robot">
                {robot_html}
                <div style="font-size:15px;">
                    {safe_html_text(char)}
                </div>
            </div>

            <div class="machine">
                {equipment_icon}
            </div>

            <div class="floor"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_attention_task():
    st.subheader("🎯 Attention Challenge")

    st.write("Find the target **X** as quickly as you can.")

    grid = [
        "O O O O O",
        "O O O O O",
        "O O X O O",
        "O O O O O",
        "O O O O O",
    ]

    st.code("\n".join(grid))

    answer = st.text_input(
        "What was the target?",
        key="lab_attention_answer",
    )

    if st.button("Check Attention", key="check_attention"):
        if answer.strip().upper() == "X":
            st.session_state.lab_result = (
                "Correct. The target was detected successfully. "
                "This task demonstrates selective visual attention."
            )
        else:
            st.session_state.lab_result = (
                "The target was X. Your response illustrates how "
                "attention can be influenced by competing information."
            )

        st.session_state.experiment_completed = True
        st.session_state.lab_completed += 1
        st.rerun()


def run_memory_task():
    st.subheader("🧠 Memory Sequence")

    sequence = "729418"

    st.write("Study this sequence for a few seconds:")
    st.code(sequence)

    time.sleep(0.2)

    answer = st.text_input(
        "Enter the sequence from memory",
        key="lab_memory_answer",
    )

    if st.button("Check Memory", key="check_memory"):
        if answer.strip() == sequence:
            st.session_state.lab_result = (
                "Excellent recall. The sequence was reproduced accurately."
            )
        else:
            st.session_state.lab_result = (
                f"The correct sequence was {sequence}. "
                "Memory performance can change with attention, "
                "interference and working-memory demands."
            )

        st.session_state.experiment_completed = True
        st.session_state.lab_completed += 1
        st.rerun()


def run_decision_task():
    st.subheader("💰 Decision & Reward")

    choice = st.radio(
        "Choose one:",
        [
            "Rs 1,000 today",
            "Rs 1,500 after 30 days",
        ],
        key="lab_decision_choice",
    )

    if st.button("Submit Decision", key="check_decision"):
        st.session_state.lab_result = (
            f"You selected: {choice}. "
            "This illustrates intertemporal choice and the tension "
            "between immediate and delayed rewards."
        )

        st.session_state.experiment_completed = True
        st.session_state.lab_completed += 1
        st.rerun()


def run_stroop_task():
    st.subheader("🎨 Stroop Control")

    st.write(
        "Identify the **INK COLOR**, not the written word."
    )

    color = st.selectbox(
        "What is the ink color?",
        ["RED", "BLUE", "GREEN", "YELLOW"],
        key="stroop_answer",
    )

    if st.button("Submit Stroop", key="check_stroop"):
        st.session_state.lab_result = (
            f"You selected {color}. Stroop-style tasks demonstrate "
            "how competing information can create cognitive interference."
        )

        st.session_state.experiment_completed = True
        st.session_state.lab_completed += 1
        st.rerun()


def ayna_lab_explanation():
    result = st.session_state.lab_result

    if not result:
        return

    st.markdown(
        f"""
        <div class="success-box">
        <h3>🤖 Ayna's Lab Analysis</h3>
        <p>{safe_html_text(result)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    browser_speech_button(
        result,
        "🔊 Play Ayna's Lab Explanation",
    )

    if not st.session_state.lab_followup:
        if st.button(
            "🧩 Try Follow-up Challenge",
            use_container_width=True,
        ):
            st.session_state.lab_followup = True
            st.rerun()
    else:
        st.subheader("🧩 Follow-up Challenge")

        followup = st.selectbox(
            "Choose your next challenge:",
            [
                "Increase difficulty",
                "Try another experiment",
                "Explore the brain system",
            ],
        )

        if followup == "Increase difficulty":
            st.info(
                "Next round: reduce response time and add more competing information."
            )

        elif followup == "Try another experiment":
            if st.button("Choose Next Experiment"):
                st.session_state.experiment_completed = False
                st.session_state.lab_result = None
                st.session_state.lab_followup = False
                st.session_state.page = "Lab"
                st.rerun()

        else:
            st.info(
                "Explore the relevant brain systems in the Explore Brain section."
            )


def page_lab():
    st.header("🧪 Cognitive Neuroscience Lab")

    st.write(
        "Select your researcher, equipment and experiment. "
        "Then run the task and receive Ayna's explanation."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.character = st.selectbox(
            "👤 Character",
            list(CHARACTERS.keys()),
            index=list(CHARACTERS.keys()).index(
                st.session_state.character
            ),
        )

    with col2:
        st.session_state.equipment = st.selectbox(
            "🔬 Equipment",
            list(EQUIPMENT.keys()),
            index=list(EQUIPMENT.keys()).index(
                st.session_state.equipment
            ),
        )

    with col3:
        st.session_state.experiment = st.selectbox(
            "🧪 Experiment",
            list(EXPERIMENTS.keys()),
            index=list(EXPERIMENTS.keys()).index(
                st.session_state.experiment
            ),
        )

    st.info(
        EXPERIMENTS[st.session_state.experiment]["description"]
    )

    if st.button(
        "⚙️ Apply Lab Setup",
        use_container_width=True,
    ):
        st.session_state.experiment_started = True
        st.session_state.experiment_completed = False
        st.session_state.lab_result = None
        st.session_state.lab_followup = False
        st.rerun()

    if st.session_state.experiment_started:
        lab_scene()

        st.markdown("### ▶️ Experiment Active")

        task_type = EXPERIMENTS[
            st.session_state.experiment
        ]["task"]

        if not st.session_state.experiment_completed:
            if task_type == "attention":
                run_attention_task()

            elif task_type == "memory":
                run_memory_task()

            elif task_type == "decision":
                run_decision_task()

            elif task_type == "stroop":
                run_stroop_task()

        else:
            ayna_lab_explanation()


# ============================================================
# EXPLORE BRAIN
# ============================================================

BRAIN_SYSTEMS = {
    "Prefrontal Cortex": {
        "description": (
            "Important for cognitive control, planning, working memory "
            "and goal-directed behavior."
        ),
        "function": "Cognitive control",
    },
    "Hippocampus": {
        "description": (
            "A key structure involved in memory formation and spatial processing."
        ),
        "function": "Memory",
    },
    "Striatum": {
        "description": (
            "Part of the basal ganglia involved in action selection, "
            "reward-related learning and movement."
        ),
        "function": "Action and reward",
    },
    "Anterior Cingulate Cortex": {
        "description": (
            "Associated with conflict monitoring, cognitive control "
            "and performance monitoring."
        ),
        "function": "Monitoring",
    },
    "Attention Networks": {
        "description": (
            "Distributed systems that help select relevant information "
            "and maintain task goals."
        ),
        "function": "Attention",
    },
}


def page_explore_brain():
    st.header("🧠 Explore Brain Systems")

    system = st.selectbox(
        "Choose a brain system",
        list(BRAIN_SYSTEMS.keys()),
    )

    data = BRAIN_SYSTEMS[system]

    st.markdown(
        f"""
        <div class="card">
        <h2>{safe_html_text(system)}</h2>
        <p>{safe_html_text(data["description"])}</p>
        <p><b>Primary concept:</b> {safe_html_text(data["function"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🤖 Ask Ayna About This System"):
        answer = ask_ai(
            f"Explain the role of the {system} in cognitive neuroscience.",
            system_context=data["description"],
        )

        st.markdown(answer)

        browser_speech_button(
            answer,
            "🔊 Play Ayna",
        )


# ============================================================
# BRAIN PUZZLE
# ============================================================

def page_brain_puzzle():
    st.header("🧩 Brain Puzzle")

    brain_path = find_asset("brain.png")

    if brain_path:
        try:
            image = Image.open(brain_path)
            st.image(image, use_container_width=True)
        except Exception:
            pass

    st.write(
        "Arrange the brain image pieces mentally and then record your completion."
    )

    difficulty = st.selectbox(
        "Puzzle difficulty",
        ["3 × 3", "4 × 4", "5 × 5"],
    )

    size = int(difficulty[0])

    puzzle_path = brain_path

    if puzzle_path:
        image_b64 = image_to_base64(puzzle_path)

        if image_b64:
            components.html(
                f"""
                <html>
                <style>
                .board {{
                    width: min(90vw, 500px);
                    height: min(90vw, 500px);
                    margin:auto;
                    display:grid;
                    grid-template-columns:repeat({size},1fr);
                    grid-template-rows:repeat({size},1fr);
                    gap:2px;
                    border:2px solid rgba(100,150,255,.5);
                    background:#101522;
                }}

                .tile {{
                    background-image:
                        url("data:image/png;base64,{image_b64}");
                    background-size:{size*100}% {size*100}%;
                    border:1px solid rgba(255,255,255,.08);
                }}
                </style>

                <div class="board">
                {''.join(
                    f'<div class="tile" style="background-position:'
                    f'{(i % size) * 100/(size-1) if size > 1 else 0}% '
                    f'{(i // size) * 100/(size-1) if size > 1 else 0}%;"></div>'
                    for i in range(size * size)
                )}
                </div>
                </html>
                """,
                height=550,
            )

    if st.button(
        "✅ I Completed the Puzzle",
        use_container_width=True,
    ):
        st.session_state.puzzle_completed = True
        st.session_state.games_completed += 1
        st.success(
            "Puzzle completion recorded in this session."
        )


# ============================================================
# AI MOOD & BEHAVIOUR
# ============================================================

def estimate_mood_from_text(text):
    answer = ask_ai(
        f"""
Analyze the following text for broad, non-diagnostic communication cues.

Text:
{text}

Return:
1. Apparent communication tone
2. Possible behavioural cues
3. Confidence level
4. What cannot be concluded from this input

Do not diagnose the person.
Do not claim to know their exact internal emotional state.
""",
        system_context=(
            "The result is an AI-generated interpretation of "
            "communication cues, not a clinical measurement."
        ),
    )

    st.session_state.mood_result = answer
    return answer


def page_mood_behaviour():
    st.header("🎙️ AI Mood & Behaviour")

    st.write(
        "Use text or voice input to explore broad communication cues "
        "with Ayna."
    )

    st.caption(
        "AI output is an interpretation of observable input, not a direct measurement of inner emotional state."
    )

    tab1, tab2 = st.tabs(
        ["🎙️ Voice", "💬 Text"]
    )

    with tab1:
        audio = st.audio_input(
            "Record Voice",
            key="mood_audio",
        )

        if audio is not None:
            st.audio(audio)

        if st.button(
            "📤 Send Voice",
            key="send_mood_voice",
            use_container_width=True,
            disabled=audio is None,
        ):
            st.info(
                "Voice file received. For full speech analysis, "
                "connect a speech-to-text service to NEUROLENS."
            )

            answer = ask_ai(
                "Explain how vocal communication features can relate to broad behavioural cues, while clearly distinguishing observable vocal features from inner emotional state.",
            )

            st.session_state.mood_result = answer

    with tab2:
        text = st.text_area(
            "Write something for Ayna to analyze",
            placeholder="Example: I have been working on a difficult research task...",
            key="mood_text",
            height=160,
        )

        if st.button(
            "📤 Send Text",
            key="send_mood_text",
            use_container_width=True,
        ):
            if not text.strip():
                st.warning("Please enter some text first.")
            else:
                estimate_mood_from_text(text)

    if st.session_state.mood_result:
        st.markdown(
            f"""
            <div class="card">
            <h3>🤖 Ayna's Analysis</h3>
            <p>{safe_html_text(st.session_state.mood_result)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        browser_speech_button(
            st.session_state.mood_result,
            "🔊 Play Ayna",
        )


# ============================================================
# BRAIN EXERCISES
# ============================================================

def page_brain_exercises():
    st.header("🏋️ Brain Exercises")

    exercise = st.selectbox(
        "Choose an exercise",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
        ],
    )

    if exercise == "Working Memory":
        st.write("Remember: **7 2 9 4 1 8**")

        answer = st.text_input("Enter the sequence")

        if st.button("Check"):
            if answer == "729418":
                st.success("Correct.")
                st.session_state.games_completed += 1
            else:
                st.warning("Try again.")

    elif exercise == "Attention":
        st.write("Find X:")

        st.code(
            "O O O O O\n"
            "O O O O O\n"
            "O O X O O\n"
            "O O O O O\n"
            "O O O O O"
        )

        answer = st.text_input("Target")

        if st.button("Submit Attention"):
            if answer.upper() == "X":
                st.success("Correct.")
                st.session_state.games_completed += 1
            else:
                st.error("The target was X.")

    elif exercise == "Pattern Recognition":
        st.write("2 → 4 → 8 → 16 → 32 → ?")

        answer = st.number_input(
            "Next number",
            min_value=0,
            step=1,
        )

        if st.button("Check Pattern"):
            if answer == 64:
                st.success("Correct.")
                st.session_state.games_completed += 1
            else:
                st.warning("The expected next value is 64.")

    else:
        choice = st.radio(
            "Choose your preference:",
            [
                "Rs 1,000 today",
                "Rs 1,500 after 30 days",
            ],
        )

        if st.button("Record Decision"):
            st.success(
                f"Recorded choice: {choice}"
            )
            st.session_state.games_completed += 1


# ============================================================
# RESEARCH BOOK
# ============================================================

def europe_pmc_search(query, page_size=8):
    endpoint = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    )

    params = urlencode(
        {
            "query": query,
            "format": "json",
            "resultType": "core",
            "pageSize": page_size,
        }
    )

    url = endpoint + "?" + params

    try:
        req = Request(
            url,
            headers={
                "User-Agent": "NEUROLENS/1.0 research interface"
            },
        )

        with urlopen(req, timeout=15) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        return data.get("resultList", {}).get("result", [])

    except Exception:
        return []


def page_research_book():
    st.header("📚 Research Book")

    st.write(
        "Search biomedical literature through Europe PMC."
    )

    query = st.text_input(
        "Research topic",
        placeholder="Example: attention cognitive neuroscience",
    )

    if st.button(
        "🔎 Search Research",
        use_container_width=True,
    ):
        if not query.strip():
            st.warning("Enter a research topic.")
        else:
            with st.spinner("Searching literature..."):
                results = europe_pmc_search(query)

            st.session_state.research_results = results

    results = st.session_state.research_results

    if results:
        st.success(
            f"{len(results)} results found."
        )

        for index, item in enumerate(results):
            title = item.get(
                "title",
                "Untitled paper",
            )

            authors = item.get(
                "authorString",
                "Authors unavailable",
            )

            year = item.get(
                "pubYear",
                "",
            )

            pmid = item.get(
                "pmid",
                "",
            )

            doi = item.get(
                "doi",
                "",
            )

            abstract = item.get(
                "abstractText",
                "Abstract unavailable.",
            )

            with st.expander(
                f"{index + 1}. {title}"
            ):
                st.write(
                    f"**Authors:** {authors}"
                )

                if year:
                    st.write(
                        f"**Year:** {year}"
                    )

                if pmid:
                    st.write(
                        f"**PMID:** {pmid}"
                    )

                if doi:
                    st.write(
                        f"**DOI:** {doi}"
                    )

                st.write(abstract)

                if st.button(
                    "📝 Save Research Note",
                    key=f"save_note_{index}",
                ):
                    st.session_state.research_notes.append(
                        {
                            "title": title,
                            "authors": authors,
                            "year": year,
                            "pmid": pmid,
                        }
                    )

                    st.session_state.research_completed += 1

    else:
        st.info(
            "Search a topic to explore current literature."
        )


# ============================================================
# ASK AYNA
# ============================================================

def page_ask_ayna():
    st.header("🤖 Ask Ayna")

    st.write(
        "Ask an educational cognitive neuroscience question."
    )

    question = st.text_area(
        "Your question",
        placeholder=(
            "Example: How does attention affect memory?"
        ),
        height=130,
        key="ask_ayna_question",
    )

    col1, col2 = st.columns(2)

    with col1:
        send = st.button(
            "📤 Send Text",
            use_container_width=True,
        )

    with col2:
        voice = st.audio_input(
            "🎙️ Record Voice",
            key="ayna_voice",
        )

    if send:
        if not question.strip():
            st.warning("Please write a question.")
        else:
            with st.spinner("Ayna is thinking..."):
                answer = ask_ai(question)

            st.markdown(
                f"""
                <div class="card">
                <h3>🧠 Ayna</h3>
                <p>{safe_html_text(answer)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            browser_speech_button(
                answer,
                "🔊 Play Ayna",
            )

    if voice is not None:
        st.audio(voice)

        if st.button(
            "📤 Send Voice",
            key="send_ayna_voice",
            use_container_width=True,
        ):
            answer = ask_ai(
                "Explain how spoken language can be studied in cognitive neuroscience. The uploaded voice is user input; do not claim to infer the user's exact mental state from it."
            )

            st.markdown(answer)

            browser_speech_button(
                answer,
                "🔊 Play Ayna",
            )


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

def hash_pin(pin, salt):
    return hashlib.sha256(
        (salt + pin).encode("utf-8")
    ).hexdigest()


def create_private_pin():
    st.subheader("🔐 Create Private PIN")

    pin = st.text_input(
        "Create a 4–6 digit PIN",
        type="password",
        max_chars=6,
        key="new_private_pin",
    )

    confirm = st.text_input(
        "Confirm PIN",
        type="password",
        max_chars=6,
        key="confirm_private_pin",
    )

    if st.button(
        "Create PIN",
        use_container_width=True,
    ):
        if not re.fullmatch(r"\d{4,6}", pin or ""):
            st.error(
                "PIN must contain 4–6 digits."
            )
            return

        if pin != confirm:
            st.error("PINs do not match.")
            return

        salt = secrets.token_hex(16)

        st.session_state.private_pin_salt = salt
        st.session_state.private_pin_hash = hash_pin(
            pin,
            salt,
        )

        st.session_state.private_unlocked = True

        st.success(
            "Private PIN created for this session."
        )

        st.info(
            "For permanent secure accounts, connect NEUROLENS to an authenticated backend/database."
        )


def unlock_private():
    st.subheader("🔓 Unlock Private Ask Ayna")

    pin = st.text_input(
        "Enter your PIN",
        type="password",
        max_chars=6,
        key="private_unlock_pin",
    )

    if st.button(
        "Unlock",
        use_container_width=True,
    ):
        expected = st.session_state.private_pin_hash
        salt = st.session_state.private_pin_salt

        if expected and hash_pin(pin, salt) == expected:
            st.session_state.private_unlocked = True
            st.success("Unlocked.")
            st.rerun()
        else:
            st.error("Incorrect PIN.")


def page_private_ask_ayna():
    st.header("🔐 Private Ask Ayna")

    if not st.session_state.private_pin_hash:
        create_private_pin()
        return

    if not st.session_state.private_unlocked:
        unlock_private()
        return

    st.success("Private mode unlocked.")

    question = st.text_area(
        "Private question",
        placeholder="Write your private research/cognition question...",
        height=150,
        key="private_question",
    )

    if st.button(
        "📤 Send Private Question",
        use_container_width=True,
    ):
        if not question.strip():
            st.warning("Write something first.")
        else:
            answer = ask_ai(
                question,
                system_context=(
                    "This is the user's private Ask Ayna area. "
                    "Keep the answer educational and do not diagnose."
                ),
            )

            st.markdown(answer)

            browser_speech_button(
                answer,
                "🔊 Play Ayna",
            )

    if st.button(
        "🔒 Lock Private Mode",
        use_container_width=True,
    ):
        st.session_state.private_unlocked = False
        st.rerun()


# ============================================================
# BEHAVIOUR DECODING FORUM
# ============================================================

def valid_phone(phone):
    return bool(
        re.fullmatch(
            r"[+]?[0-9][0-9\s\-]{7,17}",
            phone.strip(),
        )
    )


def page_forum():
    st.header("🧠 Behaviour Decoding Forum")

    st.write(
        "Request a professional discussion appointment with Ayna."
    )

    st.markdown(
        """
        <div class="card">
        <h3>How it works</h3>
        <ol>
            <li>Submit your discussion request.</li>
            <li>Select Pakistan or international payment.</li>
            <li>Complete the payment through the selected provider.</li>
            <li>Submit the payment/reference ID.</li>
            <li>Payment is verified.</li>
            <li>Discussion becomes available after verification.</li>
        </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("forum_request_form"):
        name = st.text_input(
            "Your name",
            value=st.session_state.forum_name,
        )

        phone = st.text_input(
            "Contact number",
            value=st.session_state.forum_phone,
        )

        problem = st.text_area(
            "Problem / concern / discussion topic",
            value=st.session_state.forum_problem,
            height=150,
        )

        slot = st.selectbox(
            "Preferred discussion slot",
            [
                "Morning",
                "Afternoon",
                "Evening",
            ],
        )

        submitted = st.form_submit_button(
            "📋 Submit Appointment Request",
            use_container_width=True,
        )

    if submitted:
        if not name.strip():
            st.error("Please enter your name.")

        elif not valid_phone(phone):
            st.error(
                "Please enter a valid contact number."
            )

        elif not problem.strip():
            st.error(
                "Please enter your discussion topic."
            )

        else:
            st.session_state.forum_name = name.strip()
            st.session_state.forum_phone = phone.strip()
            st.session_state.forum_problem = problem.strip()
            st.session_state.forum_slot = slot
            st.session_state.forum_status = "Appointment request submitted"

            st.success(
                "Appointment request saved for this session."
            )

    if st.session_state.forum_status != "Not started":

        st.divider()

        st.subheader("💳 Payment")

        payment_method = st.radio(
            "Choose payment method",
            [
                "🇵🇰 Easypaisa",
                "🌍 International Payment",
            ],
            key="forum_payment_method_radio",
        )

        if payment_method == "🇵🇰 Easypaisa":

            st.markdown(
                """
                <div class="small-card">
                <h4>🇵🇰 Easypaisa</h4>
                <p>
                Use the Easypaisa details provided by the NEUROLENS
                payment account.
                </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if EASYPAISA_NUMBER:
                st.code(EASYPAISA_NUMBER)

                if EASYPAISA_NAME:
                    st.write(
                        f"Account name: **{EASYPAISA_NAME}**"
                    )

                if CONSULTATION_FEE:
                    st.write(
                        f"Fee: **PKR {CONSULTATION_FEE}**"
                    )
            else:
                st.warning(
                    "Easypaisa number has not been configured yet. "
                    "Add EASYPAISA_NUMBER in Streamlit Secrets."
                )

            transaction_id = st.text_input(
                "Easypaisa Transaction / Reference ID",
                key="easypaisa_transaction_id",
            )

            if st.button(
                "📤 Submit Easypaisa Payment",
                use_container_width=True,
            ):
                if not transaction_id.strip():
                    st.error(
                        "Enter the transaction/reference ID."
                    )
                else:
                    st.session_state.forum_transaction_id = (
                        transaction_id.strip()
                    )

                    st.session_state.forum_payment_status = (
                        "Pending verification"
                    )

                    st.session_state.forum_status = (
                        "Payment submitted"
                    )

                    st.success(
                        "Payment reference submitted. "
                        "Status: Pending verification."
                    )

        else:

            st.markdown(
                """
                <div class="small-card">
                <h4>🌍 International Payment</h4>
                <p>
                International customers can use the connected
                payment provider when it is configured.
                </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if INTERNATIONAL_PAYMENT_URL:
                st.link_button(
                    "💳 Open International Payment",
                    INTERNATIONAL_PAYMENT_URL,
                    use_container_width=True,
                )
            else:
                st.info(
                    "International payment gateway is not connected yet. "
                    "Add INTERNATIONAL_PAYMENT_URL to Streamlit Secrets "
                    "after your payment provider is configured."
                )

            international_reference = st.text_input(
                "Payment Reference ID",
                key="international_reference",
            )

            if st.button(
                "📤 Submit International Payment",
                use_container_width=True,
            ):
                if not international_reference.strip():
                    st.error(
                        "Enter your payment reference."
                    )
                else:
                    st.session_state.forum_transaction_id = (
                        international_reference.strip()
                    )

                    st.session_state.forum_payment_status = (
                        "Pending verification"
                    )

                    st.session_state.forum_status = (
                        "Payment submitted"
                    )

                    st.success(
                        "Payment reference submitted. "
                        "Status: Pending verification."
                    )

        st.divider()

        st.subheader("📌 Payment Status")

        status = st.session_state.forum_payment_status

        if status == "Pending verification":
            st.warning(
                "Payment submitted — waiting for verification."
            )

        elif status == "Verified":
            st.success(
                "Payment verified. Discussion is unlocked."
            )

        else:
            st.info(status)

        st.caption(
            "A transaction/reference ID alone does not automatically verify a payment. "
            "For automatic verification, connect the official payment provider's "
            "merchant/API/webhook system."
        )

        # ----------------------------------------------------
        # Discussion unlock
        # ----------------------------------------------------

        if status == "Verified":

            st.divider()

            st.subheader("💬 Direct Discussion")

            st.success(
                "Your payment is verified. You can now discuss your topic."
            )

            for message in st.session_state.forum_messages:
                role = message["role"]

                if role == "user":
                    st.chat_message(
                        "user"
                    ).write(message["text"])

                else:
                    st.chat_message(
                        "assistant"
                    ).write(message["text"])

            message = st.chat_input(
                "Write your discussion message..."
            )

            if message:
                st.session_state.forum_messages.append(
                    {
                        "role": "user",
                        "text": message,
                    }
                )

                answer = ask_ai(
                    message,
                    system_context=(
                        "Behaviour Decoding Forum discussion. "
                        "Provide educational cognitive neuroscience "
                        "information. Do not diagnose."
                    ),
                )

                st.session_state.forum_messages.append(
                    {
                        "role": "assistant",
                        "text": answer,
                    }
                )

                st.rerun()


# ============================================================
# DEMO / ADMIN PAYMENT VERIFICATION
# ============================================================

def page_payment_demo():
    st.header("🧾 Payment Verification Setup")

    st.info(
        "This section is for development/testing. "
        "Do not use it as a real payment verification system."
    )

    if st.button(
        "🧪 Demo: Mark Latest Payment Verified",
        use_container_width=True,
    ):
        if st.session_state.forum_transaction_id:
            st.session_state.forum_payment_status = "Verified"
            st.success(
                "Demo verification applied for this session."
            )
        else:
            st.warning(
                "No payment reference is available."
            )


# ============================================================
# MY PROGRESS
# ============================================================

def page_progress():
    st.header("📊 My Progress")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Games",
            st.session_state.games_completed,
        )

    with col2:
        st.metric(
            "Lab",
            st.session_state.lab_completed,
        )

    with col3:
        st.metric(
            "Research",
            st.session_state.research_completed,
        )

    with col4:
        st.metric(
            "AI Requests",
            st.session_state.ai_requests,
        )

    if go:
        labels = [
            "Games",
            "Lab",
            "Research",
        ]

        values = [
            st.session_state.games_completed,
            st.session_state.lab_completed,
            st.session_state.research_completed,
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=values,
                )
            ]
        )

        fig.update_layout(
            title="NEUROLENS Activity",
            height=350,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# SETTINGS
# ============================================================

def page_settings():
    st.header("⚙️ Settings")

    st.session_state.language = st.selectbox(
        "Language",
        [
            "English",
            "Roman Urdu",
        ],
        index=[
            "English",
            "Roman Urdu",
        ].index(
            st.session_state.language
        ),
    )

    st.write(
        f"AI connection: "
        f"{'Connected' if ai_available() else 'Not connected'}"
    )

    st.write(
        f"AI requests this session: "
        f"{st.session_state.ai_requests}/{AI_SESSION_LIMIT}"
    )

    st.divider()

    st.subheader("Payment Configuration")

    st.write(
        "Easypaisa configured:",
        bool(EASYPAISA_NUMBER),
    )

    st.write(
        "International gateway configured:",
        bool(INTERNATIONAL_PAYMENT_URL),
    )


# ============================================================
# SIDEBAR
# ============================================================

render_header()

with st.sidebar:

    st.markdown(
        f"""
        <div style="text-align:center;padding:10px;">
            <div style="font-size:42px;">🧠</div>
            <h2>{APP_NAME}</h2>
            <div class="muted">{CREATOR}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    pages = [
        "Welcome",
        "Lab",
        "Explore Brain",
        "Brain Puzzle",
        "AI Mood & Behaviour",
        "Brain Exercises",
        "Research Book",
        "Ask Ayna",
        "Private Ask Ayna",
        "Behaviour Decoding Forum",
        "Payment Demo",
        "My Progress",
        "Settings",
    ]

    selected_page = st.radio(
        "Navigate",
        pages,
        index=pages.index(
            st.session_state.page
        ),
    )

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()

    st.divider()

    st.caption(
        "NEUROLENS explores cognition, behaviour and brain science."
    )


# ============================================================
# PAGE ROUTER
# ============================================================

page = st.session_state.page

if page == "Welcome":
    page_welcome()

elif page == "Lab":
    page_lab()

elif page == "Explore Brain":
    page_explore_brain()

elif page == "Brain Puzzle":
    page_brain_puzzle()

elif page == "AI Mood & Behaviour":
    page_mood_behaviour()

elif page == "Brain Exercises":
    page_brain_exercises()

elif page == "Research Book":
    page_research_book()

elif page == "Ask Ayna":
    page_ask_ayna()

elif page == "Private Ask Ayna":
    page_private_ask_ayna()

elif page == "Behaviour Decoding Forum":
    page_forum()

elif page == "Payment Demo":
    page_payment_demo()

elif page == "My Progress":
    page_progress()

elif page == "Settings":
    page_settings()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    f"""
    <div style="text-align:center;opacity:.55;font-size:13px;">
        🧠 {APP_NAME} · Explore cognition, behavior & the brain
        <br>
        Created by {CREATOR}
    </div>
    """,
    unsafe_allow_html=True,
)
