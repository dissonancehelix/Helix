# Helix Workspace

**Repository:** https://github.com/dissonancehelix/Helix/

Helix is the shared working body for the operator and LLM: map, evidence,
tools, tests, reports, archives, domain rooms, and trust gates arranged by the
same grammar as `DISSONANCE.md`.

Helix began as drift prevention and mental-friction reduction, but its current role is broader: a cognitive workspace for research, pattern detection, domain testing, externalized memory, and human-LLM collaboration.

`DISSONANCE.md` is the portable person-pattern. This `README.md` is the
workspace constitution.

Best compression:

> **DISSONANCE.md is the operator map. Helix is the shared working body.**

Second compression:

> **Core compresses; domains decompress.**

Third compression:

> **The repo should be navigable by file exploration, not by psychic debugging.**

## Root Layout

```text
/
├── README.md          # workspace constitution
├── DISSONANCE.md      # portable profile and design grammar
├── AGENTS.md          # agent router and operating contract
├── core/              # compressed shared map, engine, tools, atlas
├── domains/           # active domain capsules
├── labs/              # cross-domain pressure tests and theory labs
├── archive/           # local-only substantial raw provenance by evidence type
└── inbox/             # local-only operator drop zone for unsorted evidence
```

Dotfiles such as `.gitignore` are root technical support, not ontology.
`archive/` and `inbox/` are local-only and ignored by Git; GitHub carries the
map, tools, compact extracted data, and reports, not the private source piles.

## Source Of Truth

1. **`DISSONANCE.md`** — portable human-readable canon for operator cognition,
   taste, design grammar, and pattern semantics.
2. **`core/map/`** — machine-readable companion map: patterns, gates, examples,
   probes, links, sources, and anomalies.
3. **`domains/<name>/<DOMAIN>.md`** — domain-local operational interpretation.
   Domains elaborate; they do not redefine master patterns.
4. **`labs/`** — cross-domain pressure, falsification, and demotion evidence.
5. **`domains/<name>/model/`** — durable domain interpretation, claim cards,
   local maps, and promoted local theory.
6. **`domains/<name>/data/`** — domain-owned cleaned records and compact
   generated products.
7. **`archive/`** — local-only substantial raw evidence and source dumps
   grouped by evidence type. Archive preserves heavy provenance; it is not
   active canon and is not published to GitHub.
8. **`domains/<name>/reports/` and `labs/reports/`** — generated review
   artifacts. Reports are never truth until reviewed and promoted.
9. **`core/tools/` and `domains/<name>/tools/`** — runnable machinery. Tools
   execute workflows; they do not own truth.
10. **`core/engine/`** — shared enforcement machinery: schemas, checks,
   contracts, compiler/validation.

When sources disagree, create or update `core/map/anomalies.yaml`; do not
silently reconcile. Contradictions are map updates waiting for a handler.

## Domain Capsules

Active domains are first-class because cognition has been externalized into
reusable systems, archives, tools, edits, databases, workflows, operational
models, or subjective-experience chambers.

```text
domains/<domain>/
├── <DOMAIN>.md
├── manifest.yaml
├── model/
├── data/
├── tools/
└── reports/
```

Operational domains use `tools/` only when they own runnable workflows.
Interpretive domains may omit `tools/` until a real workflow exists.
Domain-local `labs/` is optional and exists only for true local experiments.

Active capsules:

- `self/` — cognitive style, neurotype constraints, sensory/social gates,
  response debt, attention chambers, and operational terrain.
- `music/` — foobar, VGM, DSP, metadata, world-listening, bass/air/return.
- `games/` — field mechanics, authored worlds, roles, transition systems,
  curated residue, completion/playtime evidence.
- `eft/` — Extreme Football Throwdown as designed digital sport, transition-field,
  manifest-driven game design, mapmaking, player skill ecology, and continuous
  contest evidence.
- `trails/` — Trails/Kiseki continuity, database, wiki, atlas work,
  world-memory, source ingestion, spoiler discipline.
- `wiki/` — Wikipedia editing, article architecture, citations, templates,
  infoboxes, Commons/Wikidata, future-reader interface design.
