# core/engine/checks/

Drift checks. Run from this folder; underlying harness currently lives at
`core/engine/agent_harness/check_workspace.py` and is invoked via
`run_checks.py`.

## Usage

```bash
python core/engine/checks/run_checks.py
```

## What is checked

- Required root files exist: `README.md`, `DISSONANCE.md`, `AGENTS.md`.
- Required root dirs exist: `model/`, `data/`, `system/`, `labs/`, `reports/`, `quarantine/`.
- `scratch/` is allowed but warns (legacy temporary; disposition pending).
- No raw data files inside `core/engine/` outside the allow-list.
- All six `core/map/*.yaml` files parse and match the `{version, status, items}` shape.
- Exactly one root `DISSONANCE.md`; no duplicate ontology files at root.
- Every `domains/<name>/` has a named `<DOMAIN>.md` file.

## Phase awareness

The checker's allow-list reflects the current workspace ontology. It must not be stricter than the migration phase, or it becomes a trap. As future phases decide on `scratch/`, tool reclassification, or lab ownership splits, update this checker in lockstep.
