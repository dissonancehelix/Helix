"""
Promotion Engine — 03_engines/governance_bridge/promotion_engine.py

Run the 6-criterion Atlas promotion gate for a named invariant.
Reads from 06_atlas/<invariant_name>.json, updates with promotion status.
"""

from __future__ import annotations
import json
from importlib import import_module
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())


def promote_invariant(
    invariant_name: str,
    atlas_dir: str | Path | None = None,
    verbose: bool = True,
) -> dict:
    """
    Run promotion gate for a named invariant.

    Args:
        invariant_name: Name of the invariant (matches atlas filename).
        atlas_dir:      Path to 06_atlas/ (default: ROOT/06_atlas).
        verbose:        Print criterion results.

    Returns:
        dict with: passed (bool), invariant_name, criteria, atlas_path.

    Raises:
        FileNotFoundError: If atlas entry doesn't exist.
    """
    if atlas_dir is None:
        atlas_dir = ROOT / "06_atlas"
    atlas_dir = Path(atlas_dir)

    atlas_path = atlas_dir / f"{invariant_name}.json"
    if not atlas_path.exists():
        raise FileNotFoundError(
            f"Atlas entry not found: {atlas_path}. "
            f"Run 'helix atlas-build' first."
        )

    with open(atlas_path, "r", encoding="utf-8") as f:
        atlas_entry = json.load(f)

    # Run promotion gates
    gates = import_module("02_governance.promotion_gates")
    gate_result = gates.evaluate_promotion(atlas_entry)

    if verbose:
        print(f"[PROMOTE] Evaluating '{invariant_name}':")
        for criterion in gate_result["criteria"]:
            status = "PASS" if criterion["passed"] else "FAIL"
            print(f"  [{status}] {criterion['name']}: {criterion['reason']}")
        overall = "PROMOTED" if gate_result["passed"] else "BLOCKED"
        print(f"[PROMOTE] Result: {overall}")

    # Write promotion status back to atlas entry
    atlas_entry["promotion_status"] = "PROMOTED" if gate_result["passed"] else "BLOCKED"
    atlas_entry["last_promotion_check"] = import_module(
        "03_engines.runtime.run_manifest"
    ).datetime.now().isoformat() if False else __import__(
        "datetime"
    ).datetime.now(__import__("datetime").timezone.utc).isoformat()

    with open(atlas_path, "w", encoding="utf-8") as f:
        json.dump(atlas_entry, f, indent=2)

    return {
        "passed": gate_result["passed"],
        "invariant_name": invariant_name,
        "criteria": gate_result["criteria"],
        "atlas_path": str(atlas_path),
    }
