import os
import random
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import plotly.graph_objects as go

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
.main-title {
    font-size: 48px;
    font-weight: 800;
    margin-bottom: 0;
}
.subtitle {
    font-size: 20px;
    opacity: 0.75;
}
.card {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(120,120,120,.25);
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🧠 NEUROLENS</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Explore cognition, behavior & the brain</div>',
    unsafe_allow_html=True
)

# =========================================================
# GEMINI
# =========================================================

try:
    from google import genai
except Exception:
    genai = None


def get_gemini_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]

        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def ask_ayna(question, context="General neuroscience"):
    api_key = get_gemini_api_key()

    if not api_key:
        return (
            "Ask Ayna is not connected yet. "
            "Please add GEMINI_API_KEY in Streamlit Secrets."
        )

    if genai is None:
        return "Google GenAI package is not installed."

    prompt = f"""
You are Ayna, an educational cognitive neuroscience guide inside NEUROLENS.

Current learning context:
{context}

User question:
{question}

Explain clearly for a learner.

Rules:
- Be scientifically responsible.
- Do not diagnose medical conditions.
- Do not claim that simple games measure actual brain activity.
- Explain brain, cognition, behavior and neural mechanisms.
- Use simple language but maintain scientific accuracy.
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Ask Ayna could not respond right now: {e}"


# =========================================================
# BRAIN IMAGE
# =========================================================

brain_path = "brain.png"

if os.path.exists(brain_path):
    brain_image = Image.open(brain_path)
else:
    brain_image = None


# =========================================================
# NEURAL JOURNEY DATA
# =========================================================

REGIONS = {
    "Prefrontal Cortex": {
        "description":
            "The prefrontal cortex is strongly involved in planning, cognitive control, working memory and decision-making.",
        "behavior":
            "It helps you pause, evaluate options and guide behavior toward a goal.",
        "color": "#ff6b6b"
    },

    "Hippocampus": {
        "description":
            "The hippocampus is important for forming and organizing many types of memories and for spatial navigation.",
        "behavior":
            "It helps connect experiences with context and supports learning.",
        "color": "#4dabf7"
    },

    "Amygdala": {
        "description":
            "The amygdala is involved in processing emotionally significant information, especially threat and salience.",
        "behavior":
            "It can influence attention, emotional learning and defensive responses.",
        "color": "#ffd43b"
    },

    "Striatum": {
        "description":
            "The striatum is part of the basal ganglia and contributes to action selection, reward processing and learning.",
        "behavior":
            "It helps link actions with their consequences and supports habit learning.",
        "color": "#69db7c"
    },

    "Anterior Cingulate Cortex": {
        "description":
            "The anterior cingulate cortex contributes to monitoring conflict, errors, motivation and cognitive control.",
        "behavior":
            "It helps detect when behavior needs adjustment.",
        "color": "#da77f2"
    },

    "Cerebellum": {
        "description":
            "The cerebellum coordinates movement and also contributes to learning, timing and some cognitive processes.",
        "behavior":
            "It helps refine actions through prediction and error correction.",
        "color": "#20c997"
    }
}


# =========================================================
# SESSION STATE
# =========================================================

if "journey_level" not in st.session_state:
    st.session_state.journey_level = "brain"

if "selected_region" not in st.session_state:
    st.session_state.selected_region = None

if "journey_running" not in st.session_state:
    st.session_state.journey_running = False

if "journey_voice" not in st.session_state:
    st.session_state.journey_voice = True


# =========================================================
# VOICE HELPER
# =========================================================

def voice_html(text):
    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", " ")
        .replace("'", "\\'")
    )

    return f"""
    <script>
    function speakText() {{
        window.speechSynthesis.cancel();

        const text = '{safe_text}';
        const utterance = new SpeechSynthesisUtterance(text);

        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        window.speechSynthesis.speak(utterance);
    }}

    speakText();
    </script>
    """


# =========================================================
# NEURAL JOURNEY HEADER
# =========================================================

st.markdown("---")

st.subheader("🌌 Neural Journey")

st.write(
    "Click a brain region. The pathway opens and the journey moves "
    "from brain → region → neuron → axon → synapse → neurotransmitter."
)

# =========================================================
# MAP-LIKE VISUAL JOURNEY
# =========================================================

journey_html = """
<!DOCTYPE html>
<html>
<head>

<style>

body {
    margin:0;
    font-family:Arial,sans-serif;
    background:#05070d;
    color:white;
    overflow:hidden;
}

