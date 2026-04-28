# Browsable Bounded Contexts Audit

Date: 2026-04-28

## Scope

Audited Helix folder structure against the README workspace design rules added in this migration. This audit was written before file moves.

Root contract remains:

```text
/
├── README.md
├── DISSONANCE.md
├── AGENTS.md
├── core/
├── domains/
├── labs/
├── archive/
└── quarantine/
```

## Classification Rules

| Classification | Meaning |
|---|---|
| keep | Path already names a bounded context or lifecycle role clearly. |
| rename | Path role is valid but the name repeats identity or hides behavior. |
| move | Path belongs elsewhere under the new bounded context. |
| merge | Path should collapse into an existing sibling because depth repeats identity. |
| delete if generated/cache | Path is generated cache and can be removed if ignored. |
| quarantine pending review | Path is uncertain or legacy-like but not safe to delete. |

## Global Folder Audit

| Current path | Classification | Problem | Proposed path | Reason | Risk | Raw evidence involved |
|---|---|---|---|---|---|---|
| `core/` | keep | Shared infrastructure is global. | unchanged | Root contract. | Low | No |
| `domains/` | keep | Active domain capsules. | unchanged | Root contract. | Low | No |
| `labs/` | keep | Cross-domain pressure tests. | unchanged | Root contract. | Low | No |
| `archive/` | keep | Provenance, imports, analyses, and migration history. | unchanged | Root contract. | Low | Yes |
| `quarantine/` | keep | Staging and rollback area. | unchanged | Root contract. | Low | Possible |
| `archive/raw/**` | keep | Raw provenance belongs here and stays ignored. | unchanged | Do not delete raw evidence. | Low | Yes |
| `archive/analyses/**` | keep | Archived review material, not active canon. | unchanged | Archive role is clear. | Low | No |
| `archive/migrations/**` | keep | Migration history. | unchanged | Required change records. | Low | No |
| `archive/legacy/**` | delete | Parallel historical tree duplicates migration records and obscures active shape. | deleted | Retired structures belong in migration manifests, not browsable active rooms. | Medium | No raw evidence |
| `archive/quarantine/**` | delete | Duplicates root `quarantine/`. | deleted/not used | One quarantine room is enough. | Low | No |
| `**/__pycache__/` | delete if generated/cache | Generated Python cache folders should not be committed or browsed. | delete | Ignored generated cache. | Low | No |

## Domain Capsule Audit

| Current path | Classification | Problem | Proposed path | Reason | Risk | Raw evidence involved |
|---|---|---|---|---|---|---|
| `domains/<domain>/README.md` | keep | Human-facing domain profile. | unchanged | Domain orientation. | Low | No |
| `domains/<domain>/manifest.yaml` | keep | Domain machine summary. | unchanged | Domain metadata. | Low | No |
| `domains/<domain>/model/` | keep | Durable interpretation. | unchanged | README design rules. | Low | No |
| `domains/<domain>/data/` | keep | Cleaned domain records live directly here. | unchanged | Human-browsable data root. | Low | Possible |
| `domains/<domain>/data/output/` | keep | Generated or computed domain outputs. | unchanged | Separates products from records without three lifecycle rooms. | Low | No |
| `domains/<domain>/data/normalized/` | merge | Name explains lifecycle, not content. | `domains/<domain>/data/` | Records should be visible at data root. | Low | Possible |
| `domains/<domain>/data/derived/` | rename | `derived` is abstract tool language. | `domains/<domain>/data/output/` | Output names the intended use. | Low | No |
| `domains/<domain>/data/staging/` | delete | Staging expresses uncertainty and became empty/default furniture. | deleted | Quarantine handles uncertainty globally. | Low | No |
| `domains/<domain>/tools/` | keep | Runnable workflows and support material. | unchanged | Domain-owned tools. | Low | No |
| `domains/<domain>/reports/` | keep | Review artifacts. | unchanged | Reports are not truth. | Low | No |
| `domains/<domain>/labs/` | keep if meaningful | Optional local experiments. | unchanged where populated | Allowed only for local experiments. | Medium | No |
| `domains/<domain>/domains/<domain>/...` | merge | Repeats domain identity inside itself. | `domains/<domain>/...` | No folder may repeat an ancestor name. | Medium | No |
| `domains/<domain>/core/...` | move | Shared name inside domain implies false globality. | `model/` or `data/output/` | No `core/` inside domain. | Medium | No |
| `domains/<domain>/vendor/...` | move | Domain-root vendor hides role and violates rule. | `tools/toolkits/` | Toolkits/source mirrors belong under tools. | Low | No |
| `domains/<domain>/data/output/<domain>/` | rename | Repeats domain name instead of lifecycle role. | `data/output/<role>/` | Derived folder should name behavior. | Medium | No |

