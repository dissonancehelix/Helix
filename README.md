Version: 1.0
Status: HARDENED / BASIS LOCK (CE-OS ACTIVE)

Helix is a structural stress-testing engine for cross-domain persistence.

Primary objective:
Reduce cross-domain analogy to structure-preserving mappings
while minimizing obstruction entropy.

Discover the minimal structural constraints required for existence. What structure must be present for any collapse geometry to form?

------------------------------------------------------------
0. REPOSITORY ARCHITECTURE CONTRACT (NON-NEGOTIABLE)
------------------------------------------------------------

Helix is a layered instrument.
File placement reflects epistemic hierarchy.

Root directory MUST contain ONLY:

.git
.gitignore
README.md
helix.py
core/
data/
layers/
infra/ (Includes /os/ CE-OS Kernel)
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

/layers
Layered Constraint Pyramid logic (L1-L5).
- Phenomena, Elements, Primitives, Operators, Expansion.

/infra
Infrastructure, I/O, Hashing, Trace verification.
- Reads only from /core and /data.
- Writes only to /artifacts.
- Must not mutate /data or /core.

/artifacts
Machine-generated outputs only.
- JSON / CSV.
- No markdown.
- No manual edits.
- Regenerated via `helix.py run`.
- Must include a run manifest linking outputs to inputs.

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
- (Optional) Doc traceability checks.

PIPELINE FLOW (STRICT)

core + data
    ↓
layers + infra
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

helix.py run

If an artifact cannot be regenerated deterministically,
it is invalid.

DRIFT PROTECTION

If an LLM proposes:

- New top-level directories
- Schema mutation without manifest bump
- Writing derived fields into /data
- Embedding artifact numbers directly into docs
- Manual edits inside /artifacts

It must refuse and redirect to architecture compliance.

Helix is a constrained instrument.
Not an evolving folder.

------------------------------------------------------------
1. EXECUTION LAYERS (DO NOT BLEND)
------------------------------------------------------------

Layer 0 — Domain ingestion
Layer 1 — Operator extraction
Layer 2 — Persistence ontology tagging (P0–P4)
Layer 3 — Obstruction logging
Layer 4 — Entropy measurement
Layer 5 — Coordinate rotation (isotopic test)
Layer 6 — Axis proposal (Meta-Kernel Lab)
Layer 7 — Falsification / Necessity Suite
Layer 8 — Consolidation (Measurement / Operator Algebra)
Layer 9 — Hardening (CE-OS Privilege Rings / Determinism Probes)
Layer 10 — Intervention Transfer (Structural Vaccines)

LLM must not blend layers.
LLM must not promote across layers prematurely.

------------------------------------------------------------
2. HARD CONSTRAINTS
------------------------------------------------------------

- No kernel proposals without entropy comparison.
- No axis survives without ≥2 isotopic rotations.
- No new ontology class without obstruction evidence.
- No metaphor explanations.
- No skipping layers.
- No compression without falsifier.
- No kernel access without Ring 0 authorization.
- No artifact promotion without determinism pass.

If uncertain, log UNKNOWN.
Never guess.

------------------------------------------------------------
3. CORE PRIMITIVE: PERSISTENCE ONTOLOGY (AXIS ZERO)
------------------------------------------------------------

All domains MUST be tagged as exactly one primary class:

P0_STATE_LOCAL (Dynamics)
P1_PATTERN_SPATIOTEMPORAL (Information)
P2_GLOBAL_INVARIANT (Execution)
P3_ALGORITHMIC_SYNDROME (Irreversibility)
P4_DISTRIBUTIONAL_EQUILIBRIUM (Identity)
(Plus P5_VALUE_AXIS projected)

Mappings across ontology classes are disallowed
unless explicitly marked mixed.

If ontology mismatch occurs:
Log PERSISTENCE_TYPE_MISMATCH.

------------------------------------------------------------
4. MINIMAL STRUCTURAL BASIS (LOCK)
------------------------------------------------------------

The Helix kernel is defined by four orthogonal, independent bases:

