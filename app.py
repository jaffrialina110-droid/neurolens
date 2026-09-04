import os
import random
import streamlit as st
from PIL import Image

try:
    from google import genai
except ImportError:
    genai = None

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

import streamlit.components.v1 as components


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
            "The prefrontal cortex is involved in planning, "
            "cognitive control, working memory and goal-directed behavior."
        ),
        "voice": (
            "The prefrontal cortex helps us plan, control behavior, "
            "hold information in working memory, and make goal-directed decisions."
        ),
    },

    "Hippocampus": {
        "description": (
            "The hippocampus plays an important role in memory formation "
            "and spatial representation."
        ),
        "voice": (
            "The hippocampus plays an important role in memory formation "
            "and spatial representation."
        ),
    },

    "Amygdala": {
        "description": (
            "The amygdala is involved in processing emotionally significant "
            "information and emotional learning."
        ),
        "voice": (
            "The amygdala helps process emotionally significant information "
            "and contributes to emotional learning."
        ),
    },

    "Striatum": {
        "description": (
            "The striatum is involved in action selection, reward-related "
            "learning and habit-related processes."
        ),
        "voice": (
            "The striatum contributes to action selection, reward learning "
            "and habit-related behavior."
        ),
    },

    "Anterior Cingulate Cortex": {
        "description": (
            "The anterior cingulate cortex is involved in performance "
            "monitoring, conflict processing and cognitive control."
        ),
        "voice": (
            "The anterior cingulate cortex contributes to performance "
            "monitoring, conflict processing and cognitive control."
        ),
    },

    "Cerebellum": {
        "description": (
            "The cerebellum is important for coordination, motor learning, "
            "timing and balance."
        ),
        "voice": (
            "The cerebellum contributes to movement coordination, balance, "
            "timing and motor learning."
        ),
    },
}


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
    "Choose a brain region",
    list(brain_parts.keys()),
)

part_info = brain_parts[selected_part]

st.subheader(f"🔬 {selected_part}")

st.info(part_info["description"])


# ============================================================
# VOICE
# ============================================================

st.subheader("🔊 Listen to Explanation")

voice_text = part_info["voice"]

safe_text = (
    voice_text
    .replace("\\", "\\\\")
    .replace("'", "\\'")
    .replace("\n", " ")
)

components.html(
    f"""
    <div style="
        padding:15px;
        text-align:center;
        border-radius:12px;
        background:#f1f3f6;
    ">

    <button onclick="speakText()"
        style="
            padding:12px 20px;
            border:none;
            border-radius:10px;
            font-size:16px;
            cursor:pointer;
        ">
        🔊 Play
    </button>

    <button onclick="stopSpeech()"
        style="
            padding:12px 20px;
            margin-left:8px;
            border:none;
            border-radius:10px;
            font-size:16px;
            cursor:pointer;
        ">
        ⏹ Stop
    </button>

    <script>

    function speakText() {{
        window.speechSynthesis.cancel();

        const text = '{safe_text}';

        const speech = new SpeechSynthesisUtterance(text);

        speech.rate = 0.9;
        speech.pitch = 1.0;

        window.speechSynthesis.speak(speech);
    }}

    function stopSpeech() {{
        window.speechSynthesis.cancel();
    }}

    </script>

    </div>
    """,
    height=100,
)


# ============================================================
# BRAIN PUZZLE
# ============================================================

st.divider()

st.header("🧩 Full Brain Picture Puzzle")

st.write(
    "Solve the scrambled brain image by arranging the pieces "
    "in the correct order."
)

