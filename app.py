import os
import random
import base64
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
# NEUROLENS
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 NEUROLENS")
st.caption("Explore cognition, behavior, brain systems & neural pathways")

st.divider()


# ============================================================
# BRAIN IMAGE
# ============================================================

BRAIN_IMAGE = "brain.png"

brain_image = None

if os.path.exists(BRAIN_IMAGE):
    try:
        brain_image = Image.open(BRAIN_IMAGE)
    except Exception:
        brain_image = None


# ============================================================
# BRAIN PARTS
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
            "The anterior cingulate cortex contributes to performance "
            "monitoring, conflict processing and cognitive control."
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
            "The cerebellum contributes to coordination, timing, "
            "balance and motor learning."
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
# HELPER
# ============================================================

def go_to(level, region):
    st.query_params["level"] = level
    st.query_params["region"] = region
    st.rerun()


# ============================================================
# INTERACTIVE BRAIN EXPLORER
# ============================================================

st.header("🧠 Interactive Brain Explorer")

if brain_image is not None:

    st.image(
        brain_image,
        caption="NEUROLENS Brain",
        use_container_width=True,
    )

else:

    st.warning(
        "brain.png not found. Keep brain.png in the same folder as app.py."
    )


selected_part = st.selectbox(
    "🔍 Choose a brain region",
    list(brain_parts.keys()),
    key="brain_region_select",
)

info = brain_parts[selected_part]

col1, col2 = st.columns(2)

with col1:

    st.subheader(f"🔬 {selected_part}")

    st.info(
        info["description"]
    )

    st.markdown("**Behavioral role**")

    st.write(
        info["behavior"]
    )

with col2:

    st.subheader("🔗 Circuit")

    st.code(
        info["circuit"]
    )


# ============================================================
# NERVE EXPLORER
# ============================================================

st.divider()

st.header("🧬 Nerve Explorer")

st.write(
    "Tap a brain region and progressively zoom from the whole brain "
    "to neurons, axons, synapses and neurotransmitters."
)


level = st.query_params.get(
    "level",
    "brain",
)

region = st.query_params.get(
    "region",
    selected_part,
)

if region not in brain_parts:

    region = selected_part


level_names = {

    "brain": "Whole Brain",

    "region": "Brain Region",

    "neuron": "Neuron",

    "axon": "Axon & Myelin",

    "synapse": "Synapse",

    "nt": "Neurotransmitter",
}


st.markdown(
    """
    ### 🔎 Exploration Path

    🧠 Brain  
    ↓  
    🔬 Brain Region  
    ↓  
    🧬 Neuron  
    ↓  
    ⚡ Axon & Myelin  
    ↓  
    🔗 Synapse  
    ↓  
    🧪 Neurotransmitter
    """
)

st.caption(
    f"Current level: **{level_names.get(level, 'Whole Brain')}**"
)


# ============================================================
# WHOLE BRAIN — CLICKABLE REGIONS
# ============================================================

