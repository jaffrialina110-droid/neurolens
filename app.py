import os
import random
import streamlit as st
from PIL import Image
import streamlit.components.v1 as components

# Optional libraries
try:
    from google import genai
except Exception:
    genai = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 48px;
    font-weight: 800;
    margin-bottom: 0;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    opacity: 0.75;
    margin-bottom: 30px;
}

.section-title {
    font-size: 30px;
    font-weight: 750;
    margin-top: 25px;
}

.info-card {
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(120,120,120,0.25);
    margin: 10px 0;
}

.zoom-card {
    padding: 15px;
    border-radius: 20px;
    border: 2px solid rgba(100,100,100,0.20);
    text-align: center;
}

.breadcrumb {
    padding: 12px 18px;
    border-radius: 14px;
    background: rgba(120,120,120,0.10);
    margin-bottom: 20px;
}

.signal-track {
    position: relative;
    height: 90px;
    margin: 25px 0;
    overflow: hidden;
    border-radius: 45px;
    background: rgba(100,100,100,0.10);
}

.signal-line {
    position: absolute;
    top: 43px;
    left: 5%;
    right: 5%;
    height: 5px;
    border-radius: 5px;
    background: currentColor;
}

.signal-dot {
    position: absolute;
    top: 31px;
    left: 5%;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: currentColor;
    animation: moveSignal 2.5s linear infinite;
}

@keyframes moveSignal {
    0% { left: 5%; }
    100% { left: 90%; }
}

.neuron {
    position: relative;
    width: 100%;
    height: 330px;
    margin: auto;
    overflow: hidden;
}

.soma {
    position: absolute;
    width: 110px;
    height: 110px;
    border-radius: 50%;
    left: 43%;
    top: 100px;
    background: rgba(150,150,150,0.35);
    border: 4px solid currentColor;
}

.nucleus {
    position: absolute;
    width: 42px;
    height: 42px;
    border-radius: 50%;
    left: 34px;
    top: 30px;
    background: currentColor;
    opacity: 0.6;
}

.dendrite {
    position: absolute;
    height: 5px;
    background: currentColor;
    transform-origin: left center;
    border-radius: 5px;
}

.d1 { left: 44%; top: 145px; width: 180px; transform: rotate(205deg); }
.d2 { left: 44%; top: 150px; width: 200px; transform: rotate(160deg); }
.d3 { left: 45%; top: 165px; width: 180px; transform: rotate(25deg); }
.d4 { left: 44%; top: 155px; width: 190px; transform: rotate(340deg); }

.axon {
    position: absolute;
    height: 12px;
    width: 400px;
    left: 52%;
    top: 150px;
    background: currentColor;
    border-radius: 10px;
}

.terminal {
    position: absolute;
    right: 2%;
    top: 120px;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 5px solid currentColor;
}

.synapse-box {
    position: relative;
    height: 300px;
    margin: 20px auto;
    overflow: hidden;
}

.pre-neuron {
    position: absolute;
    left: 5%;
    top: 100px;
    width: 40%;
    height: 60px;
    border-radius: 30px;
    background: rgba(120,120,120,0.25);
}

.post-neuron {
    position: absolute;
    right: 5%;
    top: 100px;
    width: 40%;
    height: 60px;
    border-radius: 30px;
    background: rgba(120,120,120,0.25);
}

.synaptic-gap {
    position: absolute;
    left: 46%;
    top: 70px;
    width: 8%;
    height: 120px;
    border-left: 4px dashed currentColor;
    border-right: 4px dashed currentColor;
}

.nt {
    position: absolute;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: currentColor;
    animation: ntMove 2s linear infinite;
}

.nt1 { left: 42%; top: 95px; animation-delay: 0s; }
.nt2 { left: 42%; top: 125px; animation-delay: .5s; }
.nt3 { left: 42%; top: 155px; animation-delay: 1s; }

