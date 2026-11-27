# modules/experiments.py

import random
import time
from datetime import date

import streamlit as st


# =========================================================
# EXPERIMENT BANK
# =========================================================

EXPERIMENTS = [
    {
        "id": "working_memory",
        "title": "Working Memory Challenge",
        "category": "Working Memory",
        "description": (
            "Remember a short sequence of symbols and reproduce it "
            "after a brief delay."
        ),
        "levels": [3, 4, 5, 6, 7],
        "research_note": (
            "Working memory temporarily maintains and manipulates "
            "information needed for ongoing cognitive activity."
        ),
    },
    {
        "id": "attention",
        "title": "Selective Attention Test",
        "category": "Attention",
        "description": (
            "Identify the target stimulus while ignoring distracting "
            "information."
        ),
        "levels": [5, 6, 7, 8, 9],
        "research_note": (
            "Selective attention helps prioritize relevant information "
            "while reducing processing of competing stimuli."
        ),
    },
    {
        "id": "inhibition",
        "title": "Inhibitory Control Challenge",
        "category": "Cognitive Control",
        "description": (
            "Respond to the correct stimulus while resisting an "
            "automatic response."
        ),
        "levels": [4, 5, 6, 7, 8],
        "research_note": (
            "Inhibitory control is an executive function involved in "
            "suppressing inappropriate or prepotent responses."
        ),
    },
    {
        "id": "decision",
        "title": "Decision-Making Challenge",
        "category": "Decision Making",
        "description": (
            "Choose between options with different rewards and risks."
        ),
        "levels": [2, 3, 4, 5, 6],
        "research_note": (
            "Decision making involves interactions among valuation, "
            "learning, cognitive control, and reward-related systems."
        ),
    },
    {
        "id": "flexibility",
        "title": "Cognitive Flexibility Test",
        "category": "Cognitive Flexibility",
        "description": (
            "Switch between changing rules and adapt your responses."
        ),
        "levels": [3, 4, 5, 6, 7],
        "research_note": (
            "Cognitive flexibility allows behaviour and attention "
            "to adapt when task rules or environmental demands change."
        ),
    },
    {
        "id": "perception",
        "title": "Perception Challenge",
        "category": "Perception",
        "description": (
            "Interpret ambiguous or competing visual information."
        ),
        "levels": [3, 4, 5, 6],
        "research_note": (
            "Perception emerges from interactions between sensory "
            "information and higher-level interpretation."
        ),
    },
    {
        "id": "memory",
        "title": "Memory Recall Challenge",
        "category": "Memory",
        "description": (
            "Study information briefly and then recall it."
        ),
        "levels": [3, 4, 5, 6, 7],
        "research_note": (
            "Memory performance depends on encoding, consolidation, "
            "storage, and retrieval processes."
        ),
    },
    {
        "id": "reward",
        "title": "Reward Prediction Challenge",
        "category": "Reward",
        "description": (
            "Predict which option is more likely to produce a reward."
        ),
        "levels": [2, 3, 4, 5],
        "research_note": (
            "Reward prediction and prediction error are important "
            "concepts in reinforcement learning and decision behaviour."
        ),
    },
]


# =========================================================
# DAILY EXPERIMENT
# =========================================================

def get_daily_experiment():
    """
    Select one experiment deterministically for the day.

    This means every user sees a stable daily experiment instead
    of the experiment changing every Streamlit rerun.
    """

    day_number = date.today().toordinal()

    index = day_number % len(EXPERIMENTS)

    return EXPERIMENTS[index]


def get_experiment_by_id(experiment_id):
    for experiment in EXPERIMENTS:
        if experiment["id"] == experiment_id:
            return experiment

    return None


# =========================================================
# DIFFICULTY
# =========================================================

def get_difficulty(experiment_id):
    """
    Adaptive difficulty based on previous performance.
    """

    key = f"experiment_level_{experiment_id}"

    if key not in st.session_state:
        st.session_state[key] = 0

    return st.session_state[key]


def set_difficulty(experiment_id, level):
    experiment = get_experiment_by_id(experiment_id)

    if experiment is None:
        return

    levels = experiment.get("levels", [1])

    level = max(0, min(level, len(levels) - 1))

    st.session_state[f"experiment_level_{experiment_id}"] = level


