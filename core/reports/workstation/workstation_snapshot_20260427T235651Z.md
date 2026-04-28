# Workstation Snapshot — 2026-04-27T23:56:51+00:00

- **Repo root:** `C:\Users\dissonance\Desktop\dissonance`
- **Mode:** shallow
- **Files scanned:** 4499
- **Bytes scanned:** 243.2 MiB

## Sources

| ID | Path | Exists | Files | Bytes | Skipped |
|---|---|---|---|---|---|
| `source.repo_root` | `.` | True | 4498 | 243.2 MiB |  |
| `source.data_lake` | `data` | True | 1 | 461.0 B | shallow scan; pass --deep for full recursion |

### Source registry (core/map/sources.yaml)

- `source.repo_root` — Repository Root [active, read_only] @ `.`
- `source.data_lake` — Data Evidence Lake [active, read_only] @ `data/`
- `source.foobar` — foobar2000 Local Music Atlas [planned, read_only_pending] @ `domains/music/tools/bridge/`
- `source.root_unsorted` — Root Unsorted Drops [deprecated, read_only] @ `.`
- `source.reports` — Reports [active, generated_outputs] @ `reports/`

## Top-level inventory

- 📄 `.gitattributes`
- 📄 `.gitignore`
- 📄 `AGENTS.md`
- 📄 `CLAUDE.md`
- 📁 `data` (README)
- 📄 `DISSONANCE.md`
- 📁 `labs` (README)
- 📁 `model` (README)
- 📁 `quarantine` (README)
- 📄 `README.md`
- 📁 `reports` (README)
- 📁 `system` (README)

## domains/ README coverage

- Covered (11): aesthetics, food, games, internet, language, music, self, software, sports, trails, wiki
- Missing (0): (none)

## tools/ README coverage

- Covered (5): foobar, spatial_dsp, music_bridge, trails, workstation_bridge
- Missing (7): cognition_pipeline, games_pipeline, language_pipeline, music_pipeline, spanish, spc2mid, wiki_tools

## labs/ README coverage

- Covered (2): cognitive_mapping, inhabited_interiority
- Missing (1): research

## Warnings

- tool missing README: domains/self/tools/cognition_pipeline/
- tool missing README: domains/games/tools/games_pipeline/
- tool missing README: domains/language/tools/language_pipeline/
- tool missing README: domains/music/tools/pipeline/
- tool missing README: domains/language/tools/spanish/
- tool missing README: domains/music/tools/spc2mid/
- tool missing README: domains/wiki/tools/wiki_tools/
- lab missing README: labs/research/

## Next recommended actions

- Resolve `missing` warnings above (add READMEs / map files).
- Re-run with `--deep` if a complete byte/file count is required.
