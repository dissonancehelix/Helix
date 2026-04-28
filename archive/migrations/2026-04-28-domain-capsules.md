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
| `domains/music/tools/music_bridge/` | `domains/music/tools/music_bridge/` | Music-owned workflow. |
| `domains/music/tools/music_pipeline/` | `domains/music/tools/music_pipeline/` | Music-owned workflow. |
| `domains/music/tools/foobar/` | `domains/music/tools/foobar/` | Music-owned workflow. |
| `domains/music/tools/spc2mid/` | `domains/music/tools/spc2mid/` | Music-owned workflow. |
| `domains/music/tools/foobar-spatial-dsp/` | `domains/music/tools/foobar-spatial-dsp/` | Music-owned build workspace. |
| `domains/music/vendor/music_toolkits/` | `domains/music/vendor/music_toolkits/` | Music-owned vendor mirrors; ignored except pointer docs. |
| `domains/games/tools/games_pipeline/` | `domains/games/tools/games_pipeline/` | Games-owned workflow. |
| `domains/trails/tools/trails/` | `domains/trails/tools/trails/` | Trails-owned workflow. |
| `domains/wiki/tools/wiki_tools/` | `domains/wiki/tools/wiki_tools/` | Wiki-owned workflow. |
| `domains/language/tools/language_pipeline/` | `domains/language/tools/language_pipeline/` | Language-owned workflow. |
| `domains/language/tools/spanish/` | `domains/language/tools/spanish/` | Spanish nested under language. |
| `domains/self/tools/cognition_pipeline/` | `domains/self/tools/cognition_pipeline/` | Self-domain cognition workflow. |
| `archive/raw/` | `archive/raw/` | Raw provenance. |
| `archive/legacy/` | `archive/legacy/` | Legacy/provenance notes. |
| `domains/music/domains/music/data/normalized/` | `domains/music/domains/music/domains/music/data/normalized/` | Existing normalized records are music records. |
| `domains/music/data/derived/music/` | `archive/raw/music/` plus `domains/music/data/derived/` | Heavy local exports stay archived/ignored; compact derived artifacts move into capsule. |
| `domains/games/data/derived/games/` | `domains/games/data/derived/` | Game cache and derived records. |
| `domains/language/data/derived/language/` | `domains/language/data/derived/` | Language datasets and caches. |
| `domains/self/data/derived/self/` | `domains/self/data/derived/` | Self-domain datasets. |
| `core/atlas/` | `core/atlas/` | Shared compiled atlas artifacts. |
| `domains/music/core/atlas/` | `domains/music/core/atlas/` | Music atlas artifacts. |
| `domains/language/core/atlas/` | `domains/language/core/atlas/` | Language atlas artifacts. |
| `labs/invariants/core/atlas/` | `labs/invariants/core/atlas/` | Cross-domain invariant artifacts. |
| `domains/music/data/derived/music_pipeline/` | `domains/music/domains/music/data/derived/music_pipeline/` | Music pipeline output. |
| `domains/trails/data/derived/trails/` | `domains/trails/data/derived/` | Trails derived output. |
| `domains/music/core/atlas_staging/` | `domains/music/domains/music/core/atlas_staging/` | Current staging content is music-owned. |
| `domains/music/labs/research/` | `domains/music/labs/` | Music lab work. |
| `domains/games/labs/research/` | `domains/games/labs/` | Games lab work. |
| `domains/language/labs/research/` | `domains/language/labs/` | Language lab work. |
| `labs/invariants/` | `labs/invariants/` | Cross-domain theory lab. |
| `labs/inhabited_interiority/consciousness/` | `labs/inhabited_interiority/consciousness/` | Interiority/consciousness lab depth. |
| `core/reports/workstation/` | `core/reports/workstation/` | Workspace sensor reports. |
| `archive/imports/` | `archive/imports/` | Import review history. |
| `archive/migrations/regenerations/` | `archive/migrations/regenerations/` | Migration/regeneration history. |
| `labs/labs/reports/tests/` | `labs/labs/labs/reports/tests/` | Cross-domain lab reports. |

## Safety Rules

- Do not delete raw evidence.
- Do not promote generated output into canon.
- Reports remain review artifacts, not truth.
- Vendor mirrors and bulky raw/generated data are ignored.
- Compatibility notes may point to new homes, but old active roots must not
  remain active ontology.
