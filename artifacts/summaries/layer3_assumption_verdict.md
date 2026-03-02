# Helix Layer 3 Assumption Stress & Reduction Verdict

**Verdict:** IRREDUCIBLE_PLURALITY

## Phase 1: Necessity Ablation (ΔIG)
| Assumption | C1 | C2 | C3 | C4 |
| :--- | :--- | :--- | :--- | :--- |
| A1 | -0.009 | 0.088 | 0.014 | 0.032 |
| A2 | 0.099 | -0.040 | -0.000 | -0.035 |
| A3 | 0.082 | 0.005 | 0.024 | -0.058 |
| A4 | 0.119 | -0.066 | -0.034 | -0.075 |
| A5 | 0.037 | -0.111 | -0.127 | 0.286 |

## Phase 2: Sufficiency Summary
- **C1 Emergence:** INSUFFICIENT (Black Box) (MI: 0.4569)
- **C2 Emergence:** INSUFFICIENT (Black Box) (MI: 0.2419)
- **C3 Emergence:** INSUFFICIENT (Black Box) (MI: 0.1492)
- **C4 Emergence:** INSUFFICIENT (Black Box) (MI: 0.3566)

## Phase 3: Reduction Matrix
- **A1:** PRIMITIVE (Compression Ratio: 0.0169)
- **A2:** PRIMITIVE (Compression Ratio: 0.0472)
- **A3:** PRIMITIVE (Compression Ratio: 0.0166)
- **A4:** PRIMITIVE (Compression Ratio: 0.0170)
- **A5:** PRIMITIVE (Compression Ratio: 0.0004)

## Phase 4: Assumption Independence Graph (MI Matrix)
| | A1 | A2 | A3 | A4 | A5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| A1 | 1.000 | 0.052 | 0.149 | 0.048 | 0.020 |
| A2 | 0.052 | 1.000 | 0.344 | 0.351 | 0.000 |
| A3 | 0.149 | 0.344 | 1.000 | 0.070 | 0.000 |
| A4 | 0.048 | 0.351 | 0.070 | 1.000 | 0.017 |
| A5 | 0.020 | 0.000 | 0.000 | 0.017 | 1.000 |

## Phase 5: Circularity Audit
- CIRCULARITY_NOT_DETECTED (Structural isolation maintained)

---
Derived From: Assumption Stress Suite v1
