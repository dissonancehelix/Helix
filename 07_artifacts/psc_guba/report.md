# GUBA Analysis Report (Geometrically Unstable but Behaviorally Anchored)

## Objective
Identify components that fail PSC geometric stability gates but retain significant, robust predictive signal.

## Cross-Dataset GUBA Status
### Dataset: iris
- **Unstable Candidates**: 0
- **GUBA Candidates Found**: 0
- **Verdict**: GUBA_ABSENT

### Dataset: wine
- **Unstable Candidates**: 4
- **GUBA Candidates Found**: 1
- **Verdict**: GUBA_PRESENT
  - Component 0: BAS=0.7647, CSI=0.0054, PSS=0.1063

### Dataset: synthetic
- **Unstable Candidates**: 3
- **GUBA Candidates Found**: 1
- **Verdict**: GUBA_PRESENT
  - Component 0: BAS=0.9732, CSI=0.0053, PSS=0.0653

