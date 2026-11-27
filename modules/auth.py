import streamlit as st
from supabase import create_client
from modules.config import get_settings

def get_supabase():
    """Return a client scoped to this Streamlit user's session, never a global cache."""
    cfg = get_settings()
    if not cfg.supabase_url or not cfg.supabase_anon_key:
        raise RuntimeError("Supabase URL and anon/public key are required.")
    client = st.session_state.get("_neurolens_supabase_client")
    if client is None:
        client = create_client(cfg.supabase_url, cfg.supabase_anon_key)
        st.session_state["_neurolens_supabase_client"] = client
    return client

def sign_in(email: str, password: str):
    if not email.strip() or not password:
        raise ValueError("Email and password are required.")
    return get_supabase().auth.sign_in_with_password(
        {"email": email.strip(), "password": password}
    )

def sign_up(email: str, password: str):
    if not email.strip() or len(password) < 10:
        raise ValueError("Use a valid email and a password of at least 10 characters.")
    return get_supabase().auth.sign_up(
        {"email": email.strip(), "password": password}
    )

def sign_out():
    client = st.session_state.get("_neurolens_supabase_client")
    try:
        if client is not None:
            client.auth.sign_out()
    finally:
        st.session_state.pop("_neurolens_supabase_client", None)
        st.session_state.auth_user = None
        st.session_state.auth_session = None
        st.session_state.chat_history = []
