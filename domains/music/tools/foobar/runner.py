"""
runner.py — CLI entrypoint for the Helix Foobar Tool v0.

Two-root model:
  --library-root    C:\\Users\\dissonance\\Music
                    Live library/content root. Used for file discovery,
                    path reconciliation, album/track structure checks,
                    and corpus integrity.

  --runtime-root    C:\\Users\\dissonance\\AppData\\Roaming\\foobar2000-v2
                    Foobar application-state root. Used for reading
                    metadb.sqlite, config.sqlite, playlists, and other
                    runtime state sources. Read-only inspection only.
                    Never mutated.

Safety rules:
  - No Atlas writes
  - No direct Foobar SQLite mutation
  - No external tag rewriting (v0)
  - Patch plans are generated for operator review, not auto-applied

Usage:
  python -m applications.tools.foobar.runner --help
  python -m applications.tools.foobar.runner --audit
  python -m applications.tools.foobar.runner --sync
  python -m applications.tools.foobar.runner --report
  python -m applications.tools.foobar.runner --repair-plan
  python -m applications.tools.foobar.runner --lastfm
  python -m applications.tools.foobar.runner --report --lastfm
  python -m applications.tools.foobar.runner --phase4
  python -m applications.tools.foobar.runner --corpus --franchise "Sonic the Hedgehog" --expected-tracks 58
  python -m applications.tools.foobar.runner --query --franchise "Sonic" --loved
  python -m applications.tools.foobar.runner --query --platform "Mega Drive" --states schema_gap
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Default roots (from ingestion config — override via CLI args)
# ---------------------------------------------------------------------------

try:
    from domains.music.tools.music_pipeline.config import LIBRARY_ROOT, FOOBAR_APPDATA, DB_PATH
    _DEFAULT_LIBRARY_ROOT = str(LIBRARY_ROOT)
    _DEFAULT_RUNTIME_ROOT = str(FOOBAR_APPDATA)
    _DEFAULT_DB_PATH = str(DB_PATH)
except ImportError:
    _DEFAULT_LIBRARY_ROOT = r"C:\Users\dissonance\Music"
    _DEFAULT_RUNTIME_ROOT = r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2"
    _DEFAULT_DB_PATH = str(_REPO_ROOT / "domains" / "music" / "ingestion" / "data" / "helix_music.db")


# ---------------------------------------------------------------------------
# Core run function
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    library_root = Path(args.library_root)
    runtime_root = Path(args.runtime_root)
    db_path = Path(args.db_path) if args.db_path else None

    print(f"[foobar] Library corpus root : {library_root}")
    print(f"[foobar] Foobar runtime root  : {runtime_root}")

    # Validate roots
    if not library_root.exists():
        print(f"[foobar] WARNING: library root does not exist: {library_root}")
    if not runtime_root.exists():
        print(f"[foobar] WARNING: runtime root does not exist: {runtime_root}")

    # Lazy imports — keep startup fast
    from .sync import (
        compute_sync, load_codex_tracks, load_field_index, scan_foobar_library,
        query_tracks,
    )
    from .audit import (
        audit_corpus, audit_custom_schema, audit_library,
        audit_loved_stats, audit_release_structure,
    )
    from .reports import (
        print_summary, write_album_issues, write_audit_summary,
        write_codex_orphans, write_corpus_manifest, write_loved_drift,
        write_new_in_foobar, write_normalization_candidates,
        write_sync_manifest, write_track_issues,
    )
    from .repair_plan import (
        build_repair_plan, print_repair_plan_summary,
        write_repair_plan_csv, write_repair_plan_json,
    )

    # -----------------------------------------------------------------------
    # --health : quick status without full scan
    # -----------------------------------------------------------------------
    if args.health:
        from domains.music.tools.music_pipeline.track_db import TrackDB
        codex_path = db_path or Path(_DEFAULT_DB_PATH)
        print(f"\n[foobar] Health check")
        print(f"  Library root : {library_root}")
        print(f"  Runtime root : {runtime_root}")
        print(f"  Corpus root  : {library_root} {'(exists)' if library_root.exists() else '(MISSING)'}")

        # Runtime root artifacts
        metadb = runtime_root / "metadb.sqlite"
        field_index = _REPO_ROOT / "codex" / "library" / "music" / ".field_index.json"
        print(f"  metadb.sqlite: {'present' if metadb.exists() else 'not found'}")
        print(f"  field_index  : {'present' if field_index.exists() else 'not found'}")

        if codex_path.exists():
            try:
                db = TrackDB(codex_path)
                stats = db.stats()
                print(f"  TrackDB      : {stats['total_tracks']} tracks, "
                      f"{stats['loved_tracks']} loved, "
                      f"{stats['vectorized']} vectorized")
            except Exception as e:
                print(f"  TrackDB      : error ({e})")
        else:
            print(f"  TrackDB      : not found at {codex_path}")
        return 0

    # -----------------------------------------------------------------------
    # Data loading (shared across most commands)
    # -----------------------------------------------------------------------
    # --semantic is standalone — reads field index only, no library scan
    if getattr(args, "semantic", None) is not None:
        args.semantic_cmd = args.semantic
        from .semantic import run_semantic
        return run_semantic(args)

    # --phase6 is standalone — reads field index + signal sources, no library scan
    if getattr(args, "phase6", None) is not None:
        from .phase6 import run_phase6
        return run_phase6(args)

    needs_scan = any([
        args.audit, args.sync, args.report, args.repair_plan,
        args.corpus, args.query, args.phase4,
    ])
    needs_lastfm = getattr(args, "lastfm", False)

    # Last.fm standalone — does not require library scan
    if needs_lastfm and not needs_scan:
        _run_lastfm(args, foobar_records=[], codex_records={})
        return 0

    if not needs_scan:
        print("[foobar] No action specified. Use --help.")
        return 0

    print("[foobar] Loading codex track records...")
    codex_path = db_path or Path(_DEFAULT_DB_PATH)
    codex_records = load_codex_tracks(codex_path)

    print("[foobar] Scanning Foobar library...")
    # Pass runtime_root for metadb.sqlite lookup, library_root for filesystem scan
    from .sync import scan_foobar_library as _scan
    foobar_records = _scan_with_roots(library_root, runtime_root)

    if args.phase4:
        from .phase4 import run_phase4
        run_phase4(
            foobar_records=foobar_records,
            codex_records=codex_records,
            lastfm_path=getattr(args, "lastfm_path", None),
        )
        return 0

    print(f"[foobar] Computing sync state ({len(foobar_records)} Foobar, "
          f"{len(codex_records)} codex)...")
    sync_result = compute_sync(foobar_records, codex_records)

    # -----------------------------------------------------------------------
    # --sync : sync status only
    # -----------------------------------------------------------------------
    if args.sync:
        print_summary(sync_result, verbose=args.verbose)
        write_sync_manifest(sync_result)
        write_new_in_foobar(sync_result)
        write_codex_orphans(sync_result)
        print(f"[foobar] Written to: {Path(__file__).parent / 'artifacts'}")
        return 0

    # -----------------------------------------------------------------------
    # --query : filtered track view
    # -----------------------------------------------------------------------
    if args.query:
        states_filter = args.states.split(",") if args.states else None
        results = query_tracks(
            sync_result.get("track_results", []),
            franchise=args.franchise,
            platform=args.platform,
            sound_chip=args.sound_chip,
            sound_team=args.sound_team,
            loved=True if args.loved else None,
            states=states_filter,
            album=args.album,
        )
        print(f"\n[foobar] Query matched {len(results)} tracks")
        for tr in results[:args.limit]:
            fb = tr.get("foobar_record", {})
            from .diff import _norm
            title = _norm(fb.get("title")) or "(no title)"
            album = _norm(fb.get("album")) or "(no album)"
            platform = _norm(fb.get("platform")) or ""
            states = tr.get("states", [])
            print(f"  [{', '.join(states)}] {title} — {album} ({platform})")
        if len(results) > args.limit:
            print(f"  ... and {len(results) - args.limit} more. "
                  f"Use --limit N to see more.")
        return 0

    # -----------------------------------------------------------------------
    # --corpus : research corpus integrity check
    # -----------------------------------------------------------------------
    if args.corpus:
        corpus_result = audit_corpus(
            sync_result.get("track_results", []),
            franchise=args.franchise,
            album=args.album,
            expected_track_count=args.expected_tracks,
            corpus_name=args.corpus_name or (args.franchise or args.album or "corpus"),
        )
        status = corpus_result.get("status", "unknown")
        print(f"\n[foobar] Corpus: {corpus_result.get('corpus_name')}")
        print(f"  Status      : {status}")
        print(f"  Track count : {corpus_result.get('track_count')}")
        print(f"  In codex    : {corpus_result.get('in_codex')}")
        print(f"  Issues      : {corpus_result.get('issue_count')}")
        for iss in corpus_result.get("issues", []):
            print(f"  ⚠  [{iss['issue_code']}] {iss.get('detail', '')}")
        write_corpus_manifest(corpus_result)
        print(f"[foobar] Corpus manifest written to: "
              f"{Path(__file__).parent / 'artifacts'}")
        return 0

    # -----------------------------------------------------------------------
    # --audit / --report / --repair-plan : full run
    # -----------------------------------------------------------------------
    print("[foobar] Running library audit...")
    lib_audit = audit_library(sync_result.get("track_results", []))

    print("[foobar] Running custom schema audit...")
    schema_audit = audit_custom_schema(sync_result.get("track_results", []))

    print("[foobar] Running release structure audit...")
    struct_audit = audit_release_structure(sync_result.get("track_results", []))

    print("[foobar] Running loved/stats audit...")
    loved_audit = audit_loved_stats(sync_result.get("track_results", []))

    # Corpus checks (always run S3K if data is present, plus any --corpus args)
    corpus_results = []
    s3k_corpus = audit_corpus(
        sync_result.get("track_results", []),
        franchise="Sonic",
        album="Sonic the Hedgehog 3",
        expected_track_count=None,  # don't assert count unless explicitly passed
        corpus_name="S3K",
    )
    if s3k_corpus.get("track_count", 0) > 0:
        corpus_results.append(s3k_corpus)

    if args.franchise or args.album:
        if not (args.franchise == "Sonic"):  # avoid double-checking S3K
            user_corpus = audit_corpus(
                sync_result.get("track_results", []),
                franchise=args.franchise,
                album=args.album,
                expected_track_count=args.expected_tracks,
                corpus_name=args.corpus_name or (args.franchise or args.album),
            )
            corpus_results.append(user_corpus)

    print_summary(sync_result, verbose=args.verbose)

    if args.audit or args.report:
        # Write all artifacts
        write_sync_manifest(sync_result)
        write_new_in_foobar(sync_result)
        write_codex_orphans(sync_result)
        write_track_issues(lib_audit)
        write_album_issues(struct_audit)
        write_loved_drift(loved_audit)
        write_normalization_candidates(schema_audit)
        for cr in corpus_results:
            write_corpus_manifest(cr)

        path = write_audit_summary(
            sync_result, lib_audit, schema_audit, struct_audit, loved_audit,
            library_root=str(library_root),
            runtime_root=str(runtime_root),
            corpus_results=corpus_results,
        )
        print(f"[foobar] Audit summary: {path}")

    if args.repair_plan or args.report:
        print("[foobar] Building repair plan...")
        actions = build_repair_plan(
            sync_result, lib_audit, loved_audit, corpus_results,
        )
        csv_path = write_repair_plan_csv(actions)
        json_path = write_repair_plan_json(actions)
        print_repair_plan_summary(actions)
        print(f"[foobar] Repair plan: {csv_path}")

    # Last.fm reconciliation (append to full run if requested)
    if needs_lastfm:
        _run_lastfm(
            args,
            foobar_records=foobar_records,
            codex_records=codex_records,
        )

    return 0


# ---------------------------------------------------------------------------
# Last.fm action
# ---------------------------------------------------------------------------

def _run_lastfm(
    args: "argparse.Namespace",
    foobar_records: list[dict],
    codex_records: dict,
) -> None:
    """Run Last.fm trace reconciliation."""
    from .lastfm_reconciler import reconcile_lastfm, format_lastfm_summary_section
    from .reports import write_json, ARTIFACTS_DIR, _now_str
    from domains.music.tools.music_pipeline.adapters.lastfm import LastFmAdapter, DEFAULT_LASTFM_PATH

    lastfm_path = getattr(args, "lastfm_path", None) or DEFAULT_LASTFM_PATH
    adapter = LastFmAdapter(lastfm_path)

    if not adapter.available:
        print(f"[lastfm] WARNING: Last.fm JSON not found at {lastfm_path}")
        print(f"[lastfm] Set --lastfm-path or ingest the file to:")
        print(f"         {DEFAULT_LASTFM_PATH}")
        return

    adapter.load()
    stats = adapter.stats()
    print(f"[lastfm] {stats['total_scrobbles']:,} scrobbles | "
          f"{stats['unique_tracks']:,} unique tracks | "
          f"{stats['unique_artists']:,} artists")

    # Reconcile against library + codex
    # codex_records may be a list[dict] (from sync result) — normalize to dict
    if isinstance(codex_records, list):
        codex_map = {r.get("file_path", str(i)): r for i, r in enumerate(codex_records)}
    else:
        codex_map = codex_records

    print("[lastfm] Reconciling against library and codex...")
    result = reconcile_lastfm(
        adapter, foobar_records, codex_map,
        top_n_tracks=getattr(args, "lastfm_top_n", 500),
    )

    # Write artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Match report
    match_report_path = write_json("lastfm_match_report.json", {
        "generated": _now_str(),
        "username": result["username"],
        "total_scrobbles": result["total_scrobbles"],
        "total_unique_tracks": result["total_unique_tracks"],
        "tracks_analyzed": result["tracks_analyzed"],
        "summary": result["summary"],
        "alias_candidates": result["alias_candidates"],
        "ambiguous": result["ambiguous"],
    })

    # Unmatched
    write_json("unmatched_lastfm_history.json", {
        "generated": _now_str(),
        "count": len(result["unmatched_sample"]),
        "note": "Sample of 200 unmatched low-play scrobbles",
        "entries": result["unmatched_sample"],
    })

    # High-signal missing
    write_json("high_signal_missing_library.json", {
        "generated": _now_str(),
        "count": len(result["high_signal_missing"]),
        "threshold_plays": 5,
        "entries": result["high_signal_missing"],
    })

    # Priority cleanup
    write_json("priority_cleanup_candidates.json", {
        "generated": _now_str(),
        "count": len(result["priority_cleanup"]),
        "entries": result["priority_cleanup"],
    })

    # Active listening corpus
    write_json("active_listening_corpus.json", {
        "generated": _now_str(),
        "top_albums_analyzed": len(result["active_corpus"]),
        "albums": result["active_corpus"],
    })

    # Ingest candidates
    write_json("priority_ingest_candidates.json", {
        "generated": _now_str(),
        "count": len(result["priority_ingest"]),
        "entries": result["priority_ingest"],
    })

    # Last.fm summary markdown
    lines = [
        "# Helix Foobar Tool — Last.fm Trace Reconciliation",
        f"Generated: {_now_str()}",
        f"Source: `{lastfm_path}`",
        "",
        "---",
        "",
        f"## Library Stats",
        f"- Username: @{result['username']}",
        f"- Total scrobbles: {result['total_scrobbles']:,}",
        f"- Unique tracks: {result['total_unique_tracks']:,}",
        f"- Top tracks analyzed: {result['tracks_analyzed']}",
        "",
        "## Match Summary",
        "| State | Count |",
        "|-------|-------|"]
    for k, v in sorted(result["summary"].items(), key=lambda x: -x[1]):
        lines.append(f"| `{k}` | {v} |")

    lines += ["", "## Output Artifacts",
        "| File | Contents |",
        "|------|----------|",
        "| `lastfm_match_report.json` | Full match classification |",
        "| `unmatched_lastfm_history.json` | Unmatched low-play scrobbles |",
        "| `high_signal_missing_library.json` | High-play tracks not in library |",
        "| `priority_cleanup_candidates.json` | High-signal tracks with schema gaps |",
        "| `active_listening_corpus.json` | Top albums by listen count + coverage |",
        "| `priority_ingest_candidates.json` | High-play tracks not in codex |",
    ]

    summary_path = ARTIFACTS_DIR / "lastfm_ingest_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[lastfm] Summary: {summary_path}")
    print(f"[lastfm] Artifacts written to: {ARTIFACTS_DIR}")
    s = result["summary"]
    print(f"  matched_to_library          : {s.get('matched_to_library', 0)}")
    print(f"  high_signal_missing         : {s.get('missing_from_library_high_signal', 0)}")
    print(f"  priority_cleanup_candidates : {s.get('priority_cleanup_candidates', 0)}")
    print(f"  priority_ingest_candidates  : {s.get('priority_ingest_candidates', 0)}")
    print(f"  unmatched                   : {s.get('unmatched', 0)}")


# ---------------------------------------------------------------------------
# Two-root scan helper
# ---------------------------------------------------------------------------

def _scan_with_roots(library_root: Path, runtime_root: Path) -> list[dict]:
    """
    Scan Foobar library using the two-root model.
    Runtime root → metadb.sqlite (richer, faster).
    Library root → filesystem scan fallback.
    """
    records = []

    # Try runtime root metadb.sqlite first
    metadb_path = runtime_root / "metadb.sqlite"
    if metadb_path.exists():
        try:
            from domains.music.tools.music_pipeline.adapters.metadb_sqlite import MetadbSqliteReader
            reader = MetadbSqliteReader(str(metadb_path))
            raw = reader.read_all()
            records = [reader.normalize(r) for r in raw]
            print(f"[foobar] metadb.sqlite (runtime root): {len(records)} tracks")
            return records
        except Exception as e:
            print(f"[foobar] metadb.sqlite error ({e}), falling back to filesystem scan")

    # Library root filesystem scan
    try:
        from domains.music.tools.music_pipeline.adapters.foobar import FoobarAdapter
        adapter = FoobarAdapter(str(library_root))
        tracks = adapter.scan()
        for t in tracks:
            records.append({
                "file_path": t.file_paths[0] if t.file_paths else None,
                "title": t.canonical_title,
                "artist": t.canonical_artist,
                "album": t.album,
                "platform": t.platform,
                "format": t.format_type,
                "loved": getattr(t, "is_love", False),
            })
        print(f"[foobar] Filesystem scan (library root): {len(records)} tracks")
    except Exception as e:
        print(f"[foobar] ERROR: could not scan library: {e}")

    return records


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foobar_tool",
        description=(
            "Helix Foobar Tool v0 — Library audit, sync, diff, and repair planning.\n"
            "Read-only against Foobar internals. Patch-plan first."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Root configuration
    roots = parser.add_argument_group("roots")
    roots.add_argument(
        "--library-root",
        default=_DEFAULT_LIBRARY_ROOT,
        metavar="PATH",
        help=f"Music library corpus root (default: {_DEFAULT_LIBRARY_ROOT})",
    )
    roots.add_argument(
        "--runtime-root",
        default=_DEFAULT_RUNTIME_ROOT,
        metavar="PATH",
        help=f"Foobar runtime/config root for metadb.sqlite etc. (default: {_DEFAULT_RUNTIME_ROOT})",
    )
    roots.add_argument(
        "--db-path",
        default=None,
        metavar="PATH",
        help="Override TrackDB path (default: from ingestion config)",
    )

    # Primary actions
    actions = parser.add_argument_group("actions")
    actions.add_argument("--health",      action="store_true", help="Quick health check (no scan)")
    actions.add_argument("--sync",        action="store_true", help="Sync status: new, stale, orphaned, in_sync")
    actions.add_argument("--audit",       action="store_true", help="Full library audit (all checks + artifacts)")
    actions.add_argument("--report",      action="store_true", help="Full report (audit + repair plan)")
    actions.add_argument("--repair-plan", action="store_true", help="Generate repair plan only")
    actions.add_argument("--corpus",      action="store_true", help="Research corpus integrity check")
    actions.add_argument("--query",       action="store_true", help="Filtered track query")
    actions.add_argument("--lastfm",      action="store_true",
                         help="Last.fm trace reconciliation (match, signal, cleanup)")
    actions.add_argument("--lastfm-path", metavar="PATH", default=None,
                         help="Override Last.fm JSON path from a local archive extraction or configured bridge")
    actions.add_argument("--lastfm-top-n", type=int, default=500, metavar="N",
                         help="Top N tracks to classify in Last.fm reconciliation (default: 500)")
    actions.add_argument("--semantic",     nargs="?", const="summary", metavar="CMD",
                         help="Semantic query: featuring | collaborations | corpus | chip | unresolved | loved | summary")
    actions.add_argument("--semantic-arg",    dest="semantic_arg",    metavar="ARG",  default=None,
                         help="Primary argument for --semantic (artist name, chip name, etc.)")
    actions.add_argument("--partner",         metavar="ARTIST", default=None,
                         help="Secondary artist for --semantic collaborations")
    actions.add_argument("--artist-filter",   dest="artist_filter",   metavar="ARTIST", default=None,
                         help="Artist filter for --semantic chip / unresolved / loved")
    actions.add_argument("--phase6",      nargs="?", const="full", metavar="CMD",
                         help="Phase 6: signals | materialize | full | beefweb | report")
    actions.add_argument("--phase4",      action="store_true",
                         help="Run full Phase 4 trace fusion, validation, and refresh planning pipeline")

    # Filters / corpus config
    filters = parser.add_argument_group("filters and corpus")
    filters.add_argument("--franchise",       metavar="NAME",  help="Filter/target by franchise name")
    filters.add_argument("--album",           metavar="NAME",  help="Filter/target by album name")
    filters.add_argument("--platform",        metavar="NAME",  help="Filter by platform")
    filters.add_argument("--sound-chip",      metavar="CHIP",  help="Filter by sound chip")
    filters.add_argument("--sound-team",      metavar="TEAM",  help="Filter by sound team")
    filters.add_argument("--loved",           action="store_true", help="Filter to loved tracks only")
    filters.add_argument("--states",          metavar="S1,S2", help="Filter by sync states (comma-separated)")
    filters.add_argument("--expected-tracks", type=int, metavar="N",
                         help="Expected track count for corpus check")
    filters.add_argument("--corpus-name",     metavar="NAME",  help="Name for corpus in reports")
    filters.add_argument("--limit",           type=int, default=50,
                         help="Max tracks to show in query output (default: 50)")

    # Output options
    out = parser.add_argument_group("output")
    out.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()

