import os
import io
import csv
import time
import random
import sqlite3
import hashlib
import hmac
import secrets
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

try:
    from google import genai
except Exception:
    genai = None

try:
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
    from brainflow.data_filter import DataFilter
    BRAINFLOW_OK = True
except Exception:
    BRAINFLOW_OK = False

try:
    from PIL import Image
except Exception:
    Image = None


# ============================================================
# NEUROLENS CONFIG
# ============================================================

APP_NAME = "NEUROLENS"
APP_TAGLINE = "Explore cognition, behavior & the brain"
DB_FILE = "neurolens.db"

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATABASE
# ============================================================

def db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            category TEXT,
            name TEXT,
            score REAL,
            details TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            title TEXT,
            note TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            module TEXT,
            input_type TEXT,
            topic TEXT,
            response TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            name TEXT,
            contact TEXT,
            topic TEXT,
            duration INTEGER,
            fee INTEGER,
            payment_method TEXT,
            payment_reference TEXT,
            payment_status TEXT,
            discussion_status TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            message TEXT,
            response TEXT
        )
    """)

    con.commit()
    con.close()


init_db()


# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_activity(category, name, score, details=""):
    con = db()
    con.execute(
        """
        INSERT INTO activity
        (timestamp, category, name, score, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), category, name, score, details)
    )
    con.commit()
    con.close()


