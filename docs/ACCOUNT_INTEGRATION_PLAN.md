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
4. The standalone account adapter may be used only in a controlled test harness until integration is separately approved.
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

Implemented on the Phase 1 branch as a standalone, read-only adapter in `modules/account_adapter.py`:

- Accepts the existing app's authenticated `current_user()` dictionary shape.
- Preserves the legacy text user ID exactly; it does not coerce it to an integer.
- Returns only the minimum identity/profile context needed by a future integration.
- Rejects missing or malformed identity/profile fields.
- Does not access a database, authenticate a user, create an account, change a password, migrate rows, or write private content.
- Does not return password/hash/salt/token fields even if they appear in the input dictionary.

The adapter is intentionally not imported or called by `app.py`. Existing authentication and data ownership remain untouched. Unit tests cover the legacy session contract, invalid/missing values, exact ID preservation, minimal output, and exclusion of secret fields.

## Staging preparation artifacts

- `docs/STAGING_TEST_RUNBOOK.md` describes a staging-only test procedure and its preconditions.
- `.streamlit/secrets.staging.toml.example` is a placeholder template for a staging secret manager. It contains no real credentials and deliberately excludes privileged service-role keys and production values.
- `modules/config.py` reads only the explicit `SUPABASE_ANON_KEY`; it does not fall back to the legacy `SUPABASE_KEY`.

These artifacts are preparation only. No staging project, deployment, credentials, production backup, migration, or live-app integration is claimed.

## Current verification status

- GitHub Actions passed on commit `bf66673adf9f408918b9fa25b05a136903975144` for both push and pull-request workflows.
- GitHub Actions passed on commit `4717c031e5a7460ca05dad301df91733e382eef3` for both push and pull-request workflows.
- Later documentation/configuration commits must each receive their own CI result before they are described as verified.
- The PR remains a draft and must not be merged or deployed on the strength of isolated unit tests alone.
