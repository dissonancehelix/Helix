# Helix Simulation Stack

---

## Overview

The simulation stack describes how Helix runs experiments from command to result.

```
Operator intent
      │
      ▼
tool/script invocation
      │
      ▼
Kernel: parse → validate → normalize
      │
      ▼
Dispatcher: route to engine
      │
      ├──► Python Engine ──► probe/experiment runs
      │                            │
      └──► Godot Engine ──► spatial simulation
                                   │
                                   ▼
                           Raw results / telemetry
                                   │
                                   ▼
                           Atlas: store observations
                                   │
                                   ▼
                           Discovery: detect patterns
                                   │
                                   ▼
                           Atlas: record invariant candidates
```

---

## Python Engine Stack

For computational experiments:

1. Runtime request arrives at the Python runner
2. Engine resolves probe from `PROBE_REGISTRY` using target
3. Probe module executes with params
4. Results returned as structured dict
5. Dispatcher writes result to atlas

**Probe types:**
- `network` — graph topology analysis
- `dynamical` — ODE/attractor systems
- `oscillator` — coupled oscillator phase locking
- `cellular` — cellular automata pattern detection
- `evolutionary` — selection and population dynamics
- `information` — entropy and compression measures
- `dataset` — structural fingerprinting of datasets

---

## Godot Engine Stack

For spatial and embodied experiments:

1. Runtime request arrives at `GodotAdapter`
2. Adapter generates or selects a `.tscn` scene
3. Godot launched headless with scene + params
4. Telemetry captured from Godot stdout or file output
5. Results returned as structured dict

**Spatial probe types (Phase 9):**
- Multi-agent emergence
- Environment generation and traversal
- Physics interaction patterns
- Embodied constraint detection

---

## Artifact Discipline

All experiment outputs follow deterministic naming:

```
atlas/experiments/{engine}/{probe}/{run_id}/
    params.json
    result.json
    observations.json
    metadata.json
```

Run IDs are timestamps + probe name hash. No random IDs. No silent drops.

---

## Cross-Substrate Comparison

To test whether a pattern is substrate-independent:

1. Run the same structural probe on Python engine (mathematical substrate)
2. Run the equivalent spatial probe on Godot engine (embodied substrate)
3. Compare regime maps and invariant signatures
4. If pattern survives substrate change → invariant candidate promoted

This is the core discovery mechanism of Helix.
