"""
materialization_runner.py — Orchestrate Phase 6 Part B semantic materialization.

Runs artist materialization and edge materialization together,
optionally enriched with signal data from Part A.

Produces:
  artist_entity_materialization.json
  contributor_edge_materialization.json
  semantic_materialization_report.json (summary)

All outputs go to the artifacts_dir passed by the caller.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .artist_materializer import ArtistMaterializer
from .edge_materializer import EdgeMaterializer
from system.tools.music_pipeline.signal_record import SignalRecord

_FIELD_INDEX_PATH = _REPO_ROOT / "codex" / "library" / "music" / ".field_index.json"


def run_materialization(
    artifacts_dir: Path,
    signal_registry: Optional[dict[str, SignalRecord]] = None,
    *,
    verbose: bool = False,
) -> dict:
    """
    Run full Part B materialization.

    Parameters:
        artifacts_dir     — where to write JSON output files
        signal_registry   — optional SignalRecord registry from Part A
        verbose           — print progress

    Returns summary dict.
    """
    t0 = time.time()
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ── Load field index ───────────────────────────────────────────────────────
    if not _FIELD_INDEX_PATH.exists():
        raise FileNotFoundError(f"Field index not found: {_FIELD_INDEX_PATH}")

    if verbose:
        print("[materialization] Loading field index...")
    field_index = json.loads(_FIELD_INDEX_PATH.read_text(encoding="utf-8"))
    by_loved    = set(field_index.get("by_loved", []))

    # ── Part B.1: Artist entity materialization ────────────────────────────────
    if verbose:
        print("[materialization] Running artist materialization...")

    materializer = ArtistMaterializer(
        field_index=field_index,
        signal_registry=signal_registry,
        by_loved=by_loved,
    )
    artist_records = materializer.run()
    artist_summary = materializer.summary(artist_records)

    if verbose:
        print(f"[materialization] {len(artist_records):,} artist keys processed")
        for k, v in artist_summary.items():
            print(f"  {k}: {v}")

    # Write artist records
    artist_out = artifacts_dir / "artist_entity_materialization.json"
    artist_out.write_text(
        json.dumps(
            {
                "generated_at":    datetime.now(tz=timezone.utc).isoformat(),
                "summary":         artist_summary,
                "records":         [r.to_dict() for r in artist_records],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if verbose:
        print(f"[materialization] Wrote {artist_out}")

    # ── Part B.2: Edge (relationship) materialization ──────────────────────────
    if verbose:
        print("[materialization] Running edge materialization...")

    edge_materializer = EdgeMaterializer(
        field_index=field_index,
        signal_registry=signal_registry,
        by_loved=by_loved,
    )
    edges = edge_materializer.run()
    edge_summary = edge_materializer.summary(edges)

    if verbose:
        print(f"[materialization] {len(edges):,} edges materialized")
        for k, v in edge_summary.items():
            print(f"  {k}: {v}")

    # Write edge records
    edge_out = artifacts_dir / "contributor_edge_materialization.json"
    edge_out.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "summary":      edge_summary,
                "edges":        [e.to_dict() for e in edges],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if verbose:
        print(f"[materialization] Wrote {edge_out}")

    # ── Summary report ────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    summary = {
        "generated_at":    datetime.now(tz=timezone.utc).isoformat(),
        "elapsed_s":       round(elapsed, 1),
        "signal_enriched": signal_registry is not None,
        "artist_materialization": artist_summary,
        "edge_materialization":   edge_summary,
        "outputs": {
            "artist_entity_materialization": str(artist_out),
            "contributor_edge_materialization": str(edge_out),
        },
    }

    report_out = artifacts_dir / "semantic_materialization_report.json"
    report_out.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return summary

