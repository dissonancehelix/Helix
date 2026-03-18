# Helix

**Helix is a research framework for discovering patterns in datasets and storing those discoveries in a structured knowledge graph called the atlas.**

Helix analyzes data, extracts measurable structure, and records the results so they can be compared across many experiments. Instead of treating analysis output as temporary files, Helix converts results into persistent entities and relationships. Over time this builds a map of patterns that can be explored, expanded, and tested.

The system is designed to help both humans and reasoning systems understand how complex structures appear across different domains such as music, language, simulations, and other structured data.

---

# Philosophy

Helix is built around a simple principle:

**patterns that appear across different systems often reveal deeper structural rules.**

Many complex systems—music, language, games, biological rhythms, and mathematical models—share forms that are not obvious when each system is studied separately. Helix attempts to reveal these forms by measuring structure and storing the results in a connected graph of knowledge.

Every dataset processed by Helix becomes part of this graph. Measurements, observations, and discovered relationships are preserved so they can be compared with new experiments later.

This philosophy guides the design of the system:

* discoveries should accumulate rather than disappear
* datasets should be comparable across domains
* experiments should be reproducible
* knowledge should be stored as connected entities rather than isolated files

Helix therefore acts both as an analysis environment and as a system for documenting discovery.

---

# Purpose

The purpose of Helix is to make it easier to **discover patterns by organizing data into a structured network of relationships**.

In many research workflows, scripts generate results that are written to files and then forgotten. Helix takes a different approach. Each analysis produces structured artifacts that are compiled into the atlas, where they become part of a persistent graph of knowledge.

Because the information is connected, new analyses can build on previous results. Patterns that are invisible in isolated datasets can become visible when many observations are combined.

Helix is also designed to work well with large language models. The atlas provides a structured representation of entities and relationships that allows reasoning systems to explore connections between datasets.

---

# Core Concepts

## The atlas

The atlas is the central knowledge graph used by Helix. It stores entities and the relationships between them.

Entities can represent many different kinds of objects, including:

* artists
* musical tracks
* motifs or musical patterns
* audio features
* hardware sound chips
* software sound drivers
* datasets and experiments

Relationships describe how these entities interact. For example, a musical track may be connected to the artist who created it, the sound hardware used to produce it, and motifs detected in its structure.

The atlas is designed to grow continuously as new datasets are analyzed.

---

## Artifacts

Artifacts are structured outputs produced by analysis tools.

They contain measurements or representations extracted from data, such as:

* symbolic representations of music
* audio feature measurements
* motif detection results
* similarity graphs
* dataset metadata

Artifacts act as an intermediate layer between analysis tools and the atlas. They preserve raw results before those results are compiled into graph entities.

---

## Operators and Adapters

Helix separates **running analysis tools** from **storing knowledge**.

Operators define analysis tasks such as ingesting datasets or analyzing tracks.

Adapters translate the output of external tools into structured artifacts that Helix can store. All adapters follow a strict tier system based on availability:

| Tier | Description | Adapters |
|------|-------------|---------|
| A | Static constants — always available, no build required | `nuked_opn2`, `nuked_opm`, `nuked_opl3`, `smps`, `gems` |
| B | Compiled C libraries or binaries — requires build step | `libvgm`, `gme`, `vgmstream` |
| C | Python symbolic analysis packages | `music21`, `pretty_midi` |
| D | Python MIR / signal analysis packages | `librosa`, `essentia` |

The substrate operates at the highest available tier. Missing Tier B libraries degrade gracefully to Tier A — the system never fails on missing optional dependencies.

This separation ensures that external tools cannot directly modify the atlas.

---

# Language-Based Architecture

Helix is structured as a hierarchical translation system where all data is treated as a language.

### HSL (Helix Structural Language)
HSL is the **root structural language** of Helix. It provides the base abstraction for representing structure, enabling translation between domains, and facilitating invariant discovery. HSL acts as the unifying layer across all substrates.

### Substrates as Languages
Every substrate in Helix is a **SubstrateLanguage** derived from HSL. A substrate describes how structure exists within a specific domain:
*   **Music**: A temporal and expressive structural language.
*   **Math**: A symbolic and formal structural language.
*   **Control**: A state-transition and causal language.

