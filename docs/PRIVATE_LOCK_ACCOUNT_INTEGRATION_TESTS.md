# Private Lock Account Integration Test Contract

## Status

This is an isolated staging-style test harness, not live application
integration. The test uses fixture account records, an in-memory identity
mapping callback, fixture PIN hashes, and a temporary SQLite database.

It does not import `app.py`, access Supabase, inspect real user records, use
production secrets, create a staging deployment, or change the live app.

## Workflow covered

1. Obtain a minimal legacy identity through a callable server-side
   `current_user` test fixture.
2. Resolve the exact legacy text ID through a one-to-one mapping fixture.
3. Use the resolved Phase 1 ID to select the fixture's PIN hash.
4. Verify and persist the PIN attempt atomically in temporary SQLite.
5. Create a private-session record only after a successful verification.
6. Validate the private-session record against the current account ID and
   authenticated-session reference.

## Scenarios

- Valid mapped account and correct PIN can create a private-session record.
- Missing identity mapping fails before a PIN hash can be selected.
- Wrong PIN does not create an unlocked session.
- Active lockout blocks even a correct PIN until the deadline.
- Switching accounts invalidates the previous private session.
- Rotating the authenticated-session reference invalidates the old record.
- Failed-attempt state is isolated between mapped accounts.
- Staff role has no implicit PIN/session bypass in this test contract.

## Important limits

The fixture `current_user` function is not the actual app authentication
implementation. The fixture mapping is not a real mapping table. The PIN hash
dictionary is not a production credential store. The test does not establish
that the app has a stable auth-session ID, checks account active status, or
checks the private-session gate before every private-data read and write.

Before real staging integration, separately verify the existing account
session's trusted identity source, active-account status, role rules, a
versioned unique mapping table, server-side PIN-hash retrieval, stable session
rotation/revocation, database permissions, backup/restore, and rollback.

Do not connect this harness to `app.py` or production. Merge, migration, and
deployment require separate explicit approval.
