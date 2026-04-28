# HELIX MUSIC SUBSTRATE SPECIFICATION

**Version:** 2.2
**Status:** Authoritative target specification — implementation status tracked in README.md §11
**Relationship:** Extends `model/domains/music/README.md`

---

## 1. DOMAIN SCOPE

The Music Substrate operates across three observability layers:
- **Causal**: Hardware synthesis logic (register writes, chip state)
- **Symbolic**: Compositional intent (MIDI, score notation)
- **Perceptual**: Psychoacoustic outcome (rendered audio, MIR features)

Its goal is to extract structural invariants that survive across these layers when format, hardware, or era changes.

---

## 2. DOMAIN-LOCAL STRUCTURAL SIGNALS

These signals are extracted by the music pipeline and are domain-local. They are NOT the same as HelixEmbedding axes. They feed into the feature fusion stage, which then produces a `MusicStyleVector` that is projected into the shared embedding.

### 2.1 Causal Signals (Hardware/Driver)
- **`register_write_density`**: Chip register writes per second
- **`operator_topology_complexity`**: Graph complexity of FM synthesis algorithms
- **`driver_tick_jitter`**: Temporal variance in command dispatch
- **`lfsr_noise_entropy`**: Entropy of noise channel bitstreams

### 2.2 Symbolic Signals (Compositional)
- **`interval_entropy`**: Shannon entropy of melodic intervals
- **`rhythmic_quantization_error`**: Deviation from absolute grid centers
- **`harmonic_vocab_size`**: Number of unique chord types used
- **`phrase_recurrence_ratio`**: Percentage of phrases that repeat ≥ 90% similarity

### 2.3 Perceptual Signals (Audio / MIR)
- **`spectral_centroid_drift`**: Variance in spectral brightness over time
- **`onset_density`**: Perceived rhythmic events per second
- **`timbre_cluster_count`**: Number of distinct MFCC clusters detected

---

## 3. SHARED EMBEDDING PROJECTION

Music-domain signals are fused into a `MusicStyleVector` and projected into the shared `HelixEmbedding` format via Stage 9.

**Projection mapping** (signal → embedding axis):

| HelixEmbedding Axis | Primary Music Signal | Normalization Method |
|---------------------|----------------------|----------------------|
| `structure` | `phrase_recurrence_ratio` | Domain baseline: VGM loop-density |
| `complexity` | `rhythmic_quantization_error` | Inverse of deviation from grid |
| `repetition` | `hierarchical_motif_depth` | Normalized count of nested repeats |
| `density` | `register_write_density` | Log-normalized per-chip event rate |
| `variation` | `interval_entropy` | Percentile of composer-specific variance |
| `expression` | `spectral_transition_slope` | Sigmoid-mapped slope of timbral shifts |

**Non-equivalence rule**: The embedding axis names (`structure`, `complexity`, etc.) are shared system-wide. The music signal names are domain-local. The mapping above is explicit and should not be treated as naming equivalence.

**Projection schema versioning**: A `projection_schema` field should be stamped on all music embedding artifacts to enable comparison across schema versions. (Not yet implemented — see §4 status.)

---

## 4. PIPELINE STAGES

| Stage | Responsibility | Input | Output | Status |
|-------|----------------|-------|--------|--------|
| 1 | Ingestion | Source path | Library index entry | ✅ |
| 2 | Decoding | VGM/FLAC/MIDI | ControlSequence / Audio / SymbolicScore | ✅ |
| 3 | Static parse | Header data | Metadata artifact | ✅ |
| 4 | Causal trace | Register log | Timeline trace artifact | ✅ |
| 5 | Symbolic extraction | Event stream | SymbolicScore artifact | ✅ |
| 6 | MIR analysis | Rendered audio | SignalProfile artifact | ✅ |
| 7 | Motif detection | Phrasal data | Motif entity candidates | ✅ |
| 8 | Feature fusion | All artifacts | MusicStyleVector | ✅ |
| 9 | HelixEmbedding projection | MusicStyleVector | HelixEmbedding artifact | ⚠️ Partial |
| 10 | Atlas compilation | All artifacts | Atlas entities | ⚠️ Partial |

---

## 5. ARTIFACT SCHEMAS

### ControlSequence (`artifacts/music/<id>/control_seq.json`)
```json
{
  "track_id": "...",
  "chip_target": "YM2612",
  "events": [...],
  "timing_vblank": true
}
```

### SymbolicScore (`artifacts/music/<id>/symbolic.json`)
```json
{
  "track_id": "...",
  "notes": [...],
  "interval_histogram": {}
}
```

### SignalProfile (`artifacts/music/<id>/signal.json`)
```json
{
  "track_id": "...",
  "spectral_centroid": 2800.3,
  "onset_density": 4.2
}
```

### HelixEmbedding (`artifacts/music/<id>/embedding.json`)
```json
{
  "complexity": 0.71,
  "structure": 0.88,
  "repetition": 0.64,
  "density": 0.53,
  "expression": 0.41,
  "variation": 0.37,
  "confidence": 0.72,
  "domain": "music",
  "source_vector": "music_style_vector",
  "projection_schema": "music_v1"
}
```

