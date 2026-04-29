# music_pipeline

Role: `canonical`.

Music metadata, entity, taste, retrieval, and materialization pipeline. Start from `core/tools/TOOL_INDEX.yaml`; the normal entrypoint is `python -m domains.music.tools.pipeline.router`.

Substantial original source dumps stay in local archive evidence-type folders or in local bridge targets such as `domains/music/data/library/`. Extracted music records belong under `domains/music/data/`; generated pipeline state belongs under `domains/music/data/pipeline/`. Review output belongs under `domains/music/reports/`.

Hardcoded music-library, foobar2000, temp-folder, `/home/dissonance`, and legacy `Desktop/Helix` paths in helper scripts are local-only bridge defaults or archived research coordinates. Prefer the canonical router and config before adding or changing path constants.
