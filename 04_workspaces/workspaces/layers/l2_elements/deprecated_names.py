import warnings

# Helix — Element Name Mapping (Canonicalization)
# This module provides a mapping for backwards compatibility during refactor.

ELEMENT_MAPPING = {
    "C3": "C3",
    "C4": "C4"
}

def get_canonical(name):
    if name in ELEMENT_MAPPING:
        warnings.warn(f"Deprecated element name '{name}' used. Mapping to '{ELEMENT_MAPPING[name]}'.", DeprecationWarning, stacklevel=2)
        return ELEMENT_MAPPING[name]
    return name

# Reverse mapping for forensic analysis
LEGACY_MAPPING = {v: k for k, v in ELEMENT_MAPPING.items()}
