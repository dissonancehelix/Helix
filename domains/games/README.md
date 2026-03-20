# HELIX GAMES SUBSTRATE SPECIFICATION

**Version:** 2.0
**Status:** Authoritative formal substrate specification
**Authority:** This document is the implementation contract for the Helix Games Substrate.
**Purpose:** Enable reconstruction of the Games Substrate without architectural invention. If code conflicts with this document, this document takes precedence until intentionally revised.

---

## 0. WHY THIS DOCUMENT EXISTS

This document is the formal design specification for the Helix Games Substrate.

Its purpose:
- An LLM can rebuild the substrate without inventing architecture
- Domain logic is not misplaced into Core or Labs
- Future implementations follow the same structural DNA

---

## 1. SUBSTRATE IDENTITY

### 1.1 What the Games Substrate is

The Games Substrate studies complex agent behavior inside structured environments.

Games provide controlled systems where agents must:
- interpret information under uncertainty
- make sequential decisions
- adapt strategies in response to opponent or environment
- coordinate or compete with other agents

These environments produce rich, measurable decision dynamics. They are ideal research subjects for Helix because they are:
- fully observable (replay logs capture all state)
- deterministic given the same input
- adversarially structured (decision pressure is non-trivial)
- cross-domain applicable (decision invariants found in games appear in language and music)

### 1.2 What the Games Substrate is not

The Games Substrate is not:
- a game engine or runtime
- a game AI training framework
- a reinforcement learning research platform
- a game development toolkit

It exists to extract decision structure from game data, not to produce playable agents.

### 1.3 Core identity statement

The Games Substrate extracts the latent decision architecture underlying game play.

It studies:
- how agents form and execute strategies
- how decision spaces compress under pressure
- where irreversible decision points occur
- what equilibria and phase transitions exist in strategy space

---

## 2. CLOSED SYSTEM LAW

The Games Substrate operates under Helix's Closed System Law.

**Substrates never write to Atlas directly.**

The substrate produces artifacts. The Atlas Compiler converts artifacts into Atlas entities.

**Pipeline:**
```
RUN operator:SCAN substrate:games
    → discover game datasets
    → write game entity artifacts to artifacts/games/

RUN operator:ANALYZE entity:game_session:<id>
    → analyze decision structure
    → write analysis artifacts to artifacts/games/

RUN operator:COMPILE_ATLAS
    → compile artifacts to codex/atlas/games/
```

---

## 3. HELIX LAYER POSITION

```
HIL
→ Normalization
→ Semantics
→ Operator Runtime (SCAN, ANALYZE, COMPILE_ATLAS)
→ Atlas Compiler
→ Atlas

Operator Runtime
       │
       ▼
Games Substrate Pipeline
       │
       ▼
 artifacts/games/
       │
       ▼
  Atlas Compiler
       │
       ▼
  codex/atlas/games/
```

### 3.1 Substrate responsibility

The Games Substrate is responsible for:
- replay log ingestion and parsing
- game state reconstruction from replays
- strategy and policy analysis
- decision compression metric extraction
- feature extraction (action distributions, policy entropy, decision trees)
- pattern detection (equilibria, strategy clusters, policy collapse)
- artifact generation

### 3.2 Games Lab responsibility

Games Lab (`labs/games_lab/`) is responsible for higher-level experimentation:
- comparative strategy experiments across games
- policy embedding and clustering studies
- cross-game invariant validation
- research notebooks and visualization
- anything exploratory or replaceable without affecting canonical artifacts

---

## 4. DOMAIN TYPES

The Games Substrate analyzes:

| Domain | Examples |
|--------|---------|
| Board games | Chess, Go, Shogi, checkers |
| Competitive strategy games | RTS, MOBA, card games |
| Cooperative games | Pandemic, co-op RTS |
| Economic simulations | Market simulations, auction environments |
| Reinforcement learning environments | OpenAI Gym environments, Atari, custom |
| Human gameplay logs | Professional match replays, tournament data |

---

## 5. ACTIVE PROBES

### 5.1 decision_compression

The `decision_compression` probe tests the Decision Compression Principle (DCP):

> When an agent faces a critical irreversible decision, the available decision space compresses measurably before and after the decision point.

**Status:** Verified (86% pass rate, 3 domains)
**Dataset:** `decision_compression_dataset.json`
**Signal:** `decision_entropy_slope` — rate of entropy reduction approaching decision point

### 5.2 oscillator_locking

The `oscillator_locking` probe tests synchronization behavior in multi-agent systems:

> Coupled agents converge to synchronized oscillation patterns under sufficient coupling strength, regardless of initial phase difference.

**Status:** Verified (100% pass rate, 3 domains)
**Dataset:** `oscillator_locking_dataset.json`
**Signal:** `phase_coherence` — degree of synchronization at steady state

---

## 6. ANALYSIS PIPELINE

The Games Substrate uses a deterministic, stage-based pipeline.

### 6.1 Stage sequence

