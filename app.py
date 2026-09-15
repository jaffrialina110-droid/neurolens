import os
import random
import time
import hashlib
import base64
import html
import json
import urllib.parse
import urllib.request

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


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# PATHS / ASSETS
# =========================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset_path(name):
    p1 = os.path.join(ROOT, name)
    p2 = os.path.join(ASSETS, name)

    if os.path.exists(p1):
        return p1

    if os.path.exists(p2):
        return p2

    return None


def find_video(*names, keywords=()):
    for name in names:
        p = asset_path(name)
        if p:
            return p

    for folder in [ROOT, ASSETS]:
        if not os.path.isdir(folder):
            continue

        for filename in os.listdir(folder):
            low = filename.lower()

            if low.endswith((".mp4", ".mov", ".webm")):
                if not keywords or any(k.lower() in low for k in keywords):
                    return os.path.join(folder, filename)

    return None


BRAIN_PATH = asset_path("brain.png")

LAB_VIDEO = find_video(
    "cognitive_lab_brain.mp4",
    keywords=("lab", "cognitive")
)

REBOOT_VIDEO = find_video(
    "ayna_reboot_voiced.mp4",
    "ayna_reboot_voiced_faster_louder.mp4",
    "ayna_reboot.mp4",
    "ayna_welcome.mp4",
    keywords=("ayna", "reboot", "welcome")
)

JOURNEY_VIDEO = find_video(
    "brain_animation.mp4",
    keywords=("brain", "journey")
)


# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
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
        background: linear-gradient(135deg, #122c49, #111a32);
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

    .small {
        opacity: .78;
        font-size: .9rem;
    }

    .lab-scene {
        min-height: 390px;
        border-radius: 25px;
        position: relative;
        overflow: hidden;
        background:
        radial-gradient(circle at 50% 30%, #285b88 0%, #102c49 35%, #07111f 78%);
        border: 1px solid #45617d;
        padding: 20px;
    }

    .lab-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .scientist {
        position: absolute;
        left: 8%;
        bottom: 35px;
        font-size: 5rem;
        animation: scientistMove 2s infinite alternate ease-in-out;
    }

    .subject {
        position: absolute;
        left: 40%;
        bottom: 55px;
        font-size: 5rem;
        animation: subjectMove 1.7s infinite alternate ease-in-out;
    }

    .equipment {
        position: absolute;
        right: 12%;
        bottom: 75px;
        font-size: 4rem;
        animation: equipmentPulse 1.2s infinite;
    }

    .experiment-box {
        position: absolute;
        left: 10%;
        right: 10%;
        top: 65px;
        text-align: center;
        padding: 15px;
        border-radius: 15px;
        background: rgba(8, 20, 35, .78);
        border: 1px solid #527795;
    }

    .signal-line {
        position: absolute;
        left: 20%;
        right: 20%;
        bottom: 150px;
        height: 3px;
        background: #67c8ff;
        opacity: .7;
        animation: signal 1.2s linear infinite;
    }

    @keyframes scientistMove {
        from { transform: translateY(0); }
        to { transform: translateY(-8px); }
    }

    @keyframes subjectMove {
        from { transform: scale(1); }
        to { transform: scale(1.06); }
    }

    @keyframes equipmentPulse {
        50% { transform: scale(1.12); }
    }

    @keyframes signal {
        from { transform: scaleX(.2); opacity: .2; }
        to { transform: scaleX(1); opacity: 1; }
    }

    .mood-card {
        padding: 25px;
        border-radius: 20px;
        background: #102942;
        border: 1px solid #45617d;
        text-align: center;
    }

    .mood-emoji {
        font-size: 5rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# DATA
# =========================================================

CHARACTERS = {
    "Nova": {
        "emoji": "👩",
        "description": "Curious and fast-learning participant."
    },
    "Mira": {
        "emoji": "👩",
        "description": "Attention-focused participant."
    },
    "Ray": {
        "emoji": "👨",
        "description": "Decision and reaction participant."
    },
    "Zara": {
        "emoji": "👩",
        "description": "Memory and flexibility participant."
    }
}


EQUIPMENT = {
    "EEG Scanner": {
        "emoji": "🧠",
        "description": "Educational illustration of scalp electrical activity."
    },
    "Eye Tracker": {
        "emoji": "👁️",
        "description": "Educational gaze and fixation tracking setup."
    },
    "Reaction-Time Monitor": {
        "emoji": "⏱️",
        "description": "Measures response latency in a simple task."
    },
    "Cognitive Task Screen": {
        "emoji": "🖥️",
        "description": "Runs structured cognitive tasks."
    },
    "Auditory Attention Station": {
        "emoji": "🎧",
        "description": "Educational selective-attention sound setup."
    },
    "Behaviour Observation Station": {
        "emoji": "🔎",
        "description": "Observes behavioural response patterns."
    },
    "Emotion Recognition Display": {
        "emoji": "🙂",
        "description": "Uses predefined educational emotional cues."
    }
}


EXPERIMENTS = {
    "Attention Gate": {
        "domain": "Attention",
        "instruction": "Find how many X characters appear in the sequence.",
        "stimulus": "A  X  K  M  X  T  P  X  R  B  X  Q",
        "answer": "4"
    },

    "Working Memory Sprint": {
        "domain": "Working Memory",
        "instruction": "Memorize the sequence and reproduce it.",
        "stimulus": "7 2 9 4 1 8",
        "answer": "729418"
    },

    "Decision Under Delay": {
        "domain": "Decision Making",
        "instruction": "Choose between an immediate and delayed reward.",
        "stimulus": "A: Rs. 1,000 today   |   B: Rs. 1,500 after 30 days",
        "answer": None
    },

    "Inhibition Challenge": {
        "domain": "Inhibitory Control",
        "instruction": "Select the displayed target.",
        "stimulus": None,
        "answer": None
    },

    "Cognitive Flexibility": {
        "domain": "Cognitive Flexibility",
        "instruction": "Continue the alternating pattern.",
        "stimulus": "Circle → Square → Circle → Square → ?",
        "answer": "Circle"
    },

    "Memory Retrieval": {
        "domain": "Memory",
        "instruction": "Recall which target number was present.",
        "stimulus": "3 8 1 6 4 9",
        "answer": "6"
    }
}


BRAIN_INFO = {
    "Prefrontal Cortex": (
        "Supports planning, working memory, cognitive control and goal-directed behaviour.",
        "Planning, decision-making and inhibition."
    ),
    "Hippocampus": (
        "Important for episodic memory formation and spatial representation.",
        "Learning, memory and navigation."
    ),
    "Amygdala": (
        "Processes emotionally significant information and contributes to emotional learning.",
        "Threat processing, salience and emotional learning."
    ),
    "Striatum": (
        "Contributes to action selection, reward learning and habits.",
        "Reward learning, action selection and habits."
    ),
    "Anterior Cingulate Cortex": (
        "Contributes to performance monitoring, conflict processing and cognitive control.",
        "Conflict, error processing and effort-related control."
    ),
    "Cerebellum": (
        "Supports coordination, timing and motor learning and also contributes to cognition.",
        "Timing, balance, coordination and motor learning."
    )
}


MOODS = {
    "Happy": "😊",
    "Excited": "🤩",
    "Calm": "😌",
    "Neutral": "😐",
    "Worried": "😟",
    "Sad": "😔",
    "Frustrated": "😤",
    "Tired": "😴"
}


# =========================================================
# SESSION STATE
# =========================================================

def fresh_progress():
    return {
        "experiments": 0,
        "puzzles": 0,
        "games": 0,
        "research": 0,
        "streak": 1
    }


defaults = {
    "page": "Welcome Reboot",
    "language": "English",
    "character": "Nova",
    "equipment": "EEG Scanner",
    "experiment": "Attention Gate",
    "lab_started": False,
    "lab_result": None,
    "lab_start_time": None,
    "messages": [],
    "private_messages": [],
    "private_pin_hash": None,
    "private_unlocked": False,
    "progress": fresh_progress(),
    "ai_requests": 0,
    "ai_cache": {},
    "research_results": [],
    "journey_region": "Prefrontal Cortex"
}


for key, value in defaults.items():

    if key not in st.session_state:

        if isinstance(value, dict):
            st.session_state[key] = value.copy()

        elif isinstance(value, list):
            st.session_state[key] = value.copy()

        else:
            st.session_state[key] = value


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
    "My Progress"
]


# =========================================================
# BRAIN IMAGE
# =========================================================

@st.cache_data(show_spinner=False)
def load_brain():

    try:

        if BRAIN_PATH and os.path.exists(BRAIN_PATH):
            return Image.open(BRAIN_PATH).convert("RGB")

    except Exception:
        pass

    return None


brain = load_brain()


# =========================================================
# GEMINI
# =========================================================

def get_api_key():

    for name in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:

        try:
            value = st.secrets.get(name)

            if value:
                return str(value).strip()

        except Exception:
            pass

        value = os.getenv(name)

        if value:
            return value.strip()

    return None


@st.cache_resource(show_spinner=False)
def get_client(api_key):

    if genai is None or not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)

    except Exception:
        return None


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


AI_LIMIT = 140


def ask_ai(prompt, context=""):

    key = hashlib.sha256(
        (prompt + context).encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()

    if key in st.session_state.ai_cache:
        return st.session_state.ai_cache[key], "cache"

    if st.session_state.ai_requests >= AI_LIMIT:
        return (
            "AI session limit reached. Local NEUROLENS activities are still available.",
            "limit"
        )

    client = get_client(get_api_key())

    if client is None:
        return (
            "Ask Ayna is unavailable. Please add GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    system_prompt = f"""
You are Ayna, the educational cognitive neuroscience assistant inside NEUROLENS.

Rules:
- Be scientifically cautious.
- Never diagnose.
- Never claim a simple game measures brain activity.
- Never claim voice can reveal someone's exact internal mental state.
- Clearly distinguish AI-estimated cues from measurements.
- Answer in the requested language.
- If language is Roman English, use simple Roman Urdu/English.
- Keep answers useful and concise.

Current context:
{context[-5000:]}

User request:
{prompt}
"""

    try:

        st.session_state.ai_requests += 1

        if types:

            config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=500
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=system_prompt,
                config=config
            )

        else:

            response = client.models.generate_content(
                model=MODEL,
                contents=system_prompt
            )

        text = (
            getattr(response, "text", None)
            or "Ayna returned no text."
        ).strip()

        st.session_state.ai_cache[key] = text

        return text, "ai"

    except Exception:

        return (
            "Ayna could not complete that request right now.",
            "error"
        )


def ask_ai_audio(audio, prompt):

    client = get_client(get_api_key())

    if client is None:
        return (
            "Voice AI needs GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    if types is None:
        return (
            "Voice processing is unavailable in this environment.",
            "offline"
        )

    if st.session_state.ai_requests >= AI_LIMIT:
        return "AI session limit reached.", "limit"

    try:

        st.session_state.ai_requests += 1

        part = types.Part.from_bytes(
            data=audio.getvalue(),
            mime_type=audio.type or "audio/wav"
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=[part, prompt]
        )

        text = (
            getattr(response, "text", None)
            or "No voice result returned."
        ).strip()

        return text, "ai"

    except Exception:

        return (
            "Ayna could not process the voice recording right now.",
            "error"
        )


# =========================================================
# HELPERS
# =========================================================

def go_to(page):

    st.session_state.page = page
    st.rerun()


def record(name):

    st.session_state.progress[name] = (
        st.session_state.progress.get(name, 0) + 1
    )


def speak_button(text, key, language="en-US"):

    safe = html.escape(str(text)).replace("`", "\\`")

    components.html(
        f"""
        <button
            onclick="speak()"
            style="
                padding:9px 15px;
                border-radius:10px;
                border:1px solid #789;
                background:#173b5f;
                color:white;
                cursor:pointer;
            ">
            🔊 Play Ayna
        </button>

        <script>

        function speak() {{

            window.speechSynthesis.cancel();

            let u = new SpeechSynthesisUtterance(
                `{safe}`
            );

            u.lang = "{language}";
            u.rate = .92;
            u.pitch = 1.03;

            window.speechSynthesis.speak(u);
        }}

        </script>
        """,
        height=55
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    language = st.radio(
        "Ayna language",
        ["English", "Roman English"],
        index=(
            0
            if st.session_state.language == "English"
            else 1
        )
    )

    st.session_state.language = language

    st.divider()

    for i, page in enumerate(PAGES):

        label = (
            "● " if page == st.session_state.page
            else "○ "
        ) + page

        if st.button(
            label,
            key=f"navigation_{i}",
            use_container_width=True
        ):

            go_to(page)

    st.divider()

    st.caption(
        f"AI requests: "
        f"{st.session_state.ai_requests}/{AI_LIMIT}"
    )

    st.progress(
        min(
            st.session_state.ai_requests / AI_LIMIT,
            1.0
        )
    )


# =========================================================
# HEADER
# =========================================================

if st.session_state.page != "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">

        <h1>🧠 NEUROLENS</h1>

        <p>
        Explore cognition, behaviour & the brain
        </p>

        <small>
        Interactive Cognitive Neuroscience Lab
        • Created by Ayna Jaffri
        </small>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# WELCOME
# =========================================================

if st.session_state.page == "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">

        <h1>🧠 NEUROLENS</h1>

        <p>Welcome Reboot</p>

        <small>
        Initializing Ayna Cognitive Neuroscience System...
        </small>

        </div>
        """,
        unsafe_allow_html=True
    )

    if REBOOT_VIDEO:

        try:

            with open(REBOOT_VIDEO, "rb") as f:
                st.video(
                    f.read(),
                    format="video/mp4"
                )

        except Exception:

            st.video(REBOOT_VIDEO)

    elif brain:

        st.image(
            brain,
            use_container_width=True
        )

    else:

        st.markdown(
            """
            <div class="lab-scene">
            <div class="lab-title">
            AYNA • NEUROSCIENCE LAB
            </div>
            🧠
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.session_state.language == "Roman English":

        welcome = (
            "Welcome to NeuroLens! Main Ayna hoon, "
            "aap ki cognitive neuroscience lab assistant. "
            "Hum brain, behaviour aur cognition explore karenge."
        )

    else:

        welcome = (
            "Welcome to NeuroLens! I'm Ayna, "
            "your cognitive neuroscience lab assistant. "
            "Let's explore the brain, behaviour, and cognition together."
        )

    st.markdown("### 🤖 Ayna")

    st.write(welcome)

    speak_button(
        welcome,
        "welcome_voice"
    )

    if st.button(
        "🚀 Enter NeuroLens Lab",
        type="primary",
        use_container_width=True
    ):

        go_to("Lab")


# =========================================================
# LAB
# =========================================================

elif st.session_state.page == "Lab":

    st.subheader("🔬 Interactive Cognitive Neuroscience Lab")

    st.caption(
        "You are the scientist. Choose a subject, equipment "
        "and experiment, then run the live simulation."
    )

    left, right = st.columns(
        [1.15, 1]
    )

    # -----------------------------------------------------
    # LEFT
    # -----------------------------------------------------

    with left:

        st.markdown("### 👩‍🔬 Scientist Setup")

        character = st.selectbox(
            "👤 Select lab subject",
            list(CHARACTERS.keys()),
            index=list(CHARACTERS.keys()).index(
                st.session_state.character
            ),
            key="selected_character"
        )

        equipment = st.selectbox(
            "🧪 Select equipment",
            list(EQUIPMENT.keys()),
            index=list(EQUIPMENT.keys()).index(
                st.session_state.equipment
            ),
            key="selected_equipment"
        )

        experiment = st.selectbox(
            "🧠 Select experiment",
            list(EXPERIMENTS.keys()),
            index=list(EXPERIMENTS.keys()).index(
                st.session_state.experiment
            ),
            key="selected_experiment"
        )

        st.session_state.character = character
        st.session_state.equipment = equipment
        st.session_state.experiment = experiment

        st.info(
            EQUIPMENT[equipment]["description"]
        )

        # Dynamic setup
        char_emoji = CHARACTERS[character]["emoji"]
        equip_emoji = EQUIPMENT[equipment]["emoji"]
        exp_domain = EXPERIMENTS[experiment]["domain"]

        st.markdown(
            f"""
            <div class="lab-scene">

                <div class="lab-title">
                🔬 LIVE NEUROLENS LAB
                </div>

                <div class="experiment-box">

                    <b>
                    🧠 {experiment}
                    </b>

                    <br>

                    <span class="small">
                    Domain: {exp_domain}
                    </span>

                </div>

                <div class="signal-line"></div>

                <div class="scientist">
                👩‍🔬
                </div>

                <div class="subject">
                {char_emoji}
                </div>

                <div class="equipment">
                {equip_emoji}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            f"👩‍🔬 Scientist → {char_emoji} {character} "
            f"→ {equip_emoji} {equipment} "
            f"→ 🧠 {experiment}"
        )

        if LAB_VIDEO:

            st.markdown("### 🎥 Lab environment")

            try:

                with open(LAB_VIDEO, "rb") as f:
                    st.video(
                        f.read(),
                        format="video/mp4"
                    )

            except Exception:

                st.video(LAB_VIDEO)

            st.caption(
                "The video is the laboratory environment. "
                "The live overlay above dynamically reflects "
                "your selected subject, equipment and experiment."
            )

    # -----------------------------------------------------
    # RIGHT
    # -----------------------------------------------------

    with right:

        st.markdown("### 🤖 Ask Ayna")

        lab_language = st.radio(
            "Ayna response language",
            ["English", "Roman English"],
            horizontal=True,
            key="lab_language"
        )

        if lab_language == "Roman English":

            guide = (
                f"Ab hum {character} ke saath "
                f"{equipment} use kar ke "
                f"{experiment} perform karenge."
            )

        else:

            guide = (
                f"We will now perform {experiment} "
                f"with {character} using the {equipment}."
            )

        st.info(guide)

        speak_button(
            guide,
            "lab_guide_voice"
        )

        st.markdown("### ▶️ Experiment control")

        if not st.session_state.lab_started:

            if st.button(
                "▶️ Start Live Experiment",
                type="primary",
                use_container_width=True,
                key="start_live_experiment"
            ):

                st.session_state.lab_started = True
                st.session_state.lab_result = None
                st.session_state.lab_start_time = time.time()

                st.rerun()

        else:

            current = EXPERIMENTS[experiment]

            st.success(
                f"🔬 {character} is performing "
                f"{experiment}."
            )

            st.markdown(
                f"### {current['instruction']}"
            )

            # ---------------- Attention
            if experiment == "Attention Gate":

                st.write(
                    current["stimulus"]
                )

                response = st.text_input(
                    "How many X characters?",
                    key="live_attention"
                )

                correct = response.strip() == "4"

            # ---------------- Memory
            elif experiment == "Working Memory Sprint":

                st.info(
                    "Memorize: "
                    + current["stimulus"]
                )

                response = st.text_input(
                    "Enter the sequence",
                    key="live_memory"
                )

                correct = (
                    response
                    .replace(" ", "")
                    == "729418"
                )

            # ---------------- Decision
            elif experiment == "Decision Under Delay":

                st.write(
                    current["stimulus"]
                )

                response = st.radio(
                    "Choose your option",
                    ["A", "B"],
                    horizontal=True,
                    key="live_decision"
                )

                correct = True

            # ---------------- Inhibition
            elif experiment == "Inhibition Challenge":

                target = st.session_state.get(
                    "inhibition_target"
                )

                if not target:

                    target = random.choice(
                        ["RED", "BLUE", "GREEN"]
                    )

                    st.session_state.inhibition_target = target

                st.markdown(
                    f"### Target: {target}"
                )

                response = st.selectbox(
                    "Your response",
                    ["RED", "BLUE", "GREEN"],
                    key="live_inhibition"
                )

                correct = response == target

            # ---------------- Flexibility
            elif experiment == "Cognitive Flexibility":

                st.write(
                    current["stimulus"]
                )

                response = st.radio(
                    "Next item",
                    ["Circle", "Square"],
                    horizontal=True,
                    key="live_flexibility"
                )

                correct = response == "Circle"

            # ---------------- Retrieval
            else:

                st.info(
                    "Recall: "
                    + current["stimulus"]
                )

                response = st.text_input(
                    "Enter the target number",
                    key="live_retrieval"
                )

                correct = response.strip() == "6"

            if st.button(
                "✅ Submit Experiment",
                use_container_width=True,
                key="submit_live_experiment"
            ):

                elapsed = round(
                    time.time()
                    - st.session_state.lab_start_time,
                    2
                )

                result = {
                    "character": character,
                    "equipment": equipment,
                    "experiment": experiment,
                    "domain": current["domain"],
                    "correct": bool(correct),
                    "reaction_time": elapsed
                }

                st.session_state.lab_result = result

                record("experiments")
                record("games")

                if correct:

                    st.success(
                        f"🎉 Correct! Response time: "
                        f"{elapsed}s"
                    )

                else:

                    st.warning(
                        "Not quite. Treat this as practice, "
                        "not a diagnostic result."
                    )

            result = st.session_state.lab_result

            if result:

                st.markdown("### 🧠 Ayna Analysis")

                if result["correct"]:

                    analysis = (
                        f"{result['character']} completed "
                        f"{result['experiment']} correctly "
                        f"in {result['reaction_time']} seconds. "
                        "This is an educational performance result, "
                        "not a direct measurement of brain activity."
                    )

                else:

                    analysis = (
                        f"The response did not match the expected "
                        f"task answer. Performance can vary with "
                        "attention, instructions, practice and context. "
                        "This activity is not a diagnosis."
                    )

                st.write(analysis)

                speak_button(
                    analysis,
                    "lab_analysis_voice"
                )

                st.markdown("### 🔁 Follow-up")

                st.write(
                    "Repeat the experiment and try to improve "
                    "accuracy or response time."
                )

                if st.button(
                    "🔄 New Trial",
                    use_container_width=True,
                    key="new_lab_trial"
                ):

                    st.session_state.lab_started = False
                    st.session_state.lab_result = None
                    st.session_state.inhibition_target = None

                    st.rerun()

        st.divider()

        st.markdown("### 💬 Ask Ayna about this experiment")

        lab_question = st.text_input(
            "Question",
            placeholder="Ask about equipment, task, result or brain system...",
            key="lab_question"
        )

        if st.button(
            "🤖 Ask Ayna",
            key="lab_ask"
        ) and lab_question:

            context = (
                f"Character: {character}\n"
                f"Equipment: {equipment}\n"
                f"Experiment: {experiment}\n"
                f"Domain: {exp_domain}"
            )

            answer, source = ask_ai(
                lab_question,
                context
            )

            st.write(answer)
            st.caption(source)

            speak_button(
                answer,
                "lab_question_answer"
            )

    st.divider()

    st.caption(
        "Educational cognitive simulation. "
        "Validated research requires predefined protocols, "
        "appropriate consent, ethics review where applicable, "
        "and validated measurements."
    )


# =========================================================
# EXPLORE BRAIN
# =========================================================

elif st.session_state.page == "Explore Brain":

    st.subheader("🧠 Explore the Brain")

    region = st.selectbox(
        "Choose a brain region",
        list(BRAIN_INFO.keys()),
        index=list(BRAIN_INFO.keys()).index(
            st.session_state.journey_region
        ),
        key="brain_region_select"
    )

    st.session_state.journey_region = region

    left, right = st.columns(2)

    with left:

        if JOURNEY_VIDEO:

            st.video(JOURNEY_VIDEO)

        elif brain:

            st.image(
                brain,
                use_container_width=True
            )

        st.markdown(
            f"## 🔬 {region}"
        )

        st.info(
            BRAIN_INFO[region][0]
        )

        st.write(
            "**Behavioural relevance:**",
            BRAIN_INFO[region][1]
        )

    with right:

        st.markdown("## 🔗 Circuit context")

        st.code(
            f"{region} → distributed neural networks → cognition & behaviour"
        )

        components.html(
            """
            <div style="
                height:230px;
                border-radius:20px;
                background:radial-gradient(circle,#285b88,#081321);
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:3rem;
                color:white;
            ">
            🧠 → ⚙️ → 🔵 → 🧠
            </div>
            """,
            height=240
        )

        explanation = (
            f"Welcome inside the {region}. "
            "Complex cognition and behaviour emerge from "
            "interacting distributed neural systems."
        )

        st.write(explanation)

        speak_button(
            explanation,
            "brain_region_voice"
        )


# =========================================================
# BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    st.subheader("🧩 Brain Picture Puzzle")

    st.caption(
        "Use your finger or mouse to pick up a brain piece "
        "and drag it onto the correct position."
    )

    if not brain:

        st.error(
            "brain.png is required for the picture puzzle."
        )

    else:

        difficulty = st.select_slider(
            "Difficulty",
            ["3 × 3", "4 × 4", "5 × 5"],
            value="3 × 3",
            key="puzzle_difficulty"
        )

        N = int(difficulty[0])

        buffer = base64.b64encode(
            brain_to_bytes(brain)
        ).decode()

        puzzle_html = f"""
        <div style="
            font-family:Arial;
            color:white;
            max-width:900px;
            margin:auto;
        ">

        <button id="newPuzzle"
            style="
            padding:10px 18px;
            border-radius:10px;
            border:1px solid #789;
            background:#173b5f;
            color:white;
            margin-bottom:10px;
            ">
            🔀 New Puzzle
        </button>

        <div id="stats"></div>

        <div id="board"></div>

        <div id="complete"
            style="
            text-align:center;
            font-size:22px;
            margin-top:15px;
            ">
        </div>

        </div>

        <style>

        #board {{
            display:grid;
            grid-template-columns:repeat({N},1fr);
            gap:7px;
            max-width:720px;
            margin:auto;
        }}

        .slot {{
            aspect-ratio:1;
            border:2px dashed #789;
            border-radius:10px;
            overflow:hidden;
            background:#102235;
        }}

        .piece {{
            width:100%;
            height:100%;
            background-image:url(data:image/png;base64,{buffer});
            background-size:{N*100}% {N*100}%;
            border-radius:8px;
            cursor:grab;
            touch-action:none;
            user-select:none;
        }}

        .piece.dragging {{
            opacity:.65;
            transform:scale(.96);
        }}

        .correct {{
            outline:3px solid #5bc58a;
            cursor:default;
        }}

        .ghost {{
            position:fixed;
            pointer-events:none;
            z-index:9999;
            opacity:.85;
            width:100px;
            height:100px;
            border-radius:10px;
        }}

        </style>

        <script>

        (() => {{

            const N = {N};
            const total = N * N;

            const board =
                document.getElementById("board");

            const stats =
                document.getElementById("stats");

            const complete =
                document.getElementById("complete");

            const newPuzzle =
                document.getElementById("newPuzzle");

            let moves = 0;
            let startTime = Date.now();
            let dragged = null;
            let ghost = null;

            function shuffle(array) {{

                for (
                    let i = array.length - 1;
                    i > 0;
                    i--
                ) {{

                    const j =
                        Math.floor(
                            Math.random() * (i + 1)
                        );

                    [
                        array[i],
                        array[j]
                    ] = [
                        array[j],
                        array[i]
                    ];
                }}

            }}

            function update() {{

                const correct =
                    document.querySelectorAll(
                        ".piece.correct"
                    ).length;

                const seconds =
                    Math.floor(
                        (Date.now() - startTime) / 1000
                    );

                stats.innerHTML =
                    "Moves: " + moves +
                    " • Correct: " +
                    correct + "/" + total +
                    " • Time: " +
                    seconds + "s";

                if (correct === total) {{

                    complete.innerHTML =
                        "🎉 Brain puzzle solved!";

                }}

            }}

            function markCorrect() {{

                document
                    .querySelectorAll(".piece")
                    .forEach(piece => {{

                        const slot =
                            piece.parentElement;

                        const correct =
                            Number(piece.dataset.id)
                            ===
                            Number(slot.dataset.slot);

                        piece.classList.toggle(
                            "correct",
                            correct
                        );

                    }});

                update();

            }}

            function moveGhost(event) {{

                if (!ghost) return;

                ghost.style.left =
                    (event.clientX - 50) + "px";

                ghost.style.top =
                    (event.clientY - 50) + "px";

            }}

            function removeGhost() {{

                if (ghost) {{

                    ghost.remove();
                    ghost = null;

                }}

            }}

            function setup() {{

                board.innerHTML = "";
                complete.innerHTML = "";

                moves = 0;
                startTime = Date.now();

                const pieces =
                    [...Array(total).keys()];

                shuffle(pieces);

                pieces.forEach(id => {{

                    const slot =
                        document.createElement("div");

                    slot.className = "slot";
                    slot.dataset.slot = id;

                    const piece =
                        document.createElement("div");

                    piece.className = "piece";
                    piece.dataset.id = id;

                    const row =
                        Math.floor(id / N);

                    const col =
                        id % N;

                    const x =
                        N === 1
                        ? 0
                        : (col / (N - 1)) * 100;

                    const y =
                        N === 1
                        ? 0
                        : (row / (N - 1)) * 100;

                    piece.style.backgroundPosition =
                        x + "% " + y + "%";

                    piece.addEventListener(
                        "pointerdown",
                        event => {{

                            if (
                                piece.classList.contains(
                                    "correct"
                                )
                            ) return;

                            dragged = piece;

                            piece.classList.add(
                                "dragging"
                            );

                            ghost =
                                piece.cloneNode(true);

                            ghost.className =
                                "ghost";

                            document.body.appendChild(
                                ghost
                            );

                            moveGhost(event);

                            piece.setPointerCapture(
                                event.pointerId
                            );

                        }}
                    );

                    piece.addEventListener(
                        "pointermove",
                        event => {{

                            if (
                                dragged === piece
                            ) {{

                                moveGhost(event);

                            }}

                        }}
                    );

                    piece.addEventListener(
                        "pointerup",
                        event => {{

                            if (
                                dragged !== piece
                            ) return;

                            const target =
                                document
                                .elementFromPoint(
                                    event.clientX,
                                    event.clientY
                                )
                                ?.closest(".slot");

                            if (target) {{

                                const oldParent =
                                    piece.parentElement;

                                const other =
                                    target.querySelector(
                                        ".piece"
                                    );

                                if (
                                    other &&
                                    other !== piece
                                ) {{

                                    oldParent.appendChild(
                                        other
                                    );

                                }}

                                target.appendChild(
                                    piece
                                );

                                moves++;

                            }}

                            piece.classList.remove(
                                "dragging"
                            );

                            dragged = null;

                            removeGhost();

                            markCorrect();

                        }}
                    );

                    slot.appendChild(piece);
                    board.appendChild(slot);

                }});

                update();

            }}

            newPuzzle.onclick = setup;

            setInterval(
                update,
                1000
            );

            setup();

        }})();

        </script>
        """

        components.html(
            puzzle_html,
            height=760
        )

        if st.button(
            "✅ Record Puzzle Completion",
            use_container_width=True,
            key="record_picture_puzzle"
        ):

            record("puzzles")

            st.success(
                "Puzzle activity recorded."
            )


# =========================================================
# HELPER FOR PUZZLE
# =========================================================

def brain_to_bytes(image):

    from io import BytesIO

    b = BytesIO()

    image.save(
        b,
        format="PNG"
    )

    return b.getvalue()


# =========================================================
# MOOD & BEHAVIOUR
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.subheader("🎯 AI Mood & Behaviour")

    st.write(
        "Voice comes first. Ayna gives a broad AI-estimated "
        "mood cue, then you can add text and an emoji for "
        "a combined educational analysis."
    )

    # -----------------------------------------------------
    # VOICE FIRST
    # -----------------------------------------------------

    st.markdown("### 1️⃣ Record your voice")

    try:

        audio = st.audio_input(
            "🎙️ Record your voice",
            key="mood_voice_input"
        )

    except Exception:

        audio = None

        st.info(
            "Voice recording is unavailable in this browser. "
            "You can still use text."
        )

    if st.button(
        "🎙️ Send Voice to Ayna",
        use_container_width=True,
        key="send_mood_voice"
    ) and audio:

        prompt = f"""
Analyze the apparent conversational affect in this voice.

Choose exactly one broad mood from:
Happy, Excited, Calm, Neutral, Worried, Sad, Frustrated, Tired.

Return JSON only:

{{
  "mood": "...",
  "emoji": "...",
  "confidence": "Low/Medium/High",
  "cue": "...",
  "explanation": "..."
}}

Important:
This is only an AI-estimated conversational cue.
Do not diagnose.
Do not claim certainty about the person's internal state.
"""

        answer, source = ask_ai_audio(
            audio,
            prompt
        )

        st.session_state.mood_voice_result = answer

    voice_result = st.session_state.get(
        "mood_voice_result"
    )

    if voice_result:

        st.markdown("### 🧠 Ayna's apparent mood cue")

        mood_found = None

        try:

            cleaned = voice_result.strip()

            if cleaned.startswith("```"):
                cleaned = (
                    cleaned
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

            parsed = json.loads(cleaned)

            mood_found = parsed.get("mood")
            emoji_found = parsed.get(
                "emoji",
                MOODS.get(
                    mood_found,
                    "😐"
                )
            )

            confidence = parsed.get(
                "confidence",
                "Medium"
            )

            cue = parsed.get(
                "cue",
                ""
            )

            explanation = parsed.get(
                "explanation",
                ""
            )

            st.markdown(
                f"""
                <div class="mood-card">

                <div class="mood-emoji">
                {emoji_found}
                </div>

                <h2>{html.escape(str(mood_found))}</h2>

                <p>
                AI confidence: {html.escape(str(confidence))}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )

            if cue:
                st.write("**Voice cue:**", cue)

            if explanation:
                st.write(explanation)

        except Exception:

            st.info(
                voice_result
            )

    # -----------------------------------------------------
    # TEXT + EMOJI
    # -----------------------------------------------------

    st.markdown("### 2️⃣ Add text and emoji")

    text = st.text_area(
        "What would you like Ayna to know?",
        height=130,
        key="mood_text_input"
    )

    emoji_choice = st.selectbox(
        "Choose an emoji",
        [
            "😊 Happy",
            "🤩 Excited",
            "😌 Calm",
            "😐 Neutral",
            "😟 Worried",
            "😔 Sad",
            "😤 Frustrated",
            "😴 Tired"
        ],
        key="mood_emoji"
    )

    if st.button(
        "✨ Send Text + Emoji",
        use_container_width=True,
        key="send_mood_text"
    ) and text:

        combined_context = (
            f"Voice estimate: {voice_result}\n"
            f"Text: {text}\n"
            f"Emoji: {emoji_choice}"
        )

        answer, source = ask_ai(
            """
Give a combined educational analysis of the user's
voice estimate, text and selected emoji.

Do not diagnose.
Do not claim the mood is certain.
Explain that voice, text and emoji are context-dependent.
Mention one cognitive neuroscience concept relevant
to the interpretation.
""",
            combined_context
        )

        st.markdown("### 🤖 Combined Ayna Analysis")

        st.write(answer)

        st.caption(source)

        speak_button(
            answer,
            "combined_mood_voice"
        )

    st.caption(
        "Important: AI-estimated mood from voice, text or emojis "
        "is not a direct measurement of brain activity, "
        "mental state or a clinical diagnosis."
    )


# =========================================================
# BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    st.subheader("🧠 Brain Exercises")

    titles = list(EXPERIMENTS.keys())

    index = (
        time.gmtime().tm_yday - 1
    ) % len(titles)

    title = titles[index]

    current = EXPERIMENTS[title]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {current['domain']}"
    )

    if title == "Attention Gate":

        st.write(
            current["stimulus"]
        )

        response = st.text_input(
            "How many Xs?",
            key="exercise_attention"
        )

        if st.button(
            "Check",
            key="exercise_attention_check"
        ):

            if response.strip() == "4":

                st.success("🎉 Correct!")
                record("games")

            else:

                st.warning(
                    "Not quite. Try again."
                )

    elif title == "Working Memory Sprint":

        st.info(
            "Memorize: 7 2 9 4 1 8"
        )

        response = st.text_input(
            "Enter the sequence",
            key="exercise_memory"
        )

        if st.button(
            "Check",
            key="exercise_memory_check"
        ):

            if response.replace(" ", "") == "729418":

                st.success("🎉 Correct!")
                record("games")

            else:

                st.warning(
                    "Not quite."
                )

    elif title == "Decision Under Delay":

        response = st.radio(
            "Choose",
            [
                "Rs. 1,000 today",
                "Rs. 1,500 after 30 days"
            ],
            key="exercise_decision"
        )

        if st.button(
            "Submit",
            key="exercise_decision_submit"
        ):

            st.success(
                "Choice recorded. This task explores delayed-reward preference."
            )

            record("games")

    elif title == "Inhibition Challenge":

        target = random.choice(
            ["RED", "BLUE", "GREEN"]
        )

        st.markdown(
            f"### Target: {target}"
        )

        response = st.selectbox(
            "Response",
            ["RED", "BLUE", "GREEN"],
            key="exercise_inhibition"
        )

        if st.button(
            "Submit",
            key="exercise_inhibition_submit"
        ):

            if response == target:

                st.success("🎉 Correct!")
                record("games")

            else:

                st.warning("Not quite.")

    elif title == "Cognitive Flexibility":

        st.write(
            "Circle → Square → Circle → Square → ?"
        )

        response = st.radio(
            "Next item",
            ["Circle", "Square"],
            horizontal=True,
            key="exercise_flexibility"
        )

        if st.button(
            "Check",
            key="exercise_flexibility_check"
        ):

            if response == "Circle":

                st.success("🎉 Correct!")
                record("games")

            else:

                st.warning("Not quite.")

    else:

        st.info(
            "Recall: 3 8 1 6 4 9"
        )

        response = st.text_input(
            "Which target number was present?",
            key="exercise_retrieval"
        )

        if st.button(
            "Check",
            key="exercise_retrieval_check"
        ):

            if response.strip() == "6":

                st.success("🎉 Correct!")
                record("games")

            else:

                st.warning("Not quite.")

    st.info(
        "Educational practice only. "
        "A single task does not diagnose a condition "
        "or directly measure brain activity."
    )


# =========================================================
# DAILY EXPERIMENT
# =========================================================

elif st.session_state.page == "Daily Cognitive Experiment":

    st.subheader("🧪 Daily Cognitive Experiment")

    titles = list(EXPERIMENTS.keys())

    index = (
        time.gmtime().tm_yday - 1
    ) % len(titles)

    title = titles[index]

    current = EXPERIMENTS[title]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {current['domain']}"
    )

    st.write(
        current["instruction"]
    )

    if current["stimulus"]:

        st.info(
            current["stimulus"]
        )

    answer = st.text_input(
        "Your response",
        key="daily_response"
    )

    if st.button(
        "✅ Submit Daily Experiment",
        key="daily_submit"
    ):

        correct = False

        if title == "Attention Gate":
            correct = answer.strip() == "4"

        elif title == "Working Memory Sprint":
            correct = (
                answer.replace(" ", "")
                == "729418"
            )

        elif title == "Cognitive Flexibility":
            correct = (
                answer.strip().lower()
                == "circle"
            )

        elif title == "Memory Retrieval":
            correct = answer.strip() == "6"

        else:
            correct = True

        record("experiments")
        record("games")

        if correct:
            st.success("🎉 Response recorded.")
        else:
            st.warning(
                "Not quite. Treat this as practice."
            )


# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    st.subheader(
        "📖 Cognitive Neuroscience Research Book"
    )

    st.caption(
        "Search real literature through Europe PMC."
    )

    topic = st.text_input(
        "🔎 Search research papers",
        placeholder="e.g. working memory, attention, dopamine"
    )

    limit = st.selectbox(
        "Number of papers",
        [5, 10]
    )

    years = st.selectbox(
        "Date filter",
        [
            "All years",
            "Last 5 years",
            "Last 10 years"
        ]
    )

    if st.button(
        "🔍 Search Research",
        use_container_width=True
    ):

        if not topic.strip():

            st.warning(
                "Enter a research topic first."
            )

        else:

            from datetime import datetime

            query = topic.strip()

            current_year = datetime.utcnow().year

            if years == "Last 5 years":

                query += (
                    f" AND FIRST_PDATE:"
                    f"[{current_year - 5}-01-01 "
                    f"TO {current_year}-12-31]"
                )

            elif years == "Last 10 years":

                query += (
                    f" AND FIRST_PDATE:"
                    f"[{current_year - 10}-01-01 "
                    f"TO {current_year}-12-31]"
                )

            url = (
                "https://www.ebi.ac.uk/"
                "europepmc/webservices/rest/search"
                f"?query={urllib.parse.quote_plus(query)}"
                f"&format=json&pageSize={limit}"
            )

            try:

                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent":
                        "NEUROLENS Research Book"
                    }
                )

                with st.spinner(
                    "Searching Europe PMC..."
                ):

                    with urllib.request.urlopen(
                        request,
                        timeout=20
                    ) as response:

                        data = json.loads(
                            response
                            .read()
                            .decode("utf-8")
                        )

                results = (
                    data
                    .get("resultList", {})
                    .get("result", [])
                )

                st.session_state.research_results = results

                if results:

                    record("research")

                    st.success(
                        f"Found {len(results)} research records."
                    )

                else:

                    st.info(
                        "No papers matched this search."
                    )

            except Exception:

                st.error(
                    "Research search failed. Please try again."
                )

    results = st.session_state.research_results

    for i, paper in enumerate(results):

        paper_title = (
            paper.get("title")
            or "Untitled paper"
        )

        authors = (
            paper.get("authorString")
            or "Authors not listed"
        )

        journal = (
            paper.get("journalTitle")
            or ""
        )

        year = (
            paper.get("pubYear")
            or ""
        )

        abstract = (
            paper.get("abstractText")
            or ""
        )

        pmid = paper.get("pmid") or ""
        pmcid = paper.get("pmcid") or ""

        with st.expander(
            f"📄 {i + 1}. {paper_title}"
        ):

            st.write(
                "**Authors:**",
                authors
            )

            if journal:
                st.write(
                    "**Journal:**",
                    journal
                )

            if year:
                st.write(
                    "**Year:**",
                    year
                )

            if abstract:

                st.markdown(
                    "### Abstract"
                )

                st.write(
                    abstract
                )

            if pmid:

                st.link_button(
                    "🔗 View PubMed",
                    f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                )

            if pmcid:

                st.link_button(
                    "📖 View Europe PMC",
                    f"https://europepmc.org/articles/{pmcid}"
                )

            if st.button(
                "🤖 Explain with Ayna",
                key=f"paper_explain_{i}"
            ):

                prompt = f"""
Explain this real research record for an educational
cognitive neuroscience platform.

Title:
{paper_title}

Authors:
{authors}

Journal:
{journal}

Year:
{year}

Abstract:
{abstract}

Explain:
1. Research question
2. Why it matters
3. Methods if stated
4. Main findings if supported
5. Limitations
6. Relevance to cognition/neuroscience

Do not invent missing information.
"""

                answer, source = ask_ai(
                    prompt
                )

                st.markdown(
                    "### 🧠 Ayna's Explanation"
                )

                st.write(answer)

                st.caption(source)


# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    st.subheader("💬 Ask Ayna")

    language = st.radio(
        "Response language",
        ["English", "Roman English"],
        horizontal=True,
        key="ask_language"
    )

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    try:

        voice = st.audio_input(
            "🎙️ Optional voice message",
            key="ask_voice"
        )

    except Exception:

        voice = None

    if st.button(
        "🧠 Send Voice to Ayna",
        key="ask_voice_send"
    ) and voice:

        if language == "Roman English":

            prompt = (
                "Answer the user's voice request "
                "in simple Roman English."
            )

        else:

            prompt = (
                "Answer the user's voice request "
                "in English."
            )

        answer, source = ask_ai_audio(
            voice,
            prompt
        )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": "🎙️ Voice message"
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.rerun()

    question = st.chat_input(
        "Ask Ayna...",
        key="ask_text"
    )

    if question:

        context = "\n".join(
            f"{m['role']}: {m['content'][:600]}"
            for m in st.session_state.messages[-6:]
        )

        if language == "Roman English":

            question = (
                question
                + "\nRespond in simple Roman English."
            )

        else:

            question = (
                question
                + "\nRespond in English."
            )

        answer, source = ask_ai(
            question,
            context
        )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.rerun()

    if st.session_state.messages:

        last = st.session_state.messages[-1]["content"]

        speak_button(
            last,
            "ask_ayna_last_voice"
        )

        if st.button(
            "🗑️ Clear Chat",
            key="clear_ask_ayna"
        ):

            st.session_state.messages = []

            st.rerun()


# =========================================================
# PRIVATE ASK AYNA
# =========================================================

elif st.session_state.page == "Private Ask Ayna":

    st.subheader(
        "🔐 Private Ask Ayna"
    )

    st.caption(
        "Create a 4–6 digit session PIN. "
        "The raw PIN is not stored; this build uses a session hash."
    )

    if not st.session_state.private_unlocked:

        if st.session_state.private_pin_hash is None:

            st.info(
                "Create your own PIN. "
                "Do not reuse a banking or important-account PIN."
            )

            new_pin = st.text_input(
                "Create PIN",
                type="password",
                max_chars=6,
                key="private_create"
            )

            confirm_pin = st.text_input(
                "Confirm PIN",
                type="password",
                max_chars=6,
                key="private_confirm"
            )

            if st.button(
                "🔐 Create PIN",
                use_container_width=True,
                key="create_private"
            ):

                if not new_pin.isdigit():

                    st.error(
                        "PIN must contain digits only."
                    )

                elif not 4 <= len(new_pin) <= 6:

                    st.error(
                        "PIN must be 4–6 digits."
                    )

                elif new_pin != confirm_pin:

                    st.error(
                        "PINs do not match."
                    )

                else:

                    st.session_state.private_pin_hash = (
                        hashlib.sha256(
                            new_pin.encode()
                        ).hexdigest()
                    )

                    st.session_state.private_unlocked = True

                    st.rerun()

        else:

            pin = st.text_input(
                "Enter PIN",
                type="password",
                max_chars=6,
                key="private_unlock_input"
            )

            if st.button(
                "🔓 Unlock",
                use_container_width=True,
                key="private_unlock_button"
            ):

                entered = hashlib.sha256(
                    pin.encode()
                ).hexdigest()

                if (
                    entered
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
            "🔓 Private Ask Ayna unlocked for this session."
        )

        for message in st.session_state.private_messages:

            with st.chat_message(
                message["role"]
            ):

                st.markdown(
                    message["content"]
                )

        question = st.chat_input(
            "Private message to Ayna...",
            key="private_question"
        )

        if question:

            context = "\n".join(
                f"{m['role']}: {m['content'][:600]}"
                for m in st.session_state.private_messages[-6:]
            )

            answer, source = ask_ai(
                question,
                context
            )

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "content": question
                }
            )

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.rerun()

        if st.session_state.private_messages:

            speak_button(
                st.session_state.private_messages[-1]["content"],
                "private_answer_voice"
            )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "🔒 Lock",
                use_container_width=True,
                key="lock_private_chat"
            ):

                st.session_state.private_unlocked = False

                st.rerun()

        with c2:

            if st.button(
                "🗑️ Delete Session",
                use_container_width=True,
                key="delete_private_chat"
            ):

                st.session_state.private_messages = []
                st.session_state.private_pin_hash = None
                st.session_state.private_unlocked = False

                st.rerun()

        st.caption(
            "This is a session-level lock, not encrypted storage "
            "or a clinical privacy system."
        )


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.subheader("📊 My Progress")

    progress = st.session_state.progress

    columns = st.columns(5)

    metrics = [
        ("Experiments", "experiments"),
        ("Puzzles", "puzzles"),
        ("Games", "games"),
        ("Research", "research"),
        ("Streak", "streak")
    ]

    for column, (label, key) in zip(
        columns,
        metrics
    ):

        column.metric(
            label,
            progress.get(key, 0)
        )

    if go:

        fig = go.Figure(
            go.Bar(
                x=[
                    "Experiments",
                    "Puzzles",
                    "Games",
                    "Research"
                ],
                y=[
                    progress.get("experiments", 0),
                    progress.get("puzzles", 0),
                    progress.get("games", 0),
                    progress.get("research", 0)
                ]
            )
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.info(
        "Progress is session-based in this build."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education "
    "• Created by Ayna Jaffri"
)
