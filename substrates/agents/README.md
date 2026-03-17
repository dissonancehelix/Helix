# HELIX AGENTS SUBSTRATE SPECIFICATION

**Version:** 2.0
**Status:** Authoritative formal substrate specification
**Authority:** This document is the implementation contract for the Helix Agents Substrate.
**Purpose:** Enable reconstruction of the Agents Substrate without architectural invention. If code conflicts with this document, this document takes precedence until intentionally revised.

---

## 0. WHY THIS DOCUMENT EXISTS

This document is the formal design specification for the Helix Agents Substrate.

Its purpose:
- An LLM can rebuild the substrate without inventing architecture
- Domain logic is not misplaced into Core or Labs
- Future implementations follow the same structural DNA

---

## 1. SUBSTRATE IDENTITY

### 1.1 What the Agents Substrate is

The Agents Substrate models multi-agent decision systems in simulated environments.

Where the Games Substrate studies real agent behavior extracted from existing game replays, the Agents Substrate creates controlled synthetic environments to study how decision invariants emerge under manipulable conditions.

The Agents Substrate is the experimental laboratory for Helix invariants. It allows:
- precise control of coupling strength, topology, information structure
- systematic parameter sweeps across agent configuration space
- isolation of specific decision phenomena under controlled conditions
- generation of synthetic datasets for invariant validation

### 1.2 What the Agents Substrate is not

The Agents Substrate is not:
- a general-purpose agent simulation framework
- a multi-agent reinforcement learning training platform
- a game engine
- a production agent deployment system

It exists to generate controlled experimental data that confirms or disconfirms Helix invariants.

### 1.3 Core identity statement

The Agents Substrate generates controlled synthetic environments to isolate and measure specific decision phenomena.

It is the experimental partner to the Mathematics Substrate's theory: mathematics predicts, agents test under controlled conditions, other substrates validate at scale.

---

## 2. CLOSED SYSTEM LAW

The Agents Substrate operates under Helix's Closed System Law.

**Substrates never write to Atlas directly.**

The substrate produces artifacts. The Atlas Compiler converts artifacts into Atlas entities.

**Pipeline:**
```
SWEEP parameter:coupling_strength range:0..1 steps:20 experiment:oscillator_locking
    → run agent simulations at each parameter value
    → write simulation artifacts to artifacts/agents/

RUN operator:COMPILE_ATLAS
    → compile artifacts to atlas/signals/
```

---

## 3. HELIX LAYER POSITION

```
HIL
→ Normalization
→ Semantics
→ Operator Runtime (SCAN, ANALYZE, SWEEP, COMPILE_ATLAS)
→ Atlas Compiler
→ Atlas

Operator Runtime
       │
       ▼
Agents Substrate Simulation
       │
       ▼
 artifacts/agents/
       │
       ▼
  Atlas Compiler
       │
       ▼
  atlas/signals/
```

### 3.1 Substrate responsibility

The Agents Substrate is responsible for:
- defining environment topologies and agent configurations
- running agent simulations under specified parameters
- recording full agent behavior time series
- extracting decision metrics (entropy, compression, synchronization)
- parameter sweep coordination
- artifact generation

### 3.2 Agents Lab responsibility

Agents Lab (`labs/agents_lab/`) is responsible for higher-level experimentation:
- exploratory topology experiments
- comparative studies across environment types
- novel invariant proposals from simulation results
- research notebooks and visualization
- anything exploratory or replaceable

---

## 4. DOMAIN TYPES

The Agents Substrate simulates:

| Domain | Examples |
|--------|---------|
| Coupled oscillator systems | Kuramoto model, coupled pendulums |
| Multi-agent coordination | Collective action, consensus formation |
| Competitive decision systems | Two-player zero-sum, N-player games |
| Network diffusion | Information spreading, epidemic models |
| Emergent behavior systems | Flocking, swarming, synchronization |
| Economic agent systems | Auction dynamics, market formation |

---

## 5. ACTIVE EXPERIMENTS

### 5.1 oscillator_locking

**Purpose:** Test the oscillator locking invariant under controlled coupling parameters.

**Design:**
- N agents with initial random phases
- Coupling strength K swept from 0 to 1
- Measure phase coherence at steady state

