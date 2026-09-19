import os
import re
import time
import json
import random
import hashlib
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime
from io import BytesIO

import streamlit as st
from PIL import Image

# =========================================================
# OPTIONAL PACKAGES
# =========================================================

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

try:
    import numpy as np
except Exception:
    np = None

try:
    import cv2
except Exception:
    cv2 = None

try:
    import mediapipe as mp
except Exception:
    mp = None

try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
except Exception:
    webrtc_streamer = None
    VideoProcessorBase = object

try:
    from streamlit_dnd import dnd, apply_move
except Exception:
    dnd = None
    apply_move = None

try:
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
except Exception:
    BoardShim = None
    BrainFlowInputParams = None
    BoardIds = None


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


# =========================================================
# ASSETS
# =========================================================

def asset(name):
    p1 = os.path.join(ASSETS, name)
    p2 = os.path.join(ROOT, name)

    if os.path.exists(p1):
        return p1
    if os.path.exists(p2):
        return p2
    return None


BRAIN_PATH = asset("brain.png")
AYNA_ROBOT = asset("ayna_robot.png")
REBOOT_VIDEO = asset("ayna_reboot_voiced.mp4")
LAB_VIDEO = asset("cognitive_lab_brain.mp4")
BRAIN_VIDEO = asset("brain_animation.mp4")


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 0%, #173e63 0%, transparent 30%),
        radial-gradient(circle at 100% 20%, #1b3458 0%, transparent 25%),
        linear-gradient(135deg,#06101d,#0a1728);
}

.block-container {
    max-width: 1450px;
    padding-top: 1rem;
}

.hero {
    padding: 25px;
    border-radius: 24px;
    background: linear-gradient(135deg,#102b48,#111a30);
    border: 1px solid #365777;
    margin-bottom: 18px;
}

.card {
    padding: 18px;
    border-radius: 18px;
    background: #0d2035;
    border: 1px solid #294866;
    margin: 8px 0;
}

.lab {
    min-height: 300px;
    border-radius: 25px;
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle,#2b6598 0,#102d4d 28%,#06101d 70%);
    border: 1px solid #3c607d;
}

.orb {
    position:absolute;
    width:100px;
    height:100px;
    border-radius:50%;
    left:calc(50% - 50px);
    top:calc(50% - 50px);
    background:radial-gradient(circle,#fff,#8fd8ff 20%,#6674ff 55%,#30245f);
    box-shadow:0 0 55px #74c7ff;
    animation:pulse 2s infinite;
}

@keyframes pulse {
    50% { transform:scale(1.12); }
}

.stage {
    min-height:230px;
    border-radius:22px;
    background:radial-gradient(circle,#153d63,#071321);
    border:1px solid #38536e;
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
}

.neuron {
    font-size:5rem;
    animation:pulse 1.5s infinite;
}

.signal {
    font-size:3rem;
    animation:moveSignal 2s linear infinite;
}

@keyframes moveSignal {
    from {transform:translateX(-180px);}
    to {transform:translateX(180px);}
}

.small {
    opacity:.75;
    font-size:.9rem;
}

.puzzle-piece {
    border-radius:12px;
    overflow:hidden;
    border:2px solid #284d6b;
}

.badge {
    display:inline-block;
    padding:6px 10px;
    border-radius:12px;
    background:#173b5f;
    margin:3px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE
# =========================================================

DB_PATH = os.path.join(ROOT, "neurolens.db")


def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activity(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity TEXT,
            score REAL,
            details TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS research_notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            note TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS consultations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            contact TEXT,
            topic TEXT,
            duration TEXT,
            amount INTEGER,
            payment_ref TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


def save_activity(name, score=0, details=""):
    conn = db()
    conn.execute(
        """
        INSERT INTO activity(activity,score,details,created_at)
        VALUES(?,?,?,?)
        """,
        (
            name,
            float(score),
            str(details)[:2000],
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()


def save_note(title, note):
    conn = db()
    conn.execute(
        """
        INSERT INTO research_notes(title,note,created_at)
        VALUES(?,?,?)
        """,
        (
            title[:300],
            note[:5000],
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()


def save_ai(kind):
    conn = db()
    conn.execute(
        "INSERT INTO ai_requests(request_type,created_at) VALUES(?,?)",
        (kind, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


# =========================================================
# SESSION STATE
# =========================================================

def default_progress():
    return {
        "experiments": 0,
        "games": 0,
        "puzzles": 0,
        "research": 0,
        "ai": 0,
        "accuracy": 0,
    }


defaults = {
    "page": "Welcome",
    "language": "English",
    "character": "Researcher",
    "equipment": "EEG Simulator",
    "progress": default_progress(),
    "ai_count": 0,
    "ai_window_start": time.time(),
    "messages": [],
    "private_messages": [],
    "private_pin_hash": None,
    "private_unlocked": False,
    "research_results": [],
    "research_notes": [],
    "experiment_history": [],
    "puzzle_board": None,
    "puzzle_solution": None,
    "puzzle_grid": 3,
    "puzzle_started": None,
    "puzzle_moves": 0,
    "puzzle_round": 1,
    "puzzle_completed": False,
    "puzzle_best_time": None,
    "puzzle_best_score": 0,
    "puzzle_best_moves": None,
    "puzzle_challenge": "Time Challenge",
    "daily_done": False,
    "eye_samples": [],
}

for k, v in defaults.items():
    if k not in st.session_state:
        if isinstance(v, dict):
            st.session_state[k] = dict(v)
        elif isinstance(v, list):
            st.session_state[k] = list(v)
        else:
            st.session_state[k] = v


# =========================================================
# NAVIGATION
# =========================================================

PAGES = [
    "Welcome",
    "Virtual Cognitive Lab",
    "Eye Tracking",
    "EEG / Biosignal Lab",
    "Visual Brain Journey",
    "Brain Puzzle",
    "Ask Ayna",
    "Private Ask Ayna",
    "Voice Mood",
    "AI Mood & Behaviour",
    "Research Book",
    "Behaviour Decoding",
    "Brain Exercises",
    "Daily Experiment",
    "My Progress",
    "Security & Privacy",
    "Settings",
]


def go(page):
    st.session_state.page = page
    st.rerun()


# =========================================================
# SECURITY HELPERS
# =========================================================

def clean_text(value, limit=3000):
    value = str(value or "")
    value = value.replace("\x00", " ")
    return value.strip()[:limit]


def pin_hash(pin):
    salt = b"NEUROLENS-PIN-SALT"
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt,
        120000,
    ).hex()


# =========================================================
# GEMINI
# =========================================================

def api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY", "").strip()


MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


@st.cache_resource(show_spinner=False)
def gemini_client(key):
    if not key or genai is None:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def ai_allowed():
    now = time.time()

    if now - st.session_state.ai_window_start > 3600:
        st.session_state.ai_window_start = now
        st.session_state.ai_count = 0

    return st.session_state.ai_count < 40


def ask_ai(prompt, context="", max_tokens=500):
    prompt = clean_text(prompt, 3500)
    context = clean_text(context, 5000)

    if not ai_allowed():
        return (
            "AI session protection limit reached. "
            "You can continue using the local NEUROLENS tools.",
            "rate-limit",
        )

    client = gemini_client(api_key())

    if client is None:
        return (
            "Ayna is not connected. Add GEMINI_API_KEY in "
            "Streamlit Secrets.",
            "offline",
        )

    system = """
You are Ayna, the educational cognitive-neuroscience AI assistant
inside NEUROLENS.

Rules:
- Be scientifically cautious.
- Do not diagnose.
- Do not claim a simple game measures brain activity.
- Do not claim voice analysis can reveal someone's hidden personality,
  mental disorder or exact internal emotional state.
- Distinguish observation, interpretation and uncertainty.
- Keep answers useful and concise.
"""

    full_prompt = (
        system
        + "\n\nCONTEXT:\n"
        + context
        + "\n\nUSER REQUEST:\n"
        + prompt
    )

    try:
        st.session_state.ai_count += 1
        st.session_state.progress["ai"] += 1
        save_ai("text")

        if types:
            cfg = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_tokens,
            )

            result = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
                config=cfg,
            )
        else:
            result = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
            )

        text = (getattr(result, "text", "") or "").strip()

        if not text:
            text = "Ayna returned no text."

        return text, "Gemini"

    except Exception as e:
        return (
            "Ayna could not complete the request right now.",
            f"error: {type(e).__name__}",
        )


def ask_ai_audio(audio, instruction):
    if not audio:
        return "No voice recording was provided.", "none"

    if not ai_allowed():
        return "AI session protection limit reached.", "rate-limit"

    client = gemini_client(api_key())

    if client is None or types is None:
        return (
            "Voice AI needs GEMINI_API_KEY and google-genai.",
            "offline",
        )

    try:
        data = audio.getvalue()
        mime = audio.type or "audio/wav"

        part = types.Part.from_bytes(
            data=data,
            mime_type=mime,
        )

        st.session_state.ai_count += 1
        st.session_state.progress["ai"] += 1
        save_ai("voice")

        result = client.models.generate_content(
            model=MODEL,
            contents=[part, instruction],
        )

        text = (getattr(result, "text", "") or "").strip()

        return text or "No voice interpretation was returned.", "Gemini voice"

    except Exception:
        return (
            "Ayna could not process this voice recording.",
            "voice-error",
        )


# =========================================================
# BROWSER VOICE
# =========================================================

def speak(text, key):
    safe = (
        clean_text(text, 5000)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    html = f"""
    <button
      onclick="speakAyna()"
      style="
      padding:10px 16px;
      border-radius:10px;
      border:1px solid #789;
      background:#ffffff;
      color:#111;
      font-weight:600;
      cursor:pointer;">
      🔊 Speak Ayna
    </button>

    <script>
    function speakAyna(){{
        window.speechSynthesis.cancel();

        const text = `{safe}`;
        const utterance = new SpeechSynthesisUtterance(text);

        utterance.lang = "en-US";
        utterance.rate = 1.05;
        utterance.pitch = 1.03;

        window.speechSynthesis.speak(utterance);
    }}
    </script>
    """

    st.components.v1.html(html, height=55)


# =========================================================
# DATA
# =========================================================

BRAIN_REGIONS = {
    "Prefrontal Cortex": {
        "description": "Planning, working memory, cognitive control and goal-directed behaviour.",
        "function": "Decision-making, inhibition, planning.",
        "network": "Prefrontal cortex ↔ basal ganglia ↔ thalamus ↔ cortex",
    },
    "Hippocampus": {
        "description": "Important for episodic memory and spatial representation.",
        "function": "Memory, learning and navigation.",
        "network": "Hippocampus ↔ entorhinal cortex ↔ distributed cortex",
    },
    "Striatum": {
        "description": "Participates in action selection, reward learning and habits.",
        "function": "Reward learning, action selection and habits.",
        "network": "Cortex → striatum → pallidal pathways → thalamus → cortex",
    },
    "Anterior Cingulate Cortex": {
        "description": "Contributes to conflict processing, performance monitoring and control.",
        "function": "Error monitoring, conflict and effort.",
        "network": "ACC ↔ prefrontal ↔ striatal networks",
    },
    "Amygdala": {
        "description": "Processes emotionally significant information and contributes to emotional learning.",
        "function": "Salience, threat-related processing and learning.",
        "network": "Amygdala ↔ hypothalamus ↔ brainstem/cortex",
    },
    "Cerebellum": {
        "description": "Supports coordination, timing and motor learning and also contributes to cognition.",
        "function": "Timing, coordination and motor learning.",
        "network": "Cerebellum → deep nuclei → thalamus → cortex",
    },
}


NEUROTRANSMITTERS = {
    "Dopamine": "Reward learning, motivation, movement and several cognitive processes.",
    "Serotonin": "Mood-related processes, sleep, appetite and physiological functions.",
    "GABA": "Major inhibitory neurotransmitter in the central nervous system.",
    "Glutamate": "Major excitatory neurotransmitter important for learning and plasticity.",
    "Acetylcholine": "Contributes to attention, learning, memory and neuromuscular communication.",
}


EQUIPMENT = [
    "EEG Simulator",
    "Eye Tracker",
    "Reaction-Time System",
    "Cognitive Task Monitor",
    "Physiological Sensor",
]


EXPERIMENTS = [
    ("Attention Gate", "Attention"),
    ("Working Memory Sprint", "Working Memory"),
    ("Decision Under Delay", "Decision & Reward"),
    ("Stroop Control", "Cognitive Control"),
    ("Pattern Recognition", "Pattern Recognition"),
]


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    st.caption("Explore cognition, behaviour & the brain")

    language = st.radio(
        "Language",
        ["English", "Roman English"],
        index=0 if st.session_state.language == "English" else 1,
    )

    st.session_state.language = language

    st.divider()

    for i, page in enumerate(PAGES):

        active = page == st.session_state.page

        label = ("● " if active else "○ ") + page

        if st.button(
            label,
            key=f"nav_{i}",
            use_container_width=True,
        ):
            go(page)

    st.divider()

    st.caption(
        f"AI requests this session: "
        f"{st.session_state.ai_count}/40"
    )

    st.progress(
        min(st.session_state.ai_count / 40, 1)
    )


# =========================================================
# HEADER
# =========================================================

if st.session_state.page != "Welcome":

    st.markdown(
        """
        <div class="hero">
        <h1>🧠 NEUROLENS</h1>
        <p>Explore cognition, behaviour & the brain</p>
        <small>
        Independent cognitive neuroscience project •
        Created by Ayna Jaffri
        </small>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# WELCOME
# =========================================================

if st.session_state.page == "Welcome":

    st.markdown(
        """
        <div class="hero">
        <h1>🧠 NEUROLENS</h1>
        <h3>Welcome to the Cognitive Neuroscience Lab</h3>
        <p>Brain • Behaviour • Cognition • AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if REBOOT_VIDEO:

        try:
            with open(REBOOT_VIDEO, "rb") as f:
                st.video(f.read())
        except Exception:
            st.video(REBOOT_VIDEO)

    elif AYNA_ROBOT:
        st.image(AYNA_ROBOT, use_container_width=True)

    else:
        st.markdown(
            """
            <div class="lab">
              <div class="orb"></div>
              <div style="position:absolute;top:20px;left:20px">
              AYNA • COGNITIVE NEUROSCIENCE SYSTEM
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if language == "Roman English":
        welcome = (
            "Welcome to NeuroLens! Main Ayna hoon, "
            "aap ki cognitive neuroscience lab assistant. "
            "Let's explore brain, behaviour aur cognition together."
        )
    else:
        welcome = (
            "Welcome to NeuroLens! I'm Ayna, your cognitive "
            "neuroscience lab assistant. Let's explore the brain, "
            "behaviour, and cognition together."
        )

    st.markdown("### 🤖 Ayna")
    st.write(welcome)

    speak(welcome, "welcome_voice")

    st.info(
        "Browser voice ke liye Speak Ayna button use karein. "
        "Video ki original voice aur browser speech automatically "
        "frame-perfect lip-sync nahi hoti."
    )

    if st.button(
        "🚀 Enter NEUROLENS",
        type="primary",
        use_container_width=True,
    ):
        go("Virtual Cognitive Lab")


# =========================================================
# VIRTUAL LAB
# =========================================================

elif st.session_state.page == "Virtual Cognitive Lab":

    st.subheader("🔬 Virtual Cognitive Neuroscience Lab")

    character = st.selectbox(
        "👤 Character",
        [
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent",
        ],
        index=[
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent",
        ].index(st.session_state.character),
    )

    st.session_state.character = character

    equipment = st.selectbox(
        "🧪 Equipment",
        EQUIPMENT,
        index=EQUIPMENT.index(st.session_state.equipment),
    )

    st.session_state.equipment = equipment

    c1, c2 = st.columns([1.4, 1])

    with c1:

        if LAB_VIDEO:

            try:
                with open(LAB_VIDEO, "rb") as f:
                    st.video(f.read())
            except Exception:
                st.video(LAB_VIDEO)

        else:

            st.markdown(
                """
                <div class="lab">
                <div class="orb"></div>
                <div style="position:absolute;top:20px;left:20px">
                LIVE COGNITIVE LAB SIMULATION
                </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c2:

        st.markdown("### Current setup")

        st.write(f"**Character:** {character}")
        st.write(f"**Equipment:** {equipment}")

        st.info(
            "Educational simulation. Equipment does not automatically "
            "measure real neural activity."
        )

    st.markdown("### 🧪 Select experiment")

    experiment_names = [x[0] for x in EXPERIMENTS]

    experiment = st.selectbox(
        "Experiment",
        experiment_names,
    )

    domain = dict(EXPERIMENTS)[experiment]

    st.caption(f"Domain: {domain}")

    if experiment == "Attention Gate":

        target = random.choice(["X", "O", "K"])
        letters = [
            random.choice(["X", "O", "K", "M", "P"])
            for _ in range(12)
        ]
        letters[random.randint(0, 11)] = target

        st.write("Find the target:", " ".join(letters))

        answer = st.text_input(
            f"How many {target}s do you see?"
        )

        if st.button("Run Attention Experiment"):

            try:
                correct = int(answer) == letters.count(target)
            except Exception:
                correct = False

            score = 100 if correct else 0

            if correct:
                st.success("Correct response recorded.")
            else:
                st.warning(
                    f"Expected {letters.count(target)}."
                )

            save_activity(
                experiment,
                score,
                f"Target={target}",
            )

            st.session_state.progress["experiments"] += 1
            st.session_state.progress["games"] += 1

    elif experiment == "Working Memory Sprint":

        seq = "7 2 9 4 1 8"

        st.info(f"Memorize: {seq}")

        time.sleep(0.1)

        answer = st.text_input("Enter the sequence")

        if st.button("Run Memory Experiment"):

            correct = answer.replace(" ", "") == "729418"

            if correct:
                st.success("Memory response correct.")
                score = 100
            else:
                st.warning("Sequence did not match.")
                score = 0

            save_activity(
                experiment,
                score,
                "Working memory sequence",
            )

            st.session_state.progress["experiments"] += 1
            st.session_state.progress["games"] += 1

    elif experiment == "Decision Under Delay":

        choice = st.radio(
            "Choose one:",
            [
                "Rs. 1,000 today",
                "Rs. 1,500 after 30 days",
            ],
        )

        if st.button("Record Decision"):

            st.success("Decision recorded.")

            save_activity(
                experiment,
                0,
                choice,
            )

            st.session_state.progress["experiments"] += 1

            st.info(
                "This task explores delayed-reward preference. "
                "One choice does not define personality or behaviour."
            )

    elif experiment == "Stroop Control":

        word = random.choice(
            ["RED", "BLUE", "GREEN"]
        )

        st.markdown(f"### {word}")

        answer = st.selectbox(
            "Select the displayed word:",
            ["RED", "BLUE", "GREEN"],
        )

        if st.button("Submit Stroop Response"):

            correct = answer == word

            if correct:
                st.success("Correct.")
                score = 100
            else:
                st.warning("Response mismatch.")
                score = 0

            save_activity(
                experiment,
                score,
                word,
            )

            st.session_state.progress["experiments"] += 1

    else:

        st.write("Complete the pattern:")

        st.markdown("### 2 → 4 → 8 → 16 → ?")

        answer = st.number_input(
            "Next number",
            min_value=0,
            value=0,
        )

        if st.button("Run Pattern Experiment"):

            correct = answer == 32

            if correct:
                st.success("Pattern correct.")
                score = 100
            else:
                st.warning("Try again.")
                score = 0

            save_activity(
                experiment,
                score,
                "Pattern recognition",
            )

            st.session_state.progress["experiments"] += 1

    st.divider()

    st.markdown("### 📈 Simulated laboratory signal")

    if np is not None and go is not None:

        x = np.linspace(0, 4, 250)

        signal = (
            np.sin(2 * np.pi * 8 * x)
            + 0.35 * np.sin(2 * np.pi * 14 * x)
            + 0.15 * np.random.randn(len(x))
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=x,
                y=signal,
                mode="lines",
                name="Simulated signal",
            )
        )

        fig.update_layout(
            height=300,
            title="Conceptual simulated neural signal",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.caption(
        "⚠️ This waveform is simulated. It is not an EEG/fMRI measurement."
    )


# =========================================================
# EYE TRACKING
# =========================================================

elif st.session_state.page == "Eye Tracking":

    st.subheader("👁️ Webcam Eye Tracking")

    st.warning(
        "This is webcam-based gaze estimation, not research-grade "
        "eye tracking. Camera permission is required."
    )

    if webrtc_streamer is None:

        st.error(
            "streamlit-webrtc is not installed."
        )

    elif mp is None or cv2 is None:

        st.error(
            "MediaPipe/OpenCV is not available."
        )

    else:

        class GazeProcessor(VideoProcessorBase):

            def __init__(self):
                self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )

                self.samples = []

            def recv(self, frame):

                image = frame.to_ndarray(format="bgr24")

                rgb = cv2.cvtColor(
                    image,
                    cv2.COLOR_BGR2RGB,
                )

                result = self.face_mesh.process(rgb)

                if result.multi_face_landmarks:

                    landmarks = result.multi_face_landmarks[0]

                    left = landmarks.landmark[468]

                    gx = float(left.x)
                    gy = float(left.y)

                    self.samples.append(
                        {
                            "x": gx,
                            "y": gy,
                            "time": time.time(),
                        }
                    )

                    self.samples = self.samples[-300:]

                    cv2.circle(
                        image,
                        (
                            int(gx * image.shape[1]),
                            int(gy * image.shape[0]),
                        ),
                        8,
                        (0, 255, 255),
                        -1,
                    )

                return frame.from_ndarray(
                    image,
                    format="bgr24",
                )

        ctx = webrtc_streamer(
            key="neurolens-eye",
            video_processor_factory=GazeProcessor,
            media_stream_constraints={
                "video": True,
                "audio": False,
            },
            async_processing=True,
        )

        st.info(
            "Move your eyes around the screen after camera access. "
            "The displayed point is a rough webcam landmark estimate."
        )

        st.markdown("### 👁️ What this module can demonstrate")

        st.write(
            """
            • approximate gaze position  
            • visual attention demonstrations  
            • webcam landmark tracking  
            • conceptual fixation data  
            """
        )


# =========================================================
# EEG / BIOSIGNAL
# =========================================================

elif st.session_state.page == "EEG / Biosignal Lab":

    st.subheader("🧠 EEG / Biosignal Lab")

    st.info(
        "Real EEG requires compatible physical hardware. "
        "The synthetic mode works without hardware."
    )

    mode = st.radio(
        "Mode",
        ["Synthetic EEG", "Real BrainFlow connection"],
        horizontal=True,
    )

    if mode == "Synthetic EEG":

        if np is None or go is None:

            st.error(
                "NumPy/Plotly required."
            )

        else:

            t = np.linspace(0, 5, 1000)

            alpha = np.sin(
                2 * np.pi * 10 * t
            )

            beta = 0.4 * np.sin(
                2 * np.pi * 20 * t
            )

            noise = 0.2 * np.random.randn(
                len(t)
            )

            signal = alpha + beta + noise

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=t,
                    y=signal,
                    mode="lines",
                    name="Synthetic EEG",
                )
            )

            fig.update_layout(
                height=350,
                title="Synthetic EEG-like waveform",
                xaxis_title="Time (s)",
                yaxis_title="Amplitude",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.success(
                "Synthetic EEG running."
            )

    else:

        if BoardShim is None:

            st.error(
                "BrainFlow is not installed."
            )

        else:

            if st.button(
                "🔌 Test BrainFlow Synthetic Board"
            ):

                board = None

                try:

                    params = BrainFlowInputParams()

                    board_id = (
                        BoardIds.SYNTHETIC_BOARD.value
                    )

                    board = BoardShim(
                        board_id,
                        params,
                    )

                    board.prepare_session()
                    board.start_stream()

                    time.sleep(2)

                    data = board.get_board_data()

                    board.stop_stream()
                    board.release_session()

                    st.success(
                        f"BrainFlow connection successful. "
                        f"Received shape: {data.shape}"
                    )

                except Exception as e:

                    if board:

                        try:
                            board.release_session()
                        except Exception:
                            pass

                    st.error(
                        f"BrainFlow test failed: {e}"
                    )

            st.caption(
                "For actual EEG hardware, configure the correct BrainFlow board "
                "and device connection parameters."
            )


# =========================================================
# VISUAL BRAIN JOURNEY
# =========================================================

elif st.session_state.page == "Visual Brain Journey":

    st.subheader("🧠 Visual Brain Journey")

    if BRAIN_VIDEO:

        try:
            with open(BRAIN_VIDEO, "rb") as f:
                st.video(f.read())
        except Exception:
            st.video(BRAIN_VIDEO)

    if BRAIN_PATH:

        st.image(
            BRAIN_PATH,
            use_container_width=True,
        )

    region = st.selectbox(
        "Choose brain region",
        list(BRAIN_REGIONS),
    )

    info = BRAIN_REGIONS[region]

    st.markdown(f"## {region}")

    st.write(info["description"])

    st.success(
        f"Primary conceptual role: {info['function']}"
    )

    st.markdown(
        f"**Network / pathway:** {info['network']}"
    )

    stage = st.selectbox(
        "Journey stage",
        [
            "Brain Region",
            "Neuron",
            "Axon",
            "Electrical Signal",
            "Synapse",
            "Neurotransmitter",
        ],
    )

    stage_icons = {
        "Brain Region": "🧠",
        "Neuron": "🧬",
        "Axon": "➰",
        "Electrical Signal": "⚡",
        "Synapse": "🔗",
        "Neurotransmitter": "🧪",
    }

    st.markdown(
        f"""
        <div class="stage">
        <div class="neuron">
        {stage_icons[stage]}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### Current stage: {stage}")

    if stage == "Brain Region":
        st.write(
            "The selected region is considered as part of a distributed "
            "network rather than an isolated 'single-function box'."
        )

    elif stage == "Neuron":
        st.write(
            "Neurons receive, integrate and transmit information."
        )

    elif stage == "Axon":
        st.write(
            "Axons carry electrical signals toward downstream targets."
        )

    elif stage == "Electrical Signal":
        st.write(
            "Action potentials are electrical events that propagate "
            "along neuronal axons."
        )

    elif stage == "Synapse":
        st.write(
            "Synapses allow communication between neurons or other cells."
        )

    else:

        nt = st.selectbox(
            "Choose neurotransmitter",
            list(NEUROTRANSMITTERS),
        )

        st.info(
            NEUROTRANSMITTERS[nt]
        )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("⬅ Previous Region"):
            names = list(BRAIN_REGIONS)
            i = names.index(region)
            go(
                "Visual Brain Journey"
            )

    with c2:
        if st.button("🔄 Restart Journey"):
            st.rerun()

    with c3:
        if st.button("➡ Next Region"):
            names = list(BRAIN_REGIONS)
            i = names.index(region)
            next_region = names[
                (i + 1) % len(names)
            ]
            st.session_state["journey_region"] = next_region
            st.rerun()


# =========================================================
# BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    st.subheader("🧩 Brain Jigsaw Challenge")

    st.caption(
        "Finger/mouse press-hold drag-and-drop. "
        "Correct tile placement is required."
    )

    if dnd is None:

        st.error(
            "Install streamlit-dnd>=0.2.0 in requirements.txt."
        )

    elif not BRAIN_PATH:

        st.error(
            "brain.png not found. Put brain.png in the app root "
            "or inside the assets folder."
        )

    else:

        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
        )

        challenge = st.selectbox(
            "Challenge mode",
            [
                "Time Challenge",
                "Minimum Moves",
                "Speed Mode",
                "Memory Mode",
            ],
        )

        grid_map = {
            "Easy": 3,
            "Medium": 4,
            "Hard": 5,
        }

        grid = grid_map[difficulty]

        st.session_state.puzzle_challenge = challenge

        def make_tiles():

            img = Image.open(
                BRAIN_PATH
            ).convert("RGB")

            w, h = img.size

            tiles = []

            for row in range(grid):

                for col in range(grid):

                    left = int(col * w / grid)
                    top = int(row * h / grid)
                    right = int((col + 1) * w / grid)
                    bottom = int((row + 1) * h / grid)

                    tile = img.crop(
                        (
                            left,
                            top,
                            right,
                            bottom,
                        )
                    )

                    buf = BytesIO()

                    tile.save(
                        buf,
                        format="PNG",
                    )

                    tiles.append(
                        buf.getvalue()
                    )

            return tiles

        def start_puzzle():

            tiles = make_tiles()

            order = list(
                range(len(tiles))
            )

            for _ in range(10 + grid * 5):

                a = random.randrange(
                    len(order)
                )

                b = random.randrange(
                    len(order)
                )

                if a != b:
                    order[a], order[b] = (
                        order[b],
                        order[a],
                    )

            st.session_state.puzzle_solution = list(
                range(len(tiles))
            )

            st.session_state.puzzle_board = {
                "board": order
            }

            st.session_state.puzzle_grid = grid
            st.session_state.puzzle_started = time.time()
            st.session_state.puzzle_moves = 0
            st.session_state.puzzle_completed = False

        if (
            st.session_state.puzzle_board is None
            or st.session_state.puzzle_grid != grid
        ):

            start_puzzle()

        tiles = make_tiles()

        board = st.session_state.puzzle_board

        elapsed = 0

        if st.session_state.puzzle_started:

            elapsed = int(
                time.time()
                - st.session_state.puzzle_started
            )

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.metric(
                "Round",
                st.session_state.puzzle_round,
            )

        with m2:
            st.metric(
                "Moves",
                st.session_state.puzzle_moves,
            )

        with m3:
            st.metric(
                "Time",
                f"{elapsed}s",
            )

        with m4:
            st.metric(
                "Best Score",
                st.session_state.puzzle_best_score,
            )

        st.markdown(
            f"**Mode:** {challenge} • "
            f"**Grid:** {grid}×{grid}"
        )

        container_key = "puzzle_board"

        with st.container(
            key=container_key,
            border=True,
        ):

            for index, tile_index in enumerate(
                board["board"]
            ):

                row = index // grid
                col = index % grid

                if col == 0:
                    cols = st.columns(grid)

                with cols[col]:

                    with st.container(
                        key=f"piece_{tile_index}",
                        border=True,
                    ):

                        st.image(
                            tiles[tile_index],
                            use_container_width=True,
                        )

        event = dnd(
            container_key,
            cross=False,
            key="neurolens_puzzle_dnd",
        )

        if event:

            old_order = list(
                board["board"]
            )

            if apply_move is not None:

                try:

                    apply_move(
                        event,
                        {
                            container_key: board["board"]
                        },
                    )

                    st.session_state.puzzle_moves += 1

                    st.rerun()

                except Exception:

                    st.session_state.puzzle_board[
                        "board"
                    ] = old_order

        current = st.session_state.puzzle_board[
            "board"
        ]

        if (
            current
            == st.session_state.puzzle_solution
            and not st.session_state.puzzle_completed
        ):

            st.session_state.puzzle_completed = True

            final_time = int(
                time.time()
                - st.session_state.puzzle_started
            )

            moves = st.session_state.puzzle_moves

            score = max(
                1000
                - final_time * 5
                - moves * 10,
                100,
            )

            if challenge == "Speed Mode":
                score += max(
                    500 - final_time * 10,
                    0,
                )

            if challenge == "Minimum Moves":
                score += max(
                    500 - moves * 20,
                    0,
                )

            st.session_state.puzzle_best_score = max(
                st.session_state.puzzle_best_score,
                score,
            )

            if (
                st.session_state.puzzle_best_time is None
                or final_time
                < st.session_state.puzzle_best_time
            ):
                st.session_state.puzzle_best_time = final_time

            if (
                st.session_state.puzzle_best_moves is None
                or moves
                < st.session_state.puzzle_best_moves
            ):
                st.session_state.puzzle_best_moves = moves

            st.session_state.progress[
                "puzzles"
            ] += 1

            save_activity(
                "Brain Puzzle",
                score,
                f"{grid}x{grid};{challenge};"
                f"{final_time}s;{moves} moves",
            )

            st.balloons()

            st.success(
                f"🎉 Puzzle complete! "
                f"Score: {score} • "
                f"Time: {final_time}s • "
                f"Moves: {moves}"
            )

        c1, c2, c3 = st.columns(3)

        with c1:

            if st.button(
                "🆕 New Puzzle",
                use_container_width=True,
            ):
                start_puzzle()
                st.rerun()

        with c2:

            if st.button(
                "🔄 Reset Puzzle",
                use_container_width=True,
            ):
                start_puzzle()
                st.rerun()

        with c3:

            if st.button(
                "➡ Next Round",
                use_container_width=True,
            ):

                st.session_state.puzzle_round += 1

                next_grid = min(
                    7,
                    3
                    + (
                        st.session_state.puzzle_round
                        // 3
                    ),
                )

                st.session_state.puzzle_grid = next_grid

                start_puzzle()

                st.rerun()

        st.caption(
            "Puzzle tiles are derived from brain.png. "
            "The drag system supports touch interaction in current "
            "streamlit-dnd releases."
        )


# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    st.subheader("🤖 Ask Ayna")

    st.caption(
        "Cognitive neuroscience • AI • behaviour • learning • attention"
    )

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    st.markdown("### 🎙️ Voice")

    try:
        audio = st.audio_input(
            "Record your message",
            key="ask_ayna_audio",
        )
    except Exception:
        audio = None

    if st.button(
        "🧠 SEND VOICE",
        use_container_width=True,
    ) and audio:

        answer, source = ask_ai_audio(
            audio,
            """
            Listen to this user voice message.
            Transcribe the relevant request internally and answer as Ayna.
            Keep the answer educational and concise.
            Do not diagnose.
            """,
        )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": "🎙️ Voice message",
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    st.markdown("### 💬 Text")

    text_input = st.text_area(
        "Message Ayna",
        height=110,
        placeholder="Ask something about the brain, cognition or behaviour...",
    )

    if st.button(
        "SEND",
        type="primary",
        use_container_width=True,
    ):

        if text_input.strip():

            context = "\n".join(
                f"{m['role']}: {m['content']}"
                for m in st.session_state.messages[-6:]
            )

            answer, source = ask_ai(
                text_input,
                context,
            )

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": text_input,
                }
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            st.rerun()

    if st.session_state.messages:

        last = st.session_state.messages[-1][
            "content"
        ]

        st.markdown("### 🔊 Ayna Voice")

        speak(
            last,
            "ask_ayna_last",
        )

        if st.button(
            "🗑️ Clear Chat"
        ):

            st.session_state.messages = []

            st.rerun()


# =========================================================
# PRIVATE ASK AYNA
# =========================================================

elif st.session_state.page == "Private Ask Ayna":

    st.subheader("🔐 Private Ask Ayna")

    st.caption(
        "Session-level private chat with a 4–6 digit PIN."
    )

    if not st.session_state.private_unlocked:

        if st.session_state.private_pin_hash is None:

            st.info(
                "Create your private PIN."
            )

            p1 = st.text_input(
                "Create PIN",
                type="password",
                max_chars=6,
            )

            p2 = st.text_input(
                "Confirm PIN",
                type="password",
                max_chars=6,
            )

            if st.button(
                "Create Private PIN",
                use_container_width=True,
            ):

                if (
                    p1.isdigit()
                    and 4 <= len(p1) <= 6
                    and p1 == p2
                ):

                    st.session_state.private_pin_hash = (
                        pin_hash(p1)
                    )

                    st.session_state.private_unlocked = True

                    st.rerun()

                else:

                    st.error(
                        "PIN must be 4–6 digits and both entries must match."
                    )

        else:

            p = st.text_input(
                "Enter PIN",
                type="password",
                max_chars=6,
            )

            if st.button(
                "🔓 Unlock",
                use_container_width=True,
            ):

                if (
                    pin_hash(p)
                    == st.session_state.private_pin_hash
                ):

                    st.session_state.private_unlocked = True

                    st.rerun()

                else:

                    st.error(
                        "Incorrect PIN."
                    )

    else:

        st.success(
            "🔓 Private session unlocked."
        )

        for message in st.session_state.private_messages:

            with st.chat_message(
                message["role"]
            ):

                st.write(
                    message["content"]
                )

        try:
            audio = st.audio_input(
                "Private voice",
                key="private_voice",
            )
        except Exception:
            audio = None

        if st.button(
            "SEND PRIVATE VOICE",
            use_container_width=True,
        ) and audio:

            answer, _ = ask_ai_audio(
                audio,
                "Answer this private message as Ayna. "
                "Be educational, concise and non-diagnostic.",
            )

            st.session_state.private_messages.extend(
                [
                    {
                        "role": "user",
                        "content": "🎙️ Voice message",
                    },
                    {
                        "role": "assistant",
                        "content": answer,
                    },
                ]
            )

            st.rerun()

        private_text = st.text_area(
            "Private message",
            height=100,
        )

        if st.button(
            "SEND PRIVATE",
            type="primary",
            use_container_width=True,
        ):

            if private_text.strip():

                context = "\n".join(
                    f"{m['role']}: {m['content']}"
                    for m in st.session_state.private_messages[-6:]
                )

                answer, _ = ask_ai(
                    private_text,
                    context,
                )

                st.session_state.private_messages.extend(
                    [
                        {
                            "role": "user",
                            "content": private_text,
                        },
                        {
                            "role": "assistant",
                            "content": answer,
                        },
                    ]
                )

                st.rerun()

        if st.session_state.private_messages:

            speak(
                st.session_state.private_messages[-1][
                    "content"
                ],
                "private_voice_output",
            )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "🔒 Lock",
                use_container_width=True,
            ):

                st.session_state.private_unlocked = False

                st.rerun()

        with c2:

            if st.button(
                "🗑️ Delete Private Session",
                use_container_width=True,
            ):

                st.session_state.private_messages = []
                st.session_state.private_pin_hash = None
                st.session_state.private_unlocked = False

                st.rerun()


# =========================================================
# VOICE MOOD
# =========================================================

elif st.session_state.page == "Voice Mood":

    st.subheader("🎙️ Voice Mood & Communication")

    st.warning(
        "Voice analysis is an AI-assisted interpretation of the "
        "recording. It cannot reliably determine someone's hidden "
        "emotional state or diagnose a condition."
    )

    try:
        voice = st.audio_input(
            "Record your voice",
            key="voice_mood_input",
        )
    except Exception:
        voice = None

    if voice:

        st.audio(
            voice,
            format=voice.type or "audio/wav",
        )

        if st.button(
            "🧠 Analyse Voice",
            type="primary",
            use_container_width=True,
        ):

            prompt = """
Analyse this voice recording for observable communication/acoustic
features such as apparent speaking pace, pauses, energy and expressed
affective tone.

Return:
1. One emoji.
2. A cautious mood/communication interpretation.
3. Confidence: low/medium/high.
4. One limitation.

Do not diagnose.
Do not infer personality, criminality, hidden trauma or mental illness.
"""

            answer, source = ask_ai_audio(
                voice,
                prompt,
            )

            st.markdown("### 🤖 Ayna Voice Interpretation")

            st.write(answer)

            st.caption(source)

            speak(
                answer,
                "voice_mood_output",
            )


# =========================================================
# AI MOOD & BEHAVIOUR
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.subheader("🧠 AI Mood & Behaviour Lab")

    st.caption(
        "Self-report + optional voice/text interpretation."
    )

    c1, c2 = st.columns(2)

    with c1:

        stress = st.slider(
            "Stress",
            0,
            10,
            5,
        )

        attention = st.slider(
            "Attention",
            0,
            10,
            5,
        )

        energy = st.slider(
            "Energy",
            0,
            10,
            5,
        )

        mood = st.slider(
            "Mood",
            0,
            10,
            5,
        )

    with c2:

        sleep = st.slider(
            "Sleep quality",
            0,
            10,
            5,
        )

        motivation = st.slider(
            "Motivation",
            0,
            10,
            5,
        )

        emojis = st.multiselect(
            "Optional emojis",
            [
                "😊",
                "😌",
                "😐",
                "😟",
                "😔",
                "😤",
                "😴",
                "😂",
                "❤️",
                "🔥",
                "🤔",
                "🙏",
            ],
        )

    text = st.text_area(
        "Optional description",
        height=110,
    )

    try:
        voice = st.audio_input(
            "Optional voice",
            key="mood_voice",
        )
    except Exception:
        voice = None

    if st.button(
        "🧠 SEND TO AYNA",
        type="primary",
        use_container_width=True,
    ):

        voice_observation = ""

        if voice:

            voice_observation, _ = ask_ai_audio(
                voice,
                """
                Describe only observable communication characteristics
                and expressed affect in this voice. Do not diagnose.
                Do not infer sensitive personal traits.
                """,
            )

        prompt = f"""
Interpret this self-report educationally.

Stress: {stress}/10
Attention: {attention}/10
Energy: {energy}/10
Mood: {mood}/10
Sleep: {sleep}/10
Motivation: {motivation}/10
Emojis: {" ".join(emojis)}

Text:
{text}

Voice observation:
{voice_observation}

Return:
- one suitable emoji
- concise interpretation
- possible cognitive/behavioural context
- uncertainty/limitation

Do not diagnose.
"""

        answer, source = ask_ai(
            prompt,
            max_tokens=450,
        )

        st.markdown(
            "### 🤖 Ayna Interpretation"
        )

        st.write(answer)

        st.caption(source)

        speak(
            answer,
            "mood_output",
        )

        st.info(
            "Self-report scores and AI interpretation are not "
            "brain measurements or clinical assessments."
        )


# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    st.subheader("📚 Cognitive Neuroscience Research Book")

    st.caption(
        "Search literature through Europe PMC."
    )

    topic = st.text_input(
        "Research topic",
        placeholder="working memory, dopamine, attention, neuroplasticity...",
    )

    years = st.selectbox(
        "Date",
        [
            "All years",
            "Last 5 years",
            "Last 10 years",
        ],
    )

    limit = st.selectbox(
        "Number of papers",
        [5, 10],
    )

    if st.button(
        "🔎 Search Europe PMC",
        type="primary",
        use_container_width=True,
    ):

        if not topic.strip():

            st.warning(
                "Enter a research topic."
            )

        else:

            query = topic.strip()

            current_year = datetime.utcnow().year

            if years == "Last 5 years":

                query += (
                    f" AND FIRST_PDATE:["
                    f"{current_year-5}-01-01 TO "
                    f"{current_year}-12-31]"
                )

            elif years == "Last 10 years":

                query += (
                    f" AND FIRST_PDATE:["
                    f"{current_year-10}-01-01 TO "
                    f"{current_year}-12-31]"
                )

            url = (
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
                "?format=json"
                f"&pageSize={limit}"
                f"&query={urllib.parse.quote_plus(query)}"
            )

            try:

                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent":
                        "NEUROLENS Research Book"
                    },
                )

                with st.spinner(
                    "Searching literature..."
                ):

                    with urllib.request.urlopen(
                        request,
                        timeout=20,
                    ) as response:

                        data = json.loads(
                            response.read().decode()
                        )

                results = (
                    data.get(
                        "resultList",
                        {},
                    ).get(
                        "result",
                        [],
                    )
                )

                st.session_state.research_results = results

                st.session_state.progress[
                    "research"
                ] += len(results)

                st.success(
                    f"{len(results)} paper(s) found."
                )

            except Exception as e:

                st.error(
                    "Research search failed."
                )

                st.caption(
                    str(e)
                )

    for i, paper in enumerate(
        st.session_state.research_results
    ):

        title = paper.get(
            "title",
            "Untitled",
        )

        with st.expander(
            f"📄 {i+1}. {title}"
        ):

            st.write(
                "**Authors:**",
                paper.get(
                    "authorString",
                    "Not listed",
                ),
            )

            st.write(
                "**Journal:**",
                paper.get(
                    "journalTitle",
                    "",
                ),
            )

            st.write(
                "**Year:**",
                paper.get(
                    "pubYear",
                    "",
                ),
            )

            abstract = paper.get(
                "abstractText",
                "",
            )

            if abstract:

                st.markdown(
                    "### Abstract"
                )

                st.write(abstract)

            pmid = paper.get(
                "pmid"
            )

            if pmid:

                st.link_button(
                    "🔗 PubMed",
                    f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                )

            pmcid = paper.get(
                "pmcid"
            )

            if pmcid:

                st.link_button(
                    "📖 Europe PMC",
                    f"https://europepmc.org/articles/{pmcid}",
                )

            if st.button(
                "🤖 Explain with Ayna",
                key=f"explain_{i}",
            ):

                prompt = f"""
Explain this research record.

Title: {title}
Authors: {paper.get('authorString','')}
Journal: {paper.get('journalTitle','')}
Year: {paper.get('pubYear','')}
Abstract: {abstract}

Explain:
- research question
- methods only if stated
- main findings only if supported
- limitations
- relevance to cognitive neuroscience

Do not invent missing information.
"""

                answer, source = ask_ai(
                    prompt,
                    max_tokens=650,
                )

                st.markdown(
                    "### 🧠 Ayna Explanation"
                )

                st.write(answer)

                st.caption(source)

                speak(
                    answer,
                    f"paper_voice_{i}",
                )

            note = st.text_area(
                "Research note",
                key=f"note_{i}",
            )

            if st.button(
                "💾 Save Note",
                key=f"save_note_{i}",
            ):

                if note.strip():

                    save_note(
                        title,
                        note,
                    )

                    st.success(
                        "Research note saved."
                    )


# =========================================================
# BEHAVIOUR DECODING
# =========================================================

elif st.session_state.page == "Behaviour Decoding":

    st.subheader("🧠 Behaviour Decoding — 1-to-1 Session")

    st.caption(
        "Educational cognitive/behaviour discussion. "
        "Not diagnosis or forensic profiling."
    )

    name = st.text_input(
        "Name"
    )

    contact = st.text_input(
        "Contact"
    )

    topic = st.text_area(
        "Discussion topic",
        height=100,
    )

    duration = st.selectbox(
        "Session length",
        [
            "20 minutes — PKR 1,000",
            "30 minutes — PKR 1,500",
            "45 minutes — PKR 2,000",
        ],
    )

    amount = {
        "20 minutes — PKR 1,000": 1000,
        "30 minutes — PKR 1,500": 1500,
        "45 minutes — PKR 2,000": 2000,
    }[duration]

    st.markdown(
        f"### 💳 Amount: PKR {amount:,}"
    )

    payment_ref = st.text_input(
        "Payment reference"
    )

    st.info(
        "Automatic Easypaisa verification requires an official "
        "merchant/API integration. Until that exists, payment "
        "verification remains manual."
    )

    if st.button(
        "📩 Submit Session Request",
        type="primary",
        use_container_width=True,
    ):

        if not name or not contact or not topic:

            st.error(
                "Complete the required fields."
            )

        else:

            conn = db()

            conn.execute(
                """
                INSERT INTO consultations
                (name,contact,topic,duration,amount,payment_ref,status,created_at)
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    name[:200],
                    contact[:200],
                    topic[:2000],
                    duration,
                    amount,
                    payment_ref[:300],
                    "Pending Verification",
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

            conn.commit()
            conn.close()

            st.success(
                "Request submitted. Payment status is Pending Verification."
            )

    st.divider()

    st.markdown(
        "### 🎙️ Voice Behaviour Interpretation"
    )

    try:
        voice = st.audio_input(
            "Send a voice sample",
            key="behaviour_voice",
        )
    except Exception:
        voice = None

    if voice:

        if st.button(
            "🧠 Analyse Communication",
            use_container_width=True,
        ):

            answer, source = ask_ai_audio(
                voice,
                """
                Analyse observable communication characteristics
                in this recording.

                Return:
                - emoji
                - apparent expressed affect
                - communication style
                - uncertainty

                Do not diagnose.
                Do not infer hidden personality, criminality,
                mental illness or sensitive traits.
                """,
            )

            st.write(answer)

            st.caption(source)

            speak(
                answer,
                "behaviour_voice_output",
            )


# =========================================================
# BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    st.subheader("🧠 Brain Exercises")

    exercise = st.selectbox(
        "Exercise",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
            "Quick Reaction",
        ],
    )

    if exercise == "Working Memory":

        st.info(
            "Memorize: 3 8 1 6 4 9"
        )

        answer = st.text_input(
            "Recall sequence"
        )

        if st.button("Check Memory"):

            correct = (
                answer.replace(" ", "")
                == "381649"
            )

            if correct:
                st.success("Correct!")
            else:
                st.warning("Not quite.")

            st.session_state.progress[
                "games"
            ] += 1

    elif exercise == "Attention":

        st.write(
            "Find every X:"
        )

        st.markdown(
            "A X K P X R M X Q T X"
        )

        answer = st.number_input(
            "How many X?",
            0,
            20,
            0,
        )

        if st.button("Check Attention"):

            if answer == 4:
                st.success("Correct!")
            else:
                st.warning("Expected 4.")

            st.session_state.progress[
                "games"
            ] += 1

    elif exercise == "Pattern Recognition":

        st.markdown(
            "### 2 → 4 → 8 → 16 → ?"
        )

        answer = st.number_input(
            "Answer",
            0,
            100,
            0,
        )

        if st.button("Check Pattern"):

            if answer == 32:
                st.success("Correct!")
            else:
                st.warning("Try again.")

            st.session_state.progress[
                "games"
            ] += 1

    elif exercise == "Decision Challenge":

        choice = st.radio(
            "Choose:",
            [
                "Rs. 1,000 now",
                "Rs. 1,500 after 30 days",
            ],
        )

        if st.button("Record Decision"):

            st.success(
                "Decision recorded."
            )

            st.info(
                "This illustrates delayed-reward decision-making."
            )

            st.session_state.progress[
                "games"
            ] += 1

    else:

        st.write(
            "When the screen says GO, press the button."
        )

        if "reaction_start" not in st.session_state:

            st.session_state.reaction_start = None

        if st.button(
            "START",
            use_container_width=True,
        ):

            st.session_state.reaction_start = (
                time.perf_counter()
            )

            st.success(
                "GO — press STOP now!"
            )

        if st.button(
            "STOP",
            use_container_width=True,
        ):

            if st.session_state.reaction_start:

                rt = (
                    time.perf_counter()
                    - st.session_state.reaction_start
                )

                st.metric(
                    "Reaction time",
                    f"{rt:.3f} sec",
                )

                st.session_state.progress[
                    "games"
                ] += 1

                st.session_state.reaction_start = None


# =========================================================
# DAILY EXPERIMENT
# =========================================================

elif st.session_state.page == "Daily Experiment":

    st.subheader("🧪 Daily Cognitive Experiment")

    day = datetime.now().timetuple().tm_yday

    experiments = [
        (
            "Attention",
            "How many X are present?  X A M X P Q X R",
            "3",
        ),
        (
            "Memory",
            "Remember: 8 4 2 9 1",
            "84291",
        ),
        (
            "Pattern",
            "Continue: 3, 6, 12, 24, ?",
            "48",
        ),
    ]

    domain, question, expected = experiments[
        day % len(experiments)
    ]

    st.markdown(
        f"### {domain}"
    )

    st.write(question)

    answer = st.text_input(
        "Your answer"
    )

    if st.button(
        "Submit Daily Experiment",
        type="primary",
    ):

        correct = (
            answer.replace(" ", "").lower()
            == expected.lower()
        )

        if correct:
            st.success("🎉 Correct!")
        else:
            st.warning(
                f"Expected: {expected}"
            )

        st.session_state.daily_done = True

        st.session_state.progress[
            "experiments"
        ] += 1

        save_activity(
            "Daily Experiment",
            100 if correct else 0,
            domain,
        )

    st.info(
        "Daily experiments are educational practice tasks, "
        "not clinical or neurological tests."
    )


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.subheader("📊 My Progress")

    p = st.session_state.progress

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Experiments",
        p["experiments"],
    )

    c2.metric(
        "Games",
        p["games"],
    )

    c3.metric(
        "Puzzles",
        p["puzzles"],
    )

    c4.metric(
        "Research",
        p["research"],
    )

    c5.metric(
        "AI Requests",
        p["ai"],
    )

    if go:

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=[
                    "Experiments",
                    "Games",
                    "Puzzles",
                    "Research",
                    "AI",
                ],
                y=[
                    p["experiments"],
                    p["games"],
                    p["puzzles"],
                    p["research"],
                    p["ai"],
                ],
            )
        )

        fig.update_layout(
            title="NEUROLENS Activity",
            height=350,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.markdown("### 🏆 Achievements")

    achievements = []

    if p["games"] >= 1:
        achievements.append(
            "🎮 First Cognitive Game"
        )

    if p["experiments"] >= 1:
        achievements.append(
            "🧪 First Experiment"
        )

    if p["puzzles"] >= 1:
        achievements.append(
            "🧩 First Brain Puzzle"
        )

    if p["research"] >= 1:
        achievements.append(
            "📚 Research Explorer"
        )

    if p["ai"] >= 1:
        achievements.append(
            "🤖 Asked Ayna"
        )

    if achievements:

        for item in achievements:
            st.markdown(
                f'<span class="badge">{item}</span>',
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "Complete an activity to unlock achievements."
        )

    st.markdown(
        "### 🧠 Puzzle Bests"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Best Score",
        st.session_state.puzzle_best_score,
    )

    c2.metric(
        "Best Time",
        (
            f"{st.session_state.puzzle_best_time}s"
            if st.session_state.puzzle_best_time
            else "—"
        ),
    )

    c3.metric(
        "Fewest Moves",
        (
            st.session_state.puzzle_best_moves
            if st.session_state.puzzle_best_moves
            else "—"
        ),
    )


# =========================================================
# SECURITY
# =========================================================

elif st.session_state.page == "Security & Privacy":

    st.subheader("🔐 Security & Privacy Center")

    st.markdown(
        """
        ### API Key Protection

        - Gemini API key should stay in Streamlit Secrets.
        - Never put the real API key directly in `app.py`.
        - Do not expose API keys in screenshots or GitHub.

        ### AI Protection

        - Session AI request limit is enabled.
        - Inputs are length-limited.
        - AI prompts contain safety constraints.

        ### Private Ask Ayna

        - PIN is hashed with PBKDF2-HMAC-SHA256.
        - Private chat is session-level.
        - Do not use it for highly sensitive clinical or financial data.

        ### Voice

        Voice interpretation is an AI-assisted interpretation and is
        not a clinical emotion detector.

        ### EEG

        Synthetic EEG is simulated. Real EEG requires compatible
        hardware and a properly configured BrainFlow connection.

        ### Eye Tracking

        Webcam gaze estimation is not equivalent to research-grade
        eye tracking hardware.

        ### Payment

        Automatic Easypaisa verification requires an official merchant/API
        integration. A payment reference alone does not prove payment.
        """
    )


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "Settings":

    st.subheader("⚙️ Settings")

    st.write(
        "**AI model:**",
        MODEL,
    )

    st.write(
        "**Gemini connection:**",
        "Connected"
        if api_key()
        else "Not configured",
    )

    st.write(
        "**Brain image:**",
        "Found"
        if BRAIN_PATH
        else "Missing",
    )

    st.write(
        "**Ayna reboot video:**",
        "Found"
        if REBOOT_VIDEO
        else "Optional / missing",
    )

    st.write(
        "**Lab video:**",
        "Found"
        if LAB_VIDEO
        else "Optional / missing",
    )

    st.write(
        "**Brain journey video:**",
        "Found"
        if BRAIN_VIDEO
        else "Optional / missing",
    )

    st.divider()

    if st.button(
        "🗑️ Reset Session Progress",
        use_container_width=True,
    ):

        keys = [
            "progress",
            "messages",
            "private_messages",
            "research_results",
            "experiment_history",
        ]

        for key in keys:

            if key == "progress":
                st.session_state[key] = default_progress()

            else:
                st.session_state[key] = []

        st.success(
            "Session progress reset."
        )

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • "
    "Created by Ayna Jaffri"
)