def adapt_difficulty(experiment_id, accuracy):
    """
    Increase/decrease difficulty after a completed task.
    """

    current = get_difficulty(experiment_id)

    if accuracy >= 0.80:
        current += 1

    elif accuracy < 0.50:
        current -= 1

    set_difficulty(experiment_id, current)

    return get_difficulty(experiment_id)


# =========================================================
# SESSION STATE
# =========================================================

def initialise_experiment(experiment):
    experiment_id = experiment["id"]

    state_key = f"exp_state_{experiment_id}"

    if state_key not in st.session_state:

        st.session_state[state_key] = {
            "started": False,
            "completed": False,
            "score": 0,
            "correct": 0,
            "total": 0,
            "start_time": None,
            "reaction_times": [],
            "round": 0,
        }

    return st.session_state[state_key]


def reset_experiment(experiment_id):

    st.session_state[f"exp_state_{experiment_id}"] = {
        "started": False,
        "completed": False,
        "score": 0,
        "correct": 0,
        "total": 0,
        "start_time": None,
        "reaction_times": [],
        "round": 0,
    }


# =========================================================
# GENERATORS
# =========================================================

def generate_sequence(length):
    symbols = [
        "▲",
        "●",
        "■",
        "◆",
        "★",
        "☀",
        "☾",
        "✚",
    ]

    return random.sample(symbols, min(length, len(symbols)))


def generate_numbers(length):
    return random.sample(range(1, 10), min(length, 9))


def generate_attention_items():

    target = random.choice(
        ["RED", "BLUE", "GREEN", "YELLOW"]
    )

    distractors = [
        "RED",
        "BLUE",
        "GREEN",
        "YELLOW",
    ]

    options = [target]

    while len(options) < 4:
        options.append(random.choice(distractors))

    random.shuffle(options)

    return target, options


# =========================================================
# WORKING MEMORY
# =========================================================

def working_memory_task(level):

    length = level

    sequence = generate_sequence(length)

    state_key = "working_memory_current"

    if state_key not in st.session_state:

        st.session_state[state_key] = {
            "sequence": sequence,
            "show": True,
            "created": time.time(),
        }

    data = st.session_state[state_key]

    if data["show"]:

        elapsed = time.time() - data["created"]

        st.markdown("### 🧠 Remember this sequence")

        st.markdown(
            f"""
            <div style="
                font-size:42px;
                text-align:center;
                padding:25px;
                border-radius:20px;
                background:rgba(255,255,255,.08);
            ">
            {" ".join(data["sequence"])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if elapsed >= 3:

            data["show"] = False
            st.rerun()

        st.caption("Look carefully...")

        return None

    st.markdown("### 🔁 Reproduce the sequence")

    answer = st.text_input(
        "Enter the symbols separated by spaces",
        key="working_memory_answer",
    )

    if st.button(
        "Submit",
        key="working_memory_submit",
        use_container_width=True,
    ):

        submitted = answer.split()

        correct = submitted == data["sequence"]

        del st.session_state[state_key]

        return 1 if correct else 0

    return None


# =========================================================
# NUMBER MEMORY
# =========================================================

def memory_task(level):

    length = min(level + 1, 8)

    numbers = generate_numbers(length)

    if "memory_current" not in st.session_state:

        st.session_state["memory_current"] = {
            "numbers": numbers,
            "show": True,
            "created": time.time(),
        }

    data = st.session_state["memory_current"]

    if data["show"]:

        st.markdown("### 🔢 Memorise the numbers")

        st.markdown(
            f"""
            <div style="
                font-size:38px;
                text-align:center;
                padding:25px;
            ">
            {" • ".join(map(str, data["numbers"]))}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if time.time() - data["created"] >= 3:

            data["show"] = False
            st.rerun()

        return None

    answer = st.text_input(
        "Type the numbers in the same order",
        key="memory_answer",
    )

    if st.button(
        "Submit Recall",
        key="memory_submit",
        use_container_width=True,
    ):

        try:
            submitted = [
                int(x)
                for x in answer.replace(",", " ").split()
            ]
        except Exception:
            submitted = []

        correct = submitted == data["numbers"]

        del st.session_state["memory_current"]

        return 1 if correct else 0

    return None


# =========================================================
# ATTENTION TASK
# =========================================================

def attention_task():

    if "attention_current" not in st.session_state:

        target, options = generate_attention_items()

        st.session_state["attention_current"] = {
            "target": target,
            "options": options,
        }

    data = st.session_state["attention_current"]

    st.markdown("### 👁️ Selective Attention")

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:22px;
            padding:15px;
        ">
        Find: <strong>{data["target"]}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Choose the correct item",
        data["options"],
        key="attention_choice",
    )

    if st.button(
        "Submit Attention Response",
        key="attention_submit",
        use_container_width=True,
    ):

        correct = choice == data["target"]

        del st.session_state["attention_current"]

        return 1 if correct else 0

    return None


