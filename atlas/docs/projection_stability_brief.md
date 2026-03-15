# Project Brief: Projection Stability Condition (PSC)

## 1. Problem
Projection artifacts often mislead modelers into identifying structural patterns that do not exist in the underlying data. Dimensionality reduction techniques (PCA, SVD, t-SNE) frequently produce low-rank representations that are sensitive to coordinate transformations and scaling.

## 2. Risk
When solver-dependent artifacts are interpreted as intrinsic geometry, the resulting models exhibit extreme instability under drift and rotation. This leads to the misidentification of "eigenspaces" and "latent dimensions" that collapse when data is standardized or re-scaled.

## 3. Solution
Helix introduces the **Projection Stability Condition (PSC)** as a primary admissibility gate for structural claims. It requires that any identified dimension must survive **isotopic transformation** (scaling, rotation, standardization).

The **Projection Stability Score (PSS)** maps these constraints into a single metric:
`PSS = RetentionOverlap * (1 - DominanceDrift)`

## 4. Results
Initial validation (B1-B4 Basis testing) compares the PSC against naive rank heuristics (e.g., "First component > 10% variance").
- **Naive Heuristic**: Often accepts high-variance components that disappear under random rotation or feature whitening.
- **PSC/PSS**: Rejects unstable components, correctly isolating dimensions that represent persistent physical or algorithmic constraints.

## 5. Practical Use
The PSC is implemented as a **pre-validation layer** in modern ML pipelines to filter out spurious latent dimensions before model training. It ensures that the discovered architecture represents structural truth rather than projection error.
