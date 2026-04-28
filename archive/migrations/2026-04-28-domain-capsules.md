# 2026-04-28 Domain Capsule Migration

Status: implementation manifest

This migration compresses Helix around the `DISSONANCE.md` grammar:
minimal root, shared core infrastructure, nested domain-owned work, labs as
pressure surfaces, archive as provenance, and quarantine as staging.

## Root Contract

Old active roots:

- `model/`
- `data/`
- `system/`
- `reports/`

New active roots:

- `core/`
- `domains/`
- `labs/`
- `archive/`
- `quarantine/`

## Path Map

| Old path | New path | Notes |
| --- | --- | --- |
| `core/map/` | `core/map/` | Compressed machine-readable map. |
| `core/engine/` | `core/engine/` | Shared validation, schemas, contracts, and workspace checks. |
| `core/tools/TOOL_INDEX.yaml` | `core/tools/TOOL_INDEX.yaml` | Global tool registry. |
| `core/tools/workstation_bridge/` | `core/tools/workstation_bridge/` | Cross-domain workspace sensor. |
| `domains/<domain>/README.md` | `domains/<domain>/README.md` | Domain capsule front door. |
| `domains/<domain>/manifest.yaml` | `domains/<domain>/manifest.yaml` | Domain capsule manifest. |
| `domains/<domain>/...` | `domains/<domain>/model/...` | Domain-owned model depth. |
| `domains/music/tools/bridge/` | `domains/music/tools/bridge/` | Music-owned workflow. |
| `domains/music/tools/pipeline/` | `domains/music/tools/pipeline/` | Music-owned workflow. |
| `domains/music/tools/foobar/` | `domains/music/tools/foobar/` | Music-owned workflow. |
| `domains/music/tools/spc2mid/` | `domains/music/tools/spc2mid/` | Music-owned workflow. |
| `domains/music/tools/spatial_dsp/` | `domains/music/tools/spatial_dsp/` | Music-owned build workspace. |
| `domains/music/tools/toolkits/` | `domains/music/tools/toolkits/` | Music-owned vendor mirrors; ignored except pointer docs. |
| `domains/games/tools/games_pipeline/` | `domains/games/tools/games_pipeline/` | Games-owned workflow. |
| `domains/trails/tools/trails/` | `domains/trails/tools/trails/` | Trails-owned workflow. |
| `domains/wiki/tools/wiki_tools/` | `domains/wiki/tools/wiki_tools/` | Wiki-owned workflow. |
| `domains/language/tools/language_pipeline/` | `domains/language/tools/language_pipeline/` | Language-owned workflow. |
| `domains/language/tools/spanish/` | `domains/language/tools/spanish/` | Spanish nested under language. |
| `domains/self/tools/cognition_pipeline/` | `domains/self/tools/cognition_pipeline/` | Self-domain cognition workflow. |
| `archive/raw/` | `archive/raw/` | Raw provenance. |
| `archive/migrations/` | `archive/migrations/` | Migration/provenance notes. |
| `domains/music/data/` | `domains/music/data/` | Cleaned music records live at the data root. |
| `domains/music/data/output/library/` | `archive/raw/music/` plus `domains/music/data/output/` | Heavy local exports stay archived/ignored; compact derived artifacts move into capsule. |
| `domains/games/data/output/pipeline/` | `domains/games/data/output/` | Game cache and derived records. |
| `domains/language/data/output/corpora/` | `domains/language/data/output/` | Language datasets and caches. |
| `domains/self/data/output/profile/` | `domains/self/data/output/` | Self-domain datasets. |
| `core/atlas/` | `core/atlas/` | Shared compiled atlas artifacts. |
| `domains/music/data/output/atlas/` | `domains/music/data/output/atlas/` | Music atlas artifacts. |
| `domains/language/core/atlas/` | `domains/language/core/atlas/` | Language atlas artifacts. |
| `labs/invariants/core/atlas/` | `labs/invariants/core/atlas/` | Cross-domain invariant artifacts. |
| `domains/music/data/output/pipeline/` | `domains/music/data/output/pipeline/` | Music pipeline output. |
| `domains/trails/data/output/pipeline/` | `domains/trails/data/output/` | Trails derived output. |
| `domains/music/data/staging/atlas/` | deleted | Generated staging content was retired during later compression. |
| `domains/music/labs/` | `domains/music/labs/` | Music lab work. |
| `domains/games/labs/` | `domains/games/labs/` | Games lab work. |
| `domains/language/labs/` | `domains/language/labs/` | Language lab work. |
| `labs/invariants/` | `labs/invariants/` | Cross-domain theory lab. |
| `labs/inhabited_interiority/consciousness/` | `labs/inhabited_interiority/consciousness/` | Interiority/consciousness lab depth. |
| `core/reports/workstation/` | `core/reports/workstation/` | Workspace sensor reports. |
| `archive/imports/` | `archive/imports/` | Import review history. |
| `archive/migrations/regenerations/` | `archive/migrations/regenerations/` | Migration/regeneration history. |
| `labs/reports/tests/` | `labs/reports/tests/` | Cross-domain lab reports. |

## Safety Rules

- Do not delete raw evidence.
- Do not promote generated output into canon.
- Reports remain review artifacts, not truth.
- Vendor mirrors and bulky raw/generated data are ignored.
- Compatibility notes may point to new homes, but old active roots must not
  remain active ontology.
