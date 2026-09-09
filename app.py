import os
import json
import random
import html
import streamlit as st

# ============================================================
# NEUROLENS
# Cognitive Neuroscience × AI × Behaviour
# Created by Ayna Jaffri
# ============================================================

st.set_page_config(
    page_title="NEUROLENS — Cognitive Neuroscience Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "Home",
    "ai_requests": 0,
    "experiment_score": 0,
    "exercise_score": 0,
    "puzzle_score": 0,
    "puzzle_moves": 0,
    "puzzle_completed": False,
    "streak": 1,
    "private_unlocked": False,
    "private_pin": "",
    "private_messages": [],
    "ask_messages": [],
    "behaviour_result": None,
    "lab_result": None,
    "journey_stage": 0,
    "selected_character": "Ayna",
    "research_mode": False,
    "exercise_level": 1,
    "exercise_index": 0,
    "memory_sequence": [],
    "memory_answer": "",
    "attention_target": "",
    "puzzle_level": 3,
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

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(40,180,255,.10), transparent 30%),
        radial-gradient(circle at 85% 80%, rgba(100,80,255,.08), transparent 30%),
        #050911;
    color: #eef6ff;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 4rem;
    max-width: 1400px;
}

h1, h2, h3 {
    color: #f4f9ff;
}

.neuro-card {
    background: rgba(10,18,31,.82);
    border: 1px solid rgba(80,180,255,.20);
    border-radius: 20px;
    padding: 24px;
    margin: 12px 0;
    box-shadow: 0 8px 30px rgba(0,0,0,.25);
}

.lab-card {
    background:
        linear-gradient(145deg, rgba(10,27,42,.95), rgba(7,13,24,.95));
    border: 1px solid rgba(64,200,255,.25);
    border-radius: 24px;
    padding: 28px;
    box-shadow: inset 0 0 30px rgba(0,180,255,.035),
                0 10px 40px rgba(0,0,0,.30);
}

.glow-title {
    font-size: 2.7rem;
    font-weight: 800;
    letter-spacing: -1px;
}

.subtitle {
    color: #a9bfd4;
    font-size: 1.05rem;
}

