# PSC Embedding Discovery Report

## Objective
Assess whether semantic axes in a synthetic (but structured) embedding space are stable structural dimensions or projection artifacts.

## Results
- **Verdict**: STABLE
- **Baseline Dominance (Top PCA Component)**: 0.3328
- **Mean PSS (Family)**: 0.8781

### Transformation Breakdown
| Transform | RetentionOverlap | DominanceDrift | PSS |
|-----------|------------------|----------------|-----|
| T_scale | 0.8787 | 0.0634 | 0.8230 |
| T_minmax | 0.8774 | 0.0745 | 0.8120 |
| T_noise | 0.9924 | 0.0000 | 0.9924 |
| T_dropout | 0.7853 | 0.0285 | 0.7630 |
| T_rotate | 1.0000 | 0.0000 | 1.0000 |

## Falsifiers
If the mean PSS falls below 0.60 under isotopic rotation and scaling, the dominance claim for this space is REJECTED as a PROJECTION_ARTIFACT.
