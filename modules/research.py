# modules/research.py
# NEUROLENS — Cognitive Neuroscience Research Book

import streamlit as st


RESEARCH_TOPICS = {
    "Brain & Behaviour": {
        "simple": """
The brain controls and coordinates behaviour through networks of
neurons and brain regions. Behaviour is influenced by perception,
memory, emotion, learning, motivation and decision-making.
""",
        "research": """
Cognitive neuroscience examines how neural systems generate
observable behaviour and cognition. Behaviour is not usually
localized to a single brain region; distributed networks,
connectivity and interactions between cortical and subcortical
systems contribute to complex behaviour.

Key concepts:
• neural circuits
• cognitive control
• executive function
• perception-action coupling
• reinforcement learning
• decision processes
""",
        "notes": [
            "Behaviour emerges from interactions between neural systems.",
            "The same brain region can contribute to multiple cognitive functions.",
            "Cognitive neuroscience combines behavioural and neural measurements.",
        ],
        "references": [
            "Cognitive Neuroscience — Gazzaniga, Ivry & Mangun",
            "Principles of Neural Science — Kandel et al.",
        ],
    },

    "Memory": {
        "simple": """
Memory allows the brain to encode, store and retrieve information.
Different forms of memory rely on partially different neural
systems.
""",
        "research": """
Major memory systems include working memory, episodic memory,
semantic memory, procedural learning and conditioning.

The hippocampal formation is strongly associated with episodic
memory formation and spatial memory. Prefrontal systems contribute
to strategic encoding, retrieval and working-memory control.

Memory is dynamic rather than a perfect recording of the past.
""",
        "notes": [
            "Encoding converts information into a form that can be retained.",
            "Retrieval reconstructs information using stored representations and context.",
            "Memory can be modified during reconsolidation.",
        ],
        "references": [
            "Squire LR. Memory systems of the brain.",
            "Eichenbaum H. The hippocampus and declarative memory.",
        ],
    },

    "Attention": {
        "simple": """
Attention helps the brain select information that is currently
important while reducing interference from competing information.
""",
        "research": """
Attention involves interacting systems including frontoparietal
networks, sensory cortices and subcortical structures.

Selective attention can enhance processing of relevant information,
while inhibitory mechanisms can reduce processing of distractors.

Attention is closely linked with working memory and cognitive control.
""",
        "notes": [
            "Attention is limited in capacity.",
            "Top-down attention is influenced by goals.",
            "Bottom-up attention can be captured by salient stimuli.",
        ],
        "references": [
            "Posner MI. Orienting of attention.",
            "Corbetta M & Shulman GL. Control of goal-directed and stimulus-driven attention.",
        ],
    },

    "Perception": {
        "simple": """
Perception is the brain's process of interpreting sensory signals.
What we perceive is influenced by both incoming information and
previous knowledge.
""",
        "research": """
Perception involves hierarchical and recurrent processing across
sensory and association cortices.

Bottom-up sensory information interacts with top-down predictions,
attention and prior experience. This interaction helps explain
perceptual illusions and context-dependent perception.
""",
        "notes": [
            "Sensory input does not automatically equal conscious perception.",
            "Context can alter perceptual interpretation.",
            "Perception involves distributed neural processing.",
        ],
        "references": [
            "Purves et al. Neuroscience",
            "Friston K. The free-energy principle and predictive processing.",
        ],
    },

    "Emotion": {
        "simple": """
Emotion involves changes in brain activity, body state, attention,
memory and behaviour.
""",
        "research": """
Emotion is supported by distributed neural systems rather than a
single 'emotion centre'.

The amygdala contributes to threat and emotional salience processing,
while prefrontal and anterior cingulate systems contribute to
regulation, evaluation and cognitive control.

Autonomic and hormonal systems also interact with brain processes.
""",
        "notes": [
            "Emotional processing can influence attention and memory.",
            "Emotion regulation involves cognitive control systems.",
            "The amygdala is involved in multiple forms of emotional processing.",
        ],
        "references": [
            "LeDoux JE. Emotion circuits in the brain.",
            "Pessoa L. On the relationship between emotion and cognition.",
        ],
    },

    "Decision Making": {
        "simple": """
Decision-making is the process of selecting between alternatives.
The brain combines information about rewards, risks, previous
experience and current goals.
""",
        "research": """
Decision-making engages distributed cortico-striatal and
frontoparietal systems.

The prefrontal cortex contributes to goal representation and
control, while striatal circuits are important for reward learning
and action selection.

Decision behaviour can be studied using choices, reaction times,
confidence ratings and computational models.
""",
        "notes": [
            "Decision-making is influenced by expected value.",
            "Risk and uncertainty can alter choice behaviour.",
            "Past rewards influence future decisions.",
        ],
        "references": [
            "Rangel A, Camerer C & Montague PR. A framework for studying the neurobiology of value-based decision making.",
            "Daw ND. Trial-by-trial data analysis using computational models.",
        ],
    },

    "Learning": {
        "simple": """
Learning changes behaviour or knowledge as a result of experience.
Repeated practice can strengthen useful patterns and skills.
""",
        "research": """
Learning involves changes in synaptic strength, network activity
and behaviour.

Reinforcement learning models describe how prediction errors can
update expectations about rewards and actions. Dopaminergic
midbrain-striatal systems are particularly important in reward
learning.
""",
        "notes": [
            "Prediction error can drive learning.",
            "Practice can change performance and neural representations.",
            "Different learning systems support different behaviours.",
        ],
        "references": [
            "Schultz W. Dopamine reward prediction-error signalling.",
            "Dayan P & Abbott LF. Theoretical Neuroscience.",
        ],
    },

    "Cognitive Control": {
        "simple": """
Cognitive control helps you stay focused on a goal, ignore
distractions and change your response when necessary.
""",
        "research": """
Cognitive control involves interacting prefrontal, anterior
cingulate and frontoparietal systems.

Important processes include response inhibition, conflict
monitoring, task switching, working-memory maintenance and
goal-directed behaviour.
""",
        "notes": [
            "Control is strongly influenced by current goals.",
            "Conflict monitoring can signal the need for increased control.",
            "Cognitive control is adaptive rather than completely fixed.",
        ],
        "references": [
            "Botvinick MM et al. Conflict monitoring and cognitive control.",
            "Miller EK & Cohen JD. An integrative theory of prefrontal cortex function.",
        ],
    },

    "Reward": {
        "simple": """
Reward systems help the brain learn which actions or events are
valuable and influence motivation.
""",
        "research": """
Reward processing involves distributed circuits including the
ventral striatum, orbitofrontal cortex, medial prefrontal regions
and dopaminergic midbrain systems.

Reward prediction errors are central to many computational models
of reinforcement learning.
""",
        "notes": [
            "Reward is not identical to pleasure.",
            "Motivation and reward learning involve overlapping but distinct processes.",
            "Prediction errors help update future expectations.",
        ],
        "references": [
            "Schultz W. Multiple dopamine functions at different time courses.",
            "Berridge KC & Kringelbach ML. Pleasure systems in the brain.",
        ],
    },

    "Executive Functions": {
        "simple": """
Executive functions help us plan, remember goals, control impulses
and solve problems.
""",
        "research": """
Executive functions include working-memory updating, inhibition and
cognitive flexibility. These processes interact within large-scale
prefrontal and frontoparietal networks.

Executive control is particularly important when automatic responses
conflict with current goals.
""",
        "notes": [
            "Executive functions are related but separable processes.",
            "Working memory supports active goal representation.",
            "Inhibition can suppress prepotent responses.",
        ],
        "references": [
            "Miyake A et al. The unity and diversity of executive functions.",
            "Diamond A. Executive functions.",
        ],
    },

    "Neuroplasticity": {
        "simple": """
Neuroplasticity means that the nervous system can change with
experience, learning and environmental demands.
""",
        "research": """
Plasticity can occur at synaptic, cellular, circuit and systems
levels. Long-term potentiation and long-term depression are examples
of mechanisms associated with changes in synaptic efficacy.

Plasticity is not always beneficial; neural systems can adapt to
both useful and harmful experiences.
""",
        "notes": [
            "Learning can modify neural circuits.",
            "Plasticity occurs throughout life, although its mechanisms vary with age.",
            "Experience-dependent changes can occur at multiple levels.",
        ],
        "references": [
            "Hebb DO. The Organization of Behavior.",
            "Kandel ER. The molecular biology of memory storage.",
        ],
    },

    "Neural Circuits": {
        "simple": """
Neural circuits are groups of connected neurons that work together
to process information and influence behaviour.
""",
        "research": """
Cognitive functions often depend on recurrent interactions between
cortical and subcortical circuits.

Important examples include cortico-striato-thalamo-cortical loops,
hippocampal networks and frontoparietal control systems.
""",
        "notes": [
            "Neural circuits can contain feedback loops.",
            "Connectivity does not automatically prove causation.",
            "Circuit function depends on both structure and activity.",
        ],
        "references": [
            "Alexander GE, DeLong MR & Strick PL. Parallel organization of functionally segregated circuits.",
            "Pessoa L. Understanding brain networks and cognition.",
        ],
    },

    "Neurotransmitters": {
        "simple": """
Neurotransmitters are chemical messengers released by neurons to
communicate with other cells.
""",
        "research": """
Major neurotransmitter systems include glutamate, GABA, dopamine,
serotonin, acetylcholine and norepinephrine.

Their effects depend on receptor type, anatomical location,
circuit context and timing. A neurotransmitter should therefore
not be described as simply producing one emotion or behaviour.
""",
        "notes": [
            "Glutamate is the major excitatory neurotransmitter in the CNS.",
            "GABA is the major inhibitory neurotransmitter in the CNS.",
            "Dopamine has roles in movement, motivation and reinforcement learning.",
        ],
        "references": [
            "Kandel et al. Principles of Neural Science.",
            "Bear, Connors & Paradiso. Neuroscience: Exploring the Brain.",
        ],
    },
}


