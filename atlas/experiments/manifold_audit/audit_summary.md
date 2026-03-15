# Helix Manifold Audit Summary

## Core Finding
Claimed k_90 = 1.
Recomputed k_90 = -1.
Verdict: **LABEL_ERROR**

## Diagnostics
- **Dominance Ratio**: 0.1316
- **Bootstrap Stability**: UNSTABLE
- **Leakage**: Highly correlated with Substrate/Ontology tags.

## Conclusion
The statement "Manifold Rank (90% Var): 1" is AN ARTIFACT of unscaled categorical encoding. 
