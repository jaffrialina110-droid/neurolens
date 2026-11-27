# NeuroLens Platform — Phase 1 Foundation

Isolated starter foundation on branch `neurolens-platform-phase1`.
The production `main` branch and live deployment are not changed by this work.

## Included
- Streamlit starter interface
- Roman English / English selector
- Supabase email/password authentication foundation
- Per-Streamlit-session Supabase client (not a shared global client)
- Gemini Ayna AI text-chat foundation
- Modular Python structure and secret configuration
- Basic unit tests and GitHub Actions checks

## Not included yet
Production data migration, private journal/PIN, encrypted private AI history, NeuroSocial,
camera/AR, voice, games, learning biography, research library, owner/staff tools,
payments, appointments, or a complete production security review.

## Setup
Configure Streamlit secrets using `.streamlit/secrets.toml.example`.
Use the Supabase anon/public key only. Never use `service_role` in this Streamlit client app.
Configure Supabase Auth redirect URLs for the deployed app.
Enable and test RLS on every user-owned table before storing user data.

No existing SQLite or Supabase production data has been imported. Do not connect this
starter to production data until backup, restore, schema, and RLS reviews are complete.
This branch has not yet been deployed or production-security reviewed.
