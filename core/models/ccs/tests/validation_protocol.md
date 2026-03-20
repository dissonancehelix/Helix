# CCS Validation Protocol

**Version**: 1.0.0
**Applies to**: All CCS embeddings conforming to `schema/ccs_schema.json`

---

## 1. Schema Validation

Every embedding file must pass JSON Schema validation against `schema/ccs_schema.json`.

**Required checks**:

| Check | Pass Condition |
|-------|---------------|
| All 6 axes present | `ccs_embedding` contains all 6 required keys |
| Type correctness | All axis values are JSON numbers (not strings, null, or booleans) |
| Range compliance | All axis values satisfy `0.0 ≤ value ≤ 1.0` |
| Evidence block present | `evidence.signals`, `evidence.source_features`, `evidence.notes` all present |
| Confidence present | `confidence` is a number in [0.0, 1.0] |
| Version string | `ccs_version` matches pattern `\d+\.\d+\.\d+` |

**Validation command** (when tooling is implemented):
```
helix ccs-validate <path_to_embedding.json>
```

**Fail behavior**: Any schema violation causes the embedding to be rejected. Partial embeddings are not stored in the Atlas.

---

## 2. Determinism Test

**Purpose**: Verify that the same input data produces the same embedding on re-computation.

**Procedure**:
1. Record the `source_features` and input data state at computation time T₁.
2. Re-run the embedding computation at time T₂ using identical inputs.
3. Compare all 6 axis values: `|value_T1 - value_T2| < ε` where `ε = 0.001`.

**Pass condition**: All 6 axes agree within `ε = 0.001`.

**Fail behavior**: If determinism fails, log the discrepancy with input fingerprints. Do not overwrite the stored embedding. Flag for manual review.

**Sources of non-determinism to eliminate**:
- Floating-point ordering differences: use stable sort, fixed accumulation order
- Hash-based randomness: use deterministic hashing (SHA-256 content hash only)
- Time-dependent inputs: never use wall-clock time as an input to axis computation

---

## 3. Evidence Coherence Test

**Purpose**: Verify that the axis values are consistent with the stated evidence signals.

**Procedure**: For each axis, check that the stated signals are directionally consistent with the computed value.

**Rules**:

| Axis | Coherence Rule |
|------|---------------|
| `attractor_stability` | If `phrase_repetition_rate < 0.3`, then `attractor_stability < 0.5` |
| `generative_constraint` | If `scale_adherence_ratio < 0.4`, then `generative_constraint < 0.5` |
| `recurrence_depth` | If `detected_recurrence_levels ≤ 1`, then `recurrence_depth ≤ 0.25` |
| `structural_density` | If `note_density < domain_p25`, then `structural_density < 0.4` |
| `control_entropy` | If all entropy inputs < 0.3, then `control_entropy < 0.4` |
| `basin_permeability` | If `mean_transition_sharpness < 0.2`, then `basin_permeability < 0.4` |

**Fail behavior**: Coherence violations are logged as warnings, not hard failures. The embedding is stored but flagged with `coherence_warning: true`. Manual review is required before promoting the entity.

---

## 4. Axis Independence Check

**Purpose**: Detect if computed embeddings are exhibiting unexpected correlation, which would indicate a formula error or data contamination.

**Procedure**: Across a corpus of ≥20 embeddings, compute pairwise Pearson correlation for all 15 axis pairs.

**Pass condition**: No pair exceeds `|r| > 0.85` (strong collinearity threshold).

**Fail behavior**: If any pair exceeds the threshold, inspect formula definitions and input data for shared inputs being double-counted. This is a corpus-level check, not per-embedding.

**Note**: Moderate correlation between axes is expected and acceptable. Only near-perfect correlation (>0.85) indicates a structural problem.

---

## 5. Confidence Calibration Check

**Purpose**: Verify that confidence scores reflect actual data completeness, not optimism bias.

**Procedure**: For a batch of embeddings, check that the distribution of confidence scores matches the distribution of available evidence signal counts.

**Reference thresholds** (from SPEC.md Section 4):

| `evidence.signals` count | Expected `confidence` range |
|--------------------------|----------------------------|
| ≥ 12 signals, audio analysis confirmed | 0.80 – 1.00 |
| 8–11 signals, audio-based | 0.55 – 0.79 |
| 4–7 signals, metadata-only | 0.30 – 0.54 |
| 1–3 signals, partial metadata | 0.10 – 0.29 |
| 0 signals | 0.00 – 0.09 |

**Fail behavior**: Systematic over-confidence (high confidence scores with few signals) is flagged in corpus-level audit reports.

---

## 6. Drift Detection Test

**Purpose**: When an entity is re-parsed and a new embedding is computed, detect if the embedding has drifted from the previous version.

**Procedure**:
1. Load the previous embedding `E_prev`.
2. Compute the new embedding `E_new`.
3. Compute Euclidean distance in 6D space: `d = √Σ(axis_prev - axis_new)²`
4. Compare to drift threshold.

**Thresholds**:

| Distance `d` | Action |
|-------------|--------|
| `d < 0.05` | Accept new embedding. Overwrite silently. |
| `0.05 ≤ d < 0.20` | Accept new embedding. Log drift event. |
| `d ≥ 0.20` | Flag for review. Archive previous embedding with timestamp. Do NOT overwrite without confirmation. |

**Archive path convention**:
```
codex/atlas/embeddings/music/tracks/{slug}.json          ← current
codex/atlas/embeddings/music/tracks/{slug}.v{ts}.json    ← archived version
```

---

## 7. Placeholder Detection

**Purpose**: Reject zero-filled or clearly placeholder embeddings from being promoted.

**Rule**: Any embedding where all 6 axis values are `0.0` must have `confidence < 0.10`. If `confidence ≥ 0.10` but all values are `0.0`, reject as invalid placeholder.

**Implementation**: This check runs automatically during schema validation.
