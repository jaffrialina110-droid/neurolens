# Private Lock Recovery and Integration Design

## Status

Design only. This document does not implement account recovery, persistence,
encryption, or UI integration. The existing application and production data are
not modified by this design.

## Security goals

- A forgotten Private Lock PIN must not silently expose journal or private AI data.
- Recovery must prove control of the user's existing authenticated account.
- Recovery must not rely on username, display name, or an unverified email match.
- A recovery action must be auditable without logging the PIN, recovery secret,
  journal text, or private AI content.
- Staff and owner roles must not provide a bypass into private user content.

## Proposed recovery flow

1. Require a fresh re-authentication through the existing account system.
2. Require an independently verified recovery factor already enrolled by the
   account owner. Do not invent or silently enroll a recovery factor during reset.
3. Use a single-use recovery token/code stored only as a salted, slow hash.
   Generate it with a cryptographically secure random source; display it once.
4. Consume the recovery token atomically. Reject reuse, expired tokens, and
   excessive attempts. Rate-limit both token verification and PIN reset.
5. Let the authenticated owner set a new PIN that satisfies the current PIN
   policy. Never reveal the old PIN.
6. Invalidate active private-space unlock sessions and rotate/revoke any
   private-content access grants.
7. Record a minimal security audit event (event type, user reference, timestamp,
   outcome). Never record PINs, recovery codes, or private content.

If no independently verified recovery factor exists, do not provide a staff
override or automatic reset. The product must explain the limitation before
the user enables the lock and offer an explicit, carefully reviewed enrollment
flow first.

## Lockout and session requirements

- Failed-attempt counters and lockout deadlines must be stored server-side in a
  trusted persistence layer; never accept counters or timestamps from the
  browser.
- Update counters atomically to prevent concurrent requests bypassing limits.
- Apply rate limits across sessions/devices, not only a single browser session.
- Clear counters only after a successful verification or approved recovery.
- Enforce inactivity timeout using the last trusted server-side activity time.
- Re-lock on logout, account switch, session expiry, and suspicious session
  invalidation.
- A lockout must not be bypassable by refreshing the page or starting another
  browser session.

## PIN and private-data handling

- Store only a salted, slow password hash for the PIN; never store or log raw
  PINs. The isolated primitive bounds salts to 16–64 bytes and validates encoded
  digest sizes before expensive verification. Review the chosen work factor
  against production hardware before launch.
- A PIN lock is an additional privacy gate, not a replacement for account
  authentication or encryption at rest.
- Encrypt private journal and private AI content with a separately reviewed
  key-management design. Do not place plaintext private content in ordinary
  Phase 1 tables.
- Do not expose private content in Owner Dashboard, Staff Workspace, analytics,
  logs, exports, or support tooling by default.
- Do not claim that a PIN hash alone encrypts or protects database contents.

## Required tests before integration

- Fresh account re-authentication is required for recovery.
- Missing, invalid, expired, reused, and brute-forced recovery tokens fail closed.
- Recovery token consumption is atomic under concurrent requests.
- Reset invalidates every active private unlock session.
- Failed-attempt counters survive refresh, new sessions, and parallel requests.
- Account logout, account switch, and session expiry re-lock the private area.
- Cross-user access attempts fail even when a user knows another user's record ID.
- No PIN, recovery token, or private content appears in logs or audit events.
- Backup/restore and key rotation procedures are tested in isolated staging.

## Release gates

Do not connect this design to the live app until a separate staging environment,
trusted persistence, verified recovery-factor enrollment, atomic rate limiting,
private-content encryption/key management, access-control tests, and rollback
plan have been reviewed. Obtain explicit approval before production migration,
PR merge, or deployment.

## Current implementation boundary

The isolated `modules/private_lock.py` module currently provides PIN hashing,
verification, attempt-state calculations, and inactivity-timeout primitives.
The caller is responsible for trusted server-side persistence and timestamps.
These helpers are not wired into the Streamlit app and do not implement recovery,
authentication, authorization, encryption, or cross-device rate limiting.
