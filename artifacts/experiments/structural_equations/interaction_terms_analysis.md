# Interaction Terms Analysis

## Equation
`CFS = α + β_1*log(FanIn+1) + β_2*(CycleDensity * ValidationDensity)`

## Observations
The interaction term (`CycleDensity * ValidationDensity`) consistently yields a negative coefficient across all evaluated ecosystems.
- **Physical Interpretation:** Validation boundaries suppress the baseline fragility injected by cyclic topologies.
- **Magnitude:** The interaction effect size dictates that high-cycle graphs require exponential validation density to maintain constant CFS.
- **Stability:** Evaluated as ecosystem-weighted, meaning runtime constraints (compiled vs interpreted) alter the suppression scalar, but the sign remains universally negative.
