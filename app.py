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
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 2. OPTIONAL IMPORTS
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
# 3. SECRETS / CONFIG
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

EASYPAISA_NUMBER = get_secret("EASYPAISA_NUMBER")

INTERNATIONAL_PAYMENT_URL = get_secret(
    "INTERNATIONAL_PAYMENT_URL"
)

PAYMENT_ADMIN_KEY = get_secret(
    "PAYMENT_ADMIN_KEY"
)


# ============================================================
# 4. DATABASE
# ============================================================

supabase = None

if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception:
        supabase = None


# ============================================================
# 5. GEMINI
# ============================================================

gemini_client = None

if genai and GEMINI_API_KEY:
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
# 6. SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "NeuroWorld",
    "user": None,
    "email": "",
    "ai_requests": 0,
    "ai_limit": 20,
    "chat": [],
    "private_messages": [],
    "private_unlocked": False,
    "private_pin_hash": "",
    "lab_results": [],
    "exercise_results": [],
    "puzzle_results": [],
    "research_notes": [],
    "voice_result": None,
    "face_result": None,
    "last_error": "",
    "selected_brain_system": "Prefrontal Cortex",
    "lab_experiment": "Attention",
    "lab_started": False,
    "lab_result": None,
    "challenge_score": 0,
    "puzzle_size": 3,
    "puzzle_board": None,
    "puzzle_solution": None,
    "puzzle_moves": 0,
    "puzzle_started": False,
    "puzzle_finished": False,
    "puzzle_start_time": None,
    "puzzle_best": None,
    "language": "English",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 7. CSS
# ============================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: Inter, system-ui, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(76, 201, 240, .13), transparent 28%),
        radial-gradient(circle at 85% 20%, rgba(124, 58, 237, .12), transparent 30%),
        linear-gradient(135deg, #050816 0%, #081225 48%, #050816 100%);
}

.block-container {
    max-width: 1250px;
    padding-top: 1.5rem;
}

.hero {
    padding: 28px;
    border-radius: 28px;
    background: linear-gradient(
        135deg,
        rgba(13, 25, 52, .95),
        rgba(24, 34, 75, .88)
    );
    border: 1px solid rgba(255,255,255,.09);
    box-shadow: 0 20px 70px rgba(0,0,0,.28);
    margin-bottom: 24px;
}

.hero h1 {
    font-size: clamp(38px, 7vw, 72px);
    margin: 0;
    font-weight: 900;
    letter-spacing: -3px;
}

.hero p {
    color: #b8c5df;
    font-size: 18px;
}

.neuro-card {
    background: rgba(15, 25, 50, .82);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 16px;
}

.brain-world {
    text-align: center;
    padding: 30px;
    border-radius: 30px;
    background:
        radial-gradient(circle at center,
        rgba(78, 214, 255, .14),
        transparent 42%),
        rgba(8,16,35,.85);
    border: 1px solid rgba(109, 226, 255, .14);
}

.brain-character {
    font-size: 120px;
    line-height: 1;
    animation: floatBrain 3s ease-in-out infinite;
}

