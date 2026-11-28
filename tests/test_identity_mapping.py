import unittest

from modules.authenticated_context import AuthenticatedLegacyContext
from modules.identity_mapping import (
    IdentityMappingError,
    resolve_phase1_user_id,
)


class ReadOnlyIdentityMappingTests(unittest.TestCase):
    def setUp(self):
        self.context = AuthenticatedLegacyContext(
            legacy_user_id=" legacy-text-007 ",
            username="member",
            email="member@example.test",
            display_name="Member",
            role="user",
        )

    def test_uses_exact_legacy_id_and_returns_existing_phase1_id(self):
        seen = []

        def lookup(legacy_id):
            seen.append(legacy_id)
            return 42

        self.assertEqual(resolve_phase1_user_id(self.context, lookup), 42)
        self.assertEqual(seen, [" legacy-text-007 "])

    def test_missing_mapping_fails_closed(self):
        with self.assertRaises(IdentityMappingError):
            resolve_phase1_user_id(self.context, lambda legacy_id: None)

    def test_rejects_invalid_phase1_mapping_values(self):
        for invalid in (0, -1, True, False, "42", 42.0, {}, []):
            with self.subTest(value=invalid):
                with self.assertRaises(IdentityMappingError):
                    resolve_phase1_user_id(self.context, lambda legacy_id: invalid)

    def test_rejects_untrusted_or_wrong_context_type(self):
        for invalid in (None, {}, {"legacy_user_id": "legacy-text-007"}, "legacy"):
            with self.subTest(value=invalid):
                with self.assertRaises(IdentityMappingError):
                    resolve_phase1_user_id(invalid, lambda legacy_id: 42)

    def test_rejects_missing_lookup(self):
        with self.assertRaises(IdentityMappingError):
            resolve_phase1_user_id(self.context, None)

    def test_does_not_attempt_username_or_email_matching(self):
        received = []

        def lookup(legacy_id):
            received.append(legacy_id)
            return None

        with self.assertRaises(IdentityMappingError):
            resolve_phase1_user_id(self.context, lookup)
        self.assertEqual(received, [self.context.legacy_user_id])


if __name__ == "__main__":
    unittest.main()
