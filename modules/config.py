"""Centralized, safe configuration for NeuroLens Phase 1."""

from dataclasses import dataclass
import os

import streamlit as st


def _secret(name):
    """Read a named Streamlit secret, then environment fallback."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    if not value:
        value = os.environ.get(name, "")
    return str(value or "").strip()


@dataclass(frozen=True)
class Settings:
    supabase_url: str = ""
    supabase_anon_key: str = ""
    gemini_api_key: str = ""


def get_settings():
    """Return only explicitly configured public/client-safe settings.

    Never fall back from SUPABASE_ANON_KEY to legacy SUPABASE_KEY:
    the latter may contain a privileged service-role credential.
    """
    return Settings(
        supabase_url=_secret("SUPABASE_URL"),
        supabase_anon_key=_secret("SUPABASE_ANON_KEY"),
        gemini_api_key=_secret("GEMINI_API_KEY"),
    )