if level == "brain":

    st.subheader(
        "🧠 Tap a region to zoom in"
    )

    if brain_image is not None:

        with open(
            BRAIN_IMAGE,
            "rb"
        ) as image_file:

            image_base64 = base64.b64encode(
                image_file.read()
            ).decode()

        html = f"""

        <div class="brain-container">

            <img
                src="data:image/png;base64,{image_base64}"
                class="brain-image"
            >

            <button
                class="spot pfc"
                onclick="openRegion('Prefrontal Cortex')"
            >
                +
            </button>

            <button
                class="spot hippo"
                onclick="openRegion('Hippocampus')"
            >
                +
            </button>

            <button
                class="spot amygdala"
                onclick="openRegion('Amygdala')"
            >
                +
            </button>

            <button
                class="spot striatum"
                onclick="openRegion('Striatum')"
            >
                +
            </button>

            <button
                class="spot acc"
                onclick="openRegion('Anterior Cingulate Cortex')"
            >
                +
            </button>

            <button
                class="spot cerebellum"
                onclick="openRegion('Cerebellum')"
            >
                +
            </button>

        </div>


        <style>

        .brain-container {{
            position:relative;
            width:100%;
            max-width:900px;
            margin:auto;
            overflow:hidden;
            border-radius:20px;
        }}

        .brain-image {{
            width:100%;
            display:block;
        }}

        .spot {{
            position:absolute;

            transform:translate(-50%,-50%);

            width:48px;
            height:48px;

            border-radius:50%;

            border:3px solid white;

            background:rgba(75,90,255,0.55);

            color:white;

            font-size:28px;

            font-weight:bold;

            cursor:pointer;

            box-shadow:
                0 0 0 6px rgba(75,90,255,0.15),
                0 0 25px rgba(75,90,255,0.65);

            animation:pulse 1.7s infinite;

            z-index:5;
        }}

        .spot:hover {{
            transform:
                translate(-50%,-50%)
                scale(1.15);

            background:
                rgba(75,90,255,0.85);
        }}

        .pfc {{
            left:20%;
            top:38%;
        }}

        .acc {{
            left:40%;
            top:30%;
        }}

        .striatum {{
            left:48%;
            top:44%;
        }}

        .amygdala {{
            left:56%;
            top:50%;
        }}

        .hippo {{
            left:53%;
            top:62%;
        }}

        .cerebellum {{
            left:78%;
            top:72%;
        }}

        @keyframes pulse {{

            0%,100% {{
                box-shadow:
                    0 0 0 5px
                    rgba(75,90,255,0.15),
                    0 0 20px
                    rgba(75,90,255,0.35);
            }}

            50% {{
                box-shadow:
                    0 0 0 12px
                    rgba(75,90,255,0.05),
                    0 0 35px
                    rgba(75,90,255,0.75);
            }}

        }}

        </style>


        <script>

        function openRegion(region) {{

            const url =
                new URL(
                    window.parent.location.href
                );

            url.searchParams.set(
                "level",
                "region"
            );

            url.searchParams.set(
                "region",
                region
            );

            window.parent.location.href =
                url.toString();

        }}

        </script>

        """

        components.html(
            html,
            height=650,
        )

    else:

        st.info(
            "Add brain.png to activate clickable brain exploration."
        )


# ============================================================
# REGION LEVEL
# ============================================================

elif level == "region":

    st.subheader(
        f"🔬 Zoomed Brain Region — {region}"
    )

    data = brain_parts[region]

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            f"## 🧠 {region}"
        )

        st.info(
            data["description"]
        )

        st.markdown(
            "### 🧠 Behavioral Role"
        )

        st.write(
            data["behavior"]
        )

    with col2:

        st.markdown(
            "### 🔗 Circuit"
        )

        st.code(
            data["circuit"]
        )

        st.markdown(
            "### 🔎 Next Level"
        )

        if st.button(
            "🧬 Zoom into Neuron",
            use_container_width=True,
        ):

            go_to(
                "neuron",
                region,
            )

    if st.button(
        "🔙 Back to Brain",
        use_container_width=True,
    ):

        go_to(
            "brain",
            region,
        )


# ============================================================
# NEURON LEVEL
# ============================================================

