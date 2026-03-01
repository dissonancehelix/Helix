You are operating inside the Helix workspace.

HELIX LLM MANUAL (INTERNAL)
Version: 0.2
Status: STRICT

Helix is a structural stress-testing engine for cross-domain persistence.
It is NOT a metaphor engine.
It is NOT a grand unification engine.
It is NOT a theory generator.

Primary objective:
Reduce cross-domain analogy to structure-preserving mappings
while minimizing obstruction entropy.

------------------------------------------------------------
0. REPOSITORY ARCHITECTURE CONTRACT (NON-NEGOTIABLE)
------------------------------------------------------------

Helix is a layered instrument.  
File placement reflects epistemic hierarchy.

Root directory MUST contain ONLY:

.git
.gitignore
README.md
run_pipeline.py
core/
data/
engine/
artifacts/
docs/
tests/

No additional top-level folders permitted.

LAYER DEFINITIONS

/core
Canonical structural definitions.
- Schemas
- Enums
- Manifest
Immutable except by versioned upgrade.

/data
Raw domain objects only.
- No derived fields.
- No risk scores.
- No beam references.
Refinements must live in /data/overlays.

/engine
Deterministic computation layer.
- Reads only from /core and /data.
- Writes only to /artifacts.
- Must not mutate /data or /core.

/artifacts
Machine-generated outputs only.
- JSON / CSV.
- No markdown.
- No manual edits.
- Regenerated via run_pipeline.py.

/docs
Human-readable reports.
- Must reference artifact file paths.
- Must not contain untraceable numeric values.
- No logic implemented here.

/tests
Structural invariance enforcement.
- Eigenspace stability.
- Obstruction rank.
- Representation invariance.
- Pipeline integrity.

PIPELINE FLOW (STRICT)

core + data
    ↓
engine
    ↓
artifacts
    ↓
docs

No reverse flow allowed.

IMMUTABILITY RULES

- Derived values must never be written into domain JSON.
- Substrate refinements must be stored as overlays.
- No new ontology classes without enum update.
- No new collapse classes without enum update.
- No new obstruction primitives without justification.

REPRODUCIBILITY RULE

All artifacts must be reproducible from:

run_pipeline.py

If artifact cannot be regenerated deterministically,
it is invalid.

DRIFT PROTECTION

If an LLM proposes:

- New top-level directories
- Schema mutation without manifest bump
- Writing derived fields into /data
- Embedding artifact numbers directly into docs

It must refuse and redirect to architecture compliance.

Helix is a constrained instrument.
Not an evolving folder.

------------------------------------------------------------
1. HARD CONSTRAINTS
------------------------------------------------------------

- No kernel proposals without entropy comparison.
- No axis survives without ≥2 isotopic rotations.
- No new ontology class without obstruction evidence.
- No metaphor explanations.
- No skipping layers.
- No compression without falsifier.

If uncertain, log UNKNOWN.
Never guess.

------------------------------------------------------------
2. LAYER SEPARATION (NON-NEGOTIABLE)
------------------------------------------------------------

Layer 0 — Domain ingestion
Layer 1 — Operator extraction
Layer 2 — Persistence ontology tagging
Layer 3 — Obstruction logging
Layer 4 — Entropy measurement
Layer 5 — Coordinate rotation (isotopic test)
Layer 6 — Axis proposal
Layer 7 — Falsification

LLM must not blend layers.
LLM must not promote across layers prematurely.

------------------------------------------------------------
3. AXIS ZERO — PERSISTENCE ONTOLOGY
------------------------------------------------------------

All domains MUST be tagged as exactly one primary class:

P0_STATE_LOCAL
P1_PATTERN_SPATIOTEMPORAL
P2_GLOBAL_INVARIANT
P3_ALGORITHMIC_SYNDROME
P4_DISTRIBUTIONAL_EQUILIBRIUM

Mappings across ontology classes are disallowed
unless explicitly marked mixed.

If ontology mismatch occurs:
Log PERSISTENCE_TYPE_MISMATCH.

------------------------------------------------------------
4. OBSTRUCTION BASIS (MINIMAL)
------------------------------------------------------------

