# Helix Layered Constraint Pyramid

**Verdict:** PARTIALLY_REDUCIBLE

## 1. Constraint Origin Analysis (Layer 3 -> Layer 2)
### C1 (REGIME_CONSTRAINT)
- **Necessity:** NECESSARY
- **Derivation Attempts:**
  - Derived from **A2_RESOURCES** (ΔIG: 0.0990)
  - Derived from **A3_PERTURBATION** (ΔIG: 0.0821)
  - Derived from **A4_LOCALITY** (ΔIG: 0.1192)
  - **DERIVED_CONSTRAINT**: Reduced to more primitive assumptions.
### C2 (REGIME_CONSTRAINT)
- **Necessity:** NECESSARY
- **Derivation Attempts:**
  - Derived from **A1_BANDWIDTH** (ΔIG: 0.0884)
  - **DERIVED_CONSTRAINT**: Reduced to more primitive assumptions.
### C3 (REGIME_CONSTRAINT)
- **Necessity:** NECESSARY
- **Derivation Attempts:**
  - **PRIMITIVE_CONSTRAINT**: No significant reduction found among A1-A5.
### C4 (REGIME_CONSTRAINT)
- **Necessity:** NECESSARY
- **Derivation Attempts:**
  - Derived from **A5_CONSISTENCY** (ΔIG: 0.2864)
  - **DERIVED_CONSTRAINT**: Reduced to more primitive assumptions.

## 2. Dependency Matrix Snapshot
| Element | A1 | A2 | A3 | A4 | A5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| C1 | -0.009 | 0.099 | 0.082 | 0.119 | 0.037 |
| C2 | 0.088 | -0.040 | 0.005 | -0.066 | -0.111 |
| C3 | 0.014 | -0.000 | 0.024 | -0.034 | -0.127 |
| C4 | 0.032 | -0.035 | -0.058 | -0.075 | 0.286 |

## 3. Pyramid Consistency Check
- **Circularity:** NONE_DETECTED
- **Hierarchy:** Layer 3 (Abstract Assumptions) -> Layer 2 (Structural Elements) -> Layer 1 (Phenomenology)

---
Derived From: Constraint Pyramid Suite v1