@keyframes floatBrain {
    0%,100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.robot {
    font-size: 70px;
}

.small-muted {
    color: #91a0bc;
    font-size: 13px;
}

.success-box {
    padding: 18px;
    border-radius: 18px;
    background: rgba(40, 200, 130, .12);
    border: 1px solid rgba(40, 200, 130, .3);
}

.warning-box {
    padding: 18px;
    border-radius: 18px;
    background: rgba(255, 190, 50, .10);
    border: 1px solid rgba(255, 190, 50, .25);
}

.price-card {
    padding: 20px;
    border-radius: 20px;
    background: rgba(255,255,255,.045);
    border: 1px solid rgba(255,255,255,.08);
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 8. GENERAL HELPERS
# ============================================================

def clean_text(value, max_length=3000):
    if value is None:
        return ""

    value = str(value)
    value = re.sub(r"<script.*?>.*?</script>", "", value,
                   flags=re.I | re.S)
    value = re.sub(r"<.*?>", "", value)
    return value.strip()[:max_length]


def safe_json(text):
    if not text:
        return {}

    text = re.sub(
        r"```(?:json)?",
        "",
        str(text),
        flags=re.I,
    )
    text = text.replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        match = re.search(
            r"\{.*\}",
            text,
            flags=re.S,
        )

        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

    return {}


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


def current_user_id():
    user = st.session_state.get("user")

    if isinstance(user, dict):
        return user.get("id")

    return None


def record_ai_request():
    st.session_state.ai_requests += 1

    if st.session_state.ai_requests > st.session_state.ai_limit:
        st.session_state.ai_requests = st.session_state.ai_limit


def ai_limit_reached():
    return (
        st.session_state.ai_requests
        >= st.session_state.ai_limit
    )


def asset_path(name):
    candidates = [
        name,
        os.path.join("assets", name),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def show_image(name, width=500):
    path = asset_path(name)

    if path and Image:
        try:
            st.image(path, width=width)
            return True
        except Exception:
            pass

    return False


def speak_text(text):
    text = clean_text(text, 2500)

    components.html(
        f"""
        <script>
        const text = {json.dumps(text)};
        if ("speechSynthesis" in window) {{
            const u = new SpeechSynthesisUtterance(text);
            u.rate = 0.95;
            u.pitch = 1.05;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=10,
    )


def ai_generate(prompt, image_bytes=None, mime_type=None):
    if not ai_available():
        return ""

    if ai_limit_reached():
        return "AI request limit reached for this session."

    try:
        contents = [prompt]

        if image_bytes and types:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type or "image/jpeg",
                )
            )

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )

        record_ai_request()

        return getattr(response, "text", "") or ""

    except Exception as exc:
        st.session_state.last_error = str(exc)
        return ""


# ============================================================
# 9. AUTH
# ============================================================

def page_auth():
    st.markdown(
        """
        <div class="hero">
            <h1>🧠 NEUROLENS</h1>
            <p>Explore cognition, behavior & the brain</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(
        ["Create Account", "Sign In"]
    )

    with tab1:
        email = st.text_input(
            "Email",
            key="signup_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
        )

        if st.button(
            "Create NEUROLENS Account",
            use_container_width=True,
            type="primary",
        ):
            if not email or not password:
                st.warning(
                    "Please enter email and password."
                )
            elif not supabase:
                st.warning(
                    "Supabase is not connected. "
                    "You can still explore NEUROLENS locally."
                )
            else:
                try:
                    result = supabase.auth.sign_up(
                        {
                            "email": email,
                            "password": password,
                        }
                    )

                    if result.user:
                        st.success(
                            "Account created. "
                            "Check your email if confirmation is enabled."
                        )
                    else:
                        st.error(
                            "Account creation could not be completed."
                        )

                except Exception as exc:
                    st.error(
                        f"Sign-up failed: {clean_text(exc)}"
                    )

    with tab2:
        email = st.text_input(
            "Email",
            key="login_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Sign In",
            use_container_width=True,
            type="primary",
        ):
            if not supabase:
                st.warning(
                    "Supabase is not connected."
                )
            else:
                try:
                    result = supabase.auth.sign_in_with_password(
                        {
                            "email": email,
                            "password": password,
                        }
                    )

                    if result.user:
                        st.session_state.user = {
                            "id": result.user.id,
                            "email": result.user.email,
                        }
                        st.session_state.email = (
                            result.user.email or ""
                        )
                        st.session_state.page = "NeuroWorld"
                        st.rerun()

                except Exception:
                    st.error(
                        "Sign-in failed. Check your email and password."
                    )


def logout():
    try:
        if supabase:
            supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.user = None
    st.session_state.email = ""
    st.session_state.private_unlocked = False
    st.session_state.page = "NeuroWorld"
    st.rerun()


# ============================================================
# 10. NEUROWORLD
# ============================================================

def page_neuroworld():
    st.markdown(
        """
        <div class="hero">
            <h1>NEUROLENS</h1>
            <p>Explore cognition, behavior & the brain</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="brain-world">
            <div class="brain-character">🧠</div>
            <h2>Hi, I am NeuroLens.</h2>
            <p>
            Come with me — I'll show you what you can explore.
            </p>
            <div class="robot">🤖</div>
            <p class="small-muted">
            Your AI research companion is ready.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    cols = st.columns(3)

    options = [
        ("🧪", "Cognitive Lab", "Run interactive experiments."),
        ("🧠", "Brain Journey", "Explore brain systems."),
        ("🎯", "Brain Challenges", "Train cognitive skills."),
        ("🧩", "Brain Puzzle", "Reconstruct a brain image."),
        ("🤖", "Ask Ayna", "Talk with the AI research assistant."),
        ("🔬", "Research World", "Search neuroscience literature."),
    ]

    for i, (icon, title, description) in enumerate(options):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="neuro-card">
                    <h2>{icon} {title}</h2>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Enter {title}",
                key=f"world_{i}",
                use_container_width=True,
            ):
                st.session_state.page = title
                st.rerun()


# ============================================================
# 11. COGNITIVE LAB
# ============================================================

BRAIN_SYSTEMS = {
    "Prefrontal Cortex": (
        "Planning, working memory, cognitive control "
        "and flexible decision-making."
    ),
    "Hippocampus": (
        "Memory formation, spatial processing "
        "and contextual learning."
    ),
    "Striatum": (
        "Action selection, reward learning "
        "and habit-related processes."
    ),
    "Anterior Cingulate Cortex": (
        "Conflict monitoring, effort, attention "
        "and adaptive control."
    ),
    "Attention Networks": (
        "Systems supporting selection, alerting "
        "and goal-directed attention."
    ),
}


def lab_attention():
    st.markdown("### 🎯 Attention Experiment")

    target = random.choice(
        ["X", "K", "M", "T"]
    )

    st.markdown(
        f"""
        <div class="neuro-card">
            <h2>Find: {target}</h2>
            <p>Look at the grid and click the target.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    grid = [
        random.choice(["X", "K", "M", "T"])
        for _ in range(12)
    ]

    position = random.randint(0, 11)
    grid[position] = target

    cols = st.columns(4)

    for i, item in enumerate(grid):
        with cols[i % 4]:
            if st.button(
                item,
                key=f"attention_{i}",
                use_container_width=True,
            ):
                if i == position:
                    st.success(
                        "Correct target detection."
                    )
                    return {
                        "experiment": "Attention",
                        "score": 1,
                        "observation": (
                            "Target detection was successful."
                        ),
                    }

                st.error("Not the target.")

    return None


def lab_memory():
    st.markdown("### 🧠 Working Memory")

    if "memory_code" not in st.session_state:
        st.session_state.memory_code = (
            str(random.randint(100000, 999999))
        )

    if not st.session_state.get(
        "memory_revealed",
        False,
    ):
        st.markdown(
            f"""
            <div class="neuro-card">
                <h2>{st.session_state.memory_code}</h2>
                <p>Memorize this code.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Hide Code"):
            st.session_state.memory_revealed = True
            st.rerun()

        return None

    answer = st.text_input(
        "Enter the code",
        key="memory_answer",
    )

    if st.button(
        "Check Memory",
        type="primary",
    ):
        correct = (
            answer.strip()
            == st.session_state.memory_code
        )

        if correct:
            st.success("Correct memory recall.")

            result = {
                "experiment": "Memory",
                "score": 1,
                "observation": (
                    "The target sequence was recalled correctly."
                ),
            }

            st.session_state.lab_results.append(result)
            db_insert(
                "lab_results",
                {
                    "user_id": current_user_id(),
                    "experiment": "Memory",
                    "score": 1,
                    "result": result,
                },
            )

            return result

        st.error("Incorrect recall.")

    return None


def lab_decision():
    st.markdown("### 💰 Decision & Reward")

    st.write(
        "Choose between a smaller immediate reward "
        "and a larger delayed reward."
    )

    choice = st.radio(
        "Your choice:",
        [
            "PKR 1,000 today",
            "PKR 1,500 after 30 days",
        ],
    )

    if st.button(
        "Submit Decision",
        type="primary",
    ):
        result = {
            "experiment": "Decision & Reward",
            "choice": choice,
            "observation": (
                "This task illustrates delay discounting "
                "and reward preference."
            ),
        }

        st.session_state.lab_results.append(result)

        db_insert(
            "lab_results",
            {
                "user_id": current_user_id(),
                "experiment": "Decision & Reward",
                "score": 1,
                "result": result,
            },
        )

        st.success(
            f"Decision recorded: {choice}"
        )

        return result

    return None


def lab_stroop():
    st.markdown("### 🎨 Cognitive Control / Stroop")

    words = [
        ("RED", "blue"),
        ("BLUE", "red"),
        ("GREEN", "purple"),
        ("YELLOW", "green"),
    ]

    word, ink = random.choice(words)

    st.markdown(
        f"""
        <div class="neuro-card">
            <h2>{word}</h2>
            <p>Identify the ink colour, not the word.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.selectbox(
        "Ink colour:",
        ["red", "blue", "green", "purple", "yellow"],
    )

    if st.button(
        "Submit",
        type="primary",
    ):
        if answer == ink:
            st.success("Correct cognitive-control response.")

            result = {
                "experiment": "Stroop",
                "score": 1,
                "observation": (
                    "Correct response required suppression "
                    "of the competing word meaning."
                ),
            }

            st.session_state.lab_results.append(result)

            return result

        st.error("Incorrect response.")

    return None


def page_lab():
    st.markdown(
        """
        <div class="hero">
            <h1>🧪 Cognitive Lab</h1>
            <p>
            Interactive neuroscience experiments.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    experiment = st.selectbox(
        "Choose experiment",
        [
            "Attention",
            "Memory",
            "Decision & Reward",
            "Stroop-Cognitive Control",
        ],
    )

    if experiment != st.session_state.lab_experiment:
        st.session_state.lab_experiment = experiment
        st.session_state.lab_result = None

    if experiment == "Attention":
        result = lab_attention()

    elif experiment == "Memory":
        result = lab_memory()

    elif experiment == "Decision & Reward":
        result = lab_decision()

    else:
        result = lab_stroop()

    if result:
        st.session_state.lab_result = result

    if st.session_state.lab_result:
        result = st.session_state.lab_result

        st.markdown(
            """
            <div class="success-box">
                <h3>Experiment Result</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(
            result.get(
                "observation",
                "Experiment completed.",
            )
        )

        st.caption(
            "These tasks are educational simulations. "
            "They do not measure actual brain activity."
        )

    st.divider()

    st.subheader("🧠 Brain Systems")

    system = st.selectbox(
        "Explore system",
        list(BRAIN_SYSTEMS.keys()),
    )

    st.info(BRAIN_SYSTEMS[system])


# ============================================================
# 12. BRAIN JOURNEY
# ============================================================

BRAIN_JOURNEY = [
    (
        "Neuron",
        "neuron.png",
        "The neuron is a basic functional cell of the nervous system.",
    ),
    (
        "Synapse",
        "synapse.png",
        "Synapses allow neurons to communicate with other cells.",
    ),
    (
        "Neural Signaling",
        "neural_signaling.gif",
        "Neural communication involves electrical and chemical processes.",
    ),
    (
        "Prefrontal Cortex",
        "prefrontal_cortex.png",
        "Important for planning, control and complex decision-making.",
    ),
    (
        "Hippocampus",
        "hippocampus.png",
        "Strongly involved in memory and contextual learning.",
    ),
    (
        "Striatum",
        "striatum.png",
        "Important for action selection and reward-related learning.",
    ),
    (
        "Anterior Cingulate Cortex",
        "acc.png",
        "Supports conflict monitoring and adaptive control.",
    ),
    (
        "Attention Networks",
        "attention_network.png",
        "Distributed systems support attention and goal-directed behavior.",
    ),
]


def page_brain_journey():
    st.markdown(
        """
        <div class="hero">
            <h1>🧠 Brain Journey</h1>
            <p>
            Explore the brain from neurons to large-scale systems.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    names = [x[0] for x in BRAIN_JOURNEY]

    current = st.selectbox(
        "Choose a concept",
        names,
    )

    index = names.index(current)

    title, image, description = BRAIN_JOURNEY[index]

    st.markdown(
        f"""
        <div class="neuro-card">
            <h2>{title}</h2>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_image(image, width=650)

    st.caption(
        "If a concept image is not yet placed in the assets folder, "
        "NEUROLENS will show the text explanation instead."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "← Previous",
            use_container_width=True,
        ):
            index = max(0, index - 1)
            st.session_state.selected_brain_system = names[index]
            st.rerun()

    with col2:
        if st.button(
            "Restart",
            use_container_width=True,
        ):
            st.session_state.selected_brain_system = names[0]
            st.rerun()

    with col3:
        if st.button(
            "Next →",
            use_container_width=True,
        ):
            index = min(
                len(names) - 1,
                index + 1,
            )
            st.session_state.selected_brain_system = names[index]
            st.rerun()


# ============================================================
# 13. BRAIN CHALLENGES
# ============================================================

def save_exercise(name, score):
    result = {
        "exercise": name,
        "score": score,
        "timestamp": datetime.utcnow().isoformat(),
    }

    st.session_state.exercise_results.append(result)

    db_insert(
        "exercise_results",
        {
            "user_id": current_user_id(),
            "exercise": name,
            "score": score,
            "result": result,
        },
    )


def page_challenges():
    st.markdown(
        """
        <div class="hero">
            <h1>🎯 Brain Challenges</h1>
            <p>
            Educational cognitive tasks for attention,
            memory, pattern recognition and decision-making.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    challenge = st.selectbox(
        "Choose challenge",
        [
            "Working Memory",
            "Pattern Recognition",
            "Decision Challenge",
            "Attention",
            "Quick Reaction",
        ],
    )

    if challenge == "Working Memory":

        if "wm_numbers" not in st.session_state:
            st.session_state.wm_numbers = "".join(
                str(random.randint(0, 9))
                for _ in range(6)
            )
            st.session_state.wm_hidden = False

        if not st.session_state.wm_hidden:
            st.markdown(
                f"""
                <div class="neuro-card">
                    <h2>{st.session_state.wm_numbers}</h2>
                    <p>Memorize the sequence.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Hide"):
                st.session_state.wm_hidden = True
                st.rerun()

        else:
            answer = st.text_input(
                "Enter sequence"
            )

            if st.button(
                "Check",
                type="primary",
            ):
                if answer.strip() == st.session_state.wm_numbers:
                    st.success("Correct!")
                    save_exercise(
                        "Working Memory",
                        1,
                    )
                else:
                    st.error(
                        f"Incorrect. The sequence was "
                        f"{st.session_state.wm_numbers}."
                    )

    elif challenge == "Pattern Recognition":

        st.markdown(
            """
            ### Complete the pattern

            **2 → 4 → 8 → 16 → 32 → ?**
            """
        )

        answer = st.text_input(
            "Your answer"
        )

        if st.button(
            "Check Pattern",
            type="primary",
        ):
            if answer.strip() == "64":
                st.success("Correct pattern.")
                save_exercise(
                    "Pattern Recognition",
                    1,
                )
            else:
                st.error("Try again.")

    elif challenge == "Decision Challenge":

        choice = st.radio(
            "Which would you choose?",
            [
                "PKR 1,000 now",
                "PKR 1,500 after 30 days",
            ],
        )

        if st.button(
            "Record Decision",
            type="primary",
        ):
            st.success(
                f"Decision recorded: {choice}"
            )
            save_exercise(
                "Decision Challenge",
                1,
            )

    elif challenge == "Attention":

        target = "X"

        st.write(
            "Find X among the symbols."
        )

        symbols = [
            random.choice(
                ["O", "K", "M", "T", "X"]
            )
            for _ in range(16)
        ]

        target_position = random.randint(
            0,
            15,
        )

        symbols[target_position] = "X"

        cols = st.columns(4)

        for i, symbol in enumerate(symbols):
            with cols[i % 4]:
                if st.button(
                    symbol,
                    key=f"challenge_attention_{i}",
                    use_container_width=True,
                ):
                    if i == target_position:
                        st.success("Correct!")
                        save_exercise(
                            "Attention",
                            1,
                        )
                    else:
                        st.error("Not X.")

    else:

        if "reaction_started" not in st.session_state:
            st.session_state.reaction_started = False
            st.session_state.reaction_ready = False
            st.session_state.reaction_time = None

        if not st.session_state.reaction_started:
            if st.button(
                "Start Reaction Test",
                type="primary",
            ):
                st.session_state.reaction_started = True
                st.session_state.reaction_ready = False
                st.session_state.reaction_time = time.time()
                st.rerun()

        else:

            elapsed = time.time() - (
                st.session_state.reaction_time or time.time()
            )

            if not st.session_state.reaction_ready:
                st.info(
                    "Wait for the GO signal."
                )

                if elapsed > 1.5:
                    st.session_state.reaction_ready = True
                    st.session_state.reaction_time = time.time()
                    st.rerun()

            else:
                st.success("GO!")

                if st.button(
                    "CLICK NOW",
                    type="primary",
                    use_container_width=True,
                ):
                    reaction = (
                        time.time()
                        - st.session_state.reaction_time
                    )

                    st.metric(
                        "Reaction Time",
                        f"{reaction:.3f} sec",
                    )

                    save_exercise(
                        "Quick Reaction",
                        round(
                            max(
                                0,
                                1 - reaction,
                            ),
                            3,
                        ),
                    )

                    st.session_state.reaction_started = False


# ============================================================
# 14. BRAIN PUZZLE
# ============================================================

def create_puzzle(size):
    total = size * size

    solution = list(range(total))
    board = solution.copy()

    # Shuffle while keeping a usable puzzle.
    for _ in range(size * size * 20):
        a = random.randrange(total)
        b = random.randrange(total)

        board[a], board[b] = (
            board[b],
            board[a],
        )

    return board, solution


def puzzle_complete(board, solution):
    return board == solution


def page_puzzle():
    st.markdown(
        """
        <div class="hero">
            <h1>🧩 Brain Puzzle</h1>
            <p>
            Reconstruct the brain image and train visual-spatial attention.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    size = st.selectbox(
        "Puzzle size",
        [3, 4, 5],
        index=0,
    )

    if (
        st.session_state.puzzle_board is None
        or st.session_state.puzzle_size != size
    ):
        st.session_state.puzzle_size = size
        board, solution = create_puzzle(size)

        st.session_state.puzzle_board = board
        st.session_state.puzzle_solution = solution
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_finished = False
        st.session_state.puzzle_started = True
        st.session_state.puzzle_start_time = time.time()

    if st.button(
        "🔄 New Puzzle",
        use_container_width=True,
    ):
        board, solution = create_puzzle(size)

        st.session_state.puzzle_board = board
        st.session_state.puzzle_solution = solution
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_finished = False
        st.session_state.puzzle_started = True
        st.session_state.puzzle_start_time = time.time()
        st.rerun()

    board = st.session_state.puzzle_board
    solution = st.session_state.puzzle_solution

    st.write(
        f"**Moves:** {st.session_state.puzzle_moves}"
    )

    elapsed = 0

    if st.session_state.puzzle_start_time:
        elapsed = (
            time.time()
            - st.session_state.puzzle_start_time
        )

    st.write(
        f"**Time:** {elapsed:.1f} sec"
    )

    st.caption(
        "Tap two tiles to swap them. "
        "This provides a mobile-friendly fallback when "
        "true pointer drag/drop is unavailable."
    )

    cols = st.columns(size)

    selected = st.session_state.get(
        "puzzle_selected",
        None,
    )

    for i, value in enumerate(board):
        with cols[i % size]:

            label = "🧠" if value == 0 else str(value)

            if st.button(
                label,
                key=f"puzzle_tile_{i}",
                use_container_width=True,
            ):

                if selected is None:
                    st.session_state.puzzle_selected = i

                else:
                    if selected != i:
                        board[selected], board[i] = (
                            board[i],
                            board[selected],
                        )

                        st.session_state.puzzle_moves += 1

                    st.session_state.puzzle_selected = None

                    if puzzle_complete(
                        board,
                        solution,
                    ):
                        st.session_state.puzzle_finished = True

                        result = {
                            "size": size,
                            "moves": st.session_state.puzzle_moves,
                            "time": round(
                                elapsed,
                                2,
                            ),
                        }

                        st.session_state.puzzle_results.append(
                            result
                        )

                        db_insert(
                            "brain_puzzle_results",
                            {
                                "user_id": current_user_id(),
                                "score": max(
                                    1,
                                    1000
                                    - st.session_state.puzzle_moves * 5,
                                ),
                                "result": result,
                            },
                        )

                    st.rerun()

    if st.session_state.puzzle_finished:
        st.balloons()

        st.markdown(
            """
            <div class="success-box">
                <h2>🎉 Puzzle Completed!</h2>
                <p>
                Your brain puzzle was successfully reconstructed.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    show_image(
        "brain.png",
        width=500,
    )


# ============================================================
# 15. ASK AYNA
# ============================================================

def ask_ayna_prompt(question):
    return f"""
You are Ayna, the AI research assistant inside NEUROLENS.

The user asks:
{question}

Answer clearly and naturally.

Focus on:
- cognitive neuroscience
- brain and behavior
- learning
- attention
- memory
- decision-making
- consciousness
- AI and cognition

Do not diagnose the user.
Do not claim to read hidden emotions.
Do not claim that games measure brain activity.
Do not present educational tasks as medical tests.

If uncertainty exists, say so.
"""


def page_ask_ayna():
    st.markdown(
        """
        <div class="hero">
            <h1>🤖 Ask Ayna</h1>
            <p>
            Your AI cognitive-neuroscience research companion.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not ai_available():
        st.warning(
            "Gemini is not connected. "
            "Add GEMINI_API_KEY in Streamlit Secrets."
        )

    for message in st.session_state.chat:
        with st.chat_message(
            message["role"]
        ):
            st.write(message["content"])

    question = st.chat_input(
        "Ask Ayna about the brain, cognition or behavior..."
    )

    if question:

        question = clean_text(
            question,
            2000,
        )

        st.session_state.chat.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.write(question)

        answer = ai_generate(
            ask_ayna_prompt(question)
        )

        if not answer:
            answer = (
                "I could not connect to the AI right now. "
                "Please check your Gemini configuration."
            )

        st.session_state.chat.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):
            st.write(answer)

            if st.button(
                "🔊 Speak Ayna",
                key=f"speak_{len(st.session_state.chat)}",
            ):
                speak_text(answer)


# ============================================================
# 16. VOICE + FACE AI MOOD
# ============================================================

def page_mood():
    st.markdown(
        """
        <div class="hero">
            <h1>🎙️ AI Mood & Behaviour</h1>
            <p>
            Explore AI-assisted voice and facial-expression cues.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="warning-box">
        <b>Important:</b> This is an experimental AI interpretation.
        It cannot reliably determine someone's true emotion,
        personality, mental health or hidden state.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(
        ["🎙️ Voice", "📷 Face"]
    )

    with tab1:

        voice = st.audio_input(
            "Record a short voice sample"
        )

        if voice:

            if st.button(
                "📤 Analyze Voice",
                type="primary",
            ):

                prompt = """
Return ONLY JSON with:

{
 "transcript": "",
 "emoji": "",
 "vibe_label": "",
 "explanation": ""
}

Use only observable communication/acoustic cues.
Do not claim certainty about hidden emotion.
Do not diagnose.
"""

                if types and ai_available():

                    try:
                        response = gemini_client.models.generate_content(
                            model=GEMINI_MODEL,
                            contents=[
                                prompt,
                                types.Part.from_bytes(
                                    data=voice.getvalue(),
                                    mime_type=(
                                        voice.type
                                        or "audio/wav"
                                    ),
                                ),
                            ],
                        )

                        record_ai_request()

                        result = safe_json(
                            getattr(
                                response,
                                "text",
                                "",
                            )
                        )

                        if not result:
                            result = {
                                "transcript": "",
                                "emoji": "🧩",
                                "vibe_label": "Uncertain",
                                "explanation": (
                                    "The response could not "
                                    "be structured reliably."
                                ),
                            }

                        st.session_state.voice_result = result

                    except Exception:
                        st.error(
                            "Voice analysis failed safely."
                        )

                else:
                    st.warning(
                        "Gemini is not connected."
                    )

        if st.session_state.voice_result:

            result = st.session_state.voice_result

            st.markdown(
                f"## {result.get('emoji', '🧩')} "
                f"{result.get('vibe_label', 'Uncertain')}"
            )

            st.subheader("Transcript")
            st.write(
                result.get(
                    "transcript",
                    "",
                )
            )

            st.subheader(
                "AI voice-vibe interpretation"
            )

            st.write(
                result.get(
                    "explanation",
                    "",
                )
            )

    with tab2:

        picture = st.camera_input(
            "Take a photo"
        )

        if picture:

            if st.button(
                "📷 Analyze Facial Expression",
                type="primary",
            ):

                prompt = """
Return ONLY JSON:

{
 "emoji": "",
 "expression": "",
 "explanation": ""
}

Describe only visible facial-expression cues.
Do not identify the person.
Do not infer mental illness.
Do not claim certainty about internal emotions.
"""

                result_text = ai_generate(
                    prompt,
                    image_bytes=picture.getvalue(),
                    mime_type=(
                        picture.type
                        or "image/jpeg"
                    ),
                )

                result = safe_json(
                    result_text
                )

                if not result:
                    result = {
                        "emoji": "🧩",
                        "expression": "Uncertain",
                        "explanation": (
                            "The expression could not "
                            "be interpreted reliably."
                        ),
                    }

                st.session_state.face_result = result

        if st.session_state.face_result:

            result = st.session_state.face_result

            st.markdown(
                f"## {result.get('emoji', '🧩')} "
                f"{result.get('expression', 'Uncertain')}"
            )

            st.write(
                result.get(
                    "explanation",
                    "",
                )
            )


# ============================================================
# 17. RESEARCH WORLD
# ============================================================

def page_research():
    st.markdown(
        """
        <div class="hero">
            <h1>🔬 Research World</h1>
            <p>
            Search biomedical and neuroscience literature.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search Europe PMC",
        placeholder=(
            "e.g. attention reward decision making"
        ),
    )

    if st.button(
        "Search Papers",
        type="primary",
    ):

        if not query:
            st.warning(
                "Enter a research topic."
            )
        elif not requests:
            st.error(
                "Requests package is unavailable."
            )
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

                results = data.get(
                    "resultList",
                    {},
                ).get(
                    "result",
                    [],
                )

                if not results:
                    st.info(
                        "No papers found."
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

                    authors = paper.get(
                        "authorString",
                        "",
                    )

                    pmid = paper.get(
                        "pmid",
                        "",
                    )

                    st.markdown(
                        f"""
                        ### {title}

                        **Year:** {year}

                        **Authors:** {authors}
                        """
                    )

                    if pmid:
                        st.markdown(
                            f"[Open on Europe PMC]"
                            f"(https://europepmc.org/article/MED/{pmid})"
                        )

                    st.divider()

            except Exception:
                st.error(
                    "Research search failed."
                )

    st.subheader("📝 Research Notes")

    note = st.text_area(
        "Write a research note"
    )

    if st.button(
        "Save Research Note"
    ):

        note = clean_text(
            note,
            5000,
        )

        if note:

            st.session_state.research_notes.append(
                {
                    "note": note,
                    "time": datetime.utcnow().isoformat(),
                }
            )

            db_insert(
                "research_notes",
                {
                    "user_id": current_user_id(),
                    "note": note,
                },
            )

            st.success(
                "Research note saved."
            )

    for item in reversed(
        st.session_state.research_notes
    ):
        st.markdown(
            f"""
            <div class="neuro-card">
                {item.get("note", "")}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 18. PRIVATE ASK AYNA
# ============================================================

def hash_pin(pin, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt,
        120000,
    )

    return (
        salt.hex(),
        hashed.hex(),
    )


def verify_pin(pin, stored):
    try:
        salt_hex, hash_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)

        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode(),
            salt,
            120000,
        ).hex()

        return secrets.compare_digest(
            calculated,
            hash_hex,
        )

    except Exception:
        return False


def page_private():
    st.markdown(
        """
        <div class="hero">
            <h1>🔐 Private Ayna</h1>
            <p>
            A private session area protected by a PIN.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.private_unlocked:

        pin = st.text_input(
            "Create / enter PIN",
            type="password",
            max_chars=6,
        )

        if st.button(
            "Unlock",
            type="primary",
        ):

            if not pin.isdigit() or not (
                4 <= len(pin) <= 6
            ):
                st.error(
                    "PIN must contain 4–6 digits."
                )

            elif st.session_state.private_pin_hash:

                if verify_pin(
                    pin,
                    st.session_state.private_pin_hash,
                ):
                    st.session_state.private_unlocked = True
                    st.rerun()
                else:
                    st.error(
                        "Incorrect PIN."
                    )

            else:

                salt, hashed = hash_pin(pin)

                st.session_state.private_pin_hash = (
                    salt + ":" + hashed
                )

                st.session_state.private_unlocked = True
                st.success(
                    "Private session unlocked."
                )
                st.rerun()

        st.caption(
            "The PIN is protected with PBKDF2-HMAC-SHA256 "
            "for this application session."
        )

        return

    st.success(
        "Private session unlocked."
    )

    message = st.text_area(
        "Private message for Ayna"
    )

    if st.button(
        "Send Privately",
        type="primary",
    ):

        if message:

            message = clean_text(
                message,
                3000,
            )

            answer = ai_generate(
                f"""
You are Ayna in a private conversation.

Respond supportively and thoughtfully.

Do not diagnose.
Do not claim certainty about hidden mental states.

User message:
{message}
"""
            )

            if not answer:
                answer = (
                    "Private AI response is currently unavailable."
                )

            st.session_state.private_messages.append(
                {
                    "user": message,
                    "ayna": answer,
                }
            )

            db_insert(
                "private_ayna_messages",
                {
                    "user_id": current_user_id(),
                    "message": message,
                    "response": answer,
                },
            )

    for item in st.session_state.private_messages:
        st.markdown(
            f"""
            <div class="neuro-card">
                <b>You</b><br>
                {item["user"]}
                <br><br>
                <b>Ayna</b><br>
                {item["ayna"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button(
        "🔒 Lock Private Area"
    ):
        st.session_state.private_unlocked = False
        st.rerun()


# ============================================================
# 19. BEHAVIOUR DECODING / CONSULTATION
# ============================================================

def page_behaviour():
    st.markdown(
        """
        <div class="hero">
            <h1>🧩 Behaviour Decoding</h1>
            <p>
            Book a structured educational discussion.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prices = [
        ("20 minutes", "PKR 1,000", "$8"),
        ("30 minutes", "PKR 1,500", "$10"),
        ("45 minutes", "PKR 2,000", "$12"),
        ("Advice / Consultation", "PKR 1,500", "$10"),
    ]

    cols = st.columns(4)

    for i, (duration, local, international) in enumerate(
        prices
    ):
        with cols[i]:
            st.markdown(
                f"""
                <div class="price-card">
                    <h3>{duration}</h3>
                    <h2>{local}</h2>
                    <p>{international} international</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    name = st.text_input(
        "Name"
    )

    contact = st.text_input(
        "Contact / Email"
    )

    topic = st.text_area(
        "Topic"
    )

    duration = st.selectbox(
        "Session",
        [
            "20 minutes — PKR 1,000 / $8",
            "30 minutes — PKR 1,500 / $10",
            "45 minutes — PKR 2,000 / $12",
            "Advice / Consultation — PKR 1,500 / $10",
        ],
    )

    payment = st.selectbox(
        "Payment method",
        [
            "Easypaisa",
            "International payment",
        ],
    )

    reference = st.text_input(
        "Payment reference"
    )

    if payment == "Easypaisa":
        if EASYPAISA_NUMBER:
            st.info(
                f"Easypaisa payment number: "
                f"{EASYPAISA_NUMBER}"
            )
        else:
            st.warning(
                "Easypaisa number is not configured yet."
            )

    else:
        if INTERNATIONAL_PAYMENT_URL:
            st.markdown(
                "[Open international payment page]"
                f"({INTERNATIONAL_PAYMENT_URL})"
            )
        else:
            st.warning(
                "International payment URL is not configured."
            )

    if st.button(
        "Submit Consultation Request",
        type="primary",
    ):

        if not name or not contact or not topic:
            st.warning(
                "Please complete the required fields."
            )
        else:

            payload = {
                "user_id": current_user_id(),
                "name": clean_text(name, 200),
                "contact": clean_text(contact, 300),
                "topic": clean_text(topic, 3000),
                "duration": duration,
                "payment_method": payment,
                "payment_reference": clean_text(
                    reference,
                    200,
                ),
                "status": "pending",
            }

            db_insert(
                "consultation_requests",
                payload,
            )

            st.success(
                "Request submitted. "
                "Payment verification remains pending."
            )

            st.caption(
                "Automatic Easypaisa verification requires "
                "official merchant/API integration."
            )


# ============================================================
# 20. PROGRESS
# ============================================================

def page_progress():
    st.markdown(
        """
        <div class="hero">
            <h1>📈 My Progress</h1>
            <p>
            Track your NEUROLENS learning activity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    lab_count = len(
        st.session_state.lab_results
    )

    exercise_count = len(
        st.session_state.exercise_results
    )

    puzzle_count = len(
        st.session_state.puzzle_results
    )

    research_count = len(
        st.session_state.research_notes
    )

    ai_count = st.session_state.ai_requests

    cols = st.columns(5)

    stats = [
        ("🧪", "Lab", lab_count),
        ("🎯", "Exercises", exercise_count),
        ("🧩", "Puzzles", puzzle_count),
        ("🔬", "Research Notes", research_count),
        ("🤖", "AI Requests", ai_count),
    ]

    for i, (icon, label, value) in enumerate(stats):
        with cols[i]:
            st.metric(
                f"{icon} {label}",
                value,
            )

    st.divider()

    if st.session_state.exercise_results:

        if pd:

            df = pd.DataFrame(
                st.session_state.exercise_results
            )

            st.subheader(
                "Exercise History"
            )

            st.dataframe(
                df,
                use_container_width=True,
            )

            if px and "score" in df.columns:
                fig = px.bar(
                    df,
                    x="exercise",
                    y="score",
                    title="Exercise Performance",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

    st.subheader("🏆 Achievements")

    achievements = []

    if lab_count >= 1:
        achievements.append(
            "🧪 First Lab Experiment"
        )

    if exercise_count >= 1:
        achievements.append(
            "🎯 First Brain Challenge"
        )

    if puzzle_count >= 1:
        achievements.append(
            "🧩 Puzzle Explorer"
        )

    if research_count >= 1:
        achievements.append(
            "🔬 Research Explorer"
        )

    if ai_count >= 5:
        achievements.append(
            "🤖 AI Explorer"
        )

    if achievements:
        for item in achievements:
            st.success(item)
    else:
        st.info(
            "Complete activities to unlock achievements."
        )


# ============================================================
# 21. SECURITY CENTER
# ============================================================

def page_security():
    st.markdown(
        """
        <div class="hero">
            <h1>🛡️ Security & Privacy</h1>
            <p>
            NEUROLENS security overview.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    items = [
        (
            "🔑 API Keys",
            "Gemini and Supabase keys should be stored "
            "only in Streamlit Secrets."
        ),
        (
            "🧹 Input Sanitization",
            "User text is length-limited and basic HTML/script "
            "content is removed before processing."
        ),
        (
            "🤖 AI Rate Limiting",
            "AI requests are limited per session."
        ),
        (
            "🔐 Private Ayna",
            "Private session PINs use PBKDF2-HMAC-SHA256."
        ),
        (
            "💳 Payments",
            "Payment references are treated as pending until "
            "verified. Automatic verification requires official APIs."
        ),
        (
            "🧠 Scientific Limitations",
            "Cognitive games and AI interpretations are educational "
            "and must not be treated as clinical diagnosis or actual "
            "brain-activity measurements."
        ),
    ]

    for title, description in items:
        st.markdown(
            f"""
            <div class="neuro-card">
                <h3>{title}</h3>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 22. SETTINGS
# ============================================================

def page_settings():
    st.markdown(
        """
        <div class="hero">
            <h1>⚙️ Settings</h1>
            <p>Configure your NEUROLENS experience.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.language = st.selectbox(
        "Language",
        ["English", "Roman English"],
        index=(
            0
            if st.session_state.language == "English"
            else 1
        ),
    )

    st.write(
        f"AI Model: `{GEMINI_MODEL}`"
    )

    st.write(
        f"AI requests this session: "
        f"{st.session_state.ai_requests}/"
        f"{st.session_state.ai_limit}"
    )

    st.write(
        "Supabase:",
        "Connected" if supabase else "Not connected",
    )

    st.write(
        "Gemini:",
        "Connected" if ai_available() else "Not connected",
    )

    st.write(
        "Easypaisa:",
        "Configured" if EASYPAISA_NUMBER else "Not configured",
    )

    st.write(
        "International payment:",
        "Configured"
        if INTERNATIONAL_PAYMENT_URL
        else "Not configured",
    )

    st.divider()

    if st.button(
        "Reset Session Progress",
        type="secondary",
    ):

        for key in [
            "lab_results",
            "exercise_results",
            "puzzle_results",
            "research_notes",
            "chat",
            "voice_result",
            "face_result",
        ]:
            st.session_state[key] = (
                [] if isinstance(
                    DEFAULTS.get(key),
                    list,
                )
                else None
            )

        st.success(
            "Session progress reset."
        )


# ============================================================
# 23. ACCOUNT
# ============================================================

def page_account():
    st.markdown(
        """
        <div class="hero">
            <h1>👤 Account</h1>
            <p>Manage your NEUROLENS account.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.user:

        st.success(
            f"Signed in as "
            f"{st.session_state.email}"
        )

        st.write(
            "User ID:",
            current_user_id(),
        )

        if st.button(
            "Log Out",
            type="primary",
        ):
            logout()

    else:

        st.info(
            "You are currently exploring NEUROLENS "
            "without an account."
        )

        if st.button(
            "Open Sign In",
            type="primary",
        ):
            st.session_state.page = "Account Login"
            st.rerun()


# ============================================================
# 24. SOCIAL PLACEHOLDER / WORLD
# ============================================================

def page_social():
    st.markdown(
        """
        <div class="hero">
            <h1>🌐 NeuroSocial</h1>
            <p>
            A future social layer for neuroscience,
            challenges and research communities.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "The database foundation supports profiles, "
        "friend requests, conversations, stories and challenges. "
        "The social interface can be expanded without changing "
        "the core NEUROLENS router."
    )

    name = st.text_input(
        "Profile display name"
    )

    bio = st.text_area(
        "Research / neuroscience bio"
    )

    if st.button(
        "Save Profile",
        type="primary",
    ):

        payload = {
            "user_id": current_user_id(),
            "display_name": clean_text(name, 100),
            "bio": clean_text(bio, 1000),
        }

        db_insert(
            "profiles",
            payload,
        )

        st.success(
            "Profile information submitted."
        )


# ============================================================
# 25. SIDEBAR
# ============================================================

def sidebar():
    with st.sidebar:

        st.markdown(
            """
            <div style="text-align:center;">
                <div style="font-size:55px;">🧠</div>
                <h2>NEUROLENS</h2>
                <p style="color:#91a0bc;">
                Explore cognition, behavior & the brain
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        pages = [
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

        selected = st.radio(
            "Explore",
            pages,
            index=pages.index(
                st.session_state.page
            )
            if st.session_state.page in pages
            else 0,
        )

        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()

        st.divider()

        if st.session_state.user:
            st.caption(
                f"Signed in: "
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
# 26. ROUTER
# ============================================================

def main_router():

    page = st.session_state.page

    if page == "NeuroWorld":
        page_neuroworld()

    elif page == "Cognitive Lab":
        page_lab()

    elif page == "Brain Journey":
        page_brain_journey()

    elif page == "Brain Challenges":
        page_challenges()

    elif page == "Brain Puzzle":
        page_puzzle()

    elif page == "Ask Ayna":
        page_ask_ayna()

    elif page == "AI Mood & Behaviour":
        page_mood()

    elif page == "Research World":
        page_research()

    elif page == "Private Ayna":
        page_private()

    elif page == "Behaviour Decoding":
        page_behaviour()

    elif page == "NeuroSocial":
        page_social()

    elif page == "My Progress":
        page_progress()

    elif page == "Security & Privacy":
        page_security()

    elif page == "Settings":
        page_settings()

    elif page == "Account":
        page_account()

    elif page == "Account Login":
        page_auth()

    else:
        st.session_state.page = "NeuroWorld"
        page_neuroworld()


# ============================================================
# 27. RUN APP
# ============================================================

sidebar()
main_router()
