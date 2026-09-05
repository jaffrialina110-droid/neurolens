import os
import random
import streamlit as st
from PIL import Image
import streamlit.components.v1 as components

try:
    from google import genai
except ImportError:
    genai = None

try:
    import plotly.graph_objects as go
except ImportError:
    go = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🧠 NEUROLENS")
st.caption("Explore cognition, behavior & the brain")

st.divider()


# ============================================================
# BRAIN IMAGE
# ============================================================

BRAIN_IMAGE = "brain.png"

brain_image = None

if os.path.exists(BRAIN_IMAGE):
    try:
        brain_image = Image.open(BRAIN_IMAGE).convert("RGB")
    except Exception:
        brain_image = None


# ============================================================
# BRAIN REGIONS
# ============================================================

brain_parts = {

    "Prefrontal Cortex": {
        "description": (
            "The prefrontal cortex contributes to planning, "
            "working memory, cognitive control and goal-directed behavior."
        ),
        "behavior": (
            "Planning, decision-making, inhibition and cognitive control."
        ),
        "circuit": (
            "Prefrontal Cortex → Striatum → Thalamus → Cortex"
        ),
    },

    "Hippocampus": {
        "description": (
            "The hippocampus is important for memory formation, "
            "memory organization and spatial representation."
        ),
        "behavior": (
            "Learning, memory and spatial navigation."
        ),
        "circuit": (
            "Hippocampus ↔ Cortex"
        ),
    },

    "Amygdala": {
        "description": (
            "The amygdala processes emotionally significant "
            "information and contributes to emotional learning."
        ),
        "behavior": (
            "Emotion, threat processing and emotional learning."
        ),
        "circuit": (
            "Amygdala → Hypothalamus → Brainstem"
        ),
    },

    "Striatum": {
        "description": (
            "The striatum participates in action selection, "
            "reward-related learning and habit-related processes."
        ),
        "behavior": (
            "Reward learning, action selection and habits."
        ),
        "circuit": (
            "Cortex → Striatum → Globus Pallidus → Thalamus → Cortex"
        ),
    },

    "Anterior Cingulate Cortex": {
        "description": (
            "The anterior cingulate cortex contributes to "
            "performance monitoring, conflict processing "
            "and cognitive control."
        ),
        "behavior": (
            "Conflict monitoring, error processing and cognitive control."
        ),
        "circuit": (
            "ACC → Prefrontal Cortex → Striatum"
        ),
    },

    "Cerebellum": {
        "description": (
            "The cerebellum contributes to coordination, "
            "timing, balance and motor learning."
        ),
        "behavior": (
            "Coordination, timing, balance and motor learning."
        ),
        "circuit": (
            "Cerebellum → Thalamus → Motor Cortex"
        ),
    },
}


# ============================================================
# NAVIGATION
# ============================================================

def navigate(level, region):

    st.query_params["level"] = level
    st.query_params["region"] = region

    st.rerun()


level = st.query_params.get(
    "level",
    "brain"
)

region = st.query_params.get(
    "region",
    "Prefrontal Cortex"
)

if region not in brain_parts:
    region = "Prefrontal Cortex"


# ============================================================
# INTERACTIVE BRAIN EXPLORER
# ============================================================

st.header("🧠 Interactive Brain Explorer")

if brain_image is not None:

    st.image(
        brain_image,
        caption="NEUROLENS Brain",
        use_container_width=True
    )

else:

    st.warning(
        "⚠️ brain.png not found. "
        "Make sure brain.png is in the same folder as app.py."
    )


selected_part = st.selectbox(
    "🔍 Choose a brain region",
    list(brain_parts.keys()),
    index=list(brain_parts.keys()).index(region),
    key="brain_region"
)

selected_info = brain_parts[selected_part]


col1, col2 = st.columns(2)


with col1:

    st.subheader(
        f"🔬 {selected_part}"
    )

    st.info(
        selected_info["description"]
    )

    st.markdown(
        "**Behavioral Role**"
    )

    st.write(
        selected_info["behavior"]
    )


with col2:

    st.subheader(
        "🔗 Neural Circuit"
    )

    st.code(
        selected_info["circuit"]
    )


