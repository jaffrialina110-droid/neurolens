
import streamlit as st

from modules.ui import setup_page, render_brand, render_sidebar
from modules.storage import init_db
from modules.auth import render_auth, current_user, logout


setup_page()
init_db()

# Initialize app state
if "nl_user" not in st.session_state:
    st.session_state["nl_user"] = None

# Sidebar navigation
page = render_sidebar()

# Header
render_brand()
st.divider()

# Account status
user = current_user()

if user:
    st.sidebar.success(f"Welcome, {user['display_name']}")
    if st.sidebar.button("Log out", key="app_logout"):
        logout()
else:
    st.sidebar.info("You are exploring as a guest.")

# Page router
if page == "Home":
    st.title("Welcome to NeuroLens 🧠")
    st.write(
        "Explore cognition, behavior, learning, attention, "
        "memory, decision-making, and the brain."
    )

    st.subheader("Your neuroscience space")
    col1, col2 = st.columns(2)

    with col1:
        st.info("🔬 Interactive Neuroscience Lab")
        st.write("Explore cognitive tasks and learn how they work.")

    with col2:
        st.info("🌐 Brain Explorer")
        st.write("Discover brain regions and their functions.")

    st.warning(
        "NeuroLens is an educational project. Its activities do not "
        "measure brain activity or provide medical diagnoses."
    )

elif page == "Settings":
    st.title("⚙️ Settings")
    st.write("Account and app settings will be expanded in a later part.")

    if user:
        st.write(f"**Display name:** {user['display_name']}")
        st.write(f"**Username:** @{user['username']}")
        st.write(f"**Email:** {user['email']}")
        if st.button("Log out", key="settings_logout"):
            logout()
    else:
        st.info("Create an account or log in to access account features.")
        render_auth()

elif page == "Architecture & Status":
    st.title("🏗️ NeuroLens Architecture")
    st.write("**Creator:** Ayna Jaffri")
    st.write("**Platform:** Streamlit")
    st.write("**Database:** SQLite foundation")
    st.write("**Authentication:** Signup and login foundation")
    st.write("**AI integration:** To be connected in a later part")

    st.subheader("Project modules")
    modules = [
        "ui.py — branding and navigation",
        "storage.py — database foundation",
        "auth.py — signup and login",
        "brain_learning.py — brain explorer",
        "cognitive_lab.py — cognitive tasks",
        "brain_puzzle.py — brain puzzle",
        "smart_filters.py — photo filters",
        "ask_ayna.py — AI assistant",
        "neuro_emotion.py — voice and emotion reflection",
        "personal_insight.py — private journaling",
        "appointments.py — appointment requests",
        "neurosocial.py — community",
        "research_book.py — research notes",
        "progress.py — XP and achievements",
        "settings.py — settings",
    ]
    for item in modules:
        st.write(f"• {item}")

else:
    st.title(f"🚧 {page}")
    st.write("This feature will be connected in the next development parts.")
    st.info(
        "The page structure is ready. Its full functionality will be "
        "added step by step."
    )
