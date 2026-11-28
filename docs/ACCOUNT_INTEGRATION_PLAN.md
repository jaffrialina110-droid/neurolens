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

## Trusted server-session context wrapper (isolated test boundary)

Added `modules/authenticated_context.py` as a narrow, read-only wrapper around
the existing server-side `current_user` accessor:

- It accepts a callable and invokes it once; it does not accept a user dictionary
  supplied directly by a form, URL, request payload, or browser.
- It validates the returned session user through the existing read-only adapter.
- It returns a frozen context containing the exact legacy text ID and minimal
  profile fields; no password/hash/salt/token fields are copied.
- It does not authenticate, check active status independently, authorize roles,
  create a Phase 1 ID, resolve an identity mapping, or grant access to storage.
- The caller must supply the actual trusted `app.py` `current_user` function
  after the existing login flow. A callable passed by arbitrary code is not
  inherently trusted; this wrapper is not a security boundary by itself.
- It is not wired into `app.py` and must not be used to call integer-ID storage
  helpers. The legacy text ID and Phase 1 integer ID remain distinct until an
  approved mapping and verified linking flow exist.

Unit tests cover one-time accessor invocation, immutable context, missing or
incomplete sessions, rejection of direct dictionary input, secret-field
exclusion, and preservation of the legacy text ID.

## Staging preparation artifacts

- `docs/STAGING_TEST_RUNBOOK.md` describes a staging-only test procedure and its preconditions.
- `.streamlit/secrets.staging.toml.example` is a placeholder template for a staging secret manager. It contains no real credentials and deliberately excludes privileged service-role keys and production values.
- `modules/config.py` reads only the explicit `SUPABASE_ANON_KEY`; it does not fall back to the legacy `SUPABASE_KEY`.

These artifacts are preparation only. No staging project, deployment, credentials, production backup, migration, or live-app integration is claimed.

## Current verification status

- GitHub Actions passed on commit `bf66673adf9f408918b9fa25b05a136903975144` for both push and pull-request workflows.
- GitHub Actions passed on commit `4717c031e5a7460ca05dad301df91733e382eef3` for both push and pull-request workflows.
- GitHub Actions passed on commit `5ccf0f36e1c62a8e234335b996ce7cfcaa320c3d` for both push and pull-request workflows.
- GitHub Actions passed on commit `f3f1ac83241efc7e27fd84e13028295933653b80` for both push and pull-request workflows.
- GitHub Actions passed on commit `e45d85846ea91f76aa3c0e784ab48a75e42b7023` for both push and pull-request workflows.
- GitHub Actions passed on the latest branch commit `f764a427c0029c9cfac9d19f54e5146ab7572c2e` (push run #43).
- These checks validate only the isolated Phase 1 scope; they do not verify staging, production integration, data migration, or the live Streamlit app.
- The PR remains a draft and must not be merged or deployed on the strength of isolated unit tests alone.


## Follow-up source audit: legacy session lifecycle gaps

A read-only inspection of the existing `app.py` confirmed two additional
integration blockers, recorded in `docs/LEGACY_AUTH_SESSION_GAP_AUDIT.md`:

- The account's `active` flag is checked during password authentication, but
  the cached `current_user()` accessor does not re-query account status.
  Deactivation after login may therefore leave an existing session active.
- The current session accessor exposes no dedicated stable session ID or
  session version. A user ID alone cannot distinguish separate sessions.

These findings must be addressed in a separately reviewed, isolated session
lifecycle design before Private Lock is wired into the app. No changes were
made to `app.py`, the live session flow, database, or deployment.
