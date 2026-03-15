# Falsifier Expansion

## L1_TopologicalMass: `d(CFS) / d(FanIn) > 0`
**Synthetic Breakdown:** A highly-fanned configuration manifest (JSON/YAML mapped into code objects) has enormous FanIn but zero logic fragility.
**Verdict:** `STRONG` for logic execution layers; `FAILS` on configuration/data substrate layers. Must filter nodes with McCabe Complexity = 1.

## L2_ValidationAnchoring: `d(SDR) / d(ValidationDensity) < 0`
**Synthetic Breakdown:** A repository using generative type wrappers where validation strings are procedurally generated but never enforce runtime truth.
**Verdict:** `STRONG` for compiled languages (Go); `VULNERABLE` in dynamically typed ecosystems (JS/Lua) if validations evaluate to no-ops.

## L3_TraceObservability: `d(OD) / d(TraceDensity) < 0`
**Synthetic Breakdown:** Trace density artificially inflated by automated linters inserting default IDs without human-semantic mapping.
**Verdict:** `VULNERABLE`. Traces only reduce Observability Deficit if they connect cross-references. Isolated traces provide no reduction.

## L4_CycleFragilitySpike: `d(CFS) / d(CycleDensity) > 1.0`
**Synthetic Breakdown:** Functional pure ecosystems (Haskell) or immutable cycle reducers where cyclical references are handled purely safely at compile-time.
**Verdict:** `STRONG` explicitly for imperative block memory patterns (Python, JS, Lua, Go); naturally falsifiable under pure functional paradigms.
