# Law: Kuramoto Synchronization Phase Transition

**Type:** Dynamical Law  
**Status:** Empirically Verified  
**Origin:** Helix sweep — oscillator_sync, N=50, uniform freq [0.5,1.5]  
**Date:** 2026-03-15  

---

## Statement

A population of N coupled oscillators (Kuramoto model) undergoes a sharp
phase transition at a critical coupling K_c. Below K_c the system is
incoherent (R ≈ 0); above K_c synchronization emerges (R → 1).

**For natural frequencies uniform on [ω₀-D, ω₀+D]:**

    K_c = 2 / (π · g(ω₀)) = 2D · π / 2  →  K_c = 2/π ≈ 0.637  (D=0.5)

## Empirical Result

| K     | R (sync) |
|-------|----------|
| 0.000 | 0.156    |
| 0.500 | 0.325    |
| 0.625 | **0.739** ← transition |
| 0.750 | 0.900    |
| 1.000 | 0.953    |
| 2.000 | 0.990    |
| 3.000 | 0.995    |

- K_c empirical : **0.56 ± 0.06**  
- K_c theory    : **0.637** (N→∞)  
- Finite-N correction: ~12% (expected for N=50)

## Mechanism

Below K_c: coupling too weak to overcome frequency spread — phases drift.  
Above K_c: mean-field synchronization locks a fraction ∝ √((K-K_c)/K_c) of oscillators.

## Universality

This transition is substrate-independent: observed in neural oscillations, 
laser arrays, power grids, chemical reactions, and biological clocks.

## Falsifiers

1. R > 0.5 for K < 0.4 (would contradict incoherent phase)  
2. R < 0.5 for K > 1.0 (would contradict synchronized phase)  
3. K_c outside [0.5, 0.8] for these frequency parameters

## Data

- Source:   
- Method: RK4 integration, 100 time units, N=50, fixed seed
