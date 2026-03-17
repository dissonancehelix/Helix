# Helix Deep-Layer Compression Verdict

**Verdict:** PARTIAL_KERNEL (Relabeling Risk)

## 1. Compression Results (K* Discovery)
- **Effective Rank (k_eff):** 4
- **Primary SV:** 13.8601
- **Explained Variance Ratio (Top 3):** [0.5488613693434846, 0.2299531750335365, 0.13347430916318737]

## 2. Representation Invariance
- **Max Isotopic Drift:** 4.00e-13
- **Status:** STABLE

## 3. Non-Circularity Audit (Kill Test)
- **C-Element -> K* Reconstruction Ratio:** 0.9868
- **Result:** CIRCULAR (Relabel)

## 4. Predictive Power Verification
- **Pathological Regime Accuracy (K*-only):** 1.0000

## 5. Adversarial Robustness
- **Status:** ROBUST_KERNEL
- **Persistence Score:** 0.98

---
Derived From: Deep-Layer Compression Suite v1