**Parameter space:**
```
SWEEP parameter:coupling_strength range:0..1 steps:20 experiment:oscillator_locking
SWEEP parameter:agent_count range:5..50 steps:10 experiment:oscillator_locking
SWEEP parameter:topology range:... experiment:oscillator_locking
```

**Expected result:** Phase coherence transitions from near-0 to near-1 at critical coupling K_c.

### 5.2 decision_compression

**Purpose:** Test decision compression under controlled information pressure.

**Design:**
- Agents face sequential binary decisions
- Information availability manipulated to increase irreversibility
- Measure decision entropy at each step

**Parameter space:**
```
SWEEP parameter:irreversibility_pressure range:0..1 steps:20 experiment:decision_compression
SWEEP parameter:horizon range:1..10 steps:9 experiment:decision_compression
```

**Expected result:** Decision entropy compresses monotonically as irreversibility pressure increases.

---

## 6. ANALYSIS PIPELINE

The Agents Substrate uses a deterministic, stage-based pipeline.

### 6.1 Stage sequence

```
1. ENVIRONMENT SETUP
   define topology (graph structure of agent connections)
   initialize agent states (random or prescribed)
   set coupling parameters

2. SIMULATION EXECUTION
   run time steps until convergence or max_steps
   record full agent state at each step
   record all decision events

3. DECISION ANALYSIS
   extract decision points from time series
   compute decision entropy at each point
   compute decision compression slope

4. SYNCHRONIZATION ANALYSIS
   compute phase coherence over time
   detect synchronization onset
   characterize locking behavior

5. PATTERN EXTRACTION
   identify critical parameter values (K_c, threshold)
   characterize transition sharpness
   extract invariant signatures

6. ARTIFACT GENERATION
   write to artifacts/agents/<run_id>/
```

### 6.2 Artifact outputs

All artifacts written to `artifacts/agents/<run_id>/`:

| Artifact | Description |
|----------|-------------|
| `simulation_config.json` | Full simulation parameters |
| `agent_states.json` | Agent state time series (compressed) |
| `decision_events.json` | All decision events with timestamps |
| `entropy_series.json` | Decision entropy over time |
| `coherence_series.json` | Phase coherence over time |
| `invariant_signatures.json` | Extracted invariant measurements |
| `probe_result.json` | Canonical probe output (pass/fail + confidence) |

---

## 7. ENTITY TYPES

### 7.1 Agents entities

| Entity Type | ID Format | Description |
|-------------|-----------|-------------|
| `AgentEnvironment` | `agent.env:<slug>` | Environment definition |
| `Simulation` | `agent.sim:<id>` | Simulation run instance |
| `AgentNetwork` | `agent.network:<slug>` | Network topology |
| `PhaseCoherence` | `agent.coherence:<id>` | Coherence measurement |
| `DecisionCompression` | `agent.compression:<id>` | Compression measurement |

### 7.2 Relationships

```
Simulation → INSTANCE_OF → AgentEnvironment
Simulation → USES_TOPOLOGY → AgentNetwork
Simulation → PRODUCES_MEASUREMENT → PhaseCoherence
Simulation → PRODUCES_MEASUREMENT → DecisionCompression
PhaseCoherence → SUPPORTS → Invariant
DecisionCompression → SUPPORTS → Invariant
```

---

## 8. REPOSITORY STRUCTURE

```
substrates/agents/
├── README.md                     ← this document
├── environments/
│   ├── kuramoto/                 ← Kuramoto oscillator environment
│   ├── binary_decision/          ← Binary decision environment
│   ├── network_diffusion/        ← Network diffusion environment
│   └── topology_configs/         ← Graph topology definitions
├── simulations/
│   ├── oscillator_locking/       ← Oscillator locking simulation logic
│   ├── decision_compression/     ← Decision compression simulation logic
│   └── parameter_sweep/          ← Parameter sweep coordination
├── decision_analysis/
│   ├── entropy_extractor.py      ← Decision entropy computation
│   ├── compression_detector.py   ← Compression event detection
│   └── coherence_analyzer.py     ← Phase coherence analysis
└── atlas_export/
    └── artifact_formatter.py     ← Format simulation results for compiler
```

