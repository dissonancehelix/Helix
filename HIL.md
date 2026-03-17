# HELIX INTERFACE LANGUAGE (HIL) SPECIFICATION

**Version:** 2.0
**Status:** Authoritative formal language specification
**Authority:** This document defines the Helix Interface Language. The grammar.ebnf file is the authoritative grammar source.
**Purpose:** Formal definition of HIL syntax, semantics, execution pipeline, and constraints. Helix must be reconstructible from this document alone.

---

## 0. WHY THIS DOCUMENT EXISTS

HIL is the **only** legal interface to the Helix execution system.

Every command that executes in Helix passes through HIL. No substrate, operator, or external script may invoke Helix components by other means in runtime mode.

This document exists to:
- Define HIL syntax precisely enough for re-implementation
- Document all command families, their signatures, and semantics
- Specify the execution pipeline and its gates
- Define what is prohibited and why
- Enable Helix to regenerate from this spec alone

If code conflicts with this document, this document takes precedence until intentionally revised.

---

## 1. DESIGN PRINCIPLES

### 1.1 Closed-world execution

HIL operates in a closed world. Commands that reference unregistered operators, undefined entity types, or unparseable structures are rejected before execution. There is no fallthrough, no silent degradation, no partial execution of invalid commands.

### 1.2 Typed addressing

Every system object is addressed through a typed reference (`type:identifier`). There are no anonymous targets. Every command names its subjects explicitly.

### 1.3 AST-first parsing

Commands are parsed into a structured AST before any validation or execution occurs. This enables pre-execution semantic checks and complete command logging.

### 1.4 Deterministic behavior

Given identical input, HIL produces identical output. Randomized behavior is controlled through explicit `seed:` parameters.

### 1.5 Reproducible audit trail

Every validated command is logged as a structured artifact before execution. The log is immutable. Execution failure does not remove the log entry.

### 1.6 Protocol semantics

HIL commands behave like structured packets, not natural language. Meaning is carried in structure, not in word choice.

---

## 2. AUTHORITATIVE GRAMMAR

The authoritative EBNF grammar lives at `core/hil/grammar.ebnf`.

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
            | "message" | "track" | "composer" | "lab" | "domain" ;
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

Canonical entity IDs used within HIL typed references must match:

```
^[a-z_]+\.[a-z_]+:[a-z0-9_]+$
```

Examples:
- `music.track:angel_island_zone_act_1`
- `music.composer:jun_senoue`
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
| `sound_chip` | music.sound_chip entity |
| `entity` | Generic entity by full ID |

### 3.3 Resolution order

1. Typed reference prefix determines lookup space
2. Identifier is resolved against the registry
3. Unresolved references fail with `HILValidationError` before execution
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
- Validates operator exists in OperatorRegistry — unknown operator raises `HILValidationError`
- Validates input types against operator's `accepted_input_types`
- Dispatches operator's predefined pipeline
- Writes output artifacts; never writes Atlas directly

**Built-in operator dispatch examples:**
```
RUN operator:PROBE invariant:decision_compression
RUN operator:INGEST_TRACK track:music.track:angel_island_zone_act_1
RUN operator:ANALYZE_TRACK track:music.track:angel_island_zone_act_1
RUN operator:STYLE_VECTOR composer:music.composer:yuzo_koshiro
RUN operator:COMPILE_ATLAS
RUN operator:SCAN
RUN operator:DISCOVER
```

**Error:** `RUN operator:UNDEFINED` → `HILValidationError: operator 'UNDEFINED' not registered`

---

### 4.3 SWEEP

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
3. Type existence check (HILValidationError if unknown type)
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

Search for recurring structural patterns across substrates. Does not execute — produces HIL command candidates.

**Signature:**
```
DISCOVER invariants [domain:<name>] [depth:<n>]
DISCOVER patterns experiment:<name>
DISCOVER related invariant:<name>
```

**Execution path:**
- Reads Atlas + current artifacts
- Identifies structural similarities above threshold
- Returns ranked list of candidate HIL commands for review
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

## 5. EXECUTION PIPELINE

Every HIL command passes through the following pipeline before execution:

