# Probe Catalog

Probe instruments live in `04_labs/probes/`. Each probe is a self-contained Python script that implements a measurement of a candidate invariant.

## Probe Contract

Every probe must:
1. Declare `VERSION = "x.y.z"` at module level
2. Read `HELIX_SYSTEM_INPUT` env var (JSON path to `{dataset_path, lab_name, run_id}`)
3. Write `probe_result.json` to `HELIX_ARTIFACT_DIR` env var
4. Exit 0 (pass) or 1 (fail)
5. Include canonical output fields: `signal`, `confidence`, `passed`, `probe_name`, `domain`

## Active Probes

| Probe | Invariant | Status |
|-------|-----------|--------|
| decision_compression_probe.py | Decision Compression | Active |
| oscillator_locking_probe.py | Oscillator Locking | Active |


---

## Architecture Guardrail

**Helix Architecture Law**
`HSL → Operator → Adapter → Toolkit → Artifact → Atlas Compiler`

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
