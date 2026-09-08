# modules/behaviour.py
# NEUROLENS — AI Mood & Behaviour Lab

import streamlit as st


MOODS = {
    "😊": "Positive",
    "😌": "Calm",
    "😐": "Neutral",
    "😟": "Worried",
    "😔": "Low",
    "😤": "Frustrated",
    "😴": "Tired",
}


def _init_state():
    defaults = {
        "behaviour_result": None,
        "behaviour_text": "",
        "behaviour_language": "English",
        "behaviour_voice_count": 0,
        "behaviour_text_count": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _behaviour_css():

    st.markdown(
        """
        <style>

        .behaviour-title {
            font-size: 36px;
            font-weight: 900;
            margin-bottom: 4px;
        }

        .behaviour-subtitle {
            color: #9ca3af;
            margin-bottom: 24px;
        }

        .mood-card {
            padding: 28px;
            border-radius: 24px;
            text-align: center;
            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,.07),
                    rgba(255,255,255,.025)
                );
            border: 1px solid rgba(255,255,255,.10);
            margin-top: 20px;
        }

        .mood-emoji {
            font-size: 70px;
            margin-bottom: 8px;
        }

        .mood-name {
            font-size: 28px;
            font-weight: 800;
        }

        .mood-note {
            color: #aab4c0;
            margin-top: 10px;
        }

        .voice-panel {
            padding: 22px;
            border-radius: 20px;
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(255,255,255,.09);
            margin: 15px 0;
        }

        .brain-monitor {
            height: 90px;
            border-radius: 18px;
            position: relative;
            overflow: hidden;
            background: rgba(0,0,0,.18);
            border: 1px solid rgba(255,255,255,.08);
            margin: 18px 0;
        }

        .monitor-line {
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            height: 2px;
            background: rgba(120,190,255,.35);
        }

        .monitor-dot {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            top: calc(50% - 5px);
            animation: behaviourSignal 2s linear infinite;
        }

        @keyframes behaviourSignal {
            from {
                left: -10px;
            }

            to {
                left: 100%;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def _fallback_analysis(text):

    value = text.lower()

    if any(
        word in value
        for word in [
            "happy",
            "good",
            "great",
            "excited",
            "amazing",
            "khush",
            "acha",
            "achha",
        ]
    ):
        return {
            "emoji": "😊",
            "mood": "Positive",
            "message": (
                "Ayna ko tumhari language mein positive "
                "aur energetic pattern nazar aa raha hai."
            ),
        }

    if any(
        word in value
        for word in [
            "tired",
            "sleepy",
            "thak",
            "neend",
            "exhausted",
        ]
    ):
        return {
            "emoji": "😴",
            "mood": "Tired",
            "message": (
                "Tumhari baat mein tiredness ka pattern "
                "notice ho raha hai."
            ),
        }

    if any(
        word in value
        for word in [
            "sad",
            "upset",
            "cry",
            "low",
            "udaas",
            "dukhi",
        ]
    ):
        return {
            "emoji": "😔",
            "mood": "Low",
            "message": (
                "Tumhari baat mein low ya emotionally heavy "
                "pattern nazar aa raha hai."
            ),
        }

    if any(
        word in value
        for word in [
            "angry",
            "annoyed",
            "frustrated",
            "gussa",
            "ghussa",
        ]
    ):
        return {
            "emoji": "😤",
            "mood": "Frustrated",
            "message": (
                "Tumhari language mein frustration ka "
                "pattern notice ho raha hai."
            ),
        }

    if any(
        word in value
        for word in [
            "worried",
            "stress",
            "anxious",
            "tension",
            "pareshan",
            "fikar",
        ]
    ):
        return {
            "emoji": "😟",
            "mood": "Worried",
            "message": (
                "Tumhari baat mein worry ya tension ka "
                "pattern nazar aa raha hai."
            ),
        }

    if any(
        word in value
        for word in [
            "calm",
            "peace",
            "relaxed",
            "sukoon",
            "pur-sukoon",
        ]
    ):
        return {
            "emoji": "😌",
            "mood": "Calm",
            "message": (
                "Tumhari language relatively calm aur "
                "relaxed pattern show kar rahi hai."
            ),
        }

    return {
        "emoji": "😐",
        "mood": "Neutral",
        "message": (
            "Abhi available information se Ayna ko "
            "koi strong mood pattern clear nahi mila."
        ),
    }


def _ai_analysis(text):

    """
    AI analysis is optional.

    Agar Gemini available ho to AI use hoga.
    Agar API/secret/quota/error ho to local fallback chalega.
    """

    if not text.strip():
        return None

    try:

        from google import genai

        client = genai.Client()

        prompt = f"""
You are Ayna, an educational cognitive-neuroscience AI assistant.

Analyze the user's message for broad conversational mood/affective
signals.

User message:
{text}

Return ONLY valid JSON in this format:

{{
  "emoji": "😊",
  "mood": "Positive",
  "message": "short friendly explanation"
}}

Allowed mood labels:
Positive, Calm, Neutral, Worried, Low, Frustrated, Tired

Do not diagnose a mental-health condition.
Do not claim certainty.
Keep the explanation friendly and concise.
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        raw = response.text.strip()

        import json

        result = json.loads(raw)

        emoji = result.get("emoji", "😐")
        mood = result.get("mood", "Neutral")
        message = result.get(
            "message",
            "Ayna ko abhi koi strong pattern clear nahi mila.",
        )

        if mood not in MOODS.values():
            mood = "Neutral"

        if emoji not in MOODS:
            emoji = "😐"

        return {
            "emoji": emoji,
            "mood": mood,
            "message": message,
        }

    except Exception:
        return _fallback_analysis(text)


def _voice_output(text):

    safe_text = (
        text
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", " ")
    )

    st.markdown(
        f"""
        <button
            onclick="
                const text = '{safe_text}';
                const speech =
                    new SpeechSynthesisUtterance(text);

                speech.lang = 'en-US';

                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(speech);
            "
            style="
                width:100%;
                padding:13px;
                border:none;
                border-radius:12px;
                cursor:pointer;
                font-weight:700;
            "
        >
            🔊 Ayna Speak
        </button>
        """,
        unsafe_allow_html=True,
    )


def _analyse_voice(audio):

    """
    Browser/Streamlit audio is received here.

    Full speech-to-text depends on the transcription backend/API.
    If transcription is unavailable, the app does not crash.
    """

    if audio is None:
        return None

    try:

        # Try optional Gemini audio understanding.
        from google import genai

        client = genai.Client()

        audio_bytes = audio.getvalue()

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                {
                    "mime_type": "audio/wav",
                    "data": audio_bytes,
                },
                """
Listen to this user's voice recording.

Estimate broad conversational affective signals
from tone/content where possible.

Return ONLY JSON:

{
  "emoji": "😊",
  "mood": "Positive",
  "message": "short friendly explanation"
}

Allowed mood:
Positive, Calm, Neutral, Worried, Low, Frustrated, Tired

Do not diagnose.
Do not claim certainty.
""",
            ],
        )

        raw = response.text.strip()

        import json

        result = json.loads(raw)

        emoji = result.get("emoji", "😐")
        mood = result.get("mood", "Neutral")
        message = result.get(
            "message",
            "Ayna ko voice se koi strong pattern clear nahi mila.",
        )

        if emoji not in MOODS:
            emoji = "😐"

        if mood not in MOODS.values():
            mood = "Neutral"

        return {
            "emoji": emoji,
            "mood": mood,
            "message": message,
        }

    except Exception:

        return {
            "emoji": "🎙️",
            "mood": "Voice received",
            "message": (
                "Ayna ne tumhari voice recording receive kar li. "
                "Detailed voice analysis ke liye AI audio service "
                "available honi zaroori hai."
            ),
        }


