import os
import random
import hashlib
import base64
import json
import urllib.parse
import urllib.request
from io import BytesIO

import streamlit as st
from PIL import Image
import streamlit.components.v1 as components

# ============================================================
# OPTIONAL LIBRARIES
# ============================================================

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
# PAGE
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset(*parts):
    return os.path.join(ROOT, *parts)


def existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


BRAIN_IMAGE = existing(
    asset("brain.png"),
)

REBOOT_VIDEO = existing(
    asset("assets", "ayna_reboot_voiced.mp4"),
    asset("ayna_reboot_voiced_faster_louder.mp4"),
    asset("ayna_reboot_voiced_louder.mp4"),
)

LAB_VIDEO = existing(
    asset("cognitive_lab_brain.mp4"),
    asset("assets", "brain_animation.mp4"),
)

AYNA_ROBOT = existing(
    asset("assets", "ayna_robot.png"),
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "Welcome",
    "progress": {},
    "lab_character": "Mira",
    "lab_equipment": "EEG",
    "lab_experiment": "Attention Gate",
    "lab_applied": False,
    "lab_running": False,
    "lab_result": None,
    "lab_guide_language": "English",
    "ayna_chat": [],
    "mood": None,
    "mood_reason": "",
    "mood_audio": None,
    "behaviour_analysis": None,
    "private_hash": None,
    "private_created": False,
    "private_unlocked": False,
    "private_chat": [],
    "puzzle_completed": False,
    "daily_choice": None,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# PROGRESS
# ============================================================

def add_progress(name, points=1):
    st.session_state.progress[name] = (
        st.session_state.progress.get(name, 0) + points
    )


# ============================================================
# GEMINI
# ============================================================

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


def api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


def client():
    if genai is None:
        return None

    key = api_key()

    if not key:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def ai_text(prompt):
    c = client()

    if c is None:
        return (
            "Ayna AI is not connected. "
            "Please check GEMINI_API_KEY in Streamlit Secrets."
        )

    try:
        response = c.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

        return "Ayna could not generate a response."

    except Exception as e:
        return f"Ayna AI error: {e}"


def ai_audio(prompt, audio_data, mime_type):
    c = client()

    if c is None:
        return (
            "Ayna AI is not connected. "
            "Please check GEMINI_API_KEY in Streamlit Secrets."
        )

    if types is None:
        return "Gemini audio support is unavailable."

    try:
        part = types.Part.from_bytes(
            data=audio_data,
            mime_type=mime_type or "audio/wav",
        )

        response = c.models.generate_content(
            model=MODEL,
            contents=[prompt, part],
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

        return "Ayna could not analyse the recording."

    except Exception as e:
        return f"Voice analysis error: {e}"


# ============================================================
# IMAGE
# ============================================================

def image_base64(path):
    if not path or not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.neuro-title {
    font-size: 3.2rem;
    font-weight: 800;
    margin-bottom: 0;
}

.neuro-subtitle {
    font-size: 1.1rem;
    color: #8b93a5;
    margin-bottom: 25px;
}

.neuro-card {
    border: 1px solid rgba(120,150,190,.22);
    border-radius: 20px;
    padding: 20px;
    margin: 10px 0;
    background: rgba(20,30,45,.35);
}

.hero-card {
    border: 1px solid rgba(60,170,230,.30);
    border-radius: 25px;
    padding: 30px;
    background: linear-gradient(
        135deg,
        rgba(10,35,65,.90),
        rgba(8,18,35,.96)
    );
}

.lab-card {
    border: 1px solid rgba(65,180,240,.35);
    border-radius: 20px;
    padding: 20px;
    background: rgba(8,25,45,.9);
}

.mood-card {
    text-align: center;
    border: 1px solid rgba(100,160,220,.25);
    border-radius: 25px;
    padding: 30px;
}

.big-emoji {
    font-size: 70px;
}

.small-note {
    color: #8b93a5;
    font-size: 0.88rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# NAVIGATION
# ============================================================

PAGES = [
    "Welcome",
    "Cognitive Lab",
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

    st.caption(
        "Explore cognition, behaviour & the brain"
    )

    page = st.radio(
        "Navigation",
        PAGES,
        index=PAGES.index(
            st.session_state.page
        ),
    )

    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()

    st.divider()

    st.markdown("### 👩‍🔬 Researcher")

    st.markdown(
        "**Ayna Jaffri**"
    )

    st.caption(
        "Independent cognitive neuroscience researcher"
    )


# ============================================================
# WELCOME / REBOOT
# ============================================================

if st.session_state.page == "Welcome":

    st.markdown(
        '<div class="neuro-title">🧠 NEUROLENS</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="neuro-subtitle">'
        "Explore cognition, behaviour & the brain"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hero-card">

        <h2>Welcome to NeuroLens</h2>

        <p>
        I’m Ayna. Let’s explore the brain, behaviour,
        cognition and artificial intelligence together.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎬 Ayna Reboot")

    if REBOOT_VIDEO:

        st.video(REBOOT_VIDEO)

    else:

        st.warning(
            "Reboot video not found. Expected: "
            "assets/ayna_reboot_voiced.mp4"
        )

    st.markdown("### 🚀 Start")

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "🧪 Enter Cognitive Lab",
            use_container_width=True,
        ):
            st.session_state.page = "Cognitive Lab"
            st.rerun()

    with c2:

        if st.button(
            "🧩 Brain Puzzle",
            use_container_width=True,
        ):
            st.session_state.page = "Brain Puzzle"
            st.rerun()

    with c3:

        if st.button(
            "🤖 Ask Ayna",
            use_container_width=True,
        ):
            st.session_state.page = "Ask Ayna"
            st.rerun()


# ============================================================
# COGNITIVE LAB
# ============================================================

elif st.session_state.page == "Cognitive Lab":

    st.markdown("## 🧪 Cognitive Neuroscience Lab")

    st.write(
        "You are the researcher. Build the experimental setup "
        "and run it."
    )

    PARTICIPANTS = {
        "Nova": {
            "emoji": "👩",
            "description": "Attention-focused participant.",
        },
        "Mira": {
            "emoji": "👩",
            "description": "Memory and attention participant.",
        },
        "Ray": {
            "emoji": "🧑",
            "description": "Decision and inhibition participant.",
        },
        "Zara": {
            "emoji": "👩",
            "description": "Cognitive flexibility participant.",
        },
    }

    EQUIPMENT = {
        "EEG": (
            "Electrical brain activity recording concept."
        ),
        "Eye Tracker": (
            "Gaze and visual attention tracking."
        ),
        "Reaction Pad": (
            "Behavioural response and reaction-time recording."
        ),
        "Memory Console": (
            "Memory stimulus presentation and response recording."
        ),
        "Decision Panel": (
            "Decision and reward-choice presentation."
        ),
        "Cognitive Monitor": (
            "Visual stimulus and task presentation."
        ),
    }

    EXPERIMENTS = {
        "Attention Gate": (
            "Selective attention and distractor control."
        ),
        "Working Memory Sprint": (
            "Temporary maintenance of information."
        ),
        "Decision Under Delay": (
            "Immediate versus delayed reward decisions."
        ),
        "Inhibition Challenge": (
            "Suppressing a dominant response."
        ),
        "Cognitive Flexibility": (
            "Switching between changing rules."
        ),
        "Memory Retrieval": (
            "Retrieving previously presented information."
        ),
    }

    a, b, c = st.columns(3)

    with a:

        character = st.selectbox(
            "👤 Participant",
            list(PARTICIPANTS.keys()),
            index=list(PARTICIPANTS.keys()).index(
                st.session_state.lab_character
            ),
        )

    with b:

        equipment = st.selectbox(
            "🔬 Equipment",
            list(EQUIPMENT.keys()),
            index=list(EQUIPMENT.keys()).index(
                st.session_state.lab_equipment
            ),
        )

    with c:

        experiment = st.selectbox(
            "🧠 Experiment",
            list(EXPERIMENTS.keys()),
            index=list(EXPERIMENTS.keys()).index(
                st.session_state.lab_experiment
            ),
        )

    st.markdown("### Selected Setup")

    x, y, z = st.columns(3)

    with x:
        st.info(
            f"{PARTICIPANTS[character]['emoji']} "
            f"**{character}**\n\n"
            f"{PARTICIPANTS[character]['description']}"
        )

    with y:
        st.info(
            f"🔬 **{equipment}**\n\n"
            f"{EQUIPMENT[equipment]}"
        )

    with z:
        st.info(
            f"🧠 **{experiment}**\n\n"
            f"{EXPERIMENTS[experiment]}"
        )

    if st.button(
        "⚙️ Apply Experiment Setup",
        use_container_width=True,
    ):

        st.session_state.lab_character = character
        st.session_state.lab_equipment = equipment
        st.session_state.lab_experiment = experiment
        st.session_state.lab_applied = True
        st.session_state.lab_running = False

        add_progress("Lab Setup")

        st.success(
            "Experiment setup applied."
        )

    if st.session_state.lab_applied:

        st.markdown(
            f"""
            <div class="lab-card">
            <b>Current Setup</b><br><br>
            👩‍🔬 Ayna →
            {PARTICIPANTS[st.session_state.lab_character]["emoji"]}
            {st.session_state.lab_character}
            →
            🔬 {st.session_state.lab_equipment}
            →
            🧠 {st.session_state.lab_experiment}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "▶️ Run Equipment / Experiment",
            use_container_width=True,
        ):

            st.session_state.lab_running = True
            add_progress("Live Lab Experiment")
            st.rerun()

    if st.session_state.lab_running:

        char = st.session_state.lab_character
        equip = st.session_state.lab_equipment
        exp = st.session_state.lab_experiment

        st.markdown("## 🔴 Live Lab")

        scene = f"""
        <style>

        body {{
            margin:0;
            background:#06111e;
            color:white;
            font-family:Arial,sans-serif;
        }}

        .scene {{
            position:relative;
            height:430px;
            border-radius:25px;
            overflow:hidden;
            background:
                radial-gradient(
                    circle at 50% 0%,
                    #244f73,
                    #06111e 65%
                );
            border:1px solid #315d7f;
        }}

        .ceiling {{
            position:absolute;
            top:20px;
            left:10%;
            right:10%;
            height:6px;
            background:#38bdf8;
            box-shadow:0 0 22px #38bdf8;
        }}

        .scientist {{
            position:absolute;
            left:8%;
            bottom:55px;
            font-size:75px;
            text-align:center;
        }}

        .subject {{
            position:absolute;
            left:42%;
            bottom:70px;
            font-size:80px;
            text-align:center;
        }}

        .machine {{
            position:absolute;
            right:7%;
            bottom:65px;
            width:190px;
            min-height:130px;
            border-radius:20px;
            background:#102c48;
            border:1px solid #4e88ad;
            padding:15px;
            text-align:center;
            box-sizing:border-box;
        }}

        .experiment {{
            position:absolute;
            top:45px;
            left:50%;
            transform:translateX(-50%);
            background:#123453;
            border:1px solid #4ba8dd;
            border-radius:999px;
            padding:14px 25px;
            font-size:20px;
            white-space:nowrap;
        }}

        .wave {{
            position:absolute;
            left:31%;
            right:29%;
            bottom:250px;
            height:3px;
            background:#38bdf8;
            box-shadow:0 0 14px #38bdf8;
            animation:pulse 1.1s infinite;
        }}

        .status {{
            position:absolute;
            bottom:18px;
            left:50%;
            transform:translateX(-50%);
            color:#9feaff;
        }}

        @keyframes pulse {{
            0% {{
                transform:scaleX(.55);
                opacity:.25;
            }}
            50% {{
                transform:scaleX(1);
                opacity:1;
            }}
            100% {{
                transform:scaleX(.55);
                opacity:.25;
            }}
        }}

        </style>

        <div class="scene">

            <div class="ceiling"></div>

            <div class="experiment">
                🧠 {exp}
            </div>

            <div class="scientist">
                👩‍🔬
                <div style="font-size:14px;">Ayna</div>
            </div>

            <div class="subject">
                {PARTICIPANTS[char]["emoji"]}
                <div style="font-size:15px;">{char}</div>
            </div>

            <div class="wave"></div>

            <div class="machine">
                <div style="font-size:38px;">🔬</div>
                <b>{equip}</b>
                <br>
                <small>{EQUIPMENT[equip]}</small>
            </div>

            <div class="status">
                ● LIVE EXPERIMENT RUNNING
            </div>

        </div>
        """

        components.html(
            scene,
            height=450,
            scrolling=False,
        )

        st.markdown("### 🎥 Lab Environment")

        if LAB_VIDEO:

            st.video(LAB_VIDEO)

        else:

            st.warning(
                "Lab video not found. Expected: "
                "cognitive_lab_brain.mp4"
            )

        st.markdown("### ⚡ Run Experimental Task")

        if exp == "Attention Gate":

            target = random.choice(
                ["X", "△", "●", "★"]
            )

            st.write(
                f"Find the target: **{target}**"
            )

            grid = [
                random.choice(
                    ["O", "Q", "0", "△", "●", "★"]
                )
                for _ in range(16)
            ]

            position = random.randrange(16)
            grid[position] = target

            st.markdown(
                f"""
                <div class="neuro-card"
                style="font-size:28px;
                letter-spacing:15px;
                text-align:center;">
                {" ".join(grid)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            answer = st.number_input(
                "Position of target",
                1,
                16,
                1,
            )

            if st.button(
                "Submit Attention Response",
                key="lab_attention",
            ):

                if answer == position + 1:

                    st.success(
                        "Correct response."
                    )

                    st.session_state.lab_result = (
                        "Attention response: correct"
                    )

                else:

                    st.error(
                        "Incorrect response."
                    )

        elif exp == "Working Memory Sprint":

            sequence = "729418"

            st.write(
                "Remember this sequence:"
            )

            st.markdown(
                f"""
                <div class="neuro-card"
                style="font-size:38px;
                text-align:center;
                letter-spacing:12px;">
                {sequence}
                </div>
                """,
                unsafe_allow_html=True,
            )

            answer = st.text_input(
                "Enter remembered sequence",
                key="lab_memory_answer",
            )

            if st.button(
                "Submit Memory Response",
                key="lab_memory",
            ):

                if answer.replace(" ", "") == sequence:

                    st.success(
                        "Correct memory response."
                    )

                    st.session_state.lab_result = (
                        "Working memory: correct"
                    )

                else:

                    st.error(
                        "Memory response incorrect."
                    )

        elif exp == "Decision Under Delay":

            choice = st.radio(
                "Choose one:",
                [
                    "Rs 1,000 today",
                    "Rs 1,500 after 30 days",
                ],
                key="lab_decision",
            )

            if st.button(
                "Record Decision",
                key="lab_decision_button",
            ):

                st.success(
                    f"Decision recorded: {choice}"
                )

                st.session_state.lab_result = (
                    f"Decision: {choice}"
                )

        elif exp == "Inhibition Challenge":

            st.write(
                "Press only when the target is **GREEN**."
            )

            colour = random.choice(
                ["GREEN", "RED"]
            )

            st.markdown(
                f"""
                <div class="neuro-card"
                style="font-size:45px;
                text-align:center;">
                {colour}
                </div>
                """,
                unsafe_allow_html=True,
            )

            press = st.button(
                "RESPONSE",
                key="inhibition_response",
            )

            if st.button(
                "Finish Inhibition Trial",
                key="inhibition_finish",
            ):

                if (
                    colour == "GREEN"
                    and press
                ) or (
                    colour == "RED"
                    and not press
                ):

                    st.success(
                        "Inhibition response recorded."
                    )

                else:

                    st.warning(
                        "Response pattern recorded."
                    )

                st.session_state.lab_result = (
                    "Inhibition trial completed."
                )

        elif exp == "Cognitive Flexibility":

            rule = random.choice(
                ["Odd / Even", "Greater / Smaller"]
            )

            number = random.randint(
                1,
                20,
            )

            st.write(
                f"Current rule: **{rule}**"
            )

            st.write(
                f"Number: **{number}**"
            )

            if rule == "Odd / Even":

                options = [
                    "Odd",
                    "Even",
                ]

                correct = (
                    "Even"
                    if number % 2 == 0
                    else "Odd"
                )

            else:

                options = [
                    "Greater than 10",
                    "10 or less",
                ]

                correct = (
                    "Greater than 10"
                    if number > 10
                    else "10 or less"
                )

            answer = st.radio(
                "Response",
                options,
                key="flex_response",
            )

            if st.button(
                "Submit Flexibility Trial",
                key="flex_submit",
            ):

                if answer == correct:

                    st.success(
                        "Correct flexible response."
                    )

                else:

                    st.error(
                        "Response incorrect."
                    )

        else:

            words = [
                "memory",
                "attention",
                "reward",
                "brain",
                "learning",
            ]

            selected_word = random.choice(words)

            st.write(
                "Remember this word:"
            )

            st.markdown(
                f"""
                <div class="neuro-card"
                style="font-size:35px;
                text-align:center;">
                {selected_word}
                </div>
                """,
                unsafe_allow_html=True,
            )

            answer = st.text_input(
                "Retrieve the word",
                key="retrieval_answer",
            )

            if st.button(
                "Submit Retrieval",
                key="retrieval_submit",
            ):

                if answer.lower().strip() == selected_word:

                    st.success(
                        "Correct retrieval."
                    )

                else:

                    st.error(
                        "Incorrect retrieval."
                    )

        st.markdown("### 🤖 Ask Ayna — Lab Guide")

        guide_language = st.radio(
            "Language",
            ["English", "Roman English"],
            horizontal=True,
            key="lab_language",
        )

        lab_question = st.text_input(
            "Ask about the current setup",
            placeholder="What does this equipment do?",
            key="lab_question",
        )

        if st.button(
            "Ask Ayna",
            key="lab_ask",
        ):

            if guide_language == "English":

                language = "Answer in clear English."

            else:

                language = (
                    "Answer in simple Roman English/Roman Urdu."
                )

            prompt = f"""
You are Ask Ayna inside a cognitive neuroscience
virtual laboratory.

Participant:
{char}

Equipment:
{equip}

Experiment:
{exp}

Equipment description:
{EQUIPMENT[equip]}

Experiment description:
{EXPERIMENTS[exp]}

User question:
{lab_question}

{language}

Guide the user step-by-step.
Explain the science simply.
Do not diagnose the participant.
"""

            st.info(
                ai_text(prompt)
            )


# ============================================================
# EXPLORE BRAIN
# ============================================================

elif st.session_state.page == "Explore Brain":

    st.markdown("## 🧠 Explore Brain")

    systems = {
        "Prefrontal Cortex": (
            "Supports planning, working memory, cognitive control "
            "and goal-directed decision-making."
        ),
        "Hippocampus": (
            "Important for memory formation, contextual processing "
            "and spatial learning."
        ),
        "Striatum": (
            "Part of the basal ganglia and involved in action "
            "selection, reward learning and movement."
        ),
        "Anterior Cingulate Cortex": (
            "Involved in conflict monitoring, error processing "
            "and cognitive control."
        ),
        "Attention Networks": (
            "Distributed systems that help select relevant "
            "information and maintain attention."
        ),
        "CSTC Circuit": (
            "Cortico-striato-thalamo-cortical loops connect cortex, "
            "striatum, basal ganglia output nuclei and thalamic "
            "regions in recurrent information-processing circuits."
        ),
    }

    selected = st.selectbox(
        "Choose brain system",
        list(systems.keys()),
    )

    st.markdown(
        f"""
        <div class="neuro-card">
        <h2>{selected}</h2>
        <p>{systems[selected]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if BRAIN_IMAGE:

        st.image(
            BRAIN_IMAGE,
            use_container_width=True,
        )


# ============================================================
# BRAIN PUZZLE
# ============================================================

elif st.session_state.page == "Brain Puzzle":

    st.markdown("## 🧩 Brain Image Puzzle")

    st.write(
        "Touch and drag each brain piece with your finger "
        "to arrange the complete image."
    )

    if not BRAIN_IMAGE:

        st.error(
            "brain.png is missing from the project."
        )

    else:

        b64 = image_base64(BRAIN_IMAGE)

        puzzle = f"""
        <style>

        body {{
            margin:0;
            background:#07111f;
            color:white;
            font-family:Arial;
        }}

        .container {{
            text-align:center;
            max-width:420px;
            margin:auto;
        }}

        .board {{
            position:relative;
            width:360px;
            height:360px;
            margin:20px auto;
            border:3px solid #38bdf8;
            border-radius:20px;
            overflow:hidden;
            touch-action:none;
            background:#0b1c30;
        }}

        .piece {{
            position:absolute;
            width:33.3333%;
            height:33.3333%;
            box-sizing:border-box;
            border:1px solid rgba(255,255,255,.45);
            background-image:url("data:image/png;base64,{b64}");
            background-size:300% 300%;
            touch-action:none;
            user-select:none;
        }}

        .drag {{
            z-index:999;
            transform:scale(1.06);
            box-shadow:0 0 25px #38bdf8;
        }}

        #done {{
            display:none;
            background:#12442e;
            color:#a7f3d0;
            border-radius:15px;
            padding:15px;
            font-weight:bold;
        }}

        </style>

        <div class="container">

        <h3>🧠 Drag the pieces</h3>

        <div class="board" id="board"></div>

        <div id="done">
        🧠 Brain puzzle completed!
        </div>

        </div>

        <script>

        const N = 3;
        const board = document.getElementById("board");
        const done = document.getElementById("done");

        let positions = [];

        for(let i=0;i<N*N;i++){{
            positions.push(i);
        }}

        function shuffle(a){{
            for(let i=a.length-1;i>0;i--){{
                let j=Math.floor(Math.random()*(i+1));
                [a[i],a[j]]=[a[j],a[i]];
            }}
            return a;
        }}

        positions = shuffle(positions);

        const pieces = [];

        function move(piece,pos){{
            const row=Math.floor(pos/N);
            const col=pos%N;

            piece.style.left=(col*100/N)+"%";
            piece.style.top=(row*100/N)+"%";
        }}

        positions.forEach((correct,pos)=>{{

            const piece=document.createElement("div");

            piece.className="piece";

            piece.dataset.correct=correct;
            piece.dataset.position=pos;

            const correctRow=Math.floor(correct/N);
            const correctCol=correct%N;

            piece.style.backgroundPosition =
                (correctCol/(N-1)*100)+"% "+
                (correctRow/(N-1)*100)+"%";

            move(piece,pos);

            board.appendChild(piece);
            pieces.push(piece);

            let sx=0;
            let sy=0;
            let startLeft=0;
            let startTop=0;

            piece.addEventListener(
                "pointerdown",
                e=>{{

                    e.preventDefault();

                    piece.classList.add("drag");

                    sx=e.clientX;
                    sy=e.clientY;

                    startLeft=parseFloat(piece.style.left);
                    startTop=parseFloat(piece.style.top);

                    piece.setPointerCapture(
                        e.pointerId
                    );
                }}
            );

            piece.addEventListener(
                "pointermove",
                e=>{{

                    if(
                        !piece.classList.contains("drag")
                    ) return;

                    const rect=
                        board.getBoundingClientRect();

                    const dx=
                        (e.clientX-sx)/
                        rect.width*100;

                    const dy=
                        (e.clientY-sy)/
                        rect.height*100;

                    piece.style.left=
                        (startLeft+dx)+"%";

                    piece.style.top=
                        (startTop+dy)+"%";
                }}
            );

            piece.addEventListener(
                "pointerup",
                e=>{{

                    piece.classList.remove("drag");

                    const rect=
                        board.getBoundingClientRect();

                    let x=e.clientX-rect.left;
                    let y=e.clientY-rect.top;

                    x=Math.max(
                        0,
                        Math.min(
                            rect.width-1,
                            x
                        )
                    );

                    y=Math.max(
                        0,
                        Math.min(
                            rect.height-1,
                            y
                        )
                    );

                    const col=
                        Math.floor(
                            x/(rect.width/N)
                        );

                    const row=
                        Math.floor(
                            y/(rect.height/N)
                        );

                    const target=
                        row*N+col;

                    const other=
                        pieces.find(
                            p=>
                            Number(
                                p.dataset.position
                            )===target
                        );

                    const old=
                        Number(
                            piece.dataset.position
                        );

                    if(
                        other &&
                        other!==piece
                    ){{

                        other.dataset.position=old;
                        piece.dataset.position=target;

                        move(other,old);
                        move(piece,target);

                    }}else{{

                        piece.dataset.position=target;

                        move(piece,target);
                    }}

                    check();
                }}
            );

        }});

        function check(){{
            let complete=true;

            pieces.forEach(p=>{{
                if(
                    Number(p.dataset.correct)!==
                    Number(p.dataset.position)
                ){{
                    complete=false;
                }}
            }});

            if(complete){{
                done.style.display="block";
            }}
        }}

        </script>
        """

        components.html(
            puzzle,
            height=450,
            scrolling=False,
        )

        if st.button(
            "✅ Record Puzzle Completion",
            use_container_width=True,
        ):

            st.session_state.puzzle_completed = True
            add_progress("Brain Puzzle")
            st.success(
                "Brain puzzle added to progress."
            )


# ============================================================
# AI MOOD & BEHAVIOUR
# ============================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.markdown(
        "## 🎙️ AI Mood & Behaviour"
    )

    st.write(
        "Start with your voice. Then add text and emoji "
        "for combined behavioural analysis."
    )

    st.markdown("### Step 1 — Voice")

    audio = st.audio_input(
        "Record your voice",
        key="behaviour_voice",
    )

    if audio:

        st.audio(audio)

        if st.button(
            "🎙️ Send Voice",
            use_container_width=True,
        ):

            prompt = """
You are an AI cognitive neuroscience assistant.

Analyse the supplied voice recording for broad
apparent emotional/mood cues.

Choose exactly ONE:

Happy
Excited
Calm
Neutral
Worried
Sad
Frustrated
Tired

Return:

MOOD: <one choice>
REASON: <one short sentence>

This is an AI-estimated apparent cue.
Do not diagnose.
Do not claim certainty about internal emotional state.
"""

            result = ai_audio(
                prompt,
                audio.getvalue(),
                audio.type or "audio/wav",
            )

            mood = "Neutral"

            mood_list = [
                "Happy",
                "Excited",
                "Calm",
                "Neutral",
                "Worried",
                "Sad",
                "Frustrated",
                "Tired",
            ]

            for m in mood_list:

                if m.lower() in result.lower():

                    mood = m
                    break

            reason = result

            if "REASON:" in result:

                reason = result.split(
                    "REASON:",
                    1,
                )[1].strip()

            st.session_state.mood = mood
            st.session_state.mood_reason = reason
            st.session_state.mood_audio = audio.getvalue()

            add_progress(
                "Voice Behaviour Analysis"
            )

    if st.session_state.mood:

        mood_icons = {
            "Happy": "😊",
            "Excited": "🤩",
            "Calm": "😌",
            "Neutral": "😐",
            "Worried": "😟",
            "Sad": "😔",
            "Frustrated": "😤",
            "Tired": "😴",
        }

        mood = st.session_state.mood

        st.markdown(
            f"""
            <div class="mood-card">

            <div class="big-emoji">
            {mood_icons[mood]}
            </div>

            <h2>{mood}</h2>

            <p>
            AI-estimated apparent mood cue
            </p>

            <p>
            {st.session_state.mood_reason}
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "### Step 2 — Text + Emoji"
    )

    text = st.text_area(
        "Your text",
        placeholder="Write what happened or how you feel...",
        key="behaviour_text",
    )

    emoji = st.selectbox(
        "Your emoji",
        [
            "😊",
            "🤩",
            "😌",
            "😐",
            "😟",
            "😔",
            "😤",
            "😴",
        ],
    )

    if st.button(
        "🧠 Send Text + Emoji",
        use_container_width=True,
    ):

        previous_voice = (
            st.session_state.mood
            if st.session_state.mood
            else "No voice estimate available."
        )

        prompt = f"""
You are Ask Ayna.

Analyse these behavioural cues:

Voice cue:
{previous_voice}

Text:
{text}

Emoji:
{emoji}

Explain briefly how these signals may relate to
emotion, arousal, attention or behaviour.

Mention that different signals can disagree.

Do not diagnose.
Do not claim certainty.
"""

        with st.spinner(
            "Ayna is analysing..."
        ):

            analysis = ai_text(prompt)

        st.session_state.behaviour_analysis = analysis

        add_progress(
            "Text + Emoji Behaviour Analysis"
        )

    if st.session_state.behaviour_analysis:

        st.markdown(
            "### 🧠 Combined Behavioural Analysis"
        )

        st.write(
            st.session_state.behaviour_analysis
        )


# ============================================================
# BRAIN EXERCISES
# ============================================================

elif st.session_state.page == "Brain Exercises":

    st.markdown(
        "## 🧠 Brain Exercises"
    )

    exercise = st.selectbox(
        "Choose exercise",
        [
            "Memory",
            "Attention",
            "Stroop",
            "Pattern",
        ],
    )

    if exercise == "Memory":

        sequence = "729418"

        st.markdown(
            f"""
            <div class="neuro-card"
            style="font-size:38px;
            text-align:center;
            letter-spacing:12px;">
            {sequence}
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.text_input(
            "Enter from memory",
        )

        if st.button(
            "Check Memory",
            key="exercise_memory",
        ):

            if answer.replace(" ", "") == sequence:

                st.success(
                    "Correct! 🧠"
                )

                add_progress("Memory Exercise")

            else:

                st.error(
                    "Try again."
                )

    elif exercise == "Attention":

        target = "X"

        chars = [
            random.choice(
                ["O", "Q", "0", "C"]
            )
            for _ in range(24)
        ]

        position = random.randrange(24)

        chars[position] = target

        st.markdown(
            f"""
            <div class="neuro-card"
            style="font-size:25px;
            letter-spacing:12px;
            text-align:center;">
            {" ".join(chars)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.number_input(
            "Position of X",
            1,
            24,
            1,
        )

        if st.button(
            "Check Attention",
            key="exercise_attention",
        ):

            if answer == position + 1:

                st.success(
                    "Correct! 👁️"
                )

                add_progress(
                    "Attention Exercise"
                )

            else:

                st.error(
                    "Try again."
                )

    elif exercise == "Stroop":

        st.markdown(
            """
            <div class="neuro-card">
            <h1>BLUE</h1>
            <p>
            Report the ink colour.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.selectbox(
            "Colour",
            [
                "Blue",
                "Red",
                "Green",
                "Yellow",
            ],
        )

        if st.button(
            "Check Stroop",
            key="exercise_stroop",
        ):

            if answer == "Blue":

                st.success(
                    "Correct!"
                )

                add_progress(
                    "Stroop Exercise"
                )

            else:

                st.error(
                    "Try again."
                )

    else:

        st.markdown(
            """
            <div class="neuro-card"
            style="text-align:center;">
            <h2>2 → 4 → 8 → 16 → ?</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.number_input(
            "Next number",
            0,
            1000,
            1,
        )

        if st.button(
            "Check Pattern",
            key="exercise_pattern",
        ):

            if answer == 32:

                st.success(
                    "Correct!"
                )

                add_progress(
                    "Pattern Exercise"
                )

            else:

                st.error(
                    "Try again."
                )


# ============================================================
# DAILY EXPERIMENT
# ============================================================

elif st.session_state.page == "Daily Cognitive Experiment":

    st.markdown(
        "## 🧪 Daily Cognitive Experiment"
    )

    st.write(
        "Study your choice between immediate and delayed reward."
    )

    choice = st.radio(
        "Choose:",
        [
            "Rs 1,000 today",
            "Rs 1,500 after 30 days",
        ],
    )

    if st.button(
        "Record My Decision",
        use_container_width=True,
    ):

        st.session_state.daily_choice = choice

        add_progress(
            "Daily Cognitive Experiment"
        )

        st.success(
            f"Decision recorded: {choice}"
        )

        st.write(
            "This demonstration explores concepts related "
            "to delay and reward-based decision-making."
        )


# ============================================================
# RESEARCH BOOK
# ============================================================

elif st.session_state.page == "Research Book":

    st.markdown(
        "## 📚 Research Book"
    )

    query = st.text_input(
        "Search biomedical literature",
        placeholder="cognitive control, attention, memory...",
    )

    if st.button(
        "🔎 Search Research",
        use_container_width=True,
    ):

        if not query.strip():

            st.warning(
                "Enter a research topic."
            )

        else:

            try:

                q = urllib.parse.quote(
                    query
                )

                url = (
                    "https://www.ebi.ac.uk/"
                    "europepmc/webservices/rest/search?"
                    f"query={q}&format=json&pageSize=10"
                )

                with urllib.request.urlopen(
                    url,
                    timeout=15,
                ) as response:

                    data = json.loads(
                        response.read().decode()
                    )

                articles = (
                    data
                    .get("resultList", {})
                    .get("result", [])
                )

                if not articles:

                    st.info(
                        "No research articles found."
                    )

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
                            f"[Open article on Europe PMC]"
                            f"(https://europepmc.org/article/MED/{pmid})"
                        )

                    st.divider()

                add_progress(
                    "Research Book Search"
                )

            except Exception as e:

                st.error(
                    f"Research search error: {e}"
                )


# ============================================================
# ASK AYNA
# ============================================================

elif st.session_state.page == "Ask Ayna":

    st.markdown(
        "## 🤖 Ask Ayna"
    )

    language = st.radio(
        "Language",
        [
            "English",
            "Roman English",
        ],
        horizontal=True,
    )

    if language == "English":

        instruction = (
            "Answer in clear and simple English."
        )

    else:

        instruction = (
            "Answer in simple Roman English/Roman Urdu. "
            "Keep important scientific terms in English."
        )

    question = st.text_area(
        "Ask Ayna",
        placeholder="Ask anything about cognition or the brain...",
    )

    if st.button(
        "Send to Ayna",
        use_container_width=True,
    ):

        if question.strip():

            prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience AI.

{instruction}

Topics:
memory
attention
learning
emotion
decision-making
reward
perception
cognitive control
brain systems
behaviour
neuroplasticity
AI and cognition

Explain accurately.
Do not diagnose.
Do not claim simple games measure actual brain activity.

Question:
{question}
"""

            answer = ai_text(prompt)

            st.session_state.ayna_chat.append(
                {
                    "q": question,
                    "a": answer,
                }
            )

            add_progress(
                "Ask Ayna"
            )

    for item in reversed(
        st.session_state.ayna_chat
    ):

        st.markdown(
            f"**You:** {item['q']}"
        )

        st.markdown(
            f"**Ayna:** {item['a']}"
        )

        st.divider()

    st.markdown(
        "### 🎙️ Ask Ayna with Voice"
    )

    voice = st.audio_input(
        "Record your question",
        key="ask_ayna_voice",
    )

    if voice:

        if st.button(
            "🎙️ Send Voice Question",
            key="ask_ayna_voice_send",
        ):

            if language == "English":

                instruction = (
                    "Answer in clear English."
                )

            else:

                instruction = (
                    "Answer in simple Roman English/Roman Urdu."
                )

            prompt = f"""
You are Ask Ayna.

Listen to the user's voice question.

{instruction}

Answer the cognitive neuroscience question
clearly and scientifically.

Do not diagnose.
"""

            answer = ai_audio(
                prompt,
                voice.getvalue(),
                voice.type or "audio/wav",
            )

            st.markdown(
                "### Ayna"
            )

            st.write(answer)

            add_progress(
                "Voice Ask Ayna"
            )


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    st.markdown(
        "## 🔐 Private Ask Ayna"
    )

    if not st.session_state.private_created:

        st.write(
            "Create a Secret Key/PIN for this session."
        )

        pin = st.text_input(
            "Create PIN",
            type="password",
        )

        confirm = st.text_input(
            "Confirm PIN",
            type="password",
        )

        if st.button(
            "Create Secret Key",
            use_container_width=True,
        ):

            if not pin:

                st.error(
                    "Enter a PIN."
                )

            elif pin != confirm:

                st.error(
                    "PINs do not match."
                )

            else:

                st.session_state.private_hash = (
                    hashlib.sha256(
                        pin.encode()
                    ).hexdigest()
                )

                st.session_state.private_created = True

                st.success(
                    "Secret Key created."
                )

    elif not st.session_state.private_unlocked:

        pin = st.text_input(
            "Enter Secret Key",
            type="password",
        )

        if st.button(
            "🔓 Unlock",
            use_container_width=True,
        ):

            entered = hashlib.sha256(
                pin.encode()
            ).hexdigest()

            if entered == st.session_state.private_hash:

                st.session_state.private_unlocked = True
                st.success(
                    "Private chat unlocked."
                )

            else:

                st.error(
                    "Incorrect Secret Key."
                )

    else:

        st.success(
            "🔓 Private Ask Ayna unlocked."
        )

        question = st.text_area(
            "Private question",
            placeholder="Ask Ayna...",
        )

        if st.button(
            "Send Private Question",
            use_container_width=True,
        ):

            if question.strip():

                prompt = f"""
You are Ask Ayna.

Answer this private educational
cognitive neuroscience question:

{question}

Be scientifically careful.
Do not diagnose.
"""

                answer = ai_text(
                    prompt
                )

                st.session_state.private_chat.append(
                    {
                        "q": question,
                        "a": answer,
                    }
                )

                add_progress(
                    "Private Ask Ayna"
                )

        for item in reversed(
            st.session_state.private_chat
        ):

            st.markdown(
                f"**You:** {item['q']}"
            )

            st.markdown(
                f"**Ayna:** {item['a']}"
            )

            st.divider()

        if st.button(
            "🔒 Lock Private Chat",
            use_container_width=True,
        ):

            st.session_state.private_unlocked = False
            st.rerun()

        st.caption(
            "The Secret Key is stored as a hash in the "
            "current session. This is not a guarantee of "
            "complete privacy."
        )


# ============================================================
# PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    st.markdown(
        "## 📊 My Progress"
    )

    progress = st.session_state.progress

    total = sum(
        progress.values()
    )

    st.metric(
        "Total Activity Points",
        total,
    )

    if not progress:

        st.info(
            "Complete NeuroLens activities to build progress."
        )

    else:

        for name, points in progress.items():

            st.write(
                f"**{name}** — {points} point(s)"
            )

        if go is not None:

            fig = go.Figure(
                data=[
                    go.Bar(
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


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NEUROLENS • Explore cognition, behaviour & the brain • "
    "Ayna Jaffri"
)
