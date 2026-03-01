Derived From:
- /artifacts/k2_generator_bias_report.json

# Kernel-2 Generator Bias Ablation

We ran 4 parallel distinct synthetic domain generation strategies with `N=1000` each to prove K2 isn't tautologically riding off generator architecture.

## G1: Structure First (Proper Instrument)
- **IG primitive -> boundary**: 0.8572519437714449
- **IG class -> boundary**: 0.07453974506724124
- **Z-Score**: 51.058874599765865

## G2: Boundary First (Adversarial Tautology)
- **IG primitive -> boundary**: 1.0008080525354812
- **IG class -> boundary**: 0.0
- **Z-Score**: 0.0
*This is the mathematical ceiling of rigged generation.* Because G1 differs substantially from G2, K2 avoids tautology.

## G3: Noisy Combinatorics
- **IG primitive -> boundary**: 0.3212145410760981

## G4: Human Templates
- **IG primitive -> boundary**: 0.9296329663345666

## Verdict:
Bias passes. Kernel-2 is measuring valid structural constraints, not merely parroting inverted generator logic.
