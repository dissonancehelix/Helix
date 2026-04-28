# Music Bridge Phase 1 — Metadata, Runtime, and Identity Contract

**Status**: ✅ COMPLETED
**Phase Scope**: Read-only integration contract for foobar metadata and runtime planes.

## Phase Overview
Music Bridge Phase 1 stabilizes the integration between foobar2000 and Helix. It explicitly distinguishes between the **Metadata Plane** (authoritative tags in `external-tags.db`) and the **Runtime Plane** (live telemetry via Beefweb). This phase establishes a robust identity resolution layer that handles naming variations and metadata gaps using the Helix Alias Graph.

### Key Components Built
1.  **Metadata Adapter**: Directly reads and decodes the foobar-facing `external-tags.db`. Decodes complex binary blobs into normalized `TrackMeta` records.
2.  **Runtime Adapter**: Interfaces with Beefweb (localhost:8880) to observe current playback state, track progress, and active playlist details.
3.  **Identity Resolver**: A high-tolerance matching engine that connects live tracks to their metadata identity using paths, variants, and semantic aliases from the Helix codex.
4.  **Diagnostics Suite**: Comprehensive health reporting for both integration planes, measuring connectivity, coverage, and resolution success.

## Deliverables Generated
- **`foobar_bridge_contract.md`**: Defines governance and rules for Foobar-Helix integration.
- **`writeback_preparation_policy.json`**: Explicitly maps writeable vs. internal-only fields to prepare for future Stage 14 writeback.
- **Diagnostics Reports**: 
    - `bridge_health_report.json`
    - `foobar_metadata_adapter_report.json`
    - `beefweb_runtime_adapter_report.json`
    - `bridge_identity_resolution_report.json`

## Resolution Statistics
Based on the current bridge snapshot:
- **Metadata Plane**: ~71,421 tracks mapped in external-tags.db.
- **Alias Graph**: ~2,804 entities seeded from codex (Phase 1 seed).
- **Runtime Connectivity**: Live via Beefweb (requires auth for some telemetry).

## Path to Phase 14 (Writeback)
The bridge is currently read-only. We have defined the `writeable_foobar_tags` policy which includes platform, sound_chip, and composer (when verified). Bulk writeback is locked until formal Stage 14 promotion.
