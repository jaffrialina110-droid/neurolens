import streamlit as st
from pathlib import Path

# =========================================================
# NEUROLENS — BRAIN JOURNEY
# =========================================================

BASE = Path(__file__).resolve().parent.parent
ASSETS = BASE / "assets"

BRAIN_VIDEO = ASSETS / "brain_animation.mp4"


# =========================================================
# JOURNEY DATA
# =========================================================

JOURNEY_STAGES = [
    {
        "name": "Whole Brain",
        "icon": "🧠",
        "description": (
            "The brain works as a distributed network. "
            "Different regions and circuits contribute to "
            "cognition, emotion, perception and behaviour."
        ),
        "question": "What does the brain do?",
    },
    {
        "name": "Brain Region",
        "icon": "🔬",
        "description": (
            "Different brain regions have specialised roles "
            "while communicating with other regions."
        ),
        "question": "How do brain regions work together?",
    },
    {
        "name": "Neural Circuit",
        "icon": "🕸️",
        "description": (
            "Cognitive processes emerge from communication "
            "across interconnected neural circuits."
        ),
        "question": "What is a neural circuit?",
    },
    {
        "name": "Neuron",
        "icon": "🧬",
        "description": (
            "Neurons are specialised cells that receive, "
            "process and transmit information."
        ),
        "question": "How does a neuron communicate?",
    },
    {
        "name": "Dendrites",
        "icon": "🌿",
        "description": (
            "Dendrites receive many incoming signals from "
            "other neurons."
        ),
        "question": "What do dendrites do?",
    },
    {
        "name": "Axon",
        "icon": "➖",
        "description": (
            "The axon carries electrical signals away "
            "from the neuronal cell body."
        ),
        "question": "How does an axon carry information?",
    },
    {
        "name": "Myelin",
        "icon": "⚡",
        "description": (
            "Myelin forms insulating segments around many "
            "axons and supports efficient signal conduction."
        ),
        "question": "Why is myelin important?",
    },
    {
        "name": "Electrical Signal",
        "icon": "⚡",
        "description": (
            "An action potential is an electrical event "
            "that propagates along an excitable neuron."
        ),
        "question": "What is an action potential?",
    },
    {
        "name": "Synapse",
        "icon": "🔗",
        "description": (
            "A synapse is a specialised communication point "
            "between neurons."
        ),
        "question": "What happens at a synapse?",
    },
    {
        "name": "Neurotransmitter",
        "icon": "🧪",
        "description": (
            "Neurotransmitters are chemical signalling "
            "molecules involved in communication between cells."
        ),
        "question": "What are neurotransmitters?",
    },
    {
        "name": "Cognition & Behaviour",
        "icon": "💭",
        "description": (
            "Distributed neural systems support cognitive "
            "processes such as attention, memory, decision "
            "making and behavioural regulation."
        ),
        "question": "How does brain activity influence behaviour?",
    },
]


# =========================================================
# VIDEO
# =========================================================

def show_brain_video():

    if BRAIN_VIDEO.exists():

        st.video(
            str(BRAIN_VIDEO)
        )

    else:

        st.warning(
            "brain_animation.mp4 was not found in assets/."
        )


# =========================================================
# ANIMATED NEURAL VISUAL
# =========================================================

def neural_animation(stage):

    st.markdown(
        f"""
        <style>

        .neural-scene {{
            width:100%;
            min-height:300px;
            border-radius:24px;
            position:relative;
            overflow:hidden;

            background:
                radial-gradient(
                    circle at center,
                    rgba(73,180,255,.25),
                    transparent 25%
                ),
                radial-gradient(
                    circle at 20% 70%,
                    rgba(130,80,255,.18),
                    transparent 25%
                ),
                #06111f;

            border:1px solid rgba(100,210,255,.22);
        }}

        .core-brain {{
            position:absolute;
            left:50%;
            top:50%;
            transform:translate(-50%,-50%);

            width:130px;
            height:130px;

            border-radius:50%;

            background:
                radial-gradient(
                    circle,
                    #8de6ff 0%,
                    #477cff 25%,
                    #302060 55%,
                    transparent 72%
                );

            box-shadow:
                0 0 30px rgba(90,210,255,.8),
                0 0 90px rgba(80,100,255,.45);

            animation:brainPulse 2.2s infinite;
        }}

        .signal {{
            position:absolute;
            width:10px;
            height:10px;
            border-radius:50%;
            background:#a5efff;
            box-shadow:0 0 15px #7eeaff;
            animation:moveSignal 2.5s linear infinite;
        }}

        .signal.s1 {{
            top:48%;
            left:10%;
        }}

        .signal.s2 {{
            top:30%;
            left:20%;
            animation-delay:.6s;
        }}

        .signal.s3 {{
            top:65%;
            left:25%;
            animation-delay:1.2s;
        }}

        .signal.s4 {{
            top:40%;
            left:75%;
            animation-delay:1.7s;
        }}

        @keyframes brainPulse {{
            0%,100% {{
                transform:translate(-50%,-50%) scale(1);
            }}

            50% {{
                transform:translate(-50%,-50%) scale(1.08);
            }}
        }}

        @keyframes moveSignal {{
            0% {{
                transform:translateX(0);
                opacity:.1;
            }}

            50% {{
                opacity:1;
            }}

            100% {{
                transform:translateX(180px);
                opacity:.1;
            }}
        }}

        .scene-title {{
            position:absolute;
            top:20px;
            left:25px;
            color:#dff7ff;
            font-size:20px;
            font-weight:700;
        }}

        </style>

        <div class="neural-scene">

            <div class="scene-title">
                {stage}
            </div>

            <div class="core-brain"></div>

            <div class="signal s1"></div>
            <div class="signal s2"></div>
            <div class="signal s3"></div>
            <div class="signal s4"></div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# AYNА STAGE VOICE
# =========================================================

def stage_voice(text):

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

            window.speechSynthesis.cancel();

            const voice =
                new SpeechSynthesisUtterance(text);

            voice.lang = "en-US";
            voice.rate = 0.94;
            voice.pitch = 1.0;

            window.speechSynthesis.speak(voice);
        }}

        </script>
        """,
        height=1
    )


