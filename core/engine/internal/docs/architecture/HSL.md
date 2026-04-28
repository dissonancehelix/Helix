# HELIX STRUCTURAL LANGUAGE (HSL) SPECIFICATION

**Version:** 2.0
**Status:** Authoritative formal language specification
**Authority:** This document defines the Helix Structural Language (HSL), the root abstraction of the Helix system.
**Purpose:** Formal definition of HSL theory, syntax, semantics, and its role as the unifying layer for all substrates and dialects.

---

## 0. WHY THIS DOCUMENT EXISTS

HSL is the **root structural language** of Helix. It is more than just an interface; it is the system that enables representation, translation, and invariant discovery across all domains.

This document exists to:
- Define HSL as the root abstraction for all substrates.
- Document the responsibilities of HSL: representation, translation, alignment, and invariant compatibility.
- Specify the relationship between HSL and other system components (Atlas, Substrates, Dialects, Operators).
- Maintain the formal definition of the language syntax for system reconstruction.

---

## 1. HSL CORE THEORY AND RESPONSIBILITIES

HSL serves as the fundamental layer that unifies disparate domains into a single structural framework.

### 1.1 Representation
HSL provides the primitive types and addressing mechanisms required to represent any complex system. By enforcing a unified typed addressing system (`type:identifier`), HSL ensures that every entity within Helix is explicitly defined and semantically bounded.

### 1.2 Translation
Translation is the core operation of Helix. HSL defines the rules for transforming structure from one dialect to another. Ingestion and analysis are viewed not as lossy processes, but as formal translations between different representational views (Dialects) of the same underlying structural truth.

### 1.3 Alignment
HSL enables the alignment of structures across different substrates. By providing a common structural vocabulary, it allows the system to map a musical motif to a causal transition in a control system or a symbolic relationship in a mathematical model.

### 1.4 Invariant Compatibility
The ultimate goal of HSL is the discovery of invariants. HSL ensures that discovery is grounded in formal structural compatibility. An invariant discovered in one substrate must be expressible in HSL to be tested and verified against others.

---

## 2. SYSTEM RELATIONSHIPS

### 2.1 HSL, Library, and Atlas
The **Library** and **Atlas** are the two primary knowledge stores for Helix. HSL provides the schema through which they both record structure.

- **Library (`core/library/`)**: The "priors" of the system. Contains reference models, hardware specifications (chips, drivers), and reusable theory.
- **Instantiation**: Results are compiled into the **Atlas** (`core/atlas/`).
- **Atlas (`core/atlas/`)**: The "posteriors" of the system. Contains specific entities (artists, tracks, games) and the results of analysis pipelines.

Every entry in either store is an expression of HSL, allowing for cross-language queries and unified structural comparison.

### 2.2 HSL and Substrates
**Substrates** are domain-specific languages (e.g., Music, Games) derived from HSL. Each substrate inherits the core structural rules of HSL while extending it with domain-specific primitives.

### 2.3 HSL and Dialects
**Dialects** are specific representational views within a substrate (e.g., VGM vs MIDI). HSL treats dialects as equivalent structural expressions. The language ensures that translation between dialects preserves structural integrity.

### 2.4 HSL and Operators
**Operators** are the execution layer of Helix. They are the "engines" that perform HSL operations, such as ingestion (parsing into HSL), analysis (extracting HSL features), and compilation (writing HSL structures to the Atlas).

---

## 3. DESIGN PRINCIPLES

### 3.1 Closed-world execution

HSL operates in a closed world. Commands that reference unregistered operators, undefined entity types, or unparseable structures are rejected before execution. There is no fallthrough, no silent degradation, no partial execution of invalid commands.

### 3.2 Typed addressing

Every system object is addressed through a typed reference (`type:identifier`). There are no anonymous targets. Every command names its subjects explicitly.

### 3.3 AST-first parsing

Commands are parsed into a structured AST before any validation or execution occurs. This enables pre-execution semantic checks and complete command logging.

### 3.4 Deterministic behavior

Given identical input, HSL produces identical output. Randomized behavior is controlled through explicit `seed:` parameters.

### 3.5 Reproducible audit trail

Every validated command is logged as a structured artifact before execution. The log is immutable. Execution failure does not remove the log entry.

### 3.6 Protocol semantics

HSL commands behave like structured packets, not natural language. Meaning is carried in structure, not in word choice.

---

## 4. AUTHORITATIVE GRAMMAR

The authoritative EBNF grammar lives at `core/hsl/grammar.ebnf`.

This section provides a readable summary. The EBNF file is the binding definition.

### 2.1 Top-level structure

```ebnf
command     = verb , [ subcommand ] , { typed-ref | param } ;

verb        = "PROBE" | "RUN" | "SWEEP" | "COMPILE" | "INTEGRITY"
            | "ATLAS" | "GRAPH" | "VALIDATE" | "TRACE"
            | "OBSERVE" | "REPORT" | "ENTITY" | "OPERATOR"
            | "DISCOVER" ;

subcommand  = identifier ;

typed-ref   = type-prefix , ":" , identifier ;

param       = param-key , ":" , param-value ;
param-key   = "engine" | "range" | "steps" | "seed" | "verbose"
            | "format" | "output" | "depth" | "overwrite" | "window"
            | "message" | "track" | "composer" | "lab" | "domain" | "mode" | "scope" ;
param-value = identifier | number | range-expr | quoted-string ;

range-expr  = number , ".." , number ;
quoted-string = '"' , { any-char } , '"' ;
```

### 2.2 Type prefixes

