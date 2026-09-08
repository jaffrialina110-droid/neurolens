# modules/ayna.py

import streamlit as st
import streamlit.components.v1 as components
import os
from typing import Optional


# =========================================================
# AYNA — AI ASSISTANT CORE
# =========================================================

def get_language():
    """Return the currently selected Ayna language."""
    return st.session_state.get("ayna_language", "English")


def language_selector():
    """English / Roman English buttons."""
    
    current = get_language()

    choice = st.radio(
        "Ayna language",
        ["English", "Roman English"],
        index=0 if current == "English" else 1,
        horizontal=True,
        key="ayna_language_selector",
    )

    st.session_state["ayna_language"] = choice
    return choice


def browser_voice(text: str):
    """
    Browser-based Ayna voice.
    Works on most modern PC/mobile browsers.
    """

    if not text:
        return

    safe_text = (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("</script>", "")
    )

    components.html(
        f"""
        <script>
        const text = `{safe_text}`;

        if ("speechSynthesis" in window) {{
            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);

            utterance.rate = 0.92;
            utterance.pitch = 1.02;
            utterance.volume = 1.0;

            window.speechSynthesis.speak(utterance);
        }}
        </script>
        """,
        height=1,
    )


def local_fallback(question: str, language: str = "English") -> str:
    """
    Safe local response when AI/API is unavailable.
    This prevents the whole app from crashing.
    """

    q = question.lower().strip()

    if language == "Roman English":

        if any(x in q for x in ["memory", "yaad", "memory"]):
            return (
                "Memory brain ka aik complex process hai. "
                "Is mein information ko encode, store aur baad mein retrieve kiya jata hai."
            )

        if any(x in q for x in ["attention", "focus", "tawajjo"]):
            return (
                "Attention ka matlab hai brain ka available information mein se "
                "kisi important cheez par resources focus karna."
            )

        if any(x in q for x in ["stress", "tension"]):
            return (
                "Stress ke waqt brain attention aur decision-making ko different "
                "tareeqe se handle kar sakta hai. Short-term stress kabhi alertness "
                "barha sakta hai, jab ke prolonged stress cognitive performance ko affect kar sakta hai."
            )

        return (
            "Main is waqt AI response generate nahi kar pa rahi, "
            "lekin aapka sawal cognitive neuroscience ke perspective se important hai. "
            "Dobara try karein."
        )

    # English fallback

    if "memory" in q:
        return (
            "Memory is a complex cognitive process involving encoding, "
            "storage, and later retrieval of information."
        )

    if "attention" in q or "focus" in q:
        return (
            "Attention is the process of selectively allocating cognitive "
            "resources to information that is currently relevant."
        )

    if "stress" in q:
        return (
            "Stress can change attention, decision-making, and cognitive performance. "
            "Short-term stress may increase alertness, while prolonged stress can interfere "
            "with some cognitive processes."
        )

    return (
        "I couldn't reach the AI system right now, but your question is relevant "
        "to cognitive neuroscience. Please try again."
    )


def call_gemini(question: str, context: str = "") -> Optional[str]:
    """
    Gemini call.

    The API key is read from Streamlit secrets or environment variables.
    Nothing is hard-coded here.
    """

    try:
        from google import genai

        api_key = None

        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            return None

        client = genai.Client(api_key=api_key)

        language = get_language()

        if language == "Roman English":
            language_instruction = """
Respond in simple Roman English / Roman Urdu.
Do not use Urdu script.
Keep scientific terminology accurate.
"""
        else:
            language_instruction = """
Respond in clear, simple scientific English.
Keep the explanation understandable for normal users.
"""

        prompt = f"""
You are Ayna, the AI cognitive neuroscience assistant inside NEUROLENS.

NEUROLENS explores:
- cognitive neuroscience
- brain and behaviour
- attention
- memory
- perception
- emotion
- decision making
- learning
- cognitive control
- reward
- neural circuits
- neuroplasticity
- AI and human cognition

{language_instruction}

Current context:
{context}

User question:
{question}

Rules:
1. Answer directly.
2. Be scientifically responsible.
3. Do not invent research findings.
4. Do not claim to diagnose a mental or medical condition.
5. Keep the answer reasonably concise.
6. If the user asks about their personal mood or behaviour, describe possibilities rather than giving a diagnosis.
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

    except Exception:
        return None

    return None


def ask_ayna(
    question: str,
    context: str = "",
    speak: bool = True,
):
    """
    Main Ayna response function.
    """

    if not question or not question.strip():
        return ""

    language = get_language()

    # Cache identical questions during the current session.
    cache_key = (
        f"{language}|{context}|{question.strip().lower()}"
    )

    if "ayna_cache" not in st.session_state:
        st.session_state["ayna_cache"] = {}

    if cache_key in st.session_state["ayna_cache"]:
        answer = st.session_state["ayna_cache"][cache_key]

        if speak:
            browser_voice(answer)

        return answer

    answer = call_gemini(
        question=question,
        context=context,
    )

    if not answer:
        answer = local_fallback(
            question=question,
            language=language,
        )

    st.session_state["ayna_cache"][cache_key] = answer

    # Prevent unlimited session-memory growth.
    if len(st.session_state["ayna_cache"]) > 100:
        first_key = next(iter(st.session_state["ayna_cache"]))
        del st.session_state["ayna_cache"][first_key]

    if speak:
        browser_voice(answer)

    return answer


# =========================================================
# VOICE INPUT
# =========================================================

def voice_input():
    """
    Native Streamlit microphone recorder.

    Returns an audio object or None.
    """

    try:
        return st.audio_input(
            "🎙️ Speak to Ayna",
            key="ayna_voice_input",
        )
    except Exception:
        return None


def analyse_voice_with_ai(audio_file, context: str = ""):
    """
    Send recorded voice to Gemini when available.

    The model is asked to understand the spoken content.
    """

    if audio_file is None:
        return None

    try:
        from google import genai

        api_key = None

        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            return None

        client = genai.Client(api_key=api_key)

        language = get_language()

        if language == "Roman English":
            language_instruction = (
                "Return the response in simple Roman English / Roman Urdu."
            )
        else:
            language_instruction = (
                "Return the response in clear English."
            )

        audio_bytes = audio_file.getvalue()

        uploaded = client.files.upload(
            file=audio_bytes,
            config={
                "mime_type": "audio/wav"
            },
        )

        prompt = f"""
