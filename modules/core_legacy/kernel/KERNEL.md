# KERNEL-002: Stability Mechanism Taxonomy

**Status:** CAPTURE
**Version:** 002
**Supersedes:** kernel-001 (DEPRECATED — incomplete trichotomy; descriptive only)
**Machine spec:** `core/kernel/kernel-002.json`
**KB claim object:** `kb/kernel-002.json`
**Audit evidence:** `docs/kernel-002_audit.md`

---

## 1. Purpose

Kernel-002 provides a taxonomy of the mechanisms by which far-from-equilibrium systems maintain structural persistence. It extends kernel-001's trichotomy (A/B/C) by two additional classes (D/E), adds explicit UNCLASSIFIED buckets for known gaps, distinguishes STATE from PATTERN persistence, and provides a minimal generative interface: a Mechanism Interface Template, HYBRID composition rules, and three falsifiable predictions.

This kernel does NOT assert the taxonomy is complete. It asserts: any far-from-equilibrium system that exhibits structural persistence instantiates at least one of A–E, OR belongs to an explicitly named UNCLASSIFIED bucket with a defined test plan.

---

## 2. Five Mechanism Classes

### 2.1 Class A — BARRIER

**Formal condition:** E_a/δ >> 1
**Formalism:** Transition State Theory (TST) / Kramers escape rate
**Stability condition:** τ_escape = τ₀ · exp(E_a/δ) >> T_observation
**Definition:** Structural persistence via kinetic trapping. The system occupies a local free-energy minimum from which thermal (or equivalent) fluctuations cannot escape on relevant timescales. No active throughput is required.
**Active maintenance required:** No. The barrier is a static property of the energy landscape.
**Failure mode:** Nucleation escape — a rare large fluctuation of amplitude ≥ E_a. Rate is Arrhenius: ~exp(-E_a/δ). Failure is stochastic in time even for δ < E_a.
**Key distinction:** Unlike Class D (TOPOLOGICAL), a Class A barrier is continuous — the system can approach the transition state via gradual fluctuations. There is always a finite escape rate for any δ > 0.
**Examples:** Diamond (E_a ≈ 7 eV vs. kT ≈ 0.025 eV), silicate glass, protein native fold, bacterial endospores, metallic glasses.
**Diagnostics:** E_a/kT ratio; Kissinger plot slope (activation energy from rate measurements); DSC transition enthalpy.

---

### 2.2 Class B — THROUGHPUT

**Formal condition:** M/δ > 1
**Formalism:** Input-to-State Stability (ISS) / Contraction theory (non-autonomous Lyapunov)
**Stability condition:** ∃ Lyapunov function V(x,t) for the driven system with V̇ < 0 while M is active.
**Definition:** Structural persistence via energy-dissipating active maintenance. The system is maintained far from equilibrium by a continuous energy flux M that opposes perturbation δ. Without M, the structure decays.
**Active maintenance required:** Yes. Removing M causes structural collapse.
**Adaptive maintenance:** M = f(δ) is explicitly permitted. If feedback gain ∂M/∂δ > 0 (perturbation-triggered repair), the system is still Class B. Perturbation-activated maintenance is THROUGHPUT, not a new class.
**Timescale specification:** M/δ > 1 may hold instantaneously or as a time-average over τ_avg. Systems with oscillatory M (M_inst < δ but M_avg > δ) are Class B if M_avg/δ > 1 over the relevant structural timescale τ_structure.
**Failure mode:** Throughput interruption — M → 0 or δ → M from above. Failure is deterministic above the critical threshold, not stochastic.
**Key distinction:** Unlike Class A, the stability basin exists only while M is active. Unlike Class C, the system is NOT at a critical manifold — structure is maintained by restoring force, not by divergent fluctuations.
**Examples:** Living cells (ATP flux vs. entropic/pathogenic load), Bénard convection, Belousov–Zhabotinsky oscillators, ferromagnets maintained by exchange coupling below T_c.
**Diagnostics:** M/δ ratio with explicit time-averaging window; power spectral density of maintenance signal; ISS gain margin.

