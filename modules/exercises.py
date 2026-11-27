# modules/exercises.py
# NEUROLENS — Adaptive Cognitive Brain Exercises

import random
import time
import streamlit as st


EXERCISE_BANK = {
    "Attention": [
        {
            "question": "Which symbol is different?",
            "items": ["●", "●", "●", "○", "●"],
            "answer": "○",
        },
        {
            "question": "Which number appears only once?",
            "items": ["7", "3", "7", "7", "9"],
            "answer": "9",
        },
        {
            "question": "Find the different letter.",
            "items": ["A", "A", "A", "H", "A"],
            "answer": "H",
        },
    ],

    "Working Memory": [
        {
            "question": "Remember this sequence:",
            "items": ["4", "8", "2", "7"],
            "answer": "4827",
        },
        {
            "question": "Remember this sequence:",
            "items": ["9", "1", "6", "3"],
            "answer": "9163",
        },
        {
            "question": "Remember this sequence:",
            "items": ["5", "2", "8", "4", "1"],
            "answer": "52841",
        },
    ],

    "Memory": [
        {
            "question": "Which item was shown?",
            "items": ["Apple", "Chair", "Moon", "Book"],
            "answer": "Moon",
        },
        {
            "question": "Which object belongs to the previous set?",
            "items": ["Key", "Cloud", "Bottle", "Tree"],
            "answer": "Key",
        },
    ],

    "Decision Making": [
        {
            "question": "Which option gives the highest reward?",
            "items": [
                "Option A — 10 points, 90% chance",
                "Option B — 30 points, 40% chance",
                "Option C — 5 points, 100% chance",
            ],
            "answer": "Option A — 10 points, 90% chance",
        },
        {
            "question": "Which option is the safest?",
            "items": [
                "Option A — 20 points, 50% chance",
                "Option B — 8 points, 95% chance",
                "Option C — 40 points, 20% chance",
            ],
            "answer": "Option B — 8 points, 95% chance",
        },
    ],

    "Inhibitory Control": [
        {
            "question": "Select the word that matches the instruction.",
            "items": ["GO", "STOP", "GO", "GO"],
            "answer": "STOP",
        },
        {
            "question": "Choose the item that should be inhibited.",
            "items": ["TARGET", "TARGET", "DISTRACTOR", "TARGET"],
            "answer": "DISTRACTOR",
        },
    ],

    "Cognitive Flexibility": [
        {
            "question": "Switch the rule: choose the item that is now BLUE.",
            "items": ["RED", "GREEN", "BLUE", "YELLOW"],
            "answer": "BLUE",
        },
        {
            "question": "New rule: select the largest number.",
            "items": ["12", "48", "23", "31"],
            "answer": "48",
        },
    ],
}


LEVELS = {
    1: {
        "name": "Starter",
        "time": 25,
        "questions": 5,
    },
    2: {
        "name": "Focused",
        "time": 20,
        "questions": 6,
    },
    3: {
        "name": "Advanced",
        "time": 15,
        "questions": 7,
    },
    4: {
        "name": "Expert",
        "time": 12,
        "questions": 8,
    },
}


