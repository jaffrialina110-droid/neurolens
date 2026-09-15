import os
import random
import time
import hashlib
import base64
import html
from io import BytesIO
import urllib.request
import urllib.parse

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
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# PATHS / ASSETS
# =========================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")

BRAIN_IMAGE = os.path.join(ROOT, "brain.png")

LAB_VIDEO = os.path.join(ROOT, "cognitive_lab_brain.mp4")
if not os.path.exists(LAB_VIDEO):
    LAB_VIDEO = os.path.join(ASSETS, "brain_animation.mp4")

REBOOT_VIDEO = os.path.join(ASSETS, "ayna_reboot_voiced.mp4")

if not os.path.exists(REBOOT_VIDEO):
    REBOOT_VIDEO = os.path.join(ROOT, "ayna_reboot_voiced_faster_louder.mp4")

AYNA_ROBOT = os.path.join(ASSETS, "ayna_robot.png")


def first_existing(*paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "Welcome",
    "progress": {},
    "lab_character": "Mira",
    "lab_equipment": "EEG",
    "lab_experiment": "Attention Gate",
    "lab_started": False,
    "lab_applied": False,
    "lab_guide_language": "English",
    "mood_result": None,
    "mood_reason": "",
    "mood_audio": None,
    "mood_text": "",
    "mood_emoji": "😐",
    "ayna_messages": [],
    "private_messages": [],
    "private_unlocked": False,
    "private_pin_hash": None,
    "private_pin_created": False,
    "daily_result": None,
    "puzzle_completed": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# PROGRESS
# =========================================================

def record(activity, points=1):
    st.session_state.progress[activity] = (
        st.session_state.progress.get(activity, 0) + points
    )


# =========================================================
# AI
# =========================================================

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


def make_client():
    if genai is None:
        return None

    key = get_api_key()

    if not key:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def ask_ai(prompt):
    client = make_client()

    if client is None:
        return (
            "AI connection is not available right now. "
            "Please check your GEMINI_API_KEY in Streamlit Secrets."
        )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

        return "I could not generate a response right now."

    except Exception as e:
        return f"AI temporarily unavailable: {str(e)}"


def ask_ai_with_audio(prompt, audio_bytes, mime_type="audio/wav"):
    client = make_client()

    if client is None:
        return (
            "AI connection is not available. "
            "Please check GEMINI_API_KEY in Streamlit Secrets."
        )

    if types is None:
        return "Audio analysis is unavailable in this environment."

    try:
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type,
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                prompt,
                audio_part,
            ],
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

        return "I could not analyse the voice recording."

    except Exception as e:
        return f"Voice analysis temporarily unavailable: {str(e)}"


# =========================================================
# IMAGE HELPERS
# =========================================================

def image_to_base64(path):
    if not path or not os.path.exists(path):
        return None

    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def image_bytes(path):
    if not path or not os.path.exists(path):
        return None

    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def show_image(path, width=None):
    if path and os.path.exists(path):
        st.image(
            path,
            width=width,
        )


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.main-title {
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 0.2rem;
}

.subtitle {
    color: #6b7280;
    font-size: 1.1rem;
    margin-bottom: 1.5rem;
}

.card {
    padding: 1.2rem;
    border-radius: 18px;
    border: 1px solid rgba(120,120,120,.20);
    background: rgba(255,255,255,.04);
    margin-bottom: 1rem;
}

.lab-box {
    border-radius: 20px;
    padding: 1.4rem;
    border: 1px solid rgba(100,150,255,.30);
    background:
        linear-gradient(
            135deg,
            rgba(20,40,80,.90),
            rgba(10,20,45,.95)
        );
    color: white;
}

.big-emoji {
    font-size: 4rem;
}

.mood-box {
    text-align: center;
    padding: 2rem;
    border-radius: 22px;
    border: 1px solid rgba(100,100,100,.2);
}

.robot-box {
    text-align: center;
    padding: 1rem;
}

