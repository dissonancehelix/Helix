# Helix Architecture Refactor Plan

## Constitutional Migration: 6-Layer → 8-Layer

The 8-layer epistemic hierarchy enforces clearer separation between the sacred kernel,
structural vocabulary, governance, execution engines, labs, applications, atlas, and artifacts.

### Layer Assignments

| Layer | Path | Role |
|-------|------|------|
| 0 | 00_kernel/ | Sacred Python primitives — immutable |
| 1 | 01_basis/ | Structural vocabulary — enums, schemas |
| 2 | 02_governance/ | Validation, ring checks, promotion gates |
| 3 | 03_engines/ | Execution runtime, atlas, orchestration |
| 4 | 04_labs/ | Probes, invariants, experiments, corpus |
| 5 | 05_applications/ | Deployed tools (eft, rrs) |
| 6 | 06_atlas/ | Generated invariant confidence entries |
| 7 | 07_artifacts/ | Immutable probe run outputs |

### Ring Rules

- 04_labs and below must not import from 00_kernel or 02_governance directly
- All writes must flow to 07_artifacts/ or 06_atlas/ only
- Probes execute inside sandbox subprocess (no direct engine import)
