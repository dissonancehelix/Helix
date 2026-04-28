# core/map/

Machine-readable cognitive map.

## Layered file roles

The seven YAMLs are not interchangeable. Each holds one layer of the graph:

| File | Layer | Holds |
|---|---|---|
| `patterns.yaml` | **Compressed pattern IDs** | Stable, named patterns. Source of truth for pattern identity. |
| `gates.yaml` | **Discriminations** | Boundaries the profile draws (admit/deny, trusted/untrusted, …). |
| `examples.yaml` | **Evidence anchors** | Concrete examples linking up to patterns and down to domain/data paths. |
| `probes.yaml` | **Open questions** | Active questions/tests/measurements targeting patterns. |
| `anomalies.yaml` | **Contradictions** | Unresolved tensions and false positives, kept first-class. |
| `links.yaml` | **Semantic relations** | Cross-references binding the graph; consumed by drift checks. |
| `sources.yaml` | **Attention boundary** | Registry of allowed evidence sources and modes (Phase 3+). Defines what Helix may attend to. |

**Map files must not become prose dumps.** A YAML entry that wants to be a paragraph belongs in a domain README or a report — link to it, do not inline it.

## Stable shape

Every YAML uses:

```yaml
version: 0.1
status: scaffold
items: [...]
```

Top-level shape is fixed so generators and checks never have to guess between list and mapping.

## Rules

1. One canonical ID per node. IDs are snake_case and never reused.
2. No major pattern exists only in prose. If `DISSONANCE.md` names it, it must appear here.
3. Domain READMEs elaborate; they do not redefine patterns.
4. Every example supports at least one pattern, or is marked `status: unresolved`.
5. Contradictions become `anomalies.yaml` entries, not silent edits.
6. When a definition changes, downstream domains/labs are flagged stale until reviewed.

## Source-of-truth direction

`DISSONANCE.md` is human-readable canon. `core/map/` is machine-readable canon.
They must agree. When they disagree, raise an anomaly rather than silently reconciling.

