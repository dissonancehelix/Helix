# PSC Behavioral Impact Report

## Objective
Determine whether projection-unstable components materially affect classification performance or induce fragility under drift.

## Hypotheses
- **H1**: Unstable components cause high drift under transforms.
- **H2**: Stable components retain core predictive power.

## Cross-Dataset Summary
### Dataset: iris
- **Stable/Unstable Split**: 2 / 0
- **Full Stability Ratio**: 0.8667
- **Stable Model Delta (Perf Loss)**: 0.4889
- **Verdict**: H2_SUCCESS

### Dataset: wine
- **Stable/Unstable Split**: 0 / 13
- **Full Stability Ratio**: 0.8462
- **Stable Model Delta (Perf Loss)**: 0.5556
- **Verdict**: H2_SUCCESS

### Dataset: synthetic
- **Stable/Unstable Split**: 2 / 4
- **Full Stability Ratio**: 0.9117
- **Stable Model Delta (Perf Loss)**: 0.3700
- **Verdict**: H2_SUCCESS

