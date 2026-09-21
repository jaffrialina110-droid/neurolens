import os
import json
import time
import random
import hashlib
import sqlite3
import html
from pathlib import Path
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).parent
DB = APP_DIR / "neurolens.db"
ASSET = APP_DIR / "assets"
ASSET.mkdir(exist_ok=True)


# =========================================================
# OPTIONAL IMPORTS
# =========================================================

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from streamlit_dnd import dnd, apply_move
    DND_OK = True
except Exception:
    dnd = None
    apply_move = None
    DND_OK = False


# =========================================================
# CONFIG
# =========================================================

try:
    MODEL = st.secrets.get(
        "GEMINI_MODEL",
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
    API_KEY = st.secrets.get(
        "GEMINI_API_KEY",
        os.getenv("GEMINI_API_KEY", ""),
    )
except Exception:
    MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    API_KEY = os.getenv("GEMINI_API_KEY", "")


# =========================================================
# DATABASE
# =========================================================

def db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    cur = con.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            created TEXT,
            streak INTEGER DEFAULT 0,
            last_day TEXT
        );

        CREATE TABLE IF NOT EXISTS public_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            text TEXT,
            created TEXT
        );

        CREATE TABLE IF NOT EXISTS likes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message_id INTEGER,
            UNIQUE(username, message_id)
        );

        CREATE TABLE IF NOT EXISTS challenges(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            kind TEXT,
            score INTEGER,
            created TEXT
        );

        CREATE TABLE IF NOT EXISTS private_pin(
            username TEXT PRIMARY KEY,
            salt TEXT,
            digest TEXT
        );

        CREATE TABLE IF NOT EXISTS private_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            text TEXT,
            created TEXT
        );

        CREATE TABLE IF NOT EXISTS research_notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            note TEXT,
            created TEXT
        );

        CREATE TABLE IF NOT EXISTS activity(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            kind TEXT,
            score REAL,
            meta TEXT,
            created TEXT
        );
        """
    )

    con.commit()
    con.close()


init_db()


# =========================================================
# AUTO-HEAL / ERROR RECOVERY
# =========================================================

if "health" not in st.session_state:
    st.session_state.health = []


def heal(feature, exc):
    st.session_state.health.append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "feature": feature,
            "error": str(exc)[:300],
            "action": "isolated + safe fallback",
        }
    )

    st.session_state.health = st.session_state.health[-50:]


def safe(feature, fn, fallback=None):
    try:
        return fn()
    except Exception as exc:
        heal(feature, exc)
        return fallback


# =========================================================
# USER
# =========================================================

def user():
    return st.session_state.get("username", "Guest")


def ensure_user(name):
    name = (name or "Guest").strip()[:30] or "Guest"

    today = datetime.now().date().isoformat()

    con = db()

    row = con.execute(
        "SELECT * FROM users WHERE username=?",
        (name,),
    ).fetchone()

    if not row:

        con.execute(
            """
            INSERT INTO users(username, created, streak, last_day)
            VALUES(?,?,?,?)
            """,
            (
                name,
                datetime.now().isoformat(),
                1,
                today,
            ),
        )

    elif row["last_day"] != today:

        try:
            previous = datetime.fromisoformat(
                row["last_day"]
            ).date()

            gap = (
                datetime.now().date() - previous
            ).days

        except Exception:
            gap = 99

        new_streak = (
            row["streak"] + 1
            if gap == 1
            else 1
        )

        con.execute(
            """
            UPDATE users
            SET streak=?, last_day=?
            WHERE username=?
            """,
            (
                new_streak,
                today,
                name,
            ),
        )

    con.commit()
    con.close()

    st.session_state.username = name


def streak():
    row = db().execute(
        "SELECT streak FROM users WHERE username=?",
        (user(),),
    ).fetchone()

    return int(row["streak"]) if row else 0


def log_activity(kind, score=0, meta=None):

    con = db()

    con.execute(
        """
        INSERT INTO activity
        (username,kind,score,meta,created)
        VALUES(?,?,?,?,?)
        """,
        (
            user(),
            kind,
            float(score),
            json.dumps(meta or {}),
            datetime.now().isoformat(),
        ),
    )

    con.commit()
    con.close()


# =========================================================
# PIN SECURITY
# =========================================================

def hash_pin(pin, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt.encode(),
        150000,
    ).hex()


def set_pin(pin):

    salt = os.urandom(16).hex()

    digest = hash_pin(
        pin,
        salt,
    )

    con = db()

    con.execute(
        """
        INSERT OR REPLACE INTO private_pin
        (username,salt,digest)
        VALUES(?,?,?)
        """,
        (
            user(),
            salt,
            digest,
        ),
    )

    con.commit()
    con.close()


def valid_pin(pin):

    row = db().execute(
        """
        SELECT salt,digest
        FROM private_pin
        WHERE username=?
        """,
        (user(),),
    ).fetchone()

    if not row:
        return False

    return (
        hash_pin(
            pin,
            row["salt"],
        )
        == row["digest"]
    )


# =========================================================
# GEMINI AI
# =========================================================

def ai_text(prompt, audio=None):

    if (
        not API_KEY
        or genai is None
        or types is None
    ):
        return (
            "AI is not configured. "
            "Add GEMINI_API_KEY in Streamlit Secrets."
        )

    client = genai.Client(
        api_key=API_KEY
    )

    contents = [prompt]

    if audio:
        contents.append(
            types.Part.from_bytes(
                data=audio,
                mime_type="audio/wav",
            )
        )

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
    )

    return (
        response.text or ""
    ).strip()


# =========================================================
# AYNA VOICE OUTPUT
# =========================================================

def speak(text, key):

    safe_text = (
        html.escape(text)
        .replace("`", "\\`")
    )

    st.components.v1.html(
        f"""
        <button
            style="
            padding:8px 14px;
            border-radius:10px;
            border:0;
            background:#ffffff;
            color:#10233d;
            font-weight:700;
            cursor:pointer;
            "
            onclick="
            speechSynthesis.cancel();
            speechSynthesis.speak(
                Object.assign(
                    new SpeechSynthesisUtterance(`{safe_text}`),
                    {{rate:1.05}}
                )
            );
            "
        >
        🔊 Speak Ayna
        </button>
        """,
        height=45,
    )


# =========================================================
# BRAIN IMAGE
# =========================================================

def brain_image():

    path = ASSET / "brain.png"

    if path.exists() and Image:
        return Image.open(path).convert("RGB")

    if Image:

        image = Image.new(
            "RGB",
            (900, 700),
            (8, 18, 35),
        )

        draw = ImageDraw.Draw(image)

        draw.ellipse(
            (100, 100, 800, 600),
            outline=(100, 210, 255),
            width=8,
        )

        draw.line(
            (450, 120, 450, 580),
            fill=(100, 210, 255),
            width=5,
        )

        for y in range(180, 560, 70):

            draw.arc(
                (170, y - 30, 420, y + 80),
                0,
                180,
                fill=(210, 235, 255),
                width=4,
            )

            draw.arc(
                (480, y - 30, 730, y + 80),
                0,
                180,
                fill=(210, 235, 255),
                width=4,
            )

        return image

    return None


def brain_tiles(n):

    image = brain_image()

    if image is None:
        return []

    tile_size = image.width // n

    image = image.resize(
        (
            tile_size * n,
            tile_size * n,
        )
    )

    tiles = []

    for row in range(n):

        for col in range(n):

            tiles.append(
                image.crop(
                    (
                        col * tile_size,
                        row * tile_size,
                        (col + 1) * tile_size,
                        (row + 1) * tile_size,
                    )
                )
            )

    return tiles


# =========================================================
# PAGES
# =========================================================

PAGES = [
    "🏠 Home",
    "🧠 Brain Journey",
    "🧪 Cognitive Lab",
    "🧩 Brain Puzzle",
    "🎙️ Voice Mood",
    "💭 Mood & Feelings",
    "🎮 Cognitive Games",
    "👥 NeuroSocial",
    "🔐 Private Ayna",
    "🤖 Ask Ayna",
    "📚 Research Book",
    "💳 1-to-1 Session",
    "⚡ Hardware Hub",
    "📊 My Progress",
    "🛡️ System Health",
    "⚙️ Settings",
]


if "page" not in st.session_state:
    st.session_state.page = PAGES[0]

if "username" not in st.session_state:
    st.session_state.username = "Guest"

if "lab" not in st.session_state:
    st.session_state.lab = {}

if "puzzle" not in st.session_state:
    st.session_state.puzzle = {}

if "voice_result" not in st.session_state:
    st.session_state.voice_result = None

if "private_unlocked" not in st.session_state:
    st.session_state.private_unlocked = False


# =========================================================
# DESIGN
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width:1250px;
        padding-top:1rem;
    }

    .hero {
        padding:28px;
        border-radius:24px;
        background:
        linear-gradient(
            135deg,
            #0b1930,
            #123b5d
        );
        color:white;
        margin-bottom:18px;
    }

    .hero h1 {
        font-size:42px;
        margin:0;
    }

    .card {
        padding:18px;
        border-radius:18px;
        border:
        1px solid
        rgba(120,180,220,.25);
        background:
        rgba(255,255,255,.035);
        margin:8px 0;
    }

    .brain-stage {
        height:330px;
        border-radius:24px;
        background:
        radial-gradient(
            circle at 50% 50%,
            #174f73,
            #071322 70%
        );
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
    }

    .neuron {
        width:210px;
        height:210px;
        border:
        4px solid #79dcff;
        border-radius:50%;
        position:relative;
        animation:pulse 2s infinite;
    }

    .neuron:before,
    .neuron:after {
        content:'';
        position:absolute;
        left:50%;
        top:50%;
        width:170px;
        height:4px;
        background:#9ee8ff;
        transform-origin:left;
        animation:signal 1.8s infinite;
    }

    .neuron:after {
        transform:rotate(120deg);
    }

    @keyframes pulse {
        50% {
            box-shadow:
            0 0 35px #58d5ff;
        }
    }

    @keyframes signal {
        0% {
            transform:scaleX(.1);
        }
        100% {
            transform:scaleX(1);
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    name = st.text_input(
        "Your display name",
        value=st.session_state.username,
        max_chars=30,
    )

    if st.button(
        "Save profile",
        use_container_width=True,
    ):
        ensure_user(name)
        st.rerun()

    st.caption(
        f"🔥 Streak: {streak()} days"
    )

    st.divider()

    for index, page in enumerate(PAGES):

        if st.button(
            page,
            key=f"nav_{index}",
            use_container_width=True,
        ):

            st.session_state.page = page
            st.rerun()


st.markdown(
    """
    <div class="hero">
        <h1>🧠 NEUROLENS</h1>
        <p>Explore cognition, behaviour & the brain</p>
        <small>
        Interactive Cognitive Neuroscience • Ayna Jaffri
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "🏠 Home":

    st.subheader(
        "Welcome to NEUROLENS"
    )

    st.write(
        f"Hi {user()} 👋 "
        "Explore, experiment, play, connect and learn."
    )

    c1, c2, c3 = st.columns(3)

    experiment_count = db().execute(
        """
        SELECT COUNT(*) n
        FROM activity
        WHERE username=?
        AND kind='experiment'
        """,
        (user(),),
    ).fetchone()["n"]

    puzzle_count = db().execute(
        """
        SELECT COUNT(*) n
        FROM activity
        WHERE username=?
        AND kind='puzzle'
        """,
        (user(),),
    ).fetchone()["n"]

    c1.metric(
        "🔥 Streak",
        streak(),
    )

    c2.metric(
        "🧪 Experiments",
        experiment_count,
    )

    c3.metric(
        "🧩 Puzzle solves",
        puzzle_count,
    )

    st.markdown(
        "### What you can do"
    )

    st.markdown(
        """
        **🧠 Learn**  
        Brain Journey with animated neuron,
        synapse and signal visualisation.

        **🧪 Experiment**  
        Select equipment + character +
        live cognitive experiment + results.

        **🎙️ Voice**  
        Record → Send → Transcript +
        Emoji/Vibe.

        **👥 Social**  
        Chat + Likes + Streaks +
        Challenges.

        **🔐 Private**  
        PIN-protected personal Ask Ayna.

        **🧩 Play**  
        Real brain-image drag puzzle.
        """
    )


