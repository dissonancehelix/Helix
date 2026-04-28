# Lab: cognitive_mapping

## Purpose
Pressure-test the cognitive map itself. The operator ontology in `DISSONANCE.md` and `model/core/map/patterns.yaml` is the object under test — not a foundation taken for granted.

## Claim under pressure
The pattern set in `model/core/map/patterns.yaml` is *coherent* (no silent duplicates), *covering* (every major behavior the operator exhibits maps to at least one pattern), and *non-overfit* (patterns survive rephrasing and adversarial paraphrase).

## Fixtures / data
- `personal_ontology/` — test harness for the operator ontology. Migrated from `labs/cognitive_mapping/personal_ontology/` in the Phase 1 refactor.
- Validated against `core/engine/schemas/personal_ontology_test_schema.json`.

## Scripts
Test runner integration pending. Will read fixtures, validate against schema, and emit per-pattern verdicts.

## Outputs / reports
Generated test results land in `labs/reports/tests/cognitive_mapping/`.

## False-positive controls
The lab must reject explanations that work *because* they restate the pattern in different words. Adversarial paraphrase tests are required.

## Demotion criteria
- A pattern that fails coverage in repeated runs → mark `speculative`.
- Two patterns that always co-occur in test outcomes → flag as candidate-merge anomaly.
- A pattern that survives only by absorbing every counterexample → mark `overfit` and demote.

## Status
Scaffolded in Phase 1 refactor. Schema migrated to `core/engine/schemas/`. Runner integration pending.


