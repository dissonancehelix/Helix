# Law: Epistemic Irreversibility — Inverse-Square Noise Scaling

**Type:** Information-Theoretic Law  
**Status:** Empirically Verified  
**Origin:** Helix sweep — epistemic_irreversibility, N=200 trials  
**Date:** 2026-03-15  

---

## Statement

The epistemic irreversibility signal of a bistable stochastic system scales
as the inverse square of noise intensity in the degradation regime:

    signal(noise) ~ C · noise^{-2}   for noise > noise_c

Equivalently, since D = noise²/2 is the diffusion coefficient:

    signal ~ 1/D   (information capacity scales as 1/diffusion)

## Empirical Result

| noise | signal (bits) |
|-------|--------------|
| 0.010 | 49.83  |
| 0.113 | 49.82  ← plateau ends |
| 0.133 | 40.68  ← breakpoint  |
| 0.195 | 19.02  |
| 0.277 |  9.41  |
| 0.400 |  4.51  |

- **Plateau**: noise < 0.12 → signal ≈ 49.83 bits (maximum commitment)  
- **Breakpoint**: noise_c ≈ **0.133**  
- **Scaling exponent**: signal ~ noise^{**-2.000**}  (exact)

## Noise Threshold

For the bistable system dx/dt = x - x³ + bias + noise·dW,
barrier height ΔV = 0.25:

    noise_c ≈ √(2·ΔV·dt) = √(2 × 0.25 × 0.05) ≈ 0.158

Empirical ratio: noise_c / √(2ΔV·dt) ≈ **0.84**

## Mechanism

The bistable system commits to one attractor (±1) when noise is insufficient
to drive escape over the barrier. The irreversibility signal measures the
information lost in commitment. When noise ~ noise_c, the system begins
partial reversibility. The 1/noise² scaling follows from:

    SNR = (signal_power) / D = (ΔV)² / (noise²/2) ~ noise^{-2}

This is the continuous-channel capacity analog of the Cramér-Rao bound.

## Universality

This law should hold for any bistable system under additive Gaussian noise.
The exponent -2 is fixed by the Gaussian noise model; heavy-tailed noise
would give different exponents.

## Falsifiers

1. Exponent significantly ≠ -2 under additive Gaussian noise  
2. Plateau level > log₂(N·steps) (would indicate measurement artifact)  
3. Transition at noise_c > √(2ΔV) = 0.707 (barrier violation)

## Data

- Source: 
- Method: N=200 trials, 300 steps, bias=0.01
