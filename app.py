import os
import re
import json
import time
import secrets
import hashlib
import random

from datetime import datetime
from pathlib import Path

import streamlit as st
import requests


# ============================================================
# OPTIONAL CONNECTIONS
# ============================================================

try:
    from supabase import create_client
except Exception:
    create_client = None


try:
    from google import genai
except Exception:
    genai = None


try:
    from google.genai import types as genai_types
except Exception:
    genai_types = None


try:
    import plotly.graph_objects as go
except Exception:
    go = None


# ============================================================
# NEUROLENS CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"

AI_MODEL = "gemini-2.5-flash"
AI_SESSION_LIMIT = 20


# ============================================================
# SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name)

        if value:
            return str(value)

    except Exception:
        pass

    return os.getenv(name, default)


GEMINI_API_KEY = get_secret(
    "GEMINI_API_KEY"
)

SUPABASE_URL = get_secret(
    "SUPABASE_URL"
)

SUPABASE_KEY = get_secret(
    "SUPABASE_KEY"
)

EASYPAISA_NUMBER = get_secret(
    "EASYPAISA_NUMBER"
)

INTERNATIONAL_PAYMENT_URL = get_secret(
    "INTERNATIONAL_PAYMENT_URL"
)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session():

    defaults = {

        "page": "NeuroWorld",

        "ai_requests": 0,

        "messages": [],

        "private_messages": [],

        "private_hash": None,

        "private_unlocked": False,

        "auth_user": None,

        "lab_history": [],

        "exercise_history": [],

        "puzzle_score": 0,

        "research_results": [],

        "research_notes": [],

        "mood_result": "",

        "selected_friend": None,

        "last_error": "",

        "health_log": [],

        "reaction_started": None,

        "reaction_result": None,

        "memory_sequence": "729418",

        "brain_tile_order": list(range(9)),

        "brain_target_order": list(range(9)),
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            if isinstance(value, list):

                st.session_state[key] = list(value)

            else:

                st.session_state[key] = value


initialize_session()


# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def create_supabase_client():

    if create_client is None:

        return None

    if not SUPABASE_URL:

        return None

    if not SUPABASE_KEY:

        return None

    try:

        return create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

    except Exception:

        return None


supabase = create_supabase_client()


def supabase_available():

    return supabase is not None


# ============================================================
# GEMINI CONNECTION
# ============================================================

@st.cache_resource
def create_gemini_client():

    if genai is None:

        return None

    if not GEMINI_API_KEY:

        return None

    try:

        return genai.Client(
            api_key=GEMINI_API_KEY
        )

    except Exception:

        return None


gemini = create_gemini_client()


def ai_available():

    return gemini is not None


# ============================================================
# DATABASE HELPERS
# ============================================================

def db_select(
    table,
    filters=None,
    limit=100,
    order=None,
    descending=False
):

    if not supabase_available():

        return []

    try:

        query = (
            supabase
            .table(table)
            .select("*")
        )

        for key, value in (
            filters or {}
        ).items():

            query = query.eq(
                key,
                value
            )

        if order:

            query = query.order(
                order,
                desc=descending
            )

        query = query.limit(limit)

        response = query.execute()

        return response.data or []

    except Exception as exc:

        st.session_state.last_error = (
            f"Supabase read {table}: "
            f"{type(exc).__name__}"
        )

        return []


def db_insert(
    table,
    data
):

    if not supabase_available():

        return None

    try:

        return (
            supabase
            .table(table)
            .insert(data)
            .execute()
        )

    except Exception as exc:

        st.session_state.last_error = (
            f"Supabase insert {table}: "
            f"{type(exc).__name__}"
        )

        return None


def db_update(
    table,
    data,
    filters
):

    if not supabase_available():

        return None

    try:

        query = (
            supabase
            .table(table)
            .update(data)
        )

        for key, value in filters.items():

            query = query.eq(
                key,
                value
            )

        return query.execute()

    except Exception as exc:

        st.session_state.last_error = (
            f"Supabase update {table}: "
            f"{type(exc).__name__}"
        )

        return None


def db_delete(
    table,
    filters
):

    if not supabase_available():

        return None

    try:

        query = (
            supabase
            .table(table)
            .delete()
        )

        for key, value in filters.items():

            query = query.eq(
                key,
                value
            )

        return query.execute()

    except Exception as exc:

        st.session_state.last_error = (
            f"Supabase delete {table}: "
            f"{type(exc).__name__}"
        )

        return None


# ============================================================
# AUTH
# ============================================================

def get_auth_user():

    if st.session_state.auth_user:

        return st.session_state.auth_user

    if not supabase_available():

        return None

    try:

        session = (
            supabase.auth.get_session()
        )

        user = getattr(
            session,
            "user",
            None
        )

        if user:

            st.session_state.auth_user = user

            return user

    except Exception:

        pass

    return None


def get_user_id():

    user = get_auth_user()

    if not user:

        return None

    if isinstance(user, dict):

        return user.get("id")

    return getattr(
        user,
        "id",
        None
    )


def get_user_email():

    user = get_auth_user()

    if not user:

        return ""

    if isinstance(user, dict):

        return (
            user.get("email", "")
            or ""
        )

    return (
        getattr(
            user,
            "email",
            ""
        )
        or ""
    )


def safe_username(value):

    return re.sub(
        r"[^A-Za-z0-9_.-]",
        "",
        (value or "").strip()
    )[:30]


def get_username(user_id):

    rows = db_select(
        "profiles",
        {"id": user_id},
        1
    )

    if rows:

        return rows[0].get(
            "username",
            "user"
        )

    return "user"


# ============================================================
# GEMINI / AYNA
# ============================================================

def ask_ayna(
    prompt,
    context=""
):

    if not ai_available():

        return (
            "Ayna AI is not connected yet. "
            "Please add GEMINI_API_KEY "
            "to Streamlit Secrets."
        )

    if (
        st.session_state.ai_requests
        >= AI_SESSION_LIMIT
    ):

        return (
            "Your AI session limit has "
            "been reached. You can still "
            "use the non-AI features."
        )

    system_prompt = """

You are Ayna, the AI assistant inside NEUROLENS.

NEUROLENS is an educational cognitive neuroscience
platform.

You can explain:

- cognition
- attention
- memory
- learning
- reward
- decision-making
- cognitive control
- brain systems
- behaviour
- neuroscience
- AI and behaviour

Safety rules:

Never diagnose a person.

Never claim that a game measures brain activity.

Never claim that voice or facial analysis can
reliably reveal hidden emotions or personality.

Never present self-report scores as clinical
measurements.

Clearly separate evidence, interpretation and
uncertainty.

Use scientifically cautious language.

"""

    full_prompt = (
        system_prompt
        + "\n\nRecent context:\n"
        + context[-5000:]
        + "\n\nUser request:\n"
        + prompt
    )

    try:

        st.session_state.ai_requests += 1

        arguments = {
            "model": AI_MODEL,
            "contents": full_prompt
        }

        if genai_types:

            arguments["config"] = (
                genai_types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=800
                )
            )

        response = (
            gemini
            .models
            .generate_content(
                **arguments
            )
        )

        answer = (
            getattr(
                response,
                "text",
                ""
            )
            or ""
        )

        return answer.strip()

    except Exception as exc:

        return (
            "Ayna could not complete "
            "the request safely. "
            f"Technical error: "
            f"{type(exc).__name__}"
        )


