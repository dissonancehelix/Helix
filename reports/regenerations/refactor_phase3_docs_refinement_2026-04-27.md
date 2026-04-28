# Phase 3 — Documentation Refinement Pass
**Date:** 2026-04-27
**Scope:** Documentation only. No implementation; no Phase 4 work begun.

> Post-Phase-3 doc refinement codified the workstation laws across README/CLAUDE/app/domain/report/map docs. No implementation scope changed.

## Files modified

- [README.md](../../README.md) — expanded "Workstation Laws" from 7 short headlines to 10 numbered laws each with a one-line compression and a meaning block. Phase-3-as-foundation framing made explicit; Phase 4 must build on sources/snapshots, not bypass them.
- [CLAUDE.md](../../CLAUDE.md) — added "Agent rules (Phase 3+)": no collapse of observation/interpretation/transformation; reports are not canon; consult `model/map/sources.yaml` before source-specific work; bridges connect without absorbing; transformation requires the six trust artifacts; workspace must obey ontology.
- [system/tools/workstation_bridge/README.md](../../system/tools/workstation_bridge/README.md) — added "Role" section: read-only sensor (not controller); outputs are reports (not canon); deep scans are opt-in; plug-in foundation for future source bridges.
- [system/tools/music_bridge/README.md](../../system/tools/music_bridge/README.md) — added "Observability-first contract" linking to workstation_bridge model; foobar remains independent; first integration is read-only export; outputs are proposals; six trust artifacts gate any writeback.
- [model/domains/software/README.md](../../model/domains/software/README.md) — added "Foundation note (Phase 3)": workstation observability is the foundation for software-domain understanding; snapshots are evidence, not canon; future authoring should decompress from stable reports.
- [reports/README.md](../../reports/README.md) — added "Reports as epistemic airlocks" section: quarantine, never canon by default, must be reviewed before promotion, phase reports are implementation history.
- [model/map/README.md](../../model/map/README.md) — replaced flat file list with a "Layered file roles" table: patterns / gates / examples / probes / anomalies / links / sources, each with its layer name and content. Codified "map files must not become prose dumps."

## Laws codified

The ten governing refinements are now load-bearing in the docs:

1. Observation before interpretation before transformation.
2. Trustworthy as sensor before trustworthy as actor.
3. Bridges preserve sovereignty.
4. Reports are epistemic airlocks.
5. `model/map/sources.yaml` is Helix's attention boundary.
6. Read-only is active perception.
7. Core compresses; domains decompress.
8. Workstation = cognitive body; Helix = nervous system.
9. Workspace must obey the ontology it contains.
10. Claims earn height by surviving pressure.

## Explicit non-actions

- No Phase 4 implementation.
- No `data/` migration.
- No foobar writeback.
- No metadata changes.
- No playlist import.
- No `system/tools/*` reclassification.
- No domain README content authoring (only the software-domain pointer was extended).
- No fragile-pipeline edits.
- No new schemas or scripts.
- No changes to `model/map/patterns.yaml`, `model/map/sources.yaml`, or any other YAML payload.

## Checks run

```
python system/engine/checks/run_checks.py
```

- Result: **exit 0, 0 warnings.**
- All seven `model/map/*.yaml` still parse and match `{version, status, items}` shape.
- Phase 1, Phase 2, and Phase 3 expected paths all present.

## Final rule

This pass strengthened the conceptual contracts after Phase 3. It did not begin Phase 4.

