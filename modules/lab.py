# modules/lab.py
# NEUROLENS — Cognitive Neuroscience Lab

import random
from datetime import date
import streamlit as st


CHARACTERS = {
    "Ayla": {
        "emoji": "👩‍🔬",
        "role": "Neuroscience Explorer",
        "description": "Curious, focused and ready for today's experiment.",
    },
    "Nova": {
        "emoji": "🧑‍🔬",
        "role": "Cognitive Scientist",
        "description": "Analytical character focused on cognition and behaviour.",
    },
    "Milo": {
        "emoji": "👨‍🔬",
        "role": "Neural Researcher",
        "description": "Explores neural circuits, memory and decision-making.",
    },
    "Zara": {
        "emoji": "👩‍💻",
        "role": "Brain Data Analyst",
        "description": "Studies patterns in cognitive performance.",
    },
}


EXPERIMENTS = [
    {
        "title": "Working Memory Challenge",
        "system": "Working Memory",
        "icon": "🧠",
        "instruction": (
            "Remember the sequence shown below, then enter it "
            "in the same order."
        ),
        "stimulus": ["7", "2", "9", "4"],
        "answer": "7294",
        "research_note": (
            "Working memory temporarily maintains and manipulates "
            "information needed for ongoing cognition."
        ),
    },
    {
        "title": "Selective Attention Test",
        "system": "Attention",
        "icon": "👁️",
        "instruction": (
            "Find the unique symbol among the distractors."
        ),
        "stimulus": ["●", "●", "●", "○", "●"],
        "answer": "○",
        "research_note": (
            "Selective attention helps prioritize relevant information "
            "while reducing interference from competing stimuli."
        ),
    },
    {
        "title": "Decision-Making Challenge",
        "system": "Decision Making",
        "icon": "🎯",
        "instruction": (
            "Choose the option with the highest expected value."
        ),
        "stimulus": [
            "A — 10 points × 90% chance",
            "B — 30 points × 40% chance",
            "C — 5 points × 100% chance",
        ],
        "answer": "A — 10 points × 90% chance",
        "research_note": (
            "Decision-making integrates reward, probability, "
            "uncertainty and current goals."
        ),
    },
    {
        "title": "Cognitive Control Test",
        "system": "Cognitive Control",
        "icon": "⚡",
        "instruction": (
            "Select the item that should be inhibited."
        ),
        "stimulus": [
            "TARGET",
            "TARGET",
            "DISTRACTOR",
            "TARGET",
        ],
        "answer": "DISTRACTOR",
        "research_note": (
            "Cognitive control supports goal-directed behaviour "
            "and suppression of inappropriate responses."
        ),
    },
    {
        "title": "Perception Challenge",
        "system": "Perception",
        "icon": "👁️",
        "instruction": (
            "Select the colour that matches the current rule."
        ),
        "stimulus": [
            "RED",
            "GREEN",
            "BLUE",
            "YELLOW",
        ],
        "answer": "BLUE",
        "research_note": (
            "Perception is influenced by sensory information, "
            "attention, context and prior knowledge."
        ),
    },
    {
        "title": "Cognitive Flexibility Test",
        "system": "Cognitive Flexibility",
        "icon": "🔄",
        "instruction": (
            "The rule has changed. Select the largest number."
        ),
        "stimulus": [
            "12",
            "48",
            "23",
            "31",
        ],
        "answer": "48",
        "research_note": (
            "Cognitive flexibility allows behaviour and attention "
            "to adapt when task rules or goals change."
        ),
    },
]


