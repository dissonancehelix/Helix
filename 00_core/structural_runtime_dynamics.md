# Structural Runtime Dynamics (SRD)

## 1. Definition
Structural Runtime Dynamics (SRD) is the study of instability amplification, damping, and entropy propagation in mutable directed graphs with runtime state transitions.

## 2. Necessary Conditions (ALL must hold)
- **Runtime state mutation.**
- **Directed propagation edges.**
- **Potential feedback cycles.**
- **Partial observability or state hiding.**
- **Absence of full compile-time constraint elimination.**

If any condition fails → SRD does not apply.

## 3. Canonical Model (Current Minimal Form)
`CFS = α + β₁·log(FanIn) + β₂·(CycleDensity / (1 + k·ValidationCoverage)) + β₃·ExceptionDensity`

**Mark as:** `SRD_MODEL_V2 (PROVISIONAL — EMPIRICAL)`

## 4. Domain-of-Applicability Table

**Validated:**
- Python
- JavaScript
- Lua
- Go
- Ruby

**Invalid:**
- Rust
- Haskell
- OCaml
- Idris

**WHY invalid:** Compile-time elimination of runtime entropy. Purely functional language constraints (Haskell) or strict memory borrow lifetimes (Rust) structurally forbid runtime cycles and hidden state accumulation without explicit markers, invalidating the SRD geometric assumptions. Exception variants like `Result` evaluate as observable return paths, not hidden propagation.

## 5. Explicit Falsifiers
SRD is falsified if:
- Fragility does not scale under mutation.
- Damping term has no measurable effect.
- Entropy injection does not correlate with instability.
- Model fails cross-ecosystem replication.

No ambiguity.
