import os
import re
import json
import time
import random
import hashlib
import secrets
import base64
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# OPTIONAL IMPORTS
# ============================================================

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

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from streamlit_dnd import dnd
except Exception:
    dnd = None


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"
TAGLINE = "Explore cognition, behavior & the brain"
AI_SESSION_LIMIT = 20

SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY", "")
)

GEMINI_MODEL = st.secrets.get(
    "GEMINI_MODEL",
    os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
)

EASYPAISA_NUMBER = st.secrets.get(
    "EASYPAISA_NUMBER",
    os.getenv("EASYPAISA_NUMBER", "")
)

INTERNATIONAL_PAYMENT_URL = st.secrets.get(
    "INTERNATIONAL_PAYMENT_URL",
    os.getenv("INTERNATIONAL_PAYMENT_URL", "")
)


# ============================================================
# CLIENTS
# ============================================================

supabase = None
supabase_error = ""

if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        supabase_error = str(exc)


def supabase_available():
    return supabase is not None


def ai_available():
    return bool(genai and GEMINI_API_KEY)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "NeuroWorld",
    "auth_user": None,
    "ai_requests": 0,
    "ai_history": [],
    "ayna_messages": [],
    "private_unlocked": False,
    "private_pin_hash": "",
    "private_pin_salt": "",
    "lab_result": None,
    "lab_history": [],
    "experiment_started": False,
    "experiment_completed": False,
    "experiment_score": 0,
    "puzzle_tiles": [],
    "puzzle_grid": 3,
    "puzzle_moves": 0,
    "puzzle_completed": False,
    "puzzle_started_at": 0,
    "puzzle_elapsed": 0,
    "puzzle_round": 1,
    "puzzle_best_time": None,
    "exercise_scores": [],
    "voice_result": None,
    "face_result": None,
    "combined_result": None,
    "research_results": [],
    "research_notes": [],
    "games_completed": 0,
    "achievements": [],
    "social_selected_friend": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: Inter, system-ui, sans-serif;
}

.neuro-hero {
    padding: 28px;
    border-radius: 24px;
    background:
        radial-gradient(circle at 20% 20%, rgba(80,150,255,.35), transparent 30%),
        radial-gradient(circle at 80% 30%, rgba(190,90,255,.28), transparent 30%),
        linear-gradient(135deg,#081329,#101d3d 55%,#17112d);
    border: 1px solid rgba(255,255,255,.12);
    margin-bottom: 22px;
}

.neuro-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 2px;
}

.neuro-subtitle {
    font-size: 20px;
    opacity: .9;
    margin-top: 5px;
}

.world-card {
    padding: 22px;
    border-radius: 20px;
    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.10);
    margin-bottom: 14px;
}

.brain-character {
    text-align:center;
    font-size:100px;
    padding:20px;
}

.robot-character {
    text-align:center;
    font-size:82px;
}

.lab-card {
    padding:20px;
    border-radius:20px;
    background:linear-gradient(135deg,#09182d,#122b42);
    border:1px solid rgba(100,200,255,.2);
}

.small-muted {
    opacity:.7;
    font-size:13px;
}

.result-box {
    padding:18px;
    border-radius:18px;
    background:rgba(255,255,255,.05);
    border:1px solid rgba(255,255,255,.1);
}

button {
    border-radius:12px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE HELPERS
# ============================================================

def db_select(
    table,
    columns="*",
    filters=None,
    limit=100,
    order=None,
    descending=False,
):
    if not supabase_available():
        return []

    try:
        q = supabase.table(table).select(columns)

        for key, value in (filters or {}).items():
            if value is not None:
                q = q.eq(key, value)

        if order:
            q = q.order(order, desc=descending)

        if limit:
            q = q.limit(limit)

        return q.execute().data or []

    except Exception as exc:
        st.session_state["last_error"] = (
            f"Supabase read {table}: {type(exc).__name__}"
        )
        return []


def db_insert(table, data):
    if not supabase_available():
        return None

    try:
        return supabase.table(table).insert(data).execute()
    except Exception as exc:
        st.session_state["last_error"] = (
            f"Supabase insert {table}: {type(exc).__name__}"
        )
        return None


def db_update(table, data, filters):
    if not supabase_available():
        return None

    try:
        q = supabase.table(table).update(data)

        for key, value in filters.items():
            q = q.eq(key, value)

        return q.execute()

    except Exception as exc:
        st.session_state["last_error"] = (
            f"Supabase update {table}: {type(exc).__name__}"
        )
        return None


# ============================================================
# AUTH
# ============================================================

def current_user():
    if st.session_state.get("auth_user"):
        return st.session_state.auth_user

    if not supabase_available():
        return None

    try:
        session = supabase.auth.get_session()

        if session:
            user = getattr(session, "user", None)
            if user:
                return user

    except Exception:
        pass

    return None


def user_id():
    user = current_user()

    if user is None:
        return None

    if isinstance(user, dict):
        return user.get("id")

    return getattr(user, "id", None)


def user_email():
    user = current_user()

    if user is None:
        return ""

    if isinstance(user, dict):
        return user.get("email", "")

    return getattr(user, "email", "") or ""


def profile():
    uid = user_id()

    if not uid:
        return {}

    rows = db_select(
        "profiles",
        filters={"id": uid},
        limit=1,
    )

    return rows[0] if rows else {}


def login_ui():
    st.subheader("🔐 NEUROLENS Account")

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
        ):
            if not supabase_available():
                st.error("Supabase is not connected.")
            else:
                try:
                    result = supabase.auth.sign_in_with_password(
                        {
                            "email": email.strip(),
                            "password": password,
                        }
                    )

                    st.session_state.auth_user = result.user
                    st.success("Login successful.")
                    st.rerun()

                except Exception:
                    st.error(
                        "Login failed. Check your email and password."
                    )

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
        )
        username = st.text_input(
            "Username",
            key="signup_username",
        )

        if st.button(
            "Create Account",
            use_container_width=True,
        ):
            if not supabase_available():
                st.error("Supabase is not connected.")
            elif len(password) < 8:
                st.error("Password should contain at least 8 characters.")
            else:
                try:
                    result = supabase.auth.sign_up(
                        {
                            "email": email.strip(),
                            "password": password,
                        }
                    )

                    uid = getattr(result.user, "id", None)

                    if uid:
                        db_insert(
                            "profiles",
                            {
                                "id": uid,
                                "username": re.sub(
                                    r"[^A-Za-z0-9_.-]",
                                    "",
                                    username.strip(),
                                )[:30],
                                "display_name": username.strip()[:80],
                            },
                        )

                    st.success(
                        "Account created. Check your email if confirmation is enabled."
                    )

                except Exception:
                    st.error("Could not create account.")


