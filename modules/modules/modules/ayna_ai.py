
"""NeuroLens — Ayna AI Assistant."""

import streamlit as st
from google import genai


SYSTEM_PROMPT = """
You are Ayna, the AI learning assistant inside NeuroLens.

Your focus:
- Cognitive neuroscience
- Brain and behaviour
- Learning, memory and attention
- Consciousness and awareness
- Decision-making and reward
- CSTC circuits
- Scientific research education

Communication:
- Understand Roman English, Urdu and English.
- Reply in the language used by the user.
- Explain difficult science in simple language.
- Be respectful, warm and scientifically accurate.
- Distinguish established evidence from hypotheses.

Safety:
- Never diagnose medical or mental health conditions.
- Never claim that NeuroLens games measure actual brain activity.
- Do not invent scientific references.
- Explain uncertainty and recommend qualified professionals
  for personal medical concerns.

You are an educational AI, not a human therapist or doctor.
"""


def get_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


def render(st):
    st.title("✨ Ask Ayna AI")

    st.write(
        "Explore cognition, behaviour and the brain "
        "with your AI learning companion."
    )

    if "ayna_ai_messages" not in st.session_state:
        st.session_state.ayna_ai_messages = []

    if st.button("Clear current chat"):
        st.session_state.ayna_ai_messages = []
        st.rerun()

    for message in st.session_state.ayna_ai_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask Ayna anything...")

    if prompt:
        st.session_state.ayna_ai_messages.append({
            "role": "user",
            "content": prompt,
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        client = get_client()

        if client is None:
            st.warning(
                "Ayna AI is not configured. "
                "GEMINI_API_KEY is missing from Streamlit Secrets."
            )
            return

        history = st.session_state.ayna_ai_messages[-12:]

        conversation = "\n".join(
            f"{item['role'].upper()}: {item['content']}"
            for item in history
        )

        full_prompt = (
            SYSTEM_PROMPT
            + "\n\nConversation:\n"
            + conversation
            + "\n\nRespond to the latest user message."
        )

        with st.chat_message("assistant"):
            try:
                with st.spinner("Ayna is thinking..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=full_prompt,
                    )

                    answer = response.text or (
                        "I couldn't generate a response. "
                        "Please try again."
                    )

                st.markdown(answer)

                st.session_state.ayna_ai_messages.append({
                    "role": "assistant",
                    "content": answer,
                })

            except Exception:
                st.error(
                    "Ayna AI is temporarily unavailable. "
                    "Please try again later."
                )
