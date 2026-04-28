# system/engine/checks/

Drift checks. Run from this folder; underlying harness currently lives at
`system/engine/agent_harness/check_workspace.py` and is invoked via
`run_checks.py`.

## Usage

```bash
python system/engine/checks/run_checks.py
```

## What is checked

- Required root files exist: `README.md`, `DISSONANCE.md`, `AGENTS.md`.
- Required root dirs exist: `model/`, `data/`, `system/`, `labs/`, `reports/`, `quarantine/`.
- `scratch/` is allowed but warns (legacy temporary; disposition pending).
- No raw data files inside `system/engine/` outside the allow-list.
- All six `model/map/*.yaml` files parse and match the `{version, status, items}` shape.
- Exactly one root `DISSONANCE.md`; no duplicate ontology files at root.
- Every `model/domains/<name>/` has a `README.md` or `README.template.md`.

## Phase awareness

The checker's allow-list reflects the current workspace ontology. It must not be stricter than the migration phase, or it becomes a trap. As future phases decide on `scratch/`, tool reclassification, or `labs/research/*` splits, update this checker in lockstep.