# ============================================================
# ASSET SYSTEM
# ============================================================

def find_asset(name):

    possible = [

        Path(name),

        Path("assets") / name,

    ]

    for path in possible:

        if path.exists():

            return path

    return None


# ============================================================
# SAVE ACTIVITY
# ============================================================

def save_lab_result(
    experiment,
    score,
    role="",
    equipment=""
):

    record = {

        "experiment": experiment,

        "score": score,

        "role": role,

        "equipment": equipment,

        "created_at":
            datetime.utcnow().isoformat(),
    }

    st.session_state.lab_history.append(
        record
    )

    if supabase_available():

        db_insert(
            "lab_results",
            record
        )


def save_exercise_result(
    exercise,
    score
):

    record = {

        "exercise": exercise,

        "score": score,

        "created_at":
            datetime.utcnow().isoformat(),
    }

    st.session_state.exercise_history.append(
        record
    )

    if supabase_available():

        db_insert(
            "exercise_results",
            record
        )


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
<style>

.neuro-hero {
    padding: 30px;
    border-radius: 24px;

    background:
        linear-gradient(
            135deg,
            #071522,
            #123653
        );

    border:
        1px solid
        rgba(120,180,230,.35);

    margin-bottom: 20px;
}

.neuro-card {

    padding: 20px;

    border-radius: 18px;

    border:
        1px solid
        rgba(120,170,220,.30);

    margin-bottom: 15px;
}

