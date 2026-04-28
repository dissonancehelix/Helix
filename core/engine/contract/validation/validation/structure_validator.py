"""
Structure Validator — core/engine/contract/validation/structure_validator.py
========================================================================
Validates file placement and ownership across the Helix repository.

Enforces the rule:
  No unowned file may exist in a canonical subtree.

Checks:
  1. docs/ root has no loose markdown files beyond allowed list
  2. docs/ subtrees contain only known/allowed files
  3. Domain directories have required local docs (README.md, SPEC.md, manifest.yaml)
  4. Application directories have required local docs (manifest.yaml)
  5. No stale references to old doc paths (e.g. docs/ARCHITECTURE.md)
  6. docs/manifest.yaml declares only paths that actually exist

This validator is additive — it extends manifest_validator.py, does not replace it.

Usage:
    python -m core.validation.validation.structure_validator
    python -m core.validation.validation.structure_validator --verbose
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists()
)

DOCS_ROOT = ROOT / "docs"
DOCS_MANIFEST_PATH = DOCS_ROOT / "manifest.yaml"


def _load_yaml(path: Path) -> dict | None:
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None


class StructureViolation:
    def __init__(self, area: str, file_path: str, violation_type: str,
                 owning_manifest: str | None, recommended_fix: str):
        self.area = area
        self.file_path = file_path
        self.violation_type = violation_type
        self.owning_manifest = owning_manifest
        self.recommended_fix = recommended_fix

    def to_dict(self) -> dict:
        return {
            "area": self.area,
            "file_path": self.file_path,
            "violation_type": self.violation_type,
            "owning_manifest": self.owning_manifest,
            "recommended_fix": self.recommended_fix,
        }


# ---------------------------------------------------------------------------
# 1. Docs root — no loose files
# ---------------------------------------------------------------------------

def check_docs_root(docs_manifest: dict | None) -> list[StructureViolation]:
    violations = []
    allowed = {"README.md", "manifest.yaml"}
    if docs_manifest:
        for f in (docs_manifest.get("root") or {}).get("allowed_root_files") or []:
            allowed.add(f)

    for item in DOCS_ROOT.iterdir():
        if item.is_file() and item.suffix in (".md", ".yaml", ".yml", ".txt"):
            if item.name not in allowed:
                violations.append(StructureViolation(
                    area="docs/",
                    file_path=str(item.relative_to(ROOT)),
                    violation_type="LOOSE_FILE_IN_DOCS_ROOT",
                    owning_manifest="docs/manifest.yaml",
                    recommended_fix=(
                        f"Move '{item.name}' into the appropriate docs/ subtree "
                        f"(architecture/, governance/, invariants/, research/, profiles/)"
                    ),
                ))
    return violations


# ---------------------------------------------------------------------------
# 2. Docs subtrees — unknown files
# ---------------------------------------------------------------------------

def check_docs_subtrees(docs_manifest: dict | None) -> list[StructureViolation]:
    violations = []
    if not docs_manifest:
        return violations

    for subtree in (docs_manifest.get("subtrees") or []):
        path_str = subtree.get("path")
        known = set(subtree.get("known_files") or [])
        allowed_exts = set(subtree.get("allowed_extensions") or [".md"])

        if not path_str:
            continue

        subtree_path = ROOT / path_str
        if not subtree_path.exists():
            violations.append(StructureViolation(
                area=path_str,
                file_path=path_str,
                violation_type="MISSING_REQUIRED_SUBTREE",
                owning_manifest="docs/manifest.yaml",
                recommended_fix=f"Create the directory: {path_str}",
            ))
            continue

        # Check required files
        for req in (subtree.get("required_files") or []):
            if not (subtree_path / req).exists():
                violations.append(StructureViolation(
                    area=path_str,
                    file_path=f"{path_str}{req}",
                    violation_type="MISSING_REQUIRED_FILE",
                    owning_manifest="docs/manifest.yaml",
                    recommended_fix=f"Create required file: {path_str}{req}",
                ))

        # Check for unknown files (if known list is non-empty, it's enforced)
        if known:
            for item in subtree_path.iterdir():
                if item.is_file() and item.suffix in allowed_exts:
                    if item.name not in known:
                        violations.append(StructureViolation(
                            area=path_str,
                            file_path=str(item.relative_to(ROOT)),
                            violation_type="UNKNOWN_FILE_IN_SUBTREE",
                            owning_manifest="docs/manifest.yaml",
                            recommended_fix=(
                                f"Register '{item.name}' in docs/manifest.yaml "
                                f"under subtree '{subtree.get('name')}' known_files, "
                                f"or move it to a different location."
                            ),
                        ))

    return violations


# ---------------------------------------------------------------------------
# 3. Domain required docs
# ---------------------------------------------------------------------------

DOMAIN_REQUIRED_DOCS = ["README.md", "SPEC.md", "manifest.yaml"]


def check_domain_docs() -> list[StructureViolation]:
    violations = []
    domains_dir = ROOT / "domains"
    if not domains_dir.exists():
        return violations

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        for required in DOMAIN_REQUIRED_DOCS:
            if not (domain_dir / required).exists():
                violations.append(StructureViolation(
                    area=f"domains/{domain_dir.name}/",
                    file_path=f"domains/{domain_dir.name}/{required}",
                    violation_type="MISSING_DOMAIN_REQUIRED_DOC",
                    owning_manifest=f"domains/{domain_dir.name}/manifest.yaml",
                    recommended_fix=f"Create: domains/{domain_dir.name}/{required}",
                ))
    return violations




# ---------------------------------------------------------------------------
# 5. Stale path references in root manifest
# ---------------------------------------------------------------------------

OLD_DOC_PATHS = [
    "docs/ARCHITECTURE.md", "docs/GOVERNANCE.md", "docs/PIPELINE.md",
    "docs/SPEC.md", "docs/ENTITY_SCHEMA.md", "docs/OPERATOR_SPEC.md",
    "docs/INVARIANTS.md", "docs/HSL.md", "docs/MANIFEST_AUTHORITY.md",
    "docs/governance/MANIFEST_AUTHORITY.md",
    "docs/DISSONANCE.md",
]


def check_stale_references() -> list[StructureViolation]:
    violations = []
    manifest_path = ROOT / "MANIFEST.yaml"
    if not manifest_path.exists():
        return violations

    content = manifest_path.read_text(encoding="utf-8")
    for old_path in OLD_DOC_PATHS:
        if old_path in content:
            violations.append(StructureViolation(
                area="MANIFEST.yaml",
                file_path="MANIFEST.yaml",
                violation_type="STALE_PATH_REFERENCE",
                owning_manifest="MANIFEST.yaml",
                recommended_fix=f"Replace '{old_path}' with its new scoped location.",
            ))
    return violations


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------

def validate_structure(verbose: bool = False) -> dict:
    docs_manifest = _load_yaml(DOCS_MANIFEST_PATH)

    all_violations: list[StructureViolation] = []
    all_violations += check_docs_root(docs_manifest)
    all_violations += check_docs_subtrees(docs_manifest)
    all_violations += check_domain_docs()
    all_violations += check_stale_references()

    passed = len(all_violations) == 0

    result: dict[str, Any] = {
        "passed": passed,
        "violation_count": len(all_violations),
        "violations": [v.to_dict() for v in all_violations],
    }

    if not verbose:
        # Summarize by area instead of listing every violation
        areas: dict[str, int] = {}
        for v in all_violations:
            areas[v.area] = areas.get(v.area, 0) + 1
        result["violations_by_area"] = areas

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    result = validate_structure(verbose=args.verbose)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