@keyframes ntMove {
    0% { left: 42%; opacity: 0; }
    20% { opacity: 1; }
    100% { left: 58%; opacity: 1; }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🧠 NEUROLENS</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Explore cognition, behavior & the brain</div>',
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "explorer_level" not in st.session_state:
    st.session_state.explorer_level = "brain"

if "explorer_region" not in st.session_state:
    st.session_state.explorer_region = None

if "explorer_explanation" not in st.session_state:
    st.session_state.explorer_explanation = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# =========================================================
# BRAIN DATA
# =========================================================

BRAIN_PARTS = {
    "Prefrontal Cortex": {
        "emoji": "🎯",
        "function": "Planning, decision-making, cognitive control and goal-directed behavior.",
        "behavior": "Helps you control impulses, plan ahead and evaluate choices.",
        "circuit": "Prefrontal–striatal circuits are important for cognitive control and decision-making."
    },

    "Hippocampus": {
        "emoji": "🧩",
        "function": "Memory formation, spatial navigation and contextual learning.",
        "behavior": "Helps connect experiences with places, events and contexts.",
        "circuit": "Hippocampal networks interact with cortical and limbic systems during memory."
    },

    "Amygdala": {
        "emoji": "⚡",
        "function": "Processes emotionally significant information, especially threat and salience.",
        "behavior": "Can influence fear, emotional learning and rapid responses to important stimuli.",
        "circuit": "Amygdala communicates with prefrontal and hippocampal networks."
    },

    "Striatum": {
        "emoji": "🎁",
        "function": "Important for action selection, reward learning and habit-related processes.",
        "behavior": "Helps connect actions with outcomes and supports learned behaviors.",
        "circuit": "Part of cortico-striatal circuits involved in action and cognitive control."
    },

    "Anterior Cingulate Cortex": {
        "emoji": "🔎",
        "function": "Involved in monitoring conflict, errors, effort and motivational signals.",
        "behavior": "Helps detect when behavior needs adjustment.",
        "circuit": "Interacts with prefrontal, striatal and limbic systems."
    },

    "Cerebellum": {
        "emoji": "⚙️",
        "function": "Coordinates movement and also contributes to timing, learning and some cognitive processes.",
        "behavior": "Helps refine actions and predict the timing of movements.",
        "circuit": "Cerebellar circuits communicate with motor and association areas."
    }
}


# =========================================================
# NEUROTRANSMITTER DATA
# =========================================================

NEUROTRANSMITTERS = {
    "Dopamine": {
        "emoji": "🎯",
        "role": "Reward learning, motivation, movement and salience.",
        "simple": "Dopamine helps the brain learn which actions or events are important.",
    },

    "Serotonin": {
        "emoji": "🌿",
        "role": "Modulates mood, sleep, appetite and many other brain functions.",
        "simple": "Serotonin acts as a broad regulatory signal across many brain systems.",
    },

    "GABA": {
        "emoji": "🛑",
        "role": "Major inhibitory neurotransmitter in the brain.",
        "simple": "GABA generally reduces neuronal excitability and helps regulate network activity.",
    },

    "Glutamate": {
        "emoji": "⚡",
        "role": "Major excitatory neurotransmitter involved in learning and plasticity.",
        "simple": "Glutamate is central to communication and many forms of synaptic plasticity.",
    },

    "Acetylcholine": {
        "emoji": "🧠",
        "role": "Involved in attention, learning, memory and autonomic functions.",
        "simple": "Acetylcholine helps modulate attention and several learning-related processes.",
    }
}


# =========================================================
# GEMINI / ASK AYNA
# =========================================================

MODEL_NAME = "gemini-3.6-flash"


def get_gemini_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]

        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def ask_ayna(prompt):
    api_key = get_gemini_api_key()

    if not api_key:
        return (
            "Ask Ayna abhi connected nahi hai. "
            "Streamlit Secrets mein GEMINI_API_KEY add karein."
        )

    if genai is None:
        return "Google Gemini library available nahi hai."

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if response and response.text:
            return response.text

        return "Ayna ko is waqt response nahi mila."

    except Exception as e:
        return f"Ask Ayna temporary unavailable hai: {str(e)}"


