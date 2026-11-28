"""Read-only resolution of an existing legacy-to-Phase-1 identity mapping.

No mapping is created here. The lookup callable must query an approved,
authoritative mapping store and enforce uniqueness. This module is not
authentication, account linking, or authorization.
"""

from modules.authenticated_context import AuthenticatedLegacyContext


class IdentityMappingError(ValueError):
    """Raised when a verified identity mapping is absent or malformed."""


def resolve_phase1_user_id(authenticated_context, mapping_lookup):
    """Resolve an existing Phase 1 integer ID using the exact legacy text ID.

    The caller must obtain the context from the existing server-side
    authentication flow. The lookup must return the unique mapped Phase 1 ID,
    or None when no mapping exists. No username/email matching or auto-linking
    is performed. The result is an identifier only; it grants no privileges.
    """
    if type(authenticated_context) is not AuthenticatedLegacyContext:
        raise IdentityMappingError(
            "A server-session authenticated legacy context is required."
        )
    if not callable(mapping_lookup):
        raise IdentityMappingError("An authoritative mapping lookup is required.")

    # The context type alone is not sufficient: callers can construct this
    # dataclass directly. Validate the identifier before passing it to storage.
    legacy_user_id = authenticated_context.legacy_user_id
    if type(legacy_user_id) is not str or not legacy_user_id.strip() or len(legacy_user_id) > 128:
        raise IdentityMappingError("The authenticated legacy account ID is invalid.")

    try:
        phase1_user_id = mapping_lookup(legacy_user_id)
    except Exception as exc:
        raise IdentityMappingError(
            "The authoritative account mapping could not be verified."
        ) from exc
    if phase1_user_id is None:
        raise IdentityMappingError("No verified account mapping exists.")
    # Accept only a built-in integer, not an int subclass with custom
    # comparison/conversion behavior supplied by an untrusted mapping layer.
    if type(phase1_user_id) is not int or phase1_user_id <= 0:
        raise IdentityMappingError("The stored Phase 1 mapping is invalid.")

    return phase1_user_id
