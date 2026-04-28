# Helix Workspace

**Repository:** https://github.com/dissonancehelix/Helix/

Helix is the shared working body for the operator and LLM: map, evidence,
tools, tests, reports, archives, and trust gates arranged by the same grammar
as `DISSONANCE.md`.

`DISSONANCE.md` is the portable person-pattern. This `README.md` is the
workspace constitution.

Best compression:

> **DISSONANCE.md is the operator map. Helix is the shared working body.**

Second compression:

> **Core compresses; domains decompress.**

## Root Layout

```text
/
├── README.md          # workspace constitution
├── DISSONANCE.md      # portable profile and design grammar
├── AGENTS.md          # agent router and operating contract
├── core/              # compressed shared map, engine, tools, atlas
├── domains/           # active domain capsules
├── labs/              # cross-domain pressure tests and theory labs
├── archive/           # raw provenance, imports, analyses, migration history
└── quarantine/        # staged removals and uncertain moves
```

Dotfiles such as `.gitignore` are root technical support, not ontology.

## Source Of Truth

1. **`DISSONANCE.md`** — portable human-readable canon for operator cognition,
   taste, design grammar, and pattern semantics.
2. **`core/map/`** — machine-readable companion map: patterns, gates, examples,
   probes, links, sources, and anomalies.
3. **`domains/<name>/README.md`** — domain-local operational interpretation.
   Domains elaborate; they do not redefine master patterns.
4. **`labs/`** — cross-domain pressure, falsification, and demotion evidence.
5. **`domains/<name>/data/`** — domain-owned cleaned records and generated
   outputs.
6. **`archive/`** — raw evidence, local source dumps, analyses, and migration
   history. Archive preserves provenance; it is not active canon.
7. **`domains/<name>/reports/` and `labs/reports/`** — generated review
   artifacts. Reports are never truth until reviewed and promoted.
8. **`core/tools/` and `domains/<name>/tools/`** — runnable machinery. Tools
   execute workflows; they do not own truth.
9. **`core/engine/`** — shared enforcement machinery: schemas, checks,
   contracts, compiler/validation.

When sources disagree, create or update `core/map/anomalies.yaml`; do not
silently reconcile.

## Domain Capsules

Active domains are first-class because cognition has been externalized into
reusable systems, archives, tools, edits, databases, workflows, or operational
models.

```text
domains/<domain>/
├── README.md
├── manifest.yaml
├── model/
├── data/
│   └── output/
├── tools/
└── reports/
```

Domain-local `labs/` is optional and exists only for true local experiments.

Active capsules:

- `self/` — cognitive style, neurotype constraints, sensory/social gates.
- `music/` — foobar, VGM, DSP, metadata, world-listening.
- `games/` — field mechanics, EFT/GMod, roles, transition systems.
- `trails/` — Trails/Kiseki continuity, database, wiki, atlas work.
- `wiki/` — Wikipedia editing, article architecture, citations, templates.
- `software/` — Helix, schemas, inspectable agency, workspace design.
- `language/` — linguistics, English, Spanish, grammar, public-language tools.

## Core

`core/` contains shared infrastructure only:

- `core/map/` — compressed map canon.
- `core/engine/` — validation, schemas, contracts, compiler/enforcement.
- `core/tools/` — cross-domain tools and tool registry.
- `core/atlas/` — shared compiled atlas artifacts.
- `core/reports/` — reports produced by core workspace sensors.

Shared infrastructure stays global. Domain-owned work nests under the domain.

## Workspace Design Rules

Helix must be navigable by human file exploration, not only by LLM memory,
manifests, or tool registries. The path should explain the thing before a
README has to defend it.

Best rule:

> **Fewer folders, better rooms.**

Second rule:

> **Depth must reveal behavior. If depth only repeats names, compress it.**

Rules:

- Folders should group by role/category, not repeat identity.
- Nesting must increase orientation, not express uncertainty.
- Depth must reveal behavior. If depth only repeats names, compress it.
- No folder may repeat an ancestor name.
- No domain-root `vendor/`.
- No `core/` inside a domain.
- No `labs/labs` or `reports/reports`.
- Domain roots normally contain only `README.md`, `manifest.yaml`, `model/`,
  `data/`, `tools/`, and `reports/`.
- Domain-local `labs/` is optional and only allowed for true local
  experiments.
- `data/` contains cleaned domain records directly; generated products belong
  under `data/output/`.
- `model/` contains durable interpretation.
- `tools/` contains runnable workflows and tool-support material.
- `reports/` contains review artifacts only.
- `archive/` preserves raw provenance, imports, analyses, and migration history.
- `quarantine/` stages uncertain moves/removals.
- SDKs, toolkits, cloned helper libraries, and source mirrors belong under
  `tools/toolkits/` or `tools/<tool_name>/toolkits/`, not `vendor/`.

A folder may exist only if it can answer:

1. What is this?
2. What belongs here?
3. What does not belong here?
4. What reads it?
5. What writes it?
6. What promotes it?
7. What would break if this folder disappeared?

## Labs And Archive

`labs/` is for pressure tests that cross domains or test master claims. A lab
must be able to weaken a claim.

`labs/inhabited_interiority/` is the special future/cross-domain lab for
consciousness and inhabited-interiority work.

`archive/` preserves raw provenance, migration notes, imports, and review
history. Raw evidence is not deleted. Generated material does not become canon
by being archived. Retired structures are recorded in migration manifests
instead of kept as parallel folder trees.

## Workstation Laws

1. Observation before interpretation before transformation.
2. Trustworthy as sensor before trustworthy as actor.
3. Bridges preserve sovereignty.
4. Reports are epistemic airlocks.
5. `core/map/sources.yaml` is Helix's attention boundary.
6. Read-only is active perception.
7. Core compresses; domains decompress.
8. Workspace = cognitive body; `core/engine` = nervous machinery.
9. Workspace must obey the ontology it contains.
10. Claims earn height by surviving pressure.

## Tool Rule

Before creating a script, read `core/tools/TOOL_INDEX.yaml`.

If a canonical pipeline exists, use it or extend it. New scripts are allowed
only when:

- no existing pipeline owns the task,
- the new script is added to `core/tools/TOOL_INDEX.yaml`,
- inputs/outputs and safety mode are documented,
- generated output lands in the owning domain capsule or a cross-domain lab,
  not beside the script.

## Git And Size Policy

Helix should keep as much structure on GitHub as possible: READMEs, manifests,
schemas, source code, compact model files, small curated artifacts, and
migration notes.

Helix should not publish gigabytes of local evidence: raw archives, media,
databases, caches, generated bulk outputs, build products, nested `.git`
folders, and vendor mirrors stay ignored unless explicitly curated.

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

Structural moves require a migration manifest under `archive/migrations/` or
`quarantine/` before the move.

Best final compression:

> **Helix should make the operator and the LLM more powerful without making either babysit the structure.**
