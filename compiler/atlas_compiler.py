"""
Atlas Compiler — Helix Phase 7
==============================
Converts raw experimental artifacts into structured Atlas knowledge entries.

Flow:
    artifacts/<run>/  →  atlas_compiler  →  atlas/laws/<name>.md
                                         →  atlas/regimes/<name>.md
                                         →  atlas/audits/<name>.md
                                         →  atlas/index.md (updated)

Design rules:
  - Atlas entries must NEVER contain raw experiment data
  - Atlas entries must link to artifacts, not copy them
  - Atlas entries must remain short and structured
  - Atlas is the reasoning memory of Helix
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths (resolved relative to this file's location → project root)
# ---------------------------------------------------------------------------

REPO_ROOT     = Path(__file__).parent.parent
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
ATLAS_DIR     = REPO_ROOT / "atlas"
LAWS_DIR      = ATLAS_DIR / "laws"
REGIMES_DIR   = ATLAS_DIR / "regimes"
AUDITS_DIR    = ATLAS_DIR / "audits"
REPORTS_DIR   = ATLAS_DIR / "reports"
DATASETS_DIR  = ATLAS_DIR / "datasets"
INDEX_PATH    = ATLAS_DIR / "index.md"


# ---------------------------------------------------------------------------
# Entry template
# ---------------------------------------------------------------------------

LAW_TEMPLATE = """\
# Law: {name}

**Confidence:** {confidence}
**Last Updated:** {date}
**Source:** {source}

---

## Description

{description}

---

## Observed Conditions

{observed_conditions}

---

## Failure Conditions

{failure_conditions}

---

## Evidence

{evidence}

---

## Notes

{notes}
"""

REGIME_TEMPLATE = """\
# Regime: {name}

**Confidence:** {confidence}
**Last Updated:** {date}
**Source:** {source}

---

## Description

{description}

---

## Observed Conditions

{observed_conditions}

---

## Boundary Conditions

{failure_conditions}

---

## Evidence

{evidence}

---

## Notes

