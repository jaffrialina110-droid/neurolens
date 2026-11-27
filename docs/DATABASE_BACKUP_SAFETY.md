# NeuroLens database backup safety

The `modules/db_backup.py` helper creates a consistent SQLite snapshot using
SQLite's online backup API. It opens the source in read-only mode, validates
the snapshot with `PRAGMA integrity_check`, enforces a size limit, and returns
the bytes plus a SHA-256 checksum helper.

## Production integration gate

This helper is not itself a user-facing download control. Before enabling a
production Owner-only download:
1. Verify the authenticated Owner identity server-side (never rely on a hidden button).
2. Add a clearly labelled Owner Control Center download action.
3. Confirm the production database location and whether Streamlit Cloud's local
   filesystem is persistent. If the app uses Supabase as its authoritative
   store, a SQLite file backup is not a backup of Supabase data.
4. Keep backup files out of the public repository and application static paths.
5. Test restore into a separate staging database before relying on a backup.
6. Do not expose passwords, API keys, or Streamlit Secrets in the backup package.

The current helper does not access Streamlit Cloud, Supabase backups, or
deployment secrets and does not deploy or alter production data.
