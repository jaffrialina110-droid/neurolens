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
    return Settings(_secret("SUPABASE_URL"), _secret("SUPABASE_ANON_KEY") or _secret("SUPABASE_KEY"), _secret("GEMINI_API_KEY"))
