# Trails Database: Atlas Generation Specification

**Companion to:** `docs/atlas.md` (layer definition), `docs/schema.md` (Metadata schema)

This document specifies the internal system for generating Atlas entries from Metadata and curated prose slots. It is implementation-oriented: precise enough to drive MediaWiki templates, Cargo tables, and curation tooling.

---

## 1. Generation Model

### Core Principle

```
metadata + prose slots → canonical Atlas rendering
```

An Atlas entry is not written from scratch. It is rendered from two inputs:

1. **Metadata** — structured fields from `entity_registry`, `appearance_registry`, `relationship_registry`, `media_registry`, and `lifecycle_registry`. These fields are authoritative and machine-readable.
2. **Prose slots** — curated sections written by the curator. Each slot occupies a defined structural position in the entry. Slots are written once and occupy the same position every time the entry renders.

The section structure is not invented per entry. It is determined by the entity class. The curator's job is to fill prose slots — not to design article architecture.

---

### Slot Types

Each section in an Atlas entry is one of three slot types:

| Slot Type | Source | Curator role |
| :--- | :--- | :--- |
| **Auto** | Derived directly from Metadata. Rendered by Scribunto/template logic. | None — do not touch |
| **Prose-required** | Written by the curator. Cannot be auto-generated. The core explanatory content. | Write it |
| **Conditional** | Rendered only when supporting Metadata or curator prose exists. Suppressed otherwise. | Write if applicable; leave blank to suppress |

Auto slots include: lead identity line, infobox fields, appearances list (from `appearance_registry`), affiliation cross-references (from `relationship_registry`).

Prose-required slots include: Continuity, Identity & Role prose body, Course & Outcome (events), Function (concepts).

Conditional slots include: Personality & Behavioral Structure (characters), Abilities (characters with defined combat roles), Production Notes (media), Key Members prose (organizations), Associated Entities (places).

---

### Section Presence Rules

Section presence is determined by entity class plus field/slot availability. The system never renders empty sections. If a prose-required slot is empty, the section heading does not appear. If optional Metadata is absent, the corresponding auto section is suppressed.

```
section_present = (slot_type == "prose-required" AND slot_filled)
               OR (slot_type == "auto" AND metadata_field_not_null)
               OR (slot_type == "conditional" AND (metadata_field_not_null OR slot_filled))
```

---

### Graceful Degradation

| Condition | Behavior |
| :--- | :--- |
| Optional prose slot is empty | Section suppressed. No heading rendered. |
| Required prose slot is empty | Section rendered as `[stub — awaiting curator]` marker. Entry cannot be promoted past `normalized`. |
| Optional Metadata field is null | Section suppressed or fallback text: `not documented` |
| Required Metadata field is null | Entry flagged in `lifecycle_registry` as incomplete. Infobox shows `—`. |
| entity has appearances but appearance_registry is empty | Appearances section renders: `No appearances registered.` |
| Spoiler band ceiling reached | All sections at or above that band are suppressed from the rendered view. Master entry is unchanged. |

---

### Master Entry vs. Render-Time View

The Atlas entry is the **master form**. It contains all content across all arcs, including high-band content.

Spoiler suppression is a **render-time operation**: a viewer's declared band ceiling is applied when the entry is displayed. It does not affect the underlying Atlas page or its stored structure.

This means:
- A character with content across Sky (band 10), Crossbell (band 20), and Erebonia (band 40–55) has one Atlas entry
- A Sky-only viewer sees that entry truncated at band 10
- The entry itself is never fragmented or duplicated by spoiler band

---

## 2. Canonical Section Models by Entity Class

### 2.1 Character

**Lead sentence pattern:**
```
{name} is [the protagonist of / a {role} in / a {role} operating in] the {arc} arc[, {one-line identity extension}].
```

| # | Section | Slot type | Required | Spoiler truncation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Lead | Auto + prose preamble | Yes | Lead must not exceed page spoiler_band |
| 2 | Identity & Role | Prose-required | Yes | No — identity/role content is not spoiler-banded by default |
| 3 | Chronological History | Prose-required | Yes if multi-arc | Arc sections truncated at their respective bands |
| 4 | Personality & Behavioral Structure | Conditional | No | Suppress above band if behavior changes across arcs |
| 5 | Affiliations & Relationships | Auto + conditional prose | Yes | Suppress high-band affiliations |
| 6 | Abilities / Combat Profile | Conditional | No | Include only if character has defined combat role or class |
| 7 | Appearances | Auto | Yes | Suppress entries above band ceiling |
| 8 | Continuity Notes | Conditional | No | May contain high-band content; truncate accordingly |
| 9 | Sources | Auto | Yes | None |

