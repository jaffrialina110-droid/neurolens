import os
import random
import base64
import html
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

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


def brain_b64():
    if not os.path.exists(BRAIN_IMAGE):
        return ""
    with open(BRAIN_IMAGE, "rb") as f:
        return base64.b64encode(f.read()).decode()


BRAIN_B64 = brain_b64()


# ============================================================
# BRAIN DATA
# ============================================================

brain_parts = {
    "Prefrontal Cortex": {
        "description": "Planning, working memory, cognitive control and goal-directed behavior.",
        "behavior": "Planning, decision-making, inhibition and cognitive control.",
        "circuit": "Prefrontal Cortex → Striatum → Thalamus → Cortex",
    },
    "Hippocampus": {
        "description": "Important for memory formation, memory organization and spatial representation.",
        "behavior": "Learning, memory and spatial navigation.",
        "circuit": "Hippocampus ↔ Cortex",
    },
    "Amygdala": {
        "description": "Processes emotionally significant information and contributes to emotional learning.",
        "behavior": "Emotion, threat processing and emotional learning.",
        "circuit": "Amygdala → Hypothalamus → Brainstem",
    },
    "Striatum": {
        "description": "Participates in action selection, reward-related learning and habit-related processes.",
        "behavior": "Reward learning, action selection and habits.",
        "circuit": "Cortex → Striatum → Globus Pallidus → Thalamus → Cortex",
    },
    "Anterior Cingulate Cortex": {
        "description": "Contributes to performance monitoring, conflict processing and cognitive control.",
        "behavior": "Conflict monitoring, error processing and cognitive control.",
        "circuit": "ACC → Prefrontal Cortex → Striatum",
    },
    "Cerebellum": {
        "description": "Contributes to coordination, timing, balance and motor learning.",
        "behavior": "Coordination, timing, balance and motor learning.",
        "circuit": "Cerebellum → Thalamus → Motor Cortex",
    },
}


# ============================================================
# GEMINI / ASK AYNA
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


