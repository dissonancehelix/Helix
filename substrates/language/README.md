# HELIX LANGUAGE SUBSTRATE SPECIFICATION

**Version:** 2.0
**Status:** Authoritative formal substrate specification
**Authority:** This document is the implementation contract for the Helix Language Substrate.
**Purpose:** Enable reconstruction of the Language Substrate without architectural invention. If code conflicts with this document, this document takes precedence until intentionally revised.

---

## 0. WHY THIS DOCUMENT EXISTS

This document is the formal design specification for the Helix Language Substrate.

Its purpose:
- An LLM can rebuild the substrate without inventing architecture
- Domain logic is not misplaced into Core or Labs
- Future implementations follow the same structural DNA

---

## 1. SUBSTRATE IDENTITY

### 1.1 What the Language Substrate is

The Language Substrate analyzes structured communication systems and symbolic compression.

Language is treated as a dynamic information system where meaning emerges through:
- symbol sequences (tokens, words, morphemes)
- grammar structures (syntax trees, dependency graphs)
- semantic relationships (concept networks, embedding spaces)
- contextual inference (discourse structure, pragmatic meaning)
- communication protocols (turn-taking, repair, compression)

The goal is to detect structural invariants in symbolic systems — patterns that persist across languages, scales, and communication modalities.

### 1.2 What the Language Substrate is not

The Language Substrate is not:
- a natural language processing (NLP) application
- a chatbot or dialogue system
- a translation service
- a text generation tool
- a sentiment analysis pipeline

It exists to extract structural invariants from language data, not to produce or interpret natural language for its own sake.

### 1.3 Core identity statement

The Language Substrate treats language as an information-theoretic system.

It studies:
- how symbol sequences encode meaning under compression constraints
- where information bottlenecks and compression events occur
- how semantic structure emerges from distributional patterns
- what invariants appear across different language families and modalities

---

## 2. CLOSED SYSTEM LAW

The Language Substrate operates under Helix's Closed System Law.

**Substrates never write to Atlas directly.**

The substrate produces artifacts. The Atlas Compiler converts artifacts into Atlas entities.

**Pipeline:**
```
RUN operator:SCAN substrate:language
    → discover language corpora
    → write corpus entity artifacts to artifacts/language/

RUN operator:ANALYZE entity:language.corpus:<id>
    → analyze symbolic structure
    → write analysis artifacts to artifacts/language/

RUN operator:COMPILE_ATLAS
    → compile artifacts to atlas/language/
```

---

## 3. HELIX LAYER POSITION

```
HIL
→ Normalization
→ Semantics
→ Operator Runtime (SCAN, ANALYZE, COMPILE_ATLAS)
→ Atlas Compiler
→ Atlas

Operator Runtime
       │
       ▼
Language Substrate Pipeline
       │
       ▼
 artifacts/language/
       │
       ▼
  Atlas Compiler
       │
       ▼
 atlas/language/
```

### 3.1 Substrate responsibility

The Language Substrate is responsible for:
- corpus ingestion and preprocessing
- tokenization and morphological parsing
- syntax tree extraction and dependency graph construction
- semantic embedding generation
- information-theoretic feature extraction
- compression event detection
- symbol emergence analysis
- artifact generation

### 3.2 Language Lab responsibility

Language Lab (`labs/language_lab/`) is responsible for higher-level experimentation:
- cross-language comparative studies
- semantic drift experiments
- symbol emergence experiments
- communication efficiency research
- research notebooks and visualization
- anything exploratory or replaceable

---

## 4. DOMAIN TYPES

The Language Substrate analyzes:

| Domain | Examples |
|--------|---------|
| Natural language corpora | Books, news, conversation transcripts |
| Constructed languages | Esperanto, Lojban, programming languages |
| Dialog systems | Conversation logs, customer service transcripts |
| Semantic networks | WordNet, ConceptNet, knowledge graphs |
| Translation datasets | Parallel corpora, multilingual corpora |
| Communication protocols | HTTP logs, protocol traces, radio transcripts |

---

## 5. ACTIVE PROBES

### 5.1 decision_compression

The `decision_compression` probe tests the Decision Compression Principle in language choice:

> When a communicator faces a high-stakes lexical or structural decision, the available symbol space compresses measurably before selection.

**Status:** Verified (86% pass rate, 3 domains)
**Dataset:** `decision_compression_dataset.json`
**Signal:** Token selection entropy at semantically critical positions

### 5.2 oscillator_locking

The `oscillator_locking` probe tests synchronization in dialogic systems:

> Interlocutors in extended dialogue converge to shared rhythmic and structural patterns, exhibiting oscillator locking behavior.

**Status:** Verified (100% pass rate, 3 domains)
**Dataset:** `oscillator_locking_dataset.json`
**Signal:** Structural alignment index between conversation participants

---

## 6. ANALYSIS PIPELINE

The Language Substrate uses a deterministic, stage-based pipeline.

### 6.1 Stage sequence

```
1. INGESTION
   text corpora, dialogue logs, translation datasets
   → normalize encoding, detect language, tokenize

2. PARSING
   tokenization → syntax trees → dependency graphs
   → morphological decomposition

3. STRUCTURAL ANALYSIS
   grammar extraction (context-free rules, dependency patterns)
   semantic network construction
   embedding generation (word / sentence / document level)

4. FEATURE EXTRACTION
   information-theoretic features:
     - token entropy (per position, per context)
     - perplexity profiles
     - compression ratio estimates
     - branching factor in syntax trees
   semantic features:
     - embedding distances
     - semantic cluster membership
     - lexical diversity

5. PATTERN DETECTION
   semantic clustering across documents
   symbol emergence events (new vocabulary diffusion)
   information bottlenecks (compression events)
   communication efficiency patterns

6. ARTIFACT GENERATION
   write to artifacts/language/<corpus_id>/
```

