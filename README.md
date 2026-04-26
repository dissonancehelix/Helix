# Helix

Compact personal cognition, research, data, and tool-building workspace.
`DISSONANCE.md` is the operator profile. Everything else serves it.

## Read Order

1. **This file** — workspace structure, placement rules, agent rules.
2. **DISSONANCE.md** — when operator taste, design constraints, or profile alignment matter.

## Root Structure

```text
HELIX/
├── README.md           # workspace overview and operating rules
├── DISSONANCE.md       # operator profile / personal ontology
├── helix/              # constraint engine, research, memory
├── domains/            # modeled reality surfaces (Python package)
├── apps/               # practical tools (Python package)
└── data/               # raw and domain-keyed data
```

## Directory Contracts

### `helix/` — internal machinery

```text
helix/
├── engine/
│   ├── contract/   # schemas, validators, manifests, boundaries
│   ├── store/      # local DBs, Arrow/Parquet, import/export, lineage
│   ├── compute/    # math kernels, graphs, invariant metrics
│   ├── simulate/   # agent-based/physics sandboxes
│   └── run/        # execution, configs, seeds, fixtures
├── research/       # consciousness, games, language, music, invariants, agi
├── memory/         # Atlas entries, embeddings, ledger
├── reports/        # research and refactor outputs
└── internal/       # config, architecture docs, governance
```

Engine is Python-first and native-backed, coordinating the core capabilities.
Research owns questions, hypotheses, tests, falsifiers, results, and anomaly logs.
No raw data, no app-specific scripts, no speculative theory without executable role.

### `domains/` — modeled reality surfaces

```text
domains/
├── self/           # structured profile-derived features, taste coordinates
├── music/          # library, VGM, foobar, MIR/taste graph, composer fingerprints
├── games/          # EFT, Rocket League, Dota, Overwatch, NFL, map/state analysis
├── language/       # Spanish, grammar operators, chunking, typology
├── trails/         # Trails database, continuity/world-memory modeling
├── wiki/           # Wikipedia tools, article schemas, infobox logic
└── aesthetics/     # colors, spaces, visual attraction, environmental preferences
```

A domain defines terrain. It contains models, taxonomies, features, and domain-local docs.
A domain is not research — research belongs in `helix/research/`.

### `apps/` — practical tools

```text
apps/
├── agent_harness/      # workspace validation, test runners
├── music_pipeline/     # ingestion, analysis, retrieval scripts
├── music_bridge/       # library identity resolution
├── music_toolkits/     # C++ audio libraries (libvgm, vgmtools, etc.)
├── foobar_bridge/      # foobar2000 library management
├── foobar-spatial-dsp/ # foobar2000 C++ DSP plugins
├── spc2mid/            # SNES SPC-to-MIDI converter
├── games_pipeline/     # game analysis tools
├── language_pipeline/  # Wikipedia/language processing
├── wiki_tools/         # Wikipedia article tools
└── trails/             # Trails corpus and translation
```

Apps own their local build/cache/output folders. No generic workspace-level `outputs/`.

### `data/` — raw and domain-keyed data

```text
data/
├── raw/            # unprocessed imports (Reddit, Twitter, Steam, Wikipedia, scrobbles)
├── music/          # processed music metadata
├── games/          # processed game data
├── language/       # UD datasets, corpora
├── self/           # cognition datasets
└── wiki/           # (future)
```

Data does not explain itself in prose. Explanations belong in the relevant domain or research module.

## File Placement Rules

Every proposed file or folder must answer at least one:

1. Which boundary does this sharpen?
2. Which friction does this remove?
3. Which affordance does this create?
4. Which existing ambiguity does this collapse?
5. Which future agent failure does this prevent?

If none apply, do not create it.

**Forbidden root-level names:** `outputs/`, `work/`, `misc/`, `archive/`, `notes/`, `labs/`, `old/`, `stuff/`.
Outputs live where their meaning lives.

## Agent Operating Rules

These rules apply to all AI agents working inside Helix.

**Read `DISSONANCE.md` when operator taste, constraints, or profile alignment matter.**

### Behavior
- Do not flatter the operator.
- Do not turn ontology into destiny.
- Prefer mechanisms over vibes.
- Preserve anomalies and contradictions.
- If speculative, mark it as speculative.
- If a claim needs testing, route it to `helix/research/`.
- If a pattern becomes stable, route it to a domain model or engine schema.
- If implementation is needed, produce concrete files — no stubs, no placeholder logic.

### Writing
- Dense, structural prose. Short named sections.
- No academic preamble. No generic AI sludge.
- Good prose makes the workspace more navigable. Bad prose adds fog.

### Research
- Every theory needs confidence tiers.
- Every research module needs falsifiers.
- Every result needs a failure mode.
- Every anomaly gets logged.
- The goal is not to protect the theory. The goal is to find what survives.

### Refactoring
- Compression over decorative clarity.
- Boundaries over buckets.
- Root small. Directories bounded.
- The engine is not the house — `helix/` is the constraint engine; the workspace is the organism.
- Do not add root folders unless they protect a real boundary.

## Active Chamber

```yaml
active_chamber: workspace_refactor
mode: threshold
active_question: Structural refactor in progress.
next_action: Complete root compression, research routing, and domain normalization.
```

One active chamber at a time. Low switching cost. Explicit state. Minimal ambient clutter.

## Design Principles

1. **Compression over decorative clarity.** Names should be short, load-bearing, and obvious from use.
2. **Boundaries over buckets.** A directory exists only if it protects a real conceptual boundary.
3. **Motion over dead order.** The workspace must support active traversal, testing, return, and update.
4. **Root small. Directories bounded.** The root is not an index of every thought.
5. **Outputs live where meaning lives.** Reports live with the research module or app that produced them.
6. **The engine is not the house.** `helix/` is the constraint engine; the workspace is the organism.
7. **Anomalies are first-class.** Contradictions update the map instead of being smoothed away.

## Bandwidth Law

Helix exists to increase usable human+LLM bandwidth.

Bandwidth increases when:
1. Dissonance has fewer exposed decisions, fewer vague buckets, and less root clutter.
2. The LLM has stronger internal constraints, obvious placement rules, and self-describing folder names.
3. The root stays compressed while internal structure carries complexity behind clear boundaries.
4. Expansion happens inside load-bearing walls, not by adding visible sprawl.

Use this model:
- **floor** = Dissonance-side cognitive friction floor
- **ceiling** = maximum complexity the workspace can safely hold
- **walls** = Helix constraints, folder boundaries, schemas, validation rules, and naming contracts

Goal: raise the ceiling while lowering the friction floor.

The root is not where complexity lives. The root is where complexity becomes navigable.

`helix/` contains internal machinery: engine, research, memory, reports, internal config.
`domains/` contains modeled subject areas.
`apps/` contains usable tools.
`data/` contains raw and processed inputs.

A folder is allowed only if it reduces ambiguity more than it increases surface area.
A document is allowed at root only if it improves orientation more than it costs attention.
A rule is allowed only if violating it would cause real drift.

Do not optimize only for human minimalism.
Do not optimize only for LLM explicitness.
Optimize for the combined bandwidth of Dissonance + LLM.

Everything else goes under the hood.
