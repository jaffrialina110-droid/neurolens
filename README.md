# NeuroLens Platform — Phase 1 Foundation

Separate starter foundation. The live app's `main` branch is unchanged.

Included: Streamlit UI, Roman English/English selector, Supabase email/password auth foundation, Gemini Ayna AI text chat, modular Python structure.

Not included: production data migration, private journal/PIN, NeuroSocial, camera/AR, voice, games, biography, research library, owner/staff tools, payments, or production security review.

Configure Streamlit secrets from `.streamlit/secrets.toml.example`. Use Supabase anon/public key only; never use service_role in a client app. Enable and test RLS before storing user-owned data. No existing production data has been imported. Not deployed or production-security reviewed.
