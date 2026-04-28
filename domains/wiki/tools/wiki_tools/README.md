# wiki_tools

Role: `stage_helper`.

Wiki-oriented helper runner for import/export and page operations. Start from `core/tools/TOOL_INDEX.yaml`; the entrypoint is `python -m domains.wiki.tools.wiki_tools.runner`.

External wiki writeback requires the full trust gate. Default mode is proposal/report generation under `domains/wiki/reports/`.

## Restored History

`ingest_full_wikimedia_history.py` fetches the full public Wikimedia contribution history for `Dissident93` from enwiki, Wikidata, and Commons, then writes:

- `domains/wiki/data/dissident93_wikimedia_full_history.jsonl`
- `domains/wiki/data/dissident93_wikimedia_full_history_profile.json`
- `domains/wiki/reports/dissident93_wiki_habits_profile.md`

`restore_wikimedia_archive.py` restores the archived Dissident93 Wikimedia API pipeline run from `archive/raw/raw_datasets/wikipedia_2026-04-28.zip` into current wiki-domain normalized data:

- `domains/wiki/data/dissident93_wikimedia_history.json`
- `domains/wiki/data/dissident93_wikimedia_history_summary.json`
- `domains/wiki/reports/dissident93_wikimedia_history_restore.md`
