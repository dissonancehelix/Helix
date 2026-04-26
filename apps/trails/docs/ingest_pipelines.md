# Ingest Pipelines Reference

All ingest scripts populate the **Metadata layer** registry tables in `retrieval/index/trails.db`. They do not produce Atlas content — that is handled by `pipelines/generate/generate_atlas.py`.

All scripts are idempotent (`INSERT OR IGNORE`) unless noted otherwise.

---

## Active Ingest Sources

### English Wikipedia

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/ingest_en_wikipedia.py` |
| Corpus | `corpus/wiki/en_wikipedia_characters.json` |
| Trust tier | 1 (Wikipedia) |
| Language | `en` |
| Target tables | `entity_registry`, `chunk_registry` (chunk_type: background, lead) |
| Run frequency | Re-run only when corpus files change |

Ingests EN Wikipedia character pages for the series. The full Phase 20 mirror pass is complete; only run again if corpus is refreshed.

---

### JA Wikipedia (characters)

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/ingest_ja_wiki.py` |
| Corpus | `corpus/wiki/ja_wikipedia_characters.json` |
| Trust tier | 1 (Wikipedia) |
| Language | `ja` |
| Target tables | `chunk_registry` (chunk_type: background, language='ja'), `aliases` |
| Run frequency | Re-run after `seed_ja_aliases.py` to improve match coverage |

Parses 408 JA character blocks and matches them to existing entities via JA name extraction from EN chunk text. Currently matches ~298/408. Re-seeding aliases before re-run improves coverage.

Pre-run: `python scripts/enrich/seed_ja_aliases.py`

---

### Kiseki Fandom Wiki (EN)

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/parse_en_fandom.py` |
| Corpus | `corpus/raw/fandom_en/` |
| Trust tier | 2 (fan wiki) |
| Language | `en` |
| Target tables | `chunk_registry` (background, lead, appearance, personality) |
| Run frequency | Re-run when fandom corpus is refreshed |

Extracts character profiles, lore, and relationship information from the Kiseki Fandom wiki mirror.

---

### TV Tropes

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/parse_tvtropes_bulk.py` |
| Corpus | `corpus/raw/tvtropes/` |
| Trust tier | 2 (fan wiki) |
| Language | `en` |
| Target tables | `chunk_registry` (lore, personality) |
| Run frequency | Re-run when corpus is refreshed |

Ingests TV Tropes character entries as `lore` and `personality` chunks — useful for trait analysis and thematic context.

---

### Official Bios (XSEED/NISA/Falcom)

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/parse_en_official_bios.py` |
| Corpus | `corpus/official/` |
| Trust tier | 0 (official) |
| Language | `en` |
| Target tables | `chunk_registry` (lead, background) |
| Run frequency | Re-run when official corpus is updated |

Highest-trust source. Falcom official character bios, XSEED localization text, and NISA promotional copy.

---

### Voice Actor Data

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/ingest_va_data.py` |
| Corpus | Inline / `corpus/meta/va_data.csv` |
| Trust tier | 1 |
| Language | `en` / `ja` |
| Target tables | `relationship_registry` (voiced_by_jp, voiced_by_en), `entity_registry` (staff) |
| Run frequency | Re-run when VA roster is updated |

Maps character entities to voice actor staff entries via typed relationship edges.

---

### World Lore

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/ingest_world_lore.py` |
| Corpus | `corpus/lore/` |
| Trust tier | 1–2 |
| Language | `en` |
| Target tables | `chunk_registry` (lore), `entity_registry` (concept) |
| Run frequency | Re-run when lore corpus is expanded |

World-building lore entries: Zemurian history, Sept-Terrion lore, Ouroboros documents, etc.

---

### Geography / Locations

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/ingest_geography.py` |
| Corpus | `corpus/geo/` |
| Trust tier | 1–2 |
| Language | `en` |
| Target tables | `entity_registry` (location), `chunk_registry` (background) |
| Run frequency | Re-run when geography corpus is updated |

Registers location entities and ingests descriptive background chunks for cities, regions, dungeons, and landmarks.

---

### Media Registry (Games, Anime, etc.)

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/ingest_media_scale_up.py` |
| Corpus | `corpus/meta/media_catalog.csv` |
| Trust tier | 0 (official) |
| Language | `en` |
| Target tables | `media_registry`, `games_registry` |
| Run frequency | Re-run only when new media titles are added |

Registers all transmedia objects (23 entries: games, anime, manga, drama CDs) in `media_registry`.

---

### Staff Metadata

| Field | Value |
| :--- | :--- |
| Script | `pipelines/ingest/ingest_staff_metadata.py` |
| Corpus | `corpus/meta/staff.csv` |
| Trust tier | 0–1 |
| Language | `en` / `ja` |
| Target tables | `entity_registry` (staff) |
| Run frequency | Re-run when staff roster is updated |

Registers Falcom staff (composers, directors, writers) and third-party staff (EN/JP VAs, XSEED/NISA producers).

---

## Normalization Pipelines

Run after ingest to resolve aliases and link entities.

| Script | Purpose |
| :--- | :--- |
| `pipelines/normalize/optimized_mapper.py` | JA↔EN name resolution across chunk_registry and entity_registry |
| `pipelines/normalize/backfill_jp_names.py` | Fill `japanese_name` on entity_registry from alias table |
| `pipelines/normalize/link_faction_members.py` | Create `member_of` edges from chunk text faction mentions |

---

## Enrichment Scripts

Run after normalization to add typed edges, spoiler bands, and JA aliases.

| Script | Purpose |
| :--- | :--- |
| `scripts/enrich/extract_relationships.py` | Extract typed edges (trained_under, rivals, family) from chunk text |
| `scripts/enrich/auto_bander.py` | Assign `spoiler_band` values by arc to entity_registry and chunk_registry |
| `scripts/enrich/seed_ja_aliases.py` | Seed known JA katakana aliases into the aliases table |

---

## Trust Tier Reference

| Tier | Source |
| :--- | :--- |
| 0 | Official (Falcom, XSEED, NIS America) |
| 1 | Wikipedia (EN or JA) |
| 2 | Fan wiki (Kiseki Fandom, Miraheze, TV Tropes) |
| 3 | Speculative / unverified |

---

## One-Time Seeds (Archived)

These scripts ran exactly once during Phase 20 bootstrap and are preserved in `archive/one_time_seeds/` for reference:

- `parse_en_wiki_full_clone.py` — Full EN Wikipedia mirror ingest
- `parse_full_mirror.py` — Phase 20 routing script
- `ingest_backbone_scale_up.py` — Initial backbone entity seeding
- `wiki_discovery.py` — Corpus bootstrap discovery
- `wiki_bulk_export.py` — Corpus export for offline processing
