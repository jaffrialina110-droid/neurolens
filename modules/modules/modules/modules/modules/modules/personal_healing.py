
"""NeuroLens — Personal Healing and Reflection."""

import streamlit as st


MOODS = [
    "Calm",
    "Happy",
    "Stressed",
    "Anxious",
    "Sad",
    "Overwhelmed",
    "Not sure",
]

EXERCISES = {
    "Grounding exercise": [
        "Notice 5 things you can see.",
        "Notice 4 things you can feel.",
        "Notice 3 things you can hear.",
        "Notice 2 things you can smell.",
        "Notice 1 thing you can taste.",
    ],
    "Gentle breathing": [
        "Sit comfortably and relax your shoulders.",
        "Breathe in gently for 4 seconds.",
        "Breathe out slowly for 6 seconds.",
        "Repeat at a comfortable pace.",
        "Stop if you feel dizzy or uncomfortable.",
    ],
    "Thought reflection": [
        "What happened?",
        "What thought came into your mind?",
        "What emotion did you notice?",
        "What might be another way to understand the situation?",
        "What small helpful step can you take?",
    ],
}


def render(st):
    st.title("💜 Personal Healing")

    st.write(
        "A private space for self-reflection, emotional awareness "
        "and gentle wellbeing exercises."
    )

    st.info(
        "This space provides educational wellbeing support. "
        "It is not therapy, diagnosis or medical treatment."
    )

    st.subheader("How are you feeling today?")

    mood = st.selectbox(
        "Choose the feeling that best describes this moment",
        MOODS,
        key="nl_healing_mood",
    )

    reflection = st.text_area(
        "Would you like to describe what's on your mind?",
        placeholder="Write only what you feel comfortable sharing...",
        height=130,
        key="nl_healing_reflection",
    )

    st.caption(
        "Your reflection remains in this active session. "
        "Do not enter highly sensitive information here."
    )

    st.divider()
    st.subheader("Guided exercises")

    exercise = st.selectbox(
        "Choose an exercise",
        list(EXERCISES.keys()),
        key="nl_healing_exercise",
    )

    with st.container(border=True):
        st.markdown(f"### {exercise}")

        for index, instruction in enumerate(
            EXERCISES[exercise], start=1
        ):
            st.markdown(f"**{index}.** {instruction}")

    st.divider()
    st.subheader("A gentle reminder")

    reminders = {
        "Calm": "Allow yourself to enjoy this peaceful moment.",
        "Happy": "Notice what is contributing to your happiness.",
        "Stressed": "You can break a difficult task into smaller steps.",
        "Anxious": "Focus on what is within your control right now.",
        "Sad": "You deserve kindness and support, even on difficult days.",
        "Overwhelmed": "You do not have to solve everything at once.",
        "Not sure": "It is okay not to have a clear answer right now.",
    }

    st.success(reminders[mood])

    if st.button("Save reflection in this session"):
        if not reflection.strip():
            st.warning("Write a reflection before saving.")
        else:
            if "nl_healing_entries" not in st.session_state:
                st.session_state.nl_healing_entries = []

            st.session_state.nl_healing_entries.append({
                "mood": mood,
                "reflection": reflection.strip(),
            })

            st.success("Reflection saved in this session.")

    st.divider()

    entries = st.session_state.get("nl_healing_entries", [])

    st.subheader("My session reflections")

    if entries:
        for index, entry in enumerate(reversed(entries), start=1):
            with st.expander(f"Reflection {index} — {entry['mood']}"):
                st.write(entry["reflection"])
    else:
        st.caption("No reflections saved in this session.")

    st.warning(
        "If you feel unsafe or may hurt yourself, contact a trusted "
        "person and local emergency or professional support immediately."
    )
