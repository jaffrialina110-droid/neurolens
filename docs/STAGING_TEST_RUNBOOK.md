# NeuroLens Phase 1 — Staging Test Runbook

## Purpose

This runbook defines the next controlled validation step for the read-only legacy account adapter. It is a procedure to follow after a separate staging environment is prepared; it does not mean staging has been created or tested.

## Current boundary

- Keep the existing `app.py` authentication flow as the source of truth.
- Keep `modules/account_adapter.py` standalone and read-only.
- Do not import the adapter into the production app or call it from the live account flow.
- Do not connect the Phase 1 SQLite auth database to existing user records.
- Do not copy journal entries, AI conversations, credentials, tokens, or other private content.
- Do not merge this draft PR or deploy it to the live Streamlit app as part of this test.

## Preconditions

Before any staging test:

1. Create a separate staging deployment and a separate staging database/project. Confirm that no production database path or production Supabase project is configured.
2. Use only a Supabase public anon key in staging configuration. Never place a service-role key in client-side configuration, source code, logs, screenshots, or chat.
3. Use synthetic test accounts and fictional profile data. Do not copy production users or private records.
4. Confirm a recoverable backup and rollback procedure for the staging environment.
5. Record the exact branch commit being tested.
6. Restrict staging access to the people conducting the test.

If any precondition is not met, stop. Do not substitute production credentials or data.

## Read-only adapter checks

Run the existing isolated test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

Expected behavior of `from_legacy_session_user(user)`:

- A dictionary matching the authenticated legacy `current_user()` profile shape is accepted.
- The existing text ID is preserved exactly and is not converted to an integer.
- The returned context contains only the legacy ID, username, email, display name, role, and identity-source label.
- Missing, blank, or non-string required values are rejected.
- Passwords, password hashes, salts, and access tokens are never returned.
- No database writes or account creation occur.

## Staging smoke-test protocol

Use only a synthetic account created within staging:

1. Sign in through the unchanged legacy authentication flow.
2. Obtain the authenticated profile dictionary from the existing `current_user()` function in a controlled test harness.
3. Pass that dictionary to the standalone adapter in the test harness only.
4. Compare the returned `legacy_user_id` with the staging account's original text ID.
5. Confirm the output contains no password, hash, salt, token, or private-content fields.
6. Confirm account count, account ID, password fields, and owned-record counts are unchanged before and after the read-only call.
7. Sign out and confirm the existing logout behavior still works.
8. Repeat with a missing user, malformed profile, and inactive test account. Authentication must reject inactive accounts before an authenticated context reaches the adapter.

Do not add a production integration hook merely to perform these checks. A standalone test harness is sufficient for this phase.

## Evidence to record

Record the tested commit SHA, Python version, CI run links, staging-only test account identifier (synthetic), test outcomes, and any errors. Never record passwords, secret values, private journal text, AI conversation content, or production user identifiers.

## Exit criteria

The staging slice is complete only when all preconditions and smoke tests pass, no account or owned-record data changes, and the results are reviewed. This still does not authorize a production migration, PR merge, or deployment. Those require a separate written migration/rollback plan and explicit owner approval.

## Status

Runbook committed as preparation only. No staging project, staging deployment, production backup, production migration, or live-app integration is claimed by this document.
