"""Pure private-session lifecycle helpers.

The caller must keep session records in trusted server-side session state.
These helpers are not authentication, authorization, or persistent revocation.
"""

import time

from modules.private_lock import PrivateLockError, _validate_timestamp


SESSION_TIMEOUT_SECONDS = 900


def unlock_private_session(user_id, auth_session_id, *, now=None):
    """Create a server-side unlock record after successful PIN verification."""
    _validate_user_id(user_id)
    _validate_auth_session_id(auth_session_id)
    current = time.time() if now is None else _validate_timestamp(now)
    return {
        "unlocked": True,
        "user_id": user_id,
        "auth_session_id": auth_session_id,
        "last_activity_at": current,
    }


def validate_private_session(
    record,
    *,
    user_id,
    auth_session_id,
    now=None,
    timeout_seconds=SESSION_TIMEOUT_SECONDS,
):
    """Return (is_valid, refreshed_record); fail closed on logout/account switch.

    Call only after the main account authentication layer has independently
    validated the current auth_session_id. The record itself is not proof of
    identity and must never be accepted from browser/client input.
    """
    _validate_user_id(user_id)
    try:
        _validate_auth_session_id(auth_session_id)
    except PrivateLockError:
        return False, locked_private_session()
    if (
        type(timeout_seconds) is not int
        or timeout_seconds < 1
    ):
        raise PrivateLockError("timeout_seconds must be a positive integer.")
    current = time.time() if now is None else _validate_timestamp(now)

    # Accept only the plain server-created record shape; custom mapping
    # subclasses can execute arbitrary code from get()/iteration methods.
    if type(record) is not dict or record.get("unlocked") is not True:
        return False, locked_private_session()
    try:
        record_user_id = _validate_user_id(record.get("user_id"))
        record_auth_session_id = _validate_auth_session_id(
            record.get("auth_session_id")
        )
        last_activity = _validate_timestamp(record.get("last_activity_at"))
    except PrivateLockError:
        return False, locked_private_session()

    if record_user_id != user_id or record_auth_session_id != auth_session_id:
        return False, locked_private_session()
    if current < last_activity or current - last_activity >= timeout_seconds:
        return False, locked_private_session()

    # Rebuild only the approved fields instead of carrying unknown keys into
    # refreshed session state.
    refreshed = {
        "unlocked": True,
        "user_id": record_user_id,
        "auth_session_id": record_auth_session_id,
        "last_activity_at": current,
    }
    return True, refreshed


def locked_private_session():
    """Return a locked state with no retained account/session identifiers."""
    return {
        "unlocked": False,
        "user_id": None,
        "auth_session_id": None,
        "last_activity_at": None,
    }


def _validate_user_id(user_id):
    if type(user_id) is not int or user_id <= 0:
        raise PrivateLockError("A positive authenticated user ID is required.")
    return user_id


def _validate_auth_session_id(value):
    if (
        type(value) is not str
        or not value
        or len(value) > 256
        or not value.isprintable()
        or any(character.isspace() for character in value)
    ):
        raise PrivateLockError("A valid authenticated session reference is required.")
    return value
