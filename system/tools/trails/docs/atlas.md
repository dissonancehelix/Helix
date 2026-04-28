# Trails Database: The Atlas Layer

## 1. What the Atlas Is

The Atlas is the explanatory entry layer of the Trails Database. Its job is to explain — not to know. The Metadata layer knows what everything is. The Atlas explains what it means.

Atlas entries cover:
- who a character is, what role they play, and how they move through the continuity
- what a place is, how it functions in the world, and what it means to the series
- what an organization does, who controls it, and what its structural role is
- what an event is, how it changes the world, and what it triggers
- what a concept or technology is and how it operates within the series' worldbuilding
- how a media entry fits into the larger arc and what it contributes to the continuity

**The Atlas is not a wiki mirror.** It is not constrained by Wikipedia MOS size limits or Kiseki Wiki format conventions. It is richer, more structurally explicit, and more continuity-aware than any public resource. Smaller export views are generated from it — it is the master form.

**Atlas entries draw from Metadata. They are not Metadata.** An Atlas entry references entity IDs, source IDs, and spoiler bands from the Metadata layer. It does not replace them.

---

## 2. Page Classes

The Atlas organizes entries into six page classes:

| Class | Covers |
| :--- | :--- |
| **Character** | Named individuals — protagonists, antagonists, supporting cast, staff |
| **Place** | Cities, dungeons, landmarks, regions, nations |
| **Organization** | Guilds, governments, criminal factions, military bodies, religious orders |
| **Event** | Named in-world historical or narrative events |
| **Concept** | Technologies, artifacts, magic systems, lore terms, game mechanics with lore grounding |
| **Media** | Individual game titles, anime adaptations, manga, drama CDs, side stories |

---

## 3. Standard Page Structure

### Character
1. **Lead** — Identity statement. Who they are, what arc they anchor, what role they occupy.
2. **Identity & Role** — Occupation, affiliation, position within the world. Structural function.
3. **Continuity** — Arc-by-arc trajectory. What they do, what they know, what they reveal. Arc transitions explicitly marked.
4. **Relationships** — Connections to other characters, factions, and events. Typed where possible.
5. **Appearances** — Media entries by arc, in chronological order.
6. **Sources** — Source IDs grounding the entry. Trust tier noted where relevant.

### Place
1. **Lead** — What it is, where it sits, what function it serves.
2. **Geography & Structure** — Physical description, internal organization, surrounding regions.
3. **Political & Social Context** — Who controls it, what its role in the broader world is.
4. **Continuity** — How it appears and changes across arcs.
5. **Appearances** — Media entries featuring this location.
6. **Sources**

### Organization
1. **Lead** — What the organization is and what it does.
2. **Structure & Function** — Chain of command, operational domain, membership type.
3. **Continuity** — Arc-by-arc role. What the organization does and how its position shifts.
4. **Key Members** — Linked character entries. No full prose — cross-references only.
5. **Appearances**
6. **Sources**

### Event
1. **Lead** — What happened and when in the continuity.
2. **Background** — Causes, actors involved, structural setup.
3. **Course & Outcome** — What occurred and what it changed.
4. **Continuity Impact** — What the event triggers or enables in subsequent arcs.
5. **Involved Entities** — Linked characters, factions, places.
6. **Appearances**
7. **Sources**

### Concept
1. **Lead** — What the concept is and what domain it belongs to.
2. **Function** — How it works within the series' worldbuilding.
3. **Continuity** — Where and how it appears across arcs.
4. **Related Concepts** — Cross-references to connected items and technologies.
5. **Appearances**
6. **Sources**

### Media
1. **Lead** — Title, type, arc, release context.
2. **Synopsis** — What the entry covers narratively. Spoiler-banded sections for late-game content.
3. **Continuity Position** — Where it fits in the arc structure and series timeline.
4. **Playable Cast / Key Characters** — Linked character entries.
5. **Production Notes** — Developer, publisher, platform, staff credits.
6. **Sources**

---

## 4. Writing Rules (Dissonance Encyclopedic Mode)

All Atlas entries are written in Dissonance encyclopedic mode. These are not soft preferences — they are the standard.

### Identity-First Lead
The first sentence is a high-compression identity statement.

> **Van Arkride** is the protagonist of the *Daybreak* arc.

> **Estelle Bright** is the protagonist of the *Sky* arc.

> **The Bracer Guild** is a transnational mutual-aid and security organization operating across Zemuria.

Never open with backstory, adjectives, or plot setup. State what the subject *is* first.

### Function Over Adjectives
Describe what something *does* and what *role it occupies*, not how it feels or what players think of it.