B1_BASIN: Energy/effort transition boundary.
B2_EXPRESSION: Volumetric state-space dimension.
B3_COORDINATION: Multi-agent coupling/network depth.
B4_SYMBOLIC_DEPTH: Logic-stack / referential recursion limit.

A basis vector must satisfy:
- Independence (Pairwise MI < 0.60)
- Necessity (Ablation loss > 15%)
- Sufficiency (Reconstruction > 90%)
- Invariance (Survives isotopic rotation)

Failure to satisfy triggers demotion to "Mode".

------------------------------------------------------------
5. OBSTRUCTION BASIS (MINIMAL)

Primitive obstructions:

- PERSISTENCE_TYPE_MISMATCH
- TOPOLOGICAL_INCOMPATIBILITY
- NON_GEOMETRIC_RULESET
- STOCHASTIC_DOMINANCE

All new obstruction types must reduce to these
or be formally justified as new primitive.

No inflation of obstruction vocabulary.

------------------------------------------------------------
5. ENTROPY + ROTATION DISCIPLINE
------------------------------------------------------------

Entropy reduction = structural simplification.
Entropy increase = false compression.
Entropy zero = possible over-segmentation (must test).

Every axis proposal must include:

- H_baseline
- H_new
- % change
- mapping yield change

ISOTOPIC TESTING (MANDATORY)

Every proposed axis must undergo ≥2 rotations.

Example:

If proposing axis S:
- Test categorical S
- Test scalar relaxation of S
- Test orthogonal axis candidate
- Compare entropy + yield

If entropy reduction disappears under rotation,
axis is not fundamental.

SUBSTRATE HANDLING RULE

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
6. EQUATION DISCIPLINE
------------------------------------------------------------

Differential templates (e.g., dC/dt = …) are:

- Local response operator decompositions.
- Not universal laws.
- Scope-limited until substrate invariance demonstrated.

Local curvature cannot generate global topological invariants.
Algorithmic projection requires discrete operators.

------------------------------------------------------------
7. PROMOTION CRITERIA
------------------------------------------------------------

A structure becomes KERNEL_CANDIDATE only if:

- Survives isotopic rotation.
- Reduces entropy across ≥3 ontologies.
- Produces at least one measurable prediction.
- Does not increase obstruction dimensionality.

Otherwise:
Mark as CAPTURE or STRESS_TESTED.

------------------------------------------------------------
8. MEASUREMENT LAYER (M1)
------------------------------------------------------------

When dealing with limits, thresholds, and boundary locations:

- Numeric targets must be derived strictly from field values inherently present
  within the domain’s thresholds data (if present).
- Do not hallucinate spectral gaps, Lyapunov exponents, KAM limits, etc.
  where the domain supplies only qualitative text.

Un-operationalized numeric hypotheses are classified as:
NUMERICAL_ARTIFACT
and must not be used for calculations.

If boundary location is not structurally expressible,
record the obstruction and stop.
Do not invent proxies.

------------------------------------------------------------
9. BEAMS + PREDICTIVE GEOMETRY
------------------------------------------------------------

Boundary collapse types and locations must be predicted strictly using minimal
validated eigenspaces ("Beams").

Currently validated:
Beams_v2 = Substrate (S1c) + Ontology (P0–P4)

- Do not invent new predictive axes unless Beams_v2 fails isotopic rotation
  or drops below Information Gain bounds.
- Hybrid systems natively trigger REPRESENTATION_DECOUPLING.
  Do not attempt to force smooth mappings on mathematically decoupled
  state/decision spaces.

------------------------------------------------------------
10. MINIMAL STRUCTURAL BASIS REGISTRY (LIVING, NOT STATIC)
------------------------------------------------------------

The Helix Structural Basis is a living, testable atlas.

Definition:
A minimal set of independent mathematical axes that span the measurable collapse geometry of constraint systems.

Rules:
- The atlas must be regenerated from /artifacts outputs via `helix.py run`.
- Docs may summarize atlas findings ONLY by referencing artifact paths.
- No manual edits to atlas outputs.
- If a “law” is claimed, it must have:
  (a) artifact anchoring
  (b) a falsifier hook
  (c) a regression test when feasible