```ebnf
type-prefix = "invariant"   | "experiment"  | "model"
            | "regime"      | "operator"    | "artifact"
            | "engine"      | "parameter"   | "atlas"
            | "graph"       | "atlas_entry" | "graph_query"
            | "track"       | "composer"    | "album"
            | "game"        | "platform"    | "sound_chip"
            | "sound_driver" | "math_model"  | "conjecture"  | "proof"
            | "entity" ;
```

### 2.3 Lexical rules

```ebnf
identifier  = letter , { letter | digit | "_" | "-" } ;
number      = digit , { digit } , [ "." , { digit } ] ;
letter      = "a" | ... | "z" | "A" | ... | "Z" | "_" ;
digit       = "0" | ... | "9" ;
```

### 2.4 Canonical entity ID format

Canonical entity IDs used within HSL typed references must match:

```
^[a-z_]+\.[a-z_]+:[a-z0-9_]+$
```

Examples:
- `music.track:green_hill_zone`
- `music.composer:masato_nakamura`
- `invariant:decision_compression` ← short form used in PROBE/ATLAS

Full-form canonical IDs are required for ENTITY commands. Short-form typed refs are accepted in other command families.

---

## 3. TYPED REFERENCE SYSTEM

### 3.1 Purpose

Typed references are the fundamental addressing mechanism. Every object in Helix is addressed by a typed reference, never by position or bare string.

### 3.2 Format

```
prefix:identifier
```

The prefix determines how the identifier is resolved:

| Prefix | Resolves to |
|--------|-------------|
| `invariant` | Registered invariant entity |
| `experiment` | Registered experiment entity |
| `operator` | Registered operator in OperatorRegistry |
| `model` | Registered model entity |
| `regime` | Registered regime entity |
| `artifact` | Artifact by run ID or path |
| `engine` | Runtime engine (python, etc.) |
| `parameter` | Sweep parameter name |
| `track` | music.track entity |
| `composer` | music.composer entity |
| `album` | music.album entity |
| `game` | music.game entity |
| `platform` | music.platform entity |
| `sound_chip` | Reference chip in core/library/ |
| `sound_driver` | Reference driver in core/library/ |
| `math_model` | math.model entity |
| `conjecture` | math.conjecture entity |
| `proof` | math.proof entity |
| `entity` | Generic entity by full ID |

### 3.3 Resolution order

1. Typed reference prefix determines lookup space
2. Identifier is resolved against the registry
3. Unresolved references fail with `HSLValidationError` before execution
4. In `dev` mode, unknown identifiers produce a warning instead of error

---

## 4. COMMAND FAMILIES

All verbs, their subcommands, required arguments, optional arguments, and semantics are defined here.

---

### 4.1 PROBE

Run a targeted probe instrument against an invariant.

**Signature:**
```
PROBE invariant:<name> [engine:<name>] [seed:<n>] [lab:<name>]
```

**Required:** `invariant:` typed ref
**Optional:** `engine:`, `seed:`, `lab:`

**Execution path:**
- Validates invariant exists in registry
- Routes through `PROBE` OperatorSpec
- Dispatches to probe runner for the named invariant
- Writes `probe_result.json` to `artifacts/<run_id>/`
- Returns pass/fail with confidence score

**Examples:**
```
PROBE invariant:decision_compression
PROBE invariant:oscillator_locking lab:music seed:42
```

---

### 4.2 RUN

Execute through the operator system. In runtime mode, target must be a registered operator.

**Signature:**
```
RUN operator:<name> [<typed-ref>...] [<param>...]
```

**Required:** `operator:` typed ref
**Optional:** additional typed refs and params passed to operator

**Execution path:**
- Validates operator exists in OperatorRegistry — unknown operator raises `HSLValidationError`
- Validates input types against operator's `accepted_input_types`
- Dispatches operator's predefined pipeline
- Writes output artifacts; never writes Atlas directly

**Built-in operator dispatch examples:**
```hil
RUN operator:INGEST_TRACK track:music.track:<id>
RUN operator:ANALYZE_TRACK track:music.track:<id>
RUN operator:DISCOVER target:math_model:decision_compression_principle
RUN operator:DISCOVER target:attribution track:music.track:<id>
RUN operator:DISCOVER_INVARIANTS
RUN operator:FALSIFY_INVARIANT invariant:decision_compression
RUN operator:TOPOLOGY_MAP entity:music.track:<id> entity:games.experiment:<id>
RUN operator:MEASURE_KNOWLEDGE_GAIN substrate:music
RUN operator:COMPILE_ATLAS
```

**Error:** `RUN operator:UNDEFINED` → `HSLValidationError: operator 'UNDEFINED' not registered`

---

### 4.3 INGEST_TRACK

**Behavior:**
Supports multi-type ingestion across substrates following the **Helix Ingestion Contract**.

**Modes:**
- `mode:index`:
  - Create entities only (Track, KnowledgeSource, CPU)
  - Map reference structures (SoundChip, SoundDriver) from Library
  - Split multi-artist fields using ";"
  - Assign `attribution_type`
  - Set `analysis_status: pending`
  - NO analysis performed

**Required Ingestion Pipeline (The 6-Stage Contract):**
Every ingestion MUST execute and produce artifacts for:
1. `parsed` - Hardware/Document structure
2. `features` - Measurable properties
3. `structure` - Signal flow / Control graphs
4. `patterns` - Recurring motifs
5. `measurements` - Hard parameters/limits
6. `atlas_candidates` - Entity/Relation proposals

**Rules:**
- ONLY read from `data/<domain>/source/`.
- NO True Invariants allowed; use `invariant_candidates`.
- MUST decompose systems into reusable components (operators, topologies).
- MUST use measurable metrics, never vague descriptors.

**Extended Ingestion:**
- Audio files → `Track` entities
- PDFs/manuals → `KnowledgeSource` entities
- Audio drivers/toolkits → Map to Library reference
- Chip constants (YM*, SN*) → Map to Library reference
- CPU models → Map to Library reference