.small-muted {
    color: #7b8190;
    font-size: .9rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

PAGES = [
    "Welcome",
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

with st.sidebar:
    st.markdown("## 🧠 NEUROLENS")

    st.caption("Explore cognition, behaviour & the brain")

    current_index = (
        PAGES.index(st.session_state.page)
        if st.session_state.page in PAGES
        else 0
    )

    selected_page = st.radio(
        "Navigate",
        PAGES,
        index=current_index,
    )

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()

    st.divider()

    st.markdown("### Researcher")
    st.markdown("👩‍🔬 **Ayna Jaffri**")
    st.caption("Independent cognitive neuroscience researcher")


# =========================================================
# WELCOME
# =========================================================

if st.session_state.page == "Welcome":

    st.markdown(
        '<div class="main-title">🧠 NEUROLENS</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Explore cognition, behaviour & the brain"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card">
        <h2>Welcome to NeuroLens</h2>
        <p>
        I’m Ayna. Let’s explore the brain, behaviour, and cognition together.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if os.path.exists(REBOOT_VIDEO):
        st.video(REBOOT_VIDEO)

    st.markdown("### Start exploring")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🧪 Enter Lab", use_container_width=True):
            st.session_state.page = "Lab"
            st.rerun()

    with c2:
        if st.button("🧩 Brain Puzzle", use_container_width=True):
            st.session_state.page = "Brain Puzzle"
            st.rerun()

    with c3:
        if st.button("🤖 Ask Ayna", use_container_width=True):
            st.session_state.page = "Ask Ayna"
            st.rerun()


# =========================================================
# LAB
# =========================================================

elif st.session_state.page == "Lab":

    st.markdown("## 🧪 Cognitive Neuroscience Lab")
    st.caption(
        "Design an experiment, choose your subject and equipment, "
        "then run the live lab setup."
    )

    characters = {
        "Nova": {
            "emoji": "👩",
            "description": "Focused participant for attention experiments.",
        },
        "Mira": {
            "emoji": "👩",
            "description": "Participant suitable for memory and attention tasks.",
        },
        "Ray": {
            "emoji": "🧑",
            "description": "Participant for decision and inhibition experiments.",
        },
        "Zara": {
            "emoji": "👩",
            "description": "Participant for flexible cognition experiments.",
        },
    }

    equipment = {
        "EEG": "Measures electrical brain activity at the scalp.",
        "Eye Tracker": "Tracks gaze and visual attention.",
        "Reaction Pad": "Records behavioural response timing.",
        "Memory Console": "Presents and records memory tasks.",
        "Decision Panel": "Presents choice and reward scenarios.",
    }

    experiments = {
        "Attention Gate": "Selective attention and distractor control.",
        "Working Memory Sprint": "Short-term information maintenance.",
        "Decision Under Delay": "Immediate versus delayed reward choice.",
        "Inhibition Challenge": "Suppressing a dominant response.",
        "Cognitive Flexibility": "Switching between changing rules.",
        "Memory Retrieval": "Retrieving previously encoded information.",
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        character = st.selectbox(
            "👤 Choose participant",
            list(characters.keys()),
            index=list(characters.keys()).index(
                st.session_state.lab_character
            ),
        )

    with col2:
        equipment_choice = st.selectbox(
            "🔬 Choose equipment",
            list(equipment.keys()),
            index=list(equipment.keys()).index(
                st.session_state.lab_equipment
            ),
        )

    with col3:
        experiment = st.selectbox(
            "🧠 Choose experiment",
            list(experiments.keys()),
            index=list(experiments.keys()).index(
                st.session_state.lab_experiment
            ),
        )

    st.markdown("### Current selection")

    selected_character = characters[character]

    a, b, c = st.columns(3)

    with a:
        st.info(
            f"{selected_character['emoji']} **{character}**\n\n"
            f"{selected_character['description']}"
        )

    with b:
        st.info(
            f"🔬 **{equipment_choice}**\n\n"
            f"{equipment[equipment_choice]}"
        )

    with c:
        st.info(
            f"🧠 **{experiment}**\n\n"
            f"{experiments[experiment]}"
        )

    if st.button(
        "⚙️ Apply Experiment Setup",
        use_container_width=True,
    ):
        st.session_state.lab_character = character
        st.session_state.lab_equipment = equipment_choice
        st.session_state.lab_experiment = experiment
        st.session_state.lab_applied = True
        st.session_state.lab_started = False
        record("Lab setup")

    if st.session_state.lab_applied:

        st.success(
            f"Setup applied: {character} + {equipment_choice} + {experiment}"
        )

        if st.button(
            "▶️ Run Live Experiment",
            use_container_width=True,
        ):
            st.session_state.lab_started = True
            record("Live experiment")
            st.rerun()

    if st.session_state.lab_started:

        char = st.session_state.lab_character
        equip = st.session_state.lab_equipment
        exp = st.session_state.lab_experiment

        char_data = characters[char]

        st.markdown("## 🔴 Live Experimental Setup")

        scene_html = f"""
        <style>
        body {{
            margin:0;
            background:#07111f;
            font-family:Arial,sans-serif;
            color:white;
        }}

        .scene {{
            position:relative;
            height:390px;
            overflow:hidden;
            border-radius:24px;
            background:
                radial-gradient(circle at 50% 10%, #1c4771, #07111f 65%);
            border:1px solid #2c547d;
        }}

        .lights {{
            position:absolute;
            top:18px;
            left:10%;
            right:10%;
            height:8px;
            background:#38bdf8;
            box-shadow:0 0 25px #38bdf8;
            opacity:.7;
        }}

        .scientist {{
            position:absolute;
            left:8%;
            bottom:42px;
            text-align:center;
            font-size:64px;
        }}

        .subject {{
            position:absolute;
            left:42%;
            bottom:58px;
            text-align:center;
            font-size:72px;
        }}

        .equipment {{
            position:absolute;
            right:9%;
            bottom:60px;
            width:180px;
            padding:18px;
            border-radius:18px;
            background:#102944;
            border:1px solid #3c6c98;
            text-align:center;
            font-size:19px;
        }}

        .experiment {{
            position:absolute;
            top:48px;
            left:50%;
            transform:translateX(-50%);
            padding:14px 24px;
            border-radius:999px;
            background:#132f4c;
            border:1px solid #4ca9e8;
            font-size:20px;
        }}

        .signal {{
            position:absolute;
            left:34%;
            right:28%;
            bottom:205px;
            height:3px;
            background:linear-gradient(
                90deg,
                transparent,
                #38bdf8,
                #a7f3d0,
                #38bdf8,
                transparent
            );
            animation:pulse 1.2s infinite;
        }}

        @keyframes pulse {{
            0% {{opacity:.2; transform:scaleX(.7);}}
            50% {{opacity:1; transform:scaleX(1);}}
            100% {{opacity:.2; transform:scaleX(.7);}}
        }}

        .status {{
            position:absolute;
            bottom:15px;
            left:50%;
            transform:translateX(-50%);
            color:#9fe8ff;
        }}
        </style>

        <div class="scene">
            <div class="lights"></div>

            <div class="experiment">
                🧠 {html.escape(exp)}
            </div>

            <div class="scientist">
                👩‍🔬
                <div style="font-size:14px;">Ayna</div>
            </div>

            <div class="subject">
                {char_data["emoji"]}
                <div style="font-size:16px;">{html.escape(char)}</div>
            </div>

            <div class="signal"></div>

            <div class="equipment">
                🔬<br>
                <b>{html.escape(equip)}</b>
            </div>

            <div class="status">
                ● LIVE EXPERIMENT RUNNING
            </div>
        </div>
        """

        components.html(
            scene_html,
            height=410,
            scrolling=False,
        )

        st.markdown("### 🎥 Lab Environment")

        if os.path.exists(LAB_VIDEO):
            st.video(LAB_VIDEO)
        else:
            st.warning("Lab animation video was not found.")

        st.markdown("### 🤖 Ask Ayna — Lab Guide")

        guide_lang = st.radio(
            "Guide language",
            ["English", "Roman English"],
            horizontal=True,
            key="lab_guide_language_radio",
        )

        question = st.text_input(
            "Ask about the current experiment",
            placeholder="e.g. What does EEG measure?",
        )

        if st.button(
            "Ask Ayna",
            key="lab_ask_button",
        ):

            if guide_lang == "English":
                language_instruction = "Answer in clear English."
            else:
                language_instruction = (
                    "Answer in simple Roman English/Roman Urdu style."
                )

            prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience laboratory guide.

Current participant: {char}
Participant description: {char_data['description']}

Current equipment: {equip}
Equipment purpose: {equipment[equip]}

Current experiment: {exp}
Experiment purpose: {experiments[exp]}

The user asks:
{question}

{language_instruction}

Explain the experiment scientifically but simply.
Do not diagnose the participant.
Do not claim this simple demonstration measures the user's actual brain activity.
"""

            st.info(ask_ai(prompt))


# =========================================================
# EXPLORE BRAIN
# =========================================================

elif st.session_state.page == "Explore Brain":

    st.markdown("## 🧠 Explore Brain Systems")

    systems = {
        "Prefrontal Cortex": (
            "Supports cognitive control, planning, working memory, "
            "decision-making and goal-directed behaviour."
        ),
        "Hippocampus": (
            "A key structure for memory formation, spatial processing "
            "and contextual learning."
        ),
        "Striatum": (
            "Part of the basal ganglia and involved in action selection, "
            "reward-related learning and movement."
        ),
        "Anterior Cingulate Cortex": (
            "Involved in cognitive control, conflict monitoring, "
            "error processing and motivational processes."
        ),
        "Attention Networks": (
            "Distributed systems that help select relevant information "
            "and maintain goal-directed attention."
        ),
    }

    selected = st.selectbox(
        "Select a brain system",
        list(systems.keys()),
    )

    st.markdown(
        f"""
        <div class="card">
        <h2>{selected}</h2>
        <p>{systems[selected]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if os.path.exists(BRAIN_IMAGE):
        show_image(BRAIN_IMAGE)

    st.caption(
        "Educational visualization only. A simple app visualization "
        "does not represent real-time brain activity."
    )


# =========================================================
# BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    st.markdown("## 🧩 Brain Image Puzzle")

    st.write(
        "Use your finger to drag the brain pieces into their correct "
        "positions. This is a visual touch-and-drag puzzle."
    )

    if not os.path.exists(BRAIN_IMAGE):
        st.error("brain.png was not found in the project folder.")

    else:

        brain_b64 = image_to_base64(BRAIN_IMAGE)

        if brain_b64:

            puzzle_html = f"""
            <style>

            body {{
                margin:0;
                background:#07111f;
                color:white;
                font-family:Arial,sans-serif;
            }}

            .wrapper {{
                max-width:500px;
                margin:auto;
                text-align:center;
            }}

            .board {{
                position:relative;
                width:360px;
                height:360px;
                margin:20px auto;
                border:3px solid #4ca9e8;
                border-radius:18px;
                overflow:hidden;
                background:#0b1c30;
                touch-action:none;
            }}

            .slot {{
                position:absolute;
                width:33.3333%;
                height:33.3333%;
                box-sizing:border-box;
                border:1px dashed rgba(255,255,255,.18);
            }}

            .piece {{
                position:absolute;
                width:33.3333%;
                height:33.3333%;
                box-sizing:border-box;
                border:1px solid rgba(255,255,255,.5);
                background-image:url("data:image/png;base64,{brain_b64}");
                background-size:300% 300%;
                cursor:grab;
                touch-action:none;
                transition:transform .12s;
            }}

            .piece.dragging {{
                z-index:100;
                transform:scale(1.05);
                box-shadow:0 0 25px #38bdf8;
            }}

            .success {{
                display:none;
                margin-top:12px;
                padding:14px;
                border-radius:14px;
                background:#123d2b;
                color:#a7f3d0;
                font-weight:bold;
            }}

            </style>

            <div class="wrapper">

            <h3>Drag the brain pieces 🧠</h3>

            <div class="board" id="board"></div>

            <div class="success" id="success">
                🧠 Puzzle completed!
            </div>

            </div>

            <script>

            const board = document.getElementById("board");
            const success = document.getElementById("success");

            const N = 3;
            const total = N * N;

            let positions = [];

            for (let i = 0; i < total; i++) {{
                positions.push(i);
            }}

            function shuffle(array) {{
                for (let i = array.length - 1; i > 0; i--) {{
                    const j = Math.floor(Math.random() * (i + 1));
                    [array[i], array[j]] = [array[j], array[i]];
                }}

                return array;
            }}

            positions = shuffle(positions);

            function createSlots() {{

                for (let i = 0; i < total; i++) {{

                    const row = Math.floor(i / N);
                    const col = i % N;

                    const slot = document.createElement("div");

                    slot.className = "slot";

                    slot.style.left = (col * 100 / N) + "%";
                    slot.style.top = (row * 100 / N) + "%";

                    board.appendChild(slot);
                }}
            }}

            createSlots();

            const pieces = [];

            positions.forEach((correctIndex, positionIndex) => {{

                const piece = document.createElement("div");

                piece.className = "piece";

                piece.dataset.correct = correctIndex;
                piece.dataset.position = positionIndex;

                const row = Math.floor(correctIndex / N);
                const col = correctIndex % N;

                piece.style.backgroundPosition =
                    `${{
                        N === 1 ? 0 : (col / (N - 1) * 100)
                    }}% ${{ 
                        N === 1 ? 0 : (row / (N - 1) * 100)
                    }}%`;

                const currentRow = Math.floor(positionIndex / N);
                const currentCol = positionIndex % N;

                piece.style.left = (currentCol * 100 / N) + "%";
                piece.style.top = (currentRow * 100 / N) + "%";

                board.appendChild(piece);

                pieces.push(piece);

                let startX = 0;
                let startY = 0;
                let startLeft = 0;
                let startTop = 0;

                piece.addEventListener("pointerdown", (event) => {{

                    event.preventDefault();

                    piece.classList.add("dragging");

                    startX = event.clientX;
                    startY = event.clientY;

                    startLeft = parseFloat(piece.style.left);
                    startTop = parseFloat(piece.style.top);

                    piece.setPointerCapture(event.pointerId);
                }});

                piece.addEventListener("pointermove", (event) => {{

                    if (!piece.classList.contains("dragging")) return;

                    const rect = board.getBoundingClientRect();

                    const dx =
                        ((event.clientX - startX) / rect.width) * 100;

                    const dy =
                        ((event.clientY - startY) / rect.height) * 100;

                    piece.style.left = (startLeft + dx) + "%";
                    piece.style.top = (startTop + dy) + "%";
                }});

                piece.addEventListener("pointerup", (event) => {{

                    piece.classList.remove("dragging");

                    const rect = board.getBoundingClientRect();

                    let x = event.clientX - rect.left;
                    let y = event.clientY - rect.top;

                    x = Math.max(0, Math.min(rect.width - 1, x));
                    y = Math.max(0, Math.min(rect.height - 1, y));

                    const col = Math.floor(x / (rect.width / N));
                    const row = Math.floor(y / (rect.height / N));

                    const targetPosition = row * N + col;

                    const occupyingPiece = pieces.find(
                        p => Number(p.dataset.position) === targetPosition
                    );

                    const oldPosition = Number(piece.dataset.position);

                    if (
                        occupyingPiece &&
                        occupyingPiece !== piece
                    ) {{

                        const otherPosition =
                            Number(occupyingPiece.dataset.position);

                        piece.dataset.position = targetPosition;
                        occupyingPiece.dataset.position = oldPosition;

                        movePiece(piece, targetPosition);
                        movePiece(occupyingPiece, oldPosition);

                    }} else {{

                        piece.dataset.position = targetPosition;

                        movePiece(piece, targetPosition);
                    }}

                    checkPuzzle();
                }});
            }}


            function movePiece(piece, position) {{

                const row = Math.floor(position / N);
                const col = position % N;

                piece.style.left = (col * 100 / N) + "%";
                piece.style.top = (row * 100 / N) + "%";
            }}


            function checkPuzzle() {{

                let correct = true;

                pieces.forEach(piece => {{

                    if (
                        Number(piece.dataset.correct) !==
                        Number(piece.dataset.position)
                    ) {{
                        correct = false;
                    }}
                }});

                if (correct) {{
                    success.style.display = "block";
                }}
            }}

            </script>
            """

            components.html(
                puzzle_html,
                height=450,
                scrolling=False,
            )

            if st.button(
                "✅ I completed the puzzle",
                use_container_width=True,
            ):
                st.session_state.puzzle_completed = True
                record("Brain Puzzle")
                st.success("Puzzle recorded in your progress.")


# =========================================================
# AI MOOD & BEHAVIOUR
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.markdown("## 🎙️ AI Mood & Behaviour")

    st.info(
        "Voice analysis gives an AI-estimated apparent mood cue. "
        "It does not directly measure your inner emotional state "
        "and is not a diagnosis."
    )

    st.markdown("### Step 1 — Record your voice")

    audio = st.audio_input(
        "Record a short voice sample",
        key="mood_audio_input",
    )

    if audio is not None:

        st.audio(audio)

        if st.button(
            "🎙️ Send Voice for AI Mood Estimate",
            use_container_width=True,
        ):

            audio_bytes = audio.getvalue()

            prompt = """
You are an educational cognitive neuroscience assistant.

Analyse this voice sample only for broad apparent emotional/mood cues.

Return EXACTLY in this format:

MOOD: one of
Happy
Excited
Calm
Neutral
Worried
Sad
Frustrated
Tired

REASON: one short sentence.

Important:
- This is only an apparent AI-estimated mood cue.
- Do not diagnose.
- Do not claim to know the person's true internal emotional state.
- Do not make medical claims.
"""

            result = ask_ai_with_audio(
                prompt,
                audio_bytes,
                mime_type=audio.type or "audio/wav",
            )

            mood = "Neutral"
            reason = result

            for possible in [
                "Happy",
                "Excited",
                "Calm",
                "Neutral",
                "Worried",
                "Sad",
                "Frustrated",
                "Tired",
            ]:
                if possible.lower() in result.lower():
                    mood = possible
                    break

            if "REASON:" in result:
                reason = result.split(
                    "REASON:",
                    1
                )[1].strip()

            emoji_map = {
                "Happy": "😊",
                "Excited": "🤩",
                "Calm": "😌",
                "Neutral": "😐",
                "Worried": "😟",
                "Sad": "😔",
                "Frustrated": "😤",
                "Tired": "😴",
            }

            st.session_state.mood_result = mood
            st.session_state.mood_reason = reason
            st.session_state.mood_audio = audio_bytes

            record("Voice mood experiment")

    if st.session_state.mood_result:

        mood = st.session_state.mood_result

        emoji_map = {
            "Happy": "😊",
            "Excited": "🤩",
            "Calm": "😌",
            "Neutral": "😐",
            "Worried": "😟",
            "Sad": "😔",
            "Frustrated": "😤",
            "Tired": "😴",
        }

        st.markdown(
            f"""
            <div class="mood-box">
                <div class="big-emoji">{emoji_map[mood]}</div>
                <h2>{mood}</h2>
                <p>
                AI-estimated apparent mood cue
                </p>
                <p>{html.escape(st.session_state.mood_reason)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Step 2 — Add text + emoji")

    mood_text = st.text_area(
        "How are you feeling or what happened?",
        value=st.session_state.mood_text,
        placeholder="Write something about your current experience...",
    )

    emoji_options = [
        "😊",
        "🤩",
        "😌",
        "😐",
        "😟",
        "😔",
        "😤",
        "😴",
    ]

    selected_emoji = st.selectbox(
        "Choose an emoji",
        emoji_options,
        index=emoji_options.index(
            st.session_state.mood_emoji
        ),
    )

    if st.button(
        "🧠 Analyse Voice + Text + Emoji",
        use_container_width=True,
    ):

        st.session_state.mood_text = mood_text
        st.session_state.mood_emoji = selected_emoji

        voice_description = "No voice sample provided."

        if st.session_state.mood_result:
            voice_description = (
                f"Previous AI-estimated apparent mood cue: "
                f"{st.session_state.mood_result}"
            )

        prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience assistant.

The user provided:

Voice cue:
{voice_description}

Text:
{mood_text}

Emoji:
{selected_emoji}

Give a short educational interpretation.

Discuss:
- possible emotional cues,
- attention/arousal or cognitive context when relevant,
- uncertainty,
- how text and emoji can differ from vocal cues.

Do not diagnose.
Do not claim that the AI knows the user's true internal state.
Do not present this as a clinical assessment.
"""

        with st.spinner("Ayna is analysing..."):
            analysis = ask_ai(prompt)

        st.markdown("### 🧠 Combined Analysis")
        st.write(analysis)

        record("Combined mood analysis")


# =========================================================
# BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    st.markdown("## 🧠 Brain Exercises")

    exercise = st.selectbox(
        "Choose an exercise",
        [
            "Memory Sequence",
            "Attention Search",
            "Stroop Challenge",
            "Pattern Completion",
        ],
    )

    if exercise == "Memory Sequence":

        st.write("Remember this sequence:")

        sequence = "729418"

        st.markdown(
            f"""
            <div class="card">
            <h1 style="text-align:center;letter-spacing:12px;">
            {sequence}
            </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.text_input(
            "Enter the sequence from memory"
        )

        if st.button(
            "Check Memory",
            key="memory_check",
        ):

            if answer.replace(" ", "") == sequence:
                st.success("Correct! 🧠")
                record("Memory exercise")
            else:
                st.error("Not quite. Try again.")

    elif exercise == "Attention Search":

        st.write("Find the letter X.")

        letters = [
            random.choice(["O", "0", "Q"])
            for _ in range(24)
        ]

        target = random.randint(0, 23)
        letters[target] = "X"

        grid = " ".join(letters)

        st.markdown(
            f"""
            <div class="card"
            style="font-size:28px;letter-spacing:14px;text-align:center;">
            {grid}
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.number_input(
            "Which position contains X?",
            min_value=1,
            max_value=24,
            step=1,
        )

        if st.button(
            "Check Attention",
            key="attention_check",
        ):

            if answer == target + 1:
                st.success("Correct! 👁️")
                record("Attention exercise")
            else:
                st.error("Try again.")

    elif exercise == "Stroop Challenge":

        st.markdown(
            """
            <div class="card">
            <h2>BLUE</h2>
            <p>
            Ignore the word. Think about the ink colour.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.selectbox(
            "What colour should you report?",
            ["Blue", "Red", "Green", "Yellow"],
        )

        if st.button(
            "Submit Stroop",
            key="stroop_check",
        ):

            if answer == "Blue":
                st.success("Correct!")
                record("Stroop exercise")
            else:
                st.error("Try again.")

    else:

        st.markdown(
            """
            <div class="card">
            <h2>2 → 4 → 8 → 16 → ?</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.number_input(
            "Next number",
            min_value=0,
            step=1,
        )

        if st.button(
            "Check Pattern",
            key="pattern_check",
        ):

            if answer == 32:
                st.success("Correct! 🔢")
                record("Pattern exercise")
            else:
                st.error("Try again.")


# =========================================================
# DAILY COGNITIVE EXPERIMENT
# =========================================================

elif st.session_state.page == "Daily Cognitive Experiment":

    st.markdown("## 🧪 Daily Cognitive Experiment")

    st.write(
        "Choose between an immediate and delayed reward."
    )

    option = st.radio(
        "Your choice",
        [
            "Rs 1,000 today",
            "Rs 1,500 after 30 days",
        ],
    )

    if st.button(
        "Record Decision",
        use_container_width=True,
    ):

        st.session_state.daily_result = option
        record("Daily cognitive experiment")

        st.success(
            f"You selected: {option}"
        )

        st.caption(
            "This is an educational decision-making demonstration, "
            "not a diagnostic test."
        )


# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    st.markdown("## 📚 Research Book")

    query = st.text_input(
        "Search biomedical literature",
        placeholder="e.g. attention cognitive neuroscience",
    )

    if st.button(
        "🔎 Search Europe PMC",
        use_container_width=True,
    ):

        if not query.strip():
            st.warning("Enter a research topic first.")

        else:

            encoded = urllib.parse.quote(query)

            url = (
                "https://www.ebi.ac.uk/europepmc/webservices/"
                "rest/search?"
                f"query={encoded}&format=json&pageSize=8"
            )

            try:

                with urllib.request.urlopen(
                    url,
                    timeout=15,
                ) as response:

                    data = response.read().decode("utf-8")

                results = __import__("json").loads(data)

                articles = results.get(
                    "resultList",
                    {}
                ).get(
                    "result",
                    []
                )

                if not articles:
                    st.info("No articles found.")

                for article in articles:

                    title = article.get(
                        "title",
                        "Untitled",
                    )

                    journal = article.get(
                        "journalTitle",
                        "",
                    )

                    year = article.get(
                        "pubYear",
                        "",
                    )

                    pmid = article.get(
                        "pmid",
                        "",
                    )

                    st.markdown(
                        f"### {title}"
                    )

                    st.caption(
                        f"{journal} · {year}"
                    )

                    if pmid:

                        st.markdown(
                            f"[View on Europe PMC]"
                            f"(https://europepmc.org/article/MED/{pmid})"
                        )

                    st.divider()

            except Exception as e:

                st.error(
                    f"Literature search failed: {e}"
                )


# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    st.markdown("## 🤖 Ask Ayna")

    st.caption(
        "Your educational cognitive neuroscience assistant."
    )

    language = st.radio(
        "Response language",
        ["English", "Roman English"],
        horizontal=True,
    )

    if language == "English":
        language_instruction = (
            "Answer in clear, simple English."
        )
    else:
        language_instruction = (
            "Answer in simple Roman English/Roman Urdu. "
            "Keep scientific terms in English where useful."
        )

    st.markdown(
        """
        <div class="card">
        Ask about memory, attention, learning, emotion,
        decision-making, reward, perception, cognitive control,
        neuroplasticity, brain systems and behaviour.
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_question = st.text_area(
        "Your question",
        placeholder="Ask Ayna something about the brain...",
    )

    if st.button(
        "Send to Ayna",
        use_container_width=True,
    ):

        if user_question.strip():

            prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience assistant.

{language_instruction}

Explain concepts accurately but accessibly.

Topics include:
- cognitive neuroscience
- memory
- attention
- learning
- emotion
- decision-making
- reward
- perception
- cognitive control
- behaviour
- neuroplasticity
- brain systems

Rules:
- Do not diagnose.
- Do not claim simple cognitive games measure actual brain activity.
- Distinguish scientific evidence from speculation.
- Mention uncertainty when appropriate.

User question:
{user_question}
"""

            answer = ask_ai(prompt)

            st.session_state.ayna_messages.append(
                {
                    "question": user_question,
                    "answer": answer,
                }
            )

            record("Ask Ayna")

    if st.session_state.ayna_messages:

        st.markdown("### Conversation")

        for item in reversed(
            st.session_state.ayna_messages
        ):

            st.markdown(
                f"**You:** {item['question']}"
            )

            st.markdown(
                f"**Ayna:** {item['answer']}"
            )

            st.divider()

    st.markdown("### 🎙️ Voice Question")

    voice = st.audio_input(
        "Record a question",
        key="ask_ayna_voice",
    )

    if voice is not None:

        if st.button(
            "🎙️ Ask Ayna with Voice",
            key="voice_ayna_send",
        ):

            if language == "English":
                language_instruction = (
                    "Answer in clear English."
                )
            else:
                language_instruction = (
                    "Answer in simple Roman English/Roman Urdu."
                )

            prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience assistant.

Listen to the user's voice question.

{language_instruction}

Answer the scientific question clearly.

Do not diagnose.
Do not make unsupported medical claims.
"""

            answer = ask_ai_with_audio(
                prompt,
                voice.getvalue(),
                mime_type=voice.type or "audio/wav",
            )

            st.markdown("### Ayna")
            st.write(answer)

            record("Voice Ask Ayna")


# =========================================================
# PRIVATE ASK AYNA
# =========================================================

elif st.session_state.page == "Private Ask Ayna":

    st.markdown("## 🔐 Private Ask Ayna")

    st.caption(
        "Create a session-only PIN to unlock this private chat."
    )

    if not st.session_state.private_pin_created:

        new_pin = st.text_input(
            "Create Secret Key / PIN",
            type="password",
        )

        confirm_pin = st.text_input(
            "Confirm Secret Key / PIN",
            type="password",
        )

        if st.button(
            "Create Private Key",
            use_container_width=True,
        ):

            if not new_pin:
                st.error("Enter a key first.")

            elif new_pin != confirm_pin:
                st.error("Keys do not match.")

            else:

                st.session_state.private_pin_hash = (
                    hashlib.sha256(
                        new_pin.encode()
                    ).hexdigest()
                )

                st.session_state.private_pin_created = True

                st.success(
                    "Private key created for this session."
                )

    else:

        if not st.session_state.private_unlocked:

            entered_pin = st.text_input(
                "Enter Secret Key / PIN",
                type="password",
            )

            if st.button(
                "🔓 Unlock",
                use_container_width=True,
            ):

                entered_hash = hashlib.sha256(
                    entered_pin.encode()
                ).hexdigest()

                if (
                    entered_hash
                    == st.session_state.private_pin_hash
                ):

                    st.session_state.private_unlocked = True
                    st.success("Unlocked.")

                else:

                    st.error("Incorrect key.")

        else:

            st.success(
                "🔓 Private Ask Ayna is unlocked."
            )

            private_question = st.text_area(
                "Private question",
                placeholder="Ask Ayna privately...",
            )

            if st.button(
                "Send Private Question",
                use_container_width=True,
            ):

                if private_question.strip():

                    prompt = f"""
You are Ask Ayna.

This is a private educational cognitive neuroscience
conversation.

Answer carefully and scientifically.

Do not diagnose.

Question:
{private_question}
"""

                    answer = ask_ai(prompt)

                    st.session_state.private_messages.append(
                        {
                            "question": private_question,
                            "answer": answer,
                        }
                    )

                    record("Private Ask Ayna")

            for item in reversed(
                st.session_state.private_messages
            ):

                st.markdown(
                    f"**You:** {item['question']}"
                )

                st.markdown(
                    f"**Ayna:** {item['answer']}"
                )

                st.divider()

            if st.button(
                "🔒 Lock Private Chat",
                use_container_width=True,
            ):

                st.session_state.private_unlocked = False
                st.rerun()

            st.caption(
                "The PIN is stored as a hash in the current Streamlit "
                "session. This should not be treated as a guarantee "
                "of complete privacy."
            )


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.markdown("## 📊 My Progress")

    progress = st.session_state.progress

    total_points = sum(
        progress.values()
    )

    st.metric(
        "Total Activity Points",
        total_points,
    )

    if not progress:

        st.info(
            "Complete an activity to start building your progress."
        )

    else:

        for activity, points in progress.items():

            st.write(
                f"**{activity}** — {points}"
            )

        if plotly_go is not None:

            fig = plotly_go.Figure(
                data=[
                    plotly_go.Bar(
                        x=list(progress.keys()),
                        y=list(progress.values()),
                    )
                ]
            )

            fig.update_layout(
                title="NEUROLENS Activity Progress",
                xaxis_title="Activity",
                yaxis_title="Points",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NEUROLENS • Educational cognitive neuroscience project "
    "by Ayna Jaffri"
)
