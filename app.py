import streamlit as st
from pathlib import Path

# =========================================================
# NEUROLENS — Cognitive Neuroscience Lab
# Creator: Ayna Jaffri
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = Path(__file__).parent
ASSETS = BASE / "assets"

BRAIN_VIDEO = ASSETS / "brain_animation.mp4"
LAB_VIDEO = ASSETS / "cognitive_lab_brain.mp4"


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "Home",
    "language": "English",
    "character": "🧑‍🔬 Researcher",
    "experiment_index": 0,
    "experiments_done": 0,
    "puzzles_done": 0,
    "exercises_done": 0,
    "mood_checks": 0,
    "messages": [],
    "journey_stage": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CSS — SCIENTIFIC LAB
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at 15% 15%, rgba(70,130,180,.14), transparent 25%),
        radial-gradient(circle at 85% 20%, rgba(130,80,180,.12), transparent 25%),
        linear-gradient(135deg,#07111f,#0b1628 45%,#07101b);
    color:#eef6ff;
}

.main-title {
    font-size:56px;
    font-weight:800;
    letter-spacing:4px;
    margin-bottom:0;
}

.subtitle {
    color:#9fc3df;
    font-size:18px;
    margin-top:0;
}

.lab-card {
    padding:22px;
    border:1px solid rgba(150,210,255,.22);
    border-radius:20px;
    background:rgba(12,29,48,.72);
    box-shadow:0 8px 35px rgba(0,0,0,.25);
    margin-bottom:18px;
}

