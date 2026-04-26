"""
phase4.py — Phase 4 orchestrator for the Helix Foobar Tool.

Ties together the full staged trace fusion pipeline:
  1. Stage all sources (library, foobar runtime, Last.fm, Spotify, codex)
  2. Resolve entities across sources (confidence-scored matching)
  3. Validate resolved groups (7 checkpoint rules)
  4. Plan codex refresh (dry-run, 7 action categories)
  5. Build active corpora (derived from real signals)
  6. Write all artifacts to artifacts/runs/<run_id>/
  7. Write run_log.json

Entry point:
  from applications.tools.foobar.phase4 import run_phase4
  run_phase4(args, foobar_records, codex_records)

Or via CLI:
  python -m applications.tools.foobar.runner --phase4
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


# ---------------------------------------------------------------------------
# Phase 4 pipeline
# ---------------------------------------------------------------------------

def run_phase4(
    foobar_records: list[dict],
    codex_records: dict[str, dict],
    *,
    lastfm_path: Path | None = None,
    spotify_path: Path | None = None,
    include_lastfm: bool = True,
    include_spotify: bool = True,
    top_n_corpus: int = 1000,
    dry_run: bool = True,
    label: str = "phase4",
) -> dict:
    """
    Execute the full Phase 4 trace fusion pipeline.

    Parameters:
        foobar_records  list[dict] from sync.scan_foobar_library
        codex_records   dict[path, dict] from sync.load_codex_tracks
        lastfm_path     override Last.fm JSON path
        spotify_path    override Spotify JSON path
        include_lastfm  whether to include Last.fm (default True)
        include_spotify whether to include Spotify (default True)
        top_n_corpus    top N entities to include in corpus (by scrobbles)
        dry_run         if False, scaffold for future apply mode (not yet active)
        label           run label prefix

    Returns:
        dict with run_id, artifact_paths, and summary counts
    """
    from domains.music.fusion.run_log import RunLog
    from domains.music.fusion.staging import (
        stage_all_sources,
        _LASTFM_PATH, _SPOTIFY_PATH,
    )
    from domains.music.fusion.entity_resolver import resolve_entities, summarize_resolution
    from domains.music.fusion.validator import validate_all, summarize_validation
    from domains.music.fusion.refresh_planner import (
        plan_refresh, summarize_plan,
        write_refresh_plan, write_patch_candidates,
        write_manual_review, write_new_candidates,
    )
    from domains.music.fusion.corpus_builder import (
        build_corpora, corpus_to_dict, build_corpus_index,
    )

    log = RunLog(label=label)
    log.start()
    log.set_meta("dry_run", dry_run)
    log.set_meta("foobar_record_count", len(foobar_records))
    log.set_meta("codex_record_count", len(codex_records))

    run_dir = log.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    eff_lastfm  = Path(lastfm_path)  if lastfm_path  else _LASTFM_PATH
    eff_spotify = Path(spotify_path) if spotify_path else _SPOTIFY_PATH

    # -----------------------------------------------------------------------
    # 1. Stage all sources
    # -----------------------------------------------------------------------
    print("\n[phase4] ── STAGE ──────────────────────────────────────────────")
    try:
        snapshots = stage_all_sources(
            foobar_records, codex_records,
            snapshot_id    = log.run_id,
            lastfm_path    = eff_lastfm,
            spotify_path   = eff_spotify,
            include_lastfm  = include_lastfm,
            include_spotify = include_spotify,
        )
    except Exception as e:
        log.error(f"staging failed: {e}")
        log.finish("error")
        log.write()
        raise

    source_counts = {src: snap.record_count for src, snap in snapshots.items()}
    log.record("source_counts", source_counts)

    # Write source snapshot manifest
    snap_manifest = {
        "snapshot_id": log.run_id,
        "sources": {
            src: {
                "record_count": snap.record_count,
                "meta": snap.meta,
            }
            for src, snap in snapshots.items()
        },
    }
    snap_path = log.write_artifact("source_snapshot_manifest.json", snap_manifest)

    # Write staged source summary markdown
    _write_staged_source_summary(run_dir, log.run_id, snapshots)
    log.add_output(run_dir / "staged_source_summary.md")

    # -----------------------------------------------------------------------
    # 2. Entity resolution
    # -----------------------------------------------------------------------
    print("\n[phase4] ── RESOLVE ────────────────────────────────────────────")
    try:
        groups = resolve_entities(snapshots)
    except Exception as e:
        log.error(f"entity resolution failed: {e}")
        log.finish("error")
        log.write()
        raise

    res_summary = summarize_resolution(groups)
    log.record("match_counts", res_summary)

    # Split ambiguous matches for separate report
    ambiguous = [g for g in groups
                 if g.match_class in ("ambiguous_match", "conflict_requires_review")]

    # Write entity resolution report (top matches + full summary)
    er_path = log.write_artifact("entity_resolution_report.json", {
        "summary": res_summary,
        "high_confidence_sample": [
            g.to_dict() for g in groups
            if g.confidence >= 0.85 and len(g.sources_matched) > 1
        ][:500],
    })

    amb_path = log.write_artifact("ambiguous_matches.json", {
        "count": len(ambiguous),
        "matches": [g.to_dict() for g in ambiguous[:200]],
    })

    # -----------------------------------------------------------------------
    # 3. Validation
    # -----------------------------------------------------------------------
    print("\n[phase4] ── VALIDATE ───────────────────────────────────────────")
    try:
        validation_results = validate_all(groups)
    except Exception as e:
        log.error(f"validation failed: {e}")
        log.finish("error")
        log.write()
        raise

    val_summary = summarize_validation(validation_results)
    log.record("validation_counts", {
        "pass":   val_summary["pass_count"],
        "fail":   val_summary["fail_count"],
        "review": val_summary["review_count"],
        "refresh_eligible": val_summary["refresh_eligible"],
    })

    val_path = log.write_artifact("validation_results.json", {
        "summary": val_summary,
        "failures": [
            r.to_dict() for r in validation_results
            if r.status == "fail"
        ][:300],
        "reviews": [
            r.to_dict() for r in validation_results
            if r.status == "manual_review"
        ][:300],
    })

    # -----------------------------------------------------------------------
    # 4. Refresh planning
    # -----------------------------------------------------------------------
    print("\n[phase4] ── PLAN ───────────────────────────────────────────────")
    try:
        candidates = plan_refresh(groups, validation_results)
    except Exception as e:
        log.error(f"refresh planning failed: {e}")
        log.finish("error")
        log.write()
        raise

    plan_summary = summarize_plan(candidates)
    log.record("refresh_counts", plan_summary.get("by_action", {}))

    write_refresh_plan(candidates, run_dir / "codex_refresh_plan.json")
    log.add_output(run_dir / "codex_refresh_plan.json")

    write_patch_candidates(candidates, run_dir / "codex_patch_candidates.json")
    log.add_output(run_dir / "codex_patch_candidates.json")

    write_manual_review(candidates, run_dir / "codex_manual_review.json")
    log.add_output(run_dir / "codex_manual_review.json")

    write_new_candidates(candidates, run_dir / "codex_new_candidates.json")
    log.add_output(run_dir / "codex_new_candidates.json")

    # -----------------------------------------------------------------------
    # 5. Active corpus generation
    # -----------------------------------------------------------------------
    print("\n[phase4] ── CORPORA ────────────────────────────────────────────")
    try:
        corpora = build_corpora(groups, validation_results, candidates)
    except Exception as e:
        log.error(f"corpus building failed: {e}")
        log.finish("error")
        log.write()
        raise

    corpus_index = build_corpus_index(corpora)
    log.record("corpus_counts", {k: len(v) for k, v in corpora.items()})

    # Write each corpus (limit to manageable size)
    for name, entries in corpora.items():
        filename = f"corpus_{_safe_name(name)}.json"
        log.write_artifact(filename, corpus_to_dict(name, entries[:top_n_corpus], log.run_id))

    log.write_artifact("corpus_index.json", corpus_index)

    # -----------------------------------------------------------------------
    # 6. Phase 4 summary markdown
    # -----------------------------------------------------------------------
    _write_phase4_summary(run_dir, log, snapshots, res_summary, val_summary, plan_summary, corpora)
    log.add_output(run_dir / "phase4_summary.md")

    # -----------------------------------------------------------------------
    # 7. Finalize run log
    # -----------------------------------------------------------------------
    log.finish("complete")
    log_path = log.write()

    print(f"\n[phase4] ── DONE ───────────────────────────────────────────────")
    print(f"  Run ID   : {log.run_id}")
    print(f"  Run dir  : {run_dir}")
    print(f"  Outputs  : {len(log.data['outputs_written'])} artifacts")
    print(f"  Warnings : {len(log.data['warnings'])}")
    print(f"  Errors   : {len(log.data['errors'])}")

    return {
        "run_id":       log.run_id,
        "run_dir":      str(run_dir),
        "source_counts": source_counts,
        "match_counts":  res_summary,
        "validation":    val_summary,
        "refresh_plan":  plan_summary,
        "corpus_summary": corpus_index,
        "log_path":     str(log_path),
    }


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------

def _write_staged_source_summary(
    run_dir: Path,
    snapshot_id: str,
    snapshots: dict,
) -> None:
    lines = [
        "# Helix Phase 4 — Staged Source Summary",
        f"Snapshot ID: `{snapshot_id}`",
        "",
        "## Sources Staged",
        "| Source | Records | Notes |",
        "|--------|---------|-------|",
    ]
    for src, snap in snapshots.items():
        meta_note = ""
        if src == "lastfm":
            meta_note = f"{snap.meta.get('total_scrobbles', 0):,} total scrobbles"
        elif src == "spotify":
            meta_note = snap.meta.get("source_path", "")
        elif not snap.meta.get("available", True):
            meta_note = "⚠ not available"
        lines.append(f"| `{src}` | {snap.record_count:,} | {meta_note} |")

    lines += [
        "",
        "## Authority Model",
        "| Source | Role |",
        "|--------|------|",
        "| `foobar_runtime` | Canonical metadata authority (TITLE, ARTIST, SOUND TEAM, etc.) |",
        "| `codex` | Prior structured mirror (stable IDs, normalization history) |",
        "| `lastfm` | Behavioral trace (listening priority, usage signal) |",
        "| `spotify` | Preference trace (popularity, taste signal) |",
    ]
    (run_dir / "staged_source_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _write_phase4_summary(
    run_dir: Path,
    log: "RunLog",
    snapshots: dict,
    res_summary: dict,
    val_summary: dict,
    plan_summary: dict,
    corpora: dict,
) -> None:
    from datetime import datetime, timezone
    lines = [
        "# Helix Phase 4 — Trace Fusion Summary",
        f"Run ID: `{log.run_id}`",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Duration: {log.data.get('duration_sec', '?')}s",
        "",
        "---",
        "",
        "## Source Snapshot",
        "| Source | Records |",
        "|--------|---------|",
    ]
    for src, snap in snapshots.items():
        lines.append(f"| `{src}` | {snap.record_count:,} |")

    lines += [
        "",
        "## Entity Resolution",
        "| Match Class | Count |",
        "|-------------|-------|",
    ]
    for mc, count in sorted(res_summary.get("by_match_class", {}).items(), key=lambda x: -x[1]):
        lines.append(f"| `{mc}` | {count:,} |")

    lines += [
        "",
        f"Multi-source groups: {res_summary.get('multi_source_count', 0):,}  ",
        f"High confidence (≥0.85): {res_summary.get('high_confidence_count', 0):,}  ",
        "",
        "## Validation",
        f"- PASS : {val_summary.get('pass_count', 0):,}",
        f"- FAIL : {val_summary.get('fail_count', 0):,}",
        f"- REVIEW : {val_summary.get('review_count', 0):,}",
        f"- Refresh eligible : {val_summary.get('refresh_eligible', 0):,}",
        "",
        "## Refresh Plan (Dry-run)",
        "| Action | Count |",
        "|--------|-------|",
    ]
    for action, count in sorted(plan_summary.get("by_action", {}).items(), key=lambda x: -x[1]):
        lines.append(f"| `{action}` | {count:,} |")
    lines.append(f"| **safe to apply** | "
                 f"{plan_summary.get('safe_to_apply_count', 0):,} |")

    lines += [
        "",
        "## Active Corpora Generated",
        "| Corpus | Entries |",
        "|--------|---------|",
    ]
    for name, entries in sorted(corpora.items()):
        lines.append(f"| `{name}` | {len(entries):,} |")

    lines += [
        "",
        "## Artifacts Written",
        "| File | Contents |",
        "|------|----------|",
        "| `staged_source_summary.md` | Source staging overview |",
        "| `source_snapshot_manifest.json` | Per-source record counts |",
        "| `entity_resolution_report.json` | Match classes and signals |",
        "| `ambiguous_matches.json` | Matches needing manual review |",
        "| `validation_results.json` | PASS/FAIL/REVIEW per entity |",
        "| `codex_refresh_plan.json` | Full dry-run plan (7 actions) |",
        "| `codex_patch_candidates.json` | Safe narrow field patches |",
        "| `codex_manual_review.json` | Records requiring operator review |",
        "| `codex_new_candidates.json` | New library records for codex |",
        "| `corpus_*.json` | Per-named-corpus entry lists |",
        "| `corpus_index.json` | Index of all generated corpora |",
        "| `run_log.json` | Full machine-readable run record |",
        "",
        "## Safety",
        "> **DRY-RUN**: No codex records were written in this run.",
        "> Apply paths are scaffolded but require explicit operator invocation.",
        "> Last.fm / Spotify strings were not written to canonical metadata fields.",
    ]

    if log.data.get("warnings"):
        lines += ["", "## Warnings"]
        for w in log.data["warnings"]:
            lines.append(f"- {w['msg']}")
    if log.data.get("errors"):
        lines += ["", "## Errors"]
        for e in log.data["errors"]:
            lines.append(f"- {e['msg']}")

    (run_dir / "phase4_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _safe_name(s: str) -> str:
    import re
    return re.sub(r"[^\w\-]", "_", s.lower())[:48]
