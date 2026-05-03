# Helix Governance

## Authority Hierarchy

1. `DISSONANCE.md` — portable operator/person-pattern authority.
2. `README.md` — workspace constitution and source-of-truth hierarchy.
3. `AGENTS.md` — agent routing and operating contract.
4. `core/map/` — machine-readable companion map and anomaly/source registry.
5. Domain files and manifests — smallest owning domain authority.
6. Lab specs/reports — pressure-test and review artifacts, not canon by default.
7. Runtime/tool contracts — execution details, not truth ownership.

## Validation Rules

### Promotion Gate

A claim, invariant, or domain update should not be promoted unless it survives the relevant pressure checks:

1. **Source fit** — the update belongs in the smallest owning file.
2. **Evidence lineage** — the claim can be traced to direct correction, dataset, report, or source file.
3. **False-positive pressure** — cheap substitutes and lookalikes have been named.
4. **Domain fit** — the domain file agrees or has been patched.
5. **Validation status** — runnable artifacts/tests declare pass/fail/unknown.
6. **Reviewability** — changed files, diffs, or summaries are inspectable.

### Root Structure Enforcement

Only allowed root files and directories should exist. Root docs define the workspace; domain chambers hold local interpretation.

### Lab Boundary

Lab outputs do not automatically become canon. Reports may recommend promotion, demotion, or follow-up tests.

### Tool Boundary

Tools execute workflows and produce artifacts. They do not own truth. If a tool output conflicts with a source document, create an anomaly or patch the owning source after review.

## Anti-Drift Rules

Architectural drift occurs when:

- system structure changes without documentation updates,
- concepts are renamed or merged implicitly,
- domain boundaries are violated,
- stale command/runtime language survives after the workflow changed,
- reports are treated as canon without promotion,
- or tools silently define truth by side effect.

All drift should be corrected in the smallest owning file.
