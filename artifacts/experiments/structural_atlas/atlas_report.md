# HELIX STRUCTURAL ATLAS — DOMAIN ATAVISM REPORT

## 1. Metric Overview

| Domain | Stability (PSS) | Compression (1/k) | BAS | Status |
| :--- | :--- | :--- | :--- | :--- |
| **iris** | 0.920 | 0.833 | 0.980 | ROBUST |
| **wine** | 0.580 | 0.952 | 0.910 | BIC_CANDIDATE |
| **synthetic_imbalanced** | 0.840 | 0.556 | 0.420 | METRIC_SENSITIVE |
| **embedding_cluster** | 0.650 | 0.294 | 0.760 | HIGH_DENSITY |

## 2. Structural Manifold
(Representation of Domain Proximity in Stability/Compression Space)

```markdown
COMPRESSION ^
            | 
            | [Top-Left] (GUBA/Fragile)       [Top-Right] (Robust/Elite)
    1.00 ---|    * wine                      * iris
            | 
            | 
    0.50 ---|    * embedding_cluster         * synthetic_imbalanced
            | [Bottom-Left] (Noise)           [Bottom-Right] (Distributed)
            +--------------------------------------------------------> INTEGRITY
              0.00                    0.50                    1.00
```

## 3. Analysis
- **Wine Anomaly**: Identified as a high-compression, low-integrity domain. It represents structure that survives behaviorally but decomposes geometrically under rot. This marks it as a prime target for 'Invariance Extraction'.
- **Iris Dominance**: Represents the structural ideal for Helix substrate admission—highly stable and highly compressed.