**Chronology rendering rules:**
- Each arc in which the character appears with meaningful development gets its own subsection heading
- Heading format: `{arc name} — {game title}` (e.g., `Sky Arc — Trails in the Sky SC`)
- Arcs are ordered chronologically, not by release date
- Cross-arc continuity notes (how the character is referenced in arcs where they do not appear) go in Continuity Notes, not in Chronology

**Affiliation rendering rules:**
- Primary affiliation (from `relationship_registry` where `relationship_type = 'affiliation'`) renders as: `Member of {org_name}`
- Historical affiliations (changed across arcs) list in order with arc marker: `[Sky] Bracers Guild → [Erebonia] Independent Contractor`
- Relationship cross-references are linked by entity_id, not prose-described

**Class-specific notes:**
- Separate identity (what the character structurally is) from history (what happens to them)
- Personality section must not drift into character analysis; it describes behavioral patterns with factual basis
- Abilities section covers class, combat style, and notable skills; no power-scaling language

---

### 2.2 Place

**Lead sentence pattern:**
```
{name} is [a / the] {place_type} [located / situated] in {region/nation}[, {one-line functional role in the series}].
```

| # | Section | Slot type | Required | Spoiler truncation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Lead | Auto + prose preamble | Yes | — |
| 2 | Geographic & Political Identity | Prose-required | Yes | — |
| 3 | Historical Context | Conditional | No | May span bands |
| 4 | Role in the Series | Prose-required | Yes | Truncate if role shifts after band threshold |
| 5 | Associated People, Institutions & Events | Auto + conditional | No | Suppress high-band associations |
| 6 | Appearances | Auto | Yes | Suppress above band |
| 7 | Continuity Notes | Conditional | No | — |
| 8 | Sources | Auto | Yes | — |

**Chronology rendering rules:**
- Places do not have personal chronologies, but if a place's status or role changes across arcs, use arc-headed subsections within "Role in the Series"
- Destroyed, occupied, or renamed places should have this noted with arc marker

**Affiliation rendering rules:**
- Nation and governing body are rendered from Metadata (nation, controlling_faction fields)
- If control changes across arcs, use arc markers in the Geographic & Political Identity section

---

### 2.3 Organization

**Lead sentence pattern:**
```
{name} is [a / the] {org_type} [operating across / based in] {scope/region}[, {one-line structural function}].
```

| # | Section | Slot type | Required | Spoiler truncation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Lead | Auto + prose preamble | Yes | — |
| 2 | Structure & Function | Prose-required | Yes | — |
| 3 | Operational History | Prose-required | Yes if multi-arc | Truncate high-band arcs |
| 4 | Key Members | Auto (cross-references) | No | Suppress high-band members |
| 5 | Appearances | Auto | Yes | Suppress above band |
| 6 | Continuity Notes | Conditional | No | — |
| 7 | Sources | Auto | Yes | — |

**Chronology rendering rules:**
- Use arc-headed subsections within Operational History for organizations with distinct arc roles
- Org dissolution, reorganization, or revelation of hidden purpose requires its own arc subsection

**Affiliation rendering rules:**
- Key Members is cross-reference only: linked entity names with brief role description (1 line max)
- No full prose biography for members in this section — link to their Character entry

**Class-specific notes:**
- "Structure & Function" should address chain of command, membership type (guild/military/criminal/religious), and operational jurisdiction
- Do not editorialize about the organization's morality; describe function and continuity role

---

### 2.4 Event

**Lead sentence pattern:**
```
{name} [is / was] {a / the} {event characterization} [occurring / that occurred] [during / at the end of] the {arc} arc[, {one-line consequence statement}].
```

| # | Section | Slot type | Required | Spoiler truncation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Lead | Auto + prose preamble | Yes | Lead must not exceed event spoiler_band |
| 2 | Background | Prose-required | Yes | — |
| 3 | Course & Outcome | Prose-required | Yes | Truncate if event is above viewer band |
| 4 | Continuity Impact | Prose-required | Yes | Truncate high-band downstream effects |
| 5 | Involved Entities | Auto | No | Suppress high-band participants |
| 6 | Appearances | Auto | Yes | — |
| 7 | Sources | Auto | Yes | — |

**Chronology rendering rules:**
- Events with multiple phases may use subheadings within Course & Outcome
- Event chronology_position (from Metadata) determines where the entry sits in cross-linked timeline views