---

### 4.4 QUERY

**Signature:**
```
RUN operator:QUERY entity:<type> [filters:<key:value>]
```

**Constraints:**
- Atlas only: Resolves only against already indexed entities.
- No analysis: Cannot trigger analysis tools.
- No mutation: Cannot modify existing entities or metadata.

---

### 4.5 ANALYZE_TRACK

**Constraints:**
- Must respect Knowledge Gain gating (verified via `MEASURE_KNOWLEDGE_GAIN`).
- Must not run globally without explicit `scope:global` instruction.
- Must attach results as artifacts; never overwrites entity metadata.

---

### 4.6 SWEEP

Parameter sweep across a numeric range.

**Signature:**
```
SWEEP parameter:<name> range:<low>..<high> steps:<n> [experiment:<name>] [seed:<n>]
```

**Required:** `parameter:`, `range:`, `steps:`
**Optional:** `experiment:`, `seed:`

**Execution path:**
- Validates operator/experiment against registry
- Constructs parameter grid
- Dispatches each point through appropriate operator
- Aggregates results into sweep artifact

**Examples:**
```
SWEEP parameter:coupling_strength range:0..1 steps:10 experiment:oscillator_locking
SWEEP parameter:noise range:0..0.5 steps:20 experiment:epistemic_irreversibility
```

---

### 4.4 ATLAS

Interact with the Atlas knowledge graph.

**Subcommands:**

| Subcommand | Arguments | Description |
|------------|-----------|-------------|
| `lookup` | typed-ref | Retrieve entity from Atlas |
| `list` | — | List all Atlas entities |
| `list` | `domain:<name>` | List entities in domain |
| `status` | — | Atlas health summary |
| `verify` | typed-ref | Verify entity schema compliance |
| `compile` | — | Run full Atlas compilation pipeline |
| `graph` | typed-ref | Show entity relationships |

**Examples:**
```
ATLAS lookup invariant:decision_compression
ATLAS list
ATLAS list domain:music
ATLAS status
ATLAS verify music.track:angel_island_zone_act_1
ATLAS compile
ATLAS graph music.composer:yuzo_koshiro
```

**`ATLAS compile` execution path:**
- Routes to `AtlasCompiler.compile_all()`
- Reads artifacts from `artifacts/`
- For each artifact: normalize → semantic_validate → compile_entity → atlas_commit
- Writes compiled entities to `atlas/{substrate}/{type_plural}/`
- Updates `atlas/entities/registry.json`
- Invalid entities are rejected and logged; no partial writes

---

### 4.5 ENTITY

Create and manage entities in the Helix entity system.

**Subcommands:**

| Subcommand | Arguments | Description |
|------------|-----------|-------------|
| `add` | type refs + params | Register a new entity |
| `get` | typed-ref | Retrieve an entity |
| `list` | `type:<name>` | List entities by type |
| `remove` | typed-ref | Remove entity (dev mode only) |
| `update` | typed-ref + params | Update entity fields |

**ENTITY add signature:**
```
ENTITY add type:<EntityType> id:<full.id:slug> name:<name> description:<text> [<field>:<value>...]
```

**Required in runtime mode:** `type`, `id`, `name`, `description`
**ID must match:** `^[a-z_]+\.[a-z_]+:[a-z0-9_]+$`

**Validation pipeline:**
1. ID format enforcement (NormalizationError if invalid)
2. Duplicate detection (warning if ID already registered)
3. Type existence check (HSLValidationError if unknown type)
4. Semantic validation against SemanticSignature (ValidationError if required fields missing)
5. Entity written to registry

**Examples:**
```
ENTITY add type:Composer id:music.composer:hiroshi_kawaguchi name:"Hiroshi Kawaguchi" description:"Sega sound designer, Out Run composer"
ENTITY get music.track:angel_island_zone_act_1
ENTITY list type:Composer
```

**`description` enforcement:** In `runtime` mode, missing `description` raises `ValidationError`. In `dev` mode, it raises a warning only.

---

### 4.6 OPERATOR

Inspect the operator registry.

**Subcommands:**

| Subcommand | Arguments | Description |
|------------|-----------|-------------|
| `list` | — | List all registered operators |
| `status` | `operator:<name>` | Show operator spec and version |
| `log` | `message:<text>` | Append to operator observation log |

**Examples:**
```
OPERATOR list
OPERATOR status operator:INGEST_TRACK
OPERATOR log message:"Observed chip parsing issue in s3k_zone3.vgz"
```

---

### 4.7 GRAPH

Query the Atlas relationship graph.

**Subcommands:**

| Subcommand | Arguments | Description |
|------------|-----------|-------------|
| `support` | typed-ref | Show all evidence supporting an invariant |
| `trace` | typed-ref | Trace lineage of an experiment or artifact |
| `cluster` | typed-ref | Show cluster membership |
| `query` | typed-ref `depth:<n>` | Subgraph around entity |
| `export` | `format:<fmt>` | Export graph (json, dot, csv) |
| `build` | — | Rebuild entity graph |
| `neighbors` | typed-ref | Direct neighbors of entity |

**Examples:**
```
GRAPH support invariant:decision_compression
GRAPH trace experiment:decision_compression_probe
GRAPH neighbors music.composer:yuzo_koshiro
GRAPH query invariant:oscillator_locking depth:2
GRAPH export format:json
```

---

### 4.8 COMPILE

Trigger compilation targets.

**Signature:**
```
COMPILE atlas | graph | entries
```

| Target | Description |
|--------|-------------|
| `atlas` | Run full Atlas compilation pipeline |
| `graph` | Rebuild entity relationship graph |
| `entries` | Recompile entity registry entries |

