# Helix Entity Schema

## ID Format

All entity IDs use: `domain.type:slug`

| Component | Description | Example |
|-----------|-------------|---------|
| `domain`  | Knowledge domain | `music`, `tech`, `games`, `language`, `cognition` |
| `type`    | Entity type within domain | `track`, `proof`, `text`, `mechanic` |
| `slug`    | Snake-case identifier | `yuzo_koshiro`, `ym2612` |

## Universal Entity Types

These types exist in every domain:

| Type | Description |
|------|-------------|
| `invariant` | Discovered structural law |
| `experiment` | Research probe result |
| `claim` | Falsifiable hypothesis |
| `relationship` | Connection between two entities |
| `entity` | Generic, unclassified entry |

## Universal Required Fields

Every entity in every domain must include:

| Field | Description |
|-------|-------------|
| `id` | Canonical `domain.type:slug` |
| `type` | Entity type from the list above |
| `name` | Human-readable label |
| `metadata.source` | File path or data origin |

## DCP and Substrate — Unified Framework

Both the **track-level** and **substrate-level** structural profiles use the same axis vocabulary derived from Decision Compression Protocol (DCP). The distinction is scope:

| Scope | Block name | Derived from | Changes per... |
|-------|------------|--------------|----------------|
| Substrate | `substrate` | Medium spec (chip, grammar, axiom set) | Medium type |
| Track | `dcp` | Actual content at structural boundary | Individual work |

The `substrate` block answers: *"What is the theoretical upper bound on generative complexity for this medium?"*
The `dcp` block answers: *"What did this specific work do at its structural closure point?"*

They share the same conceptual axes because both measure possibility-space dynamics — just at different levels of abstraction.

## Domain: music

Schema file: `codex/library/music/SCHEMA.json`

### Music entity types

| Type | Description |
|------|-------------|
| `artist` | Composer / performer |
| `track` | Individual musical work |
| `album` | Collection of tracks |
| `genre` | Musical genre classification |
| `era` | Historical time period |
| `motif` | Recurring musical pattern |
| `technique` | Compositional technique |
| `style_vector` | Computed composer fingerprint |
| `voice_structure` | Channel arrangement |
| `harmonic_pattern` | Chord / harmony sequence |
| `rhythmic_pattern` | Rhythmic structure |
| `timbre_profile` | Spectral / timbral characteristics |

### Tech entity types (used within music domain)

| Type | Description |
|------|-------------|
| `sound_chip` | Hardware synthesis component |
| `platform` | Gaming / computing platform |
| `operator_topology` | FM operator configuration |

### Track entity blocks

| Block | Description |
|-------|-------------|
| `metadata` | Identity, artist, source path, tags, library state |
| `hardware` | Chips, voice count, duration, loop point |
| `substrate` | DCP profile of the primary chip — static generative ceiling |
| `dcp` | DCP proxies measured at the loop seam — track-level structural dynamics |
| `symbolic` | Musical content: key, pitch entropy, rhythm, note density |
| `composer_attribution` | Attribution pipeline result |
| `analysis` | Raw codec_pipeline tier + confidence |


### Substrate axes (music)

Derived from primary chip spec. Values: float [0.0, 1.0].

| Axis | Music meaning |
|------|--------------|
| `possibility_space` | Max expressible pitch/timbre entropy |
| `constraint` | How tightly the hardware limits output |
| `attractor_stability` | Loop/repeat hardware support quality |
| `basin_permeability` | Envelope flexibility (attack/release floor) |
| `recurrence_depth` | Polyphony × patch variation ceiling |

### DCP axes (music — track level)

Computed from note events at the loop seam.

| Axis | Music meaning |
|------|--------------|
| `possibility_space` | Pitch class entropy of pre-loop region |
| `collapse` | Note density change at seam |
| `tension` | Active channel count in pre-seam window |
| `post_narrowing` | Channel count drop after loop restart |
| `composite` | Mean of available proxies |
| `qualification` | `FULL` / `UNCONFIRMED` / `INSUFFICIENT` |

The loop seam is a high-confidence DCP measurement point: structural closure is explicit in the hardware log, not inferred.

---

## Probe Family: math

Schema file: `core/probes/math/SCHEMA.json` *(TBD)*

Math is not a target corpus domain; it is a formal probe family used for invariant stress-testing, null model construction, and geometry calibration across real-world traces.

### Math entity types

| Type | Description |
|------|-------------|
| `proof` | Formal proof of a statement |
| `conjecture` | Unproven claim under investigation |
| `theorem` | Proven general statement |
| `lemma` | Auxiliary result used in a proof |
| `axiom` | Foundational assumption |
| `model` | Formal mathematical model |

### Math entity blocks

| Block | Description |
|-------|-------------|
| `metadata` | Statement, domain (algebra, topology...), source |
| `substrate` | DCP profile of the axiom system (expressiveness ceiling) |
| `dcp` | Decision compression at proof completion boundary |
| `formal` | Formal representation (Lean, Coq, symbolic) |
| `structure` | Proof steps, dependency graph, axiom set |
| `invariant_links` | Connections to Helix invariants |
| `falsification` | Known counterexamples / boundary conditions |

---

## Domain: language

Schema file: `codex/library/language/SCHEMA.json` *(TBD)*

### Language entity types

| Type | Description |
|------|-------------|
| `text` | A document, passage, or corpus entry |
| `author` | Creator of a text |
| `vocabulary` | Lexical inventory of a language or corpus |
| `grammar` | Formal or descriptive grammar system |
| `token` | Atomic unit (word, morpheme, glyph) |

### Language entity blocks

| Block | Description |
|-------|-------------|
| `metadata` | Title, author, language, source |
| `substrate` | DCP profile of grammar/vocabulary (expressiveness ceiling) |
| `dcp` | Decision compression at structural boundaries (chapter ends, etc.) |
| `corpus` | Tokenization, vocabulary size, n-gram statistics |
| `structure` | Document segmentation, section graph |
| `semantic` | Topic distribution, embedding vector |

---

## Domain: games

Schema file: `codex/library/games/SCHEMA.json` *(TBD)*

### Games entity types

| Type | Description |
|------|-------------|
| `game` | A playable software title |
| `mechanic` | A discrete rule or interaction system |
| `level` | A contained play environment |
| `character` | An agent within the game system |
| `system` | A set of interacting mechanics (e.g. economy, combat) |

### Games entity blocks

| Block | Description |
|-------|-------------|
| `metadata` | Title, platform, developer, year, source |
| `substrate` | DCP profile of ruleset (mechanic space ceiling) |
| `dcp` | Decision compression at win/lose/save conditions |
| `mechanics` | Core loop, decision points, feedback structures |
| `structure` | Stage/level graph, branching factor |
| `invariant_links` | Connections to system invariants |