- Not: "a mysterious and enigmatic figure"
- Yes: "a former Intelligence Division officer operating outside guild jurisdiction"

- Not: "one of the most beloved characters in the series"
- Yes: "a recurring operational contact across the Sky and Erebonia arcs"

### Strict Third-Person Neutrality
The prose must remain indifferent to the subject's ego and to the player's position.

- Not: "you first meet him in..."
- Yes: "he is introduced in..."
- Not: "fan-favorite," "beloved," "overpowered," "strongest"
- Yes: "recurring," "high-leverage," "cross-arc"

### Compressed But Load-Bearing Prose
Reduce large factual surfaces into tighter prose without losing structural information. Every sentence should carry weight. Remove setup sentences that only restate what the next sentence proves.

### Continuity-Aware Structure
Character and place entries must be arc-structured. Use arc headings where the subject appears in multiple arcs. Do not collapse a character's entire history into a single paragraph if they appear across three arcs with meaningful development.

### No Fan-Wiki Gush
Avoid:
- "This character has a lot of fans because..."
- "Many players feel that..."
- Superlatives without structural grounding
- Lore speculation presented as fact

### No Marketing Tone
Avoid:
- "One of the most complex antagonists in the series"
- "A masterclass in character writing"
- Promotional phrasing of any kind

---

## 5. Source and Citation Contract

Atlas entries are allowed to be fuller and more explicit than Wikipedia or Kiseki Wiki. That latitude does not remove the requirement for source discipline.

Every Atlas entry must meet the following minimum contract before it can be promoted to Main and approved:

| Requirement | Description |
| :--- | :--- |
| **Source basis** | The entry must name or link the source(s) its claims derive from. At minimum: the source_id(s) from `source_registry` that ground the prose. |
| **Provenance trace** | Claims that go beyond what is directly stated in source material must be marked as inference or synthesis, not stated as fact. |
| **Disputed points** | Where sources conflict or information is uncertain, this must be noted explicitly in the prose. Do not silently prefer one source. |
| **Spoiler band compliance** | The entry's prose must not contain content from a band higher than the page's declared spoiler_band. Cross-arc entries must truncate at the safe band. |
| **Metadata grounding** | Every Atlas page must link to its Metadata-side Cargo record (entity_id or media_id). A prose-only Atlas entry with no Metadata anchor is not complete. |
| **No unsupported assertions** | Do not include plot claims, character motivations, or lore interpretations that are not traceable to a source in source_registry or to direct in-game text. |

The Atlas is allowed to synthesize and explain. It is not allowed to invent.

Sourcing does not require inline footnotes for every sentence. It requires that the curator can trace any significant claim to a registered source. When a chunk in `chunk_registry` is the direct basis for a passage, the chunk_id should be noted in the page's talk page or edit summary.

---

## 6. Relationship to Metadata

Atlas entries are curated prose. They are stored as `curated_bio` chunks in `chunk_registry`, linked to their source entity via `entity_id`. They are generated from Metadata — they do not replace it.

When an Atlas entry is complete and curator-approved, its lifecycle state advances to `curated` in `lifecycle_registry`.

In MediaWiki, the Atlas prose occupies the main page body below the structured infobox, which is rendered from Cargo (Metadata) data by a Scribunto module.

---

## 7. Specimen Entries

### Van Arkride (Character)

> **Van Arkride** is the protagonist of the *Daybreak* arc. He operates as a Spriggan based in Calvard, specializing in work that falls between the jurisdiction of the police and the Bracer Guild. His professional trajectory centers on the resolution of case files involving factions such as Almata, maintaining a position of leveraged neutrality within the Republic's underground.

### Estelle Bright (Character)

> **Estelle Bright** is the protagonist of the *Sky* arc. She operates as a junior Bracer in the Liberl Kingdom, initially under the mentorship of her father Cassius Bright. Her trajectory across *Sky FC*, *Sky SC*, and *Sky 3rd* moves from field training and a missing-persons investigation into direct confrontation with Ouroboros and the Liber Ark incident. She remains a recurring contact in subsequent arcs, operating from the Liberl branch of the Bracer Guild.

### Crossbell City (Place)

> **Crossbell City** is the administrative and commercial capital of the Crossbell State, a small autonomous territory situated between the Erebonian Empire and the Calvard Republic. It functions as a trade hub and flashpoint for imperial-republican geopolitical tension across the *Zero* and *Azure* arcs. The city's internal power structure involves the Crossbell Police Department, the local Bracer Guild branch, and entrenched criminal organizations operating under the city's political surface.
