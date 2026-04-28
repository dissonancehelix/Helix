# Domain: Software

<!-- to be authored — Phase 1 scaffold; operator fills in content in a later pass -->

## Domain Role


## External / Operational Model


## Dissonance Mapping


## Evidence Anchors


## Dataset Notes


## False Positives


## Anomalies / Open Questions


## Upward Links


## Downward Links


---

## Workstation / Helix Runtime Surface

This domain is not yet authored. As a forward pointer:

- [system/tools/workstation_bridge/](../../system/tools/workstation_bridge/) is the **read-only observability foundation** — it inventories the repo and registered sources without modifying anything.
- [system/tools/music_bridge/](../../system/tools/music_bridge/) is the **first deep interactive-source candidate** (foobar2000), still read-only in Phase 3.
- [model/map/sources.yaml](../../model/map/sources.yaml) is the **source registry** naming every evidence stream and the mode it is permitted under.
- `reports/analyses/workstation/` is the **generated evidence stream** for snapshots.
- **No writeback** — neither metadata nor file moves nor configuration changes — until trust infrastructure (target identity, diff, backup, rollback, approval) exists. Phase 3 does not provide that infrastructure.

### Foundation note (Phase 3)

Workstation observability is the foundation for software-domain understanding. The Phase 3 [workstation snapshot reports](../../reports/analyses/workstation/) are **evidence**, not canon. Future authoring of this domain should *decompress from stable reports and source-registry entries*, not narrate from memory.

