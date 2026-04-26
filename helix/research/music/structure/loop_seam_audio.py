"""
Loop-Seam Audio Probe — domains/music/analysis/loop_seam_audio.py
==================================================================
Processes Spotify audio-analysis data to produce real DCP events
with collapse_proxy filled from actual waveform/structure data.

This is the audio-level complement to loop_seam.py (metadata probe).

What this adds over the metadata probe:
  - Section boundary sharpness → collapse_proxy (FILLED, not None)
  - Multi-section seam detection → multiple DCPEvents per track
  - Pre-seam tension from segment loudness accumulation
  - Post-seam narrowing from section stability after boundary

DCP event interpretation:
  A section boundary in a structured track is a candidate DCP event:
  - The developing trajectory of the track (pre-boundary features)
    collapses into the post-boundary state at the seam.
  - High boundary sharpness = clean compression event.
  - Circular return = the post-boundary state matches an earlier state.

Requires:
  - Cached audio analysis files from spotify_audio_analysis.py
  - loop_seam_candidates.csv from loop_seam.py

Usage:
    python -m domains.music.analysis.loop_seam_audio
    python -m domains.music.analysis.loop_seam_audio --min-sharpness 0.4
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists()
)
sys.path.insert(0, str(ROOT))

from core.invariants.dcp.event import DCPEvent
from core.invariants.dcp.metrics import compute_dcp_score

ANALYSIS_CACHE = ROOT / "domains/music/data/music/processed/audio_analysis"
CANDIDATES_CSV = ROOT / "domains/music/outputs/loop_seam_probe/loop_seam_candidates.csv"
OUTPUT_DIR     = ROOT / "domains/music/outputs/loop_seam_audio"


# ═══════════════════════════════════════════════════════════════════════════════
# Section boundary metrics
# ═══════════════════════════════════════════════════════════════════════════════

def section_boundary_sharpness(prev: dict, curr: dict) -> float:
    """
    Measure how sharply a track changes at a section boundary.

    Combines:
      - Loudness delta (normalised to typical range)
      - Tempo delta (normalised)
      - Key change (binary)
      - Mode change (binary)

    Returns 0–1. Higher = sharper / more compressed transition.
    """
    loudness_delta = abs(curr.get("loudness", 0) - prev.get("loudness", 0))
    loudness_score = min(1.0, loudness_delta / 12.0)   # 12 dB = full range

    tempo_prev = prev.get("tempo", 120.0) or 120.0
    tempo_curr = curr.get("tempo", 120.0) or 120.0
    tempo_delta = abs(tempo_curr - tempo_prev) / max(tempo_prev, 1.0)
    tempo_score = min(1.0, tempo_delta * 3.0)           # 33% change = max

    key_change  = 1.0 if curr.get("key") != prev.get("key") else 0.0
    mode_change = 0.5 if curr.get("mode") != prev.get("mode") else 0.0

    sharpness = (
        0.45 * loudness_score +
        0.25 * tempo_score    +
        0.20 * key_change     +
        0.10 * mode_change
    )
    return float(min(1.0, sharpness))


def is_circular_return(sections: list[dict], idx: int, window: int = 3) -> float:
    """
    Score how much section[idx] resembles an earlier section —
    the circular-return / loop-seam signature.

    Compares loudness and tempo of section[idx] against earlier sections.
    Returns 0–1. Higher = stronger circular return.
    """
    if idx < 2:
        return 0.0

    current = sections[idx]
    best_match = 0.0

    # Look back at sections before the immediately preceding one
    for j in range(max(0, idx - window - 1), idx - 1):
        prev = sections[j]
        loudness_sim = 1.0 - min(1.0,
            abs(current.get("loudness", 0) - prev.get("loudness", 0)) / 12.0
        )
        tempo_this = current.get("tempo", 120.0) or 120.0
        tempo_ref  = prev.get("tempo", 120.0) or 120.0
        tempo_sim  = 1.0 - min(1.0,
            abs(tempo_this - tempo_ref) / max(tempo_ref, 1.0) * 3.0
        )
        key_sim  = 1.0 if current.get("key")  == prev.get("key")  else 0.0
        mode_sim = 1.0 if current.get("mode") == prev.get("mode") else 0.0

        match = (
            0.35 * loudness_sim +
            0.25 * tempo_sim    +
            0.25 * key_sim      +
            0.15 * mode_sim
        )
        best_match = max(best_match, match)

    return float(best_match)


def pre_seam_tension(sections: list[dict], idx: int) -> float:
    """
    Estimate tension accumulation before the seam at idx.
    Uses the trend in loudness across the preceding section.
    A section that is loud + long before a sudden drop = high tension.
    Returns 0–1.
    """
    if idx < 1:
        return 0.0
    prev = sections[idx - 1]
    loudness = prev.get("loudness", -20.0)
    duration = prev.get("duration", 0.0)

    # Loud + long pre-seam section = high tension proxy
    loudness_score = min(1.0, (loudness + 25.0) / 20.0)  # norm: -25 to -5 dB
    duration_score = min(1.0, duration / 60.0)             # norm: 0 to 60s
    return float(0.6 * loudness_score + 0.4 * duration_score)


def post_seam_narrowing(sections: list[dict], idx: int) -> float:
    """
    How much does the track narrow (stabilise) after the seam?
    Measured by feature consistency of the post-seam section.
    Uses duration as a proxy for stability (longer post-seam = more settled).
    Returns 0–1.
    """
    if idx >= len(sections):
        return 0.0
    curr = sections[idx]
    duration_score = min(1.0, curr.get("duration", 0.0) / 60.0)
    return float(duration_score)


# ═══════════════════════════════════════════════════════════════════════════════
# DCP event extractor
# ═══════════════════════════════════════════════════════════════════════════════

def extract_dcp_events_from_analysis(
    track_record: dict,
    analysis: dict,
    min_sharpness: float = 0.3,
) -> list[DCPEvent]:
    """
    Extract DCP events from a Spotify audio-analysis response.
    Each significant section boundary is a candidate DCP event.

    Returns a list of DCPEvents, one per qualifying boundary.
    Events are sorted by collapse_proxy (sharpness) descending.
    """
    sections = analysis.get("sections", [])
    if len(sections) < 2:
        return []

    track_uri  = track_record.get("track_uri", "")
    track_id   = track_uri.split(":")[-1]
    track_name = track_record.get("track_name", "unknown")
    artist     = track_record.get("artist", "unknown")

    events: list[DCPEvent] = []

    for i in range(1, len(sections)):
        prev = sections[i - 1]
        curr = sections[i]

        sharpness        = section_boundary_sharpness(prev, curr)
        circular_return  = is_circular_return(sections, i)
        tension          = pre_seam_tension(sections, i)
        narrowing        = post_seam_narrowing(sections, i)

        # Only emit events above min_sharpness threshold
        if sharpness < min_sharpness:
            continue

        # Possibility space: how many distinct sections precede this boundary?
        n_prior = i
        possibility_space = min(1.0, n_prior / 8.0)

        # Constraint: estimated from track structure density
        # (more sections = more constrained composition)
        constraint = min(1.0, len(sections) / 10.0)

        dcp_score = compute_dcp_score(
            possibility_space=possibility_space,
            constraint=constraint,
            tension=tension,
            collapse=sharpness,
            post_narrowing=narrowing,
        )
        confidence = float(min(0.80, dcp_score * 0.90))

        seam_time = curr.get("start", 0.0)
        event_id  = f"music.loopseam.{track_id}.section_{i}"

        event = DCPEvent(
            source_domain="music",
            source_artifact=f"audio_analysis:{track_uri}",
            event_id=event_id,
            possibility_space_proxy=possibility_space,
            constraint_proxy=constraint,
            tension_proxy=tension,
            collapse_proxy=sharpness,          # NOW FILLED from real audio data
            post_collapse_narrowing=narrowing,
            confidence=confidence,
            calibration_status="provisional",
            notes=(
                f"Track: '{track_name}' by {artist}. "
                f"Section boundary {i-1}→{i} at {seam_time:.1f}s. "
                f"Sharpness={sharpness:.3f}. "
                f"Circular return score={circular_return:.3f}. "
                f"Qualification: {'' if sharpness >= 0.5 else 'weak'} seam."
            ),
            domain_metadata={
                "track_name":       track_name,
                "artist":           artist,
                "track_uri":        track_uri,
                "seam_time_s":      round(seam_time, 3),
                "seam_index":       i,
                "total_sections":   len(sections),
                "circular_return":  round(circular_return, 4),
                "sharpness":        round(sharpness, 4),
                "prev_loudness":    prev.get("loudness"),
                "curr_loudness":    curr.get("loudness"),
                "prev_tempo":       prev.get("tempo"),
                "curr_tempo":       curr.get("tempo"),
                "key_change":       curr.get("key") != prev.get("key"),
                "mode_change":      curr.get("mode") != prev.get("mode"),
                "dcp_composite":    round(dcp_score, 4),
            },
        )
        events.append(event)

    # Sort strongest seam first
    events.sort(key=lambda e: e.collapse_proxy or 0, reverse=True)
    return events


# ═══════════════════════════════════════════════════════════════════════════════
# Run probe
# ═══════════════════════════════════════════════════════════════════════════════

def run_audio_probe(min_sharpness: float = 0.3) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load candidates
    import csv
    if not CANDIDATES_CSV.exists():
        print(f"Run metadata probe first: python -m domains.music.analysis.loop_seam")
        sys.exit(1)
    with open(CANDIDATES_CSV, encoding="utf-8") as f:
        candidates = list(csv.DictReader(f))

    # Find which ones have cached audio analysis
    cached = [
        c for c in candidates
        if (ANALYSIS_CACHE / f"{c['track_uri'].split(':')[-1]}.json").exists()
    ]
    print(f"Candidates: {len(candidates)} total, {len(cached)} with cached audio analysis")

    if not cached:
        print(
            "\nNo cached audio analysis found."
            "\nRun first:\n"
            "  $env:SPOTIFY_CLIENT_ID='<id>'\n"
            "  $env:SPOTIFY_CLIENT_SECRET='<secret>'\n"
            "  python -m domains.music.ingestion.adapters.spotify_audio_analysis"
        )
        sys.exit(1)

    all_events: list[dict] = []
    track_summaries: list[dict] = []

    for rec in cached:
        track_id = rec["track_uri"].split(":")[-1]
        analysis = json.loads(
            (ANALYSIS_CACHE / f"{track_id}.json").read_text(encoding="utf-8")
        )
        events = extract_dcp_events_from_analysis(rec, analysis, min_sharpness)
        n_sections  = len(analysis.get("sections", []))
        best_sharp  = max((e.collapse_proxy or 0 for e in events), default=0)
        best_return = max(
            (e.domain_metadata.get("circular_return", 0) for e in events), default=0
        )

        track_summaries.append({
            "track_name":          rec.get("track_name"),
            "artist":              rec.get("artist"),
            "candidacy_score":     rec.get("candidacy_score"),
            "sections_total":      n_sections,
            "dcp_events_emitted":  len(events),
            "best_sharpness":      round(best_sharp, 4),
            "best_circular_return": round(best_return, 4),
            "qualification":       events[0].qualification_status() if events else "NO_EVENTS",
        })

        for e in events:
            all_events.append(e.domain_metadata | {
                "event_id":       e.event_id,
                "confidence":     e.confidence,
                "qualification":  e.qualification_status(),
                "dcp_composite":  e.domain_metadata.get("dcp_composite"),
            })

    # Sort tracks by best sharpness
    track_summaries.sort(key=lambda x: x["best_sharpness"], reverse=True)
    all_events.sort(key=lambda x: x.get("sharpness", 0), reverse=True)

    # Output
    report = {
        "probe": "loop_seam_audio",
        "domain": "music",
        "tracks_analyzed": len(cached),
        "total_dcp_events_emitted": len(all_events),
        "min_sharpness_threshold": min_sharpness,
        "note": (
            "collapse_proxy is now FILLED from real Spotify audio-analysis section data. "
            "circular_return score measures structural identity matching across sections — "
            "the primary loop-seam signature."
        ),
        "dcp_invariant_ref": "codex/library/invariants/decision_compression_principle.yaml",
        "track_summaries": track_summaries,
        "top_events": all_events[:50],
    }

    out_path = OUTPUT_DIR / "loop_seam_audio_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport: {out_path}")

    # CSV
    if all_events:
        import csv as csv_mod
        csv_path = OUTPUT_DIR / "loop_seam_events.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv_mod.DictWriter(f, fieldnames=list(all_events[0].keys()))
            writer.writeheader()
            writer.writerows(all_events)
        print(f"Events CSV: {csv_path}")

    # Print summary
    print(f"\n{'='*65}")
    print(f"TOP 15 TRACKS BY SECTION BOUNDARY SHARPNESS")
    print(f"{'='*65}")
    print(f"{'Sharp':>6}  {'Return':>6}  {'Events':>6}  {'Sections':>8}  Artist / Track")
    print(f"{'-'*6}  {'-'*6}  {'-'*6}  {'-'*8}  {'-'*35}")
    for t in track_summaries[:15]:
        artist_track = f"{t['artist'][:20]} / {t['track_name'][:20]}"
        print(
            f"{t['best_sharpness']:>6.3f}  "
            f"{t['best_circular_return']:>6.3f}  "
            f"{t['dcp_events_emitted']:>6}  "
            f"{t['sections_total']:>8}  "
            f"{artist_track}"
        )

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-sharpness", type=float, default=0.3,
                        help="Minimum boundary sharpness to emit a DCP event (0-1, default 0.3)")
    args = parser.parse_args()
    run_audio_probe(min_sharpness=args.min_sharpness)