```
User Input
    │
    ▼
Tokenizer
    │  Splits input into tokens
    │
    ▼
Parser (recursive-descent)
    │  Produces HILCommand AST
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
    │  unknown operator → HILValidationError
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

1. **Alias resolution** — Human shorthand expanded to canonical HIL (`"analyze track" → "RUN operator:ANALYZE_TRACK"`)
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

The existing `core/hil/normalizer.py` is a shim that delegates to `core/normalization/normalizer.py`.

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
- Unknown operator → `HILValidationError` (not degraded silently)
- Input entity types checked against `accepted_input_types`
- Operators dispatch predefined pipelines only — no arbitrary script execution

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
| Operators must be registered | Unknown operator → HILValidationError |
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

The HIL safety layer blocks commands containing the following patterns (pre-execution):

```
Filesystem destructors:   rm, rmdir, dd, mkfs, shred, truncate, unlink
Privilege escalation:     sudo, su, chmod, chown, chroot
Network commands:         curl, wget, nc, netcat, ssh, scp, rsync
Database destructors:     DROP, DELETE FROM, TRUNCATE TABLE
Code injection:           exec(, eval(, __import__, subprocess
Shell escape:             os.system, shell=True, Popen
Helix-internal writes:    atlas_commit (outside compiler context)
```

Any command containing these tokens is rejected with a `HILSafetyError` before reaching the dispatcher.

### 10.2 Atlas write protection

In runtime mode, direct writes to `atlas/` are blocked at the filesystem level. Only the Atlas Compiler (`core/compiler/atlas_compiler.py`) may write to `atlas/`. Attempts by substrates, operators, or user commands to write directly to `atlas/` raise `HILSafetyError`.

### 10.3 Prohibited HIL patterns

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

The Atlas compilation pipeline is enforced in `core/compiler/atlas_compiler.py`.

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

## 14. HIL IMPLEMENTATION FILES

```
core/hil/
├── grammar.ebnf           ← AUTHORITATIVE grammar source
├── parser.py              ← recursive-descent HIL parser
├── ast_nodes.py           ← HILCommand, TypedRef, RangeExpr AST nodes
├── normalizer.py          ← shim → delegates to core/normalization/
├── validator.py           ← 10-stage command validator
├── interpreter.py         ← command dispatcher + _exec_* handlers
├── dispatch_interface.py  ← dispatch protocol definition
├── command_logger.py      ← structured command logging
├── aliases.py             ← alias expansion table
├── command_registry.py    ← command family registry
├── ontology.py            ← HIL ontology bindings
├── semantic_roles.py      ← semantic role definitions
├── errors.py              ← HILError, HILValidationError, HILSafetyError
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

HIL is the gate between human/agent intent and Helix execution.

```
User / Agent Intent
        │
        ▼
  HIL (this layer)
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

Substrates (`substrates/`) operate below HIL. They produce artifacts. They do not receive HIL commands directly — operators route to substrate pipeline stages via `pipeline_core.py`.

---

## 16. RECONSTRUCTION SPECIFICATION

A future system can reconstruct the HIL implementation from this document. Required components:

- [ ] Tokenizer splitting input on whitespace, respecting `"..."` quoted strings
- [ ] Recursive-descent parser producing `HILCommand(verb, subcommand, targets, params)` AST
- [ ] Normalization pass: alias expansion, casing, ID enforcement, ref resolution
- [ ] Semantic validation: type lookup, required fields, relationship check
- [ ] Operator registry: dict of name → OperatorSpec; `require(name)` raises on miss
- [ ] Execution mode: env var `HELIX_MODE` → runtime (default) or dev
- [ ] Safety layer: token scan before dispatch, block on prohibited patterns
- [ ] Logger: append JSON record to `artifacts/hil_command_log.jsonl` pre-execution
- [ ] Dispatcher: match verb → `_exec_*` method, route to operator or subsystem
- [ ] Atlas compiler: normalize → validate → compile_entity → atlas_commit pipeline
- [ ] All 15 verb families above implemented as `_exec_*` methods
- [ ] `HILValidationError`, `HILSafetyError`, `NormalizationError`, `ValidationError` defined

---

*This document is the authoritative specification for the Helix Interface Language.*
*Version 2.0 — 2026-03-17*
