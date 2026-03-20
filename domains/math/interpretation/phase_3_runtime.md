# Phase 3 Migration: Experimental Runtime + First Probe

**Date:** 2026-03-14
**Branch:** helix_constitutional_refactor
**Tag:** phase-3

---

## Overview

Phase 3 introduces the full probe execution pipeline, Atlas generation, and the first
experimental invariant probe (`decision_compression`). All execution is sandboxed via
subprocess isolation established in Phase 2.

---

## New Engine Modules

### `03_engines/runtime/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `run_manifest.py` | Run ID generation, file/data hashing, env snapshot, artifact bundle writer |

Key functions in `run_manifest.py`:
- `generate_run_id(probe_name)` → `{probe_name}_{YYYYMMDD_HHMMSS}_{hex6}`
- `compute_file_hash(path)` → SHA-256 of file bytes
- `compute_data_hash(data)` → SHA-256 of JSON-sorted dict
- `build_run_manifest(...)` → structured dict written to `run_manifest.json`
- `write_artifact_bundle(run_dir, ...)` → writes `run_manifest.json`, `dataset_hash.txt`, `env_snapshot.json`

### `03_engines/orchestrator/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `probe_registry.py` | Discovers `*.py` probes under `04_labs/probes/`, strips `_probe` suffix |
| `probe_runner.py` | Full probe execution: dataset loading, sandbox, artifact writing, Atlas rebuild |

Dataset loading convention in `probe_runner.py`:
1. `04_labs/{lab}/{probe_name}_dataset.json` (probe-specific)
2. First `.json` alphabetically in `04_labs/{lab}/` (fallback)

### `03_engines/codex/atlas/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `confidence_scoring.py` | Aggregates run results → confidence class (Exploratory/Candidate/Verified/Structural) |
| `atlas_builder.py` | Scans `execution/artifacts/`, builds per-probe Atlas entries, writes `codex/codex/atlas/*.json` + `index.json` |

Confidence thresholds:
| Domains | Pass Rate | Class |
|---------|-----------|-------|
| ≥ 4 | ≥ 90% | Structural |
| ≥ 3 | ≥ 75% | Verified |
| ≥ 2 | ≥ 50% | Candidate |
| any | any | Exploratory |

### `03_engines/governance_bridge/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `promotion_engine.py` | Loads Atlas entry, runs 6-criterion gate from `02_governance`, writes promotion_status |

---

## First Probe: `decision_compression`

**File:** `04_labs/probes/decision_compression_probe.py`
**VERSION:** `1.0.0`

**Invariant:** Decision Compression — influence concentrates on a small subset of agents in
multi-agent decision systems, compressing the effective decision space.

**Measurement:**
```
k_eff = 1 / Σ(w_i²)   where w_i are normalised influence weights per round
signal_strength = 1 - k_eff / N
detected if signal_strength > 0.3
```

**Dataset format:**
```json
{
  "domain": "<str>",
  "agents": [{"id": "...", "role": "...", "influence_weight": 0.0}],
  "decision_rounds": [{"round": 1, "weights": [...], "outcome": "..."}]
}
```

**Output fields:** `probe_name`, `domain`, `passed`, `signal`, `signal_strength`,
`confidence`, `decision_dimension`, `n_agents`, `n_rounds`, `k_eff_per_round`,
`compression_ratio`, `version`

---

## Datasets Added

| File | Domain | Description |
|------|--------|-------------|
| `04_labs/games/simple_consensus.json` | games | 5-player board game, player_1 weight=0.55 |
| `04_labs/language/grammar_resolution.json` | language | 5-rule grammar, rule_subject_verb weight=0.48 |
| `04_labs/music/rhythm_phase_shift.json` | music | 4-voice rhythm, kick_drum weight=0.60 |

---

## helix.py CLI Additions

Commands added (all pre-wired in Phase 2's helix.py rewrite):

```
helix probe-run <probe> [--lab <lab>]   Run a single probe in a lab
helix atlas-build                        Rebuild Atlas from all artifact runs
helix promote-invariant <name>           Run 6-criterion Atlas promotion gate
```

---

## Test Results

```
python helix.py probe-run decision_compression --lab games    → PASS
python helix.py probe-run decision_compression --lab language → PASS
python helix.py probe-run decision_compression --lab music    → PASS
python helix.py atlas-build
  decision_compression: confidence=Verified, domains=['games','language','music'], runs=3
python helix.py verify → Architectural coherence verified.
```

---

## Atlas State After Phase 3

| Invariant | Confidence | Domains | Pass Rate |
|-----------|-----------|---------|-----------|
| decision_compression | Verified | games, language, music | 100% |