## Flagged Domain Paths

| Current path | Classification | Problem | Proposed path | Reason | Risk | Raw evidence involved |
|---|---|---|---|---|---|---|
| `domains/music/vendor/` | move | Domain-root vendor. | `domains/music/tools/toolkits/` | Toolkits belong under tools. | Low | No |
| `domains/music/data/output/music/` | rename | Repeats `music`. | `domains/music/data/output/library/` | Names role: library-derived outputs. | Medium | No |
| `domains/music/data/output/music_pipeline/` | rename | Repeats tool/domain identity. | `domains/music/data/output/pipeline/` | Names lifecycle output role. | Medium | No |
| `domains/music/data/output/atlas_embeddings/` | rename | Atlas-specific derived embeddings should be role bucket. | `domains/music/data/output/embeddings/` | Names behavior. | Low | No |
| `domains/music/data/output/atlas_staging/` | delete | Generated staging output did not deserve a permanent room. | deleted | Staging was retired. | Low | No |
| `domains/music/core/atlas/` | move if present | Domain-local `core/`. | `domains/music/data/output/atlas/` | Domain atlas output is derived data. | Medium | No |
| `domains/music/tools/music_bridge/` | rename | Tool repeats domain name. | `domains/music/tools/bridge/` | Tool role is bridge. | Medium | No |
| `domains/music/tools/music_pipeline/` | rename | Tool repeats domain name. | `domains/music/tools/pipeline/` | Tool role is pipeline. | Medium | No |
| `domains/music/tools/foobar-spatial-dsp/` | rename | Hyphenated legacy name, unclear relation. | `domains/music/tools/spatial_dsp/` | Names tool role. | Medium | No |
| `domains/games/data/output/games/` | rename | Repeats `games`. | `domains/games/data/output/pipeline/` | Derived output role. | Medium | No |
| `domains/language/data/output/language/` | rename | Repeats `language`. | `domains/language/data/output/corpora/` | Derived language corpora/datasets. | Medium | No |
| `domains/self/data/output/self/` | rename | Repeats `self`. | `domains/self/data/output/profile/` | Derived self/profile datasets. | Medium | No |
| `domains/trails/data/output/trails/` | rename | Repeats `trails`. | `domains/trails/data/output/pipeline/` | Trails pipeline outputs. | Medium | No |
| `labs/invariants/invariants/` | merge | Repeats lab identity. | `labs/invariants/` | Depth repeats names. | Medium | No |
| `labs/inhabited_interiority/consciousness/cognition/cognition/` | merge | Repeats `cognition`. | `labs/inhabited_interiority/consciousness/cognition/` | Depth repeats names. | Medium | No |
| `labs/reports/tests/` | keep | Lab report output is acceptable. | unchanged | Not `reports/reports`. | Low | No |
| `quarantine/**` | quarantine pending review | Staged legacy/uncertain material. | unchanged | Quarantine role is explicit. | Medium | Possible |

## Missing Or Weak Folder Purpose

| Current path | Classification | Problem | Proposed path | Reason | Risk | Raw evidence involved |
|---|---|---|---|---|---|---|
| Empty `data/output/`, `tools/`, `reports/` in young domains | keep with manifest purpose | Required capsule rooms may be empty while domain is young. | unchanged | Domain roots normally contain these rooms. | Low | No |
| Empty optional `labs/` in domains | quarantine or remove if no local experiments | Optional room without purpose. | remove or add local README when used | Domain-local labs only for true experiments. | Low | No |

## Generated / Cache Deletion Candidates

All `__pycache__/` directories under `core/`, `domains/`, and `labs/` are generated cache folders. They are ignored by `.gitignore` and may be deleted after path moves.

## Move Map Preview

See `MIGRATION_MANIFEST.md` after application for the final before/after map and validation result.
