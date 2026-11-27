"""Authenticated encryption helpers for persisted NeuroLens AI chat messages.

This module provides encryption at rest, not end-to-end encryption.
The deployment master secret must be supplied by the caller and never stored here.
"""
import base64
import hashlib
import json
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


CONTENT_VERSION = 1
NONCE_BYTES = 12
KEY_BYTES = 32
_CONTEXT = b"neurolens/ai-chat/aesgcm/v1"


class AIChatCryptoError(Exception):
    """Safe-to-handle AI chat encryption/decryption failure."""


def _derive_user_key(master_secret, user_id):
    if not isinstance(master_secret, str) or len(master_secret.encode("utf-8")) < 32:
        raise AIChatCryptoError("AI chat encryption is not configured.")
    if not isinstance(user_id, str) or not user_id.strip():
        raise AIChatCryptoError("AI chat encryption context is invalid.")
    user_salt = hashlib.sha256(
        b"neurolens-ai-chat-user-salt-v1:" + user_id.encode("utf-8")
    ).digest()
    try:
        return HKDF(
            algorithm=hashes.SHA256(),
            length=KEY_BYTES,
            salt=user_salt,
            info=_CONTEXT + b":" + user_id.encode("utf-8"),
        ).derive(master_secret.encode("utf-8"))
    except Exception as exc:
        raise AIChatCryptoError("AI chat encryption is unavailable.") from exc


def _aad(message_id, conversation_id, user_id, role):
    fields = (message_id, conversation_id, user_id, role)
    if any(not isinstance(value, str) or not value for value in fields):
        raise AIChatCryptoError("AI chat message context is invalid.")
    return json.dumps(
        {"v": CONTENT_VERSION, "message_id": message_id,
         "conversation_id": conversation_id, "user_id": user_id, "role": role},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def encrypt_ai_message(master_secret, message_id, conversation_id, user_id, role, plaintext):
    if not isinstance(plaintext, str):
        raise AIChatCryptoError("AI chat message must be text.")
    key = _derive_user_key(master_secret, user_id)
    nonce = secrets.token_bytes(NONCE_BYTES)
    try:
        encrypted = AESGCM(key).encrypt(
            nonce, plaintext.encode("utf-8"),
            _aad(message_id, conversation_id, user_id, role),
        )
    except AIChatCryptoError:
        raise
    except Exception as exc:
        raise AIChatCryptoError("AI chat message could not be encrypted.") from exc
    return (
        base64.b64encode(encrypted).decode("ascii"),
        base64.b64encode(nonce).decode("ascii"),
        CONTENT_VERSION,
    )


def decrypt_ai_message(master_secret, message_id, conversation_id, user_id, role,
                       ciphertext_b64, nonce_b64, content_version):
    if content_version != CONTENT_VERSION:
        raise AIChatCryptoError("Unsupported AI chat encryption version.")
    key = _derive_user_key(master_secret, user_id)
    try:
        ciphertext = base64.b64decode(ciphertext_b64, validate=True)
        nonce = base64.b64decode(nonce_b64, validate=True)
        if len(nonce) != NONCE_BYTES:
            raise ValueError("Invalid nonce length")
        plaintext = AESGCM(key).decrypt(
            nonce, ciphertext,
            _aad(message_id, conversation_id, user_id, role),
        )
        return plaintext.decode("utf-8")
    except AIChatCryptoError:
        raise
    except Exception as exc:
        raise AIChatCryptoError("AI chat message could not be authenticated.") from exc
