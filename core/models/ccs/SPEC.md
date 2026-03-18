# Cognitive Coordinate System (CCS) — Technical Specification

**Version**: 1.1.0
**Module**: `core/models/ccs/`
**Status**: Stable

---

## 1. Purpose

CCS maps any entity with computable structural properties to a point in a 6-dimensional unit hypercube [0.0, 1.0]⁶. Each axis measures one distinct structural property. Values are derived from observable features only. No axis is defined in terms of another axis.

CCS does not describe what an entity is (genre, category, label). It describes what an entity does structurally.

---

## 2. Axis Definitions

### Axis 1 — `attractor_stability`

**Range**: [0.0, 1.0]

**Definition**: The degree to which structural patterns recur identically or near-identically within the entity.

**Observable inputs**:
- Phrase repetition rate: `repeated_phrase_count / total_phrase_count`
- Pattern variance: standard deviation of phrase-to-phrase similarity scores
- Section return frequency: how often sections reappear vs. how often new sections appear

**Boundary values**:
- `0.0` — no structural pattern repeats at any scale; every phrase is novel (through-composed, aleatoric)
- `1.0` — all phrases and sections are exact repetitions; full loop with no variation

**Formula**:
```
attractor_stability = (repeated_units / total_units) × (1 − normalize(pattern_variance))
```

Where `normalize(x)` maps the observed variance range to [0, 1] against the domain baseline.

---

### Axis 2 — `generative_constraint`

**Range**: [0.0, 1.0]

**Definition**: The degree to which the event space (pitch, rhythm, timbre) is restricted by detectable compositional rules.

**Observable inputs**:
- Scale adherence ratio: fraction of pitch events within the dominant detected scale
- Rhythmic quantization error: mean deviation of note onsets from the nearest grid position
- Harmonic vocabulary size: count of distinct chord types normalized to domain maximum

**Boundary values**:
- `0.0` — no detectable constraints; full chromatic pitch space, free rhythm, unbounded harmonic vocabulary
- `1.0` — maximum constraint; single diatonic scale with no chromatic notes, strict metric grid, minimal chord set (1–3 types)

**Formula**:
```
generative_constraint = scale_adherence
                      × (1 − normalize(rhythmic_quantization_error))
                      × (1 − normalize(harmonic_vocab_size))
```

---

### Axis 3 — `recurrence_depth`

**Range**: [0.0, 1.0]

**Definition**: The count of distinct hierarchical levels at which recurrent structure is detectable, normalized to the domain-defined maximum number of levels.

**Hierarchical levels** (example — music domain default):
1. **Motif** — 2–4 note cell that reappears across phrases
2. **Phrase** — 4–16 bar unit that reappears within sections
3. **Section** — 16+ bar unit that reappears within the full form
4. **Form** — section-level return (e.g., A–B–A, arch, rondo)

**Boundary values**:
- `0.0` — no detectable recurrence at any level
- `1.0` — recurrence confirmed at all `max_possible_levels` for the domain

**Formula**:
```
recurrence_depth = detected_levels / max_possible_levels(domain)
```

Where:
- `detected_levels` ∈ {0, …, max_possible_levels(domain)}
- `max_possible_levels(domain)` is an integer defined per domain, not globally fixed
- Music domain default: `max_possible_levels = 4`
- `max_possible_levels` must be recorded in `evidence.notes` or `source_version`

---

### Axis 4 — `structural_density`

**Range**: [0.0, 1.0]

**Definition**: The rate of structural events per unit time, normalized to the domain baseline.

**Observable inputs**:
- Note density: events per second (NPS)
- Harmonic rhythm: chord changes per bar
- Timbral event rate: distinct timbre-change events per second

**Boundary values**:
- `0.0` — minimal events: sparse note spacing, static harmony, no timbral change
- `1.0` — maximum density relative to domain: rapid notes, fast harmonic rhythm, continuous timbre change

**Formula**:
```
structural_density = normalize(
    note_density_normalized
    × harmonic_rhythm_normalized
    × (1 + timbre_change_rate_normalized)
    / 2
)
```

Normalization is performed against the observed domain distribution (per-domain percentile rank).

---

### Axis 5 — `control_entropy`

**Range**: [0.0, 1.0]

**Definition**: The information-theoretic entropy of control signal distributions (pitch, dynamics, articulation), normalized to the theoretical maximum for each distribution.

**Observable inputs**:
- Pitch class distribution: histogram of the 12 pitch classes used
- Dynamic distribution: histogram of velocity/amplitude quantiles
- Articulation variety: count of distinct articulation types (staccato, legato, accent, etc.)

