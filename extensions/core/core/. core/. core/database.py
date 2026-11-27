"""
NeuroLens Supabase connection.

This module only creates a connection.
It does not modify, delete, or migrate existing tables.
"""

import streamlit as st
from supabase import create_client


@st.cache_resource
def get_supabase_client():
    """Create and cache the Supabase client."""

    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]

        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials are missing.")

        return create_client(
            supabase_url,
            supabase_key
        )

    except KeyError as error:
        raise RuntimeError(
            "Supabase configuration is missing from Streamlit Secrets."
        ) from error

    except Exception as error:
        raise RuntimeError(
            "Unable to initialize Supabase connection."
        ) from error


def test_connection():
    """Check whether the Supabase client can communicate."""

    try:
        client = get_supabase_client()

        # Read-only check; no table data is modified.
        response = client.table("profiles").select(
            "id"
        ).limit(1).execute()

        return {
            "success": True,
            "message": "Supabase connection is working."
        }

    except Exception:
        return {
            "success": False,
            "message": "Supabase connection could not be verified."
        }
