import os
import random
import time
from datetime import date

import streamlit as st
from PIL import Image

try:
    from google import genai
except Exception:
    genai = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# =========================================================
# NEUROLENS — COGNITIVE NEUROSCIENCE LAB
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "Lab",
    "character": "Researcher",
    "journey_stage": 0,
    "chat": [],
    "experiment_done": False,
    "experiment_score": 0,
    "puzzle_moves": 0,
    "puzzle_score": 0,
    "exercise_score": 0,
    "mood_result": None,
    "daily_experiment": None,
    "selected_region": "Prefrontal Cortex",
    "research_mode": "Simple Mode",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# DATA
# =========================================================

BRAIN_PARTS = {
    "Prefrontal Cortex": {
        "function": "Planning, decision-making, attention and cognitive control.",
        "behavior": "Helps you control impulses and make goal-directed decisions.",
    },
    "Hippocampus": {
        "function": "Memory formation and spatial learning.",
        "behavior": "Helps form and retrieve memories and navigate environments.",
    },
    "Amygdala": {
        "function": "Emotional processing and threat detection.",
        "behavior": "Helps detect emotionally important or potentially threatening information.",
    },
    "Striatum": {
        "function": "Action selection, reward and habit learning.",
        "behavior": "Helps connect actions with rewards and learned habits.",
    },
    "Anterior Cingulate Cortex": {
        "function": "Conflict monitoring, error processing and cognitive control.",
        "behavior": "Helps notice mistakes and adjust behavior.",
    },
    "Cerebellum": {
        "function": "Motor coordination and motor learning.",
        "behavior": "Helps refine movement and learn precise actions.",
    },
}

JOURNEY = [
    (
        "Whole Brain",
        "The brain is an interconnected biological system containing specialized but communicating networks.",
    ),
    (
        "Brain Region",
        "Different regions contribute to cognition, emotion, movement, memory and decision-making.",
    ),
    (
        "Neural Pathway",
        "Neural circuits allow distant brain regions to communicate and coordinate behavior.",
    ),
    (
        "Neuron",
        "Neurons are specialized cells that receive, process and transmit information.",
    ),
    (
        "Dendrites",
        "Dendrites receive signals from other neurons and send information toward the cell body.",
    ),
    (
        "Axon",
        "The axon carries electrical signals away from the neuron cell body.",
    ),
    (
        "Myelin",
        "Myelin forms an insulating layer around many axons and increases signal conduction speed.",
    ),
    (
        "Electrical Signal",
        "Changes in membrane voltage allow neurons to generate and propagate action potentials.",
    ),
    (
        "Synapse",
        "A synapse is a communication junction where one neuron influences another cell.",
    ),
    (
        "Neurotransmitter",
        "Chemical messengers can cross the synaptic gap and influence the next cell.",
    ),
    (
        "Cognition & Behavior",
        "Networks of neurons ultimately contribute to perception, memory, attention, emotion and behavior.",
    ),
]

RESEARCH = {
    "Memory": {
        "simple": "Memory is the ability to encode, store and retrieve information.",
        "research": "Memory involves interacting neural systems including hippocampal, cortical and subcortical networks. Encoding, consolidation and retrieval depend on distributed network activity.",
    },
    "Attention": {
        "simple": "Attention helps the brain prioritize some information over other information.",
        "research": "Attention involves coordinated frontoparietal, thalamic and sensory systems that regulate selection and processing of behaviorally relevant information.",
    },
    "Decision Making": {
        "simple": "Decision-making involves comparing options and selecting an action.",
        "research": "Decision-making recruits interacting valuation, executive-control and action-selection systems, including prefrontal and striatal circuitry.",
    },
    "Emotion": {
        "simple": "Emotion influences attention, memory, decisions and behavior.",
        "research": "Emotion emerges from distributed interactions among limbic, cortical and subcortical systems rather than from one isolated brain region.",
    },
    "Learning": {
        "simple": "Learning changes how we respond based on experience.",
        "research": "Learning involves synaptic plasticity and network-level changes influenced by prediction error, reinforcement and experience-dependent adaptation.",
    },
    "Cognitive Control": {
        "simple": "Cognitive control helps us stay focused and adjust behavior.",
        "research": "Cognitive control involves interactions among prefrontal, anterior cingulate, parietal and subcortical systems supporting monitoring and goal maintenance.",
    },
}


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at 20% 10%, rgba(45,100,180,.18), transparent 28%),
        radial-gradient(circle at 80% 20%, rgba(120,70,180,.14), transparent 30%),
        linear-gradient(135deg,#050914,#091321 50%,#050811);
    color: #f4f7ff;
}

