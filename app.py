import os
import random
import base64
import html
import streamlit as st

from PIL import Image

try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

try:
    from google import genai
    GEMINI_OK = True
except Exception:
    GEMINI_OK = False

import streamlit.components.v1 as components


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# GLOBAL DATA
# =========================================================

BRAIN_PARTS = {
    "Prefrontal Cortex": {
        "short": "Planning, decision-making and cognitive control.",
        "function": "Supports planning, working memory, inhibition and goal-directed decisions.",
        "behavior": "Helps you pause, evaluate choices and control impulses.",
        "journey": "A major control hub involved in higher-order cognition."
    },

    "Hippocampus": {
        "short": "Memory formation and spatial navigation.",
        "function": "Important for forming and retrieving episodic and spatial memories.",
        "behavior": "Helps you remember experiences and navigate familiar environments.",
        "journey": "A key memory-related structure within the medial temporal lobe."
    },

    "Amygdala": {
        "short": "Emotional learning and threat processing.",
        "function": "Processes emotionally significant information, especially threat and salience.",
        "behavior": "Can influence fear, vigilance and rapid emotional responses.",
        "journey": "Part of networks involved in emotion and salience."
    },

    "Striatum": {
        "short": "Action selection, learning and reward.",
        "function": "Participates in action selection, reinforcement learning and reward-related processing.",
        "behavior": "Helps link actions with outcomes and learned habits.",
        "journey": "A central component of cortico-striatal circuits."
    },

    "Anterior Cingulate Cortex": {
        "short": "Conflict monitoring and cognitive control.",
        "function": "Involved in monitoring conflict, errors, effort and control demands.",
        "behavior": "Helps detect when behavior needs adjustment.",
        "journey": "An important node in cognitive-control networks."
    },

    "Cerebellum": {
        "short": "Coordination, timing and motor learning.",
        "function": "Supports coordination, timing and motor learning and also contributes to some cognitive processes.",
        "behavior": "Helps make movements smoother and more precisely timed.",
        "journey": "Contains highly organized neural circuitry with dense neuronal populations."
    }
}


NEUROTRANSMITTERS = {
    "Dopamine": {
        "role": "Reward, motivation, learning and movement.",
        "examples": "Reward prediction, reinforcement learning and motor control."
    },

    "Serotonin": {
        "role": "Mood, sleep, appetite and many regulatory processes.",
        "examples": "Modulates several brain networks and behavioral states."
    },

    "GABA": {
        "role": "Major inhibitory neurotransmitter.",
        "examples": "Helps regulate neuronal excitability and network balance."
    },

    "Glutamate": {
        "role": "Major excitatory neurotransmitter.",
        "examples": "Important for learning, memory and synaptic plasticity."
    },

    "Acetylcholine": {
        "role": "Attention, learning, memory and neuromodulation.",
        "examples": "Important in attention and memory-related networks."
    }
}


JOURNEY = [
    ("brain", "Whole Brain", "Start with the large-scale brain landscape."),
    ("region", "Brain Region", "Move toward a selected functional region."),
    ("circuit", "Neural Circuit", "Follow connected brain regions."),
    ("neuron", "Neuron", "Travel from tissue into a single neuron."),
    ("axon", "Axon + Myelin", "Follow the path carrying electrical signals."),
    ("synapse", "Synapse", "Reach the communication point between neurons."),
    ("chemical", "Neurotransmitter", "Explore chemical signaling between neurons.")
]


# =========================================================
# SESSION STATE
# =========================================================

if "selected_region" not in st.session_state:
    st.session_state.selected_region = "Prefrontal Cortex"

if "journey_stage" not in st.session_state:
    st.session_state.journey_stage = 0

if "progress" not in st.session_state:
    st.session_state.progress = set()

if "ask_messages" not in st.session_state:
    st.session_state.ask_messages = []

if "game_score" not in st.session_state:
    st.session_state.game_score = 0


# =========================================================
# HELPERS
# =========================================================

def get_brain_image():
    path = os.path.join(os.path.dirname(__file__), "brain.png")

    if os.path.exists(path):
        return Image.open(path)

    return None


def brain_base64():
    path = os.path.join(os.path.dirname(__file__), "brain.png")

    if not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def mark_progress(item):
    st.session_state.progress.add(item)


def voice(text, key="voice"):
    safe_text = html.escape(text).replace("\n", " ")

    components.html(
        f"""
        <button
            onclick="speakText()"
            style="
                padding:9px 16px;
                border-radius:10px;
                border:1px solid #aaa;
                background:#ffffff;
                cursor:pointer;
                font-size:14px;
            ">
            🔊 Voice
        </button>

        <script>
        function speakText() {{
            const text = `{safe_text}`;
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.95;
            utterance.pitch = 1;
            window.speechSynthesis.speak(utterance);
        }}
        </script>
        """,
        height=48
    )


