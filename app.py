import os
import random
import base64
import html
import streamlit as st
from PIL import Image

try:
    from google import genai
except Exception:
    genai = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
)

# ============================================================
# DATA
# ============================================================

BRAIN_PARTS = {
    "Prefrontal Cortex": {
        "description": (
            "Supports planning, cognitive control, working memory, "
            "decision-making and flexible behavior."
        ),
        "behavior": (
            "Planning, inhibition, goal-directed decisions and "
            "complex problem solving."
        ),
        "focus": "front",
    },

    "Hippocampus": {
        "description": (
            "A key structure for forming and retrieving many types "
            "of memories and supporting spatial representation."
        ),
        "behavior": "Learning, memory formation and navigation.",
        "focus": "temporal",
    },

    "Amygdala": {
        "description": (
            "Participates in processing emotionally significant "
            "information, including threat and reward-related cues."
        ),
        "behavior": (
            "Emotional learning, salience and responses to "
            "threat-related information."
        ),
        "focus": "amygdala",
    },

    "Striatum": {
        "description": (
            "Part of the basal ganglia and involved in action "
            "selection, reward learning and habit-related processes."
        ),
        "behavior": "Reward learning, action selection and habits.",
        "focus": "striatum",
    },

    "Anterior Cingulate Cortex": {
        "description": (
            "Contributes to monitoring, cognitive control, "
            "motivation and processing of conflict or errors."
        ),
        "behavior": "Conflict monitoring, effort and adaptive control.",
        "focus": "acc",
    },

    "Cerebellum": {
        "description": (
            "Coordinates movement and also contributes to timing, "
            "prediction and some cognitive processes."
        ),
        "behavior": "Motor coordination, timing and prediction.",
        "focus": "cerebellum",
    },
}


NEUROTRANSMITTERS = {
    "Dopamine": (
        "Participates in reward learning, motivation, movement "
        "and several cognitive processes."
    ),

    "Serotonin": (
        "Participates in mood regulation, sleep, appetite and "
        "many physiological and cognitive processes."
    ),

    "GABA": (
        "The major inhibitory neurotransmitter in the "
        "central nervous system."
    ),

    "Glutamate": (
        "The major excitatory neurotransmitter in the central "
        "nervous system and important for learning."
    ),

    "Acetylcholine": (
        "Contributes to attention, learning, memory and "
        "neuromuscular communication."
    ),
}


JOURNEY = [
    ("brain", "Whole Brain"),
    ("region", "Brain Region"),
    ("neuron", "Neuron"),
    ("axon", "Axon + Myelin"),
    ("synapse", "Synapse"),
    ("nt", "Neurotransmitter"),
]


# ============================================================
# SESSION STATE
# ============================================================

if "journey_stage" not in st.session_state:
    st.session_state.journey_stage = 0

if "selected_region" not in st.session_state:
    st.session_state.selected_region = "Prefrontal Cortex"

if "progress" not in st.session_state:
    st.session_state.progress = set()

if "ayna_messages" not in st.session_state:
    st.session_state.ayna_messages = []


# ============================================================
# HELPERS
# ============================================================

def get_gemini_api_key():

    for name in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:

        try:
            key = st.secrets.get(name)

            if key:
                return str(key).strip()

        except Exception:
            pass

        key = os.getenv(name)

        if key:
            return key.strip()

    return None


def ask_ayna(question, context=""):

    if genai is None:
        return (
            "⚠️ Gemini package is not installed. "
            "Check requirements.txt."
        )

    api_key = get_gemini_api_key()

    if not api_key:
        return (
            "⚠️ GEMINI_API_KEY nahi mili. "
            "Streamlit Secrets mein add karo."
        )

    prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience
assistant inside NEUROLENS.

Explain neuroscience clearly and accurately.

Rules:
1. Do not diagnose.
2. Do not claim simple games measure brain activity.
3. Do not present self-report ratings as clinical measurements.
4. Distinguish established evidence from hypotheses.
5. Use simple but scientifically accurate language.
6. If medical diagnosis is requested, recommend a qualified professional.

Current context:
{context}

