# Helix Engine Documentation Specification

**Status:** current docs/contract summary after the domain-refactor pass  
**Scope:** `core/engine/internal/docs/` architecture language, not runtime code cleanup  
**Authority:** `README.md`, `AGENTS.md`, `DISSONANCE.md`, domain manifests, and validation contracts  
**Not role:** obsolete command-language specification, domain capsule, personal profile, or proof file

Helix is no longer documented as a formal command-language-first system. The current architecture is a repo/workspace contract: root docs define authority, domains decompress local meaning, labs run pressure tests, tools execute bounded workflows, and reports remain review artifacts until promoted.

Best compression:

> **Core enforces; domains explain; labs pressure-test; tools execute; reports wait for promotion.**

---

## 1. Current System Shape

Current high-level flow:

```text
operator intent / agent task
→ read order and source-of-truth check
→ smallest owning domain or lab
→ direct tool/script/agent workflow
→ artifact or report
→ validation / review
→ optional promotion into owning docs or maps
```

This replaces the older command-language framing. The system should not require a formal command DSL to describe intent, route execution, or validate documentation.

---

## 2. Authority Stack

1. `DISSONANCE.md` — portable person-pattern and cognitive/taste map.
2. `README.md` — workspace constitution and root layout.
3. `AGENTS.md` — agent router, read order, and operating contract.
4. `core/map/` — machine-readable companion map, links, sources, anomalies, and examples.
5. `domains/<domain>/<DOMAIN>.md` — domain-local interpretation.
6. `domains/<domain>/manifest.yaml` — domain runtime/status metadata.
7. `labs/` — pressure tests, falsification, and theory reports.
8. `core/engine/contract/validation/` — validation contracts and checks.
9. `core/tools/` and `domains/<domain>/tools/` — executable utilities.

When sources conflict, update the smallest owning source or record an anomaly. Do not silently reconcile contradictory docs.

---

## 3. Core Responsibilities

`core/engine/` owns shared enforcement machinery:

- schema contracts,
- validation checks,
- structure checks,
- artifact gates,
- shared compiler/persistence utilities,
- runtime support code,
- and documentation contracts for those systems.

It does **not** own the meaning of every domain. Domain meaning belongs in named domain files and manifests.

---

## 4. Domain Responsibilities

Domains are first-class chambers when local evidence would otherwise flatten the main map.

Each active domain should provide:

```text
domains/<domain>/<DOMAIN>.md
domains/<domain>/manifest.yaml
optional model/
optional data/
optional tools/
optional reports/
```

Rules:

- Domain files name the room directly.
- Domain-local interpretive docs should not be recreated as generic root READMEs.
- Domains elaborate global patterns; they do not redefine the root constitution.
- Reports inside domains are review artifacts until promoted.

---

## 5. Lab Responsibilities

`labs/` contains cross-domain pressure tests and theory experiments.

Lab docs may keep conventional `README.md` and `SPEC.md` names because they describe experiment containers, not domain capsules.

Labs should:

- define the target question,
- split layers,
- list false proxies,
- run pressure reports,
- recommend claim status,
- avoid direct canon promotion unless explicitly requested.

---

## 6. Execution Entry Points

Current documentation should describe execution through direct tools, scripts, tests, or agent workflows.

Valid entry-point language:

```text
direct Python script
CLI tool
validation check
agent-mediated repo task
domain tool runner
manual dataset/report pass
```

Invalid current-doc language:

```text
formal command-language route
missing command-language entry point as a blocker
command DSL as primary authority
```

A missing formal command layer should not be listed as a gap. A missing runnable script, missing validation harness, missing artifact path, missing test, or missing source-of-truth link **is** a real gap.

---

## 7. Artifact and Report Rules

Artifacts and reports must remain inspectable:

- write outputs to explicit paths,
- preserve source lineage,
- include validation status when relevant,
- avoid hidden writes,
- avoid automatic promotion,
- include enough context for re-entry.

Reports are epistemic airlocks. They can recommend; they do not become truth until reviewed and promoted.

---

## 8. Cleanup Rule

Obsolete command-language documents, draft interface-language specs, and command-template files should be deleted rather than archived when they no longer match current Helix.

Best compression:

> **Delete dead command layers; preserve only the active contracts that still constrain work.**
