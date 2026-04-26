# HELIX MATH PROBE FAMILY

**Version:** 1.3
**Status:** Authoritative target specification — see §11 for current implementation status
**Reference SPEC:** [SPEC.md](SPEC.md)

---

## 1. PURPOSE

The Math Probe Family provides deterministic, ground-truth validation of structural invariants. Because mathematical simulations have known inputs and verifiable outputs, the math probe family is the primary substrate for calibrating the shared cross-domain embedding and for establishing null baselines against which invariant candidates in other domains are measured.

Scope: canonical simulations (Kuramoto, etc.), domain-local structural metric extraction, projection to the shared embedding format, and invariant candidate production. Not a general math library.

---

## 2. ROLE WITHIN HELIX

The substrate provides the **Validation and Formalization bridge** between Library input and Atlas output:

- **Input**: Theoretical models and axioms (`codex/library/math/`)
- **Engine**: Runs simulations, extracts domain-local metrics, projects to shared embedding
- **Output**: Invariant candidates → governance validation → Atlas (via compiler gate)

---

## 3. COORDINATE SYSTEM SEPARATION

Two distinct axis systems exist within Helix. They are **not interchangeable**.

### A. Math-Domain Structural Metrics (`MathStructuralVector`)

Domain-local. Computed from simulation outputs. Description of structural properties in math-domain terms. Does not directly enter the Atlas.

| Axis | Symbol | Derived From |
|------|--------|-------------|
| Attractor Stability | `A_s` | Variance of periodic orbital points |
| Generative Constraint | `G_c` | Ratio of restricted to total state space |
| Recurrence Depth | `R_d` | Fractal dimension / self-similarity depth |
| Structural Density | `S_d` | Events per unit time window (sigmoid-normalized) |
| Control Entropy | `C_e` | Shannon entropy of control signal distribution |
| Basin Permeability | `B_p` | Lyapunov exponent-derived transition smoothness |

Implemented in: `domain_analysis/math_structural_vector.py`

### B. Shared Cross-Domain Embedding (`HelixEmbedding`)

System-wide format. Required on all Atlas entities. Six axes: Complexity, Structure, Repetition, Density, Expression, Variation. All float in [0.0, 1.0].

**Rule**: `MathStructuralVector` → `HelixEmbedding` is a named, versioned, documented projection. The axes share dimensional count by design; they are not equivalent.

Projection adapter: `embedding/projection.py` (schema version: `math_v1`)

---

## 4. PIPELINE (TARGET ARCHITECTURE)

```
Simulation Input
    ↓
Simulation Run (simulation/)
    ↓  [raw output]
Signal Extraction + MathStructuralVector (domain_analysis/)
    ↓  [MathStructuralVector]
Projection to HelixEmbedding (embedding/projection.py)
    ↓  [HelixEmbedding — projection_schema: math_v1]
Invariant Candidate Construction
    ↓
Governance Validation (core/governance/validation/)
    ↓
Compiler-Gated Atlas Persistence (core/compiler/)
    ↓
Atlas (codex/atlas/math/)
```

---

## 5. ENTRY POINT

**Target**: HSL command (`DISCOVER math.kuramoto ...`)\
**Current**: Direct Python pipeline. `pipeline.py` is a stub. Math testing enters via simulation scripts and `e2e.py` directly.

HSL integration is a known gap. No HSL route currently exists for the math probe family.

---

## 6. CONFIDENCE / CALIBRATION STATUS

The `0.30` minimum confidence threshold for embedding validity is **provisional**. It was set as a conservative initial default.

Calibration procedure (not yet performed):
1. Run Kuramoto model with K=0 (no coupling), randomized phases, N ≥ 100 times
2. Compute mean and std of projected embedding L2 norms
3. Set threshold at `mean + 2 * std`

Until calibration is completed, all threshold-based promotion decisions are provisional.

---

## 7. FORMAL PRINCIPLES

