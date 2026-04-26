"""
Falsifier Runner -- Helix Formal System
Discovers and executes all active falsifier probes in helix/research/ against the
locked Atlas memory. Aggregates pass/fail results and writes run reports.

Discovery contract:
    A file in helix/research/ is a probe if it satisfies ALL of:
      1. Ends with .py
      2. Not __init__.py, conftest.py, or any file starting with _
      3. Has: def run(atlas: dict) -> dict
         OR:  PROBE_SPEC = {"invariant": str, ...}

ProbeResult (what run() must return):
    {
        "passed":          bool,    # REQUIRED
        "signal":          float,   # REQUIRED  0.0-1.0
        "invariant":       str,     # REQUIRED
        "domain":          str,     # REQUIRED
        "run_id":          str,     # injected if absent
        "notes":           str,     # optional
        "counterexamples": list,    # optional
    }

Reports:
    helix/research/<domain>/results/falsifier_run_<ts>.json  (per domain)
    helix/research/_summary/falsifier_run_<ts>.json          (global)
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Root resolution
# ---------------------------------------------------------------------------

ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists()),
    Path(__file__).resolve().parent.parent.parent,
)
sys.path.insert(0, str(ROOT))

RESEARCH_DIR = ROOT / "helix" / "research"
ATLAS_DIR = ROOT / "helix" / "memory" / "atlas"

_SKIP_NAMES = {"__init__.py", "conftest.py", "setup.py"}

# ---------------------------------------------------------------------------
# Atlas snapshot loader
# ---------------------------------------------------------------------------

def _load_atlas_snapshot() -> dict:
    """
    Build a read-only Atlas snapshot for probe consumption.
    Returns {"invariants": {slug: data}, "entities": [...], "loaded_at": iso}
    """
    snapshot: dict = {
        "invariants": {},
        "entities":   [],
        "loaded_at":  datetime.now(timezone.utc).isoformat(),
    }

    invariants_dir = ATLAS_DIR / "invariants"
    if invariants_dir.exists():
        for path in invariants_dir.rglob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                snapshot["invariants"][path.stem] = data
            except Exception:
                pass

    registry_path = ATLAS_DIR / "entities" / "registry.json"
    if registry_path.exists():
        try:
            reg = json.loads(registry_path.read_text(encoding="utf-8"))
            snapshot["entities"] = reg.get("entities", [])
        except Exception:
            pass

    return snapshot


# ---------------------------------------------------------------------------
# Probe discovery
# ---------------------------------------------------------------------------

def _is_probe_file(path: Path) -> bool:
    if path.name in _SKIP_NAMES:
        return False
    if path.name.startswith("_"):
        return False
    return path.suffix == ".py"


def _load_probe(path: Path) -> Any:
    """Dynamically import a probe file. Returns the module, or None on failure."""
    try:
        spec = importlib.util.spec_from_file_location(
            "_probe_{}".format(path.stem), str(path)
        )
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod
    except Exception:
        return None


def _probe_runnable(mod: Any) -> bool:
    if callable(getattr(mod, "run", None)):
        return True
    spec = getattr(mod, "PROBE_SPEC", None)
    return isinstance(spec, dict) and "invariant" in spec


def discover_probes() -> list:
    """
    Walk helix/research/ and return metadata dicts for every valid probe file.
    Each entry: {"path": Path, "domain": str, "module": module}
    """
    probes = []
    if not RESEARCH_DIR.exists():
        return probes

    for path in sorted(RESEARCH_DIR.rglob("*.py")):
        if not _is_probe_file(path):
            continue
        try:
            rel    = path.relative_to(RESEARCH_DIR)
            domain = rel.parts[0] if len(rel.parts) > 1 else "root"
        except ValueError:
            domain = "root"

        mod = _load_probe(path)
        if mod is None or not _probe_runnable(mod):
            continue

        probes.append({"path": path, "domain": domain, "module": mod})

    return probes


# ---------------------------------------------------------------------------
# Probe execution
# ---------------------------------------------------------------------------

def _make_run_id(probe_path: Path) -> str:
    ts   = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^a-z0-9]", "_", probe_path.stem.lower()).strip("_")
    return "{}_{}".format(slug, ts)


def _execute_probe(probe: dict, atlas: dict) -> dict:
    """
    Run a single probe against the Atlas snapshot.
    Never raises -- all exceptions captured into result["error"].
    """
    path   = probe["path"]
    domain = probe["domain"]
    mod    = probe["module"]
    run_id = _make_run_id(path)

    base: dict = {
        "run_id":          run_id,
        "probe":           path.name,
        "probe_path":      str(path.relative_to(ROOT)),
        "domain":          domain,
        "passed":          False,
        "signal":          0.0,
        "invariant":       "",
        "notes":           "",
        "counterexamples": [],
        "error":           None,
    }

    try:
        run_fn = getattr(mod, "run", None)
        if callable(run_fn):
            result = run_fn(atlas)
        else:
            # PROBE_SPEC-only stub -- structural declaration, not runnable yet
            spec = getattr(mod, "PROBE_SPEC", {})
            result = {
                "passed":    None,
                "signal":    0.0,
                "invariant": spec.get("invariant", ""),
                "notes":     "PROBE_SPEC stub -- no run() defined",
            }

        if not isinstance(result, dict):
            raise TypeError(
                "run() must return dict, got {}".format(type(result).__name__)
            )
        for k, v in result.items():
            base[k] = v
        if not base.get("run_id"):
            base["run_id"] = run_id

    except Exception as e:
        base["error"] = traceback.format_exc()
        base["notes"] = "Probe raised: {}".format(e)

    return base


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def _write_report(domain: str, results: list, run_ts: str) -> Path:
    """Write per-domain falsifier report to helix/research/<domain>/results/."""
    results_dir = ROOT / "helix" / "reports"
    results_dir.mkdir(parents=True, exist_ok=True)

    passed  = [r for r in results if r.get("passed") is True]
    failed  = [r for r in results if r.get("passed") is False]
    errored = [r for r in results if r.get("error")]
    stubs   = [r for r in results if r.get("passed") is None]

    report = {
        "run_id":    "falsifier_{}_{}".format(domain, run_ts),
        "domain":    domain,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total":   len(results),
            "passed":  len(passed),
            "failed":  len(failed),
            "errored": len(errored),
            "stubs":   len(stubs),
        },
        "results": results,
    }

    out = results_dir / "falsifier_run_{}.json".format(run_ts)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _write_summary(all_results: list, run_ts: str) -> Path:
    """Write cross-domain summary to helix/research/_summary/."""
    summary_dir = ROOT / "helix" / "reports"
    summary_dir.mkdir(parents=True, exist_ok=True)

    passed  = sum(1 for r in all_results if r.get("passed") is True)
    failed  = sum(1 for r in all_results if r.get("passed") is False)
    errored = sum(1 for r in all_results if r.get("error"))
    stubs   = sum(1 for r in all_results if r.get("passed") is None)

    violated = sorted({
        r["invariant"] for r in all_results
        if r.get("passed") is False and r.get("invariant")
    })

    summary = {
        "run_id":    "falsifier_global_{}".format(run_ts),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total":     len(all_results),
            "passed":    passed,
            "failed":    failed,
            "errored":   errored,
            "stubs":     stubs,
            "pass_rate": round(passed / max(passed + failed, 1), 4),
        },
        "violated_invariants": violated,
        "probe_index": [
            {
                "probe":     r["probe"],
                "domain":    r["domain"],
                "invariant": r.get("invariant"),
                "passed":    r.get("passed"),
                "signal":    r.get("signal"),
            }
            for r in all_results
        ],
    }

    out = summary_dir / "falsifier_run_{}.json".format(run_ts)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_falsifiers(verbose: bool = True) -> dict:
    """
    Discover all probes in helix/research/, load Atlas snapshot, execute, write reports.
    Returns global summary dict.
    """
    log    = print if verbose else (lambda *a, **k: None)
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    log("=== Helix Falsifier Runner ===")
    log("Root:  {}".format(ROOT))
    log("Research: {}".format(RESEARCH_DIR.relative_to(ROOT)))
    log("Atlas: {}".format(ATLAS_DIR.relative_to(ROOT)))

    log("\n[1/3] Loading Atlas memory snapshot...")
    atlas     = _load_atlas_snapshot()
    log("  {} invariants, {} entities loaded".format(
        len(atlas["invariants"]), len(atlas["entities"])))

    log("\n[2/3] Discovering probes in helix/research/...")
    probes = discover_probes()
    if not probes:
        log("  No runnable probes found.")
        return {"total": 0, "passed": 0, "failed": 0, "errored": 0}

    domains: dict = {}
    for p in probes:
        domains.setdefault(p["domain"], []).append(p)
    for domain, ps in sorted(domains.items()):
        log("  {}: {} probe(s)".format(domain, len(ps)))
    log("  Total: {} runnable probes".format(len(probes)))

    log("\n[3/3] Running probes against Atlas memory...")
    all_results:    list = []
    domain_results: dict = {}

    for probe in probes:
        result = _execute_probe(probe, atlas)
        all_results.append(result)
        domain_results.setdefault(probe["domain"], []).append(result)

        if result.get("error"):
            log("  ERROR  {}: {}".format(result["probe_path"], result["notes"]))
        elif result.get("passed") is None:
            log("  STUB   {}: {}".format(
                result["probe_path"], result.get("invariant", "?")))
        elif result["passed"]:
            log("  PASS   {} [{}] signal={:.3f}".format(
                result["probe_path"],
                result.get("invariant", "?"),
                result.get("signal", 0.0)))
        else:
            log("  FAIL   {} [{}] signal={:.3f} cx={}".format(
                result["probe_path"],
                result.get("invariant", "?"),
                result.get("signal", 0.0),
                len(result.get("counterexamples", []))))

    written: list = []
    for domain, results in domain_results.items():
        out = _write_report(domain, results, run_ts)
        log("  WRITE: {}".format(out.relative_to(ROOT)))
        written.append(out)

    summary_path = _write_summary(all_results, run_ts)
    log("  WRITE: {}".format(summary_path.relative_to(ROOT)))

    passed  = sum(1 for r in all_results if r.get("passed") is True)
    failed  = sum(1 for r in all_results if r.get("passed") is False)
    errored = sum(1 for r in all_results if r.get("error"))

    log("\n=== Falsifier Run complete ===")
    log("  Total:   {}".format(len(all_results)))
    log("  Passed:  {}".format(passed))
    log("  Failed:  {}".format(failed))
    log("  Errored: {}".format(errored))
    if failed:
        violated = sorted({
            r["invariant"] for r in all_results
            if r.get("passed") is False and r.get("invariant")
        })
        log("  Violated: {}".format(", ".join(violated) or "none named"))

    return {
        "total":   len(all_results),
        "passed":  passed,
        "failed":  failed,
        "errored": errored,
        "reports": [str(p) for p in written],
        "summary": str(summary_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Helix Falsifier Runner")
    p.add_argument("--quiet",  action="store_true", help="Suppress output")
    p.add_argument("--domain", default=None,
                   help="Restrict to a specific lab domain (e.g. music_probes)")
    args = p.parse_args()

    if args.domain:
        _target = args.domain
        _orig   = discover_probes

        def discover_probes():  # type: ignore[misc]
            return [p for p in _orig() if p["domain"] == _target]

    run_falsifiers(verbose=not args.quiet)
