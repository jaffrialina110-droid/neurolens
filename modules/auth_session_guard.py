"""Fail-closed adapter for revalidating a legacy authenticated session.

All callbacks must read trusted server-side state. This module does not create
sessions, authenticate credentials, or provide authorization by itself.
"""

from dataclasses import dataclass


class AuthSessionError(ValueError):
    """Raised when trusted authentication-session state is unavailable."""


@dataclass(frozen=True)
class ActiveAuthSession:
    legacy_user_id: str
    auth_session_id: str
    session_generation: int


def resolve_active_auth_session(
    *,
    current_user_fn,
    auth_session_id_fn,
    account_is_active_fn,
    session_generation_fn,
):
    """Revalidate identity, active status, and session generation on each call.

    The callbacks must be trusted server-side functions. The session ID must
    be unguessable, server-generated, rotated on login, and revoked on logout.
    The generation must be server-controlled and incremented when sessions
    should be invalidated (for example password reset or global logout).
    """
    callbacks = (
        current_user_fn,
        auth_session_id_fn,
        account_is_active_fn,
        session_generation_fn,
    )
    if not all(callable(callback) for callback in callbacks):
        raise AuthSessionError("All trusted server-side callbacks are required.")

    try:
        user = current_user_fn()
    except Exception as exc:
        raise AuthSessionError("Trusted authentication state could not be verified.") from exc
    if not isinstance(user, dict):
        raise AuthSessionError("No authenticated server-side user is available.")

    legacy_user_id = user.get("id")
    if not isinstance(legacy_user_id, (str, int)) or isinstance(legacy_user_id, bool):
        raise AuthSessionError("A valid authenticated user ID is required.")
    legacy_user_id = str(legacy_user_id).strip()
    if not legacy_user_id or len(legacy_user_id) > 128:
        raise AuthSessionError("A valid authenticated user ID is required.")

    try:
        session_id = auth_session_id_fn()
    except Exception as exc:
        raise AuthSessionError("Trusted authentication state could not be verified.") from exc
    if (
        not isinstance(session_id, str)
        or not session_id
        or len(session_id) > 256
        or not session_id.isprintable()
        or any(character.isspace() for character in session_id)
    ):
        raise AuthSessionError("A server-controlled authentication session ID is required.")

    try:
        active = account_is_active_fn(legacy_user_id)
    except Exception as exc:
        raise AuthSessionError("Trusted authentication state could not be verified.") from exc
    if active is not True:
        raise AuthSessionError("The account is inactive or could not be verified.")

    try:
        generation = session_generation_fn(legacy_user_id)
    except Exception as exc:
        raise AuthSessionError("Trusted authentication state could not be verified.") from exc
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise AuthSessionError("A valid server-controlled session generation is required.")

    return ActiveAuthSession(
        legacy_user_id=legacy_user_id,
        auth_session_id=session_id,
        session_generation=generation,
    )


def session_generation_matches(authenticated_generation, current_generation):
    """Return true only when the login-time generation still matches server state.

    authenticated_generation must be the generation captured in trusted
    server-side session state at login. current_generation must be freshly
    read from the authoritative account store. A mismatch invalidates the
    authentication session and any private unlock bound to it.
    """
    for value in (authenticated_generation, current_generation):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return False
    return authenticated_generation == current_generation