# =========================================================
# MAIN JOURNEY
# =========================================================

def render_brain_journey(
    ai_function=None
):

    st.header(
        "🧠 Inside-Brain Journey"
    )

    st.caption(
        "Travel from the whole brain toward the neural and synaptic level."
    )

    # -----------------------------------------------------
    # VIDEO
    # -----------------------------------------------------

    show_brain_video()

    # -----------------------------------------------------
    # STAGE
    # -----------------------------------------------------

    if "journey_stage" not in st.session_state:

        st.session_state.journey_stage = 0

    current_index = st.session_state.journey_stage

    current = JOURNEY_STAGES[
        current_index
    ]

    # -----------------------------------------------------
    # ANIMATION
    # -----------------------------------------------------

    neural_animation(
        current["name"]
    )

    st.write("")

    # -----------------------------------------------------
    # STAGE INFORMATION
    # -----------------------------------------------------

    st.markdown(
        f"""
        <div style="
            padding:22px;
            border-radius:20px;
            background:rgba(15,35,55,.8);
            border:1px solid rgba(120,210,255,.18);
        ">

        <h2>
        {current["icon"]}
        {current["name"]}
        </h2>

        <p style="font-size:17px;">
        {current["description"]}
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    # -----------------------------------------------------
    # AYNА VOICE
    # -----------------------------------------------------

    if st.button(
        "🔊 Ayna — Explain this stage",
        use_container_width=True
    ):

        stage_voice(
            current["description"]
        )

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    left, center, right = st.columns(
        [1, 2, 1]
    )

    with left:

        if current_index > 0:

            if st.button(
                "⬅ Previous",
                use_container_width=True
            ):

                st.session_state.journey_stage -= 1
                st.rerun()

    with center:

        st.markdown(
            f"""
            <div style="text-align:center;">
            <b>
            Stage {current_index + 1}
            / {len(JOURNEY_STAGES)}
            </b>
            </div>
            """,
            unsafe_allow_html=True
        )

    with right:

        if current_index < len(JOURNEY_STAGES) - 1:

            if st.button(
                "Next ➡",
                use_container_width=True
            ):

                st.session_state.journey_stage += 1
                st.rerun()

    # -----------------------------------------------------
    # ASK AYNA — CONTEXTUAL
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "💬 Ask Ayna about this stage"
    )

    question = st.text_input(
        current["question"],
        key=f"journey_question_{current_index}"
    )

    if st.button(
        "📤 Send to Ayna",
        key=f"journey_send_{current_index}",
        use_container_width=True
    ):

        if not question.strip():

            st.warning(
                "Write a question first."
            )

        elif ai_function is not None:

            answer = ai_function(
                f"""
                The user is currently exploring:

                {current["name"]}

                Explain the concept in relation
                to cognitive neuroscience.

                User question:
                {question}
                """
            )

            st.markdown(
                "### 🧠 Ayna"
            )

            st.write(answer)

            if st.button(
                "🔊 Hear Ayna",
                key=f"hear_{current_index}"
            ):

                stage_voice(answer)

        else:

            st.info(
                "Ayna AI connection will be supplied by the main app."
            )


# =========================================================
# EXPORT
# =========================================================

__all__ = [
    "render_brain_journey",
    "JOURNEY_STAGES",
]
