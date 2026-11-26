# NeuroLens AI chat encryption and migration plan

Date: 2026-11-26
Target branch: `safety/database-security-foundation`
Status: design only — no application code or database has been changed by this document.

## 1. Current verified state

- `ai_messages.content` is currently a `TEXT NOT NULL` column and existing Ask Ayna messages are stored as readable plaintext.
- The development branch has conversation ownership checks on both message reads and writes.
- The Owner Control Center's AI Activity view displays operational metadata, not message content.
- The Private Journal has a separate Fernet-based vault and PIN-wrapped master key. That vault is not currently the AI chat encryption system.
- `cryptography` is already listed in `requirements.txt`.
- The app reads deployment configuration through Streamlit secrets/environment variables.
- This is a static code inspection, not a production database or deployment inspection. The deployed database contents, backup process, and actual Streamlit secrets configuration have not been accessed.

## 2. Security objective and limits

Protect persisted AI chat message content against someone who obtains a copy of the SQLite database without also obtaining the deployment encryption secret.

This is **encryption at rest**, not end-to-end encryption. The running NeuroLens server must be able to decrypt messages to display chat history. Messages sent to the configured AI provider may also be processed by that provider under its service terms; database encryption does not encrypt data after it is sent to the provider.

The design does not protect against a compromised running application, malicious code running with application access, a compromised deployment secret, or an authorized user viewing their own decrypted history.

## 3. Proposed cryptographic design

- Use authenticated encryption with `cryptography.hazmat.primitives.ciphers.aead.AESGCM`.
- Generate a high-entropy 256-bit application master secret outside the repository. Configure it only in the deployment secret manager, for example Streamlit Secrets as `AI_CHAT_ENCRYPTION_KEY`.
- Never commit the secret, print it in logs, place it in SQLite, or expose it in the UI.
- For each account, derive a separate 256-bit key using HKDF-SHA256 from the master secret, with a random per-user salt stored as non-secret metadata and a fixed, versioned context string such as `neurolens/ai-chat/v1/<user_id>`.
- Use a fresh cryptographically random 96-bit nonce for every message encryption. Store the nonce separately from ciphertext.
- Authenticate stable message context as AES-GCM associated data (AAD), including the encryption format version, message ID, conversation ID, user ID, and role. This prevents ciphertext being silently transplanted between rows or accounts.
- Store ciphertext as base64 text in the existing content column. Do not store derived keys or the master secret.
- Fail closed for persistent writes: if the encryption key is absent, malformed, or decryption/authentication fails, do not write plaintext as a fallback. Show a clear, non-secret error. A session-only response may be offered separately, but it must not be described as saved.

The exact implementation must be reviewed against the installed `cryptography` version and tested before merge.

## 4. Backward-compatible schema plan

Use an additive migration only. Do not rebuild or replace the existing tables.

Proposed additions:

- `ai_messages.content_version INTEGER NOT NULL DEFAULT 0`
  - `0` = legacy plaintext row.
  - `1` = AES-GCM encrypted row.
- `ai_messages.encryption_nonce TEXT`
  - Base64-encoded 12-byte nonce for version 1; NULL for version 0.
- A small per-user key metadata table, for example `ai_chat_crypto_users(user_id TEXT PRIMARY KEY, key_salt TEXT NOT NULL, key_version INTEGER NOT NULL, created_at TEXT NOT NULL)`, with a foreign key to users where supported by the existing database setup.

Migration requirements:

1. Inspect the actual deployed schema and take a verified backup before any migration.
2. Confirm backup restore in a separate staging copy.
3. Add columns/table using idempotent, additive SQL and record a schema migration version.
4. Keep existing rows at version 0; do not silently rewrite or delete historical messages.
5. New messages are version 1 only after the secret is configured and a successful encrypt/decrypt self-test passes.
6. Reads must branch on version: version 0 reads legacy plaintext; version 1 requires successful authenticated decryption. Unknown versions or failed authentication must never be displayed as plaintext.
7. Keep existing ownership checks on every read and write, and bind the authenticated user to the conversation and message rows.
8. Update conversation timestamps only after successful persistence.