.block-container {
    max-width: 1250px;
    padding-top: 1.2rem;
}

.lab-title {
    font-size: 48px;
    font-weight: 800;
    letter-spacing: 4px;
    margin-bottom: 0;
}

.lab-subtitle {
    color: #9fb1d1;
    font-size: 16px;
    margin-bottom: 20px;
}

.glass {
    background: rgba(15,25,43,.76);
    border: 1px solid rgba(130,170,220,.18);
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 15px 50px rgba(0,0,0,.28);
}

.neural {
    height: 270px;
    border-radius: 24px;
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 50% 50%, rgba(110,190,255,.25), transparent 14%),
        radial-gradient(circle at 30% 35%, rgba(80,130,255,.14), transparent 18%),
        radial-gradient(circle at 70% 65%, rgba(180,90,255,.15), transparent 20%),
        #07101d;
    border: 1px solid rgba(110,170,255,.25);
}

.neural:before,
.neural:after {
    content: "";
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(100,190,255,.28);
    animation: pulse 3s infinite;
}

.neural:before {
    width: 150px;
    height: 150px;
    left: calc(50% - 75px);
    top: 60px;
}

.neural:after {
    width: 220px;
    height: 220px;
    left: calc(50% - 110px);
    top: 25px;
    animation-delay: 1s;
}

@keyframes pulse {
    0% {transform:scale(.85);opacity:.25}
    50% {transform:scale(1.05);opacity:.8}
    100% {transform:scale(.85);opacity:.25}
}

.stage {
    font-size: 28px;
    font-weight: 700;
}

.small {
    color: #aebbd0;
    font-size: 14px;
}

.score {
    font-size: 30px;
    font-weight: 800;
}

.character {
    font-size: 70px;
    text-align: center;
}

.footer {
    text-align:center;
    color:#7788a5;
    padding:35px 0 10px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def get_client():
    if genai is None:
        return None

    key = None

    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

    if not key:
        key = os.getenv("GEMINI_API_KEY")

    if not key:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


def ask_ai(prompt, context=""):
    client = get_client()

    if client is None:
        return (
            "Ayna AI is currently running in local mode. "
            "Add GEMINI_API_KEY in Streamlit Secrets to activate the AI layer."
        )

    system = """
You are Ayna, the AI research assistant inside NEUROLENS,
an educational cognitive neuroscience platform.

Give scientifically responsible, concise answers.
Do not diagnose medical or psychiatric conditions.
Do not claim that an experimental result is clinically validated.
Explain neuroscience in understandable language.
"""

    full_prompt = f"""
{system}

Current context:
{context}

User:
{prompt}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )

        if response and getattr(response, "text", None):
            return response.text

    except Exception as e:
        return f"Ayna is temporarily unavailable. Please try again. ({type(e).__name__})"

    return "Ayna could not generate a response right now."


def speak(text):
    safe = (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "'")
        .replace('"', '\\"')
        .replace("\n", " ")
    )

    st.components.v1.html(
        f"""
        <script>
        const text = "{safe}";
        if ("speechSynthesis" in window) {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.lang = "en-US";
            u.rate = 0.95;
            u.pitch = 1.0;
            window.speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=0,
    )


def local_daily_experiment():
    experiments = [
        {
            "name": "Working Memory Challenge",
            "description": "Remember the sequence and reproduce it.",
            "task": "Remember: 7 — 2 — 9 — 4 — 1",
            "question": "What was the third number?",
            "answer": "9",
        },
        {
            "name": "Attention Challenge",
            "description": "Identify the target letter while ignoring distractors.",
            "task": "A  A  X  A  A  A",
            "question": "Which letter was the target?",
            "answer": "X",
        },
        {
            "name": "Decision Challenge",
            "description": "Choose the option with the highest expected value.",
            "task": "Option A: 80% chance of 10 points. Option B: 30% chance of 30 points.",
            "question": "Which option has the higher expected value?",
            "answer": "A",
        },
        {
            "name": "Cognitive Flexibility",
            "description": "Switch between two rules.",
            "task": "Rule 1: classify by color. Rule 2: classify by shape.",
            "question": "What ability is being challenged?",
            "answer": "Cognitive flexibility",
        },
    ]

    return experiments[date.today().toordinal() % len(experiments)]


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="lab-title">NEUROLENS</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="lab-subtitle">Explore cognition • behavior • neural systems • AI</div>',
    unsafe_allow_html=True,
)


