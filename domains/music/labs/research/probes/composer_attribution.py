"""
composer_attribution.py — Per-track composer attribution via style fingerprinting.

Spec: docs/research/composer_attribution_spec.md

How it works
------------
The library stores per-track composer credits from tags (label='unknown').
For single-composer albums, those credits are reliable training data.
For multi-composer albums, we use the album's composer pool as candidates
and ask: does this track's musical fingerprint agree with its tag credit?

Phases
------
  --build-centroids   Read analysis artifacts for tracks in *single-composer albums*.
                      Compute per-composer style centroids.
                      Output → codex/atlas/music/composers/*.json

  --score             For each track in a *multi-composer album*, score against the
                      album's composer pool. If fingerprint agrees with tag credit →
                      label 'estimated_confirmed'. If not → label 'contested'.
                      Output → updated attribution field in library records.

  --validate          Hold-out validation: find albums where per-track credits are
                      label='known'. Measure precision/recall. Prints report, no writes.

Usage
-----
  python domains/music/model/probes/composer_attribution.py --build-centroids
  python domains/music/model/probes/composer_attribution.py --validate
  python domains/music/model/probes/composer_attribution.py --score --min-confidence 0.60
  python domains/music/model/probes/composer_attribution.py --score --album sonic_3_knuckles
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir())
sys.path.insert(0, str(ROOT))

LIB_ALBUM   = ROOT / "codex" / "library" / "music" / "album"
ARTIFACTS   = ROOT / "domains" / "language" / "artifacts" / "analysis"
ATLAS_COMP  = ROOT / "codex" / "atlas" / "music" / "composers"

# Minimum solo-credited tracks (from single-composer albums) to build a reliable centroid.
MIN_SOLO_TRACKS = 5

# Tiers that have symbolic (music21) analysis — both old and new naming.
SYMBOLIC_TIERS = {"AB", "B", "A+D", "A+D+C"}

# Features used in the fingerprint vector.
NUMERIC_FEATURES = [
    # Harmonic
    "harmonic_rhythm",
    "dissonance_density",
    "interval_roughness",
    # Melodic
    "pitch_range",
    "step_ratio",         # derived: intervals ≤2 semitones / total intervals
    "upper_pitch_mean",
    # Rhythmic
    "tempo_bpm",
    "rhythmic_entropy",
    "off_beat_ratio",
    "pulse_coherence",
    # Orchestration
    "active_voices",
    "bass_channel_mean_pitch",
]

CATEGORICAL_FEATURES = [
    "key_mode",
    "melodic_contour",
]


# ---------------------------------------------------------------------------
# Album index helpers
# ---------------------------------------------------------------------------

def _load_album_index() -> dict[str, list[str]]:
    """
    Returns {album_slug → [artist_id, ...]} from album.json files.
    """
    index: dict[str, list[str]] = {}
    for album_dir in LIB_ALBUM.iterdir():
        if not album_dir.is_dir():
            continue
        album_json = album_dir / "album.json"
        if album_json.exists():
            try:
                rec = json.loads(album_json.read_text(encoding="utf-8"))
                aids = rec.get("artist_ids", []) or rec.get("metadata", {}).get("artist_ids", [])
                index[album_dir.name] = aids
            except Exception:
                index[album_dir.name] = []
    return index


def _artifact_path(entity_id: str) -> Path:
    slug = entity_id.replace(":", "_").replace(".", "_")
    return ARTIFACTS / f"{slug}.json"


def _load_artifact(entity_id: str) -> Optional[dict]:
    af = _artifact_path(entity_id)
    if not af.exists():
        return None
    try:
        return json.loads(af.read_text(encoding="utf-8")).get("analysis", {})
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(analysis: dict) -> dict[str, float | str | None]:
    """
    Pull the fingerprint feature vector from a raw analysis dict.
    Returns dict of feature_name → value (None if unavailable).
    """
    sym = analysis.get("symbolic") or {}
    if isinstance(sym, dict) and sym.get("error"):
        sym = {}

    note_events = analysis.get("note_events", [])

    f: dict[str, float | str | None] = {}

    # Harmonic
    f["harmonic_rhythm"]    = _f(sym, "harmonic_rhythm")
    f["dissonance_density"] = _f(sym, "dissonance_density")
    f["interval_roughness"] = _f(sym, "interval_roughness")

    # Melodic
    f["pitch_range"]        = _f(sym, "pitch_range")
    f["upper_pitch_mean"]   = _f(sym, "upper_pitch_mean")
    f["melodic_contour"]    = sym.get("melodic_contour")
    f["key_mode"]           = sym.get("mode")

    # Compute step_ratio from note_events if available
    if note_events:
        pitches = sorted(
            e["pitch_midi"] for e in note_events
            if isinstance(e, dict) and e.get("pitch_midi", -1) >= 0
        )
        if len(pitches) >= 2:
            intervals = [abs(pitches[i+1] - pitches[i]) for i in range(len(pitches)-1)]
            steps = sum(1 for x in intervals if x <= 2)
            f["step_ratio"] = steps / len(intervals)
        else:
            f["step_ratio"] = None
    else:
        f["step_ratio"] = None

    # Rhythmic
    f["tempo_bpm"]        = _f(sym, "tempo_bpm")
    f["rhythmic_entropy"] = _f(sym, "rhythmic_entropy")
    f["off_beat_ratio"]   = _f(sym, "off_beat_ratio")
    f["pulse_coherence"]  = _f(sym, "pulse_coherence")

    # Orchestration
    f["active_voices"]           = _f(analysis, "active_voices")
    f["bass_channel_mean_pitch"] = _channel_bass_mean(sym)

    return f


def _f(d: dict, key: str) -> float | None:
    v = d.get(key)
    if v is None:
        return None
    try:
        fv = float(v)
        return fv if math.isfinite(fv) else None
    except (TypeError, ValueError):
        return None


def _channel_bass_mean(sym: dict) -> float | None:
    means   = sym.get("channel_pitch_means", {})
    bass_ch = sym.get("bass_channel", -1)
    if bass_ch is not None and bass_ch >= 0:
        v = means.get(str(bass_ch)) or means.get(bass_ch)
        return float(v) if v is not None else None
    return None


def _compute_centroids_from_accum(accum: dict[str, list[dict]]) -> dict[str, dict]:
    """Compute raw centroid dicts from an accumulator. No MIN_SOLO_TRACKS filter."""
    centroids: dict[str, dict] = {}
    for composer, track_feats in accum.items():
        n = len(track_feats)
        if n < 3:
            continue
        centroid: dict = {"n_tracks": n, "tracks": [f["_entity_id"] for f in track_feats]}
        numeric: dict[str, list[float]] = defaultdict(list)
        categorical: dict[str, list]    = defaultdict(list)
        for feats in track_feats:
            for fname in NUMERIC_FEATURES:
                v = feats.get(fname)
                if v is not None:
                    numeric[fname].append(v)
            for fname in CATEGORICAL_FEATURES:
                v = feats.get(fname)
                if v is not None:
                    categorical[fname].append(v)
        centroid["numeric"] = {}
        for fname, vals in numeric.items():
            if vals:
                mean     = sum(vals) / len(vals)
                variance = sum((x - mean) ** 2 for x in vals) / len(vals)
                centroid["numeric"][fname] = {"mean": mean, "std": math.sqrt(variance), "n": len(vals)}
        centroid["categorical"] = {}
        for fname, vals in categorical.items():
            counts: dict = {}
            for v in vals:
                counts[v] = counts.get(v, 0) + 1
            total = sum(counts.values())
            centroid["categorical"][fname] = {k: v / total for k, v in sorted(counts.items(), key=lambda x: -x[1])}
        centroids[composer] = centroid
    return centroids


def _primary_chip(analysis: dict) -> str:
    chips = analysis.get("chips", [])
    return chips[0] if chips else "unknown"


# ---------------------------------------------------------------------------
# Centroid building
# ---------------------------------------------------------------------------

def build_centroids(verbose: bool = False) -> dict:
    """
    Build per-composer style centroids from tracks in *single-composer albums*.

    A single-composer album is one whose album.json has exactly one artist_id.
    All tracks in that album are treated as reliable solo-credit data for that composer.

    Returns centroid dict: { artist_id → { feature → {mean, std, n} } }
    """
    album_index = _load_album_index()

    # Single-composer album slugs → artist_id
    solo_albums = {
        slug: aids[0]
        for slug, aids in album_index.items()
        if len(aids) == 1
    }
    print(f"Single-composer albums: {len(solo_albums):,}")

    # Step 1: Load analysis artifacts for solo-album tracks
    print("Loading analysis artifacts...")
    accum: dict[str, list[dict]] = defaultdict(list)   # artist_id → [feature_dicts]
    total_tracks = 0
    usable_tracks = 0

    for album_slug, composer in solo_albums.items():
        album_dir = LIB_ALBUM / album_slug
        if not album_dir.is_dir():
            continue

        for lib_file in album_dir.glob("*.json"):
            if lib_file.name == "album.json":
                continue
            try:
                lib_rec = json.loads(lib_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            total_tracks += 1
            eid = lib_rec.get("id", "")
            analysis = _load_artifact(eid)
            if not analysis:
                continue

            tier = analysis.get("analysis_tier", "")
            if tier not in SYMBOLIC_TIERS:
                continue

            feats = extract_features(analysis)
            feats["_entity_id"] = eid
            feats["_chip"]      = _primary_chip(analysis)
            accum[composer].append(feats)
            usable_tracks += 1

    print(f"  {total_tracks:,} solo-album tracks found")
    print(f"  {usable_tracks:,} with symbolic analysis")
    print(f"  {len(accum):,} composers with at least one track")

    # Step 2: Compute initial centroids (first pass — may include foreign tracks)
    centroids_pass1 = _compute_centroids_from_accum(accum)
    if len(centroids_pass1) >= 2:
        weights_pass1 = compute_discriminant_weights(centroids_pass1)
        # Self-consistency filter: drop tracks that score higher for a *different*
        # composer than the one they're attributed to. This catches the common case
        # of "album is credited to A but track 7 was actually by B".
        purged = 0
        for composer, track_feats_list in accum.items():
            kept = []
            for feats in track_feats_list:
                all_composers = list(centroids_pass1.keys())
                ranked = score_track(feats, all_composers, centroids_pass1, weights_pass1)
                top_c, top_p = ranked[0]
                if top_c == composer or top_p < 0.65:
                    # Consistent with tag OR not strongly attributed elsewhere → keep
                    kept.append(feats)
                else:
                    purged += 1
            accum[composer] = kept
        if purged:
            print(f"  Self-consistency pass: dropped {purged} tracks inconsistent with their album credit")

    # Step 3: Compute final centroids from filtered accum (apply MIN_SOLO_TRACKS)
    if verbose:
        for composer, track_feats in accum.items():
            if len(track_feats) < MIN_SOLO_TRACKS:
                print(f"  skip {composer}: only {len(track_feats)} tracks (< {MIN_SOLO_TRACKS})")

    filtered_accum = {c: t for c, t in accum.items() if len(t) >= MIN_SOLO_TRACKS}
    centroids = _compute_centroids_from_accum(filtered_accum)

    if verbose:
        for composer, centroid in centroids.items():
            print(f"  {composer}: {centroid['n_tracks']} tracks → centroid built")

    print(f"\n{len(centroids):,} composer centroids built (>= {MIN_SOLO_TRACKS} tracks)")
    return centroids


# ---------------------------------------------------------------------------
# Fisher discriminant weights
# ---------------------------------------------------------------------------

def compute_discriminant_weights(centroids: dict) -> dict[str, float]:
    """
    Compute Fisher discriminant ratio per feature:
        weight[f] = between_composer_variance[f] / within_composer_variance[f]

    Higher weight = feature better distinguishes composers.
    """
    feature_means: dict[str, list[float]] = defaultdict(list)
    feature_stds:  dict[str, list[float]] = defaultdict(list)

    for centroid in centroids.values():
        for fname, stats in centroid.get("numeric", {}).items():
            feature_means[fname].append(stats["mean"])
            feature_stds[fname].append(stats["std"])

    weights: dict[str, float] = {}
    for fname in NUMERIC_FEATURES:
        means = feature_means.get(fname, [])
        stds  = feature_stds.get(fname, [])
        if len(means) < 2:
            weights[fname] = 1.0
            continue

        grand_mean  = sum(means) / len(means)
        between_var = sum((m - grand_mean) ** 2 for m in means) / len(means)
        within_var  = sum(s ** 2 for s in stds) / len(stds) if stds else 1.0
        within_var  = max(within_var, 1e-6)

        weights[fname] = between_var / within_var

    max_w = max(weights.values()) if weights else 1.0
    if max_w > 0:
        weights = {k: v / max_w for k, v in weights.items()}

    return weights


# ---------------------------------------------------------------------------
# Attribution scoring
# ---------------------------------------------------------------------------

def score_track(
    feats: dict,
    candidates: list[str],
    centroids: dict,
    weights: dict[str, float],
) -> list[tuple[str, float]]:
    """
    Score a track's features against each candidate composer's centroid.
    Returns list of (artist_id, probability) sorted by descending probability.
    """
    raw_scores: dict[str, float] = {}

    for composer in candidates:
        centroid = centroids.get(composer)
        if not centroid:
            raw_scores[composer] = 0.0
            continue

        score      = 0.0
        weight_sum = 0.0

        # Numeric features: Gaussian log-likelihood proxy
        for fname in NUMERIC_FEATURES:
            v = feats.get(fname)
            if v is None:
                continue
            stats = centroid["numeric"].get(fname)
            if not stats:
                continue

            mu  = stats["mean"]
            std = max(stats["std"], 0.01)
            w   = weights.get(fname, 1.0)

            z = (v - mu) / std
            score      += w * math.exp(-0.5 * z * z)
            weight_sum += w

        # Categorical features: soft log-probability contribution
        for fname in CATEGORICAL_FEATURES:
            v = feats.get(fname)
            if v is None:
                continue
            dist = centroid["categorical"].get(fname, {})
            prob = dist.get(v, 0.01)
            score += math.log(prob + 1e-9) * 0.5

        if weight_sum > 0:
            score = score / weight_sum
        raw_scores[composer] = max(score, 1e-9)

    # Softmax-style normalisation → probabilities
    total = sum(raw_scores.values())
    if total <= 0:
        n = len(candidates)
        return [(c, 1.0 / n) for c in candidates]

    probs = [(c, s / total) for c, s in raw_scores.items()]
    return sorted(probs, key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_build_centroids(verbose: bool = False) -> None:
    centroids = build_centroids(verbose=verbose)
    weights   = compute_discriminant_weights(centroids)

    ATLAS_COMP.mkdir(parents=True, exist_ok=True)

    for composer_id, centroid in centroids.items():
        slug = composer_id.split(".")[-1]
        out  = ATLAS_COMP / f"{slug}.json"
        payload = {
            "id":                   composer_id,
            "type":                 "ComposerStyleCentroid",
            "pipeline_version":     "attribution_v1",
            "n_tracks":             centroid["n_tracks"],
            "source_tracks":        centroid["tracks"],
            "numeric":              centroid["numeric"],
            "categorical":          centroid["categorical"],
            "discriminant_weights": weights,
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"\nWrote {len(centroids)} centroid files to {ATLAS_COMP}")
    print("\nTop discriminating features:")
    for fname, w in sorted(weights.items(), key=lambda x: -x[1])[:8]:
        print(f"  {fname:<30} {w:.3f}")


def run_score(
    min_confidence: float = 0.55,
    album_slug: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """
    For each track in a multi-composer album, score its fingerprint against the
    album's composer pool and check whether it agrees with the tag attribution.

    If the fingerprint top-match == tag credit AND confidence >= threshold:
      → set label 'estimated_confirmed'
    If the fingerprint top-match != tag credit:
      → set label 'contested', include ranked candidates
    """
    centroids: dict[str, dict] = {}
    if not ATLAS_COMP.exists():
        print("ERROR: No centroids found. Run --build-centroids first.")
        sys.exit(1)

    for f in ATLAS_COMP.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cid = data.get("id")
            if cid:
                centroids[cid] = data
        except Exception:
            pass

    if not centroids:
        print("ERROR: Centroid directory exists but no composer JSONs found.")
        sys.exit(1)

    weights: dict[str, float] = {}
    for data in centroids.values():
        if "discriminant_weights" in data:
            weights = data["discriminant_weights"]
            break

    album_index = _load_album_index()
    # Multi-composer albums: album has >= 2 composers
    multi_albums = {
        slug: aids
        for slug, aids in album_index.items()
        if len(aids) >= 2
    }

    print(f"Loaded {len(centroids)} composer centroids")
    print(f"Multi-composer albums to score: {len(multi_albums):,}")
    print(f"Min confidence: {min_confidence}")

    confirmed = 0
    contested = 0
    no_centroid = 0
    skipped   = 0

    for slug, album_composers in multi_albums.items():
        if album_slug and slug != album_slug:
            continue

        album_dir = LIB_ALBUM / slug
        if not album_dir.is_dir():
            continue

        # Candidates = composers in this album who have centroids
        candidates = [c for c in album_composers if c in centroids]
        if len(candidates) < 2:
            no_centroid += len(list(album_dir.glob("*.json"))) - 1
            continue

        for lib_file in album_dir.glob("*.json"):
            if lib_file.name == "album.json":
                continue

            try:
                lib_rec = json.loads(lib_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            eid           = lib_rec.get("id", "")
            tag_composer  = (lib_rec.get("metadata", {}).get("artist_ids") or [None])[0]
            analysis      = _load_artifact(eid)

            if not analysis:
                skipped += 1
                continue

            tier = analysis.get("analysis_tier", "")
            if tier not in SYMBOLIC_TIERS:
                skipped += 1
                continue

            feats  = extract_features(analysis)
            ranked = score_track(feats, candidates, centroids, weights)
            top_composer, top_prob = ranked[0]

            # Write fingerprint output to a separate field — never overwrite
            # the user's original composition_credit (tag-derived, may be a guess
            # but is the best available data and shouldn't be clobbered).
            fingerprint_result = {
                "top_match":       top_composer,
                "top_score":       round(top_prob, 4),
                "agrees_with_tag": top_composer == tag_composer,
                "candidates": [
                    {"artist_id": c, "score": round(s, 4)} for c, s in ranked
                ],
                "features_used": [
                    fn for fn in NUMERIC_FEATURES + CATEGORICAL_FEATURES
                    if feats.get(fn) is not None
                ],
                "centroid_n": {
                    c: centroids[c]["n_tracks"] for c in candidates if c in centroids
                },
                "source": "style_fingerprint_v1",
            }

            if top_composer == tag_composer and top_prob >= min_confidence:
                fingerprint_result["verdict"] = "confirmed"
                confirmed += 1
            else:
                fingerprint_result["verdict"] = "contested"
                fingerprint_result["tag_credit"] = tag_composer
                contested += 1

            if not dry_run:
                lib_rec.setdefault("attribution", {})
                lib_rec["attribution"]["fingerprint"] = fingerprint_result
                lib_file.write_text(
                    json.dumps(lib_rec, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )

    print(f"\nScoring complete:")
    print(f"  Confirmed (fingerprint agrees with tag): {confirmed:,}")
    print(f"  Contested (fingerprint disagrees):       {contested:,}")
    print(f"  No centroid for album composers:         {no_centroid:,}")
    print(f"  Skipped (no analysis / wrong tier):      {skipped:,}")
    if dry_run:
        print("  [DRY RUN — no files written]")


def run_validate() -> None:
    """
    Measure attribution accuracy on tracks where per-track credits are known
    (attribution.composition_credit.label == 'known').
    """
    centroids: dict[str, dict] = {}
    for f in ATLAS_COMP.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cid  = data.get("id")
            if cid:
                centroids[cid] = data
        except Exception:
            pass

    weights: dict[str, float] = {}
    for data in centroids.values():
        if "discriminant_weights" in data:
            weights = data["discriminant_weights"]
            break

    album_index = _load_album_index()
    correct   = 0
    total     = 0
    contested = 0

    for album_dir in LIB_ALBUM.iterdir():
        if not album_dir.is_dir():
            continue
        album_composers = album_index.get(album_dir.name, [])
        candidates      = [c for c in album_composers if c in centroids]

        for lib_file in album_dir.glob("*.json"):
            if lib_file.name == "album.json":
                continue
            try:
                lib_rec = json.loads(lib_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            credit         = lib_rec.get("attribution", {}).get("composition_credit", {})
            if credit.get("label") != "known":
                continue

            true_composer  = (credit.get("artist_ids") or [None])[0]
            if not true_composer:
                continue

            if len(candidates) < 2:
                continue

            eid      = lib_rec.get("id", "")
            analysis = _load_artifact(eid)
            if not analysis or analysis.get("analysis_tier", "") not in SYMBOLIC_TIERS:
                continue

            feats            = extract_features(analysis)
            ranked           = score_track(feats, candidates, centroids, weights)
            pred_composer, pred_prob = ranked[0]

            total += 1
            if pred_prob < min_confidence:
                contested += 1
            elif pred_composer == true_composer:
                correct += 1

    min_confidence = 0.55
    if total == 0:
        print("No validation tracks found.")
        print("(Need tracks with attribution.composition_credit.label == 'known')")
        return

    decided = total - contested
    acc     = correct / decided if decided > 0 else 0.0
    print(f"\nValidation results on {total} known-credit tracks:")
    print(f"  Decided (>= {min_confidence} conf): {decided}")
    print(f"  Contested:                           {contested}")
    print(f"  Correct / Decided:                   {correct}/{decided} = {acc:.1%}")
    print(f"  Coverage:                             {decided/total:.1%} of tracks above threshold")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--build-centroids", action="store_true",
                   help="Build composer style centroids from single-composer albums")
    p.add_argument("--score", action="store_true",
                   help="Score multi-composer album tracks against centroids")
    p.add_argument("--validate", action="store_true",
                   help="Validate against tracks with label='known' credits")
    p.add_argument("--min-confidence", type=float, default=0.55,
                   help="Min score to confirm/contest an attribution (default: 0.55)")
    p.add_argument("--album", default=None,
                   help="Restrict scoring to one album slug")
    p.add_argument("--dry-run", action="store_true",
                   help="Do not write any files")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    if args.build_centroids:
        run_build_centroids(verbose=args.verbose)
    elif args.score:
        run_score(min_confidence=args.min_confidence,
                  album_slug=args.album,
                  dry_run=args.dry_run)
    elif args.validate:
        run_validate()
    else:
        p.print_help()


if __name__ == "__main__":
    main()

