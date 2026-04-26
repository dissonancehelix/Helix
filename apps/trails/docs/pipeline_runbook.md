# Pipeline Runbook

Ordered commands to run or re-run each pipeline stage. All Python commands run from the project root on Windows (`python`). DB path: `C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db`.

---

## Stage 0 — Verify DB State

```bash
python scripts/inspect/inspect_db.py
```

Quick entity count:
```python
import sqlite3
c = sqlite3.connect('C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db').cursor()
c.execute('SELECT entity_type, COUNT(*) FROM entity_registry GROUP BY entity_type ORDER BY COUNT(*) DESC')
print(c.fetchall())
```

---

## Stage 1 — Ingest (Source → chunk_registry)

Run only when adding new source material. All ingest scripts are idempotent (INSERT OR IGNORE).

### JA Wikipedia (characters)
```bash
python pipelines/ingest/ingest_ja_wiki.py
```
Parses `corpus/wiki/ja_wikipedia_characters.json` → chunk_registry (language='ja').
Re-seeding JA aliases before re-run: `python scripts/enrich/seed_ja_aliases.py`

### EN Wikipedia + series overview
Already ingested during Phase 20. No re-run needed unless corpus files change.

### Kiseki Fandom wiki (EN)
```bash
python pipelines/ingest/parse_en_fandom.py
```

### TV Tropes
```bash
python pipelines/ingest/parse_tvtropes_bulk.py
```

### Official bios
```bash
python pipelines/ingest/parse_en_official_bios.py
```

### Voice actor data
```bash
python pipelines/ingest/ingest_va_data.py
```

### World lore / geography
```bash
python pipelines/ingest/ingest_world_lore.py
python pipelines/ingest/ingest_geography.py
```

---

## Stage 2 — Normalize (Resolve aliases, link factions)

```bash
python pipelines/normalize/optimized_mapper.py   # JA↔EN name resolution
python pipelines/normalize/backfill_jp_names.py  # fill JP names on entities
python pipelines/normalize/link_faction_members.py  # member_of edges
```

---

## Stage 3 — Enrich Schema

Run once; safe to re-run (INSERT OR IGNORE / UPDATE).

```bash
python scripts/enrich/extract_relationships.py   # typed edges (trained_under, rivals, family)
python scripts/enrich/auto_bander.py             # assign spoiler_band by arc
python scripts/enrich/seed_ja_aliases.py         # expand JA alias table
```

---

## Stage 4 — Maintenance (if DB is corrupted or artifacts crept back)

```bash
# Audit for wiki subsection artifacts (gallery/story/gameplay fused IDs, list_of pages)
python scripts/maintenance/purge_subsection_artifacts_v2.py
python scripts/maintenance/purge_subsection_artifacts_v2.py --apply

# Recover missing entities from chunk_registry references + clean artifacts in one pass
python scripts/maintenance/recover_and_purge.py
python scripts/maintenance/recover_and_purge.py --apply

# Fix garbled display names (extract canonical from chunk text)
python scripts/maintenance/normalize_display_names.py
python scripts/maintenance/normalize_display_names.py --apply
```

---

## Stage 5 — JA Translation Pass ✅ COMPLETE (2026-04-17)

All 1,069 JA chunks translated into English using XSEED/NISA canonical terminology.
Stored in `chunk_registry.translated_content`. 0 errors across all 19 source IDs.
Model used: claude-haiku-4-5. Re-run only if new JA chunks are ingested.

```bash
# One-time schema migration (safe to re-run)
python scripts/translation/migrate_add_translated_content.py

# Dry-run: preview prompt for first chunk
python scripts/translation/translate_ja_chunks.py --dry-run

# Translate highest-value source first (character descriptions, 202 chunks)
python scripts/translation/translate_ja_chunks.py --source-id wikipedia:ja_chars

# Full run (all 1,069 JA chunks, Haiku model)
python scripts/translation/translate_ja_chunks.py

# High-quality pass for important chunks (Opus model)
python scripts/translation/translate_ja_chunks.py --source-id wikipedia:ja_chars --quality

# Verify
python -c "
import sqlite3
c = sqlite3.connect('C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db').cursor()
c.execute(\"SELECT COUNT(*) FROM chunk_registry WHERE language='ja' AND translated_content IS NOT NULL\")
print('Translated:', c.fetchone()[0])
c.execute(\"SELECT COUNT(*) FROM chunk_registry WHERE language='ja' AND (translated_content IS NULL OR translated_content='')\")
print('Remaining:', c.fetchone()[0])
"
```

