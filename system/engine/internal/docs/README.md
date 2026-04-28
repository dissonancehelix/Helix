# system/engine/internal/docs/

Internal engine documentation lives here. It is not a second root documentation system; root `README.md`, `DISSONANCE.md`, and `AGENTS.md` remain the workspace-level canon.

**Machine-readable manifest:** [`manifest.yaml`](manifest.yaml)

## Structure

```text
system/engine/internal/docs/
  README.md
  manifest.yaml
  architecture/
  governance/
  invariants/
  research/
  profiles/
```

## Boundaries

- Domain docs stay with their domain under `model/domains/<domain>/`.
- Tool docs stay with their tool under `system/tools/<tool>/`.
- Engine subsystem docs stay with their subsystem under `system/engine/`.
- Experiment artifacts belong under `labs/`.
- Library, atlas, and generated data belong under `data/`.

These documents can explain engine internals, but they do not override the root workspace ontology.

