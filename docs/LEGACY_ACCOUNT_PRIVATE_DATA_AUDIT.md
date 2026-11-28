# Legacy Account, Private Data, Owner and Staff Audit

**Branch:** `neurolens-staging-preview`  
**Scope:** Read-only source inspection of `app.py` and the isolated Phase 1 boundary documents.  
**Date:** 2026-11-28  
**Status:** Findings only. No production data, credentials, database, or account flow was accessed or changed.

## Executive summary

The legacy app contains account registration/login, encrypted journal routines, Personal Healing session-only reflections, an owner dashboard, and a staff workspace. These are source-code features, not evidence of a secure or operationally verified deployment. The Phase 1 auth/storage modules remain isolated and are not a drop-in replacement for the legacy text-ID account system.

Do not invite real users to store sensitive information in this staging build until the blockers below are addressed and tested against a separate synthetic-data environment.

## Confirmed source findings

### 1. Legacy account and session

- Registration and login use the local SQLite database at `APP_DIR / "neurolens_data.db"`.
- The legacy user ID is a random text ID. Login checks the account's `active` flag, but `current_user()` subsequently trusts the Streamlit session-state flag and cached user object without re-reading account status.
- Logout clears the app's authentication fields and AI message list, but a server-side session identifier/version and cross-session revocation mechanism are not present in the inspected accessor.
- Account records and user data are therefore tied to the local SQLite deployment model; no durable shared database or multi-instance consistency was verified.

**Required:** move account/session authority to a durable server-side identity/session layer; check active status and session generation on protected requests; add revocation and expiry tests; preserve legacy IDs through a reviewed migration.

### 2. Private Journal

- Journal entry content is encrypted before insertion into `journal_entries.encrypted_content`, using a per-vault master key wrapped by PIN-derived and recovery-code-derived keys.
- The journal query filters entries by the current session's user ID. Delete also filters by both entry ID and current user ID.
- The UI has a 10-minute private-session timeout and a five-failed-attempt / five-minute lockout counter.
- The failed-attempt counter and lock-until timestamp are stored in Streamlit session state, not in durable shared storage. A fresh session can therefore reset the local counter; this is not robust cross-session rate limiting.
- The unwrapped master key is held in Streamlit session state while the vault is unlocked.
- The journal uses the legacy local SQLite database. Persistence, backups, key recovery after deployment changes, and multi-instance behavior have not been verified.

**Required:** move rate-limit state to durable atomic storage; bind unlock state to a verified authenticated session; clear key material on logout/session revocation; validate timeout behavior; test recovery and backup/restore; review server-side key handling and deployment persistence before real data use.

### 3. Personal Healing

- Mood, energy, and reflection check-ins are appended to Streamlit session state and described in the UI as session-only.
- Prompt reflections are also stored in session state and described as session-only.
- No durable user-scoped storage or private-lock gate is used by these check-in/reflection controls in the inspected page.

**Required:** keep this explicitly session-only until the user asks for durable storage; if persistence is added, make it opt-in, owner-scoped, encrypted where appropriate, and excluded from staff/owner views by default.

### 4. Owner Control Center

- Access requires a logged-in session and an email match against the configured owner email.
- The dashboard reads platform-wide account metadata, appointment information, bookmark metadata, AI message metadata, and audit records.
- The inspected owner queries do not select private journal entry content or AI message content.
- The page itself warns that dashboard checks do not replace database-level security, RLS, or server-side authorization.

**Required:** protect owner configuration outside source; enforce authorization at every owner data function, not only page rendering; add negative tests for ordinary users and altered session state; minimize displayed personal metadata and audit every privileged operation.

### 5. Staff Workspace

- Staff role records and task operations are implemented in the legacy app.
- Staff task reads are filtered to assigned user for non-Admin roles; the Admin role can read all tasks.
- Task updates use assignment filtering for non-Admin roles, while Admin updates are global.
- The inspected workspace checks staff permissions before task-status updates, but the broader staff-management and role-assignment paths require a dedicated authorization review.

**Required:** centralize role/permission checks in server-side service functions; prevent ordinary staff from assigning roles or escalating privileges; test inactive/revoked staff, forged IDs, cross-assignment access, and Admin-only actions.

## Integration boundary

- Do not wire the Phase 1 integer-ID storage helpers directly to legacy text IDs.
- Do not store journal content in the Phase 1 plaintext journal table.
- Do not copy production secrets or production data into staging.
- Use a separate staging database and synthetic accounts only.
- Keep production branch, production app, and production database unchanged until explicit owner approval.

## Next verification gates

1. Add isolated tests for session revocation, account deactivation after login, and session expiry.
2. Add durable, atomic journal attempt-limit tests across multiple sessions.
3. Add two-user journal read/delete isolation tests against the legacy schema in a disposable test database.
4. Add owner/staff negative authorization tests, including privilege escalation and task reassignment.
5. Verify persistence and backup/restore on a separate staging database.
6. Complete security review and obtain explicit approval before integrating or releasing.

## What this audit does not claim

This is a source-level inspection, not a penetration test, live runtime test, cryptographic audit, or proof that user data is safe. No production changes were made.
