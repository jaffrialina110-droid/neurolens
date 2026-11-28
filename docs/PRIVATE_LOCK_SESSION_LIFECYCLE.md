# Private Lock Session Lifecycle

## Scope

The pure helper module `modules/private_lock_session.py` defines a server-side
session record and fail-closed checks for inactivity timeout, logout, and
account/session changes. It is not connected to Streamlit or the existing
account system.

## Required integration contract

- The main authentication layer must independently validate the current
  authenticated user and current auth-session reference on every request.
- Create an unlocked private-session record only after successful PIN
  verification and lockout checks.
- Keep the record exclusively in trusted server-side session state. Never
  accept it, its user ID, auth-session reference, or activity timestamp from
  query parameters, forms, browser storage, or client messages.
- Call `validate_private_session` before every private-data read or write.
  Pass the current user ID and current auth-session reference obtained from
  the trusted authentication layer.
- Persist the returned refreshed record only in server-side session state.
- On logout, account switch, auth-session rotation, auth-session expiry, or
  invalidation, replace the record with `locked_private_session()`.
- Use a stable auth-session reference that changes when the authenticated
  session is replaced. Do not use a username or email as the session reference.
- The helper is a local session gate only. It does not revoke other devices,
  invalidate database grants, or provide distributed session revocation.

## Atomic PIN verification boundary

For a production PIN attempt, the intended persistence entry point is
`SqlitePrivateLockAttemptStore.verify_and_record_attempt`, not a separate
`get_state` → verify → `record_attempt` sequence.

The atomic method:

- Acquires a SQLite `BEGIN IMMEDIATE` write reservation before reading the
  user's lockout state.
- Refuses verification while the server-side lockout deadline is active,
  including when the supplied PIN is correct.
- Verifies the supplied PIN against a salted hash fetched by trusted server
  code for the same authenticated account.
- Persists the success reset or failed-attempt increment before releasing the
  transaction, serializing parallel attempts across connections to the same
  SQLite database.
- Does not store the submitted PIN or encoded PIN hash.

The caller must obtain the Phase 1 integer user ID from an approved,
one-to-one identity mapping after validating the existing authenticated
account. It must fetch the encoded PIN hash from trusted server-side storage
for that exact Phase 1 user ID. Never accept either value from client input.
Only create the private-session record when the result says `verified=true`
and `locked=false`, then bind it to the independently authenticated session
reference using `unlock_private_session`.

The older `record_attempt` method is a low-level state-persistence primitive
for isolated tests and controlled maintenance. It accepts a caller-supplied
success boolean and therefore must not be used as the production PIN
verification flow. Do not split verification from the atomic method: doing so
would reintroduce a parallel-request lockout race.

## Integration test contract before app wiring

- An unauthenticated request cannot resolve a user ID or retrieve a PIN hash.
- A legacy text user ID without an approved unique mapping fails closed.
- Duplicate or cross-account mappings fail closed.
- Inactive or disabled accounts cannot unlock the private area.
- PIN hash lookup is scoped to the mapped user ID; a hash from another account
  cannot unlock the current user's area.
- A correct PIN cannot bypass an active lockout.
- Parallel wrong PIN attempts cannot be lost or exceed the configured limit.
- A successful PIN attempt clears the counter only for that user.
- Logout, account switch, auth-session rotation, and inactivity timeout lock
  the private area before any private-data operation.
- Every private-data read and write checks the current authenticated identity,
  current auth-session reference, and unlocked private-session record.
- Owner/Staff roles receive no implicit bypass; private content remains
  inaccessible through dashboards, analytics, exports, and support tools.
- No PIN, PIN hash, private content, or session secret is written to logs.

These are pre-integration requirements, not a claim that the current Streamlit
application already satisfies them.

## Tests and release gates

Tests cover valid activity refresh, inactivity timeout, logout/missing session,
account switch, auth-session rotation, clock rollback, malformed records, and
identity-free locked state.

Do not wire this into the live app until the trusted authentication layer,
server-side session storage, persistent revocation strategy, and private-content
authorization/encryption have been reviewed in isolated staging. Production
migration, PR merge, and deployment require separate explicit approval.