You are Ayna inside NEUROLENS.

Listen to the user's recorded voice.

{language_instruction}

Current context:
{context}

Do the following:
1. Understand what the user said.
2. Respond naturally to the actual question or statement.
3. If the user is discussing mood or behaviour, describe observable possibilities,
   not a medical diagnosis.
4. Keep the answer concise.
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[uploaded, prompt],
        )

        text = getattr(response, "text", None)

        if text:
            return text.strip()

    except Exception:
        return None

    return None


# =========================================================
# ASK AYNA CHAT UI
# =========================================================

def render_ask_ayna(context: str = "General NEUROLENS conversation"):
    """
    Full Ask Ayna interface.

    Supports:
    - English
    - Roman English
    - text input
    - voice input
    - AI text response
    - browser voice response
    """

    st.markdown("## 🧠 Ask Ayna")

    st.caption(
        "Talk to Ayna about cognition, behaviour, the brain, "
        "your current experiment, or what you are exploring."
    )

    language_selector()

    if "ayna_messages" not in st.session_state:
        st.session_state["ayna_messages"] = []

    # -----------------------------------------------------
    # Existing conversation
    # -----------------------------------------------------

    for message in st.session_state["ayna_messages"][-8:]:

        role = message.get("role", "user")
        text = message.get("text", "")

        if role == "user":
            with st.chat_message("user"):
                st.write(text)

        else:
            with st.chat_message("assistant"):
                st.write("🧠 Ayna")
                st.write(text)

    # -----------------------------------------------------
    # Text input
    # -----------------------------------------------------

    text_question = st.text_input(
        "Type your question",
        placeholder="Ask Ayna anything about the brain...",
        key="ayna_text_question",
    )

    if st.button(
        "📤 Send Text",
        key="ayna_send_text",
        use_container_width=True,
    ):

        if text_question.strip():

            st.session_state["ayna_messages"].append(
                {
                    "role": "user",
                    "text": text_question.strip(),
                }
            )

            answer = ask_ayna(
                question=text_question.strip(),
                context=context,
                speak=False,
            )

            st.session_state["ayna_messages"].append(
                {
                    "role": "assistant",
                    "text": answer,
                }
            )

            browser_voice(answer)

            st.rerun()

    # -----------------------------------------------------
    # Voice
    # -----------------------------------------------------

    st.markdown("### 🎙️ Voice")

    audio = voice_input()

    if st.button(
        "📤 Send Voice to Ayna",
        key="ayna_send_voice",
        use_container_width=True,
    ):

        if audio is None:

            st.warning(
                "Please record your voice first."
            )

        else:

            with st.spinner("Ayna is listening..."):

                answer = analyse_voice_with_ai(
                    audio_file=audio,
                    context=context,
                )

            if not answer:

                answer = (
                    "I couldn't process the voice recording right now. "
                    "Please try again or use text."
                )

            st.session_state["ayna_messages"].append(
                {
                    "role": "user",
                    "text": "🎙️ Voice message",
                }
            )

            st.session_state["ayna_messages"].append(
                {
                    "role": "assistant",
                    "text": answer,
                }
            )

            browser_voice(answer)

            st.rerun()


# =========================================================
# CONTEXTUAL AYNA
# =========================================================

def contextual_ayna(stage_name: str, stage_description: str):
    """
    Ayna interface for a specific Brain Journey stage.
    """

    context = f"""
Brain Journey current stage:
{stage_name}

Stage information:
{stage_description}
"""

    st.markdown("### 🧠 Ask Ayna about this stage")

    language_selector()

    question = st.text_input(
        "Your question",
        key=f"stage_question_{stage_name}",
        placeholder=f"Ask Ayna about {stage_name}...",
    )

    if st.button(
        "📤 Send",
        key=f"stage_send_{stage_name}",
        use_container_width=True,
    ):

        if question.strip():

            answer = ask_ayna(
                question=question,
                context=context,
                speak=False,
            )

            st.markdown("#### 🧠 Ayna")
            st.write(answer)

            if st.button(
                "🔊 Hear Ayna",
                key=f"stage_voice_{stage_name}",
            ):
                browser_voice(answer)
