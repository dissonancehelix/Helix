# HELIX MUSIC LAB — SYSTEM ARCHITECTURE

## 1. System Purpose

Helix Music Lab is a research subsystem within the Helix framework designed to analyze video game music at multiple structural levels.

The system integrates musicology, signal processing, chip-level synthesis analysis, and metadata knowledge graphs to study patterns in video game music composition and production.

Primary goals include:

- Analyzing musical structure
- Analyzing synthesis techniques used by game composers
- Identifying stylistic patterns across composers and sound teams
- Supporting composer attribution research
- Mapping relationships between composers, games, sound teams, and platforms

Helix Music Lab is not just a media library. It is a computational musicology platform specialized for video game music.

---

## 2. Data Sources

Helix Music Lab ingests both local and external data.

### Local Data Sources

- foobar2000 library database (`metadb.sqlite`)
- Embedded file metadata
- External tag databases
- Audio files: MP3, FLAC, Opus
- Chip music formats: VGM, SPC, NSF, SID
- Symbolic representations: MIDI, MusicXML

### External Data Sources

Helix can enrich its knowledge graph using external databases:

- Wikidata
- Wikipedia
- MusicBrainz
- VGMDB
- VGMPF (Video Game Music Preservation Foundation)
- VGMRips Wiki
- Last.fm
- Spotify

These sources provide composer identities, release metadata, soundtrack credits, and historical context.

---

## 3. Metadata Normalization

Helix adapts metadata from the foobar2000 library schema.

Existing tags include: `Title`, `Artist`, `Album`, `Date`, `Genre`, `Featuring`, `Album Artist`, `Sound Team`, `Franchise`, `Track Number`, `Total Tracks`, `Disc Number`, `Total Discs`, `Comment`, `Platform`, `Sound Chip`.

For video game music, Helix interprets these fields as follows:

| Tag | Helix Interpretation |
|-----|----------------------|
| `ARTIST` | Primary composer |
| `ALBUM ARTIST` | Soundtrack release artist |
| `FEATURING` | Additional contributors |
| `SOUND TEAM` | Composer collective or studio |
| `FRANCHISE` | Game series grouping |
| `PLATFORM` | Hardware platform |
| `SOUND CHIP` | Synthesis hardware used |

This normalization allows Helix to treat game music metadata consistently across different file formats.

---

## 4. Analysis Pipeline

Helix Music Lab processes music through nine analysis layers.

### Layer 1 — Library Ingestion

Helix reads the foobar2000 database and builds a track index containing metadata and file paths.

Tracks are registered as Helix entities and linked to games, franchises, composers, and platforms.

### Layer 2 — Chip-Level Analysis

For chip music formats such as VGM, SPC, NSF, and SID, Helix extracts synthesis data using chip emulation tools.

Relevant tools include: `libvgm`, `vgm2x`, chip emulation libraries.

Extracted data includes:

- Register writes
- Operator parameters (TL, DT, MUL, algorithms)
- Instrument patches
- DAC sample usage
- Channel activity
- Sound chip configuration

This reveals how composers used hardware synthesis systems.

### Layer 3 — Symbolic Music Extraction

Chip music and audio files are converted into symbolic representations such as MIDI or MusicXML.

This allows Helix to analyze musical structure independently of hardware implementation.

Tools include: `symusic`, MIDI utilities, MusicXML conversion pipelines.

### Layer 4 — Computational Musicology Analysis

Symbolic music is analyzed using computational musicology tools including `music21`, `musif`, `symusic`, and `partitura`.

Extracted features include:

- Pitch class distributions
- Melodic interval patterns
- Harmonic progressions
- Phrase structure and segmentation
- Motif repetition and cell detection
- Rhythmic density
- Cadence patterns
- Voice-leading analysis
- Pitch class sets

### Layer 5 — MIR Audio Analysis

Audio-level analysis is performed using Music Information Retrieval tools including `librosa`, `essentia`, and `MusPy`.

Extracted features include:

- Tempo and beat grid
- Spectral brightness and centroid
- Energy profiles
- Onset density
- Rhythmic regularity
- Loudness curves

### Layer 6 — Ludomusicology Analysis

Video game music follows structural patterns related to gameplay loops and interactivity. Helix analyzes:

- Loop architecture: boundary detection, harmonic behavior at loop restart, phrase alignment, cadence type, loop stability index
- Energy curves: rhythmic density, harmonic tension, and arrangement density over time; curve shape classification (flat / build / drop / arch / valley)
- Gameplay function detection: 10-role classifier (boss / exploration / tension / menu / cutscene / bonus / special / jingle / ambient / unknown)
- VGM-specific patterns: channel role analysis, patch identity, groove pattern clustering

### Layer 7 — Feature Synthesis

All extracted features are combined into a structured fingerprint vector per track. Composer-level aggregates are built from per-track distributions.

Feature vectors include: harmonic tendencies, melodic interval profiles, rhythmic features, synthesis palette signatures, loop stability, energy curve shape, gameplay role confidence.

### Layer 8 — Style Space Analysis

Track and composer fingerprint vectors are projected into lower-dimensional style spaces using:

- PCA (numpy fallback, always available)
- t-SNE (scikit-learn)
- UMAP (umap-learn)

Outputs include: composer style clusters, soundtrack similarity maps, motif similarity networks, instrument patch reuse graphs.

Pattern discovery uses HDBSCAN (density-based), k-means (auto-k by silhouette), greedy cosine clustering, and track similarity networks via networkx modularity.

### Layer 9 — LLM Interpretation

Structured analysis outputs are passed to Claude for musicological interpretation.

The system builds structured prompts from analysis dicts without feeding raw chip or MIDI data. Per-track interpretation uses `claude-sonnet-4-6`; corpus-level synthesis uses `claude-opus-4-6`.