elif level == "neuron":

    st.subheader(
        f"🧬 Neuron — {region}"
    )

    neuron_part = st.selectbox(
        "🔍 Explore a neuron part",
        [
            "Dendrites",
            "Cell Body (Soma)",
            "Nucleus",
            "Axon",
            "Axon Terminal",
        ],
        key="neuron_part",
    )

    neuron_info = {

        "Dendrites":
            "Dendrites receive incoming signals and contribute to integrating information.",

        "Cell Body (Soma)":
            "The soma contains the nucleus and supports the neuron's metabolic functions.",

        "Nucleus":
            "The nucleus contains genetic material and regulates many cellular activities.",

        "Axon":
            "The axon carries electrical signals away from the cell body toward other targets.",

        "Axon Terminal":
            "Axon terminals are specialized regions where neurons communicate with other cells.",
    }

    st.success(
        neuron_info[neuron_part]
    )


    neuron_html = """

    <div class="neuron">

        <div class="branch b1"></div>
        <div class="branch b2"></div>
        <div class="branch b3"></div>
        <div class="branch b4"></div>

        <div class="soma">
            ●
        </div>

        <div class="axon">

            <div class="myelin m1"></div>
            <div class="myelin m2"></div>
            <div class="myelin m3"></div>

        </div>

        <div class="terminal t1"></div>
        <div class="terminal t2"></div>

    </div>


    <style>

    .neuron {{

        position:relative;

        height:360px;

        max-width:900px;

        margin:auto;

        background:
            linear-gradient(
                135deg,
                #f7f9ff,
                #eef2ff
            );

        border-radius:25px;

        overflow:hidden;

    }}


    .soma {{

        position:absolute;

        left:34%;

        top:40%;

        width:100px;

        height:100px;

        border-radius:50%;

        background:#e7b1cf;

        border:
            5px solid
            #8c4d78;

        display:flex;

        align-items:center;

        justify-content:center;

        font-size:35px;

    }}


    .axon {{

        position:absolute;

        left:45%;

        top:49%;

        width:45%;

        height:16px;

        background:#8b6b50;

        border-radius:20px;

    }}


    .myelin {{

        position:absolute;

        top:-12px;

        width:80px;

        height:40px;

        border-radius:25px;

        background:#dce7f4;

        border:
            3px solid
            #8da1ba;

    }}


    .m1 {{
        left:40px;
    }}

    .m2 {{
        left:145px;
    }}

    .m3 {{
        left:250px;
    }}


    .branch {{

        position:absolute;

        left:15%;

        top:50%;

        width:190px;

        height:10px;

        background:#8b6b50;

        border-radius:10px;

        transform-origin:right center;

    }}


    .b1 {{
        transform:rotate(-60deg);
    }}

    .b2 {{
        transform:rotate(-25deg);
    }}

    .b3 {{
        transform:rotate(25deg);
    }}

    .b4 {{
        transform:rotate(60deg);
    }}


    .terminal {{

        position:absolute;

        right:7%;

        top:44%;

        width:45px;

        height:45px;

        border-radius:50%;

        background:#b486c4;

        border:
            4px solid
            #70477b;

    }}


    .t1 {{
        transform:translateY(-35px);
    }}

    .t2 {{
        transform:translateY(35px);
    }}

    </style>

    """

    components.html(
        neuron_html,
        height=390,
    )


    if st.button(
        "⚡ Zoom into Axon & Myelin",
        use_container_width=True,
    ):

        go_to(
            "axon",
            region,
        )


    if st.button(
        "🔙 Back to Region",
        use_container_width=True,
    ):

        go_to(
            "region",
            region,
        )


# ============================================================
# AXON & MYELIN
# ============================================================

