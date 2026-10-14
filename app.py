
import streamlit as st

st.set_page_config(
    page_title="NeuroLens | Ayna Jaffri",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- STYLE ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #071329, #111a36 55%, #191638);
    color: #f3f5ff;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1250px;
}
[data-testid="stSidebar"] {
    background: #0b1228;
    border-right: 1px solid #283653;
}
.hero {
    padding: 28px;
    border-radius: 24px;
    background: linear-gradient(120deg, #182d54, #302452);
    border: 1px solid #40517a;
    margin-bottom: 22px;
}
.hero h1 {
    color: #ffffff;
    font-size: 42px;
    margin-bottom: 8px;
}
.hero p {
    color: #c5d2f5;
    font-size: 17px;
}
.panel {
    background: rgba(20, 31, 60, 0.92);
    border: 1px solid #33476c;
    border-radius: 18px;
    padding: 20px;
    min-height: 145px;
    margin-bottom: 14px;
}
.panel h3 {
    color: #d8e5ff;
    font-size: 19px;
}
.panel p {
    color: #bac7e7;
}
.small-note {
    color: #9caed2;
    font-size: 13px;
}
div.stButton > button {
    border-radius: 12px;
    border: 1px solid #526b9b;
    background: #1d3157;
    color: white;
    min-height: 42px;
}
div.stButton > button:hover {
    background: #344b79;
    border-color: #93b6ff;
}
</style>
/* MOBILE RESPONSIVE FIX */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.8rem 2rem 0.8rem !important;
        max-width: 100% !important;
    }

    .hero {
        padding: 18px !important;
        border-radius: 16px !important;
        overflow-wrap: anywhere;
    }

    .hero h1 {
        font-size: 28px !important;
        line-height: 1.25 !important;
    }

    .hero p {
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    .panel {
        padding: 16px !important;
        min-height: auto !important;
        overflow-wrap: anywhere;
    }

    .panel h3 {
        font-size: 17px !important;
    }

    .panel p {
        font-size: 14px !important;
        line-height: 1.6 !important;
    }

    div.stButton > button {
        min-height: 44px !important;
        white-space: normal !important;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------- NAVIGATION ----------
PAGES = [
    "Welcome",
    "NeuroWorld",
    "Interactive Lab",
    "Brain Journey",
    "Brain Explorer",
    "Brain Puzzle",
    "Brain Exercises",
    "Ask Ayna",
    "Voice to Emoji",
    "Mood & Feelings",
    "Behaviour Decoding",
    "Healing & Personal Insight",
    "Visual Memory Map",
    "Research Book",
    "Private Space",
    "NeuroSocial",
    "Eye Tracking Lab",
    "EEG & Biosignals",
    "Progress Dashboard",
    "Settings"
]

if "nl_page" not in st.session_state:
    st.session_state.nl_page = "Welcome"

def go_to(page):
    st.session_state.nl_page = page

def panel(title, description, icon="🧠"):
    st.markdown(
        f"""
        <div class="panel">
            <h3>{icon} {title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("## 🧠 NeuroLens")
    st.caption("Explore cognition, behaviour & the brain")
    st.markdown("---")

    for page in PAGES:
        if page == "Welcome":
            continue
        if st.button(
            page,
            key="nav_" + page,
            use_container_width=True
        ):
            go_to(page)

    st.markdown("---")
    st.markdown("**Created by Ayna Jaffri**")
    st.caption("Independent cognitive neuroscience researcher")

page = st.session_state.nl_page

# ---------- WELCOME ----------
if page == "Welcome":
    st.markdown("""
    <div class="hero">
        <h1>🧠 Welcome to NeuroLens</h1>
        <p>Explore your mind. Discover the brain. Understand behaviour.</p>
        <p>Interactive neuroscience, cognitive experiments and personal insight.</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.3, 1])

    with left:
        st.markdown("### Meet Ayna")
        st.write(
            "Your guide through the NeuroLens world of cognition, "
            "neuroscience and behaviour."
        )
        st.markdown("### Explore the experience")
        st.write(
            "Learn about brain regions, explore cognitive tasks, "
            "reflect on personal goals and discover research."
        )

        if st.button(
            "🚀 Enter NeuroLens",
            key="enter_neurolens",
            use_container_width=True
        ):
            go_to("NeuroWorld")
            st.rerun()

    with right:
        st.markdown("""
        <div class="panel" style="text-align:center;min-height:260px;">
            <div style="font-size:75px;">🧠</div>
            <div style="font-size:45px;">🤖</div>
            <h3>Ayna & NeuroBot</h3>
            <p>Your interactive neuroscience environment</p>
        </div>
        """, unsafe_allow_html=True)

    st.caption(
        "UI prototype: AI, accounts, database and experiments "
        "are not connected yet."
    )

# ---------- NEUROWORLD ----------
elif page == "NeuroWorld":
    st.markdown("""
    <div class="hero">
        <h1>🌌 NeuroLens World</h1>
        <p>Your central hub for neuroscience, cognition and discovery.</p>
    </div>
    """, unsafe_allow_html=True)

    a, b, c = st.columns(3)
    with a:
        panel("Ayna", "Your learning and reflection guide.", "👩‍🔬")
    with b:
        panel("NeuroBot", "Your future interactive AI companion.", "🤖")
    with c:
        panel("Neural Lab", "A home for cognitive experiments.", "🔬")

    st.markdown("### Choose your destination")

    destinations = [
        ("Interactive Lab", "Attention, memory, reaction and decision tasks.", "🔬"),
        ("Brain Journey", "Brain regions, circuits, neurons and synapses.", "🧬"),
        ("Brain Explorer", "Explore selected brain regions.", "🧠"),
        ("Brain Puzzle", "A future interactive brain assembly puzzle.", "🧩"),
        ("Ask Ayna", "A future text and voice assistant.", "💬"),
        ("Healing & Personal Insight", "Journaling, goals and reflection.", "🌱"),
        ("Behaviour Decoding", "Review task results and reflect on patterns.", "🔍"),
        ("Research Book", "A future neuroscience literature workspace.", "📚"),
        ("NeuroSocial", "A future social learning environment.", "🌐")
    ]

    columns = st.columns(3)

    for index, (name, description, icon) in enumerate(destinations):
        with columns[index % 3]:
            panel(name, description, icon)
            if st.button(
                "Open " + name,
                key="open_" + name,
                use_container_width=True
            ):
                go_to(name)
                st.rerun()

# ---------- MODULE SCREENS ----------
else:
    st.markdown(f"""
    <div class="hero">
        <h1>🧠 {page}</h1>
        <p>NeuroLens interactive workspace</p>
    </div>
    """, unsafe_allow_html=True)

    if page == "Interactive Lab":
        st.subheader("Cognitive Experiment Setup")
        st.selectbox(
            "Lab guide",
            ["Ayna", "Nova", "Mira", "Ray", "Zara"]
        )
        st.selectbox(
            "Equipment",
            [
                "Neural Scanner",
                "Reaction Console",
                "Memory Chamber",
                "Attention Monitor"
            ]
        )
        st.selectbox(
            "Experiment",
            [
                "Attention & Response",
                "Memory Sequence",
                "Decision & Reward",
                "Stroop Control",
                "Reaction Time"
            ]
        )
        st.button("Prepare experiment")
        st.info("Experiment mechanics will be implemented after UI testing.")

    elif page == "Brain Journey":
        st.selectbox(
            "Learning stage",
            [
                "Brain Regions",
                "Neural Circuits",
                "Neurons",
                "Dendrites, Axons & Myelin",
                "Electrical Signaling",
                "Synapses & Neurotransmitters",
                "Behaviour & Experience"
            ]
        )
        panel(
            "Learning pathway",
            "Brain regions → circuits → neurons → signaling → synapses → cognition.",
            "🧬"
        )

    elif page == "Brain Explorer":
        st.selectbox(
            "Brain region",
            [
                "Prefrontal Cortex",
                "Hippocampus",
                "Striatum",
                "Anterior Cingulate Cortex",
                "Amygdala",
                "Thalamus"
            ]
        )
        panel(
            "Interactive brain viewer",
            "The anatomical image and rotatable 3D brain model will be connected later.",
            "🧠"
        )

    elif page == "Brain Puzzle":
        st.selectbox("Puzzle grid", ["3 × 3", "4 × 4", "5 × 5"])
        panel(
            "Brain assembly puzzle",
            "Puzzle board, movable pieces, snapping and scoring will be added after interface testing.",
            "🧩"
        )
        st.button("Prepare puzzle")

    elif page == "Brain Exercises":
        st.selectbox(
            "Exercise",
            [
                "Attention",
                "Memory",
                "Reaction",
                "Pattern Recognition",
                "Decision-Making"
            ]
        )
        st.button("Open exercise")

    elif page == "Ask Ayna":
        st.text_area("Ask a neuroscience or cognition question")
        st.file_uploader(
            "Optional audio upload",
            type=["wav", "mp3", "m4a", "ogg"]
        )
        st.button("Send to Ayna")
        st.caption("AI and voice responses are not connected in this UI prototype.")

    elif page == "Voice to Emoji":
        st.file_uploader(
            "Upload a voice recording",
            type=["wav", "mp3", "m4a", "ogg"]
        )
        st.button("Analyse voice")
        st.caption(
            "Voice analysis is not active. Any future result must include uncertainty."
        )

    elif page == "Mood & Feelings":
        st.select_slider("Current mood", options=[1, 2, 3, 4, 5])
        st.select_slider("Mental load", options=[1, 2, 3, 4, 5])
        st.select_slider("Attention confidence", options=[1, 2, 3, 4, 5])
        st.text_area("Optional personal note")
        st.button("Save self-report")

    elif page == "Behaviour Decoding":
        st.text_area("Situation")
        st.text_area("Your response")
        st.text_area("Outcome")
        st.button("Explore possible patterns")
        st.caption(
            "Interpretations will be hypotheses, not diagnoses or proof of hidden motives."
        )

    elif page == "Healing & Personal Insight":
        st.tabs([
            "Personal Journal",
            "Life Timeline",
            "Goals & Progress",
            "Memory Map"
        ])
        st.info("This screen is a UI preview. Detailed journal workflows come later.")

    elif page == "Visual Memory Map":
        st.text_input("Map item title")
        st.selectbox(
            "Category",
            [
                "Important experience",
                "Current challenge",
                "Support system",
                "Personal strength",
                "Future hope"
            ]
        )
        st.text_area("Short note")
        st.button("Add map item")

    elif page == "Research Book":
        st.text_input("Search neuroscience literature")
        st.selectbox(
            "Research topic",
            [
                "Consciousness",
                "Learning & Memory",
                "Attention",
                "Decision-Making",
                "Stress & Cognition",
                "CSTC Circuits"
            ]
        )
        st.button("Search papers")
        st.caption("External literature search is not connected yet.")

    elif page == "Private Space":
        st.text_input("Private Space PIN", type="password")
        st.button("Unlock Private Space")
        st.caption("Authentication and encrypted storage are not implemented yet.")

    elif page == "NeuroSocial":
        st.text_input("Username")
        st.text_input("Search for a friend")
        st.button("Find users")
        panel(
            "Community",
            "Profiles, friend requests, chat, streaks and challenges are planned UI sections.",
            "🌐"
        )

    elif page == "Eye Tracking Lab":
        panel(
            "Eye Tracking Workspace",
            "Webcam permissions and gaze estimation are not active in this prototype.",
            "👁️"
        )
        st.button("Prepare calibration")

    elif page == "EEG & Biosignals":
        panel(
            "EEG & Biosignal Workspace",
            "Hardware connection and real signal processing are not active.",
            "📈"
        )
        st.selectbox("Data source", ["Hardware", "Clearly labelled demo data"])

    elif page == "Progress Dashboard":
        a, b, c = st.columns(3)
        a.metric("Experiments", "—")
        b.metric("Completed goals", "—")
        c.metric("Achievements", "—")
        st.info("Progress tracking will be connected after UI testing.")

    elif page == "Settings":
        st.selectbox("Language", ["English", "Roman English"])
        st.selectbox("Appearance", ["Dark", "Light"])
        st.write("Creator: Ayna Jaffri")
        st.caption("Authentication, privacy controls and database settings are not connected.")

    st.divider()
    if st.button("← Back to NeuroWorld", key="back_world"):
        go_to("NeuroWorld")
        st.rerun()

st.markdown("---")
st.markdown(
    '<p class="small-note" style="text-align:center;">'
    'NEUROLENS · Explore cognition, behaviour & the brain · '
    'Ayna Jaffri</p>',
    unsafe_allow_html=True
)
