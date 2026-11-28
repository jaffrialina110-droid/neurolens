# Phase 1 Integration Review (Non-Destructive)

**Status:** Review only. This document does not authorize merging, deployment, database migration, or changes to production user data.

## Current verified architecture

The existing Streamlit application in `app.py` already owns the active account flow:

- `register_user(username, email, password, display_name)`
- `authenticate_user(identifier, password)`
- `page_account()`
- Existing SQLite `users` table with text IDs, username, email, PBKDF2 password hash + separate salt, display name, role, created timestamp, and active flag.
- Related `user_settings`, `ai_conversations`, `ai_messages`, `journal_entries`, `audit_logs`, and other user-owned tables.

The new Phase 1 `modules/auth.py` and `modules/storage.py` define a separate account/storage model:

- Integer auto-increment user IDs.
- `password_hash` stored as a combined salt:digest string.
- Different profile and activity tables.
- New standalone database path `neurolens.sqlite3` by default.

These schemas and identity formats are not interchangeable. Calling the new `render_auth()` or switching existing pages to `modules.auth.current_user()` would create a second account system and could orphan or mis-associate existing user data. **Do not wire the new auth module directly into the live app.**

## Credential configuration finding

The existing `app.py` reads `SUPABASE_KEY` and uses it to initialize a Supabase client when the URL and key are present. The key name does not prove whether the value is an anon/publishable key or a privileged service-role key. Treat it as potentially privileged until verified in the Supabase dashboard.

The new `modules/config.py` intentionally reads only `SUPABASE_ANON_KEY` and never falls back to `SUPABASE_KEY`. Keep that separation. Do not print, log, commit, or request secret values in chat. If the existing value is a service-role key, it must remain server-side only and must never be exposed to browser/client code.

## Safe integration decision

1. Keep the existing `app.py` account flow as the sole account source of truth during this review.
2. Do not run both auth systems in parallel for real users.
3. Before any migration, create a verified backup of the production SQLite database and test restore from that backup.
4. Inspect the actual deployed database location and persistence behavior. A local SQLite file on an ephemeral hosting filesystem is not a reliable production persistence strategy.
5. Prepare a read-only inventory of users and dependent records. Do not copy password hashes or private content to a staging environment unless the migration design explicitly requires it and the user approves.
6. Build a schema mapping and migration script that preserves existing user IDs or maintains a deterministic old-ID to new-ID mapping across every user-owned table.
7. Validate foreign-key relationships, row counts, duplicate usernames/emails, password verification compatibility, and rollback on a disposable staging copy.
8. Only after a separate Supabase staging project is configured, test Supabase Auth and Row Level Security using the anon/publishable key. Never use the service-role key in client code. Test each user's access isolation with separate test accounts.
9. Keep the PR in Draft until staging authentication, persistence, backup/restore, and privacy tests pass.

## Existing schema compatibility map

| Concern | Existing app | New isolated module | Integration requirement |
|---|---|---|---|
| User ID | Random text ID | SQLite integer ID | Preserve/map IDs before migration |
| Password storage | Separate salt + digest columns | Combined salt:digest | Explicit verifier/migration compatibility test |
| Account status | `active` flag and `role` | Not represented equivalently | Preserve authorization/status semantics |
| Settings | `user_settings` per account | Not present | Preserve language preference and future settings |
| AI history | Conversation + message tables | Not present | Define retention, export, deletion, and access controls |
| Private journal | Encrypted content field | Plain `content` column in new storage schema | Do not migrate into plaintext storage |
| Audit trail | `audit_logs` | `activity_log` | Define event mapping and retention |

## Current release gate

- [x] Isolated Phase 1 CI checks pass.
- [x] Existing account schema and new module schema compared.
- [x] Direct auth replacement identified as unsafe.
- [ ] Supabase staging project and non-production credentials configured.
- [ ] Existing database backup and successful restore verified.
- [ ] Persistent production storage plan verified.
- [ ] Migration/adapter tested on a disposable copy.
- [ ] Auth, RLS, account isolation, and private-data tests pass.
- [ ] Explicit approval before any merge or production deployment.

**Release decision: HOLD.** This branch is a tested foundation, not a production-ready account migration. Main branch and live deployment must remain unchanged until every release gate above is addressed.
