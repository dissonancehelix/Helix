# HELIX MATH SUBSTRATE SPECIFICATION

**Version:** 1.2
**Status:** Authoritative target specification — implementation status tracked in README.md §11
**Relationship:** Extends `core/probes/math/README.md`

---

## 1. DOMAIN SCOPE

The Math Substrate operates on formal mathematical simulations with known inputs and verifiable outputs. Its role is twofold:
1. Produce ground-truth invariant candidates (e.g., oscillator locking) that other domains can reference
2. Provide the canonical implementation of `MathStructuralVector → HelixEmbedding` projection for use as template by other domains

It does not analyze arbitrary mathematics or serve as a general math library.

---

## 2. DOMAIN-LOCAL STRUCTURAL METRICS (`MathStructuralVector`)

These metrics are computed from simulation outputs and are domain-local. They are NOT the same as HelixEmbedding axes. They must be projected via an explicit adapter before any Atlas interaction.

Implemented in: `domain_analysis/math_structural_vector.py`

### 2.1 Attractor Stability (`A_s`)

$$A_s = 1 - \frac{V_{po}}{V_{max}}$$

`V_po` = variance of periodic orbit points; `V_max` = theoretical maximum variance. Near 1.0 = stable attractor; near 0.0 = instability or chaos.

### 2.2 Generative Constraint (`G_c`)

$$G_c = 1 - \frac{\dim(S_{res})}{\dim(S_{tot})}$$

High `G_c` = system operating in a tightly bounded region of its full state space.

### 2.3 Recurrence Depth (`R_d`)

$$R_d = \frac{D_f}{k_{norm}}$$

`D_f` = fractal dimension; `k_norm` = domain normalization constant. Higher = deeper hierarchical self-similarity.

### 2.4 Structural Density (`S_d`)

$$S_d = \text{sigmoid}\!\left(\lambda \cdot \frac{E}{\Delta t}\right)$$

Events per unit time, sigmoid-normalized. Domain-λ must be set per simulation type. **Not the same as `density` in HelixEmbedding.**

### 2.5 Control Entropy (`C_e`)

$$C_e = \frac{-\sum P(x) \log P(x)}{H_{max}}$$

Normalized Shannon entropy of control signal distribution. Near 1.0 = maximum unpredictability; near 0.0 = deterministic behavior.

### 2.6 Basin Permeability (`B_p`)

$$B_p = \exp(-\lambda_L)$$

`λ_L` = leading Lyapunov exponent. High `B_p` = fluid state transitions; low `B_p` = strong attractor trapping.

---

## 3. SHARED EMBEDDING PROJECTION

Math-domain structural metrics are projected into the shared `HelixEmbedding` format via: `embedding/projection.py`

**Schema version**: `math_v1` (stamped on every output artifact)

**Axis projection mapping** (math metric → HelixEmbedding axis):

| HelixEmbedding Axis | Math Metric | Rationale |
|---------------------|-------------|-----------|
| `structure` | `attractor_stability` | Stability ↔ structural persistence |
| `complexity` | `generative_constraint` | Constraint ↔ expressive complexity |
| `repetition` | `recurrence_depth` | Self-similarity ↔ repetition depth |
| `density` | `structural_density` | Event density maps directly |
| `expression` | `basin_permeability` | Transition fluidity ↔ expressive range |
| `variation` | `control_entropy` | Entropy ↔ variation |

**Non-equivalence rule**: These axes are NOT identical. The mapping reflects semantic analogy, not mathematical equivalence. If the shared embedding axes are redefined, this mapping must be re-evaluated and `PROJECTION_SCHEMA_VERSION` incremented.

**Confidence heuristic**: L2 norm of the 6D embedding vector, normalized by √6. This is a proxy, not a calibrated score.

---

## 4. PIPELINE STAGES

| Stage | Responsibility | Input | Output | Status |
|-------|----------------|-------|--------|--------|
| 1 | Model definition | Parameters | Formal axiom set | ⚠️ Partial — no axiom schema |
| 2 | Simulation run | Model config | Phase trajectories | ✅ Kuramoto implemented |
| 3 | Signal extraction | Trajectories | Time series, order parameter | ✅ Implemented |
| 4 | Metric calculation | Time series | `MathStructuralVector` | ✅ Implemented |
| 5 | Embedding projection | `MathStructuralVector` | `HelixEmbedding` (schema `math_v1`) | ✅ Implemented |
| 6 | Principle validation | Embedding | DCP trajectory mode classification (collapse/floor/oscillating) | ❌ Not calibrated |
| 7 | Invariant validation | Scores | P-value vs null model | ⚠️ Null model exists; not integrated |

---

## 5. ARTIFACT SCHEMAS

### FormalModel (`artifacts/math/<id>/model.json`)
```json
{
  "model_type": "kuramoto",
  "parameters": {"K": 0.5, "n": 100, "seed": 42},
  "axioms": []
}
```
Note: `axioms` is empty pending formal axiom schema definition.

