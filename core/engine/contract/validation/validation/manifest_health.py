"""
Manifest Health / Introspection — core/engine/contract/validation/manifest_health.py
================================================================================
Lightweight health check for the Helix manifest system.

Reads the root manifest, enumerates all referenced domains and applications,
verifies their manifests exist and parse, and summarizes structural health.

Does NOT replace the manifest validator. This is a quick smoke-check:
  - Are all referenced manifests present?
  - Are all domain/app directories represented?
  - Are there unregistered dirs that should have manifests?
  - What is the aggregate runtime maturity?

Usage:
    python -m core.validation.validation.manifest_health
    python -m core.validation.validation.manifest_health --verbose
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
SYSTEM_MANIFEST_PATH = ROOT / "MANIFEST.yaml"


def _load_yaml(path: Path) -> dict | None:
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None


def _check_manifest(path: Path) -> dict[str, Any]:
    m = _load_yaml(path)
    if m is None:
        return {"exists": False, "parseable": False, "status": "MISSING", "data": None}
    return {"exists": True, "parseable": True, "status": m.get("status", "unknown"), "data": m}


def run_health_check(verbose: bool = False) -> dict:
    root_m = _load_yaml(SYSTEM_MANIFEST_PATH)
    if root_m is None:
        return {
            "healthy": False,
            "fatal": f"Root manifest not found or unparseable: {SYSTEM_MANIFEST_PATH}",
        }

    system_ok = True
    issues = []
    summary = {
        "system": root_m.get("system"),
        "version": root_m.get("version"),
        "status": root_m.get("status"),
    }

    # --- Domains ---
    registered_domains = {d["name"]: d for d in (root_m.get("domains") or [])}
    actual_domain_dirs = {
        d.name for d in (ROOT / "domains").iterdir()
        if d.is_dir() and not d.name.startswith("_")
    }

    domain_health = {}
    for name, entry in registered_domains.items():
        manifest_ref = entry.get("manifest")
        mpath = ROOT / manifest_ref if manifest_ref else None
        check = _check_manifest(mpath) if mpath else {"exists": False, "parseable": False, "status": "NO_PATH"}
        runtime = (check["data"] or {}).get("runtime", {})
        pipeline_status = runtime.get("pipeline_status", "unknown") if isinstance(runtime, dict) else "unknown"
        domain_health[name] = {
            "manifest_path": manifest_ref,
            "manifest_exists": check["exists"],
            "status": check["status"],
            "pipeline_status": pipeline_status,
        }
        if not check["exists"]:
            issues.append(f"DOMAIN [{name}] manifest missing: {manifest_ref}")
            system_ok = False

    unregistered_domains = actual_domain_dirs - set(registered_domains.keys())
    for name in sorted(unregistered_domains):
        issues.append(f"DOMAIN [{name}] directory exists but is NOT registered in system manifest")
        domain_health[name] = {"manifest_path": None, "manifest_exists": False,
                               "status": "UNREGISTERED", "pipeline_status": "unknown"}

    # Applications folder removed — tooling lives in domains/
    app_health: dict = {}

    # --- Governance references ---
    gov = root_m.get("governance") or {}
    gov_health = {}
    for key, path_str in gov.items():
        exists = (ROOT / path_str).exists() if path_str else False
        gov_health[key] = {"path": path_str, "exists": exists}
        if not exists:
            issues.append(f"GOVERNANCE [{key}] path broken: {path_str}")
            system_ok = False

    # --- Known gaps summary ---
    known_gaps = root_m.get("known_gaps") or []

    result = {
        "healthy": system_ok and len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
        "summary": summary,
        "domains": domain_health,
        "applications": app_health,
        "governance_references": gov_health,
        "known_gaps_count": len(known_gaps),
    }

    if verbose:
        result["known_gaps"] = known_gaps

    return result


if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Include known_gaps in output")
    args = parser.parse_args()

    result = run_health_check(verbose=args.verbose)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["healthy"] else 1)


