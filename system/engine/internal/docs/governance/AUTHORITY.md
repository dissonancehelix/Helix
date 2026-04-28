# MANIFEST AUTHORITY RULES

**Version:** 1.0
**Location:** `docs/governance/AUTHORITY.md`
**Applies to:** All manifests under `MANIFEST.yaml` and `model/domains/*/manifest.yaml`

---

## Three-Layer Doc System

Helix uses three complementary documentation types. They are not interchangeable.

| Type | File | Authoritative For | Format |
|------|------|-------------------|--------|
| **README** | `*/README.md` | Human-readable operational description, design intent, narrative explanation | Markdown prose |
| **SPEC** | `*/SPEC.md` | Formal domain definitions, metric formulas, artifact schemas, pipeline stage contracts | Structured markdown + math |
| **Manifest** | `*/manifest.yaml` | Machine-readable structural index: what exists, where, in what state | YAML |

---

## What Each Is Authoritative For

### README is authoritative for:
- Why a domain/application exists
- How it fits into the Helix architecture
- What it is and is not
- Canonical examples and fixtures (narrative form)
- Known gaps in plain language

### SPEC is authoritative for:
- Formal metric definitions (formulas, units, normalization)
- Artifact schema shapes
- Pipeline stage contracts (input/output types)
- Calibration procedures and threshold derivation
- Promotion conditions

### Manifest is authoritative for:
- Whether a path exists right now
- What the runtime status of a component actually is (`implemented` / `partial` / `stub` / `not_started`)
- Which docs a component references
- Structural dependencies between components
- Known gaps as a structured list (not prose)

---

## When They Disagree

If a manifest says `pipeline_status: stub` but a README says the domain is running, the **manifest is correct for runtime state**. The README should be updated.

If a SPEC defines a formal metric but the manifest does not list it, the **SPEC is correct for formal definitions**. The manifest carries operational facts, not design intent.

If a README describes a design intent that no manifest or SPEC yet covers, the **README is correct for intent**. A manifest or SPEC entry should be added when implementation begins.

**Priority order for dispute resolution:**
```
runtime truth   → manifest wins
formal contract → SPEC wins
design intent   → README wins
```

---

## What Manifests Must NOT Do

- Restate full metric formulas (those belong in SPEC)
- Repeat prose descriptions (those belong in README)
- Claim unimplemented components are implemented
- Become a primary documentation source for human readers
- Drift silently from actual repo structure

---

## Structural Rules

- Every domain in `model/domains/` must have a `manifest.yaml`
- The root `MANIFEST.yaml` must list all canonical domains
- All manifests must carry `manifest_schema: manifest_schema_v1`
- Validator: `system/engine/contract/validation/manifest_validator.py`
- Health check: `system/engine/contract/validation/manifest_health.py`

---

## Adding a New Domain

1. Create the directory under `model/domains/`
2. Write `README.md` and `SPEC.md`
3. Create `manifest.yaml` using `manifest_schema_v1`
4. Register it in `MANIFEST.yaml` under `domains:`
5. Run `python -m core.governance.validation.manifest_validator` — must pass
6. Run `python -m core.governance.validation.manifest_health` — must pass

---

## Manifest Status Vocabulary

| Value | Meaning |
|-------|---------|
| `implemented` | Code path exists and is functional |
| `partial` | Code path exists; some stages functional, others not |
| `stub` | File exists; raises NotImplementedError or equivalent |
| `not_started` | Not yet begun |
| `not_implemented` | Explicitly absent; no code exists |
| `unknown` | Directory or code exists but has not been audited |
| `active` | Application is in active use |
| `deprecated` | No longer maintained |
| `experimental` | Exists but not canonical |

Use `unknown` honestly when a directory exists but its contents have not been read and verified.