- `software/` — Helix, schemas, inspectable agency, agent collaboration,
  workspace design, foobar/wiki tooling, executable personal ontology.
- `language/` — linguistics, English, Spanish, Japanese/source access,
  grammar as movement, phrase automation, public-language tools.
- `attraction/` — sexual / visual attraction, face-primary beauty gate,
  channel convergence, warm/dark palette, body-signal hierarchy.
- `food/` — plain/simple meals, bounded abundance, soft base / sharp event,
  autumn+football+favorite-food Thanksgiving anchor, cold/creamy comfort.
- `aesthetics/` — color, warmth, darkness, enclosure, texture, ruins,
  Mesoamerican/earthy motifs, inhabited environments.
- `body_sensory/` — DOMS, massage, stretch, localizable body maps,
  controlled intensity, signal ownership.
- `sports/` — Commanders fandom, Jayden Daniels, team continuity,
  future-state leverage, denial, emotional fandom plus public-knowledge
  maintenance.
- `worldview/` — politics, morals, institutions, religion/spirituality,
  metaphysical leaning, other-mind/personality views, open knowledge ethics,
  suffering, power, and shared standards.

## Domain Promotion Rule

A chamber becomes first-class when local evidence would otherwise flatten the
main map.

A domain must answer:

1. What this domain is to the operator.
2. What it is not.
3. Core reward mechanics.
4. Core rejection mechanics.
5. Evidence anchors.
6. False positives / negative controls.
7. Local anomalies.
8. How the domain feeds the global cognitive map.
9. Best compression.

Access layers are not automatically domains. Reddit, Twitter/X, YouTube,
bookmarks, Last.fm, ListenBrainz, Steam exports, screenshots, old web residue,
and raw archives usually feed domains; they do not become rooms unless they
develop a distinct operational interior.

Best compression:

> **The main map names the doors; domain files hold the rooms; raw data holds the basement.**

## Domain File Naming

Domain capsules use named domain files instead of generic local README files.

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

Root `README.md` remains the workspace constitution. Other infrastructure
README files may remain conventional when they describe a container, tool index,
lab, or technical subsystem. Domain chambers are different: their main file
should name the room directly.

Rules:

- Domain files live at `domains/<domain>/<DOMAIN>.md`.
- New first-class domains must be added to the active capsule list, domain-file naming list, `AGENTS.md`, and `DISSONANCE.md`.
- Update all active references after the rename.
- Keep root `README.md` as-is.
- Do not rename `AGENTS.md`, `DISSONANCE.md`, root `README.md`, or core/lab
  technical README files unless there is a separate explicit migration.
- Historical references inside tracked change notes may remain if they are
  clearly historical.
- New domain work must target the named domain file, not a regenerated local
  README.

Best compression:

> **Generic README works at the root; domain chambers deserve named doors.**


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
- Domain roots normally contain only `<DOMAIN>.md`, `manifest.yaml`, `model/`,
  `data/`, `tools/`, and `reports/`.
- Domain-local `labs/` is optional and only allowed for true local experiments.
- `data/` contains cleaned domain records and compact generated products
  directly, grouped by meaningful local role rather than lifecycle buckets.
- `model/` contains durable interpretation.
- `tools/` contains runnable workflows and tool-support material.
- `reports/` contains review artifacts only.
- `archive/` preserves local-only substantial raw provenance and source dumps
  grouped by evidence type.
- `inbox/` receives local-only unsorted operator drops. Agents sort from it into domain
  data, domain models, labs, or the matching archive evidence-type folder, then
  leave the raw drop ignored only when it is substantial. Tiny source slips
  should be deleted after extraction. Reports are optional review artifacts,
  not required inbox output.
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

## Profile-Aligned Design Laws

These laws encode the settled cross-domain patterns from the current
chambered-domain pass.

1. **Signal integrity beats category.** The label is never the payload; the
   surviving signal is.
2. **Stable base + controlled event.** Comfort needs a floor; pleasure comes
   from controlled events on top.
3. **Currentness pressure belongs to live state objects.** When an object
   carries live state, stale structure feels wrong.
4. **Public artifacts need clean entry; private worlds need durable re-entry.**
   A lead is only good if the body can still reopen it.