def save_ai_request(module, input_type, topic, response):
    con = db()
    con.execute(
        """
        INSERT INTO ai_requests
        (timestamp, module, input_type, topic, response)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), module, input_type, topic[:500], response[:5000])
    )
    con.commit()
    con.close()


def get_activity():
    con = db()
    df = pd.read_sql_query(
        "SELECT * FROM activity ORDER BY id DESC",
        con
    )
    con.close()
    return df


def get_notes():
    con = db()
    df = pd.read_sql_query(
        "SELECT * FROM research_notes ORDER BY id DESC",
        con
    )
    con.close()
    return df


def get_ai_requests():
    con = db()
    df = pd.read_sql_query(
        "SELECT * FROM ai_requests ORDER BY id DESC",
        con
    )
    con.close()
    return df


def clean_text(value, limit=2000):
    if value is None:
        return ""
    value = str(value)
    return value.strip()[:limit]


# ============================================================
# GEMINI
# ============================================================

def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return (
            "Gemini API key configured nahi hai. "
            "Streamlit Secrets mein GEMINI_API_KEY add karein."
        )

    if genai is None:
        return (
            "google-genai package available nahi hai. "
            "requirements.txt install karein."
        )

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        text = getattr(response, "text", None)

        if not text:
            return "AI ne koi text response return nahi kiya."

        return text.strip()

    except Exception as e:
        return f"AI connection error: {str(e)}"


# ============================================================
# PRIVATE PIN SECURITY
# ============================================================

def hash_pin(pin):
    salt = secrets.token_bytes(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt,
        150000
    )

    return salt.hex(), hashed.hex()


def verify_pin(pin, salt_hex, hash_hex):
    try:
        salt = bytes.fromhex(salt_hex)

        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode(),
            salt,
            150000
        )

        return hmac.compare_digest(
            calculated.hex(),
            hash_hex
        )

    except Exception:
        return False


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Home",
    "private_unlocked": False,
    "private_salt": None,
    "private_hash": None,
    "puzzle_complete": False,
    "lab_results": [],
    "gaze_history": [],
    "last_ai_response": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.block-container {
    max-width: 1250px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

.neuro-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 2px;
}

.neuro-subtitle {
    font-size: 18px;
    opacity: 0.75;
}

.card {
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 15px;
}

.small-note {
    font-size: 13px;
    opacity: 0.7;
}

button {
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")
    st.caption(APP_TAGLINE)

    pages = [
        "Home",
        "Virtual Lab",
        "Eye Tracking",
        "EEG Lab",
        "Brain Journey",
        "Brain Puzzle",
        "Ask Ayna",
        "Private Ask Ayna",
        "Mood & Behaviour",
        "Research Book",
        "Behaviour Decoding",
        "Brain Exercises",
        "My Progress",
        "Security & Privacy",
        "Settings"
    ]

    selected = st.radio(
        "Navigate",
        pages,
        index=pages.index(st.session_state.page)
    )

    st.session_state.page = selected

    st.divider()

    st.caption(
        "Research/educational prototype. "
        "Not a clinical diagnostic system."
    )


# ============================================================
# HOME
# ============================================================

if st.session_state.page == "Home":

    st.markdown(
        '<div class="neuro-title">NEUROLENS</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="neuro-subtitle">'
        'Explore cognition, behavior & the brain'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2 = st.columns([1.2, 1])

    with col1:

        st.markdown("""
        ### Welcome to NEUROLENS

        NEUROLENS is an interactive cognitive-neuroscience
        research/education environment.

        You can explore:

        - Attention
        - Memory
        - Cognitive control
        - Decision-making
        - Reward
        - Reaction time
        - Eye-gaze estimation
        - EEG simulation
        - Brain systems
        - AI-assisted research
        """)

        st.info(
            "Simulation Mode: EEG data is synthetic and "
            "does NOT represent real human brain activity."
        )

    with col2:

        st.markdown("### System status")

        st.success("🧠 Cognitive experiments: Ready")

        if BRAINFLOW_OK:
            st.success("🔬 BrainFlow: Available")
        else:
            st.warning(
                "🔬 BrainFlow: Not installed/available"
            )

        if GEMINI_API_KEY:
            st.success("🤖 Gemini: Configured")
        else:
            st.warning("🤖 Gemini: API key missing")

        st.success("📊 Local database: Ready")
        st.success("📁 Excel/CSV export: Ready")


# ============================================================
# VIRTUAL LAB
# ============================================================

elif st.session_state.page == "Virtual Lab":

    st.title("🔬 Virtual Cognitive Neuroscience Lab")

    st.info(
        "Lab instruments are software interfaces. "
        "EEG output is simulated unless supported hardware "
        "is actually connected."
    )

    character = st.selectbox(
        "Select your lab role",
        [
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent"
        ]
    )

    equipment = st.multiselect(
        "Select equipment",
        [
            "EEG Simulator",
            "Eye Tracker",
            "Reaction-Time System",
            "Cognitive Task Monitor",
            "Physiological Sensor"
        ],
        default=[
            "Cognitive Task Monitor",
            "Reaction-Time System"
        ]
    )

    experiment = st.selectbox(
        "Experiment",
        [
            "Attention",
            "Memory",
            "Stroop-Cognitive Control",
            "Decision & Reward",
            "Pattern Recognition",
            "Reaction Time"
        ]
    )

    trials = st.slider(
        "Number of trials",
        5,
        50,
        10
    )

    st.divider()

    if st.button("▶ Start Experiment", use_container_width=True):

        correct = 0
        reaction_times = []

        progress = st.progress(0)

        for i in range(trials):

            time.sleep(0.05)

            rt = random.randint(350, 950)
            reaction_times.append(rt)

            if random.random() > 0.2:
                correct += 1

            progress.progress(
                int(((i + 1) / trials) * 100)
            )

        accuracy = correct / trials
        mean_rt = np.mean(reaction_times)

        save_activity(
            "Virtual Lab",
            experiment,
            accuracy,
            f"Character={character}; "
            f"Equipment={equipment}; "
            f"Trials={trials}; "
            f"MeanRT={mean_rt:.1f}"
        )

        st.session_state.lab_results.append({
            "Experiment": experiment,
            "Accuracy": accuracy,
            "Mean RT": mean_rt
        })

        st.success("Experiment completed.")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Correct",
            f"{correct}/{trials}"
        )

        c2.metric(
            "Accuracy",
            f"{accuracy * 100:.1f}%"
        )

        c3.metric(
            "Mean RT",
            f"{mean_rt:.0f} ms"
        )

        st.warning(
            "These results are behavioral/simulated "
            "prototype data and are not clinical measurements."
        )


# ============================================================
# EYE TRACKING
# ============================================================

elif st.session_state.page == "Eye Tracking":

    st.title("👁️ Webcam Eye Tracking")

    st.write(
        "Browser camera se approximate gaze coordinates "
        "estimate karne ka prototype."
    )

    st.warning(
        "Camera-based gaze estimation research-grade eye "
        "tracker ka replacement nahi hai."
    )

    components_code = """
    <!DOCTYPE html>
    <html>
    <head>
    <script src="https://webgazer.cs.brown.edu/webgazer.js"></script>
    <style>
    body {
        font-family: Arial;
        text-align: center;
        padding: 20px;
    }
    #status {
        font-size: 18px;
        margin: 20px;
    }
    </style>
    </head>

    <body>

    <h3>NEUROLENS Camera Eye Tracking</h3>

    <div id="status">
    Starting camera...
    </div>

    <script>

    webgazer.setGazeListener(function(data, elapsedTime) {

        if (data == null) return;

        document.getElementById("status").innerHTML =
            "Gaze X: " + Math.round(data.x) +
            " | Gaze Y: " + Math.round(data.y);

    }).begin();

    </script>

    </body>
    </html>
    """

    st.components.v1.html(
        components_code,
        height=450,
        scrolling=False
    )

    st.caption(
        "WebGazer is an open-source webcam-based gaze "
        "estimation library."
    )


# ============================================================
# EEG LAB
# ============================================================

elif st.session_state.page == "EEG Lab":

    st.title("🧠 EEG Laboratory")

    mode = st.radio(
        "EEG mode",
        [
            "Simulation",
            "Hardware-ready"
        ],
        horizontal=True
    )

    if mode == "Simulation":

        st.info(
            "Synthetic EEG stream — this is NOT real EEG."
        )

        seconds = st.slider(
            "Simulation duration",
            2,
            15,
            5
        )

        if st.button(
            "▶ Generate EEG Signal",
            use_container_width=True
        ):

            fs = 250
            t = np.arange(0, seconds, 1 / fs)

            alpha = np.sin(
                2 * np.pi * 10 * t
            )

            theta = 0.5 * np.sin(
                2 * np.pi * 6 * t
            )

            noise = np.random.normal(
                0,
                0.25,
                len(t)
            )

            signal = alpha + theta + noise

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=t,
                    y=signal,
                    mode="lines",
                    name="Simulated EEG"
                )
            )

            fig.update_layout(
                title="Conceptual Simulated EEG",
                xaxis_title="Time (s)",
                yaxis_title="Amplitude"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.success(
                "Synthetic signal generated successfully."
            )

    else:

        st.info(
            "Hardware-ready architecture: connect a "
            "BrainFlow-supported board and configure its "
            "board ID/settings before acquisition."
        )

        if BRAINFLOW_OK:

            st.success(
                "BrainFlow Python package detected."
            )

            st.code("""
