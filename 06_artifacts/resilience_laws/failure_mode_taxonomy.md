# Failure Mode Taxonomy

These are structural failure vectors identifiable purely from codebase topology and validation constraints.

## 1. Initialization-Order Collapse
*   **Signals:** High import inter-dependency, extensive global variable definitions, topological cycles.
*   **Stabilizers:** Lazy evaluation loops, strict Substrate initialization boundaries.
*   **Falsifiers:** Shuffling import sequential order without compilation breakage.

## 2. Validator Bypass Collapse (Silent Decay)
*   **Signals:** Missing schema validation, sparse explicit typing, `except Exception: pass` clusters.
*   **Stabilizers:** Rigid boundary models, invariant checks, strict typing.
*   **Falsifiers:** Input fuzzing natively catches the bypass without domain intervention.

## 3. Name-Coupling Collapse
*   **Signals:** Hardcoded strings mapping to functional states, lack of static reflection constraints.
*   **Stabilizers:** Symbol extractors, declarative class hierarchies protecting logic paths.
*   **Falsifiers:** Re-naming internal states causes immediate compilation halt rather than deferred runtime failure.

## 4. Trace Rot Collapse
*   **Signals:** High proportion of orphaned documentation trace links, stale ID metadata.
*   **Stabilizers:** Cross-registry trace tracking during automated generation (e.g., Atlas indexer).
*   **Falsifiers:** Trace IDs structurally dictate behavior, breaking the execution loop if decoupled.

## 5. Confidence Inflation (The Trap)
*   **Signals:** High test suite line-coverage but low mechanical relevance (excessive mocking of core IO).
*   **Stabilizers:** Hostility mutation tests, true Adversarial Analog frameworks.
*   **Falsifiers:** 5% dropout mutations consistently fail the active pipeline, rather than passing cleanly.
