# Substrate Capability Vector Embedding Pipeline — Music Domain

**Schema**: `core/models/substrate/schema/substrate_schema.json`
**Spec**: `core/models/substrate/SPEC.md`
**Validation**: `core/models/substrate/tests/validation_protocol.md`

---

## Pipeline Stages

```
Raw Data (VGM, tags, metadata)
    ↓
[1] Feature Extraction
    ↓
[2] Substrate Capability Vector Axis Computation
    ↓
[3] Evidence Assembly
    ↓
[4] Schema Validation
    ↓
[5] Drift Detection
    ↓
[6] Write to atlas/embeddings/music/tracks/{slug}.json
    ↓
[7] Propagate to artist/album aggregates
```

---

## Stage 1 — Feature Extraction

Extract measurable signals from available data sources. Signal priority (highest to lowest):

| Priority | Source | Signals Available |
|----------|--------|-----------------|
| 1 | Audio analysis (waveform + VGM parse) | note_density, pitch_class_entropy, harmonic_rhythm, timbre_change_rate, transition_sharpness |
| 2 | VGM structural parse (driver-level) | loop_type, section_boundaries, fm_channels_used, driver_opcodes |
| 3 | Metadata tags | tempo_bpm, time_signature, detected_scale, composer |
| 4 | Atlas entity cross-reference | driver name → driver structural properties |

All signals extracted must be named and stored in `evidence.signals`. Unextracted signals reduce confidence.

---

## Stage 2 — Substrate Capability Vector Axis Computation

Apply the formulas defined in `core/models/substrate/SPEC.md` Section 2. Rules:

- Use only signals extracted in Stage 1
- Apply domain normalization against the current corpus baseline
- If a required input signal is missing, exclude it from the formula and apply the partial confidence penalty
- Round to 4 decimal places only at output time, not during intermediate computation

---

## Stage 3 — Evidence Assembly

Populate the `evidence` block:

```json
{
  "signals": [ ...all signals from Stage 1... ],
  "source_features": [ ...file paths, driver name, hardware, analysis version... ],
  "notes": "...document any gaps, approximations, edge cases..."
}
```

`notes` must explicitly mention:
- Any axis that used fewer than its full input set
- Any normalization approximation
- Any driver-specific structural constraints that influenced axis values

---

## Stage 4 — Schema Validation

Validate the assembled embedding against `core/models/substrate/schema/substrate_schema.json`.

- All 6 axes present and in [0.0, 1.0] → proceed
- Missing or out-of-range axis → reject, do not write to atlas
- Evidence coherence check (see validation protocol Section 3) → log warnings, do not block

---

## Stage 5 — Drift Detection

If a prior embedding exists for this entity:

```
d = √Σ(axis_current - axis_prior)²

d < 0.05   → overwrite silently
d < 0.20   → overwrite + log drift event
d ≥ 0.20   → archive prior, flag for review, do NOT overwrite
```

Archive naming:
```
atlas/embeddings/music/tracks/{slug}.v{YYYYMMDD_HHMMSS}.json
```

If no prior embedding exists, write directly.

---

## Stage 6 — Write Track Embedding

Write to:
```
atlas/embeddings/music/tracks/{slug}.json
```

Slug is the track's `entity_id` suffix (after the colon), e.g., `sonic_3d_blast_rusty_ruin_act1`.

File is the single authoritative Substrate Capability Vector embedding for this track. It is not a raw artifact — it is a resolved entity. Overwriting requires drift check to pass.

---

## Stage 7 — Aggregate Propagation

After any track embedding is written or updated:

1. **Artist aggregate**: Recompute duration-weighted mean across all tracks attributed to the artist. Write to `atlas/embeddings/music/artists/{artist_slug}.json`.
2. **Album aggregate**: Recompute duration-weighted mean across all tracks in the album. Write to `atlas/embeddings/music/albums/{album_slug}.json`.

Aggregate computation rules:
- Weight: track duration in seconds (if available); else equal weight
- Carry `source_version` from the newest track embedding used
- `confidence` = mean of constituent track confidences, reduced by 10% per missing track

---

## Reparse Behavior

When the music library is reparsed:

1. All existing track embeddings in `atlas/embeddings/music/tracks/` are read as priors
2. New embeddings are computed for each reparsed track
3. Drift detection runs before any write
4. Tracks that were NOT reparsed retain their existing embeddings unchanged
5. Artist and album aggregates are recomputed only for artists/albums with at least one updated track

**Never** delete an existing embedding without drift detection. **Never** batch-overwrite all embeddings without individual drift comparison.

---

## Invariant

Same input → same embedding. If reparse produces different values for the same underlying VGM/tag data, the discrepancy is a pipeline bug, not expected behavior.

