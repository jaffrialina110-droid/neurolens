# NeuroLens Staging Preview

## Purpose

This branch is the isolated preview track for NeuroLens development. It is
based on the Phase 1 development branch and must remain separate from
`main` and the official Streamlit deployment.

- Development source: `neurolens-platform-phase1`
- Staging branch: `neurolens-staging-preview`
- Production branch: `main` (do not modify or merge automatically)

## Important deployment boundary

Creating this branch does **not** publish a public preview. A separate
Streamlit Community Cloud app must be created and explicitly connected to
this repository, this branch, and the correct entrypoint. That hosting action
requires the repository owner's Streamlit account access and confirmation.
No deployment token, account credential, or production secret belongs in
GitHub source code.

## Owner setup required for a public preview URL

1. Sign in to Streamlit Community Cloud using the account that owns the
   existing NeuroLens deployment.
2. Create a **new app**; do not edit or redeploy the existing official app.
3. Select repository `jaffrialina110-droid/neurolens`.
4. Select branch `neurolens-staging-preview`.
5. Select the intended entrypoint only after confirming it is safe for
   staging. The current app may use `app.py`; verify the repository file
   before selecting it.
6. Configure only staging-specific secrets and a separate staging database.
   Never copy production credentials or production data into staging.
7. Deploy the new app and verify its URL, branch, commit, login, data
   isolation, and error logs.
8. Share the preview URL with the owner for acceptance testing.

## Release gate

No changes are published to the official website until all of the following
are true:

- Staging CI checks pass for the exact commit under review.
- The owner verifies the feature on the staging URL.
- Authentication, privacy, authorization, and data-isolation checks pass.
- A backup and rollback plan exists for any database migration.
- The owner explicitly approves the release.
- Production deployment is performed as a separate, reviewed action.

## Feature reporting standard

Every release report must classify each feature as one of:

- **Implemented and tested** — code exists and automated tests pass.
- **Working in staging** — manually verified in the separate staging app.
- **Partial / limited** — some parts exist but full workflow is incomplete.
- **Not implemented** — planned only.
- **Blocked** — waiting on credentials, owner setup, external service, or
  unresolved security review.

Passing unit tests alone must never be described as a feature working in the
live app.

## Current status

- Staging branch created from the Phase 1 development head.
- Public Streamlit preview: **not deployed yet**.
- Existing official app: **unchanged**.
- Production database and secrets: **untouched**.
- No merge to `main` is authorized by this setup.
