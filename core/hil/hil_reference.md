# HIL Reference — Helix Interface Language v1.0

HIL is the formal command language for the Helix research platform.
It is not a chat interface, not a general-purpose language, and not
a shell wrapper. It is a constrained, typed, auditable DSL for
controlling experiment dispatch, atlas queries, and graph traversal.

---

## Syntax

```
VERB [SUBCOMMAND] [typed-ref...] [key:value...]
```

All tokens are whitespace-separated. No parentheses, no operators,
no control flow.

---

## Typed References

The core semantic unit of HIL is the **typed reference**:

```
prefix:name
```

Where `prefix` is a known object type and `name` is the object ID.

| Prefix       | Object Class           | Atlas-backed |
|------------- |------------------------|:------------:|
| `invariant`  | Atlas invariant        | yes          |
| `experiment` | Atlas experiment       | yes          |
| `model`      | Atlas model            | yes          |
| `regime`     | Atlas regime           | yes          |
| `operator`   | Atlas operator         | yes          |
| `parameter`  | Sweep parameter name   | no           |
| `engine`     | Execution engine       | no           |
| `artifact`   | Stored artifact file   | no           |
| `atlas`      | The atlas as a whole   | no           |
| `graph`      | The knowledge graph    | no           |
| `atlas_entry`| Generic atlas entry    | no           |
| `graph_query`| Graph query object     | no           |

---

## Command Families

### PROBE
Run a targeted probe against an invariant, experiment, or operator.

```
PROBE invariant:decision_compression
PROBE invariant:oscillator_locking
PROBE operator:commitment_probe
```

### RUN
Execute an experiment, operator, or model.

```
RUN experiment:decision_compression_probe
RUN experiment:decision_compression_probe engine:python
RUN operator:commitment_probe
```

### SWEEP
Sweep a parameter across a numeric range.

```
SWEEP parameter:coupling_strength range:0..1
SWEEP parameter:coupling_strength range:0..1 engine:python
SWEEP parameter:threshold range:0.1..0.9
```

### COMPILE
Compile atlas entries, graph, or full pipeline.

```
COMPILE atlas
COMPILE graph
COMPILE entries
```

### INTEGRITY
Run the environment integrity verification suite.

```
INTEGRITY check
INTEGRITY report
INTEGRITY gate
```

### ATLAS
Look up, list, or verify atlas entries.

```
ATLAS lookup invariant:decision_compression
ATLAS list
ATLAS status model:control_subspace_collapse
ATLAS verify invariant:oscillator_locking
```

### GRAPH
Query or export the Atlas Knowledge Graph.

```
GRAPH support invariant:decision_compression
GRAPH trace invariant:decision_compression
GRAPH cluster
GRAPH build
GRAPH export
```

### VALIDATE
Validate atlas entries against HIL schemas.

```
VALIDATE atlas invariant:decision_compression
VALIDATE entry experiment:decision_compression_sweep
VALIDATE invariant invariant:oscillator_locking
```

### TRACE
Trace the execution history of an experiment or artifact.

```
TRACE experiment:decision_compression_probe
TRACE experiment:decision_compression_sweep
```

### OBSERVE
Passively observe an invariant or experiment without triggering execution.

```
OBSERVE invariant:decision_compression
OBSERVE experiment:decision_compression_sweep
```

### REPORT
Generate a report on atlas objects or the knowledge graph.

```
REPORT summary invariant:decision_compression
REPORT full
REPORT graph
```

---

## Parameters

| Param key | Values                | Used by          |
|-----------|----------------------|------------------|
| `engine`  | `python`, `godot`    | RUN, SWEEP, PROBE|
| `range`   | `low..high` (floats) | SWEEP            |
| `steps`   | integer              | SWEEP            |
| `seed`    | integer              | RUN, SWEEP       |
| `verbose` | identifier           | INTEGRITY, etc.  |
| `format`  | identifier           | REPORT, ATLAS    |
| `output`  | identifier           | REPORT, GRAPH    |
| `depth`   | integer              | GRAPH, TRACE     |

---

## Normalization

HIL normalizes semantically equivalent inputs to one canonical string.

| Input                            | Canonical                                     |
|----------------------------------|-----------------------------------------------|
| `probe decision compression`     | `PROBE invariant:decision_compression`        |
| `run decision compression probe` | `RUN experiment:decision_compression_probe`   |
| `integrity`                      | `INTEGRITY check`                             |
| `compile the atlas`              | `COMPILE atlas`                               |
| `compile atlas`                  | `COMPILE atlas`                               |

Alias resolution runs before parsing. Aliases are registry-backed and
explicit — no fuzzy matching, no inference.

---

## Error Classes

| Error                    | Raised when                                           |
|--------------------------|-------------------------------------------------------|
| `HILSyntaxError`         | Tokenizer or parser cannot parse the input            |
| `HILValidationError`     | Parsed command fails semantic constraints             |
| `HILUnknownCommandError` | Verb not in command registry                          |
| `HILUnknownTargetError`  | Target name not found in atlas registry               |
| `HILUnsafeCommandError`  | Command contains a blocked safety pattern             |
| `HILAmbiguityError`      | Alias expansion matches multiple patterns             |

All error classes expose `.to_dict()` for structured logging.

---

## Validator Behavior

The validator checks (in order):

1. Grammar validity (parser already enforced)
2. Known command family (verb in registry)
3. Subcommand required (per CommandSpec)
4. Target type validity (prefix in OBJECT_TYPES)
5. At least one target (if spec requires it)
6. Target type match (prefix must be in required_target_types)
7. Engine name validity
8. Range validity (low <= high, numeric)
9. Atlas registry lookup (if registry provided)
10. Defense-in-depth blocked patterns

---

## Safety Policy

The following patterns are unconditionally blocked at parse time:

- Shell commands: `rm`, `dd`, `mkfs`, `chmod`, `chown`, `wget`, `curl`, `sudo`
- SQL injection: `DROP`, `DELETE FROM`
- Device writes: `> /dev/`
- Python execution: `exec(`, `eval(`, `__import__`, `os.system`, `subprocess`

Rejection is immediate and raises `HILUnsafeCommandError`.

---

## Command Logging

Every validated command is logged to `artifacts/hil_command_log.jsonl`.

Log record fields:
- `timestamp`         ISO-8601 UTC
- `original`          Raw input string
- `canonical`         Normalized HIL string
- `ast_summary`       Full parsed AST dict
- `targets`           List of typed reference strings
- `engine`            Resolved engine name
- `dispatch_route`    Inferred or explicit route
- `validation_status` Always `"VALID"` for logged commands
- `integrity_gate`    `true`/`false`/`null`

---

## Dispatch Routes

| Verb        | Route                                |
|-------------|--------------------------------------|
| `PROBE`     | `core/integrity -> labs/invariants`  |
| `RUN`       | `engines/python/engine`              |
| `SWEEP`     | `engines/python/engine`              |
| `COMPILE`   | `compiler/atlas_compiler`            |
| `INTEGRITY` | `core/integrity/integrity_tests`     |
| `ATLAS`     | `atlas/`                             |
| `GRAPH`     | `core/graph/`                        |
| `VALIDATE`  | `core/validator/`                    |
| `TRACE`     | `artifacts/`                         |

---

## Compat API

Pre-Phase-11 callers can still use:

```python
from core.hil import parse_command, validate_command, normalize_command
```

These wrap the new system and return legacy dict formats.
