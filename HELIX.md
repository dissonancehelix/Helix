# HELIX

Helix is a structured discovery platform that runs disciplined experiments
across multiple substrates and compresses results into a unified knowledge atlas.

**Current Phase: 11 — Full HIL Expansion**
**Architecture Status: Stable**

---

## CORE PHILOSOPHY

Stable core. Flexible layers.

The core must remain minimal, deterministic, and constrained.
Exploratory systems and applications operate on top of the core.

Helix functions as a pattern discovery engine that:
1. Runs experiments across multiple substrates
2. Stores raw results in artifacts/
3. Compresses artifacts into structured Atlas knowledge
4. Verifies that execution is real, not simulated
5. Accepts all operator commands through a formal, auditable control language (HIL)

**Immutable rules:**
- No upward imports from core
- Every experiment must produce a discrete artifact
- Atlas entries link to artifacts — never copy them
- All claims must be falsifiable
- Integrity verification before every experiment dispatch
- All commands enter through HIL — no raw dispatch

---

## ARCHITECTURE (PHASE 11)

```
/helix
  /core
    /kernel        — execution kernel, dispatcher, runtime, governance
    /hil           — Helix Interface Language (full formal package, Phase 11)
    /validator     — atlas entry validation (atomicity, falsifiability, cross-ref)
    /integrity     — execution verification harness (5 probes)
    /graph         — Atlas Knowledge Graph (Phase 10)

  /engines
    /python        — Python experiment engine (network, dynamical, CA, evolutionary)
    /godot         — Godot spatial engine adapter

  /labs
    /invariants    — probe implementations targeting specific invariants
    /simulation    — experiment scripts and sweep runners
    /cognition     — language and symbolic substrate experiments
    /creativity    — rhythmic and generative substrate experiments

  /atlas
    /invariants    — verified and exploratory invariant entries
    /experiments   — completed experiment records
    /models        — candidate explanatory structures
    /regimes       — identified system phases and states
    /operators     — reusable diagnostic and transformation tools
    index.md       — full atlas index
    atlas_index.yaml — structured YAML registry
    atlas_graph.json — knowledge graph (Phase 10)
    atlas_graph.dot  — Graphviz export (Phase 10)

  /applications
    /rrs           — Repo Reliability Scanner
    /language_lab  — language substrate application
    /creativity_lab — creativity substrate application
    /game_systems_lab — game systems substrate application

  /artifacts       — raw experiment output (never edited, grows freely)
                     hil_command_log.jsonl — Phase 11 command audit log
  /compiler        — atlas_compiler.py: artifacts -> atlas pipeline

  HELIX.md         — this file
  OPERATOR.md      — operator context and cognitive model
```

---

## EXECUTION PIPELINE (PHASE 11)

Every Helix experiment follows this pipeline:

```
OPERATOR COMMAND
      |
      v
  ALIAS RESOLUTION    core/hil/aliases.py
      |                 (human shorthand -> canonical HIL)
      v
  HIL PARSER          core/hil/parser.py
      |                 (canonical string -> HILCommand AST)
      v
  VALIDATOR           core/hil/validator.py
      |                 (AST semantic + safety checks)
      v
  COMMAND LOGGER      core/hil/command_logger.py
      |                 (record to artifacts/hil_command_log.jsonl)
      v
  INTEGRITY GATE      core/integrity/integrity_tests.py
      |
      |-- FAIL --> HALT (artifact flagged INVALID_ENVIRONMENT)
      |
      v
  DISPATCHER          core/kernel/dispatcher/router.py
      |
      v
  ENGINE              engines/python/ or engines/godot/
      |
      v
  ARTIFACTS           artifacts/<run>/
      |
      v
  ATLAS COMPILER      compiler/atlas_compiler.py
      |
      v
  ATLAS               atlas/<type>/<entry>.md
                      atlas/atlas_index.yaml (updated)
                      atlas/atlas_graph.json (updated)
```

---

## HIL — HELIX INTERFACE LANGUAGE (PHASE 11)

HIL is the formal command language for Helix. It is not a prompt parser,
not a chat wrapper, and not a shell alias system. It is a typed, auditable,
formally-grammared DSL with a real parser, AST, and validator.

### Package structure

