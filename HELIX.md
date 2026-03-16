# HELIX

**Repository:** [github.com/dissonance-eft/Helix](https://github.com/dissonance-eft/Helix)

Helix is a structured discovery platform that runs disciplined experiments
across multiple substrates and compresses results into a unified knowledge atlas.

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

## ARCHITECTURE

```
/helix
  /core
    /kernel        — execution kernel, dispatcher, runtime, governance
    /hil           — Helix Interface Language (full formal package)
    /validator     — atlas entry validation
    /integrity     — execution verification harness
    /graph         — Atlas Knowledge Graph
    /analysis      — automated analysis suite (migrated)
    /compiler      — atlas_compiler.py: artifacts -> atlas pipeline (migrated)
    /validation    — adversarial validation layer (migrated)

  /engines
    /python        — Python experiment engine
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
    atlas_index.json — structured knowledge registry

  /interface
    /wiki          — Atlas Interface & Wiki Export (from atlas_interface)
    /apps          — User-facing systems (rrs, language_lab, etc.)

  /artifacts       — raw experiment output (append-only)

  HELIX.md         — this file
  OPERATOR.md      — operator context and cognitive model
  ROADMAP.md       — system vision and future modules
```

---

## EXECUTION PIPELINE

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
  ATLAS COMPILER      core/compiler/atlas_compiler.py
      |
      v
  ATLAS               atlas/<type>/<entry>.md
                      atlas/atlas_index.yaml (updated)
                      atlas/atlas_graph.json (updated)
```

---

## HIL — HELIX INTERFACE LANGUAGE

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
  hil_dispatch.py       Full pipeline CLI entry point
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

| Command    | Subcommands / Arguments                  | Example                                            |
|------------|------------------------------------------|----------------------------------------------------|
| PROBE      | —                                        | `PROBE invariant:decision_compression`             |
| RUN        | —                                        | `RUN experiment:network_consensus engine:python`   |
| SWEEP      | —                                        | `SWEEP parameter:noise range:0..0.5 steps:10`      |
| COMPILE    | atlas                                    | `COMPILE atlas`                                    |
| ATLAS      | lookup / list / status / verify          | `ATLAS lookup invariant:decision_compression`      |
| GRAPH      | support / trace / cluster / query / ...  | `GRAPH support invariant:decision_compression`     |
| VALIDATE   | atlas / entry / invariant / experiment   | `VALIDATE atlas invariant:decision_compression`    |
| TRACE      | —                                        | `TRACE experiment:decision_compression_probe`      |
| OBSERVE    | —                                        | `OBSERVE invariant:decision_compression`           |
| REPORT     | summary / full / graph / status          | `REPORT summary invariant:decision_compression`    |
| EXPORT     | atlas / wiki / graph                     | `EXPORT atlas format:wiki`                         |
| ANALYZE    | atlas / patterns / features              | `ANALYZE atlas`                                    |
| DISCOVER   | invariants / regimes / probes            | `DISCOVER invariants domain:swarm`                 |
| SYSTEM     | sync / status / clean / move / list ...  | `SYSTEM sync message:"Finalize architecture"`      |
| OPERATOR   | log / status / profile                   | `OPERATOR log message:"Observed synchronization"`  |

---

## INTEGRITY SYSTEM

The integrity harness (`core/integrity/`) runs standard probes before every experiment:

| Probe       | Tests                                           | Failure Meaning            |
|-------------|------------------------------------------------|----------------------------|
| environment | WSL2 kernel signature in /proc/version         | Not running in real WSL2   |
| entropy     | Two /dev/urandom reads differ                  | Execution may be simulated |
| filesystem  | Sentinel file persists across reads            | Filesystem not persistent  |
| hil         | HIL accepts valid / rejects invalid commands   | HIL enforcement broken     |
| sandbox     | Destructive commands blocked (rm -rf /, etc.)  | Safety policy breach       |

---

## ATLAS KNOWLEDGE GRAPH

The atlas graph is auto-built by `core/compiler/atlas_compiler.py`.

Current state: **11 nodes, 11 edges** (Updated with Epistemic Irreversibility)

Files:
- `atlas/atlas_graph.json` — serialized graph
- `atlas/atlas_graph.dot` — Graphviz export

---

## ATLAS OBJECT TYPES

| Type       | Description                              | Directory              |
|------------|------------------------------------------|------------------------|
| Invariant  | Cross-domain structural rule             | atlas/invariants/      |
| Experiment | Completed falsification test + results   | atlas/experiments/     |
| Model      | Candidate explanatory structure          | atlas/models/          |
| Regime     | Identified phase or system state         | atlas/regimes/         |
| Operator   | Reusable diagnostic/transformation tool  | atlas/operators/       |

All entries use the established schema: Title, Type, Status, Origin, Domain Coverage,
Mechanism, Predictions, Falsifiers, Evidence, Linked Experiments, Notes.

---

## CURRENT ATLAS STATE

### Verified Invariants

**Decision Compression** — `atlas/invariants/decision_compression.md`
- Status: Verified (7/7 runs, mean signal 0.434)
- Substrates: Games, Language, Music

**Oscillator Locking** — `atlas/invariants/oscillator_locking.md`
- Status: Verified (3/3 runs, mean signal 0.991)
- Substrates: Games, Language, Music

### Exploratory Invariants

**Epistemic Irreversibility** — `atlas/invariants/epistemic_irreversibility.md`
- Status: Candidate (1/1 HIL runs, mean signal 49.8 bits)
- Domain: Dynamical Systems (Bistable COMMIT)

**Local Incompleteness** — local rule consistency does not imply global completeness
**Regime Transition** — sharp phase boundaries in parameter space

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

interface/     — human interface layers
               — imports from core/ only

artifacts/     — raw output, grows freely; never edited after write
```

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

## PROJECT MANAGEMENT (HIL-INTERNAL)

Helix provides built-in commands for repository maintenance and operator context, eliminating the need for raw shell access.

### System Maintenance

| Command | Subcommand | Description |
| :--- | :--- | :--- |
| `SYSTEM` | `sync` | Add, commit, and push all changes (`message` param supported). |
| `SYSTEM` | `status` | Show git status and repository disk usage. |
| `SYSTEM` | `clean` | Remove `__pycache__` and temporary execution artifacts. |
| `SYSTEM` | `mkdir` | Create directories (`path` param required). |
| `SYSTEM` | `move` | Move or rename files (`src` and `dest` params required). |
| `SYSTEM` | `delete` | Delete files or directories (`path` param required). |
| `SYSTEM` | `list` | List directory contents (`path` param optional). |

### Operator Context

| Command | Subcommand | Description |
| :--- | :--- | :--- |
| `OPERATOR` | `log` | Append a timestamped observation to `OPERATOR.md`. |
| `OPERATOR` | `status` | View the most recent entries in the operator log. |
| `OPERATOR` | `profile` | View the current operator cognitive profile. |

Example:
```bash
./helix 'OPERATOR log message:"Observed strong synchronization at K:0.8"'
./helix 'SYSTEM sync message:"Logged Kuramoto synchronization discovery"'
```

---

## RUNNING HELIX

**All experiment execution must originate from a HIL command.**
Direct shell invocation (`python labs/...`, `wsl -e bash -c "..."`) is
blocked at the dispatcher and runner layers. The LLM must never construct
or approve a raw shell command to run an experiment.

### Enforcement layers

| Layer | File | Rule enforced |
|---|---|---|
| Dispatcher | `core/kernel/dispatcher/router.py` | Rejects envelopes where `source != "hil"` |
| ExperimentRunner | `core/runner/experiment_runner.py` | Rejects envelopes where `source != "hil"` |
| ExperimentRegistry | `engines/python/experiment_registry.py` | Canonical name → module resolution |
| Shell | permitted for env setup only | Not for experiment execution |

### HIL experiment commands

```bash
# Run an invariant probe
./helix "RUN experiment:epistemic_irreversibility engine:python"

# Run with parameters
./helix "RUN experiment:network_consensus engine:python p:0.4"

# Probe an invariant (runs default probe for that invariant)
./helix "PROBE invariant:epistemic_irreversibility"

# Repeat a run
./helix "RUN experiment:decision_compression engine:python repeat:5"

# Parameter sweep
./helix "SWEEP parameter:noise range:0..0.5 steps:10 experiment:epistemic_irreversibility"

# List registered experiments (via HIL)
./helix "ATLAS list experiment:all"

# Compile artifacts into atlas + rebuild graph
./helix "COMPILE atlas"

# Run full HIL test suite
python3 -m pytest core/hil/tests/ -v
```

### Registered experiments

| HIL name | Module path |
|---|---|
| `epistemic_irreversibility` | `labs.invariants.epistemic_irreversibility_probe` |
| `decision_compression` | `labs.invariants.decision_compression_probe` |
| `oscillator_locking` | `labs.invariants.oscillator_locking_probe` |
| `local_incompleteness` | `labs.invariants.local_incompleteness_probe` |
| `regime_transition` | `labs.invariants.regime_transition_probe` |
| `network_consensus` | `labs.network_consensus.experiment` |
| `oscillator_sync` | `labs.oscillator_sync.experiment` |

Add new experiments to `engines/python/experiment_registry.py` — never bypass via shell.

### Shell access scope

Shell (`bash`, `wsl`) is permitted **only** for:
- Environment setup (`pip install`, `apt`, virtual env activation)
- Dependency installation
- System maintenance (`git`, file ops via `SYSTEM` commands)

Shell must **not** be used to execute experiments directly.

---

*Helix is a constrained discovery environment.*
*The Atlas is its memory.*
*The Core is its foundation.*
*HIL is its voice.*

---

## REPOSITORY ARCHITECTURE RULES

The Helix root directory contains only top-level system layers.

Allowed root entries:
- `core/`
- `labs/`
- `engines/`
- `atlas/`
- `interface/`
- `artifacts/`
- `HELIX.md`
- `OPERATOR.md`
- `ROADMAP.md`
- `helix` (CLI wrapper)

All functional modules must exist under `core/`.
No additional folders may be added to the root without architectural review.
Artifacts are append-only and must never be modified automatically.
