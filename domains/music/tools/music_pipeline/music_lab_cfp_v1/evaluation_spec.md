# music_lab_cfp_v1 — Evaluation Specification

## Objective

Attribute Genesis/YM2612 tracks to their composer from chip-level features,
symbolic structure, and (optionally) MIR audio features.

---

## Feature Families

Each model is trained on one or more feature family groups:

| Family | ID | Source | Dims | Tier |
|--------|----|--------|------|------|
| Chip synthesis | `chip` | feature_extractor chip stats | 12 | A |
| Symbolic/theory | `sym` | key_estimator + rhythm_analyzer + motif_detector | 8 | C |
| MIR audio | `mir` | mir_extractor (or chip proxy) | 30 | D |
| Combined | `all` | all 64 dims of feature_vector_v0 | 64 | A/C/D |

Ablation matrix (models trained on each combination):
- `chip` only
- `sym` only
- `mir` only
- `chip+sym`
- `chip+mir`
- `sym+mir`
- `all` (full 64-dim)

---

## Baseline Models

| Baseline | Description |
|----------|-------------|
| `random` | Uniform random from N composers |
| `majority` | Always predict most frequent composer in train set |
| `nearest_centroid` | Euclidean distance to per-composer centroid (same as ComposerProfiler without covariance) |

## Evaluation Models

| Model | Description |
|-------|-------------|
| `gaussian_bayes` | ComposerProfiler (diagonal Gaussian, Bayesian posterior) |
| `cosine_knn_k1` | 1-nearest-neighbour via cosine similarity |
| `cosine_knn_k5` | 5-nearest-neighbour majority vote |

---

## Metrics

All metrics computed on the **test split** of each split policy:

| Metric | Definition |
|--------|-----------|
| `top1_accuracy` | Fraction of test tracks where top prediction = ground truth |
| `top3_accuracy` | Fraction where ground truth appears in top-3 predictions |
| `macro_f1` | Macro-averaged F1 across all composer classes |
| `per_composer_f1` | Individual F1 for each composer |
| `mean_reciprocal_rank` | MRR across ranked prediction lists |
| `confusion_matrix` | N×N count matrix (ground truth vs prediction) |

Baseline comparison: `top1_accuracy` vs `random` must be > 2× for success.
Chip incremental value: `chip+sym` top1 − `sym` top1 > 0.05 for success.

---

## Artifact Outputs

All outputs written to `artifacts/benchmarks/music_lab_cfp_v1/`:

| File | Content |
|------|---------|
| `split_manifest.json` | Track IDs per split (random + game_held_out) |
| `feature_matrix.npy` | N×64 float32 array (all tracks) |
| `labels.json` | `{"track_id": "composer_name", ...}` |
| `results_per_feature_family.json` | All metrics for each feature family × model |
| `confusion_matrix.json` | Per-model confusion matrices |
| `attribution_report.md` | Human-readable summary with tables |

---

## Report Template

`attribution_report.md` must contain:
1. Dataset summary (N tracks, N composers, split sizes)
2. Top-1 accuracy table across feature families × models
3. Best model ablation delta (chip contribution)
4. Per-composer breakdown for best model
5. Failure analysis: top-10 most confused composer pairs
6. Reproducibility note (seeds, schema_version, run timestamp)

---

## Extensibility

To add SNES/SPC700:
- Add `spc_parser.py` Tier A output as additional feature source
- Add SPC700-specific chip dims (voice ADSR, echo delay, KON density)
- New platform onehot dim active
- Re-run benchmark with `target_platform: SNES/SPC700`

To add NES/2A03:
- Use `nsf_parser.py` + expansion chip flags as additional features
- New chip onehot dim active
