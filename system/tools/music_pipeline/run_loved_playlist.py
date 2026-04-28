"""
loved.m3u8 Runner — model/domains/music/run_loved_playlist.py
=============================================================
Reads the loved.m3u8 playlist and runs the full codec pipeline
on every file, generating a unified TrackAnalysis JSON report.

Usage:
    python model/domains/music/run_loved_playlist.py
    python model/domains/music/run_loved_playlist.py --limit 10
    python model/domains/music/run_loved_playlist.py --formats vgm spc
    python model/domains/music/run_loved_playlist.py --out my_report.json

Wait for the GO from the user before running.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add Helix root to path
_HELIX_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(_HELIX_ROOT))

from model.domains.music.analysis.codec_pipeline import analyze

# ---------------------------------------------------------------------------
# M3U8 reader
# ---------------------------------------------------------------------------

def read_m3u8(playlist_path: Path) -> list[Path]:
    """
    Parse an M3U8 file and return a list of absolute file paths.
    Handles both absolute and relative paths. Skips comment lines.
    Skips files that don't exist on disk.
    """
    paths: list[Path] = []
    try:
        lines = playlist_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        print(f"ERROR: Cannot read playlist {playlist_path}: {e}")
        return []

    playlist_dir = playlist_path.parent

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = Path(line)
        if not p.is_absolute():
            p = (playlist_dir / p).resolve()
        if p.exists():
            paths.append(p)
        else:
            print(f"  SKIP (not found): {p.name}", flush=True)

    return paths


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def _format_summary(results: list[dict]) -> str:
    """Generate a human-readable summary of analysis results."""
    total = len(results)
    errors = sum(1 for r in results if r.get("error"))
    by_format: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    symbolic_count = 0
    loved_count = 0
    loop_count = 0

    for r in results:
        fmt = r.get("format", "?")
        tier = r.get("analysis_tier", "?")
        by_format[fmt] = by_format.get(fmt, 0) + 1
        by_tier[tier]  = by_tier.get(tier, 0) + 1
        if r.get("symbolic"):
            symbolic_count += 1
        if r.get("library_is_loved"):
            loved_count += 1
        if r.get("has_loop"):
            loop_count += 1

    lines = [
        "",
        "=" * 60,
        "  HELIX MUSIC ANALYSIS — LOVED PLAYLIST REPORT",
        "=" * 60,
        f"  Total tracks:        {total}",
        f"  Errors:              {errors}",
        f"  Loved (library):     {loved_count}",
        f"  Has loop point:      {loop_count}",
        f"  Symbolic (Tier D):   {symbolic_count}",
        "",
        "  By format:",
    ]
    for fmt, count in sorted(by_format.items(), key=lambda x: -x[1]):
        lines.append(f"    {fmt:<12} {count}")
    lines.append("")
    lines.append("  By analysis tier:")
    for tier, count in sorted(by_tier.items(), key=lambda x: -x[1]):
        tier_desc = {
            "A":    "Native chip parse (snapshot)",
            "A+":   "Native parse + note events",
            "A+D":  "Native parse + symbolic MIDI",
            "A+C":  "Native parse + waveform",
            "C":    "Waveform only",
            "error":"Failed",
        }.get(tier, tier)
        lines.append(f"    {tier:<8} {count:>4}  ({tier_desc})")
    lines.append("")

    # Music theory highlights (if symbolic data available)
    modes: dict[str, int] = {}
    contours: dict[str, int] = {}
    arcs: dict[str, int] = {}
    for r in results:
        sf = r.get("symbolic") or {}
        full = (r.get("library_meta") or {}).get("symbolic_full") or {}
        mode = full.get("scale_mode") or sf.get("scale_mode", "")
        contour = full.get("melodic_contour", "")
        arc = full.get("dynamic_arc", "")
        if mode: modes[mode] = modes.get(mode, 0) + 1
        if contour: contours[contour] = contours.get(contour, 0) + 1
        if arc: arcs[arc] = arcs.get(arc, 0) + 1

    if modes:
        lines.append("  Scale modes detected:")
        for m, c in sorted(modes.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"    {m:<16} {c}")
        lines.append("")

    if contours:
        lines.append("  Melodic contours:")
        for c, n in sorted(contours.items(), key=lambda x: -x[1]):
            lines.append(f"    {c:<16} {n}")
        lines.append("")

    if arcs:
        lines.append("  Dynamic arcs:")
        for a, n in sorted(arcs.items(), key=lambda x: -x[1]):
            lines.append(f"    {a:<16} {n}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEFAULT_PLAYLIST = r"C:\Users\dissonance\Desktop\loved.m3u8"
DEFAULT_OUTPUT   = str(_HELIX_ROOT / "data" / "music" / "loved_analysis.json")
DEFAULT_SUMMARY  = str(_HELIX_ROOT / "data" / "music" / "loved_analysis_summary.txt")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze the loved.m3u8 playlist through the Helix codec pipeline."
    )
    parser.add_argument(
        "--playlist", default=DEFAULT_PLAYLIST,
        help=f"Path to M3U8 playlist (default: {DEFAULT_PLAYLIST})"
    )
    parser.add_argument(
        "--out", default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--summary", default=DEFAULT_SUMMARY,
        help="Output path for human-readable summary"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Analyze only the first N files (for testing)"
    )
    parser.add_argument(
        "--formats", nargs="*", default=None,
        help="Only analyze these formats (e.g. --formats vgm spc mp3)"
    )
    parser.add_argument(
        "--skip-errors", action="store_true",
        help="Continue on errors, include error records in output"
    )
    args = parser.parse_args()

    playlist_path = Path(args.playlist)
    if not playlist_path.exists():
        print(f"ERROR: Playlist not found: {playlist_path}")
        sys.exit(1)

    print(f"Reading playlist: {playlist_path}")
    all_paths = read_m3u8(playlist_path)
    print(f"  Found {len(all_paths)} files on disk")

    # Filter by format if requested
    if args.formats:
        fmt_exts = {f".{f.lower().lstrip('.')}" for f in args.formats}
        all_paths = [p for p in all_paths if p.suffix.lower() in fmt_exts]
        print(f"  Filtered to {len(all_paths)} files matching formats: {args.formats}")

    # Limit
    if args.limit:
        all_paths = all_paths[:args.limit]
        print(f"  Limiting to first {args.limit} files")

    if not all_paths:
        print("No files to analyse.")
        sys.exit(0)

    print(f"\nStarting analysis of {len(all_paths)} tracks...\n")

    results: list[dict] = []
    t_start = time.time()

    for i, path in enumerate(all_paths):
        t0 = time.time()
        print(f"[{i+1:>4}/{len(all_paths)}] {path.name}", end=" ", flush=True)

        try:
            analysis = analyze(path)
            d = analysis.to_dict()
            results.append(d)
            tier = d.get("analysis_tier", "?")
            sym  = "✓MIDI" if d.get("symbolic") else ""
            loop = "⟳" if d.get("has_loop") else ""
            err  = f" ERROR: {d['error'][:40]}" if d.get("error") else ""
            elapsed = time.time() - t0
            print(f"  [{tier}] {sym}{loop}{err}  ({elapsed:.1f}s)", flush=True)
        except Exception as e:
            print(f"  FAILED: {e}", flush=True)
            if not args.skip_errors:
                raise

    total_time = time.time() - t_start
    print(f"\nCompleted {len(results)} tracks in {total_time:.1f}s "
          f"({total_time / max(1, len(results)):.1f}s avg)")

    # Write JSON output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"JSON output: {out_path}")

    # Write summary
    summary = _format_summary(results)
    print(summary)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()