# Future hardware acquisition concept

params = BrainFlowInputParams()

board = BoardShim(
    YOUR_BOARD_ID,
    params
)

board.prepare_session()
board.start_stream()

data = board.get_board_data()

board.stop_stream()
board.release_session()
            """)

        else:

            st.warning(
                "BrainFlow package is not currently available."
            )


# ============================================================
# BRAIN JOURNEY
# ============================================================

elif st.session_state.page == "Brain Journey":

    st.title("🧠 Visual Brain Journey")

    regions = [
        (
            "Prefrontal Cortex",
            "Cognitive control, planning, working memory "
            "and decision-related functions."
        ),
        (
            "Hippocampus",
            "Important for memory formation and spatial "
            "memory."
        ),
        (
            "Striatum",
            "Important component of cortico-striatal "
            "circuits and reward/action selection."
        ),
        (
            "Anterior Cingulate Cortex",
            "Associated with monitoring, conflict and "
            "cognitive control."
        ),
        (
            "Attention Networks",
            "Distributed systems supporting selection "
            "and control of attention."
        )
    ]

    if "brain_index" not in st.session_state:
        st.session_state.brain_index = 0

    idx = st.session_state.brain_index

    region, description = regions[idx]

    st.markdown(
        f"## {region}"
    )

    st.info(description)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("⬅ Previous"):
            st.session_state.brain_index = max(
                0,
                idx - 1
            )
            st.rerun()

    with c2:
        if st.button("🔄 Restart"):
            st.session_state.brain_index = 0
            st.rerun()

    with c3:
        if st.button("Next ➡"):
            st.session_state.brain_index = min(
                len(regions) - 1,
                idx + 1
            )
            st.rerun()

    st.progress(
        (idx + 1) / len(regions)
    )

    st.caption(
        "Brain Journey visualizations are conceptual "
        "educational representations."
    )


# ============================================================
# BRAIN PUZZLE
# ============================================================

elif st.session_state.page == "Brain Puzzle":

    st.title("🧩 Brain Puzzle")

    image_path = "brain.png"

    if os.path.exists(image_path) and Image:

        image = Image.open(image_path)

        st.image(
            image,
            caption="Brain Puzzle Source Image",
            use_container_width=True
        )

    else:

        st.warning(
            "brain.png project folder mein add karein."
        )

    st.write(
        "Prototype 3×3 puzzle. Full drag-and-drop puzzle "
        "ke liye browser-side component use kiya ja sakta hai."
    )

    pieces = list(range(1, 10))

    random.shuffle(pieces)

    cols = st.columns(3)

    for i, piece in enumerate(pieces):

        with cols[i % 3]:

            st.button(
                f"Piece {piece}",
                key=f"piece_{i}"
            )

    if st.button(
        "✓ Record Puzzle Completion",
        use_container_width=True
    ):

        st.session_state.puzzle_complete = True

        save_activity(
            "Puzzle",
            "Brain Puzzle",
            1,
            "Manual completion record"
        )

        st.success(
            "Puzzle completion recorded."
        )


# ============================================================
# ASK AYNA
# ============================================================

elif st.session_state.page == "Ask Ayna":

    st.title("🤖 Ask Ayna")

    st.caption(
        "AI cognitive neuroscience educational assistant"
    )

    topic = st.text_area(
        "Ask Ayna",
        placeholder=(
            "Example: Why does stress affect attention?"
        )
    )

    input_type = st.radio(
        "Input type",
        ["Text", "Voice"],
        horizontal=True
    )

    if input_type == "Voice":

        st.info(
            "Browser speech recognition availability "
            "device/browser par depend karti hai."
        )

        st.components.v1.html("""
        <button onclick="startVoice()">
        🎙 Start Voice
        </button>

        <p id="voice"></p>

        <script>
        function startVoice() {

            const SpeechRecognition =
                window.SpeechRecognition ||
                window.webkitSpeechRecognition;

            if (!SpeechRecognition) {
                document.getElementById("voice").innerHTML =
                "Speech recognition supported nahi hai.";
                return;
            }

            const recognition =
                new SpeechRecognition();

            recognition.lang = "en-US";

            recognition.onresult = function(event) {

                document.getElementById("voice").innerHTML =
                event.results[0][0].transcript;

            };

            recognition.start();
        }
        </script>
        """, height=180)

    if st.button(
        "SEND",
        use_container_width=True
    ):

        if not topic.strip():

            st.warning(
                "Pehle apna question likhein."
            )

        else:

            prompt = f"""