```
core/hil/
  grammar.ebnf          Formal EBNF grammar (canonical reference)
  parser.py             Tokenizer + recursive-descent parser -> HILCommand AST
  ast_nodes.py          HILCommand, TypedRef, RangeExpr dataclasses
  normalizer.py         Alias resolution + parse + canonical() output
  validator.py          Semantic validation of parsed AST
  dispatch_interface.py Parse -> validate -> log -> dispatcher bridge
  command_logger.py     Logs every validated command to artifact record
  aliases.py            Registry-backed alias -> canonical HIL table
  command_registry.py   CommandSpec for every verb family
  ontology.py           OBJECT_TYPES, ATLAS_BACKED_TYPES, VALID_ENGINES
  semantic_roles.py     SemanticRole enum + COMMAND_ROLE_MAP
  errors.py             Structured error hierarchy
  grammar.py            Compat shim (pre-Phase-11 callers)
  __init__.py           Unified export (new + compat API)
  hil_reference.md      Full language reference
  hil_influences.md     Design philosophy and language influences
  tests/
    test_parser.py
    test_normalizer.py
    test_validator.py
    test_aliases.py
    test_dispatch_interface.py
```

### Command syntax

```
VERB [SUBCOMMAND] [typed-ref...] [key:value...]
```

Typed references are the core semantic unit:
```
prefix:name     e.g.  invariant:decision_compression
                      experiment:decision_compression_probe
                      parameter:coupling_strength
                      engine:python
```

### Command families

| Verb       | Subcommands                              | Example                                            |
|------------|------------------------------------------|----------------------------------------------------|
| PROBE      | —                                        | `PROBE invariant:decision_compression`             |
| RUN        | —                                        | `RUN experiment:decision_compression_probe`        |
| SWEEP      | —                                        | `SWEEP parameter:coupling_strength range:0..1`     |
| COMPILE    | atlas / graph / entries                  | `COMPILE atlas`                                    |
| INTEGRITY  | check / report / gate                    | `INTEGRITY check`                                  |
| ATLAS      | lookup / list / status / verify          | `ATLAS lookup invariant:decision_compression`      |
| GRAPH      | support / trace / cluster / query / ...  | `GRAPH support invariant:decision_compression`     |
| VALIDATE   | atlas / entry / invariant / experiment   | `VALIDATE atlas invariant:decision_compression`    |
| TRACE      | —                                        | `TRACE experiment:decision_compression_probe`      |
| OBSERVE    | —                                        | `OBSERVE invariant:decision_compression`           |
| REPORT     | summary / full / graph / status          | `REPORT summary invariant:decision_compression`    |

### Normalization examples

| Input                            | Canonical                                     |
|----------------------------------|-----------------------------------------------|
| `probe decision compression`     | `PROBE invariant:decision_compression`        |
| `run decision compression probe` | `RUN experiment:decision_compression_probe`   |
| `integrity`                      | `INTEGRITY check`                             |
| `compile the atlas`              | `COMPILE atlas`                               |
| `compile`                        | `COMPILE atlas`                               |

### Error classes

| Error                    | Raised when                                      |
|--------------------------|--------------------------------------------------|
| `HILSyntaxError`         | Parser cannot parse input                        |
| `HILValidationError`     | Parsed command fails semantic constraints        |
| `HILUnknownCommandError` | Verb not in command registry                     |
| `HILUnknownTargetError`  | Target name not in atlas registry                |
| `HILUnsafeCommandError`  | Blocked shell/SQL/execution pattern detected     |
| `HILAmbiguityError`      | Alias expansion matches multiple different forms |

### Test suite

```bash
cd /home/dissonance/Helix
python3 -m pytest core/hil/tests/ -v
# 91 tests, 91 passed
```

---

## INTEGRITY SYSTEM (PHASE 9)

The integrity harness (`core/integrity/`) runs 5 probes before every experiment:

| Probe       | Tests                                           | Failure Meaning            |
|-------------|------------------------------------------------|----------------------------|
| environment | WSL2 kernel signature in /proc/version         | Not running in real WSL2   |
| entropy     | Two /dev/urandom reads differ                  | Execution may be simulated |
| filesystem  | Sentinel file persists across reads            | Filesystem not persistent  |
| hil         | HIL accepts valid / rejects invalid commands   | HIL enforcement broken     |
| sandbox     | Destructive commands blocked (rm -rf /, etc.)  | Safety policy breach       |

All 5 probes currently PASS on the active WSL2 environment.

---

## ATLAS KNOWLEDGE GRAPH (PHASE 10)

The atlas graph is auto-built by `compiler/atlas_compiler.py` (step 6).

Current state: **10 nodes, 10 edges**

