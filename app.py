import os
import random
import hashlib
import base64
import html
import time
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from supabase import create_client

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
# CONFIG
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")


def asset(name):
    p = os.path.join(ASSETS, name)
    if os.path.exists(p):
        return p

    p = os.path.join(ROOT, name)
    if os.path.exists(p):
        return p

    return None


# ============================================================
# SECRETS
# ============================================================

def secret(name, default=""):
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass

    return os.getenv(name, default)


SUPABASE_URL = secret("SUPABASE_URL")
SUPABASE_KEY = secret("SUPABASE_PUBLISHABLE_KEY")

GEMINI_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret("GEMINI_MODEL", "gemini-3.6-flash")

EASYPAISA_NAME = secret("EASYPAISA_NAME", "Ayna Jaffri")
EASYPAISA_NUMBER = secret("EASYPAISA_NUMBER", "")
CONSULTATION_FEE = secret("CONSULTATION_FEE", "")


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        return create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
    except Exception:
        return None


supabase = get_supabase()


def db_ready():
    return supabase is not None


# ============================================================
# AUTH HELPERS
# ============================================================

def current_user():
    if not db_ready():
        return None

    try:
        response = supabase.auth.get_user()

        if response and response.user:
            return response.user

    except Exception:
        pass

    return None


def sign_up(email, password, name):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": name
                }
            }
        })

        return response, None

    except Exception as e:
        return None, str(e)


def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        return response, None

    except Exception as e:
        return None, str(e)


def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.clear()
    st.rerun()


# ============================================================
# DATABASE HELPERS
# ============================================================

def insert(table, data):
    if not db_ready():
        return None

    try:
        return supabase.table(table).insert(data).execute()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None


def select(table, columns="*", limit=None):
    if not db_ready():
        return []

    try:
        q = supabase.table(table).select(columns)

        if limit:
            q = q.limit(limit)

        response = q.execute()

        return response.data or []

    except Exception:
        return []


def select_user_rows(table, user_id, columns="*", limit=None):
    if not db_ready():
        return []

    try:
        q = (
            supabase
            .table(table)
            .select(columns)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )

        if limit:
            q = q.limit(limit)

        response = q.execute()

        return response.data or []

    except Exception:
        return []


def update_user_row(table, user_id, data):
    if not db_ready():
        return None

    try:
        return (
            supabase
            .table(table)
            .update(data)
            .eq("user_id", user_id)
            .execute()
        )

    except Exception:
        return None


# ============================================================
# PROFILE
# ============================================================

def ensure_profile(user):
    if not db_ready() or not user:
        return

    try:
        existing = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user.id)
            .limit(1)
            .execute()
        )

        if existing.data:
            return

        name = (
            user.user_metadata.get("full_name")
            if user.user_metadata
            else ""
        )

        supabase.table("profiles").insert({
            "id": user.id,
            "username": user.email.split("@")[0],
            "full_name": name or "",
            "language": "English"
        }).execute()

        supabase.table("progress").insert({
            "user_id": user.id,
            "experiments": 0,
            "puzzles": 0,
            "games": 0,
            "research": 0,
            "streak": 1,
            "accuracy": 0
        }).execute()

    except Exception:
        pass


def get_profile(user):
    if not user:
        return {}

    try:
        r = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user.id)
            .limit(1)
            .execute()
        )

        return r.data[0] if r.data else {}

    except Exception:
        return {}


# ============================================================
# PROGRESS
# ============================================================

def save_progress(user, field, amount=1):
    if not user:
        return

    try:
        rows = (
            supabase
            .table("progress")
            .select("*")
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )

        if not rows.data:
            return

        row = rows.data[0]
        new_value = int(row.get(field, 0) or 0) + amount

        (
            supabase
            .table("progress")
            .update({
                field: new_value,
                "updated_at": "now()"
            })
            .eq("user_id", user.id)
            .execute()
        )

    except Exception:
        pass


def get_progress(user):
    if not user:
        return {}

    try:
        r = (
            supabase
            .table("progress")
            .select("*")
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )

        return r.data[0] if r.data else {}

    except Exception:
        return {}


# ============================================================
# AI
# ============================================================

@st.cache_resource
def get_gemini():
    if not GEMINI_KEY or genai is None:
        return None

    try:
        return genai.Client(api_key=GEMINI_KEY)
    except Exception:
        return None