User question:
{question}
"""

    try:

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        answer = getattr(response, "text", None)

        if answer:
            return answer.strip()

        return "⚠️ Ask Ayna received an empty response."

    except Exception as e:

        return (
            "⚠️ Ask Ayna could not connect to Gemini.\n\n"
            f"Error: `{type(e).__name__}`\n\n"
            f"Details: `{str(e)}`"
        )


def voice_button(text, key):

    safe_text = html.escape(
        text.replace("\n", " ")
    )

    code = f"""
    <button
        onclick="speakText()"
        style="
            border:0;
            border-radius:12px;
            padding:10px 18px;
            background:#111827;
            color:white;
            cursor:pointer;
            font-size:15px;
        "
    >
        🔊 Voice
    </button>

    <script>

    function speakText() {{

        window.speechSynthesis.cancel();

        const text = "{safe_text}";

        const speech =
            new SpeechSynthesisUtterance(text);

        speech.rate = 0.95;
        speech.pitch = 1;

        window.speechSynthesis.speak(speech);
    }}

    </script>
    """

    st.components.v1.html(
        code,
        height=55,
    )


def brain_path():

    return os.path.join(
        os.path.dirname(__file__),
        "brain.png",
    )


def brain_base64():

    path = brain_path()

    if not os.path.exists(path):
        return None

    with open(path, "rb") as file:
        return base64.b64encode(
            file.read()
        ).decode("utf-8")


def mark_progress():

    key = JOURNEY[
        st.session_state.journey_stage
    ][0]

    st.session_state.progress.add(key)


# ============================================================
# HEADER
# ============================================================

st.title("🧠 NEUROLENS")

st.caption(
    "Explore cognition, behavior & the brain • "
    "Created by Ayna Jaffri"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🧭 NEUROLENS")

    page = st.radio(
        "Explore",
        [
            "🧠 Brain Explorer",
            "🎬 Neural Journey",
            "🧬 Neuron Explorer",
            "🧪 Neurotransmitter Explorer",
            "🎮 Cognitive Games",
            "🧩 Brain Puzzle",
            "📊 Cognitive Self-Report",
            "📈 3D Neural Visualization",
            "🤖 Ask Ayna",
            "📚 Science Notes",
        ],
    )

    st.divider()

    st.subheader("🏆 Learning Progress")

    progress_value = (
        len(st.session_state.progress)
        / len(JOURNEY)
    )

    st.progress(
        min(progress_value, 1.0)
    )

    st.caption(
        f"{len(st.session_state.progress)} / "
        f"{len(JOURNEY)} stages explored"
    )


# ============================================================
# BRAIN EXPLORER
# ============================================================

if page == "🧠 Brain Explorer":

    st.header("🧠 Interactive Brain Explorer")

    st.write(
        "Select a brain region to explore its "
        "function and behavioral relevance."
    )

    names = list(BRAIN_PARTS.keys())

    columns = st.columns(3)

    for i, name in enumerate(names):

        with columns[i % 3]:

            if st.button(
                name,
                key=f"region_button_{i}",
                use_container_width=True,
            ):

                st.session_state.selected_region = name

    region = st.session_state.selected_region

    information = BRAIN_PARTS[region]

    st.divider()

    left, right = st.columns(
        [1.2, 1]
    )

    with left:

        if os.path.exists(brain_path()):

            st.image(
                brain_path(),
                use_container_width=True,
            )

        else:

            st.error(
                "brain.png nahi mil rahi. "
                "brain.png ko app.py ke same folder mein rakho."
            )

    with right:

        st.subheader(
            f"🔎 {region}"
        )

        st.write(
            information["description"]
        )

        st.markdown(
            "**Behavioral relevance**"
        )

        st.info(
            information["behavior"]
        )

        voice_button(
            (
                region
                + ". "
                + information["description"]
                + " "
                + information["behavior"]
            ),
            "brain_voice",
        )

        if st.button(
            "🎬 Explore in Neural Journey",
            use_container_width=True,
        ):

            st.session_state.selected_region = region

            st.session_state.journey_stage = 1

            st.session_state.progress.add(
                "brain"
            )

            st.rerun()


# ============================================================
# CINEMATIC NEURAL JOURNEY
# ============================================================

elif page == "🎬 Neural Journey":

    st.header("🎬 Cinematic Neural Journey")

    st.write(
        "Brain se andar travel karo: "
        "Region → Neuron → Axon → Synapse → Neurotransmitter."
    )

    region = st.selectbox(
        "Starting brain region",
        list(BRAIN_PARTS.keys()),
        index=list(BRAIN_PARTS.keys()).index(
            st.session_state.selected_region
        ),
    )

    st.session_state.selected_region = region

    mark_progress()

    stage_index = (
        st.session_state.journey_stage
    )

    stage_key, stage_name = JOURNEY[
        stage_index
    ]

    image_data = brain_base64()

    if image_data:

        focus_points = {

            "front": (42, 43),

            "temporal": (58, 66),

            "amygdala": (57, 57),

            "striatum": (52, 51),

            "acc": (48, 48),

            "cerebellum": (77, 70),
        }

        focus = BRAIN_PARTS[
            region
        ]["focus"]

        fx, fy = focus_points[
            focus
        ]

        zoom_values = [
            1.0,
            1.8,
            2.6,
            3.5,
            4.4,
            5.1,
        ]

        zoom = zoom_values[
            stage_index
        ]

        translate_x = (
            50 - fx * zoom
        )

        translate_y = (
            50 - fy * zoom
        )

        neuron_visible = (
            stage_index >= 2
        )

        axon_visible = (
            stage_index >= 3
        )

        synapse_visible = (
            stage_index >= 4
        )

        chemical_visible = (
            stage_index >= 5
        )

        animation_html = f"""

        <div class="journey">

            <div class="journey-title">
                LIVE NEURAL JOURNEY
                • {html.escape(stage_name)}
            </div>


            <div
                class="brain-world"
                style="
                    transform:
                    translate(
                        {translate_x:.1f}%,
                        {translate_y:.1f}%
                    )
                    scale({zoom:.2f});
                "
            >

                <img
                    src="data:image/png;base64,{image_data}"
                    class="brain-image"
                >

                <div
                    class="route"
                    style="
                        left:{fx}%;
                        top:{fy}%;
                    "
                ></div>

                <div
                    class="pulse"
                    style="
                        left:{fx}%;
                        top:{fy}%;
                    "
                ></div>

            </div>


            <div
                class="neuron
                {'visible' if neuron_visible else ''}"
            >

                <div class="soma"></div>

                <div class="dendrite d1"></div>

                <div class="dendrite d2"></div>

                <div class="dendrite d3"></div>

                <div class="axon"></div>

                <div class="myelin m1"></div>

                <div class="myelin m2"></div>

                <div class="myelin m3"></div>

                <div class="signal"></div>

            </div>


            <div
                class="synapse
                {'visible' if synapse_visible else ''}"
            >

                <div class="terminal"></div>

                <div class="cleft"></div>

                <div class="receptor r1"></div>

                <div class="receptor r2"></div>

                <div class="receptor r3"></div>

                <div class="particle p1"></div>

                <div class="particle p2"></div>

                <div class="particle p3"></div>

                <div class="particle p4"></div>

                <div class="particle p5"></div>

            </div>


            <div
                class="chemical
                {'visible' if chemical_visible else ''}"
            >

                <span>DOPAMINE</span>

                <span>SEROTONIN</span>

                <span>GABA</span>

                <span>GLUTAMATE</span>

                <span>ACETYLCHOLINE</span>

            </div>


            <div
                class="signal-label
                {'visible' if axon_visible else ''}"
            >

                ⚡ Signal travelling through axon

            </div>

        </div>


        <style>

        .journey {{
            position:relative;
            height:570px;
            overflow:hidden;
            border-radius:28px;
            background:
                radial-gradient(
                    circle at center,
                    #172554,
                    #020617 72%
                );
            box-shadow:
                0 20px 60px
                rgba(0,0,0,.35);
        }}


        .journey-title {{
            position:absolute;
            z-index:20;
            top:18px;
            left:20px;
            color:white;
            background:
                rgba(0,0,0,.4);
            padding:10px 14px;
            border-radius:12px;
            font:
                700 12px Arial;
            letter-spacing:1.3px;
        }}


        .brain-world {{
            position:absolute;
            width:100%;
            height:100%;
            transform-origin:
                {fx}% {fy}%;
            transition:
                transform
                2.8s
                cubic-bezier(
                    .16,.75,.18,1
                );
        }}


        .brain-image {{
            position:absolute;
            width:72%;
            left:14%;
            top:13%;
            filter:
                drop-shadow(
                    0 25px 35px
                    rgba(0,0,0,.4)
                );
        }}


        .route {{
            position:absolute;
            width:7px;
            height:270px;
            border-radius:20px;
            background:
                linear-gradient(
                    #ffffff,
                    #38bdf8,
                    #a78bfa
                );
            box-shadow:
                0 0 20px #38bdf8;
            transform:
                rotate(28deg);
            transform-origin:
                top;
            animation:
                routeOpen
                2.4s
                ease-out;
        }}


        .pulse {{
            position:absolute;
            width:28px;
            height:28px;
            border-radius:50%;
            background:white;
            box-shadow:
                0 0 15px white,
                0 0 45px #38bdf8;
            transform:
                translate(-50%,-50%);
            animation:
                pulse
                1.8s
                ease-in-out
                infinite;
        }}


        .neuron {{
            position:absolute;
            left:50%;
            top:52%;
            width:340px;
            height:240px;
            transform:
                translate(-50%,-50%)
                scale(.15);
            opacity:0;
            transition:
                2s ease;
        }}


        .neuron.visible {{
            opacity:1;
            transform:
                translate(-50%,-50%)
                scale(1);
        }}


        .soma {{
            position:absolute;
            left:125px;
            top:80px;
            width:80px;
            height:80px;
            border-radius:50%;
            background:
                radial-gradient(
                    circle,
                    #fde68a,
                    #f59e0b
                );
            box-shadow:
                0 0 40px #fbbf24;
        }}


        .dendrite {{
            position:absolute;
            height:8px;
            width:130px;
            border-radius:20px;
            background:#f59e0b;
        }}


        .d1 {{
            left:5px;
            top:70px;
            transform:rotate(-25deg);
        }}


        .d2 {{
            left:0;
            top:135px;
            transform:rotate(18deg);
        }}


        .d3 {{
            left:45px;
            top:40px;
            transform:rotate(-48deg);
        }}


        .axon {{
            position:absolute;
            left:200px;
            top:114px;
            width:180px;
            height:12px;
            border-radius:20px;
            background:#c4b5fd;
            box-shadow:
                0 0 18px #a78bfa;
        }}


        .myelin {{
            position:absolute;
            top:103px;
            width:38px;
            height:34px;
            border-radius:18px;
            background:#e0e7ff;
            box-shadow:
                0 0 12px white;
        }}


        .m1 {{left:220px}}

        .m2 {{left:270px}}

        .m3 {{left:320px}}


        .signal {{
            position:absolute;
            left:200px;
            top:109px;
            width:22px;
            height:22px;
            border-radius:50%;
            background:white;
            box-shadow:
                0 0 18px white,
                0 0 40px #22d3ee;
            animation:
                signalMove
                1.6s
                linear
                infinite;
        }}


        .synapse {{
            position:absolute;
            left:50%;
            top:52%;
            width:430px;
            height:240px;
            transform:
                translate(-50%,-50%)
                scale(.15);
            opacity:0;
            transition:2s ease;
        }}


        .synapse.visible {{
            opacity:1;
            transform:
                translate(-50%,-50%)
                scale(1);
        }}


        .terminal {{
            position:absolute;
            left:40px;
            top:55px;
            width:145px;
            height:125px;
            border-radius:
                70px 20px 20px 70px;
            background:#f97316;
            box-shadow:
                0 0 35px #fb923c;
        }}


        .cleft {{
            position:absolute;
            left:200px;
            top:60px;
            height:115px;
            border-left:
                3px dashed white;
        }}


        .receptor {{
            position:absolute;
            right:45px;
            width:48px;
            height:18px;
            border-radius:20px;
            background:#67e8f9;
            box-shadow:
                0 0 18px #22d3ee;
        }}


        .r1 {{top:55px}}

        .r2 {{top:100px}}

        .r3 {{top:145px}}


        .particle {{
            position:absolute;
            width:13px;
            height:13px;
            border-radius:50%;
            background:#fef08a;
            box-shadow:
                0 0 16px #fef08a;
            animation:
                particleMove
                1.7s
                linear
                infinite;
        }}


        .p1 {{left:155px;top:70px}}

        .p2 {{left:150px;top:105px;animation-delay:.3s}}

        .p3 {{left:160px;top:140px;animation-delay:.6s}}

        .p4 {{left:165px;top:85px;animation-delay:.9s}}

        .p5 {{left:160px;top:125px;animation-delay:1.2s}}


        .chemical {{
            position:absolute;
            left:50%;
            bottom:38px;
            width:90%;
            transform:
                translateX(-50%);
            display:flex;
            justify-content:center;
            flex-wrap:wrap;
            gap:9px;
            opacity:0;
            transition:1.5s;
        }}


        .chemical.visible {{
            opacity:1;
        }}


        .chemical span {{
            color:white;
            background:
                rgba(255,255,255,.12);
            border:
                1px solid
                rgba(255,255,255,.25);
            padding:
                9px 12px;
            border-radius:999px;
            font:
                600 11px Arial;
            backdrop-filter:
                blur(8px);
        }}


        .signal-label {{
            position:absolute;
            left:50%;
            bottom:90px;
            transform:
                translateX(-50%);
            color:white;
            background:
                rgba(0,0,0,.45);
            padding:
                10px 14px;
            border-radius:12px;
            opacity:0;
            transition:1s;
            font:
                600 13px Arial;
        }}


        .signal-label.visible {{
            opacity:1;
        }}


        @keyframes pulse {{

            0%,100% {{
                transform:
                    translate(-50%,-50%)
                    scale(.8);
            }}

            50% {{
                transform:
                    translate(-50%,-50%)
                    scale(1.35);
            }}

        }}


        @keyframes routeOpen {{

            from {{
                height:0;
                opacity:0;
            }}

            to {{
                height:270px;
                opacity:.9;
            }}

        }}


        @keyframes signalMove {{

            from {{
                left:200px;
            }}

            to {{
                left:360px;
            }}

        }}


        @keyframes particleMove {{

            from {{
                transform:
                    translateX(0)
                    scale(.7);
            }}

            to {{
                transform:
                    translateX(105px)
                    scale(1);
            }}

        }}

        </style>
        """

        st.components.v1.html(
            animation_html,
            height=590,
        )

    else:

        st.error(
            "brain.png missing hai."
        )


    # ========================================================
    # JOURNEY MAP
    # ========================================================

    st.subheader("🗺️ Neural Route")

    map_columns = st.columns(
        len(JOURNEY)
    )

    for i, (_, label) in enumerate(JOURNEY):

        with map_columns[i]:

            if (
                i
                == st.session_state.journey_stage
            ):

                st.success(
                    f"● {label}"
                )

            else:

                st.caption(label)


    descriptions = {

        0:
        f"Whole brain view. Starting point for exploring {region}.",

        1:
        f"{region}: {BRAIN_PARTS[region]['description']}",

        2:
        "Neuron level: the cell receives, integrates and communicates signals.",

        3:
        "Axon level: electrical activity can travel along the axon.",

        4:
        "Synapse level: neurons communicate across a specialized junction.",

        5:
        "Chemical level: neurotransmitters participate in neural communication.",
    }


    current_description = descriptions[
        st.session_state.journey_stage
    ]

    st.info(
        current_description
    )

    voice_button(
        current_description,
        "journey_voice",
    )


    # ========================================================
    # NAVIGATION
    # ========================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "⬅️ Back",
            disabled=(
                st.session_state.journey_stage
                == 0
            ),
            use_container_width=True,
        ):

            st.session_state.journey_stage -= 1

            st.rerun()


    with c2:

        if st.button(
            "➡️ Travel deeper",
            disabled=(
                st.session_state.journey_stage
                == len(JOURNEY) - 1
            ),
            use_container_width=True,
        ):

            st.session_state.journey_stage += 1

            mark_progress()

            st.rerun()


    with c3:

        if st.button(
            "🔄 Start Again",
            use_container_width=True,
        ):

            st.session_state.journey_stage = 0

            st.rerun()


    # ========================================================
    # ASK AYNA CONTEXT
    # ========================================================

    st.divider()

    st.subheader(
        "🤖 Ask Ayna about this point"
    )

    question = st.text_input(
        "Question",
        placeholder=(
            f"Ask about {stage_name.lower()}..."
        ),
        key="journey_question",
    )

    if st.button(
        "Ask Ayna",
        key="journey_ask",
    ):

        if question:

            context = f"""
