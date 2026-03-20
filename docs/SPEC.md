# Helix Specification

This document is the authoritative reconstruction source for Helix.

## Identity

Helix is a closed-system invariant discovery engine.

## Repository contract

```text
README.md
/docs
/core
/codex/library
/codex/atlas
/domains
/labs
/applications
/execution
/runtime
/governance
```

## Closed-system law

- No untyped input.
- No undefined meaning.
- No unregistered execution.
- No direct Atlas writes.
- No mixed library/atlas truth.

## Canonical paths

- Library root: `codex/library/`
- Atlas root: `codex/atlas/`
- Artifacts root: `execution/artifacts/`
- Dataset root: `labs/datasets/`
- Domain root: `domains/`
- Governance code: `core/governance/`

## Canonical execution path

```text
HSL -> normalization -> semantics -> operators -> atlas_compiler -> codex/atlas
```

## Canonical identity rule

Every persisted entity ID must match:

```text
^[a-z_]+\.[a-z_]+:[a-z0-9_]+$
```

## Directory roles

- `core/`: execution and enforcement only.
- `codex/library/`: raw priors and references only.
- `codex/atlas/`: compiled truth only.
- `domains/`: stable pipelines only.
- `labs/`: experiments and datasets only.
- `applications/`: built consumer tools only.
- `governance/`: audits and templates only.
- `execution/`: runtime state and artifacts only.
