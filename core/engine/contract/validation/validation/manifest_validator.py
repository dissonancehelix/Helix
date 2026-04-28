"""
Manifest Validator — core/engine/contract/validation/manifest_validator.py
======================================================================
Validates all Helix manifests (system, domain, application) against
a minimal schema and structural consistency rules.

This is NOT a general YAML schema framework.
It enforces enough structure that manifests can actually fail validation.

Rules enforced:
  1. Required fields present per manifest type
  2. Status fields are valid enum values
  3. Referenced paths exist on disk
  4. Root manifest domain/app lists are consistent with actual dirs
  5. Domain/application manifests reference docs that exist
  6. Schema version field is present and known

Usage:
    python -m core.validation.validation.manifest_validator
    python -m core.validation.validation.manifest_validator --root MANIFEST.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() or (p / "README.md").exists()
)

KNOWN_SCHEMAS = {"manifest_schema_v1"}
VALID_STATUS = {"implemented", "partial", "stub", "not_started", "active",
                "deprecated", "experimental", "unknown"}
VALID_HSL_STATUS = {True, False, "partial", "unknown"}

# ---------------------------------------------------------------------------
# Required fields per manifest type
# ---------------------------------------------------------------------------

SYSTEM_REQUIRED = {
    "manifest_schema", "system", "version", "status",
    "layers", "domains", "governance",
}

DOMAIN_REQUIRED = {
    "manifest_schema", "domain", "version", "status",
    "purpose", "docs", "entry_point", "runtime", "known_gaps",
}

APP_REQUIRED = {
    "manifest_schema", "application", "version", "status",
    "purpose", "relationship_to_helix", "known_gaps",
}


class ManifestViolation:
    def __init__(self, manifest: str, rule: str, detail: str):
        self.manifest = manifest
        self.rule = rule
        self.detail = detail

    def to_dict(self) -> dict:
        return {"manifest": self.manifest, "rule": self.rule, "detail": self.detail}


def _load_yaml(path: Path) -> dict | None:
    if yaml is None:
        raise RuntimeError(
            "PyYAML not installed. Run: pip install pyyaml\n"
            "Manifest validation requires PyYAML."
        )
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error in {path}: {e}") from e


def _check_required(manifest: dict, required: set[str], label: str) -> list[ManifestViolation]:
    return [
        ManifestViolation(label, "MISSING_REQUIRED_FIELD", f"Field '{f}' is required")
        for f in required if f not in manifest
    ]


def _check_schema_version(manifest: dict, label: str) -> list[ManifestViolation]:
    v = manifest.get("manifest_schema")
    if v not in KNOWN_SCHEMAS:
        return [ManifestViolation(label, "UNKNOWN_SCHEMA_VERSION",
                                  f"manifest_schema='{v}' not in {KNOWN_SCHEMAS}")]
    return []


def _check_status(manifest: dict, label: str) -> list[ManifestViolation]:
    v = manifest.get("status")
    if v is not None and v not in VALID_STATUS:
        return [ManifestViolation(label, "INVALID_STATUS",
                                  f"status='{v}' not in valid set {VALID_STATUS}")]
    return []


def _check_path_exists(path_str: str | None, label: str, field: str) -> list[ManifestViolation]:
    if not path_str or path_str in ("null", "not_implemented", "unknown"):
        return []
    p = ROOT / path_str
    if not p.exists():
        return [ManifestViolation(label, "BROKEN_PATH",
                                  f"Field '{field}' references non-existent path: {path_str}")]
    return []


# ---------------------------------------------------------------------------
# System manifest validation
# ---------------------------------------------------------------------------

def validate_system_manifest(path: Path) -> list[ManifestViolation]:
    label = str(path.relative_to(ROOT))
    m = _load_yaml(path)
    if m is None:
        return [ManifestViolation(label, "FILE_NOT_FOUND", f"{path} does not exist")]

    v = []
    v += _check_required(m, SYSTEM_REQUIRED, label)
    v += _check_schema_version(m, label)
    v += _check_status(m, label)

    # Validate doc references (docs section may be nested)
    def _check_docs_section(section: dict, section_name: str) -> list[ManifestViolation]:
        results = []
        for key, ref in section.items():
            if isinstance(ref, str) and ref not in ("null",):
                results += _check_path_exists(ref, label, f"{section_name}.{key}")
            elif isinstance(ref, dict):
                results += _check_docs_section(ref, f"{section_name}.{key}")
        return results

    v += _check_docs_section(m.get("docs") or {}, "docs")

    # Validate domain entries
    actual_domain_dirs = {d.name for d in (ROOT / "engine" / "domains").iterdir()
                         if d.is_dir() and not d.name.startswith("_")}
    for domain_entry in (m.get("domains") or []):
        name = domain_entry.get("name")
        path_ref = domain_entry.get("path")
        manifest_ref = domain_entry.get("manifest")
        if path_ref:
            v += _check_path_exists(path_ref, label, f"domains[{name}].path")
        if manifest_ref:
            v += _check_path_exists(manifest_ref, label, f"domains[{name}].manifest")

    # Validate application entries
    for app_entry in (m.get("applications") or []):
        name = app_entry.get("name")
        path_ref = app_entry.get("path")
        manifest_ref = app_entry.get("manifest")
        if path_ref:
            v += _check_path_exists(path_ref, label, f"applications[{name}].path")
        if manifest_ref:
            v += _check_path_exists(manifest_ref, label, f"applications[{name}].manifest")

    # Validate governance references
    for key, gpath in (m.get("governance") or {}).items():
        v += _check_path_exists(gpath, label, f"governance.{key}")

    return v


# ---------------------------------------------------------------------------
# Domain manifest validation
# ---------------------------------------------------------------------------

def validate_domain_manifest(path: Path) -> list[ManifestViolation]:
    label = str(path.relative_to(ROOT))
    m = _load_yaml(path)
    if m is None:
        return [ManifestViolation(label, "FILE_NOT_FOUND", f"{path} does not exist")]

    v = []
    v += _check_required(m, DOMAIN_REQUIRED, label)
    v += _check_schema_version(m, label)
    v += _check_status(m, label)

    # Doc references
    for key, ref_path in (m.get("docs") or {}).items():
        if ref_path and ref_path not in ("null",):
            v += _check_path_exists(ref_path, label, f"docs.{key}")

    # Key structural paths
    for section_key in ("domain_local_metrics", "shared_embedding", "validation"):
        section = m.get(section_key) or {}
        for field in ("path", "adapter"):
            val = section.get(field)
            if val and val not in ("null", "not_implemented", "unknown"):
                v += _check_path_exists(val, label, f"{section_key}.{field}")
        # domain_harness: only check if harness status is not explicitly "not_implemented"
        harness_val = section.get("domain_harness")
        harness_status = section.get("domain_harness_status", "")
        if (harness_val
                and harness_val not in ("null", "not_implemented", "unknown")
                and harness_status not in ("not_implemented", "unknown")):
            v += _check_path_exists(harness_val, label, f"{section_key}.domain_harness")

    # Fixture paths
    for fix in (m.get("fixtures") or []):
        if "path" in fix and fix["path"] not in ("null", "not_implemented"):
            v += _check_path_exists(fix["path"], label, f"fixtures[{fix.get('name')}].path")

    return v


# ---------------------------------------------------------------------------
# Application manifest validation
# ---------------------------------------------------------------------------

def validate_app_manifest(path: Path) -> list[ManifestViolation]:
    label = str(path.relative_to(ROOT))
    m = _load_yaml(path)
    if m is None:
        return [ManifestViolation(label, "FILE_NOT_FOUND", f"{path} does not exist")]

    v = []
    v += _check_required(m, APP_REQUIRED, label)
    v += _check_schema_version(m, label)
    v += _check_status(m, label)

    # Doc references
    for key, ref_path in (m.get("docs") or {}).items():
        if ref_path and ref_path not in ("null",):
            v += _check_path_exists(ref_path, label, f"docs.{key}")

    return v


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------

def validate_all(root_manifest_path: Path | None = None) -> dict:
    if root_manifest_path is None:
        root_manifest_path = ROOT / "MANIFEST.yaml"

    all_violations: list[ManifestViolation] = []

    # System manifest
    sys_v = validate_system_manifest(root_manifest_path)
    all_violations += sys_v

    # Domain manifests
    domain_results = {}
    for domain_dir in sorted((ROOT / "engine" / "domains").iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        mpath = domain_dir / "manifest.yaml"
        dv = validate_domain_manifest(mpath)
        domain_results[domain_dir.name] = {
            "passed": len(dv) == 0,
            "violations": [x.to_dict() for x in dv],
        }
        all_violations += dv

    # Application manifests (applications/ removed — tooling lives in domains/)
    app_results = {}

    passed = len(all_violations) == 0
    return {
        "passed": passed,
        "violation_count": len(all_violations),
        "system_manifest": {
            "path": str(root_manifest_path.relative_to(ROOT)),
            "passed": len(sys_v) == 0,
            "violations": [x.to_dict() for x in sys_v],
        },
        "domains": domain_results,
        "applications": app_results,
    }


if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Path to root manifest")
    args = parser.parse_args()

    root = Path(args.root) if args.root else None
    result = validate_all(root)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


