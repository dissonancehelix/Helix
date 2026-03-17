# REGIME DESIGN SPECIFICATION

## REGIME B1: FEEDBACK LOOP AMPLIFICATION
**Dynamics:**
- Edges act as directed flow channels with unit time delays.
- Load cascades across edges with an amplification gain multiplier (`g = 1.2`).
- A node fails only if its load exceeds capacity for `T=2` consecutive timesteps (hysteresis resistance).
**Anti-Centrality Core:**
Because of the positive gain, cyclic subgraphs explode in load rapidly, irrespective of global MaxDegree. High-degree hubs without cyclic embedding remain robust, whereas low-degree nodes trapped in cyclic reverb cascade quickly.

## REGIME B2: CORRELATED SHOCK PROPAGATION
**Dynamics:**
- Nodes possess continuous underlying exposure embeddings across `K=3` latent factors.
- Network capacities are normalized uniformly (`C = 3.0`). 
- Shocks are injected probabilistically against latent dimensions.
- Collapse flow routes structurally through edges, scaling proportionally to the dot-product similarity (overlap) of latent vectors.
**Anti-Centrality Core:**
Failures cascade through correlation clusters. A massive central hub with zero latent alignment acts as a firewall, while a peripheral sparse cluster with high latent synchronization fragments instantly. Structural correlation dominates over aggregate connectivity.