### MathStructuralVector (`artifacts/math/<id>/math_structural_vector.json`)
```json
{
  "attractor_stability": 0.82,
  "generative_constraint": 0.61,
  "recurrence_depth": 0.44,
  "structural_density": 0.73,
  "control_entropy": 0.29,
  "basin_permeability": 0.55
}
```

### HelixEmbedding (`artifacts/math/<id>/helix_embedding.json`)
```json
{
  "complexity": 0.61,
  "structure": 0.82,
  "repetition": 0.44,
  "density": 0.73,
  "expression": 0.55,
  "variation": 0.29,
  "confidence": 0.78,
  "domain": "math",
  "source_vector": "math_structural_vector",
  "projection_schema": "math_v1"
}
```

### ValidationReport (`artifacts/math/<id>/validation_report.json`)
```json
{
  "fixture": "kuramoto",
  "fixture_version": "1.0",
  "projection_schema": "math_v1",
  "passed": true,
  "sections": [],
  "generated_at": "..."
}
```

### InvariantCandidate (`artifacts/math/<id>/invariant.json`)
```json
{
  "entity_id": "math.invariant:oscillator-locking-K2.00-n50-s42",
  "entity_type": "invariant",
  "status": "CANDIDATE",
  "confidence": 0.78,
  "calibration_status": "provisional",
  "projection_schema": "math_v1",
  "validation_flags": {
    "null_baseline_used": false,
    "multi_domain_observed": false,
    "adversarial_validation_run": false
  },
  "persistence_target": "codex/atlas/math/",
  "persistence_gate": "system/engine/store/compiler/atlas_compiler.py via enforce_persistence()"
}
```

---

## 6. VALIDATION RULES

Domain validation harness: `validation/kuramoto_fixture.py`

Produces structured JSON artifacts with three sections:
- **A. Metric Sanity**: high-K → higher sync + attractor stability; low-K → higher entropy
- **B. Simulation Fixture**: null-model confusion guard (K=0 sync < 0.3), locking guard (K=4 sync > 0.8), deterministic seed
- **C. Projection Consistency**: range validity, determinism, self-similarity = 1.0, triangle inequality on distance, distance = 1 - similarity

---

## 7. METRIC SPACE / SIMILARITY / DISTANCE

The HelixEmbedding metric space uses Euclidean distance normalized by √6:

```
distance(a, b) = euclidean(a, b) / sqrt(6)          ∈ [0, 1]
similarity(a, b) = 1 - distance(a, b)               ∈ [0, 1]
```

These are dual quantities:
```
distance(a, a) = 0       similarity(a, a) = 1
distance(a, b) = 1 - similarity(a, b)              (always)
```

**Triangle inequality applies to DISTANCE, not similarity**:
```
d(a, c) ≤ d(a, b) + d(b, c)
```

A violation is a `STRUCTURAL_FAILURE` and must be flagged before Atlas promotion. Validation: `embedding/projection.py::validate_triangle_inequality()`.

---

## 8. ENTRY / HSL INTEGRATION STATE

**Target**: `DISCOVER math.kuramoto --K=0.5 --n=100 --steps=1000`\
**Current**: Direct Python. `core/probes/math/e2e.py` is the current canonical entry path.

No HSL command routes to the math domain. This is a known, documented gap.

---

## 9. THRESHOLDS AND CALIBRATION

| Threshold | Value | Calibration Status |
|-----------|-------|--------------------|
| Minimum embedding confidence | 0.30 | **Provisional** — not calibrated |
| Null-model sync guard (K=0) | sync < 0.3 | Mechanistic — valid per Kuramoto theory |
| Strong-locking guard (K=4) | sync > 0.8 | Mechanistic — valid per Kuramoto theory |

**Calibration procedure for confidence floor** (not yet performed):
1. Run Kuramoto with K=0, randomized phases, N ≥ 100 times
2. Project each run to HelixEmbedding
3. Compute `mean(l2_norms)` and `std(l2_norms)`
4. Set `PROVISIONAL_CONFIDENCE_FLOOR = mean + 2 * std`
5. Update `PROJECTION_SCHEMA_VERSION` if floor value changes significantly

Until calibration is performed, treat all promotions above the provisional floor as structurally eligible but not definitively validated.

---

## 10. PROMOTION CONDITIONS

Invariant candidates follow the global 6-criterion gate (see `docs/GOVERNANCE.md`). Math-domain candidates are additionally required to specify:
- `calibration_status` (provisional / calibrated)
- `null_baseline_used` (true / false)
- `validation_flags` (full dict)
- `projection_schema` (schema version string)

---

## 11. KNOWN ASSUMPTIONS / OPEN CONSTRAINTS

- Kuramoto model assumes mean-field (all-to-all) coupling unless an adjacency matrix is provided
- K_c (critical coupling) scales with natural frequency spread; the 0.30 null guard is not theoretically derived from K_c, just empirically observed
- `basin_permeability = exp(-λ_L)` requires computing the leading Lyapunov exponent; the current `from_kuramoto_results()` implementation uses a sync-based proxy, not actual Lyapunov computation
- EIP/DCP/LIP principle metrics (§7 of pipeline) are not computed; they are conceptually defined only
- Formal axiom schema for model definitions is not yet specified

