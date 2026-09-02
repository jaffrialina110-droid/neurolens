import os
import random

import streamlit as st


# ============================================================
# GEMINI IMPORT
# ============================================================

try:
    from google import genai
except ImportError:
    genai = None


# ============================================================
# NEUROLENS
# Cognitive Neuroscience Educational App
# ============================================================

st.set_page_config(
    page_title="NEUROLENS",
    page_icon="🧠",
    layout="wide",
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
        "Pattern Challenge",
    ],
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
            "Rs. 1,500 after 30 days",
        ],
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

        cleaned_answer = answer.replace(" ", "")

        if cleaned_answer == "729418":

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
            "A B C F",
        ],
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
        "YELLOW",
    ]

    if "stroop_correct_color" not in st.session_state:
        st.session_state.stroop_correct_color = random.choice(
            color_options
        )

    if "stroop_word" not in st.session_state:
        st.session_state.stroop_word = random.choice(
            color_options
        )

    correct_color = st.session_state.stroop_correct_color
    word = st.session_state.stroop_word

    st.markdown(
        f"## **{word}**"
    )

    answer = st.selectbox(
        "What color do you think the word represents?",
        color_options,
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
        step=1,
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

visualization_data = {
    "Cognitive Measure": [
        "Mental Load",
        "Sleep Quality",
        "Attention",
        "Memory Confidence",
    ],
    "Score": [
        mental_load,
        sleep_quality,
        attention_level,
        memory_confidence,
    ],
}

st.bar_chart(
    visualization_data,
    x="Cognitive Measure",
    y="Score",
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
        "Attention Networks",
    ],
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
# ASK AYNA AI — GEMINI
# ============================================================

st.divider()

st.header("🤖 Ask Ayna 🧠")

st.write(
    "Ask questions about cognitive neuroscience, memory, "
    "attention, learning, emotions, decision-making and the brain."
)


# ============================================================
# CHAT SESSION STATE
# ============================================================

if "ayna_messages" not in st.session_state:
    st.session_state.ayna_messages = []


# ============================================================
# SHOW PREVIOUS MESSAGES
# ============================================================

for message in st.session_state.ayna_messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# GEMINI API KEY
# ============================================================

def get_gemini_api_key():

    # First: GEMINI_API_KEY from Streamlit Secrets
    try:
        key = st.secrets.get("GEMINI_API_KEY")

        if key:
            return str(key).strip()
    except Exception:
        pass

    # Second: GOOGLE_API_KEY from Streamlit Secrets
    try:
        key = st.secrets.get("GOOGLE_API_KEY")

        if key:
            return str(key).strip()
    except Exception:
        pass

    # Third: environment variable
    key = os.getenv("GEMINI_API_KEY")

    if key:
        return key.strip()

    # Fourth: Google environment variable
    key = os.getenv("GOOGLE_API_KEY")

    if key:
        return key.strip()

    return None


# ============================================================
# ASK AYNA FUNCTION
# ============================================================

def ask_ayna(question):

    # Check package
    if genai is None:

        return (
            "⚠️ Gemini package is missing.\n\n"
            "Please add `google-genai` to requirements.txt "
            "and redeploy the app."
        )

    # Get API key
    api_key = get_gemini_api_key()

    if not api_key:

        return (
            "⚠️ Ask Ayna is not connected yet.\n\n"
            "Please add your Gemini API key to Streamlit "
            "Secrets as `GEMINI_API_KEY`."
        )

    try:

        # Create Gemini client
        client = genai.Client(
            api_key=api_key
        )

        # System instructions
        instructions = """
You are Ask Ayna, an educational cognitive neuroscience assistant.

Your purpose is to explain cognitive neuroscience clearly,
accurately and in an easy-to-understand way.

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
- cognitive psychology
- behavioral neuroscience

Important rules:

1. Keep explanations educational and scientifically responsible.

2. Do not diagnose medical, psychiatric or psychological disorders.

3. Do not claim that a simple game measures actual brain activity.

4. Do not present self-reported scores as clinical measurements.

5. Clearly distinguish established scientific evidence from
hypotheses or uncertain findings.

6. If a question is medical or requires diagnosis, encourage
the user to consult a qualified healthcare professional.

7. Use simple language while maintaining scientific accuracy.

8. Answer directly and avoid unnecessary repetition.

9. Use short examples when useful.

You are called "Ask Ayna".
"""

        full_prompt = (
            instructions
            + "\n\nUser question:\n"
            + question
        )

        # Gemini request
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )

        # Read response safely
        answer = getattr(response, "text", None)

        if answer:

            return answer.strip()

        return (
            "⚠️ Ask Ayna received no text response.\n\n"
            "Please try your question again."
        )

    except Exception as e:

        # Show actual error type and details
        error_name = type(e).__name__
        error_details = str(e)

        if not error_details:
            error_details = "No additional error details were provided."

        return (
            "⚠️ Ask Ayna could not connect to Gemini.\n\n"
            f"**Error type:** `{error_name}`\n\n"
            f"**Details:** `{error_details}`\n\n"
            "Please check your Gemini API key, API access, "
            "model availability and requirements.txt."
        )


# ============================================================
# ASK AYNA INPUT
# ============================================================

question = st.chat_input(
    "Ask Ayna a neuroscience question..."
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    # Save user message
    st.session_state.ayna_messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    # Generate answer
    with st.chat_message("assistant"):

        with st.spinner("🧠 Ayna is thinking..."):

            answer = ask_ayna(question)

        st.markdown(answer)

    # Save assistant response
    st.session_state.ayna_messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# ============================================================
# CLEAR CHAT
# ============================================================

if st.session_state.get("ayna_messages"):

    if st.button("🗑️ Clear Ask Ayna Chat"):

        st.session_state.ayna_messages = []

        st.rerun()


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
