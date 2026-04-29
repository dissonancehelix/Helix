# HELIX GAMES SUBSTRATE SPECIFICATION

**Version:** 2.1
**Status:** Authoritative target specification — implementation status tracked in README.md §11
**Relationship:** Extends `domains/games/model/README.md`

---

## 1. DOMAIN SCOPE

The Games Substrate operates on structured adversarial environments where agents make sequential decisions under uncertainty. Its unit of analysis is the game session: a bounded sequence of agent decisions and state transitions with measurable outcome.

It does not simulate games or train agents. It extracts decision structure from existing replay logs and simulation outputs.

---

## 2. DOMAIN-LOCAL STRUCTURAL SIGNALS

These signals are extracted by the games pipeline and are domain-local. They are NOT the same as HelixEmbedding axes. They feed into the feature extraction and pattern detection stages.

### 2.1 Decision Signals
- **`decision_entropy_slope`**: Rate of entropy reduction in the approach to a decision point (primary DCP signal)
- **`policy_entropy`**: Shannon entropy of action distribution at a given decision point
- **`action_distribution`**: Per-agent action frequency per game phase
- **`commitment_density`**: Degree to which influence is concentrated in a small set of locked states

### 2.2 Strategy Signals
- **`strategy_cluster_id`**: k-means cluster assignment over per-session policy vectors
- **`equilibrium_flag`**: Boolean — detected stable strategy equilibrium
- **`policy_collapse_flag`**: Boolean — detected convergence to degenerate strategy

### 2.3 Coordination Signals (multi-agent)
- **`phase_coherence`**: Degree of synchronization at steady state (primary oscillator locking signal)
- **`coupling_strength_proxy`**: Derived measure of agent-to-agent influence (not directly observed)

---

## 3. SHARED EMBEDDING PROJECTION

Games-domain signals project into the shared `HelixEmbedding` format via the artifact preparation layer (Stage 6 → Atlas Compiler).

**Projection mapping** (signal → embedding axis):

| HelixEmbedding Axis | Primary Games Signal | Normalization Method |
|---------------------|----------------------|----------------------|
| `structure` | `phase_coherence` | Direct: sync index [0, 1] |
| `complexity` | `commitment_density` | Inverse of flattening: high constraint = high complexity |
| `repetition` | `strategy_cluster_recurrence` | Frequency of returning to same cluster |
| `density` | `action_distribution_density` | Actions per decision window |
| `variation` | `policy_entropy` | Normalized Shannon entropy |
| `expression` | `equilibrium_smoothness` | Transition gradient to stable state |

**Non-equivalence rule**: HelixEmbedding axis names are system-wide. Games signal names are domain-local. The mapping above is the intended projection; implementation status is not confirmed.

**Projection schema versioning**: A `projection_schema` field should be stamped on all games embedding artifacts: `games_v1`. Not yet implemented.

---

## 4. PIPELINE STAGES

| Stage | Responsibility | Input | Output | Status |
|-------|----------------|-------|--------|--------|
| 1 | Ingestion | Replay logs | Canonical game event format | ❌ Not implemented |
| 2 | State reconstruction | Game events | Game state graph, agent transitions | ❌ Not implemented |
| 3 | Strategy analysis | State graph | Policy inference, decision tree | ❌ Not implemented |
| 4 | Feature extraction | Policy data | GamesStructuralSignals | ❌ Not implemented |
| 5 | Pattern detection | Signals | Strategy clusters, equilibria, phase transitions | ❌ Not implemented |
| 6 | Artifact generation | All above | `artifacts/games/<session_id>/` | ❌ Not implemented |

---

## 5. ENTITY SCHEMAS

### Game Entity (`atlas/games/game/<slug>.json`)
```json
{ "entity_id": "game:<slug>", "entity_type": "game", "title": "Chess", "domain": "games" }
```

### GameSession (`artifacts/games/<id>/session.json`)
```json
{
  "entity_id": "game.session:<id>",
  "entity_type": "game_session",
  "game": "chess",
  "agents": ["agent_a", "agent_b"],
  "decision_points": [],
  "action_sequences": []
}
```