# =========================================================
# GEMINI / ASK AYNA
# =========================================================

def get_gemini_key():
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


def ask_ayna(question, context=""):
    key = get_gemini_key()

    if not key:
        return "Gemini API key nahi mili. Streamlit Secrets mein GEMINI_API_KEY add karein."

    if not GEMINI_OK:
        return "google-genai package installed nahi hai."

    prompt = f"""
You are Ask Ayna inside NEUROLENS, an educational cognitive neuroscience platform.

Answer scientifically and clearly.

Context:
{context}

Question:
{question}

Rules:
- Educational explanation only.
- Do not diagnose.
- Do not claim that simple cognitive games measure brain activity.
- Explain uncertainty when appropriate.
- Keep the answer understandable for students and general learners.
"""

    try:
        client = genai.Client(api_key=key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Ask Ayna temporarily unavailable: {e}"


# =========================================================
# HEADER
# =========================================================

st.title("🧠 NEUROLENS")

st.caption(
    "Explore cognition, behavior & the brain — by Ayna Jaffri"
)

st.divider()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🧠 NEUROLENS")

page = st.sidebar.radio(
    "Explore",
    [
        "Brain Explorer",
        "Neural Journey",
        "Neuron Explorer",
        "Signal Animation",
        "Synapse Explorer",
        "Neurotransmitter Explorer",
        "3D Neural Visualization",
        "Cognitive Games",
        "Brain Picture Puzzle",
        "Cognitive Self-Report",
        "Ask Ayna",
        "Learning Progress",
        "Science Notes"
    ]
)

st.sidebar.divider()

st.sidebar.caption("Created by Ayna Jaffri")
st.sidebar.caption("Cognitive Neuroscience × AI × Behavior")


# =========================================================
# 1. BRAIN EXPLORER
# =========================================================

if page == "Brain Explorer":

    st.header("🧠 Interactive Brain Explorer")

    image = get_brain_image()

    col1, col2 = st.columns([1.5, 1])

    with col1:

        if image:
            st.image(
                image,
                use_container_width=True
            )
        else:
            st.error("brain.png nahi mili.")

    with col2:

        region = st.selectbox(
            "Select a brain region",
            list(BRAIN_PARTS.keys()),
            index=list(BRAIN_PARTS.keys()).index(
                st.session_state.selected_region
            )
        )

        st.session_state.selected_region = region

        data = BRAIN_PARTS[region]

        st.subheader(region)

        st.write(data["short"])

        st.markdown("### Function")
        st.write(data["function"])

        st.markdown("### Behavior")
        st.write(data["behavior"])

        voice(
            f"{region}. {data['function']} {data['behavior']}",
            key=f"brainvoice_{region}"
        )

        if st.button(
            "🔬 Explore this region in Neural Journey",
            key="explore_region"
        ):
            st.session_state.selected_region = region
            st.session_state.journey_stage = 1
            mark_progress("Brain Region")
            st.rerun()


# =========================================================
# 2. CINEMATIC NEURAL JOURNEY
# =========================================================

elif page == "Neural Journey":

    st.header("🗺️ Neural Journey")

    st.write(
        "Travel through the brain like a scientific animation: "
        "Whole Brain → Region → Circuit → Neuron → Axon → Synapse → Neurotransmitter."
    )

    image_b64 = brain_base64()

    if not image_b64:

        st.error(
            "brain.png missing hai. GitHub repo mein app.py ke saath brain.png upload karein."
        )

    else:

        region = st.session_state.selected_region
        stage = st.session_state.journey_stage

        stage_name = JOURNEY[stage][1]
        stage_description = JOURNEY[stage][2]

        # Different camera positions for selected region.
        focus_positions = {
            "Prefrontal Cortex": (-18, -7),
            "Hippocampus": (7, 13),
            "Amygdala": (10, 22),
            "Striatum": (2, 3),
            "Anterior Cingulate Cortex": (-3, -1),
            "Cerebellum": (22, 20)
        }

        tx, ty = focus_positions.get(region, (0, 0))

        zoom_values = {
            0: 1.0,
            1: 1.7,
            2: 2.2,
            3: 3.0,
            4: 4.0,
            5: 5.0,
            6: 6.0
        }

        zoom = zoom_values.get(stage, 1)

        show_route = stage >= 1
        show_neuron = stage >= 3
        show_axon = stage >= 4
        show_synapse = stage >= 5
        show_chemical = stage >= 6

        route_html = ""

        if show_route:
            route_html = """
            <div class="neural-route">
                <div class="route-pulse"></div>
            </div>
            """

        neuron_html = ""

        if show_neuron:
            neuron_html = """
            <div class="neuron">
                <div class="dendrite d1"></div>
                <div class="dendrite d2"></div>
                <div class="dendrite d3"></div>
                <div class="soma">
                    <div class="nucleus"></div>
                </div>
                <div class="axon">
                    <div class="signal"></div>
                </div>
                <div class="terminal"></div>
            </div>
            """

        synapse_html = ""

        if show_synapse:
            synapse_html = """
            <div class="synapse">
                <div class="pre-neuron"></div>
                <div class="synaptic-gap"></div>
                <div class="post-neuron"></div>
                <div class="vesicle v1"></div>
                <div class="vesicle v2"></div>
                <div class="vesicle v3"></div>
                <div class="neurotransmitter n1"></div>
                <div class="neurotransmitter n2"></div>
                <div class="neurotransmitter n3"></div>
            </div>
            """

        chemical_html = ""

        if show_chemical:
            chemical_html = """
            <div class="chemical-cloud">
                <span>●</span>
                <span>●</span>
                <span>●</span>
                <span>●</span>
                <span>●</span>
                <span>●</span>
            </div>
            """

        scene = f"""
        <style>

        * {{
            box-sizing:border-box;
        }}

        body {{
            margin:0;
            background:#050816;
            font-family:Arial, sans-serif;
            color:white;
        }}

        .journey {{
            height:650px;
            width:100%;
            overflow:hidden;
            position:relative;
            border-radius:24px;
            background:
                radial-gradient(circle at 50% 45%, #16244c 0%, #070b1c 45%, #02030a 100%);
            box-shadow:0 20px 60px rgba(0,0,0,.45);
        }}

        .space {{
            position:absolute;
            inset:0;
            overflow:hidden;
        }}

        .brain-world {{
            position:absolute;
            width:78%;
            left:11%;
            top:5%;
            transform:
                translate({tx}%, {ty}%)
                scale({zoom});
            transform-origin:center center;
            transition:
                transform 2.4s cubic-bezier(.2,.8,.2,1);
        }}

        .brain-world img {{
            width:100%;
            display:block;
            filter:
                drop-shadow(0 0 25px rgba(80,160,255,.25));
        }}

        .route {{
            position:absolute;
            left:50%;
            top:35%;
            width:5px;
            height:35%;
            background:
                linear-gradient(
                    to bottom,
                    transparent,
                    #55e7ff,
                    #b4f7ff,
                    transparent
                );
            box-shadow:
                0 0 10px #55e7ff,
                0 0 30px rgba(85,231,255,.7);
            transform:rotate(18deg);
            opacity:.9;
        }}

        .route-pulse {{
            width:15px;
            height:15px;
            background:#fff;
            border-radius:50%;
            position:absolute;
            left:-5px;
            top:-5px;
            box-shadow:
                0 0 15px #fff,
                0 0 30px #55e7ff;
            animation:travel 2s linear infinite;
        }}

        @keyframes travel {{
            0% {{ top:0%; opacity:0; }}
            10% {{ opacity:1; }}
            90% {{ opacity:1; }}
            100% {{ top:100%; opacity:0; }}
        }}

        .neuron {{
            position:absolute;
            left:55%;
            top:42%;
            width:260px;
            height:180px;
            transform:scale(.55);
            transform-origin:center;
        }}

        .soma {{
            position:absolute;
            width:90px;
            height:90px;
            border-radius:50%;
            left:75px;
            top:45px;
            background:
                radial-gradient(circle at 40% 35%, #ffb6e8, #9a45d5);
            box-shadow:
                0 0 30px rgba(210,100,255,.7);
        }}

        .nucleus {{
            width:35px;
            height:35px;
            border-radius:50%;
            background:#42115f;
            position:absolute;
            left:28px;
            top:28px;
        }}

        .dendrite {{
            position:absolute;
            height:7px;
            width:100px;
            background:#c57cff;
            border-radius:10px;
            transform-origin:right center;
            box-shadow:0 0 10px #c57cff;
        }}

        .d1 {{
            left:0;
            top:30px;
            transform:rotate(20deg);
        }}

        .d2 {{
            left:0;
            top:75px;
            transform:rotate(-8deg);
        }}

        .d3 {{
            left:55px;
            top:130px;
            transform:rotate(-35deg);
        }}

        .axon {{
            position:absolute;
            width:170px;
            height:9px;
            background:#63dfff;
            left:155px;
            top:86px;
            border-radius:10px;
            box-shadow:0 0 15px #63dfff;
        }}

        .signal {{
            position:absolute;
            width:20px;
            height:20px;
            border-radius:50%;
            background:white;
            top:-5px;
            box-shadow:
                0 0 12px white,
                0 0 30px #54e9ff;
            animation:signalMove 1.3s linear infinite;
        }}

        @keyframes signalMove {{
            from {{ left:0; }}
            to {{ left:150px; }}
        }}

        .terminal {{
            position:absolute;
            width:35px;
            height:35px;
            border-radius:50%;
            background:#8cf3ff;
            left:315px;
            top:73px;
            box-shadow:0 0 25px #8cf3ff;
        }}

        .synapse {{
            position:absolute;
            left:50%;
            top:50%;
            transform:scale(.8);
            width:420px;
            height:180px;
        }}

        .pre-neuron,
        .post-neuron {{
            position:absolute;
            width:150px;
            height:30px;
            border-radius:50%;
            background:#a951ff;
            box-shadow:0 0 20px #a951ff;
        }}

        .pre-neuron {{
            left:0;
            top:70px;
        }}

        .post-neuron {{
            right:0;
            top:70px;
            background:#4be7ff;
            box-shadow:0 0 20px #4be7ff;
        }}

        .synaptic-gap {{
            position:absolute;
            width:80px;
            height:4px;
            background:white;
            left:170px;
            top:84px;
            box-shadow:0 0 20px white;
        }}

        .vesicle {{
            position:absolute;
            width:15px;
            height:15px;
            border-radius:50%;
            background:#ffdb69;
            left:135px;
            animation:release 2s infinite;
        }}

        .v1 {{ top:60px; }}
        .v2 {{ top:80px; animation-delay:.3s; }}
        .v3 {{ top:100px; animation-delay:.6s; }}

        @keyframes release {{
            0%,30% {{ transform:translateX(0); opacity:1; }}
            80% {{ transform:translateX(100px); opacity:.8; }}
            100% {{ transform:translateX(120px); opacity:0; }}
        }}

        .neurotransmitter {{
            position:absolute;
            width:13px;
            height:13px;
            border-radius:50%;
            background:#fff;
            box-shadow:
                0 0 10px white,
                0 0 25px #55e7ff;
        }}

        .n1 {{
            left:190px;
            top:65px;
            animation:chemical 2s infinite;
        }}

        .n2 {{
            left:200px;
            top:95px;
            animation:chemical 2s infinite .4s;
        }}

        .n3 {{
            left:180px;
            top:110px;
            animation:chemical 2s infinite .8s;
        }}

        @keyframes chemical {{
            0% {{ opacity:0; transform:translateX(0); }}
            25% {{ opacity:1; }}
            100% {{ opacity:0; transform:translateX(100px); }}
        }}

        .chemical-cloud {{
            position:absolute;
            inset:0;
            pointer-events:none;
        }}

        .chemical-cloud span {{
            position:absolute;
            font-size:24px;
            color:#ffe76a;
            text-shadow:
                0 0 10px #ffe76a,
                0 0 25px #ff9d4d;
            animation:floatChemical 2.5s infinite;
        }}

        .chemical-cloud span:nth-child(1) {{
            left:45%;
            top:45%;
        }}

        .chemical-cloud span:nth-child(2) {{
            left:50%;
            top:50%;
            animation-delay:.3s;
        }}

        .chemical-cloud span:nth-child(3) {{
            left:55%;
            top:42%;
            animation-delay:.6s;
        }}

        .chemical-cloud span:nth-child(4) {{
            left:48%;
            top:58%;
            animation-delay:.9s;
        }}

        .chemical-cloud span:nth-child(5) {{
            left:58%;
            top:55%;
            animation-delay:1.2s;
        }}

        .chemical-cloud span:nth-child(6) {{
            left:52%;
            top:38%;
            animation-delay:1.5s;
        }}

        @keyframes floatChemical {{
            0% {{
                transform:translate(0,0) scale(.5);
                opacity:0;
            }}
            40% {{
                opacity:1;
            }}
            100% {{
                transform:translate(70px,-40px) scale(1.3);
                opacity:0;
            }}
        }}

        .overlay {{
            position:absolute;
            left:25px;
            right:25px;
            bottom:20px;
            padding:18px 22px;
            border-radius:18px;
            background:rgba(4,8,22,.76);
            backdrop-filter:blur(12px);
            border:1px solid rgba(255,255,255,.12);
        }}

        .stage {{
            font-size:24px;
            font-weight:700;
        }}

        .description {{
            margin-top:6px;
            color:#cbd4ef;
        }}

        </style>

        <div class="journey">
            <div class="space">

                <div class="brain-world">
                    <img src="data:image/png;base64,{image_b64}">
                    {route_html}
                    {neuron_html}
                    {synapse_html}
                    {chemical_html}
                </div>

            </div>

            <div class="overlay">
                <div class="stage">
                    🧠 {html.escape(stage_name)}
                </div>

                <div class="description">
                    {html.escape(stage_description)}
                </div>
            </div>
        </div>
        """

        components.html(scene, height=680, scrolling=False)

        st.subheader(f"Current destination: {stage_name}")

        st.info(
            f"Selected region: {region}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button(
                "⬅️ Back",
                disabled=(stage == 0),
                use_container_width=True
            ):
                st.session_state.journey_stage -= 1
                st.rerun()

        with c2:
            if st.button(
                "🚀 Travel deeper",
                disabled=(stage == len(JOURNEY) - 1),
                use_container_width=True
            ):
                st.session_state.journey_stage += 1
                mark_progress(stage_name)
                st.rerun()

        with c3:
            if st.button(
                "🔄 Start again",
                use_container_width=True
            ):
                st.session_state.journey_stage = 0
                st.rerun()

        if stage == 0:
            explanation = (
                "You are viewing the whole brain. "
                "The next step moves toward a selected brain region."
            )

        elif stage == 1:
            explanation = BRAIN_PARTS[region]["journey"]

        elif stage == 2:
            explanation = (
                "Neural circuits are networks of connected regions "
                "that work together to support behavior and cognition."
            )

        elif stage == 3:
            explanation = (
                "Neurons are specialized cells that communicate using "
                "electrical and chemical signals."
            )

        elif stage == 4:
            explanation = (
                "The axon carries electrical signals away from the soma. "
                "Myelin can increase the efficiency of signal conduction."
            )

        elif stage == 5:
            explanation = (
                "A synapse is a communication site where one neuron "
                "can influence another."
            )

        else:
            explanation = (
                "Neurotransmitters are chemical messengers released "
                "by neurons and detected by receptors."
            )

        st.markdown("### 🔊 Explanation")

        st.write(explanation)

        voice(
            f"{stage_name}. {explanation}",
            key=f"journey_voice_{stage}"
        )

        st.markdown("### 💬 Ask Ayna about this stage")

        q = st.text_input(
            "Your question",
            key=f"journey_question_{stage}"
        )

        if st.button(
            "Ask Ayna",
            key=f"journey_ask_{stage}"
        ):

            context = (
                f"Neural Journey stage: {stage_name}. "
                f"Selected brain region: {region}. "
                f"Educational context: {explanation}"
            )

            answer = ask_ayna(q, context)

            st.markdown("#### Ask Ayna")
            st.write(answer)

            voice(
                answer,
                key=f"journey_answer_voice_{stage}"
            )


# =========================================================
# 3. NEURON EXPLORER
# =========================================================

elif page == "Neuron Explorer":

    st.header("🔬 Neuron Explorer")

    neuron_part = st.selectbox(
        "Choose a neuron structure",
        [
            "Dendrites",
            "Soma",
            "Nucleus",
            "Axon",
            "Myelin",
            "Axon Terminal"
        ]
    )

    neuron_info = {
        "Dendrites":
            "Dendrites receive and integrate signals from other cells.",

        "Soma":
            "The soma contains the nucleus and integrates cellular processes.",

        "Nucleus":
            "The nucleus contains genetic material and regulates gene expression.",

        "Axon":
            "The axon conducts electrical signals away from the soma.",

        "Myelin":
            "Myelin forms insulating layers around many axons and supports efficient signal conduction.",

        "Axon Terminal":
            "Axon terminals can release neurotransmitters at synapses."
    }

    st.markdown("### 🧬 " + neuron_part)

    st.info(neuron_info[neuron_part])

    voice(
        f"{neuron_part}. {neuron_info[neuron_part]}",
        key=f"neuron_voice_{neuron_part}"
    )

    st.markdown("""
    ### Basic neural pathway

    **Dendrites → Soma → Axon → Axon Terminal → Synapse**
    """)


# =========================================================
# 4. SIGNAL ANIMATION
# =========================================================

elif page == "Signal Animation":

    st.header("⚡ Neural Signal Animation")

    st.write(
        "Watch a simplified educational representation of a signal traveling along an axon."
    )

    signal_html = """
    <style>
    .signalbox{
        height:220px;
        background:#060b20;
        border-radius:20px;
        position:relative;
        overflow:hidden;
    }

    .axonline{
        position:absolute;
        left:8%;
        right:8%;
        top:50%;
        height:12px;
        background:#62e8ff;
        border-radius:20px;
        box-shadow:0 0 20px #62e8ff;
    }

    .pulse{
        position:absolute;
        top:calc(50% - 15px);
        left:8%;
        width:30px;
        height:30px;
        border-radius:50%;
        background:white;
        box-shadow:
            0 0 15px white,
            0 0 40px #62e8ff;
        animation:move 3s linear infinite;
    }

    @keyframes move{
        from{left:8%;}
        to{left:90%;}
    }

    .label{
        position:absolute;
        bottom:20px;
        width:100%;
        text-align:center;
        color:white;
        font-size:20px;
    }
    </style>

    <div class="signalbox">
        <div class="axonline"></div>
        <div class="pulse"></div>
        <div class="label">⚡ Electrical signal traveling along axon</div>
    </div>
    """

    components.html(
        signal_html,
        height=230
    )

    voice(
        "An electrical signal can travel along an axon and ultimately influence neurotransmitter release at the axon terminal.",
        key="signal_voice"
    )


# =========================================================
# 5. SYNAPSE EXPLORER
# =========================================================

elif page == "Synapse Explorer":

    st.header("🔗 Synapse Explorer")

    st.write(
        "A simplified view of communication between two neurons."
    )

    synapse_html = """
    <style>
    .synbox{
        height:300px;
        background:#050816;
        border-radius:22px;
        position:relative;
        overflow:hidden;
    }

    .pre{
        position:absolute;
        left:8%;
        top:40%;
        width:32%;
        height:80px;
        border-radius:50%;
        background:#a14cff;
        box-shadow:0 0 35px #a14cff;
    }

    .post{
        position:absolute;
        right:8%;
        top:40%;
        width:32%;
        height:80px;
        border-radius:50%;
        background:#42ddff;
        box-shadow:0 0 35px #42ddff;
    }

    .gap{
        position:absolute;
        left:42%;
        right:42%;
        top:50%;
        height:5px;
        background:white;
    }

    .chemical{
        position:absolute;
        left:43%;
        top:48%;
        width:15px;
        height:15px;
        border-radius:50%;
        background:#ffe66b;
        box-shadow:0 0 15px #ffe66b;
        animation:release 2s infinite;
    }

    @keyframes release{
        from{
            transform:translateX(0);
            opacity:1;
        }
        to{
            transform:translateX(120px);
            opacity:0;
        }
    }
    </style>

    <div class="synbox">
        <div class="pre"></div>
        <div class="gap"></div>
        <div class="post"></div>
        <div class="chemical"></div>
    </div>
    """

    components.html(
        synapse_html,
        height=310
    )

    st.markdown("""
    **Basic sequence:**

    Electrical activity → vesicle release → neurotransmitter → receptor → postsynaptic response
    """)

    voice(
        "At a chemical synapse, neuronal activity can lead to neurotransmitter release. The neurotransmitter crosses the synaptic cleft and interacts with receptors on the next cell.",
        key="synapse_voice"
    )


# =========================================================
# 6. NEUROTRANSMITTER EXPLORER
# =========================================================

elif page == "Neurotransmitter Explorer":

    st.header("🧪 Neurotransmitter Explorer")

    selected_nt = st.selectbox(
        "Select neurotransmitter",
        list(NEUROTRANSMITTERS.keys())
    )

    nt = NEUROTRANSMITTERS[selected_nt]

    st.subheader(selected_nt)

    st.markdown("### Main role")
    st.write(nt["role"])

    st.markdown("### Examples")
    st.write(nt["examples"])

    nt_html = """
    <style>
    .ntbox{
        height:220px;
        background:#050816;
        border-radius:20px;
        position:relative;
        overflow:hidden;
    }

    .particle{
        position:absolute;
        width:18px;
        height:18px;
        border-radius:50%;
        background:#ffe76a;
        box-shadow:
            0 0 10px #ffe76a,
            0 0 30px #ff9d4d;
        animation:float 3s infinite;
    }

    .p1{left:30%;top:50%;}
    .p2{left:45%;top:40%;animation-delay:.5s;}
    .p3{left:60%;top:55%;animation-delay:1s;}
    .p4{left:40%;top:65%;animation-delay:1.5s;}

    @keyframes float{
        0%{
            transform:translate(0,0) scale(.6);
            opacity:0;
        }
        30%{opacity:1;}
        100%{
            transform:translate(120px,-60px) scale(1.2);
            opacity:0;
        }
    }
    </style>

    <div class="ntbox">
        <div class="particle p1"></div>
        <div class="particle p2"></div>
        <div class="particle p3"></div>
        <div class="particle p4"></div>
    </div>
    """

    components.html(
        nt_html,
        height=230
    )

    voice(
        f"{selected_nt}. {nt['role']} {nt['examples']}",
        key=f"nt_voice_{selected_nt}"
    )


# =========================================================
# 7. 3D NEURAL VISUALIZATION
# =========================================================

elif page == "3D Neural Visualization":

    st.header("🧠 3D Neural Visualization")

    if not PLOTLY_OK:

        st.error(
            "Plotly installed nahi hai. requirements.txt check karein."
        )

    else:

        random.seed(7)

        n = 18

        xs = [random.uniform(-5, 5) for _ in range(n)]
        ys = [random.uniform(-5, 5) for _ in range(n)]
        zs = [random.uniform(-5, 5) for _ in range(n)]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers",
                marker=dict(
                    size=7
                ),
                name="Neural nodes"
            )
        )

        for i in range(n - 1):

            fig.add_trace(
                go.Scatter3d(
                    x=[xs[i], xs[i + 1]],
                    y=[ys[i], ys[i + 1]],
                    z=[zs[i], zs[i + 1]],
                    mode="lines",
                    line=dict(
                        width=3
                    ),
                    showlegend=False
                )
            )

        fig.update_layout(
            height=650,
            margin=dict(
                l=0,
                r=0,
                t=30,
                b=0
            ),
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.caption(
            "Educational conceptual neural network visualization — not an anatomical reconstruction."
        )


# =========================================================
# 8. COGNITIVE GAMES
# =========================================================

elif page == "Cognitive Games":

    st.header("🎮 Cognitive Games")

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

    # ---------------- DECISION ----------------

    if game == "Decision":

        st.subheader("⚖️ Decision Challenge")

        st.write(
            "Aap ke paas do options hain. Which one would you choose?"
        )

        option = st.radio(
            "Choose:",
            [
                "Immediate small reward",
                "Larger delayed reward"
            ]
        )

        if st.button("Submit Decision"):

            if option == "Larger delayed reward":
                st.success(
                    "You selected delayed reward. This is often discussed in research on delay discounting and self-control."
                )
            else:
                st.info(
                    "You selected immediate reward. Choice can depend on context, reward value and delay."
                )

            mark_progress("Decision Game")

    # ---------------- MEMORY ----------------

    elif game == "Memory":

        st.subheader("🧠 Memory Challenge")

        numbers = [7, 2, 9, 4, 1]

        st.write("Remember:")
        st.code("  ".join(map(str, numbers)))

        answer = st.number_input(
            "What was the third number?",
            min_value=0,
            max_value=9,
            step=1
        )

        if st.button("Check Memory"):

            if answer == 9:
                st.success("Correct!")
                st.session_state.game_score += 1
            else:
                st.error("Not quite. The third number was 9.")

            mark_progress("Memory Game")

    # ---------------- ATTENTION ----------------

    elif game == "Attention":

        st.subheader("👀 Attention Challenge")

        target = random.choice(
            ["RED", "BLUE", "GREEN"]
        )

        st.write(
            f"Find the target: **{target}**"
        )

        choices = ["RED", "BLUE", "GREEN"]

        selected = st.radio(
            "Choose target",
            choices
        )

        if st.button("Check Attention"):

            if selected == target:
                st.success("Correct target detection!")
                st.session_state.game_score += 1
            else:
                st.error("Try again.")

            mark_progress("Attention Game")

    # ---------------- STROOP ----------------

    elif game == "Stroop":

        st.subheader("🎨 Stroop Challenge")

        word = random.choice(
            ["RED", "BLUE", "GREEN"]
        )

        st.markdown(
            f"<h2>{word}</h2>",
            unsafe_allow_html=True
        )

        selected = st.selectbox(
            "What does the word say?",
            ["RED", "BLUE", "GREEN"]
        )

        if st.button("Submit Stroop"):

            if selected == word:
                st.success("Correct!")
            else:
                st.error("Incorrect.")

            mark_progress("Stroop Game")

    # ---------------- PATTERN ----------------

    else:

        st.subheader("🔢 Pattern Challenge")

        st.write(
            "2 → 4 → 8 → 16 → ?"
        )

        answer = st.number_input(
            "Next number",
            min_value=0,
            step=1
        )

        if st.button("Check Pattern"):

            if answer == 32:
                st.success("Correct!")
                st.session_state.game_score += 1
            else:
                st.error("The answer is 32.")

            mark_progress("Pattern Game")

    st.divider()

    st.metric(
        "Game Score",
        st.session_state.game_score
    )

    st.caption(
        "These games are educational tasks and are not clinical or diagnostic brain tests."
    )


# =========================================================
# 9. BRAIN PICTURE PUZZLE
# =========================================================

elif page == "Brain Picture Puzzle":

    st.header("🧩 Brain Picture Puzzle")

    st.write(
        "Reconstruct the brain by identifying the correct order of image pieces."
    )

    image = get_brain_image()

    if not image:

        st.error("brain.png nahi mili.")

    else:

        level = st.selectbox(
            "Difficulty",
            [
                "Easy — 3 × 3",
                "Medium — 4 × 4",
                "Hard — 5 × 5"
            ]
        )

        if level.startswith("Easy"):
            grid = 3
        elif level.startswith("Medium"):
            grid = 4
        else:
            grid = 5

        pieces = []

        width, height = image.size

        piece_w = width // grid
        piece_h = height // grid

        for row in range(grid):

            for col in range(grid):

                left = col * piece_w
                upper = row * piece_h
                right = (
                    (col + 1) * piece_w
                    if col < grid - 1
                    else width
                )
                lower = (
                    (row + 1) * piece_h
                    if row < grid - 1
                    else height
                )

                pieces.append(
                    image.crop(
                        (left, upper, right, lower)
                    )
                )

        order = list(range(len(pieces)))

        random.shuffle(order)

        st.write(
            "Pieces shuffled. Identify their original positions."
        )

        cols = st.columns(grid)

        for i, piece_index in enumerate(order):

            with cols[i % grid]:

                st.image(
                    pieces[piece_index],
                    use_container_width=True
                )

                st.caption(
                    f"Piece {piece_index + 1}"
                )

        answer = st.text_input(
            f"Enter original order of {grid * grid} pieces, e.g. 1,2,3..."
        )

        if st.button("Check Puzzle"):

            try:

                entered = [
                    int(x.strip())
                    for x in answer.split(",")
                ]

                correct = list(
                    range(1, grid * grid + 1)
                )

                if entered == correct:
                    st.success(
                        "🎉 Perfect! Brain reconstructed."
                    )
                    mark_progress(
                        f"Brain Puzzle {grid}x{grid}"
                    )
                else:
                    st.error(
                        "Order correct nahi hai. Dobara try karein."
                    )

            except Exception:
                st.error(
                    "Numbers comma se enter karein."
                )

        st.info(
            "Note: Ye current version image-order puzzle hai. True drag-and-drop jigsaw ke liye custom interactive component required hota hai."
        )


# =========================================================
# 10. COGNITIVE SELF REPORT
# =========================================================

elif page == "Cognitive Self-Report":

    st.header("📊 Cognitive Self-Report")

    st.write(
        "Ye self-reflection tool hai, clinical assessment nahi."
    )

    focus = st.slider(
        "Aaj focus kaisa tha?",
        1,
        10,
        5
    )

    memory = st.slider(
        "Aaj memory/recall kaisa laga?",
        1,
        10,
        5
    )

    stress = st.slider(
        "Aaj perceived stress kitna tha?",
        1,
        10,
        5
    )

    sleep = st.slider(
        "Sleep quality kaisi thi?",
        1,
        10,
        5
    )

    motivation = st.slider(
        "Motivation level?",
        1,
        10,
        5
    )

    if st.button("Save Reflection"):

        mark_progress("Self Report")

        st.success(
            "Reflection saved for this session."
        )

        st.write(
            {
                "Focus": focus,
                "Memory": memory,
                "Stress": stress,
                "Sleep": sleep,
                "Motivation": motivation
            }
        )

    st.caption(
        "Self-report scores subjective hain aur diagnosis nahi dete."
    )


# =========================================================
# 11. ASK AYNA
# =========================================================

elif page == "Ask Ayna":

    st.header("💬 Ask Ayna")

    st.write(
        "Ask questions about cognition, neuroscience, behavior, AI and the brain."
    )

    for message in st.session_state.ask_messages:

        if message["role"] == "user":
            st.markdown(
                f"**You:** {message['content']}"
            )

        else:
            st.markdown(
                f"**Ayna:** {message['content']}"
            )

    question = st.text_area(
        "Your question",
        placeholder="e.g. Why does stress affect attention?"
    )

    if st.button("Ask Ayna", type="primary"):

        if question.strip():

            answer = ask_ayna(question)

            st.session_state.ask_messages.append(
                {
                    "role": "user",
                    "content": question
                }
            )

            st.session_state.ask_messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            mark_progress("Ask Ayna")

            st.rerun()

    if st.session_state.ask_messages:

        last_answer = None

        for m in reversed(
            st.session_state.ask_messages
        ):
            if m["role"] == "assistant":
                last_answer = m["content"]
                break

        if last_answer:
            voice(
                last_answer,
                key="ask_ayna_voice"
            )

    if st.button("🗑️ Clear Chat"):

        st.session_state.ask_messages = []

        st.rerun()


# =========================================================
# 12. LEARNING PROGRESS
# =========================================================

elif page == "Learning Progress":

    st.header("📈 Learning Progress")

    completed = len(
        st.session_state.progress
    )

    total = 13

    percentage = min(
        100,
        int((completed / total) * 100)
    )

    st.progress(
        percentage / 100
    )

    st.metric(
        "Progress",
        f"{percentage}%"
    )

    st.markdown("### Completed")

    if st.session_state.progress:

        for item in sorted(
            st.session_state.progress
        ):
            st.write(
                f"✅ {item}"
            )

    else:

        st.info(
            "Abhi learning activities complete nahi hui."
        )


# =========================================================
# 13. SCIENCE NOTES
# =========================================================

elif page == "Science Notes":

    st.header("📚 Science Notes")

    notes = {
        "Cognitive Control":
            "Cognitive control involves processes that help regulate thoughts and actions according to goals.",

        "Memory":
            "Memory is not one single system. Different forms of memory involve partially overlapping neural networks.",

        "Attention":
            "Attention helps prioritize selected information while reducing processing of competing information.",

        "Reward":
            "Reward-related learning involves interactions among several brain systems, including cortico-striatal networks.",

        "Neuroplasticity":
            "Neuroplasticity refers to changes in neural structure or function associated with experience, learning or other processes.",

        "Synaptic Communication":
            "Neurons communicate through electrical and chemical mechanisms, including neurotransmitter signaling at many synapses."
    }

    for title, text in notes.items():

        with st.expander(title):

            st.write(text)

            voice(
                f"{title}. {text}",
                key=f"science_voice_{title}"
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NEUROLENS — Educational cognitive neuroscience platform"
)

st.caption(
    "Created by Ayna Jaffri • Brain × Behavior × AI"
)