.muted {

    opacity: .7;

    font-size: 13px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# NAVIGATION
# ============================================================

PAGES = [

    "NeuroWorld",

    "Account",

    "Cognitive Lab",

    "Brain Journey",

    "Brain Puzzle",

    "Brain Exercises",

    "AI Mood & Behaviour",

    "Ask Ayna",

    "Private Ask Ayna",

    "Research Book",

    "NeuroSocial",

    "Behaviour Decoding",

    "My Progress",

    "Security & Privacy",

    "Settings",

]


# ============================================================
# NEUROWORLD
# ============================================================

def page_neuroworld():

    st.markdown(
        """
<div class="neuro-hero">

<h1>🧠 NEUROLENS</h1>

<h3>
Explore cognition, behavior & the brain
</h3>

<p>
Welcome to your interactive cognitive
neuroscience world.
</p>

</div>
""",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(
        [1, 1]
    )

    with col1:

        brain = find_asset(
            "brain.png"
        )

        if brain:

            st.image(
                str(brain),
                use_container_width=True
            )

        else:

            st.markdown(
                "# 🧠"
            )

    with col2:

        st.markdown(
            "## Hi, I am NeuroLens."
        )

        st.write(
            "Come with me — "
            "I'll show you what "
            "you can explore."
        )

        robot = find_asset(
            "ayna_robot.png"
        )

        if robot:

            st.image(
                str(robot),
                width=180
            )

        st.info(
            "Ayna is your AI neuroscience "
            "companion. She can explain "
            "experiments, cognition and research."
        )

    st.divider()

    columns = st.columns(4)

    destinations = [

        ("🔬 Lab", "Cognitive Lab"),

        ("🧠 Brain", "Brain Journey"),

        ("🎮 Challenges", "Brain Exercises"),

        ("🤖 Ayna", "Ask Ayna"),

    ]

    for column, item in zip(
        columns,
        destinations
    ):

        label, page = item

        with column:

            if st.button(
                label,
                use_container_width=True
            ):

                st.session_state.page = page

                st.rerun()


# ============================================================
# ACCOUNT
# ============================================================

def page_account():

    st.header(
        "👤 NEUROLENS Account"
    )

    if not supabase_available():

        st.error(
            "Supabase is not connected. "
            "Add SUPABASE_URL and "
            "SUPABASE_KEY in Secrets."
        )

        return

    if get_user_id():

        st.success(
            f"Signed in: "
            f"{get_user_email()}"
        )

        profile = db_select(
            "profiles",
            {"id": get_user_id()},
            1
        )

        if profile:

            st.write(
                "Username:",
                profile[0].get(
                    "username",
                    ""
                )
            )

        if st.button(
            "Sign out"
        ):

            try:

                supabase.auth.sign_out()

            except Exception:

                pass

            st.session_state.auth_user = None

            st.rerun()

        return

    tab1, tab2 = st.tabs(
        [
            "Sign in",
            "Create account"
        ]
    )

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
            "Sign in",
            type="primary"
        ):

            try:

                result = (
                    supabase
                    .auth
                    .sign_in_with_password(
                        {
                            "email":
                                email.strip(),

                            "password":
                                password
                        }
                    )
                )

                st.session_state.auth_user = (
                    getattr(
                        result,
                        "user",
                        None
                    )
                )

                st.success(
                    "Signed in."
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    "Sign in failed: "
                    + type(exc).__name__
                )

    with tab2:

        email = st.text_input(
            "Email",
            key="signup_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        username = st.text_input(
            "Username",
            key="signup_username"
        )

        display_name = st.text_input(
            "Display name",
            key="signup_display"
        )

        if st.button(
            "✨ Create Account",
            type="primary"
        ):

            username = safe_username(
                username
            )

            if (
                not email.strip()
                or len(password) < 6
                or len(username) < 3
            ):

                st.error(
                    "Use a valid email, "
                    "password of at least "
                    "6 characters and "
                    "username of at least "
                    "3 characters."
                )

            else:

                try:

                    result = (
                        supabase
                        .auth
                        .sign_up(
                            {
                                "email":
                                    email.strip(),

                                "password":
                                    password,

                                "options": {
                                    "data": {
                                        "username":
                                            username,

                                        "display_name":
                                            display_name
                                            or username
                                    }
                                }
                            }
                        )
                    )

                    user = getattr(
                        result,
                        "user",
                        None
                    )

                    if user:

                        st.session_state.auth_user = user

                        st.success(
                            "Account created. "
                            "Confirm your email "
                            "if required."
                        )

                        try:

                            db_insert(
                                "profiles",
                                {
                                    "id":
                                        user.id,

                                    "username":
                                        username,

                                    "display_name":
                                        display_name
                                        or username
                                }
                            )

                        except Exception:

                            pass

                except Exception as exc:

                    st.error(
                        "Account creation "
                        "failed: "
                        + type(exc).__name__
                    )


# ============================================================
# COGNITIVE LAB
# ============================================================

def page_cognitive_lab():

    st.header(
        "🔬 Cognitive Neuroscience Lab"
    )

    role = st.selectbox(
        "Research role",
        [
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent"
        ]
    )

    equipment = st.selectbox(
        "Equipment",
        [
            "EEG Simulator",
            "Eye Tracker",
            "Reaction-Time System",
            "Cognitive Task Monitor",
            "Physiological Sensor"
        ]
    )

    experiment = st.selectbox(
        "Experiment",
        [
            "Attention",
            "Working Memory",
            "Decision & Reward",
            "Stroop / Cognitive Control",
            "Pattern Recognition",
            "Cognitive Flexibility"
        ]
    )

    st.caption(
        f"Role: {role} • "
        f"Equipment: {equipment}"
    )

    score = 0

    if experiment == "Attention":

        st.write(
            "Find X:"
        )

        st.code(
            "O   O   X   O   O   O   O"
        )

        answer = st.number_input(
            "Position of X",
            1,
            7,
            1
        )

        if st.button(
            "Submit Attention"
        ):

            score = (
                100
                if answer == 3
                else 0
            )

            if score:

                st.success(
                    "Correct."
                )

            else:

                st.warning(
                    "The target was "
                    "position 3."
                )

    elif experiment == "Working Memory":

        st.write(
            "Memorize this sequence:"
        )

        st.code(
            "729418"
        )

        answer = st.text_input(
            "Enter sequence"
        )

        if st.button(
            "Submit Memory"
        ):

            if (
                answer
                .replace(" ", "")
                == "729418"
            ):

                score = 100

                st.success(
                    "Correct."
                )

            else:

                score = 0

                st.warning(
                    "Not quite."
                )

    elif experiment == "Decision & Reward":

        choice = st.radio(
            "Choose your reward",
            [
                "PKR 1,000 today",
                "PKR 1,500 after 30 days"
            ]
        )

        if st.button(
            "Submit Decision"
        ):

            score = 1

            st.success(
                f"Selected: {choice}"
            )

            st.caption(
                "This illustrates "
                "intertemporal choice."
            )

    elif experiment == "Stroop / Cognitive Control":

        word = random.choice(
            [
                "RED",
                "BLUE",
                "GREEN"
            ]
        )

        st.markdown(
            f"### Target word: {word}"
        )

        answer = st.selectbox(
            "Select the word",
            [
                "RED",
                "BLUE",
                "GREEN"
            ]
        )

        if st.button(
            "Submit Stroop"
        ):

            score = (
                100
                if answer == word
                else 0
            )

            if score:

                st.success(
                    "Correct."
                )

            else:

                st.warning(
                    f"The word was {word}."
                )

    elif experiment == "Pattern Recognition":

        st.write(
            "2 → 4 → 8 → 16 → ?"
        )

        answer = st.number_input(
            "Answer",
            0,
            1000,
            0
        )

        if st.button(
            "Submit Pattern"
        ):

            score = (
                100
                if answer == 32
                else 0
            )

            if score:

                st.success(
                    "Correct."
                )

            else:

                st.warning(
                    "Answer: 32."
                )

    else:

        rule = st.radio(
            "Which rule is being used?",
            [
                "Add 3 each time",
                "Double then subtract 1"
            ]
        )

        if st.button(
            "Submit Flexibility"
        ):

            score = (
                100
                if rule
                == "Double then subtract 1"
                else 0
            )

            if score:

                st.success(
                    "Correct."
                )

            else:

                st.info(
                    "This is a simple "
                    "rule-switching illustration."
                )

    if score:

        save_lab_result(
            experiment,
            score,
            role,
            equipment
        )

    st.warning(
        "These are educational cognitive "
        "tasks. Simulated signals are "
        "conceptual and are not real "
        "EEG/fMRI measurements."
    )


# ============================================================
# BRAIN JOURNEY
# ============================================================

def page_brain_journey():

    st.header(
        "🧠 Brain Journey"
    )

    concepts = {

        "Neuron":
            "Basic functional unit "
            "of the nervous system.",

        "Synapse":
            "Junction through which "
            "neurons communicate.",

        "Neural Signaling":
            "Electrical and chemical "
            "processes transmit information.",

        "Prefrontal Cortex":
            "Supports planning, working "
            "memory and cognitive control.",

        "Hippocampus":
            "Important for many forms "
            "of memory and contextual "
            "processing.",

        "Striatum":
            "Part of the basal ganglia "
            "involved in action selection "
            "and reward learning.",

        "Anterior Cingulate Cortex":
            "Involved in conflict and "
            "error monitoring and "
            "cognitive control.",

        "Attention Networks":
            "Distributed systems involved "
            "in selecting and maintaining "
            "attention."
    }

    images = {

        "Neuron":
            "neuron.png",

        "Synapse":
            "synapse.png",

        "Neural Signaling":
            "neural_signaling.gif",

        "Prefrontal Cortex":
            "prefrontal_cortex.png",

        "Hippocampus":
            "hippocampus.png",

        "Striatum":
            "striatum.png",

        "Anterior Cingulate Cortex":
            "acc.png",

        "Attention Networks":
            "attention_network.png"
    }

    concept = st.selectbox(
        "Choose concept",
        list(concepts.keys())
    )

    image = find_asset(
        images[concept]
    )

    if image:

        st.image(
            str(image),
            caption=concept,
            use_container_width=True
        )

    else:

        st.info(
            "Visual asset not found: "
            + images[concept]
        )

    st.markdown(
        f"### {concept}"
    )

    st.write(
        concepts[concept]
    )


# ============================================================
# BRAIN PUZZLE
# ============================================================

def page_brain_puzzle():

    st.header(
        "🧩 Brain Puzzle"
    )

    brain = find_asset(
        "brain.png"
    )

    if brain:

        st.image(
            str(brain),
            width=350
        )

    st.write(
        "Arrange the numbered positions "
        "from 0 to 8."
    )

    values = []

    for index in range(9):

        value = st.number_input(
            f"Tile {index + 1}",
            0,
            8,
            int(
                st.session_state
                .brain_tile_order[index]
            ),
            key=f"brain_tile_{index}"
        )

        values.append(
            value
        )

    if st.button(
        "Check Puzzle",
        type="primary"
    ):

        if values == list(range(9)):

            st.success(
                "🎉 Puzzle solved!"
            )

            st.session_state.puzzle_score += 1

            if supabase_available():

                db_insert(
                    "brain_puzzle_results",
                    {
                        "score": 100,
                        "moves": 1,
                        "created_at":
                            datetime.utcnow().isoformat()
                    }
                )

        else:

            st.warning(
                "Not solved yet."
            )

    if st.button(
        "🔄 New Puzzle"
    ):

        st.session_state.brain_tile_order = (
            random.sample(
                range(9),
                9
            )
        )

        st.rerun()

    st.metric(
        "Puzzle completions",
        st.session_state.puzzle_score
    )


# ============================================================
# BRAIN EXERCISES
# ============================================================

def page_brain_exercises():

    st.header(
        "🏋️ Brain Exercises"
    )

    exercise = st.selectbox(
        "Exercise",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
            "Quick Reaction"
        ]
    )

    if exercise == "Working Memory":

        st.write(
            "Remember: **381649**"
        )

        answer = st.text_input(
            "Enter sequence"
        )

        if st.button(
            "Check Memory"
        ):

            score = (
                100
                if answer.replace(
                    " ",
                    ""
                ) == "381649"
                else 0
            )

            if score:

                st.success(
                    "Correct."
                )

            else:

                st.warning(
                    "Try again."
                )

            save_exercise_result(
                exercise,
                score
            )

    elif exercise == "Attention":

        st.code(
            "O  O  O  X  O  O  O  O"
        )

        answer = st.number_input(
            "Position of X",
            1,
            8,
            1
        )

        if st.button(
            "Check Attention"
        ):

            score = (
                100
                if answer == 4
                else 0
            )

            if score:

                st.success(
                    "Correct."
                )

            else:

                st.warning(
                    "X was position 4."
                )

            save_exercise_result(
                exercise,
                score
            )

    elif exercise == "Pattern Recognition":

        answer = st.number_input(
            "2 → 4 → 8 → 16 → ?",
            0,
            1000,
            0
        )

        if st.button(
            "Check Pattern"
        ):

            score = (
                100
                if answer == 32
                else 0
            )

            if score:

                st.success(
                    "Correct."
                )

            else:

                st.warning(
                    "Answer: 32."
                )

            save_exercise_result(
                exercise,
                score
            )

    elif exercise == "Decision Challenge":

        choice = st.radio(
            "Choose",
            [
                "Smaller reward now",
                "Larger reward later"
            ]
        )

        if st.button(
            "Submit Decision"
        ):

            st.success(
                f"Selected: {choice}"
            )

            save_exercise_result(
                exercise,
                1
            )

    else:

        if st.button(
            "⚡ Start Reaction Timer"
        ):

            st.session_state.reaction_started = (
                time.time()
            )

            st.session_state.reaction_result = None

            st.info(
                "Now press React."
            )

        if (
            st.session_state
            .reaction_started
        ):

            if st.button(
                "🟢 React"
            ):

                elapsed = (
                    time.time()
                    - st.session_state
                    .reaction_started
                )

                st.session_state.reaction_started = None

                st.session_state.reaction_result = elapsed

                st.success(
                    f"Reaction time: "
                    f"{elapsed:.3f} seconds"
                )