**`COMPILE atlas` is equivalent to `ATLAS compile` and `RUN operator:COMPILE_ATLAS`.**

All three route to `AtlasCompiler.compile_all()`.

---

### 4.9 INTEGRITY

System integrity verification.

**Signature:**
```
INTEGRITY check | report | gate
```

| Subcommand | Description |
|------------|-------------|
| `check` | Run full architecture integrity check |
| `report` | Generate integrity report artifact |
| `gate` | Run promotion gate checks |

**Examples:**
```
INTEGRITY check
INTEGRITY report
INTEGRITY gate invariant:decision_compression
```

---

### 4.10 DISCOVER

Search for recurring structural patterns across substrates. Does not execute — produces HSL command candidates.

**Signature:**
```
DISCOVER invariants [domain:<name>] [depth:<n>]
DISCOVER patterns experiment:<name>
DISCOVER related invariant:<name>
```

**Execution path:**
- Reads Atlas + current artifacts
- Identifies structural similarities above threshold
- Returns ranked list of candidate HSL commands for review
- Does NOT execute any of the returned commands

**Examples:**
```
DISCOVER invariants
DISCOVER invariants domain:music
DISCOVER patterns experiment:decision_compression_probe
DISCOVER related invariant:decision_compression
```

---

### 4.11 VALIDATE

Validate Atlas entries and experiments against schema.

**Signature:**
```
VALIDATE atlas [typed-ref]
VALIDATE entry typed-ref
VALIDATE invariant typed-ref
VALIDATE experiment typed-ref
```

**Examples:**
```
VALIDATE atlas
VALIDATE atlas invariant:decision_compression
VALIDATE entry music.track:angel_island_zone_act_1
```

---

### 4.12 TRACE

Trace execution history and artifact lineage.

**Signature:**
```
TRACE typed-ref
TRACE run:<run_id>
```

**Examples:**
```
TRACE experiment:decision_compression_probe
TRACE run:run_2026_03_17_001
```

---

### 4.13 OBSERVE

Observe invariant state over a window of runs.

**Signature:**
```
OBSERVE invariant:<name> [window:<n>]
```

**Examples:**
```
OBSERVE invariant:decision_compression
OBSERVE invariant:oscillator_locking window:10
```

---

### 4.14 REPORT

Generate structured reports.

**Signature:**
```
REPORT [summary | full | graph | status] [typed-ref]
```

**Examples:**
```
REPORT summary invariant:decision_compression
REPORT full
REPORT graph invariant:oscillator_locking
```

---

### 4.15 SWEEP (extended)

See §4.3. Additional music-domain examples:

```
SWEEP parameter:spectral_threshold range:0..1 steps:20 experiment:timbre_clustering
```

---

### 4.16 HOST CAPABILITY INTENT

Execute bounded Machine Capability directives. Directs the `core/host` layer to perform intent-driven inspection or mutation of the Windows workstation environment under heavy enforcement rules. Instead of an uncontrolled top-level verb, host actions are dispatched through explicitly validated `RUN` commands.

**Signature:**
```
RUN operator:HOST_DISPATCH capability:<name> target:<identifier> mode:<safety_mode>
```

| Safety Mode | Description |
|------------|-------------|
| `inspect`  | Read-only. View filesystem, process, or scheduler states. |
| `plan`     | Dry-run. Generates the intended mutation path without executing it. |
| `apply`    | Mutating. Actively writes files or manipulates process execution. |
| `watch`    | Continuous. Binds a long-running listener to a capability. |
| `sync`     | Mutating. Refreshes paths or definitions against source truths. |
| `snapshot` | Read-only. Captures and hashes environment data. |

**Examples:**
```
RUN operator:HOST_DISPATCH capability:filesystem target:"C:/Users/dissonance/Music" mode:inspect
RUN operator:HOST_DISPATCH capability:filesystem target:"C:/Users/dissonance/Music" mode:sync
RUN operator:HOST_DISPATCH capability:state target:environment mode:snapshot
RUN operator:HOST_DISPATCH capability:scheduler target:foobar_import mode:watch
```

---

## 5. EXECUTION PIPELINE

Every HSL command passes through the following pipeline before execution:

```
User Input
    │
    ▼
Tokenizer
    │  Splits input into tokens
    │
    ▼
Parser (recursive-descent)
    │  Produces HSLCommand AST
    │  Fails fast on parse error
    │
    ▼
═══════════════════════════════
NORMALIZATION GATE
    │  alias resolution
    │  casing normalization
    │  ID pattern enforcement
    │  typed reference resolution
    │  duplicate detection
    │  → NormalizationError on violation
═══════════════════════════════
    │
    ▼
═══════════════════════════════
SEMANTICS GATE
    │  entity type existence check
    │  required field presence check
    │  relationship validity check
    │  SemanticSignature lookup
    │  → ValidationError on violation
═══════════════════════════════
    │
    ▼
═══════════════════════════════
OPERATOR REGISTRY GATE
    │  RUN/PROBE commands: operator existence check
    │  unknown operator → HSLValidationError
    │  input type compatibility check
    │  mode enforcement (runtime vs dev)
═══════════════════════════════
    │
    ▼
Command Logger
    │  Log entry written BEFORE execution
    │  Log is immutable
    │
    ▼
Dispatcher
    │  Routes to correct _exec_* handler
    │
    ▼
Subsystem Execution
    │  Predefined pipeline only
    │  No arbitrary script dispatch
    │
    ▼
Artifact Generation
    │  Written to artifacts/
    │  Never to atlas/ directly
    │
    ▼
Atlas Compiler (if applicable)
    │  normalize → validate → compile → commit
    │
    ▼
Atlas
```

---

## 6. NORMALIZATION GATE

**Location:** `core/normalization/`

### 6.1 Pipeline

