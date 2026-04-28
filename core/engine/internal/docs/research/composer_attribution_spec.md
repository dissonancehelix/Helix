# Composer Attribution via Style Fingerprinting
## Helix Music Library — Research Spec

**Status:** Implementation ready (pending full library analysis pass)
**Probe:** `domains/music/model/probes/composer_attribution.py`
**Data source:** `labs/artifacts/analysis/` (post-pipeline)
**Atlas output:** `codex/atlas/music/composers/` + per-track `attribution` field

---

## Motivation

Most VGM releases credit multiple composers at the album level with no per-track
breakdown. Per-track credits in the library come from tag data — often the best
available guess, but unverified. Style fingerprinting uses the musical structure
extracted by the analysis pipeline (Tier AB) to:

1. **Confirm** tag-derived per-track credits for tracks in multi-composer albums
   (where the fingerprint agrees with the tag → `estimated_confirmed`)
2. **Contest** credits where the fingerprint strongly suggests a different composer
   (`contested`, with ranked candidates)
3. **Build** durable per-composer style signatures usable for musicological
   "talking music" — asking questions like "what harmonies did Maeda prefer?"
   or "how did Sakimoto's rhythmic density change between SNES and PS1 games?"

The library stores 1,370 multi-composer albums. All track credits are currently
`label='unknown'`. After the analysis pass + fingerprinting, contested tracks can
be manually reviewed using the ranked candidate list as a research starting point.

---

## Feature Vector

Each track gets a fixed-length feature vector built from its `TrackAnalysis`. Features
are grouped by type. All numeric features are z-score normalised within each chip
family before distance computation (YM2612, SPC700, etc. have different absolute
value ranges).

### Harmonic (from SymbolicFeatures / music21)
| Field | Type | Notes |
|-------|------|-------|
| `key_mode` | categorical | major / minor / dorian / aeolian / phrygian / lydian / mixolydian |
| `key_root` | categorical | C D E F G A B (+ accidentals) |
| `harmonic_rhythm` | float | avg chord changes per beat |
| `dissonance_density` | float | dissonant interval density |
| `chord_vocab_size` | int | distinct Roman numerals used |
| `iv_usage` | float | fraction of chords that are IV (Plagal tendency) |
| `v_usage` | float | fraction that are V (dominant-functional tendency) |
| `borrow_ratio` | float | fraction of chords borrowed from parallel mode |

### Melodic
| Field | Type | Notes |
|-------|------|-------|
| `pitch_range` | float | semitones between lowest and highest note in melody channel |
| `melodic_contour` | categorical | arch / ascending / descending / wave / flat |
| `step_ratio` | float | fraction of melodic intervals that are ≤2 semitones |
| `leap_ratio` | float | fraction ≥4 semitones |
| `upper_pitch_mean` | float | mean MIDI pitch of upper (melody) channel |

### Rhythmic
| Field | Type | Notes |
|-------|------|-------|
| `tempo_bpm` | float | estimated beat tempo |
| `rhythmic_entropy` | float | Shannon entropy of inter-onset intervals |
| `off_beat_ratio` | float | syncopation proxy |
| `pulse_coherence` | float | regularity of dominant pulse |

### Orchestration (VGM/SPC only)
| Field | Type | Notes |
|-------|------|-------|
| `active_voices` | int | channels used simultaneously |
| `bass_channel_mean_pitch` | float | mean MIDI pitch of bass channel |
| `channel_density_variance` | float | how evenly notes are distributed across channels |
| `loop_seam_present` | bool | composer habit of using VGM loop vs. fade |

---

## Composer Centroid

A composer centroid is computed from all **solo-credited** tracks with analysis_tier
`AB` or `B` (i.e. symbolic analysis present). Minimum corpus: **5 tracks**.

```
centroid[composer] = {
    feature_f: {
        mean:   avg(track[f] for track in solo_tracks),
        std:    std(track[f] for track in solo_tracks),
        n:      len(solo_tracks),
    }
    for each numeric feature f
}
```

Categorical features (key_mode, melodic_contour) are stored as frequency
distributions, not means.

**Solo-credited album definition:** `album.json` has exactly one `artist_id` AND
that entry resolves to a single composer (not a band or sound team aggregate).
All tracks within that album are used as training data for that composer's centroid.

