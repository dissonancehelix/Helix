"""
s3k_analysis.py — Sonic 3 & Knuckles Composer Attribution Pipeline
===================================================================
Three-phase analysis pipeline for attributing Sonic 3 & Knuckles tracks
to their composers using symbolic fingerprinting and FM timbre matching.

Phase 1 — Composer Fingerprint Building (from s3k_composer_fingerprint.py)
    Runs ANALYZE TRACK via HSL for each confirmed S3K composer across their
    full library. Builds calibration fingerprints (symbolic + FM timbre) per
    composer and writes s3k_composer_fingerprints.json.

Phase 2 — Fingerprint Comparison Against S3K Tracks (from s3k_fingerprint_compare.py)
    Loads calibrated composer fingerprints and compares them against the full
    S3K soundtrack using Jaccard similarity (FM patches) and Euclidean distance
    (symbolic features). Predicts composer per track with confidence labels.
    Special hunt: Takaoka overlap detection for the Bonus Theme question.

Phase 3 — Metadata Remapping (from s3k_remap_metadata.py)
    Scans artifact analysis files for S3K tracks, loads field index to resolve
    artist IDs, and produces s3k_mapped_tracks.json for downstream use.

Usage:
    python model/domains/music/probes/s3k_analysis.py              # all phases
    python model/domains/music/probes/s3k_analysis.py --phase 1    # calibration only
    python model/domains/music/probes/s3k_analysis.py --phase 2    # comparison only
    python model/domains/music/probes/s3k_analysis.py --phase 3    # remap only
    python model/domains/music/probes/s3k_analysis.py --dry-run    # phase 1 dry run
    python model/domains/music/probes/s3k_analysis.py --s3k        # phase 1 + full S3K run
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.hsl.context import CommandContext
from core.hsl.interpreter import run_command
from core.hsl.provenance import RunProvenance

# ─── S3K composers ────────────────────────────────────────────────────────────
# Source: VGMdb / Sonic Retro composer credits for Sonic 3 & Knuckles
# Slug format: lowercase underscore (how HSL carpenter resolves titles)
S3K_COMPOSERS = [
    ("Tatsuyuki Maeda",   "tatsuyuki_maeda"),
    ("Sachio Ogawa",      "sachio_ogawa"),
    ("Tomonori Sawada",   "tomonori_sawada"),
    ("Masaru Setsumaru",  "masaru_setsumaru"),
    ("Jun Senoue",        "jun_senoue"),
    ("Masayuki Nagao",    "masayuki_nagao"),
    ("Yoshiaki Kashima",  "yoshiaki_kashima"),
    ("Masanori Hikichi",  "masanori_hikichi"),
    ("Miyoko Takaoka",    "miyoko_takaoka"),
]

# ─── Feature keys we care about for fingerprinting ────────────────────────────
FINGERPRINT_KEYS = [
    "scale_mode",
    "progression_fingerprint",
    "melodic_contour",
    "dynamic_arc",
    "groove_score",
    "bass_rhythmic_regularity",
    "melody_bass_independence",
    "motif_recurrence",
    "pitch_entropy",
    "rhythmic_entropy",
    "pulse_coherence",
    "off_beat_ratio",
    "chromatic_intrusion_rate",
    "interval_roughness",
    "harmonic_tension_score",
    "sustained_ratio",
    "register_separation",
    "tempo_bpm",
    "pre_seam_density_spike",
    "seam_sharpness",
    "emergence_index",
    "disappearance_index",
    "fm_unique_patches",
    "fm_timbre_reuse_ratio",
    "prevalence_of_tritones",
    "vertical_dissonance",
]


# =============================================================================
# PHASE 1: Composer Fingerprint Building
# =============================================================================

def extract_fingerprint(analysis_result: dict) -> dict:
    """Pull fingerprint keys from a single track's analysis result dict.
    Primary source: library_meta.symbolic_full (full SymbolicAnalysis asdict).
    Fallback: analysis.symbolic (SymbolicFeatures subset).
    """
    analysis = analysis_result.get("analysis", {})
    # Rich source: full SymbolicAnalysis dict (set by Tier D pipeline)
    symbolic = analysis.get("library_meta", {}).get("symbolic_full") or {}
    # Narrow fallback: SymbolicFeatures dataclass-dict
    if not symbolic:
        symbolic = analysis.get("symbolic") or {}

    fp = {}
    for k in FINGERPRINT_KEYS:
        fp[k] = symbolic.get(k)
    return fp


def summarise_composer(name: str, track_results: list[dict]) -> dict:
    """
    Aggregate fingerprint across all of a composer's tracks.
    Numeric fields: mean. String fields: mode (most common value).
    """
    if not track_results:
        return {"composer": name, "track_count": 0}

    numeric: dict[str, list[float]] = {}
    categorical: dict[str, list[str]] = {}

    for r in track_results:
        fp = extract_fingerprint(r)
        for k, v in fp.items():
            if isinstance(v, (int, float)) and v is not None:
                numeric.setdefault(k, []).append(float(v))
            elif isinstance(v, str) and v:
                categorical.setdefault(k, []).append(v)

    summary: dict = {"composer": name, "track_count": len(track_results)}

    for k, vals in numeric.items():
        summary[k] = round(sum(vals) / len(vals), 4)

    from collections import Counter
    for k, vals in categorical.items():
        summary[k] = Counter(vals).most_common(1)[0][0]

    all_patches = []
    for r in track_results:
        # Get raw patches (dicts from _extract_vgm_fm_patches)
        patches = r.get("analysis", {}).get("library_meta", {}).get("fm_patch_hashes", [])
        # Convert to stable JSON strings for hashing
        patches = [json.dumps(p, sort_keys=True) if isinstance(p, dict) else p for p in patches]
        all_patches.extend(patches)

    if all_patches:
        unique_patch_set = set(all_patches)
        summary["fm_unique_patches"] = len(unique_patch_set)
        summary["fm_timbre_reuse_ratio"] = round(1.0 - (len(unique_patch_set) / len(all_patches)), 4)
        summary["fm_patch_catalog"] = list(unique_patch_set)
    else:
        summary["fm_unique_patches"] = 0
        summary["fm_timbre_reuse_ratio"] = 0.0
        summary["fm_patch_catalog"] = []

    # SPC-specific catalogs
    all_brr = []
    for r in track_results:
        brr = r.get("analysis", {}).get("library_meta", {}).get("spc_brr_hashes", [])
        all_brr.extend(brr)
    summary["spc_brr_catalog"] = list(set(all_brr))

    return summary


def build_composer_index(composers: list[tuple[str, str]]) -> dict[str, list[dict]]:
    """
    Load composer -> track list from .field_index.json (O(1) instead of full library walk).
    Filters to VGM/SPC format categories only.
    """
    IDX_PATH = ROOT / "codex" / "library" / "music" / ".field_index.json"
    if not IDX_PATH.exists():
        raise FileNotFoundError(
            f"Field index not found: {IDX_PATH}\n"
            "Run: python model/domains/music/probes/library_pipeline.py --stage index"
        )

    VGM_EXTS = {
        ".vgz", ".vgm", ".spc", ".nsf", ".nsfe",
        ".psf", ".psf2", ".s98", ".gym", ".dsf", ".ssf",
        ".usf", ".gsf", ".gbs", ".hes",
        ".mini2sf", ".miniusf", ".minincsf", ".minigsf", ".minipsf",
    }

    idx        = json.loads(IDX_PATH.read_text(encoding="utf-8"))
    by_artist  = idx.get("by_artist", {})
    source_map = idx.get("source_map", {})

    results: dict[str, list[dict]] = {name: [] for name, _ in composers}

    print("\nBuilding composer index from field index...")
    for name, _ in composers:
        key = name.lower()
        track_ids: list[str] = by_artist.get(key, [])
        for tid in track_ids:
            src = source_map.get(tid, "")
            if not src or Path(src).suffix.lower() not in VGM_EXTS:
                continue
            results[name].append({
                "id":     tid,
                "title":  tid.split(".")[-1],
                "source": src,
            })
        print(f"  {name}: {len(results[name])} VGM/SPC tracks")

    return results


def run_composer(name: str, tracks: list[dict], dry_run: bool) -> tuple[dict | None, list[dict]]:
    """Run ANALYZE TRACK via HSL for each of a composer's tracks."""
    if not tracks:
        print(f"  No tracks found in library.")
        return None, []

    print(f"  Analyzing {len(tracks)} tracks...")
    ctx = CommandContext.canonical(
        provenance=RunProvenance.from_cli_inline(
            f"ANALYZE TRACK track:{tracks[0]['id']}"
        )
    )
    track_results = []
    errors = []

    for t in tracks:
        entity_id = t["id"]
        cmd = f"ANALYZE TRACK track:{entity_id}"
        if dry_run:
            print(f"    [dry-run] {cmd}")
            continue

        result = run_command(cmd, ctx)
        if result.get("status") == "ok":
            track_results.append(result.get("data", {}))
            title = t.get("title", entity_id.split(".")[-1])
            print(f"    OK {title}")
        else:
            err = result.get("error", "?")
            errors.append(f"{entity_id}: {err}")
            print(f"    ERR {entity_id}: {err}")

    if errors:
        print(f"  {len(errors)} errors")

    summary = summarise_composer(name, track_results)
    return summary, track_results