def ask_ayna_structure(level, name, details):
    prompt = f"""
You are Ask Ayna inside NEUROLENS, an educational cognitive neuroscience platform.

Current level:
{level}

Current structure:
{name}

Scientific context:
{details}

Explain this to a curious learner in simple Roman Urdu mixed with English.

Structure your answer as:
1. What is it?
2. What does it do?
3. How does it relate to behavior/cognition?
4. What happens at the neuron/circuit level?
5. One interesting fact.

Be scientifically careful.
Do not diagnose the user.
Do not claim that a simple game can measure brain activity.
Keep it understandable but scientifically responsible.
"""

    return ask_ayna(prompt)


# =========================================================
# IMAGE
# =========================================================

brain_image = None

if os.path.exists("brain.png"):
    try:
        brain_image = Image.open("brain.png")
    except Exception:
        brain_image = None


# =========================================================
# BRAIN CROP
# =========================================================

CROP_BOXES = {
    "Prefrontal Cortex": (0.00, 0.05, 0.48, 0.62),
    "Anterior Cingulate Cortex": (0.18, 0.05, 0.65, 0.65),
    "Hippocampus": (0.30, 0.30, 0.78, 0.85),
    "Amygdala": (0.38, 0.32, 0.76, 0.72),
    "Striatum": (0.25, 0.20, 0.68, 0.68),
    "Cerebellum": (0.55, 0.42, 1.00, 1.00)
}


def crop_brain(region):

    if brain_image is None:
        return None

    if region not in CROP_BOXES:
        return brain_image

    w, h = brain_image.size

    x1, y1, x2, y2 = CROP_BOXES[region]

    box = (
        int(w * x1),
        int(h * y1),
        int(w * x2),
        int(h * y2)
    )

    return brain_image.crop(box)


# =========================================================
# NAVIGATION HELPERS
# =========================================================

def go_to(level):
    st.session_state.explorer_level = level
    st.rerun()


def back_to_brain():
    st.session_state.explorer_level = "brain"
    st.session_state.explorer_region = None
    st.session_state.explorer_explanation = ""
    st.rerun()


def show_breadcrumb():

    level = st.session_state.explorer_level
    region = st.session_state.explorer_region

    if level == "brain":
        text = "🧠 Whole Brain"

    elif level == "region":
        text = f"🧠 Whole Brain → {region}"

    elif level == "neuron":
        text = f"🧠 Whole Brain → {region} → 🧬 Neuron"

    elif level == "axon":
        text = f"🧠 Whole Brain → {region} → 🧬 Neuron → ⚡ Axon/Myelin"

    elif level == "synapse":
        text = f"🧠 Whole Brain → {region} → 🧬 Neuron → ⚡ Axon → 🔬 Synapse"

    elif level == "neurotransmitter":
        text = (
            f"🧠 Whole Brain → {region} → 🧬 Neuron → "
            f"⚡ Axon → 🔬 Synapse → 🧪 Neurotransmitter"
        )

    else:
        text = "🧠 NEUROLENS"

    st.markdown(
        f'<div class="breadcrumb">{text}</div>',
        unsafe_allow_html=True
    )


def ask_current_structure():

    level = st.session_state.explorer_level
    region = st.session_state.explorer_region

    if level == "region":

        data = BRAIN_PARTS[region]

        explanation = ask_ayna_structure(
            "Brain Region",
            region,
            f"""
Function: {data['function']}
Behavior: {data['behavior']}
Circuit: {data['circuit']}
"""
        )

    elif level == "neuron":

        explanation = ask_ayna_structure(
            "Neuron",
            f"Neuron connected to {region}",
            """
A neuron is an electrically excitable cell.
It receives information through dendrites,
integrates signals in the cell body,
and sends information through the axon.
"""
        )

    elif level == "axon":

        explanation = ask_ayna_structure(
            "Axon / Myelin",
            f"Axon carrying signals from {region}",
            """
The axon carries electrical signals away from the neuronal cell body.
Myelin can increase the efficiency and speed of signal propagation.
"""
        )

    elif level == "synapse":

        explanation = ask_ayna_structure(
            "Synapse",
            f"Synapse associated with {region}",
            """
A synapse is a communication junction between neurons.
Chemical synapses can use neurotransmitters to transmit signals
across a small synaptic cleft.
"""
        )

    else:

        explanation = ask_ayna_structure(
            "Neurotransmitter",
            f"Neurotransmitters related to {region}",
            """
Neurotransmitters are chemical messengers released by neurons
that can influence activity in other neurons or target cells.
Examples include dopamine, serotonin, GABA, glutamate and acetylcholine.
"""
        )

    st.session_state.explorer_explanation = explanation


