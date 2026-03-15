# Helix Development Roadmap

---

## Phase 6 — Architecture Stabilization and Kernel Refactor *(current)*

**Goal:** Lock the repository structure. Establish the five-layer architecture.

- Restructure repo into `kernel / engines / discovery / atlas / modules`
- Define and scaffold HIL (Helix Interface Language)
- Migrate all existing experiments and artifacts into the atlas
- Write architecture, philosophy, and HIL spec documents
- Establish the `HELIX.md` and `OPERATOR.md` root contracts

**Exit criterion:** The repository structure does not change after this phase.

---

## Phase 7 — HIL Implementation and Dispatcher

**Goal:** Make the kernel functional. All commands enter through HIL.

- Implement full HIL parser and normalizer
- Build the kernel dispatcher with engine routing
- Add command validation with error reporting
- Write HIL tests covering grammar edge cases
- Connect dispatcher to Python and Godot engine adapters

---

## Phase 8 — Python Experimental Engine Expansion

**Goal:** Make the Python engine capable of running real experiments.

- Implement all seven probe types: network, dynamical, oscillator, cellular, evolutionary, information, dataset
- Run baseline experiments across each probe type
- Store results in `atlas/experiments/`
- Build parameter sweep tooling in `discovery/sweeps/`
- First cross-probe invariant detection attempts

---

## Phase 9 — Godot Embodiment Engine Integration

**Goal:** Connect Helix to spatial simulation via Godot.

- Implement `GodotAdapter` scene generation and telemetry capture
- Build first spatial probe: multi-agent emergence
- Cross-substrate comparison: Python dynamical vs Godot spatial
- Begin regime map construction for spatial experiments

---

## Phase 10 — Atlas Knowledge System and Indexing

**Goal:** Make the atlas queryable and exportable.

- Build atlas indexer across experiments, observations, regimes, invariants
- Implement cross-experiment linking
- Add wiki-style export capability
- Create invariant candidate scoring and ranking
- Document all discoveries with provenance chains

---

## Phase 11 — Adversarial Validation and Falsification Probes

**Goal:** Test every invariant candidate against adversarial conditions.

- Design falsification probe suite for each invariant class
- Run adversarial rotations, corruptions, and edge cases
- Reclassify invariants based on falsification results
- Publish falsification reports to `atlas/invariants/`

---

## Phase 12 — Module Expansion and Applied Systems

**Goal:** Build user-facing systems on top of validated discoveries.

- Expand Language Lab with structure-discovery experiments
- Expand Creativity Lab with generative pattern systems
- Build Game Systems Lab on spatial/emergent foundations
- Open module interface for external operator modules
- Begin cross-module invariant transfer experiments
