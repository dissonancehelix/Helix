"""
Validation Pipeline — Helix Phase 8

Runs an atlas entry through all validation rules and returns
a structured ValidationResult.

Usage:
    from core.validator import validate_entry
    result = validate_entry(entry_dict)
    if not result.passed:
        print(result.report())
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .rules import AtomicityRule, FalsifiabilityRule, CrossRefRule


RULES = [
    AtomicityRule(),
    FalsifiabilityRule(),
    CrossRefRule(),
]


# ---------------------------------------------------------------------------
# Entry parser
# Reads a Phase 8 markdown atlas file into a dict of sections.
# ---------------------------------------------------------------------------

SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def parse_entry_md(path: Path) -> dict:
    """Parse a Phase 8 atlas markdown file into section dict."""
    text = path.read_text()
    entry: dict[str, str] = {}

    # Extract title from first heading
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if title_match:
        entry["title"] = title_match.group(1).strip()

    # Extract metadata lines (bold key: value)
    for m in re.finditer(r"\*\*(.+?)\*\*[:\s]+(.+)", text):
        key = m.group(1).strip().lower().replace(" ", "_").rstrip(":")
        entry[key] = m.group(2).strip()

    # Extract sections
    sections = SECTION_RE.split(text)
    # sections alternates: [pre, heading, body, heading, body, ...]
    for i in range(1, len(sections) - 1, 2):
        heading = sections[i].strip().lower().replace(" ", "_")
        body    = sections[i + 1].strip() if i + 1 < len(sections) else ""
        entry[heading] = body

    return entry


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class RuleResult:
    rule:   str
    passed: bool
    reason: str


@dataclass
class ValidationResult:
    entry_path: str
    passed:     bool
    results:    list[RuleResult] = field(default_factory=list)

    def report(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines  = [f"[{status}] {self.entry_path}"]
        for r in self.results:
            icon = "✓" if r.passed else "✗"
            lines.append(f"  {icon} {r.rule}: {r.reason}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def validate_entry(entry: dict, path: str = "<unknown>") -> ValidationResult:
    """
    Run all rules against an atlas entry dict.
    Returns a ValidationResult.
    """
    rule_results = []
    all_passed   = True

    for rule in RULES:
        passed, reason = rule.check(entry)
        rule_results.append(RuleResult(rule=rule.name, passed=passed, reason=reason))
        if not passed:
            all_passed = False

    return ValidationResult(
        entry_path=path,
        passed=all_passed,
        results=rule_results,
    )


def validate_file(path: Path) -> ValidationResult:
    """Parse a markdown atlas entry file and validate it."""
    try:
        entry = parse_entry_md(path)
    except Exception as e:
        return ValidationResult(
            entry_path=str(path),
            passed=False,
            results=[RuleResult(rule="parse", passed=False, reason=str(e))],
        )
    return validate_entry(entry, path=str(path))