### Dialects as Representations
Within a substrate language, different representations of the same underlying structure are defined as **Dialects**. For example, in the Music substrate:
*   `chip_control`: Register writes and hardware instructions (e.g., VGM).
*   `symbolic_music`: High-level musical notation (e.g., MIDI, music21).
*   `perceptual_audio`: Rendered sound and spectral features (e.g., waveform).

These are not independent silos; they are equivalent structural views expressed in different dialects.

### Translation as Operation
All processing in Helix is framed as **Translation between dialects**. Ingestion and analysis pipelines are translation chains that transform one representation into another without loss of structural meaning (e.g., `chip_control` → `symbolic_music` → `perceptual_audio`).

### Unified Musical Object
A track or work in Helix is not a file. It is a **Unified Musical Object (UMO)** — a structural entity that may be expressed through multiple dialects simultaneously:
- `chip_control`: Register writes and hardware instructions (causal generation logic)
- `symbolic_music`: High-level compositional notation (MIDI, music21, MusicXML)
- `perceptual_audio`: Rendered sound and spectral feature summaries

These are not separate works. They are aligned views of the same underlying structure. Where complete translation exists, all views are equivalent. Where translation is lossy, each view preserves information the others cannot.

### Observability Depth
Different formats expose different amounts of structural information. Helix formalizes this as **observability depth**:
- **Causal**: Full register-write timeline visible (VGM, NSF, SPC, S98, etc.)
- **Symbolic**: Compositional intent visible, hardware detail absent (MIDI, MusicXML)
- **Perceptual**: Listener-facing features only; generation logic not recoverable (MP3, WAV, FLAC)
- **Hybrid**: Partial causal + partial perceptual (compressed game audio, PSF/2SF)

The substrate operates at the highest available observability depth for each input.

### Composer Identity as Invariant Structure
Helix is not primarily classifying formats or chips. The deeper goal is identifying **persistent compositional identity** across representations — what survives when the format, hardware, and era change. A composer fingerprint is defined by structural habits, decision patterns, motif behavior, harmonic tendencies, and control idioms. This identity is representation-invariant and must be discoverable whether the source is a VGM register dump, a MIDI file, or a rendered audio recording.

### Representation Availability Model

Different works have different available dialects. Helix is designed to function at every level of representation availability:

| Stack Level | Available Dialects | Typical Sources |
|-------------|-------------------|-----------------|
| **Full stack** | chip_control + symbolic_music + perceptual_audio | VGM + MIDI + audio render |
| **Partial stack** | symbolic_music + perceptual_audio | MIDI + MP3, DAW project + render |
| **Minimal stack** | perceptual_audio only | MP3, streaming audio, live recording |

Helix must function under all of these conditions. Missing dialects must not block analysis — all available structure must still be extracted and stored in the atlas. A composer whose only accessible representation is a streaming audio file must be representable in the same structural space as a chip composer with full register-write access.

Helix does not require perfect information to model structure. It operates under partial observability and reconstructs invariants from whatever representations are available.

### Atlas as Structural Memory
The **atlas** is a graph of structures expressed across languages and dialects. It explicitly supports cross-dialect mapping, invariant detection across representations, and structural comparison independent of specific file formats.

---

# Architecture

Helix uses a structured execution pipeline that separates user interaction, analysis tools, and knowledge storage.

The system operates in the following stages:

Human Interface Layer → Operators → Adapters → Toolkits → Artifacts → Atlas compiler

## Data Layer (Helix Data Root)

Helix enforces a unified root data layer at `data/`. This separates raw and processed knowledge from the engine logic.

*   `data/<domain>/source/`: Raw inputs — chip specification PDFs, source code repositories, VGM files.
*   `data/<domain>/processed/`: Pipeline-generated outputs (parsed, features, structure, atlas candidates). Never committed — rebuilt by the pipeline.
*   `data/<domain>/metadata/`: Tags, annotations, and curated metadata.

Source code repositories in `data/music/source/code/` serve as **substrate language references** — the canonical source material for chip emulators, sound drivers, and format converters used by the adapter layer.

## Execution Layer

All runtime traces and probe outputs are stored in `execution/`.

*   `execution/runs/`: Probe run artifacts and experiment outputs.
*   `execution/logs/`: Detailed trace logs.
*   `execution/integrity/`: Tests and validation reports.

Large execution outputs (archives, per-run data dumps) are excluded from version control via `.gitignore`.

---

# Music Analysis

Music analysis is currently one of the main experimental domains in Helix.