def ask_ayna(question, context="General neuroscience"):
    if genai is None:
        return "Gemini package is not installed."

    api_key = get_gemini_api_key()

    if not api_key:
        return "GEMINI_API_KEY is missing. Add it in Streamlit Secrets."

    prompt = f"""
You are Ask Ayna inside NEUROLENS.

Current context:
{context}

User question:
{question}

Answer in a friendly, simple and scientifically accurate way.
Keep the answer concise unless more detail is needed.
Explain neuroscience, cognition, behavior, brain systems, neurons,
synapses and related concepts clearly.

Do not diagnose the user.
Do not claim that a simple game can directly measure brain activity.
Do not turn a response into a clinical diagnosis.
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

        return "Ask Ayna did not receive an answer."

    except Exception as e:
        return f"Ask Ayna connection error: {type(e).__name__}"


def voice(text, key):
    safe = html.escape(str(text), quote=True)

    components.html(
        f"""
        <div style="
            display:flex;
            align-items:center;
            gap:10px;
            font-family:Arial;
        ">
        <button
            onclick="
            speechSynthesis.cancel();
            let u = new SpeechSynthesisUtterance({safe!r});
            u.lang='en-US';
            u.rate=0.95;
            speechSynthesis.speak(u);
            "
            style="
                border:0;
                border-radius:14px;
                padding:10px 18px;
                background:#111827;
                color:white;
                cursor:pointer;
                font-size:15px;
            ">
            🔊 Hear Ayna
        </button>
        </div>
        """,
        height=55,
    )


# ============================================================
# INTERACTIVE BRAIN EXPLORER
# ============================================================

st.divider()
st.header("🧠 Interactive Brain Explorer")

if brain_image is not None:
    st.image(
        brain_image,
        caption="NEUROLENS Brain",
        use_container_width=True,
    )
else:
    st.warning("brain.png ko app.py ke same folder mein rakho.")


selected_part = st.selectbox(
    "🔍 Choose a brain region",
    list(brain_parts.keys()),
    key="brain_region",
)

info = brain_parts[selected_part]

c1, c2 = st.columns(2)

with c1:
    st.subheader(f"🔬 {selected_part}")
    st.info(info["description"])
    st.markdown("**Behavior**")
    st.write(info["behavior"])

with c2:
    st.subheader("🔗 Circuit")
    st.code(info["circuit"])

    if st.button(
        "🔊 Hear this explanation",
        key="region_voice",
        use_container_width=True,
    ):
        voice(
            f"{selected_part}. {info['description']} "
            f"It is involved in {info['behavior']}.",
            "region_voice_player",
        )


# ============================================================
# CINEMATIC NEURAL JOURNEY
# ============================================================

st.divider()
st.header("🧬 Nerve Explorer")
st.write(
    "Travel deeper through the brain: "
    "Brain → Region → Neuron → Axon → Synapse → Neurotransmitter"
)

if "journey_level" not in st.session_state:
    st.session_state.journey_level = "brain"

if "journey_region" not in st.session_state:
    st.session_state.journey_region = selected_part

region = st.session_state.journey_region

if region not in brain_parts:
    region = selected_part

level = st.session_state.journey_level

levels = [
    "brain",
    "region",
    "neuron",
    "axon",
    "synapse",
    "nt",
]

level_names = {
    "brain": "Whole Brain",
    "region": "Brain Region",
    "neuron": "Neuron",
    "axon": "Axon & Myelin",
    "synapse": "Synapse",
    "nt": "Neurotransmitter",
}

hotspots = {
    "Prefrontal Cortex": (19, 38),
    "Hippocampus": (50, 61),
    "Amygdala": (55, 48),
    "Striatum": (48, 43),
    "Anterior Cingulate Cortex": (40, 30),
    "Cerebellum": (75, 72),
}

x, y = hotspots.get(region, (50, 50))

zoom = {
    "brain": 1,
    "region": 2.2,
    "neuron": 3.5,
    "axon": 4.8,
    "synapse": 5.8,
    "nt": 6.5,
}[level]

stage_text = {
    "brain": "Select a brain region and begin the journey.",
    "region": f"Zoomed into the {region}.",
    "neuron": f"Now entering a neuron connected with the {region} pathway.",
    "axon": "Electrical signaling travels along the axon.",
    "synapse": "The neural signal reaches the synapse.",
    "nt": "Neurotransmitters carry chemical signals across the synapse.",
}

journey_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>

body {{
    margin:0;
    background:#050b14;
    font-family:Arial,sans-serif;
}}

.scene {{
    position:relative;
    width:100%;
    height:540px;
    overflow:hidden;
    border-radius:28px;
    background:#050b14;
}}

.world {{
    position:absolute;
    inset:0;
    display:flex;
    justify-content:center;
    align-items:center;
    transform-origin:{x}% {y}%;
    transform:scale({zoom});
    transition:
        transform 1.8s cubic-bezier(.2,.8,.2,1);
}}

.brain {{
    width:90%;
    max-width:950px;
}}

.focus {{
    position:absolute;
    left:{x}%;
    top:{y}%;
    width:48px;
    height:48px;
    margin:-24px;
    border-radius:50%;
    border:3px solid white;
    box-shadow:
        0 0 0 10px rgba(50,180,255,.18),
        0 0 35px rgba(50,200,255,.9);
    animation:pulse 1.5s infinite;
}}

.pathway {{
    position:absolute;
    left:{x}%;
    top:{y}%;
    width:45%;
    height:5px;
    background:linear-gradient(
        90deg,
        transparent,
        #55eaff,
        white
    );
    transform-origin:left;
    animation:path 2s infinite;
}}

.neuron {{
    position:absolute;
    left:12%;
    top:38%;
    width:76%;
    height:120px;
    opacity:{"1" if level in ["neuron","axon","synapse","nt"] else "0"};
    transition:opacity 1s;
}}

.soma {{
    position:absolute;
    left:5%;
    top:25px;
    width:65px;
    height:65px;
    border-radius:50%;
    background:#d8a5cf;
    border:4px solid white;
}}

.dend {{
    position:absolute;
    left:-80px;
    top:55px;
    width:120px;
    height:4px;
    background:#d8a5cf;
}}

.d1 {{transform:rotate(-35deg)}}
.d2 {{transform:rotate(35deg)}}

.axon {{
    position:absolute;
    left:13%;
    right:5%;
    top:55px;
    height:12px;
    border-radius:20px;
    background:#a77c55;
}}

.myelin {{
    position:absolute;
    top:-10px;
    width:70px;
    height:34px;
    border-radius:20px;
    background:#dfeafb;
    border:3px solid #94a8bd;
}}

.m1 {{left:12%}}
.m2 {{left:30%}}
.m3 {{left:48%}}
.m4 {{left:66%}}

.signal {{
    position:absolute;
    top:-8px;
    left:0;
    width:28px;
    height:28px;
    border-radius:50%;
    background:white;
    box-shadow:0 0 30px #5cecff;
    animation:signal 2s linear infinite;
}}

.synapse {{
    position:absolute;
    right:2%;
    top:34%;
    width:130px;
    height:120px;
    opacity:{"1" if level in ["synapse","nt"] else "0"};
    transition:opacity 1s;
}}

.pre,.post {{
    position:absolute;
    top:20px;
    width:48px;
    height:80px;
    border-radius:20px;
    border:3px solid white;
}}

.pre {{
    left:0;
    background:#c78fc0;
}}

.post {{
    right:0;
    background:#8bb8df;
}}

.cleft {{
    position:absolute;
    left:48px;
    top:10px;
    width:30px;
    height:100px;
    border-left:2px dashed white;
    border-right:2px dashed white;
}}

.neuro {{
    position:absolute;
    width:12px;
    height:12px;
    border-radius:50%;
    background:#fff;
    box-shadow:0 0 18px white;
    animation:cross 1.5s infinite;
}}

.n1 {{left:43px;top:45px}}
.n2 {{left:50px;top:65px;animation-delay:.4s}}

.nt {{
    position:absolute;
    left:45%;
    top:75%;
    display:flex;
    gap:12px;
    opacity:{"1" if level == "nt" else "0"};
}}

.nt span {{
    width:20px;
    height:20px;
    border-radius:50%;
    background:white;
    box-shadow:0 0 20px white;
    animation:float 1.2s infinite alternate;
}}

.caption {{
    position:absolute;
    left:20px;
    right:20px;
    bottom:18px;
    padding:15px;
    border-radius:16px;
    background:rgba(0,0,0,.58);
    color:white;
    font-size:16px;
}}

@keyframes pulse {{
    50% {{transform:scale(1.2)}}
}}

@keyframes path {{
    0%,100% {{transform:scaleX(.1);opacity:.2}}
    50% {{transform:scaleX(1);opacity:1}}
}}

@keyframes signal {{
    from {{left:0}}
    to {{left:92%}}
}}

@keyframes cross {{
    from {{transform:translateX(0);opacity:.1}}
    50% {{opacity:1}}
    to {{transform:translateX(30px);opacity:.1}}
}}

@keyframes float {{
    to {{transform:translateY(-15px)}}
}}

</style>
</head>

<body>

<div class="scene">

<div class="world">

<img
class="brain"
src="data:image/png;base64,{BRAIN_B64}"
>

<div class="focus"></div>
<div class="pathway"></div>

<div class="neuron">

<div class="dend d1"></div>
<div class="dend d2"></div>
<div class="soma"></div>

<div class="axon">

<div class="myelin m1"></div>
<div class="myelin m2"></div>
<div class="myelin m3"></div>
<div class="myelin m4"></div>

<div class="signal"></div>

</div>
</div>

<div class="synapse">

<div class="pre"></div>
<div class="cleft"></div>
<div class="post"></div>

<div class="neuro n1"></div>
<div class="neuro n2"></div>

</div>

<div class="nt">
<span></span>
<span></span>
<span></span>
<span></span>
</div>

</div>

<div class="caption">
<b>{level_names[level]}</b>
<br>
{stage_text[level]}
</div>

</div>

</body>
</html>
"""