---

### 2.3 Class C — CRITICAL

**Formal condition:** System poised near divergence of ξ (correlation length) or χ (susceptibility)
**Formalism:** Renormalization Group (RG) / Critical phenomena
**Stability condition:** |β - β_c|/β_c → 0; ξ ~ |β - β_c|^{-ν} → ∞; χ ~ |β - β_c|^{-γ} → ∞
**Definition:** Structural persistence (maximum structural complexity, sensitivity, and information transmission) via proximity to a critical point or critical manifold. Maximum structure occurs at M ≈ δ, not M >> δ.
**Active maintenance required:** Secondary only — a metabolic floor (Class B) may be required to sustain the critical state, but the primary structural complexity is from criticality, not throughput.
**Failure mode:** Detuning — parameter drift away from the critical manifold (β moves away from β_c). Structural complexity collapses both above (supercritical: seizure-like runaway) and below (subcritical: quenched order) the critical point.
**Key distinction from Class E:** In Class C, noise is a perturbation δ to be managed. In Class E, noise is the constructive agent. In Class C, the system is tuned to a thermodynamic/dynamical critical point parameterized by temperature, coupling constant, or equivalent. In Class E, the noise amplitude σ IS the parameter that controls structure.
**Scope guard for Class C:** Power-law statistics alone are NOT sufficient to assign Class C. Many non-critical mechanisms (agent heterogeneity, heavy-tailed distributions, multifractality) produce power-law statistics without ξ → ∞ or χ → ∞. Class C requires demonstrable critical point (measurable ξ divergence, finite-size scaling, or tuning parameter). This class does NOT apply to financial markets, DNNs, or evolutionary game dynamics unless a specific formal critical point with measurable ξ/χ is demonstrated.
**Examples:** SOC sandpiles (Bak et al. 1987), biological neural systems at criticality (Beggs & Plenz 2003), ferromagnets at T_c, second-order phase transitions.
**Diagnostics:** Avalanche exponent τ ≈ -3/2; 1/f spectral slope α ≈ 1; PCI (perturbational complexity index) for neural systems; finite-size scaling collapse.

---

### 2.4 Class D — TOPOLOGICAL

**Formal condition:** Discrete topological invariant Q ∈ ℤ (or other discrete group); ΔQ = 0 required for structural persistence; ΔQ ≠ 0 requires a defect-insertion event.
**Formalism:** TOPO — homotopy groups, topological field theory, K-theory (topological insulators)
**Stability condition:** Any smooth (continuous) perturbation of amplitude δ cannot change Q. Failure requires a discrete topological event (defect creation, vortex insertion, etc.) at cost E_defect.
**Active maintenance required:** No. The topological invariant is preserved by continuity of the field, not by active process.
**Key distinction from Class A (BARRIER):** A Class A barrier is continuous — any perturbation carries a finite escape rate. Class D protection is discrete: sub-threshold perturbations (δ < E_defect) carry ZERO escape rate, not merely an exponentially small one. The protection is exact, not probabilistic, for sub-threshold perturbations.
**Failure mode:** Topological defect insertion — a discrete event that changes Q. Failure is threshold-gated, not time-exponential. τ_failure → ∞ for δ < E_defect (zero rate, not small rate).
**Examples:** Vortex lattices in superfluids (winding number Q), topological insulators (Chern number), magnetic skyrmions (skyrmion number), knotted polymers (linking number Lk = Tw + Wr), logical qubits in topological QEC codes (code distance d).
**Diagnostics:** Topological charge Q (via winding number integral, or discrete parity); defect density; topological gap energy E_defect; persistence under sub-threshold perturbation (P1 prediction).

---

### 2.5 Class E — NOISE_CONSTRUCTIVE