def _init_state():

    defaults = {
        "exercise_category": "Attention",
        "exercise_level": 1,
        "exercise_index": 0,
        "exercise_score": 0,
        "exercise_correct": 0,
        "exercise_total": 0,
        "exercise_started": False,
        "exercise_start_time": None,
        "exercise_current": None,
        "exercise_finished": False,
        "exercise_feedback": "",
        "exercise_history": [],
        "exercise_session_id": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _new_question():

    category = st.session_state.exercise_category

    bank = EXERCISE_BANK.get(category, EXERCISE_BANK["Attention"])

    question = random.choice(bank)

    # Copy so original bank is never modified.
    question = {
        "question": question["question"],
        "items": list(question["items"]),
        "answer": question["answer"],
    }

    random.shuffle(question["items"])

    return question


def _start_session():

    st.session_state.exercise_index = 0
    st.session_state.exercise_score = 0
    st.session_state.exercise_correct = 0
    st.session_state.exercise_total = 0
    st.session_state.exercise_started = True
    st.session_state.exercise_start_time = time.time()
    st.session_state.exercise_current = _new_question()
    st.session_state.exercise_finished = False
    st.session_state.exercise_feedback = ""
    st.session_state.exercise_session_id += 1


def _finish_session():

    st.session_state.exercise_finished = True
    st.session_state.exercise_started = False

    accuracy = 0

    if st.session_state.exercise_total > 0:
        accuracy = round(
            (
                st.session_state.exercise_correct
                / st.session_state.exercise_total
            )
            * 100
        )

    elapsed = 0

    if st.session_state.exercise_start_time:
        elapsed = round(
            time.time()
            - st.session_state.exercise_start_time
        )

    result = {
        "category": st.session_state.exercise_category,
        "level": st.session_state.exercise_level,
        "score": st.session_state.exercise_score,
        "correct": st.session_state.exercise_correct,
        "total": st.session_state.exercise_total,
        "accuracy": accuracy,
        "time": elapsed,
        "timestamp": time.strftime(
            "%Y-%m-%d %H:%M"
        ),
    }

    st.session_state.exercise_history.append(result)

    # Keep only recent results in session memory.
    st.session_state.exercise_history = (
        st.session_state.exercise_history[-30:]
    )


def _submit_answer(answer):

    question = st.session_state.exercise_current

    if not question:
        return

    st.session_state.exercise_total += 1

    if answer == question["answer"]:

        st.session_state.exercise_correct += 1

        # Base score.
        points = 100

        # Faster answers receive a small bonus.
        if st.session_state.exercise_start_time:

            elapsed = time.time() - st.session_state.exercise_start_time

            if elapsed <= 5:
                points += 30

            elif elapsed <= 10:
                points += 15

        st.session_state.exercise_score += points

        st.session_state.exercise_feedback = (
            "✅ Correct! Your cognitive response was accurate."
        )

    else:

        st.session_state.exercise_feedback = (
            "❌ Not quite. The next challenge will help you practice."
        )

    st.session_state.exercise_index += 1

    total_questions = LEVELS[
        st.session_state.exercise_level
    ]["questions"]

    if st.session_state.exercise_index >= total_questions:

        _finish_session()

    else:

        st.session_state.exercise_current = _new_question()
        st.session_state.exercise_start_time = time.time()


def _adaptive_level():

    history = st.session_state.exercise_history

    if not history:
        return 1

    recent = history[-3:]

    accuracies = [
        item["accuracy"]
        for item in recent
    ]

    average = sum(accuracies) / len(accuracies)

    current = st.session_state.exercise_level

    if average >= 85 and current < 4:
        return current + 1

    if average < 50 and current > 1:
        return current - 1

    return current


def _progress_metrics():

    history = st.session_state.exercise_history

    if not history:
        return {
            "sessions": 0,
            "accuracy": 0,
            "score": 0,
        }

    total_correct = sum(
        item["correct"]
        for item in history
    )

    total_questions = sum(
        item["total"]
        for item in history
    )

    total_score = sum(
        item["score"]
        for item in history
    )

    accuracy = 0

    if total_questions:
        accuracy = round(
            total_correct
            / total_questions
            * 100
        )

    return {
        "sessions": len(history),
        "accuracy": accuracy,
        "score": total_score,
    }


def exercises_screen():

    _init_state()

    st.markdown(
        """
        <style>

        .exercise-title {
            font-size: 34px;
            font-weight: 800;
            margin-bottom: 5px;
        }

        .exercise-subtitle {
            color: #9ca3af;
            margin-bottom: 20px;
        }

        .exercise-card {
            padding: 22px;
            border-radius: 20px;
            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,.06),
                    rgba(255,255,255,.025)
                );
            border: 1px solid rgba(255,255,255,.10);
            margin-bottom: 18px;
        }

        .exercise-question {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 15px;
        }

        .exercise-info {
            color: #aeb7c4;
            font-size: 14px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="exercise-title">'
        '🧠 AI Brain Exercises'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="exercise-subtitle">'
        'Train attention, memory, decision-making, '
        'inhibitory control and cognitive flexibility.'
        '</div>',
        unsafe_allow_html=True,
    )

    metrics = _progress_metrics()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Sessions",
            metrics["sessions"],
        )

    with c2:
        st.metric(
            "Accuracy",
            f'{metrics["accuracy"]}%',
        )

    with c3:
        st.metric(
            "Total Score",
            metrics["score"],
        )

    st.markdown("---")

    # -------------------------------
    # EXERCISE SETTINGS
    # -------------------------------

    category = st.selectbox(
        "Choose cognitive system",
        list(EXERCISE_BANK.keys()),
        index=list(EXERCISE_BANK.keys()).index(
            st.session_state.exercise_category
        ),
        key="exercise_category_control",
    )

    if category != st.session_state.exercise_category:

        st.session_state.exercise_category = category

        st.session_state.exercise_started = False
        st.session_state.exercise_finished = False
        st.session_state.exercise_current = None

    level_options = {
        f"Level {number} — {data['name']}": number
        for number, data in LEVELS.items()
    }

    selected_label = st.selectbox(
        "Difficulty",
        list(level_options.keys()),
        index=st.session_state.exercise_level - 1,
        key="exercise_level_control",
    )

    selected_level = level_options[selected_label]

    if selected_level != st.session_state.exercise_level:

        st.session_state.exercise_level = selected_level
        st.session_state.exercise_started = False
        st.session_state.exercise_finished = False
        st.session_state.exercise_current = None

    # -------------------------------
    # START
    # -------------------------------

    if not st.session_state.exercise_started:

        if not st.session_state.exercise_finished:

            st.info(
                "Choose a cognitive system and start "
                "your training session."
            )

            if st.button(
                "🚀 Start Brain Exercise",
                use_container_width=True,
                type="primary",
            ):
                _start_session()
                st.rerun()

        else:

            result = (
                st.session_state.exercise_history[-1]
                if st.session_state.exercise_history
                else None
            )

            if result:

                st.markdown(
                    '<div class="exercise-card">',
                    unsafe_allow_html=True,
                )

                st.subheader(
                    "🎉 Exercise Complete"
                )

                st.write(
                    f"**Accuracy:** "
                    f"{result['accuracy']}%"
                )

                st.write(
                    f"**Correct:** "
                    f"{result['correct']} / "
                    f"{result['total']}"
                )

                st.write(
                    f"**Score:** "
                    f"{result['score']}"
                )

                st.write(
                    f"**Time:** "
                    f"{result['time']} seconds"
                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )

            adaptive = _adaptive_level()

            if adaptive != st.session_state.exercise_level:

                if adaptive > st.session_state.exercise_level:

                    st.success(
                        "🧠 Strong performance! "
                        "Your next recommended level is "
                        f"Level {adaptive}."
                    )

                else:

                    st.info(
                        "Your next recommended level is "
                        f"Level {adaptive} so you can "
                        "strengthen the skill."
                    )

                if st.button(
                    f"Continue at Level {adaptive}",
                    use_container_width=True,
                ):

                    st.session_state.exercise_level = adaptive
                    st.session_state.exercise_finished = False
                    st.session_state.exercise_started = False
                    st.session_state.exercise_current = None
                    st.rerun()

            if st.button(
                "🔄 Start Again",
                use_container_width=True,
            ):

                _start_session()
                st.rerun()

        return

    # -------------------------------
    # ACTIVE EXERCISE
    # -------------------------------

    question = st.session_state.exercise_current

    if not question:
        _start_session()
        st.rerun()
        return

    level_data = LEVELS[
        st.session_state.exercise_level
    ]

    question_number = (
        st.session_state.exercise_index + 1
    )

    total_questions = level_data["questions"]

    elapsed = 0

    if st.session_state.exercise_start_time:

        elapsed = round(
            time.time()
            - st.session_state.exercise_start_time
        )

    remaining = max(
        0,
        level_data["time"] - elapsed,
    )

    st.markdown(
        f"""
        <div class="exercise-card">

        <div class="exercise-info">
        {st.session_state.exercise_category}
        &nbsp; • &nbsp;
        Level {st.session_state.exercise_level}
        &nbsp; • &nbsp;
        Question {question_number}/{total_questions}
        </div>

        <div class="exercise-question">
        {question["question"]}
        </div>

        <div class="exercise-info">
        ⏱️ Time remaining: {remaining}s
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # Time limit.
    if remaining <= 0:

        st.warning(
            "⏱️ Time is up. Moving to the next challenge."
        )

        st.session_state.exercise_total += 1
        st.session_state.exercise_index += 1

        if (
            st.session_state.exercise_index
            >= total_questions
        ):

            _finish_session()

        else:

            st.session_state.exercise_current = _new_question()
            st.session_state.exercise_start_time = time.time()

        st.rerun()

    # -------------------------------
    # ANSWERS
    # -------------------------------

    for item_index, item in enumerate(
        question["items"]
    ):

        if st.button(
            item,
            key=(
                "exercise_answer_"
                f"{st.session_state.exercise_session_id}_"
                f"{st.session_state.exercise_index}_"
                f"{item_index}"
            ),
            use_container_width=True,
        ):

            _submit_answer(item)
            st.rerun()

    if st.session_state.exercise_feedback:

        st.markdown("---")

        st.write(
            st.session_state.exercise_feedback
        )

    # Small auto-refresh so timer stays active.
    components = None

    try:
        import streamlit.components.v1 as components

        components.html(
            """
            <script>
            setTimeout(function() {
                window.parent.location.reload();
            }, 1000);
            </script>
            """,
            height=1,
        )

    except Exception:
        pass


def render():
    exercises_screen()