# =========================================================
# NAVIGATION
# =========================================================

pages = [
    "🧪 Lab",
    "🧠 Explore Brain",
    "🧬 Inside Brain",
    "🧩 Brain Puzzle",
    "😊 AI Mood",
    "⚡ Brain Exercises",
    "📖 Research Book",
    "💬 Ask Ayna",
    "📊 My Progress",
]

selected = st.radio(
    "Navigation",
    pages,
    horizontal=True,
    label_visibility="collapsed",
)

st.session_state.page = selected


# =========================================================
# LAB
# =========================================================

if selected == "🧪 Lab":

    st.markdown(
        """
        <div class="glass">
        <h2>Welcome to the Cognitive Neuroscience Lab</h2>
        <p class="small">
        A visual environment for exploring brain systems, cognition,
        behavior and interactive experiments.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown('<div class="neural"></div>', unsafe_allow_html=True)

        st.write("")

        st.markdown(
            """
            <div class="glass">
            <h3>🧠 Neural Activity Monitor</h3>
            <p class="small">
            NEUROLENS models cognition as an interaction between
            distributed neural systems rather than one isolated brain area.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("### Choose your lab character")

        characters = {
            "Researcher": "🧑‍🔬",
            "Explorer": "🧑‍🚀",
            "Student": "🧑‍🎓",
            "Observer": "🧑",
        }

        character = st.selectbox(
            "Character",
            list(characters.keys()),
            index=list(characters.keys()).index(
                st.session_state.character
            ),
        )

        st.session_state.character = character

        st.markdown(
            f'<div class="character">{characters[character]}</div>',
            unsafe_allow_html=True,
        )

        st.success(
            f"{character} selected. Your neuroscience lab is ready."
        )

        if st.button("🚀 Start Today's Experiment", use_container_width=True):
            st.session_state.page = "🧪 Lab"
            st.session_state.daily_experiment = local_daily_experiment()
            st.rerun()

    st.write("")

    experiment = (
        st.session_state.daily_experiment
        or local_daily_experiment()
    )

    st.markdown(
        f"""
        <div class="glass">
        <h3>🔬 Today's Cognitive Experiment</h3>
        <p><b>{experiment["name"]}</b></p>
        <p class="small">{experiment["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.markdown("### Ayna Lab Assistant")

    question = st.text_input(
        "Ask something about today's experiment",
        placeholder="Why does this task test working memory?",
    )

    if question:
        answer = ask_ai(
            question,
            context=f"Current experiment: {experiment['name']}",
        )

        st.info(answer)

        if st.button("🔊 Hear Ayna"):
            speak(answer)


# =========================================================
# EXPLORE BRAIN
# =========================================================

elif selected == "🧠 Explore Brain":

    st.markdown("## Interactive Brain Explorer")

    image_path = "brain.png"

    col1, col2 = st.columns([1.4, 1])

    with col1:
        if os.path.exists(image_path):
            image = Image.open(image_path)
            st.image(
                image,
                use_container_width=True,
                caption="Scientific brain overview",
            )
        else:
            st.warning(
                "brain.png not found. Upload brain.png to the same folder as app.py."
            )

    with col2:

        region = st.selectbox(
            "Select a brain region",
            list(BRAIN_PARTS.keys()),
        )

        st.session_state.selected_region = region

        info = BRAIN_PARTS[region]

        st.markdown(
            f"""
            <div class="glass">
            <h2>{region}</h2>
            <p><b>Function</b></p>
            <p>{info["function"]}</p>
            <p><b>Behavioral relevance</b></p>
            <p>{info["behavior"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🧬 Enter This Region", use_container_width=True):
            st.session_state.journey_stage = 1
            st.rerun()


# =========================================================
# INSIDE BRAIN
# =========================================================

elif selected == "🧬 Inside Brain":

    stage_index = st.session_state.journey_stage

    title, description = JOURNEY[stage_index]

    st.markdown("## 🧬 Inside-Brain Journey")

    st.markdown(
        f"""
        <div class="neural">
        <div style="position:absolute;inset:0;display:flex;
        flex-direction:column;align-items:center;justify-content:center;">
        <div style="font-size:70px;">🧠</div>
        <div class="stage">{title}</div>
        <div class="small">{description}</div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    progress = (stage_index + 1) / len(JOURNEY)
    st.progress(progress)

    st.markdown(
        f"""
        <div class="glass">
        <h3>Stage {stage_index + 1}: {title}</h3>
        <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if stage_index > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state.journey_stage -= 1
                st.rerun()

    with col2:
        if st.button("🔊 Ayna Explain", use_container_width=True):
            speak(
                f"We are exploring {title}. {description}"
            )

    with col3:
        if stage_index < len(JOURNEY) - 1:
            if st.button("Next Stage →", use_container_width=True):
                st.session_state.journey_stage += 1
                st.rerun()

    st.write("")

    st.markdown("### Ask Ayna about this neural stage")

    q = st.text_input(
        "Question",
        key=f"journey_q_{stage_index}",
        placeholder=f"Ask about {title}...",
    )

    if q:
        ans = ask_ai(
            q,
            context=f"""
            User is currently inside the brain at:
            {title}

            Explanation:
            {description}
            """,
        )

        st.info(ans)

        if st.button("🔊 Hear answer", key=f"hear_{stage_index}"):
            speak(ans)


# =========================================================
# BRAIN PUZZLE
# =========================================================

elif selected == "🧩 Brain Puzzle":

    st.markdown("## 🧩 Brain Picture Puzzle")

    st.write(
        "Drag each piece with your finger or mouse and drop it into the correct position."
    )

    size = st.select_slider(
        "Puzzle difficulty",
        options=[3, 4, 5],
        value=3,
    )

    if os.path.exists("brain.png"):

        image = Image.open("brain.png").convert("RGB")

        width, height = image.size

        piece_w = width // size
        piece_h = height // size

        pieces = []

        for row in range(size):
            for col in range(size):
                left = col * piece_w
                top = row * piece_h

                right = (
                    (col + 1) * piece_w
                    if col < size - 1
                    else width
                )

                bottom = (
                    (row + 1) * piece_h
                    if row < size - 1
                    else height
                )

                crop = image.crop(
                    (left, top, right, bottom)
                )

                import io
                buffer = io.BytesIO()
                crop.save(buffer, format="PNG")

                pieces.append(
                    {
                        "row": row,
                        "col": col,
                        "data": buffer.getvalue(),
                    }
                )

        random.shuffle(pieces)

        html = """
        <style>
        .puzzle {
            display:grid;
            grid-template-columns:repeat(%d,1fr);
            gap:6px;
            max-width:700px;
            margin:auto;
        }

        .piece {
            aspect-ratio:1;
            border:2px solid #4b6388;
            border-radius:10px;
            background:#101a2b;
            overflow:hidden;
            cursor:grab;
            touch-action:none;
        }

        .piece img {
            width:100%%;
            height:100%%;
            object-fit:cover;
            pointer-events:none;
        }

        .piece.dragging {
            opacity:.45;
        }

        .piece.correct {
            border:3px solid #45e39b;
        }
        </style>

        <div class="puzzle" id="puzzle">
        """ % size

        for i, piece in enumerate(pieces):

            import base64

            encoded = base64.b64encode(
                piece["data"]
            ).decode()

            html += f"""
            <div
                class="piece"
                draggable="true"
                data-row="{piece['row']}"
                data-col="{piece['col']}"
                id="piece{i}"
            >
                <img src="data:image/png;base64,{encoded}">
            </div>
            """

        html += """
        </div>

        <script>

        let dragged = null;

        document.querySelectorAll(".piece").forEach(piece => {

            piece.addEventListener("dragstart", e => {
                dragged = piece;
                piece.classList.add("dragging");
            });

            piece.addEventListener("dragend", e => {
                piece.classList.remove("dragging");
            });

            piece.addEventListener("dragover", e => {
                e.preventDefault();
            });

            piece.addEventListener("drop", e => {

                e.preventDefault();

                if (!dragged || dragged === piece)
                    return;

                const parent = piece.parentNode;

                const all = Array.from(parent.children);

                const a = all.indexOf(dragged);
                const b = all.indexOf(piece);

                if (a < b) {
                    parent.insertBefore(dragged, piece.nextSibling);
                } else {
                    parent.insertBefore(dragged, piece);
                }

                checkPuzzle();
            });

            let startX = 0;
            let startY = 0;

            piece.addEventListener("pointerdown", e => {

                piece.setPointerCapture(e.pointerId);

                dragged = piece;

                startX = e.clientX;
                startY = e.clientY;

                piece.classList.add("dragging");
            });

            piece.addEventListener("pointerup", e => {

                piece.classList.remove("dragging");

                let target = document.elementFromPoint(
                    e.clientX,
                    e.clientY
                );

                if (
                    target &&
                    target.closest(".piece") &&
                    target.closest(".piece") !== dragged
                ) {

                    let other =
                        target.closest(".piece");

                    const parent = dragged.parentNode;

                    const a =
                        Array.from(parent.children)
                        .indexOf(dragged);

                    const b =
                        Array.from(parent.children)
                        .indexOf(other);

                    if (a < b) {
                        parent.insertBefore(
                            dragged,
                            other.nextSibling
                        );
                    } else {
                        parent.insertBefore(
                            dragged,
                            other
                        );
                    }
                }

                checkPuzzle();
            });

        });

        function checkPuzzle() {

            const pieces =
                Array.from(
                    document.querySelectorAll(".piece")
                );

            let correct = 0;

            pieces.forEach((piece,index) => {

                const row =
                    Number(piece.dataset.row);

                const col =
                    Number(piece.dataset.col);

                const expected =
                    row * %d + col;

                if (index === expected) {

                    piece.classList.add("correct");
                    correct++;

                } else {

                    piece.classList.remove("correct");

                }

            });

            if (correct === pieces.length) {

                window.parent.postMessage(
                    {
                        type:"neurolens_puzzle_complete",
                        score:100
                    },
                    "*"
                );

                setTimeout(() => {
                    alert(
                        "🧠 Puzzle complete! Excellent neural reconstruction."
                    );
                },100);

            }

        }

        </script>
        """ % size

        st.components.v1.html(
            html,
            height=700,
            scrolling=False,
        )

    else:
        st.warning(
            "Upload brain.png to enable the Brain Puzzle."
        )


# =========================================================
# AI MOOD
# =========================================================

elif selected == "😊 AI Mood":

    st.markdown("## 😊 AI Mood & Behaviour")

    st.markdown(
        """
        <div class="glass">
        <h3>Talk naturally with Ayna</h3>
        <p class="small">
        You can record your voice or type a message. Ayna estimates
        emotional/behavioral patterns from the available input.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    voice = st.audio_input(
        "🎙️ Speak to Ayna"
    )

    text = st.text_area(
        "Or type what you're feeling",
        placeholder="Tell Ayna how your day is going...",
    )

    if voice is not None:

        st.audio(voice)

        if st.button("🧠 Analyze Voice", use_container_width=True):

            client = get_client()

            if client is None:

                st.session_state.mood_result = (
                    "😊 Positive / Neutral",
                    "Ayna needs GEMINI_API_KEY to analyze the recorded voice."
                )

            else:

                try:

                    audio_bytes = voice.getvalue()

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            """
Analyze this voice sample conservatively for
observable emotional/communication patterns.

Do not diagnose.
Return:
1. One likely broad mood category.
2. One secondary state if appropriate.
3. A short friendly explanation.
""",
                            {
                                "inline_data": {
                                    "mime_type": "audio/wav",
                                    "data": audio_bytes,
                                }
                            },
                        ],
                    )

                    result = (
                        "😊 Mood estimate",
                        response.text
                        if response
                        and getattr(response, "text", None)
                        else "Unable to analyze the sample."
                    )

                    st.session_state.mood_result = result

                except Exception:
                    st.session_state.mood_result = (
                        "🙂 Unable to estimate",
                        "Ayna could not process this recording."
                    )

    elif text:

        if st.button("🧠 Analyze Text", use_container_width=True):

            result = ask_ai(
                f"""
Estimate broad emotional/behavioral tone from this message.

Message:
{text}

Return a friendly result with emojis.
Do not diagnose any mental-health condition.
""",
                context="AI Mood & Behaviour Lab",
            )

            st.session_state.mood_result = (
                "🧠 Ayna's estimate",
                result,
            )

    if st.session_state.mood_result:

        title, result = st.session_state.mood_result

        st.markdown(
            f"""
            <div class="glass">
            <h2>{title}</h2>
            <p>{result}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔊 Hear Ayna's response"):
            speak(result)


# =========================================================
# BRAIN EXERCISES
# =========================================================

elif selected == "⚡ Brain Exercises":

    st.markdown("## ⚡ AI Brain Exercises")

    st.write(
        "Train attention, memory, decision-making and cognitive flexibility."
    )

    if "exercise_level" not in st.session_state:
        st.session_state.exercise_level = 1

    if "exercise_score" not in st.session_state:
        st.session_state.exercise_score = 0

    level = st.session_state.exercise_level

    st.markdown(
        f"""
        <div class="glass">
        <h2>Level {level}</h2>
        <p class="small">Current score</p>
        <div class="score">{st.session_state.exercise_score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    exercises = [
        {
            "name": "Working Memory",
            "question": "Which number comes third? 8 — 3 — 9 — 2 — 6",
            "options": ["3", "9", "2", "6"],
            "answer": "9",
        },
        {
            "name": "Attention",
            "question": "Which symbol is different?  ○ ○ ○ △ ○",
            "options": ["First", "Second", "Fourth", "Fifth"],
            "answer": "Fourth",
        },
        {
            "name": "Decision Making",
            "question": "Which has greater expected value? A: 50% × 20. B: 80% × 10.",
            "options": ["A", "B"],
            "answer": "A",
        },
        {
            "name": "Cognitive Flexibility",
            "question": "Switching from one rule to another mainly tests:",
            "options": [
                "Cognitive flexibility",
                "Vision",
                "Hearing",
                "Balance",
            ],
            "answer": "Cognitive flexibility",
        },
    ]

    exercise = exercises[
        (level - 1) % len(exercises)
    ]

    st.markdown(f"### {exercise['name']}")

    answer = st.radio(
        exercise["question"],
        exercise["options"],
        key=f"exercise_{level}",
    )

    if st.button("Check Answer", use_container_width=True):

        if answer == exercise["answer"]:

            st.success("✅ Correct!")

            st.session_state.exercise_score += 10
            st.session_state.exercise_level += 1

        else:

            st.error(
                f"❌ Not quite. Correct answer: {exercise['answer']}"
            )


# =========================================================
# RESEARCH BOOK
# =========================================================

elif selected == "📖 Research Book":

    st.markdown("## 📖 Cognitive Neuroscience Research Book")

    st.session_state.research_mode = st.radio(
        "Mode",
        ["Simple Mode", "Research Mode"],
        horizontal=True,
    )

    topic = st.selectbox(
        "Choose a topic",
        list(RESEARCH.keys()),
    )

    data = RESEARCH[topic]

    if st.session_state.research_mode == "Simple Mode":
        content = data["simple"]
    else:
        content = data["research"]

    st.markdown(
        f"""
        <div class="glass">
        <h2>{topic}</h2>
        <p>{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.markdown("### Research connection")

    research_question = st.text_input(
        "Ask about this topic",
        placeholder=f"How is {topic.lower()} studied?",
    )

    if research_question:

        answer = ask_ai(
            research_question,
            context=f"""
            Research Book topic: {topic}
            Mode: {st.session_state.research_mode}
            """,
        )

        st.info(answer)

        if st.button("🔊 Hear explanation"):
            speak(answer)


# =========================================================
# ASK AYNA
# =========================================================

elif selected == "💬 Ask Ayna":

    st.markdown("## 💬 Ask Ayna")

    st.markdown(
        """
        <div class="glass">
        <h3>Private-style conversation space</h3>
        <p class="small">
        Ask Ayna about neuroscience, behavior, cognition,
        decisions, learning or everyday questions.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    for message in st.session_state.chat:

        if message["role"] == "user":
            st.markdown(
                f"**You:** {message['content']}"
            )
        else:
            st.markdown(
                f"**🧠 Ayna:** {message['content']}"
            )

    prompt = st.text_area(
        "Message Ayna",
        placeholder="Ask anything...",
        key="ask_ayna_input",
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Send",
            use_container_width=True,
        ):

            if prompt.strip():

                st.session_state.chat.append(
                    {
                        "role": "user",
                        "content": prompt,
                    }
                )

                recent = st.session_state.chat[-6:]

                context = "\n".join(
                    f"{m['role']}: {m['content']}"
                    for m in recent
                )

                answer = ask_ai(
                    prompt,
                    context=context,
                )

                st.session_state.chat.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

                st.rerun()

    with col2:

        if st.button(
            "🗑️ Clear Chat",
            use_container_width=True,
        ):

            st.session_state.chat = []
            st.rerun()

    if st.session_state.chat:

        last = st.session_state.chat[-1]

        if last["role"] == "assistant":

            if st.button("🔊 Hear Ayna"):

                speak(last["content"])


# =========================================================
# PROGRESS
# =========================================================

elif selected == "📊 My Progress":

    st.markdown("## 📊 My Progress")

    experiment_score = (
        100 if st.session_state.experiment_done else 0
    )

    puzzle_score = st.session_state.puzzle_score

    exercise_score = st.session_state.exercise_score

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Daily Experiment",
            experiment_score,
        )

    with c2:

        st.metric(
            "Puzzle Score",
            puzzle_score,
        )

    with c3:

        st.metric(
            "Brain Exercise",
            exercise_score,
        )

    st.write("")

    if go is not None:

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=[
                    "Experiment",
                    "Puzzle",
                    "Exercises",
                ],
                y=[
                    experiment_score,
                    puzzle_score,
                    exercise_score,
                ],
            )
        )

        fig.update_layout(
            title="Cognitive Activity Overview",
            height=400,
            template="plotly_dark",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="glass">
        <h3>🧠 NEUROLENS Research Journey</h3>
        <p class="small">
        Your progress can eventually include experiment history,
        cognitive-task accuracy, reaction time, puzzle performance,
        research topics and learning streaks.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
    NEUROLENS • Cognitive Neuroscience Lab<br>
    Created by Ayna Jaffri
    </div>
    """,
    unsafe_allow_html=True,
)