if brain_image is not None:

    difficulty = st.selectbox(
        "Puzzle difficulty",
        [
            "Easy — 4 pieces",
            "Medium — 9 pieces",
            "Hard — 16 pieces",
        ],
    )

    if difficulty.startswith("Easy"):
        rows, cols = 2, 2

    elif difficulty.startswith("Medium"):
        rows, cols = 3, 3

    else:
        rows, cols = 4, 4


    image = brain_image.convert("RGB")

    width, height = image.size

    piece_width = width // cols
    piece_height = height // rows

    pieces = []

    for row in range(rows):

        for col in range(cols):

            left = col * piece_width
            top = row * piece_height

            right = (
                (col + 1) * piece_width
                if col < cols - 1
                else width
            )

            bottom = (
                (row + 1) * piece_height
                if row < rows - 1
                else height
            )

            piece = image.crop(
                (left, top, right, bottom)
            )

            pieces.append(piece)


    total = rows * cols


    if (
        "puzzle_order" not in st.session_state
        or st.session_state.get("puzzle_total") != total
    ):

        st.session_state.puzzle_order = list(
            range(total)
        )

        random.shuffle(
            st.session_state.puzzle_order
        )

        st.session_state.puzzle_total = total


    if st.button("🔀 New Puzzle"):

        st.session_state.puzzle_order = list(
            range(total)
        )

        random.shuffle(
            st.session_state.puzzle_order
        )

        st.rerun()


    st.subheader("🧩 Scrambled Pieces")

    index = 0

    for row in range(rows):

        columns = st.columns(cols)

        for col in range(cols):

            piece_number = (
                st.session_state.puzzle_order[index]
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


    st.subheader("🧠 Your Solution")

    st.write(
        f"Enter the correct piece numbers from "
        f"top-left to bottom-right."
    )

    example = " ".join(
        str(i)
        for i in range(1, total + 1)
    )

    answer = st.text_input(
        f"Example: {example}"
    )


    if st.button("✅ Check Puzzle"):

        try:

            user_order = [
                int(x)
                for x in answer.split()
            ]

            correct_order = list(
                range(1, total + 1)
            )

            if user_order == correct_order:

                st.success(
                    "🎉 Brain puzzle solved!"
                )

                st.balloons()

                st.info(
                    "This educational task explores visual-spatial "
                    "organization and attention."
                )

            else:

                st.error(
                    "Not correct yet. Try again."
                )

        except ValueError:

            st.error(
                "Enter numbers separated by spaces."
            )

else:

    st.info(
        "Upload brain.png to activate the puzzle."
    )


# ============================================================
# 3D NEURAL VISUALIZATION
# ============================================================

st.divider()

st.header("🧬 3D Neural Visualization")

st.write(
    "Educational 3D-style visualization of neurons and their connections."
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

    x = [p[0] for p in points]
    y = [p[1] for p in points]
    z = [p[2] for p in points]

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
                x=[x[start], x[end]],
                y=[y[start], y[end]],
                z=[z[start], z[end]],
                mode="lines",
                line=dict(width=4),
                showlegend=False,
            )
        )


    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(size=10),
            text=[
                "Neuron 1",
                "Neuron 2",
                "Neuron 3",
                "Neuron 4",
                "Neuron 5",
                "Neuron 6",
                "Neuron 7",
                "Neuron 8",
                "Neuron 9",
                "Neuron 10",
            ],
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        )
    )


    fig.update_layout(
        title="Educational Neural Network",
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


st.caption(
    "Educational visualization only; it does not represent actual "
    "neural activity."
)


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

    st.subheader("🧠 Memory Challenge")

    sequence = "7 2 9 4 1 8"

    st.write("Remember:")

    st.markdown(
        f"## **{sequence}**"
    )

    answer = st.text_input(
        "Enter the sequence:"
    )

    if st.button("Check Memory"):

        if answer.replace(" ", "") == "729418":

            st.success("🎉 Correct!")

        else:

            st.error("Not quite. Try again.")


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

            st.info(
                "This task explores visual search and attention."
            )

        else:

            st.error("Try again!")


elif game == "Stroop Challenge":

    st.subheader("🎨 Stroop Challenge")

    colors = [
        "RED",
        "BLUE",
        "GREEN",
        "YELLOW",
    ]

    if "stroop_color" not in st.session_state:

        st.session_state.stroop_color = random.choice(
            colors
        )

    if "stroop_word" not in st.session_state:

        st.session_state.stroop_word = random.choice(
            colors
        )

    st.markdown(
        f"## **{st.session_state.stroop_word}**"
    )

    answer = st.selectbox(
        "Choose the displayed color:",
        colors,
    )

    if st.button("Check Stroop"):

        if answer == st.session_state.stroop_color:

            st.success(
                "🎯 Correct! This explores response control."
            )

        else:

            st.info(
                "Stroop tasks explore attention and interference."
            )


elif game == "Pattern Challenge":

    st.subheader("🔢 Pattern Recognition")

    st.markdown(
        "### 2 → 4 → 8 → 16 → ?"
    )

    answer = st.number_input(
        "Your answer",
        min_value=0,
        step=1,
    )

    if st.button("Check Pattern"):

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

st.header("📊 Cognitive Self-Report")

st.caption(
    "These are self-reported educational ratings, "
    "not measurements of brain activity."
)

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

st.bar_chart(
    {
        "Mental Load": mental_load,
        "Sleep Quality": sleep_quality,
        "Attention": attention_level,
        "Memory Confidence": memory_confidence,
    }
)


# ============================================================
# ASK AYNA
# ============================================================

st.divider()

st.header("🤖 Ask Ayna 🧠")

st.write(
    "Ask Ayna about memory, attention, learning, "
    "behavior, cognition, brain systems and neuroscience."
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


# ============================================================
# GEMINI KEY
# ============================================================

def get_gemini_api_key():

    try:

        key = st.secrets.get(
            "GEMINI_API_KEY"
        )

        if key:

            return str(key).strip()

    except Exception:

        pass


    try:

        key = st.secrets.get(
            "GOOGLE_API_KEY"
        )

        if key:

            return str(key).strip()

    except Exception:

        pass


    key = os.getenv(
        "GEMINI_API_KEY"
    )

    if key:

        return key.strip()


    key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if key:

        return key.strip()


    return None


# ============================================================
# ASK AYNA FUNCTION
# ============================================================

def ask_ayna(question):

    if genai is None:

        return (
            "⚠️ Gemini package is not installed. "
            "Check requirements.txt."
        )


    api_key = get_gemini_api_key()

    if not api_key:

        return (
            "⚠️ Ask Ayna is not connected. "
            "Add GEMINI_API_KEY to Streamlit Secrets."
        )


    try:

        client = genai.Client(
            api_key=api_key
        )


        prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience assistant.

Explain neuroscience accurately and clearly.

You can discuss:

- memory
- attention
- learning
- emotion
- decision-making
- reward
- perception
- cognitive control
- brain systems
- neuroplasticity
- neurons
- synapses
- neural networks
- behavioral neuroscience

Rules:

1. Do not diagnose medical or psychiatric disorders.
2. Do not claim simple games measure brain activity.
3. Do not present self-reported ratings as clinical measurements.
4. Distinguish established evidence from hypotheses.
5. Use simple but scientifically accurate language.
6. If a question requires medical diagnosis, recommend a qualified professional.
7. Answer directly.

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


# ============================================================
# CHAT
# ============================================================

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

        st.markdown(question)


    with st.chat_message("assistant"):

        with st.spinner(
            "🧠 Ayna is thinking..."
        ):

            answer = ask_ayna(
                question
            )

        st.markdown(answer)


    st.session_state.ayna_messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# ============================================================
# CLEAR CHAT
# ============================================================

if st.session_state.get(
    "ayna_messages"
):

    if st.button(
        "🗑️ Clear Ask Ayna Chat"
    ):

        st.session_state.ayna_messages = []

        st.rerun()


# ============================================================
# SCIENCE NOTE
# ============================================================

st.divider()

st.header("📚 Science Note")

st.write(
    "NEUROLENS is an educational cognitive neuroscience tool. "
    "Its games, self-reported ratings and visualizations are "
    "not clinical assessments or direct measurements of brain activity."
)

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • Created by Ayna"
)