def compare_summaries(summaries: list[dict]) -> None:
    """Print a comparison table of numeric fingerprint features by composer."""
    numeric_keys = [k for k in FINGERPRINT_KEYS
                    if isinstance(summaries[0].get(k), (int, float))]
    str_keys = [k for k in FINGERPRINT_KEYS
                if isinstance(summaries[0].get(k), str)]

    print("\n" + "=" * 80)
    print("COMPOSER FINGERPRINT COMPARISON")
    print("=" * 80)

    # Categorical features
    print("\n── Categorical ──")
    header = f"{'Composer':<22}" + "".join(f"  {k:<18}" for k in str_keys)
    print(header)
    for s in summaries:
        row = f"{s['composer']:<22}"
        for k in str_keys:
            v = str(s.get(k, "—"))
            row += f"  {v:<18}"
        print(row)

    # Numeric features — sorted by variance across composers (most discriminating first)
    print("\n── Numeric (sorted by discriminative power) ──")
    import statistics

    def spread(k):
        vals = [s.get(k) for s in summaries if isinstance(s.get(k), float)]
        return statistics.pstdev(vals) if len(vals) > 1 else 0.0

    ranked = sorted(numeric_keys, key=spread, reverse=True)

    for k in ranked:
        vals = [s.get(k) for s in summaries if isinstance(s.get(k), (int, float))]
        std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        print(f"\n  {k}  (std={std:.3f})")
        for s in summaries:
            v = s.get(k)
            bar = ""
            if isinstance(v, float) and v is not None:
                bar = "█" * max(0, min(40, int(v * 40)))
            print(f"    {s['composer']:<22}  {str(v or '—'):>7}  {bar}")