def _topic_summary(topic):
    data = RESEARCH_TOPICS.get(topic)

    if not data:
        return {
            "simple": "Research information is currently unavailable.",
            "research": "Research information is currently unavailable.",
            "notes": [],
            "references": [],
        }

    return data


def research_screen():

    st.markdown(
        """
        <style>

        .research-title {
            font-size: 34px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .research-subtitle {
            color: #9ca3af;
            margin-bottom: 20px;
        }

        .research-card {
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

        .research-note {
            padding: 14px 16px;
            border-left: 3px solid rgba(120,180,255,.7);
            background: rgba(255,255,255,.035);
            border-radius: 8px;
            margin: 8px 0;
        }

        .mode-box {
            padding: 12px;
            border-radius: 12px;
            background: rgba(255,255,255,.04);
            margin-bottom: 12px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="research-title">📖 '
        'Cognitive Neuroscience Research Book</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="research-subtitle">'
        'Explore cognition, behaviour, neural systems and '
        'brain mechanisms.'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Reading mode",
        ["Simple Mode", "Research Mode"],
        horizontal=True,
        key="research_mode",
    )

    topic = st.selectbox(
        "Choose a research topic",
        list(RESEARCH_TOPICS.keys()),
        key="research_topic",
    )

    data = _topic_summary(topic)

    st.markdown(
        '<div class="research-card">',
        unsafe_allow_html=True,
    )

    st.subheader(topic)

    if mode == "Simple Mode":

        st.write(data["simple"])

        st.markdown(
            "### 🔎 Key ideas"
        )

        for note in data["notes"]:
            st.markdown(
                f'<div class="research-note">• {note}</div>',
                unsafe_allow_html=True,
            )

    else:

        st.write(data["research"])

        st.markdown(
            "### 🧪 Research Notes"
        )

        for note in data["notes"]:
            st.markdown(
                f'<div class="research-note">• {note}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            "### 📚 Suggested References"
        )

        for reference in data["references"]:
            st.markdown(
                f"- {reference}"
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # -------------------------------
    # CONCEPT MAP
    # -------------------------------

    st.markdown("### 🧠 Cognitive Neuroscience Map")

    map_data = {
        "Brain & Behaviour": [
            "Perception",
            "Attention",
            "Memory",
            "Emotion",
            "Decision Making",
        ],
        "Memory": [
            "Hippocampus",
            "Working Memory",
            "Encoding",
            "Retrieval",
            "Reconsolidation",
        ],
        "Attention": [
            "Selective Attention",
            "Working Memory",
            "Cognitive Control",
            "Inhibition",
        ],
        "Decision Making": [
            "Prefrontal Cortex",
            "Striatum",
            "Reward",
            "Risk",
            "Learning",
        ],
        "Learning": [
            "Prediction Error",
            "Reward",
            "Plasticity",
            "Memory",
        ],
        "Emotion": [
            "Amygdala",
            "Prefrontal Cortex",
            "Attention",
            "Memory",
            "Regulation",
        ],
    }

    related = map_data.get(
        topic,
        [
            "Neural circuits",
            "Cognition",
            "Behaviour",
            "Learning",
        ],
    )

    cols = st.columns(
        min(4, len(related))
    )

    for i, item in enumerate(related):

        with cols[i % len(cols)]:
            st.info(item)

    # -------------------------------
    # RESEARCH NOTE BUILDER
    # -------------------------------

    st.markdown("---")

    st.subheader("📝 My Research Notes")

    note_key = f"research_note_{topic}"

    if note_key not in st.session_state:
        st.session_state[note_key] = ""

    note = st.text_area(
        "Write your observation or research note",
        value=st.session_state[note_key],
        height=140,
        key=f"note_area_{topic}",
        placeholder=(
            "Example: This topic may relate to "
            "attention, memory and cognitive control..."
        ),
    )

    if st.button(
        "💾 Save Note",
        use_container_width=True,
    ):

        st.session_state[note_key] = note

        st.success(
            f"Research note saved for {topic}."
        )


def render():
    research_screen()