Topological refinement:
If continuous-field systems collapse via discrete invariant update,
use substrate refinement overlays (e.g., CONTINUOUS_TOPOLOGICAL)
without mutating base domains.

------------------------------------------------------------
11. CROSS-LINKING + TRACEABILITY (REQUIRED)
------------------------------------------------------------

Artifacts must be cross-linked through a run manifest.

`helix.py run` MUST write:

/artifacts/run_manifest.json

It must include:
- timestamp
- git commit hash (if available)
- dataset hash (domains + overlays)
- schema version (/core/manifest.json)
- artifact file list + hashes

Docs must reference:
- the artifact file paths
- the run_manifest entry for the run they describe

Numbers in docs must be traceable to artifacts.
If not traceable, the doc is invalid.

(Optional test):
Reject docs containing numeric claims not linked to artifacts.

------------------------------------------------------------
12. COLD START BEHAVIOR
------------------------------------------------------------

On entering Helix:

1. Load:
   - Current ontology definitions
   - Obstruction basis
   - Latest entropy report
   - Active axes
   - /docs/structural_phase_log.md (if present)
   - /artifacts/run_manifest.json (latest)

2. Refuse kernel synthesis until loaded.
3. Begin at appropriate layer.

------------------------------------------------------------
13. DRIFT GUARD
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

Helix is a lab.
Not a myth engine.
------------------------------------------------------------
14. CROSSLINKING PROTOCOL (MANDATORY)
------------------------------------------------------------

All claims must be traceable to:
- A specific artifact file
- A specific run_manifest entry
- A specific dataset hash

No numeric statement is valid unless:
1) It exists in /artifacts
2) It references run_manifest.json
3) It can be regenerated via `helix.py run`

If dataset_hash changes:
Docs referencing prior runs are historical only.

Helix claims are run-bound, not timeless.

------------------------------------------------------------
16. MINIMAL STRUCTURAL CONSTRAINTS DISCOVERY
------------------------------------------------------------

Objective: Identify the minimal necessary structural conditions required for collapse geometry to exist.

PHASE 1 — NECESSITY ABSTRACTION
Construct ablation packs (A1–A5) removing: Ontology, Multi-Basin, Nonlinearity, Feedback, Memory.

PHASE 2 — COLLAPSE EXISTENCE
Measure IG(feature -> CollapseGeometryPresent).

PHASE 3 — RANK REDUCTION
Run SVD on Domain × Constraint matrix to find minimal rank (Rank <= 3 = Success).

------------------------------------------------------------
17. CONSOLIDATION & FORMALIZATION
------------------------------------------------------------

PILLAR 1 — MEASUREMENT FORMALIZATION
- projection_registry.json: Allowed dimensionless forms.
- layers/l5_expansion/measurement_validator.py: Scans for unit leakage.
- layers/l5_expansion/numeric_expansion.py: Qualitative to numeric densification.

PILLAR 2 — COUNTEREXAMPLE ENGINE
- Structural mutation (remove feedback, linearize, etc.).
- Detect boundary geometry flips.

PILLAR 3 — OPERATOR ALGEBRA
- Formal composition (Sequential, Parallel, Nested, Feedback).
- Minimal generating operator sets per collapse class.

PILLAR 4 — CE-OS HARDENING (RING 0 PROTECTION)
- Admissibility Firewall: Semantic pre-scrubbing.
- Determinism Probe: Hash-reproducibility verification.
- Throughput Guard: Execution budget enforcement.
- Stable Channel: Promoting artifacts from /latest_attempt only upon success.

PILLAR 5 — CONVERGENCE ATTACK & INTERVENTION
- Resolution Escalation: Detecting projection artifacts via higher-order probes (temp_rev, noise_exp).
- Structural Vaccines: Validated operator transfers (e.g., TCP_AIMD -> Physics).

PILLAR 4 — LONGITUDINAL SPINE
- artifacts/kernel_registry.json: Archive of validated eigenspaces.
- layers/l2_elements/eigenspace_tracker.py: Monitor drift and isotopic rotation history.
- docs/phase_log.md: Append-only ledger of survival.

------------------------------------------------------------
