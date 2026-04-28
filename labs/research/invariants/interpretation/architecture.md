# Helix Architecture

**Version:** Phase 6 — Architectural Stabilization
**Status:** Locked

---

## Layer Overview

Helix is organized into five architectural layers. Each layer has a defined responsibility. Dependencies flow downward only.

```
Kernel
  └── Engines
        └── Discovery
              └── Atlas
                    └── Modules
```

---

## 1. Kernel

The stable execution core. Rarely changes.

**Responsibilities:**
- Runtime environment control
- Command normalization via HIL (Helix Interface Language)
- Command validation and dispatch
- Filesystem discipline and artifact writing
- Deterministic execution guarantees

**Components:**
- `kernel/hil/` — grammar, normalizer, validator, dispatch interface
- `kernel/dispatcher/` — routes normalized commands to engines
- `kernel/runtime/` — execution lifecycle and environment management

**Rule:** Nothing outside the kernel modifies kernel internals.

---

## 2. Engines

Modular execution environments. New engines can be added without touching the kernel.

**Current engines:**
- `engines/python/` — computational experiments (networks, dynamics, CA, evolutionary, info theory)
- `engines/godot/` — spatial simulation (multi-agent, physics, embodied experiments)

**Interface:** Each engine exposes a `run(envelope: dict) -> dict` method that accepts a normalized HIL envelope.

---

## 3. Discovery

The active search layer. Contains experiments, probes, and parameter sweeps.

**Responsibilities:**
- Running structured experiments across engines
- Probing parameter spaces for regime transitions
- Detecting emergent invariants and structural patterns

**Components:**
- `discovery/probes/` — individual probe definitions
- `discovery/experiments/` — full experimental runs
- `discovery/sweeps/` — parameter sweep configurations

---

## 4. Atlas

Helix's persistent memory and knowledge system.

**Responsibilities:**
- Storing experiment results and observations
- Indexing regime maps and invariant candidates
- Holding all project documentation

**Components:**
- `atlas/experiments/` — historical experiment artifacts
- `atlas/observations/` — raw observations and measurements
- `atlas/regimes/` — detected regime maps
- `atlas/invariants/` — invariant candidates and proofs
- `atlas/docs/` — architecture, philosophy, roadmap, HIL spec, simulation stack

---

## 5. Modules

User-facing systems built on top of Helix.

**Responsibilities:**
- Applying Helix's discovery capabilities to specific domains
- Providing interfaces for operators and researchers

**Current modules:**
- `modules/language_lab/` — structural experiments on language
- `modules/creativity_lab/` — generative and creative systems
- `modules/game_systems_lab/` — game mechanics and emergent dynamics

**Rule:** Modules must never modify kernel internals.

---

## Dependency Rules

| Layer | May depend on |
|-------|--------------|
| Kernel | Nothing above itself |
| Engines | Kernel only |
| Discovery | Kernel + Engines |
| Atlas | Receives outputs from all layers |
| Modules | Kernel + Engines + Discovery |