components.html(journey_html, height=560)


# ============================================================
# JOURNEY CONTROLS
# ============================================================

a, b, c = st.columns(3)

with a:
    if st.button("🔙 Back", use_container_width=True):
        index = levels.index(level)

        if index > 0:
            st.session_state.journey_level = levels[index - 1]

        st.rerun()

with b:
    if st.button("✨ Zoom Deeper", use_container_width=True):
        index = levels.index(level)

        if index < len(levels) - 1:
            st.session_state.journey_level = levels[index + 1]

        st.session_state.journey_region = region
        st.rerun()

with c:
    if st.button("🔊 Voice", use_container_width=True):
        voice(
            f"{level_names[level]}. {stage_text[level]}",
            "journey_voice",
        )


# ============================================================
# CONTEXTUAL ASK AYNA
# ============================================================

st.subheader("🤖 Ask Ayna — Current Journey")

context = (
    f"User is currently exploring {region}. "
    f"Current level: {level_names[level]}. "
    f"Description: {stage_text[level]}"
)

journey_question = st.text_input(
    "Ask Ayna about what you are seeing",
    placeholder="What is happening here?",
    key="journey_question",
)

if st.button("Ask Ayna", key="journey_ask") and journey_question:
    with st.spinner("🧠 Ayna is thinking..."):
        answer = ask_ayna(journey_question, context)

    st.markdown("### 💬 Ayna")
    st.write(answer)
    voice(answer, "journey_answer_voice")