**Formula**:
```
control_entropy = mean([
    H(pitch_class_distribution) / log₂(12),
    H(dynamic_distribution) / log₂(dynamic_bins),
    H(articulation_distribution) / log₂(articulation_types)
])
```

Where `H(X) = −Σ pᵢ log₂(pᵢ)` is Shannon entropy.

**Boundary values**:
- `0.0` — single pitch class, single dynamic level, single articulation type
- `1.0` — uniform distribution across all pitch classes, all dynamic levels, all articulation types

---

### Axis 6 — `basin_permeability`

**Range**: [0.0, 1.0]

**Definition**: The degree to which structural transitions between sections or states are gradual rather than abrupt.

**Observable inputs**:
- Transition sharpness score per boundary: 0.0 (hard cut) to 1.0 (crossfade/gradual)
- Shared material ratio: fraction of thematic material appearing in both adjacent sections
- Boundary count: total number of detected section boundaries

**Formula**:
```
basin_permeability = mean(transition_sharpness_scores)
                   × (1 + shared_material_ratio) / 2
```

**Boundary values**:
- `0.0` — all transitions are hard cuts; no material shared across section boundaries
- `1.0` — all transitions are fully gradual; material is continuously shared (no distinct sections)

---

## 3. Axis Independence Guarantees

The following pairs are structurally independent:

| Pair | Reason |
|------|--------|
| `attractor_stability` ≠ `recurrence_depth` | A piece can have deep recurrence hierarchy but vary each repetition heavily (low stability) |
| `generative_constraint` ≠ `structural_density` | A highly constrained scale/grid piece can be sparse; a dense piece can be chromatic |
| `control_entropy` ≠ `structural_density` | A dense piece can use a narrow pitch range; a sparse piece can span the full pitch space |
| `basin_permeability` ≠ `attractor_stability` | A piece can loop identically (high stability) but with hard abrupt cuts between loops (low permeability) |
| `generative_constraint` ≠ `control_entropy` | Entropy measures distribution uniformity; constraint measures rule adherence — a piece can use all 12 pitch classes uniformly while still following strict rules |
| `recurrence_depth` ≠ `basin_permeability` | Hierarchical structure and transition smoothness are independent properties |

### Signal Isolation Rule

Each named signal in `evidence.signals` contributes to exactly one primary axis (`axis` field). The same signal instance must not appear under two different `axis` values.

Cross-axis influence is permitted only indirectly — if a raw measurement informs two axes, it must be processed into two distinct derived signals (with distinct names and distinct `axis` assignments), not referenced twice as the same signal.

**Permitted**: `scale_adherence_ratio → generative_constraint` and `pitch_class_entropy → control_entropy` (two separate signals derived from the same pitch data)

**Not permitted**: a signal named `scale_adherence_ratio` appearing once with `"axis": "generative_constraint"` and again with `"axis": "control_entropy"`

---

## 4. Confidence Score

A per-embedding confidence score [0.0, 1.0] is computed from three factors. All factors are required and deterministic.

```
confidence = (
    0.40 × signal_count_score
  + 0.40 × axis_coverage_score
  + 0.20 × source_reliability_score
)
```

**Factor 1 — `signal_count_score`** (quantity of evidence):

```
signal_count_score = min(signal_count / 12, 1.0)
```

Where 12 is the target number of signals for a fully-evidenced embedding. Missing signals must be absent from `evidence.signals` — they may not be present with placeholder values.

**Factor 2 — `axis_coverage_score`** (coverage across all 6 axes):

```
axis_coverage_score = axes_with_at_least_one_signal / 6
```

An axis with no signals in `evidence.signals` counts as uncovered. An axis whose signals were excluded due to missing data must reduce this score — it cannot be assumed covered.

**Factor 3 — `source_reliability_score`** (quality and method of source data):

| Source | Score |
|--------|-------|
| Full audio analysis + structural segmentation + tags | 1.00 |
| Audio analysis only (no structural segmentation) | 0.75 |
| Tags and metadata only, no audio analysis | 0.50 |
| Partial metadata (fields missing) | 0.25 |
| No computable data (placeholder) | 0.05 |

**Reference ranges** (for calibration, not enforcement):

| Confidence | Interpretation |
|------------|---------------|
| 0.80 – 1.00 | High — all axes covered, ≥12 signals, audio analysis |
| 0.55 – 0.79 | Moderate — most axes covered, audio-based |
| 0.30 – 0.54 | Low — metadata-only or partial axis coverage |
| 0.00 – 0.29 | Unreliable — treat embedding as structural placeholder |