# =========================================================
# EXPLORER — WHOLE BRAIN
# =========================================================

def brain_explorer():

    st.markdown(
        '<div class="section-title">🔬 Interactive Brain Explorer</div>',
        unsafe_allow_html=True
    )

    show_breadcrumb()

    if brain_image is not None:
        st.image(
            brain_image,
            caption="Select a brain region to zoom in",
            use_container_width=True
        )
    else:
        st.warning(
            "brain.png nahi mila. GitHub repo mein app.py ke saath brain.png upload karein."
        )

    st.markdown("### 🧠 Select a region")

    names = list(BRAIN_PARTS.keys())

    for i in range(0, len(names), 3):

        cols = st.columns(3)

        for j, col in enumerate(cols):

            index = i + j

            if index >= len(names):
                continue

            name = names[index]
            data = BRAIN_PARTS[name]

            with col:

                if st.button(
                    f"{data['emoji']} {name}",
                    use_container_width=True,
                    key=f"region_{name}"
                ):

                    st.session_state.explorer_region = name
                    st.session_state.explorer_level = "region"
                    st.session_state.explorer_explanation = ""

                    st.rerun()


# =========================================================
# REGION LEVEL
# =========================================================

def region_view():

    region = st.session_state.explorer_region
    data = BRAIN_PARTS[region]

    show_breadcrumb()

    st.markdown(
        f'<div class="section-title">{data["emoji"]} {region}</div>',
        unsafe_allow_html=True
    )

    crop = crop_brain(region)

    col1, col2 = st.columns([1.2, 1])

    with col1:

        st.markdown(
            '<div class="zoom-card">',
            unsafe_allow_html=True
        )

        if crop is not None:
            st.image(
                crop,
                caption=f"🔍 Zoomed view — {region}",
                use_container_width=True
            )
        else:
            st.info("Brain image unavailable.")

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with col2:

        st.markdown("### 🧠 What does it do?")
        st.write(data["function"])

        st.markdown("### 🧍 Behavior & cognition")
        st.write(data["behavior"])

        st.markdown("### 🔗 Circuit")
        st.write(data["circuit"])

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "🧬 Zoom into Neuron",
            use_container_width=True
        ):
            go_to("neuron")

    with c2:
        if st.button(
            "🗣️ Ask Ayna — Explain This",
            use_container_width=True
        ):
            ask_current_structure()

    with c3:
        if st.button(
            "🔊 Voice Explanation",
            use_container_width=True
        ):

            text = (
                f"{region}. "
                f"{data['function']} "
                f"{data['behavior']}"
            )

            components.html(
                f"""
                <script>
                const text = {text!r};
                const speech = new SpeechSynthesisUtterance(text);
                speech.rate = 0.9;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(speech);
                </script>
                """,
                height=20
            )

    if st.session_state.explorer_explanation:

        st.markdown("### 🗣️ Ask Ayna")

        st.info(
            st.session_state.explorer_explanation
        )

    if st.button("⬅️ Back to Whole Brain"):
        back_to_brain()


# =========================================================
# NEURON LEVEL
# =========================================================