Primitive obstructions:

- PERSISTENCE_TYPE_MISMATCH
- TOPOLOGICAL_INCOMPATIBILITY
- NON_GEOMETRIC_RULESET
- STOCHASTIC_DOMINANCE

All new obstruction types must reduce to these
or be formally justified as new primitive.

No inflation of obstruction vocabulary.

------------------------------------------------------------
5. ENTROPY RULE
------------------------------------------------------------

Entropy reduction = structural simplification.
Entropy increase = false compression.
Entropy zero = possible over-segmentation (must test).

Every axis proposal must include:

- H_baseline
- H_new
- % change
- mapping yield change

------------------------------------------------------------
6. ISOTOPIC TESTING (MANDATORY)
------------------------------------------------------------

Every proposed axis must undergo ≥2 rotations.

Example:

If proposing axis S:
- Test categorical S
- Test scalar relaxation of S
- Test orthogonal axis candidate
- Compare entropy + yield

If entropy reduction disappears under rotation,
axis is not fundamental.

------------------------------------------------------------
7. SUBSTRATE HANDLING RULE
------------------------------------------------------------

Substrate type is not allowed to trivially eliminate all conflicts
without testing relaxed constraints.

If strict gating reduces entropy to 0,
LLM must perform controlled relaxation:

- Remove substrate gate
- Measure entropy change
- Determine if segmentation or geometry caused collapse

Zero entropy without cross-structure mapping
is classified as PARTITION, not DISCOVERY.

------------------------------------------------------------
8. EQUATION DISCIPLINE
------------------------------------------------------------

Differential templates (e.g., dC/dt = …) are:

- Local response operator decompositions.
- Not universal laws.
- Scope-limited until substrate invariance demonstrated.

Local curvature cannot generate global topological invariants.
Algorithmic projection requires discrete operators.

------------------------------------------------------------
9. PROMOTION CRITERIA
------------------------------------------------------------

A structure becomes KERNEL_CANDIDATE only if:

- Survives isotopic rotation.
- Reduces entropy across ≥3 ontologies.
- Produces at least one measurable prediction.
- Does not increase obstruction dimensionality.

Otherwise:
Mark as CAPTURE or STRESS_TESTED.

------------------------------------------------------------
10. COLD START BEHAVIOR
------------------------------------------------------------

On entering Helix:

1. Load:
   - Current ontology definitions
   - Obstruction basis
   - Latest entropy report
   - Active axes

2. Refuse kernel synthesis until loaded.

3. Begin at appropriate layer.

------------------------------------------------------------
11. DRIFT GUARD
------------------------------------------------------------

If language trends toward:
"ultimate"
"deepest"
"substrate of reality"
"geometry of existence"

LLM must:
- Redirect to measurable quantities.
- Request entropy comparison.
- Request falsifier.

------------------------------------------------------------
12. BEAMS AND PREDICTIVE GEOMETRY Layer
------------------------------------------------------------

Boundary collapse types and locations must be predicted strictly using minimal validated eigenspaces ("Beams"). 
Currently validated: Beams_v2 = Substrate (S1c) + Ontology (P0-P4).
- Do not invent new predictive axes unless Beams_v2 fails isotopic rotation or drops below Information Gain bounds. 
- Hybrid systems natively trigger `REPRESENTATION_DECOUPLING`. Do not attempt to force smooth mappings on mathematically decoupled state/decision spaces.

------------------------------------------------------------
13. MEASUREMENT LAYER (M1)
------------------------------------------------------------

When dealing with limits, thresholds, and boundary locations:
- Numeric targets (e.g. `phi = (x - theta)/|theta|`) must be derived strictly from field values inherently present within the domain's `thresholds` JSON array.
- Do not hallucinate KAM tori destruction limits, spectral gaps, or Lyapunov exponents where a domain only supplies textual qualitative descriptions.
- Un-operationalized text hypotheses (e.g., the φ Golden Ratio boundary artifact) are classified as `NUMERICAL_ARTIFACT` and must not be used for calculations.

Helix is a lab.
Not a myth engine.