# Workspace Refactor Migration Manifest

Date: 2026-04-27

Purpose: implement the Helix workspace refactor where the whole repository is Helix, `DISSONANCE.md` remains the portable profile, and root folders are separated by role.

## Root Moves

| Old path | New path | Role | Reason | Rollback |
|---|---|---|---|---|
| `map/` | `model/map/` | machine-readable model | Keep compressed pattern graph with modeled understanding. | Move directory back to `map/`. |
| `domains/` | `model/domains/` | domain models | Keep decompressed interpretation beside map. | Move directory back to `domains/`. |
| `apps/` | `system/tools/` | executable tools | Separate runnable machinery from model and data. | Move contents back to `apps/`. |
| `helix/` engine/check/schema parts | `system/engine/` | enforcement engine | Keep checks, schemas, contracts, and validators under machinery. | Move directory back to `helix/`. |
| `apps/music_toolkits/` | `system/vendor/music_toolkits/` | third-party/vendor code | Keep external toolkits out of executable workspace tools. | Move directory back under `system/tools/`. |
| `system/tools/trails/corpus/` | `data/raw/trails/corpus/` | raw/source corpus | Corpora are evidence, not tool code. | Move directory back under `system/tools/trails/`. |
| `system/tools/trails/retrieval/index/` | `data/derived/trails/retrieval/index/` | derived index | Generated DB/index belongs in derived data. | Move directory back under `system/tools/trails/retrieval/`. |
| `system/tools/music_pipeline/data/` | `data/derived/music_pipeline/data/` | derived tool data | Pipeline DBs and artifacts are generated data. | Move directory back under `system/tools/music_pipeline/`. |
| `system/tools/music_pipeline/artifacts/` | `data/derived/music_pipeline/artifacts/` | derived artifacts | Generated artifacts should not live with executable code. | Move directory back under `system/tools/music_pipeline/`. |
| `data/derived/atlas/` | `data/derived/atlas/` | generated atlas/memory | Atlas output is derived memory, not engine code. | Move directory back under `system/engine/memory/`. |
| `intake/` | `quarantine/2026-04-27-workspace-refactor/intake/` | retired intake folder | Loose root files are now unsorted instead of using a permanent intake tray. | Move directory back to `intake/`. |
| `TEST_ATLAS.md` | `quarantine/2026-04-27-workspace-refactor/TEST_ATLAS.md` | loose generated/test atlas | Root loose files are unsorted and must not become a second ontology surface. | Move file back to root only if promoted deliberately. |
| nested vendor `.git/` directories | `quarantine/2026-04-27-workspace-refactor/nested_git/` | local clone metadata | Keep source mirrors from behaving like nested repositories inside Helix. | Move a specific `.git/` directory back only if that mirror is deliberately restored as a nested repo. |

## Documentation Updates

- Rewrite root `README.md` around `model/`, `data/`, `system/`, `labs/`, `reports/`, and `quarantine/`.
- Rewrite `AGENTS.md` to read the new workspace ontology.
- Reduce or quarantine duplicated agent-router content in `CLAUDE.md`.
- Update READMEs, manifests, and specs to the new paths.
- Add `system/tools/README.md` and `system/tools/TOOL_INDEX.yaml` so LLMs reuse existing tools.

## Deletion Policy

No raw evidence is deleted in this migration. Deletion candidates must remain in quarantine or be listed here before removal.

## Pre-existing Dirty State

Before this migration, the worktree already contained modified root docs, modified `model/domains/music/README.md`, modified `system/engine/.gitignore`, modified `system/engine/agent_harness/check_workspace.py`, modified `labs/research/consciousness/theory.md`, and many deleted paths under `system/tools/foobar-spatial-dsp/SDK-2025-03-07/` and `system/tools/foobar-spatial-dsp/foo_dragonfly_reverb/`. These are not rollback targets for this migration unless explicitly touched by the new structure.

