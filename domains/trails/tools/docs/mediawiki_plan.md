# Trails Database: MediaWiki Backend Plan

## 0. Version Baseline

**Required: MediaWiki 1.41 or later.**

This extension stack (Cargo, Page Forms, Page Schemas, Scribunto, Approved Revs, AbuseFilter, TemplateData) has been scoped against MediaWiki 1.41. If the target version changes, extension compatibility must be revalidated before Phase A begins. Do not begin installation against an earlier version.

---

## 1. Role of MediaWiki

The local MediaWiki installation is a **background structural enforcement and storage backend**. It is not a human-facing interface. The user does not browse it, edit pages manually, or use web forms.

All interaction with the Trails Database happens through Claude Code (this chat). Claude reads from and writes to MediaWiki programmatically via the MediaWiki API and direct DB access. MediaWiki provides:
- **Cargo** — Wikidata-like structured field enforcement and queryable storage for Metadata
- **Schema enforcement** — page class definitions that constrain what fields exist and what types they hold
- **Atlas prose storage** — structured wikitext storage for curated entries, written by Claude
- **Editorial state tracking** — Approved Revs separates stable from in-progress entries programmatically

MediaWiki is **not** the ingest spine. Raw ingest, parsing, and normalization remain in the Python pipelines feeding `trails.db`.

---

## 2. Extension Stack

All seven extensions below are required. External Data is optional.

| Extension | Role |
| :--- | :--- |
| **Cargo** | Structured storage and query layer backing Metadata. Replaces Semantic MediaWiki for structured data. |
| **Page Forms** | Controlled page creation and editing. Separates Metadata fields (form-validated) from Atlas prose (free wikitext). |
| **Page Schemas** | Defines the class/page schema for each entity type. Generates templates, categories, and Cargo tables from a schema definition. |
| **Scribunto** | Lua-based rendering engine. Powers infoboxes, derived displays, chronology boxes, relationship summaries, and helper formatting. |
| **Approved Revs** | Separates stable curator-approved entries from in-progress edits and draft work. Only approved revisions are shown to standard readers. |
| **AbuseFilter** | Prevents malformed edits, schema violations, namespace misuse, and structural corruption. |
| **TemplateData** | Documents template parameters. Improves parameter consistency and tooling support. |
| **External Data** | *(Optional)* Bridge for surfacing local file data or structured exports inside the wiki. |

---

## 3. Namespace Plan

| Namespace | ID | Purpose |
| :--- | :--- | :--- |
| `(Main)` | 0 | Atlas entries — long-form encyclopedic pages |
| `Metadata:` | custom | Structured data pages (Cargo-backed, form-controlled). Parallel to Atlas entries. |
| `Draft:` | custom | In-progress Atlas entries pending Approved Revs approval |
| `Template:` | 10 | Infobox templates, Cargo declare templates |
| `Form:` | (PF) | Page Forms entry forms |
| `Schema:` | (PS) | Page Schemas definitions |
| `Module:` | 828 | Scribunto/Lua rendering modules |
| `Category:` | 14 | Page class categories, arc categories, spoiler-band categories |

`LocalSettings.php` must define the custom `Metadata:` and `Draft:` namespaces.

---

## 4. Page Classes and Cargo Tables

Each of the six Atlas page classes has a corresponding Cargo table definition. These tables are the MediaWiki-side implementation of the Metadata layer fields defined in `docs/schema.md`.

### 4.1 Character

**Cargo table**: `cargo_characters`

| Field | Cargo Type | Notes |
| :--- | :--- | :--- |
| `entity_id` | String | Stable ID, e.g. `char:estelle_bright` |
| `name_en` | String | Canonical English name |
| `name_ja` | String | Japanese name |
| `aliases` | List (String) | All known alternate names |
| `arc_first_appearance` | String | Arc of first appearance |
| `spoiler_band` | Integer | 10–100 |
| `affiliation` | List (Page) | Linked Organization pages |
| `voice_jp` | Page | Linked Character/Staff page |
| `voice_en` | Page | Linked Character/Staff page |
| `entity_type` | String | Always `char` for this class |

**Template**: `Template:Infobox Character`
**Form**: `Form:Character`
**Module**: `Module:Infobox/Character`

---

### 4.2 Place

**Cargo table**: `cargo_places`

| Field | Cargo Type | Notes |
| :--- | :--- | :--- |
| `entity_id` | String | e.g. `loc:crossbell_city` |
| `name_en` | String | |
| `name_ja` | String | |
| `region` | String | Geographic region |
| `nation` | String | Political nation/state |
| `place_type` | String | city, dungeon, landmark, region, nation |
| `first_appearance` | String | Arc or media of first appearance |
| `spoiler_band` | Integer | |