{notes}
"""


# ---------------------------------------------------------------------------
# Artifact discovery
# ---------------------------------------------------------------------------

def discover_artifacts() -> list[dict]:
    """
    Walk artifacts/ and collect all JSON result files.
    Returns a list of dicts with artifact metadata.
    """
    found = []
    for root, _dirs, files in os.walk(ARTIFACTS_DIR):
        for fname in files:
            if fname.endswith(".json") and not fname.startswith("_"):
                path = Path(root) / fname
                try:
                    with open(path) as f:
                        data = json.load(f)
                    found.append({
                        "path": path,
                        "rel_path": path.relative_to(REPO_ROOT),
                        "data": data,
                    })
                except (json.JSONDecodeError, OSError):
                    pass
    return found


def discover_atlas_json() -> list[dict]:
    """
    Collect existing top-level atlas JSON files (legacy format).
    These are authoritative and should be promoted to law entries.
    """
    found = []
    for path in ATLAS_DIR.glob("*.json"):
        if path.name == "index.json":
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            found.append({
                "path": path,
                "rel_path": path.relative_to(REPO_ROOT),
                "data": data,
            })
        except (json.JSONDecodeError, OSError):
            pass
    return found


# ---------------------------------------------------------------------------
# Pattern extraction
# ---------------------------------------------------------------------------

def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")


def _format_run_list(runs: list[dict]) -> str:
    lines = []
    for r in runs:
        run_id  = r.get("run_id", "unknown")
        domain  = r.get("domain", "?")
        passed  = r.get("passed", None)
        signal  = r.get("signal", None)
        status  = "PASS" if passed else "FAIL"
        sig_str = f", signal={signal:.4f}" if signal is not None else ""
        lines.append(f"- `{run_id}` ({domain}{sig_str}) [{status}]")
    return "\n".join(lines) if lines else "- None recorded"


def extract_from_invariant_json(artifact: dict) -> dict | None:
    """
    Extract a law entry from a Helix invariant JSON blob.
    Expected shape: {invariant, confidence, observed_in, supporting_runs,
                     pass_rate, mean_signal, run_count}
    """
    d = artifact["data"]
    if not isinstance(d, dict):
        return None  # raw arrays / lists are data, not knowledge
    invariant = d.get("invariant")
    if not invariant:
        return None

    confidence     = d.get("confidence", "experimental")
    observed_in    = d.get("observed_in", [])
    supporting     = d.get("supporting_runs", [])
    pass_rate      = d.get("pass_rate", None)
    mean_signal    = d.get("mean_signal", None)
    run_count      = d.get("run_count", len(supporting))

    observed_lines = []
    if observed_in:
        observed_lines.append(f"- Substrates: {', '.join(observed_in)}")
    if mean_signal is not None:
        observed_lines.append(f"- Mean signal: {mean_signal:.4f}")
    if pass_rate is not None:
        observed_lines.append(f"- Pass rate: {pass_rate:.1%} ({run_count} runs)")

    run_block = _format_run_list(supporting)
    evidence_lines = [
        f"- Source JSON: `{artifact['rel_path']}`",
        "",
        "Supporting runs:",
        run_block,
    ]

    return {
        "type":       "law",
        "name":       invariant.replace("_", " ").title(),
        "slug":       _slugify(invariant),
        "confidence": confidence,
        "description": (
            f"Structural invariant detected across substrates: "
            f"{', '.join(observed_in) or 'unknown'}.\n"
            f"Signal mean: {mean_signal:.4f}. "
            f"Pass rate: {pass_rate:.1%} across {run_count} runs."
            if mean_signal is not None else
            f"Structural invariant candidate observed in: {', '.join(observed_in) or 'unknown'}."
        ),
        "observed_conditions": "\n".join(observed_lines) if observed_lines else "- Not yet characterized",
        "failure_conditions":  "- Failure conditions not yet characterized — adversarial probes needed (Phase 11)",
        "evidence":            "\n".join(evidence_lines),
        "source":              str(artifact["rel_path"]),
        "notes":               f"Auto-compiled from `{artifact['rel_path']}` by atlas_compiler.",
    }


def extract_from_generic_json(artifact: dict) -> dict | None:
    """
    Try to extract any useful law/regime from a generic JSON artifact.
    Returns None if no meaningful pattern is detectable.
    """
    d = artifact["data"]
    if not isinstance(d, dict):
        return None  # raw arrays are data, not knowledge entries

    # Must have at least a result or signal field to be meaningful
    if not any(k in d for k in ("result", "signal", "regime", "pattern", "law", "findings")):
        return None

    name = artifact["path"].stem.replace("_", " ").title()
    slug = _slugify(artifact["path"].stem)
    confidence = d.get("confidence", "experimental")

    findings = d.get("findings") or d.get("result") or d.get("pattern") or {}
    desc = (
        json.dumps(findings, indent=2)[:500] + "..."
        if isinstance(findings, (dict, list))
        else str(findings)[:500]
    )

    return {
        "type":       "regime",
        "name":       name,
        "slug":       slug,
        "confidence": confidence,
        "description": f"Pattern extracted from artifact.\n\n```\n{desc}\n```",
        "observed_conditions": "- Conditions not yet characterized",
        "failure_conditions":  "- Failure conditions not yet characterized",
        "evidence":            f"- `{artifact['rel_path']}`",
        "source":              str(artifact["rel_path"]),
        "notes":               f"Auto-compiled from `{artifact['rel_path']}` by atlas_compiler.",
    }


# ---------------------------------------------------------------------------
# Entry generation
# ---------------------------------------------------------------------------

def entry_exists(entry: dict) -> bool:
    if entry["type"] == "law":
        return (LAWS_DIR / f"{entry['slug']}.md").exists()
    elif entry["type"] == "regime":
        return (REGIMES_DIR / f"{entry['slug']}.md").exists()
    return False


def write_entry(entry: dict, overwrite: bool = False) -> Path | None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    template = LAW_TEMPLATE if entry["type"] == "law" else REGIME_TEMPLATE
    target_dir = LAWS_DIR if entry["type"] == "law" else REGIMES_DIR
    out_path = target_dir / f"{entry['slug']}.md"

    if out_path.exists() and not overwrite:
        return None  # skip — don't overwrite human-edited entries

    content = template.format(
        name                = entry["name"],
        confidence          = entry["confidence"],
        date                = today,
        source              = entry["source"],
        description         = entry["description"],
        observed_conditions = entry["observed_conditions"],
        failure_conditions  = entry["failure_conditions"],
        evidence            = entry["evidence"],
        notes               = entry["notes"],
    )
    out_path.write_text(content)
    return out_path


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------

def collect_index_entries() -> dict[str, list[str]]:
    """
    Scan atlas subdirectories and collect entry names for the index.
    """
    sections: dict[str, list[str]] = {
        "Laws":     [],
        "Regimes":  [],
        "Audits":   [],
        "Reports":  [],
        "Datasets": [],
    }

    def _collect(directory: Path, section: str) -> None:
        if not directory.exists():
            return
        for p in sorted(directory.glob("*.md")):
            # Read the first heading to get the display name
            try:
                first_line = p.read_text().split("\n", 1)[0].lstrip("# ").strip()
                display = first_line if first_line else p.stem.replace("_", " ").title()
            except OSError:
                display = p.stem.replace("_", " ").title()
            rel = p.relative_to(ATLAS_DIR)
            sections[section].append(f"- [{display}]({rel})")

    _collect(LAWS_DIR,     "Laws")
    _collect(REGIMES_DIR,  "Regimes")
    _collect(AUDITS_DIR,   "Audits")
    _collect(REPORTS_DIR,  "Reports")
    _collect(DATASETS_DIR, "Datasets")
    return sections


def write_index(sections: dict[str, list[str]]) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Helix Atlas",
        "",
        f"*Generated by atlas_compiler on {today}*",
        "",
        "The Atlas is Helix's long-term reasoning memory.",
        "It contains only compressed, structured knowledge.",
        "Raw experiment data lives in `artifacts/`.",
        "",
        "---",
        "",
    ]
    for section, entries in sections.items():
        lines.append(f"## {section}")
        lines.append("")
        if entries:
            lines.extend(entries)
        else:
            lines.append("*No entries yet.*")
        lines.append("")

    lines += [
        "---",
        "",
        f"*Atlas last compiled: {today}*",
        "",
        "To add a new entry: run `python compiler/atlas_compiler.py` after",
        "placing experiment results in `artifacts/`.",
        "",
    ]

    INDEX_PATH.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(verbose: bool = True, overwrite: bool = False) -> dict[str, Any]:
    """
    Full Atlas compilation pipeline.
    Returns a summary dict of what was created/skipped.
    """
    stats = {"created": [], "skipped": [], "errors": []}
    log = print if verbose else (lambda *a, **k: None)

    log("=== Helix Atlas Compiler ===")
    log(f"Artifacts root: {ARTIFACTS_DIR}")
    log(f"Atlas root:     {ATLAS_DIR}")
    log("")

    # --- 1. Promote legacy atlas JSON files to law entries ---
    log("[1/4] Scanning legacy atlas JSON files...")
    for artifact in discover_atlas_json():
        try:
            entry = extract_from_invariant_json(artifact)
            if entry is None:
                continue
            if entry_exists(entry) and not overwrite:
                log(f"  SKIP (exists): {entry['slug']}")
                stats["skipped"].append(entry["slug"])
                continue
            out = write_entry(entry, overwrite=overwrite)
            if out:
                log(f"  WRITE: {out.relative_to(REPO_ROOT)}")
                stats["created"].append(str(out.relative_to(REPO_ROOT)))
        except Exception as e:
            log(f"  ERROR ({artifact['path'].name}): {e}")
            stats["errors"].append(str(artifact["path"]))

    # --- 2. Scan artifact directories for result JSON ---
    log("\n[2/4] Scanning artifacts/ for result files...")
    for artifact in discover_artifacts():
        try:
            # Try invariant format first, then generic
            entry = extract_from_invariant_json(artifact)
            if entry is None:
                entry = extract_from_generic_json(artifact)
            if entry is None:
                continue
            if entry_exists(entry) and not overwrite:
                stats["skipped"].append(entry["slug"])
                continue
            out = write_entry(entry, overwrite=overwrite)
            if out:
                log(f"  WRITE: {out.relative_to(REPO_ROOT)}")
                stats["created"].append(str(out.relative_to(REPO_ROOT)))
        except Exception as e:
            log(f"  ERROR ({artifact['path'].name}): {e}")
            stats["errors"].append(str(artifact["path"]))

    # --- 3. Collect index entries ---
    log("\n[3/4] Collecting atlas entries for index...")
    sections = collect_index_entries()
    for section, entries in sections.items():
        log(f"  {section}: {len(entries)} entries")

    # --- 4. Write index ---
    log("\n[4/4] Writing atlas/index.md...")
    write_index(sections)
    log(f"  WRITE: atlas/index.md")

    log("\n=== Compilation complete ===")
    log(f"  Created: {len(stats['created'])}")
    log(f"  Skipped: {len(stats['skipped'])}")
    log(f"  Errors:  {len(stats['errors'])}")
    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Helix Atlas Compiler")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing atlas entries (default: skip existing)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output",
    )
    args = parser.parse_args()
    run(verbose=not args.quiet, overwrite=args.overwrite)