You are Ayna, an educational cognitive neuroscience
assistant inside NEUROLENS.

Answer scientifically and clearly.

Topics can include:
memory, attention, learning, emotion,
decision-making, reward, perception,
cognitive control, brain systems,
neuroplasticity and behavioral neuroscience.

Rules:
- Do not diagnose.
- Do not claim simple cognitive games measure brain activity.
- Explain uncertainty when evidence is limited.
- Distinguish educational information from clinical advice.

User question:
{clean_text(topic)}
"""

            answer = ask_gemini(prompt)

            st.session_state.last_ai_response = answer

            save_ai_request(
                "Ask Ayna",
                input_type,
                topic,
                answer
            )

            st.markdown("### Ayna")

            st.write(answer)

            st.components.v1.html(
                f"""
                <button onclick="speakText()">
                🔊 Speak Ayna
                </button>

                <script>
                function speakText() {{

                    const text =
                    {answer.replace(chr(39), '').__repr__()};

                    const speech =
                    new SpeechSynthesisUtterance(text);

                    speech.lang = "en-US";

                    window.speechSynthesis.speak(speech);
                }}
                </script>
                """,
                height=80
            )


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    st.title("🔐 Private Ask Ayna")

    if st.session_state.private_salt is None:

        st.subheader("Create private PIN")

        pin = st.text_input(
            "Create 4–6 digit PIN",
            type="password",
            max_chars=6
        )

        if st.button("Create PIN"):

            if (
                pin.isdigit()
                and 4 <= len(pin) <= 6
            ):

                salt, hashed = hash_pin(pin)

                st.session_state.private_salt = salt
                st.session_state.private_hash = hashed

                st.success(
                    "PIN created for this session."
                )

            else:

                st.error(
                    "PIN exactly 4–6 digits ka hona chahiye."
                )

    elif not st.session_state.private_unlocked:

        pin = st.text_input(
            "Enter PIN",
            type="password",
            max_chars=6
        )

        if st.button("Unlock"):

            if verify_pin(
                pin,
                st.session_state.private_salt,
                st.session_state.private_hash
            ):

                st.session_state.private_unlocked = True

                st.success("Private area unlocked.")

            else:

                st.error("Incorrect PIN.")

    else:

        st.success("🔓 Private area unlocked.")

        private_message = st.text_area(
            "Private question"
        )

        if st.button("Send Private Message"):

            if private_message.strip():

                prompt = f"""