**Formal condition:** Structure requires noise amplitude σ > 0; φ(σ = 0) = 0; φ(σ_opt) > 0 (peak exists); φ(σ → ∞) = 0. M and δ are NOT independently operationalizable — the noise source is constitutive of the structure.
**Formalism:** NOISE — stochastic resonance theory, noise-induced phase transitions (Horsthemke & Lefever 1984), Gaussian multiplicative noise SDEs.
**Stability condition:** ∃ σ_opt > 0 such that φ(σ_opt) = max_σ φ(σ) > 0. Structure is a non-monotonic function of noise amplitude.
**Key distinction from Class B:** In Class B, noise IS the perturbation δ to be resisted. M opposes δ. Reducing δ → 0 INCREASES structural stability. In Class E, reducing σ → 0 DESTROYS structure. The noise source is constructive, not adversarial.
**Key distinction from Class C:** In Class C, the system is tuned to a specific critical point in parameter space (temperature, coupling). Noise is δ. In Class E, noise amplitude σ IS the tuning parameter that creates structure. There is no separate critical point; σ_opt is not a thermodynamic phase transition.
**Failure modes:** Noise removal (σ → 0) OR noise excess (σ → ∞). Both collapse structure. The P2 prediction specifies this precisely.
**The M/δ distinction collapses:** In Class E, the same physical process generates both the perturbation and the structure. Attempting to define M and δ as separate quantities yields M/δ ≡ 1, which is not informative. The M/δ > 1 condition (Class B) is undefined or identically unity for Class E systems.
**Examples:** Stochastic resonance in sensory neurons (Moss & Wiesenfeld 1995), noise-induced symmetry breaking (Horsthemke & Lefever 1984), stochastic Turing patterns (noise-induced spatial order), noise-enhanced immune activation at appropriate bacterial load.
**Diagnostics:** Signal coherence or order parameter φ as function of σ; peak at σ_opt; mutual information I(signal; output) vs. σ; Class E is confirmed if φ(0) = 0 AND φ(σ_opt) > φ(0).

---

## 3. UNCLASSIFIED and Out-of-Scope Buckets

Systems that cannot be cleanly assigned to A–E are recorded here with explicit criteria and test plans. Promotion to a new class requires: (a) formal definition of the stability condition, (b) measurable diagnostic, (c) at least two non-trivial examples in distinct domains, (d) a break test.

### 3.1 NEUTRAL PERSISTENCE (UNCLASSIFIED — test plan pending)

**Description:** Structural persistence via high-dimensional neutral connectivity, without barrier, throughput, criticality, topological invariant, or noise-constructive mechanism.
**Primary example:** Evolutionary neutral networks (Kimura 1983). A population drifting along a neutral ridge in genotype space. E_a ≈ 0 (no fitness barrier), M ≈ 0 (no selection pressure), ξ finite (no critical divergence), no topological invariant, noise is not constructive.
**Why not promoted to Class F now:** The mechanism is not well-characterized beyond evolutionary dynamics. No formal stability condition has been stated. No measurable diagnostic has been defined. No non-evolutionary examples are established.
**Test plan for Class F promotion:**
- Define neutral connectivity measure N_d as a graph-theoretic property of the neutral network (e.g., degree distribution, path length distribution in phenotype-neutral genotype space).
- Candidate stability condition: N_d · |δ_drift| < 1 (drift rate times network diameter < 1 → population trapped in network).
- Test: compare persistence times in high-dimensional vs. low-dimensional neutral networks under equivalent drift amplitude. If persistence scales with N_d, Class F is justified.
- Decision review: next kernel iteration after evolutionary dynamics data assessed.

### 3.2 PATTERN PERSISTENCE (Out of scope for kernel-002)

