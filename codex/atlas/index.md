# Helix Atlas

*Last updated: 2026-03-18*

The Atlas is Helix's structured entity memory. Raw data lives in `data/` and `execution/`. Only resolved, validated entities live here. All writes pass through the Atlas Compiler or explicit Atlas Candidate promotion.

---

## Structure

```
codex/atlas/
├── music/                        ← Resolved music entities (domain-first)
│   ├── sound_chips/              ← Hardware synthesis chips
│   ├── sound_drivers/            ← Software audio driver engines
│   ├── sound_engines/            ← High-level sound engine entities
│   ├── sound_teams/              ← Studio/team entities
│   ├── artists/                  ← Individual composer/artist entities
│   ├── albums/                   ← Album entities
│   ├── tracks/                   ← Individual track entities (reparsed on demand)
│   ├── games/                    ← Game entities (cross-referenced with music)
│   ├── franchises/               ← Franchise groupings
│   └── hardware_platforms/       ← Platform entities
│
├── embeddings/                   ← Computed structural embeddings
│   └── music/
│       ├── tracks/               ← Per-track CCS embeddings
│       ├── artists/              ← Artist-aggregate CCS embeddings
│       ├── albums/               ← Album-aggregate CCS embeddings
│       └── PIPELINE.md           ← Embedding computation pipeline
│
├── invariants/                   ← Proven invariants, laws, and models
│
└── index/                        ← Cross-entity indexes and integrity reports
    ├── entity_graph.json         ← Node/edge graph of resolved entities
    ├── motif_graph/              ← Per-track motif relationships
    └── system_integrity/         ← Helix system integrity snapshots
```

---

## Music Entities

### Sound Chips

| Entity | File |
|--------|------|
| YM2612 (Yamaha OPN2) | `music/sound_chips/ym2612.json` |

### Sound Drivers

| Entity | File |
|--------|------|
| GEMS v2.0 (Genesis Editor for Music and Sound) | `music/sound_drivers/gems.json` |

### Artists

| Entity | File |
|--------|------|
| Tatsuyuki Maeda | `music/artists/tatsuyuki_maeda.json` |
| Masayuki Nagao | `music/artists/masayuki_nagao.json` |
| Morihiko Akiyama | `music/artists/morihiko_akiyama.json` |
| Hirofumi Murasaki | `music/artists/hirofumi_murasaki.json` |

### Tracks / Albums / Games / Platforms

Not yet populated. Will be filled when the music library is reparsed. Entity files use slug-only filenames (`{slug}.json`). `entity_id` with full domain prefix (`music.track:{slug}`) is stored inside the file.

---

## Embeddings

CCS (Cognitive Coordinate System) structural embeddings. 6-axis characterization of music entities derived from observable features. Schema: `core/models/ccs/schema/ccs_schema.json`.

### Track Embeddings (`embeddings/music/tracks/`)

| Entity | File |
|--------|------|
| Sonic 3D Blast — Rusty Ruin Act 1 | `embeddings/music/tracks/sonic_3d_blast_rusty_ruin_act1.json` |

### Artist Aggregates (`embeddings/music/artists/`)

| Entity | File |
|--------|------|
| Tatsuyuki Maeda | `embeddings/music/artists/tatsuyuki_maeda.json` |

### Album Aggregates (`embeddings/music/albums/`)

Not yet populated. Will be computed after track embeddings are available.

---

## Invariants

| Name | File | Status |
|------|------|--------|
| Composer Style Signature | `invariants/composer_style_signature.md` | Active |
| Decision Compression | `invariants/decision_compression.md` | Verified (86% pass rate) |
| Epistemic Irreversibility | `invariants/epistemic_irreversibility.md` | Active |
| Law: Epistemic Irreversibility — Noise Scaling | `invariants/law_epistemic_irreversibility_noise.md` | Active |
| Law: Kuramoto Finite-Size Scaling | `invariants/law_kuramoto_finite_size.md` | Active |
| Law: Kuramoto Synchronization Phase Transition | `invariants/law_kuramoto_transition.md` | Active |
| Local Incompleteness | `invariants/local_incompleteness.md` | Active |
| Oscillator Locking | `invariants/oscillator_locking.md` | Verified (100% pass rate) |
| Regime Transition | `invariants/regime_transition.md` | Active |
| Composer Style Space (model) | `invariants/composer_style_space.md` | Active |
| Control Subspace Collapse (model) | `invariants/control_subspace_collapse.md` | Active |

---

## Entity Naming Convention

- Filename: slug only — `{slug}.json`
- `entity_id` inside file: `{domain}.{type}:{slug}` (e.g., `music.sound_chip:ym2612`)
- Colons are illegal in Windows filenames — the full entity_id is stored inside the JSON, never in the filename

---

## Entity Lifecycle

```
Raw Data → Feature Extraction → Artifact (data/processed/ or execution/runs/)
         → Atlas Candidate    → Atlas Compiler
         → Atlas Entity       → codex/atlas/{domain}/{type}/{slug}.json
```

Artifacts are disposable and recomputable. Atlas entities are resolved and reusable. Do not treat Atlas entities as artifacts.