You are Ayna inside a private educational
cognitive-neuroscience conversation.

Answer carefully and do not diagnose.

Message:
{clean_text(private_message)}
"""

                answer = ask_gemini(prompt)

                con = db()

                con.execute(
                    """
                    INSERT INTO private_messages
                    (timestamp, message, response)
                    VALUES (?, ?, ?)
                    """,
                    (
                        now(),
                        private_message,
                        answer
                    )
                )

                con.commit()
                con.close()

                st.write(answer)

        if st.button("🔒 Lock"):

            st.session_state.private_unlocked = False

            st.rerun()


# ============================================================
# MOOD & BEHAVIOUR
# ============================================================

elif st.session_state.page == "Mood & Behaviour":

    st.title("🧠 AI Mood & Behaviour")

    st.warning(
        "Self-report interpretation only. "
        "This is not a mental-health diagnosis."
    )

    stress = st.slider(
        "Stress",
        0,
        100,
        50
    )

    attention = st.slider(
        "Attention",
        0,
        100,
        50
    )

    energy = st.slider(
        "Energy",
        0,
        100,
        50
    )

    mood = st.slider(
        "Mood",
        0,
        100,
        50
    )

    sleep = st.slider(
        "Sleep quality",
        0,
        100,
        50
    )

    motivation = st.slider(
        "Motivation",
        0,
        100,
        50
    )

    if st.button(
        "SEND",
        use_container_width=True
    ):

        prompt = f"""
Interpret these self-reported values educationally.

Stress: {stress}
Attention: {attention}
Energy: {energy}
Mood: {mood}
Sleep quality: {sleep}
Motivation: {motivation}

