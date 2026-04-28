## HISTORICAL_RESULT
(Warning: Unverified Numeric Claims)

# PSC Discovery Claims: Structural Truth vs Projection Artifacts

## Claim 1: Embedding Stability (Embedding PSC)
**Finding**: Semantic axes in structured (rank-5) embedding spaces exhibit **STABLE** (PSS: 0.8781) dominance claims across T_scale and T_rotate.
**Condition**: Neighborhood retention persists above 0.85 despite dimension scaling, suggesting that semantic structure in such spaces is primarily topological and coordinate-independent.

## Claim 2: Tabular PCA Dominance (Tabular PSC)
**Finding**: Dominance claims in unscaled tabular datasets (e.g., wine, iris) are **PROJECTION_ARTIFACTS** (PSS: 0.3375 to 0.8013).
**Condition**: In the wine dataset, the top-variance component (99.8%) collapses to near-zero (approx. 11% PSS) after standardization. This confirms that "importance" in unscaled tabular data is a scaling-dependent error rather than an intrinsic structural property.

## Claim 3: Scaler Sensitivity
**Finding**: Robust scaling (RobustScaler) has a higher distortion effect on subspace stability (PSS: 0.6113 on iris) than MinMaxScaler (PSS: 0.8593).
**Condition**: Any "dominance" claim must be tested against at least three divergent scaling regimes (T_scale) to be considered admissible in the Helix repository.
