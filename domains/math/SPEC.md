# HELIX MATH SUBSTRATE SPECIFICATION (SPEC)

**Version:** 1.0
**Status:** Authoritative technical specification
**Relationship:** Implementation partner to `domains/math/README.md`

---

## 1. FORMAL DEFINITIONS (THE CORE 6 AXES)

The Math Substrate formalizes the CCS axes as follows:

### 1.1 Attractor Stability ($A_s$)
The inverse of the variance of the periodic orbit points ($V_{po}$).
$$A_s = 1 - \frac{V_{po}}{V_{max}}$$

### 1.2 Generative Constraint ($G_c$)
The ratio of the restricted state space ($S_{res}$) to the total possible state space ($S_{tot}$).
$$G_c = 1 - \frac{\text{dim}(S_{res})}{\text{dim}(S_{tot})}$$

### 1.3 Recurrence Depth ($R_d$)
The hierarchical level of detectable self-similarity or fractal dimension ($D_f$).
$$R_d = \frac{D_f}{k_{norm}}$$

### 1.4 Structural Density ($S_d$)
The events ($E$) per unit time window ($\Delta t$), domain-normalized.
$$S_d = \text{sigmoid}(\lambda \cdot \frac{E}{\Delta t})$$

### 1.5 Control Entropy ($C_e$)
The Shannon entropy ($H$) of the control signal distribution ($P(x)$).
$$C_e = \frac{-\sum P(x) \log P(x)}{H_{max}}$$

### 1.6 Basin Permeability ($B_p$)
The characteristic of the transition function between structural states, related to the Lyapunov exponent ($\lambda_L$).
$$B_p = \exp(-\lambda_L)$$

---

## 2. EXTRACTION & VALIDATION PIPELINE

| Stage | Responsibility | Output |
|-------|----------------|--------|
| 1 | Model Definition | Formal Axiom Set |
| 2 | Simulation Run | State Space Trajectories |
| 3 | Signal Extraction | Time-series / Topologies |
| 4 | Metric Calculation | Raw Numerical Metrics |
| 5 | CCS Projection | Normalized CCS Embedding |
| 6 | Principle Validation | Verify EIP/DCP/LIP Constants |
| 7 | Invariant Validation | P-value against Null Model |

---

## 3. FORMAL PRINCIPLE METRICS

The SPEC formalizes the principles into measurable metrics:

### 3.1 EIP (Epistemic Irreversibility)
Measured as the **Entropy Collapse Rate ($E_{cr}$)**: The speed at which a state space becomes irreversible over time.

### 3.2 DCP (Decision Compression)
Measured as the **Commitment Density**: The degree to which influence is concentrated in a limited number of "Locked" states.

### 3.3 LIP (Constrained Inference)
Measured as the **Structural Alignment Score**: The degree to which an invariant survives across independent dialects.

### 3.1 FormalModel (`artifacts/math/<id>/model.json`)
```json
{
  "model_type": "kuramoto",
  "parameters": {"k": 0.5, "n": 100},
  "axioms": ["..."]
}
```

### 3.2 InvariantReport (`artifacts/math/<id>/invariant.json`)
```json
{
  "candidate": "oscillator_locking",
  "confidence": 0.94,
  "dissonance_score": 0.06,
  "verification_status": "VERIFIED"
}
```

---

## 4. CCS EMBEDDING & DISTANCE VALIDATION

The Math Substrate is the authoritative source for the **Helix Metric Space**. All `alignment_score` calculations must be validated against the **Euclidean Distance ($\sqrt{6}$ norm)** defined in the core SPEC.

- **Similarity Check**: `score = 1 - (d / sqrt(6))`
- **Dissonance Detection**: Any embedding that violates the metric's triangle inequality must be flagged as a **Structural Failure**.