Do not diagnose any mental or medical condition.
Explain possible cognitive-behavioral patterns
and mention that self-report is subjective.
"""

        answer = ask_gemini(prompt)

        st.markdown("### 🤖 Ayna Interpretation")

        st.write(answer)

        save_ai_request(
            "Mood & Behaviour",
            "Self-report",
            "Mood/behaviour profile",
            answer
        )


# ============================================================
# RESEARCH BOOK
# ============================================================

elif st.session_state.page == "Research Book":

    st.title("📚 Research Book")

    query = st.text_input(
        "Search Europe PMC",
        placeholder="cognitive neuroscience attention"
    )

    if st.button(
        "🔎 Search Papers",
        use_container_width=True
    ):

        if query.strip():

            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

            params = {
                "query": query,
                "format": "json",
                "pageSize": 10
            }

            try:

                response = requests.get(
                    url,
                    params=params,
                    timeout=15
                )

                data = response.json()

                results = data.get(
                    "resultList",
                    {}
                ).get(
                    "result",
                    []
                )

                if not results:

                    st.info(
                        "No papers found."
                    )

                for paper in results:

                    title = paper.get(
                        "title",
                        "Untitled"
                    )

                    authors = paper.get(
                        "authorString",
                        ""
                    )

                    year = paper.get(
                        "pubYear",
                        ""
                    )

                    pmid = paper.get(
                        "pmid",
                        ""
                    )

                    st.markdown(
                        f"### {title}"
                    )

                    st.write(
                        f"**Authors:** {authors}"
                    )

                    st.write(
                        f"**Year:** {year}"
                    )

                    if pmid:

                        st.markdown(
                            f"[Open PMID](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
                        )

                    st.divider()

            except Exception as e:

                st.error(
                    f"Research search error: {e}"
                )

    st.subheader("Research Notes")

    note_title = st.text_input(
        "Paper/title"
    )

    note = st.text_area(
        "Research note"
    )

    if st.button("Save Research Note"):

        if note.strip():

            con = db()

            con.execute(
                """
                INSERT INTO research_notes
                (timestamp, title, note)
                VALUES (?, ?, ?)
                """,
                (
                    now(),
                    note_title,
                    note
                )
            )

            con.commit()
            con.close()

            st.success(
                "Research note saved."
            )


# ============================================================
# BEHAVIOUR DECODING
# ============================================================

elif st.session_state.page == "Behaviour Decoding":

    st.title("🔎 Behaviour Decoding — 1-to-1")

    st.write(
        "Structured discussion request form."
    )

    st.info(
        "Payment verification is manual unless an official "
        "payment API/merchant integration is configured."
    )

    name = st.text_input(
        "Name / Alias"
    )

    contact = st.text_input(
        "Contact"
    )

    topic = st.text_area(
        "Topic"
    )

    duration = st.selectbox(
        "Session duration",
        [20, 30, 45]
    )

    fees = {
        20: 1000,
        30: 1500,
        45: 2000
    }

    st.metric(
        "Fee",
        f"PKR {fees[duration]:,}"
    )

    payment_method = st.selectbox(
        "Payment method",
        [
            "Easypaisa",
            "International",
            "Other"
        ]
    )

    payment_reference = st.text_input(
        "Payment reference"
    )

    if st.button(
        "Submit Request",
        use_container_width=True
    ):

        if not name or not contact or not topic:

            st.error(
                "Required fields complete karein."
            )

        else:

            con = db()

            con.execute(
                """
                INSERT INTO consultations
                (
                    timestamp,
                    name,
                    contact,
                    topic,
                    duration,
                    fee,
                    payment_method,
                    payment_reference,
                    payment_status,
                    discussion_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now(),
                    name,
                    contact,
                    topic,
                    duration,
                    fees[duration],
                    payment_method,
                    payment_reference,
                    "Pending",
                    "Locked"
                )
            )

            con.commit()
            con.close()

            st.success(
                "Request saved. Payment verification pending."
            )


