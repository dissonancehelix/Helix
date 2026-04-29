# Foobar as Local Music Atlas

## Domain Role

Foobar functions as the operator's **interactive local music atlas**, not merely a player.

It provides:
- stable owned archive
- searchable library
- radio / intake surface
- loved-track return anchors
- last-played traversal memory
- custom metadata
- album art / place-memory anchors
- play-count return signals
- VGM operational grounding

## Operational Model

Foobar organizes music through:
- Library tab
- Radio tab
- Loved tab
- Last played tab
- filters / search
- album / artist / composer grouping
- track table
- metadata fields
- playback history
- loved / play-count markers

### Important custom VGM metadata

- Platform
- Sound Chip
- Sound Team
- Franchise
- Album Artist
- Composer / Artist
- Year
- Genre

These fields are **operational context**, not decoration: they record the hardware constraint a piece of music was authored under, which is how the operator distinguishes VGM material from other archive contents.

## Dissonance Mapping

Supports:
- `state_carrying_aliveness`
- `compatible_mindprint`
- `archive_worthy_return`
- `self_describing_architecture`
- `minimal_surface_nested_depth`
- `domain_grounding_rule`
- `low_end_continuity`
- `vgm_hardware_constraint`
- `controlled_signal_intake`

(IDs marked seed in `core/map/patterns.yaml` are valid anchors; IDs not yet present are flagged for Phase 3 pattern admission.)

## Evidence Anchors

From recent screenshots and live-state observation:

- **Library / Radio / Loved / Last played tabs** — four discrete return paths into the archive, each with a different temporal/affective grain.
- **James Blake filter while VGM/local archive remains active** — the archive is filterable without losing the rest of the library; the filter is a view, not a reduction.
- **VGM track grouping by album/composer/game** — composer and franchise are first-class grouping axes alongside album.
- **Custom metadata for Toy Story (SNES):** Platform = Super NES, Sound Chip = SPC700, Sound Team = Swallow Studios. Hardware is preserved as evidence.
- **Decap Attack (Mega Drive):** Sound Chip = YM2612, Album Artist = Fumito Tamayama, Artist (Stage 1) = Hiroto Kanno. Composer-vs-album-artist split is preserved.
- **DI.FM / Jazz Radio / SomaFM** — radio entries as *controlled* signal intake (curated channels, not algorithmic feed).
- **Play counts and loved icons** — return signals; the archive remembers what has been returned to and how often.
- **Album art** — place-memory anchor; visual identity for return navigation.

## Dataset Notes

- Foobar's library state is the canonical local source of truth for the archive.
- Snapshots/exports (when produced by `domains/music/tools/bridge/`) land under `domains/music/data/library/foobar/` or the existing pipeline convention. Phase 2 does not yet produce these.
- Last.fm and Spotify normalized exports under `data/` are *parallel* evidence streams; they do not replace foobar — they cross-reference it.

## False Positives

A shallow model would read this as:
- "likes music players"
- "likes metadata"
- "likes VGM"
- "likes dark themes"
- "likes organizing files"

Correct interpretation: **foobar is a navigable archive that preserves paths back into music objects.** The metadata, the loved markers, the play counts, and the radio entries together form a return-system, not a preference list.

> Compression: foobar is not a feed; it is a returnable archive with doors.

## Anomalies / Open Questions

- Pattern IDs `domain_grounding_rule` and `low_end_continuity` are referenced here but not yet seeded in `core/map/patterns.yaml`. Promote to seed, or rename, in a later pass.
- Are radio channels (DI.FM/Jazz Radio/SomaFM) better modeled as a separate evidence anchor (controlled-intake) than as part of the local atlas? Decide in Phase 3.

## Upward Links

- `core/map/examples.yaml` → `music.foobar_local_music_atlas`, `music.foobar_vgm_hardware_metadata`
- `core/map/links.yaml` → connections from these examples to relevant patterns and to this README
- [DISSONANCE.md](../../../DISSONANCE.md) → keep only a compressed anchor; full local detail lives here

## Downward Links

- Screenshots / exports / foobar snapshots — once stored under `domains/music/data/library/foobar/`
- `data/` paths once Phase 3A produces a snapshot
- Future `domains/music/reports/` outputs from `domains/music/tools/bridge/`

