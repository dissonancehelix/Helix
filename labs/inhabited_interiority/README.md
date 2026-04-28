# Lab: inhabited_interiority

## Purpose
Discriminate between systems/objects/practices that are merely *observed* and those that are *inhabited* — that carry state, accumulate texture, and remain alive across contact.

## Claim under pressure
*State-carrying aliveness* and *soft continuity / texture events* are real, separable patterns — not folk-psychological residue. They produce observable consequences in domain selection (games, music, software) that a shallow taste model would predict incorrectly.

## Fixtures / data
- `inhabited_continuity/` — theory, primitives, claim ledger, YAML test registry. Migrated from `labs/inhabited_interiority/consciousness/inhabited_continuity/` in the Phase 1 refactor.
- `bridge/` — bridge tests linking inhabited-continuity claims to other patterns. Migrated from `labs/inhabited_interiority/consciousness/bridge/`.
- Linked evidence: `data/` paths to be cited per test in the registry.

## Scripts
To be wired to `core/engine/run/falsifier_runner.py` once test schema validates against `core/engine/schemas/`.

## Outputs / reports
Generated test results land in `labs/reports/tests/inhabited_interiority/`.

## False-positive controls
A shallow model conflates *engagement intensity* with *inhabited continuity*. The lab must reject high-engagement-but-non-state-carrying examples (e.g. competitive sport spectatorship without identification with field state) as positive evidence.

## Demotion criteria
If the test registry produces a sustained majority of refutations against the master claim, mark related patterns (`state_carrying_aliveness`, `soft_continuity_texture_events`) as `speculative` in `model/core/map/patterns.yaml` and open an entry in `model/core/map/anomalies.yaml`.

## Status
Scaffolded in Phase 1 refactor. Theory + ledger present; runner integration pending.


