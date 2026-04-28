# Wiki Normalized Data

Normalized wiki-domain data lives here. Raw exports and archived API payloads stay under `archive/raw/`.

## Dissident93 Wikimedia History

- `dissident93_wikimedia_full_history.jsonl` is the full normalized local contribution history fetched from Wikimedia public APIs. It spans 2012-05-04 to 2026-04-28 and contains 186,519 rows. It is ignored by Git because it is about 84 MB.
- `dissident93_wikimedia_full_history_profile.json` is the compact machine-readable profile derived from the full history. This is the preferred artifact to share with LLMs.
- `dissident93_wikimedia_history.json` restores the archived Wikimedia API pipeline run for the `Dissident93` account.
- `dissident93_wikimedia_history_summary.json` keeps compact counts, source provenance, project split, classification split, yearly activity, and top mainspace pages.

Source provenance:

- `archive/raw/raw_datasets/wikipedia_2026-04-28.zip`

The normalized JSON is domain evidence, not canon. Reports and future profile claims should cite it as evidence and preserve the raw archive as the audit source.

For account-level interpretation, start with `domains/wiki/README.md` and `domains/wiki/reports/dissident93_wiki_habits_profile.md`, then use the compact profile JSON for machine-readable counts.
