# Trails Database: Operating Rules

This document defines the pipeline discipline and hard/soft rules governing all work in this repository.

AI agents executing tasks in this workspace must abide by these boundaries. Do NOT apply stylistic rewriting during raw ingestion. Do NOT mutate the foundational database layers without a documented curation pass.

---

## The Two-Layer Model

The project is organized into two conceptual layers:

- **Metadata** — structured semantic data; what things are, how they connect, what sources support them
- **Atlas** — explanatory entries; what things mean, how they fit into the continuity

All pipeline operations serve one or both of these layers. There is no third layer. Export is a derived feature.

---

## Pipeline Operations

The four pipeline operations map to the two layers as follows:

### 1. Ingestion → feeds Metadata
- **Goal**: Acquire, preserve, and register raw source material into `chunk_registry` and `source_registry`.
- **Action**: Scrape wikis, ingest game scripts, parse local transmedia HTML, log source URLs in `source_registry`.
- **Rule**: Do NOT summarize or rewrite. Preserve original HTML/wikitext or raw string completely. Provenance is sacred.
- **Lifecycle state produced**: `raw`

### 2. Normalization → structures Metadata
- **Goal**: Build a unified entity graph from disparate sources.
- **Action**: Consolidate aliases, resolve relational mappings (character → voice actor), assign spoiler bands, structure the baseline registry schema.
- **Rule**: Do NOT invent data. Japanese names and alternate transliterations are preserved in Metadata as structural substrate.
- **Lifecycle state produced**: `normalized`

### 3. Curation → produces Atlas
- **Goal**: Compress normalized Metadata into Atlas-grade explanatory prose.
- **Action**: Apply Dissonance encyclopedic mode. Construct identity-first leads. Compress factual arcs. Enforce third-person neutrality. Write into `chunk_registry` with `chunk_type = curated_bio`.
- **Rule**: Do NOT overwrite raw logs. The curated string is a derived output. Do NOT emit Atlas prose without source grounding in Metadata.
- **Lifecycle state produced**: `curated`

### 4. Export → derives from Metadata + Atlas
- **Goal**: Package curated content for downstream systems.
- **Action**: Generate JSONL, Markdown, or structured views from `chunk_registry` and registry tables.
- **Rule**: Do NOT emit unreviewed `raw` or `normalized` data as encyclopedic output. Adhere to `spoiler_policy.md` during all export runs.
- **Lifecycle state produced**: `export_ready`

---

## Hard Rules (Do Not Compromise)

- **Stable IDs** — `char:estelle_bright`, `faction:bracer_guild`, `media:sky_fc`. IDs are permanent once assigned.
- **Provenance preservation** — all chunks retain their `source_id` link. No chunk is authored without a grounding source.
- **Spoiler discipline** — Band 100 content is suppressed in all standard retrieval and export. Never leak Band 100 into general character summaries.
- **Foreign key integrity** — all `appearance_registry` and `relationship_registry` entries must link to valid IDs in their parent tables.
- **Games as media subtypes** — games are tracked under `media_registry`. `games_registry` is a subtype view, not an independent identity.
- **Atlas prose is derived** — curated bios and Atlas entries are never the primary source of record. They derive from Metadata.

---

## Soft Rules (Downstream Preference)

- Encyclopedic tone (Dissonance mode — see `docs/atlas.md`)
- Prose compression logic
- Japanese alias formatting in `entity_registry`
- Aesthetic presentation choices in export formats

---

## Working in This Repository

When in doubt about what layer an operation belongs to:
- If you are storing *what something is* → Metadata operation
- If you are writing *what something means or does* → Atlas operation
- If you are serializing data for another system → Export operation (not a layer change)

---

## Terminology Freeze

These are the only conceptual terms for the two-layer model:

| Term | Status | Meaning |
| :--- | :--- | :--- |
| **Metadata** | Locked | The structured semantic layer |
| **Atlas** | Locked | The explanatory entry layer |
| **Export** | Locked | A derived feature, not a layer |

Allowed implementation terms (not conceptual identity):
- registries, tables, pipelines
- Cargo tables, forms, schemas
- MediaWiki backend, MediaWiki enforcement layer

Disallowed as top-level identity framing for this project:
- `substrate` / `curation substrate`
- `RAG engine`
- `8-registry architecture` (use "8-registry implementation" or "registry tables under Metadata" if precision is needed)
- `4-layer discipline` as the project's conceptual identity (it describes pipeline operations, not the project)

The 8 registry tables still exist. They are implementation machinery under the Metadata layer. They are not the project's public conceptual identity.

Future agents working in this repository must not reintroduce the above disallowed framings. If you encounter them in any doc, correct them on sight.

---

## Documentation Verification Checklist

Run this checklist when auditing or updating project documentation.

### Framing
- [ ] "Metadata" and "Atlas" are the only two conceptual layers named in core docs
- [ ] "Export" is described only as a derived feature or pipeline output, not a third layer
- [ ] The registries are described as Metadata implementation machinery, not as the project's identity
- [ ] No doc uses "substrate", "curation substrate", or "RAG engine" as the primary project description
- [ ] No doc presents "8-registry architecture" or "4-layer discipline" as the project's top-level conceptual identity
- [ ] No doc uses inflated metaphor language (manifesto tone, mythology framing) in place of precise specification

### MediaWiki
- [ ] `docs/mediawiki_plan.md` states MediaWiki 1.41+ as the version baseline
- [ ] The Draft → Main → Approved Revs promotion path is explicitly documented
- [ ] Cargo table definitions exist for all 6 page classes
- [ ] The role of MediaWiki (background enforcement/storage backend, not ingest spine, not human-facing UI) is stated clearly

### Atlas discipline
- [ ] `docs/atlas.md` contains the source/citation contract section
- [ ] Atlas entries are described as drawing from Metadata, not replacing it
- [ ] The Atlas writing rules (Dissonance encyclopedic mode) are documented with explicit anti-patterns

### Spoiler policy
- [ ] All core docs correctly reference `spoiler_band < 100` as the safe-search default
- [ ] Band 100 (Kai) is described as suppressed in default retrieval

### Grep-based spot checks (run in repo root)
```
grep -r "curation substrate" --include="*.md" docs/ README.md
grep -r "RAG engine" --include="*.md" docs/ README.md
grep -r "8-registry architecture" --include="*.md" docs/ README.md
grep -r "Helix Trails" --include="*.md" docs/ README.md
```
All of the above should return zero matches in non-corpus, non-scratch files.
