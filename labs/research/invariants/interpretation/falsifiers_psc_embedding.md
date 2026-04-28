## HISTORICAL_RESULT
(Warning: Unverified Numeric Claims)

# Falsifier: Embedding Projection Stability (PSC)

This document defines the conditions under which the stable dominance claims in `psc_embedding_suite.py` are falsified.

## Falsifier 1: PSS Decay Gradient
If the mean Projection Stability Score (PSS) falls below **0.60** under any of the following transforms, the "semantic axis" claim is falsified:
- **T_scale**: StandardScaler standardization.
- **T_rotate**: Random orthogonal rotation.
- **T_dropout**: 10% dimension masking.

## Falsifier 2: Null Indistinguishability
If the observed PSS is within **2σ** of the PSS produced by a dimension-independent shuffle (feature_permutation null), the result is classified as a **RANDOM_PROJECTION_ARTIFACT**.

## Current Thresholds (from artifacts/psc_embedding/results.json)
- **Top PCA Component (Baseline)**: 0.3328
- **Mean PSS (Observed)**: 0.8781
- **Verdict**: STABLE (Pending higher-order adversity)
