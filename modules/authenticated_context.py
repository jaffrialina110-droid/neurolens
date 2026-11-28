"""Narrow bridge from the server-side legacy session accessor to Phase 1.

This module does not authenticate users, read client input, or map legacy IDs
to Phase 1 integer IDs. Callers must pass the existing app's trusted
`current_user` function after its normal login/session flow.
"""

from dataclasses import dataclass

from modules.account_adapter import (
    AccountContextError,
    from_legacy_session_user,
)


@dataclass(frozen=True)
class AuthenticatedLegacyContext:
    """Immutable legacy identity snapshot; not a Phase 1 storage identity."""

    legacy_user_id: str
    username: str
    email: str
    display_name: str
    role: str
    identity_source: str = "legacy_app"


def from_server_current_user(current_user_fn):
    """Build context by invoking the trusted server-side current_user accessor.

    Do not pass a user dictionary, request parameter, form value, URL value, or
    browser-provided identity. The function itself must be the existing
    app.py current_user accessor, called only after the existing login flow.
    This wrapper is not an authentication or authorization mechanism.
    """
    if not callable(current_user_fn):
        raise AccountContextError(
            "A trusted server-side current_user function is required."
        )

    try:
        user = current_user_fn()
    except Exception as exc:
        raise AccountContextError(
            "Trusted authenticated account state could not be verified."
        ) from exc
    values = from_legacy_session_user(user)
    return AuthenticatedLegacyContext(**values)