**Caveat — guest tracks:** Some single-credited albums contain a few tracks by a
different composer (e.g. sound effects, bonus tracks). A self-consistency pass
re-scores all training tracks after the initial centroid is built. Any track that
scores > 0.65 for a *different* known composer is dropped from training. This
catches the common "album is credited to A but track 7 was actually by B" case.

---

## Attribution Scoring

For each track in a multi-composer album, we score against the album's composer pool
(all artists in `album.json`). Composers without centroids are excluded. We then
compare the fingerprint top-match against the tag-attributed composer:

1. **Normalise** each numeric feature to z-score using the composer's centroid
   std (or global std if centroid std < 0.01 to avoid division by zero).

2. **Weighted cosine similarity** between the track's feature vector and the
   composer's centroid mean vector. Feature weights are computed per chip family
   as Fisher's discriminant ratio:
   ```
   weight[f] = between_composer_variance[f] / within_composer_variance[f]
   ```
   Features with high between-composer variance relative to within-composer
   spread are the most discriminating (e.g. `key_mode`, `harmonic_rhythm`).

3. **Categorical penalty**: for each categorical feature that differs from the
   composer's modal value, subtract a small penalty weighted by that feature's
   discriminant ratio.

4. **Posterior**: normalise scores across candidate composers to sum to 1.
   This gives per-composer attribution probabilities.

5. **Confidence threshold**: attribute only if max probability > 0.55.
   Tracks with max < 0.55 are flagged `contested` rather than attributed.

---

## Output Schema

Per-track attribution output written back to the library record's `attribution` field:

```json
{
  "composition_credit": {
    "artist_ids": ["music.artist.tatsuyuki_maeda"],
    "label": "estimated",
    "confidence": 0.78,
    "source": "style_fingerprint_v1"
  },
  "candidates": [
    { "artist_id": "music.artist.tatsuyuki_maeda", "score": 0.78 },
    { "artist_id": "music.artist.masaharu_iwata",  "score": 0.22 }
  ],
  "features_used": ["key_mode", "harmonic_rhythm", "tempo_bpm", ...],
  "discriminant_weights": { "key_mode": 2.1, "harmonic_rhythm": 1.8, ... },
  "centroid_n": { "tatsuyuki_maeda": 34, "masaharu_iwata": 19 }
}
```

Atlas output: `codex/atlas/music/composers/{slug}.json` — each composer entity
gets a `style_centroid` block with mean/std per feature and the track set used.

---

## Validation

Before writing any attributions to the library, validate on held-out tracks:

1. Find albums where per-track credits **are** known (e.g. some Sonic games have
   interview-verified per-track credits, or bonus discs with individual credits).
2. Hold those out from centroid training.
3. Run attribution on held-out tracks and measure precision/recall.
4. Only proceed to write library attributions if precision > 0.70 on held-out set.

---

## Limitations & Failure Modes

- **Arrangement style ≠ composition style**: if a composer was constrained by a
  game's sound driver or director brief, their fingerprint may be suppressed.
- **Co-written tracks**: some tracks within a shared-credit album may actually be
  collaborative, not solo. Attribution will still force a single winner.
- **Thin solo corpus**: composers with < 10 solo tracks will have unreliable
  centroids. Flag these with reduced confidence.
- **Chip family mismatch**: comparing a YM2612 centroid to an SPC track will
  produce meaningless orchestration features. Fingerprinting is always done
  within the same chip family.
- **Sound team credits**: some albums credit "Capcom Sound Team" not individuals.
  These cannot be used as solo training data.

---

## Implementation Phases

1. **Phase 1 (current)**: Run full library analysis pass (122k tracks, overnight).
   Output: `artifacts/analysis/*.json` per track.

2. **Phase 2**: Run `composer_attribution.py --build-centroids` to compute style
   centroids from solo-credited tracks with Tier AB analysis. Output:
   `codex/atlas/music/composers/` entities.

3. **Phase 3**: Run `composer_attribution.py --score` on multi-composer albums to
   generate per-track attribution estimates. Validate on held-out set first.

4. **Phase 4**: Write winning attributions back to library records above confidence
   threshold. Flag contested tracks for manual review.