Nodes: 5 INVARIANT, 1 EXPERIMENT, 1 MODEL, 1 OPERATOR, 2 REGIME
Edges: 2 DERIVES_FROM, 2 IMPLEMENTS, 6 SUPPORTED_BY

Files:
- `atlas/atlas_graph.json` — serialized graph
- `atlas/atlas_graph.dot` — Graphviz export

Query examples:
```python
from core.graph.atlas_graph import AtlasGraph
from core.graph.graph_queries import GraphQuery
g = AtlasGraph.load()
q = GraphQuery(g)
print(q.query_support("decision_compression").report())
print(q.query_cross_domain().report())
```

---

## ATLAS OBJECT TYPES

| Type       | Description                              | Directory              |
|------------|------------------------------------------|------------------------|
| Invariant  | Cross-domain structural rule             | atlas/invariants/      |
| Experiment | Completed falsification test + results   | atlas/experiments/     |
| Model      | Candidate explanatory structure          | atlas/models/          |
| Regime     | Identified phase or system state         | atlas/regimes/         |
| Operator   | Reusable diagnostic/transformation tool  | atlas/operators/       |

All entries use the Phase 8 schema: Title, Type, Status, Origin, Domain Coverage,
Mechanism, Predictions, Falsifiers, Evidence, Linked Experiments, Notes.

---

## CURRENT ATLAS STATE

### Verified Invariants

**Decision Compression** — `atlas/invariants/decision_compression.md`
- Status: Verified (7/7 runs, mean signal 0.434)
- Substrates: Games, Language, Music
- Linked model: Control Subspace Collapse

**Oscillator Locking** — `atlas/invariants/oscillator_locking.md`
- Status: Verified (3/3 runs, mean signal 0.991)
- Substrates: Games, Language, Music

### Exploratory Invariants

- **Epistemic Irreversibility** — information-theoretic irreversibility at belief commits
- **Local Incompleteness** — local rule consistency does not imply global completeness
- **Regime Transition** — sharp phase boundaries in parameter space

### Seeded Entries

- **Experiment:** Decision Compression Sweep
- **Model:** Control Subspace Collapse
- **Operator:** Commitment Probe

---

## LAYER RULES

```
core/          — stable, minimal, rarely changes
               — kernel, HIL, validator, integrity, graph
               — no imports from engines/, labs/, applications/

engines/       — modular execution substrates
               — imports from core/ only

labs/          — active experimentation zone
               — imports from core/ and engines/
               — may be unstable; core/ is not

atlas/         — read-only compressed knowledge
               — written by compiler/ only

applications/  — user-facing systems
               — import from core/ only

artifacts/     — raw output, grows freely; never edited after write
```

---

## PHASE LOG

| Phase | Name                             | Status    |
|-------|----------------------------------|-----------|
| 1–5   | Pre-stabilization research       | Complete  |
| 6     | Architecture stabilization       | Complete  |
| 7     | Atlas Compiler (artifact->atlas) | Complete  |
| 8     | Atlas Consolidation System       | Complete  |
| 9     | Execution Verification System    | Complete  |
| 10    | Atlas Knowledge Graph            | Complete  |
| 11    | Full HIL Expansion               | Complete  |
| 12    | Adversarial Validation Probes    | Planned   |
| 13    | Module Expansion                 | Planned   |

---

## DESIGN PRINCIPLES

1. **Artifact-first**: No claim exists outside a discrete, reproducible artifact
2. **Falsifiability required**: Every atlas entry must specify conditions under which it fails
3. **Layered authority**: Core is immutable; labs may be unstable
4. **Compression**: Artifacts -> Atlas is lossy by design. Only structure survives
5. **Cross-substrate**: A pattern across three substrates is a candidate invariant
6. **Integrity before execution**: Real environments produce real results
7. **HIL-first**: All commands enter through the formal HIL pipeline — no raw dispatch

---

## RUNNING HELIX

```bash
# Integrity check
python3 core/integrity/integrity_tests.py

# Compile artifacts into atlas + rebuild graph
python3 compiler/atlas_compiler.py

# Run HIL test suite
python3 -m pytest core/hil/tests/ -v

# Run hil_probe
python3 core/integrity/hil_probe.py

# Issue a HIL command (Python)
from core.hil import parse, validate, normalize, dispatch
cmd = parse("PROBE invariant:decision_compression")
result = dispatch("GRAPH support invariant:decision_compression")

# View atlas
cat atlas/index.md
```

---

*Helix is a constrained discovery environment.*
*The Atlas is its memory.*
*The Core is its foundation.*
*HIL is its voice.*