if st.button(
    "🔎 Explore This Region",
    use_container_width=True,
    key="explore_selected_region"
):

    navigate(
        "region",
        selected_part
    )


# ============================================================
# NERVE EXPLORER
# ============================================================

st.divider()

st.header("🧬 Nerve Explorer")

st.write(
    "Explore the nervous system progressively — "
    "from the whole brain to regions, neurons, axons, "
    "synapses and neurotransmitters."
)


st.markdown(
    """
### 🔎 Exploration Path

**🧠 Whole Brain**

↓

**🔬 Brain Region**

↓

**🧬 Neuron**

↓

**⚡ Axon & Myelin**

↓

**🔗 Synapse**

↓

**🧪 Neurotransmitter**
"""
)


st.caption(
    f"Current level: **{level.title()}**"
)


# ============================================================
# WHOLE BRAIN
# ============================================================

if level == "brain":

    st.subheader(
        "🧠 Whole Brain"
    )

    if brain_image is not None:

        st.image(
            brain_image,
            use_container_width=True
        )

    st.markdown(
        "### 🔍 Select a region to zoom in"
    )

    st.caption(
        "Choose a brain region below. The explorer will move to the next level."
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        if st.button(
            "🧠 Prefrontal Cortex",
            use_container_width=True,
            key="pfc_button"
        ):

            navigate(
                "region",
                "Prefrontal Cortex"
            )


        if st.button(
            "🧠 Hippocampus",
            use_container_width=True,
            key="hippocampus_button"
        ):

            navigate(
                "region",
                "Hippocampus"
            )


    with col2:

        if st.button(
            "🧠 Amygdala",
            use_container_width=True,
            key="amygdala_button"
        ):

            navigate(
                "region",
                "Amygdala"
            )


        if st.button(
            "🧠 Striatum",
            use_container_width=True,
            key="striatum_button"
        ):

            navigate(
                "region",
                "Striatum"
            )


    with col3:

        if st.button(
            "🧠 Anterior Cingulate Cortex",
            use_container_width=True,
            key="acc_button"
        ):

            navigate(
                "region",
                "Anterior Cingulate Cortex"
            )


        if st.button(
            "🧠 Cerebellum",
            use_container_width=True,
            key="cerebellum_button"
        ):

            navigate(
                "region",
                "Cerebellum"
            )


# ============================================================
# REGION
# ============================================================

elif level == "region":

    data = brain_parts[region]


    st.subheader(
        f"🔬 {region}"
    )


    st.success(
        "Zoomed into brain region"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.markdown(
            "### 🧠 Function"
        )

        st.write(
            data["description"]
        )

        st.markdown(
            "### 🧠 Behavior"
        )

        st.write(
            data["behavior"]
        )


    with col2:

        st.markdown(
            "### 🔗 Connected Circuit"
        )

        st.code(
            data["circuit"]
        )


    st.divider()

    st.subheader(
        "🔬 Go deeper"
    )


    if st.button(
        "🧬 Zoom into Neuron",
        use_container_width=True,
        key="region_to_neuron"
    ):

        navigate(
            "neuron",
            region
        )


    if st.button(
        "🔙 Back to Whole Brain",
        use_container_width=True,
        key="region_back"
    ):

        navigate(
            "brain",
            region
        )


# ============================================================
# NEURON
# ============================================================

elif level == "neuron":

    st.subheader(
        f"🧬 Neuron inside {region}"
    )


    st.success(
        "You are now inside the selected brain region."
    )


    neuron_part = st.selectbox(
        "🔍 Explore neuron component",
        [
            "Dendrites",
            "Cell Body (Soma)",
            "Nucleus",
            "Axon",
            "Axon Terminal"
        ],
        key="neuron_component"
    )


    neuron_info = {

        "Dendrites":
            "Dendrites receive incoming information from other neurons and contribute to signal integration.",

        "Cell Body (Soma)":
            "The soma supports the neuron's metabolic functions and contains the nucleus.",

        "Nucleus":
            "The nucleus contains the neuron's genetic material and regulates cellular activity.",

        "Axon":
            "The axon carries electrical signals away from the cell body toward other targets.",

        "Axon Terminal":
            "The axon terminal is involved in communication with another neuron or target cell."
    }


    st.info(
        neuron_info[neuron_part]
    )


    # --------------------------------------------------------
    # NEURON VISUAL
    # --------------------------------------------------------

    neuron_html = """

    <div class="neuron">

        <div class="dendrite d1"></div>
        <div class="dendrite d2"></div>
        <div class="dendrite d3"></div>
        <div class="dendrite d4"></div>

        <div class="soma">
            ●
        </div>

        <div class="axon"></div>

        <div class="myelin m1"></div>
        <div class="myelin m2"></div>
        <div class="myelin m3"></div>

        <div class="terminal"></div>

    </div>


    <style>

    .neuron {

        position: relative;

        width: 100%;

        max-width: 900px;

        height: 360px;

        margin: auto;

        background:
            linear-gradient(
                135deg,
                #f7f9ff,
                #edf2ff
            );

        border-radius: 25px;

        overflow: hidden;

    }


    .soma {

        position: absolute;

        left: 28%;

        top: 38%;

        width: 100px;

        height: 100px;

        border-radius: 50%;

        background: #e5b0ce;

        border: 5px solid #8b527b;

        display: flex;

        align-items: center;

        justify-content: center;

        font-size: 35px;

    }


    .axon {

        position: absolute;

        left: 38%;

        top: 51%;

        width: 52%;

        height: 15px;

        background: #8a6a50;

        border-radius: 20px;

    }


    .myelin {

        position: absolute;

        top: 47%;

        width: 80px;

        height: 40px;

        border-radius: 25px;

        background: #dce7f4;

        border: 3px solid #8da1ba;

        z-index: 3;

    }


    .m1 {
        left: 48%;
    }

    .m2 {
        left: 62%;
    }

    .m3 {
        left: 76%;
    }


    .dendrite {

        position: absolute;

        left: 8%;

        top: 50%;

        width: 190px;

        height: 9px;

        background: #8a6a50;

        border-radius: 20px;

        transform-origin: right center;

    }


    .d1 {
        transform: rotate(-60deg);
    }

    .d2 {
        transform: rotate(-25deg);
    }

    .d3 {
        transform: rotate(25deg);
    }

    .d4 {
        transform: rotate(60deg);
    }


    .terminal {

        position: absolute;

        right: 3%;

        top: 45%;

        width: 45px;

        height: 45px;

        border-radius: 50%;

        background: #aa7fbc;

        border: 4px solid #70477b;

    }

    </style>
    """


    components.html(
        neuron_html,
        height=390
    )


    st.divider()


    if st.button(
        "⚡ Zoom into Axon & Myelin",
        use_container_width=True,
        key="neuron_to_axon"
    ):

        navigate(
            "axon",
            region
        )


    if st.button(
        "🔙 Back to Brain Region",
        use_container_width=True,
        key="neuron_back"
    ):

        navigate(
            "region",
            region
        )


# ============================================================
# AXON
# ============================================================

elif level == "axon":

    st.subheader(
        f"⚡ Axon & Myelin — {region}"
    )


    st.info(
        "The axon carries electrical signals. "
        "Myelin provides insulation around many axons "
        "and supports rapid signal conduction."
    )


    st.markdown(
        "### ⚡ Neural Signal Traveling"
    )


    axon_html = """

    <div class="axon-track">

        <div class="axon-line"></div>

        <div class="myelin-piece p1"></div>
        <div class="myelin-piece p2"></div>
        <div class="myelin-piece p3"></div>
        <div class="myelin-piece p4"></div>

        <div class="signal"></div>

    </div>


    <style>

    .axon-track {

        position: relative;

        height: 150px;

        width: 100%;

        background: #f4f6fa;

        border-radius: 25px;

        overflow: hidden;

        border: 2px solid #d6dce5;

    }


    .axon-line {

        position: absolute;

        left: 3%;

        right: 3%;

        top: 68px;

        height: 14px;

        background: #8a6a50;

        border-radius: 20px;

    }


    .myelin-piece {

        position: absolute;

        top: 53px;

        width: 105px;

        height: 44px;

        background: #dce7f4;

        border: 3px solid #8da1ba;

        border-radius: 25px;

        z-index: 2;

    }


    .p1 {
        left: 8%;
    }

    .p2 {
        left: 31%;
    }

    .p3 {
        left: 54%;
    }

    .p4 {
        left: 77%;
    }


    .signal {

        position: absolute;

        top: 58px;

        left: 2%;

        width: 32px;

        height: 32px;

        border-radius: 50%;

        background: #6f5cff;

        box-shadow:
            0 0 25px #6f5cff;

        animation:
            signalMove
            2.5s
            linear
            infinite;

        z-index: 5;

    }


    @keyframes signalMove {

        from {
            left: 2%;
        }

        to {
            left: 96%;
        }

    }

    </style>
    """


    components.html(
        axon_html,
        height=180
    )


    st.success(
        "⚡ Signal animation represents an educational model of neural signaling."
    )


    if st.button(
        "🔗 Zoom into Synapse",
        use_container_width=True,
        key="axon_to_synapse"
    ):

        navigate(
            "synapse",
            region
        )


    if st.button(
        "🔙 Back to Neuron",
        use_container_width=True,
        key="axon_back"
    ):

        navigate(
            "neuron",
            region
        )


# ============================================================
# SYNAPSE
# ============================================================

elif level == "synapse":

    st.subheader(
        f"🔗 Synapse — {region}"
    )


    st.write(
        "A synapse is a specialized communication point "
        "between a neuron and another cell."
    )


    synapse_part = st.selectbox(
        "🔍 Explore synapse component",
        [
            "Presynaptic Terminal",
            "Synaptic Vesicles",
            "Synaptic Cleft",
            "Postsynaptic Membrane",
            "Receptors"
        ],
        key="synapse_component"
    )


    synapse_info = {

        "Presynaptic Terminal":
            "The presynaptic terminal is the sending side of a chemical synapse.",

        "Synaptic Vesicles":
            "Synaptic vesicles can store neurotransmitters before release.",

        "Synaptic Cleft":
            "The synaptic cleft is the small space between communicating cells.",

        "Postsynaptic Membrane":
            "The postsynaptic membrane receives incoming chemical signals.",

        "Receptors":
            "Receptors detect specific signaling molecules and can alter cellular responses."
    }


    st.info(
        synapse_info[synapse_part]
    )


    synapse_html = """

    <div class="synapse">

        <div class="pre"></div>

        <div class="cleft"></div>

        <div class="post"></div>

        <div class="ves v1"></div>
        <div class="ves v2"></div>
        <div class="ves v3"></div>

        <div class="chemical c1"></div>
        <div class="chemical c2"></div>
        <div class="chemical c3"></div>

        <div class="receptor r1"></div>
        <div class="receptor r2"></div>
        <div class="receptor r3"></div>

    </div>


    <style>

    .synapse {

        position: relative;

        width: 100%;

        max-width: 900px;

        height: 300px;

        margin: auto;

        background: #f8fafc;

        border-radius: 25px;

        overflow: hidden;

        border: 2px solid #d8dee8;

    }


    .pre,
    .post {

        position: absolute;

        top: 38%;

        height: 100px;

        width: 34%;

        border-radius: 35px;

    }


    .pre {

        left: 5%;

        background: #d9a9c9;

    }


    .post {

        right: 5%;

        background: #a7c7df;

    }


    .cleft {

        position: absolute;

        left: 44%;

        top: 15%;

        width: 12%;

        height: 70%;

        background: white;

        border-left: 3px dashed #aeb8c5;

        border-right: 3px dashed #aeb8c5;

    }


    .ves,
    .chemical {

        position: absolute;

        border-radius: 50%;

    }


    .ves {

        width: 18px;

        height: 18px;

        background: #9c6db0;

    }


    .v1 {
        left: 31%;
        top: 39%;
    }

    .v2 {
        left: 35%;
        top: 52%;
    }

    .v3 {
        left: 39%;
        top: 43%;
    }


    .chemical {

        width: 14px;

        height: 14px;

        background: #6e61ff;

        box-shadow:
            0 0 15px #6e61ff;

        animation:
            chemicalMove
            2s
            linear
            infinite;

    }


    .c1 {
        left: 44%;
        top: 42%;
    }

    .c2 {
        left: 47%;
        top: 52%;
    }

    .c3 {
        left: 51%;
        top: 46%;
    }


    .receptor {

        position: absolute;

        right: 28%;

        width: 14px;

        height: 35px;

        background: #557fa5;

        border-radius: 8px;

    }


    .r1 {
        top: 38%;
    }

    .r2 {
        top: 49%;
    }

    .r3 {
        top: 60%;
    }


    @keyframes chemicalMove {

        from {
            transform: translateX(0);
        }

        to {
            transform: translateX(55px);
        }

    }

    </style>
    """


    components.html(
        synapse_html,
        height=330
    )


    st.divider()


    if st.button(
        "🧪 Explore Neurotransmitters",
        use_container_width=True,
        key="synapse_to_nt"
    ):

        navigate(
            "nt",
            region
        )


    if st.button(
        "🔙 Back to Axon",
        use_container_width=True,
        key="synapse_back"
    ):

        navigate(
            "axon",
            region
        )


# ============================================================
# NEUROTRANSMITTER
# ============================================================

elif level == "nt":

    st.subheader(
        f"🧪 Neurotransmitter Explorer — {region}"
    )


    neurotransmitters = {

        "Dopamine":
            "Participates in reward learning, motivation, movement and several cognitive processes.",

        "Serotonin":
            "Participates in mood regulation, sleep, appetite and many physiological processes.",

        "GABA":
            "A major inhibitory neurotransmitter in the central nervous system.",

        "Glutamate":
            "A major excitatory neurotransmitter and an important contributor to learning and synaptic plasticity.",

        "Acetylcholine":
            "Contributes to attention, learning, memory and neuromuscular communication."
    }


    selected_nt = st.selectbox(
        "🧪 Select neurotransmitter",
        list(neurotransmitters.keys()),
        key="neurotransmitter"
    )


    st.markdown(
        f"## 🧪 {selected_nt}"
    )


    st.info(
        neurotransmitters[selected_nt]
    )


    st.markdown(
        "### ⚡ Signal Animation"
    )


    nt_html = """

    <div class="nt-track">

        <div class="nt-dot d1"></div>
        <div class="nt-dot d2"></div>
        <div class="nt-dot d3"></div>
        <div class="nt-dot d4"></div>
        <div class="nt-dot d5"></div>

    </div>


    <style>

    .nt-track {

        position: relative;

        width: 100%;

        height: 150px;

        background:
            linear-gradient(
                90deg,
                #f3eaff,
                #edf8ff
            );

        border-radius: 25px;

        overflow: hidden;

    }


    .nt-dot {

        position: absolute;

        width: 24px;

        height: 24px;

        border-radius: 50%;

        background: #705cff;

        box-shadow:
            0 0 20px #705cff;

        animation:
            fly
            2.5s
            linear
            infinite;

    }


    .d1 {
        top: 25%;
        animation-delay: 0s;
    }

    .d2 {
        top: 50%;
        animation-delay: .3s;
    }

    .d3 {
        top: 35%;
        animation-delay: .6s;
    }

    .d4 {
        top: 65%;
        animation-delay: .9s;
    }

    .d5 {
        top: 20%;
        animation-delay: 1.2s;
    }


    @keyframes fly {

        from {
            left: -5%;
        }

        to {
            left: 105%;
        }

    }

    </style>
    """


    components.html(
        nt_html,
        height=180
    )


    st.success(
        "🧪 This animation is an educational visualization of chemical signaling."
    )


    if st.button(
        "🏠 Return to Brain",
        use_container_width=True,
        key="nt_home"
    ):

        navigate(
            "brain",
            region
        )


# ============================================================
# ASK AYNA
# ============================================================

st.divider()

st.header("🤖 Ask Ayna")

st.write(
    "Ask questions about cognition, behavior, neurons, "
    "brain regions, neural circuits, synapses and neurotransmitters."
)


def get_gemini_api_key():

    for key_name in [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY"
    ]:

        try:

            value = st.secrets.get(
                key_name
            )

            if value:

                return str(value).strip()

        except Exception:

            pass


        value = os.getenv(
            key_name
        )

        if value:

            return value.strip()


    return None


def ask_ayna(question):

    if genai is None:

        return (
            "⚠️ google-genai is not installed. "
            "Check requirements.txt."
        )


    api_key = get_gemini_api_key()


    if not api_key:

        return (
            "⚠️ GEMINI_API_KEY is not configured in Streamlit Secrets."
        )


    try:

        client = genai.Client(
            api_key=api_key
        )


        prompt = f"""
You are Ask Ayna, the educational neuroscience assistant
inside NEUROLENS.

Explain cognitive neuroscience in a clear and scientifically
responsible way.

Topics can include:

- memory
- attention
- learning
- perception
- emotion
- decision-making
- reward
- cognitive control
- brain regions
- neural circuits
- neurons
- dendrites
- axons
- myelin
- synapses
- neurotransmitters
- neuroplasticity
- behavior

Rules:

1. Do not diagnose medical or psychiatric disorders.
2. Do not claim that simple games measure brain activity.
3. Do not present self-report scores as clinical measurements.
4. Distinguish established findings from hypotheses.
5. Use understandable language.
6. Do not invent scientific evidence.

Current NEUROLENS region:

{region}

User question:

{question}
"""


        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )


        answer = getattr(
            response,
            "text",
            None
        )


        if answer:

            return answer.strip()


        return (
            "⚠️ No answer was returned."
        )


    except Exception as error:

        return (
            "⚠️ Ask Ayna could not connect to Gemini.\n\n"
            f"Error: `{type(error).__name__}`\n\n"
            f"`{str(error)}`"
        )


if "ayna_messages" not in st.session_state:

    st.session_state.ayna_messages = []


for message in st.session_state.ayna_messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


question = st.chat_input(
    "Ask Ayna a neuroscience question..."
)


if question:

    st.session_state.ayna_messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    with st.chat_message("user"):

        st.markdown(
            question
        )


    with st.chat_message("assistant"):

        with st.spinner(
            "🧠 Ayna is thinking..."
        ):

            answer = ask_ayna(
                question
            )


        st.markdown(
            answer
        )


    st.session_state.ayna_messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


if st.session_state.get(
    "ayna_messages"
):

    if st.button(
        "🗑️ Clear Ask Ayna Chat",
        key="clear_chat"
    ):

        st.session_state.ayna_messages = []

        st.rerun()


# ============================================================
# COGNITIVE GAMES
# ============================================================

st.divider()

st.header("🎮 Cognitive Games")


game = st.selectbox(
    "Choose a game",
    [
        "Select a game",
        "Decision Challenge",
        "Memory Challenge",
        "Attention Challenge",
        "Stroop Challenge",
        "Pattern Challenge"
    ],
    key="game_select"
)


# ------------------------------------------------------------
# DECISION
# ------------------------------------------------------------

if game == "Decision Challenge":

    st.subheader(
        "🧠 Decision Challenge"
    )


    choice = st.radio(
        "Which would you choose?",
        [
            "Rs. 1,000 today",
            "Rs. 1,500 after 30 days"
        ],
        key="decision"
    )


    if st.button(
        "Analyze Decision",
        key="decision_check"
    ):

        if choice == "Rs. 1,000 today":

            st.success(
                "Immediate reward preference selected."
            )

        else:

            st.success(
                "Delayed reward preference selected."
            )


        st.info(
            "Educational task related to decision-making and reward."
        )


# ------------------------------------------------------------
# MEMORY
# ------------------------------------------------------------

elif game == "Memory Challenge":

    st.subheader(
        "🧠 Memory Challenge"
    )


    st.write(
        "Remember this sequence:"
    )


    st.markdown(
        "## **7 2 9 4 1 8**"
    )


    answer = st.text_input(
        "Enter the sequence",
        key="memory_input"
    )


    if st.button(
        "Check Memory",
        key="memory_check"
    ):

        if answer.replace(
            " ",
            ""
        ) == "729418":

            st.success(
                "🎉 Correct!"
            )

        else:

            st.error(
                "Not quite. Try again."
            )


# ------------------------------------------------------------
# ATTENTION
# ------------------------------------------------------------

elif game == "Attention Challenge":

    st.subheader(
        "🎯 Attention Challenge"
    )


    target = st.selectbox(
        "Which sequence contains X?",
        [
            "A B C D",
            "A B X D",
            "A B C E",
            "A B C F"
        ],
        key="attention"
    )


    if st.button(
        "Check Attention",
        key="attention_check"
    ):

        if "X" in target:

            st.success(
                "🎯 Correct!"
            )

        else:

            st.error(
                "Try again."
            )


# ------------------------------------------------------------
# STROOP
# ------------------------------------------------------------

elif game == "Stroop Challenge":

    st.subheader(
        "🎨 Stroop Challenge"
    )


    colors = {
        "RED": "#e53935",
        "BLUE": "#1e88e5",
        "GREEN": "#43a047",
        "YELLOW": "#d8b400"
    }


    if "stroop_word" not in st.session_state:

        st.session_state.stroop_word = random.choice(
            list(colors.keys())
        )

        st.session_state.stroop_color = random.choice(
            list(colors.keys())
        )


    if st.button(
        "🔄 New Trial",
        key="new_stroop"
    ):

        st.session_state.stroop_word = random.choice(
            list(colors.keys())
        )

        st.session_state.stroop_color = random.choice(
            list(colors.keys())
        )

        st.rerun()


    word = st.session_state.stroop_word

    color = st.session_state.stroop_color


    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:50px;
            font-weight:bold;
            color:{colors[color]};
            padding:20px;
        ">
        {word}
        </div>
        """,
        unsafe_allow_html=True
    )


    answer = st.selectbox(
        "What COLOR is the word displayed in?",
        list(colors.keys()),
        key="stroop_answer"
    )


    if st.button(
        "Check Stroop",
        key="stroop_check"
    ):

        if answer == color:

            st.success(
                "🎯 Correct!"
            )

        else:

            st.info(
                "Stroop tasks explore attention and interference."
            )


# ------------------------------------------------------------
# PATTERN
# ------------------------------------------------------------

elif game == "Pattern Challenge":

    st.subheader(
        "🔢 Pattern Challenge"
    )


    st.markdown(
        "## 2 → 4 → 8 → 16 → ?"
    )


    answer = st.number_input(
        "Your answer",
        min_value=0,
        step=1,
        key="pattern"
    )


    if st.button(
        "Check Pattern",
        key="pattern_check"
    ):

        if answer == 32:

            st.success(
                "🎉 Correct!"
            )

        else:

            st.error(
                "Try again."
            )


# ============================================================
# COGNITIVE SELF REPORT
# ============================================================

st.divider()

st.header(
    "📊 Cognitive Self-Report"
)


st.caption(
    "These are self-reported educational ratings, "
    "not direct measurements of brain activity."
)


mental_load = st.slider(
    "Mental Load",
    1,
    10,
    5,
    key="mental_load_slider"
)


sleep_quality = st.slider(
    "Sleep Quality",
    1,
    10,
    5,
    key="sleep_slider"
)


attention_level = st.slider(
    "Attention",
    1,
    10,
    5,
    key="attention_slider"
)


memory_confidence = st.slider(
    "Memory Confidence",
    1,
    10,
    5,
    key="memory_slider"
)


st.bar_chart(
    {
        "Mental Load": mental_load,
        "Sleep Quality": sleep_quality,
        "Attention": attention_level,
        "Memory Confidence": memory_confidence
    }
)


# ============================================================
# 3D NEURAL VISUALIZATION
# ============================================================

st.divider()

st.header(
    "🧬 3D Neural Visualization"
)


if go is not None:

    points = [

        (0, 0, 0),
        (1, 1, 1),
        (2, 0, 1),
        (3, 1, 0),
        (4, 0, 2),
        (5, 1, 1),
        (6, 0, 0),
        (2, 2, 2),
        (4, 2, 1),
        (6, 2, 2)
    ]


    x = [
        point[0]
        for point in points
    ]


    y = [
        point[1]
        for point in points
    ]


    z = [
        point[2]
        for point in points
    ]


    connections = [

        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (1, 7),
        (3, 8),
        (5, 9)
    ]


    fig = go.Figure()


    for start, end in connections:

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x[start],
                    x[end]
                ],

                y=[
                    y[start],
                    y[end]
                ],

                z=[
                    z[start],
                    z[end]
                ],

                mode="lines",

                line=dict(
                    width=4
                ),

                showlegend=False
            )
        )


    fig.add_trace(
        go.Scatter3d(

            x=x,

            y=y,

            z=z,

            mode="markers",

            marker=dict(
                size=10
            ),

            text=[
                f"Neuron {i}"
                for i in range(
                    1,
                    11
                )
            ],

            hovertemplate=
                "%{text}<extra></extra>",

            showlegend=False
        )
    )


    fig.update_layout(

        title="Educational Neural Network",

        height=600,

        scene=dict(

            xaxis_title="X",

            yaxis_title="Y",

            zaxis_title="Z"
        ),

        margin=dict(
            l=0,
            r=0,
            b=0,
            t=50
        )
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


else:

    st.warning(
        "Plotly is not installed."
    )


# ============================================================
# BRAIN PUZZLE
# ============================================================

st.divider()

st.header(
    "🧩 Brain Picture Puzzle"
)


if brain_image is not None:

    difficulty = st.selectbox(
        "Puzzle difficulty",
        [
            "Easy — 4 pieces",
            "Medium — 9 pieces",
            "Hard — 16 pieces"
        ],
        key="puzzle_level"
    )


    if difficulty.startswith("Easy"):

        rows = 2
        cols = 2

    elif difficulty.startswith("Medium"):

        rows = 3
        cols = 3

    else:

        rows = 4
        cols = 4


    total = rows * cols


    image_width, image_height = brain_image.size


    piece_width = image_width // cols

    piece_height = image_height // rows


    pieces = []


    for row in range(rows):

        for col in range(cols):

            left = col * piece_width

            top = row * piece_height

            right = (
                (col + 1) * piece_width
                if col < cols - 1
                else image_width
            )

            bottom = (
                (row + 1) * piece_height
                if row < rows - 1
                else image_height
            )


            pieces.append(
                brain_image.crop(
                    (
                        left,
                        top,
                        right,
                        bottom
                    )
                )
            )


    if (
        "puzzle_order"
        not in st.session_state
        or
        st.session_state.get(
            "puzzle_total"
        ) != total
    ):

        st.session_state.puzzle_order = list(
            range(total)
        )

        random.shuffle(
            st.session_state.puzzle_order
        )

        st.session_state.puzzle_total = total


    if st.button(
        "🔀 New Puzzle",
        key="new_puzzle"
    ):

        st.session_state.puzzle_order = list(
            range(total)
        )

        random.shuffle(
            st.session_state.puzzle_order
        )

        st.rerun()


    index = 0


    for row in range(rows):

        puzzle_columns = st.columns(
            cols
        )


        for col in range(cols):

            piece_number = (
                st.session_state
                .puzzle_order[index]
            )


            with puzzle_columns[col]:

                st.image(
                    pieces[piece_number],
                    use_container_width=True
                )

                st.caption(
                    f"Piece {piece_number + 1}"
                )


            index += 1


    st.markdown(
        "### 🧩 Reconstruct the brain"
    )


    correct_order = " ".join(
        str(i)
        for i in range(
            1,
            total + 1
        )
    )


    answer = st.text_input(
        f"Enter order: {correct_order}",
        key="puzzle_answer"
    )


    if st.button(
        "✅ Check Puzzle",
        key="puzzle_check"
    ):

        try:

            user_order = [
                int(number)
                for number in answer.split()
            ]


            expected = list(
                range(
                    1,
                    total + 1
                )
            )


            if user_order == expected:

                st.success(
                    "🎉 Puzzle solved!"
                )

                st.balloons()

            else:

                st.error(
                    "Not correct yet. Try again."
                )


        except ValueError:

            st.error(
                "Enter numbers separated by spaces."
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.header(
    "📚 Science Note"
)

st.write(
    "NEUROLENS is an educational cognitive neuroscience platform. "
    "Its games, self-report ratings and visualizations are "
    "not clinical assessments and do not directly measure brain activity."
)

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • Created by Ayna"
)
