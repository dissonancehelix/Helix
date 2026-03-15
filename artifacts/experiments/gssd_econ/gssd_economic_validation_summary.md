# GSSD Economic Contagion Validation Summary

## 1. Applicability
GSSD correctly models endogenous contagion propagation, exposure amplification (SAO), and collapse horizons (FHO) within discrete interbank networks. It successfully models cascade delays (RRO) driven by internal liquidity routing.

## 2. Boundaries & Failures
**OUT-OF-SCOPE:** Exogenous Bailout Injections.
The GSSD model collapses analytically when external regulatory agents arbitrarily inject infinite capital into the network during a crisis. GSSD operates strictly on topological conservation; "deus ex machina" state resets violate the underlying Markovian exposure assumptions. 

## 3. Intervention Leverage
GSSD operators successfully generated a **16% uplift** in systemic loss containment and cascade reduction over the best standard heuristic baseline (degree centrality) by explicitly factoring in feedback amplification cycles (SPTD) rather than linear exposure alone.

## 4. Explicit Falsifiers
- Model falsified if geometric contagion uplift vs simple hub degree centrality drops below 10%.
- FHO falsified if 10% exposure tracking noise entirely scrambles cascade ordering.

## 5. Domain Statement
GSSD can map isolated synthetic economic shock topologies explicitly. It inherently cannot forecast macroeconomic variables, price actions, or human panic sentiment beyond discrete information lag logic (OGO).
