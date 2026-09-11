import os, random, time, hashlib, base64, html
from io import BytesIO
import streamlit as st
from PIL import Image
import streamlit.components.v1 as components

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

try:
    import plotly.graph_objects as plotly_go
except Exception:
    plotly_go = None

st.set_page_config(page_title="NEUROLENS", page_icon="🧠", layout="wide")

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")

def asset_path(name):
    p = os.path.join(ASSETS, name)
    return p if os.path.exists(p) else os.path.join(ROOT, name)

def find_video(*names, keywords=()):
    for name in names:
        p = asset_path(name)
        if os.path.exists(p):
            return p
    for folder in (ASSETS, ROOT):
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            low = name.lower()
            if low.endswith((".mp4", ".webm", ".mov")) and any(k in low for k in keywords):
                return os.path.join(folder, name)
    return None

BRAIN_PATH = asset_path("brain.png")
JOURNEY_VIDEO = find_video("brain_animation.mp4", keywords=("brain", "journey"))
LAB_VIDEO = find_video("cognitive_lab_brain.mp4", keywords=("lab", "cognitive"))

REBOOT_VIDEO = find_video(
    "ayna_reboot.mp4",
    "ayna_welcome.mp4",
    "reboot.mp4",
    "welcome.mp4",
    keywords=("ayna", "reboot", "welcome")
)

st.markdown("""
<style>
.stApp{
    background:
    radial-gradient(circle at 15% 5%,#183c63,transparent 30%),
    linear-gradient(135deg,#06101d,#0b1b2d)
}

.block-container{
    max-width:1400px;
    padding-top:1rem
}

.hero{
    padding:28px;
    border-radius:24px;
    background:linear-gradient(135deg,#122c49,#111a32);
    border:1px solid #45617d;
    margin-bottom:18px
}

.card{
    padding:18px;
    border-radius:18px;
    background:#0d2035;
    border:1px solid #294560;
    margin:8px 0
}

.lab{
    min-height:320px;
    border-radius:24px;
    position:relative;
    overflow:hidden;
    background:
    radial-gradient(circle,#285b88 0,#0b1930 28%,#07111f 72%);
    border:1px solid #36536d
}

.orb{
    position:absolute;
    width:92px;
    height:92px;
    border-radius:50%;
    left:calc(50% - 46px);
    top:calc(50% - 46px);
    background:
    radial-gradient(circle,#fff,#8ed1ff 20%,#536bff 55%,#342a7d);
    box-shadow:0 0 45px #71bfff;
    animation:p 2.3s infinite
}

@keyframes p{
    50%{transform:scale(1.1)}
}

.small{
    opacity:.78;
    font-size:.9rem
}

.stage{
    height:210px;
    border-radius:22px;
    background:radial-gradient(circle,#153d63,#081321);
    border:1px solid #38536e;
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden
}

.neuron{
    font-size:5rem;
    animation:p 1.5s infinite
}

.signal{
    font-size:3rem;
    animation:move 2s linear infinite
}

@keyframes move{
    0%{transform:translateX(-170px)}
    100%{transform:translateX(170px)}
}

.syn{
    font-size:3rem;
    animation:p .9s infinite
}
</style>
""", unsafe_allow_html=True)


# ---------------- STATE ----------------

def fresh_progress():
    return {
        "experiments":0,
        "puzzles":0,
        "games":0,
        "research":0,
        "streak":1,
        "accuracy":0,
        "reaction_time":None
    }

defaults = {
    "page":"Welcome Reboot",
    "language":"English",
    "character":"Nova",
    "equipment":"EEG Scanner",
    "journey_stage":"brain",
    "journey_region":"Prefrontal Cortex",
    "messages":[],
    "private_messages":[],
    "private_unlocked":False,
    "progress":fresh_progress(),
    "ai_requests":0,
    "ai_cache":{},
    "last_experiment":None,
    "experiment_history":[],
    "puzzle_history":[],
    "research_history":[]
}

for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = (
            v.copy() if isinstance(v,dict)
            else v.copy() if isinstance(v,list)
            else v
        )

PAGES = [
    "Welcome Reboot",
    "Lab",
    "Explore Brain",
    "Brain Puzzle",
    "AI Mood & Behaviour",
    "Brain Exercises",
    "Research Book",
    "Ask Ayna",
    "Private Ask Ayna",
    "My Progress"
]


