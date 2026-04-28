# Trails Database

> Project name is currently provisional and intentionally generic. Final naming is deferred.

**Project name: Trails Database.**

## Overview

The Trails Database is a private, English-facing two-layer canon atlas for the *Trails (Kiseki)* universe. It is not a wiki mirror. It is a structured, curated reference system designed to be the most comprehensive English-facing continuity substrate for the series.

## The Two-Layer Model

### Metadata
The structured semantic layer. Knows what every entity, media object, place, organization, and concept *is* — its aliases, sources, appearances, relationships, chronology, and spoiler band. Implemented through a SQLite registry schema (`retrieval/index/trails.db`). Dry, queryable, provenance-aware.

### Atlas
The explanatory entry layer. Explains who characters are, what places mean, what events do to the continuity, how organizations operate. Written in Dissonance encyclopedic mode. Not constrained by Wikipedia MOS size limits. The master explanatory form.

**Design Law:** Metadata knows. Atlas explains. Exports are selective reductions.

## Principles

1. **English-outward.** All display text is English-primary. Japanese names and aliases are preserved in Metadata as structural substrate — they do not appear in Atlas prose unless necessary for disambiguation.
2. **Provenance.** Every chunk and entity retains its source ID. Origin is never discarded.
3. **Spoiler discipline.** Entities and chunks carry `spoiler_band` integers (10–100). Standard retrieval filters `spoiler_band < 100`. Band 100 (Kai) is suppressed by default.
4. **Export as derivation.** Export formats (JSONL, Markdown, API views) are generated from Metadata and Atlas cooperation. They are not the master form.

## Folder Map

| Folder | Serves | Purpose |
| :--- | :--- | :--- |
| `retrieval/index/trails.db` | Metadata | The SQLite database; all 8 registry tables |
| `retrieval/` | Metadata | Query utilities and FTS5 search interface |
| `pipelines/ingest/` | Metadata | Raw source → registry population |
| `pipelines/normalize/` | Metadata | Alias resolution, entity graph structuring |
| `pipelines/curate/` | Atlas | Curated bio production; style enforcement |
| `pipelines/export/` | Export feature | JSONL, Markdown, wiki-format serializers |
| `corpus/` | Metadata (source) | Raw source material: wiki mirrors, scripts, books |
| `docs/` | Both | Documentation for schema, rules, and planning |
| `scripts/` | Metadata | Diagnostic, verification, and utility scripts |
| `scratch/` | Both | One-off analysis and verification work |

## MediaWiki Backend

A local MediaWiki installation (WSL) runs as a background structural enforcement and storage backend. It is not a human-facing interface — all interaction happens through Claude Code. MediaWiki provides Cargo-based schema enforcement, Atlas prose storage, and editorial state tracking. See `docs/mediawiki_plan.md`.

## Key Documents

- `docs/schema.md` — Metadata registry schema and Atlas page class definitions
- `docs/atlas.md` — Atlas layer definition, page classes, and writing rules
- `docs/operating_rules.md` — Pipeline discipline, terminology freeze, and verification checklist
- `docs/language_policy.md` — Language architecture: English primary, Japanese substrate, future JP capability
- `docs/spoiler_policy.md` — Spoiler band policy and retrieval safety rules
- `docs/mediawiki_plan.md` — MediaWiki authoring surface plan
- `docs/ingest_pipelines.md` — Ingest pipeline index
