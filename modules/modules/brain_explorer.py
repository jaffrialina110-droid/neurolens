"""Interactive Brain Explorer for NeuroLens."""

BRAIN_REGIONS = {
    "Prefrontal Cortex": {
        "function": "Planning, decision-making, working memory "
                    "and cognitive control.",
        "details": "The prefrontal cortex helps us evaluate choices, "
                   "maintain goals and regulate behaviour.",
    },
    "Hippocampus": {
        "function": "Learning and formation of new memories.",
        "details": "The hippocampus plays an important role in "
                   "forming and organizing new episodic memories.",
    },
    "Striatum": {
        "function": "Action selection, reward learning and habits.",
        "details": "The striatum is involved in selecting actions "
                   "and learning from rewards and outcomes.",
    },
    "Anterior Cingulate Cortex": {
        "function": "Conflict monitoring, attention and error processing.",
        "details": "The ACC contributes to monitoring conflicts, "
                   "detecting errors and adjusting behaviour.",
    },
    "Thalamus": {
        "function": "Sensory and motor information processing.",
        "details": "The thalamus relays and processes information "
                   "between different brain regions and the cortex.",
    },
    "Amygdala": {
        "function": "Emotional learning and significance detection.",
        "details": "The amygdala contributes to processing emotionally "
                   "significant information and learning.",
    },
}


def render(st):
    st.title("🧠 Interactive Brain Explorer")

    st.write(
        "Explore important brain regions and understand "
        "their roles in cognition and behaviour."
    )

    region = st.selectbox(
        "Select a brain region",
        list(BRAIN_REGIONS.keys()),
        key="neurolens_brain_region",
    )

    information = BRAIN_REGIONS[region]

    st.subheader(region)

    st.markdown("**Main functions**")
    st.write(information["function"])

    st.markdown("**Scientific explanation**")
    st.info(information["details"])

    st.caption(
        "Educational information only. Brain regions work "
        "together in distributed networks."
    )
