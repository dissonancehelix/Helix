# Zemurian Index: Language Policy

## Architecture

The Zemurian Index operates a two-language architecture across its two layers.

| Layer | Primary language | Japanese role |
| :--- | :--- | :--- |
| **Metadata** | Both — structured fields are language-neutral | `japanese_name`, `aliases`, JA chunk storage |
| **Atlas** | English | JA source chunks are substrate for EN curation |
| **Export** | English-primary | JA-facing view is a planned capability |

---

## English: The Working Layer

All Atlas entries are written in English. This is non-negotiable for the primary working form of the Zemurian Index.

- All `curated_bio` chunks are in English.
- All Atlas page prose in MediaWiki is in English.
- All `english_display_name` fields in `entity_registry` are canonical.
- All cross-linking, relationship descriptions, and continuity summaries are in English.

English is the interface layer for curation, navigation, and personal use.

---

## Japanese: The Substrate

Japanese source material is preserved as substrate — not discarded, not demoted, not hidden.

**What stays in Japanese:**
- `entity_registry.japanese_name` — the canonical JP name for every entity that has one
- `entity_registry.aliases` — includes JP aliases alongside EN alternates
- `chunk_registry` rows with `language = 'ja'` — raw content from JA Wikipedia, Falcom JP sites, and JA fan wikis
- JA Wikipedia-sourced chunks: series overview, character list, timeline (stored as `series_overview`, `character_list`, `timeline` chunk types)

**Why it stays:**
- JA sources are often the highest-trust or most authoritative source for names, release dates, and series metadata
- The JA Wikipedia character list is the best systematic source for JP name coverage
- Falcom's JP official sites carry trust tier 0 — they are ground truth for canon names and release information
- Discarding JA content would reduce the provenance integrity of the entire Metadata layer

**How it's used during curation:**
- When writing an English Atlas entry, the curator draws from both EN Fandom chunks and JA substrate chunks
- JP name extraction runs automatically on JA character list pages during sync, backfilling `entity_registry.japanese_name`
- Translation of JA prose into EN Atlas content is done at curation time by the curator (or with LLM assistance) — no automated translation pipeline is needed

---

## Japanese Name Coverage

Current state: 2,306 of 5,172 entities have `japanese_name` populated (44.6%).

Target: all characters, factions, locations, and major concepts should have `japanese_name` set. Quests and minor concepts are lower priority.

The `mediawiki_sync.py` pipeline backfills `japanese_name` automatically when the JA Wikipedia character list page is updated. Manual backfill passes (`pipelines/normalize/backfill_jp_names.py`, `pipelines/normalize/map_ja_names.py`) can extend coverage further.

---

## Future: Japanese-Facing Output

The Zemurian Index is designed so a Japanese-language view can be generated from the same Metadata and Atlas data without schema changes.

What a JP-facing view would use:
- `entity_registry.japanese_name` as the display name
- `entity_registry.aliases` for JP alternate forms
- `chunk_registry` rows with `language = 'ja'` as the primary text content
- `entity_registry.english_display_name` as a cross-reference field

What it would not require:
- A separate database
- New registry tables
- Changes to the spoiler band system
- Changes to the relationship or appearance registries

This is a planned capability, not current work. The primary interface remains English. The JA data is preserved because it is valuable and because the cost of preserving it is zero — the infrastructure already supports it.

---

## Sync Pipeline Language Handling

The `mediawiki_sync.py` pipeline respects this architecture:

| Source | Handler | Language stored |
| :--- | :--- | :--- |
| `wiki:kiseki_fandom` | `ingest_page()` — entity classification | `en` |
| `wiki:ja_wikipedia_*` | `ingest_ja_aggregate_page()` — JA substrate handler | `ja` |

JA Wikipedia pages are never run through the EN entity classifier. They are stored as `language='ja'` chunks and used for JP name backfill only. No JA Wikipedia content becomes a curated Atlas entry directly — it feeds the substrate, and a curator writes the EN Atlas entry from it.

---

## What Is NOT Done

- No automated machine translation of JA chunks into EN
- No replacing `english_display_name` with Japanese text
- No switching the Atlas prose language
- No separate JA Atlas layer (there is one Atlas, written in English)
- No discarding JA source material to save space

Translation is a curation act, done by a human or LLM at Atlas-writing time, not an automated pipeline step.
