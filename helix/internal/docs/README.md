# docs/

This directory is the canonical documentation tree for Helix.

**Machine-readable manifest:** [`manifest.yaml`](manifest.yaml)
**Authority rules:** [`governance/AUTHORITY.md`](governance/AUTHORITY.md)

---

## Structure

```
docs/
  README.md                 ← this file (index/map)
  manifest.yaml             ← machine-readable docs tree definition
  architecture/             ← system architecture, pipeline, schemas
  governance/               ← authority rules, validation, manifest rules
  invariants/               ← invariant index and invariant family docs
  research/                 ← working notes, open questions, exploratory docs
  profiles/                 ← operator/user cognitive profiles
```

**Rule:** No loose markdown files belong in `docs/` root other than `README.md` and `manifest.yaml`.

---

## Subtrees

### `architecture/`
System-wide architectural documentation. These are stable reference docs.

| File | Contents |
|------|----------|
| `ARCHITECTURE.md` | Layer model, pipeline diagram |
| `PIPELINE.md` | End-to-end pipeline description |
| `SPEC.md` | Full system specification |
| `ENTITY_SCHEMA.md` | Atlas entity schema definitions |
| `OPERATOR_SPEC.md` | Operator interface specification |
| `HSL.md` | Helix Structural Language reference |

### `governance/`
Authority, validation, and schema governance docs.

| File | Contents |
|------|----------|
| `GOVERNANCE.md` | Authority hierarchy, promotion gate, anti-drift rules |
| `AUTHORITY.md` | What README / SPEC / manifest are each authoritative for |

### `invariants/`
Invariant family documentation. Named invariants get their own doc here.

| File | Contents |
|------|----------|
| `INVARIANTS.md` | Index of all named invariants with status and references |
| `decision_compression_principle.md` | Authoritative DCP doc |

### `research/`
Working notes and open questions. These are **not** specifications.
They are research handles — explicitly provisional.

| File | Contents |
|------|----------|
| `dcp_trajectory_open_questions.md` | DCP / trajectory open questions, next tests, falsification |
| `cross_domain_formalism.md` | Shared k_eff equation across language and Kuramoto — what would make it a real discovery |
| `gwt_consciousness_probe_findings.md` | GWT / IIT probe results: Paths A–B complete, real-domain chess/LLM/Wikipedia probes, 5 open paths |
| `analysis_phases.md` | Music library phased rollout plan (Phases 0–5) — status and scripts reference |
| `ud_preregistration.md` | UD treebank calibration preregistration for language domain k_eff ordering |
| `composer_attribution_spec.md` | S3K composer attribution specification |
| `s3k.md` | S3K full analysis document |
| `genesis_vgm_remaster_spatial_engine_project_doc.md` | Genesis VGM remaster / spatial engine project doc |

### `profiles/`
Operator and user cognitive profiles used as research substrate by Helix.

| File | Contents |
|------|----------|
| `DISSONANCE.md` | Cognitive profile — analyzed as DCP / trajectory model substrate |

---

## What Does NOT Live Here

- **Domain docs** (`README.md`, `SPEC.md`, `manifest.yaml`) → stay with their domain under `domains/<domain>/`
- **Application docs** → stay with their application under `applications/<app>/`
- **Core subsystem docs** (e.g. `core/enforcement/ENFORCEMENT.md`) → stay with their subsystem
- **Experiment artifacts** → `applications/labs/`
- **Library and atlas data** → `codex/`