Region: {region}
Journey stage: {stage_name}
Description: {current_description}
"""

            st.write(
                ask_ayna(
                    question,
                    context,
                )
            )


# ============================================================
# NEURON EXPLORER
# ============================================================

elif page == "🧬 Neuron Explorer":

    st.header(
        "🧬 Neuron Explorer"
    )

    st.write(
        "Explore the major parts of a neuron."
    )

    neuron_parts = {

        "Dendrites":
        "Receive many incoming signals from other cells.",

        "Soma":
        "Contains the cell nucleus and integrates cellular information.",

        "Axon":
        "Carries electrical signals away from the cell body.",

        "Myelin":
        "Insulating material around many axons that supports efficient signal conduction.",

        "Axon Terminal":
        "The terminal region where signals can influence communication.",

        "Synapse":
        "A specialized junction where one neuron communicates with another cell.",
    }


    selected = st.radio(
        "Select neuron part",
        list(neuron_parts.keys()),
        horizontal=True,
    )

    st.subheader(
        f"🔬 {selected}"
    )

    st.info(
        neuron_parts[selected]
    )

    voice_button(
        f"{selected}. {neuron_parts[selected]}",
        "neuron_voice",
    )


# ============================================================
# NEUROTRANSMITTER EXPLORER
# ============================================================

elif page == "🧪 Neurotransmitter Explorer":

    st.header(
        "🧪 Neurotransmitter Explorer"
    )

    nt = st.selectbox(
        "Choose a neurotransmitter",
        list(NEUROTRANSMITTERS.keys()),
    )

    st.subheader(
        f"🧪 {nt}"
    )

    st.info(
        NEUROTRANSMITTERS[nt]
    )

    voice_button(
        f"{nt}. {NEUROTRANSMITTERS[nt]}",
        "nt_voice",
    )

    st.markdown(
        "### ⚡ Chemical Signal"
    )

    st.markdown(
        """
        <div style="
            position:relative;
            height:130px;
            border-radius:25px;
            overflow:hidden;
            background:
            linear-gradient(
                90deg,
                #eef2ff,
                #ecfeff
            );
        ">

        <div style="
            position:absolute;
            top:50%;
            width:24px;
            height:24px;
            border-radius:50%;
            background:#7c3aed;
            box-shadow:
            0 0 25px #7c3aed;
            animation:
            chemicalMove
            2.3s
            linear
            infinite;
        "></div>

        </div>

        <style>

        @keyframes chemicalMove {

            from {
                left:-5%;
            }

            to {
                left:105%;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# COGNITIVE GAMES
# ============================================================

elif page == "🎮 Cognitive Games":

    st.header(
        "🎮 Cognitive Games"
    )

    game = st.selectbox(
        "Choose a game",
        [
            "Decision Challenge",
            "Memory Challenge",
            "Attention Challenge",
            "Stroop Challenge",
            "Pattern Challenge",
        ],
    )


    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

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
        )

        if st.button(
            "Analyze Decision"
        ):

            if choice == "Rs. 1,000 today":

                st.success(
                    "Immediate-reward preference in this task."
                )

            else:

                st.success(
                    "Delayed-reward preference in this task."
                )

            st.info(
                "Educational task only."
            )


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    elif game == "Memory Challenge":

        st.subheader(
            "🧠 Memory Challenge"
        )

        sequence = (
            "7 2 9 4 1 8"
        )

        st.write(
            "Remember:"
        )

        st.markdown(
            f"## **{sequence}**"
        )

        answer = st.text_input(
            "Enter the sequence"
        )

        if st.button(
            "Check Memory"
        ):

            if (
                answer.replace(
                    " ",
                    "",
                )
                == "729418"
            ):

                st.success(
                    "🎉 Correct!"
                )

            else:

                st.error(
                    "Not quite. Try again."
                )


    # --------------------------------------------------------
    # ATTENTION
    # --------------------------------------------------------

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
        )

        if st.button(
            "Check Attention"
        ):

            if "X" in target:

                st.success(
                    "🎯 Correct!"
                )

            else:

                st.error(
                    "Try again!"
                )

            st.info(
                "This explores visual search and attention."
            )


    # --------------------------------------------------------
    # STROOP
    # --------------------------------------------------------

    elif game == "Stroop Challenge":

        st.subheader(
            "🎨 Stroop Challenge"
        )

        colors = [
            "RED",
            "BLUE",
            "GREEN",
            "YELLOW",
        ]

        if "stroop_word" not in st.session_state:

            st.session_state.stroop_word = (
                random.choice(colors)
            )

            st.session_state.stroop_color = (
                random.choice(colors)
            )

        if st.button(
            "🔄 New Trial"
        ):

            st.session_state.stroop_word = (
                random.choice(colors)
            )

            st.session_state.stroop_color = (
                random.choice(colors)
            )

            st.rerun()

        st.markdown(
            f"# {st.session_state.stroop_word}"
        )

        answer = st.selectbox(
            "What is the ink color?",
            colors,
        )

        if st.button(
            "Check Stroop"
        ):

            if (
                answer
                == st.session_state.stroop_color
            ):

                st.success(
                    "Correct!"
                )

            else:

                st.error(
                    "Not correct."
                )

            st.info(
                "The Stroop effect illustrates interference."
            )


    # --------------------------------------------------------
    # PATTERN
    # --------------------------------------------------------

    else:

        st.subheader(
            "🔢 Pattern Challenge"
        )

        st.markdown(
            "### 2 → 4 → 8 → 16 → ?"
        )

        answer = st.number_input(
            "Your answer",
            min_value=0,
            step=1,
        )

        if st.button(
            "Check Pattern"
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

elif page == "📊 Cognitive Self-Report":

    st.header(
        "📊 Cognitive Self-Report"
    )

    st.write(
        "Rate your current subjective state."
    )

    focus = st.slider(
        "Focus",
        1,
        10,
        5,
    )

    stress = st.slider(
        "Stress",
        1,
        10,
        5,
    )

    energy = st.slider(
        "Mental Energy",
        1,
        10,
        5,
    )

    st.divider()

    st.metric(
        "Focus",
        f"{focus}/10",
    )

    st.metric(
        "Stress",
        f"{stress}/10",
    )

    st.metric(
        "Mental Energy",
        f"{energy}/10",
    )

    st.warning(
        "Self-report ratings are subjective and are "
        "not clinical measurements or direct measurements "
        "of brain activity."
    )


# ============================================================
# BRAIN PUZZLE
# ============================================================

elif page == "🧩 Brain Puzzle":

    st.header(
        "🧩 Brain Picture Puzzle"
    )

    st.write(
        "Reconstruct the whole brain by identifying "
        "the correct tile order."
    )

    level = st.selectbox(
        "Difficulty",
        [
            "Easy • 3×3",
            "Medium • 4×4",
            "Hard • 5×5",
        ],
    )

    n = int(
        level.split("×")[1]
    )

    if os.path.exists(
        brain_path()
    ):

        image = Image.open(
            brain_path()
        ).convert("RGB")

        width, height = image.size

        pieces = []

        for row in range(n):

            for col in range(n):

                box = (
                    col * width // n,
                    row * height // n,
                    (col + 1) * width // n,
                    (row + 1) * height // n,
                )

                pieces.append(
                    image.crop(box)
                )

        total = n * n

        state_key = (
            f"puzzle_order_{n}"
        )

        if state_key not in st.session_state:

            order = list(
                range(total)
            )

            random.shuffle(order)

            st.session_state[
                state_key
            ] = order

        if st.button(
            "🔀 New Puzzle"
        ):

            order = list(
                range(total)
            )

            random.shuffle(order)

            st.session_state[
                state_key
            ] = order

            st.rerun()

        order = st.session_state[
            state_key
        ]

        index = 0

        for row in range(n):

            columns = st.columns(n)

            for col in range(n):

                with columns[col]:

                    st.image(
                        pieces[
                            order[index]
                        ],
                        use_container_width=True,
                    )

                    st.caption(
                        f"Tile {order[index] + 1}"
                    )

                index += 1

        answer = st.text_input(
            f"Correct order 1–{total}",
        )

        if st.button(
            "✅ Check Puzzle"
        ):

            try:

                numbers = [
                    int(x)
                    for x in answer.split()
                ]

                if numbers == list(
                    range(
                        1,
                        total + 1,
                    )
                ):

                    st.success(
                        "🎉 Brain puzzle solved!"
                    )

                    st.balloons()

                    st.session_state.progress.add(
                        "brain"
                    )

                else:

                    st.error(
                        "Not correct yet."
                    )

            except ValueError:

                st.error(
                    "Numbers ko spaces se separate karo."
                )

    else:

        st.error(
            "brain.png missing hai."
        )


# ============================================================
# 3D NEURAL VISUALIZATION
# ============================================================

elif page == "📈 3D Neural Visualization":

    st.header(
        "📈 3D Neural Visualization"
    )

    st.write(
        "Interactive conceptual neural network."
    )

    if go is None:

        st.error(
            "Plotly installed nahi hai."
        )

    else:

        random.seed(7)

        number_nodes = 28

        x = [
            random.uniform(-3, 3)
            for _ in range(number_nodes)
        ]

        y = [
            random.uniform(-3, 3)
            for _ in range(number_nodes)
        ]

        z = [
            random.uniform(-3, 3)
            for _ in range(number_nodes)
        ]

        figure = go.Figure()

        for i in range(
            number_nodes
        ):

            for j in range(
                i + 1,
                number_nodes,
            ):

                distance = (
                    (x[i] - x[j]) ** 2
                    + (y[i] - y[j]) ** 2
                    + (z[i] - z[j]) ** 2
                )

                if distance < 2.4:

                    figure.add_trace(
                        go.Scatter3d(
                            x=[
                                x[i],
                                x[j],
                            ],
                            y=[
                                y[i],
                                y[j],
                            ],
                            z=[
                                z[i],
                                z[j],
                            ],
                            mode="lines",
                            line=dict(
                                width=2
                            ),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )

        figure.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="markers",
                marker=dict(
                    size=6
                ),
                text=[
                    f"Neural node {i+1}"
                    for i in range(
                        number_nodes
                    )
                ],
                hovertemplate=(
                    "%{text}<extra></extra>"
                ),
                name="Neural nodes",
            )
        )

        figure.update_layout(
            height=620,
            margin=dict(
                l=0,
                r=0,
                t=20,
                b=0,
            ),
            scene=dict(
                xaxis=dict(
                    showticklabels=False,
                    title="",
                ),
                yaxis=dict(
                    showticklabels=False,
                    title="",
                ),
                zaxis=dict(
                    showticklabels=False,
                    title="",
                ),
            ),
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )

        st.caption(
            "Conceptual visualization — "
            "not an anatomical reconstruction of the human brain."
        )