```
1. INGESTION
   game replays, agent logs, simulation outputs
   → parse to canonical game event format

2. STATE RECONSTRUCTION
   game event sequences → game state graphs
   → agent state transition sequences

3. STRATEGY ANALYSIS
   policy inference from state transitions
   → decision tree reconstruction

4. FEATURE EXTRACTION
   action distributions (per agent, per game phase)
   policy entropy (at each decision point)
   decision compression metrics
   equilibrium detection
   phase transition identification

5. PATTERN DETECTION
   strategy clusters (k-means over policy vectors)
   equilibrium structures
   policy collapse events
   coordination emergence

6. ARTIFACT GENERATION
   write to artifacts/games/<session_id>/
```

### 6.2 Artifact outputs

All artifacts written to `artifacts/games/<session_id>/`:

| Artifact | Description |
|----------|-------------|
| `game_state_graph.json` | Reconstructed state transitions |
| `policy_vectors.json` | Per-agent policy feature vectors |
| `decision_entropy.json` | Entropy time series at decision points |
| `strategy_clusters.json` | Strategy cluster assignments |
| `compression_metrics.json` | DCP compression measurements |
| `phase_transitions.json` | Detected phase transitions in strategy space |

---

## 7. ENTITY TYPES

### 7.1 Games entities

| Entity Type | ID Format | Description |
|-------------|-----------|-------------|
| `Game` | `game:<slug>` | Game definition (rules, structure) |
| `GameSession` | `game.session:<id>` | Single game instance or match |
| `Agent` | `game.agent:<slug>` | Decision-making agent |
| `Strategy` | `game.strategy:<slug>` | Identified strategy pattern |
| `Equilibrium` | `game.equilibrium:<slug>` | Stable strategy equilibrium |
| `DecisionPoint` | `game.decision:<id>` | Critical irreversible decision moment |

### 7.2 Relationships

```
Agent → PLAYS_IN → GameSession
GameSession → INSTANCE_OF → Game
Agent → USES_STRATEGY → Strategy
GameSession → EXHIBITS_EQUILIBRIUM → Equilibrium
GameSession → CONTAINS_DECISION_POINT → DecisionPoint
DecisionPoint → SUPPORTS → Invariant
```

---

## 8. DATASET CONTRACT

### 8.1 Probe dataset convention

Probe runner loads `{probe_name}_dataset.json` first, then falls back to first `.json` alphabetically.

Each dataset JSON must contain:
```json
{
  "probe_name": "decision_compression",
  "domain": "games",
  "items": [
    {
      "session_id": "...",
      "game": "...",
      "decision_points": [...],
      "action_sequences": [...]
    }
  ]
}
```

### 8.2 Dataset locations

```
labs/games/
├── decision_compression_dataset.json
└── oscillator_locking_dataset.json
```

---

## 9. REPOSITORY STRUCTURE

```
domains/games/
├── README.md                     ← this document
├── datasets/
│   ├── game_logs/                ← raw replay files
│   ├── replays/                  ← parsed replay cache
│   └── simulation_outputs/       ← simulation result dumps
├── pipelines/
│   ├── ingestion/                ← stage 1: parse replays to events
│   ├── replay_parsing/           ← stage 2: reconstruct game states
│   ├── state_reconstruction/     ← state graph construction
│   ├── strategy_analysis/        ← stage 3: policy inference
│   ├── policy_detection/         ← strategy identification
│   ├── pattern_detection/        ← stage 5: clustering, equilibria
│   └── atlas_integration/        ← artifact prep for compiler
├── models/
│   ├── strategy_models/          ← strategy classifiers
│   └── agent_models/             ← agent behavior models
└── experiments/
    ├── coordination_games/
    ├── competitive_games/
    ├── cooperative_games/
    └── policy_collapse/
```

---

## 10. HIL CONTRACT

All orchestration occurs through HIL.

Examples:
```
RUN operator:SCAN substrate:games
RUN operator:ANALYZE entity:game.session:chess_match_001
PROBE invariant:decision_compression lab:games
PROBE invariant:oscillator_locking lab:games
ATLAS list domain:games
ENTITY get game.session:chess_match_001
GRAPH support invariant:decision_compression
```

---

## 11. RELATIONSHIP TO HELIX INVARIANTS

The Games Substrate is a primary test bed for Helix invariants.

Games provide the clearest signals for:

| Invariant | Games signal |
|-----------|-------------|
| `decision_compression` | Policy entropy drops sharply approaching irreversible moves |
| `oscillator_locking` | Multi-agent coordination emergence in cooperative games |

Both invariants are cross-substrate: they appear in games, music, and language. The Games Substrate provides the cleanest experimental conditions for initial detection.

---

## 12. ANTI-DRIFT RULES

- Do not write game analysis directly to `codex/atlas/` — use the artifact pipeline
- Do not invent alternative orchestration languages — HIL only
- Do not place exploratory experiments in the substrate — use Games Lab
- Do not rename `decision_compression` or `oscillator_locking` without spec revision

---

## 13. RECONSTRUCTION SPECIFICATION

A future system can reconstruct the Games Substrate from this document.

Required components:
- [ ] 6-stage analysis pipeline (ingest → reconstruct → strategy → features → patterns → artifacts)
- [ ] Artifact schemas matching §6.2
- [ ] Entity types matching §7.1 with correct ID format
- [ ] Probe datasets for `decision_compression` and `oscillator_locking`
- [ ] All artifacts written to `artifacts/games/`, never to `codex/atlas/`
- [ ] HIL-only orchestration interface

---

*This document is the authoritative specification for the Helix Games Substrate.*
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
