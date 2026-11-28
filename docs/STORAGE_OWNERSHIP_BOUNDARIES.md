# Phase 1 Storage Ownership Boundaries

## Current scope

The Phase 1 SQLite storage module contains user-owned tables and seven explicitly scoped read helpers:

- `get_posts_for_user(user_id)`
- `get_activity_for_user(user_id)`\n- `get_profile_for_user(user_id)`\n- `get_comments_for_user(user_id)`\n- `get_reactions_for_user(user_id)`\n- `get_appointments_for_user(user_id)`\n- `get_research_notes_for_user(user_id)`

Each helper validates that the supplied ID is a positive integer and include that ID in the SQL `WHERE` clause. Synthetic tests verify that records for two test users are returned separately.

These helpers are query-scoping utilities. They are **not authentication or authorization** and do not independently prove that the caller owns the supplied ID.

## Mandatory caller contract

Before calling any helper, application code must:

1. Complete authentication through the trusted server-side authentication flow.
2. Obtain the authenticated account ID from server-controlled session/authentication state.
3. Never take the account ID from a URL, form field, query parameter, request body, or other user-controlled input.
4. Pass only that server-derived account ID to the scoped helper.
5. Apply the same ownership predicate to every future read, update, and delete operation for user-owned records.

Do not expose a generic lookup by arbitrary user ID to ordinary users. Administrative access, if introduced, must have a separate explicit authorization check and audit trail.

## Known gaps and restrictions

- Existing Phase 1 storage APIs are not yet a complete authorization layer.
- Owner-scoped read helpers now cover profiles, posts, comments, reactions, activity, appointments, and research notes. Journal entries remain intentionally excluded because the isolated schema stores journal content in plaintext; no helper is provided to retrieve it.
- The `journal_entries.content` column is plaintext in this isolated schema. Do not store real private journal content there.
- Do not connect this storage module to the live app or production user data.
- Do not use these tests as evidence that the complete NeuroLens application is secure.

## Required next gates

Before any real-user integration:

- Define a single trusted authenticated-user context at the application boundary.
- Implement and test owner-scoped repository methods for every user-owned table; journal access remains blocked until encryption and key management are implemented.
- Test cross-user read, update, and delete attempts using synthetic accounts.
- Add encryption and key-management design for private journal and sensitive records.
- Review staff/owner permissions, audit logging, session expiry, and recovery.
- Run tests against an isolated staging database with synthetic data only.
- Complete backup/restore and rollback checks and obtain explicit approval before production changes.

This document records current limitations and required controls. It does not authorize deployment, migration, or production data access.