# ============================================================
# AI MOOD & BEHAVIOUR
# ============================================================

def page_mood_behaviour():

    st.header(
        "🎙️ AI Mood & Behaviour"
    )

    st.caption(
        "AI-assisted reflection only. "
        "This is not diagnosis or mind-reading."
    )

    mood = st.slider(
        "Current mood",
        0,
        10,
        5
    )

    stress = st.slider(
        "Perceived stress",
        0,
        10,
        5
    )

    energy = st.slider(
        "Energy",
        0,
        10,
        5
    )

    feelings = st.text_area(
        "How are you feeling?"
    )

    if st.button(
        "🤖 Analyse with Ayna",
        type="primary"
    ):

        prompt = f"""

Reflect on this self-report:

Mood: {mood}/10
Stress: {stress}/10
Energy: {energy}/10
Feelings: {feelings}

Explain possible cognitive and behavioural
context.

Do not diagnose.

Do not claim to measure brain activity.

"""

        st.session_state.mood_result = (
            ask_ayna(prompt)
        )

    if st.session_state.mood_result:

        st.markdown(
            "### 💬 Ayna's reflection"
        )

        st.write(
            st.session_state.mood_result
        )

    if hasattr(
        st,
        "audio_input"
    ):

        audio = st.audio_input(
            "🎙️ Record voice"
        )

        if audio:

            st.audio(
                audio
            )

            if st.button(
                "Analyse Voice"
            ):

                if not ai_available():

                    st.error(
                        "Gemini is not connected."
                    )

                else:

                    try:

                        if genai_types:

                            part = (
                                genai_types
                                .Part
                                .from_bytes(
                                    data=
                                        audio.getvalue(),

                                    mime_type=
                                        audio.type
                                        or
                                        "audio/wav"
                                )
                            )

                            response = (
                                gemini
                                .models
                                .generate_content(
                                    model=
                                        AI_MODEL,

                                    contents=[
                                        """
Interpret this voice
cautiously.

Return a transcript and
communication-vibe description.

Do not claim hidden emotion,
personality, health or diagnosis.
""",
                                        part
                                    ]
                                )
                            )

                            st.write(
                                getattr(
                                    response,
                                    "text",
                                    ""
                                )
                            )

                    except Exception as exc:

                        st.error(
                            "Voice analysis failed: "
                            + type(exc).__name__
                        )

    camera = st.camera_input(
        "📷 Optional face snapshot"
    )

    if camera:

        st.info(
            "Snapshot captured. "
            "A future vision-analysis "
            "module can process this through "
            "the AI layer. It must remain "
            "probabilistic and non-diagnostic."
        )