BRAIN = {
    "Prefrontal Cortex":(
        "Supports planning, working memory, cognitive control and goal-directed behaviour.",
        "Planning, decision-making and inhibition.",
        "Prefrontal cortex ↔ basal ganglia ↔ thalamus ↔ cortex"
    ),
    "Hippocampus":(
        "Important for episodic memory formation and spatial representation.",
        "Learning, memory and navigation.",
        "Hippocampus ↔ entorhinal cortex ↔ cortex"
    ),
    "Amygdala":(
        "Processes emotionally significant information and contributes to emotional learning.",
        "Threat processing, salience and emotional learning.",
        "Amygdala ↔ hypothalamus ↔ brainstem/cortex"
    ),
    "Striatum":(
        "Contributes to action selection, reward learning and habits.",
        "Reward learning, action selection and habits.",
        "Cortex → striatum → pallidal pathways → thalamus → cortex"
    ),
    "Anterior Cingulate Cortex":(
        "Contributes to performance monitoring, conflict processing and control.",
        "Conflict, error processing and effort-related control.",
        "ACC ↔ prefrontal ↔ striatal networks"
    ),
    "Cerebellum":(
        "Supports coordination, timing and motor learning and also contributes to cognition.",
        "Timing, balance, coordination and motor learning.",
        "Cerebellum → deep nuclei → thalamus → cortex"
    )
}


NT = {
    "Dopamine":
        "Involved in reward learning, motivation, movement and several cognitive processes.",
    "Serotonin":
        "Involved in mood-related processes, sleep, appetite and many physiological functions.",
    "GABA":
        "A major inhibitory neurotransmitter in the central nervous system.",
    "Glutamate":
        "A major excitatory neurotransmitter important for learning and plasticity.",
    "Acetylcholine":
        "Contributes to attention, learning, memory and neuromuscular communication."
}


BOOK = {
    "Brain & Behaviour":(
        "Behaviour emerges from interacting brain networks, body systems and environment.",
        "Cognitive neuroscience links behaviour to distributed neural systems. Separate correlation, causation, computational models and clinical observations."
    ),
    "Memory":(
        "Memory includes encoding, consolidation, retrieval and reconsolidation.",
        "Episodic, semantic, working and procedural memory involve partly distinct but interacting systems."
    ),
    "Attention":(
        "Attention changes which information receives processing priority.",
        "Attention involves selection, enhancement and suppression interacting with sensory and control networks."
    ),
    "Perception":(
        "Perception is the brain's construction of meaningful representations from sensory input.",
        "Perception reflects interactions among sensory evidence, prior knowledge, attention and context."
    ),
    "Emotion":(
        "Emotion involves interacting brain, body and cognitive processes.",
        "Contemporary models emphasize distributed networks, appraisal, interoception, learning and context."
    ),
    "Decision Making":(
        "Decisions combine goals, rewards, uncertainty, memory and control.",
        "Decision neuroscience examines valuation, learning, uncertainty, evidence accumulation and cognitive control."
    ),
    "Cognitive Control":(
        "Control helps maintain goals and adjust behaviour.",
        "Prefrontal, cingulate, parietal and striatal systems interact in task-dependent control."
    ),
    "Neuroplasticity":(
        "The nervous system can change with development, learning and experience.",
        "Plasticity includes synaptic, circuit and systems-level changes influenced by learning and context."
    )
}


EQUIPMENT = {
    "EEG Scanner":
        "Illustrates measurement of electrical activity at the scalp; educational simulation only.",
    "Eye Tracker":
        "Illustrates measurement of gaze position and fixation patterns.",
    "Reaction-Time Monitor":
        "Measures response latency in a simple cognitive task.",
    "Auditory Attention Station":
        "Presents competing sounds to explore selective attention.",
    "Cognitive Task Screen":
        "Runs structured memory, attention and decision tasks.",
    "Physiological Monitor":
        "Illustrates non-neural physiological signals such as pulse or skin conductance; not a diagnosis."
}


EXPERIMENTS = [
    ("Attention Gate","Attention"),
    ("Working Memory Sprint","Working Memory"),
    ("Decision Under Delay","Decision Making"),
    ("Inhibition Challenge","Inhibitory Control"),
    ("Cognitive Flexibility","Cognitive Flexibility"),
    ("Memory Retrieval","Memory")
]


