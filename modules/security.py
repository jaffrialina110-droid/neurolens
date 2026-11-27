# modules/security.py
# NEUROLENS — Private Session Security

import hashlib
import streamlit as st


DEFAULT_PIN_HASH = hashlib.sha256(
    "1234".encode()
).hexdigest()


def _init_security():

    defaults = {
        "security_locked": True,
        "security_pin_hash": DEFAULT_PIN_HASH,
        "private_chat": [],
        "private_session": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


def _hash_pin(pin):

    return hashlib.sha256(
        pin.encode()
    ).hexdigest()


def _unlock_screen():

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:35px 10px;
        ">

            <div style="font-size:55px;">
                🔐
            </div>

            <h2>Private Ask Ayna</h2>

            <p>
                Enter your PIN to open your private session.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    pin = st.text_input(
        "PIN",
        type="password",
        max_chars=20,
        placeholder="Enter PIN",
    )

    if st.button(
        "🔓 Unlock",
        use_container_width=True,
        type="primary",
    ):

        if _hash_pin(pin) == st.session_state.security_pin_hash:

            st.session_state.security_locked = False
            st.session_state.private_session = True

            st.rerun()

        else:

            st.error(
                "Incorrect PIN."
            )


def _private_chat():

    st.markdown(
        """
        <div style="
            padding:20px;
            border-radius:20px;
            background:rgba(255,255,255,.04);
            border:1px solid rgba(255,255,255,.09);
        ">

        <h2>🔒 Private Ask Ayna</h2>

        <p>
        This is your private conversation space with Ayna.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------
    # CHAT HISTORY
    # -----------------------------------------

    for message in st.session_state.private_chat:

        role = message["role"]
        content = message["content"]

        if role == "user":

            with st.chat_message("user"):
                st.write(content)

        else:

            with st.chat_message("assistant"):
                st.write(content)

    # -----------------------------------------
    # INPUT
    # -----------------------------------------

    user_message = st.chat_input(
        "Talk privately with Ayna..."
    )

    if user_message:

        st.session_state.private_chat.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        response = _ask_private_ai(
            user_message
        )

        st.session_state.private_chat.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        st.rerun()

    # -----------------------------------------
    # CONTROLS
    # -----------------------------------------

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🗑️ Clear Chat",
            use_container_width=True,
        ):

            st.session_state.private_chat = []

            st.rerun()

    with col2:

        if st.button(
            "🔒 Lock",
            use_container_width=True,
        ):

            st.session_state.security_locked = True
            st.session_state.private_session = False

            st.rerun()

    # -----------------------------------------
    # PIN CHANGE
    # -----------------------------------------

    st.markdown("---")

    with st.expander(
        "⚙️ Change Private PIN"
    ):

        current_pin = st.text_input(
            "Current PIN",
            type="password",
            key="current_private_pin",
        )

        new_pin = st.text_input(
            "New PIN",
            type="password",
            key="new_private_pin",
        )

        confirm_pin = st.text_input(
            "Confirm New PIN",
            type="password",
            key="confirm_private_pin",
        )

        if st.button(
            "Change PIN",
            use_container_width=True,
        ):

            if _hash_pin(current_pin) != (
                st.session_state.security_pin_hash
            ):

                st.error(
                    "Current PIN is incorrect."
                )

            elif len(new_pin) < 4:

                st.error(
                    "PIN must contain at least 4 characters."
                )

            elif new_pin != confirm_pin:

                st.error(
                    "New PINs do not match."
                )

            else:

                st.session_state.security_pin_hash = (
                    _hash_pin(new_pin)
                )

                st.success(
                    "Private PIN changed successfully."
                )


def _ask_private_ai(user_message):

    """
    Lightweight private-chat AI.

    Only the latest user message is sent.
    The complete chat history is NOT sent every time.
    This helps reduce token usage.
    """

    try:

        from google import genai

        client = genai.Client()

        prompt = f"""
You are Ayna, the private AI companion inside NEUROLENS.

User message:
{user_message}

Reply naturally and briefly.

You may discuss:
- emotions
- behaviour
- decisions
- cognitive neuroscience
- learning
- attention
- memory
- general life problems

Be supportive and non-judgmental.

Do not claim to be a doctor or therapist.
Do not diagnose mental-health conditions.
Do not pretend to know facts about the user that were not provided.

Keep the answer concise.
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        text = response.text.strip()

        if text:

            return text

    except Exception:
        pass

    return _local_private_response(
        user_message
    )


def _local_private_response(message):

    text = message.lower()

    if any(
        word in text
        for word in [
            "sad",
            "upset",
            "udaas",
            "dukhi",
        ]
    ):

        return (
            "Ayna sun rahi hai. Tum jo feel kar rahi ho "
            "usko words mein express karna useful ho sakta hai. "
            "Agar chaho to situation ko step-by-step explore karte hain."
        )

    if any(
        word in text
        for word in [
            "stress",
            "tension",
            "worried",
            "pareshan",
        ]
    ):

        return (
            "Lagta hai situation tumhare liye mentally demanding hai. "
            "Pehle problem ko small parts mein divide karna "
            "helpful ho sakta hai."
        )

    if any(
        word in text
        for word in [
            "decision",
            "decide",
            "choice",
            "faisla",
        ]
    ):

        return (
            "Decision ko samajhne ke liye options, possible outcomes "
            "aur tumhare main goal ko separately dekhna useful hoga."
        )

    return (
        "Ayna yahan hai. Tum apni baat share kar sakti ho, "
        "aur hum usay calmly explore kar sakte hain."
    )


def security_screen():

    _init_security()

    if st.session_state.security_locked:

        _unlock_screen()

        return

    _private_chat()


def render():

    security_screen()
