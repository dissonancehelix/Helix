"""
s3k_analysis_pipeline.py — Sonic 3 & Knuckles Composer Pattern Analysis
========================================================================
Three-layer analysis pipeline on the full S3K VGM dataset.

Layer 1 — Hardware Execution (chip stats, patch identity, register ground truth)
Layer 2 — Symbolic Music   (MIDI reconstruction → melodic/harmonic/arrangement)
Layer 3 — MIR              (audio features where rendered audio exists; otherwise chip proxy)

Composer attribution candidates (from atlas/knowledge/s3k_composer_attribution.json):
  Sega Sound Team:
    Masayuki Nagao      (Sonic 3 tracks: Hydrocity, Marble Garden, Carnival Night Act1, etc.)
    Tomonori Sawada     (various Sonic 3 tracks)
    Tatsuyuki Maeda     (Sonic & Knuckles: Flying Battery, Lava Reef, etc.)
    Jun Senoue          (Bonus stages)
    Yoshiaki Kashima    (Special Stage — recycled from SegaSonic Bros.)
  Michael Jackson / associates:
    Brad Buxer          (IceCap — "Hard Times")
    Darryl Ross / Bobby Brooks / Cirocco Jones / Doug Grigsby III / Geoff Grace

Output:
  artifacts/music_lab/s3k_analysis/
    ├── track_results/         ← per-track JSON (layers 1+2+3)
    ├── composer_profiles.json ← centroid vectors per composer (known tracks)
    ├── clustering_report.json ← style clusters + attribution candidates
    └── analysis_report.md     ← human-readable research report

Usage:
    python -m labs.music_lab.pipelines.s3k_analysis_pipeline [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on path when run directly
_ROOT = Path(__file__).parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from labs.music_lab.config import S3K_PATH, ARTIFACTS

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

ARTIFACTS_DIR  = ARTIFACTS / "s3k_analysis"
TRACK_RESULTS  = ARTIFACTS_DIR / "track_results"


# ---------------------------------------------------------------------------
# Known S3K composer assignments (ground truth for training the profiler)
# Source: atlas/knowledge/s3k_composer_attribution.json + Sonic Retro research
# ---------------------------------------------------------------------------

S3K_KNOWN_COMPOSERS: dict[str, str] = {
    # Sonic 3 tracks — Sega Sound Team assignments
    "01":  "Masayuki Nagao",   # Title Screen
    "02":  "Masayuki Nagao",   # Angel Island Zone Act 1
    "03":  "Masayuki Nagao",   # Angel Island Zone Act 2
    "04":  "Masayuki Nagao",   # Hydrocity Zone Act 1
    "05":  "Masayuki Nagao",   # Hydrocity Zone Act 2
    "06":  "Masayuki Nagao",   # Marble Garden Zone Act 1
    "07":  "Masayuki Nagao",   # Marble Garden Zone Act 2
    "08":  "Jackson_Associates",  # Carnival Night Zone Act 1
    "09":  "Jackson_Associates",  # Carnival Night Zone Act 2
    "10":  "Jun Senoue",       # Ice Cap Zone Act 1 (Buxer "Hard Times" → Jackson-associated)
    "11":  "Jackson_Associates",  # Ice Cap Zone Act 2
    "12":  "Jackson_Associates",  # Launch Base Zone Act 1
    "13":  "Jackson_Associates",  # Launch Base Zone Act 2
    # Sonic & Knuckles tracks
    "14":  "Tatsuyuki Maeda",  # Mushroom Hill Zone Act 1
    "15":  "Tatsuyuki Maeda",  # Mushroom Hill Zone Act 2
    "16":  "Tatsuyuki Maeda",  # Flying Battery Zone Act 1
    "17":  "Tatsuyuki Maeda",  # Flying Battery Zone Act 2
    "18":  "Tatsuyuki Maeda",  # Sandopolis Zone Act 1
    "19":  "Tatsuyuki Maeda",  # Sandopolis Zone Act 2
    "20":  "Tatsuyuki Maeda",  # Lava Reef Zone Act 1
    "21":  "Tatsuyuki Maeda",  # Lava Reef Zone Act 2
    "22":  "Tatsuyuki Maeda",  # Hidden Palace Zone
    "23":  "Tatsuyuki Maeda",  # Sky Sanctuary Zone
    "24":  "Tatsuyuki Maeda",  # Death Egg Zone Act 1
    "25":  "Tatsuyuki Maeda",  # Death Egg Zone Act 2
    "26":  "Tatsuyuki Maeda",  # Doomsday Zone
    # Boss/menu/special
    "27":  "Masayuki Nagao",   # Mini Boss (Sonic 3 theme)
    "30":  "Jun Senoue",       # Bonus Stage
    "31":  "Yoshiaki Kashima", # Special Stage
    "35":  "Jackson_Associates",  # Credits
}

# Track type labels for structural analysis
TRACK_TYPES: dict[str, str] = {
    "01": "title", "27": "miniboss", "28": "boss", "29": "boss_s3",
    "30": "bonus", "31": "special", "32": "invincibility", "33": "speedshoes",
    "34": "extra_life", "35": "credits", "36": "continue", "37": "gameover",
}


# ---------------------------------------------------------------------------
# Single-track analysis
# ---------------------------------------------------------------------------

def analyze_track(vgm_path: Path) -> dict[str, Any]:
    """Run all three layers on one VGM/VGZ file. Returns a result dict."""
    result: dict[str, Any] = {
        "path":       str(vgm_path),
        "track_name": vgm_path.stem,
        "error":      None,
    }

    # --- Layer 1: parse + chip features ---
    try:
        from labs.music_lab.vgm_parser import parse_vgm_file
        from labs.music_lab.feature_extractor import extract as extract_features

        track = parse_vgm_file(vgm_path)
        if track.error:
            result["error"] = track.error
            return result

        layer1 = extract_features(track, symbolic=False)
        result["layer1"] = {
            "duration_sec":     round(layer1.duration_sec, 3),
            "keyon_count":      layer1.keyon_count,
            "keyon_density":    round(layer1.keyon_density, 3),
            "channel_activity": layer1.channel_activity,
            "algorithm_dist":   layer1.algorithm_dist,
            "feedback_dist":    layer1.feedback_dist,
            "pitch_entropy":    round(layer1.pitch_entropy, 3),
            "pitch_range":      layer1.pitch_range,
            "pitch_center":     round(layer1.pitch_center, 2),
            "psg_to_fm_ratio":  round(layer1.psg_to_fm_ratio, 3),
            "silence_ratio":    round(layer1.silence_ratio, 3),
            "rhythmic_entropy": round(layer1.rhythmic_entropy, 3),
            "tl_mean_op1":      round(layer1.tl_mean_op1, 2),
            "tl_mean_op2":      round(layer1.tl_mean_op2, 2),
            "ams_fms_usage":    round(layer1.ams_fms_usage, 3),
        }

        # Operator brightness using Nuked-OPN2 carrier topology
        try:
            from labs.music_lab.analysis.tool_bridge import operator_brightness, CARRIER_SLOTS
            # Use the most common algorithm in the track
            alg_dist = layer1.algorithm_dist
            dominant_alg = max(alg_dist, key=alg_dist.get) if alg_dist else 7
            tl_list = [layer1.tl_mean_op1, 0, layer1.tl_mean_op2, 0]
            result["layer1"]["carrier_brightness"] = round(
                operator_brightness(tl_list, int(dominant_alg)), 3
            )
            result["layer1"]["dominant_alg"] = int(dominant_alg)
        except Exception:
            pass

        # SMPS voice patch matching
        try:
            from labs.music_lab.analysis.codec_reference import get_library, CODEC_VGM_YM2612
            lib = get_library()
            voice_lib = lib.get_voice_library(CODEC_VGM_YM2612)
            if voice_lib:
                result["layer1"]["voice_library_size"] = len(voice_lib)
        except Exception:
            pass

    except Exception as exc:
        result["error"] = f"Layer 1 failed: {exc}"
        log.warning("Layer 1 error on %s: %s", vgm_path.name, exc)
        return result

    # --- Layer 2: symbolic reconstruction + music analysis ---
    score = None  # kept in scope for ludomusicology layer below
    try:
        from labs.music_lab.analysis.symbolic_music.vgm_note_reconstructor import reconstruct
        from labs.music_lab.analysis.symbolic_music.melodic_analyzer import analyze as melodic_analyze
        from labs.music_lab.analysis.symbolic_music.harmonic_analyzer import analyze as harmonic_analyze
        from labs.music_lab.analysis.symbolic_music.arrangement_analyzer import analyze as arrangement_analyze
        from labs.music_lab.analysis.theory_features.key_estimator import (
            estimate as key_estimate,
            pitch_histogram,
        )
        from labs.music_lab.analysis.theory_features.rhythm_analyzer import analyze as rhythm_analyze

        score = reconstruct(track)
        result["layer2_reconstruction"] = score.reconstruction_stats

        if score.note_count > 0:
            # Melodic
            melodic = melodic_analyze(score)
            result["layer2_melodic"] = melodic.to_dict()

            # Harmonic
            harmonic = harmonic_analyze(score)
            result["layer2_harmonic"] = harmonic.to_dict()

            # Arrangement
            arrangement = arrangement_analyze(score, layer1_features=layer1)
            result["layer2_arrangement"] = arrangement.to_dict()

            # Key estimation
            ph = pitch_histogram(score.notes)
            key_result = key_estimate(ph)
            result["layer2_key"] = {
                "key":        key_result.key,
                "mode":       key_result.mode,
                "confidence": round(key_result.confidence, 3),
            }

            # Rhythm
            rhythm = rhythm_analyze(score.notes)
            result["layer2_rhythm"] = {
                "tempo_bpm":       round(rhythm.tempo_bpm, 1),
                "syncopation":     round(rhythm.syncopation, 3),
                "beat_regularity": round(rhythm.beat_regularity, 3),
                "ioi_mean":        round(rhythm.ioi_mean, 4),
            }

            # Symbolic toolchain: music21 / musif / symusic / musicntwrk
            try:
                from labs.music_lab.analysis.symbolic_toolchain import from_score as symbolic_analyze
                sym = symbolic_analyze(score)
                result["layer2_symbolic"] = sym.to_dict()

                # Use music21 key as authoritative if our estimator is uncertain
                k_existing = result.get("layer2_key", {})
                if (sym.m21_key and sym.m21_key_confidence
                        and sym.m21_key_confidence > k_existing.get("confidence", 0)):
                    result["layer2_key"] = {
                        "key":        sym.m21_key,
                        "mode":       sym.m21_mode or "",
                        "confidence": round(sym.m21_key_confidence, 3),
                        "source":     "music21",
                    }

                # Use symusic tempo if rhythm analyzer returned 0
                if sym.symusic_tempo_bpm and result.get("layer2_rhythm", {}).get("tempo_bpm", 0) == 0:
                    result.setdefault("layer2_rhythm", {})["tempo_bpm"] = round(sym.symusic_tempo_bpm, 1)

            except Exception as sym_exc:
                result["layer2_symbolic_error"] = str(sym_exc)
                log.debug("symbolic toolchain error on %s: %s", vgm_path.name, sym_exc)

            # Composer fingerprint vector
            from labs.music_lab.analysis.composer_fingerprint import build_vector
            fingerprint = build_vector(melodic, harmonic, arrangement, layer1)
            result["fingerprint"] = [round(x, 4) for x in fingerprint]

    except Exception as exc:
        result["layer2_error"] = f"{exc}"
        log.warning("Layer 2 error on %s: %s", vgm_path.name, exc)

    # --- Layer 3: MIR (chip proxy since no rendered audio) ---
    try:
        from labs.music_lab.analysis.audio_features.mir_extractor import extract as mir_extract
        mir = mir_extract(vgm_path)
        if mir:
            result["layer3_mir"] = {k: round(v, 4) if isinstance(v, float) else v
                                    for k, v in mir.items()}
    except Exception:
        pass  # MIR is always optional

    # --- Ludomusicology: loop + energy + gameplay role ---
    try:
        if score is not None and score.note_count > 0:
            from labs.music_lab.analysis.ludomusicology.loop_detector import analyze_loop
            from labs.music_lab.analysis.ludomusicology.energy_curve import analyze_energy
            from labs.music_lab.analysis.ludomusicology.gameplay_role import classify

            loop_result   = analyze_loop(score)
            energy_result = analyze_energy(score)
            role_result   = classify({**result})  # pass all layers so far

            result["ludomusicology"] = {
                **loop_result.to_dict(),
                **energy_result.to_dict(),
                **role_result.to_dict(),
            }
    except Exception as exc:
        result["ludomusicology_error"] = str(exc)
        log.debug("Ludomusicology error on %s: %s", vgm_path.name, exc)

    # --- vgm2txt annotation (if compiled) ---
    try:
        from labs.music_lab.analysis.tool_bridge import vgm2txt, available_tools
        if available_tools().get("vgm2txt"):
            events = vgm2txt(vgm_path)
            result["vgm2txt_event_count"] = len(events)
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Cluster + attribution analysis
# ---------------------------------------------------------------------------

def _track_id_from_stem(stem: str) -> str:
    """Extract leading 2-digit track number from filename stem."""
    import re
    m = re.match(r"^(\d{2})", stem)
    return m.group(1) if m else stem[:2]


def build_composer_profiles(
    track_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build ComposerProfiler from results with known composer assignments."""
    from labs.music_lab.analysis.composer_fingerprint import ComposerProfiler

    profiler = ComposerProfiler()
    unattributed: list[dict[str, Any]] = []

    for r in track_results:
        if "fingerprint" not in r:
            continue
        tid = _track_id_from_stem(r["track_name"])
        composer = S3K_KNOWN_COMPOSERS.get(tid)
        if composer:
            profiler.add_track(r["track_name"], r["fingerprint"], composer)
        else:
            unattributed.append(r)

    profiler.finalize()

    # Predict composers for unattributed tracks
    predictions: list[dict[str, Any]] = []
    for r in unattributed:
        preds = profiler.predict(r["fingerprint"], top_k=3)
        knn   = profiler.knn_predict(r["fingerprint"], k=5)
        predictions.append({
            "track_name":       r["track_name"],
            "centroid_pred":    [{"composer": c, "score": round(s, 4)} for c, s in preds],
            "knn_pred":         [{"composer": c, "vote": round(v, 4)} for c, v in knn],
        })

    return {
        "known_profiles": profiler.to_dict(),
        "unattributed_predictions": predictions,
    }