def _init_state():

    defaults = {
        "lab_character": "Ayla",
        "lab_experiment": None,
        "lab_started": False,
        "lab_answered": False,
        "lab_correct": False,
        "lab_score": 0,
        "lab_total": 0,
        "lab_completed": 0,
        "lab_feedback": "",
        "lab_history": [],
        "lab_selected_language": "English",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


def _today_experiment():

    # Stable daily experiment selection.
    # The same experiment remains available during the day.
    day_number = date.today().toordinal()

    return EXPERIMENTS[
        day_number % len(EXPERIMENTS)
    ]


def _start_experiment():

    experiment = _today_experiment()

    st.session_state.lab_experiment = experiment
    st.session_state.lab_started = True
    st.session_state.lab_answered = False
    st.session_state.lab_correct = False
    st.session_state.lab_feedback = ""
    st.session_state.lab_score = 0


def _submit_answer(answer):

    experiment = st.session_state.lab_experiment

    if not experiment:
        return

    if st.session_state.lab_answered:
        return

    st.session_state.lab_answered = True
    st.session_state.lab_total += 1

    correct = answer == experiment["answer"]

    st.session_state.lab_correct = correct

    if correct:

        st.session_state.lab_score = 100

        st.session_state.lab_completed += 1

        st.session_state.lab_feedback = (
            "✅ Correct. Your response matched today's task."
        )

    else:

        st.session_state.lab_score = 0

        st.session_state.lab_feedback = (
            "🧠 Interesting response. The next challenge "
            "can help you explore the same cognitive system."
        )

    result = {
        "date": str(date.today()),
        "experiment": experiment["title"],
        "system": experiment["system"],
        "correct": correct,
        "score": st.session_state.lab_score,
    }

    st.session_state.lab_history.append(result)

    # Keep memory lightweight.
    st.session_state.lab_history = (
        st.session_state.lab_history[-30:]
    )


def _analysis_message():

    experiment = st.session_state.lab_experiment

    if not experiment:
        return ""

    if st.session_state.lab_correct:

        return (
            f"Your response was accurate for the "
            f"{experiment['system']} task. "
            "This suggests that you successfully handled "
            "the task demand in this particular session."
        )

    return (
        f"This task targeted {experiment['system']}. "
        "Your response gives us an opportunity to explore "
        "how you approach this type of cognitive challenge."
    )


def _next_challenge():

    experiment = st.session_state.lab_experiment

    if not experiment:
        return "Continue exploring another cognitive system."

    systems = [
        item["system"]
        for item in EXPERIMENTS
        if item["system"] != experiment["system"]
    ]

    return random.choice(systems)


def _language_note():

    language = st.session_state.lab_selected_language

    if language == "Roman English":

        return (
            "Ayna Roman English mein instructions aur feedback degi."
        )

    return (
        "Ayna will provide instructions and feedback in English."
    )


def _render_character(character_name):

    character = CHARACTERS[character_name]

    st.markdown(
        f"""
        <div class="character-card">

            <div class="character-avatar">
                {character["emoji"]}
            </div>

            <div>
                <div class="character-name">
                    {character_name}
                </div>

                <div class="character-role">
                    {character["role"]}
                </div>

                <div class="character-description">
                    {character["description"]}
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def _lab_css():

    st.markdown(
        """
        <style>

        .lab-title {
            font-size: 38px;
            font-weight: 900;
            margin-bottom: 4px;
        }

        .lab-subtitle {
            color: #9ca3af;
            margin-bottom: 22px;
        }

        .lab-room {
            position: relative;
            min-height: 260px;
            padding: 25px;
            border-radius: 24px;
            overflow: hidden;

            background:
                radial-gradient(
                    circle at 50% 35%,
                    rgba(70,130,190,.24),
                    transparent 34%
                ),
                linear-gradient(
                    135deg,
                    rgba(8,18,30,.98),
                    rgba(15,28,43,.94)
                );

            border:
                1px solid rgba(120,180,230,.20);

            box-shadow:
                inset 0 0 80px rgba(0,0,0,.25);
        }

        .lab-grid {
            position: absolute;
            inset: 0;

            background-image:
                linear-gradient(
                    rgba(255,255,255,.035) 1px,
                    transparent 1px
                ),
                linear-gradient(
                    90deg,
                    rgba(255,255,255,.035) 1px,
                    transparent 1px
                );

            background-size: 35px 35px;

            animation: gridMove 12s linear infinite;
        }

        @keyframes gridMove {

            from {
                transform: translate(0,0);
            }

            to {
                transform: translate(35px,35px);
            }
        }

        .lab-orb {
            position: absolute;

            width: 135px;
            height: 135px;

            left: 50%;
            top: 50%;

            transform:
                translate(-50%,-50%);

            border-radius: 50%;

            background:
                radial-gradient(
                    circle at 35% 30%,
                    #ffffff,
                    rgba(110,190,255,.75) 12%,
                    rgba(50,100,180,.35) 40%,
                    rgba(20,40,70,.05) 70%
                );

            box-shadow:
                0 0 35px rgba(90,170,255,.45);

            animation:
                brainPulse 3s ease-in-out infinite;
        }

        .lab-orb::before,
        .lab-orb::after {

            content: "";

            position: absolute;

            inset: 15px;

            border:
                1px solid rgba(150,220,255,.35);

            border-radius: 50%;

            animation:
                rotateRing 8s linear infinite;
        }

        .lab-orb::after {

            inset: 30px;

            animation-duration: 5s;
            animation-direction: reverse;
        }

        @keyframes brainPulse {

            0%,100% {
                transform:
                    translate(-50%,-50%)
                    scale(1);
            }

            50% {
                transform:
                    translate(-50%,-50%)
                    scale(1.08);
            }
        }

        @keyframes rotateRing {

            from {
                transform: rotate(0deg);
            }

            to {
                transform: rotate(360deg);
            }
        }

        .lab-screen {

            position: absolute;

            right: 25px;
            top: 25px;

            width: 150px;
            min-height: 80px;

            padding: 12px;

            border-radius: 12px;

            background:
                rgba(0,0,0,.35);

            border:
                1px solid rgba(255,255,255,.10);

            font-size: 12px;
        }

        .lab-screen-line {

            height: 5px;
            border-radius: 10px;

            background:
                rgba(120,190,255,.45);

            margin:
                8px 0;

            animation:
                signal 1.8s ease-in-out infinite;
        }

        @keyframes signal {

            0%,100% {
                width: 35%;
            }

            50% {
                width: 90%;
            }
        }

        .character-card {

            display: flex;
            align-items: center;
            gap: 18px;

            padding: 18px;

            border-radius: 18px;

            background:
                rgba(255,255,255,.045);

            border:
                1px solid rgba(255,255,255,.10);

            margin:
                10px 0 18px;
        }

        .character-avatar {

            width: 72px;
            height: 72px;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 50%;

            background:
                rgba(100,170,230,.12);

            font-size: 42px;
        }

        .character-name {
            font-size: 21px;
            font-weight: 800;
        }

        .character-role {
            color: #a7c7e8;
            font-size: 13px;
            margin-top: 2px;
        }

        .character-description {
            color: #9ca3af;
            font-size: 13px;
            margin-top: 5px;
        }

        .experiment-card {

            padding: 22px;

            border-radius: 20px;

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,.06),
                    rgba(255,255,255,.025)
                );

            border:
                1px solid rgba(255,255,255,.10);

            margin:
                18px 0;
        }

        .experiment-icon {
            font-size: 38px;
        }

        .experiment-title {
            font-size: 25px;
            font-weight: 800;
            margin-top: 5px;
        }

        .experiment-system {
            color: #9ca3af;
            margin-top: 3px;
        }

        .stimulus-box {

            margin:
                20px 0;

            padding: 22px;

            border-radius: 18px;

            text-align: center;

            background:
                rgba(0,0,0,.22);

            border:
                1px solid rgba(255,255,255,.08);

            font-size: 28px;
            letter-spacing: 10px;
        }

        .brain-signal {

            height: 70px;

            margin:
                20px 0;

            position: relative;

            overflow: hidden;

            border-radius: 15px;

            background:
                rgba(255,255,255,.035);

            border:
                1px solid rgba(255,255,255,.08);
        }

        .signal-line {

            position: absolute;

            left: 0;
            right: 0;

            top: 50%;

            height: 2px;

            background:
                rgba(100,190,255,.45);
        }

        .signal-dot {

            position: absolute;

            width: 9px;
            height: 9px;

            border-radius: 50%;

            top: calc(50% - 4px);

            animation:
                travel 2s linear infinite;
        }

        @keyframes travel {

            from {
                left: -10px;
            }

            to {
                left: 100%;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def lab_screen():

    _init_state()
    _lab_css()

    st.markdown(
        """
        <div class="lab-title">
            🔬 Cognitive Neuroscience Lab
        </div>

        <div class="lab-subtitle">
            Enter the laboratory and explore today's cognitive experiment.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------
    # LAB ROOM
    # --------------------------------

    st.markdown(
        """
        <div class="lab-room">

            <div class="lab-grid"></div>

            <div class="lab-orb"></div>

            <div class="lab-screen">
                <b>NEURAL MONITOR</b>

                <div class="lab-screen-line"></div>
                <div class="lab-screen-line"></div>
                <div class="lab-screen-line"></div>

                <small>
                    Neural activity detected
                </small>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🧑‍🔬 Choose Your Research Character")

    character_names = list(CHARACTERS.keys())

    selected_character = st.selectbox(
        "Research character",
        character_names,
        index=character_names.index(
            st.session_state.lab_character
        ),
        key="lab_character_selector",
    )

    if selected_character != st.session_state.lab_character:

        st.session_state.lab_character = selected_character

    _render_character(
        st.session_state.lab_character
    )

    # --------------------------------
    # LANGUAGE
    # --------------------------------

    language = st.radio(
        "Ayna language",
        [
            "English",
            "Roman English",
        ],
        horizontal=True,
        key="lab_language",
    )

    st.session_state.lab_selected_language = language

    st.caption(
        _language_note()
    )

    # --------------------------------
    # TODAY'S EXPERIMENT
    # --------------------------------

    experiment = _today_experiment()

    st.markdown("---")

    st.markdown(
        """
        ### 🧪 Today's Experiment
        """
    )

    st.markdown(
        f"""
        <div class="experiment-card">

            <div class="experiment-icon">
                {experiment["icon"]}
            </div>

            <div class="experiment-title">
                {experiment["title"]}
            </div>

            <div class="experiment-system">
                Target cognitive system:
                <b>{experiment["system"]}</b>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------
    # VIDEO
    # --------------------------------

    video_path = "assets/cognitive_lab_brain.mp4"

    try:

        st.video(
            video_path,
            autoplay=True,
            loop=True,
            muted=True,
        )

    except Exception:

        st.info(
            "Cognitive Lab animation is unavailable. "
            "The experiment can still be completed."
        )

    # --------------------------------
    # START
    # --------------------------------

    if not st.session_state.lab_started:

        st.info(
            "Today's cognitive task is ready."
        )

        if st.button(
            "🧪 Enter Today's Experiment",
            use_container_width=True,
            type="primary",
        ):

            _start_experiment()
            st.rerun()

        return

    # --------------------------------
    # ACTIVE EXPERIMENT
    # --------------------------------

    experiment = st.session_state.lab_experiment

    st.markdown(
        f"""
        <div class="experiment-card">

            <div class="experiment-title">
                {experiment["title"]}
            </div>

            <p>
                {experiment["instruction"]}
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # Neural activity animation.
    st.markdown(
        """
        <div class="brain-signal">

            <div class="signal-line"></div>

            <div class="signal-dot"></div>
            <div class="signal-dot"
                 style="animation-delay:.6s;"></div>
            <div class="signal-dot"
                 style="animation-delay:1.2s;"></div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------
    # STIMULUS
    # --------------------------------

    stimulus = experiment["stimulus"]

    st.markdown(
        '<div class="stimulus-box">',
        unsafe_allow_html=True,
    )

    st.write(
        "   ".join(stimulus)
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------
    # ANSWER
    # --------------------------------

    if not st.session_state.lab_answered:

        st.write(
            "**Choose your response:**"
        )

        # Use radio rather than free text so the experiment
        # remains robust on both mobile and desktop.
        answer = st.radio(
            "Response",
            stimulus,
            key="lab_answer",
            label_visibility="collapsed",
        )

        if st.button(
            "📤 Send Response",
            use_container_width=True,
            type="primary",
        ):

            _submit_answer(answer)
            st.rerun()

    else:

        # --------------------------------
        # RESULT
        # --------------------------------

        if st.session_state.lab_correct:

            st.success(
                st.session_state.lab_feedback
            )

        else:

            st.info(
                st.session_state.lab_feedback
            )

        st.markdown(
            "### 🤖 Ayna's Cognitive Analysis"
        )

        st.write(
            _analysis_message()
        )

        st.markdown(
            "### 🧠 Research Note"
        )

        st.info(
            experiment["research_note"]
        )

        next_system = _next_challenge()

        st.markdown(
            "### 🔄 Next Cognitive Challenge"
        )

        st.write(
            f"A possible next challenge can target: "
            f"**{next_system}**"
        )

        # --------------------------------
        # VOICE OUTPUT
        # --------------------------------

        speech = (
            _analysis_message()
            + " "
            + experiment["research_note"]
        )

        safe_speech = (
            speech
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", " ")
        )

        st.markdown(
            f"""
            <button
                onclick="
                    const text = '{safe_speech}';
                    const utterance =
                        new SpeechSynthesisUtterance(text);
                    utterance.lang =
                        '{'en-US' if language == 'English' else 'en-US'}';
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(utterance);
                "
                style="
                    width:100%;
                    padding:12px;
                    border:none;
                    border-radius:12px;
                    cursor:pointer;
                    font-weight:700;
                "
            >
                🔊 Ask Ayna to Speak
            </button>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        if st.button(
            "🔬 Explore Another Experiment",
            use_container_width=True,
        ):

            st.session_state.lab_started = False
            st.session_state.lab_answered = False
            st.session_state.lab_experiment = None
            st.session_state.lab_feedback = ""

            st.rerun()


def render():
    lab_screen()