# ============================================================
# ASSETS
# ============================================================

def find_asset(name):
    paths = [
        name,
        os.path.join("assets", name),
        os.path.join(".", name),
        os.path.join(".", "assets", name),
    ]

    for path in paths:
        if os.path.exists(path):
            return path

    return None


def image_data_uri(path):
    if not path:
        return ""

    try:
        with open(path, "rb") as f:
            raw = base64.b64encode(f.read()).decode()

        ext = Path(path).suffix.lower()

        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(ext, "image/png")

        return f"data:{mime};base64,{raw}"

    except Exception:
        return ""


# ============================================================
# AI
# ============================================================

def ask_gemini(prompt, image_bytes=None, image_mime=None):
    if not ai_available():
        return ""

    if st.session_state.ai_requests >= AI_SESSION_LIMIT:
        return "AI session limit reached. Please continue later."

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        contents = [prompt]

        if image_bytes and types:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_mime or "image/jpeg",
                )
            )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )

        st.session_state.ai_requests += 1

        text = getattr(response, "text", "") or ""

        return text.strip()

    except Exception:
        return ""


def safe_json(text):
    if not text:
        return {}

    clean = re.sub(
        r"```(?:json)?",
        "",
        text,
        flags=re.I,
    ).replace("```", "").strip()

    try:
        return json.loads(clean)
    except Exception:
        return {}


# ============================================================
# HEADER
# ============================================================

