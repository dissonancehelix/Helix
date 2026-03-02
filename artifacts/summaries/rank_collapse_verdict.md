# Helix Rank Collapse & Element Minimality Verdict

**Verdict:** LOW_RANK_PLURALITY

## Phase 1: Redundancy Compression
- **C3 Reconstruction Ratio:** 0.0000 (INDEPENDENT)
- **C4 Reconstruction Ratio:** 0.4466 (INDEPENDENT)

## Phase 2: Cross-Regime Holdout (Mean IG)
- **C3 Stability (N=7):** 0.0019
- **C4 Stability (N=7):** 0.0052

## Phase 3: Adversarial Inversion
- **C3 Adversarial IG:** 0.1219
- **C4 Adversarial IG:** 0.1719

## Phase 4: Minimal Basis SVD
- **Effective Rank:** 5
- **Variance Explained (Top 3):** 0.7906
- **Variance Explained (Top 4):** 0.9214
- **Singular Values:** [65.35309204188121, 50.67736276085507, 45.5959868045076, 38.412990196589504, 29.7695548040943]

## Phase 5: Element Necessity Ablation (ΔIG)
- **C1:** 0.1061 (ESSENTIAL)
- **C2:** 0.2923 (ESSENTIAL)
- **C8:** 0.0141 (REDUNDANT)
- **C3:** 0.1164 (ESSENTIAL)
- **C4:** 0.1253 (ESSENTIAL)

## Phase 6: Feature Entanglement Audit
- **C1 Leakage IG:** 0.0085 (CLEAN)
- **C2 Leakage IG:** 0.0017 (CLEAN)
- **C8 Leakage IG:** 0.0022 (CLEAN)
- **C3 Leakage IG:** 0.0019 (CLEAN)
- **C4 Leakage IG:** 0.0043 (CLEAN)

---
Derived From: Rank Collapse Suite v1
