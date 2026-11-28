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

## Tests and release gates

Tests cover valid activity refresh, inactivity timeout, logout/missing session,
account switch, auth-session rotation, clock rollback, malformed records, and
identity-free locked state.

Do not wire this into the live app until the trusted authentication layer,
server-side session storage, persistent revocation strategy, and private-content
authorization/encryption have been reviewed in isolated staging. Production
migration, PR merge, and deployment require separate explicit approval.