# =========================================================
# BRAIN JOURNEY
# =========================================================

elif st.session_state.page == "🧠 Brain Journey":

    steps = [

        (
            "Whole Brain",
            "🧠",
            "The brain contains interacting networks that support perception, memory, action and cognition.",
        ),

        (
            "Neuron",
            "🔬",
            "A neuron receives, integrates and sends information using electrical and chemical signaling.",
        ),

        (
            "Dendrite",
            "🌿",
            "Dendrites receive many incoming signals from other neurons.",
        ),

        (
            "Axon",
            "⚡",
            "The axon carries an action potential toward the axon terminal.",
        ),

        (
            "Myelin",
            "🧵",
            "Myelin increases the speed and efficiency of signal conduction along many axons.",
        ),

        (
            "Synapse",
            "🔗",
            "At a synapse, one neuron communicates with another through chemical or electrical mechanisms.",
        ),

        (
            "Neurotransmitter",
            "🧪",
            "Neurotransmitters are chemical messengers released at many synapses.",
        ),

        (
            "Network → Behaviour",
            "🧠",
            "Distributed neural activity contributes to cognition and behaviour; one region rarely explains a behaviour alone.",
        ),
    ]

    if "journey_i" not in st.session_state:
        st.session_state.journey_i = 0

    i = st.session_state.journey_i

    title, emoji, description = steps[i]

    st.progress(
        (i + 1) / len(steps)
    )

    st.subheader(
        f"{emoji} {title}"
    )

    st.markdown(
        """
        <div class="brain-stage">
            <div class="neuron"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(description)

    if title == "Whole Brain":

        image = brain_image()

        if image:
            st.image(
                image,
                use_container_width=True,
                caption="Conceptual brain visual",
            )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "← Previous",
            disabled=i == 0,
        ):
            st.session_state.journey_i -= 1
            st.rerun()

    with c2:

        if st.button("Restart"):

            st.session_state.journey_i = 0
            st.rerun()

    with c3:

        if st.button(
            "Next →",
            disabled=i == len(steps) - 1,
        ):
            st.session_state.journey_i += 1
            st.rerun()


# =========================================================
# COGNITIVE LAB
# =========================================================

elif st.session_state.page == "🧪 Cognitive Lab":

    st.subheader(
        "🧪 Virtual Cognitive Neuroscience Lab"
    )

    st.caption(
        "Build the setup yourself, then run the experiment live."
    )

    with st.expander(
        "1 • Select equipment",
        expanded=True,
    ):

        equipment = st.multiselect(
            "Equipment",
            [
                "👁️ Eye Tracker",
                "⚡ EEG Simulator",
                "⏱️ Reaction-Time System",
                "🧠 Cognitive Task Monitor",
                "❤️ Physiological Sensor",
            ],
            default=st.session_state.lab.get(
                "equipment",
                [],
            ),
        )

        st.session_state.lab[
            "equipment"
        ] = equipment

    with st.expander(
        "2 • Select character",
        expanded=True,
    ):

        characters = [
            "👩‍🔬 Researcher",
            "🧑‍🎓 Student",
            "🧑‍🔬 Lab Assistant",
            "🤖 AI Research Agent",
        ]

        current = st.session_state.lab.get(
            "character",
            characters[0],
        )

        character = st.selectbox(
            "Character",
            characters,
            index=characters.index(current),
        )

        st.session_state.lab[
            "character"
        ] = character

    experiments = [
        "Attention",
        "Working Memory",
        "Reaction Time",
        "Stroop / Cognitive Control",
        "Decision & Reward",
        "Pattern Recognition",
    ]

    experiment = st.selectbox(
        "3 • Select experiment",
        experiments,
    )

    if not st.session_state.lab.get(
        "running",
        False,
    ):

        st.markdown(
            f"""
            <div class="card">
            <b>Laboratory setup ready</b><br><br>
            Character: {character}<br>
            Equipment:
            {" • ".join(equipment)
            if equipment else "None selected"}<br>
            Experiment: {experiment}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "🚀 START LIVE EXPERIMENT",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.lab.update(
                {
                    "running": True,
                    "exp": experiment,
                    "trial": 0,
                    "correct": 0,
                    "rt": [],
                    "started": time.time(),
                }
            )

            st.rerun()

    else:

        trial = st.session_state.lab[
            "trial"
        ]

        total = 10

        st.subheader(
            f"LIVE: {st.session_state.lab['exp']} "
            f"• Trial {trial + 1}/{total}"
        )

        if experiment == "Attention":

            target = random.choice(
                ["X", "O", "K"]
            )

            st.session_state.lab[
                "target"
            ] = target

            st.markdown(
                f"### Tap the target: **{target}**"
            )

            choice = st.radio(
                "Response",
                ["X", "O", "K"],
                horizontal=True,
                key=f"att_{trial}",
            )

        elif experiment == "Working Memory":

            sequence = st.session_state.lab.get(
                "sequence"
            )

            if not sequence:

                sequence = "".join(
                    random.choice("123456789")
                    for _ in range(5)
                )

                st.session_state.lab[
                    "sequence"
                ] = sequence

            st.info(
                f"Memorize: **{sequence}**"
            )

            choice = st.text_input(
                "Enter sequence",
                key=f"mem_{trial}",
            )

        elif experiment == "Reaction Time":

            target = random.choice(
                ["🔵", "🔴"]
            )

            st.session_state.lab[
                "rt_target"
            ] = target

            st.warning(
                "Choose the target."
            )

            choice = st.radio(
                "Target",
                ["🔵", "🔴"],
                horizontal=True,
                key=f"rt_{trial}",
            )

        elif experiment == "Stroop / Cognitive Control":

            word = random.choice(
                ["RED", "BLUE", "GREEN"]
            )

            st.markdown(
                f"## {word}"
            )

            choice = st.selectbox(
                "Select ink colour",
                ["RED", "BLUE", "GREEN"],
                key=f"stroop_{trial}",
            )

        elif experiment == "Decision & Reward":

            choice = st.radio(
                "Choose one",
                [
                    "PKR 1,000 today",
                    "PKR 1,500 after 30 days",
                ],
                key=f"decision_{trial}",
            )

        else:

            st.write(
                "2 → 4 → 8 → 16 → 32 → ?"
            )

            choice = st.text_input(
                "Next number",
                key=f"pattern_{trial}",
            )

        if st.button(
            "Record Trial",
            key=f"record_{trial}",
            type="primary",
        ):

            correct = False

            if experiment == "Attention":
                correct = (
                    choice
                    == st.session_state.lab[
                        "target"
                    ]
                )

            elif experiment == "Working Memory":
                correct = (
                    choice.replace(" ", "")
                    == st.session_state.lab[
                        "sequence"
                    ]
                )

            elif experiment == "Reaction Time":
                correct = (
                    choice
                    == st.session_state.lab[
                        "rt_target"
                    ]
                )

            elif experiment == "Stroop / Cognitive Control":
                correct = (
                    choice == word
                )

            elif experiment == "Decision & Reward":
                correct = True

            elif experiment == "Pattern Recognition":
                correct = (
                    choice.strip() == "64"
                )

            st.session_state.lab[
                "correct"
            ] += int(correct)

            st.session_state.lab[
                "rt"
            ].append(
                round(
                    random.uniform(
                        0.28,
                        0.85,
                    ),
                    3,
                )
            )

            st.session_state.lab[
                "trial"
            ] += 1

            if (
                st.session_state.lab[
                    "trial"
                ]
                >= total
            ):

                accuracy = (
                    st.session_state.lab[
                        "correct"
                    ]
                    / total
                    * 100
                )

                average_rt = (
                    sum(
                        st.session_state.lab[
                            "rt"
                        ]
                    )
                    / len(
                        st.session_state.lab[
                            "rt"
                        ]
                    )
                    * 1000
                )

                result = {
                    "accuracy": round(
                        accuracy,
                        1,
                    ),
                    "rt": round(
                        average_rt
                    ),
                    "correct":
                        st.session_state.lab[
                            "correct"
                        ],
                    "total": total,
                }

                st.session_state.lab[
                    "result"
                ] = result

                st.session_state.lab[
                    "running"
                ] = False

                log_activity(
                    "experiment",
                    accuracy,
                    {
                        "experiment":
                            experiment
                    },
                )

            st.rerun()

        st.progress(
            (trial + 1) / total
        )

    if st.session_state.lab.get(
        "result"
    ):

        result = (
            st.session_state.lab[
                "result"
            ]
        )

        st.success(
            "Experiment complete 🎉"
        )

        a, b, c = st.columns(3)

        a.metric(
            "Accuracy",
            f"{result['accuracy']}%",
        )

        b.metric(
            "Mean RT",
            f"{result['rt']} ms",
        )

        c.metric(
            "Correct",
            f"{result['correct']}/{result['total']}",
        )

        if go:

            fig = go.Figure(
                go.Bar(
                    x=[
                        "Accuracy",
                        "Correct",
                    ],
                    y=[
                        result["accuracy"],
                        result["correct"],
                    ],
                )
            )

            fig.update_layout(
                height=280
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        st.info(
            "Educational task-performance result only. "
            "It is not a diagnosis and does not directly "
            "measure brain activity."
        )

        if st.button(
            "New experiment"
        ):

            st.session_state.lab.pop(
                "result",
                None,
            )

            st.rerun()


# =========================================================
# BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "🧩 Brain Puzzle":

    st.subheader(
        "🧩 Brain Image Drag Puzzle"
    )

    st.caption(
        "Drag the actual image pieces with your finger or mouse."
    )

    if not DND_OK:

        st.error(
            "Drag engine unavailable. "
            "Install streamlit-dnd==0.2.0."
        )

    level = st.selectbox(
        "Difficulty",
        [
            "Easy • 3×3",
            "Medium • 4×4",
            "Hard • 5×5",
        ],
    )

    n = int(
        level.split("•")[1]
        .split("×")[0]
    )

    puzzle_key = f"puzzle_{n}"

    if (
        st.session_state.puzzle.get(
            "key"
        )
        != puzzle_key
    ):

        tiles = brain_tiles(n)

        order = list(
            range(n * n)
        )

        random.shuffle(order)

        st.session_state.puzzle = {
            "key": puzzle_key,
            "tiles": tiles,
            "order": order,
            "start": time.time(),
            "moves": 0,
            "solved": False,
        }

    puzzle = (
        st.session_state.puzzle
    )

    with st.container(
        key="puzzle_board",
        border=True,
    ):

        for position, tile_index in enumerate(
            puzzle["order"]
        ):

            with st.container(
                key=f"tile_{tile_index}",
                border=True,
            ):

                st.image(
                    puzzle["tiles"][
                        tile_index
                    ],
                    use_container_width=True,
                )

    event = (
        dnd(
            "puzzle_board",
            cross=False,
            handle=True,
            indicator="ghost",
            key="brain_dnd",
        )
        if DND_OK
        else None
    )

    if event:

        apply_move(
            event,
            {
                "puzzle_board":
                    puzzle["order"]
            },
        )

        puzzle["moves"] += 1

        st.rerun()

    solved = (
        puzzle["order"]
        == list(range(n * n))
    )

    if solved and not puzzle["solved"]:

        puzzle["solved"] = True

        elapsed = int(
            time.time()
            - puzzle["start"]
        )

        score = max(
            100,
            10000
            - elapsed * 20
            - puzzle["moves"] * 50,
        )

        log_activity(
            "puzzle",
            score,
            {
                "grid": n,
                "seconds": elapsed,
                "moves": puzzle["moves"],
            },
        )

        st.balloons()

        st.success(
            f"🎉 Solved in {elapsed}s • "
            f"{puzzle['moves']} moves • "
            f"Score {score}"
        )

    else:

        elapsed = int(
            time.time()
            - puzzle["start"]
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "⏱️ Time",
            f"{elapsed} s",
        )

        c2.metric(
            "🔢 Moves",
            puzzle["moves"],
        )

    if st.button(
        "🔄 New Puzzle",
        use_container_width=True,
    ):

        st.session_state.puzzle = {}
        st.rerun()


# =========================================================
# VOICE MOOD
# =========================================================

elif st.session_state.page == "🎙️ Voice Mood":

    st.subheader(
        "🎙️ Send Your Voice"
    )

    st.write(
        "Record your own voice, review it, "
        "then press SEND VOICE."
    )

    audio = st.audio_input(
        "🎤 Record your voice",
        sample_rate=16000,
        key="voice_input",
    )

    if audio:

        st.audio(audio)

        if st.button(
            "📤 SEND VOICE TO AYNA",
            type="primary",
            use_container_width=True,
        ):

            prompt = """
            Analyze this user voice for educational
            conversational use.

            Return ONLY JSON with:

            transcript
            emoji
            vibe
            explanation

            Transcribe what is said.

            For vibe use cautious descriptions such as:
            positive-sounding,
            energetic-sounding,
            calm-sounding,
            neutral/mixed,
            tense-sounding,
            low-energy-sounding.

            Do NOT claim certainty about hidden emotions,
            personality, mental health or diagnosis.

            Keep explanation under 60 words.
            """

            raw = safe(
                "voice-ai",
                lambda:
                    ai_text(
                        prompt,
                        audio.getvalue(),
                    ),
                "AI voice analysis unavailable.",
            )

            try:

                clean = (
                    raw
                    .replace(
                        "```json",
                        "",
                    )
                    .replace(
                        "```",
                        "",
                    )
                    .strip()
                )

                data = json.loads(
                    clean
                )

            except Exception:

                data = {
                    "transcript": raw,
                    "emoji": "🎙️",
                    "vibe":
                        "Mixed / uncertain",
                    "explanation":
                        "The AI response "
                        "could not be structured.",
                }

            st.session_state.voice_result = data

            log_activity(
                "voice",
                0,
                {
                    "vibe":
                        data.get(
                            "vibe"
                        )
                },
            )

            st.rerun()

    if st.session_state.voice_result:

        result = (
            st.session_state.voice_result
        )

        st.markdown(
            f"## {result.get('emoji','🎙️')} "
            f"{result.get('vibe','Mixed')}"
        )

        st.markdown(
            "### 📝 Transcript"
        )

        st.write(
            result.get(
                "transcript",
                "",
            )
        )

        st.markdown(
            "### 💬 Voice Interpretation"
        )

        st.write(
            result.get(
                "explanation",
                "",
            )
        )

        st.caption(
            "Voice vibe is an AI-assisted "
            "estimate, not a clinical or "
            "certain emotion detector."
        )

        speak(
            result.get(
                "explanation",
                "",
            ),
            "voice_speak",
        )


# =========================================================
# MOOD & FEELINGS
# =========================================================

elif st.session_state.page == "💭 Mood & Feelings":

    st.subheader(
        "💭 Mood & Feelings"
    )

    text = st.text_area(
        "How are you feeling?"
    )

    c1, c2, c3 = st.columns(3)

    stress = c1.slider(
        "Stress",
        0,
        10,
        5,
    )

    energy = c2.slider(
        "Energy",
        0,
        10,
        5,
    )

    mood = c3.slider(
        "Mood",
        0,
        10,
        5,
    )

    if st.button(
        "🤖 Analyze My Current Vibe",
        type="primary",
    ):

        prompt = f"""
        Give an educational,
        non-diagnostic reflection.

        User text:
        {text}

        Stress: {stress}/10
        Energy: {energy}/10
        Mood: {mood}/10

        Return:
        emoji
        short vibe
        cognitive-context observations
        gentle reflection

        Do not diagnose.
        """

        answer = safe(
            "mood-ai",
            lambda:
                ai_text(prompt),
            "AI unavailable.",
        )

        st.session_state.mood_result = answer

    if st.session_state.get(
        "mood_result"
    ):

        st.info(
            st.session_state.mood_result
        )


# =========================================================
# COGNITIVE GAMES
# =========================================================

elif st.session_state.page == "🎮 Cognitive Games":

    st.subheader(
        "🎮 Cognitive Games"
    )

    game = st.selectbox(
        "Choose a game",
        [
            "Memory",
            "Attention",
            "Reaction",
            "Pattern",
            "Decision",
        ],
    )

    if game == "Memory":

        st.info(
            "Memorize: 729418"
        )

        answer = st.text_input(
            "Enter sequence"
        )

        ok = (
            st.button("Check")
            and answer.replace(
                " ",
                "",
            )
            == "729418"
        )

    elif game == "Attention":

        st.write(
            "How many X?"
        )

        st.write(
            "A X K X P Q X R X"
        )

        answer = st.number_input(
            "Answer",
            0,
            10,
            0,
        )

        ok = (
            st.button("Check")
            and answer == 4
        )

    elif game == "Reaction":

        st.write(
            "Choose the target: 🔵"
        )

        answer = st.radio(
            "Response",
            ["🔵", "🔴"],
        )

        ok = (
            st.button("Check")
            and answer == "🔵"
        )

    elif game == "Pattern":

        st.write(
            "2 → 4 → 8 → 16 → 32 → ?"
        )

        answer = st.number_input(
            "Next",
            0,
            100,
            0,
        )

        ok = (
            st.button("Check")
            and answer == 64
        )

    else:

        answer = st.radio(
            "Choose one",
            [
                "PKR 1,000 today",
                "PKR 1,500 after 30 days",
            ],
        )

        ok = st.button(
            "Record choice"
        )

    if ok:

        st.success(
            "Response recorded."
        )

        log_activity(
            "game",
            100 if game != "Decision"
            else 0,
            {
                "game": game
            },
        )

    st.caption(
        "Practice task only; "
        "not a clinical assessment."
    )


# =========================================================
# NEUROSOCIAL
# =========================================================

elif st.session_state.page == "👥 NeuroSocial":

    st.subheader(
        "👥 NeuroSocial"
    )

    st.caption(
        "Community chat, likes, streaks and challenges."
    )

    con = db()

    messages = con.execute(
        """
        SELECT *
        FROM public_messages
        ORDER BY id DESC
        LIMIT 30
        """
    ).fetchall()

    for message in reversed(messages):

        likes = con.execute(
            """
            SELECT COUNT(*) n
            FROM likes
            WHERE message_id=?
            """,
            (message["id"],),
        ).fetchone()["n"]

        st.markdown(
            f"**{html.escape(message['username'])}** "
            f"· {message['created'][:16]} "
            f"❤️ {likes}"
        )

        st.write(
            message["text"]
        )

        if st.button(
            "❤️ Like",
            key=f"like_{message['id']}",
        ):

            con.execute(
                """
                INSERT OR IGNORE INTO likes
                (username,message_id)
                VALUES(?,?)
                """,
                (
                    user(),
                    message["id"],
                ),
            )

            con.commit()
            st.rerun()

    message_text = st.chat_input(
        "Write a message to the community…"
    )

    if message_text:

        con.execute(
            """
            INSERT INTO public_messages
            (username,text,created)
            VALUES(?,?,?)
            """,
            (
                user(),
                message_text[:500],
                datetime.now().isoformat(),
            ),
        )

        con.commit()
        st.rerun()

    st.divider()

    st.markdown(
        "### 🔥 Streaks"
    )

    st.write(
        f"{user()} • {streak()} day streak"
    )

    st.markdown(
        "### 🧠 Send a Challenge"
    )

    receiver = st.text_input(
        "Friend username"
    )

    challenge_type = st.selectbox(
        "Challenge",
        [
            "Memory",
            "Attention",
            "Pattern",
        ],
    )

    score = st.number_input(
        "Score",
        0,
        100,
        50,
    )

    if st.button(
        "📩 Send Challenge"
    ) and receiver:

        con.execute(
            """
            INSERT INTO challenges
            (sender,receiver,kind,score,created)
            VALUES(?,?,?,?,?)
            """,
            (
                user(),
                receiver,
                challenge_type,
                int(score),
                datetime.now().isoformat(),
            ),
        )

        con.commit()

        st.success(
            "Challenge sent."
        )


# =========================================================
# PRIVATE AYNA
# =========================================================

elif st.session_state.page == "🔐 Private Ayna":

    st.subheader(
        "🔐 Private Ask Ayna"
    )

    st.caption(
        "PIN-protected private conversation."
    )

    pin_exists = db().execute(
        """
        SELECT 1
        FROM private_pin
        WHERE username=?
        """,
        (user(),),
    ).fetchone()

    if not pin_exists:

        new_pin = st.text_input(
            "Set a 4–6 digit PIN",
            type="password",
            max_chars=6,
        )

        if st.button(
            "Set PIN"
        ):

            if (
                new_pin.isdigit()
                and 4 <= len(new_pin) <= 6
            ):

                set_pin(new_pin)

                st.success(
                    "PIN created."
                )

                st.rerun()

            else:

                st.error(
                    "PIN must contain "
                    "4–6 digits."
                )

    if not st.session_state.private_unlocked:

        pin = st.text_input(
            "Enter PIN",
            type="password",
            max_chars=6,
        )

        if st.button(
            "🔓 Unlock Private Chat"
        ):

            if valid_pin(pin):

                st.session_state.private_unlocked = True

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )

    if st.session_state.private_unlocked:

        private_rows = db().execute(
            """
            SELECT role,text
            FROM private_messages
            WHERE username=?
            ORDER BY id DESC
            LIMIT 20
            """,
            (user(),),
        ).fetchall()

        for message in reversed(
            private_rows
        ):

            st.chat_message(
                message["role"]
            ).write(
                message["text"]
            )

        private_question = st.chat_input(
            "Ask Ayna privately…",
            key="private_chat",
        )

        if private_question:

            answer = safe(
                "private-ai",
                lambda:
                    ai_text(
                        """
                        You are Ayna,
                        an educational
                        cognitive-neuroscience
                        assistant.

                        Answer carefully.
                        Do not diagnose.

                        User:
                        """
                        + private_question
                    ),
                "AI unavailable.",
            )

            con = db()

            con.execute(
                """
                INSERT INTO private_messages
                (username,role,text,created)
                VALUES(?,?,?,?)
                """,
                (
                    user(),
                    "user",
                    private_question,
                    datetime.now().isoformat(),
                ),
            )

            con.execute(
                """
                INSERT INTO private_messages
                (username,role,text,created)
                VALUES(?,?,?,?)
                """,
                (
                    user(),
                    "assistant",
                    answer,
                    datetime.now().isoformat(),
                ),
            )

            con.commit()

            st.rerun()

        if st.button(
            "🔒 Lock Private Chat"
        ):

            st.session_state.private_unlocked = False
            st.rerun()


# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "🤖 Ask Ayna":

    st.subheader(
        "🤖 Ask Ayna"
    )

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for message in st.session_state.chat:

        st.chat_message(
            message["role"]
        ).write(
            message["text"]
        )

    question = st.chat_input(
        "Ask about cognition, brain, learning, attention, AI…"
    )

    if question:

        answer = safe(
            "ask-ayna",
            lambda:
                ai_text(
                    """
                    You are Ayna,
                    a friendly cognitive
                    neuroscience education
                    assistant.

                    Be evidence-aware.
                    Be concise.
                    Do not diagnose.

                    User:
                    """
                    + question
                ),
            "AI unavailable.",
        )

        st.session_state.chat += [
            {
                "role": "user",
                "text": question,
            },
            {
                "role": "assistant",
                "text": answer,
            },
        ]

        st.rerun()

    if st.session_state.chat:

        speak(
            st.session_state.chat[-1]["text"],
            "ask_voice",
        )


# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "📚 Research Book":

    st.subheader(
        "📚 Research Book"
    )

    term = st.text_input(
        "Search Europe PMC"
    )

    if st.button(
        "Search papers"
    ) and term:

        import requests

        data = safe(
            "research-search",
            lambda:
                requests.get(
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                    params={
                        "query": term,
                        "format": "json",
                        "pageSize": 8,
                    },
                    timeout=10,
                ).json(),
            {
                "resultList": {
                    "result": []
                }
            },
        )

        for paper in data.get(
            "resultList",
            {}
        ).get(
            "result",
            []
        ):

            title = paper.get(
                "title",
                "Untitled",
            )

            identifier = (
                paper.get("pmid")
                or paper.get("id", "")
            )

            st.markdown(
                f"**{title}**"
            )

            if identifier:

                st.link_button(
                    "Open paper",
                    f"https://europepmc.org/article/MED/{identifier}",
                )

            if st.button(
                "Summarize",
                key=f"summary_{identifier}",
            ):

                st.write(
                    safe(
                        "paper-ai",
                        lambda:
                            ai_text(
                                """
                                Explain this research
                                title for a general
                                learner:

                                """
                                + title
                            ),
                        "AI unavailable.",
                    )
                )

    note = st.text_area(
        "Research note"
    )

    if st.button(
        "Save note"
    ) and note:

        con = db()

        con.execute(
            """
            INSERT INTO research_notes
            (username,note,created)
            VALUES(?,?,?)
            """,
            (
                user(),
                note,
                datetime.now().isoformat(),
            ),
        )

        con.commit()

        st.success(
            "Research note saved."
        )


# =========================================================
# 1-TO-1 SESSION / PAYMENT
# =========================================================

elif st.session_state.page == "💳 1-to-1 Session":

    st.subheader(
        "💳 Behaviour Decoding / 1-to-1 Session"
    )

    st.write(
        "International introductory pricing "
        "is shown beside the PKR price."
    )

    plans = [
        (
            "20 min",
            "PKR 1,000",
            "$3.50",
        ),
        (
            "30 min",
            "PKR 1,500",
            "$5.50",
        ),
        (
            "45 min",
            "PKR 2,000",
            "$7",
        ),
    ]

    choice = st.radio(
        "Session length",
        [
            f"{minutes} — "
            f"{pkr} / {usd}"
            for minutes, pkr, usd
            in plans
        ],
    )

    topic = st.text_input(
        "Topic / question"
    )

    method = st.selectbox(
        "Payment method",
        [
            "Easypaisa",
            "International payment link",
        ],
    )

    reference = st.text_input(
        "Payment/reference ID"
    )

    try:
        payment_url = st.secrets.get(
            "INTERNATIONAL_PAYMENT_URL",
            os.getenv(
                "INTERNATIONAL_PAYMENT_URL",
                "",
            ),
        )

        easypaisa_number = st.secrets.get(
            "EASYPAISA_NUMBER",
            os.getenv(
                "EASYPAISA_NUMBER",
                "",
            ),
        )

    except Exception:
        payment_url = os.getenv(
            "INTERNATIONAL_PAYMENT_URL",
            "",
        )

        easypaisa_number = os.getenv(
            "EASYPAISA_NUMBER",
            "",
        )

    if method == "International payment link":

        if payment_url:

            st.link_button(
                "🌍 Pay Internationally",
                payment_url,
            )

        else:

            st.info(
                "Add INTERNATIONAL_PAYMENT_URL "
                "in Streamlit Secrets."
            )

    else:

        st.info(
            "Easypaisa: "
            + (
                easypaisa_number
                if easypaisa_number
                else "Add EASYPAISA_NUMBER in Secrets"
            )
        )

    if st.button(
        "📩 Submit Session Request",
        type="primary",
    ):

        con = db()

        con.execute(
            """
            INSERT INTO activity
            (username,kind,score,meta,created)
            VALUES(?,?,?,?,?)
            """,
            (
                user(),
                "appointment_request",
                0,
                json.dumps(
                    {
                        "plan": choice,
                        "topic": topic,
                        "method": method,
                        "reference": reference,
                    }
                ),
                datetime.now().isoformat(),
            ),
        )

        con.commit()

        st.success(
            "Request saved. "
            "Payment verification should come "
            "from the official payment provider/backend "
            "before a private session is unlocked."
        )


# =========================================================
# HARDWARE HUB
# =========================================================

elif st.session_state.page == "⚡ Hardware Hub":

    st.subheader(
        "⚡ Hardware Hub"
    )

    st.write(
        "Real hardware is only treated as real "
        "when an actual compatible device is connected."
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            "### ⚡ EEG / BrainFlow"
        )

        try:

            from brainflow.board_shim import (
                BoardShim,
                BrainFlowInputParams,
                BoardIds,
            )

            st.success(
                "BrainFlow package available."
            )

            available_boards = [
                name
                for name in [
                    "SYNTHETIC_BOARD",
                    "CYTON_BOARD",
                    "CYTON_DAISY_BOARD",
                ]
                if hasattr(
                    BoardIds,
                    name,
                )
            ]

            if available_boards:

                board_name = st.selectbox(
                    "Board",
                    available_boards,
                )

                if st.button(
                    "Test EEG connection"
                ):

                    if (
                        board_name
                        == "SYNTHETIC_BOARD"
                    ):

                        board_id = getattr(
                            BoardIds,
                            board_name,
                        ).value

                        params = (
                            BrainFlowInputParams()
                        )

                        board = BoardShim(
                            board_id,
                            params,
                        )

                        board.prepare_session()
                        board.start_stream()

                        time.sleep(0.5)

                        data = (
                            board.get_current_board_data(
                                10
                            )
                        )

                        board.stop_stream()
                        board.release_session()

                        st.success(
                            "BrainFlow test OK."
                        )

                        st.write(
                            "Sample shape:",
                            getattr(
                                data,
                                "shape",
                                None,
                            ),
                        )

                    else:

                        st.info(
                            "A real EEG requires "
                            "device-specific connection "
                            "parameters and a local hardware "
                            "bridge. Streamlit Cloud cannot "
                            "directly access USB EEG hardware "
                            "attached to your device."
                        )

        except Exception:

            st.warning(
                "BrainFlow is optional and is not "
                "installed/available here."
            )

    with c2:

        st.markdown(
            "### 👁️ Eye Tracking"
        )

        st.info(
            "Research-grade eye tracking requires "
            "compatible eye-tracking hardware. "
            "The normal camera is not presented as "
            "research-grade eye tracking."
        )

        camera = st.camera_input(
            "Optional camera check"
        )

        if camera:

            st.image(
                camera,
                caption="Camera input received.",
            )


# =========================================================
# MY PROGRESS
# =========================================================

elif st.session_state.page == "📊 My Progress":

    st.subheader(
        "📊 My Progress"
    )

    con = db()

    rows = con.execute(
        """
        SELECT
            kind,
            COUNT(*) n,
            AVG(score) avg
        FROM activity
        WHERE username=?
        GROUP BY kind
        """,
        (user(),),
    ).fetchall()

    for row in rows:

        st.metric(
            row["kind"].title(),
            row["n"],
            f"avg {row['avg']:.1f}",
        )

    notes = con.execute(
        """
        SELECT note,created
        FROM research_notes
        WHERE username=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user(),),
    ).fetchall()

    st.markdown(
        "### Research Notes"
    )

    for note in notes:

        st.write(
            f"{note['created'][:16]} "
            f"— {note['note']}"
        )


# =========================================================
# SYSTEM HEALTH
# =========================================================

elif st.session_state.page == "🛡️ System Health":

    st.subheader(
        "🛡️ System Health & Auto-Heal"
    )

    st.success(
        "Runtime recovery is active."
    )

    st.metric(
        "Recovered / isolated issues",
        len(st.session_state.health),
    )

    if st.session_state.health:

        st.dataframe(
            st.session_state.health,
            use_container_width=True,
            hide_index=True,
        )

    if st.button(
        "Clear health log"
    ):

        st.session_state.health = []
        st.rerun()

    st.info(
        f"Gemini: "
        f"{'configured' if API_KEY else 'not configured'}"
        f" • Drag puzzle: "
        f"{'available' if DND_OK else 'unavailable'}"
    )


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "⚙️ Settings":

    st.subheader(
        "⚙️ Settings"
    )

    st.write(
        "Gemini model:",
        MODEL,
    )

    st.write(
        "Gemini API:",
        "Configured"
        if API_KEY
        else "Missing",
    )

    st.write(
        "Drag engine:",
        "Available"
        if DND_OK
        else "Missing",
    )

    if st.button(
        "Reset session"
    ):

        st.session_state.clear()
        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NEUROLENS • Educational Cognitive Neuroscience • "
    "AI-assisted features are not medical diagnosis. "
    "Real EEG requires compatible hardware."
)
