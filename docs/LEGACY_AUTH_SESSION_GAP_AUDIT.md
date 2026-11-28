# Legacy Authentication Session Gap Audit

## Scope and method

This is a read-only source inspection of the existing `app.py` on the
`neurolens-platform-phase1` branch. No application code, database, credentials, sessions,
or deployment were changed.

The inspected source contains `authenticate_user(identifier, password)`,
`current_user()`, `require_login()`, and the `users` table definition.

## Verified observations

### 1. Active status is checked at login

`authenticate_user()` selects the user row and returns `None` when
`user["active"]` is false. A successful result includes the user ID,
username, email, display name, and role.

### 2. Current-session lookup does not re-check active status

`current_user()` checks `st.session_state.authenticated`. If true, it
returns the session's `user_id` and cached `st.session_state.user`
dictionary. It does not query the users table or re-check the account's
current `active` value.

Consequence: if an account is deactivated after a successful login, the
existing Streamlit session may continue to be treated as authenticated until
the session is otherwise cleared. This is a source-level observation, not a
claim that a live deactivation scenario was executed.

### 3. No stable authentication-session reference is exposed

The inspected `current_user()` return value contains the legacy user ID and
cached profile fields. It does not expose a dedicated session ID, session
version, or authentication generation suitable for binding a Private Lock
unlock record to a specific authenticated session.

A user ID alone is not a session reference: two sessions for the same account
would share it.

### 4. Existing logout clears the cached authentication fields

The account page's logout path clears `authenticated`, `user`, and
`user_id`, and calls `clear_private_session()`. This is useful for the
existing logout action but does not supply a stable session identifier or
prove that every other session is revoked.

## Integration blockers

Do not connect the Phase 1 Private Lock flow to the existing app until a
separately reviewed design addresses all of the following:

- Revalidate account existence and active status from a trusted server-side
  source before granting or continuing private access.
- Define revocation behavior when an account is deactivated, password is
  changed, or the user logs out.
- Provide a server-controlled, unguessable session identifier or monotonic
  session version, with rotation on authentication and revocation on logout.
- Bind Private Lock unlock state to both the verified account mapping and the
  current authentication-session reference.
- Ensure every private-data read and write checks the private-session gate;
  hiding a page or button is not an authorization control.
- Keep role checks separate from identity mapping and PIN verification.
- Add staging tests for deactivation during an active login, session rotation,
  logout, parallel sessions, and cross-account isolation.

## Safe next step

Design and review a minimal legacy-session lifecycle adapter in isolation.
Do not modify `app.py` or production session behavior until the design has
tests, a staging environment, a rollback plan, and explicit owner approval.

## Status

Audit/documentation only. No live app integration, staging execution,
production database access, migration, merge, or deployment was performed.
