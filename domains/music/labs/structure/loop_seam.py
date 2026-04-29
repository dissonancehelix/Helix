"""
Loop-Seam Probe — domains/music/model/analysis/loop_seam.py
======================================================
Detects and ranks loop-seam / circular-return candidates
in the Spotify music library using DCP event machinery.

WHAT IS A LOOP-SEAM?
A loop-seam is the structural moment where a musical trajectory
returns to a previously established state — the seam where the
loop closes. In VGM, this is a literal loop point. In composed
music, it is the phrase- or section-level return event that
collapses the developing trajectory back into a known state.

In DCP terms:
  - Possibility space: the breadth of structural direction
    the music was moving toward before the return
  - Constraint: compositional structure forcing eventual return
  - Tension: harmonic / rhythmic pressure before the seam
  - Compression event: the seam itself — where the return lands
  - Post-collapse: the re-established, narrower known state

WHAT THIS PROBE DOES:
  1. Loads the Spotify library
  2. Emits a DCPEvent for each track via the music DCP hook
  3. Ranks tracks by "loop-seam candidacy" — a score estimating
     which tracks are most likely to exhibit measurable loop-seam
     events if their audio is analyzed
  4. Exports a ranked candidate list for audio follow-up
  5. Emits a DCP candidate report connecting to core invariant tracking

WHAT THIS PROBE CANNOT DO:
  - Detect actual loop-seam events (requires audio waveform)
  - Measure collapse sharpness (no time-series data from Spotify)
  - Verify post-seam narrowing (no structural analysis from metadata)

The output of this probe is:
  > a prioritized work list for audio-level DCP loop-seam analysis

Usage:
    python -m domains.music.analysis.loop_seam
    python -m domains.music.analysis.loop_seam --top-n 50 --output-dir <path>

Architecture:
    This probe lives in the music DOMAIN (not labs) because it
    defines a reusable detection interface, not a one-off experiment.
    Experiment runs and outputs go to domains/music/model/outputs/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists()
)
sys.path.insert(0, str(ROOT))

from core.invariants.dcp.event import DCPEvent
from model.domains.music.analysis.dcp import extract_dcp_event_from_spotify

SPOTIFY_JSON = ROOT / "domains/music/data/library/metadata/spotify.json"
DEFAULT_OUT  = ROOT / "domains/music/model/outputs/loop_seam_probe"


# ─── Candidacy scoring ────────────────────────────────────────────────────────
#
# A track is a strong loop-seam candidate if it exhibits:
#   HIGH  instrumentalness  → clear structural skeleton (no lyrics masking seams)
#   HIGH  energy            → active trajectory before the seam
#   LOW   valence           → tension-bearing state (likely pre-resolution)
#   LOW   liveness          → tightly produced → structural seams are intentional
#   HIGH  danceability      → rhythmic regularity → seam lands on grid
#   LOW   speechiness       → not word-driven → structure carries meaning
#
# This aligns with the DCP prediction: high-candidacy tracks have a richer
# possibility space (energy + instrumentalness) under constraint (low liveness)
# with tension (low valence) — exactly the pre-collapse setup.
#
# The candidacy score weights these with DCP logic, not just heuristic.
# It is NOT the DCP event score — it is a "worth analyzing audio" rating.

def compute_loop_seam_candidacy(event: DCPEvent, track: dict) -> float:
    """
    Score how likely this track is to exhibit a detectable loop-seam event
    in audio analysis. Higher = more valuable audio candidate.

    Components (all [0,1]):
      - tension * constraint (DCP pre-collapse setup)
      - instrumentalness (structural skeleton clarity)
      - danceability (rhythmic grid = seam landing zone)
      - inverted speechiness (not word-masked)
      - post_collapse_narrowing proxy (seam has a target state to collapse into)
    """
    tension    = event.tension_proxy or 0.0
    constraint = event.constraint_proxy or 0.0
    post_narrow = event.post_collapse_narrowing or 0.0

    instr    = float(track.get("Instrumentalness") or 0)
    dance    = float(track.get("Danceability") or 0)
    speech   = float(track.get("Speechiness") or 0)

    score = (
        0.30 * tension * constraint     +  # DCP pre-collapse setup
        0.25 * instr                    +  # structural skeleton
        0.20 * post_narrow              +  # narrowing toward known state
        0.15 * dance                    +  # rhythmic grid
        0.10 * (1.0 - speech)           # not word-masked
    )
    return float(np.clip(score, 0.0, 1.0))


# ─── Main probe ───────────────────────────────────────────────────────────────

def run_probe(top_n: int = 100, output_dir: Path = DEFAULT_OUT) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading Spotify library: {SPOTIFY_JSON}")
    with open(SPOTIFY_JSON, encoding="utf-8") as f:
        library = json.load(f)
    print(f"  {len(library)} tracks")

    # Emit DCP events and score candidacy
    print("Scoring loop-seam candidacy…")
    candidates = []
    for track in library:
        try:
            event = extract_dcp_event_from_spotify(track)
            candidacy = compute_loop_seam_candidacy(event, track)
            candidates.append({
                "track_name":    track.get("Track Name", ""),
                "artist":        track.get("Artist Name(s)", ""),
                "track_uri":     track.get("Track URI", ""),
                "candidacy_score": round(candidacy, 4),
                "dcp_confidence":  round(event.confidence, 4),
                "dcp_composite":   round(event.domain_metadata.get("dcp_composite", 0), 4),
                "qualification":   event.qualification_status(),
                "tension_proxy":   round(event.tension_proxy or 0, 4),
                "constraint_proxy": round(event.constraint_proxy or 0, 4),
                "post_narrowing":  round(event.post_collapse_narrowing or 0, 4),
                "instrumentalness": round(float(track.get("Instrumentalness") or 0), 4),
                "energy":          round(float(track.get("Energy") or 0), 4),
                "valence":         round(float(track.get("Valence") or 0), 4),
                "danceability":    round(float(track.get("Danceability") or 0), 4),
                "tempo":           round(float(track.get("Tempo") or 0), 2),
                "dcp_event_id":    event.event_id,
            })
        except Exception as e:
            continue

    # Sort by candidacy score
    candidates.sort(key=lambda x: x["candidacy_score"], reverse=True)
    top_candidates = candidates[:top_n]

    # Qualification summary
    qual_counts: dict[str, int] = {}
    for c in candidates:
        q = c["qualification"]
        qual_counts[q] = qual_counts.get(q, 0) + 1

    # ── DCP candidate report ──────────────────────────────────────────────────
    # This is the Helix-native output — connects loop-seam detection to
    # the DCP invariant tracking system.
    dcp_report = {
        "probe": "loop_seam",
        "domain": "music",
        "source": str(SPOTIFY_JSON.relative_to(ROOT)),
        "total_tracks_scored": len(candidates),
        "qualification_summary": qual_counts,
        "note": (
            "All events have qualification_status UNCONFIRMED — "
            "collapse_proxy is None for all tracks because loop-seam "
            "sharpness cannot be measured from Spotify metadata. "
            "Top candidates below are prioritized for audio-level analysis."
        ),
        "dcp_invariant_ref": "codex/library/invariants/decision_compression_principle.yaml",
        "next_step": (
            "Run audio-level loop-seam detection on top-N candidates. "
            "Use onset detection + structural segmentation to find seam events. "
            "Emit full DCPEvents with collapse_proxy filled from waveform data."
        ),
        "top_candidates": top_candidates,
    }

    # ── Exports ───────────────────────────────────────────────────────────────
    report_path = output_dir / "loop_seam_dcp_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(dcp_report, f, indent=2)
    print(f"  DCP report: {report_path}")

    # CSV for inspection
    try:
        import csv
        csv_path = output_dir / "loop_seam_candidates.csv"
        if top_candidates:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(top_candidates[0].keys()))
                writer.writeheader()
                writer.writerows(top_candidates)
        print(f"  CSV: {csv_path}")
    except Exception:
        pass

    # ── Print top 20 ─────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"TOP 20 LOOP-SEAM CANDIDATES (of {len(candidates)} scored)")
    print(f"{'='*70}")
    print(f"{'Score':>6}  {'Tension':>7}  {'Instr':>5}  {'Artist':<28}  Track")
    print(f"{'-'*6}  {'-'*7}  {'-'*5}  {'-'*28}  {'-'*30}")
    for c in top_candidates[:20]:
        artist = c["artist"][:27]
        track  = c["track_name"][:30]
        print(
            f"{c['candidacy_score']:>6.4f}  "
            f"{c['tension_proxy']:>7.4f}  "
            f"{c['instrumentalness']:>5.3f}  "
            f"{artist:<28}  {track}"
        )

    print(f"\nQualification summary (all {len(candidates)} tracks):")
    for q, count in sorted(qual_counts.items()):
        print(f"  {q}: {count}")

    print(f"\nOutputs: {output_dir}")
    return dcp_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Loop-seam DCP probe — ranks Spotify library tracks for audio analysis."
    )
    parser.add_argument("--top-n",     type=int,  default=100)
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    out = Path(args.output_dir) if args.output_dir else DEFAULT_OUT
    run_probe(top_n=args.top_n, output_dir=out)


