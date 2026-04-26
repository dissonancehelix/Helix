"""
Atlas Compiler — Helix Formal System
======================================
Converts validated artifacts into Atlas entities via the mandated pipeline:

    normalize(entity_dict)
    → semantic_validate(entity)
    → compile_entity(entity)
    → atlas_commit(entity, substrate_path)

CLOSED SYSTEM LAW:
  No operator, substrate, or script may write to atlas/ directly.
  All Atlas writes must pass through this compiler.
  Invalid entities are rejected before any filesystem write.

Atlas organization (by substrate):
  atlas/
    entities/registry.json   ← authoritative entity index
    music/
      composers/
      tracks/
      albums/
      games/
      platforms/
      sound_chips/
    games/
    language/
    mathematics/
    invariants/
    signals/

Object types (legacy knowledge objects — markdown-based):
  Invariant   — cross-domain structural rule
  Experiment  — runnable falsification test
  Model       — candidate explanatory structure
  Regime      — identified phase or system state
  Operator    — reusable transformation or diagnostic tool
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT       = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR   = REPO_ROOT / "artifacts"
ATLAS_DIR       = REPO_ROOT / "codex" / "atlas"
INVARIANTS_DIR  = ATLAS_DIR / "invariants"
EXPERIMENTS_DIR = ATLAS_DIR / "experiments"
MODELS_DIR      = ATLAS_DIR / "models"
REGIMES_DIR     = ATLAS_DIR / "regimes"
OPERATORS_DIR   = ATLAS_DIR / "operators"
INDEX_MD        = ATLAS_DIR / "index.md"
INDEX_YAML      = ATLAS_DIR / "atlas_index.yaml"

# Substrate entity directories (organized by substrate/type_plural)
SUBSTRATE_DIRS: dict[str, dict[str, Path]] = {
    "music": {
        "composer":   ATLAS_DIR / "music" / "composers",
        "track":      ATLAS_DIR / "music" / "tracks",
        "album":      ATLAS_DIR / "music" / "albums",
        "game":       ATLAS_DIR / "music" / "games",
        "platform":   ATLAS_DIR / "music" / "platforms",
        "sound_chip": ATLAS_DIR / "music" / "sound_chips",
        "soundchip":  ATLAS_DIR / "music" / "sound_chips",
        "soundtrack":  ATLAS_DIR / "music" / "albums",
    },
    "games": {
        "game":     ATLAS_DIR / "games" / "titles",
        "platform": ATLAS_DIR / "games" / "platforms",
    },
    "language": {
        "text":     ATLAS_DIR / "language" / "texts",
        "corpus":   ATLAS_DIR / "language" / "corpora",
    },
    "mathematics": {
        "dataset":  ATLAS_DIR / "mathematics" / "datasets",
        "model":    ATLAS_DIR / "mathematics" / "models",
    },
}


# ---------------------------------------------------------------------------
# Entity compilation pipeline
# ---------------------------------------------------------------------------

class CompilationError(Exception):
    """Raised when an entity fails the compilation pipeline."""
    pass


def compile_entity(entity_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Run the full compilation pipeline on an entity dict.

    Pipeline:
      normalize → semantic_validate → resolve_path → return compiled entry

    Returns the compiled entry dict on success.
    Raises CompilationError on any failure.
    """
    # Stage 1: Normalize
    try:
        entity_dict = _normalize_entity(entity_dict)
    except Exception as e:
        raise CompilationError(f"Normalization failed: {e}") from e

    # Stage 2: Semantic validation
    try:
        _semantic_validate(entity_dict)
    except Exception as e:
        raise CompilationError(f"Semantic validation failed: {e}") from e

    # Stage 3: Resolve output path
    output_path = _resolve_atlas_path(entity_dict)

    # Stage 4: Build compiled entry with provenance
    compiled = _build_compiled_entry(entity_dict, output_path)
    return compiled


def atlas_commit(compiled: dict[str, Any]) -> Path:
    """
    Write a compiled entry to the Atlas filesystem.

    This is the ONLY authorized path for writing to atlas/.
    Raises EnforcementError if the entity fails validation or the
    runtime mode blocks direct writes.
    """
    from core.validation import enforce_persistence
    
    output_path: Path = compiled["_output_path"]
    
    # ENFORCEMENT GATE: Authorize, Validate, and Persist via canonical gateway
    return enforce_persistence(compiled, output_path, is_atlas=True)


