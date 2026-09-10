import streamlit as st
import os
import time
import random
import base64
from pathlib import Path

try:
    import plotly.graph_objects as plotly_go
except Exception:
    plotly_go = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# PATHS / ASSETS
# -----------------------------

BASE_DIR = Path(__file__).parent

ASSETS_DIR = BASE_DIR / "assets"

BRAIN_IMAGE = BASE_DIR / "brain.png"

ROBOT_IMAGE = ASSETS_DIR / "ayna_robot.png"

LAB_VIDEO = BASE_DIR / "cognitive_lab_brain.mp4"

BRAIN_VIDEO = ASSETS_DIR / "brain_animation.mp4"

REBOOT_NAMES = [
    "ayna_reboot.mp4",
    "ayna_welcome.mp4",
    "reboot.mp4",
    "welcome.mp4",
]

REBOOT_VIDEO = None

for name in REBOOT_NAMES:
    candidate = BASE_DIR / name
    if candidate.exists():
        REBOOT_VIDEO = candidate
        break

# -----------------------------
# STYLE
# -----------------------------

st.markdown(
    """
    <style>
    .stApp {
        background:
        radial-gradient(circle at top left, rgba(50,80,120,.18), transparent 35%),
        linear-gradient(135deg, #07111f 0%, #0a1628 45%, #07101c 100%);
        color: #f4f7fb;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 0;
    }

    .subtitle {
        color: #aab8cc;
        font-size: 17px;
        margin-top: 0;
    }

    .card {
        background: rgba(17, 29, 48, .78);
        border: 1px solid rgba(150, 180, 220, .14);
        border-radius: 18px;
        padding: 22px;
        margin: 10px 0;
        box-shadow: 0 12px 35px rgba(0,0,0,.18);
    }

    .small-card {
        background: rgba(20, 34, 55, .70);
        border-radius: 15px;
        padding: 16px;
        border: 1px solid rgba(150,180,220,.12);
    }

    .section-title {
        font-size: 27px;
        font-weight: 750;
        margin-bottom: 6px;
    }

    .muted {
        color: #9eacc0;
    }

    div.stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(150,180,220,.18);
        min-height: 42px;
        font-weight: 650;
    }

    [data-testid="stSidebar"] {
        background: #07101d;
    }

    .stProgress > div > div {
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# SESSION STATE
# -----------------------------

if "page" not in st.session_state:
    st.session_state.page = "Welcome Reboot"

if "language" not in st.session_state:
    st.session_state.language = "English"

if "character" not in st.session_state:
    st.session_state.character = "Nova"

if "selected_equipment" not in st.session_state:
    st.session_state.selected_equipment = "EEG Scanner"

if "mood_result" not in st.session_state:
    st.session_state.mood_result = None

if "experiment_score" not in st.session_state:
    st.session_state.experiment_score = 0

if "puzzle_score" not in st.session_state:
    st.session_state.puzzle_score = 0

if "messages" not in st.session_state:
    st.session_state.messages = []

if "private_messages" not in st.session_state:
    st.session_state.private_messages = []

if "private_unlocked" not in st.session_state:
    st.session_state.private_unlocked = False

if "daily_questions" not in st.session_state:
    st.session_state.daily_questions = 0

if "completed_experiments" not in st.session_state:
    st.session_state.completed_experiments = 0

# -----------------------------
# DATA
# -----------------------------

BRAIN_STAGES = [
    (
        "Whole Brain",
        "The brain is an interconnected biological system supporting perception, cognition, emotion, movement and behaviour.",
    ),
    (
        "Prefrontal Cortex",
        "The prefrontal cortex contributes to planning, cognitive control, working memory and decision-making.",
    ),
    (
        "Hippocampus",
        "The hippocampus is strongly involved in memory formation, spatial representation and contextual processing.",
    ),
    (
        "Striatum",
        "The striatum is a major component of basal ganglia circuits and participates in action selection, reward and learning.",
    ),
    (
        "Neural Pathway",
        "Information moves through interconnected neural circuits rather than a single isolated brain region.",
    ),
    (
        "Neuron",
        "Neurons are electrically excitable cells that communicate through changes in membrane potential and chemical signalling.",
    ),
    (
        "Dendrites",
        "Dendrites receive synaptic inputs from other neurons and contribute to integrating information.",
    ),
    (
        "Axon",
        "The axon carries electrical signals away from the neuron's cell body toward downstream targets.",
    ),
    (
        "Myelin",
        "Myelin increases the efficiency and speed of signal propagation along many axons.",
    ),
    (
        "Electrical Signal",
        "Action potentials are rapid changes in membrane voltage that propagate along the axon.",
    ),
    (
        "Synapse",
        "Synapses are specialised communication sites where one neuron influences another cell.",
    ),
    (
        "Neurotransmitter",
        "Neurotransmitters are chemical messengers released at many synapses to influence target cells.",
    ),
    (
        "Cognition & Behaviour",
        "Networks of interacting brain systems contribute to attention, learning, memory, decision-making and behaviour.",
    ),
]

EQUIPMENT = [
    "EEG Scanner",
    "Eye Tracker",
    "Reaction-Time Monitor",
    "Auditory Attention Station",
    "Cognitive Task Screen",
    "Physiological Monitor",
]

EXPERIMENTS = [
    {
        "name": "Working Memory",
        "description": "Remember the sequence and reproduce it after a short delay.",
        "sequence": ["7", "2", "9", "4", "1", "8"],
    },
    {
        "name": "Attention",
        "description": "Identify the target stimulus while ignoring distractors.",
        "sequence": ["TARGET", "DISTRACTOR", "DISTRACTOR", "TARGET"],
    },
    {
        "name": "Decision Making",
        "description": "Choose between immediate and delayed reward.",
        "sequence": ["Rs 1,000 now", "Rs 1,500 in 30 days"],
    },
    {
        "name": "Cognitive Control",
        "description": "Respond according to the task rule rather than the most automatic response.",
        "sequence": ["LEFT", "RIGHT", "LEFT", "RIGHT"],
    },
    {
        "name": "Cognitive Flexibility",
        "description": "Switch between two task rules.",
        "sequence": ["COLOR", "SHAPE", "COLOR", "SHAPE"],
    },
]

MOODS = {
    "Positive / Happy": "😊",
    "Calm": "😌",
    "Neutral": "😐",
    "Worried": "😟",
    "Low / Sad": "😔",
    "Frustrated": "😣",
    "Tired": "😴",
}

BOOK = [
    {
        "title": "Cognitive Neuroscience of Working Memory",
        "authors": "Educational research topic",
        "abstract": "Working memory refers to temporary maintenance and manipulation of information. It depends on interactions between frontal, parietal and subcortical systems.",
        "finding": "Working memory is best understood as a distributed network function rather than the activity of a single brain region.",
        "source": "PubMed / primary literature should be checked before citing a specific study.",
    },
    {
        "title": "Attention and Cognitive Control",
        "authors": "Educational research topic",
        "abstract": "Attention involves selecting information for enhanced processing while cognitive control helps regulate behaviour according to current goals.",
        "finding": "Attention and control depend on interacting neural systems whose activity changes with task demands.",
        "source": "PubMed / primary literature should be checked before citing a specific study.",
    },
    {
        "title": "Reward and Decision Making",
        "authors": "Educational research topic",
        "abstract": "Decision-making can involve reward valuation, learning, uncertainty and executive control.",
        "finding": "Choices emerge from interactions among valuation, learning and control systems.",
        "source": "PubMed / primary literature should be checked before citing a specific study.",
    },
]

# -----------------------------
# HELPERS
# -----------------------------

def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


API_KEY = get_api_key()

client = None

if genai is not None and API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception:
        client = None


def ask_ai(prompt):
    if client is None:
        return (
            "Ayna AI is currently unavailable. "
            "Please check that GEMINI_API_KEY is configured in Streamlit Secrets."
        )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if response and getattr(response, "text", None):
            return response.text

    except Exception as e:
        return f"Ayna could not respond right now. Please try again. ({type(e).__name__})"

    return "Ayna could not generate a response."


def ask_ai_audio(audio_bytes, prompt):
    if client is None or types is None:
        return "Ayna AI audio analysis is unavailable right now."

    try:
        part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type="audio/wav",
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                part,
                prompt,
            ],
        )

        if response and getattr(response, "text", None):
            return response.text

    except Exception as e:
        return f"Ayna could not analyse the voice right now. ({type(e).__name__})"

    return "No voice analysis was returned."


def speak_button(text, key):
    safe_text = (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    html = f"""
    <button
        onclick="speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(`{safe_text}`);
        u.lang='en-US';
        speechSynthesis.speak(u);"
        style="
        width:100%;
        padding:10px 14px;
        border-radius:12px;
        border:1px solid rgba(150,180,220,.25);
        background:#102238;
        color:white;
        cursor:pointer;
        font-weight:600;
        "
    >
        🔊 Ayna Voice
    </button>
    """

    st.components.v1.html(html, height=55)


def record_audio(label="🎙️ Record Voice"):
    try:
        return st.audio_input(label)
    except Exception:
        st.info("Voice recording is not available in this Streamlit version.")
        return None


def show_video(path, autoplay=False, loop=False):
    if path is None or not Path(path).exists():
        return False

    data = Path(path).read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")

    auto = "autoplay" if autoplay else ""
    lp = "loop" if loop else ""

    html = f"""
    <video
        controls
        {auto}
        {lp}
        playsinline
        style="width:100%; border-radius:18px; max-height:520px;"
    >
        <source src="data:video/mp4;base64,{encoded}" type="video/mp4">
    </video>
    """

    st.components.v1.html(html, height=540)
    return True


def ayna_reboot_welcome():
    st.markdown(
        """
        <div class="card">
            <div class="section-title">🤖 Ayna is ready</div>
            <p class="muted">
            Welcome to NeuroLens — an interactive cognitive neuroscience
            environment for exploring the brain, cognition and behaviour.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    welcome = (
        "Welcome to NeuroLens! I'm Ayna, your cognitive neuroscience "
        "lab assistant. Let's explore the brain, behaviour, and cognition together."
    )

    if ROBOT_IMAGE.exists():
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(str(ROBOT_IMAGE), use_container_width=True)

        with col2:
            st.markdown("### 👋 Welcome")
            st.write(welcome)
            speak_button(welcome, "welcome_voice")
    else:
        st.markdown(f"### 👋 {welcome}")
        speak_button(welcome, "welcome_voice")

    if REBOOT_VIDEO:
        st.markdown("### 🎬 Ayna Reboot")
        show_video(REBOOT_VIDEO, autoplay=False, loop=False)
    else:
        st.info(
            "Reboot video not found yet. Add a video named "
            "`ayna_reboot.mp4`, `ayna_welcome.mp4`, `reboot.mp4`, or `welcome.mp4`."
        )


# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:
    st.markdown("## 🧠 NEUROLENS")
    st.caption("Explore cognition, behavior & the brain")

    st.divider()

    st.markdown("### 🌐 Language")

    st.session_state.language = st.radio(
        "Choose language",
        ["English", "Roman English"],
        index=0 if st.session_state.language == "English" else 1,
        key="language_selector",
    )

    st.divider()

    pages = [
        "Welcome Reboot",
        "Cognitive Lab",
        "Brain Journey",
        "Brain Puzzle",
        "Mood & Behaviour",
        "Daily Experiment",
        "Research Book",
        "Ask Ayna",
        "Private Ask Ayna",
        "My Progress",
    ]

    for item in pages:
        if st.button(
            item,
            key=f"sidebar_{item}",
            use_container_width=True,
        ):
            st.session_state.page = item
            st.rerun()

    st.divider()

    if st.button(
        "🔄 Reboot Ayna",
        key="reboot_button",
        use_container_width=True,
    ):
        st.session_state.page = "Welcome Reboot"
        st.rerun()


# -----------------------------
# HEADER
# -----------------------------

st.markdown(
    """
    <div class="main-title">NEUROLENS</div>
    <div class="subtitle">Explore cognition, behavior & the brain</div>
    """,
    unsafe_allow_html=True,
)

st.divider()

page = st.session_state.page


# -----------------------------
# WELCOME
# -----------------------------

if page == "Welcome Reboot":

    ayna_reboot_welcome()

    st.markdown("### 🚀 Explore NeuroLens")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="small-card">
            <h4>🧪 Cognitive Lab</h4>
            <p class="muted">Run educational cognitive experiments.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="small-card">
            <h4>🧠 Brain Journey</h4>
            <p class="muted">Explore the brain from systems to synapses.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="small-card">
            <h4>🔬 Research Book</h4>
            <p class="muted">Explore neuroscience research topics.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------
# COGNITIVE LAB
# -----------------------------

elif page == "Cognitive Lab":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">🧪 Interactive Cognitive Neuroscience Lab</div>
        <p class="muted">
        Choose your researcher character, select laboratory equipment,
        and perform an educational cognitive experiment.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.character = st.selectbox(
            "👤 Choose Character",
            ["Nova", "Mira", "Ray", "Zara"],
            index=["Nova", "Mira", "Ray", "Zara"].index(
                st.session_state.character
            ),
        )

    with col2:
        st.session_state.selected_equipment = st.selectbox(
            "🔬 Choose Equipment",
            EQUIPMENT,
            index=EQUIPMENT.index(st.session_state.selected_equipment),
        )

    st.markdown("### 🎬 Lab Environment")

    if LAB_VIDEO.exists():
        show_video(LAB_VIDEO, autoplay=False, loop=True)
    else:
        st.info(
            "Cognitive Lab video not found. "
            "Keep `cognitive_lab_brain.mp4` in the project root."
        )

    st.markdown("### 🧑‍🔬 Researcher")

    st.success(
        f"{st.session_state.character} is ready at the "
        f"{st.session_state.selected_equipment}."
    )

    if st.button(
        "▶️ Start Today's Experiment",
        key="start_lab_experiment",
        use_container_width=True,
    ):
        st.session_state.page = "Daily Experiment"
        st.rerun()

    experiment = random.choice(EXPERIMENTS)

    st.markdown("### 🧠 Suggested Experiment")

    st.markdown(
        f"""
        <div class="small-card">
        <h4>{experiment["name"]}</h4>
        <p>{experiment["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    explanation = (
        f"Ayna says: Today {st.session_state.character} is using the "
        f"{st.session_state.selected_equipment} to explore {experiment['name']}."
    )

    st.write(explanation)
    speak_button(explanation, "lab_voice")


# -----------------------------
# BRAIN JOURNEY
# -----------------------------

elif page == "Brain Journey":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">🧠 Brain Journey</div>
        <p class="muted">
        Move from the whole brain toward neurons, signalling and cognition.
        Each stage focuses on a different biological level.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stage_names = [x[0] for x in BRAIN_STAGES]

    selected_stage = st.selectbox(
        "Choose a stage",
        stage_names,
        key="brain_stage_selector",
    )

    index = stage_names.index(selected_stage)

    title, explanation = BRAIN_STAGES[index]

    st.progress((index + 1) / len(BRAIN_STAGES))

    c1, c2 = st.columns([1, 2])

    with c1:
        if BRAIN_IMAGE.exists():
            st.image(str(BRAIN_IMAGE), use_container_width=True)
        elif BRAIN_VIDEO.exists():
            show_video(BRAIN_VIDEO)
        else:
            st.markdown("## 🧠")

    with c2:
        st.markdown(f"### {title}")
        st.write(explanation)

        ayna_text = (
            f"Ayna explains: At the {title} stage, "
            f"we are looking at this level of brain organisation. "
            f"{explanation}"
        )

        speak_button(ayna_text, f"brain_voice_{index}")

        st.markdown("#### 💬 Ask Ayna about this stage")

        stage_question = st.text_input(
            "Your question",
            key=f"stage_question_{index}",
        )

        if st.button(
            "Ask Ayna",
            key=f"stage_ask_{index}",
        ):
            if stage_question.strip():
                prompt = f"""
                You are Ayna, a cognitive neuroscience educational assistant.

                Current brain journey stage:
                {title}

                Scientific explanation:
                {explanation}

                User question:
                {stage_question}

                Answer accurately and simply.
                Do not diagnose disease.
                Do not claim that a simple educational task measures brain activity.
                """
                answer = ask_ai(prompt)
                st.write(answer)
                speak_button(answer, f"stage_answer_voice_{index}")


# -----------------------------
# BRAIN PUZZLE
# -----------------------------

elif page == "Brain Puzzle":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">🧩 Brain Puzzle</div>
        <p class="muted">
        Drag the pieces to solve the brain image puzzle.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    size = st.selectbox(
        "Puzzle level",
        [3, 4, 5],
        format_func=lambda x: f"{x} × {x}",
        key="puzzle_size",
    )

    image_src = ""

    if BRAIN_IMAGE.exists():
        raw = BRAIN_IMAGE.read_bytes()
        encoded = base64.b64encode(raw).decode("utf-8")
        image_src = f"data:image/png;base64,{encoded}"

    if image_src:

        puzzle_html = f"""
        <div id="puzzle-container"></div>

        <div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">
            <button id="resetPuzzle"
                style="padding:10px 15px;border-radius:10px;border:none;cursor:pointer;">
                🔄 Reset
            </button>
            <span id="puzzleStatus"
                style="padding:10px 15px;">
                Moves: 0 | Correct: 0
            </span>
        </div>

        <script>
        const size = {size};
        const image = "{image_src}";

        let tiles = [];
        let moves = 0;

        const container = document.getElementById("puzzle-container");
        const status = document.getElementById("puzzleStatus");

        function shuffle(array) {{
            for (let i = array.length - 1; i > 0; i--) {{
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }}
        }}

        function createPuzzle() {{
            container.innerHTML = "";
            moves = 0;

            tiles = Array.from(
                {{length: size * size}},
                (_, i) => i
            );

            shuffle(tiles);

            container.style.display = "grid";
            container.style.gridTemplateColumns =
                `repeat(${{size}}, 1fr)`;
            container.style.gap = "4px";
            container.style.maxWidth = "520px";
            container.style.margin = "auto";

            tiles.forEach((originalIndex, position) => {{
                const tile = document.createElement("div");

                const row = Math.floor(originalIndex / size);
                const col = originalIndex % size;

                tile.draggable = true;

                tile.style.aspectRatio = "1 / 1";
                tile.style.backgroundImage = `url('${{image}}')`;
                tile.style.backgroundSize = `${{size * 100}}% ${{size * 100}}%`;
                tile.style.backgroundPosition =
                    `${{col * 100 / (size - 1)}}% ${{row * 100 / (size - 1)}}%`;
                tile.style.borderRadius = "7px";
                tile.style.cursor = "grab";
                tile.dataset.position = position;

                tile.addEventListener("dragstart", dragStart);
                tile.addEventListener("dragover", dragOver);
                tile.addEventListener("drop", drop);

                container.appendChild(tile);
            }});

            updateStatus();
        }}

        let dragged = null;

        function dragStart(e) {{
            dragged = e.currentTarget;
        }}

        function dragOver(e) {{
            e.preventDefault();
        }}

        function drop(e) {{
            e.preventDefault();

            const target = e.currentTarget;

            if (!dragged || dragged === target) return;

            const draggedIndex = Number(dragged.dataset.position);
            const targetIndex = Number(target.dataset.position);

            [tiles[draggedIndex], tiles[targetIndex]] =
                [tiles[targetIndex], tiles[draggedIndex]];

            moves++;
            createFromTiles();
        }}

        function createFromTiles() {{
            const children = [...container.children];

            children.forEach((tile, position) => {{
                const originalIndex = tiles[position];

                const row = Math.floor(originalIndex / size);
                const col = originalIndex % size;

                tile.style.backgroundPosition =
                    `${{col * 100 / (size - 1)}}% ${{row * 100 / (size - 1)}}%`;
            }});

            updateStatus();
        }}

        function updateStatus() {{
            let correct = 0;

            tiles.forEach((value, index) => {{
                if (value === index) correct++;
            }});

            status.textContent =
                `Moves: ${{moves}} | Correct: ${{correct}}/${{size * size}}`;

            if (correct === size * size) {{
                status.textContent += " | 🎉 Complete!";
            }}
        }}

        document.getElementById("resetPuzzle")
            .addEventListener("click", createPuzzle);

        createPuzzle();
        </script>
        """

        st.components.v1.html(
            puzzle_html,
            height=650,
        )

    else:
        st.warning(
            "Brain image not found. Please keep `brain.png` in the project root."
        )

    st.info(
        "Puzzle is an educational interaction. A score here does not represent "
        "clinical or diagnostic cognitive ability."
    )

# -----------------------------
# MOOD & BEHAVIOUR
# -----------------------------

elif page == "Mood & Behaviour":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">🎙️ AI Mood & Behaviour</div>
        <p class="muted">
        Explore broad emotional signals from your voice or text.
        This is not a medical or psychiatric diagnosis.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎙️ Voice")

    audio = record_audio("🎙️ Record your voice")

    if audio is not None:

        st.audio(audio)

        if st.button(
            "📤 Send Voice",
            key="send_voice",
            use_container_width=True,
        ):

            audio_bytes = audio.getvalue()

            analysis_prompt = """
            You are Ayna, an educational cognitive neuroscience assistant.

            Analyse the user's voice broadly and cautiously.

            Do NOT diagnose depression, anxiety, trauma, psychiatric disorders,
            personality disorders, or any medical condition.

            Give only a broad conversational impression such as:
            Positive / Happy, Calm, Neutral, Worried, Low / Sad,
            Frustrated, or Tired.

            Explain that voice-based inference is uncertain and affected by
            context, recording quality, language and individual differences.

            Return:
            1. Broad mood
            2. Short explanation
            3. Supportive non-clinical message
            """

            result = ask_ai_audio(
                audio_bytes,
                analysis_prompt,
            )

            st.session_state.mood_result = result

            st.markdown("### 🧠 Ayna's Observation")
            st.write(result)

            speak_button(
                result,
                "mood_voice_result",
            )

    st.divider()

    st.markdown("### ✍️ Text")

    mood_text = st.text_area(
        "How are you feeling or what happened?",
        key="mood_text",
    )

    if st.button(
        "📤 Send Text",
        key="send_text",
        use_container_width=True,
    ):

        if mood_text.strip():

            prompt = f"""
            You are Ayna, an educational cognitive neuroscience assistant.

            User text:
            {mood_text}

            Identify only a broad conversational emotional category.

            Choose one:
            Positive / Happy
            Calm
            Neutral
            Worried
            Low / Sad
            Frustrated
            Tired

            Do not diagnose a medical or psychiatric condition.
            Explain that this is an uncertain text-based interpretation.
            """

            result = ask_ai(prompt)

            st.session_state.mood_result = result

            st.markdown("### 🧠 Ayna's Observation")
            st.write(result)

            speak_button(
                result,
                "mood_text_voice",
            )

    st.caption(
        "Important: Mood inference from voice or text is probabilistic and "
        "should not be treated as a clinical assessment."
    )


# -----------------------------
# DAILY EXPERIMENT
# -----------------------------

elif page == "Daily Experiment":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">🧪 Daily Cognitive Experiment</div>
        <p class="muted">
        A short educational task for exploring cognition.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    experiment = st.selectbox(
        "Choose experiment",
        EXPERIMENTS,
        format_func=lambda x: x["name"],
        key="daily_experiment",
    )

    st.markdown(f"### {experiment['name']}")
    st.write(experiment["description"])

    if experiment["name"] == "Working Memory":

        st.info(
            "Study this sequence for a few seconds, then enter it from memory."
        )

        sequence = "".join(experiment["sequence"])

        st.code(sequence)

        if st.button(
            "Hide Sequence",
            key="hide_sequence",
        ):
            st.session_state["wm_hidden"] = True

        answer = st.text_input(
            "Enter the sequence",
            key="wm_answer",
        )

        if st.button(
            "Check Memory",
            key="check_memory",
        ):

            correct = answer.replace(" ", "") == sequence

            if correct:
                st.success("🎉 Correct!")
                st.session_state.experiment_score += 1
            else:
                st.error("Not quite. Try another round.")

            st.session_state.completed_experiments += 1

    elif experiment["name"] == "Decision Making":

        choice = st.radio(
            "Which would you choose?",
            experiment["sequence"],
            key="decision_choice",
        )

        if st.button(
            "Submit Decision",
            key="submit_decision",
        ):

            st.success(
                "Your choice has been recorded as an educational "
                "decision-making response."
            )

            st.session_state.completed_experiments += 1

    elif experiment["name"] == "Attention":

        target = st.select_slider(
            "Which stimulus would you focus on?",
            options=[
                "DISTRACTOR",
                "TARGET",
            ],
            key="attention_answer",
        )

        if st.button(
            "Submit Attention",
            key="attention_submit",
        ):

            if target == "TARGET":
                st.success("Correct target selection.")
                st.session_state.experiment_score += 1
            else:
                st.warning("Try focusing on the task target.")

            st.session_state.completed_experiments += 1

    else:

        answer = st.radio(
            "Choose the response that follows the task rule.",
            ["Option A", "Option B"],
            key=f"generic_answer_{experiment['name']}",
        )

        if st.button(
            "Submit Experiment",
            key=f"generic_submit_{experiment['name']}",
        ):

            st.success(
                "Response recorded. This educational task does not "
                "constitute a validated neuropsychological test."
            )

            st.session_state.completed_experiments += 1

    st.divider()

    analysis_prompt = st.text_area(
        "Optional: Ask Ayna to explain what this experiment explores.",
        key="experiment_analysis_question",
    )

    if st.button(
        "🤖 Ask Ayna",
        key="experiment_ask_ayna",
    ):

        if analysis_prompt.strip():

            prompt = f"""
            Explain the cognitive neuroscience behind this educational task.

            Experiment:
            {experiment["name"]}

            User question:
            {analysis_prompt}

            Be scientifically careful.
            Do not claim the task diagnoses anything.
            Do not claim the result measures a specific brain region directly.
            """

            answer = ask_ai(prompt)

            st.write(answer)

            speak_button(
                answer,
                "experiment_answer_voice",
            )

    st.info(
        "Educational experiment only. Publishable human research requires "
        "a predefined protocol, validated measures, consent, ethics approval "
        "where applicable, and appropriate statistical analysis."
    )
    # -----------------------------
# RESEARCH BOOK
# -----------------------------

elif page == "Research Book":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">📖 Research Book</div>
        <p class="muted">
        Explore neuroscience topics and research concepts.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    topic_names = [item["title"] for item in BOOK]

    selected_topic = st.selectbox(
        "📚 Choose a topic",
        topic_names,
        key="research_topic",
    )

    article = next(
        item for item in BOOK
        if item["title"] == selected_topic
    )

    st.markdown("### 📝 Article")

    st.markdown(
        f"""
        <div class="card">
        <h3>{article["title"]}</h3>
        <p><b>Authors:</b> {article["authors"]}</p>
        <hr>
        <p><b>Abstract</b></p>
        <p>{article["abstract"]}</p>
        <p><b>Key finding</b></p>
        <p>{article["finding"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🔬 Research Source")
    st.write(article["source"])

    st.info(
        "For a real literature review, verify the paper directly through "
        "PubMed, Europe PMC, the journal website, DOI record, or another "
        "authoritative research database. NeuroLens should not invent citations."
    )

    research_question = st.text_input(
        "💬 Ask Ayna to explain this research topic",
        key="research_question",
    )

    if st.button(
        "Ask Ayna",
        key="research_ask",
        use_container_width=True,
    ):

        if research_question.strip():

            prompt = f"""
            You are Ayna, a cognitive neuroscience educational assistant.

            Research topic:
            {article["title"]}

            Abstract:
            {article["abstract"]}

            Key finding:
            {article["finding"]}

            User question:
            {research_question}

            Explain clearly for a learner/researcher.
            Separate established evidence from interpretation.
            Do not invent citations or study results.
            """

            answer = ask_ai(prompt)

            st.write(answer)

            speak_button(
                answer,
                "research_voice",
            )


# -----------------------------
# ASK AYNA
# -----------------------------

elif page == "Ask Ayna":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">🤖 Ask Ayna</div>
        <p class="muted">
        Your general cognitive neuroscience AI assistant.
        Ask about the brain, behaviour, cognition, learning,
        decisions, attention, memory and related topics.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for message in st.session_state.messages:

        role = message.get("role", "assistant")
        text = message.get("text", "")

        with st.chat_message(role):
            st.write(text)

            if role == "assistant":
                speak_button(
                    text,
                    f"chat_voice_{len(text)}",
                )

    chat_text = st.chat_input(
        "Ask Ayna anything about cognition, brain or behaviour..."
    )

    if chat_text:

        st.session_state.messages.append(
            {
                "role": "user",
                "text": chat_text,
            }
        )

        prompt = f"""
        You are Ayna, a cognitive neuroscience and AI educational assistant.

        Language preference:
        {st.session_state.language}

        User:
        {chat_text}

        Respond accurately and naturally.

        You may discuss:
        - cognitive neuroscience
        - brain systems
        - cognition
        - attention
        - memory
        - learning
        - decision making
        - behaviour
        - AI and human cognition
        - consciousness as a scientific topic

        Do not claim to be a doctor or therapist.
        Do not diagnose mental or neurological disorders.
        Do not present uncertain inferences as facts.
        """

        answer = ask_ai(prompt)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "text": answer,
            }
        )

        st.rerun()

    st.markdown("### 🎙️ Voice Ask Ayna")

    voice = record_audio(
        "🎙️ Record your question"
    )

    if voice is not None:

        st.audio(voice)

        if st.button(
            "📤 Send Voice to Ayna",
            key="ask_ayna_voice",
            use_container_width=True,
        ):

            prompt = f"""
            You are Ayna, a cognitive neuroscience educational assistant.

            Listen to the user's recorded question and answer it.

            User language:
            {st.session_state.language}

            Give a scientifically responsible answer.
            Do not diagnose.
            Do not claim to be a therapist or doctor.
            """

            answer = ask_ai_audio(
                voice.getvalue(),
                prompt,
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "text": answer,
                }
            )

            st.write(answer)

            speak_button(
                answer,
                "ask_ayna_voice_answer",
            )

    if st.button(
        "🗑️ Clear Ask Ayna Chat",
        key="clear_ask_ayna",
    ):

        st.session_state.messages = []
        st.rerun()


# -----------------------------
# PRIVATE ASK AYNA
# -----------------------------

elif page == "Private Ask Ayna":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">🔐 Private Ask Ayna</div>
        <p class="muted">
        A separate private conversation area.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.private_unlocked:

        st.markdown("### 🔑 Enter PIN")

        pin = st.text_input(
            "Private PIN",
            type="password",
            key="private_pin",
        )

        if st.button(
            "🔓 Unlock",
            key="private_unlock",
            use_container_width=True,
        ):

            verified = False

            try:
                from modules.security import verify_pin

                verified = verify_pin(pin)

            except Exception:
                verified = pin == "2026"

            if verified:

                st.session_state.private_unlocked = True
                st.rerun()

            else:
                st.error("Incorrect PIN.")

        st.caption(
            "Demo fallback PIN: 2026. For real private data, use proper "
            "authentication, encryption and a secure backend."
        )

    else:

        st.success("🔓 Private session unlocked.")

        for message in st.session_state.private_messages:

            role = message.get("role", "assistant")
            text = message.get("text", "")

            with st.chat_message(role):
                st.write(text)

                if role == "assistant":
                    speak_button(
                        text,
                        f"private_voice_{len(text)}",
                    )

        private_text = st.chat_input(
            "Write a private message to Ayna...",
            key="private_chat",
        )

        if private_text:

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "text": private_text,
                }
            )

            prompt = f"""
            You are Ayna in a private educational conversation.

            User message:
            {private_text}

            Respond naturally and safely.

            Do not claim to be a therapist or doctor.
            Do not diagnose.
            """

            answer = ask_ai(prompt)

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "text": answer,
                }
            )

            st.rerun()

        st.markdown("### 🎙️ Private Voice")

        private_voice = record_audio(
            "🎙️ Record private question"
        )

        if private_voice is not None:

            st.audio(private_voice)

            if st.button(
                "📤 Send Private Voice",
                key="private_voice_send",
                use_container_width=True,
            ):

                answer = ask_ai_audio(
                    private_voice.getvalue(),
                    """
                    You are Ayna in a private educational conversation.
                    Answer the user's question naturally.
                    Do not diagnose or claim to be a therapist or doctor.
                    """,
                )

                st.session_state.private_messages.append(
                    {
                        "role": "assistant",
                        "text": answer,
                    }
                )

                st.write(answer)

                speak_button(
                    answer,
                    "private_voice_answer",
                )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "🗑️ Clear Private Chat",
                key="clear_private",
                use_container_width=True,
            ):

                st.session_state.private_messages = []
                st.rerun()

        with c2:

            if st.button(
                "🔒 Lock Private Area",
                key="lock_private",
                use_container_width=True,
            ):

                st.session_state.private_unlocked = False
                st.rerun()

        st.warning(
            "This session PIN is not the same as full end-to-end encryption. "
            "Do not store highly sensitive information here unless a secure "
            "backend and proper authentication are implemented."
        )


