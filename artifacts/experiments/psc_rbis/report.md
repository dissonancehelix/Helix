# RBIS Verdict: Representation vs Behavior Invariance

## Objective
Identify domains where functional utility (Behavior) is decoupled from geometric coordinate stability (Representation).

## Verdict Table
| Domain | Verdict | PSS | BAS | Fragility | Relevance |
|--------|---------|-----|-----|-----------|-----------|
| iris | HYBRID | 0.733 | 0.956 | 0.122 | N/A |
| wine | BIC | 0.106 | 0.667 | 0.134 | POTENTIAL_COMPRESSION |
| breast_cancer | HYBRID | 0.157 | 0.922 | 0.161 | N/A |
| high_redundancy | HYBRID | 0.905 | 0.678 | 0.057 | N/A |
| imbalanced | HYBRID | 0.824 | 0.870 | 0.000 | N/A |

## Discovery Log Summary
- **iris** [HYBRID]: Accuracy collapsed/dependent on scale. (Relevance: N/A)
- **wine** [BIC]: Functional utility survives hostility. (Relevance: POTENTIAL_COMPRESSION)
- **breast_cancer** [HYBRID]: Accuracy collapsed/dependent on scale. (Relevance: N/A)
- **high_redundancy** [HYBRID]: Accuracy collapsed/dependent on scale. (Relevance: N/A)
- **imbalanced** [HYBRID]: Accuracy collapsed/dependent on scale. (Relevance: N/A)
