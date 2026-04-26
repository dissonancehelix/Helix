# Helix ↔ Foobar2000 Bridge Contract (Phase 1)

**Version**: 1.0
**Status**: Authoritative Read Contract
**Last Updated**: 2026-03-31

## 1. Governance Split

The Helix Music Bridge maintains a strict separation of concerns between the Foobar2000 player and the Helix analysis environment.

| Layer | Responsibility | Authority | Source of Truth |
|-------|----------------|----------|-----------------|
| **Foobar2000** | Playback, human-edited tags | Metadata Plane | `external-tags.db` |
| **Beefweb** | Live runtime telemetry | Runtime Plane | `http://localhost:8880` |
| **Helix Bridge** | Integration adapter | Junction Layer | Memory |
| **Helix Music** | Deeper analysis, style vectors | Reasoning Plane | `codex/` and `artifacts/` |
| **Atlas** | Validated persistent memory | Long-term Identity | `codex/atlas/` |

---

## 2. Metadata Plane Contract (`external-tags.db`)

Helix reads Foobar-facing metadata from the specialized `external-tags.db` database.

- **Access Level**: Read-only (Phase 1).
- **Format**: SQLite 3.
- **Table**: `tags`
- **Columns**: `path` (file:// URI), `meta` (binary blob).
- **Normalization**: All URIs must be normalized to `file:///C:/path/to/file` form.
- **Multi-value**: Decoded as lists; first value is preferred for display, all preserved in `raw`.

---

## 3. Runtime Plane Contract (Beefweb)

Helix observes the live state via the Beefweb Remote Control REST API.

- **Endpoint**: `http://localhost:8880/api/player`
- **Identity Key**: `%path%` (canonical foobar path).
- **Refresh Frequency**: Polled or on-demand. Not event-driven in Phase 1.
- **Graceful Degradation**: If Beefweb is unavailable, Helix assumes Foobar is closed and returns `playback_state: offline`.

---

## 4. Identity Resolution Contract

A track is considered **Resolved** only if its runtime path can be mapped to an entry in the Metadata Plane.

- **Primary Path**: Exact URI match.
- **Secondary Path**: Normalized Windows path match.
- **Tertiary Path**: Filename + context fuzzy match.
- **Identity Fusion**: Resolved tracks merge live runtime stats (position, volume) with canonical metadata (platform, composer).

---

## 5. Deployment Rules

1. **Independent Usability**: Foobar must be fully functional even if Helix is absent.
2. **Non-Destructive**: Helix never modifies `metadb.sqlite` or your media files in this phase.
3. **No Hidden State**: All Helix-Foobar integration state must be visible in the bridge diagnostics report.