def run_phase1(dry_run: bool = False, also_run_s3k: bool = False) -> None:
    """Phase 1: Build composer fingerprints for all S3K composers."""
    print("S3K Composer Fingerprint Calibration")
    print(f"  Composers: {len(S3K_COMPOSERS)}")
    print(f"  Dry run:   {dry_run}")

    # Single library pass — build composer->tracks index
    composer_index = build_composer_index(S3K_COMPOSERS)

    summaries: list[dict] = []
    all_track_results: dict[str, list[dict]] = {}

    for name, slug in S3K_COMPOSERS:
        print(f"\n{'─'*60}")
        print(f"Composer: {name}")
        tracks = composer_index.get(name, [])
        summary, track_results = run_composer(name, tracks, dry_run)
        if summary and summary.get("track_count", 0) > 0:
            summaries.append(summary)
            all_track_results[name] = track_results
        else:
            print(f"  (no tracks found or dry run)")

    if summaries:
        compare_summaries(summaries)

        # Write combined report
        out_dir = ROOT / "domains" / "language" / "artifacts" / "analysis"
        out_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "report": "s3k_composer_fingerprint_calibration",
            "composers": summaries,
        }
        out_path = out_dir / "s3k_composer_fingerprints.json"
        out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\nReport written: {out_path}")

    if also_run_s3k and not dry_run:
        print("\n" + "=" * 60)
        print("Running full S3K analysis...")
        cmd = (
            "ANALYZE SOUNDTRACK soundtrack:sonic_3_knuckles "
            "artist:sega_sound_team output:s3k_sega_sound_team_results"
        )
        ctx = CommandContext.canonical(
            provenance=RunProvenance.from_cli_inline(cmd)
        )
        result = run_command(cmd, ctx)
        if result.get("status") != "ok":
            print(f"S3K analysis failed: {result.get('error', '?')}")
        else:
            batch_artifact = result.get("data", {}).get("batch_artifact", "")
            print(f"S3K Sound Team results mapped to: {batch_artifact}")