# ============================================================
# GENERAL ASK AYNA
# ============================================================

st.divider()
st.header("🤖 Ask Ayna")

if "ayna_messages" not in st.session_state:
    st.session_state.ayna_messages = []

for message in st.session_state.ayna_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input(
    "Ask Ayna a neuroscience question..."
)

if question:
    st.session_state.ayna_messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("🧠 Ayna is thinking..."):
            answer = ask_ayna(question)

        st.write(answer)
        voice(answer, "general_answer")

    st.session_state.ayna_messages.append(
        {"role": "assistant", "content": answer}
    )


if st.session_state.get("ayna_messages"):
    if st.button("🗑️ Clear Ask Ayna"):
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
)


if game == "Decision Challenge":

    st.subheader("🧠 Decision Challenge")

    choice = st.radio(
        "Which would you prefer?",
        [
            "Rs. 1,000 today",
            "Rs. 1,500 after 30 days",
        ],
    )

    if st.button("Analyze Decision"):
        if choice == "Rs. 1,000 today":
            st.success("Immediate-reward preference")
        else:
            st.success("Delayed-reward preference")


elif game == "Memory Challenge":

    st.subheader("🧠 Memory Challenge")

    sequence = "7 2 9 4 1 8"

    st.write("Remember:")
    st.markdown(f"## **{sequence}**")

    answer = st.text_input(
        "Enter the sequence:"
    )

    if st.button("Check Memory"):

        if answer.replace(" ", "") == "729418":
            st.success("🎉 Correct!")
        else:
            st.error("Not quite.")


elif game == "Attention Challenge":

    st.subheader("🎯 Attention Challenge")

    target = st.selectbox(
        "Which sequence contains X?",
        [
            "A B C D",
            "A B X D",
            "A B C E",
            "A B C F",
        ],
    )

    if st.button("Check Attention"):

        if "X" in target:
            st.success("🎯 Correct!")
        else:
            st.error("Try again!")


elif game == "Stroop Challenge":

    st.subheader("🎨 Stroop Challenge")

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

    if st.button("🔄 New Stroop Trial"):
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
        padding:25px;">
        {word}
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = st.selectbox(
        "What COLOR is the word displayed in?",
        list(colors.keys()),
    )

    if st.button("Check Stroop"):

        if answer == color:
            st.success("🎯 Correct!")
        else:
            st.error("Not correct.")


elif game == "Pattern Challenge":

    st.subheader("🔢 Pattern Recognition")

    st.markdown("## 2 → 4 → 8 → 16 → ?")

    answer = st.number_input(
        "Your answer",
        min_value=0,
        step=1,
    )

    if st.button("Check Pattern"):

        if answer == 32:
            st.success("🎉 Correct!")
        else:
            st.error("Try again.")


# ============================================================
# AI BEHAVIOUR
# ============================================================

st.divider()
st.header("🧠 AI Behaviour")

st.write(
    "Choose an emoji or write what you would do."
)