The system can analyze both modern audio recordings and video game music formats that contain instructions for specialized sound hardware. These formats provide detailed information about how music is generated.

Helix uses methods from **music information retrieval (MIR)** to measure structural properties of music, including:

* melodic interval patterns
* rhythmic structure
* harmonic movement
* spectral characteristics
* recurring motifs

These measurements allow Helix to analyze how music is structured rather than relying only on metadata such as genre.

### Perceptual Reasoning Without Hearing
Helix enables LLM reasoning about musical perception through structured representations — not direct audio. An LLM reasoning over Helix artifacts can access:
- Register-write timelines that causally determine every audible event
- Extracted perceptual features (spectral centroids, MFCCs, chroma vectors, onset envelopes)
- Symbolic projections (pitch sequences, rhythm trees, harmonic motion)

This structural access can exceed the information content of raw MP3/Opus streams in chip-native formats because the generation logic is preserved directly. Conversely, rendered audio and compressed formats preserve expression, mixing, performance nuance, and perceptual realization that symbolic or chip-level representations cannot recover.

### Universal Artist Coverage

Helix is not a chiptune analysis system. Chip-native formats (VGM, SPC, NSF) provide the highest observability depth and enable full causal analysis, but they represent only a subset of supported cases. Helix equally supports:

- Modern electronic artists (MP3, WAV, FLAC, OPUS recordings)
- Live bands and orchestral recordings (audio-only, no symbolic or control layer)
- Classical works available as MIDI or MusicXML without audio
- Any artist whose music is accessible only through streaming or rendered audio

All artists — regardless of data richness — must be representable uniformly in the atlas. Entities support missing dialect fields without breaking structure. Relationships (motifs, style patterns, similarity) remain computable at minimal stack level using perceptual and structural features alone.

---

# Motifs and Musical Structure

Helix attempts to detect repeating musical fragments known as **motifs**.

Motifs are short melodic or rhythmic patterns that appear throughout a piece of music. When Helix detects motifs, they are stored as entities in the atlas and connected to the tracks where they appear.

By comparing motifs across many works, Helix can identify structural similarities between pieces of music.

Motifs can also be linked together to form networks that describe how musical ideas evolve across works or artists.

---

# Artist Style Modeling

Helix can build statistical descriptions of how an artist composes music.

These descriptions summarize patterns such as:

* melodic interval usage
* rhythmic tendencies
* harmonic movement
* motif usage

These measurements form an **artist style profile**. When profiles are compared, Helix can estimate structural similarity between artists.

This approach allows the system to reveal relationships that may not correspond to traditional genre categories.

---

# Exploring Personal Music Libraries

Helix can analyze entire personal music collections.

By measuring musical structure across many tracks, the system can identify patterns that appear frequently in the listener’s library. These patterns can describe aspects of musical taste, such as:

* preferred melodic structures
* rhythmic complexity
* recurring motif patterns
* similarities between favored artists

In this way Helix can help reconstruct the structural patterns that appear in a listener’s collection.

---

# Execution Model

Helix operates in two distinct phases:

## 1. Indexing Phase

Helix first builds a structural index of a dataset inside the atlas.

During indexing:

* entities are created (tracks, artists, games, sound chips, drivers, knowledge sources)
* relationships are established
* file paths and metadata are stored
* no structural analysis is performed

This phase converts raw data into a queryable space.

## 2. Analysis Phase

Helix then performs structural analysis on selected entities.

During analysis:

* measurable features are extracted
* motifs and patterns are detected
* artifacts are generated
* results are compiled into the atlas

Analysis is selective and controlled. Not all indexed data must be analyzed.

---

# Atlas as Primary Interface

Once data is indexed, the atlas becomes the primary interface for all interaction.

All queries must resolve through atlas entities rather than raw files.

---

# Entity States

Entities in the atlas are not required to be fully analyzed.

A track may exist as:

* indexed (metadata only)
* analyzed (features extracted)
* modeled (included in higher-level structures)

---

# Attribution as Hypothesis

Helix separates:

* recorded credit (metadata)
* inferred attribution (structural analysis)

These are stored independently. Inferred attribution is a testable hypothesis and must never overwrite recorded metadata.

---

# Helix Ingestion Contract

Every data ingestion must strictly follow the **Deterministic Structural Extraction** contract:

1.  **Source Purity**: Only read from `data/source/`.
2.  **Decomposition**: Extract atomic components (operators, topologies, envelopes).
3.  **Measurable Interpretation**: Use quantified metrics, never vague labels.
4.  **6-Stage Pipeline**: Must produce Parsed, Features, Structure, Patterns, Measurements, and Atlas Candidates.
5.  **Invariant Safety**: Only `invariant_candidates` are permitted; true invariants require cross-source validation.

---

# Atlas as a Structured Memory of Your Data

When Helix processes a personal music library, it does not simply analyze files on demand.
It builds a structured index of the entire collection inside the atlas.

Each track, artist, game, and platform is registered as an entity with relationships and metadata, including file paths. This allows Helix to treat the user’s library as a persistent, queryable space.

As a result:

* tracks can be referenced directly without manual lookup
* relationships between artists, games, and structures are preserved
* future analyses build on previously indexed knowledge

The atlas becomes a working memory of the user’s music collection rather than a temporary analysis cache.

---

# Structural vs Recorded Truth

Helix distinguishes between two types of information:

* recorded metadata (credits, tags, known information)
* inferred structure (patterns detected through analysis)

For example, a track may have an official credited composer, while Helix may detect strong structural similarity to another artist’s style.

Both are preserved separately.

This allows Helix to generate hypotheses (such as likely authorship) without overwriting or distorting known information. All inferred results remain testable and falsifiable.

---

# The Atlas as a State Space

The atlas can be understood as a structured space of relationships.

In this space:

* tracks are points defined by structural features
* artist style profiles are regions or distributions
* similarity defines distance
* invariants describe recurring geometric patterns

This allows Helix to move beyond simple queries and instead navigate the data structurally.

Users and reasoning systems can explore the atlas by:

* finding nearby structures
* clustering similar works
* tracing paths between artists or motifs

This transforms a static dataset into a navigable representation of structure.

---

# Future Research

Helix is designed as a long-term discovery system.

The research roadmap focuses on identifying structural patterns that may appear across different domains. Planned areas of investigation include:

* decision structure in complex systems
* compression of symbolic systems such as language and notation
* synchronization behavior in oscillatory systems
* effects of hardware constraints on musical structure
* communication efficiency in multi-agent systems
* phase transitions in strategic environments
* timing patterns shared across music, speech, and biological rhythms
* emergence of hierarchical structure in complex systems
* the relationship between constraints and creativity
* translation of structural patterns between different domains

These research directions form part of the Helix discovery program described in the roadmap. 

---

# Evolving into a Closed Semantic Research System

Helix has evolved from a music analysis engine into a **Closed Semantic Research System**. It now integrates observation, execution, and formal reasoning into a self-correcting loop.

### The Research Loop:
1. **Observation**: Extraction of structural signatures across substrates (Music, Games).
2. **Formalization**: Integration with the **Mathematics Substrate** to apply models like the Decision Compression Principle (DCP).
3. **Hypothesis**: Autonomous discovery of **Invariants** using the `DISCOVER_INVARIANTS` operator.
4. **Validation**: Targeted testing of invariants through the **Invariant Lifecycle** (Proposed → Tested → Verified).
5. **Falsification**: Active hunting for counterexamples via `FALSIFY_INVARIANT` to ensure scientific rigor.

### Scientific Rigor (Dissonance & Confidence)
Helix treats every piece of evidence as a weighted vote.
- **Confidence Score**: How strongly an invariant is supported by data.
- **Dissonance Score**: The ratio of counterexamples found to the total evidence pool.

By identifying **Outliers** and **Structural Deviations**, Helix distinguishes between local noise and universal structural laws.

### Design Philosophy
Helix is built on the idea that research should produce **structured knowledge that grows over time**. Instead of generating isolated analysis results, Helix records each observation as part of a connected network. As the Atlas expands, it becomes possible to explore relationships and test new hypotheses using previously discovered patterns.

---

# Related Fields

Helix draws ideas from several areas of research:

* music information retrieval
* computational musicology
* knowledge graphs
* data mining
* pattern discovery systems

---

# Project Status

Helix is an evolving experimental system. Its architecture is designed to support expansion into additional research domains while maintaining a consistent structure for documenting and connecting results.

Future work will focus on expanding the atlas, improving pattern discovery methods, and exploring new datasets that contribute to the system’s knowledge base.
