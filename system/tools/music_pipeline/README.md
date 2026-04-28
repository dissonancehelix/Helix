# music_pipeline

Role: `canonical`.

Music metadata, entity, taste, retrieval, and materialization pipeline. Start from `system/tools/TOOL_INDEX.yaml`; the normal entrypoint is `python -m system.tools.music_pipeline.router`.

Raw evidence stays in `data/raw/` or `data/music/`. Generated pipeline state belongs under `data/derived/music_pipeline/`. Review output belongs under `reports/music/`.

