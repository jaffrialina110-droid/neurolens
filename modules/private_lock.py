"""Secure primitives for a future user-controlled private-space PIN lock.

These helpers are deliberately independent of Streamlit session state and
storage. They do not implement account recovery, authentication, encryption,
or access control by themselves.
"""

import hashlib
import hmac
import math
import secrets
import time


PIN_HASH_ALGORITHM = "pbkdf2_sha256"
PIN_HASH_ITERATIONS = 600_000
PIN_HASH_MIN_ITERATIONS = 100_000
PIN_HASH_MAX_ITERATIONS = 5_000_000
PIN_MIN_LENGTH = 6
PIN_MAX_LENGTH = 12
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_LOCKOUT_SECONDS = 300


class PrivateLockError(ValueError):
    """Raised when PIN policy or lockout parameters are invalid."""


def _validate_pin(pin):
    if not isinstance(pin, str):
        raise PrivateLockError("PIN must be text.")
    if not (PIN_MIN_LENGTH <= len(pin) <= PIN_MAX_LENGTH):
        raise PrivateLockError("PIN must contain 6 to 12 digits.")
    if not pin.isascii() or not pin.isdigit():
        raise PrivateLockError("PIN must contain ASCII digits only.")
    return pin


def hash_pin(pin, *, salt=None, iterations=PIN_HASH_ITERATIONS):
    """Return a salted PBKDF2 hash string; never store the raw PIN."""
    pin = _validate_pin(pin)
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not (PIN_HASH_MIN_ITERATIONS <= iterations <= PIN_HASH_MAX_ITERATIONS):
        raise PrivateLockError("PIN hash iteration count is invalid.")
    if salt is None:
        salt_bytes = secrets.token_bytes(16)
    elif isinstance(salt, bytes) and 16 <= len(salt) <= 64:
        salt_bytes = salt
    else:
        raise PrivateLockError("PIN salt must contain 16 to 64 random bytes.")

    digest = hashlib.pbkdf2_hmac(
        "sha256", pin.encode("ascii"), salt_bytes, iterations
    )
    return "$".join(
        (PIN_HASH_ALGORITHM, str(iterations), salt_bytes.hex(), digest.hex())
    )


def verify_pin(pin, encoded_hash):
    """Verify a PIN against the encoded salted hash without raising on bad input."""
    try:
        pin = _validate_pin(pin)
        if not isinstance(encoded_hash, str):
            return False
        algorithm, iterations_text, salt_hex, digest_hex = encoded_hash.split("$")
        if algorithm != PIN_HASH_ALGORITHM:
            return False
        if not iterations_text.isascii() or not iterations_text.isdigit():
            return False
        if (
            not (32 <= len(salt_hex) <= 128)
            or len(salt_hex) % 2 != 0
            or len(digest_hex) != 64
            or any(character not in "0123456789abcdef" for character in salt_hex)
            or any(character not in "0123456789abcdef" for character in digest_hex)
        ):
            return False
        iterations = int(iterations_text)
        if iterations < PIN_HASH_MIN_ITERATIONS or iterations > PIN_HASH_MAX_ITERATIONS:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        if len(salt) < 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", pin.encode("ascii"), salt, iterations
        )
        return hmac.compare_digest(actual, expected)
    except (PrivateLockError, TypeError, ValueError):
        return False


def new_attempt_state():
    """Create a fresh in-memory attempt state for one locked session."""
    return {"failed_attempts": 0, "locked_until": 0.0}


def is_rate_limited(state, *, now=None):
    """Return True while the lockout deadline has not elapsed."""
    _validate_attempt_state(state)
    current = time.time() if now is None else _validate_timestamp(now)
    return current < state["locked_until"]


def record_pin_attempt(state, *, success, now=None, max_attempts=DEFAULT_MAX_ATTEMPTS,
                       lockout_seconds=DEFAULT_LOCKOUT_SECONDS):
    """Record one PIN attempt and return a new state dictionary.

    A successful verification clears the counter. Reaching max_attempts starts
    a timed lockout. The caller must persist this state server-side and must
    not trust client-supplied counters or timestamps.
    """
    _validate_attempt_state(state)
    if not isinstance(success, bool):
        raise PrivateLockError("success must be boolean.")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        raise PrivateLockError("max_attempts must be a positive integer.")
    if isinstance(lockout_seconds, bool) or not isinstance(lockout_seconds, int) or lockout_seconds < 1:
        raise PrivateLockError("lockout_seconds must be a positive integer.")

    current = time.time() if now is None else _validate_timestamp(now)
    if current < state["locked_until"]:
        return dict(state)

    if success:
        return new_attempt_state()

    failures = state["failed_attempts"] + 1
    locked_until = current + lockout_seconds if failures >= max_attempts else 0.0
    return {"failed_attempts": failures, "locked_until": locked_until}


def private_session_expired(last_activity_at, *, now=None, timeout_seconds=900):
    """Check inactivity since the last trusted server-side activity timestamp."""
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or timeout_seconds < 1:
        raise PrivateLockError("timeout_seconds must be a positive integer.")
    last_activity = _validate_timestamp(last_activity_at)
    current = time.time() if now is None else _validate_timestamp(now)
    return current - last_activity >= timeout_seconds


def _validate_timestamp(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PrivateLockError("Timestamp must be numeric.")
    if not math.isfinite(value) or value < 0:
        raise PrivateLockError("Timestamp must be finite and non-negative.")
    return float(value)


def _validate_attempt_state(state):
    if not isinstance(state, dict):
        raise PrivateLockError("Attempt state must be a server-side dictionary.")
    failures = state.get("failed_attempts")
    locked_until = state.get("locked_until")
    if isinstance(failures, bool) or not isinstance(failures, int) or failures < 0:
        raise PrivateLockError("Attempt counter is invalid.")
    _validate_timestamp(locked_until)