MOODS = {
    "Positive":"😊",
    "Calm":"😌",
    "Neutral":"😐",
    "Worried":"😟",
    "Low":"😔",
    "Frustrated":"😤",
    "Tired":"😴"
}


@st.cache_data(show_spinner=False)
def load_brain():
    try:
        return (
            Image.open(BRAIN_PATH).convert("RGB")
            if os.path.exists(BRAIN_PATH)
            else None
        )
    except Exception:
        return None

brain = load_brain()


# ---------------- AI ----------------

def get_api_key():
    for name in ("GEMINI_API_KEY","GOOGLE_API_KEY"):

        try:
            v = st.secrets.get(name)
            if v:
                return str(v).strip()
        except Exception:
            pass

        v = os.getenv(name)

        if v:
            return v.strip()

    return None


@st.cache_resource(show_spinner=False)
def make_client(key):
    if genai is None or not key:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


MODEL = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
AI_LIMIT = 140


def ask_ai(prompt, context="", max_tokens=450):

    cache_key = hashlib.sha256(
        (prompt + "\n" + context).encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()

    if cache_key in st.session_state.ai_cache:
        return st.session_state.ai_cache[cache_key],"cache"

    if st.session_state.ai_requests >= AI_LIMIT:
        return (
            "AI session limit reached. Local NEUROLENS activities are still available.",
            "limit"
        )

    client = make_client(get_api_key())

    if client is None:
        return (
            "Ask Ayna is unavailable. Add GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    prompt = f"""
You are Ayna, the AI assistant inside NEUROLENS,
an educational cognitive neuroscience platform.

Be accurate, concise, friendly and scientifically cautious.

Never diagnose a medical or psychiatric condition.

Do not claim that games, voice estimates or self-report scores
directly measure brain activity.

Distinguish evidence from hypotheses.

Language preference may be English or Roman English.

Avoid pretending to be a doctor or therapist.

Context:
{context[-4500:]}

Task:
{prompt}
"""

    try:
        st.session_state.ai_requests += 1

        if types:
            cfg = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_tokens
            )

            r = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=cfg
            )

        else:
            r = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

        text = getattr(r,"text",None) or "Ayna could not generate a response."

        st.session_state.ai_cache[cache_key] = text

        return text,"live"

    except Exception as e:
        return (
            "Ayna is temporarily unavailable. Please try again.",
            "error"
        )


def ask_ai_audio(audio_file, instruction):

    client = make_client(get_api_key())

    if client is None:
        return (
            "Voice AI is unavailable. Add GEMINI_API_KEY in Streamlit Secrets.",
            "offline"
        )

    try:
        data = audio_file.getvalue()

        prompt = f"""
You are Ayna inside NEUROLENS.

{instruction}

The audio is user-provided.
Transcribe it and answer the request.

Do not diagnose.
Do not infer sensitive traits.
Keep the response educational and cautious.
"""

        if types:

            audio_part = types.Part.from_bytes(
                data=data,
                mime_type=audio_file.type or "audio/wav"
            )

            cfg = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=350
            )

            r = client.models.generate_content(
                model=MODEL,
                contents=[prompt,audio_part],
                config=cfg
            )

        else:
            r = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

        return getattr(r,"text",None) or "Ayna could not process the voice.","live"

    except Exception:
        return (
            "Voice processing failed. Please try again or use text.",
            "error"
        )


# ---------------- HELPERS ----------------

def record(kind):

    if kind in st.session_state.progress:
        st.session_state.progress[kind] += 1


def voice_button(text,key):

    if not text:
        return

    safe = html.escape(str(text))

    components.html(
        f"""
        <button
        onclick="speechSynthesis.cancel();
        speechSynthesis.speak(
        new SpeechSynthesisUtterance(
        {safe!r}
        )
        )"
        style="
        padding:10px 16px;
        border-radius:12px;
        border:1px solid #45617d;
        background:#122c49;
        color:white;
        cursor:pointer;
        ">
        🔊 Ayna Voice
        </button>
        """,
        height=55
    )


# ---------------- SIDEBAR ----------------

st.sidebar.title("🧠 NEUROLENS")

st.sidebar.caption(
    "Explore cognition, behaviour & the brain"
)

st.sidebar.markdown("### Navigation")

for page in PAGES:

    if st.sidebar.button(
        page,
        key="nav_" + page.replace(" ","_").replace("&","and")
    ):
        st.session_state.page = page
        st.rerun()


st.sidebar.markdown("---")

st.sidebar.markdown("### 🌐 Language")

st.session_state.language = st.sidebar.radio(
    "Choose language",
    ["English","Roman English"],
    horizontal=True,
    key="language_choice"
)


# ---------------- HEADER ----------------

st.markdown(
    """
    <div class="hero">
        <h1>🧠 NEUROLENS</h1>
        <p>Explore cognition, behaviour & the brain</p>
        <p class="small">
        An AI-powered interactive cognitive neuroscience platform
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# ---------------- WELCOME REBOOT ----------------

if st.session_state.page == "Welcome Reboot":

    st.subheader("🚀 Welcome Reboot")

    st.write(
        "Welcome to NEUROLENS — an interactive space for "
        "cognitive neuroscience, brain systems, behaviour and AI."
    )

    if REBOOT_VIDEO:

        st.video(REBOOT_VIDEO)

    else:

        st.info(
            "Reboot video not found. Add your MP4 to the project "
            "root or assets folder."
        )

    welcome = (
        "Welcome to NeuroLens! I'm Ayna, your cognitive neuroscience "
        "lab assistant. Let's explore the brain, behaviour, and cognition together."
    )

    if st.button("🔊 Welcome from Ayna",key="welcome_voice"):
        voice_button(welcome,"welcome_voice_result")

    st.markdown("### Start exploring")

    c1,c2,c3 = st.columns(3)

    with c1:
        if st.button("🧪 Enter Lab",key="welcome_lab"):
            st.session_state.page = "Lab"
            st.rerun()

    with c2:
        if st.button("🧠 Brain Journey",key="welcome_brain"):
            st.session_state.page = "Explore Brain"
            st.rerun()

    with c3:
        if st.button("💬 Ask Ayna",key="welcome_ask"):
            st.session_state.page = "Ask Ayna"
            st.rerun()


# ---------------- LAB ----------------

if st.session_state.page == "Lab":

    st.subheader("🧪 Interactive Cognitive Neuroscience Lab")

    left,right = st.columns([1,1])

    with left:

        st.markdown("### 👩‍🔬 Choose Character")

        st.session_state.character = st.selectbox(
            "Character",
            ["Nova","Mira","Ray","Zara"],
            key="lab_character"
        )

        st.markdown("### 🔬 Equipment")

        st.session_state.equipment = st.selectbox(
            "Equipment",
            list(EQUIPMENT),
            key="lab_equipment"
        )

        st.info(
            EQUIPMENT[
                st.session_state.equipment
            ]
        )

    with right:

        st.markdown(
            f"""
            <div class="lab">
                <div class="orb"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"### {st.session_state.character} is ready"
        )

        st.caption(
            f"Equipment: {st.session_state.equipment}"
        )

    if LAB_VIDEO:

        st.markdown("### 🎬 Lab Brain Activity")

        st.video(LAB_VIDEO)

    else:

        st.info(
            "Lab animation video not found. "
            "The interactive lab simulation is still available."
        )

    st.markdown("### 🧠 Today's Experiment")

    idx = (time.gmtime().tm_yday - 1) % len(EXPERIMENTS)

    title,domain = EXPERIMENTS[idx]

    st.markdown(f"## {title}")

    st.caption(
        f"Domain: {domain}"
    )

    if st.button(
        "▶️ Start Experiment",
        key="start_lab_experiment"
    ):

        st.session_state.last_experiment = {
            "title":title,
            "domain":domain,
            "character":st.session_state.character,
            "equipment":st.session_state.equipment
        }

        st.success(
            f"{st.session_state.character} started {title}."
        )

    if st.session_state.last_experiment:

        st.markdown("### 🤖 Ayna AI Lab Assistant")

        explanation = ask_ai(
            f"""
            Explain the experiment
            {title}
            in the domain {domain}.

            Character:
            {st.session_state.character}

            Equipment:
            {st.session_state.equipment}
            """,
            max_tokens=260
        )[0]

        st.write(explanation)

        voice_button(
            explanation,
            "lab_ai_voice"
        )

        if st.button(
            "📝 Record Research Note",
            key="lab_research_note"
        ):

            st.session_state.experiment_history.append(
                st.session_state.last_experiment
            )

            record("experiments")

            st.success(
                "Research note recorded."
            )


# ---------------- EXPLORE BRAIN ----------------

elif st.session_state.page == "Explore Brain":

    st.subheader("🧠 Brain Journey")

    if brain:
        st.image(
            brain,
            caption="NEUROLENS Brain",
            use_container_width=True
        )

    region = st.selectbox(
        "Choose brain region",
        list(BRAIN),
        key="brain_region"
    )

    description,function,path = BRAIN[region]

    st.markdown(
        f"""
        <div class="card">
            <h2>{region}</h2>
            <p>{description}</p>
            <p><b>Cognitive / behavioural relevance:</b>
            {function}</p>
            <p><b>Network:</b> {path}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 🔬 Neural Scale Journey")

    stages = [
        ("Whole Brain","🧠"),
        ("Brain Region","🔵"),
        ("Neural Pathway","🔗"),
        ("Neuron","🧬"),
        ("Dendrites","🌿"),
        ("Axon","➖"),
        ("Myelin","⚡"),
        ("Electrical Signal","💫"),
        ("Synapse","🔬"),
        ("Neurotransmitter","🧪"),
        ("Cognition & Behaviour","💡")
    ]

    stage_names = [x[0] for x in stages]

    selected = st.selectbox(
        "Journey stage",
        stage_names,
        key="journey_selector"
    )

    emoji = dict(stages)[selected]

    st.markdown(
        f"""
        <div class="stage">
            <div class="neuron">{emoji}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    stage_explanation = ask_ai(
        f"""
        Explain the neuroscience of the stage
        '{selected}'
        in the context of cognitive neuroscience.

        Keep it educational and concise.
        """,
        context=description,
        max_tokens=240
    )[0]

    st.write(stage_explanation)

    if st.button(
        "🔊 Explain with Ayna",
        key="journey_explain"
    ):
        voice_button(
            stage_explanation,
            "journey_voice"
        )

    st.markdown("### 🧪 Neurotransmitters")

    nt = st.selectbox(
        "Choose neurotransmitter",
        list(NT),
        key="nt_selector"
    )

    st.info(NT[nt])

    voice_button(
        NT[nt],
        "nt_voice"
    )


# ---------------- BRAIN PUZZLE ----------------

elif st.session_state.page == "Brain Puzzle":

    st.subheader("🧩 Brain Puzzle")

    size = st.selectbox(
        "Puzzle size",
        [3,4,5],
        key="puzzle_size"
    )

    st.info(
        "Arrange the brain tiles in the correct order. "
        "This is a cognitive game, not a clinical assessment."
    )

    cols = st.columns(size)

    total = size * size

    if "puzzle_order" not in st.session_state:
        st.session_state.puzzle_order = list(
            range(1,total+1)
        )

    if "puzzle_start" not in st.session_state:
        st.session_state.puzzle_start = time.time()

    if "puzzle_moves" not in st.session_state:
        st.session_state.puzzle_moves = 0

    for i in range(total):

        with cols[i % size]:

            if st.button(
                str(st.session_state.puzzle_order[i]),
                key=f"tile_{size}_{i}_{st.session_state.puzzle_moves}"
            ):

                if i > 0:

                    arr = st.session_state.puzzle_order

                    arr[i-1],arr[i] = (
                        arr[i],
                        arr[i-1]
                    )

                    st.session_state.puzzle_moves += 1

                    st.rerun()

    elapsed = int(
        time.time() -
        st.session_state.puzzle_start
    )

    st.metric(
        "Timer",
        f"{elapsed}s"
    )

    st.metric(
        "Moves",
        st.session_state.puzzle_moves
    )

    if st.session_state.puzzle_order == list(
        range(1,total+1)
    ):

        st.success(
            "🎉 Puzzle completed!"
        )

        record("puzzles")
        record("games")

        st.session_state.puzzle_history.append(
            {
                "size":size,
                "time":elapsed,
                "moves":st.session_state.puzzle_moves
            }
        )

    if st.button(
        "🔄 Restart Puzzle",
        key="restart_puzzle"
    ):

        st.session_state.puzzle_order = list(
            range(1,total+1)
        )

        random.shuffle(
            st.session_state.puzzle_order
        )

        st.session_state.puzzle_start = time.time()
        st.session_state.puzzle_moves = 0

        st.rerun()


# ---------------- MOOD ----------------

elif st.session_state.page == "AI Mood & Behaviour":

    st.subheader("🎯 AI Mood & Behaviour")

    st.write(
        "Use voice as the main input, or type. "
        "This is an educational conversational estimate, "
        "not a clinical assessment."
    )

    v,t = st.tabs(
        ["🎙️ Voice","⌨️ Text"]
    )

    with v:

        audio = None

        try:
            audio = st.audio_input(
                "Record your voice",
                key="mood_audio"
            )
        except Exception:
            st.info(
                "Voice recording is unavailable in this browser. "
                "Use Text."
            )

        ctx = st.text_input(
            "Optional context",
            key="mood_ctx"
        )

        if st.button(
            "🧠 Send Voice to Ayna",
            key="send_mood_voice"
        ) and audio:

            ans,src = ask_ai_audio(
                audio,
                f"""
                Estimate broad conversational affect only.

                Choose one primary mood from:
                {', '.join(MOODS)}.

                Give emoji, mood, confidence
                (Low/Medium/High), and one short explanation.

                Do not diagnose or infer sensitive traits.

                Context:
                {ctx[:500]}
                """
            )

            st.success(
                "Ayna's broad conversational estimate"
            )

            st.write(ans)

            st.caption(src)

            voice_button(
                ans,
                "mood_voice_result"
            )

    with t:

        txt = st.text_area(
            "Tell Ayna how you feel",
            height=130,
            key="mood_text"
        )

        if st.button(
            "✨ Send Text to Ayna",
            key="send_mood_text"
        ) and txt:

            ans,src = ask_ai(
                f"""
                Give one emoji, one primary broad mood
                from {', '.join(MOODS)},
                optional secondary signal,
                confidence and one friendly sentence
                for this text:

                {txt}
                """,
                max_tokens=240
            )

            st.info(ans)

            st.caption(src)

            voice_button(
                ans,
                "mood_text_result"
            )

    st.caption(
        "Voice tone and text can be ambiguous and context-dependent. "
        "Results should not be treated as diagnosis, brain measurement "
        "or a definitive statement about a person's mental state."
    )


# ---------------- EXERCISES ----------------

elif st.session_state.page == "Brain Exercises":

    st.subheader("🧪 Daily Cognitive Experiment")

    index = (
        time.gmtime().tm_yday - 1
    ) % len(EXPERIMENTS)

    title,domain = EXPERIMENTS[index]

    st.markdown(
        f"## {title}"
    )

    st.caption(
        f"Domain: {domain} • "
        f"Equipment: {st.session_state.equipment}"
    )

    if domain == "Attention":

        x = st.radio(
            "Which sequence contains X?",
            [
                "A B C D",
                "A B X D",
                "A B C E",
                "A X C D"
            ],
            key="ex_att"
        )

        submitted = st.button(
            "Check",
            key="ex_att_submit"
        )

        correct = x == "A B X D"

    elif domain == "Working Memory":

        st.markdown(
            "### Memorize: 7 2 9 4 1 8"
        )

        x = st.text_input(
            "Enter sequence",
            key="ex_mem"
        )

        submitted = st.button(
            "Check",
            key="ex_mem_submit"
        )

        correct = (
            x.replace(" ","") ==
            "729418"
        )

    elif domain == "Decision Making":

        x = st.radio(
            "Choose one",
            [
                "Rs. 1,000 today",
                "Rs. 1,500 after 30 days"
            ],
            key="ex_dec"
        )

        submitted = st.button(
            "Submit",
            key="ex_dec_submit"
        )

        correct = True

    elif domain == "Inhibitory Control":

        word = st.session_state.get(
            "inhib_word"
        )

        if not word:

            word = random.choice(
                ["RED","BLUE","GREEN"]
            )

            st.session_state.inhib_word = word

        st.markdown(
            f"### {word}"
        )

        x = st.selectbox(
            "Response",
            ["RED","BLUE","GREEN"],
            key="ex_inhib"
        )

        submitted = st.button(
            "Submit",
            key="ex_inhib_submit"
        )

        correct = x == word

    elif domain == "Cognitive Flexibility":

        rule = st.radio(
            "Choose the rule",
            [
                "Odd/even",
                "Greater/less than 10"
            ],
            key="ex_flex_rule"
        )

        num = st.number_input(
            "Number",
            1,
            30,
            7,
            key="ex_flex_num"
        )

        submitted = st.button(
            "Check",
            key="ex_flex_submit"
        )

        correct = True

    else:

        seq = "7294"

        x = st.text_input(
            "Recall the sequence 7 2 9 4",
            key="ex_recall"
        )

        submitted = st.button(
            "Check",
            key="ex_recall_submit"
        )

        correct = (
            x.replace(" ","") ==
            seq
        )

    if submitted:

        if correct:

            st.success(
                "🎉 Response recorded."
            )

            record("experiments")
            record("games")

            st.session_state.experiment_history.append(
                {
                    "title":title,
                    "domain":domain,
                    "correct":True
                }
            )

        else:

            st.warning(
                "Not quite. Treat the result as practice, "
                "not a diagnostic score."
            )

            st.session_state.experiment_history.append(
                {
                    "title":title,
                    "domain":domain,
                    "correct":False
                }
            )

    st.info(
        "Educational cognitive task only. "
        "A single task does not diagnose a condition "
        "or directly measure brain activity."
    )

    if st.button(
        "💡 Ask Ayna for a follow-up challenge",
        key="follow_challenge"
    ):

        ans,src = ask_ai(
            f"""
            Give a short educational follow-up challenge
            for {title} in cognitive neuroscience.

            No diagnosis.
            """,
            max_tokens=240
        )

        st.write(ans)

        voice_button(
            ans,
            "followup_voice"
        )


# ---------------- RESEARCH BOOK ----------------

elif st.session_state.page == "Research Book":

    st.subheader(
        "📖 Cognitive Neuroscience Research Book"
    )

    mode = st.radio(
        "Mode",
        ["Simple Mode","Research Mode"],
        horizontal=True,
        key="book_mode"
    )

    topic = st.selectbox(
        "Topic",
        list(BOOK),
        key="book_topic"
    )

    simple,research = BOOK[topic]

    if mode == "Simple Mode":

        st.info(simple)

        voice_button(
            simple,
            "book_simple_voice"
        )

    else:

        st.info(research)

        st.markdown(
            "### 🔎 Research note"
        )

        st.write(
            "Interpret findings in terms of study design, "
            "measurement, effect size, uncertainty and replication."
        )

        st.markdown(
            "### 📚 Suggested source types"
        )

        st.write(
            "• PubMed-indexed research\n"
            "• peer-reviewed reviews\n"
            "• systematic reviews/meta-analyses\n"
            "• primary articles"
        )

        if st.button(
            "📝 Mark topic explored",
            key="mark_research"
        ):

            record("research")

            st.session_state.research_history.append(
                topic
            )

            st.success(
                "Research topic recorded."
            )

        st.caption(
            "This starter book does not invent citations. "
            "A future retrieval layer can connect PubMed/Europe PMC "
            "for real article metadata and legal full-text links."
        )


# ---------------- ASK AYNA ----------------

elif st.session_state.page == "Ask Ayna":

    st.subheader("💬 Ask Ayna")

    st.caption(
        "English | Roman English • Text + voice • "
        "Educational, not therapy or diagnosis"
    )

    for m in st.session_state.messages:

        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    try:

        audio = st.audio_input(
            "🎙️ Optional voice message",
            key="public_voice"
        )

    except Exception:

        audio = None

    if st.button(
        "🧠 Send Voice to Ayna",
        key="public_voice_send"
    ) and audio:

        ans,src = ask_ai_audio(
            audio,
            "Transcribe and answer this user's request. "
            "Respond as Ayna, concise and scientifically cautious."
        )

        st.session_state.messages += [
            {
                "role":"user",
                "content":"🎙️ Voice message"
            },
            {
                "role":"assistant",
                "content":ans
            }
        ]

        st.rerun()

    q = st.chat_input(
        "Ask Ayna...",
        key="public_chat"
    )

    if q:

        ctx = "\n".join(
            f"{m['role']}: {m['content'][:600]}"
            for m in
            st.session_state.messages[-6:]
        )

        ans,src = ask_ai(
            q,
            ctx
        )

        st.session_state.messages += [
            {
                "role":"user",
                "content":q
            },
            {
                "role":"assistant",
                "content":ans
            }
        ]

        st.rerun()

    if st.session_state.messages:

        last = st.session_state.messages[-1]["content"]

        voice_button(
            last,
            "public_last_voice"
        )

        if st.button(
            "🗑️ Clear chat",
            key="clear_public2"
        ):

            st.session_state.messages = []

            st.rerun()


# ---------------- PRIVATE ----------------

elif st.session_state.page == "Private Ask Ayna":

    st.subheader("🔐 Private Ask Ayna")

    if not st.session_state.private_unlocked:

        st.write(
            "Session PIN lock for a private chat."
        )

        pin = st.text_input(
            "Enter PIN",
            type="password",
            max_chars=8,
            key="private_pin"
        )

        if st.button(
            "🔓 Unlock",
            key="unlock_private"
        ):

            ok = False

            try:

                from modules.security import verify_pin

                ok = bool(
                    verify_pin(pin)
                )

            except Exception:

                ok = pin == "2026"

            if ok:

                st.session_state.private_unlocked = True

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )

        st.caption(
            "Level 1 session lock. "
            "It is not authenticated encrypted storage; "
            "do not use it for highly sensitive information."
        )

    else:

        for m in st.session_state.private_messages:

            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        try:

            pv = st.audio_input(
                "🎙️ Private voice message",
                key="private_voice"
            )

        except Exception:

            pv = None

        if st.button(
            "🧠 Send Private Voice",
            key="private_voice_send"
        ) and pv:

            ans,src = ask_ai_audio(
                pv,
                "Answer the user's private message as Ayna. "
                "Be concise, educational and non-clinical."
            )

            st.session_state.private_messages += [
                {
                    "role":"user",
                    "content":"🎙️ Voice message"
                },
                {
                    "role":"assistant",
                    "content":ans
                }
            ]

            st.rerun()

        pq = st.chat_input(
            "Private message to Ayna...",
            key="private_chat"
        )

        if pq:

            ctx = "\n".join(
                f"{m['role']}: {m['content'][:600]}"
                for m in
                st.session_state.private_messages[-6:]
            )

            ans,_ = ask_ai(
                pq,
                ctx
            )

            st.session_state.private_messages += [
                {
                    "role":"user",
                    "content":pq
                },
                {
                    "role":"assistant",
                    "content":ans
                }
            ]

            st.rerun()

        if st.session_state.private_messages:

            voice_button(
                st.session_state.private_messages[-1]["content"],
                "private_last_voice"
            )

        if st.button(
            "🗑️ Delete private session",
            key="delete_private2"
        ):

            st.session_state.private_messages = []

            st.session_state.private_unlocked = False

            st.rerun()


# ---------------- PROGRESS ----------------

elif st.session_state.page == "My Progress":

    st.subheader("📊 My Progress")

    p = st.session_state.progress

    cols = st.columns(5)

    for c,(name,key) in zip(
        cols,
        [
            ("Experiments","experiments"),
            ("Puzzles","puzzles"),
            ("Games","games"),
            ("Research","research"),
            ("Streak","streak")
        ]
    ):

        c.metric(
            name,
            p.get(key,0)
        )

    if plotly_go:

        fig = plotly_go.Figure(
            plotly_go.Bar(
                x=[
                    "Experiments",
                    "Puzzles",
                    "Games",
                    "Research"
                ],
                y=[
                    p.get("experiments",0),
                    p.get("puzzles",0),
                    p.get("games",0),
                    p.get("research",0)
                ]
            )
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown(
        "### 📚 History"
    )

    if st.session_state.experiment_history:

        st.write(
            st.session_state.experiment_history[-10:]
        )

    if st.session_state.research_history:

        st.write(
            "Research topics:",
            st.session_state.research_history[-10:]
        )

    st.info(
        "Progress is session-based in this build. "
        "Permanent accounts/history require authenticated backend storage."
    )


st.divider()

st.caption(
    "NEUROLENS • Cognitive Neuroscience Education • Created by Ayna Jaffri"
)