def header():
    st.markdown(
        f"""
        <div class="neuro-hero">
            <div class="neuro-title">🧠 {APP_NAME}</div>
            <div class="neuro-subtitle">{TAGLINE}</div>
            <div class="small-muted">
                Independent cognitive neuroscience research project by {CREATOR}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# NEUROWORLD
# ============================================================

def page_neuroworld():
    header()

    st.markdown(
        """
        <div class="world-card">
        <h2>🌌 Welcome to the NeuroLens World</h2>
        <p>
        You are entering an interactive environment where cognition,
        behaviour, brain systems, experiments, AI and research connect.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            '<div class="brain-character">🧠</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="world-card">
            <h3>🧠 NeuroLens</h3>
            <p>
            Hi, I am NeuroLens.<br>
            Come with me — I'll show you what you can explore.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        robot = find_asset("ayna_robot.png")

        if robot:
            st.image(
                robot,
                use_container_width=True,
            )
        else:
            st.markdown(
                '<div class="robot-character">🤖</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="world-card">
            <h3>🤖 Ayna AI Research Agent</h3>
            <p>
            Your female AI research companion can guide you through
            experiments, brain systems, research and challenges.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    cols = st.columns(3)

    destinations = [
        ("🧪", "Cognitive Lab", "Lab"),
        ("🧠", "Brain Journey", "Brain Journey"),
        ("🎯", "Brain Challenges", "Challenges"),
        ("🤖", "Ask Ayna", "Ask Ayna"),
        ("📚", "Research World", "Research"),
        ("🌐", "NeuroSocial", "NeuroSocial"),
    ]

    for i, (emoji, title, page) in enumerate(destinations):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="world-card">
                <h3>{emoji} {title}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Enter {title}",
                key=f"world_{page}",
                use_container_width=True,
            ):
                st.session_state.page = page
                st.rerun()


# ============================================================
# COGNITIVE LAB
# ============================================================

LABS = {
    "Attention": {
        "description": "Selective attention and response control.",
        "task": "Find the target letter X among distractors.",
    },
    "Memory": {
        "description": "Working-memory encoding and recall.",
        "task": "Remember a short sequence.",
    },
    "Decision & Reward": {
        "description": "Delayed reward and decision preference.",
        "task": "Choose between immediate and delayed reward.",
    },
    "Stroop Cognitive Control": {
        "description": "Conflict monitoring and response inhibition.",
        "task": "Identify the ink colour instead of the written word.",
    },
    "Pattern Recognition": {
        "description": "Detect regularities and predict the next item.",
        "task": "Complete a numerical pattern.",
    },
}


def page_lab():
    header()

    st.title("🧪 Virtual Cognitive Neuroscience Lab")

    st.markdown(
        """
        <div class="lab-card">
        <b>Conceptual laboratory simulation</b><br>
        The measurements generated here are simulated task-performance
        data. They are not real EEG, fMRI, physiological or clinical measurements.
        </div>
        """,
        unsafe_allow_html=True,
    )

    character = st.selectbox(
        "Research role",
        [
            "Researcher",
            "Student",
            "Lab Assistant",
            "AI Research Agent",
        ],
    )

    equipment = st.multiselect(
        "Virtual equipment",
        [
            "EEG Simulator",
            "Eye Tracker",
            "Reaction-Time System",
            "Cognitive Task Monitor",
            "Physiological Sensor",
        ],
        default=[
            "Cognitive Task Monitor",
            "Reaction-Time System",
        ],
    )

    experiment = st.selectbox(
        "Choose experiment",
        list(LABS.keys()),
    )

    st.info(
        f"{LABS[experiment]['description']} "
        f"Task: {LABS[experiment]['task']}"
    )

    if not st.session_state.experiment_started:
        if st.button(
            "▶️ Start Experiment",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.experiment_started = True
            st.session_state.experiment_completed = False
            st.session_state.experiment_score = 0
            st.rerun()

    if st.session_state.experiment_started:

        st.subheader("🔬 Live Experiment")

        if experiment == "Attention":
            target = random.choice(["X", "K", "M"])

            sequence = [
                random.choice(["A", "B", "C", "D", target])
                for _ in range(10)
            ]

            st.write("Target:", target)
            st.code(" ".join(sequence))

            answer = st.text_input(
                "Which letter was the target?",
                key="attention_answer",
            )

            if st.button(
                "Submit Attention Result",
                use_container_width=True,
            ):
                score = int(answer.upper() == target)

                st.session_state.experiment_score = score
                st.session_state.experiment_completed = True

        elif experiment == "Memory":
            if "memory_sequence" not in st.session_state:
                st.session_state.memory_sequence = "".join(
                    random.choice("0123456789")
                    for _ in range(6)
                )

            if not st.session_state.get(
                "memory_reveal_hidden",
                False,
            ):
                st.code(st.session_state.memory_sequence)

                if st.button("Hide Sequence"):
                    st.session_state.memory_reveal_hidden = True
                    st.rerun()

            else:
                answer = st.text_input(
                    "Enter the sequence you remember"
                )

                if st.button(
                    "Submit Memory Result",
                    use_container_width=True,
                ):
                    score = int(
                        answer.strip()
                        == st.session_state.memory_sequence
                    )

                    st.session_state.experiment_score = score
                    st.session_state.experiment_completed = True

        elif experiment == "Decision & Reward":

            choice = st.radio(
                "Choose one:",
                [
                    "Receive PKR 1,000 today",
                    "Receive PKR 1,500 after 30 days",
                ],
            )

            if st.button(
                "Record Decision",
                use_container_width=True,
            ):
                st.session_state.experiment_score = 1
                st.session_state.experiment_completed = True

                st.session_state.lab_result = {
                    "experiment": experiment,
                    "choice": choice,
                }

        elif experiment == "Stroop Cognitive Control":

            word, ink = random.choice(
                [
                    ("RED", "BLUE"),
                    ("BLUE", "GREEN"),
                    ("GREEN", "RED"),
                    ("YELLOW", "BLUE"),
                ]
            )

            st.markdown(
                f"<h1 style='text-align:center'>{word}</h1>",
                unsafe_allow_html=True,
            )

            answer = st.selectbox(
                "What was the ink colour?",
                ["RED", "BLUE", "GREEN", "YELLOW"],
            )

            if st.button(
                "Submit Stroop Result",
                use_container_width=True,
            ):
                st.session_state.experiment_score = int(
                    answer == ink
                )
                st.session_state.experiment_completed = True

        else:

            start = random.randint(2, 5)

            sequence = [
                start,
                start * 2,
                start * 4,
                start * 8,
                start * 16,
            ]

            st.code(" → ".join(map(str, sequence)))

            answer = st.number_input(
                "What comes next?",
                min_value=0,
                step=1,
            )

            if st.button(
                "Submit Pattern Result",
                use_container_width=True,
            ):
                st.session_state.experiment_score = int(
                    answer == start * 32
                )

                st.session_state.experiment_completed = True

        if st.session_state.experiment_completed:

            score = st.session_state.experiment_score

            st.success(
                f"Experiment completed. Score: {score}/1"
            )

            st.markdown(
                """
                <div class="result-box">
                <h3>🧠 Ayna's observation</h3>
                Task performance reflects behaviour on this specific
                simulated task. It should not be interpreted as a diagnosis
                or direct measurement of brain activity.
                </div>
                """,
                unsafe_allow_html=True,
            )

            result = {
                "experiment": experiment,
                "role": character,
                "equipment": equipment,
                "score": score,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            if st.button(
                "💾 Save Lab Result",
                use_container_width=True,
            ):
                st.session_state.lab_history.append(result)

                uid = user_id()

                if uid:
                    db_insert(
                        "lab_results",
                        {
                            "user_id": uid,
                            "result_json": result,
                        },
                    )

                st.success("Saved to your research history.")

            if st.button(
                "🔄 New Experiment",
                use_container_width=True,
            ):
                st.session_state.experiment_started = False
                st.session_state.experiment_completed = False
                st.session_state.memory_sequence = ""
                st.rerun()


# ============================================================
# BRAIN JOURNEY
# ============================================================

BRAIN_SYSTEMS = [
    (
        "Neuron",
        "The basic cellular unit that communicates information "
        "through electrical and chemical signalling.",
        "neuron.png",
    ),
    (
        "Synapse",
        "A specialized junction where neurons communicate with "
        "other cells.",
        "synapse.png",
    ),
    (
        "Neural Signaling",
        "Information can be transmitted through electrical activity "
        "within neurons and chemical signalling between cells.",
        "neural_signaling.gif",
    ),
    (
        "Prefrontal Cortex",
        "Supports executive functions including planning, working "
        "memory and cognitive control.",
        "prefrontal_cortex.png",
    ),
    (
        "Hippocampus",
        "A medial temporal structure strongly associated with memory "
        "formation and spatial processing.",
        "hippocampus.png",
    ),
    (
        "Striatum",
        "A basal-ganglia structure involved in action selection, "
        "reward-related learning and motor/cognitive loops.",
        "striatum.png",
    ),
    (
        "Anterior Cingulate Cortex",
        "Associated with conflict monitoring, error processing, "
        "motivation and cognitive control.",
        "acc.png",
    ),
    (
        "Attention Networks",
        "Distributed systems support orienting, alerting and "
        "executive control of attention.",
        "attention_network.png",
    ),
]


def page_brain_journey():
    header()

    st.title("🧠 Visual Brain Journey")

    names = [x[0] for x in BRAIN_SYSTEMS]

    if "brain_index" not in st.session_state:
        st.session_state.brain_index = 0

    idx = st.session_state.brain_index

    selected = st.selectbox(
        "Choose a concept",
        names,
        index=idx,
    )

    idx = names.index(selected)

    title, description, asset = BRAIN_SYSTEMS[idx]

    path = find_asset(asset)

    st.markdown(
        f"""
        <div class="world-card">
        <h2>🧠 {title}</h2>
        <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if path:
        if path.lower().endswith((".mp4", ".webm")):
            st.video(path)
        else:
            st.image(
                path,
                use_container_width=True,
            )
    else:
        st.info(
            f"Visual asset not found: assets/{asset}"
        )

    st.markdown(
        """
        <div class="result-box">
        <b>NeuroLens learning note</b><br>
        This explanation is an educational conceptual model and does
        not represent a complete map of brain function.
        </div>
        """,
        unsafe_allow_html=True,
    )

    q = st.text_input(
        f"Ask Ayna about {title}",
        key=f"brain_question_{idx}",
    )

    if st.button(
        "Ask Ayna",
        key=f"brain_ask_{idx}",
        use_container_width=True,
    ):
        answer = ask_gemini(
            f"""
            Explain {title} in cognitive neuroscience.
            User question: {q}
            Give a concise scientifically cautious answer.
            Do not diagnose.
            """
        )

        if answer:
            st.write(answer)
        else:
            st.warning("Gemini is not connected.")


# ============================================================
# BRAIN PUZZLE
# ============================================================

def make_puzzle(grid):
    total = grid * grid
    tiles = list(range(total))

    while True:
        random.shuffle(tiles)

        inversions = 0

        for i in range(total):
            for j in range(i + 1, total):
                if tiles[i] != total - 1 and tiles[j] != total - 1:
                    if tiles[i] > tiles[j]:
                        inversions += 1

        if inversions % 2 == 0:
            return tiles


def tile_image(image, tile_id, grid):
    width, height = image.size

    tile_w = width // grid
    tile_h = height // grid

    row = tile_id // grid
    col = tile_id % grid

    return image.crop(
        (
            col * tile_w,
            row * tile_h,
            (col + 1) * tile_w,
            (row + 1) * tile_h,
        )
    )


def page_puzzle():
    header()

    st.title("🧩 Brain Puzzle")

    image_path = find_asset("brain.png")

    if not image_path or Image is None:
        st.error(
            "brain.png is required. Put it in the project root or assets folder."
        )
        return

    image = Image.open(image_path).convert("RGB")

    grid = st.selectbox(
        "Puzzle size",
        [3, 4, 5],
        index=[3, 4, 5].index(
            st.session_state.puzzle_grid
        ),
    )

    if grid != st.session_state.puzzle_grid:
        st.session_state.puzzle_grid = grid
        st.session_state.puzzle_tiles = []
        st.session_state.puzzle_completed = False

    if not st.session_state.puzzle_tiles:
        st.session_state.puzzle_tiles = make_puzzle(grid)
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_started_at = time.time()
        st.session_state.puzzle_completed = False

    tiles = st.session_state.puzzle_tiles

    if dnd is not None:

        st.caption(
            "Drag a neighbouring brain piece into the empty position."
        )

        with st.container(
            key="brain_puzzle_board",
            border=True,
        ):
            for tile_id in tiles:

                with st.container(
                    key=f"bp_tile_{tile_id}",
                    border=True,
                ):

                    if tile_id == grid * grid - 1:
                        st.markdown(
                            "### ⬜ DROP HERE"
                        )
                    else:
                        st.image(
                            tile_image(
                                image,
                                tile_id,
                                grid,
                            ),
                            use_container_width=True,
                        )

        event = dnd(
            "brain_puzzle_board",
            cross=False,
            handle=False,
            indicator="ghost",
            key="brain_puzzle_dnd",
        )

        if event:

            old = list(
                st.session_state.puzzle_tiles
            )

            blank_index = old.index(
                grid * grid - 1
            )

            from_index = event.from_index

            valid = (
                abs(from_index - blank_index)
                in (1, grid)
            )

            if valid:

                new = list(old)

                new[blank_index], new[from_index] = (
                    new[from_index],
                    new[blank_index],
                )

                st.session_state.puzzle_tiles = new
                st.session_state.puzzle_moves += 1

                target = list(
                    range(grid * grid)
                )

                if new == target:

                    elapsed = (
                        time.time()
                        - st.session_state.puzzle_started_at
                    )

                    st.session_state.puzzle_completed = True
                    st.session_state.puzzle_elapsed = elapsed
                    st.session_state.games_completed += 1

                    if (
                        st.session_state.puzzle_best_time
                        is None
                        or elapsed
                        < st.session_state.puzzle_best_time
                    ):
                        st.session_state.puzzle_best_time = elapsed

                    uid = user_id()

                    if uid:
                        db_insert(
                            "brain_puzzle_results",
                            {
                                "user_id": uid,
                                "grid_size": grid,
                                "moves": st.session_state.puzzle_moves,
                                "elapsed_seconds": elapsed,
                            },
                        )

                    st.balloons()

                st.rerun()

            else:
                st.info(
                    "↩️ Non-adjacent piece. It stays in place."
                )

    else:
        st.warning(
            "Add streamlit-dnd==0.2.0 to requirements.txt "
            "to enable touch/mouse drag-and-drop."
        )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Moves",
        st.session_state.puzzle_moves,
    )

    c2.metric(
        "Round",
        st.session_state.puzzle_round,
    )

    c3.metric(
        "Best",
        (
            f"{st.session_state.puzzle_best_time:.1f}s"
            if st.session_state.puzzle_best_time
            else "—"
        ),
    )

    if st.session_state.puzzle_completed:

        st.success(
            f"🎉 Puzzle completed in "
            f"{st.session_state.puzzle_elapsed:.1f}s!"
        )

        if st.button(
            "➡️ Next Round",
            use_container_width=True,
        ):
            st.session_state.puzzle_round += 1
            st.session_state.puzzle_tiles = []
            st.session_state.puzzle_moves = 0
            st.session_state.puzzle_completed = False
            st.rerun()

    if st.button(
        "🔄 New Puzzle",
        use_container_width=True,
    ):
        st.session_state.puzzle_tiles = []
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_completed = False
        st.rerun()


# ============================================================
# BRAIN EXERCISES
# ============================================================

def page_challenges():
    header()

    st.title("🎯 Brain Challenges")

    challenge = st.selectbox(
        "Choose challenge",
        [
            "Working Memory",
            "Attention",
            "Pattern Recognition",
            "Decision Challenge",
            "Quick Reaction",
        ],
    )

    if challenge == "Working Memory":

        numbers = "".join(
            random.choice("0123456789")
            for _ in range(6)
        )

        st.code(numbers)

        answer = st.text_input(
            "Type the sequence",
            key="wm_answer",
        )

        if st.button(
            "Check Memory",
            use_container_width=True,
        ):

            score = int(
                answer.strip() == numbers
            )

            st.session_state.exercise_scores.append(
                {
                    "exercise": challenge,
                    "score": score,
                    "created_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )

            st.success(
                "Correct!" if score else "Not quite."
            )

    elif challenge == "Pattern Recognition":

        a = random.randint(2, 5)

        sequence = [
            a,
            a * 2,
            a * 4,
            a * 8,
        ]

        st.code(
            " → ".join(
                map(str, sequence)
            )
        )

        answer = st.number_input(
            "Next number",
            min_value=0,
            step=1,
        )

        if st.button(
            "Check Pattern",
            use_container_width=True,
        ):

            score = int(
                answer == a * 16
            )

            st.success(
                "Correct!" if score else "Try again."
            )

            st.session_state.exercise_scores.append(
                {
                    "exercise": challenge,
                    "score": score,
                }
            )

    elif challenge == "Decision Challenge":

        choice = st.radio(
            "Which would you choose?",
            [
                "PKR 1,000 today",
                "PKR 1,500 after 30 days",
            ],
        )

        if st.button(
            "Record Decision",
            use_container_width=True,
        ):

            st.session_state.exercise_scores.append(
                {
                    "exercise": challenge,
                    "choice": choice,
                    "score": 1,
                }
            )

            st.success(
                "Decision recorded for this exercise."
            )

    elif challenge == "Attention":

        target = random.choice(
            ["X", "K", "M"]
        )

        sequence = [
            random.choice(
                ["A", "B", "C", "D", target]
            )
            for _ in range(12)
        ]

        st.write(
            "Target:",
            target,
        )

        st.code(" ".join(sequence))

        answer = st.text_input(
            "Target letter",
        )

        if st.button(
            "Check Attention",
            use_container_width=True,
        ):

            score = int(
                answer.upper() == target
            )

            st.success(
                "Correct!" if score else "Incorrect."
            )

            st.session_state.exercise_scores.append(
                {
                    "exercise": challenge,
                    "score": score,
                }
            )

    else:

        st.info(
            "Press START and react as quickly as possible."
        )

        if st.button(
            "⚡ START",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.reaction_start = time.time()
            st.session_state.reaction_ready = True
            st.rerun()

        if st.session_state.get(
            "reaction_ready",
            False,
        ):

            st.success(
                "NOW — press the button!"
            )

            if st.button(
                "🟢 REACT",
                use_container_width=True,
            ):

                elapsed = (
                    time.time()
                    - st.session_state.reaction_start
                )

                st.session_state.exercise_scores.append(
                    {
                        "exercise": challenge,
                        "reaction_seconds": elapsed,
                        "score": 1,
                    }
                )

                st.session_state.reaction_ready = False

                st.success(
                    f"Reaction time: {elapsed:.3f} seconds"
                )


# ============================================================
# ASK AYNA
# ============================================================

def speak_browser(text):
    safe = (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    components.html(
        f"""
        <script>
        const text = `{safe}`;
        if ("speechSynthesis" in window) {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.rate = 0.95;
            u.pitch = 1.05;
            window.speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=0,
    )


def page_ask_ayna():
    header()

    st.title("🤖 Ask Ayna")

    for msg in st.session_state.ayna_messages:
        with st.chat_message(
            msg["role"]
        ):
            st.write(msg["content"])

    prompt = st.chat_input(
        "Ask Ayna about cognition, behaviour or neuroscience..."
    )

    if prompt:

        st.session_state.ayna_messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        answer = ask_gemini(
            f"""
            You are Ayna, a cautious cognitive neuroscience AI guide.

            Answer the user naturally.

            Rules:
            - Do not diagnose.
            - Do not claim to read minds.
            - Do not claim that simple games measure brain activity.
            - Distinguish educational explanations from clinical conclusions.
            - Use uncertainty where appropriate.

            User:
            {prompt}
            """
        )

        if not answer:
            answer = (
                "Gemini is not connected yet. "
                "Please add GEMINI_API_KEY to Streamlit Secrets."
            )

        st.session_state.ai_history.append(
            {
                "question": prompt,
                "answer": answer,
            }
        )

        st.session_state.ayna_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        uid = user_id()

        if uid:
            db_insert(
                "ai_requests",
                {
                    "user_id": uid,
                    "request_text": prompt[:5000],
                    "response_text": answer[:10000],
                },
            )

        st.rerun()

    if st.session_state.ai_history:

        latest = st.session_state.ai_history[-1]["answer"]

        if st.button(
            "🔊 Speak Ayna",
            use_container_width=True,
        ):
            speak_browser(latest)


# ============================================================
# AI MOOD + FACE
# ============================================================

def page_mood():
    header()

    st.title("🎭 AI Mood & Behaviour")

    st.caption(
        "AI-assisted interpretation of observable communication or "
        "facial-expression cues. This is not mind-reading, diagnosis "
        "or a reliable measurement of hidden emotion."
    )

    tab1, tab2 = st.tabs(
        [
            "🎙️ Voice",
            "📷 Face",
        ]
    )

    with tab1:

        voice = st.audio_input(
            "Record your voice"
        )

        if voice:

            if st.button(
                "📤 Analyze Voice",
                type="primary",
                use_container_width=True,
            ):

                prompt = """
                Return ONLY JSON with:
                transcript,
                emoji,
                vibe_label,
                explanation.

                Vibe_label must describe observable
                communication/acoustic characteristics only.

                Do not claim certainty about hidden emotion,
                personality, health or diagnosis.

                Use labels such as:
                Positive/energetic-sounding,
                Calm-sounding,
                Neutral/mixed,
                Tense/stressed-sounding,
                Low-energy-sounding,
                Uncertain/mixed.
                """

                result = ask_gemini(
                    prompt,
                    voice.getvalue(),
                    voice.type or "audio/wav",
                )

                parsed = safe_json(result)

                if not parsed:

                    parsed = {
                        "transcript": result,
                        "emoji": "🧩",
                        "vibe_label": "Uncertain/mixed",
                        "explanation": (
                            "The AI response could not be "
                            "structured reliably."
                        ),
                    }

                st.session_state.voice_result = parsed

                uid = user_id()

                if uid:
                    db_insert(
                        "voice_mood_results",
                        {
                            "user_id": uid,
                            "result_json": parsed,
                        },
                    )

        if st.session_state.voice_result:

            r = st.session_state.voice_result

            st.markdown(
                f"## {r.get('emoji','🧩')} "
                f"{r.get('vibe_label','Uncertain/mixed')}"
            )

            st.subheader("📝 Transcript")
            st.write(
                r.get(
                    "transcript",
                    "",
                )
            )

            st.subheader(
                "💬 Voice interpretation"
            )

            st.write(
                r.get(
                    "explanation",
                    "",
                )
            )

    with tab2:

        picture = st.camera_input(
            "Capture a face image"
        )

        if picture:

            if st.button(
                "🔍 Analyze Expression",
                type="primary",
                use_container_width=True,
            ):

                prompt = """
                Return ONLY JSON with:
                emoji,
                expression_label,
                explanation.

                Describe only visible facial-expression cues.
                Do not identify the person.
                Do not infer hidden mental state.
                Do not diagnose.
                """

                result = ask_gemini(
                    prompt,
                    picture.getvalue(),
                    picture.type or "image/jpeg",
                )

                parsed = safe_json(result)

                if not parsed:

                    parsed = {
                        "emoji": "🧩",
                        "expression_label": "Uncertain",
                        "explanation": result,
                    }

                st.session_state.face_result = parsed

        if st.session_state.face_result:

            r = st.session_state.face_result

            st.markdown(
                f"## {r.get('emoji','🧩')} "
                f"{r.get('expression_label','Uncertain')}"
            )

            st.write(
                r.get(
                    "explanation",
                    "",
                )
            )

    st.divider()

    st.info(
        "Voice and facial-expression analysis provide probabilistic "
        "AI interpretations only. They cannot reliably determine a "
        "person's true emotional state."
    )


# ============================================================
# RESEARCH BOOK
# ============================================================

def page_research():
    header()

    st.title("📚 Research World")

    query = st.text_input(
        "Search Europe PMC",
        placeholder="e.g. attention cognitive neuroscience",
    )

    if st.button(
        "🔎 Search Papers",
        use_container_width=True,
    ):

        if not query.strip():
            st.warning("Enter a research topic.")
        elif requests is None:
            st.error("Requests package is unavailable.")
        else:

            try:

                url = (
                    "https://www.ebi.ac.uk/europepmc/webservices/"
                    "rest/search"
                )

                response = requests.get(
                    url,
                    params={
                        "query": query,
                        "format": "json",
                        "pageSize": 10,
                    },
                    timeout=15,
                )

                data = response.json()

                st.session_state.research_results = (
                    data.get("resultList", {})
                    .get("result", [])
                )

            except Exception:
                st.error(
                    "Research search failed."
                )

    for paper in st.session_state.research_results:

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

        st.caption(
            f"Publication year: {year} | PMID: {pmid}"
        )

        if pmid:
            st.markdown(
                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            )

        if st.button(
            "🧠 AI Summary",
            key=f"summary_{pmid}_{title[:10]}",
        ):

            summary = ask_gemini(
                f"""
                Give a cautious scientific summary of this paper title:

                {title}

                Do not invent results.
                Explain that this is a title-based overview if
                the full paper is unavailable.
                """
            )

            st.write(
                summary or "AI unavailable."
            )

        st.divider()

    st.subheader("📝 Research Notes")

    note = st.text_area(
        "Write a research note",
        max_chars=5000,
    )

    if st.button(
        "Save Research Note",
        use_container_width=True,
    ):

        if note.strip():

            st.session_state.research_notes.append(
                {
                    "text": note.strip(),
                    "created_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )

            uid = user_id()

            if uid:
                db_insert(
                    "research_notes",
                    {
                        "user_id": uid,
                        "note": note.strip(),
                    },
                )

            st.success("Research note saved.")


# ============================================================
# PRIVATE AYNA
# ============================================================

def pin_hash(pin, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt,
        150000,
    ).hex()


def page_private():
    header()

    st.title("🔒 Private Ayna")

    if not st.session_state.private_pin_hash:

        st.info(
            "Create a private PIN. Use 4–6 digits."
        )

        pin = st.text_input(
            "New PIN",
            type="password",
        )

        confirm = st.text_input(
            "Confirm PIN",
            type="password",
        )

        if st.button(
            "Create Private PIN",
            use_container_width=True,
        ):

            if (
                pin.isdigit()
                and 4 <= len(pin) <= 6
                and pin == confirm
            ):

                salt = secrets.token_bytes(16)

                st.session_state.private_pin_salt = (
                    base64.b64encode(salt).decode()
                )

                st.session_state.private_pin_hash = (
                    pin_hash(pin, salt)
                )

                st.success(
                    "Private PIN created."
                )

                st.rerun()

            else:
                st.error(
                    "PIN must be 4–6 digits and both entries must match."
                )

    else:

        if not st.session_state.private_unlocked:

            pin = st.text_input(
                "Enter PIN",
                type="password",
            )

            if st.button(
                "🔓 Unlock",
                use_container_width=True,
            ):

                salt = base64.b64decode(
                    st.session_state.private_pin_salt
                )

                if (
                    pin_hash(pin, salt)
                    == st.session_state.private_pin_hash
                ):

                    st.session_state.private_unlocked = True
                    st.rerun()

                else:
                    st.error("Incorrect PIN.")

        else:

            st.success(
                "Private Ayna unlocked."
            )

            private_message = st.chat_input(
                "Write privately..."
            )

            if private_message:

                uid = user_id()

                if uid:
                    db_insert(
                        "private_ayna_messages",
                        {
                            "user_id": uid,
                            "content": private_message[:5000],
                        },
                    )

                st.success(
                    "Private message saved."
                )

            if st.button(
                "🔒 Lock Private Ayna",
                use_container_width=True,
            ):

                st.session_state.private_unlocked = False
                st.rerun()


# ============================================================
# NEUROSOCIAL
# ============================================================

def page_social():
    header()

    st.title("🌐 NeuroSocial")

    uid = user_id()

    if not uid:

        st.warning(
            "Login is required for NeuroSocial."
        )

        login_ui()
        return

    tabs = st.tabs(
        [
            "👤 Profile",
            "👥 Friends",
            "💬 Messages",
        ]
    )

    with tabs[0]:

        p = profile()

        username = st.text_input(
            "Username",
            value=p.get(
                "username",
                "",
            ),
        )

        display_name = st.text_input(
            "Display name",
            value=p.get(
                "display_name",
                "",
            ),
        )

        bio = st.text_area(
            "Bio",
            value=p.get(
                "bio",
                "",
            ),
        )

        if st.button(
            "Save Profile",
            use_container_width=True,
        ):

            db_update(
                "profiles",
                {
                    "username": re.sub(
                        r"[^A-Za-z0-9_.-]",
                        "",
                        username,
                    )[:30],
                    "display_name": display_name[:80],
                    "bio": bio[:300],
                },
                {"id": uid},
            )

            st.success("Profile saved.")

    with tabs[1]:

        search = st.text_input(
            "Find a researcher/user",
        )

        if search:

            rows = db_select(
                "profiles",
                limit=20,
            )

            for row in rows:

                if (
                    search.lower()
                    in str(
                        row.get(
                            "username",
                            "",
                        )
                    ).lower()
                ):

                    st.write(
                        f"@{row.get('username','user')}"
                    )

                    if row.get("id") != uid:

                        if st.button(
                            "Send Friend Request",
                            key=f"friend_{row.get('id')}",
                        ):

                            db_insert(
                                "friend_requests",
                                {
                                    "sender_id": uid,
                                    "receiver_id": row.get(
                                        "id"
                                    ),
                                    "status": "pending",
                                },
                            )

                            st.success(
                                "Friend request sent."
                            )

    with tabs[2]:

        st.info(
            "Messages are stored through Supabase. "
            "A dedicated realtime socket can be added later."
        )

        message = st.chat_input(
            "Write a message..."
        )

        if message:

            st.write(
                f"You: {message}"
            )


# ============================================================
# BEHAVIOUR DECODING / CONSULTATION
# ============================================================

PRICES = {
    "20 min": "PKR 1,000 / International $8",
    "30 min": "PKR 1,500 / International $10",
    "45 min": "PKR 2,000 / International $12",
    "Advice / Consultation": "PKR 1,500 / International $10",
}


def page_consultation():
    header()

    st.title("🧩 Behaviour Decoding / 1-to-1")

    for k, v in PRICES.items():
        st.write(
            f"**{k}:** {v}"
        )

    st.divider()

    name = st.text_input(
        "Name"
    )

    contact = st.text_input(
        "Contact / Email"
    )

    topic = st.text_area(
        "Topic / Question"
    )

    duration = st.selectbox(
        "Session",
        list(PRICES.keys()),
    )

    payment = st.selectbox(
        "Payment method",
        [
            "Easypaisa",
            "International Payment",
        ],
    )

    reference = st.text_input(
        "Payment reference / transaction ID"
    )

    if payment == "Easypaisa":

        if EASYPAISA_NUMBER:
            st.info(
                f"Easypaisa: {EASYPAISA_NUMBER}"
            )
        else:
            st.warning(
                "Easypaisa merchant number is not configured yet."
            )

    else:

        if INTERNATIONAL_PAYMENT_URL:
            st.markdown(
                f"Payment gateway: {INTERNATIONAL_PAYMENT_URL}"
            )
        else:
            st.warning(
                "International payment gateway is not configured."
            )

    if st.button(
        "📨 Submit Consultation Request",
        type="primary",
        use_container_width=True,
    ):

        if not name.strip() or not contact.strip():
            st.error(
                "Name and contact are required."
            )

        else:

            uid = user_id()

            payload = {
                "user_id": uid,
                "name": name[:100],
                "contact": contact[:200],
                "topic": topic[:5000],
                "session_type": duration,
                "payment_method": payment,
                "payment_reference": reference[:200],
                "payment_status": "submitted",
            }

            result = db_insert(
                "consultation_requests",
                payload,
            )

            if result is not None:
                st.success(
                    "Request submitted. Payment verification is handled separately."
                )
            else:
                st.warning(
                    "Request could not be saved. Check Supabase configuration."
                )


# ============================================================
# PROGRESS
# ============================================================

def page_progress():
    header()

    st.title("📈 My Progress")

    st.metric(
        "Lab Experiments",
        len(
            st.session_state.lab_history
        ),
    )

    st.metric(
        "Exercises",
        len(
            st.session_state.exercise_scores
        ),
    )

    st.metric(
        "Puzzle Rounds",
        st.session_state.games_completed,
    )

    st.metric(
        "AI Requests",
        st.session_state.ai_requests,
    )

    if go:

        labels = [
            "Lab",
            "Exercises",
            "Puzzle",
            "AI",
        ]

        values = [
            len(
                st.session_state.lab_history
            ),
            len(
                st.session_state.exercise_scores
            ),
            st.session_state.games_completed,
            st.session_state.ai_requests,
        ]

        fig = go.Figure(
            go.Bar(
                x=labels,
                y=values,
            )
        )

        fig.update_layout(
            title="NeuroLens Activity",
            height=350,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.subheader("🏆 Achievements")

    achievements = []

    if st.session_state.lab_history:
        achievements.append(
            "🧪 First Lab Experiment"
        )

    if st.session_state.games_completed:
        achievements.append(
            "🧩 Brain Puzzle Completed"
        )

    if st.session_state.ai_requests >= 5:
        achievements.append(
            "🤖 AI Explorer"
        )

    if st.session_state.research_notes:
        achievements.append(
            "📚 Research Note Keeper"
        )

    if not achievements:
        st.info(
            "Complete activities to unlock achievements."
        )

    for achievement in achievements:
        st.success(achievement)


# ============================================================
# SECURITY
# ============================================================

def page_security():
    header()

    st.title("🛡️ Security & Privacy Center")

    items = [
        (
            "🔑 API keys",
            "Keep Gemini and Supabase credentials inside Streamlit Secrets."
        ),
        (
            "🧂 Private PIN",
            "Private PIN uses salted PBKDF2-HMAC-SHA256 in the session."
        ),
        (
            "🤖 AI",
            "AI output is probabilistic and should not be treated as diagnosis."
        ),
        (
            "🎙️ Voice",
            "Voice interpretation describes observable communication cues only."
        ),
        (
            "📷 Face",
            "Face analysis describes visible expression cues and does not identify people."
        ),
        (
            "🧠 Experiments",
            "NeuroLens tasks are educational simulations, not clinical measurements."
        ),
        (
            "💳 Payments",
            "Automatic payment verification requires a real merchant/API integration."
        ),
    ]

    for title, text in items:

        st.markdown(
            f"""
            <div class="world-card">
            <h3>{title}</h3>
            <p>{text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# SETTINGS
# ============================================================

def page_settings():
    header()

    st.title("⚙️ Settings")

    language = st.selectbox(
        "Language",
        [
            "English",
            "Roman English",
        ],
    )

    model = st.text_input(
        "Gemini model",
        value=GEMINI_MODEL,
    )

    st.write(
        f"AI connection: "
        f"**{'Connected' if ai_available() else 'Not connected'}**"
    )

    st.write(
        f"Supabase: "
        f"**{'Connected' if supabase_available() else 'Not connected'}**"
    )

    st.write(
        f"AI requests this session: "
        f"**{st.session_state.ai_requests}/{AI_SESSION_LIMIT}**"
    )

    if st.button(
        "🧹 Reset Local Progress",
        use_container_width=True,
    ):

        for key in [
            "lab_history",
            "exercise_scores",
            "ai_history",
            "research_notes",
            "games_completed",
        ]:

            if key in st.session_state:

                if isinstance(
                    st.session_state[key],
                    list,
                ):
                    st.session_state[key] = []

                else:
                    st.session_state[key] = 0

        st.success(
            "Local session progress reset."
        )


# ============================================================
# ACCOUNT
# ============================================================

def page_account():
    header()

    st.title("👤 Account")

    if not current_user():

        login_ui()
        return

    p = profile()

    st.success(
        f"Signed in as "
        f"@{p.get('username', user_email())}"
    )

    st.write(
        f"Email: **{user_email()}**"
    )

    st.write(
        f"Bio: **{p.get('bio','No bio yet.')}**"
    )

    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):

        try:
            if supabase_available():
                supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.auth_user = None
        st.session_state.private_unlocked = False
        st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            "## 🧠 NEUROLENS"
        )

        st.caption(
            "Explore cognition, behavior & the brain"
        )

        pages = [
            "NeuroWorld",
            "Account",
            "Cognitive Lab",
            "Brain Journey",
            "Brain Puzzle",
            "Brain Challenges",
            "Ask Ayna",
            "AI Mood & Behaviour",
            "Research World",
            "NeuroSocial",
            "Private Ayna",
            "Behaviour Decoding",
            "My Progress",
            "Security & Privacy",
            "Settings",
        ]

        current = st.session_state.page

        selected = st.radio(
            "Navigate",
            pages,
            index=(
                pages.index(current)
                if current in pages
                else 0
            ),
        )

        if selected != current:
            st.session_state.page = selected
            st.rerun()

        st.divider()

        st.write(
            "AI:",
            "🟢 Connected"
            if ai_available()
            else "🔴 Not connected",
        )

        st.write(
            "Supabase:",
            "🟢 Connected"
            if supabase_available()
            else "🔴 Not connected",
        )


# ============================================================
# ROUTER
# ============================================================

def main():

    sidebar()

    page = st.session_state.page

    if page == "NeuroWorld":
        page_neuroworld()

    elif page == "Account":
        page_account()

    elif page == "Cognitive Lab":
        page_lab()

    elif page == "Brain Journey":
        page_brain_journey()

    elif page == "Brain Puzzle":
        page_puzzle()

    elif page == "Brain Challenges":
        page_challenges()

    elif page == "Ask Ayna":
        page_ask_ayna()

    elif page == "AI Mood & Behaviour":
        page_mood()

    elif page == "Research World":
        page_research()

    elif page == "NeuroSocial":
        page_social()

    elif page == "Private Ayna":
        page_private()

    elif page == "Behaviour Decoding":
        page_consultation()

    elif page == "My Progress":
        page_progress()

    elif page == "Security & Privacy":
        page_security()

    elif page == "Settings":
        page_settings()


if __name__ == "__main__":
    main()
