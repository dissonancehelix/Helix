# HIL — Helix Interface Language Specification

**Version:** 1.0 (Phase 6 scaffold)
**Status:** Draft — full implementation in Phase 7

---

## Purpose

HIL is the command language for Helix. Every action that enters the kernel — running an experiment, launching a probe, sweeping parameters — must be expressed as a HIL command. HIL normalizes intent into a canonical form before dispatch.

HIL is not a general programming language. It is a **narrow command interface** designed for one purpose: telling Helix what to do in a deterministic, auditable way.

---

## Grammar

```
command  ::= verb target? param*
verb     ::= "run" | "probe" | "sweep" | "observe" | "report" | "validate" | "reset"
target   ::= identifier ("." identifier)*
param    ::= key "=" value
key      ::= [a-zA-Z_][a-zA-Z0-9_]*
value    ::= [^\s]+
identifier ::= [a-zA-Z_][a-zA-Z0-9_]*
```

### Examples

```
run python.oscillator substrate=python steps=1000
probe python.network depth=3
sweep python.dynamical param=alpha range=0.1,2.0 steps=50
observe atlas.experiments window=7d
report atlas.invariants format=markdown
validate kernel.hil strict=true
reset scope=discovery
```

---

## Verb Definitions

| Verb | Description |
|------|-------------|
| `run` | Execute an experiment or probe |
| `probe` | Run a single structural probe on a target |
| `sweep` | Run a parameter sweep over a target |
| `observe` | Read and report on atlas state |
| `report` | Generate a structured report |
| `validate` | Validate a system component or command |
| `reset` | Reset a scope to clean state |

---

## Normalization Pipeline

All raw HIL input passes through three stages before dispatch:

```
raw string
    │
    ▼
[parse_command]     — tokenize, identify verb and target
    │
    ▼
[validate_command]  — check required fields against schema
    │
    ▼
[normalize_command] — produce canonical envelope dict
    │
    ▼
dispatcher.route(envelope)
```

### Normalized Envelope Format

```json
{
  "verb":    "run",
  "target":  "python.oscillator",
  "params":  {"substrate": "python", "steps": "1000"},
  "source":  "hil",
  "version": "1.0"
}
```

---

## Validation Rules

1. Verb must be in the allowed set
2. Required fields for the verb must be present
3. Target must be a valid dotted identifier
4. Params must be `key=value` pairs with no spaces in values
5. Unknown verbs are rejected immediately — no fallthrough

---

## Error Handling

HIL errors are returned as structured dicts, never exceptions at the dispatch boundary:

```json
{"status": "error", "stage": "parse", "message": "Unknown verb 'fly'"}
{"status": "error", "stage": "validate", "message": "Verb 'run' requires a target"}
```

---

## Extension

New verbs may be added in future phases by extending `HIL_VERBS` and `HIL_SCHEMA` in `kernel/hil/grammar.py`. The normalization and dispatch pipeline does not need to change.
