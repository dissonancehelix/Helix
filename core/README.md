# core/

Compressed shared infrastructure.

`core/` contains the map, engine, tool registry, shared atlas artifacts, and
core reports that are not owned by any one domain.

## Contents

- `map/` — machine-readable companion canon.
- `engine/` — validation, schemas, contracts, and enforcement.
- `tools/` — cross-domain tools and `TOOL_INDEX.yaml`.
- `atlas/` — shared compiled atlas artifacts.
- `reports/` — reports produced by core sensors.

Domain-owned work belongs in `domains/<domain>/`, not here.
