# music_pipeline

Role: `canonical`.

Music metadata, entity, taste, retrieval, and materialization pipeline. Start from `system/tools/TOOL_INDEX.yaml`; the normal entrypoint is `python -m system.tools.music_pipeline.router`.

Raw evidence stays in `data/raw/` or `data/music/`. Generated pipeline state belongs under `data/derived/music_pipeline/`. Review output belongs under `reports/music/`.

Hardcoded music-library, foobar2000, temp-folder, `/home/dissonance`, and legacy `Desktop/Helix` paths in helper scripts are local-only bridge defaults or archived research coordinates. Prefer the canonical router and config before adding or changing path constants.
