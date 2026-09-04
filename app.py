import os
import random
import io

import streamlit as st

try:
    from google import genai
except ImportError:
    genai = None

try:
    from PIL import Image
except ImportError:
    Image = None


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
        "Brain Image Puzzle",
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
            "This educational task explores choices between "
            "immediate and delayed rewards."
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
            st.write("You recalled the sequence correctly.")
        else:
            st.error("Not quite. Try again.")


# ============================================================
# ATTENTION CHALLENGE
# ============================================================

elif game == "Attention Challenge":

    st.subheader("🎯 Attention Challenge")

    st.write("Find the letter X.")

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

    st.markdown(f"## **{word}**")

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
                "Stroop tasks explore attention "
                "and interference control."
            )


# ============================================================
# PATTERN CHALLENGE
# ============================================================

elif game == "Pattern Challenge":

    st.subheader("🔢 Pattern Recognition")

    st.write("What number comes next?")

    st.markdown("### 2 → 4 → 8 → 16 → ?")

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
# BRAIN IMAGE PUZZLE
# ============================================================

elif game == "Brain Image Puzzle":

    st.subheader("🧠 Brain Image Puzzle")
    st.write(
        "Arrange the brain image pieces in the correct order."
    )

    if Image is None:

        st.error(
            "Pillow is not installed. Add `Pillow` to "
            "requirements.txt."
        )

    else:

        # ----------------------------------------------------
        # Load brain image
        # ----------------------------------------------------

        brain_image = None

        # First look for brain.png in the project folder
        possible_files = [
            "brain.png",
            "brain.jpg",
            "brain.jpeg",
            "brain.webp",
        ]

        for filename in possible_files:

            if os.path.exists(filename):

                try:
                    brain_image = Image.open(filename).convert("RGB")
                    break
                except Exception:
                    pass

        # If image is not found, allow upload
        if brain_image is None:

            uploaded_brain = st.file_uploader(
                "Upload your brain image",
                type=["png", "jpg", "jpeg", "webp"],
                key="brain_image_upload",
            )

            if uploaded_brain is not None:

                try:
                    brain_image = Image.open(
                        uploaded_brain
                    ).convert("RGB")

                except Exception:

                    st.error(
                        "The selected file could not be opened."
                    )

        if brain_image is None:

            st.warning(
                "Please upload your brain image above, "
                "or place a file named `brain.png` in your project."
            )

        else:

            st.success("🧠 Brain image loaded!")

            # ------------------------------------------------
            # Puzzle settings
            # ------------------------------------------------

            puzzle_size = st.selectbox(
                "Puzzle difficulty",
                [
                    "Easy — 2 × 2",
                    "Medium — 3 × 3",
                    "Hard — 4 × 4",
                ],
            )

            if puzzle_size == "Easy — 2 × 2":
                grid_size = 2
            elif puzzle_size == "Medium — 3 × 3":
                grid_size = 3
            else:
                grid_size = 4

            # ------------------------------------------------
            # Prepare image
            # ------------------------------------------------

            image_size = 600

            brain_image.thumbnail(
                (image_size, image_size)
            )

            canvas = Image.new(
                "RGB",
                (image_size, image_size),
                "white",
            )

            x_offset = (
                image_size - brain_image.width
            ) // 2

            y_offset = (
                image_size - brain_image.height
            ) // 2

            canvas.paste(
                brain_image,
                (x_offset, y_offset),
            )

            # ------------------------------------------------
            # Create puzzle pieces
            # ------------------------------------------------

            piece_width = image_size // grid_size
            piece_height = image_size // grid_size

            pieces = []

            for row in range(grid_size):

                for col in range(grid_size):

                    left = col * piece_width
                    upper = row * piece_height

                    right = (
                        (col + 1) * piece_width
                    )

                    lower = (
                        (row + 1) * piece_height
                    )

                    piece = canvas.crop(
                        (
                            left,
                            upper,
                            right,
                            lower,
                        )
                    )

                    pieces.append(piece)

            total_pieces = len(pieces)

            # ------------------------------------------------
            # Create shuffled puzzle
            # ------------------------------------------------

            if (
                "brain_puzzle_order" not in st.session_state
                or
                st.session_state.get(
                    "brain_puzzle_size"
                ) != grid_size
            ):

                puzzle_order = list(
                    range(total_pieces)
                )

                random.shuffle(puzzle_order)

                # Make sure it isn't accidentally already solved
                if puzzle_order == list(
                    range(total_pieces)
                ):

                    random.shuffle(
                        puzzle_order
                    )

                st.session_state.brain_puzzle_order = (
                    puzzle_order
                )

                st.session_state.brain_puzzle_size = (
                    grid_size
                )

                st.session_state.brain_selected = None

            # ------------------------------------------------
            # Reset puzzle
            # ------------------------------------------------

            if st.button("🔄 New Puzzle"):

                puzzle_order = list(
                    range(total_pieces)
                )

                random.shuffle(puzzle_order)

                if puzzle_order == list(
                    range(total_pieces)
                ):

                    random.shuffle(
                        puzzle_order
                    )

                st.session_state.brain_puzzle_order = (
                    puzzle_order
                )

                st.session_state.brain_selected = None

                st.rerun()

            st.write(
                "Click one piece, then click another piece "
                "to swap them."
            )

            # ------------------------------------------------
            # Puzzle display
            # ------------------------------------------------

            order = st.session_state.brain_puzzle_order

            for row in range(grid_size):

                cols = st.columns(grid_size)

                for col in range(grid_size):

                    position = (
                        row * grid_size + col
                    )

                    piece_index = order[position]

                    with cols[col]:

                        st.image(
                            pieces[piece_index],
                            use_container_width=True,
                        )

                        if st.button(
                            f"Select {position + 1}",
                            key=f"brain_piece_{position}",
                        ):

                            selected = (
                                st.session_state.brain_selected
                            )

                            if selected is None:

                                st.session_state.brain_selected = (
                                    position
                                )

                            else:

                                first = selected
                                second = position

                                order[first], order[second] = (
                                    order[second],
                                    order[first],
                                )

                                st.session_state.brain_puzzle_order = (
                                    order
                                )

                                st.session_state.brain_selected = (
                                    None
                                )

                                st.rerun()

            # ------------------------------------------------
            # Selected piece
            # ------------------------------------------------

            selected = st.session_state.get(
                "brain_selected"
            )

            if selected is not None:

                st.info(
                    f"Piece {selected + 1} selected. "
                    "Now select another piece to swap."
                )

            # ------------------------------------------------
            # Check solution
            # ------------------------------------------------

            st.divider()

            if st.button(
                "🧩 Check Brain Puzzle",
                type="primary",
            ):

                correct_order = list(
                    range(total_pieces)
                )

                if order == correct_order:

                    st.success(
                        "🎉 Brain Puzzle Solved!"
                    )

                    st.balloons()

                    st.info(
                        "Excellent! You reconstructed the "
                        "brain image correctly."
                    )

                else:

                    correct_count = sum(
                        1
                        for i, value in enumerate(order)
                        if i == value
                    )

                    st.warning(
                        f"Not solved yet. "
                        f"{correct_count}/{total_pieces} "
                        "pieces are currently in the correct position."
                    )

            # ------------------------------------------------
            # Educational note
            # ------------------------------------------------

            st.caption(
                "This is an educational visual puzzle. "
                "Puzzle performance is not a clinical measurement "
                "of memory, intelligence or brain function."
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
# DAILY ASK AYNA LIMIT
# ============================================================

from datetime import date

TODAY = str(date.today())

if (
    "ayna_date" not in st.session_state
    or st.session_state.ayna_date != TODAY
):

    st.session_state.ayna_date = TODAY
    st.session_state.ayna_daily_count = 0

if "ayna_daily_count" not in st.session_state:
    st.session_state.ayna_daily_count = 0

DAILY_LIMIT = 10


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

    try:

        secret_key = st.secrets.get(
            "GEMINI_API_KEY"
        )

        if secret_key:
            return str(secret_key).strip()

    except Exception:
        pass

    try:

        secret_key = st.secrets.get(
            "GOOGLE_API_KEY"
        )

        if secret_key:
            return str(secret_key).strip()

    except Exception:
        pass

    env_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if env_key:
        return env_key.strip()

    env_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if env_key:
        return env_key.strip()

    return None


# ============================================================
# ASK AYNA FUNCTION
# ============================================================

def ask_ayna(question):

    if genai is None:

        return (
            "⚠️ Gemini package is not installed.\n\n"
            "Please add `google-genai` to requirements.txt "
            "and redeploy the app."
        )

    api_key = get_gemini_api_key()

    if not api_key:

        return (
            "⚠️ Ask Ayna is not connected yet.\n\n"
            "Please add your Gemini API key to Streamlit "
            "Secrets using the name `GEMINI_API_KEY`."
        )

    try:

        client = genai.Client(
            api_key=api_key
        )

        prompt = f"""
You are Ask Ayna, an educational cognitive neuroscience assistant.

Explain neuroscience clearly, accurately and responsibly.

Topics include:

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
- neurons
- synapses
- neural circuits
- brain anatomy

Rules:

1. Keep explanations educational and scientifically responsible.

2. Do not diagnose medical, psychiatric or psychological disorders.

3. Do not claim that a simple game measures actual brain activity.

4. Do not present self-reported scores as clinical measurements.

5. Distinguish established evidence from hypotheses.

6. For medical questions requiring diagnosis, recommend a qualified
healthcare professional.

7. Use simple language while maintaining scientific accuracy.

8. Answer directly.

9. Use examples when useful.

10. You are called "Ask Ayna".

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
            "⚠️ Ask Ayna received an empty response. "
            "Please try again."
        )

    except Exception as e:

        error_name = type(e).__name__

        error_text = str(e)

        # Hide potentially sensitive information
        safe_error = error_text[:500]

        return (
            "⚠️ Ask Ayna could not generate a response.\n\n"
            f"**Error:** `{error_name}`\n\n"
            f"`{safe_error}`\n\n"
            "Please try again in a moment."
        )


# ============================================================
# ASK AYNA INPUT
# ============================================================

if st.session_state.ayna_daily_count < DAILY_LIMIT:

    question = st.chat_input(
        "Ask Ayna a neuroscience question..."
    )

else:

    question = None

    st.warning(
        "🌙 You have reached today's Ask Ayna limit "
        f"of {DAILY_LIMIT} questions."
    )

    st.info(
        "Your app limit automatically resets on the next day."
    )


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    st.session_state.ayna_daily_count += 1

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

            answer = ask_ayna(question)

        st.markdown(answer)

    st.session_state.ayna_messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    st.caption(
        f"Ask Ayna usage today: "
        f"{st.session_state.ayna_daily_count}/{DAILY_LIMIT}"
    )


# ============================================================
# CLEAR CHAT
# ============================================================

if st.session_state.get("ayna_messages"):

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
    "NEUROLENS provides educational cognitive tasks, "
    "visual puzzles and neuroscience explanations. "
    "Game scores and self-reported ratings should not "
    "be interpreted as clinical diagnoses or direct "
    "measurements of brain activity."
)

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education "
    "• Ask Ayna • Created by Ayna"
)