---

## 6. VALIDATION RULES

- **Deterministic check**: Re-running the pipeline on a fixed source hash must produce identical HelixEmbedding coordinates
- **Cross-layer alignment**: Symbolic score durations must match perceptual waveform durations within 5ms
- **Library reference compliance**: Any chip-level measurement must be validated against `codex/library/audio/chips/` specifications
- **Null model guard**: A null corpus (randomized register-write sequences) must not produce embedding confidence above floor — not yet implemented

---

## 7. METRIC SPACE / SIMILARITY / DISTANCE

The HelixEmbedding metric space uses Euclidean distance normalized by √6:

```
distance(a, b) = euclidean(a, b) / sqrt(6)          ∈ [0, 1]
similarity(a, b) = 1 - distance(a, b)               ∈ [0, 1]
```

**Triangle inequality** applies to **distance**, not similarity:
```
d(a, c) ≤ d(a, b) + d(b, c)
```

A violation is a `STRUCTURAL_FAILURE` and must be flagged before Atlas promotion.

---

## 8. ENTRY / HSL INTEGRATION STATE

**Target**: HSL commands `INGEST_TRACK music.<id>`, `ANALYZE_TRACK music.<id>`, `RUN operator:MUSIC`\
**Current**: **COMPLETE**. The Music Operator is registered in the core system, enabling real-time session reasoning, semantic retrieval, and safe execution loops directly via HSL.

---

## 9. THRESHOLDS AND CALIBRATION

| Threshold | Value | Status |
|-----------|-------|--------|
| Minimum embedding confidence | 0.30 | Provisional — global default, not music-calibrated |
| Cross-layer alignment tolerance | 5ms | Defined; calibration basis unknown |
| Phrase recurrence similarity floor | 90% | Defined; not validated against null music corpus |

Calibration procedure for confidence floor: establish null corpus → compute embedding distribution → set at `mean + 2 * std`. Not yet performed for music domain.

---

## 10. PROMOTION CONDITIONS

Invariant candidates must pass the global 6-criterion promotion gate (see `docs/GOVERNANCE.md`):
1. Reproducibility (≥ 2 independent runs)
2. Multi-domain observation (≥ 2 domains)
3. Minimum confidence ≥ threshold
4. Pass rate ≥ 80%
5. Signal above minimum threshold
6. Latest probe version used

---

## 12. VISUAL INVARIANTS AND ARTWORK POLICY

### 12.1 Canonical Visual Plane

Helix enforces an external, filesystem-based artwork policy for long-term stability and player
independence.

- **Primary Source**: `cover.*` located at the album/folder root.
- **Embedded Art**: Deprecated as a primary strategy. Helix ignores embedded art for
  library-level visual identity to avoid per-track redundancy and cache inconsistency.

### 12.2 Quality and Selection Heuristics (Digital-First)

Helix formally prioritizes **Digital-Native** assets:

- **Resolution**: Target ≥ 1000px. Minimum floor 500px.
- **Squareness**: Tolerance ±5% aspect ratio.
- **Preference order**:
  1. **IGN Digital** (high-res square crop, key visual focus)
  2. **VGMdb Digital** (official digital album art)
  3. **Physical Scans** (fallback only if digital is unavailable)
- **Screenshot Rejection**: High-aspect-ratio captures or title-screen rips are flagged as
  `screenshot_risk` and marked for replacement.

### 12.3 Visual Provenance (`album.json` → `visual`)

All album entities must track artwork provenance:

```json
"visual": {
  "canonical_path": "cover.jpg",
  "resolution": [1000, 1000],
  "is_square": true,
  "branding_status": "clean",
  "source_type": "ign_digital",
  "confidence": 0.98,
  "is_digital_native": true
}
```

---

## 14. MUSIC BRIDGE (FOOBAR INTEGRATION)

The Music Bridge is the primary integration layer between Foobar2000 and the Helix Music
Substrate.

### 14.1 Metadata Plane (`external-tags.db`)

- **Authority**: Authoritative source for human-edited metadata.
- **Access**: Read-only via `MetadataAdapter`.
- **Normalization**: Translates file:// URIs into canonical Helix paths.
- **Decoding**: Custom binary decoder for Foobar's internal metadata blobs.

### 14.2 Runtime Plane (Beefweb)

- **Authority**: Authoritative source for live playback telemetry.
- **Connectivity**: REST API via `BeefwebClient` (default port 8880).
- **Graceful Degradation**: Core adapters must return `is_live=False` without raising if
  connection fails.

### 14.3 Identity Resolution Policy

Tracks are resolved across planes using a prioritized matching strategy:

1. **Exact URI**: Normalized file:// match.
2. **Path Variants**: Handles case and slash-count variations.
3. **Semantic Aliases**: Matches against `AliasGraph` (Japanese/Romaji/old-name support).
4. **Fuzzy Filename**: Last-resort matching for renamed folders.

### 14.4 Writeback Policy

