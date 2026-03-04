## HISTORICAL_RESULT
(Warning: Unverified Numeric Claims)

# PSC Discovery Suite: Projection Stability Condition (PSC) Overview

## Purpose
The Projection Stability Condition (PSC) is a structural admissibility gate (Ring 1 discipline) used to identify whether dominant geometric dimensions (e.g., PCA components, embedding axes) are intrinsic to the data or mere artifacts of the projection methodology.

## Methodology
Every discovery suite implementing the PSC must compute the **Projection Stability Score (PSS)**:
`PSS = RetentionOverlap * (1 - DominanceDrift)`

1. **RetentionOverlap**: Measures how well the neighborhood structure (kNN) or the subspace identity is preserved across **isotopic transformations**.
2. **DominanceDrift**: Measures the absolute change in the explained variance ratio of the top component(s) after transformation.

### Admissible Isotopic Transformations
- **T_scale**: Standardization (zero-mean, unit-variance) or MinMax scaling.
- **T_rotate**: Random orthogonal rotation defined in the feature space.
- **T_noise**: Additive Gaussian noise (small sigma, e.g., 0.01 to 0.05).
- **T_dropout**: Feature masking/dropping (10-20% of dimensions).

## Success Criteria (PSS Thresholds)
- **STABLE (PSS >= 0.85)**: The dimension represents a fundamental architectural property.
- **UNSTABLE (PSS < 0.60)**: The dimension is a PROJECTION_ARTIFACT (scaling or coordinate-dependent error).
- **INDETERMINATE**: The claim requires higher-resolution densification or adversarial null-testing.

## Integrated Discovery Suites
- `sandbox/experiments/psc_embedding_suite.py`: Semantic embedding stability.
- `sandbox/experiments/psc_tabular_suite.py`: Tabular feature-dominance stability.
