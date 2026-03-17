"""
HIL Normalizer — shim
======================
Delegates to core.normalization (the authoritative normalization layer).

This module is kept for backward compatibility with pre-existing callers.
New code should import directly from core.normalization.
"""
from __future__ import annotations

from core.normalization.normalizer import normalize, normalize_command  # noqa: F401
