"""
semantic.py — Semantic query handler for the Helix Foobar Tool (Phase 5).

Exposes the domains/music/model/semantic/ query engine through the --semantic CLI.

Subcommands:
  featuring <artist>          All tracks featuring this artist
  collaborations <artist>     All collaborators of an artist (+optional partner)
  corpus <artist>             Full track corpus for an artist
  chip <chip> [--artist X]    Hardware-log tracks for a chip (+ optional artist)
  unresolved [--artist X]     Artist keys with no codex resolution
  loved [--artist X]          Loved tracks (optionally filtered to artist)
  summary                     Entity layer summary statistics

Usage (from runner.py --semantic):
  python -m applications.tools.foobar.runner --semantic featuring "Ashley Barrett"
  python -m applications.tools.foobar.runner --semantic collaborations "Darren Korb"
  python -m applications.tools.foobar.runner --semantic collaborations "Darren Korb" --partner "Ashley Barrett"
  python -m applications.tools.foobar.runner --semantic corpus "Masayuki Nagao"
  python -m applications.tools.foobar.runner --semantic chip YM2612 --artist "Masayuki Nagao"
  python -m applications.tools.foobar.runner --semantic unresolved
  python -m applications.tools.foobar.runner --semantic loved --artist "Darren Korb"
  python -m applications.tools.foobar.runner --semantic summary
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from domains.music.tools.pipeline.entity_layer import MusicEntityLayer
from domains.music.tools.pipeline.query_engine import SemanticQueryEngine, QueryResult


# ── Result formatter ──────────────────────────────────────────────────────────

def _print_result(result: QueryResult, verbose: bool = False, limit: int = 50) -> None:
    print(f"\n[semantic:{result.query_type}] {result.total} tracks")

    for w in result.warnings:
        print(f"  WARN: {w}")

    params_str = "  ".join(
        f"{k}={v!r}" for k, v in result.query_params.items() if v is not None
    )
    if params_str:
        print(f"  query: {params_str}")

    for key, val in result.metadata.items():
        if isinstance(val, dict):
            print(f"  {key}:")
            for k2, v2 in list(val.items())[:20]:
                print(f"    {k2}: {v2}")
            if len(val) > 20:
                print(f"    ... ({len(val) - 20} more)")
        elif isinstance(val, list):
            print(f"  {key}:")
            for item in val[:10]:
                print(f"    {item}")
            if len(val) > 10:
                print(f"    ... ({len(val) - 10} more)")
        else:
            print(f"  {key}: {val}")

    if result.track_ids:
        shown = result.track_ids[:limit]
        print(f"\n  tracks ({len(shown)} of {len(result.track_ids)} shown):")
        for tid in shown:
            print(f"    {tid}")
        if len(result.track_ids) > limit:
            print(f"    ... and {len(result.track_ids) - limit} more")


# ── Main handler ──────────────────────────────────────────────────────────────

def run_semantic(args: "argparse.Namespace") -> int:
    """
    Entry point called from runner.py when --semantic is specified.
    args.semantic_cmd   — subcommand (featuring | collaborations | corpus | chip | ...)
    args.semantic_arg   — primary positional argument
    args.partner        — secondary artist for collaborations
    args.artist         — optional artist filter
    args.limit          — output limit
    args.verbose        — verbose flag
    """
    cmd     = getattr(args, "semantic_cmd",  None)
    arg     = getattr(args, "semantic_arg",  None)
    partner = getattr(args, "partner",       None)
    artist  = getattr(args, "artist_filter", None)
    limit   = getattr(args, "limit",         50)
    verbose = getattr(args, "verbose",       False)

    if not cmd:
        print("[semantic] No subcommand given. Use: featuring | collaborations | corpus | chip | unresolved | loved | summary")
        return 1

    try:
        layer  = MusicEntityLayer.load()
        engine = SemanticQueryEngine(layer)
    except FileNotFoundError as e:
        print(f"[semantic] ERROR: {e}")
        print("  Run: python -m domains.music.probes.library_pipeline --index")
        return 1

    if cmd == "summary":
        s = layer.summary()
        print("\n[semantic:summary]")
        for k, v in s.items():
            print(f"  {k}: {v}")
        return 0

    if cmd == "featuring":
        if not arg:
            print("[semantic] featuring requires an artist name")
            return 1
        result = engine.featuring(arg)

    elif cmd == "collaborations":
        if not arg:
            print("[semantic] collaborations requires an artist name")
            return 1
        result = engine.collaborations(arg, partner)

    elif cmd == "corpus":
        if not arg:
            print("[semantic] corpus requires an artist name")
            return 1
        result = engine.corpus(arg)

    elif cmd == "chip":
        if not arg:
            print("[semantic] chip requires a chip name (e.g. YM2612)")
            return 1
        result = engine.chip_corpus(arg, artist)

    elif cmd == "unresolved":
        result = engine.unresolved(artist_filter=artist)

    elif cmd == "loved":
        result = engine.loved(artist)

    else:
        print(f"[semantic] Unknown subcommand: {cmd!r}")
        print("  Available: featuring | collaborations | corpus | chip | unresolved | loved | summary")
        return 1

    _print_result(result, verbose=verbose, limit=limit)
    return 0