**Class-specific notes:**
- "Course & Outcome" describes what happened; "Continuity Impact" describes what it triggered or enabled afterward
- Events that span multiple games (e.g., the Great War) may use arc-headed subsections in both sections
- Involved Entities renders as a linked list by entity class: Characters, Organizations, Places

---

### 2.5 Concept

**Lead sentence pattern:**
```
{name} is [a / the] {concept_type} [within / operating in] {domain}[, {one-line functional description}].
```

| # | Section | Slot type | Required | Spoiler truncation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Lead | Auto + prose preamble | Yes | — |
| 2 | Function | Prose-required | Yes | — |
| 3 | Continuity | Prose-required | No | Truncate if concept's nature is revealed late |
| 4 | Related Concepts | Auto + conditional | No | — |
| 5 | Appearances | Auto | Yes | — |
| 6 | Sources | Auto | Yes | — |

**Class-specific notes:**
- Concepts include technologies (ARCUS, Orbal Gear), artifact categories (Divine Knights), magic systems (Arts, Craft), and lore terms with worldbuilding weight
- "Function" must describe mechanical or worldbuilding operation, not narrative significance
- Continuity section covers where the concept is introduced, expanded, or redefined across arcs

---

### 2.6 Media

**Lead sentence pattern:**
```
{title_en} is [a / an] {media_type} [released in {release_year}][, the {ordinal} entry in the {arc} arc[, {one-line continuity position statement}]].
```

| # | Section | Slot type | Required | Spoiler truncation |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Lead | Auto | Yes | — |
| 2 | Synopsis | Prose-required | Yes | Late-game synopsis truncated at entry spoiler_band |
| 3 | Continuity Position | Prose-required | Yes | — |
| 4 | Playable Cast / Key Characters | Auto | No | — |
| 5 | Production Notes | Auto | No | — |
| 6 | Sources | Auto | Yes | — |

**Class-specific notes:**
- Synopsis covers narrative scope, not a full plot summary; it should orient the reader, not recount every beat
- Production Notes render from Metadata (developer, publisher, platform, release date, staff credits from media_registry)
- Playable Cast is a cross-reference list by entity_id only

---

## 3. Style Guide

### Sentence Style

Atlas prose uses compressed, load-bearing sentences. Every sentence must carry factual or structural information. Setup sentences that only restate what the next sentence proves are cut.

**Preferred:**
> Estelle Bright is the protagonist of the *Sky* arc. She operates as a junior Bracer in the Liberl Kingdom, initially under the mentorship of her father Cassius Bright.

**Rejected:**
> Estelle Bright is a very important character in the Trails series. She appears in the first three games of the franchise and has many fans because of her cheerful personality.

Sentences should be declarative. Avoid subordinate-clause chains that bury the operative fact.

---

### Paragraph Density

- One fact cluster per paragraph
- 3–6 sentences per paragraph; compress rather than pad
- No filler transition sentences ("In addition to this...", "It is also worth noting that...")
- Each paragraph must advance the section's argument or coverage; if it does not, cut it

---

### Tense and Aspect

| Content | Tense |
| :--- | :--- |
| Character identity, role, continuity placement | Present: "Estelle Bright **is** the protagonist..." |
| Completed in-world events | Past: "The Gospel Plan **targeted** the Sept-Terrion of Space." |
| Organizations and their function | Present: "The Bracer Guild **operates** across Zemuria..." |
| Media entries (what a game covers) | Present: "The game **follows** Estelle..." |
| Production facts (release, developer) | Past: "Falcom **released** *Sky FC* in 2004." |

Do not mix tense within a section except to mark temporal shift.

---

### Naming Rules

**Games and arcs:**

| Preferred | Do not use |
| :--- | :--- |
| *Trails in the Sky FC* | Sky 1, FC, first game |
| *Trails in the Sky SC* | Sky 2, SC |
| *Trails in the Sky the 3rd* | 3rd, Sky 3rd (no article) |
| *Trails from Zero* | Zero no Kiseki, Zero |
| *Trails to Azure* | Ao no Kiseki, Azure |
| *Trails of Cold Steel* | CS1, Cold Steel 1 |
| *Trails into Reverie* | Reverie alone as game title |
| *Trails through Daybreak* | Daybreak 1, Kuro |
| *Trails through Daybreak II* | Daybreak 2 |

Arc names (not game titles) may be abbreviated after first use: **Sky arc**, **Crossbell arc**, **Erebonia arc**, **Reverie arc**, **Calvard arc**.

