# Refactor Phase 3 — Workstation Foundation + Read-Only Observability Layer
**Date:** 2026-04-27
**Branch:** main
**Scope:** Foundation only. Observation; no interpretation, no transformation.

> Helix observes first, interprets second, transforms only after trust exists.

## Files created

- [core/map/sources.yaml](../../core/map/sources.yaml) — source/connector registry: `source.repo_root`, `source.data_lake`, `source.foobar` (planned), `source.intake`, `source.reports`.
- [core/engine/schemas/source.schema.json](../../core/engine/schemas/source.schema.json) — schema for entries in `core/map/sources.yaml`.
- [core/engine/schemas/workstation_snapshot.schema.json](../../core/engine/schemas/workstation_snapshot.schema.json) — output contract for workstation snapshots.
- [core/tools/workstation_bridge/README.md](../../core/tools/workstation_bridge/README.md) — bridge contract: read-only, configured-roots-only, no symlinks, no out-of-repo writes, plug-in model for future source bridges.
- [core/tools/workstation_bridge/config.example.yaml](../../core/tools/workstation_bridge/config.example.yaml) — example config (repo root recursive depth 3, `data/` shallow only).
- [core/tools/workstation_bridge/workstation_snapshot.py](../../core/tools/workstation_bridge/workstation_snapshot.py) — runnable; stdlib + optional PyYAML; produces JSON + Markdown under `core/reports/workstation/`.
- `core/reports/workstation/` — directory created.
- First snapshot artifacts: [workstation_snapshot_20260427T191408Z.json](../analyses/workstation/workstation_snapshot_20260427T191408Z.json), [workstation_snapshot_20260427T191408Z.md](../analyses/workstation/workstation_snapshot_20260427T191408Z.md).

## Files modified

- [README.md](../../README.md) — added "Workstation Observability" section.
- [core/tools/README.md](../../core/tools/README.md) — added `workstation_bridge` entry under Domain tools section.
- [domains/software/model/README.md](../../domains/software/model/README.md) — appended "Workstation / Helix Runtime Surface" pointer (template stub otherwise unauthored).
- [reports/README.md](../../reports/README.md) — added `analyses/workstation/` description.
- [core/map/README.md](../../core/map/README.md) — added `sources.yaml` to file list.
- [core/map/patterns.yaml](../../core/map/patterns.yaml) — seeded `domain_grounding_rule` and `low_end_continuity` (resolves Phase 2 dangling references).
- [core/engine/schemas/README.md](../../core/engine/schemas/README.md) — added the two new schemas.
- [core/engine/agent_harness/check_workspace.py](../../core/engine/agent_harness/check_workspace.py) — `sources.yaml` now in `MAP_YAMLS`; added warning-only `check_phase3_workstation` for the five expected Phase 3 paths.

## Map IDs added (status: seed)

Patterns:
- `domain_grounding_rule`
- `low_end_continuity`

Sources (in `core/map/sources.yaml`):
- `source.repo_root`, `source.data_lake`, `source.foobar` (planned), `source.intake`, `source.reports`.

## Schemas added

- `core/engine/schemas/source.schema.json`
- `core/engine/schemas/workstation_snapshot.schema.json`

## First snapshot (run details)

```
python core/tools/workstation_bridge/workstation_snapshot.py --root . --out core/reports/workstation
```

- Mode: shallow
- Files scanned: 4 835
- Bytes scanned: 353.7 MiB (repo root only — `data/` was shallow per config; deep scan would surface its 2 GB)
- 8 warnings — all of form `app missing README: core/tools/<name>/` for the legacy pipeline/tool subfolders that were intentionally not reclassified in Phase 1.

## Checks

```
python core/engine/checks/run_checks.py
```

- Result: **exit 0, 0 warnings.**
- All Phase 3 expected paths present.
- All seven `core/map/*.yaml` parse and match the `{version, status, items}` shape (now including `sources.yaml`).
- `domain_grounding_rule` and `low_end_continuity` patterns added → Phase 2 dangling references resolved.

## Phase boundary — explicit non-actions

- **No foobar writeback.** `source.foobar` registered as `planned, read_only_pending`; the workstation bridge does not invoke foobar.
- **No metadata writeback.**
- **No playlist import.**
- **No data/ migration.** The 2 GB lake is untouched; deep scan is opt-in.
- **No full C: drive scan.** Snapshot only walks configured roots.
- **No domain README content authoring.** The software-domain pointer is a *forward reference*, not authored content; the rest of the template remains empty.
- **No core/tools/* reclassification.** The 8 warnings about missing app READMEs are surfaced — not silently fixed by overwriting anything.
- **No fragile pipeline changes.**

## What remains for Phase 4

- **Foobar read-only export format.** Define and implement the snapshot shape; land under `domains/music/data/output/library/foobar/` (or existing pipeline convention).
- **Steam / Last.fm / Spotify source normalization.** Promote from raw exports under `data/` into registered sources in `core/map/sources.yaml`.
- **Domain README content generation** from stable snapshots. Author the empty template stubs created in Phase 1.
- **`core/map/examples.yaml` / `core/map/links.yaml` expansion.** Walk the regenerated `DISSONANCE.md` and seed evidence anchors.
- **Optional playlist proposals.** Generate into `archive/analyses/music/` first; never auto-import.
- **Metadata/tag proposals** — diff + backup + explicit approval. Build the trust gate before any write path is wired.

## Workstation Laws (codified in this phase)

Added to [README.md § Workstation Laws](../../README.md#workstation-laws) and mirrored in [CLAUDE.md](../../CLAUDE.md):

1. Observation before interpretation before transformation.
2. Bridges connect without absorbing.
3. Reports quarantine generated meaning.
4. Source registry defines attention boundary.
5. Read-only is the sensory phase of agency.
6. Main map compresses; domains decompress.
7. The workstation is the cognitive body; Helix is the nervous system.

## Final rule

Foundation first. Observation before interpretation. Interpretation before transformation. Transformation only after trust.

---

## Addendum (post-Phase-3 docs refinement)

A documentation-only refinement pass followed this report and codified the workstation laws across README, CLAUDE, the workstation_bridge / music_bridge / domains/software/model / reports / map READMEs. No implementation scope changed. See [refactor_phase3_docs_refinement_2026-04-27.md](refactor_phase3_docs_refinement_2026-04-27.md).