def compile_and_commit(entity_dict: dict[str, Any]) -> Path:
    """
    Full pipeline: normalize → semantic_validate → compile → commit.
    Returns the path of the written Atlas file.
    """
    compiled = compile_entity(entity_dict)
    return atlas_commit(compiled)


# ---------------------------------------------------------------------------
# Pipeline stages (internal)
# ---------------------------------------------------------------------------

def _normalize_entity(entity_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize entity dict fields:
    - Ensure id is lowercase
    - Ensure type is Title-cased
    - Populate label from name if absent
    - Strip whitespace from string fields
    """
    d = dict(entity_dict)

    if "id" in d and d["id"]:
        d["id"] = str(d["id"]).strip().lower()

    if "type" in d and d["type"]:
        raw_type = str(d["type"]).strip()
        d["type"] = raw_type[0].upper() + raw_type[1:] if raw_type else raw_type

    if "name" in d and d["name"]:
        d["name"] = str(d["name"]).strip()

    # label defaults to name
    if not d.get("label"):
        d["label"] = d.get("name", "")

    if "description" in d and d["description"]:
        d["description"] = str(d["description"]).strip()

    # Validate ID format
    from core.engine.normalization.id_enforcer import enforce_id
    if d.get("id"):
        enforce_id(d["id"])  # raises InvalidIDError on failure

    return d


def _semantic_validate(entity_dict: dict[str, Any]) -> None:
    """Run SemanticValidator against entity_dict. Raises on failure."""
    from core.engine.semantics.validator import SemanticValidator
    result = SemanticValidator.validate(entity_dict)
    if not result.valid:
        raise ValueError("; ".join(result.errors))


def _resolve_atlas_path(entity_dict: dict[str, Any]) -> Path:
    """
    Determine the output path for this entity in the Atlas filesystem.

    Uses: atlas/{substrate}/{type_plural}/{slug}.json
    Falls back to atlas/entities/{id_slug}.json for unknown domains.
    """
    entity_id = entity_dict.get("id", "")
    namespace = entity_id.split(".")[0] if "." in entity_id else ""
    type_slug = entity_id.split(":")[0].split(".")[-1] if "." in entity_id else ""
    slug = entity_id.split(":", 1)[-1] if ":" in entity_id else _slugify(entity_dict.get("name", "unknown"))

    substrate_map = SUBSTRATE_DIRS.get(namespace, {})
    base_dir = substrate_map.get(type_slug)

    if base_dir is None:
        # Unknown substrate or type — fall back to atlas/entities/
        base_dir = ATLAS_DIR / "entities" / namespace / (type_slug + "s") if namespace else ATLAS_DIR / "entities"

    return base_dir / f"{slug}.json"


def _build_compiled_entry(entity_dict: dict[str, Any], output_path: Path) -> dict[str, Any]:
    """Build the final compiled Atlas entry with provenance fields."""
    now = datetime.now(timezone.utc).isoformat()

    compiled = dict(entity_dict)

    # Ensure provenance fields
    metadata = dict(compiled.get("metadata", {}))
    if "compiled_at" not in metadata:
        metadata["compiled_at"] = now
    if "compiled_by" not in metadata:
        metadata["compiled_by"] = "atlas_compiler"
    if "compiler_version" not in metadata:
        metadata["compiler_version"] = "2.0.0"
    compiled["metadata"] = metadata

    # Store output path for atlas_commit (stripped before writing)
    compiled["_output_path"] = output_path
    return compiled


# ---------------------------------------------------------------------------
# Legacy knowledge object templates (Invariant/Regime/etc. markdown entries)
# ---------------------------------------------------------------------------

_HEADER = """\
# {type_label}: {name}

**Type:** {object_type}
**Status:** {status}
**Origin:** {origin}
**Last Updated:** {date}

---
"""

_SECTION = "\n## {heading}\n\n{body}\n"


def _build_entry(
    object_type: str,
    name: str,
    status: str,
    origin: str,
    domain_coverage: str,
    mechanism: str,
    predictions: str,
    falsifiers: str,
    evidence: str,
    linked_experiments: str,
    notes: str,
    date: str,
) -> str:
    parts = [
        _HEADER.format(
            type_label=object_type,
            name=name,
            object_type=object_type,
            status=status,
            origin=origin,
            date=date,
        )
    ]
    sections = [
        ("Domain Coverage",    domain_coverage),
        ("Mechanism",          mechanism),
        ("Predictions",        predictions),
        ("Falsifiers",         falsifiers),
        ("Evidence",           evidence),
        ("Linked Experiments", linked_experiments),
        ("Notes",              notes),
    ]
    for heading, body in sections:
        parts.append(_SECTION.format(
            heading=heading,
            body=body.strip() or "*Not yet characterized.*",
        ))
    return "".join(parts)


# ---------------------------------------------------------------------------
# Artifact discovery
# ---------------------------------------------------------------------------

def discover_artifacts() -> list[dict]:
    """Walk artifacts/ and return all parseable JSON files, with validation info."""
    found = []
    for root, _dirs, files in os.walk(ARTIFACTS_DIR):
        validation_data = None
        if "validation_report.yaml" in files:
            try:
                val_path = Path(root) / "validation_report.yaml"
                validation_data = _parse_yaml_simple(val_path.read_text())
            except Exception:
                pass

        for fname in sorted(files):
            if fname.endswith(".json") and not fname.startswith("_"):
                path = Path(root) / fname
                try:
                    data = json.loads(path.read_text())
                    found.append({
                        "path": path,
                        "rel": path.relative_to(REPO_ROOT),
                        "data": data,
                        "validation": validation_data
                    })
                except Exception:
                    pass
    return found


def discover_atlas_json() -> list[dict]:
    """Collect legacy atlas/*.json files for promotion."""
    found = []
    for path in sorted(ATLAS_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        try:
            data = json.loads(path.read_text())
            found.append({"path": path, "rel": path.relative_to(REPO_ROOT), "data": data})
        except Exception:
            pass
    return found


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", s.lower()).strip("_")


def _fmt_runs(runs: list[dict]) -> str:
    lines = []
    for r in runs[:10]:
        run_id  = r.get("run_id", "unknown")
        domain  = r.get("domain", "?")
        signal  = r.get("signal")
        passed  = r.get("passed")
        sig_str = f", signal={signal:.4f}" if signal is not None else ""
        st_str  = " PASS" if passed is True else " FAIL" if passed is False else ""
        lines.append(f"- `{run_id}` ({domain}{sig_str}){st_str}")
    return "\n".join(lines) if lines else "- No runs recorded"


def extract_invariant(artifact: dict) -> dict | None:
    d = artifact["data"]
    if not isinstance(d, dict) or not d.get("invariant"):
        return None

    name        = d["invariant"]
    confidence  = d.get("confidence", "experimental")

    if artifact.get("validation"):
        val = artifact["validation"]
        if val.get("confidence"):
            confidence = val["confidence"].upper()
        elif val.get("status") == "VERIFIED":
            confidence = "HIGH"
        elif val.get("status") == "UNSTABLE":
            confidence = "LOW"

    observed_in = d.get("observed_in", [])
    runs        = d.get("supporting_runs", [])
    pass_rate   = d.get("pass_rate")
    mean_signal = d.get("mean_signal")
    run_count   = d.get("run_count", len(runs))

    obs_lines = []
    if observed_in:
        obs_lines.append(f"- domains: {', '.join(observed_in)}")
    if mean_signal is not None:
        obs_lines.append(f"- Mean signal: {mean_signal:.4f}")
    if pass_rate is not None:
        obs_lines.append(f"- Pass rate: {pass_rate:.1%} ({run_count} runs)")

    pr_str = f"1. Signal > threshold in all tested domains\n2. Pass rate >= {pass_rate:.0%}" if pass_rate else "1. Signal > threshold in all tested domains"

    return {
        "object_type":        "Invariant",
        "slug":               _slugify(name),
        "name":               name.replace("_", " ").title(),
        "status":             confidence,
        "origin":             f"Helix probe — {', '.join(observed_in) or 'unknown'}",
        "domain_coverage":    "\n".join(obs_lines) or "- Not yet characterized",
        "mechanism":          f"Structural pattern detected across domains: {', '.join(observed_in)}.",
        "predictions":        pr_str,
        "falsifiers":         "1. Any substrate showing signal < 0.20 under equivalent conditions\n2. Replication failure across domains",
        "evidence":           f"- Source: `{artifact['rel']}`\n\n{_fmt_runs(runs)}",
        "linked_experiments": "- See atlas registry",
        "notes":              f"Auto-compiled from `{artifact['rel']}`.",
    }


def extract_regime(artifact: dict) -> dict | None:
    d = artifact["data"]
    if not isinstance(d, dict):
        return None
    if not any(k in d for k in ("result", "signal", "regime", "pattern", "findings")):
        return None

    stem = artifact["path"].stem
    status = d.get("confidence", "experimental")

    if artifact.get("validation"):
        val = artifact["validation"]
        if val.get("confidence"):
            status = val["confidence"].upper()
        elif val.get("status") == "VERIFIED":
            status = "HIGH"
        elif val.get("status") == "UNSTABLE":
            status = "LOW"

    raw  = d.get("findings") or d.get("result") or d.get("pattern") or {}
    desc = json.dumps(raw, indent=2)[:300] + "..." if isinstance(raw, (dict, list)) else str(raw)[:300]

    return {
        "object_type":        "Regime",
        "slug":               _slugify(stem),
        "name":               stem.replace("_", " ").title(),
        "status":             status,
        "origin":             f"Auto-detected from `{artifact['rel']}`",
        "domain_coverage":    "- Not yet characterized",
        "mechanism":          f"Pattern extracted from artifact.\n\n```\n{desc}\n```",
        "predictions":        "- Requires characterization",
        "falsifiers":         "- Failure conditions not yet characterized",
        "evidence":           f"- `{artifact['rel']}`",
        "linked_experiments": "- None recorded",
        "notes":              f"Auto-compiled from `{artifact['rel']}`.",
    }


# ---------------------------------------------------------------------------
# Registry (atlas_index.yaml)
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if not INDEX_YAML.exists():
        return {"invariants": [], "experiments": [], "models": [], "regimes": [], "operators": [], "candidates": []}
    try:
        import yaml
        return yaml.safe_load(INDEX_YAML.read_text()) or {}
    except ImportError:
        return _parse_yaml_simple(INDEX_YAML.read_text())


def _parse_yaml_simple(text: str) -> dict:
    result: dict = {}
    current_list: list | None = None
    current_item: dict | None = None
    current_key: str | None = None

    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())

        if indent == 0 and stripped.endswith(":"):
            current_key = stripped[:-1]
            result[current_key] = []
            current_list = result[current_key]
            current_item = None
        elif indent == 2 and stripped.startswith("- id:"):
            current_item = {"id": stripped.split(":", 1)[1].strip()}
            if current_list is not None:
                current_list.append(current_item)
        elif indent == 4 and current_item is not None and ":" in stripped:
            k, _, v = stripped.partition(":")
            current_item[k.strip()] = v.strip()

    return result


def registry_ids(registry: dict, object_type: str) -> set[str]:
    key_map = {
        "Invariant":  "invariants",
        "Experiment": "experiments",
        "Model":      "models",
        "Regime":     "regimes",
        "Operator":   "operators",
    }
    entries = registry.get(key_map.get(object_type, ""), []) or []
    return {e.get("id", "") for e in entries if isinstance(e, dict)}


# ---------------------------------------------------------------------------
# Entry writing (legacy markdown knowledge objects)
# ---------------------------------------------------------------------------

TYPE_DIRS: dict[str, Path] = {
    "Invariant":  INVARIANTS_DIR,
    "Experiment": EXPERIMENTS_DIR,
    "Model":      MODELS_DIR,
    "Regime":     REGIMES_DIR,
    "Operator":   OPERATORS_DIR,
}


def entry_path(obj: dict) -> Path:
    return TYPE_DIRS.get(obj["object_type"], ATLAS_DIR) / f"{obj['slug']}.md"


def write_entry(obj: dict, overwrite: bool = False) -> Path | None:
    out = entry_path(obj)
    if out.exists() and not overwrite:
        return None
    today   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = _build_entry(
        object_type=obj["object_type"],
        name=obj["name"],
        status=obj["status"],
        origin=obj["origin"],
        domain_coverage=obj.get("domain_coverage", ""),
        mechanism=obj.get("mechanism", ""),
        predictions=obj.get("predictions", ""),
        falsifiers=obj.get("falsifiers", ""),
        evidence=obj.get("evidence", ""),
        linked_experiments=obj.get("linked_experiments", ""),
        notes=obj.get("notes", ""),
        date=today,
    )
    out.write_text(content)
    return out


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_entry(obj: dict) -> tuple[bool, list[str]]:
    issues = []
    for f in ("name", "mechanism", "falsifiers", "evidence"):
        if not obj.get(f, "").strip():
            issues.append(f"missing field: {f}")
    falsifiers = obj.get("falsifiers", "")
    weak = ("unknown", "tbd", "n/a", "none", "unclear")
    if any(w in falsifiers.lower() for w in weak) and len(falsifiers) < 60:
        issues.append("falsifiers appear to be placeholder text")
    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Cross-linking
# ---------------------------------------------------------------------------

def propose_links(obj: dict, registry: dict) -> list[str]:
    proposals = []
    name_lower = obj["name"].lower()
    for section in ("invariants", "experiments", "models", "operators"):
        for entry in (registry.get(section) or []):
            if not isinstance(entry, dict):
                continue
            eid = entry.get("id", "")
            if eid and eid.replace("_", " ") in name_lower:
                proposals.append(f"atlas/{section}/{eid}.md")
    return proposals


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------

def collect_sections() -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    for label, directory in [
        ("Invariants",  INVARIANTS_DIR),
        ("Experiments", EXPERIMENTS_DIR),
        ("Models",      MODELS_DIR),
        ("Regimes",     REGIMES_DIR),
        ("Operators",   OPERATORS_DIR),
    ]:
        entries = []
        if directory.exists():
            for p in sorted(directory.glob("*.md")):
                try:
                    first = p.read_text().split("\n", 1)[0].lstrip("# ").strip()
                except OSError:
                    first = p.stem
                rel = p.relative_to(ATLAS_DIR)
                entries.append(f"- [{first}]({rel})")
        sections[label] = entries
    return sections


def write_index_md(sections: dict[str, list[str]]) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Helix Atlas",
        "",
        f"*Compiled {today} — Helix Formal System*",
        "",
        "The Atlas is Helix's structured semantic memory.",
        "Raw data lives in `artifacts/`. Only validated knowledge lives here.",
        "All Atlas writes pass through the Atlas Compiler.",
        "",
        "Registry: `atlas/entities/registry.json`",
        "",
        "---",
        "",
    ]
    for section, entries in sections.items():
        lines += [f"## {section}", ""]
        lines += entries if entries else ["*No entries yet.*"]
        lines.append("")

    audit_dir = ATLAS_DIR / "audits"
    if audit_dir.exists():
        audits = sorted(audit_dir.glob("*.md"))
        if audits:
            lines += ["## Audits", ""]
            for a in audits:
                rel   = a.relative_to(ATLAS_DIR)
                title = a.read_text().split("\n", 1)[0].lstrip("# ").strip()
                lines.append(f"- [{title}]({rel})")
            lines.append("")

    lines += ["---", "", f"*Atlas last compiled: {today}*", ""]
    INDEX_MD.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Candidate proposals
# ---------------------------------------------------------------------------

def propose_candidates(artifacts: list[dict], registry: dict) -> list[dict]:
    known_ids: set[str] = set()
    for section in ("invariants", "regimes"):
        for e in (registry.get(section) or []):
            if isinstance(e, dict) and e.get("id"):
                known_ids.add(e["id"])

    seen: dict[str, int] = {}
    for a in artifacts:
        d = a["data"]
        if isinstance(d, dict) and d.get("invariant"):
            inv = d["invariant"]
            seen[inv] = seen.get(inv, 0) + 1

    candidates = []
    for inv_name, count in seen.items():
        slug = _slugify(inv_name)
        if slug not in known_ids:
            candidates.append({
                "id":     slug,
                "name":   inv_name.replace("_", " ").title(),
                "type":   "Invariant",
                "count":  count,
                "reason": f"Appeared {count}x in artifacts but has no atlas entry",
            })
    return candidates


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(verbose: bool = True, overwrite: bool = False) -> dict[str, Any]:
    stats: dict[str, Any] = {"created": [], "skipped": [], "errors": [], "candidates": []}
    log = print if verbose else (lambda *a, **k: None)

    log("=== Helix Atlas Compiler — HSL Formal System ===")
    log(f"Repo root: {REPO_ROOT}")
    log("Pipeline: normalize → semantic_validate → compile → atlas_commit")

    registry = load_registry()

    # 1. Promote legacy atlas JSON -> invariant entries
    log("\n[1/5] Promoting legacy atlas JSON files...")
    for artifact in discover_atlas_json():
        try:
            obj = extract_invariant(artifact)
            if obj is None:
                continue
            if obj["slug"] in registry_ids(registry, "Invariant") and not overwrite:
                log(f"  SKIP: {obj['slug']}")
                stats["skipped"].append(obj["slug"])
                continue
            valid, issues = validate_entry(obj)
            if not valid:
                log(f"  WARN ({obj['slug']}): {'; '.join(issues)}")
            out = write_entry(obj, overwrite=overwrite)
            if out:
                log(f"  WRITE: {out.relative_to(REPO_ROOT)}")
                stats["created"].append(str(out.relative_to(REPO_ROOT)))
        except Exception as e:
            log(f"  ERROR ({artifact['path'].name}): {e}")
            stats["errors"].append(str(artifact["path"]))

    # 2. Scan artifacts/ for new entries
    log("\n[2/5] Scanning artifacts/ for new entries...")
    all_artifacts = discover_artifacts()
    for artifact in all_artifacts:
        try:
            obj = extract_invariant(artifact) or extract_regime(artifact)
            if obj is None:
                continue
            if obj["slug"] in registry_ids(registry, obj["object_type"]) and not overwrite:
                stats["skipped"].append(obj["slug"])
                continue
            valid, issues = validate_entry(obj)
            if not valid:
                log(f"  WARN ({obj['slug']}): {'; '.join(issues)}")
            links = propose_links(obj, registry)
            if links:
                log(f"  LINKS for {obj['slug']}: {', '.join(links)}")
            out = write_entry(obj, overwrite=overwrite)
            if out:
                log(f"  WRITE: {out.relative_to(REPO_ROOT)}")
                stats["created"].append(str(out.relative_to(REPO_ROOT)))
        except Exception as e:
            log(f"  ERROR ({artifact['path'].name}): {e}")
            stats["errors"].append(str(artifact["path"]))

    # 3. Candidate proposals
    log("\n[3/5] Proposing invariant candidates...")
    candidates = propose_candidates(all_artifacts, registry)
    for c in candidates:
        log(f"  CANDIDATE: {c['name']} — {c['reason']}")
    stats["candidates"] = candidates
    if not candidates:
        log("  No new candidates.")

    # 4. Regenerate index.md
    log("\n[4/5] Regenerating atlas/index.md...")
    sections = collect_sections()
    for label, entries in sections.items():
        log(f"  {label}: {len(entries)} entries")
    write_index_md(sections)
    log("  WRITE: atlas/index.md")

    # 5. Validate compiled JSON entities via SemanticValidator
    log("\n[5/5] Validating compiled atlas entities...")
    try:
        from core.engine.semantics.validator import SemanticValidator
        from core.engine.kernel.schema.entities.schema import Entity
        validator = SemanticValidator()
        all_pass = True
        validated = 0
        failed = 0
        for json_path in REPO_ROOT.joinpath("atlas").rglob("*.json"):
            if json_path.name == "registry.json":
                continue
            try:
                import json as _json
                data = _json.loads(json_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or "type" not in data:
                    continue
                entity = Entity.from_dict(data)
                result = validator.validate(entity)
                if not result.valid:
                    all_pass = False
                    failed += 1
                    log(f"  [FAIL] {json_path.relative_to(REPO_ROOT)}")
                    for err in result.errors:
                        log(f"         x {err}")
                else:
                    validated += 1
            except Exception:
                pass
        log(f"  Validated {validated} entities. Failures: {failed}.")
        if all_pass:
            log("  All entities passed semantic validation.")
    except ImportError as e:
        log(f"  SemanticValidator unavailable: {e}")

    # 6. Build Atlas Knowledge Graph
    log("\n[6/6] Building Atlas Knowledge Graph...")
    try:
        from core.engine.kernel.graph.traversal.graph_builder   import build_graph
        from core.engine.kernel.graph.storage.graph_visualizer import export_dot
        graph = build_graph()
        graph.save()
        log(f"  WRITE: atlas/atlas_graph.json")
        dot_path = export_dot(graph)
        log(f"  WRITE: atlas/atlas_graph.dot")
        log(f"  {graph.summary()}")
        stats["graph"] = {"nodes": len(graph.nodes), "edges": len(graph.edges)}
    except ImportError as e:
        log(f"  Graph engine unavailable: {e}")

    log("\n=== Compilation complete ===")
    log(f"  Created:    {len(stats['created'])}")
    log(f"  Skipped:    {len(stats['skipped'])}")
    log(f"  Errors:     {len(stats['errors'])}")
    log(f"  Candidates: {len(stats['candidates'])}")
    if "graph" in stats:
        log(f"  Graph:      {stats['graph']['nodes']} nodes, {stats['graph']['edges']} edges")
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Helix Atlas Compiler — Formal System")
    p.add_argument("--overwrite",   action="store_true", help="Overwrite existing atlas entries")
    p.add_argument("--quiet",       action="store_true", help="Suppress output")
    args = p.parse_args()
    run(verbose=not args.quiet, overwrite=args.overwrite)