# =============================================================================
# PHASE 2: Fingerprint Comparison Against S3K Tracks
# =============================================================================

def jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def euclidean(v1, v2):
    return math.sqrt(sum((a - b)**2 for a, b in zip(v1, v2)))


def run_phase2() -> None:
    """Phase 2: Compare calibrated fingerprints against S3K soundtrack tracks."""
    # Load calibrated composer fingerprints
    calib_path = ROOT / "domains" / "language" / "artifacts" / "analysis" / "s3k_composer_fingerprints.json"
    try:
        calib = json.loads(calib_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("Error: Calibration file not found. Run Phase 1 first.")
        return

    baselines = {}
    for fp in calib['composers']:
        cat = set(fp.get('fm_patch_catalog', []))
        baselines[fp['composer']] = {
            'groove': fp.get('groove_score', 0),
            'tension': fp.get('harmonic_tension_score', 0),
            'fm_catalog': cat,
            'brr_catalog': set(fp.get('spc_brr_catalog', []))
        }

    # Pre-scan confirmed S3K tracks to build the 'In-Game' biometric weight
    # (same-game sessions use identical patch-programming)
    project_patches = {}
    mapped_path = ROOT / "domains" / "language" / "artifacts" / "analysis" / "s3k_mapped_tracks.json"
    try:
        known_s3k = json.loads(mapped_path.read_text(encoding="utf-8"))
        for track in known_s3k:
            artist = track.get('artist')
            if artist and artist != "Sega Sound Team":
                for p in track.get('fm_patches', []):
                    project_patches[p] = artist
    except FileNotFoundError:
        pass

    # Process FULL soundtrack
    s3k_tracks = []
    full_path = ROOT / "domains" / "language" / "artifacts" / "analysis" / "s3k_full_soundtrack_results.json"
    try:
        s3k_tracks = json.loads(full_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("Warning: s3k_full_soundtrack_results.json not found yet.")

    print(f"{'S3K Track':<40} | {'Predicted Composer':<18} | {'Conf.':<6} | {'Original Artist'}")
    print("-" * 90)

    for track in s3k_tracks:
        track_fm = set(track.get('fm_patches', []))
        track_brr = set(track.get('brr_hashes', []))
        title = track.get('title', 'Unknown')
        original = track.get('original_artist', 'Sega Sound Team')

        best_match = "Unknown"
        highest_score = -1.0
        best_timbre = 0.0

        for name, base in baselines.items():
            # Score 1: Timbre Overlap (The absolute tell)
            fm_sim = jaccard(track_fm, base['fm_catalog'])
            brr_sim = jaccard(track_brr, base['brr_catalog'])

            # High Weighted Score: S3K-native Patch Match
            project_overlap = 0.0
            if track_fm:
                matches = [p for p in track_fm if project_patches.get(p) == name]
                project_overlap = len(matches) / len(track_fm) if len(track_fm) > 0 else 0.0

            timbre_sim = max(fm_sim, brr_sim)
            # Boost confidence significantly if the patches are S3K-native
            timbre_sim = (timbre_sim * 0.5) + (project_overlap * 2.0)
            timbre_sim = min(1.0, timbre_sim)

            # Score 2: Symbolic Distance
            sym_dist = euclidean(
                [track['groove'], track['tension']],
                [base['groove'], base['tension']]
            )
            sym_score = 1.0 - min(1.0, sym_dist)

            # Combined confidence
            total_score = (0.8 * timbre_sim) + (0.2 * sym_score)

            if total_score > highest_score:
                highest_score = total_score
                best_match = name
                best_timbre = timbre_sim

        conf_label = "HIGH" if highest_score > 0.6 else "MED" if highest_score > 0.3 else "LOW"

        # Hide "Original Artist" if it's the same as predicted to keep it clean,
        # but show if it's Sega Sound Team or a mismatch
        orig_display = original if original == "Sega Sound Team" or original != best_match else "--"

        print(f"{title[:40]:<40} | {best_match:<18} | {conf_label:<6} | {orig_display}")

    # Final Search for Takaoka's Bonus Theme
    print("\n[RESEARCH NOTE] Searching specifically for Takaoka overlaps (Bonus Theme hunt):")
    for track in s3k_tracks:
        track_fm = set(track.get('fm_patches', []))
        takaoka_fm = baselines.get('Miyoko Takaoka', {}).get('fm_catalog', set())
        sim = jaccard(track_fm, takaoka_fm)
        if sim > 0:
            # Check if it was originally Sound Team
            if track.get('original_artist') == "Sega Sound Team":
                print(f" -> SMOKING GUN: {track['title']} uses Takaoka's FM patches! (Sim: {sim:.4f})")
        elif sim > 0:
            print(f" -> Potential Takaoka Match: {track['title']} (Sim: {sim:.4f})")


# =============================================================================
# PHASE 3: Metadata Remapping
# =============================================================================

def run_phase3() -> None:
    """Phase 3: Scan artifact files for S3K tracks and produce mapped metadata."""
    artifacts_dir = ROOT / "domains" / "language" / "artifacts" / "analysis"

    # Load field index to map IDs to Artists
    track_to_artist = {}
    idx_path = ROOT / "codex" / "library" / "music" / ".field_index.json"
    try:
        field_index = json.loads(idx_path.read_text(encoding="utf-8"))
        for artist, track_ids in field_index.get('by_artist', {}).items():
            for t_id in track_ids:
                track_to_artist[t_id] = artist.title()
    except FileNotFoundError:
        pass

    s3k_tracks = []

    for p in artifacts_dir.glob('music_track_sonic_3_knuckles_*.json'):
        data = json.loads(p.read_text(encoding='utf-8'))
        analysis = data.get('analysis', {})
        sym = analysis.get('library_meta', {}).get('symbolic_full', {})

        if not sym:
            continue

        file_path = analysis.get('file_path', '')
        title = Path(file_path).stem if file_path else p.stem
        if ' - ' in title:
            title = title.split(' - ', 1)[1]

        track_id = data.get('entity_id', '')
        artist = track_to_artist.get(track_id, "Sega Sound Team")

        s3k_tracks.append({
            'title': title,
            'artist': artist,
            'groove': sym.get('groove_score', 0),
            'tension': sym.get('harmonic_tension_score', 0),
            'contour': sym.get('melodic_contour', 'none'),
            'mode': sym.get('scale_mode', 'none')
        })

    # Dump this mapped data so phase 2 can use it
    s3k_tracks.sort(key=lambda x: (x['artist'] == 'Sega Sound Team', x['artist'], x['title']))
    out_path = artifacts_dir / "s3k_mapped_tracks.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(s3k_tracks, indent=2), encoding='utf-8')

    print(f"Mapped {len(s3k_tracks)} tracks from artifacts.")
    print(f"Written to: {out_path}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="S3K Composer Attribution Pipeline")
    parser.add_argument(
        "--phase", choices=["1", "2", "3", "all"], default="all",
        help="Which phase to run (default: all)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Phase 1: run without calling HSL (dry run)")
    parser.add_argument("--s3k", action="store_true",
                        help="Phase 1: also run full S3K analysis after calibration")
    args = parser.parse_args()

    phase = args.phase

    if phase in ("1", "all"):
        print("\n" + "=" * 70)
        print("PHASE 1: Composer Fingerprint Building")
        print("=" * 70)
        run_phase1(dry_run=args.dry_run, also_run_s3k=args.s3k)

    if phase in ("3", "all"):
        print("\n" + "=" * 70)
        print("PHASE 3: Metadata Remapping")
        print("=" * 70)
        run_phase3()

    if phase in ("2", "all"):
        print("\n" + "=" * 70)
        print("PHASE 2: Fingerprint Comparison Against S3K Tracks")
        print("=" * 70)
        run_phase2()


if __name__ == "__main__":
    main()

