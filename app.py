# ============================================================
# NEUROLENS — FINAL BUILD
# PART 1/4
# Core + Database + AI + Auth + NeuroWorld
# ============================================================

import os
import re
import json
import time
import random
import hashlib
import secrets
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# OPTIONAL LIBRARIES
# ============================================================

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import plotly.express as px
except Exception:
    px = None

try:
    import requests
except Exception:
    requests = None

try:
    from supabase import create_client
except Exception:
    create_client = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


# ============================================================
# APP IDENTITY
# ============================================================

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"
TAGLINE = "Explore cognition, behavior & the brain"


# ============================================================
# SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, "")
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


SUPABASE_URL = get_secret("SUPABASE_URL")

SUPABASE_KEY = (
    get_secret("SUPABASE_KEY")
    or get_secret("SUPABASE_PUBLISHABLE_KEY")
    or get_secret("SUPABASE_ANON_KEY")
)

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

GEMINI_MODEL = get_secret(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

EASYPAISA_NUMBER = get_secret(
    "EASYPAISA_NUMBER"
)

INTERNATIONAL_PAYMENT_URL = get_secret(
    "INTERNATIONAL_PAYMENT_URL"
)

PAYMENT_ADMIN_KEY = get_secret(
    "PAYMENT_ADMIN_KEY"
)


# ============================================================
# SUPABASE
# ============================================================

supabase = None

if (
    create_client
    and SUPABASE_URL
    and SUPABASE_KEY
):
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception:
        supabase = None


# ============================================================
# GEMINI
# ============================================================

gemini_client = None

if (
    genai
    and GEMINI_API_KEY
):
    try:
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception:
        gemini_client = None


def ai_available():
    return bool(
        gemini_client
        and GEMINI_API_KEY
    )


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "NeuroWorld",

    "user": None,
    "email": "",

    "ai_requests": 0,
    "ai_limit": 20,

    "chat": [],

    "lab_results": [],
    "exercise_results": [],
    "puzzle_results": [],
    "research_notes": [],

    "voice_result": None,
    "face_result": None,

    "private_messages": [],
    "private_unlocked": False,
    "private_pin_hash": "",

    "lab_experiment": "Attention",
    "lab_result": None,

    "selected_brain_system": "Prefrontal Cortex",

    "puzzle_size": 3,
    "puzzle_board": None,
    "puzzle_solution": None,
    "puzzle_moves": 0,
    "puzzle_started": False,
    "puzzle_finished": False,
    "puzzle_start_time": None,

    "language": "English",

    "last_error": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 15% 10%,
            rgba(74, 144, 226, .16),
            transparent 28%
        ),
        radial-gradient(
            circle at 85% 15%,
            rgba(147, 51, 234, .14),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #050816 0%,
            #081225 50%,
            #050816 100%
        );
}

.block-container {
    max-width: 1250px;
    padding-top: 1.5rem;
}

.hero {
    padding: 30px;
    border-radius: 28px;
    background:
        linear-gradient(
            135deg,
            rgba(15, 28, 65, .96),
            rgba(28, 35, 80, .90)
        );
    border: 1px solid rgba(255,255,255,.08);
    margin-bottom: 22px;
}

.hero h1 {
    margin: 0;
    font-size: clamp(38px, 7vw, 72px);
    font-weight: 900;
    letter-spacing: -3px;
}

.hero p {
    color: #aebbd4;
    font-size: 18px;
}

.neuro-card {
    background: rgba(14, 25, 50, .82);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 16px;
}

.world-card {
    background:
        radial-gradient(
            circle at center,
            rgba(66, 211, 255, .13),
            transparent 45%
        ),
        rgba(7, 16, 36, .88);
    border: 1px solid rgba(88, 210, 255, .14);
    border-radius: 30px;
    padding: 36px 24px;
    text-align: center;
}

.brain-guide {
    font-size: 115px;
    line-height: 1;
    animation: brainFloat 3s ease-in-out infinite;
}

.robot-guide {
    font-size: 70px;
    margin-top: 12px;
}

@keyframes brainFloat {
    0%,100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-10px);
    }
}

.muted {
    color: #8f9db7;
    font-size: 14px;
}

.success-panel {
    padding: 18px;
    border-radius: 18px;
    background: rgba(40, 200, 130, .12);
    border: 1px solid rgba(40, 200, 130, .30);
}

.warning-panel {
    padding: 18px;
    border-radius: 18px;
    background: rgba(255, 190, 50, .10);
    border: 1px solid rgba(255, 190, 50, .25);
}

@media (max-width: 700px) {

    .block-container {
        padding-left: 12px;
        padding-right: 12px;
    }

    .hero {
        padding: 22px 16px;
        border-radius: 20px;
    }

    .hero h1 {
        font-size: 42px;
        letter-spacing: -2px;
    }

    .hero p {
        font-size: 15px;
    }

    .brain-guide {
        font-size: 85px;
    }

    .robot-guide {
        font-size: 55px;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_text(value, max_length=3000):
    if value is None:
        return ""

    text = str(value)

    text = re.sub(
        r"<script.*?>.*?</script>",
        "",
        text,
        flags=re.I | re.S,
    )

    text = re.sub(
        r"<.*?>",
        "",
        text,
    )

    return text.strip()[:max_length]


def current_user_id():
    user = st.session_state.get("user")

    if isinstance(user, dict):
        return user.get("id")

    return None


def db_insert(table, payload):
    if not supabase:
        return None

    try:
        return (
            supabase
            .table(table)
            .insert(payload)
            .execute()
        )
    except Exception:
        return None


def db_select(table, limit=50):
    if not supabase:
        return []

    try:
        result = (
            supabase
            .table(table)
            .select("*")
            .limit(limit)
            .execute()
        )

        return result.data or []

    except Exception:
        return []


def asset_path(filename):
    locations = [
        filename,
        os.path.join(
            "assets",
            filename,
        ),
    ]

    for path in locations:
        if os.path.exists(path):
            return path

    return None


def show_image(
    filename,
    width=600,
):
    path = asset_path(filename)

    if path and Image:

        try:
            st.image(
                path,
                width=width,
            )
            return True
        except Exception:
            pass

    return False


def safe_json(text):
    if not text:
        return {}

    text = re.sub(
        r"```(?:json)?",
        "",
        str(text),
        flags=re.I,
    )

    text = text.replace(
        "```",
        "",
    ).strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.S,
    )

    if match:

        try:
            return json.loads(
                match.group(0)
            )
        except Exception:
            pass

    return {}


# ============================================================
# AI HELPERS
# ============================================================

def ai_limit_reached():
    return (
        st.session_state.ai_requests
        >= st.session_state.ai_limit
    )


def record_ai_request():
    st.session_state.ai_requests += 1

    if (
        st.session_state.ai_requests
        > st.session_state.ai_limit
    ):
        st.session_state.ai_requests = (
            st.session_state.ai_limit
        )


def ai_generate(
    prompt,
    image_bytes=None,
    mime_type=None,
):
    if not ai_available():
        return ""

    if ai_limit_reached():
        return (
            "AI request limit reached "
            "for this session."
        )

    try:

        contents = [prompt]

        if (
            image_bytes
            and types
        ):
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=(
                        mime_type
                        or "image/jpeg"
                    ),
                )
            )

        response = (
            gemini_client
            .models
            .generate_content(
                model=GEMINI_MODEL,
                contents=contents,
            )
        )

        record_ai_request()

        return (
            getattr(
                response,
                "text",
                "",
            )
            or ""
        )

    except Exception as exc:

        st.session_state.last_error = (
            str(exc)
        )

        return ""