**Entity names:**
- Use `english_display_name` from `entity_registry` as the canonical form
- Japanese names (`japanese_name`) appear in the infobox and aliases field; they do not appear in Atlas prose unless the EN name is unavailable or the Japanese form is under direct discussion
- Honorifics are not reproduced in Atlas prose unless they are part of a formal title

**Aliases and alternate forms:**
- List in the infobox / Metadata section, not in prose body
- Exception: if the alias is structurally important (e.g., a character's assumed name that drives plot), it may be introduced in prose with a brief explanation

---

### Summarizing Multi-Arc Development

- Use arc-headed subsections, not compressed mega-paragraphs
- Do not collapse three arcs of character development into one paragraph to save space — structure it
- What to keep: structural changes (affiliation shifts, role changes, revealed identity), key operational events, cross-arc connections
- What to cut: scene-by-scene recounting, emotional color commentary, play-by-play of dungeon events

A useful test: if the sentence could be cut without losing a structural fact, cut it.

---

### Borrowing from Japanese Wikipedia

Borrow the following structural habits:
- Separate chronology from identity (character history and character role are distinct sections)
- Group characters by faction or arc affiliation in lists, not alphabetically
- Dense paragraph logic: state the role, state the history, state the continuity impact
- Treat the series as a single continuous narrative, not a collection of separate games
- Use franchise-scale structure for Media entries (situating a game within the arc, within the series)

Do not copy:
- Exact section names from JA Wikipedia
- JA article-opening conventions
- Wording or phrasing from JA source text

---

### Calibrating Against Curator English Prose

The target English voice is the curator's own encyclopedic style, as evidenced in the specimen entries in `docs/atlas.md`. Markers of that style:

- Identity-first leads that identify structural position before history
- Article-level hierarchy: strong section logic, no flat walls of prose
- Directness: no throat-clearing, no hedging without cause
- Neutral but not affectless: factual density with readability preserved
- Compression: one sentence where three could be written, when the one carries the same load

---

### Avoidance Rules

The following are forbidden in Atlas prose:

| Category | Forbidden forms |
| :--- | :--- |
| Fan-wiki enthusiasm | "beloved character," "fan-favorite," "arguably the best" |
| Marketing tone | "one of the most complex antagonists in the series," "a masterclass in writing" |
| Assistant phrasing | "It is worth noting that...", "This character demonstrates...", "We see that..." |
| Filler transitions | "In addition," "Furthermore," "It is also important to note that" |
| Player-perspective writing | "you first meet," "players encounter," "the game introduces us to" |
| Superlatives without structural grounding | "the strongest," "the most powerful," "the most important" |
| Vague importance language | "a major figure," "a key player," "incredibly significant" |
| Unattributed speculation | "many believe that," "it seems that," "fans theorize" |

---

## 4. Schema-to-Prose Rendering Contract

### 4.1 Character

| Metadata field | Rendered in | Required | Absent behavior |
| :--- | :--- | :--- | :--- |
| `entity_id` | Cargo anchor; page identity | Yes | Entry cannot exist without it |
| `english_display_name` | Lead, infobox title | Yes | Entry flagged as incomplete |
| `japanese_name` | Infobox (aliases row) | No | Infobox row suppressed |
| `aliases` | Infobox (aliases row) | No | Row suppressed |
| `arc_first_appearance` | Infobox; auto-rendered in Lead support | No | Omit from Lead; infobox shows `—` |
| `spoiler_band` | Render-time suppression ceiling | Yes | Default to band 100 if null |
| `affiliation` (relationship_registry) | Auto-rendered in Affiliations section | No | Section suppressed if no affiliation records |
| `voice_jp` | Infobox | No | Row suppressed |
| `voice_en` | Infobox | No | Row suppressed |
| Lead prose (prose slot) | Section 1 body | Yes (prose-required) | `[stub — awaiting curator]` |
| Identity & Role prose (prose slot) | Section 2 body | Yes (prose-required) | `[stub — awaiting curator]` |
| Chronological History prose (prose slot) | Section 3 body | Conditional | Suppressed if empty |
| Personality prose (prose slot) | Section 4 body | Conditional | Suppressed if empty |
| Abilities prose (prose slot) | Section 6 body | Conditional | Suppressed if empty |
| Continuity Notes prose (prose slot) | Section 8 body | Conditional | Suppressed if empty |
| Appearances (appearance_registry rows) | Section 7, auto-list | Yes | Renders `No appearances registered.` |
| Source IDs (source_registry) | Section 9, auto-list | Yes | Renders `No sources registered.` |

---

### 4.2 Place

| Metadata field | Rendered in | Required | Absent behavior |
| :--- | :--- | :--- | :--- |
| `entity_id` | Cargo anchor | Yes | Entry cannot exist |
| `english_display_name` | Lead, infobox | Yes | Entry flagged |
| `japanese_name` | Infobox | No | Row suppressed |
| `region` | Infobox; Lead auto-support | No | Lead uses `nation` fallback |
| `nation` | Infobox | No | Row suppressed |
| `place_type` | Infobox; Lead | No | Lead uses `location` as fallback type |
| `first_appearance` | Infobox | No | Row suppressed |
| `spoiler_band` | Render-time ceiling | Yes | Default to 100 |
| Geographic & Political Identity prose | Section 2 | Yes (prose-required) | `[stub]` |
| Historical Context prose | Section 3 | Conditional | Suppressed |
| Role in the Series prose | Section 4 | Yes (prose-required) | `[stub]` |
| Associated entities (relationship_registry) | Section 5, auto-list | No | Section suppressed |
| Appearances | Section 6, auto | Yes | `No appearances registered.` |
| Sources | Section 7, auto | Yes | `No sources registered.` |

---

### 4.3 Organization

| Metadata field | Rendered in | Required | Absent behavior |
| :--- | :--- | :--- | :--- |
| `entity_id` | Cargo anchor | Yes | Entry cannot exist |
| `english_display_name` | Lead, infobox | Yes | Entry flagged |
| `japanese_name` | Infobox | No | Row suppressed |
| `org_type` | Infobox; Lead | No | Lead uses `organization` as fallback |
| `headquarters` | Infobox | No | Row suppressed |
| `founding_arc` | Infobox | No | Row suppressed |
| `spoiler_band` | Render-time ceiling | Yes | Default to 100 |
| Structure & Function prose | Section 2 | Yes (prose-required) | `[stub]` |
| Operational History prose | Section 3 | Conditional | Suppressed |
| Key Members (relationship_registry, membership type) | Section 4, auto cross-ref list | No | Section suppressed |
| Appearances | Section 5, auto | Yes | `No appearances registered.` |
| Sources | Section 7, auto | Yes | `No sources registered.` |

---

### 4.4 Event

| Metadata field | Rendered in | Required | Absent behavior |
| :--- | :--- | :--- | :--- |
| `entity_id` | Cargo anchor | Yes | Entry cannot exist |
| `english_display_name` | Lead, infobox | Yes | Entry flagged |
| `arc` | Infobox; Lead | No | Lead uses `at an unspecified point in the series` |
| `chronology_position` | Timeline cross-link | No | Omit from timeline index |
| `involved_entities` | Section 5, auto cross-ref | No | Section suppressed |
| `spoiler_band` | Render-time ceiling; Lead suppressed if above ceiling | Yes | Default to 100 |
| Background prose | Section 2 | Yes (prose-required) | `[stub]` |
| Course & Outcome prose | Section 3 | Yes (prose-required) | `[stub]` |
| Continuity Impact prose | Section 4 | Yes (prose-required) | `[stub]` |
| Appearances | Section 6, auto | Yes | `No appearances registered.` |
| Sources | Section 7, auto | Yes | `No sources registered.` |

---

### 4.5 Concept

| Metadata field | Rendered in | Required | Absent behavior |
| :--- | :--- | :--- | :--- |
| `entity_id` | Cargo anchor | Yes | Entry cannot exist |
| `english_display_name` | Lead, infobox | Yes | Entry flagged |
| `concept_type` | Infobox; Lead | No | Lead uses `concept` |
| `domain` | Infobox | No | Row suppressed |
| `spoiler_band` | Render-time ceiling | Yes | Default to 100 |
| Function prose | Section 2 | Yes (prose-required) | `[stub]` |
| Continuity prose | Section 3 | Conditional | Suppressed |
| Related Concepts (relationship_registry) | Section 4, auto cross-ref | No | Section suppressed |
| Appearances | Section 5, auto | Yes | `No appearances registered.` |
| Sources | Section 6, auto | Yes | `No sources registered.` |

---

### 4.6 Media

| Metadata field | Rendered in | Required | Absent behavior |
| :--- | :--- | :--- | :--- |
| `media_id` | Cargo anchor | Yes | Entry cannot exist |
| `title_en` | Lead, infobox | Yes | Entry flagged |
| `title_ja` | Infobox | No | Row suppressed |
| `media_type` | Infobox; Lead | Yes | Lead uses `media entry` as fallback |
| `arc` | Infobox; Lead | No | Omit from Lead |
| `release_year` | Infobox; Lead | No | Omit from Lead |
| `platform` | Infobox | No | Row suppressed |
| `spoiler_band` | Render-time ceiling | Yes | Default to 100 |
| Synopsis prose | Section 2 | Yes (prose-required) | `[stub]` |
| Continuity Position prose | Section 3 | Yes (prose-required) | `[stub]` |
| Playable Cast (relationship_registry, playable type) | Section 4, auto cross-ref | No | Section suppressed |
| Production Notes (media_registry: developer, publisher, staff) | Section 5, auto | No | Section suppressed |
| Sources | Section 6, auto | Yes | `No sources registered.` |

---

## 5. Example Stubs

The stubs below demonstrate the generation model. Each stub:
- follows the section order defined for its entity class
- marks auto-rendered content with `[AUTO]`
- marks prose slots with their content, or with `[PROSE SLOT — stub]` where placeholder

---

### 5.1 Character: Estelle Bright

---

**Estelle Bright**

[AUTO — infobox: entity_id=estelle_bright, arc_first_appearance=Sky FC, spoiler_band=14, voice_jp=Kanae Itō, affiliation=Bracer Guild (Liberl), entity_type=char]

**Lead**

Estelle Bright is the protagonist of the *Sky* arc. She operates as a junior Bracer in the Liberl Kingdom, initially under the supervision of her father Cassius Bright, and later as a licensed Bracer in her own right.

---

**Identity & Role**

Estelle Bright's structural function in the *Sky* arc is dual: she is both the operational center of the arc's case-file structure and the continuity bridge that connects Liberl's internal affairs to the larger series conflict. Her affiliation with the Bracer Guild is not incidental — it defines the jurisdictional and moral framework through which she engages every problem the arc presents.

She is a licensed Bracer by the events of *Trails in the Sky SC*, operating from the Liberl Guild branch. She remains a recurring operational contact in subsequent arcs, most significantly during the *Crossbell* arc and as a background presence in the *Erebonia* arc.

---

**Chronological History**

**Sky Arc — *Trails in the Sky FC***

[PROSE SLOT — stub: Events of FC, missing persons case, relationship with Joshua, the Bose and Zeiss chapters, confrontation with the Black Orbment]

**Sky Arc — *Trails in the Sky SC***

[PROSE SLOT — stub: The Gospel Plan, Ouroboros, Cassius's absence, Estelle's search for Joshua, the Sept-Terrion of Space, the Liber Ark]

**Sky Arc — *Trails in the Sky the 3rd***

[PROSE SLOT — stub: Kevin Graham's arc, Phantasma, Estelle's supporting role in the Star Door structure]

---

**Affiliations & Relationships**

[AUTO — from relationship_registry:
- Bracer Guild (Liberl) — Member
- Joshua Bright — Bond (arc partner, family)
- Cassius Bright — Parent]

[PROSE SLOT — optional relationship prose: brief characterization of the Joshua Bright relationship's narrative function]

---

**Appearances**

[AUTO — from appearance_registry:
- *Trails in the Sky FC* (Sky arc, spoiler_band=10)
- *Trails in the Sky SC* (Sky arc, spoiler_band=12)
- *Trails in the Sky the 3rd* (Sky arc, spoiler_band=14)
- *Trails from Zero* (Crossbell arc, spoiler_band=20, supporting)
- *Trails to Azure* (Crossbell arc, spoiler_band=22, supporting)
- *Trails into Reverie* (Reverie arc, spoiler_band=65, supporting)]

---

**Sources**

[AUTO — from source_registry: wiki:kiseki_fandom (trust tier 2), wiki:ja_wikipedia_characters (trust tier 1)]

---

### 5.2 Place: Crossbell City

---

**Crossbell City**

[AUTO — infobox: entity_id=crossbell_city, place_type=city, nation=Crossbell State, region=Crossbell, spoiler_band=22, first_appearance=Trails from Zero]

**Lead**

Crossbell City is the administrative and commercial capital of the Crossbell State, a small autonomous territory situated between the Erebonian Empire and the Calvard Republic. It functions as the primary setting of the *Crossbell* arc and as the geopolitical flashpoint around which both the *Zero* and *Azure* arcs are structured.

---

**Geographic & Political Identity**

Crossbell State's position between two major continental powers makes Crossbell City the site of continuous imperial-republican tension. The city's formal governance structure includes the Crossbell Police Department and a locally elected government, but its political surface conceals both entrenched criminal networks and foreign intelligence operations.

The city is commercially significant: it serves as a major trade routing point for goods moving between Erebonia and Calvard, and this economic leverage underlies most of the geopolitical disputes that define the *Crossbell* arc.

---

**Role in the Series**

Crossbell City's narrative function in the *Crossbell* arc is total: the entire arc is structured around the city's political autonomy, its organized crime problem, and Erebonia's eventual annexation of the State.

[PROSE SLOT — stub: How the city appears and is referenced in the Erebonia and Reverie arcs following annexation and liberation]

---

**Appearances**

[AUTO — from appearance_registry:
- *Trails from Zero* (Crossbell arc, spoiler_band=20, primary setting)
- *Trails to Azure* (Crossbell arc, spoiler_band=22, primary setting)
- *Trails of Cold Steel II* (Erebonia arc, spoiler_band=50, referenced)
- *Trails of Cold Steel III* (Erebonia arc, spoiler_band=53, partial)
- *Trails into Reverie* (Reverie arc, spoiler_band=65, primary setting)]

---

**Sources**

[AUTO — wiki:kiseki_fandom (trust tier 2), wiki:ja_wikipedia_series (trust tier 1)]

---

### 5.3 Organization: Bracer Guild

---

**Bracer Guild**

[AUTO — infobox: entity_id=bracer_guild, org_type=mutual-aid and security organization, spoiler_band=10, headquarters=various (transnational), first_appearance=Trails in the Sky FC]

**Lead**

The Bracer Guild is a transnational mutual-aid and security organization operating across Zemuria. It functions as the primary civilian contractor for non-military, non-police threat resolution, and constitutes one of the series' most persistent institutional presences across arcs.

---

**Structure & Function**

The Bracer Guild operates through a network of branch offices distributed across the continent, each affiliated with a local political authority but not controlled by any single nation. Individual Bracers hold licensed rank (Junior Bracer through S-rank) and accept commissions through the local branch.

The Guild's operational domain spans monster suppression, escort work, missing-persons investigation, and civic crisis response. Its charter prohibits involvement in military or political affairs above a defined threshold, a restriction that defines the jurisdictional boundaries — and the frequent violations of those boundaries — that drive much of the arc-level conflict it is caught in.

---

**Operational History**

[PROSE SLOT — stub: Sky arc — Guild's role in Liberl, its institutional relationship to the Liberl Royal Army, and the Sky arc events that stress that relationship]

[PROSE SLOT — stub: Crossbell arc — Crossbell branch structure, its tension with CPD, Ouroboros]

[PROSE SLOT — stub: Erebonia arc — Guild's politically constrained position during the Civil War, Rean's contacts]

---

**Key Members**

[AUTO — from relationship_registry (membership):
- Estelle Bright (Liberl branch, protagonist)
- Cassius Bright (Liberl branch, S-rank)
- Olivier Lenheim (Erebonia, S-rank)
- [additional entries from relationship_registry]]

---

**Appearances**

[AUTO — from appearance_registry: present across Sky, Crossbell, Erebonia, Reverie, Calvard arcs]

---

**Sources**

[AUTO — wiki:kiseki_fandom (trust tier 2), wiki:ja_wikipedia_series (trust tier 1)]

---

### 5.4 Event: Liber Ark Incident

---

**Liber Ark Incident**

[AUTO — infobox: entity_id=liber_ark_incident, arc=Sky, chronology_position=S.1202, spoiler_band=12, involved_entities=Estelle Bright, Joshua Bright, Cassius Bright, Ouroboros, Weissmann, Liber Ark]

**Lead**

The Liber Ark Incident is the climactic event of the *Sky* arc, occurring in S.1202 of the Zemurian calendar. It marks the activation of the Gospel Plan by Ouroboros, the ascent of the ancient city of Liber Ark above Liberl, and the direct confrontation with Weissmann that concludes *Trails in the Sky SC*.

---

**Background**

[PROSE SLOT — stub: The Gospel Plan's structure, Weissmann's role in it, the Sept-Terrion of Space as the target, the prior events in FC that established the operational groundwork]

---

**Course & Outcome**

[PROSE SLOT — stub: The ascent of Liber Ark, the activation sequence, Estelle and the party's infiltration, the confrontation with Weissmann, the outcome of the Gospel Plan]

---

**Continuity Impact**

The Liber Ark Incident establishes Ouroboros as a cross-arc antagonist operating at a scale beyond any single national threat. Its outcome introduces the Anguis structure of Ouroboros, the concept of Sept-Terrion as the target of the Orpheus Final Plan, and positions Cassius Bright's return as a stabilizing factor for the series' cross-arc political structure.

[PROSE SLOT — stub: downstream references in Crossbell arc and Erebonia arc; how subsequent arcs treat the incident as historical context]

---

**Involved Entities**

[AUTO — from relationship_registry / involved_entities:
- Characters: Estelle Bright, Joshua Bright, Cassius Bright, Weissmann, Campanella
- Organizations: Ouroboros, Liberl Royal Army, Bracer Guild
- Places: Liber Ark, Liberl Kingdom]

---

**Appearances**

[AUTO — from appearance_registry:
- *Trails in the Sky SC* (Sky arc, spoiler_band=12, primary event)]

---

**Sources**

[AUTO — wiki:kiseki_fandom (trust tier 2), wiki:ja_wikipedia_series (trust tier 1), wiki:ja_wikipedia_timeline (trust tier 1)]

---

## 6. Integration Notes

### Relation to the Two-Layer Model

This spec is the operational bridge between Metadata and Atlas.

- **Metadata knows**: the structured facts — entity IDs, names, affiliations, appearances, spoiler bands, source provenance. All auto-rendered content in an Atlas entry derives from Metadata.
- **Atlas explains**: the prose slots — what a character means in the continuity, how an event changed the world, what an organization's structural role is. These slots cannot be auto-generated and require curator authorship.

The spec defines the interface between those two layers: which Metadata fields produce which rendered output, and which structural positions require curator prose.

---

### Lifecycle Progression

An Atlas entry moves through the following states in `lifecycle_registry`:

| State | Meaning for this spec |
| :--- | :--- |
| `raw` | Entity exists in Metadata. No Atlas prose slots filled. Auto sections can render; prose sections show `[stub]` markers. |
| `normalized` | Metadata fields are clean and complete. Entity relationships and appearances are registered. Atlas entry is structurally ready. |
| `curated` | Prose-required slots are filled and curator-reviewed. Entry meets the Source and Citation Contract in `docs/atlas.md`. Auto sections render fully. |
| `export_ready` | Entry has been approved in MediaWiki (Approved Revs) and is eligible for Export derivations. |

An entry cannot advance from `normalized` to `curated` with any prose-required slot unfilled. The system must enforce this gate.

---

### MediaWiki / Cargo / Page Forms / Scribunto Mapping

| Component | Role in this spec |
| :--- | :--- |
| **Cargo tables** | Store all auto-rendered Metadata: entity_id, names, affiliations, appearances, spoiler_band. Cargo is the Metadata side of the Atlas rendering pipeline. |
| **Page Forms** | Provide the structured editing interface. Form Section 1 = Metadata fields (Cargo-backed, validated). Form Section 2 = prose slots per section. The form ensures prose slots appear in the correct structural order. |
| **Scribunto (Lua)** | Renders the infobox and all auto-derived content by querying Cargo. The Lead sentence pattern is generated by the Scribunto infobox module from Metadata fields. |
| **Approved Revs** | The promotion gate from `curated` to `export_ready`. Only approved revisions are shown to standard readers. Unapproved edits remain visible to curators. |

The Scribunto module for each entity class should implement the Lead sentence pattern defined in Section 2 of this spec. This guarantees that Lead auto-rendering is consistent regardless of who is editing the page.

---

### Spoiler Suppression at Render Time

Spoiler suppression is a **rendering concern, not a schema concern**.

The master Atlas entry stores all content. At render time, the active viewer's spoiler band ceiling is applied. Any section with a band marker above the ceiling is:
- suppressed from output entirely (not shown as empty)
- not visible in the page's wikitext to standard readers

Sections that span multiple band levels (e.g., a Chronology section covering both Sky and Crossbell arcs) handle this via subsection-level band markers. The Sky subsection (band 10–14) renders for Sky-safe viewers; the Crossbell subsection (band 20–22) is suppressed.

The master Atlas page is never fragmented by spoiler band. One page exists per entity. Band suppression is an AbuseFilter + Scribunto operation applied at display time.

This preserves curatorial integrity: the complete Atlas entry is written once, structured once, and sourced once. Export views and MediaWiki views derive from the same master.

---

### Supporting Later Export

The slot model described in this spec is compatible with Export derivation without modification:

- Auto slots render from Cargo → Export queries Cargo tables directly
- Prose slots are stored as `curated_bio` chunks in `chunk_registry` → Export selects the relevant chunks
- Spoiler suppression at export time applies the same band ceiling logic as MediaWiki rendering

No schema changes are required to support export views at different band ceilings or in different formats (JSONL, Markdown, plain text). The slot structure is the export unit.
