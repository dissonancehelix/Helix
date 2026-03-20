# Core Structure

## Core is execution-only

`core/` contains:

- HSL command processing
- normalization
- semantics
- operators
- adapters
- engines
- compiler
- governance logic

## Core may not become a data store

- Library data lives in `codex/library/`
- Atlas data lives in `codex/atlas/`
- Runtime artifacts live in `execution/`

## Canonical rule

Only `core/compiler/atlas_compiler.py` may write to `codex/atlas/`.