**Description:** Persistence of dynamical attractors, cycling patterns, or statistical signatures (rather than a structural state). Examples: species cycling in intermediate-disturbance ecology (Connell 1978), the persistence of GARCH volatility clustering in financial markets.
**Why out of scope:** Kernel-002 addresses STATE persistence — the maintenance of a specific structural state against perturbation. Pattern persistence requires a separate framework: the "pattern" is not a state but a statistical property of a trajectory or an ensemble. Mixing state-persistence and pattern-persistence criteria produces self-sealing classifications.
**Marker:** Objects addressing pattern persistence should set `persistence_type: "PATTERN"` and `stability_class: "UNCLASSIFIED"`. No class assignment is made until a PATTERN kernel is developed.
**Practical impact:** Ecological succession climax state → Class B THROUGHPUT (state). Intermediate disturbance diversity peak → PATTERN (out of scope). Financial market microstructure → Class B THROUGHPUT (state, for liquidity regime). GARCH volatility clustering → PATTERN (out of scope).

### 3.3 EDGE-OF-STABILITY DYNAMICS (Out of scope for kernel-002)

**Description:** The "edge of stability" regime in DNN training (Cohen et al. 2021) where the loss landscape is being actively traversed, not occupied as a stable state.
**Why out of scope:** Kernel-002 addresses far-from-equilibrium structural persistence of a state. A frozen (deployed) DNN occupies a basin in weight space → Class A BARRIER (Hessian λ_max as barrier proxy). An actively training DNN is not in a persistent state — it is undergoing continuous structural change. The training trajectory is a dynamical process, not a persistent structure. The "far-from-equilibrium" criterion applies to the physical system being modeled, not to the mathematical optimization landscape.
**Scope note:** DNN weight space is a mathematical landscape, not a physical energy landscape. Mapping E_a to Hessian eigenvalue requires explicit justification that the mathematical analog is mechanistically equivalent, not just structurally similar.

---

## 4. STATE vs PATTERN Persistence

Every KB object classified under kernel-002 must specify `persistence_type`:

| Value | Definition | Kernel-002 in scope? |
|---|---|---|
| `STATE` | Persistence of a specific structural configuration against perturbation | Yes |
| `PATTERN` | Persistence of a dynamical attractor, statistical signature, or cycling behavior | No — requires PATTERN kernel |

Objects with `persistence_type: PATTERN` must set `stability_class: UNCLASSIFIED`.

---

## 5. Mechanism Interface Template

Every KB claim object under kernel-002 should specify the following observables. Those not applicable must be explicitly noted as N/A with justification.

```
MECHANISM INTERFACE:
  stability_class:    # A–E, HYBRID, or UNCLASSIFIED
  persistence_type:   # STATE or PATTERN
  mechanism_formalism: # TST | ISS | RG | TOPO | NOISE | OTHER

  OBSERVABLES (specify which are measurable in this domain):
    E_a:         # [Class A] Kinetic barrier height; units of δ; source: Arrhenius fit / calorimetry
    M:           # [Class B] Maintenance capacity; units of δ; timescale τ_avg must be specified
    δ:           # [A,B] Perturbation amplitude; source: thermal kT / stochastic noise / biological load
    ξ:           # [Class C] Correlation length; must show power-law divergence near critical point
    χ:           # [Class C] Susceptibility; must show power-law divergence near critical point
    Q:           # [Class D] Topological charge (integer or discrete group element); source: winding number integral
    σ:           # [Class E] Noise amplitude; measurable independently from any signal or structure
    noise_role:  # PERTURBATION (A/B/C) | CONSTRUCTIVE (E) | IRRELEVANT | MIXED
    M_adaptive:  # true/false — does M = f(δ)? If true, specify ∂M/∂δ. Still Class B if gain > 0.
    timescale_averaging: # specify τ_avg for M/δ conditions; instantaneous or time-averaged

  FAILURE MODES (specify which apply):
    nucleation_escape:          # Class A: rate ~ exp(-E_a/δ); time-exponential
    throughput_interruption:    # Class B: deterministic above threshold
    critical_detuning:          # Class C: parameter drift from critical manifold
    topological_defect_insert:  # Class D: discrete Q-change event; zero rate below E_defect
    noise_removal:              # Class E: σ → 0 collapses structure
    noise_excess:               # Class E: σ → ∞ collapses structure
```

