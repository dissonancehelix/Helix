"""
phase6.py — Phase 6 CLI handler for the Helix Foobar Tool.

Two sub-modes, matching the Phase 6 spec:
  --phase6 signals      Part A: Historical Signal Unification
  --phase6 materialize  Part B: Semantic Materialization
  --phase6 full         Run Part A then Part B
  --phase6 beefweb      Beefweb live runtime query
  --phase6 report       Generate summary report from existing artifacts

Artifacts are written to:
  domains/music/model/datasets/music/phase6/

Usage:
  python -m applications.tools.foobar.runner --phase6 signals
  python -m applications.tools.foobar.runner --phase6 materialize
  python -m applications.tools.foobar.runner --phase6 full
  python -m applications.tools.foobar.runner --phase6 beefweb
  python -m applications.tools.foobar.runner --phase6 report
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_ARTIFACTS_DIR = (
    _REPO_ROOT / "domains" / "music" / "data" / "phase6"
)


def run_phase6(args: "argparse.Namespace") -> int:
    """
    Entry point called from runner.py when --phase6 is specified.
    args.phase6     — subcommand (signals | materialize | full | beefweb | report)
    args.verbose    — verbose flag
    """
    cmd     = getattr(args, "phase6", None) or "full"
    verbose = getattr(args, "verbose", False)

    dispatch = {
        "signals":     _run_signals,
        "materialize": _run_materialize,
        "full":        _run_full,
        "beefweb":     _run_beefweb,
        "report":      _run_report,
    }

    handler = dispatch.get(cmd)
    if not handler:
        print(f"[phase6] Unknown subcommand: {cmd!r}")
        print("  Available: signals | materialize | full | beefweb | report")
        return 1

    return handler(verbose)


# ── Part A: Historical Signal Unification ────────────────────────────────────

def _run_signals(verbose: bool) -> int:
    from domains.music.tools.pipeline.signal_fuser import SignalFuser
    from domains.music.tools.pipeline.signal_record import (
        SPLIT_BOTH_ZERO, SPLIT_LOCAL_ONLY, SPLIT_LASTFM_ONLY,
        SPLIT_DIVERGENT, SPLIT_UNRESOLVABLE,
        COMPLETENESS_FULL, COMPLETENESS_HIGH,
    )

    print("[phase6:signals] Running historical signal unification...")
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    fuser    = SignalFuser()
    registry = fuser.run(verbose=verbose)

    if not registry:
        print("[phase6:signals] ERROR: No tracks found in field index.")
        return 1

    print(f"[phase6:signals] {len(registry):,} tracks in signal registry")

    # ── Build summary statistics ───────────────────────────────────────────────
    n_loved    = sum(1 for r in registry.values() if r.local_loved)
    n_local    = sum(1 for r in registry.values() if r.has_local_playcount)
    n_eps      = sum(1 for r in registry.values() if r.has_eps_data)
    n_lastfm   = sum(1 for r in registry.values() if r.has_lastfm_data)
    n_both     = sum(1 for r in registry.values() if r.has_local_playcount and r.has_lastfm_data)
    n_local_only  = sum(1 for r in registry.values() if r.local_only_signal)
    n_lfm_only    = sum(1 for r in registry.values() if r.lastfm_only_signal)
    n_priority    = sum(1 for r in registry.values() if r.priority_reconciliation_candidate)
    n_divergent   = sum(1 for r in registry.values() if r.playcount_split_state in (SPLIT_DIVERGENT, SPLIT_UNRESOLVABLE))
    n_sync        = sum(1 for r in registry.values() if r.playcount_split_state == "synchronized")
    n_full        = sum(1 for r in registry.values() if r.timeline_completeness == COMPLETENESS_FULL)
    n_high        = sum(1 for r in registry.values() if r.timeline_completeness == COMPLETENESS_HIGH)

    # Top 20 tracks by lifetime signal score
    top_tracks = sorted(
        registry.values(),
        key=lambda r: r.lifetime_signal_score or 0,
        reverse=True,
    )[:20]

    # Split state distribution
    split_dist: dict[str, int] = {}
    for r in registry.values():
        s = r.playcount_split_state or "unknown"
        split_dist[s] = split_dist.get(s, 0) + 1

    # Completeness distribution
    comp_dist: dict[str, int] = {}
    for r in registry.values():
        c = r.timeline_completeness or "unknown"
        comp_dist[c] = comp_dist.get(c, 0) + 1

    summary = {
        "generated_at":    datetime.now(tz=timezone.utc).isoformat(),
        "total_tracks":    len(registry),
        "loved_tracks":    n_loved,
        "source_coverage": {
            "local_playcount":  n_local,
            "eps_data":         n_eps,
            "lastfm_data":      n_lastfm,
            "multi_source":     n_both,
        },
        "split_state_distribution": split_dist,
        "timeline_completeness": comp_dist,
        "flags": {
            "local_only_signal":  n_local_only,
            "lastfm_only_signal": n_lfm_only,
            "divergent_counts":   n_divergent,
            "synchronized":       n_sync,
            "priority_reconciliation_candidates": n_priority,
        },
        "top_20_by_lifetime_signal": [
            {
                "track_id":            r.track_id,
                "artist_key":          r.artist_key,
                "lifetime_score":      r.lifetime_signal_score,
                "active_rotation":     round(r.active_rotation_score or 0, 3),
                "local_playcount":     r.local_playcount,
                "lastfm_playcount":    r.lastfm_playcount,
                "split_state":         r.playcount_split_state,
                "loved":               r.local_loved,
            }
            for r in top_tracks
        ],
    }

    # ── Write full registry (JSON Lines) ─────────────────────────────────────
    registry_out = _ARTIFACTS_DIR / "lifetime_signal_registry.json"
    print(f"[phase6:signals] Writing signal registry to {registry_out}...")
    with registry_out.open("w", encoding="utf-8") as f:
        f.write("[\n")
        items = list(registry.values())
        for i, rec in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + comma + "\n")
        f.write("]\n")

    # ── Write reconciliation report ────────────────────────────────────────────
    priority_records = [r for r in registry.values() if r.priority_reconciliation_candidate]
    reconcile_out = _ARTIFACTS_DIR / "historical_reconciliation_report.json"
    reconcile_out.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "total_candidates": len(priority_records),
                "candidates": [
                    {
                        "track_id":         r.track_id,
                        "artist_key":       r.artist_key,
                        "split_state":      r.playcount_split_state,
                        "local_playcount":  r.local_playcount,
                        "lastfm_playcount": r.lastfm_playcount,
                        "completeness":     r.timeline_completeness,
                        "loved":            r.local_loved,
                    }
                    for r in sorted(priority_records, key=lambda r: -(r.total_evidence_plays()))[:500]
                ],
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ── Write playcount split report ──────────────────────────────────────────
    split_out = _ARTIFACTS_DIR / "playcount_split_report.json"
    split_out.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "distribution": split_dist,
                "divergent_sample": [
                    {
                        "track_id":         r.track_id,
                        "artist_key":       r.artist_key,
                        "local_playcount":  r.local_playcount,
                        "lastfm_playcount": r.lastfm_playcount,
                        "split_state":      r.playcount_split_state,
                    }
                    for r in registry.values()
                    if r.playcount_split_state in (SPLIT_DIVERGENT, SPLIT_UNRESOLVABLE)
                ][:100],
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ── Write timeline completeness report ────────────────────────────────────
    timeline_out = _ARTIFACTS_DIR / "timeline_completeness_report.json"
    timeline_out.write_text(
        json.dumps(
            {
                "generated_at":  datetime.now(tz=timezone.utc).isoformat(),
                "distribution":  comp_dist,
                "full_coverage_sample": [
                    {
                        "track_id":         r.track_id,
                        "artist_key":       r.artist_key,
                        "lastfm_playcount": r.lastfm_playcount,
                        "eps_first":        r.first_played_enhanced,
                        "eps_last":         r.last_played_enhanced,
                    }
                    for r in registry.values()
                    if r.timeline_completeness == COMPLETENESS_FULL
                ][:50],
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ── Write summary ─────────────────────────────────────────────────────────
    summary_out = _ARTIFACTS_DIR / "phase6_signal_summary.json"
    summary_out.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    _write_signal_summary_md(summary, _ARTIFACTS_DIR)

    print(f"[phase6:signals] Done. Artifacts in {_ARTIFACTS_DIR}")
    _print_signal_summary(summary)

    return 0


def _print_signal_summary(s: dict) -> None:
    print(f"\n  Total tracks:      {s['total_tracks']:,}")
    print(f"  Loved tracks:      {s['loved_tracks']:,}")
    cov = s["source_coverage"]
    print(f"  Local playcount:   {cov['local_playcount']:,}")
    print(f"  EPS data:          {cov['eps_data']:,}")
    print(f"  Last.fm data:      {cov['lastfm_data']:,}")
    print(f"  Multi-source:      {cov['multi_source']:,}")
    flags = s["flags"]
    print(f"  Local-only:        {flags['local_only_signal']:,}")
    print(f"  Last.fm-only:      {flags['lastfm_only_signal']:,}")
    print(f"  Priority recon:    {flags['priority_reconciliation_candidates']:,}")
    print(f"\n  Split state distribution:")
    for state, count in sorted(s["split_state_distribution"].items(), key=lambda x: -x[1]):
        print(f"    {state:<25} {count:,}")
    print(f"\n  Top 3 by lifetime signal:")
    for r in s["top_20_by_lifetime_signal"][:3]:
        print(f"    {r['artist_key']:<30} score={r['lifetime_score']:.1f}  "
              f"lastfm={r['lastfm_playcount']}  local={r['local_playcount']}")


def _write_signal_summary_md(summary: dict, artifacts_dir: Path) -> None:
    lines = [
        "# Phase 6 Signal Summary",
        f"Generated: {summary['generated_at']}",
        "",
        "## Source Coverage",
        f"| Source | Tracks |",
        f"|--------|--------|",
        f"| Total tracks | {summary['total_tracks']:,} |",
        f"| Loved tracks | {summary['loved_tracks']:,} |",
    ]
    for k, v in summary["source_coverage"].items():
        lines.append(f"| {k} | {v:,} |")

    lines += [
        "",
        "## Playcount Split State",
        "| State | Count |",
        "|-------|-------|",
    ]
    for state, count in sorted(summary["split_state_distribution"].items(), key=lambda x: -x[1]):
        lines.append(f"| `{state}` | {count:,} |")

    lines += [
        "",
        "## Timeline Completeness",
        "| Level | Count |",
        "|-------|-------|",
    ]
    for level, count in sorted(summary["timeline_completeness"].items(), key=lambda x: -x[1]):
        lines.append(f"| `{level}` | {count:,} |")

    lines += [
        "",
        "## Flags",
        "| Flag | Count |",
        "|------|-------|",
    ]
    for k, v in summary["flags"].items():
        lines.append(f"| `{k}` | {v:,} |")

    lines += [
        "",
        "## Top 20 by Lifetime Signal Score",
        "| Track ID | Artist | Score | Active Rotation | Local | Last.fm | Split |",
        "|----------|--------|-------|-----------------|-------|---------|-------|",
    ]
    for r in summary["top_20_by_lifetime_signal"]:
        loved_mark = " ♥" if r["loved"] else ""
        lines.append(
            f"| `{r['track_id']}` | {r['artist_key']}{loved_mark} | "
            f"{r['lifetime_score']:.1f} | {r['active_rotation']:.3f} | "
            f"{r['local_playcount'] or '-'} | {r['lastfm_playcount'] or '-'} | "
            f"`{r['split_state']}` |"
        )

    md_out = artifacts_dir / "phase6_signal_summary.md"
    md_out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[phase6:signals] Wrote {md_out}")


# ── Part B: Semantic Materialization ─────────────────────────────────────────

def _run_materialize(verbose: bool, signal_registry=None) -> int:
    from domains.music.tools.pipeline.materialization_runner import run_materialization

    print("[phase6:materialize] Running semantic materialization...")
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        summary = run_materialization(
            artifacts_dir=_ARTIFACTS_DIR,
            signal_registry=signal_registry,
            verbose=verbose,
        )
    except FileNotFoundError as e:
        print(f"[phase6:materialize] ERROR: {e}")
        return 1

    art = summary.get("artist_materialization", {})
    edg = summary.get("edge_materialization", {})
    print(f"\n[phase6:materialize] Artist materialization:")
    print(f"  Total artist keys:     {art.get('total_artist_keys', 0):,}")
    print(f"  Existing composers:    {art.get('existing_composers', 0):,}")
    print(f"  Resolved artists:      {art.get('resolved_artists', 0):,}")
    print(f"  Stub candidates:       {art.get('stub_candidates', 0):,}")
    print(f"\n[phase6:materialize] Edge materialization:")
    print(f"  Total edges:           {edg.get('total_edges', 0):,}")
    print(f"  APPEARED_ON edges:     {edg.get('appeared_on_edges', 0):,}")
    print(f"  FEATURED_ON edges:     {edg.get('featured_on_edges', 0):,}")
    print(f"  Resolved sources:      {edg.get('resolved_sources', 0):,}")
    print(f"  Unresolved sources:    {edg.get('unresolved_sources', 0):,}")
    print(f"\n[phase6:materialize] Artifacts in {_ARTIFACTS_DIR}")

    return 0


# ── Full run ──────────────────────────────────────────────────────────────────

def _run_full(verbose: bool) -> int:
    """Run Part A then Part B, passing signal registry to Part B."""
    from domains.music.tools.pipeline.signal_fuser import SignalFuser
    from domains.music.tools.pipeline.materialization_runner import run_materialization

    print("[phase6:full] Running Phase 6 Part A + Part B...")
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Part A
    fuser    = SignalFuser()
    registry = fuser.run(verbose=verbose)
    print(f"[phase6:full] Signal registry: {len(registry):,} tracks")

    # Part A artifacts (delegate to _run_signals-level logic, but we already
    # have the registry in memory — write a quick summary)
    summary_out = _ARTIFACTS_DIR / "phase6_signal_summary.json"
    if not summary_out.exists():
        # minimal summary write so materialize can reference it
        summary_out.write_text(
            json.dumps({"track_count": len(registry),
                        "generated_at": datetime.now(tz=timezone.utc).isoformat()},
                       indent=2),
            encoding="utf-8",
        )

    # Part B
    rc = _run_materialize(verbose, signal_registry=registry)
    if rc != 0:
        return rc

    print(f"\n[phase6:full] Phase 6 complete. Artifacts: {_ARTIFACTS_DIR}")
    return 0


# ── Beefweb ───────────────────────────────────────────────────────────────────

def _run_beefweb(verbose: bool) -> int:
    """Query Beefweb for live runtime state."""
    from domains.music.tools.pipeline.beefweb_client import BeefwebClient

    client = BeefwebClient()
    print("[phase6:beefweb] Checking Beefweb connectivity...")

    if not client.is_reachable():
        print("[phase6:beefweb] Beefweb not reachable at http://localhost:8880")
        print("  Make sure Foobar2000 is running and Beefweb Remote Control is enabled.")
        print("  (This is expected when Foobar is closed.)")
        return 0

    print("[phase6:beefweb] Connected.")

    np = client.now_playing()
    if np:
        state = np.get("state", "unknown")
        print(f"\n  Playback state: {state}")
        if state != "stopped":
            print(f"  Title:          {np.get('title')}")
            print(f"  Artist:         {np.get('artist')}")
            print(f"  Album:          {np.get('album')}")
            print(f"  Local playcount:{np.get('local_playcount')}")
            print(f"  Local loved:    {np.get('local_loved')}")
            print(f"  EPS first play: {np.get('first_played')}")
            print(f"  EPS last play:  {np.get('last_played')}")
            print(f"  EPS counter:    {np.get('play_counter')}")
            print(f"  Position:       {np.get('position_s'):.0f}s / {np.get('duration_s'):.0f}s")

    pls = client.playlists()
    if pls:
        print(f"\n  Playlists ({len(pls)}):")
        for pl in pls[:10]:
            active_mark = " [active]" if pl.get("isCurrent") else ""
            print(f"    {pl.get('title','?')} — {pl.get('itemCount','?')} items{active_mark}")

    return 0


# ── Report ────────────────────────────────────────────────────────────────────

def _run_report(verbose: bool) -> int:
    """Print a summary from existing phase6 artifacts."""
    if not _ARTIFACTS_DIR.exists():
        print(f"[phase6:report] No artifacts found at {_ARTIFACTS_DIR}")
        print("  Run --phase6 full first.")
        return 1

    artifacts = list(_ARTIFACTS_DIR.glob("*.json"))
    print(f"[phase6:report] Phase 6 artifacts ({len(artifacts)} files):")
    for f in sorted(artifacts):
        size_kb = f.stat().st_size // 1024
        print(f"  {f.name:<55} {size_kb:>6} KB")

    summary_path = _ARTIFACTS_DIR / "phase6_signal_summary.json"
    if summary_path.exists():
        s = json.loads(summary_path.read_text())
        print(f"\n  Generated at: {s.get('generated_at', '?')}")
        print(f"  Total tracks: {s.get('total_tracks', s.get('track_count', '?')):,}")

    mat_path = _ARTIFACTS_DIR / "semantic_materialization_report.json"
    if mat_path.exists():
        m = json.loads(mat_path.read_text())
        art = m.get("artist_materialization", {})
        edg = m.get("edge_materialization", {})
        if art:
            print(f"  Artist stubs:  {art.get('stub_candidates', '?'):,}")
        if edg:
            print(f"  Total edges:   {edg.get('total_edges', '?'):,}")

    return 0

