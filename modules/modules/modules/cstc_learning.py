
"""NeuroLens CSTC Circuit Learning — Structural Stage."""

import streamlit as st


PATHWAYS = {
    "Direct pathway": {
        "purpose": "Facilitates selected actions.",
        "steps": [
            "Cortex excites the striatum (glutamate, +).",
            "D1 striatal neurons inhibit GPi/SNr (GABA, -).",
            "GPi/SNr inhibition of the thalamus decreases.",
            "Thalamic excitation of the cortex increases.",
        ],
        "diagram": """
digraph Direct {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#EDE7F6"];
  Cortex -> Striatum [label=" + Glutamate"];
  Striatum -> GPi [label=" - GABA (D1)"];
  GPi -> Thalamus [label=" - GABA"];
  Thalamus -> Cortex [label=" + Glutamate"];
}
""",
    },
    "Indirect pathway": {
        "purpose": "Helps suppress competing or unwanted actions.",
        "steps": [
            "Cortex excites the striatum (glutamate, +).",
            "D2 striatal neurons inhibit GPe (GABA, -).",
            "Reduced GPe activity decreases its inhibition of STN.",
            "STN excites GPi/SNr (glutamate, +).",
            "GPi/SNr increases inhibition of the thalamus.",
        ],
        "diagram": """
digraph Indirect {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#E0F2F1"];
  Cortex -> Striatum [label=" + Glutamate"];
  Striatum -> GPe [label=" - GABA (D2)"];
  GPe -> STN [label=" - GABA"];
  STN -> GPi [label=" + Glutamate"];
  GPi -> Thalamus [label=" - GABA"];
  Thalamus -> Cortex [label=" + Glutamate"];
}
""",
    },
    "Hyperdirect pathway": {
        "purpose": "Provides a rapid route for influencing action suppression.",
        "steps": [
            "Cortex directly excites the STN (glutamate, +).",
            "STN excites GPi/SNr (glutamate, +).",
            "GPi/SNr increases inhibition of the thalamus.",
        ],
        "diagram": """
digraph Hyperdirect {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#E3F2FD"];
  Cortex -> STN [label=" + Glutamate"];
  STN -> GPi [label=" + Glutamate"];
  GPi -> Thalamus [label=" - GABA"];
}
""",
    },
}


def render(st):
    st.title("🧠 CSTC Circuit Learning")

    st.write(
        "Explore the cortico-striato-thalamo-cortical "
        "circuit through its three major pathways."
    )

    pathway_name = st.selectbox(
        "Choose a pathway",
        list(PATHWAYS.keys()),
        key="neurolens_cstc_pathway",
    )

    pathway = PATHWAYS[pathway_name]

    st.subheader(pathway_name)
    st.info(pathway["purpose"])

    st.markdown("### Circuit diagram")

    st.graphviz_chart(
        pathway["diagram"],
        use_container_width=True,
    )

    st.markdown("### Step-by-step circuit flow")

    for index, step in enumerate(pathway["steps"], start=1):
        st.markdown(f"**{index}.** {step}")

    st.caption(
        "Educational structural overview. Circuit activity is "
        "more complex than these simplified pathway diagrams. "
        "The functional and molecular layers will be developed "
        "separately."
    )