---

## 6. HYBRID Composition Rules

### 6.1 Classification

A system is HYBRID if two or more class conditions are independently satisfied and independently measurable. Specify HYBRID as `HYBRID` in `stability_class` and list operative classes in `diagnostics`.

### 6.2 Dominance Rule

The mechanism with the shortest failure timescale dominates the failure mode:

```
τ_A = τ₀ · exp(E_a/δ)         [Kramers; exponential in E_a/δ]
τ_B = τ_structure · (M/δ - 1)⁻¹  [rough scaling; linear-ish in M/δ margin]
τ_C = τ_structure · |Δ/Δ_c|⁻ᶻ   [critical slowing down near detuning Δ → 0]
τ_D → ∞ for δ < E_defect        [infinite below threshold; finite above]
τ_E = τ_structure · |σ - σ_opt|⁻¹  [rough scaling; structure sharp near σ_opt]

dominant_failure = argmin over operative classes
```

### 6.3 Coupling Rule

Two variants of HYBRID:

**COEXISTING HYBRID:** Mechanisms are independently operative; no interaction term. Mechanisms can be removed independently.
- Label: `HYBRID(A+B)`, `HYBRID(B+C)`, etc.
- Prediction: asymmetric failure (τ_collapse differs by orders of magnitude when removing A vs. B, because τ_A is exponential while τ_B is linear in margin).
- Default: always start with COEXISTING assumption.

**COUPLED HYBRID:** Mechanisms interact (e.g., throughput generates barrier; barrier modifies M). Requires an explicit coupling function f(E_a, M).
- Label: `HYBRID(A↔B)` with coupling term specified.
- Without an explicit coupling term, default to COEXISTING.
- Prediction (P3): in COUPLED HYBRID(B↔C), throughput M suppresses early-warning signals before Class C criticality. Measurable as Var_observed/Var_predicted < 1 for M/δ > 1 near a B→C transition.

---

## 7. Falsifiable Predictions

These predictions are consequences of the class structure that are not trivially derivable from standard thermodynamics, control theory, or critical phenomena alone.

### P1 — TOPOLOGICAL: Threshold-gated failure (Class D)

**Statement:** For Class D systems, failure rate is exactly zero for perturbations below the defect creation threshold E_defect. Contrast with Class A (BARRIER): τ_A = τ₀·exp(E_a/δ) is finite (nonzero rate) for any δ > 0, even δ << E_a. For Class D: τ_D → ∞ for δ < E_defect (not merely large — infinite). Structural failure requires a discrete Q-change event, not gradual erosion.

**Required observables:** Q (topological charge, integer-valued); E_defect (defect creation energy threshold); δ (perturbation amplitude).

**Pass condition:** τ_decay → ∞ for all δ < E_defect. Survival rate = 1.0 for sub-threshold trials over arbitrarily long time.

**Fail condition:** τ_decay < ∞ with Arrhenius (exponential) time dependence for δ < E_defect. This would indicate Class A (continuous barrier), not Class D.

**Test harness:** `tests/test_topological_persistence.py` — 1D XY model on ring with winding number Q=1; thermal perturbations below/above vortex pair creation energy; measure survival rate vs. δ. Pass if survival rate = 1.0 for δ < δ_critical, < 1.0 for δ > δ_critical.

---

### P2 — NOISE_CONSTRUCTIVE: Non-monotonic order parameter (Class E)

**Statement:** For Class E systems, the order parameter φ is a non-monotonic function of noise amplitude σ: φ(0) = 0 (no structure without noise), φ(σ_opt) > 0 (peak exists at σ_opt > 0), φ(σ → ∞) → 0 (excess noise destroys structure). This is the opposite of Class B systems, where φ is monotonically decreasing in δ (more noise always reduces structure).

