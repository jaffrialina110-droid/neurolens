# NeuroLens database backup safety

The Owner Control Center backup action snapshots the app's current SQLite
database at `APP_DIR / "neurolens_data.db"`. The main account, AI conversation,
journal, research, appointment, audit, and NeuroSocial tables are initialized
through the same `get_local_db()` connection, so they reside in this database.
The separate `modules/storage.py` database foundation is not used by the
current app's NeuroSocial initialization path.

The helper opens the source in read-only mode, uses SQLite's online backup API,
validates the snapshot with `PRAGMA integrity_check`, enforces a size limit,
and returns bytes plus a SHA-256 checksum. The Owner UI checks the authenticated
session email against the server-side `OWNER_EMAIL` secret before rendering
Owner controls.

## Important production limitations

- A downloadable database backup contains sensitive account and user content,
  including encrypted journal and AI records. Treat the downloaded file as
  highly confidential, store it securely, and never commit or publicly upload it.
- This action backs up the local SQLite file only. It does not back up
  Streamlit Secrets, source code, or a separately configured Supabase project.
- The code can identify the SQLite path but cannot establish whether the
  Streamlit Cloud filesystem is durable across restarts/redeploys. The Owner
  should download the file and retain it in secure storage.
- A restore test is automated against a separate temporary staging database;
  this is not a production restore and does not validate Streamlit Cloud storage.
- Before relying on backups operationally, test a controlled restore in a
  separate staging environment and confirm the restored app can start and
  read its data. Do not restore over the live database as part of this check.

## Deployment gate

No production database, user records, passwords, journal entries, deployment
settings, or live app deployment are changed by this code. Do not merge/deploy
until automated checks pass and the owner has downloaded a backup from the
deployed environment and a separate staging restore has been verified.
