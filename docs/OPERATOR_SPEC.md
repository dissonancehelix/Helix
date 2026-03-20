# Operator Specification

Operators are the only valid runtime execution units.

## Contract

Every operator must:

1. Accept typed, normalized payloads.
2. Emit artifacts rather than direct Atlas writes.
3. Declare its accepted inputs and outputs.
4. Route Atlas publication through `core/compiler/atlas_compiler.py`.

## Core operators

- `INGEST_TRACK`
- `ANALYZE_TRACK`
- `DISCOVER`
- `DISCOVER_INVARIANTS`
- `FALSIFY_INVARIANT`
- `TOPOLOGY_MAP`
- `MEASURE_KNOWLEDGE_GAIN`
- `QUERY`
- `COMPILE_ATLAS`
