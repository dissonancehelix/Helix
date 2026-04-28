# Browsable Bounded Contexts Migration

Date: 2026-04-28

## Purpose

Compress Helix into browsable bounded contexts while keeping `README.md` as the
single workspace manual and design-law source. The migration follows the rule:
fewer folders, better rooms.

## README Design Rules Added

- Human file exploration must work without relying on LLM memory or registries.
- Paths should explain the thing before a README has to defend it.
- Folders group by role/category, not repeated identity.
- Depth must reveal behavior; depth that repeats names is compressed.
- Domain roots keep durable rooms: `README.md`, `manifest.yaml`, `model/`,
  `data/`, `tools/`, and `reports/`.
- Domain-local `labs/` is optional and only for true local experiments.
- Cleaned domain records live directly in `data/`; generated products live in
  `data/output/`. The older `normalized/`, `derived/`, and `staging/` rooms
  were compressed away after review.
- SDKs, toolkits, helper libraries, and source mirrors live under
  `tools/toolkits/` or `tools/<tool_name>/toolkits/`, not `vendor/`.
- Folder existence now has the seven-question test in `README.md`.

## Before / After Tree Summary

Before, active work could hide under repeated identity folders such as
`domains/<domain>/data/output/<domain>/`, domain-local `research/` wrappers,
domain-root vendor mirrors, and repeated lab names.

After, each active capsule exposes durable interpretation, cleaned data,
generated outputs, runnable workflows, optional local experiments, and reports
without repeating the domain name:

```text
domains/<domain>/
├── README.md
├── manifest.yaml
├── model/
├── data/
│   └── output/
├── tools/
└── reports/
```

`domains/games/labs/`, `domains/language/labs/`, and `domains/music/labs/`
remain because they contain real local experiments. Empty optional domain labs
were removed.

## Move Map

| Old path | New path |
|---|---|
| `domains/music/vendor/` | `domains/music/tools/toolkits/` |
| `domains/music/data/output/music/` | `domains/music/data/output/library/` |
| `domains/music/data/output/music_pipeline/` | `domains/music/data/output/pipeline/` |
| `domains/music/data/output/atlas_embeddings/` | `domains/music/data/output/embeddings/` |
| `domains/music/data/output/atlas_staging/` | deleted as generated staging output |
| `domains/music/core/atlas/` | `domains/music/data/output/atlas/` |
| `domains/music/tools/music_bridge/` | `domains/music/tools/bridge/` |
| `domains/music/tools/music_pipeline/` | `domains/music/tools/pipeline/` |
| `domains/music/tools/foobar-spatial-dsp/` | `domains/music/tools/spatial_dsp/` |
| `domains/music/tools/spatial_dsp/Foobar SDK/` | `domains/music/tools/spatial_dsp/toolkits/Foobar SDK/` |
| `domains/music/tools/spatial_dsp/WTL/` | `domains/music/tools/spatial_dsp/toolkits/WTL/` |
| `domains/music/tools/spatial_dsp/prism-dsp/` | `domains/music/tools/spatial_dsp/toolkits/prism-dsp/` |
| `domains/music/tools/spatial_dsp/vgmspc/` | `domains/music/tools/spatial_dsp/toolkits/vgmspc/` |
| `domains/games/data/output/games/` | `domains/games/data/output/pipeline/` |
| `domains/language/data/output/language/` | `domains/language/data/output/corpora/` |
| `domains/self/data/output/self/` | `domains/self/data/output/profile/` |
| `domains/trails/data/output/trails/` | `domains/trails/data/output/pipeline/` |
| `domains/games/labs/research/` | `domains/games/labs/` |
| `domains/language/labs/research/` | `domains/language/labs/` |
| `domains/music/labs/research/` | `domains/music/labs/` |
| `labs/invariants/invariants/` | `labs/invariants/` |
| `labs/inhabited_interiority/consciousness/cognition/cognition/` | `labs/inhabited_interiority/consciousness/cognition/` |
| `domains/<domain>/data/normalized/*` | `domains/<domain>/data/*` |
| `domains/<domain>/data/derived/*` | `domains/<domain>/data/output/*` |
| `domains/<domain>/data/staging/` | deleted |
| `archive/legacy/` | deleted; retained history lives in `archive/migrations/` |
| `archive/quarantine/` | deleted/not used; root `quarantine/` is canonical |

During cleanup, the leftover generated slice
`domains/music/data/output/library/library/music/album/` was merged into
`domains/music/data/output/library/catalog/music/album/` and the repeated
`library/library/` room was removed.

## Deleted Generated / Cache Files

- Removed 136 `__pycache__/` directories after confirming Python cache folders
  are ignored.
- Removed generated staging rooms and retired `archive/legacy/` after the
  operator chose the compressed layout.
- No raw evidence was deleted.

## Quarantined Uncertain Files

No new quarantine move was required in this pass. Existing quarantine material
remains staged under `quarantine/`.

## Updated References

Updated path references across:

- `README.md`
- `AGENTS.md`
- `domains/README.md`
- `core/tools/TOOL_INDEX.yaml`
- domain manifests and READMEs
- scripts, imports, path constants, and checks
- migration notes and non-raw generated reports that named old paths

Compatibility aliases were not left in place. The old paths are non-canonical.

## Validation Result

`python core/engine/agent_harness/check_workspace.py`

Result:

```text
Helix boundary check passed (0 warning(s)).
```

The checker now fails on:

- `domains/*/domains/`
- `domains/*/core/`
- `domains/*/vendor/`
- `labs/labs/`
- `reports/reports/`
- committed `__pycache__/`
- `domains/<domain>/data/output/<domain>/`
- `domains/<domain>/data/normalized/`, `data/derived/`, or `data/staging/`
- `archive/legacy/` or `archive/quarantine/`
- empty optional domain labs without a purpose note
- tracked raw archives, heavy data/binaries, vendor mirrors, or toolkit mirrors

## Rollback Notes

Use this manifest and `AUDIT.md` as the path map. Rollback is mostly path
renaming, but raw evidence should remain under `archive/raw/` and generated
caches should not be restored. Toolkit mirrors should stay ignored even if a
tool folder is renamed again.