def cluster_tracks(
    track_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Simple cosine similarity clustering of all tracks with fingerprints.
    Returns a list of cluster dicts sorted by intra-cluster cohesion.
    """
    from labs.music_lab.analysis.composer_fingerprint import _cosine

    # Collect all fingerprints
    fingerprints = [
        (r["track_name"], r["fingerprint"])
        for r in track_results
        if "fingerprint" in r
    ]

    if len(fingerprints) < 3:
        return []

    # Build similarity matrix
    n = len(fingerprints)
    sim_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            s = _cosine(fingerprints[i][1], fingerprints[j][1])
            sim_matrix[i][j] = s
            sim_matrix[j][i] = s

    # Greedy clustering: seed with highest-similarity pair not yet clustered
    clustered = set()
    clusters: list[dict[str, Any]] = []
    THRESHOLD = 0.85  # cosine similarity threshold for same cluster

    for i in range(n):
        if i in clustered:
            continue
        cluster_members = [fingerprints[i][0]]
        clustered.add(i)
        for j in range(n):
            if j != i and j not in clustered and sim_matrix[i][j] >= THRESHOLD:
                cluster_members.append(fingerprints[j][0])
                clustered.add(j)

        if len(cluster_members) > 1:
            # Intra-cluster mean similarity
            idxs = [k for k, (nm, _) in enumerate(fingerprints) if nm in cluster_members]
            pairs = [(idxs[a], idxs[b]) for a in range(len(idxs)) for b in range(a + 1, len(idxs))]
            cohesion = sum(sim_matrix[a][b] for a, b in pairs) / max(len(pairs), 1)
            clusters.append({
                "members":  cluster_members,
                "size":     len(cluster_members),
                "cohesion": round(cohesion, 4),
            })

    clusters.sort(key=lambda c: (-c["size"], -c["cohesion"]))
    return clusters


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def _write_report(
    track_results: list[dict[str, Any]],
    profiles: dict[str, Any],
    clusters: list[dict[str, Any]],
    output_path: Path,
) -> None:
    lines: list[str] = [
        "# Sonic 3 & Knuckles — Composer Pattern Analysis Report",
        "",
        f"**Tracks analyzed:** {len(track_results)}  ",
        f"**Tracks with fingerprints:** {sum(1 for r in track_results if 'fingerprint' in r)}  ",
        "",
        "---",
        "",
        "## Layer 2 Summary: Key & Tempo",
        "",
        "| Track | Key | Mode | Conf | BPM | Syncopation | Beat Reg |",
        "|-------|-----|------|------|-----|-------------|----------|",
    ]
    for r in track_results:
        k = r.get("layer2_key", {})
        rh = r.get("layer2_rhythm", {})
        lines.append(
            f"| {r['track_name']} "
            f"| {k.get('key','?')} "
            f"| {k.get('mode','?')} "
            f"| {k.get('confidence','?')} "
            f"| {rh.get('tempo_bpm','?')} "
            f"| {rh.get('syncopation','?')} "
            f"| {rh.get('beat_regularity','?')} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Composer Attribution (known tracks → profiler trained, unknown → predicted)",
        "",
        "### Known profiles",
        "",
    ]
    for composer, info in profiles.get("known_profiles", {}).items():
        lines.append(f"- **{composer}**: {info['track_count']} tracks — {', '.join(info['track_ids'])}")

    lines += ["", "### Attribution predictions for unattributed tracks", ""]
    for pred in profiles.get("unattributed_predictions", []):
        top = pred["centroid_pred"][0] if pred["centroid_pred"] else {}
        knn_top = pred["knn_pred"][0] if pred["knn_pred"] else {}
        lines.append(
            f"- **{pred['track_name']}**: centroid → {top.get('composer','?')} "
            f"({top.get('score','?'):.3f}), "
            f"knn → {knn_top.get('composer','?')} ({knn_top.get('vote','?'):.2f})"
        )

    lines += [
        "",
        "---",
        "",
        "## Style Clusters (cosine similarity ≥ 0.85)",
        "",
    ]
    for i, cl in enumerate(clusters, 1):
        lines.append(f"**Cluster {i}** (cohesion={cl['cohesion']}): {', '.join(cl['members'])}")

    lines += [
        "",
        "---",
        "",
        "## Melodic Style Comparison",
        "",
        "| Track | Step% | Leap% | PhraseLen | Motifs | Repeat |",
        "|-------|-------|-------|-----------|--------|--------|",
    ]
    for r in track_results:
        m = r.get("layer2_melodic", {})
        if m:
            lines.append(
                f"| {r['track_name']} "
                f"| {m.get('stepwise_ratio','?')} "
                f"| {m.get('leap_ratio','?')} "
                f"| {m.get('phrase_len_mean','?')} "
                f"| {m.get('motif_4gram_count','?')} "
                f"| {m.get('repetition_score','?')} |"
            )

    lines += [
        "",
        "---",
        "",
        "## Harmonic Language",
        "",
        "| Track | Dom.Chord | ProgEntropy | Bassline Step% | ChromaDensity |",
        "|-------|-----------|-------------|----------------|----------------|",
    ]
    for r in track_results:
        h = r.get("layer2_harmonic", {})
        if h:
            lines.append(
                f"| {r['track_name']} "
                f"| {h.get('dominant_chord_family','?')} "
                f"| {h.get('chord_progression_entropy','?')} "
                f"| {h.get('bassline_step_ratio','?')} "
                f"| {h.get('chromatic_density','?')} |"
            )

    lines += [
        "",
        "---",
        "",
        "## Arrangement Structure",
        "",
        "| Track | Lead Ch | Bass Ch | Sections | Breakdown% | Handoffs |",
        "|-------|---------|---------|----------|------------|----------|",
    ]
    for r in track_results:
        a = r.get("layer2_arrangement", {})
        if a:
            lines.append(
                f"| {r['track_name']} "
                f"| {a.get('lead_channel','?')} "
                f"| {a.get('bass_channel','?')} "
                f"| {a.get('section_count','?')} "
                f"| {a.get('breakdown_fraction','?')} "
                f"| {a.get('handoff_count','?')} |"
            )

    lines += [
        "",
        "---",
        "",
        "## Ludomusicology — Loop & Energy",
        "",
        "| Track | LoopStability | EnergyCurve | EnergyVar | GameplayRole | RoleConf |",
        "|-------|--------------|-------------|-----------|--------------|----------|",
    ]
    for r in track_results:
        ludo = r.get("ludomusicology", {})
        if ludo:
            lines.append(
                f"| {r['track_name']} "
                f"| {ludo.get('loop_stability_index','?')} "
                f"| {ludo.get('energy_ramp_type','?')} "
                f"| {ludo.get('energy_variance','?')} "
                f"| {ludo.get('gameplay_role','?')} "
                f"| {ludo.get('gameplay_role_confidence','?')} |"
            )

    output_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(limit: int | None = None, dry_run: bool = False) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    log.info("S3K Analysis Pipeline")
    log.info("  Source: %s", S3K_PATH)
    log.info("  Output: %s", ARTIFACTS_DIR)

    if not S3K_PATH.exists():
        log.error("S3K_PATH does not exist: %s", S3K_PATH)
        sys.exit(1)

    vgm_files = sorted(
        [p for p in S3K_PATH.iterdir() if p.suffix.lower() in (".vgm", ".vgz")],
        key=lambda p: p.name,
    )

    if limit:
        vgm_files = vgm_files[:limit]

    log.info("  Files: %d", len(vgm_files))

    if dry_run:
        for f in vgm_files:
            log.info("  DRY-RUN: would analyze %s", f.name)
        return

    TRACK_RESULTS.mkdir(parents=True, exist_ok=True)

    # Check tool availability
    from labs.music_lab.analysis.tool_bridge import available_tools
    tools = available_tools()
    log.info("  Tools available: %s", tools)

    track_results: list[dict[str, Any]] = []
    t0 = time.time()

    for i, vgm_path in enumerate(vgm_files, 1):
        log.info("[%02d/%02d] %s", i, len(vgm_files), vgm_path.name)
        result = analyze_track(vgm_path)
        track_results.append(result)

        # Save per-track result
        out_path = TRACK_RESULTS / f"{vgm_path.stem}.json"
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    elapsed = time.time() - t0
    log.info("Analysis complete — %d tracks in %.1fs", len(track_results), elapsed)

    # Composer profiles + clustering
    log.info("Building composer profiles...")
    profiles = build_composer_profiles(track_results)
    (ARTIFACTS_DIR / "composer_profiles.json").write_text(
        json.dumps(profiles, indent=2), encoding="utf-8"
    )

    log.info("Clustering tracks...")
    clusters = cluster_tracks(track_results)
    (ARTIFACTS_DIR / "clustering_report.json").write_text(
        json.dumps({"clusters": clusters, "track_count": len(track_results)}, indent=2),
        encoding="utf-8",
    )

    # --- Style space mapping (Layer 7: PCA/UMAP/t-SNE) ---
    style_space_dict: dict[str, Any] = {}
    try:
        from labs.music_lab.analysis.style_space import compute as style_space_compute
        fp_tracks  = [(r["track_name"], r["fingerprint"]) for r in track_results if "fingerprint" in r]
        if len(fp_tracks) >= 3:
            ids, vecs = zip(*fp_tracks)
            track_labels = [S3K_KNOWN_COMPOSERS.get(_track_id_from_stem(tid)) for tid in ids]
            ss = style_space_compute(list(ids), list(vecs), labels=list(track_labels))
            style_space_dict = ss.to_dict()
            (ARTIFACTS_DIR / "style_space.json").write_text(
                json.dumps(style_space_dict, indent=2), encoding="utf-8"
            )
            log.info("Style space: %d points, PCA variance=%s",
                     len(ids), ss.pca_variance_explained[:2])
    except Exception as exc:
        log.warning("Style space failed: %s", exc)

    # --- Pattern discovery (Layer 8: HDBSCAN/k-means/network) ---
    pattern_dict: dict[str, Any] = {}
    try:
        from labs.music_lab.analysis.pattern_discovery import discover as discover_patterns
        fp_tracks = [(r["track_name"], r["fingerprint"]) for r in track_results if "fingerprint" in r]
        if len(fp_tracks) >= 3:
            ids, vecs = zip(*fp_tracks)
            track_labels = [S3K_KNOWN_COMPOSERS.get(_track_id_from_stem(tid)) for tid in ids]
            mel_feats = [next((r.get("layer2_melodic") for r in track_results
                               if r["track_name"] == tid), None) for tid in ids]
            l1_feats  = [next((r.get("layer1") for r in track_results
                               if r["track_name"] == tid), None) for tid in ids]
            patterns = discover_patterns(
                list(ids), list(vecs),
                labels=list(track_labels),
                melodic_features=mel_feats,
                layer1_data=l1_feats,
            )
            pattern_dict = patterns.to_dict()
            (ARTIFACTS_DIR / "pattern_discovery.json").write_text(
                json.dumps(pattern_dict, indent=2), encoding="utf-8"
            )
            log.info("Pattern discovery: %d similarity edges, %d motif families",
                     len(patterns.similarity_edges), len(patterns.motif_families))
    except Exception as exc:
        log.warning("Pattern discovery failed: %s", exc)

    log.info("Writing analysis report...")
    _write_report(
        track_results, profiles, clusters,
        ARTIFACTS_DIR / "analysis_report.md",
    )

    # --- LLM interpretation (Layer 9) ---
    try:
        from labs.music_lab.analysis.llm_interpreter import interpret_corpus, available as llm_available
        if llm_available():
            log.info("Generating LLM corpus interpretation...")
            corpus_insight = interpret_corpus(
                profiles=profiles,
                clusters=pattern_dict if pattern_dict else {"cosine_clusters": {"n_clusters": len(clusters)}},
                style_space=style_space_dict or None,
                patterns=pattern_dict or None,
                n_tracks=len(track_results),
                soundtrack="Sonic 3 & Knuckles",
            )
            (ARTIFACTS_DIR / "llm_interpretation.json").write_text(
                json.dumps(corpus_insight, indent=2), encoding="utf-8"
            )
            log.info("LLM interpretation saved.")
        else:
            log.info("LLM interpretation skipped (ANTHROPIC_API_KEY not set or anthropic not installed)")
    except Exception as exc:
        log.warning("LLM interpretation failed: %s", exc)

    # --- Knowledge Graph: build + link + save ---
    try:
        from labs.music_lab.knowledge.composer_graph import get_graph, reset_graph
        from labs.music_lab.knowledge.linker import link_pipeline_output
        from labs.music_lab.knowledge.composer_store import ComposerStore

        reset_graph()
        kg = get_graph(seed=True)   # seed with base S3K data

        # Ingest Sonic Retro HTML (adds per-track credits + full staff list)
        try:
            from labs.music_lab.knowledge.sources.sonic_retro_ingester import ingest_s3k_default
            sr_result = ingest_s3k_default(kg)
            log.info("KG: Sonic Retro ingest → %s", sr_result)
        except Exception as exc:
            log.warning("KG: Sonic Retro ingest failed: %s", exc)

        # Link analysis results into graph
        # track_results is a list; linker expects dict keyed by track_id
        track_results_by_id = {
            r.get("track_name", r.get("file", str(i))): r
            for i, r in enumerate(track_results)
        }
        link_summary = link_pipeline_output(
            graph=kg,
            track_results=track_results_by_id,
            composer_profiles=profiles if isinstance(profiles, list) else [],
            cluster_result=pattern_dict if pattern_dict else None,
            style_space=style_space_dict if style_space_dict else None,
        )
        log.info("KG: link_pipeline_output → %s", link_summary)

        # Save graph
        store = ComposerStore(ARTIFACTS_DIR)
        store.save(kg)
        log.info("KG: graph saved to %s", ARTIFACTS_DIR)

        # Export graph stats
        (ARTIFACTS_DIR / "knowledge_graph_stats.json").write_text(
            json.dumps(kg.graph_stats(), indent=2), encoding="utf-8"
        )

        # VGMPF technical enrichment (always available, no network)
        try:
            from labs.music_lab.knowledge.sources.vgmpf_ingester import (
                enrich_all_composers, enrich_driver_node,
            )
            n_enriched = enrich_all_composers(list(kg._composers.values()))
            for d in kg.all_drivers():
                enrich_driver_node(d)
            log.info("KG: VGMPF enriched %d composers + %d drivers", n_enriched, len(kg.all_drivers()))
        except Exception as exc:
            log.warning("KG: VGMPF enrichment failed: %s", exc)

        # Build fingerprint vectors dict for queries/reports
        vec_dict: dict[str, list[float]] = {}
        for tr in track_results:
            track_id = tr.get("track_name", tr.get("file", ""))
            fv = tr.get("layer5_fingerprint") or tr.get("fingerprint_vector")
            if track_id and isinstance(fv, list) and fv:
                vec_dict[track_id] = fv

        # Reports
        try:
            from labs.music_lab.knowledge.report_generator import generate_all as gen_reports
            reports_dir = ARTIFACTS_DIR / "knowledge_reports"
            report_paths = gen_reports("sonic_3_and_knuckles", kg, vec_dict, reports_dir)
            log.info("KG: generated %d report files in %s",
                     sum(len(v) for v in report_paths.values()), reports_dir)
        except Exception as exc:
            log.warning("KG: report generation failed: %s", exc)

        # Visualizations (GEXF + DOT always; PNG if matplotlib available)
        try:
            from labs.music_lab.knowledge.visualizer import render_all as viz_all
            viz_dir = ARTIFACTS_DIR / "knowledge_viz"
            viz_results = viz_all(
                "sonic_3_and_knuckles", kg, vec_dict, viz_dir,
                formats=["gexf", "dot", "png"],
            )
            n_files = sum(len(v) for v in viz_results.values())
            log.info("KG: generated %d visualization files in %s", n_files, viz_dir)
        except Exception as exc:
            log.warning("KG: visualization failed: %s", exc)

        # Style queries report
        try:
            from labs.music_lab.knowledge.style_queries import StyleQueryEngine
            sq = StyleQueryEngine(kg, vec_dict)
            sq_out: dict[str, Any] = {}
            for c in kg.all_composers():
                if vec_dict:
                    sq_out[c.composer_id] = sq.full_style_report(
                        c.composer_id, game_id="sonic_3_and_knuckles"
                    )
            (ARTIFACTS_DIR / "style_query_report.json").write_text(
                json.dumps(sq_out, indent=2), encoding="utf-8"
            )
            log.info("KG: style query report written for %d composers", len(sq_out))
        except Exception as exc:
            log.warning("KG: style queries failed: %s", exc)

    except Exception as exc:
        log.warning("Knowledge graph step failed: %s", exc)

    log.info("Done.  Artifacts: %s", ARTIFACTS_DIR)
    log.info("Output files:")
    for f in sorted(ARTIFACTS_DIR.glob("*.json")) + sorted(ARTIFACTS_DIR.glob("*.md")):
        log.info("  %s", f.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="S3K Composer Pattern Analysis Pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Max tracks to analyze")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(limit=args.limit, dry_run=args.dry_run)
