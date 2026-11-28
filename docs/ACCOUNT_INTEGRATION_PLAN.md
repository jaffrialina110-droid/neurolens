# NeuroLens Account Integration Plan

## Decision

Do not replace or call the new Phase 1 SQLite authentication module from the existing `app.py` account flow yet. The two systems currently use different account schemas and password-hash formats. A direct switch could create duplicate identities, orphan existing records, or lock existing users out.

Until a separately reviewed migration is approved, the existing `app.py` account implementation remains the only account source of truth for the live application. The Phase 1 modules remain isolated and must not be enabled in production.

## Verified schema differences

| Concern | Existing `app.py` | Phase 1 modules |
|---|---|---|
| User ID | Random text ID | SQLite integer ID |
| Password storage | Separate hash and salt fields | Combined `salt:digest` field |
| Account attributes | Includes role, active state and settings | Basic username, email and display name |
| Related data | Existing app-specific tables and ownership links | New isolated storage tables |
| Session | Existing Streamlit session keys | `nl_user` session key |

These are not interchangeable without a deliberate mapping and migration.

## Integration boundary

1. Keep the current login, registration and session flow unchanged.
2. Do not import `modules.auth.render_auth` into the current Account page.
3. Do not copy, rewrite, or reset existing password hashes as part of routine deployment.
4. Introduce a small account adapter only after its contract and tests are approved. The adapter must accept the existing authenticated user ID and resolve ownership without silently creating a second account.
5. Keep the existing application user ID as the stable external identity during the first integration. New module records should reference that identity through an explicit mapping table, not assume integer IDs match.
6. Any mapping table must enforce a unique existing-user ID and a unique Phase 1 user ID, and must be created through a versioned, backward-compatible migration.
7. Private journal content must not be copied into the new plaintext `journal_entries.content` column. A separate encryption-at-rest design and key-management review are mandatory first.

## Required gates before integration

- [ ] Create and configure a separate Supabase staging project; use only its project URL and public anon key in staging.
- [ ] Confirm the role and permissions of the existing `SUPABASE_KEY` without exposing its value in source, logs, screenshots or chat.
- [ ] Take and independently verify a backup of the production SQLite database before any migration or deployment.
- [ ] Inventory existing account and user-owned records; establish counts and orphan checks.
- [ ] Approve an identity-mapping and rollback plan.
- [ ] Add adapter tests for existing user lookup, duplicate mapping prevention, inactive accounts, missing users, and ownership isolation.
- [ ] Test migration against a copy of the production database, never the live database.
- [ ] Verify private-data access controls and encryption before moving journal or private AI content.
- [ ] Obtain explicit approval before production migration, merge or deployment.

## First safe implementation slice

The first integration slice should be read-only: resolve the currently authenticated legacy user to a stable account context and prove that existing data ownership remains unchanged. It must not create users, change passwords, migrate rows, or write private content. Only after this read-only adapter passes tests should a separate write-path proposal be considered.

## Current status

This document is an implementation plan, not evidence that staging, backup, migration, encryption, or production integration has been completed. The current PR remains a draft and must not be merged or deployed on the strength of isolated unit tests alone.