.robot {
    width: 145px;
    height: 145px;
    margin: auto;
    border-radius: 38px;
    background: linear-gradient(145deg,#f9fcff,#b8c8d8);
    border: 4px solid #d9f4ff;
    box-shadow:
        0 0 18px rgba(60,210,255,.45),
        inset 0 -12px 25px rgba(40,80,110,.15);
    display:flex;
    align-items:center;
    justify-content:center;
    position:relative;
    animation: floatRobot 3s ease-in-out infinite;
}

.robot-face {
    width: 100px;
    height: 72px;
    border-radius: 25px;
    background: #07111c;
    border: 2px solid #5de5ff;
    display:flex;
    align-items:center;
    justify-content:center;
    gap:18px;
    box-shadow: 0 0 18px rgba(0,220,255,.30);
}

.eye {
    width: 20px;
    height: 30px;
    border-radius: 50%;
    background: #69eaff;
    box-shadow: 0 0 14px #38dfff;
}

@keyframes floatRobot {
    0%,100% { transform:translateY(0); }
    50% { transform:translateY(-8px); }
}

.brain-display {
    min-height: 260px;
    border-radius: 25px;
    border: 1px solid rgba(70,210,255,.25);
    background:
        radial-gradient(circle at 50% 50%, rgba(50,210,255,.15), transparent 35%),
        #07101b;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    position:relative;
    overflow:hidden;
}

.brain-symbol {
    font-size: 120px;
    filter: drop-shadow(0 0 18px rgba(70,220,255,.55));
    animation: pulseBrain 2.2s infinite;
}

@keyframes pulseBrain {
    0%,100% { transform:scale(1); opacity:.85; }
    50% { transform:scale(1.08); opacity:1; }
}

.stage {
    background: rgba(15,28,44,.75);
    border: 1px solid rgba(90,200,255,.18);
    border-radius: 16px;
    padding: 15px;
    text-align:center;
    margin-bottom:10px;
}

.metric {
    background: rgba(15,25,39,.8);
    border-radius: 15px;
    padding: 15px;
    text-align:center;
}

.small-muted {
    color:#8fa8bd;
    font-size:.88rem;
}

.result-box {
    border-radius:20px;
    padding:22px;
    background:rgba(13,25,40,.9);
    border:1px solid rgba(75,205,255,.22);
}

.emoji-result {
    font-size: 65px;
    text-align:center;
}

.book {
    background: linear-gradient(135deg,#f3ead5,#d7c49e);
    color:#2b2115;
    border-radius:24px;
    padding:28px;
    min-height:230px;
    box-shadow:0 10px 30px rgba(0,0,0,.25);
}

.book h3 {
    color:#2b2115;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def go_to(page):
    st.session_state.page = page
    st.rerun()


def record_ai_request():
    st.session_state.ai_requests += 1


def speak(text, button_label="🔊 Ayna Voice"):
    """
    Browser speech synthesis.
    Requires the user to interact with the page/browser.
    """
    safe_text = json.dumps(str(text))

    components_html = f"""
    <button onclick='
        const msg = new SpeechSynthesisUtterance({safe_text});
        msg.lang = "en-US";
        msg.rate = 0.92;
        msg.pitch = 1.04;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(msg);
    '
    style="
        width:100%;
        border-radius:12px;
        border:1px solid rgba(80,210,255,.35);
        background:rgba(10,25,40,.9);
        color:#eaf9ff;
        padding:10px;
        cursor:pointer;
        font-weight:600;">
        {button_label}
    </button>
    """

    st.components.v1.html(components_html, height=55)


def ayna_reply(text, emoji="🤖"):
    st.markdown(
        f"""
        <div class="result-box">
            <div style="font-size:38px;">{emoji}</div>
            <b>Ayna</b>
            <p>{html.escape(text)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    speak(text)


# ============================================================
# AI
# ============================================================

def ask_ai(prompt, system="You are Ayna, an educational cognitive neuroscience AI assistant."):
    record_ai_request()

    api_key = None

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return (
            "Ayna AI is currently running in educational fallback mode. "
            "You can still explore the neuroscience content and cognitive exercises."
        )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system}\n\nUser:\n{prompt}",
        )

        if response and getattr(response, "text", None):
            return response.text.strip()

    except Exception:
        return (
            "I couldn't connect to the AI service right now. "
            "Please continue exploring the lab — your local cognitive activities are still available."
        )

    return "Ayna is ready, but no AI response was returned."


# ============================================================
# Ayna INTRO
# ============================================================

def ayna_robot():
    st.markdown(
        """
        <div class="robot">
            <div class="robot-face">
                <div class="eye"></div>
                <div class="eye"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ayna_intro():
    ayna_robot()

    st.markdown(
        """
        <div style="text-align:center;">
            <h2>Hi, I'm Ayna 🤖</h2>
            <p class="subtitle">
            Your AI Lab Assistant for exploring cognition, behaviour,
            brain systems and neuroscience.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    intro = (
        "Hi, I'm Ayna. Welcome to NEUROLENS. "
        "Here you can explore the brain, run cognitive experiments, "
        "solve brain puzzles, train cognitive skills, explore research, "
        "and talk with me about neuroscience and behaviour."
    )

    if st.button("🔊 Introduce Ayna", use_container_width=True):
        speak(intro)


# ============================================================
# SIDEBAR
# ============================================================

PAGES = [
    "Home",
    "🧠 Explore Brain",
    "🔬 Cognitive Lab",
    "🧩 Brain Puzzle",
    "🎭 AI Mood & Behaviour",
    "⚡ Brain Exercises",
    "📖 Research Book",
    "💬 Ask Ayna",
    "🔐 Private Ask Ayna",
    "📊 My Progress",
]

with st.sidebar:
    st.markdown("## 🧠 NEUROLENS")
    st.caption("Cognitive Neuroscience Lab")

    for i, page in enumerate(PAGES):
        if st.button(
            page,
            key=f"navigation_{i}",
            use_container_width=True,
        ):
            go_to(page)

    st.markdown("---")
    st.caption("Created by Ayna Jaffri")


# ============================================================
# HOME
# ============================================================

def home_screen():

    st.markdown(
        """
        <div class="lab-card">
            <div class="glow-title">🧠 NEUROLENS</div>
            <div class="subtitle">
                Explore cognition, behaviour & the brain
            </div>
            <br>
            <div class="small-muted">
                An interactive cognitive neuroscience environment
                connecting brain science, behaviour, AI and learning.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    ayna_intro()

    st.markdown("### Enter the Lab")

    cols = st.columns(4)

    buttons = [
        ("🧠 Explore Brain", "🧠 Explore Brain"),
        ("🔬 Enter Cognitive Lab", "🔬 Cognitive Lab"),
        ("🧩 Brain Puzzle", "🧩 Brain Puzzle"),
        ("🎭 Mood & Behaviour", "🎭 AI Mood & Behaviour"),
        ("⚡ Brain Exercises", "⚡ Brain Exercises"),
        ("📖 Research Book", "📖 Research Book"),
        ("💬 Ask Ayna", "💬 Ask Ayna"),
        ("📊 My Progress", "📊 My Progress"),
    ]

    for i, (label, target) in enumerate(buttons):
        with cols[i % 4]:
            if st.button(label, key=f"home_{i}", use_container_width=True):
                go_to(target)

    st.markdown("---")

    st.markdown(
        """
        <div class="neuro-card">
        <h3>What can you explore?</h3>

        🧠 Brain anatomy & neural pathways<br>
        🔬 Cognitive experiments<br>
        🧩 Perception & reasoning puzzles<br>
        🎭 Mood & behaviour exploration<br>
        ⚡ Cognitive training<br>
        📖 Neuroscience research topics<br>
        🤖 AI-powered Ayna assistant<br>
        📊 Personal learning progress

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BRAIN JOURNEY
# ============================================================

BRAIN_STAGES = [
    (
        "Whole Brain",
        "The brain is a biological network containing billions of neurons "
        "that communicate through electrical and chemical signals.",
    ),
    (
        "Brain Region",
        "Different brain regions contribute to different functions, "
        "but most behaviour emerges from interacting networks rather than one isolated area.",
    ),
    (
        "Neural Circuit",
        "Neural circuits connect populations of neurons and allow information "
        "to flow between brain regions.",
    ),
    (
        "Neuron",
        "A neuron receives, integrates and transmits information through "
        "electrical and chemical signalling.",
    ),
    (
        "Dendrites",
        "Dendrites receive many incoming signals from other neurons.",
    ),
    (
        "Axon",
        "The axon carries electrical signals away from the neuron's cell body.",
    ),
    (
        "Myelin",
        "Myelin insulates many axons and can increase the speed and efficiency "
        "of signal transmission.",
    ),
    (
        "Electrical Signal",
        "An action potential is a rapid electrical event that travels along an axon.",
    ),
    (
        "Synapse",
        "At many synapses, one neuron communicates with another across a tiny gap.",
    ),
    (
        "Neurotransmitter",
        "Neurotransmitters are chemical messengers released by neurons "
        "that influence target cells.",
    ),
    (
        "Cognitive Function",
        "Networks of neural activity support attention, memory, decision-making, "
        "emotion, learning and other cognitive functions.",
    ),
]


def brain_screen():

    st.markdown("## 🧠 Inside-Brain Journey")

    stage_index = st.session_state.journey_stage
    title, explanation = BRAIN_STAGES[stage_index]

    st.markdown(
        f"""
        <div class="brain-display">
            <div>
                <div class="brain-symbol">🧠</div>
                <h2>{title}</h2>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress((stage_index + 1) / len(BRAIN_STAGES))

    st.markdown(f"### {title}")
    st.write(explanation)

    ayna_voice_text = (
        f"Welcome to the {title} stage of the brain journey. "
        f"{explanation}"
    )

    speak(ayna_voice_text)

    c1, c2, c3 = st.columns(3)

    with c1:
        if stage_index > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state.journey_stage -= 1
                st.rerun()

    with c2:
        if st.button("🔊 Ask Ayna about this stage", use_container_width=True):
            answer = ask_ai(
                f"Explain this neuroscience stage simply: {title}. "
                f"Context: {explanation}"
            )
            ayna_reply(answer)

    with c3:
        if stage_index < len(BRAIN_STAGES) - 1:
            if st.button("Enter deeper →", use_container_width=True):
                st.session_state.journey_stage += 1
                st.rerun()

    st.markdown("### Neural Journey")

    for i, (name, _) in enumerate(BRAIN_STAGES):
        marker = "🟢" if i <= stage_index else "⚪"
        st.markdown(
            f'<div class="stage">{marker} {name}</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# COGNITIVE LAB
# ============================================================

EXPERIMENTS = [
    {
        "name": "Working Memory",
        "question": "Remember the sequence: 7 — 2 — 9 — 4 — 6",
        "answer": "72946",
        "description": "Working memory temporarily maintains and manipulates information.",
    },
    {
        "name": "Attention",
        "question": "Which word is different? CAT — CAT — CAT — DOG — CAT",
        "answer": "DOG",
        "description": "Selective attention helps prioritize relevant information.",
    },
    {
        "name": "Decision Making",
        "question": "Option A gives 80% chance of 10 points. Option B gives 100% chance of 6 points. Which gives higher expected value?",
        "answer": "A",
        "description": "Decision-making can involve probability, reward and uncertainty.",
    },
    {
        "name": "Cognitive Control",
        "question": "If GREEN is written in red ink, which should you name: the word or the ink colour?",
        "answer": "INK",
        "description": "Cognitive control helps resolve competing responses.",
    },
]


def lab_screen():

    st.markdown("## 🔬 Cognitive Neuroscience Lab")

    st.markdown(
        """
        <div class="lab-card">
        <h3>Today's Cognitive Experiment</h3>
        <p>
        Choose a cognitive system and complete a short educational task.
        Your result is used for learning and progress tracking.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    character = st.selectbox(
        "Choose your lab character",
        ["Ayna", "Neuro Explorer", "Researcher", "Student"],
        index=0,
    )

    st.session_state.selected_character = character

    experiment = random.choice(EXPERIMENTS)

    st.markdown(f"### 🧪 {experiment['name']}")

    st.info(experiment["description"])

    st.markdown(
        f"""
        <div class="neuro-card">
        <h3>{experiment["question"]}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.text_input("Your answer", key="lab_answer")

    if st.button("Submit Experiment", use_container_width=True):

        if answer.strip().upper() == experiment["answer"].upper():
            st.session_state.experiment_score += 1
            result = "Correct — your response matched the expected answer."
            emoji = "🧠"
        else:
            result = (
                f"The expected answer was {experiment['answer']}. "
                "This task is an educational demonstration rather than a clinical test."
            )
            emoji = "🔬"

        st.session_state.lab_result = result

        st.markdown(
            f"""
            <div class="result-box">
            <div style="font-size:45px">{emoji}</div>
            <b>Ayna Lab Analysis</b>
            <p>{html.escape(result)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        speak(result)

        st.markdown("### 🧩 Follow-up Challenge")

        if experiment["name"] == "Working Memory":
            st.write("Try to remember this new sequence for 10 seconds:")
            st.code("3 — 8 — 1 — 5 — 9")

        elif experiment["name"] == "Attention":
            st.write("Count how many times the letter A appears:")
            st.code("A C A B D A F G A C B A")

        else:
            st.write(
                "Think about one factor that could change your answer "
                "if the situation became uncertain."
            )


# ============================================================
# BRAIN PUZZLE
# ============================================================

def puzzle_screen():

    st.markdown("## 🧩 Brain Puzzle")

    level = st.selectbox(
        "Puzzle Level",
        [3, 4, 5],
        index=0,
    )

    st.session_state.puzzle_level = level

    st.write(
        f"Arrange the numbers from 1 to {level * level} in the correct order."
    )

    size = level * level

    if "puzzle_tiles" not in st.session_state or (
        st.session_state.get("puzzle_size") != size
    ):
        tiles = list(range(1, size + 1))
        random.shuffle(tiles)
        st.session_state.puzzle_tiles = tiles
        st.session_state.puzzle_size = size
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_completed = False

    tiles = st.session_state.puzzle_tiles

    cols = st.columns(level)

    for i, tile in enumerate(tiles):

        with cols[i % level]:

            if st.button(
                str(tile),
                key=f"tile_{i}_{tile}",
                use_container_width=True,
            ):

                # Simple touch-friendly swap puzzle.
                if i > 0:
                    tiles[i], tiles[i - 1] = tiles[i - 1], tiles[i]
                    st.session_state.puzzle_moves += 1
                    st.rerun()

    if tiles == list(range(1, size + 1)):

        if not st.session_state.puzzle_completed:
            st.session_state.puzzle_completed = True
            st.session_state.puzzle_score += max(
                10,
                100 - st.session_state.puzzle_moves,
            )

        st.success("🎉 Puzzle completed!")
        st.balloons()

    st.markdown(
        f"""
        <div class="neuro-card">
        <b>Moves:</b> {st.session_state.puzzle_moves}
        &nbsp;&nbsp;&nbsp;
        <b>Score:</b> {st.session_state.puzzle_score}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 New Puzzle", use_container_width=True):
        st.session_state.puzzle_tiles = list(range(1, size + 1))
        random.shuffle(st.session_state.puzzle_tiles)
        st.session_state.puzzle_moves = 0
        st.session_state.puzzle_completed = False
        st.rerun()


# ============================================================
# MOOD & BEHAVIOUR
# ============================================================

MOODS = {
    "happy": ("😊", "Positive / Happy"),
    "calm": ("😌", "Calm"),
    "neutral": ("😐", "Neutral"),
    "worried": ("😟", "Worried"),
    "sad": ("😔", "Low / Sad"),
    "frustrated": ("😤", "Frustrated"),
    "tired": ("😴", "Tired"),
}


def estimate_mood(text):

    t = text.lower()

    tired_words = [
        "tired", "sleepy", "exhausted", "thak", "thaki",
        "neend", "soya", "sleep",
    ]

    worried_words = [
        "worried", "anxious", "stress", "stressed",
        "tension", "fear", "afraid", "fikar",
    ]

    sad_words = [
        "sad", "upset", "cry", "alone", "low",
        "depressed", "hurt", "dukhi",
    ]

    frustrated_words = [
        "angry", "frustrated", "annoyed", "irritated",
        "gussa", "tang",
    ]

    happy_words = [
        "happy", "great", "good", "excited", "amazing",
        "khush", "acha", "achha",
    ]

    calm_words = [
        "calm", "peaceful", "relaxed", "relax",
        "sukoon", "peace",
    ]

    for word in tired_words:
        if word in t:
            return "tired"

    for word in worried_words:
        if word in t:
            return "worried"

    for word in frustrated_words:
        if word in t:
            return "frustrated"

    for word in sad_words:
        if word in t:
            return "sad"

    for word in happy_words:
        if word in t:
            return "happy"

    for word in calm_words:
        if word in t:
            return "calm"

    return "neutral"


def behaviour_screen():

    st.markdown("## 🎭 AI Mood & Behaviour")

    st.markdown(
        """
        <div class="lab-card">
        <h3>Talk naturally with Ayna 🎙️</h3>
        <p>
        Speak or type about how you are feeling, thinking or behaving.
        Ayna provides broad educational feedback based on the available input.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎙️ Voice Input")

    audio = st.audio_input("Speak to Ayna")

    if audio is not None:
        st.success("🎙️ Voice received.")

        st.audio(audio)

        st.info(
            "Voice recording is available. Automatic speech-to-text requires "
            "a speech-recognition service/API; the browser/app cannot reliably "
            "infer the spoken words from the audio alone."
        )

        st.markdown("### ✍️ Enter the words Ayna should analyse")

    text = st.text_area(
        "What would you like to tell Ayna?",
        placeholder="Example: I feel tired and I can't focus today.",
        height=130,
    )

    if st.button("🎙️ Send to Ayna", use_container_width=True):

        if not text.strip():
            st.warning(
                "Please provide the spoken content as text for the current analysis."
            )
            return

        mood_key = estimate_mood(text)
        emoji, label = MOODS[mood_key]

        ai_text = ask_ai(
            f"""
            The user said:
            "{text}"

            Give a short, supportive educational response.
            Do not diagnose mental illness.
            Do not claim certainty about the person's internal state.
            Mention that this is broad behavioural feedback when appropriate.
            """
        )

        st.session_state.behaviour_result = {
            "mood": label,
            "emoji": emoji,
            "response": ai_text,
        }

    if st.session_state.behaviour_result:

        result = st.session_state.behaviour_result

        st.markdown(
            f"""
            <div class="result-box">
                <div class="emoji-result">{result["emoji"]}</div>
                <h2 style="text-align:center;">
                    {html.escape(result["mood"])}
                </h2>
                <p>{html.escape(result["response"])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 🔊 Ayna Voice")
        speak(result["response"], "🔊 Ayna — Speak Response")

        st.caption(
            "Educational behavioural feedback only — not a medical or psychological diagnosis."
        )


# ============================================================
# BRAIN EXERCISES
# ============================================================

def exercises_screen():

    st.markdown("## ⚡ Brain Exercises")

    st.markdown(
        """
        <div class="lab-card">
        <h3>Adaptive Cognitive Training</h3>
        <p>
        Attention → Working Memory → Memory → Decision Making →
        Inhibitory Control → Cognitive Flexibility
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stages = [
        "Attention",
        "Working Memory",
        "Memory",
        "Decision Making",
        "Inhibitory Control",
        "Cognitive Flexibility",
    ]

    current = min(
        st.session_state.exercise_level - 1,
        len(stages) - 1,
    )

    st.markdown(f"### Current level: {stages[current]}")

    if stages[current] == "Attention":

        st.write("Find the target letter **X** as quickly as possible.")

        grid = [
            random.choice(["X", "O", "A", "K"])
            for _ in range(16)
        ]

        target = st.selectbox(
            "Select the target you noticed",
            grid,
        )

        if st.button("Submit Attention Task"):
            if target == "X":
                st.session_state.exercise_score += 10
                st.success("Correct attention response! +10")
            else:
                st.warning("Try again and focus on the target.")

    elif stages[current] == "Working Memory":

        sequence = [random.randint(1, 9) for _ in range(5)]

        st.session_state.memory_sequence = sequence

        st.info("Remember this sequence:")
        st.code(" ".join(map(str, sequence)))

        answer = st.text_input(
            "Enter the sequence",
            key="memory_exercise_answer",
        )

        if st.button("Check Memory"):
            expected = "".join(map(str, sequence))
            if answer.replace(" ", "") == expected:
                st.session_state.exercise_score += 10
                st.success("Excellent working memory! +10")
            else:
                st.error("Not quite. Try focusing on the order.")

    elif stages[current] == "Memory":

        word_set = ["neuron", "attention", "memory", "reward", "synapse"]

        st.write("Which word belongs to neuroscience?")
        answer = st.radio(
            "Choose one",
            ["football", "neuron", "weather", "mountain"],
        )

        if st.button("Submit Memory"):
            if answer == "neuron":
                st.session_state.exercise_score += 10
                st.success("Correct! +10")
            else:
                st.warning("Try again.")

    elif stages[current] == "Decision Making":

        st.write(
            "You can choose a guaranteed 5 points or a 50% chance of 12 points."
        )

        answer = st.radio(
            "Which would you choose?",
            ["Guaranteed 5", "50% chance of 12"],
        )

        if st.button("Submit Decision"):
            st.session_state.exercise_score += 5
            st.info(
                "There is no single universally correct choice here. "
                "The task demonstrates how risk and reward influence decisions."
            )

    elif stages[current] == "Inhibitory Control":

        st.write("Press STOP only when the target is **RED**.")

        answer = st.radio(
            "Target colour",
            ["RED", "GREEN"],
        )

        if st.button("Respond"):
            if answer == "RED":
                st.session_state.exercise_score += 10
                st.success("Correct inhibition response! +10")
            else:
                st.info("Inhibitory control means resisting an inappropriate response.")

    else:

        st.write(
            "Cognitive flexibility involves switching between rules or perspectives."
        )

        answer = st.radio(
            "Which rule should you use now?",
            [
                "Sort by colour",
                "Sort by shape",
            ],
        )

        if st.button("Submit Flexibility"):
            st.session_state.exercise_score += 10
            st.success("Challenge completed! +10")

    st.markdown(
        f"""
        <div class="metric">
        <h3>Exercise Score</h3>
        <div style="font-size:35px;">{st.session_state.exercise_score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("➡️ Advance Cognitive Level", use_container_width=True):
        if st.session_state.exercise_level < len(stages):
            st.session_state.exercise_level += 1
            st.rerun()


# ============================================================
# RESEARCH BOOK
# ============================================================

RESEARCH_TOPICS = {
    "Brain & Behaviour": {
        "simple": "The brain continuously interacts with the body and environment to produce behaviour.",
        "research": (
            "Behaviour emerges from distributed neural systems involving "
            "cortical, subcortical and neuromodulatory networks."
        ),
    },
    "Memory": {
        "simple": "Memory allows information to be encoded, stored and retrieved.",
        "research": (
            "Memory involves interacting systems including hippocampal, "
            "cortical and subcortical networks. Retrieval can also modify "
            "subsequent memory representations."
        ),
    },
    "Attention": {
        "simple": "Attention helps the brain prioritize some information over other information.",
        "research": (
            "Attention involves coordinated interactions among frontoparietal "
            "networks, sensory systems and subcortical modulatory systems."
        ),
    },
    "Perception": {
        "simple": "Perception is the brain's interpretation of sensory information.",
        "research": (
            "Perception involves both bottom-up sensory processing and "
            "top-down predictive/contextual influences."
        ),
    },
    "Emotion": {
        "simple": "Emotion involves interacting brain and body systems that influence behaviour.",
        "research": (
            "Emotion is not localized to a single structure; valuation, "
            "interoception, learning and action systems interact dynamically."
        ),
    },
    "Decision-making": {
        "simple": "Decision-making involves evaluating options and choosing actions.",
        "research": (
            "Decision-making involves valuation, learning, cognitive control "
            "and uncertainty-related computations."
        ),
    },
    "Learning": {
        "simple": "Learning changes behaviour or knowledge through experience.",
        "research": (
            "Learning can involve synaptic plasticity, reinforcement signals, "
            "network reorganization and changes in memory representations."
        ),
    },
    "Cognitive Control": {
        "simple": "Cognitive control helps us maintain goals and regulate responses.",
        "research": (
            "Cognitive control involves interactions among prefrontal, "
            "parietal, striatal and thalamic systems."
        ),
    },
    "Reward": {
        "simple": "Reward systems help organisms learn which actions and outcomes matter.",
        "research": (
            "Reward processing involves valuation and prediction-error signals "
            "across distributed cortico-striatal and neuromodulatory systems."
        ),
    },
    "Executive Functions": {
        "simple": "Executive functions help with planning, inhibition and flexible behaviour.",
        "research": (
            "Executive control depends on distributed frontoparietal and "
            "frontostriatal networks rather than one isolated executive centre."
        ),
    },
    "Neuroplasticity": {
        "simple": "Neuroplasticity describes the brain's capacity to change with experience.",
        "research": (
            "Plasticity can involve synaptic, cellular, network-level and "
            "structural changes depending on learning and environmental demands."
        ),
    },
    "Neural Circuits": {
        "simple": "Neural circuits are connected groups of neurons that support information processing.",
        "research": (
            "Circuit-level neuroscience examines how interacting neural populations "
            "transform information and produce behaviour."
        ),
    },
    "Neurotransmitters": {
        "simple": "Neurotransmitters are chemical messengers used by neurons.",
        "research": (
            "Neuromodulatory and neurotransmitter systems influence network "
            "activity, learning, arousal, motivation and behaviour."
        ),
    },
}


def research_screen():

    st.markdown("## 📖 Research Book")

    mode = st.toggle(
        "🔬 Research Mode",
        value=st.session_state.research_mode,
    )

    st.session_state.research_mode = mode

    topic = st.selectbox(
        "Choose a neuroscience topic",
        list(RESEARCH_TOPICS.keys()),
    )

    data = RESEARCH_TOPICS[topic]

    st.markdown(
        f"""
        <div class="book">
        <h2>{html.escape(topic)}</h2>
        <h3>{html.escape(data["simple"])}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mode:

        st.markdown("### 🔬 Research Mode")

        st.markdown(
            f"""
            <div class="neuro-card">
            {html.escape(data["research"])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Research Note")

        st.write(
            "Research interpretations should be connected to peer-reviewed "
            "literature, experimental design and appropriate evidence. "
            "NEUROLENS educational content should not be treated as a substitute "
            "for a validated research protocol."
        )

    else:

        st.info(
            "Switch on Research Mode for deeper terminology and research-oriented notes."
        )


# ============================================================
# ASK AYNA
# ============================================================

def ask_ayna_screen():

    st.markdown("## 💬 Ask Ayna")

    st.markdown(
        """
        <div class="lab-card">
        <h3>Talk to Ayna 🤖</h3>
        <p>
        Ask about neuroscience, cognition, behaviour, learning,
        decisions, brain systems or general questions.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    language = st.radio(
        "Ayna response language",
        ["English", "Roman English"],
        horizontal=True,
    )

    question = st.text_area(
        "Your question",
        placeholder="Ask Ayna anything about the brain...",
        height=120,
    )

    if st.button("Send to Ayna", use_container_width=True):

        if not question.strip():
            st.warning("Write a question first.")
            return

        if language == "Roman English":
            system = (
                "Answer in simple Roman English/Hinglish. "
                "You are Ayna, an educational cognitive neuroscience assistant."
            )
        else:
            system = (
                "Answer in clear English. "
                "You are Ayna, an educational cognitive neuroscience assistant."
            )

        answer = ask_ai(question, system)

        st.session_state.ask_messages.append(
            {
                "user": question,
                "answer": answer,
            }
        )

    for message in reversed(st.session_state.ask_messages[-10:]):

        st.markdown(
            f"""
            <div class="neuro-card">
            <b>👤 You</b>
            <p>{html.escape(message["user"])}</p>
            <hr>
            <b>🤖 Ayna</b>
            <p>{html.escape(message["answer"])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        speak(message["answer"])


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

def private_ayna_screen():

    st.markdown("## 🔐 Private Ask Ayna")

    if not st.session_state.private_unlocked:

        st.info(
            "This is a basic session PIN lock. "
            "It is not equivalent to encrypted account-level privacy."
        )

        pin = st.text_input(
            "Create / enter your PIN",
            type="password",
        )

        if st.button("Unlock Private Ayna", use_container_width=True):

            if not st.session_state.private_pin:
                if len(pin) < 4:
                    st.warning("Use at least 4 digits.")
                    return

                st.session_state.private_pin = pin
                st.session_state.private_unlocked = True
                st.rerun()

            elif pin == st.session_state.private_pin:
                st.session_state.private_unlocked = True
                st.rerun()

            else:
                st.error("Incorrect PIN.")

        return

    st.success("🔓 Private Ayna unlocked for this session.")

    question = st.text_area(
        "Private message to Ayna",
        placeholder="Write something you want to discuss privately...",
        height=140,
    )

    if st.button("Send Private Message", use_container_width=True):

        if question.strip():

            answer = ask_ai(
                question,
                (
                    "You are Ayna. Respond supportively and respectfully. "
                    "Do not claim to be a therapist or doctor. "
                    "Do not diagnose."
                ),
            )

            st.session_state.private_messages.append(
                {
                    "user": question,
                    "answer": answer,
                }
            )

    for message in reversed(st.session_state.private_messages[-10:]):

        st.markdown(
            f"""
            <div class="neuro-card">
            <b>👤 You</b>
            <p>{html.escape(message["user"])}</p>
            <hr>
            <b>🤖 Ayna</b>
            <p>{html.escape(message["answer"])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        speak(message["answer"])

    if st.button("🔒 Lock Private Ayna"):
        st.session_state.private_unlocked = False
        st.rerun()


# ============================================================
# PROGRESS
# ============================================================

def progress_screen():

    st.markdown("## 📊 My Progress")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Lab Experiments",
            st.session_state.experiment_score,
        )

    with c2:
        st.metric(
            "Puzzle Score",
            st.session_state.puzzle_score,
        )

    with c3:
        st.metric(
            "Exercise Score",
            st.session_state.exercise_score,
        )

    with c4:
        st.metric(
            "AI Requests",
            st.session_state.ai_requests,
        )

    st.markdown("### 🧠 Cognitive Training Path")

    stages = [
        ("Attention", "🎯"),
        ("Working Memory", "🧠"),
        ("Memory", "💾"),
        ("Decision Making", "⚖️"),
        ("Inhibitory Control", "🛑"),
        ("Cognitive Flexibility", "🔄"),
    ]

    completed = max(
        0,
        st.session_state.exercise_level - 1,
    )

    for i, (name, emoji) in enumerate(stages):

        status = "✅" if i < completed else "🔒"

        st.markdown(
            f"""
            <div class="stage">
            {status} {emoji} <b>{name}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 📚 Research")

    st.write(
        "Explore topics in the Research Book and switch to Research Mode "
        "for deeper terminology."
    )

    st.markdown("### 🔬 Research Archive")

    st.info(
        "This prototype keeps progress in the current Streamlit session. "
        "Persistent cross-device history requires a database/backend."
    )


# ============================================================
# ROUTER
# ============================================================

page = st.session_state.page

if page == "Home":
    home_screen()

elif page == "🧠 Explore Brain":
    brain_screen()

elif page == "🔬 Cognitive Lab":
    lab_screen()

elif page == "🧩 Brain Puzzle":
    puzzle_screen()

elif page == "🎭 AI Mood & Behaviour":
    behaviour_screen()

elif page == "⚡ Brain Exercises":
    exercises_screen()

elif page == "📖 Research Book":
    research_screen()

elif page == "💬 Ask Ayna":
    ask_ayna_screen()

elif page == "🔐 Private Ask Ayna":
    private_ayna_screen()

elif page == "📊 My Progress":
    progress_screen()

else:
    home_screen()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; color:#71879a; padding:20px;">
        🧠 NEUROLENS · Cognitive Neuroscience Lab
        <br>
        Created by Ayna Jaffri
    </div>
    """,
    unsafe_allow_html=True,
)