elif level == "axon":

    st.subheader(
        f"⚡ Axon & Myelin — {region}"
    )

    st.info(
        "The axon provides a pathway for electrical signaling. "
        "Myelin insulates many axons and supports rapid signal conduction."
    )


    st.markdown(
        "### ⚡ Neural Signal"
    )


    signal_html = """

    <div class="track">

        <div class="myelin2 one"></div>
        <div class="myelin2 two"></div>
        <div class="myelin2 three"></div>
        <div class="myelin2 four"></div>

        <div class="signal"></div>

    </div>


    <style>

    .track {{

        position:relative;

        height:140px;

        max-width:900px;

        margin:auto;

        background:#f4f6fa;

        border-radius:25px;

        border:
            3px solid
            #cbd5e1;

        overflow:hidden;

    }}


    .track:before {{

        content:"";

        position:absolute;

        left:4%;

        right:4%;

        top:62px;

        height:16px;

        background:#8b6b50;

        border-radius:20px;

    }}


    .myelin2 {{

        position:absolute;

        top:47px;

        width:115px;

        height:44px;

        border-radius:25px;

        background:#dce7f4;

        border:
            3px solid
            #8da1ba;

    }}


    .one {{
        left:10%;
    }}

    .two {{
        left:31%;
    }}

    .three {{
        left:52%;
    }}

    .four {{
        left:73%;
    }}


    .signal {{

        position:absolute;

        top:55px;

        left:4%;

        width:30px;

        height:30px;

        border-radius:50%;

        background:#705cff;

        box-shadow:
            0 0 25px
            #705cff;

        animation:
            moveSignal
            2.2s
            linear
            infinite;

    }}


    @keyframes moveSignal {{

        from {{
            left:4%;
        }}

        to {{
            left:94%;
        }}

    }}

    </style>

    """

    components.html(
        signal_html,
        height=180,
    )


    st.success(
        "⚡ The signal is traveling along the educational axon model."
    )


    if st.button(
        "🔗 Continue to Synapse",
        use_container_width=True,
    ):

        go_to(
            "synapse",
            region,
        )


    if st.button(
        "🔙 Back to Neuron",
        use_container_width=True,
    ):

        go_to(
            "neuron",
            region,
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
        "🔍 Explore a synaptic component",
        [
            "Presynaptic Terminal",
            "Synaptic Vesicles",
            "Synaptic Cleft",
            "Postsynaptic Membrane",
            "Receptors",
        ],
        key="synapse_part",
    )


    synapse_info = {

        "Presynaptic Terminal":
            "The presynaptic terminal is the sending side of many chemical synapses.",

        "Synaptic Vesicles":
            "Synaptic vesicles can store neurotransmitters and release them into the synaptic cleft.",

        "Synaptic Cleft":
            "The synaptic cleft is the small extracellular space between communicating cells.",

        "Postsynaptic Membrane":
            "The postsynaptic membrane contains molecular machinery that detects incoming signals.",

        "Receptors":
            "Receptors are proteins that detect specific signaling molecules and can change cellular responses.",
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

        <div class="nt n1"></div>
        <div class="nt n2"></div>
        <div class="nt n3"></div>

        <div class="receptor r1"></div>
        <div class="receptor r2"></div>
        <div class="receptor r3"></div>

    </div>


    <style>

    .synapse {{

        position:relative;

        height:300px;

        max-width:900px;

        margin:auto;

        background:#f8fafc;

        border-radius:25px;

        overflow:hidden;

        border:
            2px solid
            #dbe2ea;

    }}


    .pre,
    .post {{

        position:absolute;

        top:45%;

        width:34%;

        height:80px;

        border-radius:35px;

    }}


    .pre {{

        left:7%;

        background:#d8a8c8;

    }}


    .post {{

        right:7%;

        background:#a8c8df;

    }}


    .cleft {{

        position:absolute;

        left:43%;

        width:14%;

        top:20%;

        height:60%;

        background:white;

        border-left:
            3px dashed
            #b7c0ca;

        border-right:
            3px dashed
            #b7c0ca;

    }}


    .ves,
    .nt {{

        position:absolute;

        border-radius:50%;

    }}


    .ves {{

        width:18px;

        height:18px;

        background:#9b6bb0;

    }}


    .v1 {{
        left:31%;
        top:44%;
    }}

    .v2 {{
        left:35%;
        top:54%;
    }}

    .v3 {{
        left:38%;
        top:40%;
    }}


    .nt {{

        width:14px;

        height:14px;

        background:#6c63ff;

        box-shadow:
            0 0 12px
            #6c63ff;

        animation:
            release
            2s
            infinite;

    }}


    .n1 {{
        left:45%;
        top:42%;
    }}

    .n2 {{
        left:49%;
        top:51%;
    }}

    .n3 {{
        left:53%;
        top:45%;
    }}


    .receptor {{

        position:absolute;

        right:29%;

        width:14px;

        height:35px;

        background:#587fa3;

        border-radius:8px;

    }}


    .r1 {{
        top:38%;
    }}

    .r2 {{
        top:48%;
    }}

    .r3 {{
        top:58%;
    }}


    @keyframes release {{

        from {{
            transform:translateX(0);
        }}

        to {{
            transform:translateX(55px);
        }}

    }}

    </style>

    """

    components.html(
        synapse_html,
        height=330,
    )


    if st.button(
        "🧪 Explore Neurotransmitters",
        use_container_width=True,
    ):

        go_to(
            "nt",
            region,
        )


    if st.button(
        "🔙 Back to Axon",
        use_container_width=True,
    ):

        go_to(
            "axon",
            region,
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
            "Participates in mood regulation, sleep, appetite and many physiological and cognitive processes.",

        "GABA":
            "The major inhibitory neurotransmitter in the central nervous system.",

        "Glutamate":
            "The major excitatory neurotransmitter in the central nervous system and is important for learning.",

        "Acetylcholine":
            "Contributes to attention, learning, memory and neuromuscular communication.",
    }


    nt = st.selectbox(
        "🧪 Choose a neurotransmitter",
        list(neurotransmitters.keys()),
        key="nt_select",
    )


    st.markdown(
        f"## 🧪 {nt}"
    )

    st.info(
        neurotransmitters[nt]
    )


    st.markdown(
        "### ⚡ Signal Animation"
    )


    signal_html = """

    <div class="nt-track">

        <div class="nt-dot d1"></div>
        <div class="nt-dot d2"></div>
        <div class="nt-dot d3"></div>
        <div class="nt-dot d4"></div>
        <div class="nt-dot d5"></div>

    </div>


    <style>

    .nt-track {{

        position:relative;

        height:150px;

        background:
            linear-gradient(
                90deg,
                #f2e9ff,
                #eef8ff
            );

        border-radius:25px;

        overflow:hidden;

    }}


    .nt-dot {{

        position:absolute;

        width:24px;

        height:24px;

        border-radius:50%;

        background:#755cff;

        box-shadow:
            0 0 20px
            #755cff;

        animation:
            fly
            2.4s
            linear
            infinite;

    }}


    .d1 {{
        top:30%;
        animation-delay:0s;
    }}

    .d2 {{
        top:55%;
        animation-delay:.35s;
    }}

    .d3 {{
        top:40%;
        animation-delay:.7s;
    }}

    .d4 {{
        top:65%;
        animation-delay:1.05s;
    }}

    .d5 {{
        top:25%;
        animation-delay:1.4s;
    }}


    @keyframes fly {{

        from {{
            left:-5%;
        }}

        to {{
            left:105%;
        }}

    }}

    </style>

    """

    components.html(
        signal_html,
        height=180,
    )


    if st.button(
        "🔙 Back to Synapse",
        use_container_width=True,
    ):

        go_to(
            "synapse",
            region,
        )


    if st.button(
        "🏠 Start Again at Brain",
        use_container_width=True,
    ):

        go_to(
            "brain",
            region,
        )


# ============================================================
# ASK AYNA
# ============================================================

st.divider()

st.header("🤖 Ask Ayna 🧠")

st.write(
    "Ask Ayna about memory, attention, learning, behavior, "
    "brain systems, neurons, synapses and neuroscience."
)


def get_gemini_api_key():

    for name in [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ]:

        try:

            key = st.secrets.get(
                name
            )

            if key:

                return str(
                    key
                ).strip()

        except Exception:

            pass


        key = os.getenv(
            name
        )

        if key:

            return key.strip()


    return None


def ask_ayna(question):

    if genai is None:

        return (
            "⚠️ Gemini package is not installed. "
            "Check requirements.txt."
        )


    api_key = get_gemini_api_key()

    if not api_key:

        return (
            "⚠️ Add GEMINI_API_KEY to Streamlit Secrets."
        )


    try:

        client = genai.Client(
            api_key=api_key
        )


        prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience assistant
inside NEUROLENS.

Explain neuroscience clearly and accurately.

Topics include:

memory
attention
learning
emotion
decision-making
reward
perception
cognitive control
brain systems
neural circuits
neurons
dendrites
axons
myelin
synapses
neurotransmitters
neuroplasticity
behavioral neuroscience

Rules:

1. Do not diagnose medical or psychiatric disorders.
2. Do not claim simple games measure brain activity.
3. Do not present self-reported ratings as clinical measurements.
4. Distinguish established evidence from hypotheses.
5. Use simple but scientifically accurate language.
6. If medical diagnosis is requested, recommend a qualified professional.
7. Do not invent scientific evidence.

User question:

{question}
"""


        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )


        answer = getattr(
            response,
            "text",
            None,
        )


        if answer:

            return answer.strip()


        return (
            "⚠️ Ask Ayna received an empty response."
        )


    except Exception as e:

        return (
            "⚠️ Ask Ayna could not connect to Gemini.\n\n"
            f"Error: `{type(e).__name__}`\n\n"
            f"Details: `{str(e)}`"
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
            "content": question,
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
            "content": answer,
        }
    )