**Required observables:** φ — order parameter or signal coherence measure; σ — noise amplitude, independently measurable.

**Pass condition:** φ(0) = 0, φ(σ_opt) = max_σ φ(σ) > 0, φ(σ_high) < φ(σ_opt). At least three noise levels show the non-monotonic shape.

**Fail condition:** φ(0) > 0 (noise not necessary; Class A or B) OR φ monotonically decreasing in σ (Class B behavior; more noise always worse).

**Test harness:** `tests/test_noise_constructive_order.py` — stochastic resonance system with subthreshold signal; measure signal coherence vs. σ. Pass if non-monotonic peak confirmed.

---

### P3 — COUPLED HYBRID (THROUGHPUT + CRITICAL): Warning signal suppression

**Statement:** In a COUPLED HYBRID(B↔C) system, active maintenance capacity M modifies the effective susceptibility: χ_eff(M) < χ(M=0) for M > 0. Specifically, early-warning signals (rising variance) before a B→C class transition are suppressed by M. The suppression scales with M/δ:

```
Var_observed / Var_predicted(M=0) = g(M/δ)
where g is a monotonically decreasing function with g(0) = 1, g(M/δ → ∞) → 0
```

This means: a HYBRID(B+C) system will show WEAKER pre-collapse warning signals than a pure Class C system, because the throughput component is actively opposing the critical fluctuations.

**Required observables:** Variance Var(t) of a relevant observable; M/δ ratio; distance from critical manifold (tuning parameter λ - λ_c).

**Pass condition:** Var_observed/Var_predicted < 1 for M/δ > 0; suppression increases monotonically with M/δ.

**Fail condition:** Var_observed/Var_predicted = 1 for all M/δ — would indicate classes B and C are fully decoupled (COEXISTING, not COUPLED). This would reclassify HYBRID(B↔C) as HYBRID(B+C) (coexisting).

**Practical implication:** Ecological and physiological HYBRID(B+C) systems may exhibit WEAKER Scheffer-type (2009) early-warning signals than pure Class C systems, potentially masking impending collapse. This is a testable prediction with clinical and ecological relevance.

**Test harness:** `tests/test_classifier_smoke.py` (structural); full P3 test requires a 2D stochastic system with both restoring force (M) and proximity to fold bifurcation (Class C). TODO: add `test_hybrid_warning_suppression.py` in future iteration.

---

## 8. Scope Guards

Kernel-002 explicitly does NOT cover:

1. **Equilibrium systems** (δ ≈ 0; passive stability at thermodynamic ground state). Kernel-002 scope is far-from-equilibrium only.

2. **Pattern persistence** (dynamical attractors, statistical signatures). Requires a PATTERN kernel. See Section 4.

3. **Non-physical "stability" without formal operationalization.** The following mappings are METAPHORICAL and do not qualify for class assignment without explicit formal justification:
   - Financial market "kinetic barriers" (regulatory capital requirements as E_a)
   - DNN "critical point" (edge of stability or double descent as ξ → ∞)
   - Consensus protocol "activation energy" (computational cost as E_a)
   These mappings require demonstrating that the formal mathematical structure is not merely analogous but mechanistically equivalent to the class condition.

4. **Class C based solely on power-law statistics.** Requires demonstrable ξ/χ divergence at a specific critical point with a tuning parameter. Multifractality, heavy tails, and 1/f-like spectra are necessary but NOT sufficient.

5. **Neutral persistence** (evolutionary neutral networks). See Section 3.1, UNCLASSIFIED bucket.

6. **The generation of new structure through succession or bifurcation.** Kernel-002 addresses persistence of existing structure, not structural emergence.

---

## 9. Deprecation Trail

```
kernel-000 (DEPRECATED) → kernel-001 (DEPRECATED) → kernel-002 (CAPTURE)
```

See `docs/kernel_history.md` for full deprecation record.
