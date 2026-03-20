# Helix

Helix is a closed-system invariant discovery engine.

Its canonical pipeline is:

```text
codex/library -> HSL -> operators -> compiler -> codex/atlas
```

## Repository shape

- `docs/` — genetic reconstruction layer for the whole system.
- `core/` — execution-only code: HSL, normalization, semantics, operators, compiler, governance, engines.
- `codex/library/` — raw priors, reference corpora, and unvalidated source material.
- `codex/atlas/` — compiler-gated semantic output.
- `domains/` — canonical domain pipelines.
- `labs/` — experiments, probes, and consolidated datasets.
- `applications/` — built interfaces and diagnostics.
- `execution/` — artifacts, logs, run history, and integrity outputs.

## Architectural rules

1. HSL is the only supported entry point for core workflows.
2. `core/compiler/atlas_compiler.py` is the only authorized Atlas write path.
3. Entity IDs must use `domain.type:slug`.
4. Library data and Atlas knowledge are separate and may not be conflated.
5. Domains are canonical pipelines; labs are experiments.

See `docs/` for the full reconstruction specification.
