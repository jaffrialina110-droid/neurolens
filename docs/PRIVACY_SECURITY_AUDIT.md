# NeuroLens privacy and security audit — development branch

Date: 2026-11-26
Scope: static review of `app.py` on `safety/database-security-foundation`.
This is a code review, not a penetration test or deployment verification.

## Confirmed findings

### 1. Private Ask Ayna route is not implemented in this app.py snapshot
The final router registers the navigation label `Private Ask Ayna` and maps it to `page_private_ask_ayna`, but no function with that name is defined in the reviewed `app.py` snapshot. The router therefore displays its generic page-unavailable message for this route unless another imported module defines the function at runtime. Trace imports and deployment configuration before deciding how to implement it.

### 2. Ask Ayna messages are stored as readable text
The schema defines `ai_messages.content TEXT NOT NULL`. The `ayna_save_message` helper inserts message content directly, and `ayna_load_messages` reads it back. The Owner Control Center currently displays AI activity metadata (conversation_id, role, created_at), not message content. This is still sensitive personal data at rest in the application database and should be disclosed and protected accordingly. Do not describe these conversations as encrypted.

### 3. AI conversation ownership and persistence — remediation committed
The initial review found that AI message loading did not filter by the logged-in user, message saves did not verify conversation ownership, and the insert helpers omitted required schema fields. These issues were corrected on this development branch: loads now join the conversation owner and match both user IDs; saves verify ownership and write explicit message IDs/user IDs; conversation creation writes its ID and both required timestamps; an invalid/stale conversation ID clears the page's chat session state. Regression tests were added for cross-account reads/writes and normal owner access. These tests have not yet been executed in a configured project environment.

### 4. Private Journal design is separate from Personal Healing check-ins
The reviewed `page_private_journal` uses a PIN-gated vault flow and encrypted-entry helper functions. In contrast, `page_personal_healing` saves check-ins and reflections only in Streamlit session state, not in the encrypted journal. UI copy must keep this distinction clear; do not imply that session-only Personal Healing text is part of the encrypted vault.

### 5. Owner dashboard does not show journal text in the reviewed code
The dashboard's allowlisted recent-record queries omit journal entries, and the UI says it does not expose journal contents. Keep this restriction in future admin changes. Counts and metadata should still be assessed for privacy risk.

### 6. Legacy Private Ask Ayna PIN module requires separate review
The legacy `modules/security.py` is not proven to be active in this app.py flow. Do not silently replace it or assume it protects the `Private Journal`. Trace imports, callers, and deployment entrypoints first. Any legacy unsalted SHA-256/default-PIN mechanism must not be used for production secrets.

## Safe remediation sequence

1. Trace actual entrypoint/imports and establish whether `modules/security.py` is used.
2. Verify the committed load/save ownership controls against the deployed schema and run the new cross-account regression tests. Review any future delete/export paths separately.
3. Decide whether AI chat history should be stored. If stored, document retention/deletion and access controls; consider encryption at rest with managed key handling.
4. Keep Personal Healing session-only until the user explicitly chooses persistent storage; if persisted, put it behind the same private-vault access controls.
5. Review the complete vault implementation, key lifecycle, recovery, rate limiting, and session timeout before changing PIN logic.
6. Run automated tests and a staging smoke test before merge. Do not run migrations against production data without a verified backup and rollback plan.

## Not done

- No user records, passwords, journal entries, or production database were read or changed.
- No authentication migration or PIN replacement was performed.
- No claim is made that this review is a complete security audit.