---

## 5. Computation Requirements

1. **Deterministic**: Given identical inputs, the embedding must produce identical outputs. No random sampling, no stochastic components.
2. **Evidence-backed**: Every axis value must be traceable to named signals in the `evidence.signals` array.
3. **Partial tolerance**: If data for a specific input is unavailable, that input's contribution is excluded from the axis formula and the axis is computed from remaining inputs only. The missing input must not be silently defaulted to zero or any other value — its absence must reduce `axis_coverage_score` and `signal_count_score` in the confidence calculation.
4. **No subjective assignment**: Values may not be assigned by human judgment without underlying signal evidence.
5. **Domain normalization**: Per-domain baselines must be stored alongside the computation code and versioned independently.
6. **Low-confidence embeddings**: An embedding with `confidence < 0.30` is structurally unreliable. It may be stored but must not be used in distance computations or aggregations without explicit acknowledgment of the confidence level.

---

## 6. Normalization Protocol

All axis values must be normalized against a defined reference distribution before being stored. Normalization is not arbitrary scaling to [0, 1] — it must be reproducible from a specified reference.

### Reference types

Two reference types are valid:

| Type | Description | When to use |
|------|-------------|------------|
| **Domain-specific** | Distribution of the raw feature across a representative corpus for the target domain (e.g., the FM synthesis VGM corpus) | Preferred when a domain corpus is available and stable |
| **Global baseline** | Distribution of the raw feature across a multi-domain dataset spanning the full intended application space | Use when domain corpus is too small (<50 entities) or domain is not yet established |

### Requirements

1. The reference type and dataset used must be recorded in `evidence.notes` or `source_version` for every embedding.
2. The normalization method must be one of:
   - **Percentile rank**: `normalize(x) = percentile_rank(x, reference_distribution)`
   - **Min-max**: `normalize(x) = (x − ref_min) / (ref_max − ref_min)` using reference distribution bounds
   - **Z-score clamped**: `normalize(x) = clamp((x − ref_mean) / ref_std × 0.5 + 0.5, 0, 1)`
3. The method used must be consistent across all embeddings sharing the same `source_version`.
4. If a reference distribution changes (new corpus version), all embeddings produced under the old reference must be flagged for recomputation.

### Recording format

In `evidence.notes` or `source_version`, include:
```
normalization: {method}, reference: {corpus_name_or_type}@{version}
```

Example: `normalization: percentile_rank, reference: vgm_fm_corpus@v1`

---

## 7. Embedding Comparison

Two CCS embeddings can be compared to produce a scalar distance and a normalized alignment score. All comparison functions are deterministic.

### Distance functions

**Euclidean distance** (default):
```
d_euclidean(A, B) = √Σᵢ (Aᵢ − Bᵢ)²
```

Range: [0.0, √6] ≈ [0.0, 2.449] for 6 axes in [0, 1].

**Cosine similarity** (alternative, for direction rather than magnitude):
```
cos_sim(A, B) = (A · B) / (‖A‖ × ‖B‖)
```

Range: [−1.0, 1.0]. Only meaningful when both embeddings are non-zero.

### Alignment score

A normalized scalar in [0.0, 1.0] derived from Euclidean distance:
```
alignment_score(A, B) = 1 − (d_euclidean(A, B) / √6)
```

- `1.0` — identical embeddings
- `0.0` — maximally distant embeddings (opposite corners of the hypercube)

### Weights

Default: uniform weights (all axes contribute equally).

Non-uniform weights may be applied externally by multiplying each axis difference by a weight factor before computing distance. Weights are not part of CCS core — they must be defined and documented outside this specification, not embedded in the schema.

### Constraints

1. Comparison is only valid between embeddings sharing the same `ccs_version`.
2. Comparison between embeddings with `confidence < 0.30` must be explicitly flagged — low-confidence embeddings produce unreliable distance values.
3. Comparison does not require identical domains — axes are domain-agnostic — but differences in normalization reference may cause systematic bias.



---

## 8. Domain Extension

CCS axes are domain-agnostic. The six structural properties apply to any sequential or compositional entity. Domain-specific application requires:

1. A mapping from domain observables to the named inputs of each formula
2. A domain baseline for normalization (distribution of values observed across the domain)
3. A domain adapter document specifying how each observable is measured

Music-domain inputs are defined here. Other domain adapters must be created separately and must not modify this specification.