- **DCP (Decision Compression Principle)**: Possibility space narrows logistically; k sorts by coupling discreteness. Verified across games, language, music, math. See `codex/atlas/invariants/decision_compression.md`.
- **Regime Transition**: Detectable as step-ratio discontinuity within a DCP trajectory. First empirical evidence from math domain (prime gaps / Zhang 2013). See `codex/atlas/invariants/regime_transition.md`.
- **EIP / LIP**: Dissolved as standalone invariants. Reclassified as DCP trajectory modes (collapse mode and floor mode respectively). See `codex/atlas/invariants/decision_compression.md` §Trajectory Modes.

DCP metric is structurally defined and empirically validated. Regime transition has first evidence; needs cross-domain replication.

---

## 8. CAPABILITIES (TARGET)

- Formalization: converting abstract domain patterns into precise mathematical formulas
- Validation: stress-testing invariant candidates using adversarial simulations
- Alignment verification: proving whether two embeddings are truly similar under the Helix distance metric

---

## 9. CANONICAL FIXTURE: Kuramoto Oscillator Locking

The Kuramoto model is the current canonical simulation. It studies synchronization emergence as a function of coupling strength K.

**What it validates**:
- Metric sanity (A): high-K → more synchrony, lower entropy; low-K → opposite
- Simulation fixture (B): null-model guard (K=0 sync < 0.3), strong-locking guard (K=4 sync > 0.8), deterministic seed
- Projection consistency (C): range validity, determinism, self-similarity = 1.0, triangle inequality on distance

**Location**: `validation/kuramoto_fixture.py`
**Produces**: structured JSON validation artifact (persisted with `--out`)

---

## 10. IMPLEMENTATION MILESTONES

| Milestone | Status |
|-----------|--------|
| **Canonical fixture** | ✅ Implemented (`validation/kuramoto_fixture.py`) |
| **Domain-local projection** | ✅ Implemented (`embedding/projection.py`, schema `math_v1`) |
| **End-to-end candidate path** | ✅ Implemented (`e2e.py`) — produces compiler-ready payload |
| **Domain runtime** | ⚠️ Partial — Kuramoto sim + extraction implemented; full pipeline stub only |
| **HSL entry point** | ❌ Not yet implemented |
| **Atlas persistence** | ❌ Deferred — `e2e.py` produces candidate; enforce_persistence() not called |
| **DCP probes (open problems)** | ✅ `core/probes/math/probes/` — Ramsey, abc/Mochizuki, prime gaps, P vs NP, 7 mystery probes |
| **Regime transition evidence** | ✅ First confirmed in prime gaps (Zhang 2013, step_ratio=3.1×) |

---

## 11. CURRENT IMPLEMENTATION STATUS

| Component | Status |
|-----------|--------|
| Kuramoto simulation (`simulation/kuramoto.py`) | ✅ |
| Oscillator base class (`simulation/oscillator.py`) | ✅ |
| Feature extractor (`domain_analysis/feature_extractor.py`) | ✅ |
| Domain-local metrics (`domain_analysis/invariant_metrics.py`) | ✅ |
| Math structural vector (`domain_analysis/math_structural_vector.py`) | ✅ |
| Embedding projection adapter (`embedding/projection.py`) | ✅ |
| Domain validation harness (`validation/kuramoto_fixture.py`) | ✅ |
| End-to-end candidate path (`e2e.py`) | ✅ |
| Full pipeline (`pipeline.py`) | ⚠️ Stub — raises NotImplementedError |
| HSL entry point | ❌ Not implemented |
| Multi-domain invariant promotion | ❌ Not implemented |
| DCP metric calibration | ❌ Not calibrated against null baselines |
| EIP/LIP (dissolved) | ✅ Reclassified as DCP trajectory modes — no separate probe needed |

---

## 12. KNOWN GAPS

- `pipeline.py` is a stub; no complete orchestration path exists
- HSL does not route to the math domain
- Confidence threshold (0.30) is provisional; null-baseline calibration not performed
- EIP, DCP, LIP principle metrics are structurally defined but not computationally validated
- Atlas persistence is deferred; the e2e path produces a candidate but does not commit

---

*For formal axis definitions, metric formulas, and artifact schemas, see [SPEC.md](SPEC.md).*
