# app.py
# NEUROLENS — Cognitive Neuroscience Interactive Lab

import os
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# GLOBAL STYLE
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 48px;
        font-weight: 900;
        letter-spacing: -1px;
        margin-bottom: 0;
    }

    .main-subtitle {
        color: #9ca3af;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .home-card {
        padding: 24px;
        border-radius: 22px;
        background: rgba(255,255,255,.045);
        border: 1px solid rgba(255,255,255,.09);
        margin-bottom: 16px;
    }

    .home-card h3 {
        margin-bottom: 7px;
    }

    .home-card p {
        color: #aab4c0;
    }

    .lab-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        background: rgba(90,170,255,.12);
        border: 1px solid rgba(90,170,255,.20);
        color: #a7d5ff;
        font-size: 13px;
        margin-bottom: 12px;
    }

    .footer {
        text-align: center;
        color: #777;
        padding: 35px 0 15px;
        font-size: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"


# =========================================================
# SAFE IMPORTS
# =========================================================

def load_module(module_name):

    try:
        return __import__(
            f"modules.{module_name}",
            fromlist=["render"],
        )

    except Exception as error:

        st.error(
            f"Module `{module_name}` could not be loaded."
        )

        with st.expander("Technical details"):
            st.code(str(error))

        return None


# =========================================================
# NAVIGATION
# =========================================================

PAGES = [
    "Home",
    "🔬 Enter Lab",
    "🧠 Explore Brain",
    "🧩 Brain Puzzle",
    "😊 AI Mood & Behaviour",
    "⚡ Brain Exercises",
    "📖 Research Book",
    "💬 Ask Ayna",
    "🔐 Private Ask Ayna",
    "📊 My Progress",
]


def go_to(page):

    st.session_state.page = page
    st.session_state.nav_page = page


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size:30px;
            font-weight:900;
            margin-bottom:0;
        ">
            🧠 NEUROLENS
        </div>

        <div style="
            color:#9ca3af;
            margin-bottom:22px;
        ">
            Explore cognition, behaviour & the brain
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_page = st.radio(
        "Navigate",
        PAGES,
        key="nav_page",
    )

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page


# =========================================================
# HOME
# =========================================================

def home_screen():

    st.markdown(
        """
        <div class="lab-badge">
            COGNITIVE NEUROSCIENCE LAB
        </div>

        <div class="main-title">
            NEUROLENS
        </div>

        <div class="main-subtitle">
            Explore cognition, behaviour & the brain
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="home-card">

        <h2>🔬 Welcome to the Lab</h2>

        <p>
        Explore the brain through interactive experiments,
        neural journeys, cognitive challenges and research notes.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # MAIN ACTIONS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "🔬 Enter Lab",
            use_container_width=True,
            type="primary",
        ):
            go_to("🔬 Enter Lab")
            st.rerun()

        if st.button(
            "🧠 Explore Brain",
            use_container_width=True,
        ):
            go_to("🧠 Explore Brain")
            st.rerun()

        if st.button(
            "🧩 Brain Puzzle",
            use_container_width=True,
        ):
            go_to("🧩 Brain Puzzle")
            st.rerun()

    with col2:

        if st.button(
            "😊 AI Mood & Behaviour",
            use_container_width=True,
        ):
            go_to("😊 AI Mood & Behaviour")
            st.rerun()

        if st.button(
            "⚡ Brain Exercises",
            use_container_width=True,
        ):
            go_to("⚡ Brain Exercises")
            st.rerun()

        if st.button(
            "📖 Research Book",
            use_container_width=True,
        ):
            go_to("📖 Research Book")
            st.rerun()

    with col3:

        if st.button(
            "💬 Ask Ayna",
            use_container_width=True,
        ):
            go_to("💬 Ask Ayna")
            st.rerun()

        if st.button(
            "🔐 Private Ask Ayna",
            use_container_width=True,
        ):
            go_to("🔐 Private Ask Ayna")
            st.rerun()

        if st.button(
            "📊 My Progress",
            use_container_width=True,
        ):
            go_to("📊 My Progress")
            st.rerun()

    # -----------------------------------------------------
    # PLATFORM MAP
    # -----------------------------------------------------

    st.markdown("---")

    st.markdown("### 🧠 NEUROLENS Research Map")

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="home-card">

            <h3>🧪 Experimental Layer</h3>

            <p>
            Daily cognitive experiments, attention,
            working memory, decision-making, perception,
            cognitive control and flexibility.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="home-card">

            <h3>🧬 Neural Layer</h3>

            <p>
            Brain → region → neural pathway → neuron →
            axon → myelin → signal → synapse →
            neurotransmitter → behaviour.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="home-card">

            <h3>🎯 Cognitive Layer</h3>

            <p>
            Brain exercises, puzzles, adaptive challenges
            and performance tracking.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="home-card">

            <h3>📚 Research Layer</h3>

            <p>
            Cognitive neuroscience concepts, research notes,
            deeper terminology and scientific learning.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="footer">
            NEUROLENS · Created by Ayna Jaffri
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# BRAIN EXPLORER FALLBACK
# =========================================================

def brain_fallback():

    st.markdown(
        """
        <div class="main-title">
            🧠 Explore Brain
        </div>

        <div class="main-subtitle">
            Explore major cognitive and neural systems.
        </div>
        """,
        unsafe_allow_html=True,
    )

    regions = {
        "Prefrontal Cortex":
            "Planning, decision-making and cognitive control.",

        "Hippocampus":
            "Memory formation and spatial learning.",

        "Amygdala":
            "Emotion, threat processing and salience.",

        "Striatum":
            "Action selection, reward and habit learning.",

        "Anterior Cingulate Cortex":
            "Conflict monitoring and cognitive control.",

        "Cerebellum":
            "Motor coordination and contributions to cognition.",
    }

    region = st.selectbox(
        "Select a brain region",
        list(regions.keys()),
    )

    st.info(
        regions[region]
    )


# =========================================================
# BRAIN JOURNEY
# =========================================================

def brain_screen():

    module = load_module("brain_journey")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Brain Journey encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))

            brain_fallback()

    else:

        brain_fallback()


# =========================================================
# LAB
# =========================================================

def lab_screen():

    module = load_module("lab")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Cognitive Lab encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# PUZZLE
# =========================================================

def puzzle_screen():

    module = load_module("puzzle")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Brain Puzzle encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# BEHAVIOUR
# =========================================================

def behaviour_screen():

    module = load_module("behaviour")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Behaviour Lab encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# EXERCISES
# =========================================================

def exercises_screen():

    module = load_module("exercises")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Brain Exercises encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# RESEARCH
# =========================================================

def research_screen():

    module = load_module("research")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Research Book encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# ASK AYNA
# =========================================================

def ask_ayna_screen():

    module = load_module("ayna")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Ask Ayna encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# PRIVATE ASK AYNA
# =========================================================

def private_ayna_screen():

    module = load_module("security")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Private Ask Ayna encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# PROGRESS
# =========================================================

def progress_screen():

    module = load_module("progress")

    if module is not None:

        try:
            module.render()

        except Exception as error:

            st.error(
                "Progress dashboard encountered an error."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(str(error))


# =========================================================
# MAIN ROUTER
# =========================================================

page = st.session_state.page


if page == "Home":

    home_screen()

elif page == "🔬 Enter Lab":

    lab_screen()

elif page == "🧠 Explore Brain":

    brain_screen()

elif page == "🧩 Brain Puzzle":

    puzzle_screen()

elif page == "😊 AI Mood & Behaviour":

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


# =========================================================
# GLOBAL FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        NEUROLENS · Cognitive Neuroscience · AI · Behaviour · Brain
    </div>
    """,
    unsafe_allow_html=True,
)
# ============================================================
# BRAIN EXERCISES
# ============================================================

elif st.session_state.page == "Brain Exercises":

    st.subheader("🧠 AI Brain Exercises")

    st.caption(
        "Train attention, memory, decision-making, "
        "inhibitory control and cognitive flexibility."
    )

    exercise_bank = [
        {
            "name": "Attention",
            "question": (
                "Count how many times the letter A appears "
                "in this sequence: A B C A D A B C D A"
            ),
            "answer": "4",
            "explanation": (
                "This task focuses on selective attention "
                "and sustained attention."
            ),
        },
        {
            "name": "Working Memory",
            "question": (
                "Remember these numbers for a few seconds: "
                "7 - 2 - 9 - 4 - 1. "
                "What was the third number?"
            ),
            "answer": "9",
            "explanation": (
                "Working memory temporarily maintains "
                "and manipulates information."
            ),
        },
        {
            "name": "Inhibitory Control",
            "question": (
                "Which word is the odd one out: "
                "RED, RED, BLUE, RED?"
            ),
            "answer": "BLUE",
            "explanation": (
                "Inhibitory control helps suppress "
                "automatic or dominant responses."
            ),
        },
        {
            "name": "Decision Making",
            "question": (
                "Option A gives a guaranteed 5 points. "
                "Option B gives either 10 points or 0 points. "
                "Which option is more certain?"
            ),
            "answer": "A",
            "explanation": (
                "Decision-making often involves balancing "
                "risk, reward and uncertainty."
            ),
        },
        {
            "name": "Cognitive Flexibility",
            "question": (
                "If you normally sort objects by colour, "
                "but the rule suddenly changes to shape, "
                "what cognitive ability is being used?"
            ),
            "answer": "Cognitive flexibility",
            "explanation": (
                "Cognitive flexibility allows the brain "
                "to switch between rules or strategies."
            ),
        },
    ]

    if "exercise_index" not in st.session_state:
        st.session_state.exercise_index = 0

    if "exercise_answered" not in st.session_state:
        st.session_state.exercise_answered = False

    exercise = exercise_bank[
        st.session_state.exercise_index
        % len(exercise_bank)
    ]

    st.markdown(
        f"### 🎯 {exercise['name']}"
    )

    st.progress(
        (
            st.session_state.exercise_index + 1
        )
        / len(exercise_bank)
    )

    st.markdown(
        f"""
        <div class="card">
        <h3>🧩 Cognitive Challenge</h3>
        <p>{exercise['question']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.text_input(
        "Your answer",
        key=(
            f"exercise_answer_"
            f"{st.session_state.exercise_index}"
        ),
    )

    if st.button(
        "Check Answer",
        use_container_width=True,
        key=(
            f"check_exercise_"
            f"{st.session_state.exercise_index}"
        ),
    ):

        correct = (
            answer.strip().lower()
            == exercise["answer"].lower()
        )

        st.session_state.exercise_answered = True

        if correct:

            st.success(
                "🎉 Correct!"
            )

            st.session_state.exercise_score += 1

        else:

            st.error(
                f"Not quite. Correct answer: "
                f"{exercise['answer']}"
            )

        st.info(
            exercise["explanation"]
        )

        record(
            "exercises"
        )

        st.session_state.ai_requests += 0

    if st.session_state.exercise_answered:

        if st.button(
            "➡️ Next Cognitive Challenge",
            use_container_width=True,
            key="next_exercise",
        ):

            st.session_state.exercise_index += 1

            st.session_state.exercise_answered = False

            st.rerun()

    st.divider()

    st.markdown(
        "### 🧠 Training pathway"
    )

    pathway = [
        "Attention",
        "Working Memory",
        "Memory",
        "Decision Making",
        "Inhibitory Control",
        "Cognitive Flexibility",
    ]

    for i, item in enumerate(pathway):

        status = (
            "🟢"
            if i <= st.session_state.exercise_index
            else "⚪"
        )

        st.write(
            f"{status} {item}"
        )

    st.caption(
        "These exercises are educational cognitive tasks, "
        "not clinical assessments."
    )


# ============================================================
# RESEARCH BOOK
# ============================================================

elif st.session_state.page == "Research Book":

    st.subheader(
        "📖 NEUROLENS Research Book"
    )

    st.caption(
        "Explore cognitive neuroscience from basic concepts "
        "to research-level terminology."
    )

    research_topics = {
        "Brain & Behaviour": {
            "simple": (
                "The brain continuously interacts with the "
                "body and environment to produce behaviour."
            ),
            "research": (
                "Behaviour emerges from distributed neural "
                "systems involving perception, action, "
                "learning, motivation and cognitive control."
            ),
        },
        "Memory": {
            "simple": (
                "Memory allows information and experiences "
                "to be encoded, stored and retrieved."
            ),
            "research": (
                "Memory involves interacting systems including "
                "working memory, episodic memory, semantic memory "
                "and procedural learning."
            ),
        },
        "Attention": {
            "simple": (
                "Attention helps the brain select information "
                "that is relevant at a given moment."
            ),
            "research": (
                "Attention involves distributed frontoparietal "
                "and subcortical systems that regulate selection "
                "and allocation of processing resources."
            ),
        },
        "Perception": {
            "simple": (
                "Perception is the process through which the "
                "brain interprets sensory information."
            ),
            "research": (
                "Perception reflects interactions between "
                "bottom-up sensory signals and top-down "
                "expectations, priors and context."
            ),
        },
        "Emotion": {
            "simple": (
                "Emotion influences attention, memory, decisions "
                "and behaviour."
            ),
            "research": (
                "Affective processing involves distributed "
                "networks including amygdala, prefrontal, "
                "striatal and autonomic systems."
            ),
        },
        "Decision-making": {
            "simple": (
                "Decision-making involves choosing between "
                "different options."
            ),
            "research": (
                "Decision behaviour can be studied through "
                "value representation, uncertainty, learning, "
                "reward prediction and cognitive control."
            ),
        },
        "Learning": {
            "simple": (
                "Learning changes behaviour or knowledge "
                "through experience."
            ),
            "research": (
                "Learning involves synaptic plasticity, "
                "reinforcement learning, memory systems and "
                "changes in network-level representations."
            ),
        },
        "Cognitive Control": {
            "simple": (
                "Cognitive control helps us regulate behaviour "
                "according to goals."
            ),
            "research": (
                "Cognitive control includes monitoring, "
                "inhibition, task switching and goal-directed "
                "regulation involving prefrontal and "
                "frontostriatal systems."
            ),
        },
        "Reward": {
            "simple": (
                "Reward influences motivation and learning."
            ),
            "research": (
                "Reward processing involves interactions "
                "between dopaminergic systems, striatum, "
                "prefrontal regions and learning mechanisms."
            ),
        },
        "Executive Functions": {
            "simple": (
                "Executive functions help us plan, control "
                "and adapt our behaviour."
            ),
            "research": (
                "Executive functions include working memory, "
                "inhibitory control and cognitive flexibility."
            ),
        },
        "Neuroplasticity": {
            "simple": (
                "Neuroplasticity refers to the nervous system's "
                "capacity to change with experience."
            ),
            "research": (
                "Plasticity can involve synaptic changes, "
                "network reorganization and experience-dependent "
                "modification of neural representations."
            ),
        },
        "Neural Circuits": {
            "simple": (
                "Brain functions are supported by connected "
                "neural circuits."
            ),
            "research": (
                "Cognitive processes emerge from interactions "
                "among distributed cortical, subcortical and "
                "thalamic networks."
            ),
        },
        "Neurotransmitters": {
            "simple": (
                "Neurotransmitters are chemical messengers "
                "used in neural communication."
            ),
            "research": (
                "Major neurotransmitter systems include "
                "dopamine, serotonin, acetylcholine, glutamate "
                "and GABA, each acting across distributed "
                "receptor and circuit systems."
            ),
        },
    }

    topic = st.selectbox(
        "Choose a research topic",
        list(research_topics.keys()),
        key="research_topic",
    )

    mode = st.radio(
        "Reading mode",
        [
            "Simple Mode",
            "Research Mode",
        ],
        horizontal=True,
        key="research_mode",
    )

    topic_data = research_topics[
        topic
    ]

    st.markdown(
        f"## 🧠 {topic}"
    )

    if mode == "Simple Mode":

        st.write(
            topic_data["simple"]
        )

    else:

        st.write(
            topic_data["research"]
        )

        st.markdown(
            "### 🔬 Research note"
        )

        st.write(
            "Research-level interpretation depends on "
            "experimental design, population, measurement "
            "method and the specific literature."
        )

    if st.button(
        "🧠 Ask Ayna about this topic",
        use_container_width=True,
        key="research_ask",
    ):

        st.session_state.page = "Ask Ayna"

        st.session_state.prefill_question = (
            f"Explain {topic} in cognitive neuroscience."
        )

        st.rerun()


# ============================================================
# ASK AYNA
# ============================================================

elif st.session_state.page == "Ask Ayna":

    st.subheader(
        "💬 Ask Ayna"
    )

    st.caption(
        "Your cognitive neuroscience and general AI assistant."
    )

    if "chat_messages" not in st.session_state:

        st.session_state.chat_messages = []

    for message in st.session_state.chat_messages:

        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        with st.chat_message(
            role
        ):

            st.write(
                content
            )

    prefill = st.session_state.pop(
        "prefill_question",
        "",
    )

    question = st.chat_input(
        "Ask Ayna anything..."
    )

    if prefill and not question:

        question = prefill

    if question:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message(
            "user"
        ):

            st.write(
                question
            )

        context_messages = (
            st.session_state.chat_messages[-8:]
        )

        conversation = "\n".join(
            [
                f"{m['role']}: {m['content']}"
                for m in context_messages
            ]
        )

        answer, source = ask_ai(
            question,
            context=conversation,
            max_tokens=450,
        )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message(
            "assistant"
        ):

            st.write(
                answer
            )

            voice_button(
                answer,
                "ask_ayna_voice",
            )


# ============================================================
# PRIVATE ASK AYNA
# ============================================================

elif st.session_state.page == "Private Ask Ayna":

    st.subheader(
        "🔐 Private Ask Ayna"
    )

    st.caption(
        "Private conversational space for your NEUROLENS session."
    )

    if not st.session_state.private_unlocked:

        st.markdown(
            """
            <div class="card">
            <h3>🔒 Private Chat</h3>
            <p>
            Enter your session PIN to access Private Ask Ayna.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pin = st.text_input(
            "PIN",
            type="password",
            key="private_pin",
        )

        if st.button(
            "Unlock",
            use_container_width=True,
            key="unlock_private",
        ):

            if pin == st.session_state.private_pin:

                st.session_state.private_unlocked = True

                st.success(
                    "Private chat unlocked."
                )

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )

    else:

        st.success(
            "🔓 Private session active"
        )

        if "private_messages" not in st.session_state:

            st.session_state.private_messages = []

        for message in (
            st.session_state.private_messages
        ):

            with st.chat_message(
                message["role"]
            ):

                st.write(
                    message["content"]
                )

        private_question = st.chat_input(
            "Talk privately with Ayna..."
        )

        if private_question:

            st.session_state.private_messages.append(
                {
                    "role": "user",
                    "content": private_question,
                }
            )

            with st.chat_message(
                "user"
            ):

                st.write(
                    private_question
                )

            context = "\n".join(
                [
                    f"{m['role']}: {m['content']}"
                    for m in (
                        st.session_state
                        .private_messages[-8:]
                    )
                ]
            )

            answer, source = ask_ai(
                private_question,
                context=context,
                max_tokens=400,
            )

            st.session_state.private_messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            with st.chat_message(
                "assistant"
            ):

                st.write(
                    answer
                )

                voice_button(
                    answer,
                    "private_answer_voice",
                )

        if st.button(
            "🔒 Lock Private Chat",
            use_container_width=True,
            key="lock_private",
        ):

            st.session_state.private_unlocked = False

            st.rerun()


# ============================================================
# MY PROGRESS
# ============================================================

elif st.session_state.page == "My Progress":

    st.subheader(
        "📊 My Progress"
    )

    st.caption(
        "Track your NEUROLENS learning and cognitive practice."
    )

    experiments_done = (
        st.session_state.metrics.get(
            "experiments",
            0,
        )
    )

    puzzles_done = (
        st.session_state.metrics.get(
            "puzzles",
            0,
        )
    )

    exercises_done = (
        st.session_state.metrics.get(
            "exercises",
            0,
        )
    )

    total_activity = (
        experiments_done
        + puzzles_done
        + exercises_done
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Experiments",
            experiments_done,
        )

    with c2:

        st.metric(
            "Puzzle Practice",
            puzzles_done,
        )

    with c3:

        st.metric(
            "Exercises",
            exercises_done,
        )

    st.divider()

    st.markdown(
        "### 🧠 Cognitive training score"
    )

    score = (
        st.session_state.exercise_score
    )

    st.metric(
        "Exercise Score",
        score,
    )

    st.progress(
        min(
            score / 10,
            1.0,
        )
    )

    st.divider()

    st.markdown(
        "### 📚 Research learning"
    )

    st.write(
        "Current research topic:"
    )

    st.write(
        st.session_state.get(
            "research_topic",
            "Not selected yet",
        )
    )

    st.divider()

    st.markdown(
        "### 🔥 NEUROLENS activity"
    )

    st.write(
        f"Total recorded activities: "
        f"**{total_activity}**"
    )

    st.info(
        "Progress is currently stored for your active "
        "session. A persistent account/database system "
        "would be required for cross-device permanent history."
    )

    if st.button(
        "🧹 Reset Session Progress",
        use_container_width=True,
        key="reset_progress",
    ):

        st.session_state.metrics = {
            "experiments": 0,
            "puzzles": 0,
            "exercises": 0,
        }

        st.session_state.exercise_score = 0

        st.success(
            "Session progress reset."
        )

        st.rerun()


# ============================================================
# GLOBAL FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:40px;
        padding:20px;
        opacity:0.75;
    ">
        <b>NEUROLENS</b><br>
        Explore cognition, behaviour & the brain<br><br>
        Created by <b>Ayna Jaffri</b>
    </div>
    """,
    unsafe_allow_html=True,
)