if st.session_state.get(
    "ayna_messages"
):

    if st.button(
        "🗑️ Clear Ask Ayna Chat",
        key="clear_ayna",
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
        "Pattern Challenge",
    ],
    key="cognitive_game",
)


if game == "Decision Challenge":

    st.subheader(
        "🧠 Decision Challenge"
    )

    choice = st.radio(
        "Which would you prefer?",
        [
            "Rs. 1,000 today",
            "Rs. 1,500 after 30 days",
        ],
        key="decision_choice",
    )


    if st.button(
        "Analyze Decision",
        key="analyze_decision",
    ):

        if choice == "Rs. 1,000 today":

            st.success(
                "Immediate-reward preference"
            )

        else:

            st.success(
                "Delayed-reward preference"
            )


        st.info(
            "This is an educational decision-making task."
        )


elif game == "Memory Challenge":

    st.subheader(
        "🧠 Memory Challenge"
    )

    sequence = "7 2 9 4 1 8"

    st.write(
        "Remember:"
    )

    st.markdown(
        f"## **{sequence}**"
    )


    answer = st.text_input(
        "Enter the sequence:",
        key="memory_answer",
    )


    if st.button(
        "Check Memory",
        key="check_memory",
    ):

        if answer.replace(
            " ",
            "",
        ) == "729418":

            st.success(
                "🎉 Correct!"
            )

        else:

            st.error(
                "Not quite. Try again."
            )


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
            "A B C F",
        ],
        key="attention_target",
    )


    if st.button(
        "Check Attention",
        key="check_attention",
    ):

        if "X" in target:

            st.success(
                "🎯 Correct!"
            )

            st.info(
                "This task explores visual search and attention."
            )

        else:

            st.error(
                "Try again!"
            )


