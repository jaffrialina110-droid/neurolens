import os
import streamlit as st

# =========================================================
# NEUROLENS CORE
# =========================================================

try:
    from google import genai
except Exception:
    genai = None


# =========================================================
# DAILY COGNITIVE EXPERIMENT BANK
# =========================================================

DAILY_EXPERIMENTS = [
    {
        "title": "Working Memory",
        "description": (
            "Remember a short sequence and reproduce it. "
            "This explores temporary information maintenance."
        ),
        "domain": "Working Memory",
    },
    {
        "title": "Selective Attention",
        "description": (
            "Focus on a target while ignoring distracting information."
        ),
        "domain": "Attention",
    },
    {
        "title": "Decision Making",
        "description": (
            "Choose between competing options and explain your reasoning."
        ),
        "domain": "Decision Making",
    },
    {
        "title": "Cognitive Flexibility",
        "description": (
            "Switch between changing rules and adapt your response."
        ),
        "domain": "Cognitive Flexibility",
    },
    {
        "title": "Inhibitory Control",
        "description": (
            "Respond to relevant signals while withholding responses "
            "to distractors."
        ),
        "domain": "Inhibitory Control",
    },
    {
        "title": "Memory Recall",
        "description": (
            "Recall information after a short delay."
        ),
        "domain": "Memory",
    },
    {
        "title": "Perception",
        "description": (
            "Explore how sensory information is interpreted."
        ),
        "domain": "Perception",
    },
    {
        "title": "Reward Processing",
        "description": (
            "Explore how choices can be influenced by reward information."
        ),
        "domain": "Reward",
    },
]


# =========================================================
# RESEARCH BOOK
# =========================================================

RESEARCH_TOPICS = [
    "Brain & Behaviour",
    "Memory",
    "Attention",
    "Perception",
    "Emotion",
    "Decision Making",
    "Learning",
    "Cognitive Control",
    "Reward",
    "Executive Functions",
    "Neuroplasticity",
    "Neural Circuits",
    "Neurotransmitters",
]


# =========================================================
# LOCAL KNOWLEDGE
# =========================================================

LOCAL_KNOWLEDGE = {

    "brain & behaviour":
        "Brain behaviour relationships emerge from interacting "
        "neural systems rather than one isolated brain area.",

    "memory":
        "Memory includes multiple processes such as encoding, "
        "consolidation, storage and retrieval.",

    "attention":
        "Attention helps select information for enhanced processing "
        "while other information receives relatively less processing.",

    "perception":
        "Perception involves interpretation of sensory information "
        "using both incoming signals and prior knowledge.",

    "emotion":
        "Emotion involves coordinated neural, physiological and "
        "cognitive processes.",

    "decision making":
        "Decision making involves evaluating options, rewards, "
        "uncertainty and goals.",

    "learning":
        "Learning can involve changes in behaviour and changes "
        "in neural representations and connections.",

    "cognitive control":
        "Cognitive control helps regulate thoughts and actions "
        "according to goals.",

    "reward":
        "Reward processing involves neural systems that influence "
        "motivation, learning and action selection.",

    "executive functions":
        "Executive functions include processes such as working "
        "memory, inhibition and cognitive flexibility.",

    "neuroplasticity":
        "Neuroplasticity refers to changes in neural structure "
        "or function associated with experience and learning.",

    "neural circuits":
        "Cognition depends on communication among distributed "
        "neural circuits.",

    "neurotransmitters":
        "Neurotransmitters are chemical signalling molecules "
        "that influence communication between neurons.",
}


# =========================================================
# LANGUAGE INSTRUCTION
# =========================================================

def language_instruction():

    language = st.session_state.get(
        "language",
        "English"
    )

    if language == "Roman English":

        return """
        Reply in simple Roman English/Roman Urdu.

        Keep important neuroscience terminology accurate.

        Do not unnecessarily use Urdu script.

        Explain difficult scientific concepts simply.
        """

    return """
    Reply in clear scientific English.

    Keep terminology appropriate for cognitive neuroscience.
    """


# =========================================================
# LOCAL FALLBACK
# =========================================================

def local_fallback(prompt):

    prompt_lower = prompt.lower()

    for topic, explanation in LOCAL_KNOWLEDGE.items():

        if topic in prompt_lower:

            if st.session_state.get(
                "language"
            ) == "Roman English":

                return (
                    "🧠 Ayna: "
                    + explanation
                    + " Is concept ko cognitive neuroscience "
                      "aur behaviour ke context mein explore "
                      "kiya ja sakta hai."
                )

            return "🧠 Ayna: " + explanation

    if st.session_state.get(
        "language"
    ) == "Roman English":

        return (
            "🧠 Ayna: Is question ko cognitive neuroscience "
            "ke perspective se explore kiya ja sakta hai. "
            "AI service temporarily available nahi hai, "
            "is liye local neuroscience response diya gaya hai."
        )

    return (
        "🧠 Ayna: This question can be explored from a "
        "cognitive-neuroscience perspective. "
        "The local neuroscience fallback is being used "
        "because the AI service is unavailable."
    )


