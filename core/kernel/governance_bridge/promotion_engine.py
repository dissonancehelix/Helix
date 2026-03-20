"""Promotion Engine.

Run the six-criterion promotion gate for invariant entries stored under
``codex/atlas/invariants``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.kernel import promotion_gates
from core.paths import ATLAS_ROOT


def promote_invariant(
    invariant_name: str,
    atlas_dir: str | Path | None = None,
    verbose: bool = True,
) -> dict:
    atlas_dir = Path(atlas_dir or (ATLAS_ROOT / "invariants"))
    atlas_path = atlas_dir / f"{invariant_name}.json"
    if not atlas_path.exists():
        raise FileNotFoundError(f"Atlas entry not found: {atlas_path}. Run 'helix atlas-build' first.")

    atlas_entry = json.loads(atlas_path.read_text(encoding="utf-8"))
    gate_result = promotion_gates.evaluate_promotion(atlas_entry)

    if verbose:
        print(f"[PROMOTE] Evaluating '{invariant_name}':")
        for criterion in gate_result["criteria"]:
            status = "PASS" if criterion["passed"] else "FAIL"
            print(f"  [{status}] {criterion['name']}: {criterion['reason']}")
        overall = "PROMOTED" if gate_result["passed"] else "BLOCKED"
        print(f"[PROMOTE] Result: {overall}")

    atlas_entry["promotion_status"] = "PROMOTED" if gate_result["passed"] else "BLOCKED"
    atlas_entry["last_promotion_check"] = datetime.now(timezone.utc).isoformat()
    atlas_path.write_text(json.dumps(atlas_entry, indent=2), encoding="utf-8")

    return {
        "passed": gate_result["passed"],
        "invariant_name": invariant_name,
        "criteria": gate_result["criteria"],
        "atlas_path": str(atlas_path),
    }
