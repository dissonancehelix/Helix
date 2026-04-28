# music_pipeline

Role: `canonical`.

Music metadata, entity, taste, retrieval, and materialization pipeline. Start from `core/tools/TOOL_INDEX.yaml`; the normal entrypoint is `python -m domains.music.tools.music_pipeline.router`.

Original source dumps stay in local archives under `archive/raw/` or in local bridge targets such as `domains/music/data/derived/music/`. Extracted/normalized music records belong under `domains/music/data/normalized/`; generated pipeline state belongs under `domains/music/data/derived/music_pipeline/`. Review output belongs under `domains/music/reports/`.

Hardcoded music-library, foobar2000, temp-folder, `/home/dissonance`, and legacy `Desktop/Helix` paths in helper scripts are local-only bridge defaults or archived research coordinates. Prefer the canonical router and config before adding or changing path constants.
