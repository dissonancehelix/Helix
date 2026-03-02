# Helix Deep-Layer Compression Verdict

**Verdict:** PARTIAL_KERNEL (Relabeling Risk)

## 1. Compression Results (K* Discovery)
- **Effective Rank (k_eff):** 4
- **Primary SV:** 13.4963
- **Explained Variance Ratio (Top 3):** [0.5204286645960016, 0.20153566140124024, 0.17131598395382816]

## 2. Representation Invariance
- **Max Isotopic Drift:** 2.80e-13
- **Status:** STABLE

## 3. Non-Circularity Audit (Kill Test)
- **C-Element -> K* Reconstruction Ratio:** 0.9856
- **Result:** CIRCULAR (Relabel)

## 4. Predictive Power Verification
- **Pathological Regime Accuracy (K*-only):** 1.0000

## 5. Adversarial Robustness
- **Status:** ROBUST_KERNEL
- **Persistence Score:** 0.98

---
Derived From: Deep-Layer Compression Suite v1
