import unittest

from modules.ai_chat_crypto import (
    AIChatCryptoError, CONTENT_VERSION, decrypt_ai_message, encrypt_ai_message
)


SECRET = "test-only-master-secret-with-at-least-32-bytes"


class AIChatCryptoTests(unittest.TestCase):
    def setUp(self):
        self.context = ("msg-1", "conv-1", "user-1", "user")
        self.plaintext = "Private research question"

    def encrypt(self, text=None, context=None, secret=SECRET):
        return encrypt_ai_message(
            secret, *(context or self.context),
            self.plaintext if text is None else text,
        )

    def decrypt(self, encrypted, context=None, secret=SECRET, version=None):
        ciphertext, nonce, stored_version = encrypted
        return decrypt_ai_message(
            secret, *(context or self.context), ciphertext, nonce,
            stored_version if version is None else version,
        )

    def test_round_trip(self):
        encrypted = self.encrypt()
        self.assertEqual(encrypted[2], CONTENT_VERSION)
        self.assertNotIn(self.plaintext, encrypted[0])
        self.assertEqual(self.decrypt(encrypted), self.plaintext)

    def test_each_encryption_uses_fresh_nonce(self):
        first = self.encrypt()
        second = self.encrypt()
        self.assertNotEqual(first[1], second[1])

    def test_wrong_user_fails_authentication(self):
        encrypted = self.encrypt()
        wrong_context = ("msg-1", "conv-1", "user-2", "user")
        with self.assertRaises(AIChatCryptoError):
            self.decrypt(encrypted, context=wrong_context)

    def test_changed_message_context_fails(self):
        encrypted = self.encrypt()
        wrong_context = ("msg-2", "conv-1", "user-1", "user")
        with self.assertRaises(AIChatCryptoError):
            self.decrypt(encrypted, context=wrong_context)

    def test_tampering_fails(self):
        ciphertext, nonce, version = self.encrypt()
        tampered = ("A" + ciphertext[1:], nonce, version)
        with self.assertRaises(AIChatCryptoError):
            self.decrypt(tampered)

    def test_wrong_master_secret_fails(self):
        encrypted = self.encrypt()
        with self.assertRaises(AIChatCryptoError):
            self.decrypt(encrypted, secret="another-test-secret-with-32-bytes")

    def test_missing_or_short_secret_fails_closed(self):
        with self.assertRaises(AIChatCryptoError):
            self.encrypt(secret="")
        with self.assertRaises(AIChatCryptoError):
            self.encrypt(secret="too-short")

    def test_unknown_version_fails_closed(self):
        encrypted = self.encrypt()
        with self.assertRaises(AIChatCryptoError):
            self.decrypt(encrypted, version=99)

    def test_nonce_validation(self):
        encrypted = self.encrypt()
        bad_nonce = (encrypted[0], "bm90LWEtMTItYnl0ZS1ub25jZQ==", encrypted[2])
        with self.assertRaises(AIChatCryptoError):
            self.decrypt(bad_nonce)


if __name__ == "__main__":
    unittest.main()
