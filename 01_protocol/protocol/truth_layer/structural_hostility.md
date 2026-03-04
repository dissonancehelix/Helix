# Structural Hostility Requirement

## 1. Scope
Every major claim (Rank, Manifold Stability, New Base, Feasible Transfer) MUST survive the following suite of adversarial tests before promotion.

## 2. Mandatory Tests
- **Scaling Invariance**: Survival across raw data, `StandardScaler`, `RobustScaler`, and whitening.
- **Encoding Dominance Test**: Detect if categorical token frequency dominates the projection (e.g., TF-IDF artifacts).
- **Projection Family Rotation**: Consistency across SVD, PCA, Kernel PCA, and Diffusion Maps.
- **Feature Permutation Null**: The claim MUST be statistically significant compared to a random feature-shuffled model.
- **Domain Dropout**: Stability of the manifold structure under random removal of up to 20% of the dataset.
- **Basis Ablation**: Measuring the effect of removing the base on overall coordinate resolution and transfer precision.
- **Leakage Audit**: Confirmation of non-derivative status relative to Ring 0 and Ring 1 metadata (R^2 < 0.10).
- **Transfer Feasibility Overlay**: Manual or mechanism-aware verification of geometric neighbors for mechanism compatibility.

## 3. Documentation Mandate
No claim can be promoted to Ring 1 or higher without a corresponding **Hostility Survival Report** detailing the outcome of the above tests.