gemini = get_gemini()


def ask_ayna(user, prompt, activity_type="chat"):
    if gemini is None:
        return "Ayna AI is not configured. Add GEMINI_API_KEY in Streamlit Secrets."

    system = """
You are Ayna, the AI assistant inside NEUROLENS.

You are an educational cognitive neuroscience assistant.

Be scientifically cautious.
Do not diagnose mental or neurological disorders.
Do not claim that a game measures brain activity.
Do not claim that voice analysis reveals a person's true mental state.
Clearly distinguish observations, estimates and scientific evidence.

The platform explores:
cognition,
attention,
memory,
decision-making,
emotion,
learning,
neuroplasticity,
brain networks,
behaviour,
AI and neuroscience.

Keep answers understandable.
"""

    full_prompt = system + "\n\nUSER:\n" + prompt

    try:
        result = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt
        )

        answer = (getattr(result, "text", None) or "").strip()

        if not answer:
            answer = "Ayna could not generate a response."

        if user:
            insert("ai_activity", {
                "user_id": user.id,
                "activity_type": activity_type,
                "prompt": prompt[:4000],
                "response": answer[:8000]
            })

        return answer

    except Exception as e:
        return f"Ayna is temporarily unavailable: {e}"


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background:
    radial-gradient(circle at 10% 5%, #16436c, transparent 30%),
    radial-gradient(circle at 90% 20%, #30205c, transparent 25%),
    linear-gradient(135deg,#050b14,#0b1728);
    color:white;
}

.block-container {
    max-width:1450px;
    padding-top:1rem;
}

.hero {
    padding:30px;
    border-radius:28px;
    background:linear-gradient(135deg,#122f4c,#15152f);
    border:1px solid #426383;
    margin-bottom:20px;
}

.card {
    padding:20px;
    border-radius:20px;
    background:#0d2035;
    border:1px solid #2d4962;
    margin:10px 0;
}

.brain-card {
    padding:22px;
    border-radius:24px;
    background:linear-gradient(135deg,#142e4c,#211d43);
    border:1px solid #55769a;
}

.lab {
    min-height:300px;
    border-radius:25px;
    position:relative;
    overflow:hidden;
    background:
    radial-gradient(circle,#285c89 0,#0b1930 35%,#050b15 75%);
    border:1px solid #42627d;
}

.orb {
    position:absolute;
    width:100px;
    height:100px;
    border-radius:50%;
    left:calc(50% - 50px);
    top:calc(50% - 50px);
    background:radial-gradient(circle,#fff,#8ed1ff 20%,#655cff 55%,#33267c);
    box-shadow:0 0 55px #71c6ff;
    animation:pulse 2s infinite;
}

@keyframes pulse {
    50% {
        transform:scale(1.12);
    }
}

.robot {
    font-size:6rem;
    animation:robotMove 1.8s infinite;
}

@keyframes robotMove {
    50% {
        transform:translateY(-10px) rotate(2deg);
    }
}

.neural {
    font-size:3rem;
    animation:pulse .9s infinite;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "private_unlocked" not in st.session_state:
    st.session_state.private_unlocked = False

if "private_pin_hash" not in st.session_state:
    st.session_state.private_pin_hash = None

if "lab_result" not in st.session_state:
    st.session_state.lab_result = None

if "lab_setup" not in st.session_state:
    st.session_state.lab_setup = False

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# AUTH SCREEN
# ============================================================

user = current_user()

if not user:

    st.markdown("""
    <div class="hero">
        <h1>🧠 NEUROLENS</h1>
        <p>Explore cognition, behaviour & the brain</p>
        <small>Created by Ayna Jaffri</small>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Login", "✨ Create Account"])

    with tab1:

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔓 Login to NEUROLENS",
            use_container_width=True,
            type="primary"
        ):

            if not db_ready():
                st.error("Supabase is not connected. Add SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY.")
            else:

                response, error = sign_in(
                    email,
                    password
                )

                if error:
                    st.error(error)

                else:
                    st.success("Welcome back to NEUROLENS.")
                    st.rerun()

    with tab2:

        name = st.text_input(
            "Your name",
            key="signup_name"
        )

        email2 = st.text_input(
            "Email",
            key="signup_email"
        )

        password2 = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        password3 = st.text_input(
            "Confirm password",
            type="password",
            key="signup_confirm"
        )

        if st.button(
            "🚀 Create NEUROLENS Account",
            use_container_width=True,
            type="primary"
        ):

            if password2 != password3:
                st.error("Passwords do not match.")

            elif len(password2) < 6:
                st.error("Password must be at least 6 characters.")

            elif not db_ready():
                st.error("Supabase is not connected.")

            else:

                response, error = sign_up(
                    email2,
                    password2,
                    name
                )

                if error:
                    st.error(error)

                else:
                    st.success(
                        "Account created. If email confirmation is enabled in Supabase, check your email before login."
                    )

    st.stop()


# ============================================================
# INITIAL USER SETUP
# ============================================================

ensure_profile(user)
profile = get_profile(user)


# ============================================================
# SIDEBAR
# ============================================================

PAGES = [
    "Home",
    "Interactive Lab",
    "Explore Brain",
    "Brain Puzzle",
    "AI Mood & Behaviour",
    "Brain Exercises",
    "Research Book",
    "Ask Ayna",
    "Private Ask Ayna",
    "Behaviour Decoding Forum",
    "Friends & Chat",
    "Stories",
    "Challenges",
    "Chess / Ludo",
    "My Notes",
    "My Progress",
    "My Account"
]

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    st.caption(
        profile.get("full_name")
        or user.email
    )

    st.divider()

    for p in PAGES:

        if st.button(
            ("● " if st.session_state.page == p else "○ ") + p,
            key="nav_" + p,
            use_container_width=True
        ):

            st.session_state.page = p
            st.rerun()

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):
        logout()


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="hero">
    <h1>🧠 NEUROLENS</h1>
    <p>Explore cognition, behaviour & the brain</p>
    <small>
        Interactive Cognitive Neuroscience Platform • Ayna Jaffri
    </small>
</div>
""", unsafe_allow_html=True)


# ============================================================
# HOME
# ============================================================

if st.session_state.page == "Home":

    st.markdown(
        '<div class="brain-card"><h2>🤖 Welcome to Ayna\'s Neuroscience Lab</h2>'
        '<p>Explore the brain, run cognitive experiments, save your progress and connect with other learners.</p></div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "🔬 Enter Interactive Lab",
            use_container_width=True
        ):
            st.session_state.page = "Interactive Lab"
            st.rerun()

    with c2:
        if st.button(
            "🧠 Explore Brain",
            use_container_width=True
        ):
            st.session_state.page = "Explore Brain"
            st.rerun()

    with c3:
        if st.button(
            "💬 Ask Ayna",
            use_container_width=True
        ):
            st.session_state.page = "Ask Ayna"
            st.rerun()

    st.markdown("### ⚡ NEUROLENS Modules")

    modules = [
        ("🔬", "Interactive Lab"),
        ("🧠", "Brain Journey"),
        ("🧩", "Brain Puzzle"),
        ("🎯", "Cognitive Exercises"),
        ("🤖", "Ask Ayna AI"),
        ("📖", "Research Book"),
        ("👥", "Friends & Chat"),
        ("🏆", "Challenges"),
        ("💳", "Consultation")
    ]

    cols = st.columns(3)

    for i, (emoji, name) in enumerate(modules):

        with cols[i % 3]:

            st.markdown(
                f"""
                <div class="card">
                    <h3>{emoji} {name}</h3>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# INTERACTIVE LAB
# ============================================================

elif st.session_state.page == "Interactive Lab":

    st.subheader("🔬 Interactive Cognitive Neuroscience Lab")

    characters = [
        "Nova",
        "Mira",
        "Ray",
        "Zara"
    ]

    equipment = [
        "EEG Scanner",
        "Eye Tracker",
        "Reaction-Time Monitor",
        "Auditory Attention Station",
        "Cognitive Task Screen"
    ]

    experiments = [
        "Attention Gate",
        "Working Memory Sprint",
        "Decision Under Delay",
        "Inhibition Challenge",
        "Cognitive Flexibility",
        "Memory Retrieval"
    ]

    character = st.selectbox(
        "👤 Choose character",
        characters
    )

    machine = st.selectbox(
        "🧪 Choose equipment",
        equipment
    )

    experiment = st.selectbox(
        "🧠 Choose experiment",
        experiments
    )

    st.markdown(
        f"""
        <div class="lab">
            <div style="position:absolute;top:18px;left:20px">
                LIVE NEUROSCIENCE SIMULATION
            </div>

            <div style="
                display:flex;
                height:100%;
                align-items:center;
                justify-content:center;
                flex-direction:column;
            ">

                <div class="robot">🤖</div>

                <h3>{html.escape(character)}</h3>

                <div class="neural">
                    🧠 ⚡
                </div>

            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🧪 Apply Experiment Setup",
        use_container_width=True,
        type="primary"
    ):

        st.session_state.lab_setup = True
        st.success(
            f"{character} + {machine} + {experiment} setup applied."
        )

    if st.session_state.lab_setup:

        if st.button(
            "▶️ Start Experiment",
            use_container_width=True
        ):

            st.markdown(
                """
                <div class="card">
                    <h3>⚡ Experiment Running</h3>
                    <p>Neural simulation active...</p>
                    <div class="neural">🧠 → ⚡ → 🔵 → ⚡ → 🧠</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.session_state.lab_result = experiment

        if st.session_state.lab_result:

            st.divider()

            st.markdown("### 🎯 Perform Your Task")

            if experiment == "Attention Gate":

                answer = st.radio(
                    "Which option contains X?",
                    [
                        "A B C D",
                        "A B X D",
                        "A C B D",
                        "A B D C"
                    ]
                )

                if st.button("Submit Attention Task"):

                    correct = answer == "A B X D"

                    insert(
                        "experiment_results",
                        {
                            "user_id": user.id,
                            "experiment": experiment,
                            "domain": "Attention",
                            "score": 1 if correct else 0,
                            "result": {
                                "correct": correct
                            }
                        }
                    )

                    save_progress(
                        user,
                        "experiments"
                    )

                    st.success(
                        "Correct! Attention task completed."
                        if correct
                        else
                        "Task completed. Try again to practice."
                    )

            elif experiment == "Working Memory Sprint":

                st.info(
                    "Remember: 7 2 9 4 1 8"
                )

                answer = st.text_input(
                    "Enter sequence"
                )

                if st.button("Submit Memory Task"):

                    correct = (
                        answer.replace(" ", "")
                        == "729418"
                    )

                    insert(
                        "experiment_results",
                        {
                            "user_id": user.id,
                            "experiment": experiment,
                            "domain": "Working Memory",
                            "score": 1 if correct else 0,
                            "result": {
                                "correct": correct
                            }
                        }
                    )

                    save_progress(
                        user,
                        "experiments"
                    )

                    st.success(
                        "Memory sequence correct!"
                        if correct
                        else
                        "Not quite — practice again."
                    )

            else:

                answer = st.radio(
                    "Choose your response",
                    [
                        "Option A",
                        "Option B",
                        "Option C"
                    ]
                )

                if st.button(
                    "Submit Experiment"
                ):

                    insert(
                        "experiment_results",
                        {
                            "user_id": user.id,
                            "experiment": experiment,
                            "domain": "Cognitive task",
                            "score": 1,
                            "result": {
                                "response": answer
                            }
                        }
                    )

                    save_progress(
                        user,
                        "experiments"
                    )

                    st.success(
                        "Experiment result saved."
                    )

            st.markdown("### 🤖 Ayna's Explanation")

            if st.button(
                "🧠 Explain My Result"
            ):

                explanation = ask_ayna(
                    user,
                    f"""
                    Explain the educational neuroscience concept behind:
                    {experiment}

                    Equipment:
                    {machine}

                    Keep it concise.
                    """
                    ,
                    "lab"
                )

                st.info(explanation)


# ============================================================
# EXPLORE BRAIN
# ============================================================

elif st.session_state.page == "Explore Brain":

    st.subheader("🧠 Explore Brain")

    regions = {
        "Prefrontal Cortex":
            "Planning, working memory, cognitive control and decision-making.",

        "Hippocampus":
            "Important for episodic memory and spatial representations.",

        "Striatum":
            "Action selection, reward learning and habits.",

        "Anterior Cingulate Cortex":
            "Conflict monitoring, error processing and cognitive control.",

        "Attention Networks":
            "Distributed systems that support selection and control of information."
    }

    region = st.selectbox(
        "Choose brain region",
        list(regions)
    )

    st.markdown(
        f"""
        <div class="brain-card">
            <h2>🧠 {region}</h2>
            <p>{regions[region]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    components.html(
        f"""
        <div style="
            height:280px;
            border-radius:25px;
            background:radial-gradient(circle,#263f79,#07111f);
            display:flex;
            align-items:center;
            justify-content:center;
            color:white;
            font-size:5rem;
        ">
        🧠
        </div>
        """,
        height=300
    )

    st.markdown("### 🔗 Circuit view")

    st.code(
        "Cortex → Striatum → Pallidal pathways → Thalamus → Cortex"
    )


# ============================================================
# BRAIN PUZZLE
# ============================================================

elif st.session_state.page == "Brain Puzzle":

    st.subheader("🧩 Brain Puzzle")

    brain_path = asset("brain.png")

    if brain_path:

        st.image(
            brain_path,
            use_container_width=True
        )

    difficulty = st.select_slider(
        "Difficulty",
        options=[
            "3 × 3",
            "4 × 4",
            "5 × 5"
        ]
    )

    st.info(
        f"Interactive {difficulty} puzzle."
    )

    if st.button(
        "🎯 Record Puzzle Result"
    ):

        insert(
            "game_results",
            {
                "user_id": user.id,
                "game": "Brain Puzzle",
                "score": 1,
                "metadata": {
                    "difficulty": difficulty
                }
            }
        )

        save_progress(
            user,
            "puzzles"
        )

        st.success(
            "Puzzle result saved to your Supabase account."
        )


# ============================================================
# AI MOOD
# ============================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.subheader("🎯 AI Mood & Behaviour")

    st.write(
        "Use text or voice to get a broad conversational estimate."
    )

    text = st.text_area(
        "⌨️ Tell Ayna how you feel"
    )

    if st.button(
        "🔵 Send Text"
    ) and text:

        result = ask_ayna(
            user,
            f"""
            Give a broad conversational affect estimate.

            User text:
            {text}

            Return:
            - broad mood
            - confidence
            - short explanation

            Do not diagnose.
            """,
            "mood_text"
        )

        st.info(result)

    audio = None

    try:

        audio = st.audio_input(
            "🎙️ Record Voice"
        )

    except Exception:

        st.info(
            "Voice recording is unavailable in this browser."
        )

    if st.button(
        "🔵 Send Voice"
    ):

        if audio:

            if gemini is None:

                st.error(
                    "GEMINI_API_KEY is not configured."
                )

            else:

                try:

                    part = types.Part.from_bytes(
                        data=audio.getvalue(),
                        mime_type=audio.type or "audio/wav"
                    )

                    result = gemini.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=[
                            part,
                            """
                            Give a cautious broad conversational
                            affect estimate.

                            Do not diagnose.
                            Do not infer sensitive traits.
                            """
                        ]
                    )

                    answer = (
                        getattr(result, "text", None)
                        or "No result."
                    )

                    insert(
                        "ai_activity",
                        {
                            "user_id": user.id,
                            "activity_type": "voice_mood",
                            "prompt": "Voice mood request",
                            "response": answer
                        }
                    )

                    st.info(answer)

                except Exception as e:

                    st.error(
                        f"Voice processing error: {e}"
                    )

        else:

            st.warning(
                "Record your voice first."
            )


# ============================================================
# BRAIN EXERCISES
# ============================================================

elif st.session_state.page == "Brain Exercises":

    st.subheader("🧪 Brain Exercises")

    exercise = st.selectbox(
        "Choose exercise",
        [
            "Attention",
            "Memory",
            "Decision Making",
            "Inhibition",
            "Cognitive Flexibility"
        ]
    )

    if exercise == "Attention":

        answer = st.radio(
            "Find X",
            [
                "A B C D",
                "A B X D",
                "A C D B",
                "B A C D"
            ]
        )

        if st.button("Check"):

            correct = answer == "A B X D"

            insert(
                "game_results",
                {
                    "user_id": user.id,
                    "game": "Attention",
                    "score": 1 if correct else 0,
                    "metadata": {}
                }
            )

            save_progress(
                user,
                "games"
            )

            st.success(
                "Correct!" if correct
                else "Try again."
            )

    elif exercise == "Memory":

        st.info(
            "Remember: 729418"
        )

        answer = st.text_input(
            "Enter sequence"
        )

        if st.button("Check Memory"):

            correct = (
                answer.replace(" ", "")
                == "729418"
            )

            insert(
                "game_results",
                {
                    "user_id": user.id,
                    "game": "Memory",
                    "score": 1 if correct else 0,
                    "metadata": {}
                }
            )

            save_progress(
                user,
                "games"
            )

            st.success(
                "Correct!" if correct
                else "Not quite."
            )

    else:

        st.info(
            f"{exercise} exercise loaded."
        )


# ============================================================
# RESEARCH BOOK
# ============================================================

elif st.session_state.page == "Research Book":

    st.subheader("📖 Research Book")

    topic = st.selectbox(
        "Research topic",
        [
            "Brain & Behaviour",
            "Memory",
            "Attention",
            "Emotion",
            "Decision Making",
            "Neuroplasticity",
            "Cognitive Control"
        ]
    )

    notes = {
        "Brain & Behaviour":
            "Behaviour emerges from interacting neural systems, body states and environment.",

        "Memory":
            "Memory includes encoding, consolidation and retrieval.",

        "Attention":
            "Attention changes which information receives processing priority.",

        "Emotion":
            "Emotion involves brain, body and cognitive processes.",

        "Decision Making":
            "Decision-making combines valuation, uncertainty, memory and control.",

        "Neuroplasticity":
            "The nervous system changes with development, learning and experience.",

        "Cognitive Control":
            "Control helps maintain goals and adjust behaviour."
    }

    st.info(
        notes[topic]
    )

    if st.button(
        "📝 Save Research Note"
    ):

        insert(
            "notes",
            {
                "user_id": user.id,
                "title": topic,
                "content": notes[topic]
            }
        )

        save_progress(
            user,
            "research"
        )

        st.success(
            "Research note saved."
        )


# ============================================================
# ASK AYNA
# ============================================================

elif st.session_state.page == "Ask Ayna":

    st.subheader("💬 Ask Ayna")

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    prompt = st.chat_input(
        "Ask Ayna..."
    )

    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        answer = ask_ayna(
            user,
            prompt,
            "chat"
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.rerun()


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    st.subheader("🔐 Private Ask Ayna")

    if not st.session_state.private_unlocked:

        st.write(
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
            "🔐 Create Private Session"
        ):

            if (
                not pin.isdigit()
                or not 4 <= len(pin) <= 6
            ):

                st.error(
                    "PIN must contain 4–6 digits."
                )

            elif pin != confirm:

                st.error(
                    "PINs do not match."
                )

            else:

                st.session_state.private_pin_hash = hashlib.sha256(
                    pin.encode()
                ).hexdigest()

                st.session_state.private_unlocked = True

                st.success(
                    "Private session created."
                )

                st.rerun()

    else:

        pin = st.text_input(
            "Enter your private PIN",
            type="password",
            max_chars=6
        )

        if st.button(
            "🔓 Verify PIN"
        ):

            if (
                st.session_state.private_pin_hash
                == hashlib.sha256(pin.encode()).hexdigest()
            ):

                st.success(
                    "Private session unlocked."
                )

                private_message = st.chat_input(
                    "Private message..."
                )

                if private_message:

                    insert(
                        "private_chat",
                        {
                            "user_id": user.id,
                            "message": private_message,
                            "sender": "user"
                        }
                    )

                    answer = ask_ayna(
                        user,
                        private_message,
                        "private_chat"
                    )

                    insert(
                        "private_chat",
                        {
                            "user_id": user.id,
                            "message": answer,
                            "sender": "ayna"
                        }
                    )

                    st.write(answer)

            else:

                st.error(
                    "Incorrect PIN."
                )

        if st.button(
            "🗑️ Delete Private Session"
        ):

            st.session_state.private_unlocked = False
            st.session_state.private_pin_hash = None
            st.rerun()


# ============================================================
# BEHAVIOUR DECODING FORUM
# ============================================================

elif st.session_state.page == "Behaviour Decoding Forum":

    st.subheader(
        "🧠 Behaviour Decoding Forum"
    )

    st.write(
        "Request a professional text-based discussion with Ayna."
    )

    name = st.text_input(
        "Your name"
    )

    phone = st.text_input(
        "Contact number"
    )

    problem = st.text_area(
        "What would you like to discuss?"
    )

    slot = st.selectbox(
        "Preferred slot",
        [
            "Morning",
            "Afternoon",
            "Evening"
        ]
    )

    payment_method = st.radio(
        "Payment Method",
        [
            "🇵🇰 Easypaisa",
            "🌍 International Payment"
        ]
    )

    st.markdown("### 💳 Payment")

    if payment_method == "🇵🇰 Easypaisa":

        if EASYPAISA_NUMBER:

            st.success(
                f"Send payment to: {EASYPAISA_NAME} — {EASYPAISA_NUMBER}"
            )

        else:

            st.warning(
                "Easypaisa number has not been configured in Streamlit Secrets."
            )

    else:

        st.info(
            "International payment gateway will be connected here."
        )

    if CONSULTATION_FEE:

        st.write(
            f"Consultation fee: PKR {CONSULTATION_FEE}"
        )

    payment_reference = st.text_input(
        "Transaction / Payment Reference"
    )

    if st.button(
        "📨 Submit Appointment Request",
        type="primary"
    ):

        if not name or not problem:

            st.error(
                "Name and problem are required."
            )

        elif not payment_reference:

            st.error(
                "Enter the payment/reference ID."
            )

        else:

            insert(
                "appointments",
                {
                    "user_id": user.id,
                    "name": name,
                    "phone": phone,
                    "problem": problem,
                    "preferred_slot": slot,
                    "payment_method": payment_method,
                    "payment_reference": payment_reference,
                    "payment_status": "pending"
                }
            )

            st.success(
                "Appointment request submitted. Payment is pending verification."
            )

    st.divider()

    st.markdown(
        "### 💬 Discussion"
    )

    st.info(
        "Discussion unlocks after payment verification."
    )

    # Future verified-payment records can unlock this section.
    # Do not automatically mark a transaction as verified
    # merely because a user entered a reference number.


# ============================================================
# FRIENDS & CHAT
# ============================================================

elif st.session_state.page == "Friends & Chat":

    st.subheader(
        "👥 Friends & Chat"
    )

    st.markdown(
        "### Add Friend"
    )

    friend_username = st.text_input(
        "Friend username"
    )

    if st.button(
        "➕ Send Friend Request"
    ):

        if friend_username:

            try:

                target = (
                    supabase
                    .table("profiles")
                    .select("id,username,full_name")
                    .eq("username", friend_username)
                    .limit(1)
                    .execute()
                )

                if target.data:

                    receiver = target.data[0]["id"]

                    insert(
                        "friendships",
                        {
                            "requester_id": user.id,
                            "receiver_id": receiver,
                            "status": "pending"
                        }
                    )

                    st.success(
                        "Friend request sent."
                    )

                else:

                    st.warning(
                        "User not found."
                    )

            except Exception as e:

                st.error(
                    str(e)
                )

    st.divider()

    st.markdown(
        "### 💬 Chat"
    )

    receiver_email = st.text_input(
        "Friend email"
    )

    message = st.chat_input(
        "Message your friend..."
    )

    if message and receiver_email:

        try:

            target = (
                supabase
                .table("profiles")
                .select("id")
                .eq("username", receiver_email.split("@")[0])
                .limit(1)
                .execute()
            )

            if target.data:

                insert(
                    "messages",
                    {
                        "sender_id": user.id,
                        "receiver_id": target.data[0]["id"],
                        "message": message
                    }
                )

                st.success(
                    "Message sent."
                )

        except Exception as e:

            st.error(
                str(e)
            )

    st.caption(
        "Chat data is stored in Supabase. Realtime subscriptions can be added when the production chat UI is finalized."
    )


# ============================================================
# STORIES
# ============================================================

elif st.session_state.page == "Stories":

    st.subheader(
        "📸 Stories"
    )

    story = st.text_area(
        "Write a story/update"
    )

    if st.button(
        "➕ Publish Story"
    ):

        if story:

            insert(
                "stories",
                {
                    "user_id": user.id,
                    "text": story
                }
            )

            st.success(
                "Story published."
            )

    st.divider()

    stories = select(
        "stories",
        "*",
        20
    )

    for story_row in stories:

        st.markdown(
            f"""
            <div class="card">
                <b>🧠 NEUROLENS Story</b>
                <p>{html.escape(story_row.get("text",""))}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# CHALLENGES
# ============================================================

elif st.session_state.page == "Challenges":

    st.subheader(
        "🏆 Challenges"
    )

    challenges = select(
        "challenges",
        "*"
    )

    if not challenges:

        st.info(
            "No challenges have been created yet."
        )

        if st.button(
            "➕ Create Starter Challenges"
        ):

            starter = [
                {
                    "title": "Attention Sprint",
                    "description": "Complete an attention task.",
                    "reward": 10
                },
                {
                    "title": "Memory Sprint",
                    "description": "Complete a working memory task.",
                    "reward": 10
                },
                {
                    "title": "Decision Challenge",
                    "description": "Complete a decision task.",
                    "reward": 15
                }
            ]

            for item in starter:

                insert(
                    "challenges",
                    item
                )

            st.rerun()

    else:

        for challenge in challenges:

            st.markdown(
                f"""
                <div class="card">
                    <h3>🏆 {html.escape(challenge["title"])}</h3>
                    <p>{html.escape(challenge["description"])}</p>
                    <small>Reward: {challenge["reward"]}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Complete",
                key="challenge_" + challenge["id"]
            ):

                insert(
                    "challenge_progress",
                    {
                        "user_id": user.id,
                        "challenge_id": challenge["id"],
                        "completed": True,
                        "score": challenge["reward"]
                    }
                )

                st.success(
                    "Challenge recorded."
                )


# ============================================================
# CHESS / LUDO
# ============================================================

elif st.session_state.page == "Chess / Ludo":

    st.subheader(
        "♟️ Chess / 🎲 Ludo"
    )

    game = st.radio(
        "Choose game",
        [
            "Chess",
            "Ludo"
        ],
        horizontal=True
    )

    st.markdown(
        f"""
        <div class="brain-card">
            <h2>{'♟️' if game == 'Chess' else '🎲'} {game}</h2>
            <p>NEUROLENS multiplayer game module.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Game results can already be saved in Supabase. Full synchronized multiplayer board logic can be attached to the same game_results/friends/messages backend."
    )

    score = st.number_input(
        "Result score",
        min_value=0,
        value=0
    )

    if st.button(
        "💾 Save Game Result"
    ):

        insert(
            "game_results",
            {
                "user_id": user.id,
                "game": game,
                "score": score,
                "metadata": {}
            }
        )

        save_progress(
            user,
            "games"
        )

        st.success(
            "Game result saved."
        )


# ============================================================
# NOTES
# ============================================================

elif st.session_state.page == "My Notes":

    st.subheader(
        "📝 My Notes"
    )

    title = st.text_input(
        "Note title"
    )

    content = st.text_area(
        "Note",
        height=200
    )

    if st.button(
        "💾 Save Note"
    ):

        if title:

            insert(
                "notes",
                {
                    "user_id": user.id,
                    "title": title,
                    "content": content
                }
            )

            st.success(
                "Note saved to Supabase."
            )

    st.divider()

    notes = select_user_rows(
        "notes",
        user.id,
        limit=30
    )

    for note in notes:

        with st.expander(
            note.get("title", "Note")
        ):

            st.write(
                note.get("content", "")
            )


# ============================================================
# PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    st.subheader(
        "📊 My Progress"
    )

    progress = get_progress(
        user
    )

    cols = st.columns(5)

    metrics = [
        ("Experiments", "experiments"),
        ("Puzzles", "puzzles"),
        ("Games", "games"),
        ("Research", "research"),
        ("Streak", "streak")
    ]

    for col, (label, key) in zip(
        cols,
        metrics
    ):

        col.metric(
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

    st.success(
        "Your progress is stored in your Supabase account."
    )


# ============================================================
# ACCOUNT
# ============================================================

elif st.session_state.page == "My Account":

    st.subheader(
        "👤 My Account"
    )

    name = st.text_input(
        "Full name",
        value=profile.get("full_name", "")
    )

    username = st.text_input(
        "Username",
        value=profile.get("username", "")
    )

    bio = st.text_area(
        "Bio",
        value=profile.get("bio", "")
    )

    if st.button(
        "💾 Update Profile"
    ):

        try:

            (
                supabase
                .table("profiles")
                .update({
                    "full_name": name,
                    "username": username,
                    "bio": bio,
                    "updated_at": "now()"
                })
                .eq("id", user.id)
                .execute()
            )

            st.success(
                "Profile updated."
            )

        except Exception as e:

            st.error(
                str(e)
            )

    st.write(
        "Email:",
        user.email
    )

    st.divider()

    if st.button(
        "🚪 Sign Out",
        use_container_width=True
    ):

        logout()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NEUROLENS • Explore cognition, behaviour & the brain • Created by Ayna Jaffri"
)
