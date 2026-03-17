"""
Root Structure Validator — Helix
=================================
Validates that the repository root contains only the allowed
architectural entries defined in HELIX.md.

Raises INVALID_ROOT_STRUCTURE if any unexpected entry is found.

Usage:
    from core.integrity.root_structure import validate_root_structure
    validate_root_structure()   # raises on violation

    # As an integrity probe:
    from core.integrity.root_structure import probe
    result = probe()            # returns RootStructureResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

ALLOWED_DIRS: frozenset[str] = frozenset({
    "core",
    "labs",
    "engines",
    "atlas",
    "interface",
    "artifacts",
    "runtime",
    "substrates",
    "applications",
    "datasets",
    "governance",
})

ALLOWED_FILES: frozenset[str] = frozenset({
    "HELIX.md",
    "OPERATOR.md",
    "ROADMAP.md",
    "README.md",
    "HIL.md",
    "DISSONANCE.md",
    "helix",
    ".git",
    ".gitignore",
    ".claude",
    "pyproject.toml",
})

ALLOWED: frozenset[str] = ALLOWED_DIRS | ALLOWED_FILES


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class INVALID_ROOT_STRUCTURE(Exception):
    """Raised when unexpected entries are found in the repository root."""


# ---------------------------------------------------------------------------
# Result dataclass (matches integrity probe interface)
# ---------------------------------------------------------------------------

@dataclass
class RootStructureResult:
    passed:     bool
    unexpected: list[str] = field(default_factory=list)
    details:    str = ""


# ---------------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------------

def validate_root_structure(root: Path = ROOT) -> RootStructureResult:
    """
    Validate that *root* contains only allowed architectural entries.

    Returns a RootStructureResult (passed=True) on success.
    Raises INVALID_ROOT_STRUCTURE on any violation.
    """
    unexpected = sorted(
        entry.name
        for entry in root.iterdir()
        if entry.name not in ALLOWED
    )

    if unexpected:
        raise INVALID_ROOT_STRUCTURE(
            "INVALID_ROOT_STRUCTURE: unexpected root entries: "
            + ", ".join(unexpected)
        )

    return RootStructureResult(
        passed=True,
        unexpected=[],
        details="Root structure is valid — all entries conform to HELIX.md.",
    )


# ---------------------------------------------------------------------------
# Integrity probe interface
# ---------------------------------------------------------------------------

def probe(root: Path = ROOT) -> RootStructureResult:
    """
    Integrity probe entry point.

    Returns RootStructureResult with passed=False (never raises) so
    the integrity harness can handle the failure uniformly.
    """
    try:
        return validate_root_structure(root)
    except INVALID_ROOT_STRUCTURE as exc:
        unexpected = sorted(
            entry.name
            for entry in root.iterdir()
            if entry.name not in ALLOWED
        )
        return RootStructureResult(
            passed=False,
            unexpected=unexpected,
            details=str(exc),
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    result = probe()
    print(result.details)
    if not result.passed:
        print("Unexpected entries:", ", ".join(result.unexpected))
    sys.exit(0 if result.passed else 1)