### GamesStructuralSignals (`artifacts/games/<id>/structural_signals.json`)
```json
{
  "session_id": "...",
  "decision_entropy_slope": -0.043,
  "policy_entropy": 0.61,
  "phase_coherence": 0.87,
  "strategy_cluster_id": 2,
  "equilibrium_flag": true,
  "policy_collapse_flag": false
}
```

### HelixEmbedding (`artifacts/games/<id>/embedding.json`)
```json
{
  "complexity": 0.74,
  "structure": 0.87,
  "repetition": 0.55,
  "density": 0.61,
  "expression": 0.49,
  "variation": 0.39,
  "confidence": 0.68,
  "domain": "games",
  "source_vector": "games_structural_signals",
  "projection_schema": "games_v1"
}
```

---

## 6. VALIDATION RULES

Two active probes define the canonical validation conditions:

### decision_compression
> When an agent faces a critical irreversible decision, the available decision space compresses measurably before and after the decision point.

- Signal: `decision_entropy_slope` — rate of entropy reduction approaching decision point
- Status: Verified — 86% pass rate, 3 domains

### oscillator_locking
> Coupled agents converge to synchronized oscillation patterns under sufficient coupling strength.

- Signal: `phase_coherence` — degree of synchronization at steady state
- Status: Verified — 100% pass rate, 3 domains

**Formal validation harness** under `domains/games/model/validation/` does not yet exist. Verification was through labs probes.

---

## 7. METRIC SPACE / SIMILARITY / DISTANCE

The HelixEmbedding metric space uses Euclidean distance normalized by √6:

```
distance(a, b) = euclidean(a, b) / sqrt(6)          ∈ [0, 1]
similarity(a, b) = 1 - distance(a, b)               ∈ [0, 1]
```

**Triangle inequality** applies to **distance**, not similarity:
```
d(a, c) ≤ d(a, b) + d(b, c)
```

A violation is a `STRUCTURAL_FAILURE`.

---

## 8. ENTRY / HSL INTEGRATION STATE

**Target HIL orchestration**:
```
RUN operator:SCAN substrate:games
RUN operator:ANALYZE entity:game.session:<id>
PROBE invariant:decision_compression lab:games
PROBE invariant:oscillator_locking lab:games
ATLAS list domain:games
```

**Current**: Command syntax is defined. Runtime implementation not confirmed. Pipeline is a stub.

---

## 9. THRESHOLDS AND CALIBRATION

| Threshold | Value | Status |
|-----------|-------|--------|
| Minimum embedding confidence | 0.30 | Provisional — global default, not games-calibrated |
| decision_compression pass rate | ≥ 80% | Active verified probe (86% current) |
| oscillator_locking pass rate | ≥ 80% | Active verified probe (100% current) |

Calibration procedure for confidence floor: establish null game corpus (randomized action sequences) → compute embedding distribution → set at `mean + 2 * std`. Not yet performed.

---

## 10. PROMOTION CONDITIONS

Invariant candidates follow the global 6-criterion gate (see `docs/GOVERNANCE.md`):
1. Reproducibility (≥ 2 independent runs)
2. Multi-domain observation (≥ 2 domains) — both active probes satisfy this
3. Minimum confidence ≥ threshold
4. Pass rate ≥ 80%
5. Signal above minimum threshold
6. Latest probe version used

`decision_compression` and `oscillator_locking` are the only games-domain candidates currently at verification status.

---

## 11. KNOWN ASSUMPTIONS / OPEN CONSTRAINTS

- Games domain assumes replay logs are available and parseable; live game state capture is not in scope
- Probe datasets reference `domains/games/data/pipeline/` — this path must remain canonical (old docs referenced `labs/games/`, which is stale)
- Projection mapping in §3 is the intended target; actual implementation not confirmed
- `projection_schema` versioning not yet implemented
- All Stage 1–6 runtime implementations are not confirmed; pipeline is a stub

