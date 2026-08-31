import streamlit as st
import random

# ============================================================
# NEUROLENS
# Cognitive Neuroscience Educational App
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide"
)

# ============================================================
# TITLE
# ============================================================

st.title("🧠 NEUROLENS")
st.caption("Explore cognition, behavior & the brain")

st.divider()

# ============================================================
# COGNITIVE GAMES
# ============================================================

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
    ]
)

# ============================================================
# DECISION CHALLENGE
# ============================================================

if game == "Decision Challenge":

    st.subheader("🧠 Quick Decision Challenge")

    st.write("Which option would you prefer?")

    choice = st.radio(
        "Choose one:",
        [
            "Rs. 1,000 today",
            "Rs. 1,500 after 30 days"
        ]
    )

    if st.button("Analyze Decision"):

        if choice == "Rs. 1,000 today":
            st.success("Pattern: Immediate-reward preference")
        else:
            st.success("Pattern: Delayed-reward preference")

        st.info(
            "This educational task explores how people make "
            "choices between immediate and delayed rewards."
        )


# ============================================================
# MEMORY CHALLENGE
# ============================================================

elif game == "Memory Challenge":

    st.subheader("🧠 Memory Challenge")

    sequence = "7 2 9 4 1 8"

    st.write("Remember this sequence:")

    st.markdown(f"## **{sequence}**")

    answer = st.text_input(
        "Enter the sequence from memory:"
    )

    if st.button("Check Memory"):

        if answer.replace(" ", "") == "729418":

            st.success("🎉 Correct!")

            st.write(
                "You recalled the sequence correctly."
            )

        else:

            st.error(
                "Not quite. Try again."
            )


# ============================================================
# ATTENTION CHALLENGE
# ============================================================

elif game == "Attention Challenge":

    st.subheader("🎯 Attention Challenge")

    st.write(
        "Find the letter X as quickly as possible."
    )

    target = st.selectbox(
        "Which sequence contains X?",
        [
            "A B C D",
            "A B X D",
            "A B C E",
            "A B C F"
        ]
    )

    if st.button("Check Attention"):

        if "X" in target:

            st.success("🎯 Correct!")

            st.info(
                "This educational task explores attention "
                "and visual search."
            )

        else:

            st.error("Try again!")


# ============================================================
# STROOP CHALLENGE
# ============================================================

elif game == "Stroop Challenge":

    st.subheader("🎨 Stroop Challenge")

    st.write(
        "Ignore the meaning of the word and choose "
        "its displayed color."
    )

    color_options = [
        "RED",
        "BLUE",
        "GREEN",
        "YELLOW"
    ]

    correct_color = random.choice(color_options)
    word = random.choice(color_options)

    st.markdown(
        f"## **{word}**"
    )

    answer = st.selectbox(
        "What color do you think the word represents?",
        color_options
    )

    if st.button("Check Stroop"):

        if answer == correct_color:

            st.success(
                "🎯 Correct! This task explores response control."
            )

        else:

            st.info(
                "Interesting! Stroop tasks explore attention "
                "and interference control."
            )


# ============================================================
# PATTERN CHALLENGE
# ============================================================

elif game == "Pattern Challenge":

    st.subheader("🔢 Pattern Recognition")

    st.write(
        "What number comes next?"
    )

    st.markdown(
        "### 2 → 4 → 8 → 16 → ?"
    )

    answer = st.number_input(
        "Your answer",
        min_value=0,
        step=1
    )

    if st.button("Check Pattern"):

        if answer == 32:

            st.success(
                "🎉 Correct! The pattern doubles each time."
            )

        else:

            st.error(
                "Try again. Look at how each number changes."
            )


# ============================================================
# COGNITIVE VISUALIZATION
# ============================================================

st.divider()

st.header("📊 Cognitive Visualization")

st.write(
    "Rate your current experience. These are self-reported "
    "scores and are not measurements of brain activity."
)

mental_load = st.slider(
    "Mental Load",
    1,
    10,
    5
)

sleep_quality = st.slider(
    "Sleep Quality",
    1,
    10,
    5
)

