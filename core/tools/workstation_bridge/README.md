# Workstation Bridge

Read-only workstation/repo inventory and source snapshot tool.

## Role

This app is **Helix's read-only workstation sensor**, not a controller.

- Its outputs are **reports**, not canon.
- Deep scans are **opt-in** (`--deep`).
- It is the **plug-in foundation** future source bridges (foobar, Steam, Last.fm, Spotify, …) extend rather than reinventing.

A bridge earns sensor trust by producing clean snapshots before it earns actor trust. This bridge is the sensor stage.

## Purpose

Helix observes the workstation before it interprets it, and interprets it before it transforms anything. This bridge is the observation layer.

## Contract

- **This app observes the workstation/repo. It does not modify files.**
- It does not move data.
- It does not scan the whole `C:` drive.
- It only scans configured roots.
- Default mode scans the repo root shallowly and safely.
- `data/` is summarized shallowly by default because it is large.
- Deep scans require an explicit `--deep` flag.
- Outputs go to `core/reports/workstation/`.
- This is the **general foundation** that foobar and other source bridges plug into later.

## Usage

```bash
python core/tools/workstation_bridge/workstation_snapshot.py \
    --root . \
    --config core/tools/workstation_bridge/config.example.yaml \
    --out core/reports/workstation
```

Flags:

- `--root PATH` — repo root (default: `.`).
- `--config PATH` — config file (default: `core/tools/workstation_bridge/config.example.yaml`). YAML if PyYAML is installed; otherwise sensible built-in defaults.
- `--out PATH` — output directory (default: `core/reports/workstation`).
- `--deep` — recurse fully into roots flagged for shallow-only (e.g. `data/`). Off by default. Slow.

## Outputs

- `workstation_snapshot_<timestamp>.json` — machine-readable, validates against `core/engine/schemas/workstation_snapshot.schema.json`.
- `workstation_snapshot_<timestamp>.md` — human-readable summary.

## Inventory produced

- top-level folder presence
- README presence at root and per locked-root folder
- map YAML presence
- domain README coverage
- app README coverage
- lab README coverage
- report directory presence
- source registry presence (`core/map/sources.yaml`)
- approximate file counts and byte counts within safe scan limits

## Warnings emitted

- missing root README
- missing map YAML
- source path not found
- domain folder without README
- app folder without README
- lab folder without README
- scan skipped due to safety limits

## Safety rules

- Do not deeply scan `data/` without `--deep`.
- Do not scan ignored folders (`.git`, `.venv`, `node_modules`, `__pycache__`, `.pytest_cache`, …).
- Do not follow symlinks.
- Do not write outside `core/reports/workstation/`.
- Refuse to run if `--out` resolves outside the repo root.

## Plug-in model

Future source bridges (foobar, Steam, Last.fm, Spotify, …) register themselves in `core/map/sources.yaml`. This bridge inventories what is registered; specialized bridges produce deeper per-source snapshots into `archive/analyses/<source>/`.

## Phase 3 boundary

- Reads only.
- No diff, no backup, no rollback machinery yet — those are Phase 4+ requirements for any transformation.
- Foobar source is `status: planned, mode: read_only_pending`; this bridge does **not** invoke foobar.

