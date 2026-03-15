# Helix Rank Collapse & Element Minimality Verdict

**Verdict:** LOW_RANK_PLURALITY

## Phase 1: Redundancy Compression
- **C3 Reconstruction Ratio:** 0.0219 (INDEPENDENT)
- **C4 Reconstruction Ratio:** 0.4629 (INDEPENDENT)

## Phase 2: Cross-Regime Holdout (Mean IG)
- **C3 Stability (N=7):** 0.0043
- **C4 Stability (N=7):** 0.0050

## Phase 3: Adversarial Inversion
- **C3 Adversarial IG:** 0.1210
- **C4 Adversarial IG:** 0.1648

## Phase 4: Minimal Basis SVD
- **Effective Rank:** 5
- **Variance Explained (Top 3):** 0.7783
- **Variance Explained (Top 4):** 0.9223
- **Singular Values:** [69.59060855729314, 54.15046382714188, 49.55282274155392, 43.5159543372912, 31.949239309577347]

## Phase 5: Element Necessity Ablation (ΔIG)
- **C1:** 0.1872 (ESSENTIAL)
- **C2:** 0.2464 (ESSENTIAL)
- **C8:** 0.0071 (REDUNDANT)
- **C3:** 0.1007 (ESSENTIAL)
- **C4:** 0.1268 (ESSENTIAL)

## Phase 6: Feature Entanglement Audit
- **C1 Leakage IG:** 0.0257 (CLEAN)
- **C2 Leakage IG:** 0.0035 (CLEAN)
- **C8 Leakage IG:** 0.0043 (CLEAN)
- **C3 Leakage IG:** 0.0042 (CLEAN)
- **C4 Leakage IG:** 0.0090 (CLEAN)

---
Derived From: Rank Collapse Suite v1