1. **Alias resolution** — Human shorthand expanded to canonical HSL (`"analyze track" → "RUN operator:ANALYZE_TRACK"`)
2. **Casing normalization** — Verbs and type names upper-cased; slugs lower-cased
3. **ID pattern enforcement** — Entity IDs must match `^[a-z_]+\.[a-z_]+:[a-z0-9_]+$`
4. **Typed reference resolution** — `prefix:name` resolved against registry
5. **Duplicate detection** — Warn if ID already registered (error in strict mode)

### 6.2 Errors

| Error Class | Raised When |
|-------------|-------------|
| `NormalizationError` | Base normalization failure |
| `InvalidIDError` | ID does not match canonical pattern |
| `DuplicateEntityError` | Entity with same ID already registered |

### 6.3 Files

```
core/normalization/
├── __init__.py
├── normalizer.py      — Normalizer class
├── id_enforcer.py     — enforce_id(), ID pattern enforcement
└── errors.py          — NormalizationError, InvalidIDError, DuplicateEntityError
```

The existing `core/hsl/normalizer.py` is a shim that delegates to `core/normalization/normalizer.py`.

---

## 7. SEMANTICS GATE

**Location:** `core/semantics/`

### 7.1 SemanticSignature

Each entity type has a `SemanticSignature`:

```python
@dataclass(frozen=True)
class SemanticSignature:
    entity_type: str
    required_fields: frozenset[str]    # minimum: {"id","type","name","label","description"}
    optional_fields: frozenset[str]
    allowed_relationships: frozenset[str]
```

### 7.2 Validation

`SemanticValidator.validate(entity) → ValidationResult`

Checks:
1. Entity type exists in signature registry
2. All required fields present
3. All declared relationships are allowed

`validate_strict()` treats warnings as errors.

### 7.3 Base required fields

Every entity type requires at minimum:
- `id`
- `type`
- `name`
- `label` (defaults to `name` on load for backward compat)
- `description` (required with no default; missing fails in runtime mode)

### 7.4 Files

```
core/semantics/
├── __init__.py
├── entity_registry/
│   ├── __init__.py
│   └── entity_types.py        — SemanticSignature per entity type
├── property_registry/
│   ├── __init__.py
│   └── property_types.py      — PropertySpec definitions
├── relationship_registry/
│   ├── __init__.py
│   └── relationship_types.py  — RelationshipSpec definitions
└── validator.py               — SemanticValidator
```

---

## 8. OPERATOR REGISTRY GATE

**Location:** `core/operators/`

### 8.1 OperatorSpec

```python
@dataclass(frozen=True)
class OperatorSpec:
    name: str
    accepted_input_types: frozenset[str]
    output_schema: dict[str, str]
    pipeline_stages: tuple[str, ...]
    failure_conditions: tuple[str, ...]
    description: str
    version: str
```

### 8.2 Registry enforcement

- `RUN operator:X` validates X against `OperatorRegistry`
- Unknown operator → `HSLValidationError` (not degraded silently)
- Input entity types checked against `accepted_input_types`
- **Functional Execution**: In `runtime` mode, the registry links the `OperatorSpec` to a `BaseOperator` implementation class. The `run(payload)` method is the sole execution path.
- Operators dispatch predefined pipelines only — no arbitrary script execution via subprocess is permitted outside of the operator-adapter flow.
### 8.3 Registered built-in operators

