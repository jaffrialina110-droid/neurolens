from dataclasses import dataclass
import os
import streamlit as st

@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    gemini_api_key: str

def _secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, "")).strip()

def get_settings() -> Settings:
    # Deliberately accept only the anon/public key. Never fall back to a
    # generically named key that could contain the Supabase service_role secret.
    return Settings(
        supabase_url=_secret("SUPABASE_URL"),
        supabase_anon_key=_secret("SUPABASE_ANON_KEY"),
        gemini_api_key=_secret("GEMINI_API_KEY"),
    )
