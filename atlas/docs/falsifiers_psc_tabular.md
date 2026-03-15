## HISTORICAL_RESULT
(Warning: Unverified Numeric Claims)

# Falsifier: Tabular Projection Stability (PSC)

This document defines the conditions under which the stable dominance claims in `psc_tabular_suite.py` are falsified.

## Falsifier 1: Scaling Drift Threshold
If the dominance drift `abs(base_share - trans_share)` exceeds **0.25** under any standard scaler (Standard, MinMaxScaler, RobustScaler), the dominance claim is REJECTED as a **SCALING_ARTIFACT**.

## Falsifier 2: Subspace Divergence
If the principal angles (mean cosine overlap) between the raw and scaled top-k subspaces (k=2) falls below **0.70**, the subspace is **NON_FUNDAMENTAL**.

## Instance: Wine Dataset (from artifacts/psc_tabular/results.json)
- **Top PCA Component (Baseline)**: 0.9981 (High raw variance dominance)
- **Mean PSS (Observed)**: 0.3375
- **Verdict**: UNSTABLE. The wine dataset's raw PCA dominance is an artifact of unscaled features and vanishes under standardization.