# =========================================================
# GEMINI AI
# =========================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False
)
def cached_ai(prompt, language):

    if genai is None:
        return local_fallback(prompt)

    try:

        api_key = st.secrets.get(
            "GEMINI_API_KEY",
            os.getenv("GEMINI_API_KEY")
        )

        if not api_key:
            return local_fallback(prompt)

        client = genai.Client(
            api_key=api_key
        )

        if language == "Roman English":

            instruction = """
            Answer in simple Roman English/Roman Urdu.
            Keep scientific neuroscience terms accurate.
            """

        else:

            instruction = """
            Answer in clear scientific English.
            """

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=f"""
            You are Ayna, the AI cognitive neuroscience
            assistant inside NEUROLENS.

            {instruction}

            You can explain:
            - cognition
            - behaviour
            - memory
            - attention
            - perception
            - emotion
            - decision making
            - neural circuits
            - neuroscience experiments

            Do not claim to diagnose mental-health disorders.

            User question:

            {prompt[:6000]}
            """
        )

        if response and response.text:

            return response.text.strip()

        return local_fallback(prompt)

    except Exception:

        return local_fallback(prompt)


# =========================================================
# PUBLIC AI FUNCTION
# =========================================================

def ai_answer(prompt):

    language = st.session_state.get(
        "language",
        "English"
    )

    return cached_ai(
        prompt,
        language
    )


# =========================================================
# AYNА VOICE OUTPUT
# =========================================================

def speak(text):

    if not text:
        return

    safe_text = (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", " ")
        .replace("\r", " ")
    )

    st.components.v1.html(

        f"""
        <script>

        const message = `{safe_text}`;

        function speakAyna() {{

            if (!("speechSynthesis" in window)) {{
                return;
            }}

            window.speechSynthesis.cancel();

            const speech =
                new SpeechSynthesisUtterance(message);

            speech.lang = "en-US";
            speech.rate = 0.95;
            speech.pitch = 1.0;

            window.speechSynthesis.speak(speech);
        }}

        speakAyna();

        </script>
        """,

        height=1
    )


# =========================================================
# PROGRESS
# =========================================================

def initialise_progress():

    if "progress" not in st.session_state:

        st.session_state.progress = {

            "experiments": 0,

            "puzzles": 0,

            "exercises": 0,

            "mood": 0,

            "research": 0,

            "journey": 0,

            "streak": 0,
        }


def save_progress(category):

    initialise_progress()

    if category not in st.session_state.progress:

        st.session_state.progress[category] = 0

    st.session_state.progress[category] += 1


def get_progress():

    initialise_progress()

    return st.session_state.progress


# =========================================================
# EXPERIMENT ANALYSIS
# =========================================================

def analyse_experiment(
    experiment_name,
    user_response
):

    prompt = f"""
    NEUROLENS cognitive neuroscience experiment.

    Experiment:
    {experiment_name}

    User response:
    {user_response}

    Provide:

    1. Brief interpretation
    2. Cognitive process involved
    3. What the task can demonstrate
    4. A follow-up challenge

    Do not diagnose the user.
    """

    return ai_answer(prompt)


# =========================================================
# MOOD ANALYSIS — TEXT
# =========================================================

def analyse_text_mood(text):

    prompt = f"""
    Analyse conversational mood signals in the following
    user text.

    Text:
    {text}

    Return:

    Emoji:
    Mood signal:
    Brief explanation:
    Helpful next suggestion:

    Important:
    This is only a conversational estimate.
    Do not diagnose a mental-health disorder.
    """

    return ai_answer(prompt)


# =========================================================
# VOICE ANALYSIS
# =========================================================

def analyse_voice_mood(audio_file):

    """
    Voice input handler.

    The audio is accepted by Streamlit.
    If an audio-capable AI backend is configured later,
    it can be connected here.

    Until then we use a safe local response.
    """

    if audio_file is None:

        return (
            "🎤 No voice recording received."
        )

    if st.session_state.get(
        "language"
    ) == "Roman English":

        return (
            "😊 Ayna: Tumhari voice receive ho gayi hai. "
            "Voice-based mood estimation ko experimental "
            "signal ke taur par treat karna chahiye. "
            "Main isay definitive psychological diagnosis "
            "nahi samajhti."
        )

    return (
        "😊 Ayna: I received your voice recording. "
        "Voice-based mood estimation should be treated "
        "as an experimental signal rather than a definitive "
        "psychological diagnosis."
    )


# =========================================================
# DAILY EXPERIMENT
# =========================================================

def get_daily_experiment():

    index = st.session_state.get(
        "experiment_index",
        0
    )

    return DAILY_EXPERIMENTS[
        index % len(DAILY_EXPERIMENTS)
    ]


# =========================================================
# NEXT EXPERIMENT
# =========================================================

def next_experiment():

    current = st.session_state.get(
        "experiment_index",
        0
    )

    st.session_state.experiment_index = (
        current + 1
    )

    save_progress("experiments")


# =========================================================
# RESEARCH NOTE
# =========================================================

def research_note(topic):

    prompt = f"""
    Create a concise cognitive neuroscience research note
    about:

    {topic}

    Include:

    • Core concept
    • Relevant neural systems
    • Cognitive process
    • Behavioural relevance
    • Typical experimental approach
    • Important limitation

    Do not invent citations.
    """

    return ai_answer(prompt)


# =========================================================
# CONTEXTUAL AYNА
# =========================================================

def contextual_ayna(
    question,
    current_stage=None
):

    context = ""

    if current_stage:

        context = f"""
        The user is currently inside the brain journey.

        Current stage:
        {current_stage}
        """

    prompt = f"""
    {context}

    User asks:
    {question}

    Answer as Ayna.

    Connect the answer to cognition,
    neuroscience and behaviour when relevant.
    """

    return ai_answer(prompt)


# =========================================================
# INITIALISE
# =========================================================

initialise_progress()
'''

print("Part 2 ready: modules/core.py")
print("Create the 'modules' folder in GitHub, then create core.py and paste this code.")
print("Next: Part 3 — real Brain Journey/video + 3D viewer module.")
