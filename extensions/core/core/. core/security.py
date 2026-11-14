"""
NeuroLens security utilities.
Existing password and journal formats are not modified.
"""

import hashlib
import hmac
import secrets
import time


def generate_secure_token(length=32):
    """Generate a cryptographically secure random token."""
    if not isinstance(length, int) or length < 16:
        raise ValueError("Token length must be at least 16.")

    return secrets.token_urlsafe(length)


def constant_time_compare(value_a, value_b):
    """Compare two values without ordinary string comparison timing."""
    if not isinstance(value_a, str):
        return False

    if not isinstance(value_b, str):
        return False

    return hmac.compare_digest(
        value_a.encode("utf-8"),
        value_b.encode("utf-8")
    )


def hash_recovery_token(token, salt):
    """Hash a recovery token using SHA-256 with a supplied salt."""
    if not token or not salt:
        raise ValueError("Token and salt are required.")

    return hashlib.sha256(
        (salt + token).encode("utf-8")
    ).hexdigest()


def verify_recovery_token(token, salt, stored_hash):
    """Verify a recovery token hash."""
    calculated = hash_recovery_token(token, salt)

    return constant_time_compare(
        calculated,
        stored_hash
    )


class AttemptLimiter:
    """Simple in-memory attempt limiter."""

    def __init__(self, max_attempts=5, lock_seconds=600):
        self.max_attempts = max_attempts
        self.lock_seconds = lock_seconds
        self.attempts = {}

    def is_locked(self, user_key):
        record = self.attempts.get(user_key)

        if not record:
            return False

        count, locked_until = record

        if locked_until and time.time() < locked_until:
            return True

        if locked_until:
            self.attempts.pop(user_key, None)

        return False

    def failed_attempt(self, user_key):
        count, _ = self.attempts.get(user_key, (0, None))
        count += 1

        locked_until = None

        if count >= self.max_attempts:
            locked_until = time.time() + self.lock_seconds

        self.attempts[user_key] = (count, locked_until)

        return self.is_locked(user_key)

    def reset(self, user_key):
        self.attempts.pop(user_key, None)