def behaviour_screen():

    _init_state()
    _behaviour_css()

    st.markdown(
        """
        <div class="behaviour-title">
            🧠 AI Mood & Behaviour Lab
        </div>

        <div class="behaviour-subtitle">
            Talk to Ayna and explore patterns in your
            current conversational state.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------
    # LANGUAGE
    # -----------------------------------------

    language = st.radio(
        "Ayna language",
        [
            "English",
            "Roman English",
        ],
        horizontal=True,
        key="behaviour_language_selector",
    )

    st.session_state.behaviour_language = language

    # -----------------------------------------
    # BRAIN MONITOR
    # -----------------------------------------

    st.markdown(
        """
        <div class="brain-monitor">

            <div class="monitor-line"></div>

            <div class="monitor-dot"></div>

            <div
                class="monitor-dot"
                style="animation-delay:.7s;"
            ></div>

            <div
                class="monitor-dot"
                style="animation-delay:1.4s;"
            ></div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------
    # VOICE
    # -----------------------------------------

    st.markdown(
        """
        <div class="voice-panel">

        ### 🎙️ Talk to Ayna

        Speak naturally and press **Send Voice**.

        </div>
        """,
        unsafe_allow_html=True,
    )

    audio = st.audio_input(
        "Record your voice"
    )

    if st.button(
        "🎙️ Send Voice",
        use_container_width=True,
        type="primary",
    ):

        if audio is None:

            st.warning(
                "Pehle voice record karo."
            )

        else:

            with st.spinner(
                "🧠 Ayna is analysing your voice..."
            ):

                result = _analyse_voice(audio)

            st.session_state.behaviour_result = result
            st.session_state.behaviour_voice_count += 1

            st.rerun()

    # -----------------------------------------
    # TEXT
    # -----------------------------------------

    st.markdown("---")

    st.markdown(
        "### 📝 Or type to Ayna"
    )

    text = st.text_area(
        "Your message",
        placeholder=(
            "Tell Ayna how you feel, what happened, "
            "or simply talk about your day..."
        ),
        key="behaviour_text_input",
        height=110,
    )

    if st.button(
        "📤 Send Text",
        use_container_width=True,
    ):

        if not text.strip():

            st.warning(
                "Pehle kuch text likho."
            )

        else:

            with st.spinner(
                "🧠 Ayna is analysing..."
            ):

                result = _ai_analysis(text)

            st.session_state.behaviour_result = result
            st.session_state.behaviour_text = text
            st.session_state.behaviour_text_count += 1

            st.rerun()

    # -----------------------------------------
    # RESULT
    # -----------------------------------------

    result = st.session_state.behaviour_result

    if result:

        st.markdown("---")

        st.markdown(
            "### 🔬 Ayna's Behaviour Read"
        )

        st.markdown(
            f"""
            <div class="mood-card">

                <div class="mood-emoji">
                    {result["emoji"]}
                </div>

                <div class="mood-name">
                    {result["mood"]}
                </div>

                <div class="mood-note">
                    {result["message"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # -------------------------------------
        # VOICE RESPONSE
        # -------------------------------------

        st.markdown("### 🔊 Ayna's Voice")

        _voice_output(
            result["message"]
        )

        st.caption(
            "Mood result is an AI-based conversational estimate, "
            "not a clinical diagnosis."
        )

        # -------------------------------------
        # RESET
        # -------------------------------------

        if st.button(
            "🔄 New Analysis",
            use_container_width=True,
        ):

            st.session_state.behaviour_result = None
            st.session_state.behaviour_text = ""

            st.rerun()


def render():
    behaviour_screen()
