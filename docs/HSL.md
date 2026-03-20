# HSL

HSL is the only sanctioned execution entry point for Helix.

## Purpose

HSL expresses intent as typed structural commands that can be normalized,
validated, dispatched to operators, and compiled into Atlas knowledge.

## Execution rule

```text
HSL -> operators -> execution/artifacts -> atlas_compiler -> codex/atlas
```

## Identity discipline

All entity references inside HSL resolve to canonical `domain.type:slug` IDs.

## Runtime discipline

- Operators may not write directly to `codex/atlas/`.
- Direct shell execution is not part of the canonical workflow.
- Labs and applications may call into Helix, but core workflows begin with HSL.
