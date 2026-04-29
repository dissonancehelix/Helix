# Agent Router

## Read Order

1. `DISSONANCE.md` — portable operator profile, taste/cognition map, design grammar.
2. `README.md` — workspace constitution, root roles, source-of-truth hierarchy.
3. `AGENTS.md` — routing and implementation contract.
4. `core/map/README.md` — compressed machine-readable map contract.
5. `core/tools/TOOL_INDEX.yaml` — canonical tool registry.
6. Relevant named domain file and manifest:
   - `domains/<domain>/<DOMAIN>.md`
   - `domains/<domain>/manifest.yaml`
7. Relevant lab README when pressure tests or cross-domain theory are involved.

## Domain File Naming

Domain capsules use named domain files, not generic local README files.

```text
- `domains/self/SELF.md`
- `domains/music/MUSIC.md`
- `domains/games/GAMES.md`
- `domains/eft/EFT.md`
- `domains/trails/TRAILS.md`
- `domains/wiki/WIKI.md`
- `domains/software/SOFTWARE.md`
- `domains/language/LANGUAGE.md`
- `domains/attraction/ATTRACTION.md`
- `domains/food/FOOD.md`
- `domains/aesthetics/AESTHETICS.md`
- `domains/body_sensory/BODY_SENSORY.md`
- `domains/sports/SPORTS.md`
- `domains/worldview/WORLDVIEW.md`
```

Rules:

- Root `README.md` remains the workspace constitution.
- `core/map/README.md` and true lab/tool README files may remain conventional.
- Domain-local interpretive files must use the domain name: `<DOMAIN>.md`.
- Do not recreate domain-root README files; update `domains/<domain>/<DOMAIN>.md`
  when the folder's active navigation contract changes.
- When renaming, update active references across root docs, manifests, prompts,
  scripts, tool registries, markdown links, and tests.
- Historical references inside tracked change notes may remain if clearly
  marked historical.

Best compression:

> **Domain files should name the room, not just say “read me.”**

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

## Operating Contract

- The operator does not code. Build complete, runnable implementations.
- Structural precision over hedging.
- No stubs or placeholder logic when implementation is requested.
- No sycophancy; preserve the map, do not flatter it.
- If a task touches files, produce reviewable diffs and validation evidence.
- If a task is analysis-only, write reports; do not silently promote claims.

## Agent Rules

- Do not collapse observation, interpretation, and transformation.
- Read-only observation is valid progress.
- Consult `core/map/sources.yaml` before source-specific work.
- Reports are not canon.
- Domains elaborate; they do not redefine master patterns.
- Worldview owns politics, morals, institutional trust, other-mind/personality views, and religious/spiritual orientation; Theory owns consciousness hypotheses and falsifiers.
- Tools execute; they do not own truth.
- Engine enforces; it does not become a dumping ground.
- Raw evidence is not deleted.
- Contradictions become entries in `core/map/anomalies.yaml`.
- Examples are evidence doors. Do not flatten them into generic traits.
- False positives and negative controls are first-class evidence.
- Direct operator corrections outrank elegant inferred theory.
- Cross-domain claims must pass through reports before promotion.
- Keep sexual, food, body, social, and sensory evidence explicit enough to
  remain predictive; do not sand it into polite mush.

## Two Compression Modes

Before transforming files, classify the task as curatorial compression or
investigative compression.

- **Curatorial compression** repairs toward a known or strongly implied target
  shape. It removes noise, preserves source lineage, aligns with standards, and
  makes the object more itself.
- **Investigative compression** narrows a question by killing false positives,
  clarifying contrast classes, and making the real uncertainty harder to fake.

Subtractive consolidation rule:

- preserve load-bearing signal,
- merge useful content into the active source of truth,
- delete stale husks when the operator's stated or inferred goal is cleanup,
- do not preserve archive/sediment by default,
- do not create archive folders unless explicitly requested.

Direct operator corrections outrank generic software-conservation instincts.

## GPT Export Analysis Rules

When analyzing a ChatGPT export:

- Treat the export as evidence, not canon.
- Do not rewrite `DISSONANCE.md` directly.
- Sort evidence into the smallest owning domain.
- Use the named domain files as active local context:
  `domains/<domain>/<DOMAIN>.md`.
- Extract corrections, false positives, negative controls, artifact history,
  best compressions, domain assignment, response-debt/social-friction evidence,
  direct attachment anchors, and local-to-global promotion candidates.
- Preserve short exact user phrasing when it is a strong correction, boundary,
  or compression.
- Do not include long raw conversation dumps in reports.
- Put review artifacts under `domains/<domain>/reports/`,
  `domains/<domain>/data/`, `domains/<domain>/model/`, and
  `labs/domain_synthesis/reports/` as appropriate.
- Any proposed change to `DISSONANCE.md` must be listed in a synthesis report,
  not applied automatically.

## Session Harvest Rules

When a live AI session contains high-value evidence, create a harvest report
instead of relying on memory or chat-scroll archaeology.

Harvest-worthy material includes:

- direct operator corrections,
- short exact phrases that define a boundary,
- agent mistakes and how they were corrected,
- best compression lines,
- domain-specific findings,
- false positives / negative controls,
- artifact ledgers,
- candidate global patterns,
- theory lineage.

Rules:

- Treat harvests as evidence, not canon.
- Separate what the operator said from what the agent inferred.
- Do not modify `DISSONANCE.md` directly from a harvest.
- Do not update unrelated domains just because a session felt important.
- Use the smallest owning domain.
- Preserve exact phrasing when it is a correction or compression.
- Keep sensitive domains explicit enough to remain predictive.
- Put session harvest outputs under:
  `archive/analyses/claude_sessions/`, `archive/analyses/gpt_export/`, or
  `labs/domain_synthesis/reports/`.

Best compression:

> **Harvest the session’s evidence structure, not its narrative.**

## Lineage Pass Rules

A lineage pass updates all and only the strands that a session actually touched.

Allowed:

- updating affected domain files,
- syncing root README / AGENTS when operating rules changed,
- creating synthesis reports,
- adding local claim cards,
- adding anomalies or negative controls.

Forbidden:

- forced updates to every domain,
- promoting theory directly into canon,
- smoothing evidence into generic traits,
- turning one beautiful pattern into proof of everything.

Best compression:

> **No strand left standing does not mean no boundary left standing.**



## Tool Rule

Before creating a script, read `core/tools/TOOL_INDEX.yaml`.

If a canonical pipeline exists, use it or extend it. New scripts are allowed only when:

- no existing pipeline owns the task,
- the new script is added to `core/tools/TOOL_INDEX.yaml`,
- inputs/outputs and safety mode are documented,
- generated output lands under the owning domain capsule or cross-domain lab,
  not beside the script.

## Forbidden

- Two active root ontology files. `DISSONANCE.md` is the only portable profile canon.
- Generic root `docs/`, `data/`, `model/`, `system/`, `reports/`, or `outputs/`.
- Treating reports as source of truth.
- Mapping a domain before building its operational model.
- Flattening taste into generic personality traits.
- Hiding agency. Complexity may be hidden; agency must remain inspectable.
- Recreating domain-root README files after the domain-file rename.
- Promoting GPT-export findings directly into canon without review.