elif game == "Stroop Challenge":

    st.subheader(
        "🎨 Stroop Challenge"
    )


    colors = {

        "RED": "#e53935",

        "BLUE": "#1e88e5",

        "GREEN": "#43a047",

        "YELLOW": "#d8b400",
    }


    if "stroop_word" not in st.session_state:

        st.session_state.stroop_word = random.choice(
            list(colors.keys())
        )

        st.session_state.stroop_color = random.choice(
            list(colors.keys())
        )


    if st.button(
        "🔄 New Stroop Trial",
        key="new_stroop",
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
        unsafe_allow_html=True,
    )


    answer = st.selectbox(
        "What COLOR is the word displayed in?",
        list(colors.keys()),
        key="stroop_answer",
    )


    if st.button(
        "Check Stroop",
        key="check_stroop",
    ):

        if answer == color:

            st.success(
                "🎯 Correct! This explores response control."
            )

        else:

            st.info(
                "Stroop tasks explore attention and interference."
            )


elif game == "Pattern Challenge":

    st.subheader(
        "🔢 Pattern Recognition"
    )


    st.markdown(
        "### 2 → 4 → 8 → 16 → ?"
    )


    answer = st.number_input(
        "Your answer",
        min_value=0,
        step=1,
        key="pattern_answer",
    )


    if st.button(
        "Check Pattern",
        key="check_pattern",
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
    "not measurements of brain activity."
)


mental_load = st.slider(
    "Mental Load",
    1,
    10,
    5,
    key="mental_load",
)


sleep_quality = st.slider(
    "Sleep Quality",
    1,
    10,
    5,
    key="sleep_quality",
)


attention_level = st.slider(
    "Attention",
    1,
    10,
    5,
    key="attention_level",
)


memory_confidence = st.slider(
    "Memory Confidence",
    1,
    10,
    5,
    key="memory_confidence",
)


