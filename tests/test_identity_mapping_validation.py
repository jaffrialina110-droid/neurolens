import unittest

from modules.identity_mapping_validation import (
    IdentityMappingValidationError,
    validate_mapping_rows,
)


class IdentityMappingSnapshotValidationTests(unittest.TestCase):
    def test_accepts_unique_one_to_one_rows(self):
        rows = [
            {"legacy_user_id": "legacy-A", "phase1_user_id": 11},
            {"legacy_user_id": "legacy-B", "phase1_user_id": 12},
        ]
        self.assertEqual(
            validate_mapping_rows(rows),
            (("legacy-A", 11), ("legacy-B", 12)),
        )

    def test_preserves_legacy_id_exactly(self):
        rows = [{"legacy_user_id": " legacy-A ", "phase1_user_id": 11}]
        self.assertEqual(
            validate_mapping_rows(rows),
            ((" legacy-A ", 11),),
        )

    def test_rejects_duplicate_legacy_ids(self):
        rows = [
            {"legacy_user_id": "legacy-A", "phase1_user_id": 11},
            {"legacy_user_id": "legacy-A", "phase1_user_id": 12},
        ]
        with self.assertRaises(IdentityMappingValidationError):
            validate_mapping_rows(rows)

    def test_rejects_duplicate_phase1_ids(self):
        rows = [
            {"legacy_user_id": "legacy-A", "phase1_user_id": 11},
            {"legacy_user_id": "legacy-B", "phase1_user_id": 11},
        ]
        with self.assertRaises(IdentityMappingValidationError):
            validate_mapping_rows(rows)

    def test_rejects_invalid_legacy_ids(self):
        for invalid in (None, 7, "", "   ", b"legacy"):
            with self.subTest(value=invalid):
                with self.assertRaises(IdentityMappingValidationError):
                    validate_mapping_rows(
                        [{"legacy_user_id": invalid, "phase1_user_id": 11}]
                    )

    def test_rejects_invalid_phase1_ids(self):
        for invalid in (None, 0, -1, True, False, "11", 11.0, [], {}):
            with self.subTest(value=invalid):
                with self.assertRaises(IdentityMappingValidationError):
                    validate_mapping_rows(
                        [{"legacy_user_id": "legacy-A", "phase1_user_id": invalid}]
                    )

    def test_rejects_non_object_rows_and_non_iterable_inputs(self):
        for invalid in (None, "not rows", {"legacy_user_id": "legacy-A"}):
            with self.subTest(value=invalid):
                with self.assertRaises(IdentityMappingValidationError):
                    validate_mapping_rows(invalid)
        with self.assertRaises(IdentityMappingValidationError):
            validate_mapping_rows([("legacy-A", 11)])

    def test_empty_snapshot_is_valid(self):
        self.assertEqual(validate_mapping_rows([]), ())


if __name__ == "__main__":
    unittest.main()
