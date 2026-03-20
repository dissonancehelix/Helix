# Helix Architecture

## Layer model

```text
codex/library  ->  core/hsl + normalization + semantics + operators  ->  core/compiler  ->  codex/atlas
                                 |                                        |
                                 v                                        v
                              domains                                 execution/
                                 |
                                 v
                               labs/
```

## Canonical boundaries

- **Core**: execution logic only.
- **Library**: priors, corpora, source references, metadata, and unvalidated entities.
- **Atlas**: validated semantic output compiled from operator artifacts.
- **Domains**: stable pipelines for music, language, math, and games.
- **Labs**: probes, experiments, and datasets used to challenge or extend domain logic.
- **Applications**: user-facing or diagnostic tools built on stabilized outputs.
- **Governance**: validation, confidence scoring, promotion, and admissibility logic.
- **Execution**: reproducibility artifacts, logs, integrity records, and transient outputs.

## Canonical roots

- Atlas: `codex/atlas/`
- Library: `codex/library/`
- Domain pipelines: `domains/`
- Datasets: `labs/datasets/`
- Artifacts: `execution/artifacts/`

## Write authority

Only `core/compiler/atlas_compiler.py` may commit to `codex/atlas/`. Operators and scripts may emit artifacts under `execution/artifacts/` only.