### 6.2 Artifact outputs

All artifacts written to `artifacts/language/<corpus_id>/`:

| Artifact | Description |
|----------|-------------|
| `corpus_index.json` | Document metadata and statistics |
| `syntax_trees.json` | Parsed syntax structures (sampled) |
| `embeddings.json` | Document/sentence embedding matrix |
| `entropy_profiles.json` | Token entropy time series |
| `compression_events.json` | Detected compression events |
| `semantic_clusters.json` | Semantic cluster assignments |
| `symbol_emergence.json` | New symbol emergence events |

---

## 7. ENTITY TYPES

### 7.1 Language entities

| Entity Type | ID Format | Description |
|-------------|-----------|-------------|
| `Corpus` | `language.corpus:<slug>` | Language corpus definition |
| `Document` | `language.doc:<id>` | Individual text document |
| `Language` | `language.lang:<slug>` | Natural or constructed language |
| `Symbol` | `language.symbol:<slug>` | Emergent or defined symbol |
| `SemanticCluster` | `language.cluster:<id>` | Semantic concept cluster |
| `CompressionEvent` | `language.compression:<id>` | Detected compression event |

### 7.2 Relationships

```
Document → INSTANCE_OF → Corpus
Document → WRITTEN_IN → Language
Symbol → APPEARS_IN → Corpus
Symbol → BELONGS_TO_CLUSTER → SemanticCluster
CompressionEvent → OCCURS_IN → Document
CompressionEvent → SUPPORTS → Invariant
```

---

## 8. DATASET CONTRACT

### 8.1 Probe dataset convention

Probe runner loads `{probe_name}_dataset.json` first, then falls back to first `.json` alphabetically.

Each dataset JSON must contain:
```json
{
  "probe_name": "decision_compression",
  "domain": "language",
  "items": [
    {
      "corpus_id": "...",
      "language": "...",
      "token_sequences": [...],
      "entropy_annotations": [...]
    }
  ]
}
```

### 8.2 Dataset locations

```
labs/language/
├── decision_compression_dataset.json
└── oscillator_locking_dataset.json
```

---

## 9. REPOSITORY STRUCTURE

```
substrates/language/
├── README.md                     ← this document
├── datasets/
│   ├── corpora/                  ← raw text files and indices
│   ├── dialogues/                ← conversation logs
│   ├── translation_sets/         ← parallel corpora
│   └── semantic_networks/        ← graph-format semantic data
├── pipelines/
│   ├── ingestion/                ← stage 1: load and normalize corpora
│   ├── parsing/                  ← stage 2: tokenize, parse, embed
│   ├── syntactic_analysis/       ← syntax tree and dependency analysis
│   ├── semantic_analysis/        ← embedding and semantic structure
│   ├── embedding_generation/     ← stage 3: vector representations
│   ├── pattern_detection/        ← stage 5: clustering, bottlenecks
│   └── atlas_integration/        ← artifact prep for compiler
├── models/
│   ├── embedding_models/         ← sentence/document embedding models
│   └── semantic_models/          ← semantic clustering models
└── experiments/
    ├── symbol_emergence/
    ├── semantic_drift/
    └── communication_efficiency/
```

---

## 10. HIL CONTRACT

All orchestration occurs through HIL.

Examples:
```
RUN operator:SCAN substrate:language
RUN operator:ANALYZE entity:language.corpus:english_news_2024
PROBE invariant:decision_compression lab:language
PROBE invariant:oscillator_locking lab:language
ATLAS list domain:language
ENTITY get language.corpus:english_news_2024
GRAPH support invariant:decision_compression
```

---

## 11. RELATIONSHIP TO HELIX INVARIANTS

The Language Substrate validates Helix invariants in symbolic communication systems.

| Invariant | Language signal |
|-----------|----------------|
| `decision_compression` | Token entropy compression at high-stakes lexical decisions |
| `oscillator_locking` | Structural synchronization between interlocutors in dialogue |

Language provides the richest dataset for semantic compression analysis because:
- Corpora can be arbitrarily large
- Multiple scales of analysis (token, phrase, document, corpus)
- Clear information-theoretic grounding

---

## 12. ANTI-DRIFT RULES

- Do not write language analysis directly to `atlas/` — use the artifact pipeline
- Do not invent alternative orchestration — HIL only
- Do not conflate linguistic structure analysis with NLP application development
- Do not place exploratory experiments in the substrate — use Language Lab

---

## 13. RECONSTRUCTION SPECIFICATION

A future system can reconstruct the Language Substrate from this document.

Required components:
- [ ] 6-stage analysis pipeline (ingest → parse → structural → features → patterns → artifacts)
- [ ] Artifact schemas matching §6.2
- [ ] Entity types matching §7.1 with correct ID format
- [ ] Probe datasets for `decision_compression` and `oscillator_locking`
- [ ] All artifacts written to `artifacts/language/`, never to `atlas/`
- [ ] HIL-only orchestration interface

---

*This document is the authoritative specification for the Helix Language Substrate.*
*Version 2.0 — 2026-03-17*