# -----------------------------
# MY PROGRESS
# -----------------------------

elif page == "My Progress":

    st.markdown(
        """
        <div class="card">
        <div class="section-title">📊 My Progress</div>
        <p class="muted">
        Track your NeuroLens activity during the current session.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "🧪 Experiments",
            st.session_state.completed_experiments,
        )

    with c2:
        st.metric(
            "🏆 Experiment Score",
            st.session_state.experiment_score,
        )

    with c3:
        st.metric(
            "🧩 Puzzle Score",
            st.session_state.puzzle_score,
        )

    with c4:
        st.metric(
            "💬 Ask Ayna Messages",
            len(st.session_state.messages),
        )

    st.divider()

    st.markdown("### 📈 Activity Overview")

    if plotly_go is not None:

        labels = [
            "Experiments",
            "Experiment Score",
            "Puzzle Score",
            "Ask Ayna Messages",
        ]

        values = [
            st.session_state.completed_experiments,
            st.session_state.experiment_score,
            st.session_state.puzzle_score,
            len(st.session_state.messages),
        ]

        fig = plotly_go.Figure(
            data=[
                plotly_go.Bar(
                    x=labels,
                    y=values,
                )
            ]
        )

        fig.update_layout(
            title="NeuroLens Activity",
            xaxis_title="Activity",
            yaxis_title="Count",
            template="plotly_dark",
            height=420,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:
        st.info(
            "Plotly is not available. Add plotly to requirements.txt."
        )

    st.markdown("### 🧠 Researcher Note")

    st.write(
        "Your NeuroLens session tracks educational interactions. "
        "These scores are not clinical cognitive measurements."
    )

    st.caption(
        "Permanent cross-device history requires a database/backend. "
        "The current version keeps progress primarily in the Streamlit session."
    )


# -----------------------------
# FOOTER
# -----------------------------

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        padding:18px;
        color:#8fa0b7;
        font-size:14px;
    ">
        <b>NEUROLENS</b><br>
        Cognitive Neuroscience • Brain • Behaviour • AI<br>
        Created by Ayna Jaffri
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "NeuroLens is an educational platform. Its interactive activities "
    "should not be treated as medical diagnosis or validated clinical testing."
)
    
