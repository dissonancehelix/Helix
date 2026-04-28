"""
runner.py — music_lab_cfp_v1 benchmark runner scaffold
=======================================================
Runs the composer fingerprint prediction benchmark end-to-end.
Full model training is NOT implemented here — this is the scaffold
that orchestrates data loading, splitting, feature selection, and
evaluation result serialisation.

Usage:
    python -m substrates.music.benchmarks.music_lab_cfp_v1.runner [options]

Options:
    --split    random|game_held_out   (default: random)
    --features chip|sym|mir|all       (default: all; comma-separated for ablation)
    --dry-run                         Validate data without running models
    --seed     42                     Random seed
    --limit    N                      Cap tracks per composer (0 = no cap)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from substrates.music.config import (
    DB_PATH, ARTIFACTS, FEATURE_VECTOR_VERSION, FEATURE_VECTOR_DIM,
)

BENCH_DIR    = Path(__file__).parent
ARTIFACT_DIR = ARTIFACTS / "benchmarks" / "music_lab_cfp_v1"

# Feature family slice indices (matching feature_vector.py v0 layout)
FAMILY_SLICES = {
    "chip": (0,  12),
    "sym":  (12, 20),
    "mir":  (20, 50),   # MFCC + chroma + spectral
    "all":  (0,  64),
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_dataset(
    db_path: Path = DB_PATH,
    min_tracks: int = 10,
    format_filter: str = "VGM",
) -> dict[str, Any]:
    """
    Load all tracks with ground-truth composer attribution and feature vectors.
    Returns:
        {"track_ids": [...], "vectors": [[...], ...], "labels": [...],
         "metadata": [{title, composer, game, ...}, ...]}
    """
    from substrates.music.db.track_db import TrackDB

    db = TrackDB(db_path)
    ids, mat = db.load_all_vectors(FEATURE_VECTOR_VERSION)
    tracks = {t["track_id"]: t for t in db.get_tracks_by_tier(max_tier=4)}

    track_ids: list[str] = []
    vectors:   list[list[float]] = []
    labels:    list[str] = []
    metadata:  list[dict] = []

    for i, tid in enumerate(ids):
        t = tracks.get(tid)
        if t is None:
            continue
        composer = (t.get("artist") or "").strip()
        if not composer or composer.lower() in ("unknown", "various", ""):
            continue
        fmt = (t.get("format") or "").upper()
        if format_filter and fmt not in format_filter.split(","):
            continue

        vec = mat[i].tolist() if hasattr(mat[i], "tolist") else list(mat[i])
        track_ids.append(tid)
        vectors.append(vec)
        labels.append(composer)
        metadata.append({
            "track_id": tid,
            "title":    t.get("title", ""),
            "composer": composer,
            "game":     t.get("album", ""),
            "format":   fmt,
        })

    # Filter to composers with ≥ min_tracks
    counts = Counter(labels)
    valid_composers = {c for c, n in counts.items() if n >= min_tracks}

    filtered = [
        (tid, vec, lbl, meta)
        for tid, vec, lbl, meta in zip(track_ids, vectors, labels, metadata)
        if lbl in valid_composers
    ]

    if not filtered:
        return {"track_ids": [], "vectors": [], "labels": [], "metadata": [],
                "composer_counts": {}}

    track_ids, vectors, labels, metadata = map(list, zip(*filtered))

    return {
        "track_ids":       track_ids,
        "vectors":         vectors,
        "labels":          labels,
        "metadata":        metadata,
        "composer_counts": dict(counts),
    }


# ---------------------------------------------------------------------------
# Split builders
# ---------------------------------------------------------------------------

def random_split(
    data: dict[str, Any],
    seed: int = 42,
    train_frac: float = 0.70,
    val_frac: float   = 0.15,
) -> dict[str, list[str]]:
    """Stratified random split by composer."""
    rng = random.Random(seed)

    groups: dict[str, list[int]] = defaultdict(list)
    for i, lbl in enumerate(data["labels"]):
        groups[lbl].append(i)

    train_ids, val_ids, test_ids = [], [], []
    for composer, indices in groups.items():
        rng.shuffle(indices)
        n_train = max(1, int(len(indices) * train_frac))
        n_val   = max(1, int(len(indices) * val_frac))
        train_ids.extend(data["track_ids"][i] for i in indices[:n_train])
        val_ids.extend(  data["track_ids"][i] for i in indices[n_train:n_train + n_val])
        test_ids.extend( data["track_ids"][i] for i in indices[n_train + n_val:])

    return {"train": train_ids, "val": val_ids, "test": test_ids}


def game_held_out_split(
    data: dict[str, Any],
) -> dict[str, list[str]]:
    """Hold out the largest game per composer as test set."""
    # Group by (composer, game)
    composer_game_tracks: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    meta_map = {m["track_id"]: m for m in data["metadata"]}

    for tid in data["track_ids"]:
        m   = meta_map.get(tid, {})
        cmp = m.get("composer", "")
        gme = m.get("game", "")
        composer_game_tracks[cmp][gme].append(tid)

    train_ids, test_ids = [], []
    excluded_composers: list[str] = []

    for composer, game_map in composer_game_tracks.items():
        if len(game_map) < 2:
            excluded_composers.append(composer)
            continue
        # Largest game → test
        held_game = max(game_map, key=lambda g: len(game_map[g]))
        test_ids.extend(game_map[held_game])
        for game, tids in game_map.items():
            if game != held_game:
                train_ids.extend(tids)

    return {"train": train_ids, "val": [], "test": test_ids,
            "excluded_single_game_composers": excluded_composers}


# ---------------------------------------------------------------------------
# Feature selection
# ---------------------------------------------------------------------------

def select_features(
    vectors: list[list[float]],
    family: str = "all",
) -> list[list[float]]:
    start, end = FAMILY_SLICES.get(family, (0, FEATURE_VECTOR_DIM))
    return [v[start:end] for v in vectors]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def _train_centroid(train_vecs, train_labels):
    """Per-composer centroid model."""
    groups: dict[str, list[list[float]]] = defaultdict(list)
    for v, l in zip(train_vecs, train_labels):
        groups[l].append(v)
    centroids = {}
    for comp, vecs in groups.items():
        dim = len(vecs[0])
        n   = len(vecs)
        centroids[comp] = [sum(v[d] for v in vecs) / n for d in range(dim)]
    return centroids


def _predict_centroid(centroids, vec, top_k=3):
    scores = []
    for comp, c in centroids.items():
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, c)))
        scores.append((comp, dist))
    scores.sort(key=lambda x: x[1])
    return [s[0] for s in scores[:top_k]]


def _train_gaussian(train_vecs, train_labels):
    from substrates.music.similarity.composer_similarity import ComposerProfiler
    p = ComposerProfiler()
    p.fit(train_vecs, train_labels)
    return p


def _predict_gaussian(profiler, vec, top_k=3):
    results = profiler.predict(vec, top_k=top_k)
    return [r.composer for r in results]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _top_k_accuracy(preds_list, gts, k=1) -> float:
    correct = sum(1 for pred, gt in zip(preds_list, gts) if gt in pred[:k])
    return correct / len(gts) if gts else 0.0


def _macro_f1(preds_list, gts) -> float:
    """Macro-averaged F1 (top-1 predictions)."""
    preds = [p[0] for p in preds_list]
    composers = list(set(gts))
    f1s = []
    for c in composers:
        tp = sum(1 for p, g in zip(preds, gts) if p == c == g)
        fp = sum(1 for p, g in zip(preds, gts) if p == c and g != c)
        fn = sum(1 for p, g in zip(preds, gts) if g == c and p != c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec  = tp / (tp + fn) if (tp + fn) else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def _mrr(preds_list, gts) -> float:
    rr_sum = 0.0
    for pred, gt in zip(preds_list, gts):
        if gt in pred:
            rank = pred.index(gt) + 1
            rr_sum += 1.0 / rank
    return rr_sum / len(gts) if gts else 0.0


def evaluate_model(
    train_vecs, train_labels,
    test_vecs, test_labels,
    model: str = "gaussian_bayes",
    top_k: int = 3,
) -> dict[str, float]:
    if model == "random":
        composers = list(set(train_labels))
        rng = random.Random(42)
        preds = [[rng.choice(composers)] * top_k for _ in test_vecs]
    elif model == "majority":
        most_common = Counter(train_labels).most_common(1)[0][0]
        preds = [[most_common] * top_k for _ in test_vecs]
    elif model == "nearest_centroid":
        centroids = _train_centroid(train_vecs, train_labels)
        preds = [_predict_centroid(centroids, v, top_k) for v in test_vecs]
    elif model == "gaussian_bayes":
        profiler = _train_gaussian(train_vecs, train_labels)
        preds = [_predict_gaussian(profiler, v, top_k) for v in test_vecs]
    elif model.startswith("cosine_knn"):
        k_nn = int(model.split("k")[-1]) if "k" in model else 1
        centroids = _train_centroid(train_vecs, train_labels)
        preds = [_predict_centroid(centroids, v, max(top_k, k_nn)) for v in test_vecs]
    else:
        return {}

    return {
        "top1_accuracy": round(_top_k_accuracy(preds, test_labels, 1), 4),
        "top3_accuracy": round(_top_k_accuracy(preds, test_labels, 3), 4),
        "macro_f1":      round(_macro_f1(preds, test_labels), 4),
        "mrr":           round(_mrr(preds, test_labels), 4),
        "n_test":        len(test_labels),
        "n_composers":   len(set(test_labels)),
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_benchmark(
    split:    str = "random",
    features: str = "all",
    seed:     int = 42,
    limit:    int = 0,
    dry_run:  bool = False,
) -> dict[str, Any]:
    print(f"\n[cfp_v1] Loading dataset …")
    data = load_dataset()

    n = len(data["track_ids"])
    n_composers = len(set(data["labels"]))
    print(f"  Tracks: {n}  Composers: {n_composers}")

    if n == 0:
        print("  No data — did you run the master pipeline first?")
        return {}

    if dry_run:
        print("  [dry-run] Validation passed — not running models")
        return {"n_tracks": n, "n_composers": n_composers, "dry_run": True}

    # Splits
    print(f"  Building {split} split …")
    if split == "random":
        splits = random_split(data, seed=seed)
    elif split == "game_held_out":
        splits = game_held_out_split(data)
    else:
        raise ValueError(f"Unknown split: {split}")

    id_to_idx = {tid: i for i, tid in enumerate(data["track_ids"])}

    def _get(id_list):
        vecs   = [data["vectors"][id_to_idx[tid]] for tid in id_list if tid in id_to_idx]
        labels = [data["labels"][id_to_idx[tid]]  for tid in id_list if tid in id_to_idx]
        return vecs, labels

    train_vecs, train_labels = _get(splits["train"])
    test_vecs,  test_labels  = _get(splits["test"])

    # Feature families
    family_list = [f.strip() for f in features.split(",")]
    if "ablation" in family_list:
        family_list = list(FAMILY_SLICES.keys())

    results: dict[str, Any] = {}
    models  = ["random", "majority", "nearest_centroid", "gaussian_bayes", "cosine_knn_k1"]

    for fam in family_list:
        tr_v = select_features(train_vecs, fam)
        te_v = select_features(test_vecs,  fam)
        results[fam] = {}
        for model in models:
            print(f"  {fam:10s} × {model:20s} … ", end="", flush=True)
            try:
                r = evaluate_model(tr_v, train_labels, te_v, test_labels, model)
                results[fam][model] = r
                print(f"top1={r.get('top1_accuracy', '?'):.3f}  macro_f1={r.get('macro_f1', '?'):.3f}")
            except Exception as e:
                results[fam][model] = {"error": str(e)}
                print(f"ERROR: {e}")

    # Compute chip incremental value
    chip_delta = {}
    if "sym" in results and "chip+sym" not in results:
        pass  # only if chip+sym was in family_list
    for base in ["sym", "mir"]:
        combo = f"chip+{base}" if f"chip+{base}" in results else None
        if combo and base in results:
            base_top1  = results[base].get("gaussian_bayes", {}).get("top1_accuracy", 0)
            combo_top1 = results[combo].get("gaussian_bayes", {}).get("top1_accuracy", 0)
            chip_delta[f"chip_delta_over_{base}"] = round(combo_top1 - base_top1, 4)

    # Write artifacts
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    (ARTIFACT_DIR / "split_manifest.json").write_text(json.dumps({
        "split": split,
        "seed":  seed,
        "train_size": len(splits["train"]),
        "val_size":   len(splits.get("val", [])),
        "test_size":  len(splits["test"]),
        "train_ids":  splits["train"][:50],   # truncate for readability
        "test_ids":   splits["test"][:50],
        "composer_counts": data["composer_counts"],
    }, indent=2))

    (ARTIFACT_DIR / "results_per_feature_family.json").write_text(
        json.dumps(results, indent=2)
    )

    labels_map = {tid: lbl for tid, lbl in zip(data["track_ids"], data["labels"])}
    (ARTIFACT_DIR / "labels.json").write_text(json.dumps(labels_map, indent=2))

    _write_report(results, chip_delta, n, n_composers, split, ARTIFACT_DIR)

    summary = {
        "benchmark_id":  "music_lab_cfp_v1",
        "split":         split,
        "n_tracks":      n,
        "n_composers":   n_composers,
        "n_train":       len(splits["train"]),
        "n_test":        len(splits["test"]),
        "chip_delta":    chip_delta,
        "ts":            datetime.now(timezone.utc).isoformat(),
    }
    (ARTIFACT_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2))

    return summary


def _write_report(results, chip_delta, n_tracks, n_composers, split, out_dir):
    lines = [
        "# music_lab_cfp_v1 — Attribution Report",
        "",
        f"- Tracks: {n_tracks}   Composers: {n_composers}   Split: {split}",
        "",
        "## Top-1 Accuracy by Feature Family × Model",
        "",
        "| Family | random | majority | nearest_centroid | gaussian_bayes | cosine_knn_k1 |",
        "|--------|--------|----------|-----------------|----------------|---------------|",
    ]

    for fam, models_r in results.items():
        row = [fam]
        for m in ["random", "majority", "nearest_centroid", "gaussian_bayes", "cosine_knn_k1"]:
            v = models_r.get(m, {}).get("top1_accuracy", "N/A")
            row.append(f"{v:.3f}" if isinstance(v, float) else str(v))
        lines.append("| " + " | ".join(row) + " |")

    lines += ["", "## Chip Incremental Value (gaussian_bayes)"]
    for k, v in chip_delta.items():
        lines.append(f"- {k}: {v:+.4f}")

    lines += [
        "",
        "## Reproducibility",
        f"- Schema version: {FEATURE_VECTOR_VERSION}",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "See `results_per_feature_family.json` for full per-composer breakdown.",
    ]

    (out_dir / "attribution_report.md").write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="music_lab_cfp_v1 benchmark runner")
    p.add_argument("--split",    default="random", choices=["random", "game_held_out"])
    p.add_argument("--features", default="all",    help="Feature families (comma-separated or 'ablation')")
    p.add_argument("--seed",     type=int, default=42)
    p.add_argument("--limit",    type=int, default=0)
    p.add_argument("--dry-run",  action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    summary = run_benchmark(
        split=args.split,
        features=args.features,
        seed=args.seed,
        limit=args.limit,
        dry_run=args.dry_run,
    )
    print("\n[cfp_v1] Summary:")
    print(json.dumps(summary, indent=2))