Script is resumable — skips chunks where `translated_content IS NOT NULL` (unless `--rerun`).

---

## Stage 6 — Atlas Generation (Claude API → entity_summary)

Requires `ANTHROPIC_API_KEY` environment variable.

```bash
# Dry-run single entity (no API call)
python pipelines/generate/generate_atlas.py --entity char:estelle_bright --dry-run

# Generate for highest-completeness characters first
$env:ANTHROPIC_API_KEY="sk-ant-..."   # PowerShell
python pipelines/generate/generate_atlas.py --type character --min-completeness 100

# Then mid-tier
python pipelines/generate/generate_atlas.py --type character --min-completeness 60

# Other entity types
python pipelines/generate/generate_atlas.py --type location --min-completeness 40
python pipelines/generate/generate_atlas.py --type faction --min-completeness 40

# All remaining (skip already-generated)
python pipelines/generate/generate_atlas.py
```

Pipeline is resumable — skips entities where `entity_summary.summary IS NOT NULL`.

---

## Stage 6 — Translation Pass (XSEED/NISA canonical names)

Phased review in Claude Code chatspace. Run one batch at a time.

```bash
# Export a batch for review (dry-run prints, no file written)
python scripts/translation/export_for_review.py --type character --batch 1 --dry-run

# Write review file
python scripts/translation/export_for_review.py --type character --batch 1

# After reviewing and editing the TSV, apply corrections
python scripts/translation/apply_corrections.py translation/review_char_1.tsv --dry-run
python scripts/translation/apply_corrections.py translation/review_char_1.tsv --apply
```

Phase order: A=character, B=location+faction, C=quest (split by arc), D=item, E=concept

---

## Stage 7 — Refresh Cargo (MediaWiki sync)

Run after any significant entity_registry changes.

```bash
# Truncate all Cargo tables
python -c "
import subprocess
DB_USER,DB_PASS,DB_NAME = 'wiki_user','trailsdb2026','trails_wiki'
def sql(q): subprocess.run(['bash','-c',f'mariadb -u {DB_USER} -p{DB_PASS} {DB_NAME}'],input=q,capture_output=True,text=True)
for t in ['cargo__Character','cargo__Faction','cargo__Location','cargo__Staff','cargo__Entity','cargo__Appearance']:
    sql(f'TRUNCATE TABLE {t};')
    print('TRUNCATE',t)
"

# Re-populate
python pipelines/setup/bulk_populate_cargo.py

# Verify
python scripts/inspect/verify_cargo.py
```

---

## Stage 8 — Export

```bash
python pipelines/export/export_character_profiles.py   # Markdown character bios
python pipelines/export/export_full_registry.py        # Full registry Markdown
python pipelines/export/export_backbone_jsonl.py       # JSONL entity graph
python pipelines/export/export_to_wiki.py              # MediaWiki Atlas pages
```

---

## Verification Queries

```python
import sqlite3
conn = sqlite3.connect('C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db')
c = conn.cursor()

# Entity breakdown
c.execute('SELECT entity_type, COUNT(*) FROM entity_registry GROUP BY entity_type ORDER BY COUNT(*) DESC')
print(c.fetchall())

# Chunk breakdown
c.execute('SELECT chunk_type, COUNT(*) FROM chunk_registry GROUP BY chunk_type ORDER BY COUNT(*) DESC')
print(c.fetchall())

# Atlas coverage
c.execute('SELECT completeness, COUNT(*) FROM entity_summary GROUP BY completeness ORDER BY completeness')
print(c.fetchall())

# Relationship types
c.execute('SELECT predicate, COUNT(*) FROM relationships GROUP BY predicate ORDER BY COUNT(*) DESC')
print(c.fetchall())

# Entities with Atlas summaries
c.execute('SELECT COUNT(*) FROM entity_summary WHERE summary IS NOT NULL AND summary != ""')
print('Atlas entries:', c.fetchone()[0])
```
