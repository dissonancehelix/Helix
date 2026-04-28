# system/tools/

Operational tools live here: pipelines, bridges, importers, exporters, diagnostics, and local utilities. Before adding a new script, read `TOOL_INDEX.yaml` and reuse an existing entrypoint if one already covers the job.

## Tool Roles

- `canonical`: the normal entrypoint for a workflow.
- `stage_helper`: a narrow helper called by a canonical pipeline or used for one stage.
- `legacy`: preserved for compatibility or reference; avoid for new work.
- `one_off_archive`: historical or seed script; do not extend unless deliberately resurrecting it.

## Rules

1. Tools produce evidence, proposals, reports, or derived artifacts. They do not redefine canon.
2. Raw evidence belongs under `data/raw/`; normalized artifacts under `data/normalized/`; generated/indexed output under `data/derived/`.
3. Reports go under `reports/`, and promotion from a report into `model/` or `DISSONANCE.md` is a separate action.
4. Any writeback to an external app requires identity, diff, backup, rollback, evidence, and explicit operator approval.
5. If a workflow is a pipeline of helpers, document the pipeline here instead of adding another top-level script.

## Local Bridge Paths

Some tools intentionally point at operator-local targets such as the music
library, foobar2000 profile database, WSL mirrors, or the legacy Trails working
tree. Treat hardcoded `C:\Users\dissonance`, `/home/dissonance`, `Desktop/Helix`,
and `Desktop/Trails` paths as local-only bridge defaults unless the tool README
or manifest marks them as portable configuration.

## First Tools To Check

- Workspace audit: `workstation_bridge`
- Music library bridge: `music_bridge`
- Music metadata/materialization pipeline: `music_pipeline`
- foobar2000 audit/diff/report actions: `foobar`
- Trails corpus and wiki pipeline: `trails`
- Language/template pipeline: `language_pipeline`
- Games taste/platform pipeline: `games_pipeline`