attention_level = st.slider(
    "Attention",
    1,
    10,
    5
)

memory_confidence = st.slider(
    "Memory Confidence",
    1,
    10,
    5
)

visualization_data = {
    "Cognitive Measure": [
        "Mental Load",
        "Sleep Quality",
        "Attention",
        "Memory Confidence"
    ],
    "Score": [
        mental_load,
        sleep_quality,
        attention_level,
        memory_confidence
    ]
}

st.bar_chart(
    visualization_data,
    x="Cognitive Measure",
    y="Score"
)

st.caption(
    "These scores are self-reported educational measures, "
    "not clinical or direct measurements of brain activity."
)


# ============================================================
# BRAIN SYSTEM EXPLORER
# ============================================================

st.divider()

st.header("🧠 Explore Brain Systems")

brain_system = st.selectbox(
    "Explore a cognitive system",
    [
        "Select a system",
        "Prefrontal Cortex",
        "Hippocampus",
        "Striatum",
        "Anterior Cingulate Cortex",
        "Attention Networks"
    ]
)

if brain_system == "Prefrontal Cortex":

    st.info(
        "The prefrontal cortex is involved in cognitive control, "
        "planning, working memory and goal-directed behavior."
    )

elif brain_system == "Hippocampus":

    st.info(
        "The hippocampus plays an important role in memory "
        "formation and spatial representation."
    )

elif brain_system == "Striatum":

    st.info(
        "The striatum is involved in action selection, "
        "reward-related learning and habit-related processes."
    )

elif brain_system == "Anterior Cingulate Cortex":

    st.info(
        "The anterior cingulate cortex is involved in monitoring "
        "conflict, performance and aspects of cognitive control."
    )

elif brain_system == "Attention Networks":

    st.info(
        "Attention networks help select relevant information "
        "and regulate the allocation of cognitive resources."
    )


# ============================================================
# ASK AYNA AI
# ============================================================

st.divider()

st.header("🤖 Ask Ayna 🧠")

st.write(
    "Ask questions about cognitive neuroscience, memory, "
    "attention, learning, emotions, decision-making and the brain."
)

# Initialize chat
if "ayna_messages" not in st.session_state:
    st.session_state.ayna_messages = []

# Show previous messages
for message in st.session_state.ayna_messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


question = st.chat_input(
    "Ask Ayna a neuroscience question..."
)

if question:

    # Show user message
    st.session_state.ayna_messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # ========================================================
    # OPENAI CONNECTION
    # ========================================================

    try:

        from openai import OpenAI

        # Check Streamlit secret
        if "OPENAI_API_KEY" not in st.secrets:

            answer = (
                "⚠️ OpenAI API key is not configured yet. "
                "Please add OPENAI_API_KEY to Streamlit Secrets."
            )

        else:

            client = OpenAI(
                api_key=st.secrets["OPENAI_API_KEY"]
            )

            response = client.responses.create(
                model="gpt-5.6-luna",
                instructions="""
You are Ask Ayna, an educational cognitive neuroscience assistant.

Explain cognitive neuroscience clearly, accurately and simply.

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

Do not diagnose medical or psychological disorders.

Do not claim that games measure actual brain activity.

Clearly explain uncertainty when scientific evidence is limited.

Keep answers educational and easy to understand.
""",
                input=question
            )

            answer = response.output_text

    except Exception as e:
    answer = (
        "⚠️ Ask Ayna error.\n\n"
        f"Error type: {type(e).__name__}\n\n"
        f"Error details: {repr(e)}"
    )

    # Save assistant message
    st.session_state.ayna_messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    # Display answer
    with st.chat_message("assistant"):
        st.markdown(answer)


# ============================================================
# SCIENCE NOTE
# ============================================================

st.divider()

st.header("📚 Science Note")

st.write(
    "NEUROLENS provides educational cognitive tasks and "
    "explanations. Game scores and self-reported ratings "
    "should not be interpreted as clinical diagnoses or "
    "direct measurements of brain activity."
)

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • Created by Ayna"
)
