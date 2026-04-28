"""
Normalization — Error Types
============================
"""
from __future__ import annotations


class NormalizationError(ValueError):
    """Raised when input cannot be normalized to a valid canonical form."""

    def __init__(self, message: str, raw: str = "") -> None:
        self.raw = raw
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"error": "NormalizationError", "message": str(self), "raw": self.raw}


class InvalidIDError(NormalizationError):
    """Raised when an entity ID does not match the canonical pattern."""
    pass


class DuplicateEntityError(NormalizationError):
    """Raised when normalization detects an entity ID already registered."""
    pass