## 5. Legacy history and user disclosure

Existing plaintext messages cannot be retroactively protected from database copies that may already exist. The rollout must explain this limitation.

Two rollout options should be evaluated in staging:

- **Recommended staged option:** leave old rows readable as legacy plaintext and encrypt all new messages. Offer a separately controlled, opt-in migration of a user's old history after backup and successful decrypt/encrypt verification.
- **Alternative:** provide an explicit user choice to clear old history and start encrypted history. Deletion must remove both message rows and associated conversation metadata in a transaction.

Never run a bulk conversion automatically on production data. Never claim legacy rows are encrypted until their version and ciphertext have been verified.

## 6. Key lifecycle and recovery

- Generate and store the master secret in the deployment's secret manager; restrict access to the smallest necessary set of maintainers.
- Maintain a secure offline backup of the secret under the project owner's control. The database alone must not be sufficient to reconstruct the key.
- If the master secret is lost, encrypted messages may be permanently unrecoverable. Communicate this before enabling encryption.
- Plan key rotation as a separately tested operation: decrypt with the old key and re-encrypt with the new key in a verified backup/staging copy first. Do not simply replace the deployment secret, because that would make existing ciphertext unreadable.
- Do not reuse the Private Journal PIN as the AI chat encryption key. Do not derive encryption keys from a short PIN or user password.

## 7. Privacy controls and data handling

- Add clear user-facing disclosure that chat history is stored encrypted at rest, that the server can decrypt it, and that prompts may be sent to the configured AI provider.
- Provide a user-initiated delete-history action that checks ownership and deletes the selected account's message and conversation rows transactionally.
- Define retention and deletion behavior before release. Avoid retaining unnecessary message content in logs, analytics, crash reports, or admin views.
- Keep the Owner Control Center limited to aggregate counts and operational metadata. Never add chat-content access to the owner dashboard by default.
- Clear in-memory chat state on logout and account switching; do not let one account's cached messages appear in another account's session.
- Review backups, exported databases, and support workflows because encryption at rest in the live database does not automatically encrypt every backup or export.

## 8. Required tests before merge

Unit and integration tests must cover:

1. Round-trip encrypt/decrypt for user and assistant messages.
2. A fresh nonce is generated for each encryption, including repeated identical plaintext.
3. Tampered ciphertext, nonce, role, message ID, conversation ID, or user ID fails authentication.
4. User A cannot decrypt or load User B's message, even if IDs are supplied directly.
5. Legacy version 0 rows remain readable through the explicit compatibility path.
6. Unknown content versions and encrypted rows with missing/invalid nonce fail closed.
7. Missing or malformed master secret prevents persistent plaintext writes.
8. Migration is idempotent and preserves row counts and IDs.
9. Delete-history affects only the authenticated user's records and is transactional.
10. Logout/account switching clears cached message content.
11. Owner dashboard queries never select message content.
12. Key rotation succeeds on a staging copy and a wrong/lost key produces a safe, non-disclosing error.

Run the existing database preflight and the full test suite against a disposable staging database. Do not use the production database for tests.

## 9. Rollout gates

Do not merge or deploy until all are true:

- A verified backup and tested restore exist.
- The actual deployment database path/schema and storage persistence behavior are confirmed.
- The deployment secret has been configured securely and is not present in Git history.
- Migration and rollback procedures have been tested on a staging copy.
- Existing ownership tests and new encryption tests pass.
- The user-facing disclosure, deletion behavior, and legacy-history choice are approved.
- A reviewer has checked the crypto implementation, key lifecycle, and error handling.

## 10. Explicitly out of scope for this design-only change

- No application code changes.
- No database migration or data conversion.
- No production database access.
- No change to the Private Journal vault or legacy `modules/security.py`.
- No change to AI provider selection or AI prompts.
- No merge of the development branch into `main`.