def speak_text(text):
    text = clean_text(
        text,
        2500,
    )

    components.html(
        f"""
        <script>
        const speechText = {json.dumps(text)};

        if ("speechSynthesis" in window) {{
            window.speechSynthesis.cancel();

            const utterance =
                new SpeechSynthesisUtterance(
                    speechText
                );

            utterance.rate = 0.95;
            utterance.pitch = 1.05;

            window.speechSynthesis.speak(
                utterance
            );
        }}
        </script>
        """,
        height=10,
    )


# ============================================================
# AUTH PAGE
# ============================================================

def page_auth():

    st.markdown(
        f"""
        <div class="hero">
            <h1>🧠 {APP_NAME}</h1>
            <p>{TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_signup, tab_login = st.tabs(
        [
            "Create Account",
            "Sign In",
        ]
    )

    with tab_signup:

        signup_email = st.text_input(
            "Email",
            key="signup_email",
        )

        signup_password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
        )

        if st.button(
            "Create Account",
            type="primary",
            use_container_width=True,
        ):

            if not signup_email:
                st.warning(
                    "Please enter your email."
                )

            elif not signup_password:
                st.warning(
                    "Please enter a password."
                )

            elif not supabase:
                st.warning(
                    "Supabase is not connected."
                )

            else:

                try:

                    result = (
                        supabase
                        .auth
                        .sign_up(
                            {
                                "email":
                                    signup_email,
                                "password":
                                    signup_password,
                            }
                        )
                    )

                    if result.user:

                        st.success(
                            "Account created. "
                            "Check your email if "
                            "confirmation is enabled."
                        )

                    else:

                        st.error(
                            "Account could not "
                            "be created."
                        )

                except Exception:

                    st.error(
                        "Sign-up failed. "
                        "Please check the details."
                    )

    with tab_login:

        login_email = st.text_input(
            "Email",
            key="login_email",
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Sign In",
            type="primary",
            use_container_width=True,
        ):

            if not supabase:

                st.warning(
                    "Supabase is not connected."
                )

            else:

                try:

                    result = (
                        supabase
                        .auth
                        .sign_in_with_password(
                            {
                                "email":
                                    login_email,
                                "password":
                                    login_password,
                            }
                        )
                    )

                    if result.user:

                        st.session_state.user = {
                            "id":
                                result.user.id,
                            "email":
                                result.user.email,
                        }

                        st.session_state.email = (
                            result.user.email
                            or ""
                        )

                        st.session_state.page = (
                            "NeuroWorld"
                        )

                        st.rerun()

                except Exception:

                    st.error(
                        "Sign-in failed."
                    )


def logout():

    try:

        if supabase:
            supabase.auth.sign_out()

    except Exception:
        pass

    st.session_state.user = None
    st.session_state.email = ""
    st.session_state.page = "NeuroWorld"
    st.session_state.private_unlocked = False

    st.rerun()


# ============================================================
# NEUROWORLD
# ============================================================

def page_neuroworld():

    st.markdown(
        f"""
        <div class="hero">
            <h1>{APP_NAME}</h1>
            <p>{TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="world-card">

            <div class="brain-guide">
                🧠
            </div>

            <h2>
                Hi, I am NeuroLens.
            </h2>

            <p>
                Come with me —
                I'll show you what you can explore.
            </p>

            <div class="robot-guide">
                🤖
            </div>

            <p class="muted">
                Your female AI research companion
                is ready to guide you.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    cards = [
        (
            "🧪",
            "Cognitive Lab",
            "Run interactive cognitive experiments.",
        ),
        (
            "🧠",
            "Brain Journey",
            "Explore neurons, brain regions and networks.",
        ),
        (
            "🎯",
            "Brain Challenges",
            "Train memory, attention and decision-making.",
        ),
        (
            "🧩",
            "Brain Puzzle",
            "Reconstruct a 12-piece brain jigsaw.",
        ),
        (
            "🤖",
            "Ask Ayna",
            "Talk with your AI neuroscience assistant.",
        ),
        (
            "🔬",
            "Research World",
            "Search neuroscience research papers.",
        ),
        (
            "🎙️",
            "AI Mood & Behaviour",
            "Explore AI-assisted voice and facial cues.",
        ),
        (
            "🌐",
            "NeuroSocial",
            "Connect around neuroscience and cognition.",
        ),
        (
            "📈",
            "My Progress",
            "Track your NEUROLENS journey.",
        ),
    ]

    columns = st.columns(3)

    for index, (
        icon,
        title,
        description,
    ) in enumerate(cards):

        with columns[index % 3]:

            st.markdown(
                f"""
                <div class="neuro-card">
                    <h3>
                        {icon} {title}
                    </h3>

                    <p>
                        {description}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Enter {title}",
                key=f"world_card_{index}",
                use_container_width=True,
            ):

                st.session_state.page = title
                st.rerun()


# ============================================================
# SIMPLE WELCOME / INTRO
# ============================================================

def page_welcome():

    st.markdown(
        f"""
        <div class="hero">
            <h1>Welcome to {APP_NAME}</h1>
            <p>{TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    video = asset_path(
        "ayna_reboot_voiced.mp4"
    )

    if video:

        st.video(video)

    else:

        st.markdown(
            """
            <div class="world-card">
                <div class="brain-guide">🧠</div>

                <h2>
                    Welcome to NeuroLens.
                </h2>

                <p>
                    Explore the brain,
                    behavior and cognition
                    through interactive experiences.
                </p>

                <div class="robot-guide">
                    🤖
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button(
        "🚀 Enter NEUROLENS",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.page = "NeuroWorld"
        st.rerun()


# ============================================================
# BRAIN SYSTEM DATA
# ============================================================

BRAIN_SYSTEMS = {

    "Prefrontal Cortex":
        "Planning, working memory, "
        "cognitive control and flexible "
        "decision-making.",

    "Hippocampus":
        "Memory formation, contextual "
        "learning and spatial processing.",

    "Striatum":
        "Action selection, reward learning "
        "and habit-related processes.",

    "Anterior Cingulate Cortex":
        "Conflict monitoring, effort, "
        "attention and adaptive control.",

    "Attention Networks":
        "Distributed systems involved in "
        "alerting, orienting and goal-directed attention.",
}


# ============================================================
# NAVIGATION SIDEBAR
# ============================================================

def render_sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:8px;
            ">

                <div style="
                    font-size:48px;
                ">
                    🧠
                </div>

                <h2>
                    NEUROLENS
                </h2>

                <div class="muted">
                    Ayna Jaffri
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        pages = [
            "Welcome",
            "NeuroWorld",
            "Cognitive Lab",
            "Brain Journey",
            "Brain Challenges",
            "Brain Puzzle",
            "Ask Ayna",
            "AI Mood & Behaviour",
            "Research World",
            "Private Ayna",
            "Behaviour Decoding",
            "NeuroSocial",
            "My Progress",
            "Security & Privacy",
            "Settings",
            "Account",
        ]

        current = st.session_state.page

        if current not in pages:
            current = "NeuroWorld"

        selected = st.radio(
            "Explore",
            pages,
            index=pages.index(current),
        )

        if selected != st.session_state.page:

            st.session_state.page = selected
            st.rerun()

        st.divider()

        if st.session_state.user:

            st.caption(
                f"Signed in as "
                f"{st.session_state.email}"
            )

        else:

            st.caption(
                "Guest exploration mode"
            )

        st.caption(
            f"AI usage: "
            f"{st.session_state.ai_requests}/"
            f"{st.session_state.ai_limit}"        
        )


# ============================================================
# END OF PART 1
# ============================================================
# ============================================================
# NEUROLENS — FINAL BUILD
# PART 2/4
# Cognitive Lab + Brain Journey + 12-Piece Jigsaw Puzzle
# ============================================================


# ============================================================
# COGNITIVE LAB
# ============================================================

def lab_save_result(experiment, score, accuracy, observation):

    result = {
        "experiment": experiment,
        "score": score,
        "accuracy": accuracy,
        "observation": observation,
        "timestamp": datetime.utcnow().isoformat(),
    }

    st.session_state.lab_results.append(result)

    user_id = current_user_id()

    if user_id:

        db_insert(
            "lab_results",
            {
                "user_id": user_id,
                "experiment": experiment,
                "score": score,
                "accuracy": accuracy,
                "observation": observation,
            },
        )


def run_attention_experiment():

    st.markdown("### 🎯 Attention Experiment")

    st.write(
        "You will see several symbols. "
        "Select the target symbol as quickly as possible."
    )

    target = "X"

    if "attention_items" not in st.session_state:

        items = []

        for _ in range(24):

            items.append(
                random.choice(
                    ["X", "O", "△", "□", "◇"]
                )
            )

        target_position = random.randrange(
            len(items)
        )

        items[target_position] = target

        st.session_state.attention_items = items
        st.session_state.attention_target = (
            target_position
        )
        st.session_state.attention_start = time.time()
        st.session_state.attention_done = False

    items = st.session_state.attention_items

    cols = st.columns(6)

    for i, symbol in enumerate(items):

        with cols[i % 6]:

            if st.button(
                symbol,
                key=f"attention_{i}",
                use_container_width=True,
            ):

                elapsed = round(
                    time.time()
                    - st.session_state.attention_start,
                    2,
                )

                correct = (
                    i
                    == st.session_state.attention_target
                )

                if correct:

                    score = max(
                        100
                        - int(elapsed * 5),
                        10,
                    )

                    st.success(
                        f"Correct! Reaction time: "
                        f"{elapsed}s"
                    )

                    lab_save_result(
                        "Attention",
                        score,
                        100,
                        "Target detected correctly.",
                    )

                else:

                    score = 0

                    st.error(
                        "That was not the target."
                    )

                    lab_save_result(
                        "Attention",
                        score,
                        0,
                        "Target selection was incorrect.",
                    )

                st.session_state.attention_done = True

    if st.button(
        "🔄 New Attention Trial",
        use_container_width=True,
    ):

        for key in [
            "attention_items",
            "attention_target",
            "attention_start",
            "attention_done",
        ]:

            st.session_state.pop(
                key,
                None,
            )

        st.rerun()


def run_memory_experiment():

    st.markdown("### 🧠 Memory Experiment")

    st.write(
        "Memorize the sequence and reproduce it."
    )

    if "memory_sequence" not in st.session_state:

        sequence = [
            random.randint(1, 9)
            for _ in range(6)
        ]

        st.session_state.memory_sequence = (
            sequence
        )

        st.session_state.memory_hidden = False

    sequence = st.session_state.memory_sequence

    if not st.session_state.memory_hidden:

        st.info(
            "Memorize this sequence:"
        )

        st.markdown(
            f"""
            <div style="
                font-size:38px;
                text-align:center;
                letter-spacing:12px;
                padding:25px;
            ">
                {" ".join(map(str, sequence))}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Hide Sequence",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.memory_hidden = True
            st.rerun()

    else:

        answer = st.text_input(
            "Enter the sequence",
            placeholder="Example: 123456",
        )

        if st.button(
            "Check Memory",
            type="primary",
            use_container_width=True,
        ):

            expected = "".join(
                map(str, sequence)
            )

            if answer.strip() == expected:

                st.success(
                    "Excellent! Sequence recalled correctly."
                )

                lab_save_result(
                    "Memory",
                    100,
                    100,
                    "The sequence was reproduced correctly.",
                )

            else:

                st.error(
                    "Not quite. The sequence was:"
                )

                st.code(expected)

                lab_save_result(
                    "Memory",
                    0,
                    0,
                    "The sequence was not reproduced correctly.",
                )

        if st.button(
            "🔄 New Memory Trial",
            use_container_width=True,
        ):

            for key in [
                "memory_sequence",
                "memory_hidden",
            ]:

                st.session_state.pop(
                    key,
                    None,
                )

            st.rerun()


def run_decision_experiment():

    st.markdown("### 💰 Decision & Reward")

    st.write(
        "Choose between an immediate reward "
        "and a larger delayed reward."
    )

    st.markdown(
        """
        <div class="neuro-card">

        <h3>Option A</h3>

        <p>
        Receive <b>PKR 1,000 today</b>
        </p>

        </div>

        <div class="neuro-card">

        <h3>Option B</h3>

        <p>
        Receive <b>PKR 1,500 after 30 days</b>
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Which would you choose?",
        [
            "PKR 1,000 today",
            "PKR 1,500 after 30 days",
        ],
    )

    if st.button(
        "Submit Decision",
        type="primary",
        use_container_width=True,
    ):

        if choice == "PKR 1,000 today":

            observation = (
                "The choice favors immediate reward."
            )

        else:

            observation = (
                "The choice favors delayed reward."
            )

        st.success(
            "Decision recorded."
        )

        st.info(
            observation
            + " This task demonstrates "
            "a simplified reward-delay decision scenario; "
            "it does not diagnose personality or behavior."
        )

        lab_save_result(
            "Decision & Reward",
            100,
            100,
            observation,
        )


def run_stroop_experiment():

    st.markdown(
        "### 🧠 Stroop / Cognitive Control"
    )

    st.write(
        "Read the COLOR of the word, "
        "not the word itself."
    )

    words = [
        ("RED", "blue"),
        ("BLUE", "red"),
        ("GREEN", "purple"),
        ("YELLOW", "green"),
    ]

    word, color = random.choice(words)

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:48px;
            font-weight:900;
            color:{color};
            padding:25px;
        ">
            {word}
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.radio(
        "What is the displayed color?",
        [
            "red",
            "blue",
            "green",
            "purple",
            "yellow",
        ],
    )

    if st.button(
        "Submit Color",
        type="primary",
        use_container_width=True,
    ):

        if answer == color:

            st.success(
                "Correct! Good cognitive control."
            )

            lab_save_result(
                "Stroop",
                100,
                100,
                "Color identification was correct.",
            )

        else:

            st.error(
                f"Incorrect. The displayed color was {color}."
            )

            lab_save_result(
                "Stroop",
                0,
                0,
                "Color identification was incorrect.",
            )


def run_pattern_experiment():

    st.markdown(
        "### 🔢 Pattern Recognition"
    )

    st.write(
        "Identify the next number."
    )

    sequence = [
        2,
        4,
        8,
        16,
        32,
    ]

    st.markdown(
        f"""
        <div class="world-card">
            <h2>
                {" → ".join(map(str, sequence))} → ?
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.number_input(
        "Your answer",
        min_value=0,
        max_value=1000,
        value=0,
        step=1,
    )

    if st.button(
        "Check Pattern",
        type="primary",
        use_container_width=True,
    ):

        if answer == 64:

            st.success(
                "Correct! The pattern doubles each time."
            )

            lab_save_result(
                "Pattern Recognition",
                100,
                100,
                "Correctly identified the doubling pattern.",
            )

        else:

            st.error(
                "Not quite. The correct answer is 64."
            )

            lab_save_result(
                "Pattern Recognition",
                0,
                0,
                "Pattern was not identified correctly.",
            )


def page_lab():

    st.markdown(
        """
        <div class="hero">
            <h1>🧪 Cognitive Lab</h1>
            <p>
                Run interactive cognitive experiments
                in a simulated neuroscience environment.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(
        "All neural signals and laboratory measurements "
        "shown in NEUROLENS are simulated/conceptual "
        "unless explicitly stated otherwise. They are "
        "not real EEG, fMRI or clinical measurements."
    )

    experiment = st.selectbox(
        "Choose experiment",
        [
            "Attention",
            "Memory",
            "Decision & Reward",
            "Stroop / Cognitive Control",
            "Pattern Recognition",
        ],
    )

    st.markdown(
        """
        <div class="neuro-card">
            <h3>🔬 Virtual Equipment</h3>
            <p>
            EEG Simulator · Eye Tracker ·
            Reaction-Time System · Cognitive Task Monitor ·
            Physiological Sensor
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if experiment == "Attention":
        run_attention_experiment()

    elif experiment == "Memory":
        run_memory_experiment()

    elif experiment == "Decision & Reward":
        run_decision_experiment()

    elif experiment == "Stroop / Cognitive Control":
        run_stroop_experiment()

    elif experiment == "Pattern Recognition":
        run_pattern_experiment()

    st.divider()

    st.markdown("### 📊 Recent Lab Results")

    if st.session_state.lab_results:

        for result in reversed(
            st.session_state.lab_results[-5:]
        ):

            st.markdown(
                f"""
                <div class="neuro-card">

                <b>
                    {result["experiment"]}
                </b>

                <br>

                Score:
                {result["score"]}

                <br>

                Accuracy:
                {result["accuracy"]}%

                <br>

                <span class="muted">
                    {result["observation"]}
                </span>

                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "Complete an experiment to see results here."
        )


# ============================================================
# BRAIN JOURNEY
# ============================================================

def page_brain_journey():

    st.markdown(
        """
        <div class="hero">
            <h1>🧠 Brain Journey</h1>
            <p>
                Explore major concepts and systems
                involved in cognition and behavior.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    concepts = [
        (
            "Neuron",
            "neuron.png",
            "The neuron is a basic functional unit of the nervous system. "
            "Neurons receive, process and transmit information."
        ),

        (
            "Synapse",
            "synapse.png",
            "A synapse is a communication junction between neurons "
            "or between a neuron and another target cell."
        ),

        (
            "Neural Signaling",
            "neural_signaling.gif",
            "Neural signaling involves electrical activity within neurons "
            "and chemical or electrical communication between cells."
        ),

        (
            "Prefrontal Cortex",
            "prefrontal_cortex.png",
            BRAIN_SYSTEMS["Prefrontal Cortex"],
        ),

        (
            "Hippocampus",
            "hippocampus.png",
            BRAIN_SYSTEMS["Hippocampus"],
        ),

        (
            "Striatum",
            "striatum.png",
            BRAIN_SYSTEMS["Striatum"],
        ),

        (
            "Anterior Cingulate Cortex",
            "acc.png",
            BRAIN_SYSTEMS["Anterior Cingulate Cortex"],
        ),

        (
            "Attention Networks",
            "attention_network.png",
            BRAIN_SYSTEMS["Attention Networks"],
        ),
    ]

    names = [
        item[0]
        for item in concepts
    ]

    if (
        st.session_state.selected_brain_system
        not in names
    ):

        st.session_state.selected_brain_system = names[0]

    selected = st.selectbox(
        "Choose a concept",
        names,
        index=names.index(
            st.session_state.selected_brain_system
        ),
    )

    st.session_state.selected_brain_system = selected

    selected_data = next(
        item
        for item in concepts
        if item[0] == selected
    )

    title, image_file, description = selected_data

    st.markdown(
        f"""
        <div class="world-card">
            <h2>{title}</h2>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not show_image(
        image_file,
        width=750,
    ):

        st.markdown(
            f"""
            <div class="neuro-card"
                 style="text-align:center">

                <div style="font-size:90px">
                    🧠
                </div>

                <h3>
                    {title}
                </h3>

                <p>
                    Add <b>{image_file}</b>
                    to your assets folder to display
                    the dedicated visual.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button(
        "🤖 Ask Ayna About This System",
        use_container_width=True,
    ):

        st.session_state.page = "Ask Ayna"

        st.session_state.chat.append(
            {
                "role": "user",
                "text":
                    f"Explain {title} in cognitive neuroscience.",
            }
        )

        st.rerun()

    st.divider()

    col1, col2, col3 = st.columns(3)

    current_index = names.index(selected)

    with col1:

        if st.button(
            "⬅️ Previous",
            use_container_width=True,
        ):

            new_index = (
                current_index - 1
            ) % len(names)

            st.session_state.selected_brain_system = (
                names[new_index]
            )

            st.rerun()

    with col2:

        if st.button(
            "🔄 Restart",
            use_container_width=True,
        ):

            st.session_state.selected_brain_system = (
                names[0]
            )

            st.rerun()

    with col3:

        if st.button(
            "Next ➡️",
            use_container_width=True,
        ):

            new_index = (
                current_index + 1
            ) % len(names)

            st.session_state.selected_brain_system = (
                names[new_index]
            )

            st.rerun()


# ============================================================
# 12-PIECE BRAIN JIGSAW
# ============================================================

def create_puzzle_board(size):

    total = size * size

    solved = list(
        range(total)
    )

    board = solved.copy()

    for _ in range(
        max(30, total * 8)
    ):

        a = random.randrange(total)
        b = random.randrange(total)

        board[a], board[b] = (
            board[b],
            board[a],
        )

    if board == solved:

        board[0], board[1] = (
            board[1],
            board[0],
        )

    return board, solved


def puzzle_grid_html(
    board,
    size,
    solution,
):

    cells = []

    for index, tile in enumerate(board):

        correct = (
            tile == solution[index]
        )

        status = (
            "correct"
            if correct
            else "tile"
        )

        cells.append(
            f"""
            <div class="{status}">
                {tile + 1}
            </div>
            """
        )

    return "".join(cells)


def page_puzzle():

    st.markdown(
        """
        <div class="hero">
            <h1>🧩 Brain Jigsaw</h1>
            <p>
                Reconstruct the brain picture
                by solving the puzzle.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "This is a cognitive puzzle challenge. "
        "It does not measure intelligence or brain activity."
    )

    # --------------------------------------------------------
    # PUZZLE CONTROLS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        size_option = st.selectbox(
            "Puzzle size",
            [
                "3 × 4 — 12 pieces",
                "4 × 4 — 16 pieces",
                "5 × 5 — 25 pieces",
            ],
        )

    with col2:

        challenge_mode = st.selectbox(
            "Challenge mode",
            [
                "Standard",
                "Time Challenge",
                "Minimum Moves",
            ],
        )

    with col3:

        if st.button(
            "🔄 New Puzzle",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.puzzle_board = None
            st.session_state.puzzle_solution = None
            st.session_state.puzzle_moves = 0
            st.session_state.puzzle_finished = False
            st.session_state.puzzle_started = False
            st.session_state.puzzle_start_time = None

            st.rerun()

    # --------------------------------------------------------
    # 12 PIECE MODE
    # --------------------------------------------------------

    if size_option.startswith("3 × 4"):

        rows = 3
        cols = 4
        total = 12

    elif size_option.startswith("4 × 4"):

        rows = 4
        cols = 4
        total = 16

    else:

        rows = 5
        cols = 5
        total = 25

    # --------------------------------------------------------
    # CREATE PUZZLE
    # --------------------------------------------------------

    if (
        st.session_state.puzzle_board is None
        or
        st.session_state.puzzle_solution is None
    ):

        board = list(
            range(total)
        )

        solution = list(
            range(total)
        )

        random.shuffle(board)

        if board == solution:

            board[0], board[1] = (
                board[1],
                board[0],
            )

        st.session_state.puzzle_board = board
        st.session_state.puzzle_solution = solution
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_finished = False
        st.session_state.puzzle_started = True
        st.session_state.puzzle_start_time = time.time()

    board = st.session_state.puzzle_board
    solution = st.session_state.puzzle_solution

    # --------------------------------------------------------
    # IMAGE PREVIEW
    # --------------------------------------------------------

    brain_path = asset_path(
        "brain.png"
    )

    if brain_path:

        st.markdown(
            "### 🧠 Reference Image"
        )

        st.image(
            brain_path,
            use_container_width=True,
        )

    else:

        st.warning(
            "Add `brain.png` to the project root "
            "or `assets/brain.png` to use the brain image."
        )

    # --------------------------------------------------------
    # PUZZLE INFORMATION
    # --------------------------------------------------------

    if st.session_state.puzzle_start_time:

        elapsed = int(
            time.time()
            - st.session_state.puzzle_start_time
        )

    else:

        elapsed = 0

    minutes = elapsed // 60
    seconds = elapsed % 60

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🧩 Pieces",
            total,
        )

    with col2:
        st.metric(
            "🔢 Moves",
            st.session_state.puzzle_moves,
        )

    with col3:
        st.metric(
            "⏱️ Time",
            f"{minutes:02d}:{seconds:02d}",
        )

    with col4:

        correct_count = sum(
            1
            for i, tile in enumerate(board)
            if tile == solution[i]
        )

        st.metric(
            "✅ Correct",
            f"{correct_count}/{total}",
        )

    # --------------------------------------------------------
    # ACTUAL VISUAL PUZZLE
    # --------------------------------------------------------

    st.markdown(
        "### 🧩 Arrange the Pieces"
    )

    st.caption(
        "On supported browsers, drag pieces with your finger "
        "or mouse. The visual puzzle area below provides "
        "the interactive board."
    )

    puzzle_html = f"""
    <div id="neurolens-puzzle"
         style="
            width:100%;
            max-width:720px;
            margin:auto;
            display:grid;
            grid-template-columns:repeat({cols},1fr);
            gap:5px;
            background:#0b1225;
            padding:8px;
            border-radius:20px;
         ">

    """

    for index, tile in enumerate(board):

        correct = (
            tile == solution[index]
        )

        puzzle_html += f"""
        <div
            draggable="true"
            data-index="{index}"
            data-tile="{tile}"
            style="
                aspect-ratio:1/1;
                border-radius:12px;
                border:2px solid
                    {'#38d996' if correct else 'rgba(255,255,255,.12)'};
                background:
                    {'linear-gradient(135deg,#123c32,#1d6b55)'
                     if correct
                     else 'linear-gradient(135deg,#172343,#25345d)'};
                display:flex;
                align-items:center;
                justify-content:center;
                color:white;
                font-size:clamp(18px,4vw,30px);
                font-weight:800;
                cursor:grab;
                user-select:none;
                touch-action:none;
                transition:.18s;
                box-sizing:border-box;
            "
        >
            {tile + 1}
        </div>
        """

    puzzle_html += """
    </div>

    <div id="puzzle-status"
         style="
            text-align:center;
            margin-top:14px;
            color:#aebbd4;
            font-size:14px;
         ">
        Drag one piece onto another piece to swap them.
    </div>

    <script>

    const board = document.getElementById(
        "neurolens-puzzle"
    );

    const status = document.getElementById(
        "puzzle-status"
    );

    let dragged = null;

    board.querySelectorAll("[draggable=true]").forEach(
        function(tile) {

            tile.addEventListener(
                "dragstart",
                function(event) {

                    dragged = tile;

                    tile.style.opacity = "0.45";

                    event.dataTransfer.effectAllowed =
                        "move";
                }
            );

            tile.addEventListener(
                "dragend",
                function() {

                    tile.style.opacity = "1";
                    dragged = null;
                }
            );

            tile.addEventListener(
                "dragover",
                function(event) {

                    event.preventDefault();

                    tile.style.transform =
                        "scale(0.96)";
                }
            );

            tile.addEventListener(
                "dragleave",
                function() {

                    tile.style.transform =
                        "scale(1)";
                }
            );

            tile.addEventListener(
                "drop",
                function(event) {

                    event.preventDefault();

                    tile.style.transform =
                        "scale(1)";

                    if (
                        !dragged ||
                        dragged === tile
                    ) {
                        return;
                    }

                    const first =
                        dragged.parentNode;

                    const firstIndex =
                        Number(
                            dragged.dataset.index
                        );

                    const secondIndex =
                        Number(
                            tile.dataset.index
                        );

                    const firstClone =
                        dragged.cloneNode(true);

                    const secondClone =
                        tile.cloneNode(true);

                    first.replaceChild(
                        secondClone,
                        dragged
                    );

                    first.replaceChild(
                        firstClone,
                        tile
                    );

                    status.textContent =
                        "Pieces swapped. "
                        + "Press the button below "
                        + "to check the puzzle.";

                    dragged = null;
                }
            );
        }
    );

    </script>
    """

    components.html(
        puzzle_html,
        height=760,
        scrolling=False,
    )

    # --------------------------------------------------------
    # IMPORTANT COMPATIBILITY FALLBACK
    # --------------------------------------------------------

    st.caption(
        "Puzzle interaction is rendered in the browser. "
        "The reference image remains visible above."
    )

    # --------------------------------------------------------
    # CHECK / DEMO SOLVE
    # --------------------------------------------------------

    st.markdown("### 🔍 Puzzle Controls")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Check Puzzle",
            type="primary",
            use_container_width=True,
        ):

            if board == solution:

                st.session_state.puzzle_finished = True

                score = max(
                    1000
                    - st.session_state.puzzle_moves * 10
                    - elapsed,
                    100,
                )

                st.success(
                    f"🎉 Puzzle complete! "
                    f"Score: {score}"
                )

                st.balloons()

                result = {
                    "pieces": total,
                    "moves":
                        st.session_state.puzzle_moves,
                    "time": elapsed,
                    "score": score,
                }

                st.session_state.puzzle_results.append(
                    result
                )

                user_id = current_user_id()

                if user_id:

                    db_insert(
                        "brain_puzzle_results",
                        {
                            "user_id": user_id,
                            "score": score,
                            "moves":
                                st.session_state.puzzle_moves,
                        },
                    )

            else:

                st.warning(
                    "The puzzle is not complete yet."
                )

    with col2:

        if st.button(
            "🔄 Reset Puzzle",
            use_container_width=True,
        ):

            st.session_state.puzzle_board = None
            st.session_state.puzzle_solution = None
            st.session_state.puzzle_moves = 0
            st.session_state.puzzle_finished = False
            st.session_state.puzzle_started = False
            st.session_state.puzzle_start_time = None

            st.rerun()

    # --------------------------------------------------------
    # PUZZLE NOTE
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="warning-panel">

        <b>Research note</b><br>

        This puzzle is designed as an interactive
        visual/cognitive challenge. Completion time,
        moves and score are game metrics only and should
        not be interpreted as clinical or diagnostic
        measures of cognition.

        </div>
        """,
        unsafe_allow_html=True,
    )
    
# ============================================================
# END OF PART 2
# ============================================================
# ============================================================
# PART 3 — CHALLENGES + ASK AYNA + AI MOOD/FACE + RESEARCH
# ============================================================

# ------------------------------------------------------------
# BRAIN CHALLENGES
# ------------------------------------------------------------

def save_exercise_result(exercise_name, score, details=None):
    result = {
        "exercise": clean_text(exercise_name, 100),
        "score": float(score),
        "details": details or {},
        "timestamp": time.time(),
    }

    st.session_state.exercise_scores.append(result)

    user_id = current_user_id()
    if user_id:
        db_insert(
            "exercise_results",
            {
                "user_id": user_id,
                "exercise": clean_text(exercise_name, 100),
                "score": float(score),
                "result_data": result,
            },
        )


def challenge_working_memory():
    st.subheader("🧠 Working Memory")

    if "wm_sequence" not in st.session_state:
        st.session_state.wm_sequence = ""
        st.session_state.wm_started = False
        st.session_state.wm_show = False
        st.session_state.wm_score = None

    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
        key="wm_difficulty",
    )

    lengths = {
        "Easy": 4,
        "Medium": 6,
        "Hard": 8,
    }

    length = lengths[difficulty]

    if st.button(
        "▶ Start Memory Challenge",
        use_container_width=True,
        key="start_wm",
    ):
        sequence = "".join(str(random.randint(0, 9)) for _ in range(length))

        st.session_state.wm_sequence = sequence
        st.session_state.wm_started = True
        st.session_state.wm_show = True
        st.session_state.wm_score = None
        st.rerun()

    if st.session_state.wm_started:

        if st.session_state.wm_show:
            st.markdown(
                f"""
                <div class="nl-card" style="text-align:center;">
                    <div style="font-size:14px;color:#9ca3af;">
                        Memorize this sequence
                    </div>
                    <div style="font-size:38px;font-weight:800;
                    letter-spacing:8px;margin-top:15px;">
                        {st.session_state.wm_sequence}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "I memorized it",
                use_container_width=True,
                key="wm_hide",
            ):
                st.session_state.wm_show = False
                st.rerun()

        else:
            answer = st.text_input(
                "Enter the sequence:",
                max_chars=20,
                key="wm_answer",
            )

            if st.button(
                "Check Answer",
                type="primary",
                use_container_width=True,
                key="wm_check",
            ):
                if answer.strip() == st.session_state.wm_sequence:
                    score = 100
                    st.session_state.wm_score = score

                    save_exercise_result(
                        "Working Memory",
                        score,
                        {
                            "difficulty": difficulty,
                            "correct": True,
                        },
                    )

                    st.success("✅ Correct! Excellent working-memory performance.")

                else:
                    score = 0
                    st.session_state.wm_score = score

                    save_exercise_result(
                        "Working Memory",
                        score,
                        {
                            "difficulty": difficulty,
                            "correct": False,
                        },
                    )

                    st.error("❌ Not quite. Try another round.")

            if st.session_state.wm_score is not None:
                st.metric(
                    "Score",
                    f"{st.session_state.wm_score}/100",
                )


def challenge_attention():
    st.subheader("👁️ Attention Challenge")

    if "attention_target" not in st.session_state:
        st.session_state.attention_target = ""
        st.session_state.attention_options = []
        st.session_state.attention_started = False

    if st.button(
        "▶ Start Attention Challenge",
        use_container_width=True,
        key="start_attention_challenge",
    ):
        target = random.choice(["X", "K", "M", "A", "R"])

        options = []

        for _ in range(15):
            options.append(random.choice(["X", "K", "M", "A", "R"]))

        correct_position = random.randint(0, len(options) - 1)
        options[correct_position] = target

        st.session_state.attention_target = target
        st.session_state.attention_options = options
        st.session_state.attention_correct = correct_position
        st.session_state.attention_started = True
        st.session_state.attention_score = None

        st.rerun()

    if st.session_state.attention_started:

        target = st.session_state.attention_target

        st.markdown(
            f"""
            <div class="nl-card" style="text-align:center;">
                <div style="color:#9ca3af;">Find the target</div>
                <div style="font-size:38px;font-weight:900;">
                    {target}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        columns = st.columns(5)

        for index, item in enumerate(
            st.session_state.attention_options
        ):
            with columns[index % 5]:

                if st.button(
                    item,
                    key=f"attention_item_{index}",
                    use_container_width=True,
                ):

                    if index == st.session_state.attention_correct:
                        score = 100

                        st.success("🎯 Correct target!")

                        save_exercise_result(
                            "Attention",
                            score,
                            {
                                "correct": True,
                            },
                        )

                    else:
                        score = 0

                        st.error("❌ That was not the target.")

                        save_exercise_result(
                            "Attention",
                            score,
                            {
                                "correct": False,
                            },
                        )

                    st.session_state.attention_score = score


def challenge_pattern():
    st.subheader("🔢 Pattern Recognition")

    patterns = [
        (
            ["2", "4", "8", "16", "?"],
            "32",
        ),
        (
            ["3", "6", "12", "24", "?"],
            "48",
        ),
        (
            ["5", "10", "20", "40", "?"],
            "80",
        ),
        (
            ["1", "4", "9", "16", "?"],
            "25",
        ),
    ]

    if "pattern_question" not in st.session_state:
        st.session_state.pattern_question = random.choice(patterns)
        st.session_state.pattern_answered = False

    question, answer = st.session_state.pattern_question

    st.markdown(
        f"""
        <div class="nl-card" style="text-align:center;">
            <div style="font-size:30px;font-weight:800;">
                {" → ".join(question)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_answer = st.text_input(
        "What comes next?",
        key="pattern_answer",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Check",
            type="primary",
            use_container_width=True,
            key="pattern_check",
        ):

            if user_answer.strip() == answer:

                st.success("✅ Correct!")

                save_exercise_result(
                    "Pattern Recognition",
                    100,
                    {"correct": True},
                )

            else:

                st.error(f"❌ Incorrect. The answer was {answer}.")

                save_exercise_result(
                    "Pattern Recognition",
                    0,
                    {"correct": False},
                )

    with col2:
        if st.button(
            "New Pattern",
            use_container_width=True,
            key="new_pattern",
        ):
            st.session_state.pattern_question = random.choice(patterns)
            st.rerun()


def challenge_decision():
    st.subheader("💰 Decision & Reward")

    st.markdown(
        """
        <div class="nl-card">
            <h3>Choose one option</h3>
            <p>
            You can receive <b>PKR 1,000 today</b>,
            or wait 30 days for <b>PKR 1,500</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Your decision:",
        [
            "PKR 1,000 today",
            "PKR 1,500 after 30 days",
        ],
        key="decision_choice",
    )

    if st.button(
        "Submit Decision",
        type="primary",
        use_container_width=True,
        key="decision_submit",
    ):

        if "30 days" in choice:
            interpretation = (
                "You selected the delayed larger reward. "
                "This choice is consistent with greater willingness "
                "to wait for a larger payoff."
            )
        else:
            interpretation = (
                "You selected the immediate reward. "
                "This choice prioritizes immediate availability."
            )

        st.info(interpretation)

        save_exercise_result(
            "Decision & Reward",
            100,
            {
                "choice": choice,
                "interpretation": interpretation,
            },
        )


def challenge_stroop():
    st.subheader("🎨 Stroop Cognitive Control")

    words = [
        ("RED", "blue"),
        ("BLUE", "red"),
        ("GREEN", "yellow"),
        ("YELLOW", "green"),
    ]

    if "stroop_item" not in st.session_state:
        st.session_state.stroop_item = random.choice(words)

    word, displayed_color = st.session_state.stroop_item

    st.markdown(
        f"""
        <div class="nl-card" style="text-align:center;">
            <div style="font-size:16px;color:#9ca3af;">
                Identify the ink colour, not the word.
            </div>
            <div style="
                font-size:44px;
                font-weight:900;
                color:{displayed_color};
                margin-top:15px;
            ">
                {word}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    options = ["red", "blue", "green", "yellow"]

    answer = st.radio(
        "Ink colour:",
        options,
        horizontal=True,
        key="stroop_answer",
    )

    if st.button(
        "Check",
        type="primary",
        use_container_width=True,
        key="stroop_check",
    ):

        if answer == displayed_color:

            st.success("✅ Correct cognitive-control response.")

            save_exercise_result(
                "Stroop Control",
                100,
                {
                    "correct": True,
                },
            )

        else:

            st.error("❌ Incorrect response.")

            save_exercise_result(
                "Stroop Control",
                0,
                {
                    "correct": False,
                },
            )

        st.session_state.stroop_item = random.choice(words)
        st.rerun()


def challenge_reaction():
    st.subheader("⚡ Quick Reaction")

    st.markdown(
        """
        <div class="nl-card">
            <h3>Reaction task</h3>
            <p>
            This simplified task uses your interaction speed as a
            basic performance indicator. It is not a clinical
            measurement of reaction time.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "reaction_started" not in st.session_state:
        st.session_state.reaction_started = False
        st.session_state.reaction_start_time = None

    if not st.session_state.reaction_started:

        if st.button(
            "🟢 Start",
            type="primary",
            use_container_width=True,
            key="reaction_start",
        ):

            st.session_state.reaction_started = True
            st.session_state.reaction_start_time = time.time()

            st.rerun()

    else:

        elapsed = (
            time.time()
            - st.session_state.reaction_start_time
        )

        st.markdown(
            """
            <div class="nl-card" style="text-align:center;">
                <div style="font-size:32px;">
                    ⚡ TAP NOW
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "TAP",
            type="primary",
            use_container_width=True,
            key="reaction_tap",
        ):

            reaction_time = time.time() - st.session_state.reaction_start_time

            score = max(
                0,
                min(
                    100,
                    int(100 - reaction_time * 50),
                ),
            )

            st.success(
                f"Reaction time: {reaction_time:.3f} seconds"
            )

            st.metric(
                "Performance score",
                f"{score}/100",
            )

            save_exercise_result(
                "Quick Reaction",
                score,
                {
                    "reaction_time": reaction_time,
                },
            )

            st.session_state.reaction_started = False


def page_challenges():

    st.title("🧠 Brain Challenges")

    st.caption(
        "Interactive cognitive exercises for attention, memory, "
        "pattern recognition, decision-making and cognitive control."
    )

    challenge = st.selectbox(
        "Choose a challenge",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision & Reward",
            "Stroop Cognitive Control",
            "Quick Reaction",
        ],
        key="challenge_selector",
    )

    st.divider()

    if challenge == "Working Memory":
        challenge_working_memory()

    elif challenge == "Attention":
        challenge_attention()

    elif challenge == "Pattern Recognition":
        challenge_pattern()

    elif challenge == "Decision & Reward":
        challenge_decision()

    elif challenge == "Stroop Cognitive Control":
        challenge_stroop()

    elif challenge == "Quick Reaction":
        challenge_reaction()


# ------------------------------------------------------------
# ASK AYNA — GEMINI AI
# ------------------------------------------------------------

def ask_ayna_ai(question):

    if not question.strip():
        return "Please enter a question."

    if not ai_available():
        return (
            "Gemini AI is not connected yet. "
            "Please add GEMINI_API_KEY in Streamlit Secrets."
        )

    prompt = f"""
You are Ayna, the AI guide inside NEUROLENS.

NEUROLENS focuses on:
- cognitive neuroscience
- cognition
- behaviour
- attention
- learning
- memory
- decision-making
- consciousness
- brain systems
- AI and neuroscience

Answer clearly and naturally.

Rules:
- Do not diagnose medical or psychiatric conditions.
- Do not claim to read someone's mind.
- Do not claim that a game measures brain activity.
- Clearly distinguish educational simulation from clinical measurement.
- If the question requires a professional diagnosis, recommend an appropriate qualified professional.
- Keep answers understandable.
- Be scientifically cautious.
- Do not invent research findings.

User question:
{clean_text(question, 3000)}
"""

    result = ai_generate(prompt)

    if result:
        return result

    return (
        "I could not generate a reliable response right now. "
        "Please try again."
    )


def page_ask_ayna():

    st.title("🤖 Ask Ayna")

    st.caption(
        "Your NEUROLENS AI guide for cognition, behaviour and neuroscience."
    )

    if "ayna_messages" not in st.session_state:
        st.session_state.ayna_messages = []

    for message in st.session_state.ayna_messages:

        role = message.get("role", "assistant")
        content = message.get("content", "")

        with st.chat_message(role):
            st.write(content)

    question = st.chat_input(
        "Ask Ayna about the brain, behaviour or cognition..."
    )

    if question:

        question = clean_text(question, 3000)

        st.session_state.ai_requests += 1

        st.session_state.ai_request_history.append(
            {
                "question": question,
                "time": time.time(),
            }
        )

        st.session_state.ayna_messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        answer = ask_ayna_ai(question)

        st.session_state.ayna_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    st.divider()

    if st.session_state.ayna_messages:

        last_answer = None

        for message in reversed(
            st.session_state.ayna_messages
        ):
            if message.get("role") == "assistant":
                last_answer = message.get("content", "")
                break

        if last_answer:

            st.subheader("🔊 Voice")

            if st.button(
                "🔊 Speak Ayna",
                use_container_width=True,
                key="speak_ayna",
            ):
                speak_text(last_answer)


# ------------------------------------------------------------
# AI MOOD + VOICE ANALYSIS
# ------------------------------------------------------------

def analyze_voice_with_ai(audio_bytes, mime_type="audio/wav"):

    if not ai_available():
        return {
            "transcript": "",
            "emoji": "🧩",
            "vibe_label": "AI unavailable",
            "explanation": "Gemini is not connected.",
        }

    try:

        from google.genai import types

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        prompt = """
Return ONLY valid JSON with these keys:

transcript
emoji
vibe_label
explanation

vibe_label must be one of:
Positive/energetic-sounding
Calm-sounding
Neutral/mixed
Tense/stressed-sounding
Low-energy-sounding
Uncertain/mixed

Use observable communication/acoustic cues only.

Do NOT claim:
- hidden emotions
- personality
- mental illness
- diagnosis
- certainty about internal state

The result is an AI-assisted communication/vocal-vibe estimate.
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type,
                ),
            ],
        )

        text = getattr(
            response,
            "text",
            "",
        ) or ""

        text = re.sub(
            r"```(?:json)?|```",
            "",
            text,
            flags=re.I,
        ).strip()

        try:
            return json.loads(text)

        except Exception:

            return {
                "transcript": text,
                "emoji": "🧩",
                "vibe_label": "Uncertain/mixed",
                "explanation": (
                    "The AI response could not be structured "
                    "reliably."
                ),
            }

    except Exception as exc:

        st.session_state.last_error = str(exc)

        return {
            "transcript": "",
            "emoji": "⚠️",
            "vibe_label": "Analysis unavailable",
            "explanation": (
                "The voice analysis could not be completed safely."
            ),
        }


def analyze_face_with_ai(image_bytes):

    if not ai_available():
        return {
            "emoji": "🧩",
            "expression": "AI unavailable",
            "explanation": "Gemini is not connected.",
        }

    try:

        from google.genai import types

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        prompt = """
Analyze the visible facial expression only.

Return ONLY valid JSON:

{
  "emoji": "one suitable emoji",
  "expression": "brief visible expression label",
  "explanation": "brief explanation based only on visible facial cues"
}

Important:
- Do not identify the person.
- Do not infer personality.
- Do not infer hidden thoughts.
- Do not diagnose mental health conditions.
- Do not claim certainty about emotion.
- Use wording such as "appears", "may suggest", or "visible expression".
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
            ],
        )

        text = getattr(
            response,
            "text",
            "",
        ) or ""

        text = re.sub(
            r"```(?:json)?|```",
            "",
            text,
            flags=re.I,
        ).strip()

        try:
            return json.loads(text)

        except Exception:

            return {
                "emoji": "🧩",
                "expression": "Uncertain",
                "explanation": text,
            }

    except Exception:

        return {
            "emoji": "⚠️",
            "expression": "Analysis unavailable",
            "explanation": (
                "The facial-expression analysis could not be completed."
            ),
        }


def page_mood():

    st.title("🎭 AI Mood & Behaviour")

    st.caption(
        "AI-assisted interpretation of visible voice and facial-expression cues."
    )

    st.warning(
        "This is an educational AI estimate, not mind-reading, "
        "a psychological diagnosis, or a measurement of true internal emotion."
    )

    tab_voice, tab_face, tab_combined = st.tabs(
        [
            "🎙️ Voice",
            "📷 Face",
            "🧠 Combined",
        ]
    )

    with tab_voice:

        st.subheader("🎙️ Voice Vibe")

        if not hasattr(st, "audio_input"):
            st.info(
                "Your current Streamlit version does not expose "
                "the audio recorder."
            )
        else:

            voice = st.audio_input(
                "Record a short voice sample",
                key="mood_voice_input",
            )

            if voice:

                if st.button(
                    "📤 Analyze Voice",
                    type="primary",
                    use_container_width=True,
                    key="analyze_voice",
                ):

                    with st.spinner(
                        "Analyzing vocal communication cues..."
                    ):

                        result = analyze_voice_with_ai(
                            voice.getvalue(),
                            voice.type or "audio/wav",
                        )

                    st.session_state.voice_result = result

                    user_id = current_user_id()

                    if user_id:
                        db_insert(
                            "voice_mood_results",
                            {
                                "user_id": user_id,
                                "result_data": result,
                            },
                        )

                    st.rerun()

            if st.session_state.voice_result:

                result = st.session_state.voice_result

                st.markdown(
                    f"""
                    <div class="nl-card">
                        <div style="font-size:42px;">
                            {result.get("emoji","🧩")}
                        </div>
                        <h3>
                            {result.get(
                                "vibe_label",
                                "Uncertain/mixed"
                            )}
                        </h3>
                        <p>
                            {result.get(
                                "explanation",
                                ""
                            )}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.subheader("📝 Transcript")

                st.write(
                    result.get(
                        "transcript",
                        "",
                    )
                )

    with tab_face:

        st.subheader("📷 Facial Expression")

        if hasattr(st, "camera_input"):

            photo = st.camera_input(
                "Take a photo",
                key="mood_camera",
            )

            if photo:

                if st.button(
                    "🔍 Analyze Visible Expression",
                    type="primary",
                    use_container_width=True,
                    key="analyze_face",
                ):

                    with st.spinner(
                        "Analyzing visible facial-expression cues..."
                    ):

                        face_result = analyze_face_with_ai(
                            photo.getvalue()
                        )

                    st.session_state.face_result = face_result

                    st.rerun()

        if st.session_state.face_result:

            result = st.session_state.face_result

            st.markdown(
                f"""
                <div class="nl-card" style="text-align:center;">
                    <div style="font-size:48px;">
                        {result.get("emoji","🧩")}
                    </div>
                    <h3>
                        {result.get(
                            "expression",
                            "Uncertain"
                        )}
                    </h3>
                    <p>
                        {result.get(
                            "explanation",
                            ""
                        )}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_combined:

        st.subheader("🧠 Combined Interpretation")

        voice_result = st.session_state.voice_result
        face_result = st.session_state.face_result

        if not voice_result and not face_result:

            st.info(
                "Run a voice analysis or facial-expression analysis first."
            )

        else:

            if voice_result:

                st.markdown(
                    f"""
                    **Voice:** {voice_result.get(
                        "emoji",
                        "🧩"
                    )} {voice_result.get(
                        "vibe_label",
                        "Uncertain/mixed"
                    )}
                    """
                )

            if face_result:

                st.markdown(
                    f"""
                    **Face:** {face_result.get(
                        "emoji",
                        "🧩"
                    )} {face_result.get(
                        "expression",
                        "Uncertain"
                    )}
                    """
                )

            st.info(
                "Different signals can disagree. That does not mean "
                "one signal is 'lying'; it means these AI estimates "
                "should be treated cautiously."
            )


# ------------------------------------------------------------
# RESEARCH WORLD
# ------------------------------------------------------------

def europe_pmc_search(query, page_size=8):

    query = clean_text(query, 250)

    if not query:
        return []

    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    )

    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "resultList",
            {}).get(
                "result",
                [],
            )

    except Exception:

        return []


def research_ai_summary(title, abstract):

    if not abstract:
        return (
            "No abstract was available for this paper."
        )

    prompt = f"""
Create a concise scientific summary of the following research paper.

Title:
{clean_text(title, 500)}

Abstract:
{clean_text(abstract, 6000)}

Return:
1. Research focus
2. Main finding
3. Method/context
4. Important limitation
5. Why it matters

Do not invent information not present in the abstract.
"""

    return ai_generate(prompt)


def page_research():

    st.title("🔬 Research World")

    st.caption(
        "Explore biomedical and neuroscience literature through Europe PMC."
    )

    query = st.text_input(
        "Search research papers",
        placeholder=(
            "e.g. cognitive neuroscience attention consciousness"
        ),
        key="research_query",
    )

    if st.button(
        "🔎 Search Literature",
        type="primary",
        use_container_width=True,
        key="research_search",
    ):

        if not query.strip():

            st.warning(
                "Enter a research topic first."
            )

        else:

            with st.spinner(
                "Searching Europe PMC..."
            ):

                results = europe_pmc_search(
                    query,
                    page_size=8,
                )

            st.session_state.research_results = results

            st.rerun()

    results = st.session_state.research_results

    if results:

        st.success(
            f"{len(results)} research results found."
        )

        for index, paper in enumerate(results):

            title = paper.get(
                "title",
                "Untitled paper",
            )

            journal = paper.get(
                "journalTitle",
                "",
            )

            year = paper.get(
                "pubYear",
                "",
            )

            authors = paper.get(
                "authorString",
                "",
            )

            abstract = paper.get(
                "abstractText",
                "",
            )

            pmid = paper.get(
                "pmid",
                "",
            )

            st.markdown(
                f"### {index + 1}. {title}"
            )

            if journal or year:
                st.caption(
                    f"{journal} · {year}"
                )

            if authors:
                st.caption(
                    authors
                )

            if abstract:

                with st.expander(
                    "Read abstract"
                ):
                    st.write(abstract)

            if pmid:

                url = (
                    "https://europepmc.org/article/MED/"
                    + str(pmid)
                )

                st.markdown(
                    f"[Open paper on Europe PMC]({url})"
                )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "🤖 AI Summary",
                    key=f"paper_summary_{index}",
                    use_container_width=True,
                ):

                    if not ai_available():

                        st.warning(
                            "Add GEMINI_API_KEY to use AI summaries."
                        )

                    else:

                        with st.spinner(
                            "Preparing scientific summary..."
                        ):

                            summary = research_ai_summary(
                                title,
                                abstract,
                            )

                        st.session_state[
                            f"summary_{index}"
                        ] = summary

            with col2:

                if st.button(
                    "📝 Save Research Note",
                    key=f"save_note_{index}",
                    use_container_width=True,
                ):

                    note = {
                        "title": title,
                        "journal": journal,
                        "year": year,
                        "pmid": pmid,
                        "abstract": abstract[:5000],
                    }

                    st.session_state.research_notes.append(
                        note
                    )

                    user_id = current_user_id()

                    if user_id:

                        db_insert(
                            "research_notes",
                            {
                                "user_id": user_id,
                                "title": title,
                                "note": abstract[:5000],
                            },
                        )

                    st.success(
                        "Research note saved."
                    )

            summary_key = f"summary_{index}"

            if summary_key in st.session_state:

                st.markdown(
                    """
                    <div class="nl-card">
                        <b>🤖 Ayna Research Summary</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write(
                    st.session_state[summary_key]
                )

            st.divider()

    st.subheader("📚 My Research Notes")

    notes = st.session_state.research_notes

    if not notes:

        st.info(
            "Your saved research notes will appear here."
        )

    else:

        for note in notes:

            with st.expander(
                note.get(
                    "title",
                    "Research note",
                )
            ):

                st.write(
                    note.get(
                        "abstract",
                        "",
                    )
                )


# ============================================================
# END OF PART 3
# ============================================================



