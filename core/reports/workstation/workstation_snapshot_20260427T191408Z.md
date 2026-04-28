# Workstation Snapshot — 2026-04-27T19:14:08+00:00

- **Repo root:** `C:\Users\dissonance\Desktop\dissonance`
- **Mode:** shallow
- **Files scanned:** 4835
- **Bytes scanned:** 353.7 MiB

## Sources

| ID | Path | Exists | Files | Bytes | Skipped |
|---|---|---|---|---|---|
| `source.repo_root` | `.` | True | 4835 | 353.7 MiB |  |
| `source.data_lake` | `data` | True | 0 | 0.0 B | shallow scan; pass --deep for full recursion |

### Source registry (core/map/sources.yaml)

- `source.repo_root` — Repository Root [active, read_only] @ `.`
- `source.data_lake` — Data Evidence Lake [active, read_only] @ `data/`
- `source.foobar` — foobar2000 Local Music Atlas [planned, read_only_pending] @ `domains/music/tools/music_bridge/`
- `source.intake` — Intake [active, read_only] @ `intake/`
- `source.reports` — Reports [active, generated_outputs] @ `reports/`

## Top-level inventory

- 📄 `.gitattributes`
- 📄 `.gitignore`
- 📁 `apps` (README)
- 📄 `CLAUDE.md`
- 📁 `data` (no README)
- 📄 `DISSONANCE.md`
- 📁 `domains` (README)
- 📁 `helix` (README)
- 📁 `intake` (README)
- 📁 `labs` (README)
- 📁 `map` (README)
- 📄 `README.md`
- 📁 `reports` (README)

## domains/ README coverage

- Covered (11): aesthetics, food, games, internet, language, music, self, software, sports, trails, wiki
- Missing (0): (none)

## core/tools/ README coverage

- Covered (5): foobar, foobar-spatial-dsp, music_bridge, trails, workstation_bridge
- Missing (8): cognition_pipeline, games_pipeline, language_pipeline, music_pipeline, music_toolkits, spanish, spc2mid, wiki_tools

## labs/ README coverage

- Covered (2): cognitive_mapping, inhabited_interiority
- Missing (0): (none)

## Warnings

- app missing README: domains/self/tools/cognition_pipeline/
- app missing README: domains/games/tools/games_pipeline/
- app missing README: domains/language/tools/language_pipeline/
- app missing README: domains/music/tools/music_pipeline/
- app missing README: domains/music/vendor/music_toolkits/
- app missing README: domains/language/tools/spanish/
- app missing README: domains/music/tools/spc2mid/
- app missing README: domains/wiki/tools/wiki_tools/

## Next recommended actions

- Resolve `missing` warnings above (add READMEs / map files).
- Re-run with `--deep` if a complete byte/file count is required.
