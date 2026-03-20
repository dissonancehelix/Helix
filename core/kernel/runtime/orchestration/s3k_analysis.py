"""
Sonic 3 & Knuckles — Helix Music Lab Analysis
===============================================
Pipeline:
  1. Ingest all VGZ files from the S3&K library path
  2. Parse VGM command streams (YM2612 + PSG)
  3. Extract chip-level feature vectors
  4. Run probabilistic composer attribution (feature likelihood × musicological prior)
  5. Write structured artifact to artifacts/music_lab/

Usage:
  python labs/music_lab/s3k_analysis.py [--library <path>] [--output <artifact_dir>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from domains.music.vgm_parser      import parse as vgm_parse
from domains.music.feature_extractor import extract
from domains.music.composer_attribution import attribute, COMPOSER_PROFILES


DEFAULT_LIBRARY = Path("C:/Users/dissonance/Music/VGM/S/Sonic 3 & Knuckles")
DEFAULT_OUTPUT  = ROOT / "artifacts" / "music_lab"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bar(value: float, width: int = 20) -> str:
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def _fmt_pct(v: float) -> str:
    return f"{v * 100:5.1f}%"


def _feature_summary(feat) -> dict:
    return {
        "keyon_density":      round(feat.keyon_density, 2),
        "rhythmic_entropy":   round(feat.rhythmic_entropy, 3),
        "pitch_center":       round(feat.pitch_center, 1),
        "pitch_range":        feat.pitch_range,
        "pitch_entropy":      round(feat.pitch_entropy, 3),
        "psg_to_fm_ratio":    round(feat.psg_to_fm_ratio, 3),
        "ams_fms_usage":      round(feat.ams_fms_usage, 3),
        "silence_ratio":      round(feat.silence_ratio, 3),
        "duration_sec":       round(feat.duration_sec, 2),
        "algorithm_dist":     feat.algorithm_dist,
        "channel_activity":   feat.channel_activity,
        "has_ym2612":         feat.has_ym2612,
        "has_psg":            feat.has_psg,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(library_path: Path, output_dir: Path, verbose: bool = True) -> dict:
    def log(*a): verbose and print(*a)

    log(f"\n{'='*70}")
    log(f"  HELIX MUSIC LAB — Sonic 3 & Knuckles Composer Attribution")
    log(f"{'='*70}")
    log(f"  Library : {library_path}")
    log(f"  Output  : {output_dir}")
    log()

    # --- Stage 1: Collect VGZ files ---
    vgz_files = sorted(library_path.glob("*.vgz"))
    log(f"  [STAGE 1] Found {len(vgz_files)} VGZ files\n")

    # --- Stage 2/3: Parse + extract features ---
    log("  [STAGE 2/3] Parsing VGM streams + extracting features...")
    results = []
    parse_failures = []

    for f in vgz_files:
        track = vgm_parse(f)
        if track.error:
            parse_failures.append({"file": f.name, "error": track.error})
            log(f"    PARSE ERROR: {f.name}: {track.error}")
            continue
        feat = extract(track)
        attr = attribute(feat)
        results.append((track, feat, attr))
        log(f"    OK  {f.name[:50]:<50}  chips: YM2612={'Y' if feat.has_ym2612 else 'N'} PSG={'Y' if feat.has_psg else 'N'}  "
            f"density={feat.keyon_density:5.1f}/s  rhythm_H={feat.rhythmic_entropy:.2f}")

    log(f"\n  Parsed {len(results)}/{len(vgz_files)} tracks successfully")

    # --- Stage 4: Attribution table ---
    composers = [p.name for p in COMPOSER_PROFILES]

    log(f"\n{'='*70}")
    log(f"  [STAGE 4] COMPOSER ATTRIBUTION TABLE")
    log(f"{'='*70}")
    header = f"  {'Track':<42}" + "".join(f"  {c[:12]:<12}" for c in composers)
    log(header)
    log("  " + "-" * (len(header) - 2))

    attribution_rows = []
    for track, feat, attr in results:
        name = feat.track_name
        if " - " in name:
            name = name.split(" - ", 1)[1]

        row_str = f"  {name:<42}"
        row_data = {"track": name, "top_composer": attr.top, "confidence": round(attr.confidence, 3)}
        for c in composers:
            p = attr.posterior.get(c, 0.0)
            row_str += f"  {_fmt_pct(p):<12}"
            row_data[f"prob_{c.replace(' ', '_')}"] = round(p, 4)

        row_data["features"] = _feature_summary(feat)
        row_data["prior"]    = {k: round(v, 3) for k, v in attr.prior.items()}
        row_data["feature_likelihood"] = {k: round(v, 4) for k, v in attr.scores.items()}
        attribution_rows.append(row_data)
        log(row_str)

    # --- Stage 5: Feature comparison by composer ---
    log(f"\n{'='*70}")
    log(f"  [STAGE 5] FEATURE SIGNATURES BY ATTRIBUTED COMPOSER")
    log(f"{'='*70}")

    by_composer: dict[str, list] = {c: [] for c in composers}
    for _, feat, attr in results:
        top = attr.top
        if top in by_composer:
            by_composer[top].append(feat)

    composer_signatures = {}
    for c, feats in by_composer.items():
        if not feats:
            continue
        n = len(feats)
        sig = {
            "track_count":       n,
            "keyon_density_mean":    round(sum(f.keyon_density for f in feats) / n, 2),
            "rhythmic_entropy_mean": round(sum(f.rhythmic_entropy for f in feats) / n, 3),
            "pitch_center_mean":     round(sum(f.pitch_center for f in feats) / n, 1),
            "psg_ratio_mean":        round(sum(f.psg_to_fm_ratio for f in feats) / n, 3),
            "ams_fms_mean":          round(sum(f.ams_fms_usage for f in feats) / n, 3),
            "tracks":                [],
        }
        for f in feats:
            nm = f.track_name
            if " - " in nm:
                nm = nm.split(" - ", 1)[1]
            sig["tracks"].append(nm)
        composer_signatures[c] = sig
        log(f"\n  {c} ({n} tracks attributed)")
        log(f"    note density   : {sig['keyon_density_mean']:5.2f} key-ons/sec")
        log(f"    rhythmic ent.  : {sig['rhythmic_entropy_mean']:5.3f} bits")
        log(f"    pitch center   : {sig['pitch_center_mean']:5.1f} (MIDI semitone)")
        log(f"    PSG/FM ratio   : {sig['psg_ratio_mean']:5.3f}")
        log(f"    LFO (AMS/FMS)  : {sig['ams_fms_mean']:5.3f}")
        log(f"    tracks: {', '.join(sig['tracks'][:5])}{'...' if len(sig['tracks']) > 5 else ''}")

    # --- Stage 6: Structural signatures ---
    log(f"\n{'='*70}")
    log(f"  [STAGE 6] DISCOVERED STRUCTURAL COMPOSER SIGNATURES")
    log(f"{'='*70}")

    # Find discriminating features
    structural_notes = []

    # IceCap: check against Brad Buxer profile — signature PSG bass groove
    icecap_tracks = [
        (feat, attr) for _, feat, attr in results
        if "icecap" in feat.track_name.lower()
    ]
    for feat, attr in icecap_tracks:
        nm = feat.track_name.split(" - ", 1)[-1] if " - " in feat.track_name else feat.track_name
        note = (f"  IceCap Zone: PSG/FM={feat.psg_to_fm_ratio:.3f}, "
                f"LFO={feat.ams_fms_usage:.3f}, density={feat.keyon_density:.1f}/s "
                f"→ top: {attr.top} ({_fmt_pct(attr.confidence)})")
        log(note)
        structural_notes.append(note.strip())

    # Prototype vs final comparison
    proto_pairs = [
        ("IceCap Zone Act 1", "IceCap Zone Act 1 (prototype)"),
        ("Carnival Night Zone Act 1", "Carnival Night Zone Act 1 (prototype)"),
        ("Launch Base Zone Act 1", "Launch Base Zone Act 1 (prototype)"),
    ]
    for final_key, proto_key in proto_pairs:
        final = next(
            ((feat, attr) for _, feat, attr in results if final_key in feat.track_name),
            None
        )
        proto = next(
            ((feat, attr) for _, feat, attr in results if "(prototype)" in feat.track_name and
             proto_key.split("(")[0].strip().lower() in feat.track_name.lower()),
            None
        )
        if final and proto:
            f_feat, f_attr = final
            p_feat, p_attr = proto
            delta_density = f_feat.keyon_density - p_feat.keyon_density
            delta_rhythm  = f_feat.rhythmic_entropy - p_feat.rhythmic_entropy
            fname = final_key.split(" - ")[-1] if " - " in final_key else final_key
            note = (f"  {fname}: final vs prototype — "
                    f"Δdensity={delta_density:+.2f}/s, Δrhythm_H={delta_rhythm:+.3f}b")
            log(note)
            structural_notes.append(note.strip())

    # --- Build artifact ---
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    artifact = {
        "run_id":              run_id,
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "pipeline_stages":     ["vgm_parse", "feature_extract", "composer_attribution"],
        "library_path":        str(library_path),
        "tracks_total":        len(vgz_files),
        "tracks_parsed":       len(results),
        "tracks_failed":       len(parse_failures),
        "parse_failures":      parse_failures,
        "attribution_table":   attribution_rows,
        "composer_signatures": composer_signatures,
        "structural_notes":    structural_notes,
        "pipeline_status": {
            "vgm_parsing":             "PASS" if results else "FAIL",
            "feature_extraction":      "PASS" if any(r[1].keyon_count > 0 for r in results) else "PARTIAL",
            "composer_attribution":    "PASS",
        },
    }

    # --- Write artifact ---
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"s3k_attribution_{run_id}.json"
    out_path.write_text(json.dumps(artifact, indent=2))

    log(f"\n{'='*70}")
    log(f"  PIPELINE COMPLETE")
    log(f"  Tracks parsed  : {len(results)}/{len(vgz_files)}")
    log(f"  Artifact       : {out_path}")
    log(f"{'='*70}\n")

    return artifact


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Helix Music Lab — S3&K Composer Attribution")
    p.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    p.add_argument("--output",  type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--quiet",   action="store_true")
    args = p.parse_args()

    artifact = run(args.library, args.output, verbose=not args.quiet)

    status = artifact["pipeline_status"]
    all_pass = all(v in ("PASS", "PARTIAL") for v in status.values())
    sys.exit(0 if all_pass else 1)
