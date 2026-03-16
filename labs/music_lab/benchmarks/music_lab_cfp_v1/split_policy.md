# music_lab_cfp_v1 — Dataset Split Policy

## Inclusion Criteria

A composer is included if:
- ≥ 10 tracks with ground-truth attribution (ARTIST tag in VGM header)
- ≥ 20 reconstructed note events per track (Tier C symbolic requirement)
- Track parses without error in Tier A (VGM/VGZ static parse)

Tracks with attribution like "Unknown", "Various", or empty ARTIST field are excluded.

## Split Definitions

Three independent splits are required:

### 1. Random Split
- 70% train / 15% val / 15% test
- Stratified by composer (each composer appears in all three splits)
- Seed: `42`
- Unit: individual tracks

### 2. Game-Held-Out Split
- Test set: all tracks from a held-out game (one game per composer, selected by largest track count)
- Train set: all remaining tracks for that composer from other games
- This tests generalisation across games — the harder, more realistic evaluation
- Leakage control: no tracks from the same `ALBUM` (game) appear in both train and test

### 3. Composer-Held-Out Split
- Leave-one-composer-out cross-validation
- Used to measure upper bound of inter-composer discriminability
- Run only on the top-20 composers by track count

## Leakage Controls

- Tracks from the same physical file (same path) cannot span splits
- Tracks from the same game title cannot appear in both train and test in the game-held-out split
- If a composer appears in only one game, they are excluded from the game-held-out split

## Label Definition

Ground-truth label = normalised ARTIST tag from VGM header:
- Lowercased, stripped, de-duped (e.g. "Masato Nakamura" and "M. Nakamura" treated as different)
- No automated alias resolution in v1 (manual alias table in future versions)

## Class Balance

- If any class has > 5× the median track count, apply max-cap downsampling (random seed 42)
- Report pre- and post-cap class distribution in results

## Artifact Output

`artifacts/benchmarks/music_lab_cfp_v1/split_manifest.json`:
```json
{
  "split": "random|game_held_out|composer_held_out",
  "seed": 42,
  "train_ids": [...],
  "val_ids":   [...],
  "test_ids":  [...],
  "composer_track_counts": {...}
}
```