st.bar_chart(
    {
        "Mental Load": mental_load,
        "Sleep Quality": sleep_quality,
        "Attention": attention_level,
        "Memory Confidence": memory_confidence,
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

        (6, 2, 2),
    ]


    x = [
        p[0]
        for p in points
    ]

    y = [
        p[1]
        for p in points
    ]

    z = [
        p[2]
        for p in points
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

        (5, 9),
    ]


    fig = go.Figure()


    for start, end in connections:

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x[start],
                    x[end],
                ],

                y=[
                    y[start],
                    y[end],
                ],

                z=[
                    z[start],
                    z[end],
                ],

                mode="lines",

                line=dict(
                    width=4
                ),

                showlegend=False,
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
                for i in range(1, 11)
            ],

            hovertemplate=
                "%{text}<extra></extra>",

            showlegend=False,
        )
    )


    fig.update_layout(

        title=
            "Educational Neural Network",

        height=600,

        scene=dict(

            xaxis_title="X",

            yaxis_title="Y",

            zaxis_title="Z",
        ),

        margin=dict(

            l=0,

            r=0,

            b=0,

            t=50,
        ),
    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )


else:

    st.warning(
        "Plotly is missing. Add plotly to requirements.txt."
    )


# ============================================================
# BRAIN PUZZLE
# ============================================================

st.divider()

st.header(
    "🧩 Full Brain Picture Puzzle"
)


if brain_image is not None:

    difficulty = st.selectbox(
        "Puzzle difficulty",
        [
            "Easy — 4 pieces",
            "Medium — 9 pieces",
            "Hard — 16 pieces",
        ],
        key="puzzle_difficulty",
    )


    if difficulty.startswith(
        "Easy"
    ):

        rows, cols = 2, 2

    elif difficulty.startswith(
        "Medium"
    ):

        rows, cols = 3, 3

    else:

        rows, cols = 4, 4


    image = brain_image.convert(
        "RGB"
    )


    width, height = image.size


    piece_width = (
        width // cols
    )

    piece_height = (
        height // rows
    )


    pieces = []


    for row in range(rows):

        for col in range(cols):

            left = (
                col * piece_width
            )

            top = (
                row * piece_height
            )


            right = (

                (col + 1)
                * piece_width

                if col < cols - 1

                else width
            )


            bottom = (

                (row + 1)
                * piece_height

                if row < rows - 1

                else height
            )


            pieces.append(
                image.crop(
                    (
                        left,
                        top,
                        right,
                        bottom,
                    )
                )
            )


    total = (
        rows * cols
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
        key="new_puzzle",
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

        columns = st.columns(
            cols
        )


        for col in range(cols):

            piece_number = (
                st.session_state
                .puzzle_order[index]
            )


            with columns[col]:

                st.image(
                    pieces[piece_number],
                    use_container_width=True,
                )

                st.caption(
                    f"Piece {piece_number + 1}"
                )


            index += 1


    example = " ".join(
        str(i)
        for i in range(
            1,
            total + 1
        )
    )


    answer = st.text_input(
        f"Enter order: {example}",
        key="puzzle_answer",
    )


    if st.button(
        "✅ Check Puzzle",
        key="check_puzzle",
    ):

        try:

            user_order = [
                int(x)
                for x in answer.split()
            ]


            correct_order = list(
                range(
                    1,
                    total + 1
                )
            )


            if user_order == correct_order:

                st.success(
                    "🎉 Brain puzzle solved!"
                )

                st.balloons()

                st.info(
                    "This educational task explores "
                    "visual-spatial organization and attention."
                )

            else:

                st.error(
                    "Not correct yet. Try again."
                )


        except ValueError:

            st.error(
                "Enter numbers separated by spaces."
            )


# ============================================================
# SCIENCE NOTE
# ============================================================

st.divider()

st.header(
    "📚 Science Note"
)

st.write(
    "NEUROLENS is an educational cognitive neuroscience tool. "
    "Its games, self-reported ratings and visualizations are "
    "not clinical assessments or direct measurements of brain activity."
)

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • Created by Ayna"
)