#scene {
    position:relative;
    width:100%;
    height:620px;
    overflow:hidden;
    border-radius:24px;
    background:
        radial-gradient(circle at center,#17213d 0%,#070a12 55%,#030409 100%);
}

#space {
    position:absolute;
    width:100%;
    height:100%;
    transform-origin:center center;
    transition:transform 2.2s cubic-bezier(.2,.8,.2,1);
}

.node {
    position:absolute;
    border-radius:50%;
    cursor:pointer;
    transition:
        transform 1.5s ease,
        box-shadow 1s ease,
        opacity 1s ease;
}

.node:hover {
    transform:scale(1.2);
}

.brain {
    width:230px;
    height:160px;
    left:calc(50% - 115px);
    top:210px;

    background:
        radial-gradient(
            ellipse at 50% 45%,
            #d9b5a9,
            #9b756e 65%,
            #55413f
        );

    border-radius:55% 45% 48% 52%;
    box-shadow:
        0 0 45px rgba(150,180,255,.4),
        inset 0 0 35px rgba(255,255,255,.15);
}

.region {
    width:34px;
    height:34px;
    background:#7dd3fc;
    box-shadow:
        0 0 10px #7dd3fc,
        0 0 30px #7dd3fc;
    opacity:0;
    pointer-events:none;
}

.path {
    position:absolute;
    height:4px;
    background:linear-gradient(
        90deg,
        transparent,
        #67e8f9,
        #a78bfa,
        transparent
    );
    box-shadow:0 0 15px #67e8f9;
    transform-origin:left center;
    opacity:0;
    transition:opacity 1.2s ease;
}

.label {
    position:absolute;
    padding:8px 14px;
    border-radius:20px;
    background:rgba(0,0,0,.55);
    border:1px solid rgba(255,255,255,.18);
    font-size:14px;
    backdrop-filter:blur(8px);
    opacity:0;
    transition:opacity 1s ease;
}

.center-text {
    position:absolute;
    left:50%;
    top:45px;
    transform:translateX(-50%);
    text-align:center;
}

.center-text h2 {
    margin:0;
    font-size:25px;
}

.center-text p {
    opacity:.65;
}

#controls {
    position:absolute;
    left:20px;
    bottom:20px;
    display:flex;
    gap:10px;
    z-index:50;
}

button {
    border:1px solid rgba(255,255,255,.2);
    background:rgba(255,255,255,.08);
    color:white;
    padding:10px 15px;
    border-radius:12px;
    cursor:pointer;
}

button:hover {
    background:rgba(255,255,255,.18);
}

#signal {
    position:absolute;
    width:13px;
    height:13px;
    border-radius:50%;
    background:#fff;
    box-shadow:
        0 0 10px #fff,
        0 0 30px #67e8f9,
        0 0 60px #67e8f9;
    opacity:0;
}

@keyframes travel {
    0% {
        transform:translateX(0);
        opacity:0;
    }

    15% {
        opacity:1;
    }

    85% {
        opacity:1;
    }

    100% {
        transform:translateX(700px);
        opacity:0;
    }
}

</style>
</head>

<body>

<div id="scene">

<div id="space">

<div class="center-text">
<h2 id="title">Whole Brain</h2>
<p id="subtitle">Choose a region to begin the journey</p>
</div>

<div id="brain" class="node brain" onclick="startJourney()"></div>

<div id="region1" class="node region" style="left:40%;top:38%;"></div>
<div id="region2" class="node region" style="left:53%;top:43%;"></div>

<div id="path1" class="path"
     style="left:43%;top:48%;width:300px;transform:rotate(-18deg);">
</div>

<div id="path2" class="path"
     style="left:52%;top:48%;width:260px;transform:rotate(25deg);">
</div>

