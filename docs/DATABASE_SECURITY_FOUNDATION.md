# NeuroLens database and security foundation — implementation notes

## Safety boundary

This branch is a preflight stage. It does not change the production application,
database schemas, user records, passwords, journal entries, or deployment settings.
The default `main` branch remains untouched.

## Confirmed database designs

The current code contains two independent SQLite foundations:

1. The main application in `app.py` uses `APP_DIR / "neurolens_data.db"`.
   Its `users.id` is TEXT and it stores `password_hash` plus `password_salt`.
2. `modules/storage.py` uses `NEUROLENS_DB` or `neurolens.sqlite3`.
   Its `users.id` is an AUTOINCREMENT INTEGER and its account module stores
   a combined PBKDF2 value in `password_hash`.

These schemas are not interchangeable. In particular, the `users` table
definitions and user ID types differ. A direct table copy or changing the active
database path could break account ownership and foreign-key relationships.

## Read-only preflight

Run this command in an environment where the actual database files are present:

```bash
python -m scripts.database_migration_preflight neurolens_data.db neurolens.sqlite3
```

The report includes database integrity, foreign-key violation counts, table
names, column metadata, and row counts. It never prints record contents and
opens databases in SQLite read-only mode. It does not create a missing database.

## Required next migration steps

1. Run the preflight against a verified backup and the live data files.
2. Confirm which database is actually used by the deployed app and whether
   either file contains production user data.
3. Design an explicit identity mapping between TEXT and INTEGER user IDs.
4. Map each dependent table and verify ownership/foreign-key relationships.
5. Preserve password hashes only after verifying their formats and login paths.
6. Preserve encrypted journal payloads and their encryption-key availability;
   never attempt to decrypt/re-encrypt without the original key material.
7. Build an idempotent, transactional migration with pre/post row-count checks.
8. Test on a copy, verify login and per-user isolation, then schedule a
   controlled deployment with a tested rollback.

## Security finding

`modules/security.py` contains a legacy session PIN implementation with a
hardcoded default PIN and unsalted SHA-256. Do not use it for private data.
The main app has a separate vault implementation; keep the two implementations
distinct until import/call sites and deployed behavior have been traced. The
legacy module must not be silently replaced until those call sites are known.

## Release gate

No production database migration or security-module replacement should be
merged until the actual deployment database files, imports/call sites,
encryption-key configuration, and rollback procedure have been verified.
