"""
NeuroLens feature flags.

Advanced features remain disabled until implemented
and tested. Initial Stage is independent.
"""

FEATURE_FLAGS = {
    "advanced_neurosocial": False,
    "behaviour_decoding": False,
    "facial_expression_studio": False,
    "advanced_ayna_ai": False,
    "research_engine_pro": False,
    "advanced_brain_lab": False,
    "hardware_hub": False,
    "owner_super_control": False,
    "advanced_privacy": False,
}


def is_enabled(feature_name):
    return FEATURE_FLAGS.get(feature_name, False)


def get_all_flags():
    return FEATURE_FLAGS.copy()
