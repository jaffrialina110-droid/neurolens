import os
import io
import re
import time
import json
import math
import hashlib
import sqlite3
import threading
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# ============================================================
# OPTIONAL IMPORTS
# ============================================================

try:
    from google import genai
    GEMINI_AVAILABLE = True
except Exception:
    genai = None
    GEMINI_AVAILABLE = False

try:
    from brainflow.board_shim import (
        BoardShim,
        BrainFlowInputParams,
        BoardIds,
    )
    BRAINFLOW_AVAILABLE = True
except Exception:
    BRAINFLOW_AVAILABLE = False

try:
    import cv2
    CV_AVAILABLE = True
except Exception:
    CV_AVAILABLE = False

try:
    import av
    from streamlit_webrtc import webrtc_streamer
    WEBRTC_AVAILABLE = True
except Exception:
    av = None
    webrtc_streamer = None
    WEBRTC_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except Exception:
    mp = None
    MEDIAPIPE_AVAILABLE = False

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
}

.neuro-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 1px;
}

.neuro-sub {
    font-size: 17px;
    opacity: 0.75;
}

.card {
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,.25);
    margin-bottom: 15px;
}

.small {
    font-size: 13px;
    opacity: .75;
}

.status-ok {
    padding: 10px;
    border-radius: 12px;
    background: rgba(0,180,80,.12);
}

.status-warn {
    padding: 10px;
    border-radius: 12px;
    background: rgba(255,180,0,.12);
}

.status-error {
    padding: 10px;
    border-radius: 12px;
    background: rgba(255,0,0,.10);
}

button {
    border-radius: 10px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"
DB_PATH = BASE_DIR / "neurolens.db"

# ============================================================
# DATABASE
# ============================================================

def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            category TEXT,
            item TEXT,
            score REAL,
            details TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            title TEXT,
            note TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            module TEXT,
            prompt TEXT,
            response TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            name TEXT,
            contact TEXT,
            topic TEXT,
            duration TEXT,
            payment_method TEXT,
            payment_reference TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()

# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_text(text, limit=5000):
    if text is None:
        return ""

    text = str(text)
    text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.I | re.S)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()[:limit]


