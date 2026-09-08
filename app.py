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
