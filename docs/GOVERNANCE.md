# Governance

## Purpose

Governance enforces admissibility, validation, confidence scoring, and promotion.

## Canonical locations

- Runtime governance code: `core/governance/`
- Audit records: `governance/audit/`
- Templates: `governance/templates/`

## Rules

1. Atlas writes are compiler-gated.
2. Confidence scoring is centralized in `core/governance/confidence_scoring.py`.
3. Promotion writes back only to entries already compiled into `codex/atlas/invariants/`.
4. Integrity and reproducibility outputs belong in `execution/`, not in Atlas root directories.