5. **Field tuning beats blank generation.** The operator tunes reachable fields
   more naturally than creating from nothing.
6. **Intensity is fine when the threshold is owned.** Chosen intensity
   regulates; unchosen impact violates.
7. **External cognition is active infrastructure.** Archives, schemas, maps,
   edits, and tools are part of the working cognitive surface, not just storage.
8. **Direct attachment must stay protected.** Structure explains the shape of
   attachment; it does not replace attachment.
9. **Negative controls are science, not pessimism.** A false positive shows
   where the real boundary lives.
10. **Domains chamber detail; core preserves the global spine.** Cross-pollinate
    through gates, not leaks.
11. **Lineage matters when it remains operational.** Source history, migration
    history, etymology, arc memory, and evidence chains should stay reopenable
    when they change interpretation.
12. **Compression has two modes.** Curatorial compression repairs toward a known
    form; investigative compression narrows unknowns by eliminating false
    substitutes.

Curatorial compression applies to repo structure, Wikipedia/public objects,
source cleanup, folder consolidation, templates, manifests, and other cases
where the target grammar is already known or strongly implied.

Investigative compression applies to labs, reports, theory pressure, taste
mapping, dataset triage, and other cases where the target is hidden by weak
explanations or false positives.

Root grammar:

```text
core compresses
domains decompress
labs pressure-test
research applies external pressure
```

Best compression:

> **Dissonance turns valued fields into maintained interiors.**

Second compression:

> **I care by making the field returnable.**

## Direct Session Patches And Lineage Passes

Some high-value AI sessions become evidence sources in their own right. They do not require a mandatory intermediate report before the map can be updated.

Claude Desktop, Claude Code, ChatGPT, Codex, and other agent sessions may directly patch touched files when they contain:

- direct operator corrections,
- strong compression lines,
- domain-local evidence,
- agent mistakes or drift,
- generated artifacts,
- theory-lineage transitions,
- examples that would otherwise be lost,
- candidate global patterns.

Direct patch flow:

```text
live session
→ identify touched domains
→ update only touched files
→ sync README/AGENTS if operating rules changed
→ avoid forced updates to unrelated rooms
```

Reports remain useful when uncertainty, evidence sorting, cross-domain promotion, or review risk needs a separate room. They are optional review artifacts, not required ceremony.

A no-strand-left-standing pass is allowed after a strong lineage session, but it must remain gated: no relevant strand should be left unexamined, and no unrelated strand should be updated just because the session felt important.

Best compression:

> **Patch the clear correction; report only when uncertainty needs its own room.**

Second compression:

> **No strand left standing means no relevant strand, not every strand in the building.**


## Labs And Archive

`labs/` is for pressure tests that cross domains or test master claims. A lab
must be able to weaken a claim.

`labs/appearance_ownership_continuity/` is the special cross-domain lab for
the Appearance–Ownership–Continuity Framework (AOC), Owned Continuity Hypothesis
(OCH), DCP, LIP, EIP, consciousness, and owned-continuity work.

`archive/` preserves local-only substantial raw provenance grouped by evidence
type. Heavy datasets, images, hard-to-reproduce exports, and not-yet-ingested
evidence can stay there. Small source slips should disappear after extraction.
Generated material does not become canon by being archived. The archive is
restore-only memory, not an active workspace, and it is ignored by Git.

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
schemas, source code, compact model files, small curated artifacts, and tracked
change notes.

Helix should not publish gigabytes of local evidence: raw archives, media,
databases, caches, generated bulk outputs, build products, nested `.git`
folders, and vendor mirrors stay ignored unless explicitly curated.

`archive/` and `inbox/` are always local-only. Extracted, compact, reviewed
records can move into domain `data/`, domain `model/`, or `labs/`; the raw
drop stays off GitHub.

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

Structural moves should leave the workspace more browsable than they found it
and update the owning README when a rule changes. Unsorted evidence drops begin
in `inbox/`, then get sorted into the smallest owning context. The inbox is a
temporary tray, not a permanent room.

Best final compression:

> **Helix should make the operator and the LLM more powerful without making either babysit the structure.**
