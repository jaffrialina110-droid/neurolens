
import streamlit as st

APP_NAME = "NEUROLENS"
CREATOR = "Ayna Jaffri"
TAGLINE = "Explore cognition, behavior & the brain"

PAGES = [
    "Home",
    "Brain Explorer",
    "Interactive Neuroscience Lab",
    "Brain Puzzle",
    "AI Smart Filters",
    "Voice & Neuro-Emotion",
    "Ask Ayna AI",
    "Personal Insight",
    "Personal Appointment",
    "NeuroSocial",
    "Research Book",
    "Progress Dashboard",
    "Settings",
    "Architecture & Status",
]


def setup_page():
    st.set_page_config(
        page_title="NeuroLens | Ayna Jaffri",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1250px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.2);
        }
        .neurolens-subtitle {
            color: #7FAED6;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand():
    st.markdown("# 🧠 NEUROLENS")
    st.markdown(
        f'<div class="neurolens-subtitle">{TAGLINE}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Created by {CREATOR}")


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🧠 NeuroLens")
        st.caption("Cognitive Neuroscience × AI")

        page = st.radio(
            "Explore NeuroLens",
            PAGES,
            index=0,
            key="neurolens_page",
        )

        st.divider()
        st.caption("Learn • Explore • Reflect")

    return page