---

## 5. Composer Knowledge Graph

Helix builds a typed graph connecting musical entities.

### Entity Types

| Entity | Description |
|--------|-------------|
| `Composer` | Individual composer with biography, external IDs, style fingerprint |
| `Track` | Individual piece with chip, duration, attribution confidence |
| `Game` | Title with platform, developer, year, sound team |
| `Soundtrack` | Album/OST release with catalog number, label, format |
| `Sound Team` | Named composer collective or studio group |
| `Studio` | Development or publishing studio |
| `Platform` | Hardware platform with chip inventory |
| `Sound Driver` | Sound engine used by a game (e.g. SMPS, SPC700) |

### Relationships

```
composer  → wrote            → track
composer  → arranged         → track
composer  → worked_on        → game
composer  → member_of        → sound_team
composer  → worked_at        → studio
composer  → collaborated_with → composer
composer  → influenced_by    → composer
track     → appears_in       → game
track     → released_on      → soundtrack
track     → uses_sound_driver → driver
game      → runs_on          → platform
game      → developed_by     → studio
game      → published_by     → studio
soundtrack → documents       → game
```

### External Identifiers

Composer and game nodes carry typed external IDs linked to: Wikidata, Wikipedia, MusicBrainz, VGMDB, VGMPF, Last.fm, Spotify, Discogs.

---

## 6. Knowledge Sources

Each external source has a dedicated ingester module.

| Source | Module | Data Provided |
|--------|--------|---------------|
| Wikidata | `wikidata_ingester.py` | Biography, nationality, instruments, employers, aliases |
| MusicBrainz | `musicbrainz_ingester.py` | Artist MBIDs, release groups, soundtrack credits |
| VGMDB | `vgmdb_ingester.py` | Soundtrack credits, team membership, game metadata |
| VGMPF | `vgmpf_ingester.py` | Sound driver facts, chip specs, technical style traits |
| Last.fm | `lastfm_ingester.py` | Biography summaries, genre tags, similar artists |
| Sonic Retro HTML | `sonic_retro_ingester.py` | Per-track credits, staff tables, historical context |

---

## 7. Style Graph Queries

The `StyleQueryEngine` class provides research-level queries combining graph topology with fingerprint vectors:

- **Tracks similar to a composer** — nearest tracks to a composer's centroid vector
- **Composers with overlapping vectors** — cosine similarity between composer centroids
- **Stylistic clusters within a soundtrack** — greedy cosine clustering of game tracks
- **Composers sharing synthesis practices** — matched by chip, driver, technique traits
- **Influence chain traversal** — BFS over `influenced_by` edges to configurable depth
- **Stylistic outliers** — tracks distant from a game's centroid vector

---

## 8. Output Products

### Report Artifacts

| File | Description |
|------|-------------|
| `composer_table.{json,csv,md}` | Per-composer summary: biography, external links, style traits, track count |
| `track_attribution_{game}.{json,csv,md}` | Per-track credits with composer names, confidence, sources |
| `knowledge_graph_summary.{json,md}` | Entity counts, top connected composers, relationship distribution |
| `style_fingerprint_report.{json,csv,md}` | Per-composer vector statistics + cosine similarity matrix |
| `composer_similarity_matrix.md` | Formatted similarity grid |
| `style_query_report.json` | Full style query results per composer |
| `llm_interpretation.json` | Claude corpus-level musicological synthesis |

### Visualization Artifacts

| File | Description |
|------|-------------|
| `collaboration_network.{gexf,dot,png}` | Composer collaboration + team membership graph |
| `stylistic_similarity.{gexf,dot,png}` | Composer fingerprint similarity network |
| `soundtrack_clusters_{game}.{gexf,dot,png}` | Track cluster graph for a single soundtrack |
| `studio_influence_network.{gexf,dot,png}` | Studio, platform, driver, game infrastructure graph |

GEXF files are compatible with Gephi. DOT files are compatible with Graphviz.

---

## 9. Initial Test Dataset

The first complete system test uses the soundtrack from:

**Sonic the Hedgehog 3 & Knuckles** (Sega, 1994)

This dataset is ideal because it includes:

- Multiple composers across three distinct teams (Sega Sound Team, MJJ Productions / Jackson crew, Cube Corp)
- A well-documented and historically contested attribution record
- Custom SMPS Z80 sound driver written by Yoshiaki Kashima
- Rich FM synthesis via YM2612 + PSG via SN76489
- 58 tracks covering the full S3 + S&K soundtrack

The Sonic Retro music development page serves as the primary ground truth source for per-track attribution.

Known attribution highlights:

| Track | Composers | Source |
|-------|-----------|--------|
| IceCap Zone | Bruce Connole, Brad Buxer | Based on The Jetzons "Hard Times" (1982) |
| Hydrocity Act 2 | Masayuki Nagao (arr.) | Sonic Retro |
| Staff Roll (S3) | Brad Buxer + MJ beatbox samples | Sonic Retro |
| Special Stage | Yoshiaki Kashima | Recycled from SegaSonic Bros. |
| Marble Garden, Mushroom Hill (+ 6 others) | Miyoko Takaoka, Masanori Hikichi (Cube Corp) | Sonic Retro |

---

## 10. Long-Term Goals

Helix Music Lab aims to become a research platform for large-scale video game music analysis.

Potential future capabilities include:

- Large-scale composer style mapping across hundreds of soundtracks
- Historical analysis of game music evolution by era and platform
- Synthesis technique classification and chip-fingerprinting
- Cross-platform composition studies
- Automated musicology research pipelines
- Integration with the Helix Atlas invariant discovery system

Within Helix, music is an additional research substrate alongside other complex domains — a signal-rich environment for studying how creative and technical constraints shape compositional style.