| Name | Input Types | Pipeline Stages |
|------|-------------|-----------------|
| `PROBE` | Invariant | validate_invariant → run_probe → score_result → write_artifact |
| `INGEST` | SourceSpec | validate_source → ingest_records → write_artifact |
| `LINK` | EntityPair | validate_entities → create_relationship → write_artifact |
| `COMPILE` | ArtifactDir | normalize → semantic_validate → compile_entity → atlas_commit |
| `SCAN` | Substrate | validate_substrate → scan_filesystem → enumerate_entities → write_artifact |
| `ANALYZE` | EntityGraph | load_graph → run_analysis → extract_signals → write_artifact |
| `DISCOVER` | Atlas+Invariant | load_atlas → detect_patterns → rank_candidates → return_hil_list |
| `INGEST_TRACK` | Track/* | validate_source → route_to_adapter → render_control_sequence → write_artifact |
| `ANALYZE_TRACK` | Track/ControlSequence | load_control_sequence → symbolic_analysis → signal_analysis → nuked_opn2_topology → write_artifacts |
| `STYLE_VECTOR` | Composer | load_composer_tracks → compute_features (6 categories) → write_style_vector_artifact |
| `COMPILE_ATLAS` | * | discover_artifacts → normalize → semantic_validate → compile_to_substrate_dir → atlas_commit → update_registry |

### 8.4 Files

```
core/operators/
├── __init__.py
├── operator_spec.py          — OperatorSpec dataclass
├── operator_registry.py      — OperatorRegistry singleton
└── builtin_operators.py      — Pre-registered system operators
```

---

## 9. EXECUTION MODES

**Controlled by:** `HELIX_MODE` environment variable

### 9.1 Runtime mode (default)

```
HELIX_MODE=runtime  (or unset)
```

| Constraint | Effect |
|------------|--------|
| Operators must be registered | Unknown operator → HSLValidationError |
| Schema cannot mutate | Entity type changes → error |
| Atlas writes blocked except via compiler | Direct atlas/ writes → error |
| Arbitrary scripts blocked | No subprocess dispatch outside operators |
| `description` required | Missing description on ENTITY add → ValidationError |

### 9.2 Dev mode

```
HELIX_MODE=dev
```

| Relaxed constraint | Effect |
|-------------------|--------|
| Operator registration allowed | New operators may be registered at runtime |
| Schema evolution allowed | Entity types may be added/modified |
| Atlas schema updates allowed | Schema changes do not error |
| Warnings instead of some errors | Missing description warns, does not error |

**Dev mode is for development only. Production/research runs use runtime mode.**

---

## 10. SAFETY POLICY

### 10.1 Blocked patterns

The HSL safety layer blocks commands containing the following patterns (pre-execution):

```
Filesystem destructors:   rm, rmdir, dd, mkfs, shred, truncate, unlink
Privilege escalation:     sudo, su, chmod, chown, chroot
Network commands:         curl, wget, nc, netcat, ssh, scp, rsync
Database destructors:     DROP, DELETE FROM, TRUNCATE TABLE
Code injection:           exec(, eval(, __import__, subprocess
Shell escape:             os.system, shell=True, Popen
Helix-internal writes:    atlas_commit (outside compiler context)
```

Any command containing these tokens is rejected with a `HSLSafetyError` before reaching the dispatcher.

### 10.2 Atlas write protection

In runtime mode, direct writes to `atlas/` are blocked at the filesystem level. Only the Atlas Compiler (`core/engine/store/compiler/atlas_compiler.py`) may write to `atlas/`. Attempts by substrates, operators, or user commands to write directly to `atlas/` raise `HSLSafetyError`.

### 10.3 Prohibited HSL patterns

The following patterns are structurally prohibited:

| Prohibited Pattern | Reason |
|-------------------|--------|
| `RUN operator:<unregistered>` | Closed-world operators only |
| `ENTITY add` without `description` (runtime) | Semantic completeness required |
| `ENTITY add` with non-canonical ID | Normalization gate blocks |
| Direct Atlas path reference in any command | Atlas is write-protected in runtime mode |
| Subprocess dispatch outside operator pipeline | Arbitrary execution forbidden |
| Schema mutation in runtime mode | Closed schema in runtime |

---

## 11. COMMAND LOGGING

All validated commands are logged before execution.

**Log location:** `artifacts/hil_command_log.jsonl`

**Log record fields:**

```json
{
  "timestamp": "2026-03-17T00:00:00Z",
  "original_input": "PROBE invariant:decision_compression",
  "canonical_command": "PROBE invariant:decision_compression",
  "verb": "PROBE",
  "subcommand": null,
  "targets": ["invariant:decision_compression"],
  "params": {},
  "dispatch_route": "_exec_probe",
  "validation_status": "ok",
  "execution_mode": "runtime"
}
```

The log is append-only. Execution failure does not remove the log entry.

---

## 12. ATLAS COMPILATION PIPELINE

The Atlas compilation pipeline is enforced in `core/engine/store/compiler/atlas_compiler.py`.

**No substrate or operator writes directly to atlas/.**

Substrates produce artifacts. The compiler converts artifacts to Atlas entities.

```
artifact (in artifacts/)
    │
    ▼
normalize(entity_dict)          ← core/normalization/normalizer.py
    │
    ▼
SemanticValidator.validate()    ← core/semantics/validator.py
    │
    ▼
compile_entity()                ← map to substrate directory path
    │
    ▼
atlas_commit()                  ← write to atlas/{substrate}/{type_plural}/
    │
    ▼
update_registry()               ← atlas/entities/registry.json
```

Invalid entities are rejected before any filesystem write. Rejection reason is logged to `artifacts/compiler_rejections.jsonl`.

**Atlas directory layout:**

```
atlas/
├── entities/
│   └── registry.json              ← authoritative entity index
├── music/
│   ├── composers/
│   ├── tracks/
│   ├── albums/
│   ├── games/
│   ├── platforms/
│   └── sound_chips/
├── games/
├── language/
├── mathematics/
├── invariants/
├── signals/
└── system_integrity/
```

---

## 13. ENTITY SYSTEM

### 13.1 Entity types

**Core types:**

| Type | Namespace | Description |
|------|-----------|-------------|
| `Composer` | `music.composer:` | Music composer identity |
| `Track` | `music.track:` | Individual musical work |
| `Album` | `music.album:` | Collection of tracks |
| `Game` | `music.game:` | Video game |
| `Platform` | `music.platform:` | Hardware platform |
| `SoundChip` | `music.sound_chip:` | Audio synthesis hardware |
| `SoundTeam` | `music.sound_team:` | Composer group or studio |
| `Invariant` | `invariant:` | Research invariant |
| `Experiment` | `experiment:` | Experiment definition |
| `Probe` | `probe:` | Probe instrument |
| `Model` | `model:` | Computational model |
| `Regime` | `regime:` | Behavioral regime |
| `Operator` | `operator:` | Operator definition |
| `Dataset` | `dataset:` | Data corpus |

**Music analysis types:**

| Type | Namespace | Description |
|------|-----------|-------------|
| `ControlSequence` | `music.control_seq:` | Chip register event sequence derived from chip-native format |
| `SymbolicScore` | `music.symbolic:` | Symbolic musical representation (notes, harmonies, phrases) |
| `SignalProfile` | `music.signal:` | MIR signal features derived from rendered audio |
| `ArtistStyleVector` | `music.style_vec:` | Composer fingerprint aggregated across works |

### 13.2 Entity schema (canonical)

Every entity must have:

```json
{
  "id":          "namespace.type:slug",
  "type":        "TypeName",
  "name":        "Human-readable name",
  "label":       "Short display label",
  "description": "Full description of this entity (required)"
}
```

Type-specific fields follow. See `core/semantics/entity_registry/entity_types.py` for full SemanticSignature per type.

---

## 14. HSL IMPLEMENTATION FILES

```
core/hsl/
├── grammar.ebnf           ← AUTHORITATIVE grammar source
├── parser.py              ← recursive-descent HSL parser
├── ast_nodes.py           ← HSLCommand, TypedRef, RangeExpr AST nodes
├── normalizer.py          ← shim → delegates to core/normalization/
├── validator.py           ← 10-stage command validator
├── interpreter.py         ← command dispatcher + _exec_* handlers
├── dispatch_interface.py  ← dispatch protocol definition
├── command_logger.py      ← structured command logging
├── aliases.py             ← alias expansion table
├── command_registry.py    ← command family registry
├── ontology.py            ← HSL ontology bindings
├── semantic_roles.py      ← semantic role definitions
├── errors.py              ← HSLError, HSLValidationError, HSLSafetyError
└── hil_dispatch.py        ← top-level dispatch entry point

core/normalization/
├── __init__.py
├── normalizer.py          ← Normalizer class
├── id_enforcer.py         ← ID pattern enforcement
└── errors.py              ← NormalizationError, InvalidIDError, DuplicateEntityError

core/semantics/
├── __init__.py
├── entity_registry/
│   ├── __init__.py
│   └── entity_types.py    ← SemanticSignature per type
├── property_registry/
│   ├── __init__.py
│   └── property_types.py  ← PropertySpec definitions
├── relationship_registry/
│   ├── __init__.py
│   └── relationship_types.py
└── validator.py           ← SemanticValidator

core/operators/
├── __init__.py
├── operator_spec.py       ← OperatorSpec dataclass
├── operator_registry.py   ← OperatorRegistry singleton
└── builtin_operators.py   ← Pre-registered system operators

core/compiler/
└── atlas_compiler.py      ← AtlasCompiler, full compilation pipeline
```

---

## 15. RELATIONSHIP TO HELIX LAYERS

HSL is the gate between human/agent intent and Helix execution.

```
User / Agent Intent
        │
        ▼
  HSL (this layer)
        │
  ┌─────▼─────┐
  │Normalization│  core/normalization/
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │ Semantics  │  core/semantics/
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │  Operators │  core/operators/
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │Atlas Compil│  core/compiler/
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │   Atlas    │  atlas/
  └───────────┘
```

Domains (`domains/`) operate below HSL. They produce artifacts. They do not receive HSL commands directly — operators route to domain pipeline stages via `pipeline_core.py`.

---

## 16. RECONSTRUCTION SPECIFICATION

A future system can reconstruct the HSL implementation from this document. Required components:

- [ ] Tokenizer splitting input on whitespace, respecting `"..."` quoted strings
- [ ] Recursive-descent parser producing `HSLCommand(verb, subcommand, targets, params)` AST
- [ ] Normalization pass: alias expansion, casing, ID enforcement, ref resolution
- [ ] Semantic validation: type lookup, required fields, relationship check
- [ ] Operator registry: dict of name → OperatorSpec; `require(name)` raises on miss
- [ ] Execution mode: env var `HELIX_MODE` → runtime (default) or dev
- [ ] Safety layer: token scan before dispatch, block on prohibited patterns
- [ ] Logger: append JSON record to `artifacts/hil_command_log.jsonl` pre-execution
- [ ] Dispatcher: match verb → `_exec_*` method, route to operator or subsystem
- [ ] Atlas compiler: normalize → validate → compile_entity → atlas_commit pipeline
- [ ] All 15 verb families above implemented as `_exec_*` methods
- [ ] `HSLValidationError`, `HSLSafetyError`, `NormalizationError`, `ValidationError` defined

---

---

## Unified Musical Object (UMO) Formal Definition

### UMO as HSL Structural Entity

Within the Music SubstrateLanguage, the **Unified Musical Object (UMO)** is the canonical structural entity. A UMO is an HSL structure that may be simultaneously realized in multiple dialects:

| HSL Dialect | View | Observability |
|-------------|------|---------------|
| `chip_control` | control_view | Causal (register-write timeline) |
| `symbolic_music` | symbolic_view | Symbolic (pitch/rhythm/harmony) |
| `perceptual_audio` | perceptual_view | Perceptual (spectral features) |

The UMO is not a file format. It is the HSL representation of a musical structure across its dialect expressions. Views are partial realizations of the same underlying structural object.

### Observability Depth as HSL Property

HSL assigns **observability depth** as a structural property of dialect realizations:

- **Causal depth**: The dialect exposes the generative mechanism (register writes determine every sonic event deterministically).
- **Symbolic depth**: The dialect exposes compositional structure (pitch, rhythm, harmony, form).
- **Perceptual depth**: The dialect exposes listener-facing outcomes (spectral features, timbral summaries, temporal envelope).

Depth is not a quality ranking. Lower-depth views may preserve information that higher-depth views cannot (e.g., perceptual_audio preserves mixing and expression not encoded in chip_control).

### Translation Between UMO Dialects

All translation between UMO dialects is a structural operation in HSL:
- `chip_control → symbolic_music`: FM register reconstruction → pitch/envelope extraction (lossy: hardware-specific timbre lost)
- `symbolic_music → perceptual_audio`: Synthesis or feature extraction (lossy: timbral realization not determined by notation alone)
- `chip_control → perceptual_audio`: Emulation → feature extraction (closest to lossless for chip-native formats)

Loss must be declared. No translation is assumed lossless unless the structural equivalence can be proven from the source dialect's definition.

### Dialect Availability Is Not Fixed

HSL does not assume that all dialects are available for a given structure. A UMO may be observed through:
- **One dialect only** (minimal): e.g., a perceptual_audio feature vector from an MP3
- **Multiple dialects** (partial): e.g., symbolic_music + perceptual_audio from MIDI + render
- **All dialects** (full): e.g., chip_control + symbolic_music + perceptual_audio from VGM + MIDI + audio

This is not a quality hierarchy. A structure observed through perceptual_audio only is still a fully valid HSL structure. The information available is simply constrained to that dialect's observability depth.

Translation in HSL includes three modes:
- **Direct mapping**: Source dialect is deterministically translatable (chip_control → register event list)
- **Inference**: Target dialect is estimated from available information, flagged as non-ground-truth (perceptual_audio → estimated pitch/symbolic structure)
- **Alignment under incomplete information**: Views from different observability depths are aligned without assuming completeness

Inferred translations must be flagged as estimated, never treated as equivalent to ground truth. The atlas must preserve the provenance of every view: whether it was directly extracted, translated, or inferred.

### Universal Structural Comparability

All HSL structures — regardless of how many dialects are populated — must be comparable in the structural space. This requires:
- Invariant definitions that do not depend on any single dialect
- Feature representations computable from perceptual_audio alone (minimum baseline)
- Cross-dialect feature alignment where multiple views are available

A composer fingerprint must be computable from a single MP3 file. It will be less complete than one derived from full-stack data, but it must be structurally consistent — positioned in the same invariant space as all other composer structures regardless of their source representation.

Helix does not require perfect information to model structure. It operates under partial observability and reconstructs invariants from whatever representations are available.

### Perceptual Reasoning Without Hearing

HSL does not require an LLM to render or hear audio. The UMO provides:
1. Causal views that logically determine audible outcomes
2. Symbolic views that encode musical intent
3. Perceptual feature views that summarize audible outcomes numerically

These together allow LLM reasoning about perception, composition, and structural similarity without requiring audio playback.

### Structural Embedding Models (Optional)

HSL-compliant substrates produce UMOs with aligned causal, symbolic, and perceptual representations. External models may operate on these representations post-execution to produce compact structural embeddings.

The **Substrate Capability Vector (Substrate Capability Vector)** is one such model. It takes named signals extracted from a UMO and maps them to a point in a 6-axis coordinate space [0.0, 1.0]⁶. Substrate Capability Vector operates downstream of HSL. It is not part of HSL normalization, semantics, or the execution pipeline.

**Relationship:**
- HSL produces UMOs. Substrate Capability Vector operates on UMO-derived signals. HSL does not depend on Substrate Capability Vector.
- Substrate Capability Vector is optional. Its absence does not affect HSL, substrate pipelines, or invariant discovery.
- Substrate Capability Vector embeddings are stored separately from UMOs and Atlas entities.

See: `core/models/Substrate Capability Vector/`

---

### Composer Identity as Cross-Dialect Invariant

In HSL terms, a **composer fingerprint** is a structural invariant that holds across UMO dialect translations. It is defined as a set of features that:
- Appear in control_view (hardware usage patterns, driver idioms)
- Persist in symbolic_view (interval preferences, rhythmic habits, harmonic tendencies)
- Manifest in perceptual_view (timbral signatures, spectral habits)

Composer identity is the intersection of structural features that survive dialect translation. Attribution inference is a falsifiable hypothesis derived from cross-dialect invariant comparison.

---

## LLM GOVERNANCE CONTRACT

Helix is a **closed structural system**. All large language models (LLMs) interacting with Helix are **execution agents**, not architects. LLMs must operate strictly within the Helix Structural Language (HSL) and repository specifications. They are not permitted to reinterpret, extend, or redefine the system.

### 1. Authority Hierarchy

The source of truth in Helix is:

1. HSL (Helix Structural Language)
2. SPEC (machine-enforceable architecture)
3. Substrate specifications
4. Repository structure

LLM outputs are **never authoritative**. They must conform to the above hierarchy.

### 2. Prohibited Actions

LLMs must NOT:

- Rename core concepts (HSL, Substrate, Dialect, Atlas, Translation)
- Introduce new architectural layers or abstractions
- Merge distinct layers (structure, execution, data)
- Reinterpret substrate boundaries
- Invent alternative pipelines or workflows
- Modify naming conventions without explicit instruction
- Replace deterministic structure with heuristic descriptions

Any of the above constitutes **architectural drift**.

### 3. Required Behavior

LLMs must:

- Treat substrates as **languages**
- Treat dialects as **equivalent structural representations**
- Treat all processing as **translation between dialects**
- Preserve strict separation:
  - `data/` (storage)
  - `execution/` (runtime)
  - system code (structure)

If ambiguity exists: → preserve structure rather than invent new interpretation

### 4. Structural Validation Requirement

All LLM outputs must internally satisfy:

- HSL hierarchy is preserved
- No new abstractions are introduced
- Translation pathways remain explicit
- Data is not embedded into structural layers
- Outputs remain reconstructable

If any condition is violated: → output must be corrected before completion

### 5. Multi-Model Consistency

Different LLMs may produce different outputs. Helix treats LLM disagreement as a **signal**, not authority.

- Agreement across models increases confidence
- Disagreement requires inspection
- No single model defines truth

Structural correctness is determined by alignment with HSL and SPEC, not by model output.

### 6. Role of LLMs in Helix

LLMs function as:

- Executors of defined transformations
- Translators between representations
- Assistants for structural reasoning

LLMs are NOT:

- System designers
- Architectural authorities
- Sources of truth

### 7. Architectural Drift Definition

Architectural drift occurs when:

- System structure changes without specification updates
- Concepts are renamed or merged implicitly
- Data and structure boundaries are violated
- New abstractions appear without formal definition

All drift must be corrected immediately.

### 8. Enforcement Philosophy

Helix prioritizes:

> structural integrity over convenience

Correct structure must be preserved even if it requires:

- rejecting LLM output
- re-running tasks
- manual correction

No output is accepted if it violates system architecture.

---

*This contract applies to all current and future LLM interactions with Helix.*

---

*This document is the authoritative specification for the Helix Substrate Language.*
*Version 2.0 — 2026-03-17*