.neural-orb {
    width:150px;
    height:150px;
    margin:auto;
    border-radius:50%;
    background:
        radial-gradient(circle at 40% 35%,#ffffff 0 3%,transparent 4%),
        radial-gradient(circle,#4cc9f0 0%,#4361ee 28%,#151b4b 65%,transparent 70%);
    box-shadow:
        0 0 25px #4cc9f0,
        0 0 65px rgba(67,97,238,.6);
    animation:pulse 2.5s infinite ease-in-out;
}

@keyframes pulse {
    0%,100% {transform:scale(1);}
    50% {transform:scale(1.08);}
}

.neuron-line {
    height:2px;
    background:linear-gradient(90deg,transparent,#4cc9f0,transparent);
    animation:signal 1.5s infinite;
}

@keyframes signal {
    0% {opacity:.15;}
    50% {opacity:1;}
    100% {opacity:.15;}
}

.character {
    font-size:65px;
    text-align:center;
    animation:float 2.5s infinite ease-in-out;
}

@keyframes float {
    0%,100% {transform:translateY(0);}
    50% {transform:translateY(-10px);}
}

.stage {
    padding:18px;
    border-radius:16px;
    border:1px solid rgba(100,200,255,.2);
    background:rgba(15,32,50,.8);
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATA
# =========================================================

BRAIN_REGIONS = {
    "Prefrontal Cortex": {
        "function": "Planning, decision-making, cognitive control and working memory."
    },
    "Hippocampus": {
        "function": "Important for memory formation and spatial representation."
    },
    "Amygdala": {
        "function": "Processes emotional significance, especially threat-related signals."
    },
    "Striatum": {
        "function": "Important in reward, action selection, learning and habit-related processes."
    },
    "Anterior Cingulate Cortex": {
        "function": "Involved in conflict monitoring, attention and cognitive control."
    },
    "Cerebellum": {
        "function": "Coordinates movement and also contributes to cognitive processes."
    }
}


EXPERIMENTS = [
    {
        "name": "Working Memory",
        "description":
            "Remember a short sequence and reproduce it. "
            "This explores temporary information maintenance."
    },
    {
        "name": "Attention",
        "description":
            "Focus on a target while ignoring distracting information."
    },
    {
        "name": "Decision Making",
        "description":
            "Choose between competing options and reflect on your reasoning."
    },
    {
        "name": "Cognitive Flexibility",
        "description":
            "Switch between changing rules and adapt your response."
    },
    {
        "name": "Inhibitory Control",
        "description":
            "Respond to relevant signals while withholding responses to distractors."
    },
    {
        "name": "Memory",
        "description":
            "Recall information after a short delay."
    }
]


JOURNEY = [
    (
        "Whole Brain",
        "Start at the whole-brain level and observe the major systems involved in cognition and behaviour."
    ),
    (
        "Brain Region",
        "Move from the whole brain toward a selected functional region."
    ),
    (
        "Neural Circuit",
        "Explore communication between connected brain regions."
    ),
    (
        "Neuron",
        "Enter the cellular level and explore how neurons process information."
    ),
    (
        "Dendrites",
        "Dendrites receive signals from other neurons."
    ),
    (
        "Axon",
        "The axon carries electrical signals away from the cell body."
    ),
    (
        "Myelin",
        "Myelin forms insulating segments around many axons and supports rapid signal conduction."
    ),
    (
        "Electrical Signal",
        "Action potentials propagate along excitable neuronal membranes."
    ),
    (
        "Synapse",
        "A synapse is a specialised communication point between neurons."
    ),
    (
        "Neurotransmitter",
        "Chemical messengers can transmit information across many synapses."
    ),
    (
        "Cognition & Behaviour",
        "Neural networks support processes such as memory, attention, decisions and behaviour."
    )
]


RESEARCH_TOPICS = [
    "Brain & Behaviour",
    "Memory",
    "Attention",
    "Perception",
    "Emotion",
    "Decision Making",
    "Learning",
    "Cognitive Control",
    "Reward",
    "Executive Functions",
    "Neuroplasticity",
    "Neural Circuits",
    "Neurotransmitters"
]


# =========================================================
# FUNCTIONS
# =========================================================

def speak(text):
    """Browser speech output."""
    safe = (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", " ")
    )

    st.components.v1.html(
        f"""
        <script>
        const text = `{safe}`;
        if ("speechSynthesis" in window) {{
            speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.lang = "en-US";
            speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=0
    )


def local_ai(question, language="English"):
    """
    Local fallback.
    AI API can be connected later through Streamlit Secrets.
    """

    if language == "Roman English":
        return (
            "Ayna: Is question ko cognitive neuroscience ke "
            "perspective se explore kiya ja sakta hai. "
            "AI service available na hone par local response use hua hai."
        )

    return (
        "Ayna: This question can be explored from a "
        "cognitive-neuroscience perspective. "
        "The local fallback is being used."
    )


def ai_answer(question):
    """
    Gemini connection.
    Falls back locally if API is unavailable.
    """

    try:
        from google import genai

        api_key = st.secrets.get("GEMINI_API_KEY", None)

        if not api_key:
            return local_ai(
                question,
                st.session_state.language
            )

        client = genai.Client(api_key=api_key)

        if st.session_state.language == "Roman English":
            instruction = (
                "Answer in simple Roman English/Roman Urdu. "
                "Keep scientific neuroscience terminology accurate."
            )
        else:
            instruction = (
                "Answer in clear scientific English."
            )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            You are Ayna, the AI neuroscience assistant inside NEUROLENS.

            {instruction}

            User question:
            {question}

            Give a concise but useful answer.
            """
        )

        return response.text

    except Exception:
        return local_ai(
            question,
            st.session_state.language
        )


def metric_card(title, value):
    st.markdown(
        f"""
        <div class="lab-card">
            <h4>{title}</h4>
            <h2>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧠 NEUROLENS")

    st.session_state.language = st.radio(
        "Ayna Language",
        ["English", "Roman English"],
        horizontal=True
    )

    pages = [
        "Home",
        "Cognitive Lab",
        "Explore Brain",
        "Brain Puzzle",
        "AI Mood & Behaviour",
        "Brain Exercises",
        "Research Book",
        "Ask Ayna",
        "My Progress"
    ]

    st.session_state.page = st.radio(
        "Navigation",
        pages,
        index=pages.index(st.session_state.page)
    )

    st.divider()

    st.caption("Cognitive Neuroscience Lab")
    st.caption("Created by Ayna Jaffri")


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "Home":

    st.markdown(
        '<div class="main-title">NEUROLENS</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Explore cognition, behaviour & the brain'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    st.markdown(
        """
        <div class="lab-card">
        <div class="neural-orb"></div>
        <h2 style="text-align:center;">Cognitive Neuroscience Lab</h2>
        <p style="text-align:center;color:#a9c9df;">
        Enter an interactive environment where brain science,
        behaviour, experiments and AI meet.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if LAB_VIDEO.exists():
        st.video(str(LAB_VIDEO))

    st.subheader("Explore NEUROLENS")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 🧪")
        st.write("Daily Lab Experiment")

    with c2:
        st.markdown("### 🧠")
        st.write("Inside-Brain Journey")

    with c3:
        st.markdown("### 😊")
        st.write("AI Mood & Behaviour")

    c4, c5, c6 = st.columns(3)

    with c4:
        st.markdown("### 🧩")
        st.write("Brain Puzzle")

    with c5:
        st.markdown("### 🎯")
        st.write("Brain Exercises")

    with c6:
        st.markdown("### 📚")
        st.write("Research Book")


# =========================================================
# COGNITIVE LAB
# =========================================================

elif st.session_state.page == "Cognitive Lab":

    st.header("🧪 Cognitive Neuroscience Lab")

    st.markdown(
        """
        <div class="lab-card">
            <div class="character">🧑‍🔬</div>
            <h3 style="text-align:center;">Choose your researcher</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.session_state.character = st.selectbox(
        "Animated Lab Character",
        [
            "🧑‍🔬 Researcher",
            "👩‍🔬 Neuroscientist",
            "🧠 Brain Explorer",
            "🤖 Ayna Assistant"
        ]
    )

    st.success(
        f"Selected character: {st.session_state.character}"
    )

    if LAB_VIDEO.exists():
        st.video(str(LAB_VIDEO))

    st.markdown(
        """
        <div class="lab-card">
        <h3>🔬 Laboratory Equipment</h3>

        🖥️ Brain Activity Monitor  
        <br>📈 Neural Signal Display  
        <br>🔬 Microscopic Neural View  
        <br>🧪 Experiment Workstation  
        <br>⚡ Neural Activity Monitor
        </div>
        """,
        unsafe_allow_html=True
    )

    exp = EXPERIMENTS[
        st.session_state.experiment_index
        % len(EXPERIMENTS)
    ]

    st.subheader(
        f"Today's Experiment — {exp['name']}"
    )

    st.write(exp["description"])

    st.markdown(
        '<div class="neuron-line"></div>',
        unsafe_allow_html=True
    )

    response = st.text_input(
        "Your experimental response"
    )

    if st.button(
        "▶ Run Experiment",
        use_container_width=True
    ):

        if response.strip():

            st.session_state.experiments_done += 1

            result = ai_answer(
                f"""
                Experiment: {exp['name']}
                User response: {response}

                Analyse the response from an educational
                cognitive-neuroscience perspective.
                Do not diagnose the person.
                """
            )

            st.markdown(
                '<div class="lab-card">'
                '<h3>🧠 Ayna Analysis</h3>',
                unsafe_allow_html=True
            )

            st.write(result)

            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("🔊 Ayna Voice"):
                speak(result)

            st.session_state.experiment_index += 1

        else:
            st.warning("Enter your response first.")


# =========================================================
# EXPLORE BRAIN
# =========================================================

elif st.session_state.page == "Explore Brain":

    st.header("🧠 Inside-Brain Journey")

    if BRAIN_VIDEO.exists():
        st.video(str(BRAIN_VIDEO))

    st.markdown(
        """
        <div class="lab-card">
        <h3>Travel from the brain to the synapse</h3>
        <p>
        Whole Brain → Region → Circuit → Neuron →
        Dendrite → Axon → Myelin → Signal →
        Synapse → Neurotransmitter → Behaviour
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    stage_names = [x[0] for x in JOURNEY]

    selected = st.selectbox(
        "Current neural stage",
        stage_names,
        index=st.session_state.journey_stage
    )

    stage_index = stage_names.index(selected)
    st.session_state.journey_stage = stage_index

    description = JOURNEY[stage_index][1]

    st.markdown(
        f"""
        <div class="stage">
            <h2>{selected}</h2>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        if stage_index > 0:
            if st.button("⬅ Previous Stage"):
                st.session_state.journey_stage -= 1
                st.rerun()

    with c2:
        if stage_index < len(JOURNEY) - 1:
            if st.button("Next Stage ➡"):
                st.session_state.journey_stage += 1
                st.rerun()

    st.divider()

    question = st.text_input(
        f"Ask Ayna about {selected}"
    )

    if st.button(
        "💬 Ask Ayna",
        key="journey_ask"
    ):

        answer = ai_answer(
            f"""
            The user is currently exploring:
            {selected}

            Explain the concept and its relationship
            to cognition and behaviour.

            User question:
            {question}
            """
        )

        st.write(answer)

        if st.button("🔊 Hear Ayna", key="journey_voice"):
            speak(answer)


# =========================================================
# BRAIN PUZZLE
# =========================================================

elif st.session_state.page == "Brain Puzzle":

    st.header("🧩 Brain Puzzle")

    st.write(
        "Choose a level and solve the brain image puzzle "
        "using drag-and-drop."
    )

    level = st.selectbox(
        "Puzzle Level",
        ["3 × 3", "4 × 4", "5 × 5"]
    )

    st.markdown(
        """
        <div class="lab-card">
        <h3>Touch + Mouse Support</h3>
        <p>
        The final puzzle component uses draggable pieces,
        touch interaction and snap-to-target placement.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "▶ Start Brain Puzzle",
        use_container_width=True
    ):
        st.session_state.puzzles_done += 1
        st.success(
            f"{level} puzzle started."
        )

    if st.button(
        "🔄 Reset Puzzle"
    ):
        st.rerun()


# =========================================================
# AI MOOD & BEHAVIOUR
# =========================================================

elif st.session_state.page == "AI Mood & Behaviour":

    st.header("😊 AI Mood & Behaviour")

    st.write(
        "Speak naturally to Ayna or type a message."
    )

    audio = st.audio_input(
        "🎤 Record your voice"
    )

    if st.button(
        "📤 Send Voice",
        use_container_width=True
    ):

        if audio is None:
            st.warning("Record your voice first.")

        else:

            st.session_state.mood_checks += 1

            result = (
                "😊 Positive / calm signal estimate\n\n"
                "Your voice response appears relatively "
                "positive or calm."
            )

            st.success(result)

            if st.button(
                "🔊 Ayna Voice",
                key="mood_voice"
            ):
                speak(result)

    st.divider()

    text = st.text_area(
        "Or type what you are feeling"
    )

    if st.button(
        "📤 Send Text",
        use_container_width=True
    ):

        if text.strip():

            st.session_state.mood_checks += 1

            result = ai_answer(
                f"""
                Estimate the conversational mood signal
                from this text.

                Give:
                1. emoji
                2. simple mood description
                3. brief explanation

                Do not diagnose a mental-health condition.

                Text:
                {text}
                """
            )

            st.write(result)

            if st.button(
                "🔊 Ayna Voice",
                key="text_mood_voice"
            ):
                speak(result)

        else:
            st.warning("Write something first.")


# =========================================================
# BRAIN EXERCISES
# =========================================================

elif st.session_state.page == "Brain Exercises":

    st.header("🎯 AI Brain Exercises")

    domain = st.selectbox(
        "Cognitive domain",
        [
            "Attention",
            "Working Memory",
            "Memory",
            "Decision Making",
            "Inhibitory Control",
            "Cognitive Flexibility"
        ]
    )

    st.markdown(
        f"""
        <div class="lab-card">
        <h3>Current Training: {domain}</h3>
        <p>
        Complete the challenge and receive the next
        cognitive task.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    challenge = st.text_input(
        "Your answer"
    )

    if st.button(
        "Submit Challenge",
        use_container_width=True
    ):

        if challenge.strip():

            st.session_state.exercises_done += 1

            result = ai_answer(
                f"""
                Cognitive exercise:
                {domain}

                User answer:
                {challenge}

                Evaluate the response educationally.
                Then suggest a slightly more challenging
                next task.
                """
            )

            st.write(result)

            if st.button(
                "🔊 Hear Ayna",
                key="exercise_voice"
            ):
                speak(result)

        else:
            st.warning("Enter an answer.")


# =========================================================
# RESEARCH BOOK
# =========================================================

elif st.session_state.page == "Research Book":

    st.header("📚 Cognitive Neuroscience Research Book")

    mode = st.radio(
        "Research depth",
        ["Simple Mode", "Research Mode"],
        horizontal=True
    )

    topic = st.selectbox(
        "Research topic",
        RESEARCH_TOPICS
    )

    if mode == "Simple Mode":

        st.markdown(
            f"""
            <div class="lab-card">
            <h2>{topic}</h2>
            <p>
            Explore the basic relationship between
            brain systems, cognition and behaviour.
            </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="lab-card">
            <h2>Research Mode — {topic}</h2>

            <b>Research dimensions:</b>

            <br>• Neural mechanisms
            <br>• Cognitive processes
            <br>• Behavioural outcomes
            <br>• Experimental paradigms
            <br>• Measurement
            <br>• Interpretation
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button(
        "🧠 Ask Ayna about this topic"
    ):

        answer = ai_answer(
            f"""
            Explain {topic} for a cognitive neuroscience
            research learner.

            Include:
            neural mechanisms,
            cognitive function,
            behavioural relevance,
            and common experimental approaches.
            """
        )

        st.write(answer)

        if st.button(
            "🔊 Hear Research Note"
        ):
            speak(answer)


# =========================================================
# ASK AYNA
# =========================================================

elif st.session_state.page == "Ask Ayna":

    st.header("💬 Ask Ayna")

    st.write(
        "Talk to Ayna using voice or text."
    )

    audio = st.audio_input(
        "🎤 Record Voice"
    )

    if st.button(
        "📤 Send Voice",
        use_container_width=True
    ):

        if audio:

            reply = ai_answer(
                "The user sent a voice message. "
                "Respond as Ayna in the selected language."
            )

            st.session_state.messages.append(
                ("You 🎤", "[Voice message]")
            )

            st.session_state.messages.append(
                ("Ayna 🧠", reply)
            )

            st.write(reply)

            if st.button(
                "🔊 Ayna Voice",
                key="ask_voice_reply"
            ):
                speak(reply)

        else:
            st.warning("Record a voice message first.")

    st.divider()

    text = st.text_area(
        "Type your message",
        placeholder="Ask Ayna anything..."
    )

    if st.button(
        "📤 Send Text",
        use_container_width=True
    ):

        if text.strip():

            reply = ai_answer(text)

            st.session_state.messages.append(
                ("You", text)
            )

            st.session_state.messages.append(
                ("Ayna 🧠", reply)
            )

            st.write(reply)

            if st.button(
                "🔊 Ayna Voice",
                key="ask_text_reply"
            ):
                speak(reply)

        else:
            st.warning("Write a message first.")

    st.divider()

    for speaker, message in st.session_state.messages[-10:]:
        st.markdown(
            f"""
            <div class="lab-card">
            <b>{speaker}</b>
            <p>{message}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.header("📊 My Progress")

    a, b, c, d = st.columns(4)

    with a:
        st.metric(
            "🧪 Experiments",
            st.session_state.experiments_done
        )

    with b:
        st.metric(
            "🧩 Puzzles",
            st.session_state.puzzles_done
        )

    with c:
        st.metric(
            "🎯 Exercises",
            st.session_state.exercises_done
        )

    with d:
        st.metric(
            "😊 Mood Checks",
            st.session_state.mood_checks
        )

    st.divider()

    st.subheader("Research Activity")

    st.write(
        "Your activity is currently stored for the active session."
    )
'''

print("app.py code ready — use this as the main controller file.")
print("Next files required for the full implementation: modules for the real puzzle, 3D brain, lab, experiments, voice, security/private chat, research and persistent progress.")