# ============================================================
# ASK AYNA
# ============================================================

elif page == "🤖 Ask Ayna":

    st.header(
        "🤖 Ask Ayna 🧠"
    )

    st.write(
        "Ask about cognition, behavior, "
        "brain systems, neurons, synapses "
        "and neuroscience."
    )

    for message in (
        st.session_state
        .ayna_messages
    ):

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

        with st.chat_message(
            "user"
        ):

            st.markdown(
                question
            )

        with st.chat_message(
            "assistant"
        ):

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

    if st.session_state.ayna_messages:

        if st.button(
            "🗑️ Clear Ask Ayna Chat"
        ):

            st.session_state.ayna_messages = []

            st.rerun()


# ============================================================
# SCIENCE NOTES
# ============================================================

elif page == "📚 Science Notes":

    st.header(
        "📚 Science Notes"
    )

    notes = {

        "CSTC Circuit":
        (
            "Cortico-striato-thalamo-cortical circuits "
            "link cortical and subcortical systems and "
            "are relevant to cognitive control, action "
            "selection and learning."
        ),

        "Memory":
        (
            "Memory involves multiple processes including "
            "encoding, consolidation and retrieval."
        ),

        "Attention":
        (
            "Attention can be influenced by goals, salience, "
            "competition and available cognitive resources."
        ),

        "Reward":
        (
            "Reward learning involves interacting neural "
            "systems rather than one single pleasure center."
        ),

        "Neuroplasticity":
        (
            "Experience can alter neural structure and "
            "function across the lifespan."
        ),

        "AI & Brain":
        (
            "Artificial neural networks are inspired by "
            "some biological ideas but are not literal "
            "copies of the human brain."
        ),
    }

    for title, text in notes.items():

        with st.expander(
            title
        ):

            st.write(
                text
            )

    st.divider()

    st.info(
        "NEUROLENS is an educational cognitive "
        "neuroscience platform. Games, self-reports "
        "and visualizations are not clinical assessments."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education "
    "• Created by Ayna Jaffri"
)
