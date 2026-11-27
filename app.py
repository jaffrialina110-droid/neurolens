import streamlit as st
from modules.config import get_settings
from modules.i18n import t
from modules.auth import sign_in, sign_up, sign_out
from modules.ai import ask_ayna

st.set_page_config(page_title="NeuroLens", page_icon="🧠", layout="wide")
settings = get_settings()
for key, default in {"language": "Roman English", "auth_user": None, "auth_session": None, "chat_history": []}.items():
    if key not in st.session_state:
        st.session_state[key] = default
st.title("🧠 NeuroLens")
st.caption("Explore cognition, behavior & the brain")
st.sidebar.selectbox(t(st.session_state.language, "language"), ["Roman English", "English"], key="language")
lang = st.session_state.language
with st.sidebar:
    st.subheader(t(lang, "account"))
    if st.session_state.auth_user:
        st.success(t(lang, "signed_in"))
        if st.button(t(lang, "sign_out"), use_container_width=True):
            sign_out(); st.rerun()
    else:
        mode = st.radio(t(lang, "account_action"), ["Sign in", "Create account"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if mode == "Sign in":
            if st.button(t(lang, "sign_in"), use_container_width=True):
                try:
                    result = sign_in(email, password)
                    st.session_state.auth_user, st.session_state.auth_session = result.user, result.session
                    st.rerun()
                except Exception:
                    st.error(t(lang, "auth_error"))
        elif st.button(t(lang, "create_account"), use_container_width=True):
            try:
                sign_up(email, password); st.success(t(lang, "signup_check_email"))
            except Exception:
                st.error(t(lang, "auth_error"))
home, ai, roadmap = st.tabs([t(lang, "home"), t(lang, "ayna_ai"), t(lang, "roadmap")])
with home:
    st.subheader(t(lang, "welcome")); st.write(t(lang, "welcome_body")); st.info(t(lang, "privacy_note"))
with ai:
    st.subheader("Ayna AI"); st.caption(t(lang, "ai_disclaimer"))
    if not settings.gemini_api_key: st.warning(t(lang, "ai_not_configured"))
    prompt = st.chat_input(t(lang, "ask_placeholder"))
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]): st.markdown(item["content"])
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            try: answer = ask_ayna(prompt, lang, settings.gemini_api_key)
            except Exception: answer = t(lang, "ai_error")
            st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
with roadmap:
    st.subheader(t(lang, "phase1")); st.markdown("- Supabase authentication foundation\n- Roman English / English interface\n- Gemini Ayna AI text-chat foundation\n- Modular architecture for later extensions")
    st.warning(t(lang, "not_complete"))
