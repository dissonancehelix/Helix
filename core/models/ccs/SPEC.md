# Cognitive Coordinate System (CCS) — Technical Specification

**Version**: 1.0.0
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

**Definition**: The count of distinct hierarchical levels at which recurrent structure is detectable, normalized to the domain maximum.

**Hierarchical levels** (bottom to top):
1. **Motif** — 2–4 note cell that reappears across phrases
2. **Phrase** — 4–16 bar unit that reappears within sections
3. **Section** — 16+ bar unit that reappears within the full form
4. **Form** — section-level return (e.g., A–B–A, arch, rondo)

**Boundary values**:
- `0.0` — no detectable recurrence at any level
- `1.0` — recurrence confirmed at all four levels (motif, phrase, section, form)

**Formula**:
```
recurrence_depth = detected_levels / 4
```

Where `detected_levels` ∈ {0, 1, 2, 3, 4}.

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

---

## 4. Confidence Score

A per-embedding confidence score [0.0, 1.0] reflects the completeness of available input data.

| Data Available | Confidence Range |
|----------------|-----------------|
| Full audio analysis + structural segmentation + tags | 0.80 – 1.00 |
| Audio analysis only (no structural segmentation) | 0.55 – 0.79 |
| Tags and metadata only (no audio analysis) | 0.30 – 0.54 |
| Partial metadata (some fields missing) | 0.10 – 0.29 |
| No computable data (placeholder only) | 0.00 – 0.09 |

---

## 5. Computation Requirements

1. **Deterministic**: Given identical inputs, the embedding must produce identical outputs. No random sampling, no stochastic components.
2. **Evidence-backed**: Every axis value must be traceable to named signals in the `evidence.signals` array.
3. **Partial tolerance**: If data for a specific input is unavailable, that input's contribution is excluded from the formula and confidence is reduced accordingly.
4. **No subjective assignment**: Values may not be assigned by human judgment without underlying signal evidence.
5. **Domain normalization**: Per-domain baselines must be stored alongside the computation code and versioned independently.

---

## 6. Domain Extension

CCS axes are domain-agnostic. The six structural properties apply to any sequential or compositional entity. Domain-specific application requires:

1. A mapping from domain observables to the named inputs of each formula
2. A domain baseline for normalization (distribution of values observed across the domain)
3. A domain adapter document specifying how each observable is measured

Music-domain inputs are defined here. Other domain adapters must be created separately and must not modify this specification.
