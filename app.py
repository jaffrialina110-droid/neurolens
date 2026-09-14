import os
import time
import random
import hashlib
import html
import streamlit as st
from streamlit import components
from pathlib import Path

import streamlit as st
from PIL import Image

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
# NEUROLENS
# Created by Ayna Jaffri
# Cognitive Neuroscience Education
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 10% 5%, #163b62 0%, transparent 28%),
        radial-gradient(circle at 90% 90%, #18275a 0%, transparent 25%),
        linear-gradient(135deg,#06101d,#0b1b2d);
}

.block-container {
    max-width: 1400px;
    padding-top: 1rem;
}

.hero {
    padding: 30px;
    border-radius: 25px;
    background: linear-gradient(135deg,#122f4f,#111a34);
    border: 1px solid #405d79;
    margin-bottom: 18px;
}

.card {
    padding: 18px;
    border-radius: 18px;
    background: #0d2035;
    border: 1px solid #294560;
    margin: 8px 0;
}

.lab-stage {
    height: 240px;
    border-radius: 24px;
    background:
        radial-gradient(circle,#214f78,#0b1b30 45%,#050c16);
    border: 1px solid #3c5e7b;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    margin: 12px 0;
}

.anim {
    font-size: 5rem;
    animation: pulse 1.3s infinite;
}

.signal {
    font-size: 3rem;
    animation: signal 1.5s linear infinite;
}

.eye {
    font-size: 5rem;
    animation: eye 2s infinite alternate;
}

.clock {
    font-size: 5rem;
    animation: pulse .7s infinite;
}

.sound {
    font-size: 4rem;
    animation: sound 1s infinite;
}

.social {
    font-size: 4rem;
    animation: pulse 1.5s infinite;
}

.brain {
    font-size: 5rem;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    50% { transform: scale(1.18); }
}

@keyframes signal {
    0% { transform: translateX(-180px); }
    100% { transform: translateX(180px); }
}

@keyframes eye {
    0% { transform: translateX(-45px); }
    100% { transform: translateX(45px); }
}

@keyframes sound {
    0% { transform: scale(.75); opacity:.45; }
    50% { transform: scale(1.2); opacity:1; }
    100% { transform: scale(.75); opacity:.45; }
}

.small {
    opacity: .78;
    font-size: .9rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# ASSETS
# ============================================================

def asset(name):
    p = ASSETS / name
    if p.exists():
        return p
    p = ROOT / name
    return p if p.exists() else None


def find_video(*names):
    for name in names:
        p = asset(name)
        if p:
            return p
    return None


BRAIN_IMAGE = asset("brain.png")

# Faster + louder version first
REBOOT_VIDEO = find_video(
    "ayna_reboot_voiced_faster_louder.mp4",
    "ayna_reboot_voiced_louder.mp4",
    "ayna_reboot_voiced.mp4"
)

LAB_VIDEO = find_video(
    "cognitive_lab_brain.mp4"
)

JOURNEY_VIDEO = find_video(
    "brain_animation.mp4"
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Welcome Reboot",
    "messages": [],
    "private_messages": [],
    "private_pin": None,
    "private_unlocked": False,
    "ai_requests": 0,
    "equipment": "EEG Scanner",
    "progress": {
        "games": 0,
        "puzzles": 0,
        "experiments": 0,
        "research": 0
    },
    "last_voice": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, dict) else value


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


# ============================================================
# SECURITY
# ============================================================

SESSION_SALT = os.urandom(16)


def clean_text(text, limit=3000):
    text = (text or "").replace("\x00", " ").strip()
    return text[:limit]


def pin_hash(pin):
    return hashlib.sha256(
        SESSION_SALT + pin.encode("utf-8")
    ).hexdigest()


def security_panel():
    with st.sidebar.expander("🔐 Security & Privacy"):
        st.caption(
            "API keys are loaded from Streamlit Secrets and are not written "
            "inside the application code."
        )
        st.caption(
            "Private Ask Ayna uses a session-level PIN lock."
        )
        st.caption(
            "Avoid entering passwords, API keys, CNIC numbers, banking "
            "information or other highly sensitive personal information."
        )
        st.caption(
            "Voice/text/emoji data is sent for AI analysis only when you "
            "press an analysis button."
        )


# ============================================================
# GEMINI
# ============================================================

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


@st.cache_resource
def get_client():
    key = get_api_key()

    if not key or genai is None:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def ask_ai(prompt, context=""):
    prompt = clean_text(prompt)
    context = clean_text(context, 5000)

    client = get_client()

    if not client:
        return (
            "Ayna AI is not connected yet. Please add GEMINI_API_KEY "
            "in Streamlit Secrets.",
            "AI unavailable"
        )

    system = """
You are Ayna, an educational cognitive neuroscience assistant.

Focus on:
memory, attention, learning, emotion, decision-making,
reward, perception, cognitive control, brain systems,
behaviour, neuroplasticity, neuroscience and AI.

Give scientifically grounded educational answers.
Do not invent research findings.
Do not make definitive clinical diagnoses.
Do not assign a definitive personality disorder or psychiatric condition
from simple behaviour, text, emoji or voice cues.

When behaviour is discussed, describe observable patterns and possible
cognitive/emotional processes as possibilities rather than certainties.

Keep answers understandable and concise.
"""

    full = f"""
{system}

Conversation context:
{context}

User:
{prompt}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full,
            config=types.GenerateContentConfig(
                max_output_tokens=650
            )
        )

        st.session_state.ai_requests += 1

        return (
            response.text if response.text else "Ayna could not generate a response.",
            "Gemini"
        )

    except Exception as e:
        return (
            "Ayna could not process that request right now.",
            f"Error: {e}"
        )


def ask_ai_voice(audio_file, instruction):
    client = get_client()

    if not client or types is None:
        return (
            "Voice AI is not connected. Add GEMINI_API_KEY in Streamlit Secrets.",
            "AI unavailable"
        )

    try:
        audio_bytes = audio_file.getvalue()

        prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

{instruction}

Analyze the submitted voice conservatively.

Focus on observable communication features such as:
speech content, apparent pace, pauses, emphasis, expressed emotion,
and communication style.

Do not diagnose a mental disorder.
Do not claim that voice alone proves a psychological condition.
Give possible cognitive/behavioural interpretations only.

Keep the answer concise.
"""

        part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=audio_file.type or "audio/wav"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, part],
            config=types.GenerateContentConfig(
                max_output_tokens=600
            )
        )

        st.session_state.ai_requests += 1

        return (
            response.text if response.text else "No response generated.",
            "Gemini voice analysis"
        )

    except Exception as e:
        return (
            "Voice analysis could not be completed.",
            f"Error: {e}"
        )


# ============================================================
# AYNА VOICE OUTPUT
# ============================================================

def speak_text(text, key):
    safe = html.escape(clean_text(text, 1800))

    components.html(
        f"""
        <button
            onclick="speechSynthesis.cancel();
            speechSynthesis.speak(
                new SpeechSynthesisUtterance(
                    {safe!r}
                )
            );"
            style="
                background:#172f4b;
                color:white;
                border:1px solid #50779b;
                border-radius:12px;
                padding:10px 18px;
                cursor:pointer;
                font-size:15px;
            ">
            🔊 Ask Ayna — Voice
        </button>
        """,
        height=55
    )


# ============================================================
# BRAIN DATA
# ============================================================

BRAIN_SYSTEMS = {
    "Prefrontal Cortex": (
        "Planning, working memory, cognitive control and goal-directed behaviour.",
        "Planning • decision-making • inhibition"
    ),
    "Hippocampus": (
        "Important for memory formation and spatial representation.",
        "Learning • memory • navigation"
    ),
    "Amygdala": (
        "Processes emotionally significant information and emotional learning.",
        "Salience • threat processing • emotional learning"
    ),
    "Striatum": (
        "Contributes to action selection, reward learning and habits.",
        "Reward • habits • action selection"
    ),
    "Anterior Cingulate Cortex": (
        "Contributes to conflict monitoring and performance control.",
        "Conflict • errors • cognitive control"
    ),
    "Cerebellum": (
        "Supports coordination, timing and motor learning and also contributes to cognition.",
        "Timing • coordination • learning"
    )
}


# ============================================================
# EQUIPMENT ANIMATIONS
# ============================================================

EQUIPMENT = {
    "EEG Scanner": {
        "emoji": "🧠",
        "title": "EEG Scanner",
        "description": "Educational simulation of scalp electrical activity measurement.",
        "animation": "signal"
    },
    "Eye Tracker": {
        "emoji": "👁️",
        "title": "Eye Tracker",
        "description": "Educational simulation of gaze position and fixation patterns.",
        "animation": "eye"
    },
    "Reaction-Time Monitor": {
        "emoji": "⏱️",
        "title": "Reaction-Time Monitor",
        "description": "Measures response latency in a simple cognitive task.",
        "animation": "clock"
    },
    "Auditory Attention Station": {
        "emoji": "🔊",
        "title": "Auditory Attention Station",
        "description": "Educational simulation of selective auditory attention.",
        "animation": "sound"
    },
    "Cognitive Task Screen": {
        "emoji": "🖥️",
        "title": "Cognitive Task Screen",
        "description": "Runs structured memory, attention and decision tasks.",
        "animation": "brain"
    },
    "Physiological Monitor": {
        "emoji": "❤️",
        "title": "Physiological Monitor",
        "description": "Educational display of non-neural physiological signals.",
        "animation": "signal"
    },
    "Behaviour Observation Station": {
        "emoji": "👀",
        "title": "Behaviour Observation Station",
        "description": "Explore observable response patterns and behaviour.",
        "animation": "eye"
    },
    "Behaviour Task Screen": {
        "emoji": "🧩",
        "title": "Behaviour Task Screen",
        "description": "Structured behavioural tasks involving attention and decisions.",
        "animation": "brain"
    },
    "Social Interaction Simulator": {
        "emoji": "🗣️",
        "title": "Social Interaction Simulator",
        "description": "Explore social cues, context and response selection.",
        "animation": "social"
    },
    "Emotion Recognition Display": {
        "emoji": "😊",
        "title": "Emotion Recognition Display",
        "description": "Explore predefined emotional cues and interpretation.",
        "animation": "pulse"
    }
}


def equipment_animation(item):
    data = EQUIPMENT[item]

    animation = data["animation"]

    if animation == "signal":
        visual = '<div class="signal">⚡〰️⚡〰️⚡</div>'
    elif animation == "eye":
        visual = '<div class="eye">👁️</div>'
    elif animation == "clock":
        visual = '<div class="clock">⏱️</div>'
    elif animation == "sound":
        visual = '<div class="sound">🔊〰️🔊</div>'
    elif animation == "social":
        visual = '<div class="social">🧑‍🤝‍🧑</div>'
    elif animation == "pulse":
        visual = '<div class="anim">😊</div>'
    else:
        visual = '<div class="brain">🧠</div>'

    st.markdown(
        f"""
        <div class="lab-stage">
            {visual}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    for page in PAGES:
        if st.button(
            page,
            key="nav_" + page,
            use_container_width=True
        ):
            st.session_state.page = page
            st.rerun()

    st.divider()

    security_panel()

    st.caption("Created by Ayna Jaffri")


# ============================================================
# WELCOME
# ============================================================

if st.session_state.page == "Welcome Reboot":

    st.markdown(
        """
        <div class="hero">
            <h1>🧠 Welcome to NeuroLens</h1>
            <h3>Explore cognition, behaviour & the brain</h3>
            <p>I'm Ayna. Let's explore the brain, behaviour and cognition together.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if REBOOT_VIDEO:
        st.video(
            REBOOT_VIDEO.read_bytes(),
            format="video/mp4"
        )
    else:
        st.warning(
            "Ayna reboot video not found. Put the video inside assets/."
        )

    if st.button(
        "🧠 Enter NeuroLens",
        use_container_width=True
    ):
        st.session_state.page = "Lab"
        st.rerun()


# ============================================================
# LAB
# ============================================================

elif st.session_state.page == "Lab":

    st.subheader("🧪 Cognitive Neuroscience Lab")

    if LAB_VIDEO:
        st.video(
            LAB_VIDEO.read_bytes(),
            format="video/mp4"
        )

    st.markdown("### 🔬 Lab Equipment")

    equipment = st.selectbox(
        "Select equipment",
        list(EQUIPMENT.keys()),
        key="equipment"
    )

    data = EQUIPMENT[equipment]

    st.markdown(
        f"""
        <div class="card">
            <h3>{data["emoji"]} {data["title"]}</h3>
            <p>{data["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        f"▶️ Watch {equipment} Animation",
        use_container_width=True,
        key="watch_" + equipment
    ):
        equipment_animation(equipment)
        st.success(
            f"{equipment} animation is running."
        )

    if st.button(
        f"🔬 Run {equipment}",
        use_container_width=True,
        key="run_" + equipment
    ):

        st.session_state.progress["experiments"] += 1

        if equipment == "Reaction-Time Monitor":

            if "rt_start" not in st.session_state:
                st.session_state.rt_start = time.time()

            st.warning("⚡ Press the button as quickly as possible.")

            if st.button(
                "🟢 RESPOND",
                key="reaction_button"
            ):
                reaction = time.time() - st.session_state.rt_start
                st.success(
                    f"Reaction time: {reaction:.3f} seconds"
                )
                st.session_state.rt_start = None

        elif equipment == "EEG Scanner":
            st.info(
                "Educational EEG simulation: neural activity would normally "
                "be represented as time-varying electrical signals."
            )

            st.markdown(
                """
                <div class="lab-stage">
                    <div class="signal">⚡〰️⚡〰️⚡〰️⚡</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        elif equipment == "Eye Tracker":
            st.info(
                "Educational eye-tracking simulation."
            )
            st.markdown(
                """
                <div class="lab-stage">
                    <div class="eye">👁️</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        elif equipment == "Auditory Attention Station":
            st.info(
                "Imagine two simultaneous sound streams. Selective attention "
                "determines which stream receives priority."
            )
            st.markdown(
                """
                <div class="lab-stage">
                    <div class="sound">🔊〰️🔊〰️🔊</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        elif equipment == "Social Interaction Simulator":
            st.info(
                "Choose the response that best matches the social context."
            )

            scenario = st.selectbox(
                "Scenario",
                [
                    "Someone asks you a question",
                    "Someone disagrees with you",
                    "Someone gives you unexpected news"
                ],
                key="social_scenario"
            )

            response = st.radio(
                "Choose response",
                [
                    "Pause and listen",
                    "Respond immediately",
                    "Ask for clarification"
                ],
                key="social_response"
            )

            if st.button(
                "🧠 Analyse Response",
                key="social_analyse"
            ):
                ans, _ = ask_ai(
                    f"""
                    Scenario: {scenario}
                    Response selected: {response}

                    Explain the cognitive processes that may be involved,
                    such as attention, inhibition, social cognition,
                    decision-making or emotion regulation.
                    """
                )
                st.write(ans)

        else:
            st.success(
                f"{equipment} simulation is ready."
            )


# ============================================================
# EXPLORE BRAIN
# ============================================================

elif st.session_state.page == "Explore Brain":

    st.subheader("🧠 Explore Brain Systems")

    if JOURNEY_VIDEO:
        st.video(
            JOURNEY_VIDEO.read_bytes(),
            format="video/mp4"
        )

    region = st.selectbox(
        "Choose brain system",
        list(BRAIN_SYSTEMS.keys())
    )

    description, functions = BRAIN_SYSTEMS[region]

    if brain:
        st.image(
            brain,
            caption=region,
            use_container_width=True
        )

    st.markdown(
        f"""
        <div class="card">
            <h2>{region}</h2>
            <p>{description}</p>
            <b>Key functions:</b> {functions}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🤖 Explain with Ayna"):
        answer, source = ask_ai(
            f"Explain the {region} for a cognitive neuroscience learner."
        )
        st.write(answer)
        st.caption(source)
        speak_text(answer, "brain_explain")


# ============================================================
# BRAIN PUZZLE
# ============================================================

elif st.session_state.page == "Brain Puzzle":

    st.subheader("🧩 Brain Puzzle")

    st.write(
        "Remember this sequence, then reproduce it."
    )

    if "puzzle_sequence" not in st.session_state:
        st.session_state.puzzle_sequence = [
            random.randint(1, 9) for _ in range(6)
        ]

    st.markdown(
        f"""
        <div class="card">
            <h2 style="text-align:center;">
            {" • ".join(map(str, st.session_state.puzzle_sequence))}
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    answer = st.text_input(
        "Enter the sequence",
        max_chars=20
    )

    if st.button(
        "🧠 Check Memory"
    ):
        target = "".join(
            map(str, st.session_state.puzzle_sequence)
        )

        st.session_state.progress["puzzles"] += 1

        if answer.replace(" ", "") == target:
            st.success("Correct! 🎉")
        else:
            st.error(
                f"Not quite. Correct sequence: {target}"
            )


# ============================================================
# AI MOOD & BEHAVIOUR
# ============================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.subheader("🧠 AI Mood & Behaviour Lab")

    st.write(
        "Explore behaviour through voice, text and emoji patterns."
    )

    tabs = st.tabs([
        "🎙️ Voice Behaviour",
        "💬 Text Behaviour",
        "😊 Emoji Behaviour",
        "🔬 Combined Behaviour"
    ])


    # ---------------- VOICE ----------------

    with tabs[0]:

        st.markdown("### 🎙️ Send Voice to Ayna")

        try:
            voice = st.audio_input(
                "Record your voice",
                key="behaviour_voice"
            )
        except Exception:
            voice = None

        if st.button(
            "📤 Send Voice to Ayna",
            key="send_behaviour_voice"
        ):

            if not voice:
                st.warning(
                    "Please record your voice first."
                )
            else:

                st.session_state.last_voice = voice

                answer, source = ask_ai_voice(
                    voice,
                    """
                    Analyze the user's communication behaviour.
                    Discuss apparent speech pace, pauses, emphasis,
                    expressed emotional tone and communication style.
                    """
                )

                st.markdown("### 🤖 Ayna — Voice Behaviour Analysis")
                st.write(answer)
                st.caption(source)

                speak_text(
                    answer,
                    "voice_behaviour_answer"
                )


        if st.session_state.last_voice:

            st.divider()

            st.markdown("### 🔊 Ask Ayna on Voice")

            if st.button(
                "🔊 Ask Ayna",
                key="voice_ask_ayna"
            ):
                answer, _ = ask_ai_voice(
                    st.session_state.last_voice,
                    """
                    Respond as Ayna after analysing the submitted voice.
                    Give a short educational explanation of the observable
                    communication and behavioural cues.
                    """
                )

                st.write(answer)

                speak_text(
                    answer,
                    "voice_ask_ayna_output"
                )


    # ---------------- TEXT ----------------

    with tabs[1]:

        st.markdown("### 💬 Text Behaviour")

        text_input = st.text_area(
            "Write something",
            max_chars=3000,
            height=160,
            key="behaviour_text"
        )

        if st.button(
            "🔍 Detect Behaviour",
            key="detect_text_behaviour"
        ):

            if not text_input.strip():
                st.warning("Write some text first.")
            else:

                answer, source = ask_ai(
                    f"""
                    Analyse this text for observable behavioural and
                    communication patterns.

                    Discuss:
                    - wording
                    - emotional expression
                    - response style
                    - attention-related cues
                    - decision-making style
                    - cognitive control cues

                    Text:
                    {clean_text(text_input)}
                    """
                )

                st.markdown("### 🧠 Behaviour Observation")
                st.write(answer)
                st.caption(source)

                speak_text(
                    answer,
                    "text_behaviour_answer"
                )


    # ---------------- EMOJI ----------------

    with tabs[2]:

        st.markdown("### 😊 Emoji Behaviour")

        emojis = st.multiselect(
            "Choose emojis",
            [
                "😀","😂","😊","😍","😐","😔",
                "😟","😤","😴","🤔","😎","😭",
                "❤️","🔥","👍","👎","🧠","✨"
            ],
            key="behaviour_emojis"
        )

        context = st.text_input(
            "Optional context",
            key="emoji_context"
        )

        if emojis:
            st.markdown(
                "### Selected pattern"
            )
            st.markdown(
                " ".join(emojis)
            )

        if st.button(
            "🧠 Detect Emoji Behaviour",
            key="detect_emoji_behaviour"
        ):

            if not emojis:
                st.warning("Select some emojis first.")
            else:

                answer, source = ask_ai(
                    f"""
                    Analyse this emoji pattern as an educational
                    behavioural communication pattern.

                    Emojis:
                    {" ".join(emojis)}

                    Context:
                    {clean_text(context,1000)}

                    Discuss possible emotional expression,
                    communication style and context dependence.
                    """
                )

                st.markdown("### 😊 Emoji Behaviour Observation")
                st.write(answer)
                st.caption(source)

                speak_text(
                    answer,
                    "emoji_behaviour_answer"
                )


    # ---------------- COMBINED ----------------

    with tabs[3]:

        st.markdown("### 🔬 Combined Behaviour")

        combined_text = st.text_area(
            "Text",
            max_chars=2500,
            key="combined_text"
        )

        combined_emojis = st.multiselect(
            "Emojis",
            [
                "😀","😂","😊","😍","😐","😔",
                "😟","😤","😴","🤔","😎","😭",
                "❤️","🔥","👍","👎","🧠","✨"
            ],
            key="combined_emojis"
        )

        try:
            combined_voice = st.audio_input(
                "Voice",
                key="combined_voice"
            )
        except Exception:
            combined_voice = None

        if st.button(
            "🔬 Analyse Combined Behaviour",
            key="analyse_combined_behaviour"
        ):

            voice_summary = (
                "Voice submitted for analysis."
                if combined_voice
                else "No voice submitted."
            )

            prompt = f"""
            Create an educational combined behavioural observation.

            Text:
            {clean_text(combined_text)}

            Emojis:
            {" ".join(combined_emojis)}

            Voice:
            {voice_summary}

            Discuss interactions among:
            communication style,
            emotional expression,
            attention,
            decision-making,
            cognitive control,
            social context.

            Keep conclusions probabilistic and context-dependent.
            """

            answer, source = ask_ai(prompt)

            st.markdown("### 🔬 Combined Behaviour Profile")
            st.write(answer)
            st.caption(source)

            speak_text(
                answer,
                "combined_behaviour_answer"
            )


# ============================================================
# BRAIN EXERCISES
# ============================================================

elif st.session_state.page == "Brain Exercises":

    st.subheader("🧠 Brain Exercises")

    game = st.selectbox(
        "Choose challenge",
        [
            "Decision Challenge",
            "Memory Challenge",
            "Attention Challenge",
            "Stroop Challenge",
            "Pattern Challenge"
        ]
    )

    if game == "Decision Challenge":

        st.write(
            "Choose between Rs 1,000 today or Rs 1,500 after 30 days."
        )

        choice = st.radio(
            "Your choice",
            [
                "Rs 1,000 today",
                "Rs 1,500 after 30 days"
            ]
        )

        if st.button("Submit Decision"):
            st.session_state.progress["games"] += 1

            if choice == "Rs 1,500 after 30 days":
                st.success(
                    "Delayed reward selected."
                )
            else:
                st.info(
                    "Immediate reward selected."
                )

    elif game == "Memory Challenge":

        sequence = "729418"

        st.info(
            f"Remember: **{sequence}**"
        )

        memory_answer = st.text_input(
            "Enter sequence",
            max_chars=10
        )

        if st.button("Check Memory"):
            st.session_state.progress["games"] += 1

            if memory_answer == sequence:
                st.success("Correct! 🎉")
            else:
                st.error("Try again.")

    elif game == "Attention Challenge":

        st.write(
            "Find the letter X:"
        )

        grid = [
            "OOOOOOOOOO",
            "OOOOOOOOOO",
            "OOOOOOXOOO",
            "OOOOOOOOOO",
            "OOOOOOOOOO"
        ]

        st.code("\n".join(grid))

        if st.button("I Found X"):
            st.session_state.progress["games"] += 1
            st.success("Attention target found.")

    elif game == "Stroop Challenge":

        st.markdown(
            """
            <div class="card">
                <h2>RED</h2>
                <p>What does the word say?</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        answer = st.radio(
            "Choose",
            ["RED", "BLUE", "GREEN"]
        )

        if st.button("Submit"):
            st.session_state.progress["games"] += 1

            if answer == "RED":
                st.success("Correct.")

    else:

        st.write(
            "2 → 4 → 8 → 16 → 32 → ?"
        )

        answer = st.number_input(
            "Next number",
            min_value=0,
            step=1
        )

        if st.button("Check Pattern"):
            st.session_state.progress["games"] += 1

            if answer == 64:
                st.success("Correct! 🎉")
            else:
                st.error("Try again.")


# ============================================================
# DAILY EXPERIMENT
# ============================================================

elif st.session_state.page == "Daily Cognitive Experiment":

    st.subheader("🧪 Daily Cognitive Experiment")

    experiment = st.selectbox(
        "Choose experiment",
        [
            "Attention Gate",
            "Working Memory Sprint",
            "Decision Under Delay",
            "Inhibition Challenge",
            "Cognitive Flexibility",
            "Memory Retrieval"
        ]
    )

    st.markdown(
        f"""
        <div class="card">
            <h2>🧪 {experiment}</h2>
            <p>Run today's short cognitive experiment.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("▶️ Start Experiment"):

        st.session_state.progress["experiments"] += 1

        if experiment == "Attention Gate":

            target = random.choice(["X", "K", "M"])

            st.write(
                f"Find **{target}** in the sequence:"
            )

            sequence = "".join(
                random.choice("XKMTAB")
                for _ in range(20)
            )

            st.code(sequence)

            ans = st.text_input("Enter position")

            if st.button("Check Position"):
                if ans.isdigit():
                    st.info(
                        "Position checking completed."
                    )

        elif experiment == "Working Memory Sprint":

            sequence = "".join(
                str(random.randint(0,9))
                for _ in range(7)
            )

            st.session_state.memory_target = sequence

            st.success(
                f"Remember: {sequence}"
            )

            if st.button("Hide Sequence"):
                st.session_state.hide_memory = True
                st.rerun()

            response = st.text_input(
                "Enter remembered sequence"
            )

            if st.button("Check"):
                if response == sequence:
                    st.success("Correct! 🎉")
                else:
                    st.error(
                        f"Correct answer: {sequence}"
                    )

        elif experiment == "Decision Under Delay":

            choice = st.radio(
                "Choose",
                [
                    "Smaller reward now",
                    "Larger reward later"
                ]
            )

            if st.button("Submit"):
                st.success(
                    f"Choice recorded: {choice}"
                )

        else:

            st.info(
                f"{experiment} simulation started."
            )

            if st.button("Finish Experiment"):
                st.success(
                    "Experiment completed."
                )


# ============================================================
# RESEARCH BOOK
# ============================================================

elif st.session_state.page == "Research Book":

    st.subheader("📚 Research Book")

    topic = st.selectbox(
        "Choose topic",
        [
            "Brain & Behaviour",
            "Memory",
            "Attention",
            "Perception",
            "Emotion",
            "Decision Making",
            "Cognitive Control",
            "Neuroplasticity"
        ]
    )

    descriptions = {
        "Brain & Behaviour":
            "Behaviour emerges from interacting brain networks, body systems and environment.",
        "Memory":
            "Memory includes encoding, consolidation and retrieval.",
        "Attention":
            "Attention changes which information receives processing priority.",
        "Perception":
            "Perception is the brain's construction of meaningful sensory representations.",
        "Emotion":
            "Emotion involves interacting brain, body and cognitive processes.",
        "Decision Making":
            "Decision-making combines goals, rewards, uncertainty and control.",
        "Cognitive Control":
            "Cognitive control helps maintain goals and adjust behaviour.",
        "Neuroplasticity":
            "The nervous system can change through development, learning and experience."
    }

    st.markdown(
        f"""
        <div class="card">
            <h2>{topic}</h2>
            <p>{descriptions[topic]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    search = st.text_input(
        "Search Europe PMC",
        value=topic
    )

    if st.button("🔎 Search Research"):

        import urllib.parse
        import urllib.request
        import json

        query = urllib.parse.quote(
            clean_text(search, 200)
        )

        url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            f"?query={query}&format=json&pageSize=10"
        )

        try:

            with st.spinner("Searching Europe PMC..."):

                with urllib.request.urlopen(
                    url,
                    timeout=20
                ) as response:

                    data = json.loads(
                        response.read().decode("utf-8")
                    )

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
                    "Authors not listed"
                )

                year = paper.get(
                    "pubYear",
                    ""
                )

                pmid = paper.get(
                    "pmid",
                    ""
                )

                abstract = paper.get(
                    "abstractText",
                    ""
                )

                with st.expander(
                    f"📄 {title}"
                ):

                    st.write(
                        f"**Authors:** {authors}"
                    )

                    st.write(
                        f"**Year:** {year}"
                    )

                    if abstract:
                        st.write(
                            abstract
                        )

                    if pmid:
                        st.link_button(
                            "🔗 PubMed",
                            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        )

        except Exception as e:

            st.error(
                "Research search failed."
            )

            st.caption(
                str(e)
            )


# ============================================================
# ASK AYNA
# ============================================================

elif st.session_state.page == "Ask Ayna":

    st.subheader("💬 Ask Ayna")

    st.caption(
        "Ask questions about cognition, neuroscience, behaviour and the brain."
    )

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):
            st.write(
                message["content"]
            )

    try:

        voice = st.audio_input(
            "🎙️ Optional voice message",
            key="ask_ayna_voice"
        )

    except Exception:

        voice = None

    if st.button(
        "📤 Send Voice to Ayna",
        key="ask_ayna_voice_button"
    ):

        if voice:

            answer, source = ask_ai_voice(
                voice,
                """
                Answer the user's voice request as Ayna.
                Focus on educational cognitive neuroscience.
                """
            )

            st.session_state.messages.extend([
                {
                    "role": "user",
                    "content": "🎙️ Voice message"
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ])

            st.rerun()

        else:

            st.warning(
                "Record your voice first."
            )

    question = st.chat_input(
        "Ask Ayna...",
        key="ask_ayna_chat"
    )

    if question:

        context = "\n".join(
            f'{m["role"]}: {m["content"]}'
            for m in st.session_state.messages[-6:]
        )

        answer, source = ask_ai(
            question,
            context
        )

        st.session_state.messages.extend([
            {
                "role": "user",
                "content": question
            },
            {
                "role": "assistant",
                "content": answer
            }
        ])

        st.rerun()

    if st.session_state.messages:

        st.divider()

        last = st.session_state.messages[-1]["content"]

        speak_text(
            last,
            "ask_ayna_last_answer"
        )

        if st.button(
            "🗑️ Clear Chat",
            key="clear_ask_ayna"
        ):

            st.session_state.messages = []

            st.rerun()


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    st.subheader("🔐 Private Ask Ayna")

    if not st.session_state.private_unlocked:

        if not st.session_state.private_pin:

            st.info(
                "Create a 4–6 digit session PIN."
            )

            pin = st.text_input(
                "Create PIN",
                type="password",
                max_chars=6
            )

            confirm = st.text_input(
                "Confirm PIN",
                type="password",
                max_chars=6
            )

            if st.button(
                "🔐 Create PIN"
            ):

                if (
                    pin.isdigit()
                    and 4 <= len(pin) <= 6
                    and pin == confirm
                ):

                    st.session_state.private_pin = pin_hash(pin)
                    st.session_state.private_unlocked = True

                    st.success(
                        "Private session unlocked."
                    )

                    st.rerun()

                else:

                    st.error(
                        "PIN must be 4–6 digits and both entries must match."
                    )

        else:

            pin = st.text_input(
                "Enter PIN",
                type="password",
                max_chars=6
            )

            if st.button(
                "🔓 Unlock"
            ):

                if pin_hash(pin) == st.session_state.private_pin:

                    st.session_state.private_unlocked = True

                    st.rerun()

                else:

                    st.error(
                        "Incorrect PIN."
                    )

    else:

        st.success(
            "🔓 Private Ask Ayna unlocked."
        )

        for message in st.session_state.private_messages:

            with st.chat_message(
                message["role"]
            ):
                st.write(
                    message["content"]
                )

        private_question = st.chat_input(
            "Private message to Ayna...",
            key="private_question"
        )

        if private_question:

            context = "\n".join(
                f'{m["role"]}: {m["content"]}'
                for m in st.session_state.private_messages[-6:]
            )

            answer, _ = ask_ai(
                private_question,
                context
            )

            st.session_state.private_messages.extend([
                {
                    "role": "user",
                    "content": private_question
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ])

            st.rerun()

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "🔒 Lock",
                use_container_width=True
            ):

                st.session_state.private_unlocked = False

                st.rerun()

        with c2:

            if st.button(
                "🗑️ Delete Session",
                use_container_width=True
            ):

                st.session_state.private_messages = []
                st.session_state.private_unlocked = False
                st.session_state.private_pin = None

                st.rerun()


# ============================================================
# PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    st.subheader("📊 My Progress")

    p = st.session_state.progress

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Games",
        p["games"]
    )

    c2.metric(
        "Puzzles",
        p["puzzles"]
    )

    c3.metric(
        "Experiments",
        p["experiments"]
    )

    c4.metric(
        "AI Requests",
        st.session_state.ai_requests
    )

    if go:

        fig = go.Figure(
            go.Bar(
                x=[
                    "Games",
                    "Puzzles",
                    "Experiments",
                    "AI Requests"
                ],
                y=[
                    p["games"],
                    p["puzzles"],
                    p["experiments"],
                    st.session_state.ai_requests
                ]
            )
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.info(
        "Progress is session-based in this version."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • Created by Ayna Jaffri"
)