def neuron_view():

    region = st.session_state.explorer_region

    show_breadcrumb()

    st.markdown(
        "## 🧬 Zoom Level 2 — Neuron"
    )

    st.write(
        f"Ab hum **{region}** se associated neuronal level ko explore kar rahe hain."
    )

    st.markdown(
        """
        <div class="neuron">
            <div class="dendrite d1"></div>
            <div class="dendrite d2"></div>
            <div class="dendrite d3"></div>
            <div class="dendrite d4"></div>

            <div class="soma">
                <div class="nucleus"></div>
            </div>

            <div class="axon"></div>
            <div class="terminal"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        **Dendrites** → receive signals  
        **Soma** → integrates information  
        **Nucleus** → contains genetic material  
        **Axon** → carries electrical signals  
        **Terminal** → communicates with the next cell
        """
    )

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "⚡ Zoom into Axon / Myelin",
            use_container_width=True
        ):
            go_to("axon")

    with c2:
        if st.button(
            "🗣️ Ask Ayna — Explain Neuron",
            use_container_width=True
        ):
            ask_current_structure()

    with c3:
        if st.button(
            "⬅️ Back to Region",
            use_container_width=True
        ):
            go_to("region")

    if st.session_state.explorer_explanation:
        st.markdown("### 🗣️ Ayna explains")
        st.info(st.session_state.explorer_explanation)


# =========================================================
# AXON LEVEL
# =========================================================

def axon_view():

    region = st.session_state.explorer_region

    show_breadcrumb()

    st.markdown(
        "## ⚡ Zoom Level 3 — Axon & Myelin"
    )

    st.write(
        "Yahan hum dekhte hain ke neuronal signal axon ke through kaise travel karta hai."
    )

    st.markdown(
        """
        <div class="signal-track">
            <div class="signal-line"></div>
            <div class="signal-dot"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        ### ⚡ Signal pathway

        **Cell body → Axon → Axon terminal → Synapse**

        Myelin axon ko electrically insulate karta hai aur many neurons mein
        signal propagation ko more efficient banata hai.
        """
    )

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "🔬 Zoom into Synapse",
            use_container_width=True
        ):
            go_to("synapse")

    with c2:
        if st.button(
            "🗣️ Ask Ayna — Explain Axon",
            use_container_width=True
        ):
            ask_current_structure()

    with c3:
        if st.button(
            "⬅️ Back to Neuron",
            use_container_width=True
        ):
            go_to("neuron")

    if st.session_state.explorer_explanation:
        st.markdown("### 🗣️ Ayna explains")
        st.info(st.session_state.explorer_explanation)


# =========================================================
# SYNAPSE LEVEL
# =========================================================

def synapse_view():

    region = st.session_state.explorer_region

    show_breadcrumb()

    st.markdown(
        "## 🔬 Zoom Level 4 — Synapse"
    )

    st.write(
        "Synapse woh communication point hai jahan ek neuron doosre cell ko signal de sakta hai."
    )

    st.markdown(
        """
        <div class="synapse-box">

            <div class="pre-neuron"></div>

            <div class="synaptic-gap"></div>

            <div class="post-neuron"></div>

            <div class="nt nt1"></div>
            <div class="nt nt2"></div>
            <div class="nt nt3"></div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        ### 🔬 Synaptic sequence

        **Electrical signal arrives → neurotransmitter release → 
        synaptic cleft → receptors → response in target cell**
        """
    )

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "🧪 Explore Neurotransmitters",
            use_container_width=True
        ):
            go_to("neurotransmitter")

    with c2:
        if st.button(
            "🗣️ Ask Ayna — Explain Synapse",
            use_container_width=True
        ):
            ask_current_structure()

    with c3:
        if st.button(
            "⬅️ Back to Axon",
            use_container_width=True
        ):
            go_to("axon")

    if st.session_state.explorer_explanation:
        st.markdown("### 🗣️ Ayna explains")
        st.info(st.session_state.explorer_explanation)


# =========================================================
# NEUROTRANSMITTER LEVEL
# =========================================================

