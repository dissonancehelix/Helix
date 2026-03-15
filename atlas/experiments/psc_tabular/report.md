# PSC Tabular Discovery Report

## Objective
Evaluate whether PCA "dominance claims" in standard tabular datasets are intrinsic structural properties or scaling artifacts.

### Dataset: iris
- **Verdict**: INDETERMINATE
- **Mean PSS**: 0.8013

| Transform | SubspaceStability | DominanceDrift | PSS |
|-----------|-------------------|----------------|-----|
| T_standard | 0.9131 | 0.1950 | 0.7350 |
| T_minmax | 0.9374 | 0.0833 | 0.8593 |
| T_robust | 0.8794 | 0.3049 | 0.6113 |
| T_noise | 1.0000 | 0.0003 | 0.9997 |

### Dataset: wine
- **Verdict**: UNSTABLE
- **Mean PSS**: 0.3375

| Transform | SubspaceStability | DominanceDrift | PSS |
|-----------|-------------------|----------------|-----|
| T_standard | 0.3219 | 0.6361 | 0.1171 |
| T_minmax | 0.3037 | 0.5906 | 0.1243 |
| T_robust | 0.3290 | 0.6696 | 0.1087 |
| T_noise | 1.0000 | 0.0000 | 1.0000 |

