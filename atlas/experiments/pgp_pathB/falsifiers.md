# PATH B FALSIFIERS

**Objective:** Define the boundaries under which Anti-Centrality Cascade Physics are considered falsified, ensuring that the model does not inadvertently become centrality-dominated or that operators aren't 'gaming' the artifacts.

## 1. Topographic Reversion Falsifier
How the regime could accidentally become centrality-dominated again:
If nodes are assigned capacities strictly linearly scaled by in-degree without hysteresis or latent factors, the regime will collapse back to `MaxDegree` dominance. If `R²(MaxDegree, CollapseSize) > 0.60` with a linear capacity map, the anti-centrality design is invalid.

## 2. Artifact Gaming Falsifier
How an operator could be gaming the simulation artifacts:
If an operator embeds `capacity_threshold` or `exposure_intersection` as an explicit input feature (rather than deriving it structurally from graph bounds), it is gaming the simulation knowledge. The operator must output predictions WITHOUT measuring the injected weights.

## 3. Propagation Disproof
What observation would invalidate any claimed uplift:
If an operator demonstrates a Δ≥0.10 uplift on B1 and B2, but fails entirely (Δ < 0) when directed edges are randomly rewired while maintaining identical degree sequences (configuration model null test), the operator is merely memorizing localized edge alignments and not identifying global topological propagation limits.
