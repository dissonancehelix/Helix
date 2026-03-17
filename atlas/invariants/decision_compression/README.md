# Invariant: decision_compression

Track for empirical invariant discovery via Helix probe system.

## Status: Exploratory

## Probe
See `04_labs/probes/decision_compression_probe.py` when implemented.


---

## Architecture Guardrail

**Helix Architecture Law**
`HIL → Operator → Adapter → Toolkit → Artifact → Atlas Compiler`

* Operators orchestrate
* Adapters translate
* Toolkits execute
* Artifacts store results
* Atlas compiler creates entities

**Prohibited Patterns**
- `master_pipeline.py`
- Direct toolkit calls from operators
- Toolkits writing artifacts
- Toolkits writing Atlas entities
- Operators writing Atlas entities
- Monolithic pipelines

*All new modules must follow the template registry located in `runtime/templates/`.*
