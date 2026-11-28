"""Read-only bridge from the legacy NeuroLens session to Phase 1 modules.

This adapter deliberately performs no database access, account creation,
password handling, or identity migration.
"""


class AccountContextError(ValueError):
    """Raised when the legacy authenticated user context is incomplete."""


def from_legacy_session_user(user):
    """Return a minimal stable account context from an authenticated legacy user.

    The caller must first establish authentication using the existing app
    login flow. This function does not authenticate the user or trust arbitrary
    client-supplied identifiers.
    """
    if type(user) is not dict:
        raise AccountContextError("An authenticated legacy user is required.")

    user_id = user.get("id")
    if not isinstance(user_id, str) or not user_id.strip():
        raise AccountContextError("Legacy user ID is missing or invalid.")

    username = user.get("username")
    email = user.get("email")
    display_name = user.get("display_name")
    role = user.get("role")

    for field, value in (
        ("username", username),
        ("email", email),
        ("display_name", display_name),
        ("role", role),
    ):
        if not isinstance(value, str) or not value.strip():
            raise AccountContextError(f"Legacy user {field} is missing.")

    # Preserve the legacy ID exactly. Never coerce it to the Phase 1 integer ID.
    return {
        "legacy_user_id": user_id,
        "username": username.strip(),
        "email": email.strip(),
        "display_name": display_name.strip(),
        "role": role.strip(),
        "identity_source": "legacy_app",
    }
