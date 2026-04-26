# Helix Governance

## Authority Hierarchy

1. HSL (Helix Structural Language) — primary authority
2. SPEC (machine-enforceable architecture) — secondary
3. Domain specifications — tertiary
4. Repository structure — quaternary

## Validation Rules

### Atlas Promotion Gate (6 Criteria)
An invariant must pass all 6 criteria to be promoted to PROMOTED status:

1. **Reproducibility**: At least 2 independent runs with matching results
2. **Multi-domain observation**: Detected in ≥ 2 distinct domains
3. **Minimum confidence**: Confidence score ≥ threshold
4. **Pass rate**: ≥ 80% pass rate across all runs
5. **Signal strength**: Mean signal above minimum threshold
6. **Probe version**: Latest probe version must have been used

### Root Structure Enforcement (`core/integrity/root_structure.py`)
Only allowed directories and files may exist at repository root.

### Substrate Guard (`core/kernel/substrate_guard.py`)
`applications/labs/` cannot write to immutable core directories.

### Ring Import Validation (`core/kernel/validate_rings.py`)
Lab code cannot import from `core.kernel` or `core.governance` directly.

### Architecture Watchdog (`core/kernel/substrate/architecture_watchdog.py`)
Periodic polling ensures required layers exist and no unauthorized root items appear.

## Anti-Drift Rules

Architectural drift occurs when:
- System structure changes without specification updates
- Concepts are renamed or merged implicitly
- Data and structure boundaries are violated
- New abstractions appear without formal definition

All drift must be corrected immediately.