# =========================================================
# INHIBITORY CONTROL
# =========================================================

def inhibition_task():

    if "inhibition_current" not in st.session_state:

        words = [
            "RED",
            "BLUE",
            "GREEN",
            "YELLOW",
        ]

        word = random.choice(words)

        colour = random.choice(words)

        st.session_state["inhibition_current"] = {
            "word": word,
            "colour": colour,
        }

    data = st.session_state["inhibition_current"]

    st.markdown("### 🛑 Inhibitory Control")

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:38px;
            padding:30px;
        ">
        {data["word"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Which word did you see?",
        [
            "RED",
            "BLUE",
            "GREEN",
            "YELLOW",
        ],
        key="inhibition_choice",
    )

    if st.button(
        "Respond",
        key="inhibition_submit",
        use_container_width=True,
    ):

        correct = choice == data["word"]

        del st.session_state["inhibition_current"]

        return 1 if correct else 0

    return None


# =========================================================
# DECISION MAKING
# =========================================================

def decision_task():

    options = [
        {
            "name": "Option A",
            "reward": 10,
            "risk": "Low",
        },
        {
            "name": "Option B",
            "reward": 25,
            "risk": "Medium",
        },
        {
            "name": "Option C",
            "reward": 50,
            "risk": "High",
        },
    ]

    st.markdown("### ⚖️ Decision-Making Challenge")

    st.write(
        "Choose the option you would prefer."
    )

    choice = st.radio(
        "Your decision",
        [
            f'{x["name"]} — reward {x["reward"]}, risk {x["risk"]}'
            for x in options
        ],
        key="decision_choice",
    )

    if st.button(
        "Confirm Decision",
        key="decision_submit",
        use_container_width=True,
    ):

        selected = options[
            [
                f'{x["name"]} — reward {x["reward"]}, risk {x["risk"]}'
                for x in options
            ].index(choice)
        ]

        # This is an exploratory behavioural choice,
        # not a diagnosis or measure of personality.
        score = selected["reward"] / 50

        return score

    return None


# =========================================================
# FLEXIBILITY
# =========================================================

def flexibility_task():

    if "flexibility_rule" not in st.session_state:

        st.session_state["flexibility_rule"] = random.choice(
            ["number", "size"]
        )

    rule = st.session_state["flexibility_rule"]

    st.markdown("### 🔄 Cognitive Flexibility")

    if rule == "number":

        st.write(
            "Current rule: choose the larger number."
        )

        options = ["2", "8"]

    else:

        st.write(
            "Current rule: choose the larger symbol."
        )

        options = ["●", "●●●"]

    choice = st.radio(
        "Choose",
        options,
        key="flexibility_choice",
    )

    if st.button(
        "Submit Flexibility Response",
        key="flexibility_submit",
        use_container_width=True,
    ):

        if rule == "number":
            correct = choice == "8"
        else:
            correct = choice == "●●●"

        del st.session_state["flexibility_rule"]

        return 1 if correct else 0

    return None


# =========================================================
# EXPERIMENT DISPATCHER
# =========================================================

def run_experiment_task(experiment, level):

    experiment_id = experiment["id"]

    if experiment_id == "working_memory":
        return working_memory_task(level)

    if experiment_id == "memory":
        return memory_task(level)

    if experiment_id == "attention":
        return attention_task()

    if experiment_id == "inhibition":
        return inhibition_task()

    if experiment_id == "decision":
        return decision_task()

    if experiment_id == "flexibility":
        return flexibility_task()

    # Safe fallback for experiments that have not yet received
    # their specialised task interface.
    st.info(
        "This experiment module is being prepared. "
        "Choose another experiment to continue."
    )

    return None


# =========================================================
# RECORD RESULT
# =========================================================

def record_result(experiment, result):

    if result is None:
        return

    experiment_id = experiment["id"]

    state = initialise_experiment(experiment)

    state["total"] += 1

    if result >= 1:
        state["correct"] += 1
        state["score"] += int(result * 100)

    state["round"] += 1

    accuracy = (
        state["correct"] / state["total"]
        if state["total"] > 0
        else 0
    )

    adapt_difficulty(
        experiment_id,
        accuracy,
    )

    # Save lightweight progress locally in session.
    if "experiment_history" not in st.session_state:
        st.session_state["experiment_history"] = []

    st.session_state["experiment_history"].append(
        {
            "date": str(date.today()),
            "experiment": experiment["title"],
            "category": experiment["category"],
            "score": state["score"],
            "accuracy": round(accuracy * 100, 1),
            "level": get_difficulty(experiment_id) + 1,
        }
    )


# =========================================================
# DAILY EXPERIMENT UI
# =========================================================

def render_daily_experiment():

    experiment = get_daily_experiment()

    initialise_experiment(experiment)

    experiment_id = experiment["id"]

    st.markdown("## 🧪 Today's Cognitive Experiment")

    st.markdown(
        f"""
        <div style="
            padding:25px;
            border-radius:22px;
            background:linear-gradient(
                135deg,
                rgba(80,80,130,.35),
                rgba(20,20,40,.65)
            );
            border:1px solid rgba(255,255,255,.12);
        ">
            <h2>{experiment["title"]}</h2>
            <p><strong>Domain:</strong> {experiment["category"]}</p>
            <p>{experiment["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    level_index = get_difficulty(experiment_id)

    level_index = min(
        level_index,
        len(experiment["levels"]) - 1,
    )

    level = experiment["levels"][level_index]

    st.write(
        f"### Difficulty Level {level_index + 1}"
    )

    st.caption(
        "Complete the task and your next challenge can adapt "
        "to your performance."
    )

    if st.button(
        "🚀 Start Today's Experiment",
        key=f"start_{experiment_id}",
        use_container_width=True,
    ):

        state = initialise_experiment(experiment)

        state["started"] = True
        state["start_time"] = time.time()

        st.session_state[
            f"experiment_running_{experiment_id}"
        ] = True

        st.rerun()

    running = st.session_state.get(
        f"experiment_running_{experiment_id}",
        False,
    )

    if running:

        st.divider()

        result = run_experiment_task(
            experiment,
            level,
        )

        if result is not None:

            record_result(
                experiment,
                result,
            )

            st.success(
                "Challenge completed."
            )

            state = initialise_experiment(
                experiment
            )

            accuracy = (
                state["correct"]
                / state["total"]
                if state["total"]
                else 0
            )

            st.metric(
                "Current Accuracy",
                f"{accuracy * 100:.0f}%",
            )

            st.metric(
                "Score",
                state["score"],
            )

            st.info(
                "Your next challenge can become "
                "slightly harder or easier based on performance."
            )

            st.markdown("### 🔬 Research Note")

            st.write(
                experiment["research_note"]
            )

            if st.button(
                "➡️ Continue",
                key=f"continue_{experiment_id}",
                use_container_width=True,
            ):

                st.session_state[
                    f"experiment_running_{experiment_id}"
                ] = False

                st.rerun()


# =========================================================
# EXPERIMENT LIBRARY
# =========================================================

def render_experiment_library():

    st.markdown("## 🧪 Cognitive Experiment Library")

    for experiment in EXPERIMENTS:

        with st.expander(
            f'{experiment["title"]} — {experiment["category"]}'
        ):

            st.write(
                experiment["description"]
            )

            st.markdown(
                "**Research note:**"
            )

            st.write(
                experiment["research_note"]
            )


# =========================================================
# PROGRESS
# =========================================================

def experiment_progress():

    history = st.session_state.get(
        "experiment_history",
        [],
    )

    if not history:
        return {
            "completed": 0,
            "average_accuracy": 0,
            "total_score": 0,
        }

    accuracies = [
        item["accuracy"]
        for item in history
    ]

    scores = [
        item["score"]
        for item in history
    ]

    return {
        "completed": len(history),
        "average_accuracy": round(
            sum(accuracies) / len(accuracies),
            1,
        ),
        "total_score": sum(scores),
    }


def render_experiment_progress():

    progress = experiment_progress()

    st.markdown("## 📊 Experiment Progress")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Experiments",
            progress["completed"],
        )

    with col2:
        st.metric(
            "Average Accuracy",
            f'{progress["average_accuracy"]}%',
        )

    with col3:
        st.metric(
            "Total Score",
            progress["total_score"],
        )
