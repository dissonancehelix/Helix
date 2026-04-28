# Music Bridge

## Purpose

Connect **foobar2000** to **Helix** without making foobar dependent on Helix.

> Foobar is the hands; Helix is the music-cognition behind the hands.

## Observability-first contract

`music_bridge` follows the same model as [`system/tools/workstation_bridge/`](../workstation_bridge/README.md):

- **Foobar remains independent.** No dependency inversion.
- **First real integration is a read-only export/snapshot.** Build sensor trust before actor trust.
- **Playlist and tag outputs are proposals**, not writes, until approval gates exist.
- **No writeback** until all six trust artifacts ship together: target identity, before/after diff, backup path, rollback path, source evidence, explicit operator approval.

Bridges connect without absorbing. This is the foobar-side application of that law.

## Division of authority

**Foobar remains:**
- playback surface
- interactive library browser
- Loved / Last-played / Radio interfaces
- local archive UI
- metadata editor

**Helix provides:**
- semantic interpretation
- pattern mapping (`model/map/patterns.yaml`)
- domain analysis (`model/domains/music/`)
- playlist generation
- tag suggestions
- report generation
- drift-safe evidence linking

## Initial mode

**READ ONLY.** The bridge crosses *into* Helix; it does not cross back.

### Allowed in Phase 2
- Document the bridge contract.
- Define expected inputs/outputs.
- Define snapshot/export concepts.
- Define future scripts (interface only).
- Define safety rules.

### Forbidden in Phase 2
- No metadata writeback.
- No automatic playlist writeback.
- No moving library files.
- No changing foobar configuration.
- No touching the playback pipeline.

## Future scripts (interface only — not necessarily implemented now)

- `export_foobar_snapshot.py` — read-only export of library state to a Helix-consumable form.
- `normalize_foobar_library.py` — produce a normalized record set under `data/` without writing back.
- `generate_helix_playlist.py` — generate a playlist *proposal* into `reports/analyses/music/`.
- `propose_tag_patches.py` — emit a diff-shaped proposal; never apply.
- `compare_foobar_to_lastfm.py` — cross-reference snapshot vs. Last.fm normalized exports under `data/`.

## Writeback gate (Phase 3+)

Any writeback must produce, in advance:

- **Target tracks** — explicit IDs, no globs.
- **Target fields** — named metadata fields.
- **Before/after diff** — full diff under `reports/analyses/music/`.
- **Backup path** — the snapshot taken immediately before writeback.
- **Rollback path** — the command/script that restores the backup.
- **Source evidence** — the `model/map/examples.yaml` ID and `data/` paths that justify the change.
- **Operator approval** — explicit, recorded, per-batch.

A writeback that cannot supply all seven artifacts does not run.

## Pre-existing content

This folder already contains Phase 1 bridge work (alias graph, audit engine, identity resolver, materialization gate, metadata adapter, runtime adapter, etc.) and an internal `music_bridge_phase1_summary.md`. That work predates this README and is preserved as-is. This README is the **architectural contract** for the bridge going forward; existing code should be reviewed against it in Phase 3.

## Phase 3 roadmap (documented, not implemented)

- **3A — Read-only Foobar Snapshot.** Exporter or expected export format; snapshot stored under `data/music/foobar/` (or existing convention); analysis written to `reports/analyses/music/foobar_snapshot_<date>.md`.
- **3B — Semantic Playlist Generation.** Helix produces playlist proposals from `model/map/patterns.yaml`; output to `reports/analyses/music/`. No foobar import until reviewed.
- **3C — Metadata/Tag Proposal.** Propose tag changes with diff, backup, explicit approval. Still no automatic writeback.
- **3D — Optional Foobar Component / Deep Integration.** Only after the bridge is stable. **No dependency inversion:** foobar remains independent.

## Final rule

This is not a platform takeover. Foobar remains the interactive archive. Helix becomes the semantic layer around it.