def neurotransmitter_view():

    region = st.session_state.explorer_region

    show_breadcrumb()

    st.markdown(
        "## 🧪 Zoom Level 5 — Neurotransmitter Explorer"
    )

    st.write(
        "Ab hum chemical signaling level par hain."
    )

    selected = st.selectbox(
        "Choose a neurotransmitter",
        list(NEUROTRANSMITTERS.keys())
    )

    data = NEUROTRANSMITTERS[selected]

    st.markdown(
        f"""
        <div class="info-card">

        <h2>{data["emoji"]} {selected}</h2>

        <h4>Role</h4>
        <p>{data["role"]}</p>

        <h4>Simple explanation</h4>
        <p>{data["simple"]}</p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="signal-track">
            <div class="signal-line"></div>
            <div class="signal-dot"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "🗣️ Ask Ayna — Explain Neurotransmitter",
            use_container_width=True
        ):

            explanation = ask_ayna_structure(
                "Neurotransmitter",
                selected,
                f"""
Role: {data['role']}
Simple explanation: {data['simple']}
Brain region currently selected: {region}
"""
            )

            st.session_state.explorer_explanation = explanation

    with c2:

        if st.button(
            "🔊 Voice",
            use_container_width=True
        ):

            voice_text = (
                f"{selected}. "
                f"{data['simple']}"
            )

            components.html(
                f"""
                <script>
                const speech = new SpeechSynthesisUtterance({voice_text!r});
                speech.rate = 0.9;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(speech);
                </script>
                """,
                height=20
            )

    with c3:

        if st.button(
            "⬅️ Back to Synapse",
            use_container_width=True
        ):
            go_to("synapse")

    if st.session_state.explorer_explanation:
        st.markdown("### 🗣️ Ayna explains")
        st.info(st.session_state.explorer_explanation)


# =========================================================
# NEURAL VISUALIZATION
# =========================================================

def neural_visualization():

    st.markdown(
        '<div class="section-title">🌐 3D Neural Visualization</div>',
        unsafe_allow_html=True
    )

    if go is None:

        st.warning(
            "Plotly available nahi hai. requirements.txt mein plotly add karein."
        )

        return

    random.seed(7)

    nodes = []

    for _ in range(30):

        nodes.append(
            (
                random.uniform(-5, 5),
                random.uniform(-5, 5),
                random.uniform(-5, 5)
            )
        )

    edge_x = []
    edge_y = []
    edge_z = []

    for i in range(len(nodes) - 1):

        x1, y1, z1 = nodes[i]
        x2, y2, z2 = nodes[i + 1]

        edge_x += [x1, x2, None]
        edge_y += [y1, y2, None]
        edge_z += [z1, z2, None]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line=dict(width=2),
            hoverinfo="none"
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[n[0] for n in nodes],
            y=[n[1] for n in nodes],
            z=[n[2] for n in nodes],
            mode="markers",
            marker=dict(
                size=6
            ),
            text=[f"Neuron {i+1}" for i in range(len(nodes))],
            hoverinfo="text"
        )
    )

    fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            zaxis=dict(showgrid=False)
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Educational neural-network visualization — not an anatomical brain reconstruction."
    )


# =========================================================
# COGNITIVE GAMES
# =========================================================

def cognitive_games():

    st.markdown(
        '<div class="section-title">🎮 Cognitive Games</div>',
        unsafe_allow_html=True
    )

    game = st.selectbox(
        "Choose a game",
        [
            "Decision",
            "Memory",
            "Attention",
            "Stroop",
            "Pattern"
        ]
    )

    if game == "Decision":

        st.write(
            "Imagine you receive a reward now or a larger reward later."
        )

        choice = st.radio(
            "What would you choose?",
            [
                "Small reward now",
                "Larger reward later"
            ]
        )

        if st.button("Submit Decision"):

            st.success(
                f"You selected: {choice}"
            )

    elif game == "Memory":

        sequence = ["🧠", "⚡", "🔬", "🎯", "🧩"]

        st.write(
            "Remember this sequence:"
        )

        st.markdown(
            " ".join(sequence)
        )

        answer = st.text_input(
            "Enter the sequence without spaces"
        )

        if st.button("Check Memory"):

            if answer.replace(" ", "") == "".join(sequence):
                st.success("Correct!")
            else:
                st.error("Try again.")

    elif game == "Attention":

        target = random.choice(
            ["RED", "BLUE", "GREEN"]
        )

        st.write(
            f"Target: **{target}**"
        )

        answer = st.text_input(
            "Type the target"
        )

        if st.button("Check Attention"):

            if answer.upper() == target:
                st.success("Correct!")
            else:
                st.error("Incorrect.")

    elif game == "Stroop":

        words = [
            "RED",
            "BLUE",
            "GREEN",
            "YELLOW"
        ]

        word = random.choice(words)

        st.markdown(
            f"### {word}"
        )

        answer = st.text_input(
            "Type the word you see"
        )

        if st.button("Check Stroop"):

            if answer.upper() == word:
                st.success("Correct!")
            else:
                st.error("Incorrect.")

    else:

        pattern = ["🔵", "🔴", "🔵", "🔴", "❓"]

        st.markdown(
            " ".join(pattern)
        )

        answer = st.selectbox(
            "What comes next?",
            ["🔵", "🔴", "🟢"]
        )

        if st.button("Check Pattern"):

            if answer == "🔵":
                st.success("Correct!")
            else:
                st.error("Try again.")


# =========================================================
# COGNITIVE SELF REPORT
# =========================================================

def self_report():

    st.markdown(
        '<div class="section-title">🧠 Cognitive Self-Report</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "This is an educational self-report, not a clinical assessment."
    )

    focus = st.slider(
        "Current focus",
        1,
        10,
        5
    )

    stress = st.slider(
        "Current stress",
        1,
        10,
        5
    )

    motivation = st.slider(
        "Current motivation",
        1,
        10,
        5
    )

    if st.button("Explore My Pattern"):

        st.info(
            f"""
            Focus: {focus}/10  
            Stress: {stress}/10  
            Motivation: {motivation}/10
            """
        )


# =========================================================
# ASK AYNA CHAT
# =========================================================

def ask_ayna_chat():

    st.markdown(
        '<div class="section-title">💬 Ask Ayna</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Ask neuroscience, cognition, behavior or brain-related questions."
    )

    for message in st.session_state.chat_history:

        if message["role"] == "user":
            st.markdown(
                f"**You:** {message['content']}"
            )

        else:
            st.markdown(
                f"**🧠 Ayna:** {message['content']}"
            )

    question = st.text_area(
        "Your question",
        placeholder="Example: Why does stress affect attention?"
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "Send to Ayna",
            use_container_width=True
        ):

            if question.strip():

                prompt = f"""
You are Ayna, an educational cognitive neuroscience assistant.

Answer the user's question clearly and scientifically.

User question:
{question}

Use simple language.
You may use Roman Urdu + English when useful.
Do not diagnose.
Do not overstate neuroscience findings.
"""

                answer = ask_ayna(prompt)

                st.session_state.chat_history.append(
                    {
                        "role": "user",
                        "content": question
                    }
                )

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

                st.rerun()

    with c2:

        if st.button(
            "Clear Chat",
            use_container_width=True
        ):

            st.session_state.chat_history = []
            st.rerun()


# =========================================================
# MAIN TABS
# =========================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🔬 Brain Explorer",
        "🎮 Cognitive Games",
        "🌐 Neural Visualization",
        "🧠 Self-Report",
        "💬 Ask Ayna"
    ]
)


# =========================================================
# TAB 1
# =========================================================

with tab1:

    level = st.session_state.explorer_level

    if level == "brain":
        brain_explorer()

    elif level == "region":
        region_view()

    elif level == "neuron":
        neuron_view()

    elif level == "axon":
        axon_view()

    elif level == "synapse":
        synapse_view()

    elif level == "neurotransmitter":
        neurotransmitter_view()


# =========================================================
# TAB 2
# =========================================================

with tab2:
    cognitive_games()


# =========================================================
# TAB 3
# =========================================================

with tab3:
    neural_visualization()


# =========================================================
# TAB 4
# =========================================================

with tab4:
    self_report()


# =========================================================
# TAB 5
# =========================================================

with tab5:
    ask_ayna_chat()


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "NEUROLENS — Explore cognition, behavior & the brain | "
    "Created by Ayna Jaffri"
)