# ============================================================
# BRAIN EXERCISES
# ============================================================

elif st.session_state.page == "Brain Exercises":

    st.title("🧠 Brain Exercises")

    exercise = st.selectbox(
        "Choose exercise",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
            "Quick Reaction"
        ]
    )

    if exercise == "Working Memory":

        sequence = "729418"

        st.write(
            "Remember this sequence:"
        )

        st.code(sequence)

        answer = st.text_input(
            "Enter sequence"
        )

        if st.button("Check Memory"):

            score = (
                100
                if answer.strip() == sequence
                else 0
            )

            st.metric(
                "Score",
                score
            )

            save_activity(
                "Brain Exercise",
                exercise,
                score,
                "Sequence memory"
            )

    elif exercise == "Attention":

        st.write(
            "Find the target X among distractors."
        )

        target_position = random.randint(
            0,
            24
        )

        grid = [
            "X" if i == target_position else "O"
            for i in range(25)
        ]

        for r in range(5):

            cols = st.columns(5)

            for c in range(5):

                idx = r * 5 + c

                with cols[c]:

                    st.write(
                        f"**{grid[idx]}**"
                    )

        selected = st.number_input(
            "Target position (1–25)",
            1,
            25,
            1
        )

        if st.button("Check Attention"):

            score = (
                100
                if selected - 1 == target_position
                else 0
            )

            st.metric(
                "Score",
                score
            )

            save_activity(
                "Brain Exercise",
                exercise,
                score,
                "Visual attention"
            )

    elif exercise == "Pattern Recognition":

        st.write(
            "2 → 4 → 8 → 16 → ?"
        )

        answer = st.number_input(
            "Next number",
            min_value=0,
            step=1
        )

        if st.button("Check Pattern"):

            score = (
                100
                if answer == 32
                else 0
            )

            st.metric(
                "Score",
                score
            )

            save_activity(
                "Brain Exercise",
                exercise,
                score,
                "Number pattern"
            )

    elif exercise == "Decision Challenge":

        st.write(
            "Choose between:"
        )

        choice = st.radio(
            "Reward",
            [
                "Rs 1,000 today",
                "Rs 1,500 after 30 days"
            ]
        )

        if st.button("Record Decision"):

            save_activity(
                "Brain Exercise",
                exercise,
                1,
                choice
            )

            st.success(
                f"Recorded: {choice}"
            )

    else:

        if "reaction_start" not in st.session_state:

            st.session_state.reaction_start = None

        if st.button(
            "START"
        ):

            st.session_state.reaction_start = time.perf_counter()

            st.info(
                "WAIT..."
            )

            time.sleep(
                random.uniform(
                    1,
                    3
                )
            )

            st.session_state.reaction_start = (
                time.perf_counter()
            )

            st.success(
                "NOW! Press the button below."
            )

        if st.button(
            "⚡ REACT"
        ):

            if st.session_state.reaction_start:

                rt = (
                    time.perf_counter()
                    -
                    st.session_state.reaction_start
                )

                ms = rt * 1000

                st.metric(
                    "Reaction Time",
                    f"{ms:.0f} ms"
                )

                save_activity(
                    "Brain Exercise",
                    exercise,
                    ms,
                    "Reaction time"
                )


