# Helix Foobar Tool v0 — SPEC

## Purpose

The Helix Foobar Tool v0 is an operator-facing audit, sync, indexing, and repair-planning layer for the Foobar library. It sits between Foobar (live operator library), the codex (structured Helix mirror), and Helix analysis layers — making the relationship between them legible, queryable, and maintainable.

It is not a generic tag editor. It is not a blind re-ingest pipeline. It does not write to Atlas.

---

## Existing Helix Infrastructure This Tool Reuses

| Component | Path | Role |
|-----------|------|------|
| TrackDB | `domains/music/model/ingestion/data/helix_music.db` | Canonical SQLite track store |
| MetadataProcessor | `domains/music/model/ingestion/metadata_processor.py` | Full-library metadata extraction |
| MetadbSqliteReader | `domains/music/model/ingestion/adapters/metadb_sqlite.py` | Foobar metadb.sqlite ingestion |
| FoobarAdapter | `domains/music/model/ingestion/adapters/foobar.py` | Foobar library scan + sidecar reading |
| Field index | `codex/library/music/.field_index.json` | 51MB fast field index |
| Codex schema | `codex/library/music/SCHEMA.json` | canonical v3.0 music entity schema |
| Ingestion config | `domains/music/model/ingestion/config.py` | All paths, formats, constants |

This tool wraps these — it does not reimplement them.

---

## Source-of-Truth Rules

### Foobar is authoritative for mutable library fields:
`title`, `artist`, `album`, `album_artist`, `date`, `genre`, `featuring`, `sound_team`, `franchise`, `track_number`, `total_tracks`, `disc_number`, `total_discs`, `comment`, `platform`, `sound_chip`

### Foobar is authoritative for live state:
`playcount`, `rating`, `loved` status, playlist inclusion

### Codex is authoritative for:
Normalized path-linked track records, field index, fast query structures, derived maintenance reports, analysis-ready library views

### Atlas is NOT involved:
No Atlas writes occur during library hygiene work. Atlas is for validated, promoted structural knowledge only.

---

## Canonical Foobar Metadata Schema

```
Title        = TITLE
Artist       = ARTIST
Album        = ALBUM
Date         = DATE
Genre        = GENRE
Featuring    = FEATURING
Album Artist = ALBUM ARTIST
Sound Team   = SOUND TEAM
Franchise    = FRANCHISE
Track Number = TRACKNUMBER
Total Tracks = TOTALTRACKS
Disc Number  = DISCNUMBER
Total Discs  = TOTALDISCS
Comment      = COMMENT
Platform     = PLATFORM
Sound Chip   = SOUND CHIP
```

These are first-class structural fields. SOUND TEAM, FRANCHISE, PLATFORM, SOUND CHIP are not optional trivia — they power the custom schema audits.

---

## Sync State Vocabulary

### Track-level states
| State | Description |
|-------|-------------|
| `in_sync` | Track exists in both Foobar and codex with matching key fields |
| `new_in_foobar` | Track found in Foobar scan but not yet in codex |
| `missing_from_codex` | Track was previously indexed but no longer in codex |
| `missing_from_foobar` | Codex has a record for a path that no longer exists on disk |
| `codex_orphan` | Codex record with no corresponding Foobar/library source |
| `metadata_drift` | Key metadata fields differ between Foobar and codex |
| `stats_drift` | Playcount, rating, or loved differs between Foobar and codex |
| `path_drift` | File path changed; record exists but path no longer matches |
| `schema_gap` | Required schema fields are missing or empty |
| `stale_analysis_candidate` | Metadata changed since last analysis run |
| `duplicate_candidate` | Multiple records appear to describe the same track |
| `alias_candidate` | Likely alias collision (e.g., composer name variants) |
| `manual_review_required` | Conflicting signals; requires operator decision |

### Album-level states
| State | Description |
|-------|-------------|
| `album_in_sync` | Full album in sync |
| `album_numbering_issue` | Track number gaps, duplicates, or missing totals |
| `album_disc_issue` | Disc number missing on multi-disc, or total_discs inconsistent |
| `album_mixed_album_artist` | album_artist field inconsistent within same release |
| `album_partial_codex_coverage` | Some tracks in codex, some missing |
| `album_platform_chip_gap` | Platform or sound_chip missing for expected VGM release |
| `album_franchise_gap` | Franchise missing where expected |
| `album_sound_team_gap` | Sound team missing for soundtrack release |
| `album_manual_review_required` | Conflicting metadata signals across album |

---

## v0 Scope

v0 is a **read / diff / report / patch-plan** tool.

**In scope:**
- Inspect live Foobar-facing data
- Inspect existing codex mirror state
- Compare and classify into sync states
- Emit repair plans and reports
- Optionally write to codex-side derived artifacts

**Out of scope for v0:**
- Full real-time Foobar plugin or UI integration
- Direct mutation of Foobar SQLite internals
- Bulk rewriting of cherished metadata automatically
- Re-ingesting the entire library every run without cause
- Making Atlas claims from metadata hygiene work

---

## Core Workflows

### 1. Library Audit
Full health report for Foobar ↔ codex relationship.

### 2. Codex Sync Audit
Account for existing codex indexing. Compute new, stale, orphaned, drifted.

### 3. Structural Metadata Audit
Custom schema check: sound_team, franchise, platform, sound_chip coverage and consistency.

### 4. Numbering and Release Structure Audit
Track number / disc / release structure integrity.

### 5. Loved and Stats Reconciliation
Loved/rating/playcount drift between live Foobar state and codex mirror.

### 6. Query and Navigation
Fast filtered views using existing metadata quality.

---

## Output Artifacts

Written to `domains/music/tools/foobar/artifacts/`:

| Artifact | Contents |
|----------|----------|
| `audit_summary.md` | Human-readable health report |
| `track_issues.json` | Per-track issue list with sync states |
| `album_issues.json` | Per-album issue list |
| `sync_manifest.json` | New, stale, orphaned, in_sync counts per source |
| `repair_plan.csv` | Reviewable patch plan — operator approves before anything changes |
| `new_in_foobar.json` | Tracks found in library scan but not in codex |
| `codex_orphans.json` | Codex records with no corresponding disk file |
| `loved_drift.json` | Loved/stats drift between Foobar and codex |
| `normalization_candidates.json` | Fields candidates for normalization (aliases, casing, etc.) |

---

## Patch Model

v0 is patch-plan first.

**Allowed in v0:** write reports, write manifests, write codex-side refreshed indices (explicit only)

**Not default in v0:** mutate Foobar metadata, rewrite external tags in bulk, modify Foobar SQLite internals

**Safe future path:** `apply_to_codex`, `export_patch_plan`, `apply_to_sidecars` — never silent mutation

---

## Implementation Order (from spec)

1. Read-only audit against Foobar source + codex mirror
2. Sync-state classification
3. Repair-plan generation  
4. Selective codex refresh
5. (Later) Controlled sidecar writeback

---

## Folder Layout

```
domains/music/tools/foobar/
├── SPEC.md           ← this file
├── README.md
├── manifest.yaml
├── runner.py         ← CLI entrypoint
├── audit.py          ← library audit checks
├── sync.py           ← codex sync + diff logic
├── diff.py           ← field-level comparison primitives
├── reports.py        ← report formatting and output
├── repair_plan.py    ← patch plan generation
└── artifacts/        ← all tool output written here
```