---

## 9. SIMULATION CONFIGURATION SCHEMA

Every simulation requires a complete configuration:

```json
{
  "experiment": "oscillator_locking",
  "environment": "kuramoto",
  "topology": "fully_connected",
  "agent_count": 20,
  "coupling_strength": 0.5,
  "natural_frequencies": "random_normal",
  "initial_phases": "uniform_random",
  "max_steps": 1000,
  "convergence_threshold": 0.01,
  "seed": 42,
  "record_full_states": true
}
```

All parameters must be explicit. No defaults should be silently applied after the initial configuration is set.

---

## 10. PARAMETER SWEEP CONTRACT

The Agents Substrate is the primary consumer of the `SWEEP` HIL command.

```
SWEEP parameter:coupling_strength range:0..1 steps:20 experiment:oscillator_locking seed:42
```

**Sweep behavior:**
1. HIL validates the parameter against the experiment's accepted sweep parameters
2. Grid of parameter values constructed from `range` and `steps`
3. Each grid point runs as a separate simulation with unique `run_id`
4. All artifacts written to `artifacts/agents/<experiment>/<run_id>/`
5. Sweep summary written to `artifacts/agents/<experiment>/sweep_summary.json`

---

## 11. HIL CONTRACT

All orchestration occurs through HIL.

Examples:
```
SWEEP parameter:coupling_strength range:0..1 steps:20 experiment:oscillator_locking seed:42
SWEEP parameter:irreversibility_pressure range:0..1 steps:10 experiment:decision_compression
RUN operator:ANALYZE entity:agent.sim:oscillator_locking_k050_run001
PROBE invariant:oscillator_locking lab:agents
PROBE invariant:decision_compression lab:agents
ATLAS list domain:signals
GRAPH support invariant:oscillator_locking
```

---

## 12. RELATIONSHIP TO HELIX INVARIANTS

The Agents Substrate provides the cleanest experimental conditions for isolating invariant mechanisms.

| Invariant | Agents test |
|-----------|------------|
| `oscillator_locking` | Kuramoto model with controlled coupling sweep; detect K_c |
| `decision_compression` | Binary decision with controlled irreversibility; detect entropy slope |

The Agents Substrate does not discover new invariants. It validates existing invariant candidates under controlled conditions, and provides the experimental backbone for parameter characterization (K_c, thresholds, sensitivity).

---

## 13. ANTI-DRIFT RULES

- Do not write simulation data directly to `atlas/` — use the artifact pipeline
- Do not build general-purpose agent simulation infrastructure — scope is Helix invariant testing only
- Do not conflate simulation generation with real-world observation (Games/Music/Language substrates)
- SWEEP parameters must be registered as accepted_params for the experiment — no arbitrary params

---

## 14. RECONSTRUCTION SPECIFICATION

A future system can reconstruct the Agents Substrate from this document.

Required components:
- [ ] 6-stage simulation pipeline (setup → execute → decision analysis → sync analysis → patterns → artifacts)
- [ ] Artifact schemas matching §6.2
- [ ] Entity types matching §7.1 with correct ID format
- [ ] Simulation configuration schema matching §9
- [ ] SWEEP command integration (parameter grid, per-run artifacts, sweep summary)
- [ ] Environments for Kuramoto, binary decision, network diffusion
- [ ] All artifacts written to `artifacts/agents/`, never to `atlas/`
- [ ] HIL-only orchestration interface

---

*This document is the authoritative specification for the Helix Agents Substrate.*
*Version 2.0 — 2026-03-17*


---

## Architecture Guardrail

**Helix Architecture Law**
`HIL → Operator → Adapter → Toolkit → Artifact → Atlas Compiler`

* Operators orchestrate
* Adapters translate
* Toolkits execute
* Artifacts store results
* Atlas compiler creates entities

**Prohibited Patterns**
- `master_pipeline.py`
- Direct toolkit calls from operators
- Toolkits writing artifacts
- Toolkits writing Atlas entities
- Operators writing Atlas entities
- Monolithic pipelines

*All new modules must follow the template registry located in `runtime/templates/`.*
