# NeuroLens Identity Mapping — Design Only

## Status

Design specification only. This document does not create a table, change a database, migrate users, or enable account integration.

The existing `app.py` account system remains the sole source of truth for the live application. The Phase 1 account/storage modules remain isolated.

## Problem being solved

The legacy application uses text user IDs, while the isolated Phase 1 SQLite module uses integer user IDs. These identifiers must never be treated as interchangeable.

A future integration may need an explicit one-to-one mapping between an already authenticated legacy account and a Phase 1 account. Username and email are profile attributes, not identity keys.

## Proposed mapping record

A future versioned migration may introduce a mapping table with these logical fields:

| Field | Requirement |
|---|---|
| `legacy_user_id` | Exact non-empty text ID from the authenticated legacy account; unique and not rewritten |
| `phase1_user_id` | Existing Phase 1 integer account ID; unique and references the Phase 1 users table |
| `created_at` | Database-generated UTC timestamp |
| `created_by` | Optional auditable system/process identifier; never a client-supplied user identity |

Required database constraints:

- Primary key may be a generated internal ID.
- `legacy_user_id` must have a UNIQUE constraint.
- `phase1_user_id` must have a UNIQUE constraint.
- Both identity columns must be NOT NULL.
- `phase1_user_id` must have a foreign key to the Phase 1 users table.
- Deletion behavior must be restrictive or explicitly reviewed; deleting one account must not silently erase or remap the other identity.
- Mapping creation must be idempotent and reject conflicting existing mappings.

This is a design contract, not executable SQL. Exact DDL depends on the approved staging database and migration framework.

## Identity verification rules

1. Authenticate using the existing legacy login flow first.
2. Obtain the identity from the server-side authenticated `current_user()` context, never from a form field, URL parameter, browser storage, or arbitrary request payload.
3. Preserve the legacy text ID byte-for-byte; do not trim, lowercase, cast, or numerically coerce it.
4. Do not match or auto-link accounts by username, email, display name, or similar profile fields.
5. Require a separate verified account-linking process before associating an independently created Phase 1 account.
6. Reject attempts to link a legacy ID or Phase 1 ID already mapped to a different account.
7. Re-check account active/disabled status through the authoritative legacy authentication/session layer before allowing an authenticated context.
8. Do not accept role or privilege claims from the mapping row; authorization must continue to use the trusted account/role source.

## Read-only mapping resolver (isolated)

Added `modules/identity_mapping.py` as a small resolver for a mapping that
already exists in an approved store:

- It accepts the immutable legacy-session context and a mapping-lookup
  callable supplied by the application integration layer.
- It passes the exact legacy text ID to the lookup; it never searches by
  username, email, or display name.
- It accepts only a positive integer Phase 1 ID and fails closed when the
  mapping is missing or malformed.
- It creates no mapping, account, table, or database connection and performs
  no migration.
- The lookup callable must query an authoritative store and enforce the
  unique constraints described above. No such mapping store is currently
  configured or accessed.
- A resolved ID is not proof of authorization. The caller must still enforce
  account active status, role policy, and record ownership. The context object
  is an application contract, not a cryptographic credential or an
  unforgeable authentication token.

Tests cover exact ID preservation, missing mappings, invalid mapped IDs,
wrong context inputs, and the absence of profile-field matching.

## Ownership and privacy

- Every user-owned Phase 1 record must resolve to one verified account identity.
- Reads and writes must enforce ownership at the data-access layer, not only by hiding interface controls.
- A mapping must not grant access to another user's posts, messages, journal, AI history, appointments, or research notes.
- Private journal and private AI content must not be migrated as part of identity linking.
- The existing legacy journal uses encrypted content; the Phase 1 storage schema currently has a plaintext journal content column. These are not compatible and must remain separate until encryption, key management, access controls, and recovery are reviewed.
- Staff/owner roles must not bypass private-content boundaries by default.

## Migration and rollback requirements

Before implementing the mapping:

- Create a separate staging project/database and use synthetic users only.
- Confirm backup and restore procedures for both systems.
- Inventory existing user IDs and related-record ownership without exporting private content.
- Write a versioned migration with preconditions, uniqueness checks, and rollback behavior.
- Test duplicate IDs, duplicate mappings, missing users, inactive users, deletion attempts, and ownership isolation.
- Verify the migration against a disposable copy, not production.
- Record row counts and integrity checks before and after.
- Obtain explicit approval before any production migration, merge, or deployment.

If the mapping operation cannot be completed atomically across the participating stores, use a documented pending/reconciliation state and never leave a partially linked account authorized.

## Not approved / not implemented

- No mapping table or SQL migration has been created.
- No user has been linked or migrated.
- No email/username matching or automatic account merging is allowed.
- No production or staging database has been accessed.
- No change has been made to `app.py`, existing login, passwords, sessions, or live data.
- This document does not authorize PR merge or deployment.
