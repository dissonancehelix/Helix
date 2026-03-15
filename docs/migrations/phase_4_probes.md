# Phase 4 Migration: Probe Expansion + Reproducibility + Oscillator

**Date:** 2026-03-14
**Branch:** helix_constitutional_refactor
**Tag:** phase-4

---

## Overview

Phase 4 expands the probe library with the Kuramoto oscillator locking instrument,
adds a reproducibility verification engine, enables cross-probe correlation analysis,
and rounds out all lab datasets with probe-specific routing files.

---

## New Engine Files

### `03_engines/runtime/reproduce_run.py`

Reproducibility verification engine. Re-runs any previous probe execution and compares
numerical outputs field-by-field within defined tolerances.

| Field | Tolerance |
|-------|-----------|
| signal_strength | 0.001 |
| signal | 0.001 |
| decision_dimension | 0.01 |
| order_parameter_R | 0.01 |
| compression_ratio | 0.01 |
| mean_signal | 0.01 |

Exact-match fields: `passed`, `probe_name`, `domain`

On mismatch: Atlas entry gains `non_reproducible_runs` list + `reproducibility_flag: DEGRADED`.

Output written to `07_artifacts/repro_checks/<run_id>/reproduce_result.json`.

### `03_engines/analysis/cross_probe_analysis.py`

Multi-probe correlation and coverage analysis.

Key functions:
- `load_all_probe_results(artifacts_root)` → scan `07_artifacts/probes/`
- `domain_coverage(results_by_probe)` → per-domain probe coverage + pass rate
- `probe_signal_stats(runs)` → mean/min/max signal, pass rate, domains
- `probe_signal_correlation(runs_a, runs_b)` → Pearson r of mean signal per shared domain
- `run_cross_probe_analysis(...)` → full report + writes `07_artifacts/cross_probe_report.json`

---

## New Probe: `oscillator_locking`

**File:** `04_labs/probes/oscillator_locking_probe.py`
**VERSION:** `1.0.0`

**Invariant:** Oscillator Locking — coupled oscillators spontaneously phase-lock when
coupling strength K exceeds the critical threshold, collapsing the state space.

**Model:** Kuramoto
```
dθ_i/dt = ω_i + (K/N) * Σ_j sin(θ_j - θ_i)
```

**Measurement:**
```
R = |(1/N) * Σ exp(i*θ_j)|   (order parameter, ∈ [0,1])
phase_lock_detected = R_tail_mean > 0.6
signal_strength = R_tail_mean  (normalised to [0,1])
passed = phase_lock_detected AND signal_strength > 0.3
```

**Dataset format:**
```json
{
  "domain": "<str>",
  "oscillators": [
    {"id": "...", "initial_phase": <radians>, "natural_frequency": <float>}
  ],
  "coupling_strength": <float>,
  "n_steps": <int>,
  "dt": <float>
}
```

**Output fields:** `probe_name`, `domain`, `passed`, `signal`, `signal_strength`,
`confidence`, `order_parameter_R`, `order_parameter_R_initial`, `phase_lock_detected`,
`n_agents`, `n_steps`, `coupling_strength`, `r_mean_tail`, `r_variance_tail`,
`interpretation`, `version`

---

## Datasets Added

### Probe-Specific Routing Files (decision_compression)

| File | Domain |
|------|--------|
| `04_labs/games/decision_compression_dataset.json` | games |
| `04_labs/language/decision_compression_dataset.json` | language |
| `04_labs/music/decision_compression_dataset.json` | music |

### Probe-Specific Routing Files (oscillator_locking)

| File | Domain | K | Expected R |
|------|--------|---|-----------|
| `04_labs/games/oscillator_locking_dataset.json` | games | 2.0 | > 0.95 |
| `04_labs/language/oscillator_locking_dataset.json` | language | 1.8 | > 0.90 |
| `04_labs/music/oscillator_locking_dataset.json` | music | 2.5 | > 0.95 |

### Extra Music Oscillator Datasets

| File | Purpose | Expected |
|------|---------|---------|
| `04_labs/music/rhythm_sync_small.json` | 3 voices, K=5.0, instant sync | PASS |
| `04_labs/music/rhythm_polyrhythm.json` | 6 voices, K=3.0, heterogeneous | PASS |
| `04_labs/music/tempo_competition.json` | 5 voices, K=0.1, wide spread | FAIL (intentional) |

---

## helix.py CLI Additions

```
helix probe-run-all [--lab <lab>]                    Batch all probes, single Atlas rebuild
helix reproduce <run_id>                             Re-run + compare within tolerance
helix cross-probe-analysis [--lab <l>] [--probes p1,p2]  Correlation report
```

---

## Test Results

```
python helix.py probe-run-all --lab games    → all_passed=True  (decision_compression: PASS, oscillator_locking: PASS)
python helix.py probe-run-all --lab language → all_passed=True  (both PASS)
python helix.py probe-run-all --lab music    → all_passed=True  (both PASS)

python helix.py atlas-build
  decision_compression: confidence=Verified, domains=['games','language','music'], runs=6
  oscillator_locking:   confidence=Verified, domains=['games','language','music'], runs=3

python helix.py cross-probe-analysis
  Total runs: 9  pass_rate: 100.0%
  Correlation decision_compression × oscillator_locking: r=0.0180
    (weak / no correlation — probes capture independent signals)

python helix.py verify → Architectural coherence verified.
```

---

## Atlas State After Phase 4

| Invariant | Confidence | Domains | Pass Rate |
|-----------|-----------|---------|-----------|
| decision_compression | Verified | games, language, music | 100% |
| oscillator_locking | Verified | games, language, music | 100% |
