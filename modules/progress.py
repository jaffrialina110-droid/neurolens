# modules/progress.py
# NEUROLENS — My Progress Dashboard

import streamlit as st
from datetime import date


def _init_progress():

    defaults = {
        "nl_experiments_completed": 0,
        "nl_puzzle_completed": 0,
        "nl_puzzle_best_score": 0,
        "nl_exercise_sessions": 0,
        "nl_exercise_correct": 0,
        "nl_exercise_total": 0,
        "nl_research_completed": [],
        "nl_daily_visits": [],
        "nl_activity_history": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Record today's visit once.
    today = str(date.today())

    if today not in st.session_state.nl_daily_visits:
        st.session_state.nl_daily_visits.append(today)


def _accuracy():

    total = st.session_state.nl_exercise_total

    if total <= 0:
        return 0

    return round(
        st.session_state.nl_exercise_correct
        / total
        * 100
    )


def _streak():

    visits = set(
        st.session_state.nl_daily_visits
    )

    if not visits:
        return 0

    current = date.today()
    streak = 0

    while str(current) in visits:

        streak += 1

        from datetime import timedelta

        current -= timedelta(days=1)

    return streak


def _overall_level():

    points = 0

    points += (
        st.session_state.nl_experiments_completed
        * 100
    )

    points += (
        st.session_state.nl_puzzle_completed
        * 75
    )

    points += (
        st.session_state.nl_exercise_sessions
        * 100
    )

    points += (
        len(st.session_state.nl_research_completed)
        * 50
    )

    if points < 250:
        return 1, "Neural Explorer"

    if points < 750:
        return 2, "Cognitive Explorer"

    if points < 1500:
        return 3, "Neuroscience Learner"

    if points < 3000:
        return 4, "Cognitive Researcher"

    return 5, "NeuroLens Master"


def _activity_score():

    experiments = (
        st.session_state.nl_experiments_completed
    )

    puzzles = (
        st.session_state.nl_puzzle_completed
    )

    exercises = (
        st.session_state.nl_exercise_sessions
    )

    research = len(
        st.session_state.nl_research_completed
    )

    return (
        experiments * 100
        + puzzles * 75
        + exercises * 100
        + research * 50
    )


def _progress_to_next_level():

    level, _ = _overall_level()

    thresholds = {
        1: (0, 250),
        2: (250, 750),
        3: (750, 1500),
        4: (1500, 3000),
        5: (3000, 5000),
    }

    if level >= 5:
        return 1.0

    low, high = thresholds[level]

    score = _activity_score()

    progress = (
        score - low
    ) / (
        high - low
    )

    return max(
        0.0,
        min(1.0, progress),
    )


def _record_activity(
    activity,
    details=None,
):

    if details is None:
        details = {}

    entry = {
        "date": str(date.today()),
        "activity": activity,
        "details": details,
    }

    st.session_state.nl_activity_history.append(
        entry
    )

    # Keep the session lightweight.
    st.session_state.nl_activity_history = (
        st.session_state.nl_activity_history[-100:]
    )


def record_experiment():

    _init_progress()

    st.session_state.nl_experiments_completed += 1

    _record_activity(
        "Daily Experiment"
    )


def record_puzzle(score=0):

    _init_progress()

    st.session_state.nl_puzzle_completed += 1

    if score > st.session_state.nl_puzzle_best_score:
        st.session_state.nl_puzzle_best_score = score

    _record_activity(
        "Brain Puzzle",
        {
            "score": score,
        },
    )


def record_exercise(
    correct,
    total,
):

    _init_progress()

    st.session_state.nl_exercise_sessions += 1

    st.session_state.nl_exercise_correct += correct

    st.session_state.nl_exercise_total += total

    _record_activity(
        "Brain Exercise",
        {
            "correct": correct,
            "total": total,
        },
    )


def record_research_topic(topic):

    _init_progress()

    if topic not in st.session_state.nl_research_completed:

        st.session_state.nl_research_completed.append(
            topic
        )

        _record_activity(
            "Research Topic",
            {
                "topic": topic,
            },
        )


def progress_screen():

    _init_progress()

    level, level_name = _overall_level()

    accuracy = _accuracy()

    streak = _streak()

    score = _activity_score()

    progress = _progress_to_next_level()

    st.markdown(
        """
        <style>

        .progress-title {
            font-size: 36px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .progress-subtitle {
            color: #9ca3af;
            margin-bottom: 22px;
        }

        .progress-card {
            padding: 20px;
            border-radius: 20px;
            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,.065),
                    rgba(255,255,255,.025)
                );
            border:
                1px solid rgba(255,255,255,.10);
            margin-bottom: 18px;
        }

        .level-number {
            font-size: 44px;
            font-weight: 900;
        }

        .level-name {
            font-size: 19px;
            font-weight: 700;
        }

        .activity-row {
            padding: 12px;
            margin: 7px 0;
            border-radius: 12px;
            background: rgba(255,255,255,.04);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="progress-title">
            📊 My Progress
        </div>

        <div class="progress-subtitle">
            Track your cognitive exploration across NEUROLENS.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------
    # LEVEL CARD
    # --------------------------------

    st.markdown(
        '<div class="progress-card">',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 2])

    with c1:

        st.markdown(
            f"""
            <div class="level-number">
                {level}
            </div>

            <div class="level-name">
                {level_name}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.write(
            f"Overall cognitive activity score: **{score}**"
        )

        st.progress(
            progress
        )

        if level < 5:

            st.caption(
                "Keep exploring to unlock the next level."
            )

        else:

            st.success(
                "🏆 Maximum NEUROLENS level reached!"
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------
    # MAIN METRICS
    # --------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "🧪 Experiments",
            st.session_state.nl_experiments_completed,
        )

    with c2:

        st.metric(
            "🧩 Puzzles",
            st.session_state.nl_puzzle_completed,
        )

    with c3:

        st.metric(
            "🧠 Exercise Accuracy",
            f"{accuracy}%",
        )

    with c4:

        st.metric(
            "🔥 Streak",
            f"{streak} days",
        )

    st.markdown("---")

    # --------------------------------
    # BRAIN PUZZLE
    # --------------------------------

    st.markdown(
        '<div class="progress-card">',
        unsafe_allow_html=True,
    )

    st.subheader(
        "🧩 Brain Puzzle"
    )

    p1, p2 = st.columns(2)

    with p1:

        st.write(
            "Completed puzzles"
        )

        st.write(
            f"### {st.session_state.nl_puzzle_completed}"
        )

    with p2:

        st.write(
            "Best score"
        )

        st.write(
            f"### {st.session_state.nl_puzzle_best_score}"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------
    # EXERCISE PERFORMANCE
    # --------------------------------

    st.markdown(
        '<div class="progress-card">',
        unsafe_allow_html=True,
    )

    st.subheader(
        "🧠 Cognitive Exercise Performance"
    )

    e1, e2, e3 = st.columns(3)

    with e1:

        st.metric(
            "Sessions",
            st.session_state.nl_exercise_sessions,
        )

    with e2:

        st.metric(
            "Correct",
            st.session_state.nl_exercise_correct,
        )

    with e3:

        st.metric(
            "Questions",
            st.session_state.nl_exercise_total,
        )

    if st.session_state.nl_exercise_total > 0:

        st.write(
            f"Overall accuracy: **{accuracy}%**"
        )

        st.progress(
            accuracy / 100
        )

    else:

        st.info(
            "Complete a Brain Exercise to see performance data."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------
    # RESEARCH
    # --------------------------------

    st.markdown(
        '<div class="progress-card">',
        unsafe_allow_html=True,
    )

    st.subheader(
        "📚 Research Progress"
    )

    research_count = len(
        st.session_state.nl_research_completed
    )

    st.metric(
        "Topics explored",
        research_count,
    )

    if research_count:

        for topic in (
            st.session_state.nl_research_completed
        ):

            st.markdown(
                f"""
                <div class="activity-row">
                    ✅ {topic}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "Explore topics in the Research Book "
            "to build your research library."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------
    # DAILY STREAK
    # --------------------------------

    st.markdown(
        '<div class="progress-card">',
        unsafe_allow_html=True,
    )

    st.subheader(
        "🔥 Activity Streak"
    )

    st.write(
        f"Current streak: **{streak} day(s)**"
    )

    if streak >= 7:

        st.success(
            "🔥 One week of continuous exploration!"
        )

    elif streak >= 3:

        st.info(
            "Great consistency. Keep going!"
        )

    else:

        st.write(
            "Return regularly to build your streak."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------
    # RECENT ACTIVITY
    # --------------------------------

    st.markdown(
        '<div class="progress-card">',
        unsafe_allow_html=True,
    )

    st.subheader(
        "🕘 Recent Activity"
    )

    history = (
        st.session_state.nl_activity_history
    )

    if not history:

        st.info(
            "Your activity will appear here."
        )

    else:

        for item in reversed(history[-15:]):

            activity = item.get(
                "activity",
                "Activity",
            )

            activity_date = item.get(
                "date",
                "",
            )

            st.markdown(
                f"""
                <div class="activity-row">
                    <b>{activity}</b>
                    <br>
                    <small>{activity_date}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------
    # RESET
    # --------------------------------

    st.markdown("---")

    with st.expander(
        "⚙️ Progress controls"
    ):

        st.warning(
            "Resetting progress removes the current "
            "session's progress."
        )

        if st.button(
            "Reset My Progress",
            use_container_width=True,
        ):

            keys = [
                "nl_experiments_completed",
                "nl_puzzle_completed",
                "nl_puzzle_best_score",
                "nl_exercise_sessions",
                "nl_exercise_correct",
                "nl_exercise_total",
                "nl_research_completed",
                "nl_daily_visits",
                "nl_activity_history",
            ]

            for key in keys:

                if key in st.session_state:
                    del st.session_state[key]

            st.rerun()


def render():
    progress_screen()
