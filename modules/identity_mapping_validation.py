"""Offline validation for a proposed legacy-to-Phase-1 mapping snapshot.

This module validates data before a future, separately approved migration.
It does not connect to a database, create mappings, or authorize accounts.
"""


class IdentityMappingValidationError(ValueError):
    """Raised when a proposed mapping snapshot is malformed or ambiguous."""


def validate_mapping_rows(rows):
    """Validate one-to-one mapping rows and return immutable identity pairs.

    Each row must contain legacy_user_id (non-empty text) and phase1_user_id
    (positive integer). Legacy IDs are preserved exactly: no trimming,
    case-folding, or numeric coercion is performed. Both sides must be unique.
    Extra row fields are ignored and never used for identity matching.
    """
    if isinstance(rows, (str, bytes, dict)) or rows is None:
        raise IdentityMappingValidationError("Mapping rows must be an iterable of row objects.")

    try:
        iterator = iter(rows)
    except TypeError as exc:
        raise IdentityMappingValidationError("Mapping rows must be iterable.") from exc

    validated = []
    seen_legacy_ids = set()
    seen_phase1_ids = set()

    for index, row in enumerate(iterator):
        if not isinstance(row, dict):
            raise IdentityMappingValidationError(f"Mapping row {index} must be an object.")

        legacy_id = row.get("legacy_user_id")
        phase1_id = row.get("phase1_user_id")

        if not isinstance(legacy_id, str) or not legacy_id or not legacy_id.strip():
            raise IdentityMappingValidationError(
                f"Mapping row {index} has an invalid legacy user ID."
            )
        if isinstance(phase1_id, bool) or not isinstance(phase1_id, int) or phase1_id <= 0:
            raise IdentityMappingValidationError(
                f"Mapping row {index} has an invalid Phase 1 user ID."
            )
        if legacy_id in seen_legacy_ids:
            raise IdentityMappingValidationError("A legacy user ID appears more than once.")
        if phase1_id in seen_phase1_ids:
            raise IdentityMappingValidationError("A Phase 1 user ID appears more than once.")

        seen_legacy_ids.add(legacy_id)
        seen_phase1_ids.add(phase1_id)
        validated.append((legacy_id, phase1_id))

    return tuple(validated)
