# Private Lock Server-Side Attempt Persistence

## Scope and status

The isolated `modules/private_lock_store.py` adapter provides a SQLite
persistence contract for failed-attempt counters and lockout deadlines. It is
not wired into Streamlit, the existing account flow, or production storage.
No production database path or credentials are configured here.

## Security and transaction behavior

- The caller injects a trusted server-side SQLite connection factory.
- The adapter creates no database or table on import or construction.
- Schema creation is explicit through `initialize_schema()`; use only an
  approved isolated/staging database.
- Each attempt update uses `BEGIN IMMEDIATE`, reads the current row, computes
  the next state, writes it, and commits in one transaction. SQLite serializes
  concurrent writers so simultaneous failed attempts are not lost.
- State is partitioned by positive Phase 1 integer user ID. This identifier
  must come from a future trusted server-side identity mapping, not a browser.
- Only user ID, failed-attempt count, and lockout deadline are stored. PINs,
  hashes, recovery codes, and private content are not stored in this table.
- A successful already-verified attempt resets the counter. Attempts received
  during an active lockout do not extend the deadline. The lockout ends at the
  exact deadline (`now >= locked_until`), when a new verification may proceed.
- Persisted counters and lockout deadlines are validated when read. Invalid
  or corrupted rows raise a storage error and fail closed; they are never
  treated as a fresh state or used to verify a PIN.

## Caller obligations

- Verify the PIN with the existing constant-time verifier before calling
  `record_attempt(success=...)`.
- Do not use the storage method as authentication or authorization.
- Omit the optional `now` argument in production; it exists for deterministic
  tests. Use server time only, never browser-supplied timestamps.
- Resolve the user ID from an authenticated server-side session and approved
  identity mapping. Neither exists as an integrated production flow yet.
- Protect the SQLite file and its backups with appropriate filesystem
  permissions and encryption-at-rest controls.
- Use a single trusted database location shared by app workers. A local
  ephemeral filesystem is not sufficient for multi-instance deployments.
- Add cross-device and distributed rate limiting if deployment moves beyond
  one shared SQLite database.

## Tests and release gates

Tests cover explicit schema initialization, persistence across connections,
per-user isolation, lockout behavior, reset behavior, invalid identifiers,
and concurrent writers. These are isolated adapter tests, not production
integration tests.

Do not wire this adapter into the live app until staging storage, identity
mapping, backup/restore, filesystem protection, multi-worker deployment
behavior, and rollback have been reviewed. Explicit approval is required
before production migration, PR merge, or deployment.
