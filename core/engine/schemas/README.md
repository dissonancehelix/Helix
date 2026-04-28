# core/engine/schemas/

JSON schemas and validation shapes used by the trust kernel.

A schema lives here when it is **enforcement machinery** — something `core/engine/checks/` or a runner validates structure against. Schemas that merely describe a domain's data shape may live with the domain.

## Current schemas

- `personal_ontology_test_schema.json` — test-harness schema for the cognitive_mapping lab. Migrated from `core/engine/contract/` in the Phase 1 refactor.
- `source.schema.json` — validates entries in `core/map/sources.yaml` (evidence sources and connector targets).
- `workstation_snapshot.schema.json` — output contract for `core/tools/workstation_bridge/workstation_snapshot.py`.

## Rules

- Schemas have stable IDs in their `$id` field.
- Breaking changes bump a version field; migrations are tracked in `archive/migrations/regenerations/`.
- A schema referenced by a lab or app is a public contract; do not edit silently.
