"""
Atlas Validation Rules — Helix Phase 8

Each rule receives a parsed atlas entry dict and returns
a (passed: bool, reason: str) tuple.

Rules enforce:
  - Atomicity:      entry describes exactly one thing
  - Falsifiability: entry has concrete failure conditions or falsifiers
  - CrossRef:       linked experiments and evidence paths exist
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# Rule base
# ---------------------------------------------------------------------------

class Rule:
    name: str = "base"

    def check(self, entry: dict) -> tuple[bool, str]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Atomicity
# One entry = one claim. No compound discoveries bundled together.
# ---------------------------------------------------------------------------

class AtomicityRule(Rule):
    name = "atomicity"

    # Fields that, if missing or empty, indicate the entry is under-defined
    REQUIRED = {"title", "status", "mechanism", "predictions"}

    # Vague hedging phrases that indicate compound or unbounded claims
    VAGUE_PHRASES = [
        "and also", "in addition", "furthermore",
        "many things", "various", "everything",
        "it depends", "unclear", "tbd", "todo",
    ]

    def check(self, entry: dict) -> tuple[bool, str]:
        missing = [f for f in self.REQUIRED if not entry.get(f, "").strip()]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

        body = " ".join(str(v) for v in entry.values()).lower()
        for phrase in self.VAGUE_PHRASES:
            if phrase in body:
                return False, f"Vague language detected: '{phrase}'"

        return True, "ok"


# ---------------------------------------------------------------------------
# Falsifiability
# Entry must specify concrete conditions under which the claim fails.
# ---------------------------------------------------------------------------

class FalsifiabilityRule(Rule):
    name = "falsifiability"

    REQUIRED = {"falsifiers"}

    WEAK_PHRASES = [
        "unknown", "not yet", "to be determined",
        "unclear", "none", "n/a", "tbd",
    ]

    def check(self, entry: dict) -> tuple[bool, str]:
        falsifiers = entry.get("falsifiers", "").strip()
        if not falsifiers:
            return False, "No falsifiers defined — entry is not falsifiable"

        lower = falsifiers.lower()
        for phrase in self.WEAK_PHRASES:
            if phrase in lower and len(falsifiers) < 80:
                return (
                    False,
                    f"Falsifiers section appears empty or placeholder: '{falsifiers[:60]}'"
                )

        return True, "ok"


# ---------------------------------------------------------------------------
# Cross-Reference Integrity
# Linked experiments and evidence paths must exist on disk.
# ---------------------------------------------------------------------------

class CrossRefRule(Rule):
    name = "cross_ref"

    def check(self, entry: dict) -> tuple[bool, str]:
        evidence = entry.get("evidence", "")
        linked   = entry.get("linked_experiments", "")
        combined = f"{evidence}\n{linked}"

        broken = []
        for raw_line in combined.splitlines():
            line = raw_line.strip().lstrip("- ").strip()

            # Skip blank lines, bullet-only lines, and plain prose
            if not line or "/" not in line:
                continue

            # Skip http links
            if line.startswith("http"):
                continue

            # Strip markdown link syntax [text](path)
            if "](" in line:
                line = line.split("](")[1].rstrip(")")

            # Extract the first backtick-quoted segment if present
            if "`" in line:
                parts = line.split("`")
                # parts[1] is inside first pair of backticks (if balanced)
                if len(parts) >= 3:
                    line = parts[1]
                else:
                    line = line.replace("`", "")

            # Drop any trailing parenthetical — "(Phase 8 target)", "(source index, ...)"
            # These indicate annotations, not path suffixes
            if " (" in line:
                line = line.split(" (")[0]

            line = line.strip().rstrip(".,;")

            # Must look like a real path segment (not prose)
            if not line or " " in line or line.startswith("Run "):
                continue

            path = REPO_ROOT / line
            if not path.exists():
                broken.append(line)

        if broken:
            return (
                False,
                f"Broken references ({len(broken)}): {'; '.join(broken[:3])}"
                + (" ..." if len(broken) > 3 else ""),
            )

        return True, "ok"
