# Forecasting Falsifiers

## Dead Code Evasion (The Silent Neutral)
**Hypothetical Attack:** A developer introduces a massive topological cycle with deep fan-in, simulating massive ΔCFS. However, the root entrypoint to this cycle is fundamentally unreachable (dead code).
**Falsification Output:** The Forecaster predicts extreme structural decay (+0.40 ΔCFS). The real hostility suite outputs +0.00 ΔCFS because the code is never traversed.
**Resolution Needed:** Forecaster must weight AST node inclusion by Reachability.

## Pure Configuration Impostors
**Hypothetical Attack:** JSON configurations parsed into static data records.
**Falsification Output:** Removing "validation" over a configuration file that only dictates localized UI color palettes predicts a structural fragility spike. Real disruption is purely aesthetic, not structural.