**Template**: `Template:Infobox Place`
**Form**: `Form:Place`
**Module**: `Module:Infobox/Place`

---

### 4.3 Organization

**Cargo table**: `cargo_organizations`

| Field | Cargo Type | Notes |
| :--- | :--- | :--- |
| `entity_id` | String | e.g. `faction:bracer_guild` |
| `name_en` | String | |
| `name_ja` | String | |
| `org_type` | String | guild, government, criminal, military, religious |
| `headquarters` | Page | Linked Place page |
| `founding_arc` | String | Arc in which first established or referenced |
| `spoiler_band` | Integer | |

**Template**: `Template:Infobox Organization`
**Form**: `Form:Organization`
**Module**: `Module:Infobox/Organization`

---

### 4.4 Event

**Cargo table**: `cargo_events`

| Field | Cargo Type | Notes |
| :--- | :--- | :--- |
| `entity_id` | String | e.g. `event:orbal_revolution` |
| `name_en` | String | |
| `arc` | String | Arc in which event occurs |
| `chronology_position` | String | Relative ordering in series timeline |
| `involved_entities` | List (Page) | Linked Character, Organization, Place pages |
| `spoiler_band` | Integer | |

**Template**: `Template:Infobox Event`
**Form**: `Form:Event`
**Module**: `Module:Infobox/Event`

---

### 4.5 Concept

**Cargo table**: `cargo_concepts`

| Field | Cargo Type | Notes |
| :--- | :--- | :--- |
| `entity_id` | String | e.g. `concept:septium`, `item:orbment` |
| `name_en` | String | |
| `name_ja` | String | |
| `concept_type` | String | technology, artifact, magic_system, lore_term |
| `domain` | String | Thematic/worldbuilding domain |
| `spoiler_band` | Integer | |

**Template**: `Template:Infobox Concept`
**Form**: `Form:Concept`
**Module**: `Module:Infobox/Concept`

---

### 4.6 Media

**Cargo table**: `cargo_media`

| Field | Cargo Type | Notes |
| :--- | :--- | :--- |
| `media_id` | String | e.g. `media:sky_fc` |
| `title_en` | String | Canonical English title |
| `title_ja` | String | Japanese title |
| `media_type` | String | game, anime, manga, drama_cd, side_story |
| `arc` | String | Narrative arc |
| `release_year` | Integer | Year of original JP release |
| `spoiler_band` | Integer | |
| `platform` | List (String) | Platforms released on |

**Template**: `Template:Infobox Media`
**Form**: `Form:Media`
**Module**: `Module:Infobox/Media`

---

## 5. Scribunto Module Architecture

Each infobox module follows the same pattern:

```lua
-- Module:Infobox/Character (example structure)
local p = {}

function p.render(frame)
    local args = frame:getParent().args
    -- Read Cargo data for this page
    -- Apply spoiler_band check
    -- Render structured infobox HTML
    -- Return wikitext
end

return p
```

Modules handle:
- Cargo data retrieval for the current page
- Spoiler-aware rendering (Band 100 fields suppressed in standard view)
- Cross-links to related entity pages
- Chronology box rendering for characters with multi-arc appearances
- Relationship summaries (members of organization, appearances in media)

---

## 6. Page Forms Structure

Each form is divided into two sections:

**Section 1: Metadata** (Cargo-stored, form-validated)
- All structured fields from the Cargo table definition
- Dropdowns for enumerated types (media_type, org_type, etc.)
- Integer validation for spoiler_band (must be 10, 14, 20, 22, 40–55, 65, 70, 75, 80, or 100)
- Required field: `entity_id` (must match `^(char|loc|faction|event|concept|item|media|staff):.+`)

**Section 2: Atlas Prose** (free wikitext)
- Full wikitext editor for long-form explanatory content
- Section headers pre-populated by the form template per page class
- No validation beyond minimum length warning (stub detection via AbuseFilter)

---

## 7. Draft and Approved Revs Workflow

The `Draft:` namespace and Approved Revs are separate mechanisms with distinct roles. They are used in sequence, not interchangeably.

### Namespace roles

| Namespace | Purpose | Approved Revs active? |
| :--- | :--- | :--- |
| `Draft:` | Working Atlas entries not yet ready for stable reference | No — drafts are inherently unstable |
| `Main` | Atlas entries intended as stable reference | Yes — Approved Revs governs here |

### Promotion path

