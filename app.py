import streamlit as st

# -----------------------------
# NEUROLENS
# Cognitive Behavior Mapper
# -----------------------------

st.set_page_config(
    page_title="NeuroLens",
    page_icon="🧠",
    layout="centered"
)

# ---------- Styling ----------
st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 2px;
}
.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 30px;
}
.card {
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #dddddd;
    margin: 12px 0;
    text-align: center;
}
.brain {
    font-size: 80px;
    text-align: center;
    margin: 10px;
}
.flow {
    text-align: center;
    font-size: 20px;
    padding: 12px;
}
.creator {
    text-align: center;
    margin-top: 40px;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown(
    '<div class="main-title">NEUROLENS</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Decode Behavior. Understand the Mind.</div>',
    unsafe_allow_html=True
)

st.markdown('<div class="brain">🧠</div>', unsafe_allow_html=True)

st.write(
    "Explore everyday behavior through a cognitive neuroscience lens."
)

st.info(
    "Educational tool only — this does not diagnose mental or neurological disorders."
)

# ---------- Behavior ----------
st.subheader("1. Choose a behavior")

behavior = st.selectbox(
    "What would you like to explore?",
    [
        "Decision-making",
        "Overthinking",
        "Attention",
        "Memory",
        "Reward & motivation",
        "Fear response",
        "Procrastination",
        "Social behavior"
    ]
)

# ---------- Questions ----------
st.subheader("2. Explore your pattern")

decision = st.radio(
    "When you face an important decision, what usually happens?",
    [
        "I decide quickly",
        "I overthink it",
        "I avoid the decision",
        "I ask other people",
        "It depends on the situation"
    ]
)

stress = st.slider(
    "Current stress level",
    min_value=1,
    max_value=10,
    value=5
)

mental_load = st.slider(
    "How mentally overloaded do you feel?",
    min_value=1,
    max_value=10,
    value=5
)

sleep = st.slider(
    "How would you rate your recent sleep?",
    min_value=1,
    max_value=10,
    value=5
)

# ---------- Analysis ----------
if st.button("🔍 Explore My Pattern"):

    if decision == "I overthink it":
        pattern = "Decision delay / prolonged deliberation"
        cognitive = "Executive control + uncertainty evaluation"
    elif decision == "I avoid the decision":
        pattern = "Decision avoidance"
        cognitive = "Uncertainty processing + cognitive load"
    elif decision == "I decide quickly":
        pattern = "Rapid decision-making"
        cognitive = "Efficient decision processing + response tendency"
    elif decision == "I ask other people":
        pattern = "Social decision support"
        cognitive = "Social cognition + uncertainty evaluation"
    else:
        pattern = "Context-dependent decision-making"
        cognitive = "Flexible cognitive processing"

    # Simple educational scores
    attention_score = max(1, 10 - mental_load + 1)
    control_score = max(1, 11 - stress)
    reward_score = 5
    flexibility_score = max(1, 11 - mental_load)
    emotional_score = stress

    st.divider()

    st.subheader("🧠 Your Cognitive Pattern")

    st.markdown(
        f'<div class="card">'
        f'<h3>{pattern}</h3>'
        f'<p>Possible cognitive processes: {cognitive}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ---------- Visual Brain → Behavior Map ----------
    st.subheader("🔬 Brain → Cognition → Behavior")

    st.markdown(
        '<div class="flow">🧠 Brain systems</div>'
        '<div class="flow">↓</div>'
        '<div class="flow">💭 Cognitive processing</div>'
        '<div class="flow">↓</div>'
        '<div class="flow">❤️ Emotional/contextual state</div>'
        '<div class="flow">↓</div>'
        '<div class="flow">⚡ Behavior</div>',
        unsafe_allow_html=True
    )

    # ---------- Profile ----------
    st.subheader("📊 Your Cognitive Profile")

    profile = {
        "Attention": attention_score,
        "Cognitive control": control_score,
        "Reward": reward_score,
        "Flexibility": flexibility_score,
        "Emotional load": emotional_score
    }

    st.bar_chart(profile)

    # ---------- Explanation ----------
    st.subheader("🧩 What may be happening?")

    st.write(
        f"Your responses indicate a pattern of **{pattern.lower()}** "
        f"in this self-report exercise."
    )

    st.write(
        "Stress and mental workload can influence how people allocate "
        "attention, evaluate uncertainty and make decisions. "
        "This result is an educational interpretation of your answers, "
        "not a measurement of brain activity."
    )

    # ---------- Research ----------
    st.subheader("📚 Research Lens")

    st.write(
        "Neuroscience research commonly examines decision-making through "
        "interacting processes involving cognitive control, valuation, "
        "attention and emotional/contextual information."
    )

    st.caption(
        "Future NeuroLens versions will connect individual modules "
        "to specific peer-reviewed research references."
    )

    # ---------- Disclaimer ----------
    st.warning(
        "This tool is not a medical or psychological diagnostic test. "
        "It does not directly measure brain activity."
    )

# ---------- Creator ----------
st.markdown(
    '<div class="creator">'
    
    '<b>NEUROLENS</b><br>'
    'Created & Research Lead: <b>Ayna Jaffri</b><br>'
    'Independent Researcher | Cognitive Neuroscience<br>'
    'Version 1.0'
    '</div>',
    unsafe_allow_html=True
) 
# 🎮 NEUROLENS COGNITIVE GAMES
st.divider()
st.header("🎮 Cognitive Games")

game = st.selectbox(
    "Choose a game",
    [
        "Select a game",
        "Decision Challenge",
        "Memory Challenge",
        "Attention Challenge"
    ]
)

if game == "Decision Challenge":
    st.subheader("🧠 Quick Decision Challenge")
    st.write("Choose the option you would prefer:")

    choice = st.radio(
        "Which would you choose?",
        [
            "Rs. 1,000 today",
            "Rs. 1,500 after 30 days"
        ]
    )

    if st.button("Analyze Decision"):
        if choice == "Rs. 1,000 today":
            st.success("Pattern: Immediate-reward preference")
        else:
            st.success("Pattern: Delayed-reward preference")

        st.info(
            "This educational task explores how people make choices "
            "between immediate and delayed rewards."
        )

elif game == "Memory Challenge":
    st.subheader("🧠 Memory Challenge")

    sequence = "7 2 9 4 1 8"
    st.write("Remember this sequence:")
    st.markdown(f"## **{sequence}**")

    answer = st.text_input("Enter the sequence from memory:")

    if st.button("Check Memory"):
        if answer.replace(" ", "") == "729418":
            st.success("🎉 Correct!")
            st.write("You recalled the sequence correctly.")
        else:
            st.error("Not quite. Try again.")

elif game == "Attention Challenge":
    st.subheader("🎯 Attention Challenge")

    target = st.radio(
        "Find the target letter: Which option contains **X**?",
        ["A B C D", "A B X D", "A B C E", "A B C F"]
    )

    if st.button("Check Attention"):
        if "X" in target:
            st.success("🎯 Correct!")
        else:
            st.error("Try again!")

st.caption(
    "Educational cognitive tasks only — these games are not diagnostic tests."
)
# =========================
# 🤖 ASK AYNA AI
# =========================

st.divider()
st.header("🤖 Ask Ayna 🧠")

st.write(
    "Ask questions about cognitive neuroscience, memory, attention, "
    "learning, emotions, decision-making and the brain."
)

if "ayna_messages" not in st.session_state:
    st.session_state.ayna_messages = []

for message in st.session_state.ayna_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask Ayna a neuroscience question...")

if question:
    st.session_state.ayna_messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )

        response = client.responses.create(
            model="gpt-5.6-luna",
            instructions="""
You are Ask Ayna, an educational cognitive neuroscience assistant.

Explain cognitive neuroscience clearly and scientifically.
You can discuss memory, attention, learning, emotion,
decision-making, reward, perception and cognitive control.

Do not diagnose medical or psychological disorders.
Do not claim that games measure actual brain activity.
Clearly explain uncertainty when scientific evidence is limited.
""",
            input=question
        )

        answer = response.output_text

        st.session_state.ayna_messages.append( 
            {"role": "assistant", "content": answer} 
    
        )

        with st.chat_message("assistant"):
            st.markdown(answer)

    except Exception as e:
        st.error(f"Ask Ayna error: {e}")

                 