# ============================================================
# ASK AYNA
# ============================================================

def page_ask_ayna():

    st.header(
        "🤖 Ask Ayna"
    )

    for message in (
        st.session_state.messages
    ):

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    question = st.chat_input(
        "Ask Ayna about cognition..."
    )

    if question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        context = "\n".join(
            [
                f"{m['role']}: "
                f"{m['content']}"
                for m in
                st.session_state.messages[-8:]
            ]
        )

        answer = ask_ayna(
            question,
            context
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.rerun()


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

def page_private_ayna():

    st.header(
        "🔐 Private Ask Ayna"
    )

    if not st.session_state.private_unlocked:

        pin = st.text_input(
            "Create / enter 4–6 digit PIN",
            type="password",
            max_chars=6
        )

        if st.button(
            "🔓 Unlock"
        ):

            if (
                not pin.isdigit()
                or not 4 <= len(pin) <= 6
            ):

                st.error(
                    "PIN must contain "
                    "4–6 digits."
                )

            else:

                hashed = (
                    hashlib.pbkdf2_hmac(
                        "sha256",
                        pin.encode(),
                        b"neurolens-private",
                        150000
                    ).hex()
                )

                if (
                    st.session_state
                    .private_hash
                    is None
                ):

                    st.session_state.private_hash = hashed

                    st.session_state.private_unlocked = True

                    st.rerun()

                elif secrets.compare_digest(
                    hashed,
                    st.session_state.private_hash
                ):

                    st.session_state.private_unlocked = True

                    st.rerun()

                else:

                    st.error(
                        "Incorrect PIN."
                    )

        return

    st.success(
        "🔓 Private session unlocked."
    )

    for message in (
        st.session_state.private_messages
    ):

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    question = st.chat_input(
        "Private question..."
    )

    if question:

        answer = ask_ayna(
            question,
            "Private educational conversation."
        )

        st.session_state.private_messages.extend(
            [
                {
                    "role": "user",
                    "content": question
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ]
        )

        st.rerun()

    if st.button(
        "🔒 Lock"
    ):

        st.session_state.private_unlocked = False

        st.rerun()


# ============================================================
# RESEARCH BOOK
# ============================================================

def page_research_book():

    st.header(
        "📚 Research Book"
    )

    query = st.text_input(
        "Search Europe PMC",
        placeholder=
            "cognitive control and reward"
    )

    if st.button(
        "🔎 Search Research"
    ):

        if not query.strip():

            st.warning(
                "Enter a research topic."
            )

        else:

            try:

                response = requests.get(
                    "https://www.ebi.ac.uk/"
                    "europepmc/webservices/rest/search",

                    params={
                        "query": query,
                        "format": "json",
                        "pageSize": 10
                    },

                    timeout=20
                )

                response.raise_for_status()

                data = response.json()

                st.session_state.research_results = (
                    data
                    .get(
                        "resultList",
                        {}
                    )
                    .get(
                        "result",
                        []
                    )
                )

            except Exception as exc:

                st.error(
                    "Research search failed: "
                    + type(exc).__name__
                )

    for index, paper in enumerate(
        st.session_state.research_results
    ):

        title = paper.get(
            "title",
            "Untitled paper"
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
            f"### 📄 {title}"
        )

        st.caption(
            f"{authors} • {year}"
        )

        if pmid:

            st.link_button(
                "Open PubMed",
                (
                    "https://pubmed.ncbi.nlm.nih.gov/"
                    + str(pmid)
                    + "/"
                )
            )

        if st.button(
            "🤖 Explain with Ayna",
            key=f"paper_{index}"
        ):

            explanation = ask_ayna(
                f"""

Explain this research paper
for a cognitive neuroscience learner.

Title:
{title}

Authors:
{authors}

Year:
{year}

PMID:
{pmid}

Do not invent methods,
results or conclusions.

"""
            )

            st.write(
                explanation
            )

        st.divider()


# ============================================================
# NEUROSOCIAL
# ============================================================

def page_neurosocial():

    st.header(
        "🌐 NeuroSocial"
    )

    if not get_user_id():

        st.warning(
            "Please sign in through "
            "Account first."
        )

        return

    tab1, tab2, tab3 = st.tabs(
        [
            "Profile & Friends",
            "Friend Requests",
            "1-to-1 Chat"
        ]
    )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    with tab1:

        profile = db_select(
            "profiles",
            {
                "id":
                    get_user_id()
            },
            1
        )

        current = (
            profile[0]
            if profile
            else {}
        )

        username = st.text_input(
            "Username",
            value=current.get(
                "username",
                ""
            )
        )

        display_name = st.text_input(
            "Display name",
            value=current.get(
                "display_name",
                username
            )
        )

        if st.button(
            "Save Profile"
        ):

            db_update(
                "profiles",
                {
                    "username":
                        safe_username(
                            username
                        ),

                    "display_name":
                        display_name
                },
                {
                    "id":
                        get_user_id()
                }
            )

            st.success(
                "Profile saved."
            )

        st.divider()

        search = st.text_input(
            "Search users by username"
        )

        if st.button(
            "🔎 Search Users"
        ) and search.strip():

            users = db_select(
                "profiles",
                limit=100
            )

            matches = [

                user

                for user in users

                if search.lower()
                in str(
                    user.get(
                        "username",
                        ""
                    )
                ).lower()

            ]

            if not matches:

                st.info(
                    "No users found."
                )

            for user in matches:

                target_id = user.get(
                    "id"
                )

                if target_id == get_user_id():

                    continue

                st.write(
                    "👤 @"
                    + str(
                        user.get(
                            "username",
                            "user"
                        )
                    )
                )

                if st.button(
                    "Send Friend Request",
                    key=
                        "request_"
                        + str(target_id)
                ):

                    result = db_insert(
                        "friend_requests",
                        {
                            "sender_id":
                                get_user_id(),

                            "receiver_id":
                                target_id,

                            "status":
                                "pending"
                        }
                    )

                    if result:

                        st.success(
                            "Friend request sent."
                        )

    # --------------------------------------------------------
    # REQUESTS
    # --------------------------------------------------------

    with tab2:

        incoming = db_select(
            "friend_requests",
            {
                "receiver_id":
                    get_user_id(),

                "status":
                    "pending"
            },
            100
        )

        if not incoming:

            st.info(
                "No pending requests."
            )

        for request in incoming:

            sender_id = request.get(
                "sender_id"
            )

            st.write(
                "@"
                + get_username(
                    sender_id
                )
            )

            accept_col, decline_col = (
                st.columns(2)
            )

            with accept_col:

                if st.button(
                    "Accept",
                    key=
                        "accept_"
                        + str(
                            request.get(
                                "id"
                            )
                        )
                ):

                    db_update(
                        "friend_requests",
                        {
                            "status":
                                "accepted"
                        },
                        {
                            "id":
                                request.get(
                                    "id"
                                )
                        }
                    )

                    db_insert(
                        "friendships",
                        {
                            "user_id":
                                get_user_id(),

                            "friend_id":
                                sender_id
                        }
                    )

                    db_insert(
                        "friendships",
                        {
                            "user_id":
                                sender_id,

                            "friend_id":
                                get_user_id()
                        }
                    )

                    st.rerun()

            with decline_col:

                if st.button(
                    "Decline",
                    key=
                        "decline_"
                        + str(
                            request.get(
                                "id"
                            )
                        )
                ):

                    db_update(
                        "friend_requests",
                        {
                            "status":
                                "declined"
                        },
                        {
                            "id":
                                request.get(
                                    "id"
                                )
                        }
                    )

                    st.rerun()

    # --------------------------------------------------------
    # CHAT
    # --------------------------------------------------------

    with tab3:

        friendships = db_select(
            "friendships",
            {
                "user_id":
                    get_user_id()
            },
            100
        )

        if not friendships:

            st.info(
                "You don't have friends yet."
            )

        else:

            options = [

                (
                    row.get(
                        "friend_id"
                    ),

                    get_username(
                        row.get(
                            "friend_id"
                        )
                    )
                )

                for row in friendships
            ]

            friend_id, friend_name = (
                st.selectbox(
                    "Chat with",
                    options,
                    format_func=
                        lambda item:
                        item[1]
                )
            )

            conversations = db_select(
                "conversations",
                {
                    "user1_id":
                        get_user_id()
                },
                100
            )

            conversation = next(
                (
                    row

                    for row in conversations

                    if row.get(
                        "user2_id"
                    )
                    == friend_id
                ),
                None
            )

            if not conversation:

                reverse = db_select(
                    "conversations",
                    {
                        "user2_id":
                            get_user_id()
                    },
                    100
                )

                conversation = next(
                    (
                        row

                        for row in reverse

                        if row.get(
                            "user1_id"
                        )
                        == friend_id
                    ),
                    None
                )

            if not conversation:

                if st.button(
                    "Start Chat"
                ):

                    db_insert(
                        "conversations",
                        {
                            "user1_id":
                                get_user_id(),

                            "user2_id":
                                friend_id
                        }
                    )

                    st.rerun()

            else:

                conversation_id = (
                    conversation.get(
                        "id"
                    )
                )

                messages = db_select(
                    "messages",
                    {
                        "conversation_id":
                            conversation_id
                    },
                    200,
                    order="created_at"
                )

                for message in messages:

                    role = (
                        "user"
                        if message.get(
                            "sender_id"
                        )
                        == get_user_id()
                        else "assistant"
                    )

                    with st.chat_message(
                        role
                    ):

                        st.write(
                            message.get(
                                "content",
                                ""
                            )
                        )

                message = st.chat_input(
                    f"Message @{friend_name}"
                )

                if message:

                    db_insert(
                        "messages",
                        {
                            "conversation_id":
                                conversation_id,

                            "sender_id":
                                get_user_id(),

                            "content":
                                message,

                            "message_type":
                                "text"
                        }
                    )

                    st.rerun()


# ============================================================
# BEHAVIOUR DECODING
# ============================================================

def page_behaviour():

    st.header(
        "🧠 Behaviour Decoding"
    )

    st.write(
        "Educational consultation request."
    )

    name = st.text_input(
        "Name"
    )

    contact = st.text_input(
        "Contact"
    )

    topic = st.text_area(
        "What would you like to discuss?"
    )

    duration = st.selectbox(
        "Session",
        [
            "20 min — PKR 1,000 / $8",
            "30 min — PKR 1,500 / $10",
            "45 min — PKR 2,000 / $12",
            "Advice / Consultation — PKR 1,500 / $10"
        ]
    )

    payment_method = st.selectbox(
        "Payment method",
        [
            "Easypaisa",
            "International"
        ]
    )

    payment_reference = st.text_input(
        "Payment reference"
    )

    if st.button(
        "Submit Consultation Request",
        type="primary"
    ):

        payload = {

            "name":
                name.strip(),

            "contact":
                contact.strip(),

            "topic":
                topic.strip(),

            "duration":
                duration,

            "payment_method":
                payment_method,

            "payment_reference":
                payment_reference.strip(),

            "status":
                "pending"
        }

        result = db_insert(
            "consultation_requests",
            payload
        )

        if result:

            st.success(
                "Consultation request saved."
            )

        else:

            st.info(
                "Supabase is not connected, "
                "so the request could not be "
                "saved permanently."
            )

    st.divider()

    if payment_method == "Easypaisa":

        st.info(
            "Easypaisa: "
            + (
                EASYPAISA_NUMBER
                or
                "Not configured."
            )
        )

    else:

        if INTERNATIONAL_PAYMENT_URL:

            st.link_button(
                "🌍 International Payment",
                INTERNATIONAL_PAYMENT_URL
            )

        else:

            st.warning(
                "International payment URL "
                "is not configured."
            )

    st.caption(
        "Automatic payment verification "
        "requires an official provider "
        "API/webhook. A reference number "
        "alone is not proof of payment."
    )


# ============================================================
# MY PROGRESS
# ============================================================

def page_progress():

    st.header(
        "📈 My Progress"
    )

    labs = (
        st.session_state.lab_history
    )

    exercises = (
        st.session_state.exercise_history
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Lab Results",
        len(labs)
    )

    c2.metric(
        "Exercise Results",
        len(exercises)
    )

    c3.metric(
        "Puzzle Completions",
        st.session_state.puzzle_score
    )

    st.metric(
        "AI Requests",
        f"{st.session_state.ai_requests}/"
        f"{AI_SESSION_LIMIT}"
    )

    if go and labs:

        scores = [

            item.get(
                "score",
                0
            )

            for item in labs
        ]

        figure = go.Figure()

        figure.add_trace(
            go.Bar(
                x=list(
                    range(
                        1,
                        len(scores) + 1
                    )
                ),

                y=scores
            )
        )

        figure.update_layout(
            title=
                "NEUROLENS Lab Scores",

            xaxis_title=
                "Experiment",

            yaxis_title=
                "Score"
        )

        st.plotly_chart(
            figure,
            use_container_width=True
        )

    st.subheader(
        "Recent Lab Activity"
    )

    for item in labs[-20:]:

        st.write(
            f"• "
            f"{item.get('experiment')}"
            f" — "
            f"{item.get('score')}"
        )


# ============================================================
# SECURITY & PRIVACY
# ============================================================

def page_security():

    st.header(
        "🔒 Security & Privacy Center"
    )

    st.markdown(
        """
### API Keys

Gemini and Supabase credentials
should remain in Streamlit Secrets.

### AI

AI responses are educational.
They are not medical diagnosis.

### Voice

Voice interpretation is probabilistic.
It cannot reliably reveal hidden emotional
states or personality.

### Face

Facial analysis should be treated as
an AI-assisted estimate, not mind-reading.

### Cognitive Tasks

Games and exercises do not directly
measure EEG, fMRI or brain activity.

### Payments

A payment reference should not be treated
as verified without official provider
confirmation.

### Private Ayna

The private area uses a salted PBKDF2
session PIN. It is not a replacement
for full encrypted authentication.
"""
    )


# ============================================================
# SETTINGS
# ============================================================

def page_settings():

    st.header(
        "⚙️ Settings"
    )

    st.write(
        "Gemini:",
        "🟢 Connected"
        if ai_available()
        else
        "🟡 Not connected"
    )

    st.write(
        "Supabase:",
        "🟢 Connected"
        if supabase_available()
        else
        "🟡 Not connected"
    )

    st.write(
        "Gemini model:",
        AI_MODEL
    )

    st.write(
        "AI session limit:",
        AI_SESSION_LIMIT
    )

    st.divider()

    st.subheader(
        "Assets"
    )

    assets = [

        "brain.png",

        "ayna_robot.png",

        "ayna_reboot_voiced.mp4",

        "cognitive_lab_brain.mp4",

        "brain_animation.mp4",

        "neuron.png",

        "synapse.png",

        "neural_signaling.gif",

        "prefrontal_cortex.png",

        "hippocampus.png",

        "striatum.png",

        "acc.png",

        "attention_network.png"

    ]

    for filename in assets:

        st.write(
            (
                "✅ "
                if find_asset(filename)
                else
                "⚪ "
            )
            + filename
        )

    if st.session_state.last_error:

        st.warning(
            st.session_state.last_error
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "# 🧠 NEUROLENS"
    )

    st.caption(
        "Explore cognition, behavior "
        "& the brain"
    )

    st.divider()

    selected_page = st.radio(
        "Navigate",
        PAGES,
        index=PAGES.index(
            st.session_state.page
        )
    )

    if (
        selected_page
        != st.session_state.page
    ):

        st.session_state.page = (
            selected_page
        )

        st.rerun()

    st.divider()

    st.write(
        "Supabase:",
        "🟢 Connected"
        if supabase_available()
        else
        "🟡 Not connected"
    )

    st.write(
        "Gemini:",
        "🟢 Connected"
        if ai_available()
        else
        "🟡 Not connected"
    )

    st.caption(
        f"AI requests: "
        f"{st.session_state.ai_requests}/"
        f"{AI_SESSION_LIMIT}"
    )


# ============================================================
# MAIN ROUTER
# ============================================================

try:

    if st.session_state.page == "NeuroWorld":

        page_neuroworld()

    elif st.session_state.page == "Account":

        page_account()

    elif st.session_state.page == "Cognitive Lab":

        page_cognitive_lab()

    elif st.session_state.page == "Brain Journey":

        page_brain_journey()

    elif st.session_state.page == "Brain Puzzle":

        page_brain_puzzle()

    elif st.session_state.page == "Brain Exercises":

        page_brain_exercises()

    elif st.session_state.page == "AI Mood & Behaviour":

        page_mood_behaviour()

    elif st.session_state.page == "Ask Ayna":

        page_ask_ayna()

    elif st.session_state.page == "Private Ask Ayna":

        page_private_ayna()

    elif st.session_state.page == "Research Book":

        page_research_book()

    elif st.session_state.page == "NeuroSocial":

        page_neurosocial()

    elif st.session_state.page == "Behaviour Decoding":

        page_behaviour()

    elif st.session_state.page == "My Progress":

        page_progress()

    elif st.session_state.page == "Security & Privacy":

        page_security()

    elif st.session_state.page == "Settings":

        page_settings()


except Exception as exc:

    st.session_state.last_error = (
        f"{st.session_state.page}: "
        f"{type(exc).__name__}: "
        f"{exc}"
    )

    st.session_state.health_log.append(
        {
            "time":
                time.strftime(
                    "%H:%M:%S"
                ),

            "page":
                st.session_state.page,

            "error":
                str(exc)[:500]
        }
    )

    st.error(
        "This section encountered an "
        "error. The rest of NEUROLENS "
        "remains available."
    )

    st.exception(exc)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🧠 NEUROLENS • "
    "Explore cognition, behavior & the brain "
    "• Created by Ayna Jaffri"
)