# ============================================================
# PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    st.title("📈 My Progress")

    df = get_activity()

    if df.empty:

        st.info(
            "Abhi koi activity recorded nahi hai."
        )

    else:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Activities",
            len(df)
        )

        c2.metric(
            "Lab Sessions",
            len(
                df[df["category"] == "Virtual Lab"]
            )
        )

        c3.metric(
            "Exercises",
            len(
                df[df["category"] == "Brain Exercise"]
            )
        )

        c4.metric(
            "Puzzle",
            len(
                df[df["category"] == "Puzzle"]
            )
        )

        st.subheader(
            "Recent activity"
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        if "score" in df.columns:

            numeric = pd.to_numeric(
                df["score"],
                errors="coerce"
            ).dropna()

            if len(numeric):

                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        y=numeric,
                        mode="lines+markers",
                        name="Activity"
                    )
                )

                fig.update_layout(
                    title="Activity Scores",
                    xaxis_title="Activity",
                    yaxis_title="Score"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

    st.subheader(
        "Research Notes"
    )

    notes = get_notes()

    st.dataframe(
        notes,
        use_container_width=True
    )


# ============================================================
# SECURITY
# ============================================================

elif st.session_state.page == "Security & Privacy":

    st.title("🛡️ Security & Privacy Center")

    controls = [
        (
            "API Key Protection",
            "Gemini API key should be stored in "
            "Streamlit Secrets, not app.py."
        ),
        (
            "PIN Security",
            "Private PIN is processed using salted "
            "PBKDF2-HMAC-SHA256."
        ),
        (
            "Input Sanitization",
            "Inputs are length-limited before AI/storage."
        ),
        (
            "AI Rate Limiting",
            "Production deployment should add "
            "per-user request limits."
        ),
        (
            "Payment Security",
            "Automatic verification requires an "
            "official payment API/merchant integration."
        ),
        (
            "Research Data",
            "Human-subject research requires appropriate "
            "consent, governance and ethics procedures."
        ),
        (
            "Synthetic EEG",
            "Synthetic signals must always remain labeled "
            "as simulated."
        )
    ]

    for title, description in controls:

        st.markdown(
            f"### {title}"
        )

        st.write(
            description
        )

        st.divider()


# ============================================================
# SETTINGS
# ============================================================

elif st.session_state.page == "Settings":

    st.title("⚙️ Settings")

    language = st.selectbox(
        "Language",
        [
            "English",
            "Roman English"
        ]
    )

    model = st.text_input(
        "Gemini Model",
        GEMINI_MODEL
    )

    st.write(
        f"Current AI model: `{model}`"
    )

    st.subheader(
        "Payment configuration"
    )

    easypaisa = get_secret(
        "EASYPAISA_NUMBER"
    )

    international = get_secret(
        "INTERNATIONAL_PAYMENT_URL"
    )

    if easypaisa:

        st.success(
            "Easypaisa configuration detected."
        )

    else:

        st.warning(
            "Easypaisa number not configured."
        )

    if international:

        st.success(
            "International payment configuration detected."
        )

    else:

        st.warning(
            "International payment URL not configured."
        )

    st.subheader(
        "Reset"
    )

    if st.button(
        "Reset Session Progress"
    ):

        st.session_state.lab_results = []
        st.session_state.gaze_history = []
        st.session_state.puzzle_complete = False

        st.success(
            "Session progress reset."
        )


# ============================================================
# EXPORT SECTION
# ============================================================

st.sidebar.divider()

st.sidebar.markdown("### 📁 Data Export")

activity_df = get_activity()
notes_df = get_notes()
ai_df = get_ai_requests()

if not activity_df.empty:

    csv_data = activity_df.to_csv(
        index=False
    ).encode("utf-8")

    st.sidebar.download_button(
        "Download Activity CSV",
        csv_data,
        "neurolens_activity.csv",
        "text/csv"
    )

if not notes_df.empty:

    notes_csv = notes_df.to_csv(
        index=False
    ).encode("utf-8")

    st.sidebar.download_button(
        "Download Research CSV",
        notes_csv,
        "neurolens_research_notes.csv",
        "text/csv"
    )

if not ai_df.empty:

    ai_csv = ai_df.to_csv(
        index=False
    ).encode("utf-8")

    st.sidebar.download_button(
        "Download AI CSV",
        ai_csv,
        "neurolens_ai_requests.csv",
        "text/csv"
    )

st.sidebar.caption(
    "NEUROLENS Research Prototype"
)