def save_activity(category, item, score=None, details=""):
    conn = db()
    conn.execute(
        """
        INSERT INTO activity
        (created_at, category, item, score, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), category, item, score, clean_text(details)),
    )
    conn.commit()
    conn.close()


def save_note(title, note):
    conn = db()
    conn.execute(
        """
        INSERT INTO research_notes
        (created_at, title, note)
        VALUES (?, ?, ?)
        """,
        (now(), clean_text(title, 200), clean_text(note, 10000)),
    )
    conn.commit()
    conn.close()


def save_ai(module, prompt, response):
    conn = db()
    conn.execute(
        """
        INSERT INTO ai_requests
        (created_at, module, prompt, response)
        VALUES (?, ?, ?, ?)
        """,
        (
            now(),
            clean_text(module, 100),
            clean_text(prompt, 5000),
            clean_text(response, 10000),
        ),
    )
    conn.commit()
    conn.close()


def get_table(query):
    conn = db()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# ============================================================
# GEMINI
# ============================================================

def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


def ask_ai(prompt, module="NEUROLENS"):
    if not GEMINI_AVAILABLE:
        return "Gemini SDK installed nahi hai."

    api_key = get_secret("GEMINI_API_KEY")

    if not api_key or api_key == "YOUR_REAL_GEMINI_API_KEY":
        return "Gemini API key configure nahi hui. `.streamlit/secrets.toml` mein key add karein."

    model = get_secret("GEMINI_MODEL", "gemini-2.5-flash")

    system = """
You are Ayna, an educational cognitive neuroscience AI assistant inside NEUROLENS.

Topics:
- cognitive neuroscience
- attention
- memory
- learning
- decision making
- reward
- perception
- emotion
- cognitive control
- neuroplasticity
- brain systems
- behavioral neuroscience
- AI and cognition

Rules:
1. Do not diagnose medical or psychiatric conditions.
2. Do not claim that simple cognitive games measure brain activity.
3. Do not claim that webcam eye tracking is equivalent to research-grade eye tracking.
4. Never describe simulated EEG as real EEG.
5. Distinguish observation, hypothesis and established evidence.
6. Use scientifically cautious language.
7. Encourage a qualified professional for medical concerns.
"""

    full_prompt = system + "\n\nUSER:\n" + clean_text(prompt, 8000)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
        )

        text = getattr(response, "text", None)

        if not text:
            return "AI ne response return nahi kiya."

        save_ai(module, prompt, text)

        return text

    except Exception as e:
        return f"AI connection error: {e}"


# ============================================================
# EXCEL EXPORT
# ============================================================

def make_excel():
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        get_table("SELECT * FROM activity").to_excel(
            writer, index=False, sheet_name="Activity"
        )

        get_table("SELECT * FROM research_notes").to_excel(
            writer, index=False, sheet_name="Research Notes"
        )

        get_table("SELECT * FROM ai_requests").to_excel(
            writer, index=False, sheet_name="AI Requests"
        )

        get_table("SELECT * FROM consultations").to_excel(
            writer, index=False, sheet_name="Consultations"
        )

    output.seek(0)
    return output


# ============================================================
# BRAIN JOURNEY
# ============================================================

BRAIN_REGIONS = {
    "Prefrontal Cortex": (
        "Executive control, planning, working memory and decision-making."
    ),
    "Hippocampus": (
        "Memory formation, spatial processing and contextual learning."
    ),
    "Striatum": (
        "Action selection, reward learning and habit-related processes."
    ),
    "Anterior Cingulate Cortex": (
        "Conflict monitoring, error processing and cognitive control."
    ),
    "Attention Networks": (
        "Systems supporting selection and maintenance of relevant information."
    ),
}


# ============================================================
# EEG
# ============================================================

def board_candidates():
    result = {
        "Synthetic EEG": BoardIds.SYNTHETIC_BOARD.value
        if BRAINFLOW_AVAILABLE else -1
    }

    if not BRAINFLOW_AVAILABLE:
        return result

    possible = [
        ("OpenBCI Cyton", "CYTON_BOARD"),
        ("OpenBCI Ganglion", "GANGLION_BOARD"),
        ("Muse 2", "MUSE_2_BOARD"),
        ("Muse S", "MUSE_S_BOARD"),
        ("BrainBit", "BRAINBIT_BOARD"),
        ("FreeEEG32", "FREEEEG32_BOARD"),
        ("Mentalab Explore", "MENTALAB_EXPLORER_BOARD"),
        ("Neurosity", "NEUROSITY_MINDROVE_BOARD"),
    ]

    for label, attr in possible:
        if hasattr(BoardIds, attr):
            try:
                result[label] = getattr(BoardIds, attr).value
            except Exception:
                pass

    return result


def build_brainflow_params(
    serial_port="",
    mac_address="",
    ip_address="",
    ip_port=0,
):
    params = BrainFlowInputParams()

    if serial_port:
        params.serial_port = serial_port

    if mac_address:
        params.mac_address = mac_address

    if ip_address:
        params.ip_address = ip_address

    if ip_port:
        params.ip_port = int(ip_port)

    return params


def read_board_once(
    board_id,
    seconds=5,
    serial_port="",
    mac_address="",
    ip_address="",
    ip_port=0,
):
    if not BRAINFLOW_AVAILABLE:
        return None, "BrainFlow installed nahi hai."

    board = None

    try:
        params = build_brainflow_params(
            serial_port,
            mac_address,
            ip_address,
            ip_port,
        )

        board = BoardShim(int(board_id), params)

        board.prepare_session()
        board.start_stream()

        time.sleep(float(seconds))

        data = board.get_board_data()

        try:
            board.stop_stream()
        except Exception:
            pass

        try:
            board.release_session()
        except Exception:
            pass

        if data is None or data.size == 0:
            return None, "Board se data receive nahi hua."

        return data, "Connected successfully."

    except Exception as e:

        if board is not None:
            try:
                board.stop_stream()
            except Exception:
                pass

            try:
                board.release_session()
            except Exception:
                pass

        return None, str(e)


def eeg_band_power(signal, fs):
    signal = np.asarray(signal, dtype=float)

    if len(signal) < 20:
        return {}

    signal = signal - np.mean(signal)

    freqs = np.fft.rfftfreq(len(signal), 1 / fs)
    power = np.abs(np.fft.rfft(signal)) ** 2

    bands = {
        "Delta": (1, 4),
        "Theta": (4, 8),
        "Alpha": (8, 13),
        "Beta": (13, 30),
        "Gamma": (30, 45),
    }

    output = {}

    for name, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs < high)

        if np.any(mask):
            output[name] = float(np.mean(power[mask]))
        else:
            output[name] = 0.0

    return output


# ============================================================
# EYE TRACKING
# ============================================================

class GazeProcessor:
    def __init__(self):
        self.lock = threading.Lock()
        self.gaze_x = None
        self.gaze_y = None
        self.face_detected = False
        self.samples = []
        self.face = None

        if MEDIAPIPE_AVAILABLE:
            try:
                self.face = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
            except Exception:
                self.face = None

    def _estimate(self, frame):
        if not CV_AVAILABLE or self.face is None:
            return None, None, False

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = self.face.process(rgb)

        if not result.multi_face_landmarks:
            return None, None, False

        landmarks = result.multi_face_landmarks[0].landmark

        h, w = frame.shape[:2]

        # MediaPipe iris landmarks
        left_ids = [474, 475, 476, 477]
        right_ids = [469, 470, 471, 472]

        def center(ids):
            xs = [landmarks[i].x for i in ids]
            ys = [landmarks[i].y for i in ids]

            return (
                float(np.mean(xs)),
                float(np.mean(ys)),
            )

        try:
            lx, ly = center(left_ids)
            rx, ry = center(right_ids)

            x = float((lx + rx) / 2)
            y = float((ly + ry) / 2)

            return x, y, True

        except Exception:
            return None, None, False

    def process(self, frame):
        x, y, found = self._estimate(frame)

        with self.lock:
            self.face_detected = found

            if found:
                self.gaze_x = x
                self.gaze_y = y

                self.samples.append(
                    {
                        "time": time.time(),
                        "x": x,
                        "y": y,
                    }
                )

                self.samples = self.samples[-1000:]

        return frame

    def latest(self):
        with self.lock:
            return {
                "x": self.gaze_x,
                "y": self.gaze_y,
                "face": self.face_detected,
            }

    def get_samples(self):
        with self.lock:
            return list(self.samples)


# ============================================================
# BRAIN PUZZLE
# ============================================================

def puzzle_page():
    st.header("🧩 Brain Puzzle")

    st.write(
        "Drag-and-drop style cognitive puzzle. "
        "Touch/mobile support browser ke hisaab se vary kar sakta hai."
    )

    if "puzzle_score" not in st.session_state:
        st.session_state.puzzle_score = 0

    sequence = list(range(1, 10))

    cols = st.columns(3)

    for i, value in enumerate(sequence):
        with cols[i % 3]:
            if st.button(
                f"Piece {value}",
                key=f"puzzle_{value}",
                use_container_width=True,
            ):
                st.session_state.puzzle_score += 1

    st.metric(
        "Puzzle Interaction Count",
        st.session_state.puzzle_score,
    )

    if st.button("Record Puzzle Completion"):
        save_activity(
            "Brain Puzzle",
            "Puzzle completion",
            100,
            "User manually recorded puzzle completion.",
        )
        st.success("Puzzle completion saved.")


# ============================================================
# EYE TRACKING PAGE
# ============================================================

def eye_tracking_page():
    st.header("👁️ AI Eye Tracking")

    st.info(
        "This is webcam-based gaze estimation. "
        "It is NOT equivalent to a research-grade eye tracker."
    )

    if not WEBRTC_AVAILABLE:
        st.error(
            "streamlit-webrtc available nahi hai. "
            "requirements.txt check karein."
        )
        return

    if not MEDIAPIPE_AVAILABLE:
        st.warning(
            "MediaPipe available nahi hai. "
            "Webcam stream chal sakti hai, lekin iris estimation nahi chalegi."
        )

    if "gaze_processor" not in st.session_state:
        st.session_state.gaze_processor = GazeProcessor()

    processor = st.session_state.gaze_processor

    st.subheader("1. Camera")

    def callback(frame):
        img = frame.to_ndarray(format="bgr24")

        processed = processor.process(img)

        return av.VideoFrame.from_ndarray(
            processed,
            format="bgr24",
        )

    webrtc_streamer(
        key="neurolens_eye_tracking",
        video_frame_callback=callback,
        media_stream_constraints={
            "video": True,
            "audio": False,
        },
        async_processing=True,
    )

    st.subheader("2. Current Gaze Estimate")

    state = processor.latest()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Face",
            "Detected" if state["face"] else "Not detected",
        )

    with c2:
        st.metric(
            "Gaze X",
            "-" if state["x"] is None
            else f"{state['x']:.3f}",
        )

    with c3:
        st.metric(
            "Gaze Y",
            "-" if state["y"] is None
            else f"{state['y']:.3f}",
        )

    st.caption(
        "X/Y normalized estimates hain. "
        "Calibration ke baghair inhe exact screen coordinates na samjhein."
    )

    if st.button("Capture Gaze Snapshot"):
        state = processor.latest()

        if state["x"] is None:
            st.warning("Abhi gaze sample available nahi hai.")
        else:
            save_activity(
                "Eye Tracking",
                "Gaze snapshot",
                None,
                json.dumps(state),
            )
            st.success("Gaze sample saved.")

    samples = processor.get_samples()

    if samples:
        df = pd.DataFrame(samples)

        st.subheader("Gaze Path")

        st.line_chart(
            df.set_index("time")[["x", "y"]]
        )

        st.subheader("Recent Samples")

        st.dataframe(
            df.tail(20),
            use_container_width=True,
        )


# ============================================================
# EEG PAGE
# ============================================================

def eeg_page():
    st.header("🧠 Real EEG / BrainFlow Lab")

    st.warning(
        "Real EEG mode requires physical EEG hardware. "
        "Cloud Streamlit cannot magically access a USB EEG connected "
        "to your local laptop/tablet."
    )

    mode = st.radio(
        "Mode",
        [
            "Synthetic EEG",
            "Real EEG Hardware",
        ],
        horizontal=True,
    )

    if mode == "Synthetic EEG":
        st.success(
            "Synthetic mode: BrainFlow generated data. "
            "This is NOT real brain activity."
        )

        seconds = st.slider(
            "Recording duration",
            2,
            15,
            5,
        )

        if st.button("Run Synthetic EEG"):
            data, message = read_board_once(
                BoardIds.SYNTHETIC_BOARD.value
                if BRAINFLOW_AVAILABLE else -1,
                seconds,
            )

            if data is None:
                st.error(message)
                return

            st.success(message)

            if BRAINFLOW_AVAILABLE:
                channels = BoardShim.get_eeg_channels(
                    BoardIds.SYNTHETIC_BOARD.value
                )

                if channels:
                    channel = channels[0]

                    signal = data[channel, :]

                    st.line_chart(
                        pd.DataFrame(
                            {"Synthetic EEG": signal}
                        )
                    )

                    fs = BoardShim.get_sampling_rate(
                        BoardIds.SYNTHETIC_BOARD.value
                    )

                    powers = eeg_band_power(
                        signal,
                        fs,
                    )

                    st.subheader("Frequency Bands")

                    st.bar_chart(
                        pd.DataFrame(
                            {"Power": powers}
                        )
                    )

                    save_activity(
                        "EEG",
                        "Synthetic recording",
                        None,
                        f"Samples={data.shape[1]}",
                    )

        return

    # REAL EEG
    st.subheader("Real Hardware Configuration")

    if not BRAINFLOW_AVAILABLE:
        st.error(
            "BrainFlow package installed nahi hai."
        )
        return

    boards = board_candidates()

    board_name = st.selectbox(
        "EEG Board",
        list(boards.keys()),
    )

    board_id = boards[board_name]

    col1, col2 = st.columns(2)

    with col1:
        serial_port = st.text_input(
            "Serial Port",
            placeholder="COM3 / /dev/ttyUSB0",
        )

        mac_address = st.text_input(
            "MAC Address",
            placeholder="For supported Bluetooth boards",
        )

    with col2:
        ip_address = st.text_input(
            "IP Address",
            placeholder="For network boards",
        )

        ip_port = st.number_input(
            "IP Port",
            min_value=0,
            max_value=65535,
            value=0,
        )

    seconds = st.slider(
        "Recording seconds",
        2,
        20,
        5,
    )

    st.caption(
        "Board-specific parameters vary. "
        "Use the connection settings required by your exact EEG device."
    )

    if st.button("Connect + Record Real EEG"):
        with st.spinner("Connecting to EEG..."):

            data, message = read_board_once(
                board_id=board_id,
                seconds=seconds,
                serial_port=serial_port,
                mac_address=mac_address,
                ip_address=ip_address,
                ip_port=ip_port,
            )

        if data is None:
            st.error(
                "EEG connection failed:\n\n" + message
            )

        else:
            st.success(
                "REAL EEG DATA RECEIVED"
            )

            eeg_channels = BoardShim.get_eeg_channels(
                board_id
            )

            fs = BoardShim.get_sampling_rate(
                board_id
            )

            if not eeg_channels:
                st.warning(
                    "Is board ke liye EEG channels detect nahi hue."
                )
                return

            channel_data = []

            for ch in eeg_channels[:8]:
                channel_data.append(
                    data[ch, :]
                )

            channel_data = np.array(
                channel_data
            )

            chart_df = pd.DataFrame(
                channel_data.T,
                columns=[
                    f"EEG {i+1}"
                    for i in range(channel_data.shape[0])
                ],
            )

            st.subheader("Live/Recorded EEG")

            st.line_chart(
                chart_df
            )

            first_channel = channel_data[0]

            powers = eeg_band_power(
                first_channel,
                fs,
            )

            st.subheader(
                "Frequency-Band Features"
            )

            st.bar_chart(
                pd.DataFrame(
                    {"Power": powers}
                )
            )

            csv = chart_df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "Download EEG CSV",
                csv,
                "neurolens_eeg.csv",
                "text/csv",
            )

            save_activity(
                "EEG",
                "Real EEG recording",
                None,
                (
                    f"Board={board_name}; "
                    f"Channels={len(eeg_channels)}; "
                    f"Samples={data.shape[1]}"
                ),
            )


# ============================================================
# COMBINED LAB
# ============================================================

def cognitive_lab():
    st.header("🧪 Virtual Cognitive Neuroscience Lab")

    character = st.selectbox(
        "Choose your role",
        [
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent",
        ],
    )

    equipment = st.multiselect(
        "Equipment",
        [
            "EEG",
            "Eye Tracker",
            "Reaction-Time System",
            "Cognitive Task Monitor",
            "Physiological Sensor",
        ],
        default=[
            "Cognitive Task Monitor"
        ],
    )

    experiment = st.selectbox(
        "Experiment",
        [
            "Attention",
            "Memory",
            "Decision & Reward",
            "Stroop / Cognitive Control",
            "Pattern Recognition",
        ],
    )

    st.write(
        f"Role: **{character}**"
    )

    st.write(
        f"Experiment: **{experiment}**"
    )

    if equipment:
        st.write(
            "Equipment: " +
            ", ".join(equipment)
        )

    st.divider()

    if experiment == "Attention":

        target = st.session_state.get(
            "attention_target",
            "X",
        )

        st.write(
            "Find the target symbol:"
        )

        symbols = [
            "O", "O", "O",
            "O", target, "O",
            "O", "O", "O",
        ]

        cols = st.columns(3)

        for i, symbol in enumerate(symbols):

            with cols[i % 3]:

                if st.button(
                    symbol,
                    key=f"attention_{i}",
                    use_container_width=True,
                ):

                    if symbol == target:
                        st.success(
                            "Correct!"
                        )

                        save_activity(
                            "Cognitive Lab",
                            "Attention",
                            100,
                            character,
                        )
                    else:
                        st.error(
                            "Try again."
                        )

    elif experiment == "Memory":

        sequence = "729418"

        st.write(
            "Memorize this sequence:"
        )

        st.code(sequence)

        answer = st.text_input(
            "Enter sequence"
        )

        if st.button(
            "Check Memory"
        ):

            score = (
                100
                if answer.strip() == sequence
                else 0
            )

            st.metric(
                "Score",
                score,
            )

            save_activity(
                "Cognitive Lab",
                "Working Memory",
                score,
                sequence,
            )

    elif experiment == "Decision & Reward":

        choice = st.radio(
            "Choose",
            [
                "PKR 1,000 today",
                "PKR 1,500 after 30 days",
            ],
        )

        if st.button(
            "Record Decision"
        ):

            save_activity(
                "Cognitive Lab",
                "Reward Decision",
                None,
                choice,
            )

            st.success(
                "Decision recorded."
            )

    elif experiment == "Stroop / Cognitive Control":

        word = st.selectbox(
            "Word",
            ["RED", "BLUE", "GREEN"],
        )

        color = st.selectbox(
            "Ink Color",
            ["RED", "BLUE", "GREEN"],
        )

        if st.button(
            "Record Stroop Response"
        ):

            correct = (
                word == color
            )

            save_activity(
                "Cognitive Lab",
                "Stroop",
                100 if correct else 0,
                f"{word}/{color}",
            )

            st.write(
                "Recorded."
            )

    else:

        pattern = [
            2,
            4,
            8,
            16,
            32,
        ]

        st.write(
            "Complete the pattern:"
        )

        st.code(
            " → ".join(
                map(str, pattern)
            )
            + " → ?"
        )

        answer = st.number_input(
            "Next value",
            min_value=0,
            value=0,
        )

        if st.button(
            "Check Pattern"
        ):

            score = (
                100
                if answer == 64
                else 0
            )

            st.metric(
                "Score",
                score,
            )

            save_activity(
                "Cognitive Lab",
                "Pattern Recognition",
                score,
                "2→4→8→16→32→64",
            )

    st.info(
        "Any EEG shown in Virtual Lab without physical hardware "
        "must be treated as conceptual/simulated data."
    )


# ============================================================
# ASK AYNA
# ============================================================

def ask_ayna_page():
    st.header("🤖 Ask Ayna")

    st.caption(
        "Cognitive neuroscience educational assistant"
    )

    if "ayna_messages" not in st.session_state:
        st.session_state.ayna_messages = []

    for message in st.session_state.ayna_messages:

        with st.chat_message(
            message["role"]
        ):
            st.write(
                message["content"]
            )

    prompt = st.chat_input(
        "Ask Ayna about cognition, brain or behaviour..."
    )

    if prompt:

        prompt = clean_text(prompt)

        st.session_state.ayna_messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = ask_ai(
            prompt,
            "Ask Ayna",
        )

        st.session_state.ayna_messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        st.rerun()

    if st.session_state.ayna_messages:

        latest = st.session_state.ayna_messages[-1]

        if latest["role"] == "assistant":

            st.markdown(
                "### 🔊 Speak Ayna"
            )

            escaped = json.dumps(
                latest["content"]
            )

            st.components.v1.html(
                f"""
                <button onclick='speakAyna()'
                style="
                padding:12px 18px;
                border-radius:10px;
                border:0;
                cursor:pointer;
                font-weight:bold;
                ">
                🔊 Speak Ayna
                </button>

                <script>
                function speakAyna() {{
                    const text = {escaped};
                    const utterance =
                        new SpeechSynthesisUtterance(text);
                    utterance.rate = 1;
                    speechSynthesis.cancel();
                    speechSynthesis.speak(utterance);
                }}
                </script>
                """,
                height=70,
            )


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

def hash_pin(pin, salt=None):

    if salt is None:
        salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt,
        150000,
    )

    return (
        salt.hex(),
        digest.hex(),
    )


def private_ask_page():

    st.header("🔐 Private Ask Ayna")

    if "private_pin_hash" not in st.session_state:

        st.info(
            "First time: create a 4–6 digit PIN."
        )

        pin = st.text_input(
            "Create PIN",
            type="password",
            max_chars=6,
        )

        confirm = st.text_input(
            "Confirm PIN",
            type="password",
            max_chars=6,
        )

        if st.button(
            "Create Private PIN"
        ):

            if (
                pin.isdigit()
                and 4 <= len(pin) <= 6
                and pin == confirm
            ):

                salt, digest = hash_pin(
                    pin
                )

                st.session_state.private_pin_salt = salt
                st.session_state.private_pin_hash = digest
                st.session_state.private_unlocked = True

                st.success(
                    "Private area unlocked."
                )

            else:
                st.error(
                    "PIN 4–6 digits ka hona chahiye."
                )

        return

    if not st.session_state.get(
        "private_unlocked",
        False,
    ):

        pin = st.text_input(
            "Enter PIN",
            type="password",
            max_chars=6,
        )

        if st.button(
            "Unlock"
        ):

            try:
                salt = bytes.fromhex(
                    st.session_state.private_pin_salt
                )

                _, digest = hash_pin(
                    pin,
                    salt,
                )

                if digest == st.session_state.private_pin_hash:
                    st.session_state.private_unlocked = True
                    st.rerun()

                else:
                    st.error(
                        "Incorrect PIN."
                    )

            except Exception:
                st.error(
                    "Unlock error."
                )

        return

    st.success(
        "Private session unlocked."
    )

    if st.button(
        "Lock Private Area"
    ):
        st.session_state.private_unlocked = False
        st.rerun()

    question = st.text_area(
        "Private question"
    )

    if st.button(
        "Ask Privately"
    ) and question.strip():

        answer = ask_ai(
            question,
            "Private Ask Ayna",
        )

        st.write(answer)


# ============================================================
# MOOD & BEHAVIOUR
# ============================================================

def mood_page():

    st.header(
        "😊 AI Mood & Behaviour"
    )

    stress = st.slider(
        "Stress",
        0,
        100,
        50,
    )

    attention = st.slider(
        "Attention",
        0,
        100,
        50,
    )

    energy = st.slider(
        "Energy",
        0,
        100,
        50,
    )

    mood = st.slider(
        "Mood",
        0,
        100,
        50,
    )

    sleep = st.slider(
        "Sleep Quality",
        0,
        100,
        50,
    )

    motivation = st.slider(
        "Motivation",
        0,
        100,
        50,
    )

    if st.button(
        "Analyze with Ayna"
    ):

        prompt = f"""
Analyze these self-reported values educationally:

Stress: {stress}
Attention: {attention}
Energy: {energy}
Mood: {mood}
Sleep: {sleep}
Motivation: {motivation}

Explain possible cognitive-behavioural relationships.
Do not diagnose anything.
"""

        answer = ask_ai(
            prompt,
            "Mood & Behaviour",
        )

        st.write(answer)


# ============================================================
# RESEARCH BOOK
# ============================================================

def research_book():

    st.header(
        "📚 Research Book"
    )

    query = st.text_input(
        "Search Europe PMC"
    )

    if st.button(
        "Search Papers"
    ) and query:

        import requests

        url = (
            "https://www.ebi.ac.uk/europepmc/webservices/"
            "rest/search"
        )

        try:

            response = requests.get(
                url,
                params={
                    "query": query,
                    "format": "json",
                    "pageSize": 10,
                },
                timeout=20,
            )

            data = response.json()

            results = data.get(
                "resultList",
                {}).get(
                    "result",
                    [],
                )

            for paper in results:

                title = paper.get(
                    "title",
                    "Untitled",
                )

                year = paper.get(
                    "pubYear",
                    "",
                )

                pmid = paper.get(
                    "pmid",
                    "",
                )

                st.markdown(
                    f"### {title}"
                )

                st.write(
                    f"Year: {year} | PMID: {pmid}"
                )

                if pmid:
                    st.link_button(
                        "Open Paper",
                        f"https://europepmc.org/article/MED/{pmid}",
                    )

                if st.button(
                    "AI Summary",
                    key=f"summary_{pmid}",
                ):

                    summary = ask_ai(
                        f"Summarize this research title scientifically:\n{title}",
                        "Research Book",
                    )

                    st.write(summary)

                st.divider()

        except Exception as e:
            st.error(
                f"Research search error: {e}"
            )

    st.subheader(
        "Research Notes"
    )

    title = st.text_input(
        "Note title"
    )

    note = st.text_area(
        "Research note"
    )

    if st.button(
        "Save Research Note"
    ):

        if title and note:
            save_note(
                title,
                note,
            )
            st.success(
                "Research note saved."
            )


# ============================================================
# BEHAVIOUR DECODING
# ============================================================

def consultation_page():

    st.header(
        "🧠 Behaviour Decoding / 1-to-1"
    )

    pricing = {
        "20 minutes": 1000,
        "30 minutes": 1500,
        "45 minutes": 2000,
    }

    st.write(
        "Educational discussion service"
    )

    duration = st.selectbox(
        "Session",
        list(pricing.keys()),
    )

    st.metric(
        "Price",
        f"PKR {pricing[duration]:,}",
    )

    name = st.text_input(
        "Name"
    )

    contact = st.text_input(
        "Contact"
    )

    topic = st.text_area(
        "Topic"
    )

    payment_method = st.selectbox(
        "Payment Method",
        [
            "Easypaisa",
            "International payment",
        ],
    )

    payment_reference = st.text_input(
        "Payment reference"
    )

    if st.button(
        "Submit Request"
    ):

        conn = db()

        conn.execute(
            """
            INSERT INTO consultations
            (
                created_at,
                name,
                contact,
                topic,
                duration,
                payment_method,
                payment_reference,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                clean_text(name),
                clean_text(contact),
                clean_text(topic),
                duration,
                payment_method,
                clean_text(payment_reference),
                "Pending verification",
            ),
        )

        conn.commit()
        conn.close()

        st.success(
            "Request submitted. Payment verification pending."
        )

    st.info(
        "Automatic Easypaisa verification requires an official "
        "merchant/API integration. This app does not fake payment verification."
    )