<div id="neuron"
     class="node"
     style="
     width:70px;
     height:70px;
     left:66%;
     top:34%;
     background:radial-gradient(circle,#f0abfc,#7e22ce);
     box-shadow:0 0 40px #c084fc;
     opacity:0;
     pointer-events:none;
     ">
</div>

<div id="axon"
     class="path"
     style="
     left:68%;
     top:40%;
     width:240px;
     transform:rotate(12deg);
     ">
</div>

<div id="synapse"
     class="node"
     style="
     width:45px;
     height:45px;
     left:87%;
     top:46%;
     background:#fef08a;
     box-shadow:0 0 45px #facc15;
     opacity:0;
     ">
</div>

<div id="signal"></div>

<div id="labelRegion" class="label" style="left:38%;top:28%;">
Region
</div>

<div id="labelNeuron" class="label" style="left:65%;top:25%;">
Neuron
</div>

<div id="labelAxon" class="label" style="left:75%;top:57%;">
Axon + signal
</div>

<div id="labelSynapse" class="label" style="left:82%;top:35%;">
Synapse
</div>

</div>

<div id="controls">
<button onclick="zoomOut()">↩ Back</button>
<button onclick="resetJourney()">↺ Reset</button>
<button onclick="voice()">🔊 Voice</button>
</div>

</div>

<script>

let stage = 0;

const space = document.getElementById("space");
const title = document.getElementById("title");
const subtitle = document.getElementById("subtitle");

function speak(text) {
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95;
    u.pitch = 1;
    u.volume = 1;

    window.speechSynthesis.speak(u);
}

function voice() {

    const texts = [
        "Whole brain. Select a region to begin.",
        "Brain region selected. We are entering a deeper neural level.",
        "Neuron level. Information is processed and communicated through neural signals.",
        "Axon level. An electrical signal is travelling along the neuron.",
        "Synapse level. The neuron communicates with another cell.",
        "Neurotransmitter level. Chemical messengers carry information across the synaptic gap."
    ];

    speak(texts[stage]);
}

function startJourney() {

    stage = 1;

    title.innerText = "Neural pathway opening";
    subtitle.innerText =
        "Following the selected brain region...";

    document.getElementById("region1").style.opacity = "1";
    document.getElementById("region2").style.opacity = "1";

    document.getElementById("path1").style.opacity = "1";
    document.getElementById("path2").style.opacity = "1";

    document.getElementById("labelRegion").style.opacity = "1";

    space.style.transform =
        "scale(1.8) translate(-12%, -5%)";

    setTimeout(() => {

        stage = 2;

        title.innerText = "Neuron";

        document.getElementById("neuron").style.opacity = "1";
        document.getElementById("neuron").style.pointerEvents = "auto";
        document.getElementById("labelNeuron").style.opacity = "1";

        space.style.transform =
            "scale(2.8) translate(-28%, -8%)";

        speak(
            "The pathway has opened. We are now entering the neuron."
        );

    }, 2200);

    setTimeout(() => {

        stage = 3;

        title.innerText = "Axon — signal travelling";

        document.getElementById("axon").style.opacity = "1";
        document.getElementById("labelAxon").style.opacity = "1";

        space.style.transform =
            "scale(3.8) translate(-48%, -12%)";

        animateSignal();

        speak(
            "The signal is travelling along the axon."
        );

    }, 4700);

    setTimeout(() => {

        stage = 4;

        title.innerText = "Synapse";

        document.getElementById("synapse").style.opacity = "1";
        document.getElementById("labelSynapse").style.opacity = "1";

        space.style.transform =
            "scale(4.8) translate(-63%, -15%)";

        speak(
            "We have reached the synapse, where communication between cells occurs."
        );

    }, 7200);

    setTimeout(() => {

        stage = 5;

        title.innerText = "Neurotransmitter";

        subtitle.innerText =
            "Chemical signalling across the synapse";

        space.style.transform =
            "scale(5.8) translate(-72%, -18%)";

        speak(
            "Neurotransmitters carry chemical messages across the synapse."
        );

    }, 9800);
}


function animateSignal() {

    const signal = document.getElementById("signal");

    signal.style.left = "63%";
    signal.style.top = "39%";
    signal.style.opacity = "1";

    signal.style.animation =
        "travel 2.5s linear infinite";
}


function zoomOut() {

    if (stage > 0) {
        stage--;

        if (stage === 0) {
            resetJourney();
        }

        else if (stage === 1) {
            space.style.transform =
                "scale(1.8) translate(-12%, -5%)";

            title.innerText = "Brain Region";
        }

        else if (stage === 2) {
            space.style.transform =
                "scale(2.8) translate(-28%, -8%)";

            title.innerText = "Neuron";
        }

        else if (stage === 3) {
            space.style.transform =
                "scale(3.8) translate(-48%, -12%)";

            title.innerText = "Axon";
        }

        else if (stage === 4) {
            space.style.transform =
                "scale(4.8) translate(-63%, -15%)";

            title.innerText = "Synapse";
        }
    }
}


function resetJourney() {

    stage = 0;

    space.style.transform =
        "scale(1) translate(0,0)";

    title.innerText = "Whole Brain";

    subtitle.innerText =
        "Choose a region to begin the journey";

    document.getElementById("region1").style.opacity = "0";
    document.getElementById("region2").style.opacity = "0";

    document.getElementById("path1").style.opacity = "0";
    document.getElementById("path2").style.opacity = "0";

    document.getElementById("neuron").style.opacity = "0";
    document.getElementById("axon").style.opacity = "0";
    document.getElementById("synapse").style.opacity = "0";

    document.getElementById("labelRegion").style.opacity = "0";
    document.getElementById("labelNeuron").style.opacity = "0";
    document.getElementById("labelAxon").style.opacity = "0";
    document.getElementById("labelSynapse").style.opacity = "0";

    document.getElementById("signal").style.opacity = "0";

    window.speechSynthesis.cancel();
}

</script>

</body>
</html>
"""

components.html(
    journey_html,
    height=650,
    scrolling=False
)


# =========================================================
# REGION SELECTION
# =========================================================

st.markdown("### 🧩 Choose a Brain Region")

cols = st.columns(3)

for i, region in enumerate(REGIONS):

    with cols[i % 3]:

        if st.button(
            region,
            key=f"region_{region}",
            use_container_width=True
        ):
            st.session_state.selected_region = region
            st.session_state.journey_level = "region"

# =========================================================
# SELECTED REGION
# =========================================================

if st.session_state.selected_region:

    region = st.session_state.selected_region
    info = REGIONS[region]

    st.markdown("---")

    st.subheader(f"🔬 {region}")

    col1, col2 = st.columns([2, 1])

    with col1:

        st.markdown(
            f"""
            <div class="card">

            <h3>What does it do?</h3>

            <p>{info["description"]}</p>

            <h3>Behavior connection</h3>

            <p>{info["behavior"]}</p>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        if st.button(
            "🔊 Voice Explanation",
            use_container_width=True
        ):

            components.html(
                voice_html(
                    f"{region}. {info['description']} "
                    f"{info['behavior']}"
                ),
                height=0
            )

        st.success("Region selected")


# =========================================================
# ASK AYNA — CONTEXT AWARE
# =========================================================

st.markdown("---")
st.subheader("💬 Ask Ayna")

context = "Whole brain"

if st.session_state.selected_region:
    context = (
        f"Selected brain region: "
        f"{st.session_state.selected_region}"
    )

question = st.text_input(
    "Ask something about what you are exploring:",
    placeholder="Why is this region important for behavior?"
)

if st.button("Ask Ayna 🧠", use_container_width=True):

    if question.strip():

        with st.spinner("Ayna is thinking..."):

            answer = ask_ayna(
                question,
                context
            )

        st.markdown(
            f"""
            <div class="card">

            <h3>🧠 Ayna</h3>

            <p>{answer}</p>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("🔊 Read Ayna's answer"):

            components.html(
                voice_html(answer),
                height=0
            )

    else:
        st.warning("Pehle apna question likho.")


# =========================================================
# NEUROTRANSMITTER EXPLORER
# =========================================================

st.markdown("---")
st.subheader("⚡ Neurotransmitter Explorer")

neurotransmitters = {

    "Dopamine":
        "Dopamine is involved in reward learning, motivation, movement and several cognitive processes.",

    "Serotonin":
        "Serotonin participates in mood regulation, sleep, appetite and many other brain functions.",

    "GABA":
        "GABA is the major inhibitory neurotransmitter in the central nervous system.",

    "Glutamate":
        "Glutamate is the major excitatory neurotransmitter and is important for learning and synaptic plasticity.",

    "Acetylcholine":
        "Acetylcholine contributes to attention, learning, memory and communication between neurons."
}

selected_neuro = st.selectbox(
    "Choose a neurotransmitter",
    list(neurotransmitters.keys())
)

st.info(neurotransmitters[selected_neuro])

if st.button("🔊 Hear neurotransmitter explanation"):

    components.html(
        voice_html(
            selected_neuro +
            ". " +
            neurotransmitters[selected_neuro]
        ),
        height=0
    )


# =========================================================
# 3D NEURAL VISUALIZATION
# =========================================================

st.markdown("---")
st.subheader("🌐 3D Neural Network")

random.seed(10)

nodes = []

for i in range(30):

    nodes.append({
        "x": random.uniform(-5, 5),
        "y": random.uniform(-5, 5),
        "z": random.uniform(-5, 5)
    })

fig = go.Figure()

for i in range(len(nodes)):

    for j in range(i + 1, len(nodes)):

        dx = nodes[i]["x"] - nodes[j]["x"]
        dy = nodes[i]["y"] - nodes[j]["y"]
        dz = nodes[i]["z"] - nodes[j]["z"]

        distance = (
            dx * dx +
            dy * dy +
            dz * dz
        ) ** 0.5

        if distance < 3:

            fig.add_trace(
                go.Scatter3d(
                    x=[
                        nodes[i]["x"],
                        nodes[j]["x"]
                    ],
                    y=[
                        nodes[i]["y"],
                        nodes[j]["y"]
                    ],
                    z=[
                        nodes[i]["z"],
                        nodes[j]["z"]
                    ],
                    mode="lines",
                    line=dict(
                        width=2
                    ),
                    showlegend=False
                )
            )

fig.add_trace(
    go.Scatter3d(
        x=[n["x"] for n in nodes],
        y=[n["y"] for n in nodes],
        z=[n["z"] for n in nodes],
        mode="markers",
        marker=dict(
            size=6
        ),
        name="Neurons"
    )
)

fig.update_layout(
    height=650,
    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================================================
# COGNITIVE GAMES
# =========================================================

st.markdown("---")
st.subheader("🎮 Cognitive Games")

game = st.selectbox(
    "Choose a challenge",
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
        "You have two options. Which would you choose?"
    )

    choice = st.radio(
        "Choose:",
        [
            "Immediate reward",
            "Delayed larger reward"
        ]
    )

    if st.button("Submit Decision"):

        if choice == "Delayed larger reward":
            st.success(
                "Interesting choice. Delay discounting is "
                "one concept studied in decision-making research."
            )
        else:
            st.info(
                "Interesting choice. Immediate reward preference "
                "can be studied in decision-making research."
            )


elif game == "Memory":

    sequence = "7 2 9 4 1"

    st.write(
        "Memorize this sequence:"
    )

    st.code(sequence)

    answer = st.text_input(
        "Enter the sequence:"
    )

    if st.button("Check Memory"):

        if answer.replace(" ", "") == sequence.replace(" ", ""):
            st.success("Correct!")
        else:
            st.error("Not quite.")


elif game == "Attention":

    st.write(
        "Find the number 7 as quickly as possible."
    )

    grid = [
        3, 8, 2, 6,
        1, 9, 4, 5,
        8, 3, 7, 2,
        6, 4, 1, 9
    ]

    st.write(" ".join(map(str, grid)))

    answer = st.text_input(
        "Which number are you looking for?"
    )

    if st.button("Check Attention"):

        if answer == "7":
            st.success("Found it!")
        else:
            st.error("Try again.")


elif game == "Stroop":

    st.write(
        "Name the INK COLOR, not the written word."
    )

    st.markdown(
        """
        <div style="
        font-size:40px;
        font-weight:bold;
        text-align:center;
        ">
        BLUE
        </div>
        """,
        unsafe_allow_html=True
    )

    answer = st.text_input(
        "Ink color:"
    )

    if st.button("Check Stroop"):

        if answer.lower() == "red":
            st.success("Correct!")
        else:
            st.error("Think about the ink color.")


else:

    st.write(
        "Complete the pattern:"
    )

    st.markdown(
        "2 → 4 → 8 → 16 → ?"
    )

    answer = st.text_input(
        "Your answer:"
    )

    if st.button("Check Pattern"):

        if answer == "32":
            st.success("Correct!")
        else:
            st.error("Try again.")


# =========================================================
# SELF REPORT
# =========================================================

st.markdown("---")
st.subheader("🧠 Cognitive Self-Report")

focus = st.slider(
    "Current focus level",
    1,
    10,
    5
)

stress = st.slider(
    "Current stress level",
    1,
    10,
    5
)

energy = st.slider(
    "Current mental energy",
    1,
    10,
    5
)

if st.button("Show My Snapshot"):

    st.write({
        "Focus": focus,
        "Stress": stress,
        "Mental Energy": energy
    })

    st.caption(
        "This is a self-report snapshot, not a clinical assessment "
        "or direct measurement of brain activity."
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "NEUROLENS — Educational exploration of cognition, "
    "behavior and neuroscience."
)

st.caption(
    "Created by Ayna Jaffri"
)
