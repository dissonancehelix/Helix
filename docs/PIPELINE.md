# Pipeline

## Canonical execution flow

1. HSL expresses intent.
2. Normalization resolves aliases, casing, and ID format.
3. Semantics validates entity, property, and relationship meaning.
4. Operators execute domain work and write artifacts to `execution/artifacts/`.
5. The Atlas compiler validates compiled entities and writes to `codex/atlas/`.

## Dataset flow

- All reusable datasets live in `labs/datasets/`.
- Probe execution reads datasets from `labs/datasets/<lab>/`.
- Domain-specific reference corpora live in `codex/library/`.

## Domain flow

- `domains/music/` is the current richest pipeline.
- `domains/language/`, `domains/math/`, and `domains/games/` remain canonical homes for future stabilized domain logic.
