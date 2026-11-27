
"""NeuroLens — Interactive Cognitive Challenges."""

import random
import streamlit as st


COLORS = ["RED", "BLUE", "GREEN", "YELLOW"]


def initialize():
    defaults = {
        "nl_memory_sequence": None,
        "nl_memory_phase": "ready",
        "nl_attention_sequence": None,
        "nl_stroop_trial": None,
        "nl_pattern_started": False,
        "nl_challenge_results": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_result(task, score, details):
    st.session_state.nl_challenge_results.append({
        "task": task,
        "score": score,
        "details": details,
    })


def memory_task():
    st.subheader("🧠 Memory Sequence")

    phase = st.session_state.nl_memory_phase

    if phase == "ready":
        st.write("Memorize the six-digit sequence.")

        if st.button("Start memory challenge"):
            st.session_state.nl_memory_sequence = "".join(
                random.choices("0123456789", k=6)
            )
            st.session_state.nl_memory_phase = "show"
            st.rerun()

    elif phase == "show":
        st.markdown("### Remember this code")

        st.markdown(
            f"<h1 style='text-align:center; letter-spacing:12px'>"
            f"{st.session_state.nl_memory_sequence}</h1>",
            unsafe_allow_html=True,
        )

        if st.button("Hide sequence and start recall"):
            st.session_state.nl_memory_phase = "recall"
            st.rerun()

    elif phase == "recall":
        st.write("The sequence is hidden. Enter what you remember.")

        answer = st.text_input(
            "Enter the six digits",
            max_chars=6,
            key="nl_memory_answer",
        )

        if st.button("Submit memory answer"):
            correct = (
                answer == st.session_state.nl_memory_sequence
            )

            score = 100 if correct else 0

            st.success("Correct recall!") if correct else (
                st.info("That sequence did not match.")
            )

            save_result(
                "Memory Sequence",
                score,
                "Correct" if correct else "Incorrect",
            )

            st.session_state.nl_memory_phase = "ready"
            st.session_state.nl_memory_sequence = None
            st.rerun()


def attention_task():
    st.subheader("🎯 Attention Challenge")

    if st.session_state.nl_attention_sequence is None:
        st.write("Count how many X characters appear below.")

        if st.button("Start attention challenge"):
            chars = random.choices(
                ["X", "O", "K", "M", "T"],
                weights=[2, 3, 3, 3, 3],
                k=30,
            )

            st.session_state.nl_attention_sequence = {
                "text": " ".join(chars),
                "answer": chars.count("X"),
            }
            st.rerun()

    else:
        trial = st.session_state.nl_attention_sequence

        st.markdown(
            f"<div style='font-size:22px;line-height:2;"
            f"padding:15px'>{trial['text']}</div>",
            unsafe_allow_html=True,
        )

        answer = st.number_input(
            "How many X characters did you find?",
            min_value=0,
            max_value=30,
            step=1,
            key="nl_attention_answer",
        )

        if st.button("Submit attention answer"):
            correct = int(answer) == trial["answer"]
            score = 100 if correct else 0

            st.success("Correct!") if correct else st.info(
                f"Correct count: {trial['answer']}"
            )

            save_result(
                "Attention",
                score,
                f"Your answer: {answer}",
            )

            st.session_state.nl_attention_sequence = None
            st.rerun()


def stroop_task():
    st.subheader("🎨 Stroop Control")

    if st.session_state.nl_stroop_trial is None:
        st.write(
            "Identify the INK COLOUR, not the word meaning."
        )

        if st.button("Start Stroop challenge"):
            word = random.choice(COLORS)
            ink = random.choice([c for c in COLORS if c != word])

            st.session_state.nl_stroop_trial = {
                "word": word,
                "ink": ink,
            }
            st.rerun()

    else:
        trial = st.session_state.nl_stroop_trial

        st.markdown(
            f"<h1 style='text-align:center;"
            f"color:{trial['ink'].lower()}'>"
            f"{trial['word']}</h1>",
            unsafe_allow_html=True,
        )

        answer = st.radio(
            "What is the ink colour?",
            COLORS,
            key="nl_stroop_answer",
        )

        if st.button("Submit Stroop answer"):
            correct = answer == trial["ink"]
            score = 100 if correct else 0

            st.success("Correct!") if correct else st.info(
                f"Ink colour: {trial['ink']}"
            )

            save_result(
                "Stroop Control",
                score,
                f"Selected: {answer}",
            )

            st.session_state.nl_stroop_trial = None
            st.rerun()


def pattern_task():
    st.subheader("🔢 Pattern Recognition")

    st.write("Find the next number in this sequence:")

    st.markdown("## 2 → 4 → 8 → 16 → ?")

    answer = st.radio(
        "Choose your answer",
        ["20", "24", "32", "36"],
        key="nl_pattern_answer",
    )

    if st.button("Check pattern answer"):
        correct = answer == "32"
        score = 100 if correct else 0

        st.success("Correct! Each number doubles.") if correct else (
            st.info("The correct answer is 32.")
        )

        save_result(
            "Pattern Recognition",
            score,
            f"Selected: {answer}",
        )


def decision_task():
    st.subheader("💡 Decision & Reward")

    st.write(
        "Imagine you receive two possible reward offers:"
    )

    st.markdown("""
    - Option A: Receive Rs. 1,000 today.
    - Option B: Receive Rs. 1,500 after 30 days.
    """)

    choice = st.radio(
        "Which option would you choose?",
        [
            "Option A — Rs. 1,000 today",
            "Option B — Rs. 1,500 after 30 days",
        ],
        key="nl_decision_answer",
    )

    if st.button("Save my decision"):
        save_result(
            "Decision & Reward",
            0,
            choice,
        )

        st.success(
            "Your preference has been recorded. "
            "There is no universally correct answer."
        )


def render(st):
    initialize()

    st.title("🧠 Cognitive Challenges")

    st.write(
        "Explore memory, attention, cognitive control, "
        "pattern recognition and decision-making."
    )

    task = st.selectbox(
        "Choose a challenge",
        [
            "Memory Sequence",
            "Attention",
            "Stroop Control",
            "Pattern Recognition",
            "Decision & Reward",
        ],
        key="nl_selected_challenge",
    )

    if task == "Memory Sequence":
        memory_task()

    elif task == "Attention":
        attention_task()

    elif task == "Stroop Control":
        stroop_task()

    elif task == "Pattern Recognition":
        pattern_task()

    elif task == "Decision & Reward":
        decision_task()

    st.divider()
    st.subheader("Your session results")

    results = st.session_state.nl_challenge_results

    if results:
        st.metric("Completed attempts", len(results))

        for item in reversed(results):
            st.write(
                f"**{item['task']}** — "
                f"{item['details']}"
            )
    else:
        st.caption("Your completed challenges will appear here.")

    st.caption(
        "These are educational cognitive tasks, not validated "
        "clinical assessments or direct measurements of brain activity."
    )
