# Substrate Capability Vector

**Location**: `core/models/substrate/`
**Version**: 1.1.0
**Status**: Standalone module. Not integrated with other modules.

---

## What It Is

Substrate Capability Vector is a 6-axis structural embedding system. It maps any entity with measurable structural properties to a point in [0.0, 1.0]⁶. Substrate Capability Vector embeddings are not absolute descriptions of structure, but constrained estimates derived from observable features under defined conditions.

The six axes:

| Axis | What It Measures |
|------|-----------------|
| `attractor_stability` | How consistently structural patterns repeat |
| `generative_constraint` | How tightly the pitch/rhythm/timbre space is rule-bound |
| `recurrence_depth` | How many hierarchical levels of recurrence exist |
| `structural_density` | Event rate per unit time, domain-normalized |
| `control_entropy` | Distribution entropy across pitch, dynamics, articulation |
| `basin_permeability` | How gradual section transitions are |

All values are in [0.0, 1.0]. All values are derived from observable features. Embeddings are **model-dependent reconstructions**; results depend on:
* available signals
* normalization reference
* domain adapter design

---

## What It Is Not

- Not a genre classifier
- Not a quality metric
- Not a perceptual model

---

## File Structure

```
core/models/substrate/
├── README.md                    ← this file
├── SPEC.md                      ← full technical specification
├── engine/                      
│   └── calculator.py            ← core computation engine
├── adapters/                    ← domain-specific mapping layers
│   ├── spotify.py               ← Spotify feature mapping
│   └── music/                   ← music domain signals & mappings
│       ├── signals.md
│       └── mappings.md
├── schema/
│   └── substrate_schema.json          ← strict JSON Schema (draft-07)
├── examples/
│   ├── music_track.json         ← single track embedding (GEMS driver)
│   └── game_system.json         ← soundtrack aggregate (Streets of Rage 2)
└── tests/
    └── validation_protocol.md   ← validation methodology
```

---

## Usage

### Embed an entity

Produce a JSON file conforming to `schema/substrate_schema.json`:

```json
{
  "entity_id": "music.track:your_slug",
  "scv_version": "1.0.0",
  "capability_vector": {
    "attractor_stability": 0.82,
    "generative_constraint": 0.65,
    "recurrence_depth": 0.63,
    "structural_density": 0.76,
    "control_entropy": 0.71,
    "basin_permeability": 0.27
  },
  "evidence": {
    "signals": [...],
    "source_features": [...],
    "notes": "..."
  },
  "confidence": 0.71
}
```

All 6 axes are required. Omitting any axis invalidates the embedding.

The `evidence.notes` or `source_version` field must record the normalization reference used (corpus name + method). See `SPEC.md` Section 6.

### Validate an embedding

Check against the schema, verify evidence coherence, and confirm determinism per `tests/validation_protocol.md`.

### Compare two embeddings

Euclidean distance and alignment score are defined in `SPEC.md` Section 7:

```
d = √Σ(Aᵢ − Bᵢ)²                          # Euclidean distance, range [0, √6]
alignment_score = 1 − (d / √6)             # normalized to [0, 1]
```

`alignment_score = 1.0` means identical structure. `0.0` means maximally opposite. Only compare embeddings sharing the same `scv_version`. Comparisons involving `confidence < 0.30` must be flagged.

### Interpret an embedding

A point near `[1, 1, 1, 1, 1, 1]` describes a maximally structured, dense, varied, and fluidy-transitioning entity with deep recurrence and tight constraints.

A point near `[0, 0, 0, 0, 0, 0]` describes a completely through-composed, sparse, uniform, hard-cut, unconstrained entity.

Most entities occupy a specific subregion of this space. Clustering by Substrate Capability Vector coordinates groups entities by structural similarity, not metadata.

---

## Extending to Other Domains

Substrate Capability Vector is domain-agnostic. The axes apply to any sequential or compositional entity. To extend Substrate Capability Vector to a new domain:

1. Define observable inputs for each axis formula (see `SPEC.md` Section 2)
2. Establish a domain normalization baseline
3. Create a domain-specific computation adapter
4. Do not modify `SPEC.md` or `schema/ccs_schema.json`