# ============================================================
# BRAIN EXERCISES
# ============================================================

def exercises_page():

    st.header(
        "🎯 Brain Exercises"
    )

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

        sequence = "581936"

        st.write(
            "Memorize:"
        )

        st.code(sequence)

        answer = st.text_input(
            "Enter sequence"
        )

        if st.button(
            "Check"
        ):

            score = (
                100
                if answer == sequence
                else 0
            )

            st.metric(
                "Score",
                score,
            )

            save_activity(
                "Exercise",
                exercise,
                score,
                answer,
            )

    elif exercise == "Pattern Recognition":

        st.write(
            "2 → 4 → 8 → 16 → ?"
        )

        answer = st.number_input(
            "Answer",
            min_value=0,
            value=0,
        )

        if st.button(
            "Check Pattern"
        ):

            score = (
                100
                if answer == 32
                else 0
            )

            st.metric(
                "Score",
                score,
            )

            save_activity(
                "Exercise",
                exercise,
                score,
                str(answer),
            )

    elif exercise == "Decision Challenge":

        answer = st.radio(
            "Choose",
            [
                "PKR 1,000 now",
                "PKR 1,500 after 30 days",
            ],
        )

        if st.button(
            "Save Decision"
        ):

            save_activity(
                "Exercise",
                exercise,
                None,
                answer,
            )

            st.success(
                "Decision saved."
            )

    elif exercise == "Attention":

        st.write(
            "Find X:"
        )

        symbols = [
            "O", "O", "O",
            "O", "X", "O",
            "O", "O", "O",
        ]

        cols = st.columns(3)

        for i, value in enumerate(symbols):

            with cols[i % 3]:

                if st.button(
                    value,
                    key=f"attention_ex_{i}",
                    use_container_width=True,
                ):

                    score = (
                        100
                        if value == "X"
                        else 0
                    )

                    st.metric(
                        "Score",
                        score,
                    )

                    save_activity(
                        "Exercise",
                        exercise,
                        score,
                        value,
                    )

    else:

        if "reaction_start" not in st.session_state:

            st.write(
                "Press Start, then press Stop."
            )

            if st.button(
                "Start Reaction Test"
            ):

                st.session_state.reaction_start = time.perf_counter()
                st.success(
                    "GO!"
                )

        else:

            if st.button(
                "STOP!"
            ):

                elapsed = (
                    time.perf_counter()
                    - st.session_state.reaction_start
                )

                ms = elapsed * 1000

                st.metric(
                    "Reaction Time",
                    f"{ms:.0f} ms",
                )

                save_activity(
                    "Exercise",
                    exercise,
                    ms,
                    "Reaction time",
                )

                del st.session_state.reaction_start


