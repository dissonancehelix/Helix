# Helix Workspace

**Repository:** https://github.com/dissonancehelix/Helix/

Helix is the whole workspace: the closed working box where the operator and LLM share models, evidence, tools, reports, labs, and trust gates.

`DISSONANCE.md` is the portable person-pattern: cognition, taste, attraction, sensory profile, design preferences, and pattern semantics.

This `README.md` is the workspace constitution: folder roles, trust boundaries, source-of-truth hierarchy, and agent expectations.

Best compression:

> **DISSONANCE.md is the operator map. Helix is the shared working body.**

---

## Root Layout

```text
/
├── README.md          # workspace constitution
├── DISSONANCE.md      # portable profile and design philosophy
├── AGENTS.md          # single agent router
├── model/             # modeled understanding
│   ├── map/           # machine-readable pattern graph
│   └── domains/       # decompressed domain chambers
├── data/              # raw, normalized, and derived evidence/artifacts
├── system/            # machinery
│   ├── engine/        # checks, schemas, contracts, compiler/enforcement
│   ├── tools/         # runnable tools, bridges, pipelines, CLIs
│   └── vendor/        # third-party SDKs, toolkits, source mirrors
├── labs/              # pressure tests and falsification surfaces
├── reports/           # generated review artifacts
└── quarantine/        # staged removals and uncertain moves
```

Loose root files are **unsorted**. They must be moved, adopted, or deleted; they are not a permanent intake system.

---

## Source Of Truth

1. **`DISSONANCE.md`** — portable human-readable canon for operator cognition, taste, and pattern semantics.
2. **`model/map/`** — machine-readable canon for pattern IDs, gates, examples, probes, links, sources, and anomalies.
3. **`model/domains/<name>/README.md`** — domain-local operational interpretation. Domains elaborate; they do not redefine master patterns.
4. **`labs/`** — claim pressure, falsification, demotion evidence.
5. **`data/`** — evidence and artifacts. Raw data is authoritative for facts, not interpretation.
6. **`reports/`** — generated review artifacts. Never canon until reviewed and promoted.
7. **`system/tools/`** — runnable machinery. Tools execute workflows; they do not own truth.
8. **`system/engine/`** — enforcement machinery: schemas, checks, contracts, compiler/validation.

When sources disagree, create or update `model/map/anomalies.yaml`; do not silently reconcile.

---

## Folder Roles

- **`model/`** — Helix's modeled understanding. `map/` compresses; `domains/` decompress.
- **`data/`** — evidence lake and generated artifacts. Use `raw/`, `normalized/`, and `derived/` when possible.
- **`system/engine/`** — the hidden machinery that enforces boundaries and validates structure.
- **`system/tools/`** — executable tools. Before adding a script, read `system/tools/TOOL_INDEX.yaml`.
- **`system/vendor/`** — third-party code and SDKs. Vendor material is provenance, not design authority.
- **`labs/`** — pressure chambers. A lab must be able to weaken a claim.
- **`reports/`** — epistemic airlocks. Generated meaning waits here before promotion.
- **`quarantine/`** — staged removals, uncertain moves, and rollback manifests.

Local bridge paths such as `C:\Users\dissonance\Music`, foobar2000 profile paths,
WSL `/home/dissonance` paths, and legacy `Desktop/Helix` or `Desktop/Trails`
references are workstation-specific bridge targets. They are configurable/local
coordinates, not Helix ontology.

---

## Workstation Laws

1. **Observation before interpretation before transformation.**
2. **Trustworthy as sensor before trustworthy as actor.**
3. **Bridges preserve sovereignty.**
4. **Reports are epistemic airlocks.**
5. **`model/map/sources.yaml` is Helix's attention boundary.**
6. **Read-only is active perception.**
7. **Core compresses; domains decompress.**
8. **Workspace = cognitive body; system/engine = nervous machinery.**
9. **Workspace must obey the ontology it contains.**
10. **Claims earn height by surviving pressure.**

---

## Tool Rule

Existing pipelines should be reused before new scripts are created.

Agents must read:

1. `system/tools/README.md`
2. `system/tools/TOOL_INDEX.yaml`
3. the tool README or manifest for the specific domain

Each tool entry names its purpose, entrypoint, inputs, outputs, safety mode, and whether it is canonical, stage helper, legacy, or one-off archive.

---

## Change Protocol

For structural changes, record:

```text
Change:
Affected IDs:
Direction: upward | downward | lateral
Files touched:
Patterns strengthened:
Patterns weakened:
False positives updated:
Needs regeneration:
Rollback:
```

Structural moves require a migration manifest under `quarantine/` before the move.

---

## Agent Guidance

Agents must:

1. Read `README.md` first.
2. Read `DISSONANCE.md` when touching profile, taste, cognition, operator patterns, or design semantics.
3. Read `AGENTS.md` for routing and implementation contract.
4. Preserve the source-of-truth hierarchy.
5. Consult `model/map/sources.yaml` before source-specific work.
6. Use existing tools before inventing new scripts.
7. Do not promote reports to canon without review.
8. Preserve examples as evidence anchors.
9. Treat contradictions as anomalies.

Best compression:

> **Helix should make the operator and the LLM more powerful without making either babysit the structure.**
