import os
import json
import time
import random
import base64
import streamlit as st

# ============================================================
# NEUROLENS — Cognitive Neuroscience Interactive Lab
# Creator: Ayna Jaffri
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "Home",
    "selected_character": "Ayna",
    "experiment_index": 0,
    "experiment_score": 0,
    "puzzle_score": 0,
    "exercise_stage": 0,
    "exercise_score": 0,
    "journey_stage": 0,
    "mood_result": None,
    "mood_text": "",
    "voice_text": "",
    "ask_history": [],
    "private_history": [],
    "private_unlocked": False,
    "private_pin": "2026",
    "research_mode": False,
    "streak": 1,
    "total_questions": 0,
    "daily_questions": 0,
    "last_day": time.strftime("%Y-%m-%d"),
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Reset daily counter
today = time.strftime("%Y-%m-%d")
if st.session_state.last_day != today:
    st.session_state.last_day = today
    st.session_state.daily_questions = 0


# ============================================================
# FILE / ASSET HELPERS
# ============================================================

def asset_exists(path):
    return os.path.exists(path)


def asset_path(*parts):
    return os.path.join(*parts)


BRAIN_IMAGE = asset_path("brain.png")
BRAIN_VIDEO = asset_path("assets", "brain_animation.mp4")
LAB_VIDEO = asset_path("cognitive_lab_brain.mp4")
AYNA_ROBOT = asset_path("assets", "ayna_robot.png")


# ============================================================
# GEMINI
# ============================================================

def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY")


@st.cache_resource
def get_gemini_client():
    key = get_api_key()

    if not key:
        return None

    try:
        from google import genai
        return genai.Client(api_key=key)
    except Exception:
        return None


def ask_ai(prompt, system_instruction=None):
    client = get_gemini_client()

    if not client:
        return None

    try:
        final_prompt = prompt

        if system_instruction:
            final_prompt = (
                system_instruction
                + "\n\nUSER REQUEST:\n"
                + prompt
            )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=final_prompt,
        )

        if response and response.text:
            st.session_state.total_questions += 1
            st.session_state.daily_questions += 1
            return response.text.strip()

    except Exception:
        return None

    return None


# ============================================================
# BROWSER VOICE
# ============================================================

def voice_button(text, button_text="🔊 Ayna Voice", key=None):
    if not text:
        return

    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", " ")
        .replace("\r", " ")
    )

    html = f"""
    <button
        onclick="speakAyna()"
        style="
            border:1px solid rgba(80,180,255,.45);
            background:linear-gradient(135deg,#101b35,#172c50);
            color:white;
            border-radius:12px;
            padding:9px 16px;
            cursor:pointer;
            font-size:14px;
            margin:5px 0;
        ">
        {button_text}
    </button>

    <script>
    function speakAyna() {{
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(`{safe_text}`);
        msg.lang = "en-US";
        msg.rate = 0.92;
        msg.pitch = 1.05;
        window.speechSynthesis.speak(msg);
    }}
    </script>
    """

    st.components.v1.html(html, height=55)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(37,99,235,.15), transparent 30%),
        radial-gradient(circle at 90% 20%, rgba(124,58,237,.13), transparent 30%),
        linear-gradient(135deg,#050914,#081225 50%,#050914);
    color:#eef5ff;
}

.block-container {
    padding-top:1.5rem;
    padding-bottom:3rem;
    max-width:1400px;
}

h1,h2,h3 {
    letter-spacing:.3px;
}