# ============================================================
# BRAIN JOURNEY
# ============================================================

def brain_journey():

    st.header(
        "🧠 Visual Brain Journey"
    )

    region = st.selectbox(
        "Brain System",
        list(BRAIN_REGIONS.keys()),
    )

    st.markdown(
        f"""
        <div class="card">
        <h2>{region}</h2>
        <p>{BRAIN_REGIONS[region]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "NEUROLENS conceptual educational visualization."
    )


# ============================================================
# PROGRESS
# ============================================================

def progress_page():

    st.header(
        "📊 My Progress"
    )

    activity = get_table(
        "SELECT * FROM activity ORDER BY id DESC"
    )

    ai = get_table(
        "SELECT * FROM ai_requests ORDER BY id DESC"
    )

    notes = get_table(
        "SELECT * FROM research_notes ORDER BY id DESC"
    )

    consultations = get_table(
        "SELECT * FROM consultations ORDER BY id DESC"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Activities",
            len(activity),
        )

    with c2:
        st.metric(
            "AI Requests",
            len(ai),
        )

    with c3:
        st.metric(
            "Research Notes",
            len(notes),
        )

    with c4:
        st.metric(
            "Consultations",
            len(consultations),
        )

    if not activity.empty:

        scores = activity[
            activity["score"].notna()
        ]

        if not scores.empty:

            st.subheader(
                "Score History"
            )

            st.line_chart(
                scores[
                    ["created_at", "score"]
                ].set_index("created_at")
            )

    st.subheader(
        "Recent Activity"
    )

    st.dataframe(
        activity.head(30),
        use_container_width=True,
    )

    excel = make_excel()

    st.download_button(
        "📥 Download NEUROLENS Excel",
        excel,
        "neurolens_data.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ============================================================
# SECURITY
# ============================================================

def security_page():

    st.header(
        "🔒 Security & Privacy Center"
    )

    st.markdown(
        """
### API Key Protection

Gemini API key should remain inside:

`.streamlit/secrets.toml`

Never put it directly inside `app.py`.

### PIN Security

Private Ask Ayna uses salted PBKDF2-HMAC-SHA256.

### Input Sanitization

User text is cleaned before database storage and AI prompts.

### AI Limitations

NEUROLENS does not use AI to diagnose users.

### EEG Privacy

EEG data should be treated as sensitive research/biometric data.
Do not upload or share it without appropriate consent and security.

### Eye Tracking Privacy

Webcam-derived gaze information can be sensitive.
Only collect what is necessary and explain the purpose to participants.

### Scientific Limitation

NEUROLENS is an educational/research prototype.
Webcam gaze estimation is not equivalent to laboratory eye tracking,
and cognitive games do not directly measure brain activity.
"""
    )


# ============================================================
# SETTINGS
# ============================================================

def settings_page():

    st.header(
        "⚙️ Settings"
    )

    st.selectbox(
        "Language",
        [
            "English",
            "Roman English",
            "Urdu",
        ],
    )

    model = get_secret(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    )

    st.write(
        f"AI Model: `{model}`"
    )

    st.write(
        "Gemini configured:",
        bool(
            get_secret("GEMINI_API_KEY")
        ),
    )

    if st.button(
        "Reset Session Progress"
    ):

        keys = list(
            st.session_state.keys()
        )

        for key in keys:

            if key.startswith(
                "reaction"
            ):
                del st.session_state[key]

        st.success(
            "Temporary session state reset."
        )


# ============================================================
# DIAGNOSTICS
# ============================================================

def diagnostics():

    st.header(
        "🛠️ System Diagnostics"
    )

    checks = {
        "Gemini SDK": GEMINI_AVAILABLE,
        "BrainFlow": BRAINFLOW_AVAILABLE,
        "OpenCV": CV_AVAILABLE,
        "MediaPipe": MEDIAPIPE_AVAILABLE,
        "WebRTC": WEBRTC_AVAILABLE,
    }

    for name, value in checks.items():

        if value:
            st.success(
                f"PASS — {name}"
            )
        else:
            st.warning(
                f"NOT AVAILABLE — {name}"
            )

    st.subheader(
        "BrainFlow Boards Detected"
    )

    st.json(
        board_candidates()
    )

    if st.button(
        "Test Gemini"
    ):

        response = ask_ai(
            "Reply with: NEUROLENS AI connection test successful.",
            "Diagnostics",
        )

        st.write(response)

    if st.button(
        "Test Europe PMC"
    ):

        try:

            import requests

            r = requests.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={
                    "query": "cognitive neuroscience",
                    "format": "json",
                    "pageSize": 1,
                },
                timeout=10,
            )

            st.success(
                f"Europe PMC HTTP {r.status_code}"
            )

        except Exception as e:
            st.error(str(e))


# ============================================================
# HOME
# ============================================================

def home():

    st.markdown(
        '<div class="neuro-title">🧠 NEUROLENS</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="neuro-sub">'
        "Explore cognition, behavior & the brain"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        """
## Welcome to NEUROLENS

An educational cognitive neuroscience platform combining:

🧠 Cognitive experiments  
👁️ Webcam-based gaze estimation  
🧠 Real / synthetic EEG  
🤖 AI cognitive explanations  
📚 Research discovery  
📊 Progress tracking  
🔐 Privacy tools
"""
    )

    st.info(
        "For real EEG, connect compatible hardware to the machine "
        "running the BrainFlow backend."
    )


# ============================================================
# ROUTER
# ============================================================

pages = {
    "🏠 Home": home,
    "🧪 Virtual Cognitive Lab": cognitive_lab,
    "👁️ AI Eye Tracking": eye_tracking_page,
    "🧠 EEG / Biosignal Lab": eeg_page,
    "🧠 Brain Journey": brain_journey,
    "🧩 Brain Puzzle": puzzle_page,
    "🤖 Ask Ayna": ask_ayna_page,
    "🔐 Private Ask Ayna": private_ask_page,
    "😊 Mood & Behaviour": mood_page,
    "📚 Research Book": research_book,
    "🧠 Behaviour Decoding": consultation_page,
    "🎯 Brain Exercises": exercises_page,
    "📊 My Progress": progress_page,
    "🔒 Security & Privacy": security_page,
    "⚙️ Settings": settings_page,
    "🛠️ Diagnostics": diagnostics,
}

with st.sidebar:

    st.markdown(
        "## 🧠 NEUROLENS"
    )

    st.caption(
        "Cognitive Neuroscience × AI"
    )

    selected_page = st.radio(
        "Navigate",
        list(pages.keys()),
    )

    st.divider()

    st.caption(
        "Created by Ayna Jaffri"
    )

    st.caption(
        "Educational / research prototype"
    )


pages[selected_page]()