scenarios = {
    "Someone suddenly disagrees with your idea.": [
        "🤔 Think first",
        "😡 React immediately",
        "😊 Stay relaxed",
        "🗣️ Ask why",
    ],
    "A friend reads your message but does not reply.": [
        "😟 Worry",
        "😌 Wait calmly",
        "😡 Get annoyed",
        "🤷 Ignore it",
    ],
    "You have two choices and little time.": [
        "⚡ Decide quickly",
        "🔍 Compare both",
        "❤️ Choose what feels right",
        "🙋 Ask someone",
    ],
}

scenario = st.selectbox(
    "Situation",
    list(scenarios.keys()),
    key="behaviour_scenario",
)

emoji_choice = st.radio(
    "Your reaction",
    scenarios[scenario],
    horizontal=True,
    key="behaviour_emoji",
)

written = st.text_area(
    "Or write your own response",
    placeholder="What would you do?",
    key="behaviour_written",
)

if st.button("🔍 Analyse My Response"):

    response = written.strip() or emoji_choice

    behaviour_prompt = f"""
Scenario:
{scenario}

User response:
{response}

Give a short behaviour-pattern reading based ONLY on this response.
Mention:
1. decision style
2. emotional response
3. problem/social approach

Keep it friendly and concise.
Do not diagnose.
"""

    with st.spinner("🧠 Analysing..."):
        behaviour_result = ask_ayna(
            behaviour_prompt,
            "AI Behaviour interaction"
        )

    st.markdown("### 🔎 Your Behaviour Pattern")
    st.write(behaviour_result)

    voice(
        behaviour_result,
        "behaviour_voice",
    )


# ============================================================
# COGNITIVE SELF REPORT
# ============================================================

st.divider()
st.header("📊 Cognitive Self-Report")

mental_load = st.slider(
    "Mental Load",
    1,
    10,
    5,
)

sleep_quality = st.slider(
    "Sleep Quality",
    1,
    10,
    5,
)

attention_level = st.slider(
    "Attention",
    1,
    10,
    5,
)

memory_confidence = st.slider(
    "Memory Confidence",
    1,
    10,
    5,
)