```
Draft:PageName  →  (curator decision)  →  Main/PageName  →  (Approved Revs)  →  approved revision
```

1. **Draft stage** — A new Atlas entry is created under `Draft:PageName`. Cargo-backed Metadata can be filled in here but should be treated as provisional. The page is not yet a stable reference.
2. **Promotion to Main** — When the Atlas prose is complete and sources are grounded, the curator moves the page to `Main/PageName` (via page move or manual recreation). This is a deliberate editorial decision.
3. **Approved Revs in Main** — The promoted page starts as unapproved in Main. The curator reviews and approves the revision. Only the approved revision is shown to standard readers.
4. **Subsequent edits** — Any edit to the Main page creates a new unapproved revision. The previous approved revision remains visible until the new one is approved.

### Cargo and stable references

Cargo-backed Metadata fields (infobox data) should be considered stable only once the Main page has an approved revision. Queries against Cargo tables will reflect whatever is currently stored, but cross-linked entry lists and relationship summaries should source from approved Main entries for publication-grade output.

### Lifecycle mapping

| Wiki state | Metadata lifecycle_registry equivalent |
| :--- | :--- |
| Draft: page | `raw` or `normalized` |
| Main, unapproved | `curated` (in progress) |
| Main, approved revision | `curated` (stable) / `export_ready` |

---

## 8. AbuseFilter Rules

| Rule | Action | Trigger |
| :--- | :--- | :--- |
| Missing Cargo template in Main | Warn + log | Page in namespace 0 without `{{Infobox` |
| Invalid spoiler_band value | Block | `spoiler_band` field value not in valid set |
| Stub Atlas prose | Warn | Atlas prose section under 100 characters |
| Namespace misuse | Block | Cargo declare template used in Main namespace directly (must use infobox wrapper) |
| entity_id format violation | Block | `entity_id` field does not match expected prefix pattern |

---

## 9. Phased Implementation

### Phase A — Core Install
- Install MediaWiki (latest LTS)
- Install all required extensions
- Configure custom namespaces in `LocalSettings.php`
- Configure Approved Revs and AbuseFilter base settings

### Phase B — Schema and Cargo Tables
- Define Page Schemas for all 6 page classes
- Run Cargo table creation for all 6 classes
- Verify Cargo storage and query via `Special:CargoTables`

### Phase C — Page Forms (Character + Media first)
- Build `Form:Character` with all Metadata fields and Atlas prose section
- Build `Form:Media`
- Test page creation round-trip for both classes
- Remaining 4 forms follow

### Phase D — Scribunto Infoboxes
- Build `Module:Infobox/Character` (highest priority)
- Build `Module:Infobox/Media`
- Build remaining 4 modules
- Wire TemplateData to all 6 infobox templates

### Phase E — Approved Revs + AbuseFilter
- Enable Approved Revs across Main and Draft namespaces
- Implement AbuseFilter rules from Section 8
- Test approval cycle end-to-end

### Phase F — Atlas Seeding
- Create initial Atlas entries for Sky and Crossbell protagonists
- Use Form:Character for creation
- Complete curation pass and approve first stable entries

### Phase G — External Data Bridge (optional)
- Configure External Data to surface `trails.db` export views inside the wiki
- Candidate: media catalog table on the main navigation page
- Candidate: character count / coverage statistics page

---

## 10. LocalSettings.php Notes

Required additions:

```php
// Custom namespaces
define('NS_METADATA', 3000);
define('NS_METADATA_TALK', 3001);
define('NS_DRAFT', 3002);
define('NS_DRAFT_TALK', 3003);

$wgExtraNamespaces[NS_METADATA] = 'Metadata';
$wgExtraNamespaces[NS_METADATA_TALK] = 'Metadata_talk';
$wgExtraNamespaces[NS_DRAFT] = 'Draft';
$wgExtraNamespaces[NS_DRAFT_TALK] = 'Draft_talk';

// Cargo
wfLoadExtension('Cargo');

// Page Forms
wfLoadExtension('PageForms');

// Page Schemas
wfLoadExtension('PageSchemas');

// Scribunto
wfLoadExtension('Scribunto');
$wgScribuntoDefaultEngine = 'luastandalone';

// Approved Revs
wfLoadExtension('ApprovedRevs');
$egApprovedRevsEnabledNamespaces = [NS_MAIN, NS_DRAFT];

// AbuseFilter
wfLoadExtension('AbuseFilter');

// TemplateData
wfLoadExtension('TemplateData');

// External Data (optional)
// wfLoadExtension('ExternalData');
```
