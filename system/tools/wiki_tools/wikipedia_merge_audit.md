# Wikipedia Operator — Merge Audit

## Prior work found

| Path | What it was |
|------|-------------|
| `model/domains/language/ingestion/wikimedia/client.py` | MediaWiki API client (usercontribs pagination) |
| `model/domains/language/ingestion/wikimedia/normalizer.py` | Raw API dict → EditEvent dataclass |
| `model/domains/language/ingestion/wikimedia/classifier.py` | 17-category structural edit classifier |
| `model/domains/language/ingestion/wikimedia/corpus.py` | Corpus aggregation + artifact generation |
| `model/domains/language/probes/wikipedia_editor_probe.py` | 7-section behavioral analysis of Dissident93 |
| `model/domains/language/probes/wikipedia_corpus.py` | TTR/DCP across article sections |
| `system/tools/wikimedia/runner.py` | Full ingest CLI (ran 2026-03-29, 185,390 traces) |
| `system/tools/wiki/wiki_tool.py` | Stub — printed "not implemented" |
| `data/language/wikipedia_dissident93.json` | Operator dataset |
| `system/tools/wikimedia/artifacts/wiki_20260329_222848/` | Full ingest artifact run |

## What was kept

Everything above was kept in place. Nothing was deleted or moved.
The ingestion layer (`model/domains/language/ingestion/wikimedia/`) is stable and correct —
it was not touched.

## What was built on top (new)

| Path | Purpose |
|------|---------|
| `model/domains/language/wikipedia/__init__.py` | Subsystem root; defines OPERATOR_USERNAME, ENWIKI_API |
| `model/domains/language/wikipedia/account_ingest/ingest.py` | Wraps ingestion layer; adds template-focused extraction from JSONL artifact |
| `model/domains/language/wikipedia/template_index/indexer.py` | Fetches template source + TemplateData + /doc via API; cache at `system/tools/wikimedia/template_index/` |
| `model/domains/language/wikipedia/sandbox/validator.py` | expandtemplates + parse API surface; before/after compare with risk classification |
| `model/domains/language/wikipedia/pattern_library/patterns.py` | 10 operator patterns (if_empty_guard, fallback_chain, ifeq→switch, switch_default, infobox cleanup, blank row suppress, pluralization, deprecated alias, ref consolidation, nowiki display) |
| `model/domains/language/wikipedia/issue_solver/solver.py` | inspect_template, explain_template_logic, validate_snippet, compare_before_after, suggest_safe_rewrite, find_similar_past_patterns, propose_patch |
| `model/domains/language/wikipedia/operator/interface.py` | WikiOperator — unified entry point |
| `system/tools/wiki/wiki_tool.py` | Replaced stub with real CLI wired to WikiOperator |

## What was deprecated / superseded

- `system/tools/wiki/wiki_tool.py` stub body replaced. Old stub said "not implemented" — now real.
- Nothing else deprecated. The existing ingest runner (`system/tools/wikimedia/runner.py`) remains the canonical re-ingest CLI.

## Merge policy

The existing `ingestion/wikimedia/` layer was treated as a stable foundation.
The new `wikipedia/` subsystem imports from it rather than duplicating it.
No parallel tooling was created for what already existed.

