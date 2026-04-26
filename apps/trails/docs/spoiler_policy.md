# Trails Database: Spoiler Policy

This document defines the spoiler handling rules for all retrieval, curation, and export operations. It applies to both the Metadata layer (registry queries) and the Atlas layer (curated prose and MediaWiki entries).

---

## 1. Core Policy

The Trails series involves continuous, highly interrelated storytelling across multiple arcs. Rather than date-based suppression, the Trails Database uses **spoiler banding** — a numeric classification applied to every entity and chunk.

**Pre-Kai material is Cleared. *Kai no Kiseki* (Band 100) is the live Frontier and is Suppressed by default.**

---

## 2. Spoiler Bands

Every entity in the Metadata layer and every chunk in `chunk_registry` carries a `spoiler_band` integer.

| Band | Coverage | Default Status |
| :--- | :--- | :--- |
| **10–14** | Sky Arc (Liberl) — FC, SC, 3rd | Cleared |
| **20–22** | Crossbell Arc — Zero, Azure | Cleared |
| **40–55** | Erebonia Arc — Cold Steel I–IV | Cleared |
| **65** | Reverie | Cleared |
| **70–75** | Calvard Arc — Daybreak I | Cleared |
| **80** | Daybreak II | Cleared |
| **100** | *Kai no Kiseki* — Beyond the Horizon | **Suppressed** |

---

## 3. Retrieval Rules

### Default Safe Search
All queries must automatically filter out the Frontier unless explicitly instructed otherwise.

```sql
WHERE spoiler_band < 100
```

### Archival / Curator Mode
When full coverage is explicitly requested:

```sql
WHERE spoiler_band <= 100
```

---

## 4. Atlas Rules

- Atlas entries must not include Band 100 content in their prose unless the page itself is spoiler-banded at 100.
- Character entries for entities with cross-band appearances must truncate their continuity sections at the current safe band.
- Band 100 Atlas pages exist in the database but are not surfaced in standard export or view generation.

---

## 5. Export Rules

- All export pipelines must check `spoiler_band` before emission.
- Do not emit Band 100 content into any general-purpose export format.
- Archival exports (band ≤ 100) require explicit curator authorization per run.