- **Status**: Read-only (Stable Read Contract)
- **Write-Locked Fields**: title, artist, album, year, genre.
- **Write-Eligible Fields**: platform, sound_chip, composer (attribution outcome), note.
- **Audit Requirement**: All writeback must be logged and reversible via Helix internal state.

---

## 15. ALIAS GRAPH AND IDENTITY RESOLUTION

Identity resolution establishes the conservative enrichment layer for the Helix identity graph.
It introduces a multi-signal evidence model to link local curated tracks with external
authoritative records while strictly preventing false positives.

### 15.1 Evidence Model (Multi-Signal)

Identity resolution is determined by an aggregate of signals, never by title similarity alone:

- **Alias Match**: Exact or normalized title match against Helix codex or external records.
- **Artist/Composer Match**: Comparison of local artist/album_artist tags with external performers/composers.
- **Platform Match**: Verification of hardware platform (SNES, PS1, Arcade) via title suffixes or platform tags.
- **Year Proximity**: Validation that local release year is within ±2 years of the external record.
- **Track Count Overlap**: Ratio of local tracks matching the external set (supports curated subsets).

### 15.2 Contradiction Gates

A single severe contradiction blocks auto-acceptance (Tier A) of a candidate:

- **Franchise Mismatch**: e.g., matching a Final Fantasy local track to a Dragon Quest external release.
- **Composer Mismatch**: Significant conflict in authoritative attribution.
- **Year Mismatch**: Gap > 5 years (excepting recognized remasters/re-releases).
- **Platform Mismatch**: e.g., local SNES suffix matching to a Sega Genesis external record.

### 15.3 Acceptance Tiers

- **TIER_A (Auto-Accept)**: High-confidence, multi-signal match with zero contradictions.
- **TIER_B (Review-Preferred)**: Strong match but single-signal or high-risk; requires human audit.
- **TIER_C (Ambiguous)**: Multiple potential candidates with similar scores; persistent in review queue.
- **TIER_D (Reject)**: Confirmed contradictions or insufficient evidence.

### 15.4 Materialization Policy

- **Gated Acceptance**: Candidates are not automatically materialized until they pass the Audit Gate.
- **Audit-Driven Gating**: Certain categories (e.g., `folder_recovery`) are permanently gated to REVIEW_ONLY regardless of score.
- **Generic Title Blacklist**: Titles such as 'Best Selection' or 'Disk 1' are blocked from Tier A to prevent collision clusters.
- **Materialization Priority**: Only Tier A candidates that pass the category-based safety policy are promoted to the permanent Helix Alias Graph.

### 15.5 Audit Framework

- **Precision Audits**: Systematic measurement of Tier A precision by category.
- **Failure Pattern Discovery**: Identifying recurring risks such as curated-subset overreach or folder-name false authority.
- **Threshold Tightening**: Adjusting acceptance logic based on observed audit data (e.g., minimum overlap > 80% for auto-accept).
- **Manual Review Queue Upgrades**: Prioritization of high-impact candidates (HIGH | MED | LOW) for manual audit.

---

## 16. PRACTICAL TASTE GRAPH RETRIEVAL

Practical retrieval moves the music substrate from a metadata pipeline to an operational
retrieval engine. It leverages audited identity and structural tags to enable taste-space
navigation.

### 16.1 Taste Retrieval Engine

The retrieval layer operates over the **Helix Taste Graph**, a directed, weighted graph where:

- **Nodes**: Canonical Helix track IDs (`music.track.*`).
- **Edges**: Similarity weights derived from feature fusion (StyleVector distance) and structural tag overlap.
- **Evidence**: Shared traits (composers, tags, release context) stored per edge.

**Retrieval standard**: `find_neighbors(track_id, limit) -> List[TasteNeighbor]`

- **Weight**: 0.0 to 1.0 (cosine similarity, normalized).
- **Graceful Fallback**: If vector data is missing, falls back to structural tag intersection count.

### 16.2 Canon Extraction

"Canon" identifies the structural anchors of the library via **Graph Centrality**:

- **Centrality Score**: Sum of incoming edge weights from nodes sharing the same structural tag.
- **Anchor Logic**: Tracks explicitly listed in `structural_tag_catalog.json` → `anchors` receive a 2.0× centrality boost.
- **Representative Selection**: The top N tracks by centrality for a given tag are designated as its Canon Set.

### 16.3 Explanation Layer

Every neighbor link is accompanied by a **TrackExplanation**:

- **Shared Traits**: List of specific tags or composer fingerprints.
- **Reasoning String**: Human-readable explanation (e.g., "Both tracks utilize the 'groove_engine' structural role").
- **Weight Attribution**: Breakdown of how much similarity comes from Style (vectors) vs. Context (tags/composers).

### 16.4 Incremental Sync Protocol (Relational)

The legacy JSON-based library is synced to a relational SQLite index to support 100k+ track retrieval:

- **`helix_id` Anchor**: Maps every foobar `file_path` to a semantic slug.
- **`semantic_tags` Table**: Fully indexed structural tags.
- **Smart Re-index**: Uses file modification timestamps (`st_mtime`) compared against `ingested_ts` to skip unchanged records, enabling sub-minute library updates.

