# HIL Design Influences

This document explains the specific design decisions in HIL and which
language/system traditions influenced each one. It does not mythologize
the language. It explains the logic.

---

## 1. SQL

**Influence:** Explicit target references, typed query structure, clear verb-object model.

SQL requires you to name what you are operating on. `SELECT * FROM experiments`
is not ambiguous — you named the table. HIL follows this: every command names
its target explicitly with a typed reference.

```
ATLAS lookup invariant:decision_compression
```

Not:
```
lookup the decision compression invariant
```

The verb is the operation. The typed reference is the target. Parameters
are named. There is no positional ambiguity.

Like SQL's separation of DQL/DML/DDL, HIL separates:
- Query operations (ATLAS, GRAPH, TRACE, REPORT)
- Execution operations (RUN, PROBE, SWEEP)
- Infrastructure operations (COMPILE, INTEGRITY, VALIDATE)

---

## 2. Lisp / Symbolic Systems

**Influence:** AST-first interpretation, minimal primitives, composability.

HIL is not parsed into a string and pattern-matched. Every command is
parsed into a typed AST (`HILCommand`) before any interpretation happens.
The AST is the authoritative representation.

This means:
- Normalization is AST → canonical string, not string → string
- Validation operates on typed AST nodes, not regex matches
- Dispatch consumes the AST, not raw text

The HIL primitive set is intentionally minimal: verb, subcommand,
typed-ref, param. Everything is composed from these.

Like Lisp, the goal is: make the structure explicit, make the semantics
derivable from the structure, never rely on positional word order alone.

---

## 3. Unix / Shell Philosophy

**Influence:** Small commands, deterministic behavior, explicit failure on invalid input.

HIL commands do one thing. `PROBE` probes. `COMPILE` compiles.
There is no multi-step implicit behavior in a single command.

Like Unix tools, HIL fails loudly and immediately when input is invalid.
There is no silent fallback, no default behavior on ambiguous input.

```
PROBE banana_space
→ HILSyntaxError: Unexpected bare word 'banana_space'
```

The parser does not guess. If the input is wrong, the error is immediate
and specific. This is the Unix way: make failure loud and early.

The safety policy is also Unix-inspired: a small, explicit blocklist of
destructive patterns, checked before any other processing.

---

## 4. Workflow DSLs / Research Pipelines

**Influence:** Reproducible experiment execution, auditable command traces, parameterized sweeps.

HIL is designed for research pipelines where reproducibility matters.
Every command that enters the pipeline is logged as a structured artifact
record. The log contains the original input, the canonical form, the full
AST, the dispatch route, and the integrity gate status.

This means: you can reconstruct exactly what happened, in what order,
with what parameters, from the log alone.

```
SWEEP parameter:coupling_strength range:0..1 engine:python
→ logged to artifacts/hil_command_log.jsonl
```

The SWEEP command is parameterized and range-typed — not freeform strings.
This is a direct workflow DSL influence: parameters are typed and bounded
so they can be reproduced exactly.

---

## 5. Graph Query Systems

**Influence:** Relationship-oriented commands, explicit semantic roles.

The GRAPH command family is scaffolded for Atlas Knowledge Graph traversal.
The subcommands (`support`, `trace`, `cluster`, `query`) are relational:

```
GRAPH support invariant:decision_compression
GRAPH trace experiment:decision_compression_probe
```

This is not a general graph query language (not Cypher, not SPARQL),
but the design intentionally makes relationship semantics first-class
through the `semantic_roles.py` module and `SemanticRole` enum.

---

## 6. Spanish State/Condition Semantics

**Influence:** Distinguishing stable properties from runtime state.

Spanish distinguishes *ser* (permanent identity) from *estar* (temporary state).
This distinction appears in HIL's object model:

- An invariant's `status: verified` is a stable property (ser) — it reflects
  the accumulated evidence across many runs.
- An experiment's `status: running` is a runtime state (estar) — it reflects
  the current execution state, not a permanent truth.

This distinction informs how the validator treats status fields and how
the graph builder models node properties. It is not enforced syntactically
in HIL v1.0 but is preserved in the ontology and semantic roles design.

---

## 7. Russian / Case-Heavy Languages

**Influence:** Explicit semantic markers, role marking over word-order reliance.

Russian marks the grammatical role of each word with a suffix (case ending),
not word order. This means you can reorder words and still understand
the sentence structure from the word forms alone.

HIL's typed references serve the same function:

```
RUN experiment:decision_compression_probe engine:python
```

`engine:python` is explicitly marked as an engine parameter. If you moved it:

```
RUN engine:python experiment:decision_compression_probe
```

The parser handles it correctly because the roles are explicit in the
prefix markers, not inferred from position.

This is why bare words are rejected after the verb/subcommand position —
HIL does not rely on word order to infer object roles. Every object
announces what it is.

---

## 8. Telecommunications / Protocol Design

**Influence:** Commands parse like structured packets with explicit fields.

A network protocol packet has defined field positions or explicit field
markers. There is no ambiguity in a well-formed packet.

HIL commands are designed the same way. Every field has a type marker
(`invariant:`, `range:`, `engine:`). Every command has a defined structure
from the grammar. A command is either well-formed or it is rejected at
parse time — there is no partial acceptance or soft parsing.

This is why HIL uses typed references everywhere rather than positional
arguments. A positional API `RUN decision_compression python` is fragile
and order-dependent. A protocol-style API
`RUN experiment:decision_compression engine:python` is explicit and
order-independent.

---

## Summary Table

| Influence              | Applied in                                      |
|------------------------|------------------------------------------------|
| SQL                    | Typed targets, verb-object structure, families  |
| Lisp / symbolic        | AST-first, typed nodes, minimal primitives      |
| Unix                   | Small commands, explicit failure, blocklist     |
| Workflow DSLs          | Logging, reproducibility, parameterized sweeps  |
| Graph query systems    | GRAPH family, SemanticRole, relationship verbs  |
| Spanish ser/estar      | Stable vs. runtime status in object model       |
| Russian case marking   | Typed prefixes as role markers, order-agnostic  |
| Telecommunications     | Packet-style explicit fields, strict parsing    |