.neuro-title {
    font-size:4rem;
    font-weight:900;
    text-align:center;
    letter-spacing:8px;
    margin-top:20px;
    background:linear-gradient(90deg,#73d5ff,#ffffff,#a78bfa);
    -webkit-background-clip:text;
    color:transparent;
}

.neuro-subtitle {
    text-align:center;
    color:#aebed6;
    font-size:1.05rem;
    margin-bottom:25px;
}

.lab-card {
    background:linear-gradient(
        145deg,
        rgba(17,30,55,.88),
        rgba(7,15,29,.92)
    );
    border:1px solid rgba(100,180,255,.20);
    border-radius:22px;
    padding:24px;
    min-height:150px;
    box-shadow:0 15px 45px rgba(0,0,0,.25);
}

.lab-card:hover {
    border-color:rgba(100,200,255,.5);
}

.neural-glow {
    animation:pulse 3s infinite ease-in-out;
    filter:
        drop-shadow(0 0 12px rgba(70,190,255,.7))
        drop-shadow(0 0 35px rgba(90,100,255,.4));
}

@keyframes pulse {
    0%,100% {
        transform:translateY(0) scale(1);
    }
    50% {
        transform:translateY(-8px) scale(1.025);
    }
}

.ayna-box {
    background:linear-gradient(
        135deg,
        rgba(16,35,66,.95),
        rgba(25,17,55,.95)
    );
    border:1px solid rgba(154,120,255,.4);
    border-radius:22px;
    padding:20px;
}

.stage-card {
    background:rgba(10,21,39,.9);
    border:1px solid rgba(80,170,255,.25);
    border-radius:18px;
    padding:20px;
    margin:10px 0;
}

.metric {
    background:rgba(255,255,255,.035);
    border:1px solid rgba(255,255,255,.08);
    padding:18px;
    border-radius:18px;
    text-align:center;
}

.small-note {
    color:#9fb0c8;
    font-size:.88rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

PAGES = [
    "Home",
    "Enter Lab",
    "Explore Brain",
    "Brain Puzzle",
    "AI Mood & Behaviour",
    "Brain Exercises",
    "Research Book",
    "Ask Ayna",
    "My Progress",
]

with st.sidebar:
    st.markdown("## 🧠 NEUROLENS")
    st.caption("Cognitive Neuroscience Lab")

    st.divider()

    for i, page in enumerate(PAGES):
        active = st.session_state.page == page

        label = ("● " if active else "○ ") + page

        if st.button(
            label,
            key=f"nav_btn_{i}",
            use_container_width=True,
        ):
            st.session_state.page = page
            st.rerun()

    st.divider()

    st.caption(
        f"Daily AI questions: "
        f"{st.session_state.daily_questions}"
    )

    st.caption("Created by Ayna Jaffri")


# ============================================================
# HEADER
# ============================================================

def page_header(title, subtitle=""):
    st.markdown(f"# {title}")

    if subtitle:
        st.markdown(
            f"<div class='small-note'>{subtitle}</div>",
            unsafe_allow_html=True,
        )

    st.divider()


# ============================================================
# AYA ROBOT
# ============================================================

def show_ayna_robot(width=210):
    if asset_exists(AYNA_ROBOT):
        st.image(
            AYNA_ROBOT,
            width=width,
        )
    else:
        st.markdown(
            """
            <div style="
                font-size:100px;
                text-align:center;
                filter:drop-shadow(0 0 25px #62d9ff);
            ">🤖</div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# HOME
# ============================================================

def home_page():

    st.markdown(
        """
        <div class="neuro-title">NEUROLENS</div>
        <div class="neuro-subtitle">
        Explore cognition, behaviour & the brain
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1.3, 1, 1.3])

    with col1:
        st.markdown(
            """
            <div class="lab-card">
            <h2>🧠 Cognitive Neuroscience</h2>
            <p>
            Explore how neural systems shape perception,
            attention, memory, decisions, emotion and behaviour.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        if asset_exists(BRAIN_IMAGE):
            st.image(
                BRAIN_IMAGE,
                use_container_width=True,
            )
        else:
            st.markdown(
                """
                <div class="neural-glow"
                style="font-size:130px;text-align:center;">
                🧠
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col3:
        st.markdown(
            """
            <div class="lab-card">
            <h2>🔬 Interactive Lab</h2>
            <p>
            Run cognitive experiments, explore neural pathways,
            solve brain puzzles and train cognitive skills.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## Enter the Research Environment")

    cols = st.columns(4)

    cards = [
        ("🔬", "Enter Lab", "Today's cognitive experiment"),
        ("🧠", "Explore Brain", "Inside-brain journey"),
        ("🧩", "Brain Puzzle", "Interactive cognitive puzzle"),
        ("🤖", "AI Mood & Behaviour", "Talk naturally with Ayna"),
    ]

    for i, (icon, title, description) in enumerate(cards):
        with cols[i]:
            st.markdown(
                f"""
                <div class="lab-card">
                <h2>{icon} {title}</h2>
                <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")

    c1, c2, c3, c4 = st.columns(4)

    buttons = [
        ("Brain Exercises", c1),
        ("Research Book", c2),
        ("Ask Ayna", c3),
        ("My Progress", c4),
    ]

    for title, col in buttons:
        with col:
            if st.button(
                title,
                use_container_width=True,
                key=f"home_{title}",
            ):
                st.session_state.page = title
                st.rerun()

    st.divider()

    st.markdown("### 🤖 Meet Ayna — AI Lab Assistant")

    c1, c2 = st.columns([1, 2])

    with c1:
        show_ayna_robot()

    with c2:
        st.markdown(
            """
            <div class="ayna-box">
            <h3>Ayna</h3>
            <p>
            Your AI neuroscience lab assistant.
            Ayna can explain brain mechanisms, guide experiments,
            discuss cognitive behaviour and help you explore
            neuroscience concepts.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        voice_button(
            "Welcome to NEUROLENS. I am Ayna, your AI neuroscience lab assistant. "
            "Choose a laboratory module and let's explore the brain."
        )


# ============================================================
# ENTER LAB
# ============================================================

EXPERIMENTS = [
    {
        "name": "Working Memory",
        "area": "Prefrontal cortex",
        "task": "Remember the sequence and reproduce it.",
        "question": "Remember this sequence:",
    },
    {
        "name": "Selective Attention",
        "area": "Frontoparietal attention network",
        "task": "Identify the target while ignoring distractors.",
        "question": "Which symbol appeared most often?",
    },
    {
        "name": "Decision Making",
        "area": "Prefrontal–striatal circuits",
        "task": "Choose between options with different rewards.",
        "question": "Which option gives the better expected outcome?",
    },
    {
        "name": "Cognitive Flexibility",
        "area": "Prefrontal control networks",
        "task": "Switch rules when the task changes.",
        "question": "What rule is active now?",
    },
    {
        "name": "Inhibitory Control",
        "area": "Fronto-striatal control system",
        "task": "Respond only when the target appears.",
        "question": "Should you respond?",
    },
]


def lab_page():

    page_header(
        "🔬 Cognitive Neuroscience Lab",
        "A structured interactive environment for cognitive exploration.",
    )

    st.markdown("### 1. Select your research character")

    characters = ["Ayna", "Researcher", "Explorer"]

    selected = st.radio(
        "Character",
        characters,
        index=characters.index(
            st.session_state.selected_character
        ),
        horizontal=True,
    )

    st.session_state.selected_character = selected

    st.markdown("### 2. Laboratory environment")

    if asset_exists(LAB_VIDEO):
        st.video(LAB_VIDEO)

    elif asset_exists(BRAIN_VIDEO):
        st.video(BRAIN_VIDEO)

    else:
        st.markdown(
            """
            <div class="lab-card">
            🧠 Neural laboratory visualisation
            </div>
            """,
            unsafe_allow_html=True,
        )

    experiment = EXPERIMENTS[
        st.session_state.experiment_index %
        len(EXPERIMENTS)
    ]

    st.markdown("### 🧪 Today's Experiment")

    st.markdown(
        f"""
        <div class="lab-card">
        <h2>{experiment["name"]}</h2>
        <p>
        <b>Neural system:</b> {experiment["area"]}
        </p>
        <p>{experiment["task"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if experiment["name"] == "Working Memory":

        sequence = st.session_state.get(
            "memory_sequence"
        )

        if sequence is None:
            sequence = [
                random.randint(1, 9)
                for _ in range(5)
            ]

            st.session_state.memory_sequence = sequence
            st.session_state.memory_answer = None

        st.info(
            "Study the sequence for a few seconds, "
            "then reproduce it."
        )

        st.code("  ".join(map(str, sequence)))

        answer = st.text_input(
            "Enter the sequence:",
            key="memory_input",
        )

        if st.button(
            "Submit Experiment",
            key="memory_submit",
        ):
            expected = "".join(map(str, sequence))
            cleaned = "".join(
                ch for ch in answer
                if ch.isdigit()
            )

            if cleaned == expected:
                st.success("Correct! Working memory response detected.")
                st.session_state.experiment_score += 1
            else:
                st.warning(
                    f"Not quite. The target sequence was {expected}."
                )

    elif experiment["name"] == "Selective Attention":

        options = [
            "Circle",
            "Triangle",
            "Square",
            "Star",
        ]

        target = random.choice(options)

        st.write(
            f"Focus on the target: **{target}**"
        )

        choices = random.sample(
            options * 2,
            4,
        )

        selected_answer = st.radio(
            "Which was the target?",
            choices,
            key="attention_choice",
        )

        if st.button(
            "Submit",
            key="attention_submit",
        ):
            if selected_answer == target:
                st.success("Correct attention selection.")
                st.session_state.experiment_score += 1
            else:
                st.error("Try again.")

    else:

        q = experiment["question"]

        st.info(q)

        options = [
            "Option A",
            "Option B",
            "Option C",
            "Option D",
        ]

        answer = st.radio(
            "Your response:",
            options,
            key=f"exp_{experiment['name']}",
        )

        if st.button(
            "Submit Experiment",
            key=f"submit_{experiment['name']}",
        ):
            if answer == "Option B":
                st.success("Correct response.")
                st.session_state.experiment_score += 1
            else:
                st.info(
                    "Response recorded. Cognitive performance "
                    "depends on task design and context."
                )

    st.markdown("### 🧠 Neural Explanation")

    explanation = ask_ai(
        f"""
        Explain the cognitive neuroscience behind the
        experiment "{experiment['name']}" in simple but scientifically
        accurate language. Mention relevant brain networks and
        cognitive processes. Keep it under 150 words.
        """
    )

    if explanation is None:
        explanation = (
            f"This task explores {experiment['name']} and involves "
            f"{experiment['area']}. Performance can reflect attention, "
            "working memory, decision processes or cognitive control."
        )

    st.write(explanation)
    voice_button(explanation)

    if st.button(
        "➡️ Next Daily Experiment",
        key="next_experiment",
    ):
        st.session_state.experiment_index += 1
        st.session_state.memory_sequence = None
        st.rerun()


# ============================================================
# EXPLORE BRAIN
# ============================================================

JOURNEY = [
    (
        "Whole Brain",
        "The brain is an interconnected biological network containing "
        "specialised regions and distributed functional systems."
    ),
    (
        "Brain Region",
        "Different regions contribute to functions such as movement, "
        "memory, language, emotion and executive control."
    ),
    (
        "Neural Circuit",
        "Cognition emerges from communication between distributed "
        "neural circuits rather than from one isolated brain area."
    ),
    (
        "Neuron",
        "Neurons receive, integrate and transmit information."
    ),
    (
        "Dendrites",
        "Dendrites receive many synaptic inputs from other neurons."
    ),
    (
        "Axon",
        "The axon carries electrical signals toward other parts of the neuron."
    ),
    (
        "Myelin",
        "Myelin increases the efficiency and speed of electrical signal propagation."
    ),
    (
        "Electrical Signal",
        "Action potentials are rapid changes in membrane voltage that "
        "propagate along the axon."
    ),
    (
        "Synapse",
        "Synapses allow one neuron to communicate with another neuron "
        "or target cell."
    ),
    (
        "Neurotransmitter",
        "Neurotransmitters are chemical messengers released at many synapses."
    ),
    (
        "Cognition & Behaviour",
        "The coordinated activity of neural systems supports perception, "
        "learning, memory, decisions and behaviour."
    ),
]


def brain_journey_page():

    page_header(
        "🧠 Inside-Brain Journey",
        "Travel from the whole brain to neurons, synapses and cognition.",
    )

    stage_index = st.session_state.journey_stage
    title, explanation = JOURNEY[stage_index]

    if asset_exists(BRAIN_VIDEO):
        st.video(BRAIN_VIDEO)

    elif asset_exists(BRAIN_IMAGE):
        st.image(
            BRAIN_IMAGE,
            use_container_width=True,
        )

    st.markdown(
        f"""
        <div class="stage-card">
        <h2>Stage {stage_index + 1}: {title}</h2>
        <p>{explanation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    voice_button(
        f"Stage {stage_index + 1}. {title}. {explanation}",
        "🔊 Ayna Explain",
    )

    st.markdown("### 🤖 Ask Ayna about this stage")

    question = st.text_input(
        "Ask a question:",
        key=f"journey_q_{stage_index}",
        placeholder="What is happening here?",
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "Send",
            key=f"journey_send_{stage_index}",
            use_container_width=True,
        ):

            if question.strip():

                answer = ask_ai(
                    question,
                    system_instruction=f"""
                    You are Ayna, an AI cognitive neuroscience
                    lab assistant.

                    Current neural stage:
                    {title}

                    Current explanation:
                    {explanation}

                    Answer the user's question specifically
                    in relation to this stage.

                    Be scientifically accurate and easy to understand.
                    Do not claim to diagnose or provide medical treatment.
                    """
                )

                if answer is None:
                    answer = (
                        f"At the {title} stage, we are examining "
                        f"how neural structure and communication "
                        f"relate to cognition and behaviour."
                    )

                st.session_state.ask_history.append(
                    {
                        "question": question,
                        "answer": answer,
                    }
                )

    with c2:
        if st.button(
            "Next Stage ➜",
            key=f"journey_next_{stage_index}",
            use_container_width=True,
        ):
            if stage_index < len(JOURNEY) - 1:
                st.session_state.journey_stage += 1
            else:
                st.session_state.journey_stage = 0

            st.rerun()

    if st.session_state.ask_history:
        last = st.session_state.ask_history[-1]

        st.markdown("### Ayna")
        st.write(last["answer"])
        voice_button(
            last["answer"],
            "🔊 Ayna Voice",
        )

    st.progress(
        (stage_index + 1) / len(JOURNEY)
    )


# ============================================================
# REAL TOUCH / MOUSE DRAG PUZZLE
# ============================================================

def puzzle_page():

    page_header(
        "🧩 Brain Puzzle Lab",
        "Pick up a tile with your finger or mouse and drag it into position.",
    )

    st.markdown(
        """
        **How to play:**  
        Hold a piece → drag it → release it over another position.
        This is a real drag interaction, not click-to-swap.
        """
    )

    size = st.selectbox(
        "Puzzle level",
        [3, 4, 5],
        format_func=lambda x: f"{x} × {x}",
    )

    # Generate tile order in session
    puzzle_key = f"puzzle_{size}"

    if puzzle_key not in st.session_state:
        tiles = list(range(size * size))
        shuffled = tiles.copy()
        random.shuffle(shuffled)

        # avoid solved puzzle
        if shuffled == tiles:
            random.shuffle(shuffled)

        st.session_state[puzzle_key] = shuffled

    tiles = st.session_state[puzzle_key]

    correct = list(range(size * size))

    html_tiles = ""

    for position, tile in enumerate(tiles):

        row = tile // size
        col = tile % size

        # CSS uses grid pieces with a brain-like visual.
        html_tiles += f"""
        <div
            class="puzzle-piece"
            draggable="true"
            data-position="{position}"
            data-tile="{tile}"
            style="
                background-image:url('/app/static/brain.png');
                background-size:{size * 100}% {size * 100}%;
                background-position:
                    {0 if size == 1 else (col/(size-1))*100}%
                    {0 if size == 1 else (row/(size-1))*100}%;
            "
        >
            <div class="piece-number">{tile + 1}</div>
        </div>
        """

    puzzle_html = f"""
    <style>
    .puzzle-wrapper {{
        max-width:650px;
        margin:auto;
        padding:15px;
        background:#081225;
        border-radius:20px;
        border:1px solid rgba(100,180,255,.3);
    }}

    .puzzle-grid {{
        display:grid;
        grid-template-columns:repeat({size},1fr);
        gap:5px;
        touch-action:none;
        user-select:none;
    }}

    .puzzle-piece {{
        aspect-ratio:1;
        border-radius:10px;
        border:2px solid rgba(100,200,255,.35);
        cursor:grab;
        position:relative;
        transition:.15s;
        overflow:hidden;
        box-shadow:0 4px 12px rgba(0,0,0,.35);
    }}

    .puzzle-piece:active {{
        cursor:grabbing;
        transform:scale(1.06);
        z-index:10;
    }}

    .piece-number {{
        position:absolute;
        top:5px;
        left:5px;
        background:rgba(0,0,0,.65);
        border-radius:7px;
        padding:3px 7px;
        color:white;
        font-size:11px;
    }}

    .drag-over {{
        border:3px solid #67e8f9;
        transform:scale(1.03);
    }}
    </style>

    <div class="puzzle-wrapper">

    <div id="puzzleGrid" class="puzzle-grid">
        {html_tiles}
    </div>

    <p id="status"
       style="text-align:center;color:#9fb0c8;margin-top:15px;">
       Drag pieces into the correct position.
    </p>

    </div>

    <script>

    const pieces = document.querySelectorAll(".puzzle-piece");
    let dragged = null;

    pieces.forEach(piece => {{

        piece.addEventListener("dragstart", function(e) {{
            dragged = this;
            this.style.opacity = "0.5";
        }});

        piece.addEventListener("dragend", function(e) {{
            this.style.opacity = "1";
        }});

        piece.addEventListener("dragover", function(e) {{
            e.preventDefault();
            this.classList.add("drag-over");
        }});

        piece.addEventListener("dragleave", function() {{
            this.classList.remove("drag-over");
        }});

        piece.addEventListener("drop", function(e) {{

            e.preventDefault();
            this.classList.remove("drag-over");

            if (!dragged || dragged === this) return;

            const grid = document.getElementById("puzzleGrid");

            const children = Array.from(grid.children);

            const from = children.indexOf(dragged);
            const to = children.indexOf(this);

            if (from < to) {{
                grid.insertBefore(dragged, this.nextSibling);
            }} else {{
                grid.insertBefore(dragged, this);
            }}

            const order = Array.from(grid.children)
                .map(x => parseInt(x.dataset.tile));

            const solved = order.every(
                (v,i) => v === i
            );

            if (solved) {{
                document.getElementById("status").innerHTML =
                    "🎉 Puzzle complete! Excellent cognitive control.";
            }}
        }});
    }});

    // Mobile / tablet pointer drag
    let active = null;
    let startX = 0;
    let startY = 0;

    pieces.forEach(piece => {{

        piece.addEventListener("pointerdown", e => {{
            active = piece;
            startX = e.clientX;
            startY = e.clientY;

            piece.setPointerCapture(e.pointerId);
            piece.style.zIndex = "100";
            piece.style.transform = "scale(1.05)";
        }});

        piece.addEventListener("pointermove", e => {{
            if (!active) return;

            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            if (Math.abs(dx) + Math.abs(dy) > 8) {{
                active.style.transform =
                    `translate(${{dx}}px,${{dy}}px) scale(1.05)`;
            }}
        }});

        piece.addEventListener("pointerup", e => {{

            if (!active) return;

            active.style.transform = "";
            active.style.zIndex = "";

            const target = document.elementFromPoint(
                e.clientX,
                e.clientY
            );

            const targetPiece =
                target?.closest(".puzzle-piece");

            if (
                targetPiece &&
                targetPiece !== active
            ) {{

                const grid =
                    document.getElementById("puzzleGrid");

                const children =
                    Array.from(grid.children);

                const from =
                    children.indexOf(active);

                const to =
                    children.indexOf(targetPiece);

                if (from < to) {{
                    grid.insertBefore(
                        active,
                        targetPiece.nextSibling
                    );
                }} else {{
                    grid.insertBefore(
                        active,
                        targetPiece
                    );
                }}

                const order =
                    Array.from(grid.children)
                    .map(x => parseInt(x.dataset.tile));

                if (
                    order.every((v,i) => v === i)
                ) {{
                    document.getElementById(
                        "status"
                    ).innerHTML =
                        "🎉 Puzzle complete!";
                }}
            }}

            active = null;
        }});
    }});

    </script>
    """

    st.components.v1.html(
        puzzle_html,
        height=760,
    )

    st.info(
        "Puzzle interaction runs inside the browser. "
        "The tile order is stored for this session."
    )


# ============================================================
# AI MOOD & BEHAVIOUR
# ============================================================

def mood_page():

    page_header(
        "🤖 AI Mood & Behaviour",
        "Talk naturally with Ayna and receive a broad behavioural reflection.",
    )

    st.markdown(
        """
        <div class="ayna-box">
        <b>Talk to Ayna</b><br>
        You can speak naturally. After recording, press
        <b>Send</b> and Ayna will analyse the available speech/content.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎙️ Voice Input")

    audio = st.audio_input(
        "Record your message",
        key="behaviour_audio",
    )

    voice_transcript = ""

    if audio is not None:

        st.audio(audio)

        st.markdown(
            "Recording ready. Press **Send Voice**."
        )

        if st.button(
            "📤 Send Voice",
            key="send_voice",
        ):

            # Try Gemini multimodal transcription
            client = get_gemini_client()

            if client:

                try:
                    audio_bytes = audio.getvalue()

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            """
                            Transcribe this user's speech accurately.
                            Return only the spoken words.
                            """,
                            {
                                "mime_type": "audio/wav",
                                "data": audio_bytes,
                            },
                        ],
                    )

                    if response and response.text:
                        voice_transcript = response.text.strip()

                except Exception:
                    voice_transcript = ""

            if not voice_transcript:
                voice_transcript = (
                    "I received your voice recording, but automatic "
                    "speech transcription is currently unavailable."
                )

            st.session_state.voice_text = voice_transcript

    if st.session_state.voice_text:

        st.markdown("### 📝 Voice Transcript")
        st.write(st.session_state.voice_text)

        analyse = ask_ai(
            f"""
            Analyse the following spoken content for a broad,
            non-clinical behavioural reflection.

            Content:
            {st.session_state.voice_text}

            Choose one broad state:
            Positive / Happy
            Calm
            Neutral
            Worried
            Low / Sad
            Frustrated
            Tired

            Return:
            Mood:
            Explanation:
            Helpful suggestion:

            Do not diagnose a medical or psychiatric condition.
            """
        )

        if analyse:

            text_lower = analyse.lower()

            if "worried" in text_lower:
                emoji = "😟"
            elif "sad" in text_lower or "low" in text_lower:
                emoji = "😔"
            elif "frustrated" in text_lower:
                emoji = "😤"
            elif "tired" in text_lower:
                emoji = "😴"
            elif "calm" in text_lower:
                emoji = "😌"
            elif "happy" in text_lower or "positive" in text_lower:
                emoji = "😊"
            else:
                emoji = "😐"

            st.session_state.mood_result = emoji
            st.session_state.mood_text = analyse

    st.divider()

    st.markdown("### 💬 Text Input")

    text_message = st.text_area(
        "Or type your message:",
        placeholder="Tell Ayna how you feel or what happened...",
        key="behaviour_text",
    )

    if st.button(
        "📤 Send Text",
        key="send_behaviour_text",
    ):

        if text_message.strip():

            answer = ask_ai(
                text_message,
                system_instruction="""
                You are Ayna, an AI cognitive neuroscience assistant.

                Respond empathetically and briefly.

                If the user asks about mood or behaviour,
                give a broad non-clinical reflection.

                Never diagnose mental illness.
                Never claim certainty from text alone.
                """
            )

            if answer is None:
                answer = (
                    "Thank you for sharing that. Your words can give "
                    "some clues about your current state, but one message "
                    "is not enough to determine a person's full emotional state."
                )

            st.session_state.mood_text = answer

            lower = text_message.lower()

            if any(
                x in lower
                for x in [
                    "happy",
                    "good",
                    "excited",
                    "great",
                ]
            ):
                st.session_state.mood_result = "😊"

            elif any(
                x in lower
                for x in [
                    "sad",
                    "cry",
                    "down",
                ]
            ):
                st.session_state.mood_result = "😔"

            elif any(
                x in lower
                for x in [
                    "angry",
                    "frustrated",
                ]
            ):
                st.session_state.mood_result = "😤"

            elif any(
                x in lower
                for x in [
                    "worried",
                    "anxious",
                    "stress",
                ]
            ):
                st.session_state.mood_result = "😟"

            else:
                st.session_state.mood_result = "😐"

    if st.session_state.mood_result:

        st.markdown("## Your current reflection")

        st.markdown(
            f"""
            <div class="lab-card"
                 style="text-align:center;">
                <div style="font-size:80px;">
                {st.session_state.mood_result}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.mood_text:

            st.write(
                st.session_state.mood_text
            )

            voice_button(
                st.session_state.mood_text,
                "🔊 Ayna Responds",
            )

        st.caption(
            "This is a broad AI reflection, not a clinical diagnosis."
        )


# ============================================================
# BRAIN EXERCISES
# ============================================================

EXERCISES = [
    {
        "name": "Attention",
        "instruction": "Find the only different number.",
        "question": "Which number is different?",
        "options": ["5", "5", "5", "8", "5"],
        "answer": "8",
    },
    {
        "name": "Working Memory",
        "instruction": "Remember: BLUE → 7 → STAR.",
        "question": "What number appeared?",
        "options": ["3", "5", "7", "9"],
        "answer": "7",
    },
    {
        "name": "Memory",
        "instruction": "Remember: apple, river, chair.",
        "question": "Which word was present?",
        "options": ["apple", "cloud", "mountain", "phone"],
        "answer": "apple",
    },
    {
        "name": "Decision Making",
        "instruction": "Choose the option with higher expected value.",
        "question": "10 points with 80% probability or 3 points guaranteed?",
        "options": [
            "10 points / 80%",
            "3 points guaranteed",
            "Both equal",
            "Cannot compare",
        ],
        "answer": "10 points / 80%",
    },
    {
        "name": "Inhibitory Control",
        "instruction": "Respond to GO, not STOP.",
        "question": "Target says: STOP. Should you respond?",
        "options": ["Yes", "No"],
        "answer": "No",
    },
    {
        "name": "Cognitive Flexibility",
        "instruction": "Switch from colour rule to shape rule.",
        "question": "Which rule should you use?",
        "options": [
            "Previous rule",
            "New rule",
            "Random rule",
            "No rule",
        ],
        "answer": "New rule",
    },
]


def exercises_page():

    page_header(
        "🧠 AI Brain Exercise System",
        "Progressive cognitive tasks across multiple domains.",
    )

    stage = st.session_state.exercise_stage

    exercise = EXERCISES[
        stage % len(EXERCISES)
    ]

    st.markdown(
        f"""
        <div class="lab-card">
        <h2>Stage {stage + 1}: {exercise["name"]}</h2>
        <p>{exercise["instruction"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎯 Challenge")

    answer = st.radio(
        exercise["question"],
        exercise["options"],
        key=f"exercise_answer_{stage}",
    )

    if st.button(
        "Submit Challenge",
        key=f"exercise_submit_{stage}",
    ):

        if answer == exercise["answer"]:
            st.success("Correct! 🧠")
            st.session_state.exercise_score += 1
        else:
            st.warning(
                f"Not quite. Correct answer: {exercise['answer']}"
            )

        st.session_state.exercise_stage += 1

        if st.session_state.exercise_stage >= len(EXERCISES):
            st.session_state.exercise_stage = 0

        st.rerun()

    st.progress(
        (stage + 1) / len(EXERCISES)
    )

    st.markdown("### 🤖 Ayna's neuroscience explanation")

    explanation = ask_ai(
        f"""
        Explain the neuroscience behind a cognitive exercise
        targeting {exercise['name']}.
        Mention relevant cognitive systems and keep it under 100 words.
        """
    )

    if explanation is None:
        explanation = (
            f"This exercise targets {exercise['name']}. "
            "Cognitive performance emerges from coordinated activity "
            "across distributed brain networks."
        )

    st.write(explanation)
    voice_button(explanation)


# ============================================================
# RESEARCH BOOK
# ============================================================

RESEARCH_TOPICS = {
    "Brain & Behaviour": (
        "Brain and behaviour are linked through interacting neural "
        "systems, physiological processes and environmental context."
    ),
    "Memory": (
        "Memory includes encoding, consolidation, storage and retrieval. "
        "Different memory systems depend on partly distinct neural networks."
    ),
    "Attention": (
        "Attention prioritises information for processing. "
        "Attention can be influenced by goals, salience and arousal."
    ),
    "Perception": (
        "Perception involves transforming sensory signals into meaningful "
        "representations through distributed neural processing."
    ),
    "Emotion": (
        "Emotion involves interactions among cortical, subcortical, "
        "autonomic and hormonal systems."
    ),
    "Decision Making": (
        "Decision making integrates reward, uncertainty, memory, "
        "attention and executive control."
    ),
    "Learning": (
        "Learning involves changes in behaviour and neural representations "
        "through experience."
    ),
    "Cognitive Control": (
        "Cognitive control supports goal-directed behaviour, inhibition, "
        "monitoring and flexible adjustment."
    ),
    "Reward": (
        "Reward processing involves interactions between valuation, "
        "motivation and reinforcement-learning systems."
    ),
    "Executive Functions": (
        "Executive functions include working memory, inhibitory control "
        "and cognitive flexibility."
    ),
    "Neuroplasticity": (
        "Neuroplasticity refers to changes in neural structure or function "
        "associated with development, experience or injury."
    ),
    "Neural Circuits": (
        "Complex behaviour emerges from communication across distributed "
        "neural circuits rather than isolated brain regions."
    ),
    "Neurotransmitters": (
        "Neurotransmitters are chemical signalling molecules used by "
        "neurons to communicate at many synapses."
    ),
}


def research_page():

    page_header(
        "📖 Research Book",
        "Explore neuroscience from simple concepts to research-level terminology.",
    )

    mode = st.toggle(
        "Research Mode",
        value=st.session_state.research_mode,
    )

    st.session_state.research_mode = mode

    topic = st.selectbox(
        "Choose a topic",
        list(RESEARCH_TOPICS.keys()),
    )

    explanation = RESEARCH_TOPICS[topic]

    st.markdown(
        f"""
        <div class="lab-card">
        <h2>{topic}</h2>
        <p>{explanation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mode:

        st.markdown("### 🔬 Research Mode")

        deeper = ask_ai(
            f"""
            Provide a concise research-level overview of {topic}.
            Include:
            1. Core concept
            2. Relevant neural systems
            3. Important terminology
            4. Current research question

            Do not invent citations.
            """
        )

        if deeper is None:
            deeper = (
                "Research-level interpretation should consider "
                "multiple interacting neural systems, experimental "
                "design, behavioural measures and methodological limitations."
            )

        st.write(deeper)

        st.markdown("### 📚 Suggested foundational sources")

        sources = [
            "Kandel et al. — Principles of Neural Science",
            "Purves et al. — Neuroscience",
            "Bear, Connors & Paradiso — Neuroscience: Exploring the Brain",
        ]

        for source in sources:
            st.markdown(f"- {source}")

    else:

        st.markdown(
            "Switch on **Research Mode** for deeper terminology "
            "and research-oriented explanations."
        )


# ============================================================
# ASK AYNA
# ============================================================

def ask_ayna_page():

    page_header(
        "🤖 Ask Ayna",
        "Your private neuroscience and general conversation space.",
    )

    c1, c2 = st.columns([1, 2])

    with c1:
        show_ayna_robot()

    with c2:

        st.markdown(
            """
            <div class="ayna-box">
            <h3>Ayna AI Assistant</h3>
            <p>
            Ask about neuroscience, cognition, behaviour,
            decisions, learning, brain systems or general questions.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 💬 Chat")

    message = st.text_area(
        "Your message",
        placeholder="Ask Ayna anything...",
        key="ask_ayna_message",
    )

    c1, c2 = st.columns(2)

    with c1:
        send = st.button(
            "📤 Send",
            key="ask_ayna_send",
            use_container_width=True,
        )

    with c2:
        clear = st.button(
            "🗑️ Clear Chat",
            key="ask_ayna_clear",
            use_container_width=True,
        )

    if clear:
        st.session_state.ask_history = []
        st.rerun()

    if send and message.strip():

        answer = ask_ai(
            message,
            system_instruction="""
            You are Ayna, the AI assistant inside NEUROLENS.

            Your main expertise is cognitive neuroscience,
            behaviour, brain systems, learning, attention,
            memory, decision making and AI.

            Be accurate, concise and human.

            Never claim to be a doctor or therapist.
            Never diagnose.
            If evidence is uncertain, say so.
            """
        )

        if answer is None:
            answer = (
                "I'm currently operating in offline mode. "
                "I can still help you explore basic neuroscience "
                "and cognitive concepts."
            )

        st.session_state.ask_history.append(
            {
                "question": message,
                "answer": answer,
            }
        )

    for item in reversed(
        st.session_state.ask_history[-8:]
    ):

        st.markdown("**You:**")
        st.write(item["question"])

        st.markdown("**Ayna:**")
        st.write(item["answer"])

        voice_button(
            item["answer"],
            "🔊 Ayna Voice",
        )

        st.divider()


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

def private_chat_page():

    page_header(
        "🔐 Private Ask Ayna",
        "Session-protected personal conversation area.",
    )

    if not st.session_state.private_unlocked:

        st.markdown(
            """
            <div class="ayna-box">
            <h3>Private Access</h3>
            <p>
            Enter your session PIN to open this conversation.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pin = st.text_input(
            "PIN",
            type="password",
            key="private_pin_input",
        )

        if st.button(
            "Unlock",
            key="private_unlock",
        ):

            if pin == st.session_state.private_pin:
                st.session_state.private_unlocked = True
                st.rerun()
            else:
                st.error("Incorrect PIN.")

        st.caption(
            "This is a session-level lock, not end-to-end encryption."
        )

        return

    st.success("Private session unlocked.")

    if st.button(
        "🔒 Lock",
        key="private_lock",
    ):
        st.session_state.private_unlocked = False
        st.rerun()

    message = st.text_area(
        "Private message",
        key="private_message",
        placeholder="Talk privately with Ayna...",
    )

    if st.button(
        "📤 Send Private Message",
        key="private_send",
    ):

        if message.strip():

            answer = ask_ai(
                message,
                system_instruction="""
                You are Ayna in a private conversation.

                Be supportive, respectful and concise.

                You can discuss neuroscience, behaviour,
                personal reflections and general problems.

                Do not diagnose medical or psychiatric conditions.
                Do not claim confidentiality beyond the application's
                actual technical security.
                """
            )

            if answer is None:
                answer = (
                    "I'm here to help you think through the situation "
                    "from a cognitive and behavioural perspective."
                )

            st.session_state.private_history.append(
                {
                    "question": message,
                    "answer": answer,
                }
            )

    for item in reversed(
        st.session_state.private_history[-10:]
    ):

        st.markdown("**You:**")
        st.write(item["question"])

        st.markdown("**Ayna:**")
        st.write(item["answer"])

        voice_button(
            item["answer"],
            "🔊 Ayna Voice",
        )

        st.divider()


# ============================================================
# PROGRESS
# ============================================================

def progress_page():

    page_header(
        "📊 My Progress",
        "Your NEUROLENS cognitive exploration dashboard.",
    )

    cols = st.columns(4)

    metrics = [
        (
            "Experiments",
            st.session_state.experiment_score,
        ),
        (
            "Puzzle Score",
            st.session_state.puzzle_score,
        ),
        (
            "Exercise Score",
            st.session_state.exercise_score,
        ),
        (
            "AI Questions",
            st.session_state.total_questions,
        ),
    ]

    for col, (label, value) in zip(cols, metrics):

        with col:

            st.markdown(
                f"""
                <div class="metric">
                <h3>{value}</h3>
                <div>{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")

    st.markdown("### 🔬 Cognitive Areas")

    areas = [
        ("Attention", 0.72),
        ("Working Memory", 0.64),
        ("Decision Making", 0.58),
        ("Inhibitory Control", 0.70),
        ("Cognitive Flexibility", 0.52),
    ]

    for name, value in areas:
        st.write(name)
        st.progress(value)

    st.markdown("### 🔥 Streak")

    st.metric(
        "Current streak",
        f"{st.session_state.streak} day",
    )

    st.markdown("### 📚 Research Archive")

    st.info(
        "Research topics explored during this session "
        "will appear here as the platform expands."
    )

    st.markdown("### ⚠️ Data note")

    st.caption(
        "Current progress is session-based. "
        "Permanent user accounts and database-backed history "
        "require a persistent backend."
    )


# ============================================================
# PAGE ROUTER
# ============================================================

page = st.session_state.page

if page == "Home":
    home_page()

elif page == "Enter Lab":
    lab_page()

elif page == "Explore Brain":
    brain_journey_page()

elif page == "Brain Puzzle":
    puzzle_page()

elif page == "AI Mood & Behaviour":
    mood_page()

elif page == "Brain Exercises":
    exercises_page()

elif page == "Research Book":
    research_page()

elif page == "Ask Ayna":
    ask_ayna_page()

elif page == "My Progress":
    progress_page()

else:
    home_page()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#73849c;
        padding:15px;
    ">
    🧠 NEUROLENS · Cognitive Neuroscience Interactive Lab<br>
    Created by Ayna Jaffri
    </div>
    """,
    unsafe_allow_html=True,
)