if go is not None:

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[
                "Mental Load",
                "Sleep Quality",
                "Attention",
                "Memory Confidence",
            ],
            y=[
                mental_load,
                sleep_quality,
                attention_level,
                memory_confidence,
            ],
        )
    )

    fig.update_layout(
        title="Your Current Ratings",
        yaxis=dict(range=[0, 10]),
        height=400,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# 3D NEURAL VISUALIZATION
# ============================================================

st.divider()
st.header("🧬 3D Neural Visualization")

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
                    points[start][0],
                    points[end][0],
                ],
                y=[
                    points[start][1],
                    points[end][1],
                ],
                z=[
                    points[start][2],
                    points[end][2],
                ],
                mode="lines",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter3d(
            x=[p[0] for p in points],
            y=[p[1] for p in points],
            z=[p[2] for p in points],
            mode="markers",
            marker=dict(size=10),
            text=[
                f"Neuron {i}"
                for i in range(1, 11)
            ],
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        title="Neural Network Visualization",
        height=600,
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


# ============================================================
# BRAIN PICTURE PUZZLE
# ============================================================

st.divider()
st.header("🧩 Brain Picture Puzzle")

st.write(
    "Rebuild the complete brain by moving the shuffled pieces."
)

if brain_image is not None:

    difficulty = st.selectbox(
        "Puzzle Level",
        [
            "Easy — 3×3",
            "Medium — 4×4",
            "Hard — 5×5",
        ],
        key="puzzle_difficulty",
    )

    if difficulty.startswith("Easy"):
        n = 3
    elif difficulty.startswith("Medium"):
        n = 4
    else:
        n = 5

    if "puzzle_seed" not in st.session_state:
        st.session_state.puzzle_seed = random.randint(
            1,
            999999,
        )

    if st.button(
        "🔀 New Puzzle",
        key="new_brain_puzzle",
    ):
        st.session_state.puzzle_seed = random.randint(
            1,
            999999,
        )
        st.rerun()

    puzzle_seed = st.session_state.puzzle_seed

    puzzle_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="
        margin:0;
        font-family:Arial;
        background:#f6f8fc;
    ">

    <div id="message"
         style="
         text-align:center;
         font-size:18px;
         font-weight:bold;
         margin:10px;">
    </div>

    <div id="puzzle"
         style="
         display:grid;
         grid-template-columns:repeat({n},1fr);
         gap:5px;
         max-width:700px;
         margin:auto;">
    </div>

    <script>

    const N = {n};
    const seed = {puzzle_seed};
    const image =
    "data:image/png;base64,{BRAIN_B64}";

    let pieces =
    [...Array(N*N).keys()];

    let s = seed >>> 0;

    function random() {{
        s =
        (s * 1664525 + 1013904223)
        >>> 0;

        return s / 4294967296;
    }}

    for (
        let i=pieces.length-1;
        i>0;
        i--
    ) {{

        let j =
        Math.floor(
            random()*(i+1)
        );

        [
            pieces[i],
            pieces[j]
        ] =
        [
            pieces[j],
            pieces[i]
        ];
    }}

    const puzzle =
    document.getElementById("puzzle");

    const message =
    document.getElementById("message");

    let selected = null;

    function makePiece(
        piece,
        position
    ) {{

        const tile =
        document.createElement("div");

        tile.draggable = true;

        tile.dataset.piece = piece;
        tile.dataset.position = position;

        const col = piece % N;
        const row =
        Math.floor(piece / N);

        const x =
        N === 1
        ? 0
        : col/(N-1)*100;

        const y =
        N === 1
        ? 0
        : row/(N-1)*100;

        tile.style.cssText = `
            aspect-ratio:1;
            border:2px solid #ccd5e1;
            border-radius:8px;
            background-image:url(${{image}});
            background-size:${{N*100}}% ${{N*100}}%;
            background-position:${{x}}% ${{y}}%;
            cursor:grab;
        `;

        tile.addEventListener(
            "dragstart",
            e => {{
                e.dataTransfer.setData(
                    "text/plain",
                    position
                );
            }}
        );

        tile.addEventListener(
            "dragover",
            e => e.preventDefault()
        );

        tile.addEventListener(
            "drop",
            e => {{

                const from =
                Number(
                    e.dataTransfer.getData(
                        "text/plain"
                    )
                );

                swap(from, position);
            }}
        );

        tile.onclick = () => {{

            if(selected === null) {{

                selected = position;

                tile.style.outline =
                "4px solid #667eea";

            }} else {{

                swap(
                    selected,
                    position
                );

                selected = null;
            }}
        }};

        return tile;
    }}

    function swap(a,b) {{

        const A =
        puzzle.children[a];

        const B =
        puzzle.children[b];

        const temp =
        document.createElement("div");

        puzzle.insertBefore(
            temp,
            A
        );

        puzzle.insertBefore(
            A,
            B
        );

        puzzle.insertBefore(
            B,
            temp
        );

        puzzle.removeChild(temp);

        refresh();
    }}

    function refresh() {{

        [
            ...puzzle.children
        ].forEach(
            (el,i) =>
            el.dataset.position=i
        );

        let correct = true;

        [
            ...puzzle.children
        ].forEach(
            (el,i) => {{

                if(
                    Number(el.dataset.piece)
                    !== i
                ) {{
                    correct=false;
                }}
            }}
        );

        if(correct) {{

            message.innerHTML =
            "🎉 BRAIN COMPLETE! 🧠";

            message.style.color =
            "#15803d";

            puzzle.style.transform =
            "scale(1.03)";

            setTimeout(
                () =>
                puzzle.style.transform =
                "scale(1)",
                300
            );

        }} else {{

            message.innerHTML =
            "Drag pieces or tap two pieces to swap.";

            message.style.color =
            "#334155";
        }}
    }}

    pieces.forEach(
        (piece,i) =>
        puzzle.appendChild(
            makePiece(piece,i)
        )
    );

    refresh();

    </script>

    </body>
    </html>
    """

    components.html(
        puzzle_html,
        height=650,
    )

else:

    st.warning(
        "brain.png missing hai."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience • Brain • Behavior • AI • Created by Ayna"
)
