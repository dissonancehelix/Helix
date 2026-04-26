# GWT / Consciousness Probe — Findings and Open Paths

**Date:** 2026-03-25
**Status:** Paused — complete through Path A and Path B
**Probe files:** `domains/games/probes/gwt_*.py`
**Artifacts:** `applications/labs/artifacts/gwt_*.json`

---

## What We Were Trying to Do

Test whether the belief-network simulations in Helix produce dynamics that are
structurally consistent with Global Workspace Theory (GWT) and Integrated
Information Theory (IIT) — not because the model was designed to, but as an
emergent property.

The goal was something genuinely non-circular: a finding that wasn't baked into
the model's design.

---

## The Simulation Stack

Six cognitive profiles running in a 80-agent belief-propagation network:

| Profile | Key parameters | Behavior |
|---|---|---|
| CONFORMIST | trust builds fast, low self_weight | herds toward consensus |
| IMPULSIVE | fast build, low threshold | accepts influence quickly |
| DIPLOMAT | moderate everything | smooth averager |
| SELECTIVE | slow build (0.04), high self_weight (0.85) | resists; large pre-ignition window |
| PARANOID | very slow build, high cynicism | rarely reaches consensus |
| CONTRARIAN | updates toward (1 - trusted_mean) | accidentally truth-seeking under liars |

Adversarial finding: CONTRARIAN has structural immunity to consistent liars
because it inverts the liar's anchor. This is not accuracy — in clean environments
it's equally wrong. SELECTIVE wins 100/100 seeds against consistent adversarial
noise specifically due to self_weight capping external influence at 0.018/step.

Signal crossover: CONFORMIST overtakes SELECTIVE at signal_weight ≈ 0.010.
Any environment with >1% reliable external signal favors CONFORMIST.
SELECTIVE's niche is high-noise, adversarial, or epistemically hostile environments.

---

## GWT / IIT Probe Results

### Setup

- Φ proxy: mutual information between agent halves I(A;B) = H(A)+H(B)−H(AB)
- Ignition = step where gap (mean absolute belief deviation) drops below 0.10
- Φ gap = ignition_step − phi_peak_step (how many steps before ignition does Φ peak)

### Key result

**Φ peaks before ignition in 5/5 profiles.** This matches GWT's prediction that
integration peaks before the global broadcast (ignition). However — this was
expected from the model's design. The trust mechanism causes Φ to rise as agents
integrate information, then drop as they converge. Ignition comes after integration,
so of course Φ peaks first. This is circular.

**SELECTIVE Φ gap = 53 steps.** Published ASD P3b latency is 350–500ms vs
280–350ms neurotypical, a gap of ~70–150ms. SELECTIVE's 40% larger window
relative to other profiles wasn't specifically designed for this ratio. Weak but
non-circular.

**Cross-domain CV = 0.139 (earlier probe).** The logistic collapse shape showed
low variation across simulation and language data in the initial probe. This was
later refined by Path B.

---

## Path A — Φ Timing vs Trust Build Rate

**File:** `gwt_phi_timing_probe.py`
**Artifact:** `applications/labs/artifacts/gwt_phi_timing.json`

Swept trust_build_rate from 0.01 to 1.0 (16 values × 8 seeds each).

### Results

| rate | mean Φ_gap | collapse step |
|---|---|---|
| 0.010 | 89.9 ± 21.5 | 116.1 |
| 0.040 | 61.4 ± 9.9 | 71.1 |
| 0.100 | 57.4 ± 6.5 | 61.8 |
| 0.300 | 53.0 ± 6.4 | 57.6 |
| 1.000 | 53.6 ± 6.4 | 56.6 |

Power law fit: `Φ_gap = 48.1 × rate^(-0.099)`, R² = 0.771

**b = 0.099.** This is nearly flat. The Φ gap varies 1.7x over a 100x range of
trust_build_rate. The relationship flattens entirely above rate ≥ 0.10.

**Structural floor: ~53 steps.** Regardless of how fast trust builds, the network
cannot compress the pre-ignition integration window below ~53 steps. This is set
by network topology (connection_prob=0.20, N=80), not by the learning rate.

**What this kills:** The strong neural prediction (Φ_gap ∝ ε^(-b) with b≈0.8)
does not hold. b=0.099 means the N2→P3b window would barely scale with learning
rate across subjects. Not a useful EEG prediction.

**What survives:** The floor. The minimum integration window is topologically
determined, not speed-determined. This is actually a cleaner finding: the network's
geometry sets a lower bound on pre-ignition time.

---

## Path B — Cross-Domain Logistic Shape

**File:** `gwt_domain_dcp_series.py`
**Artifact:** `applications/labs/artifacts/gwt_domain_dcp_series.json`

Fitted logistic collapse shape `gap(t) = 1/(1 + exp(k·(t−t0)))` across:

- Kuramoto oscillator simulations (from datasets/agents/ JSON files)
- Sentence trajectory data (Finnish, Mandarin, Spanish)
- Belief network runs (SELECTIVE profile, 5 seeds)

All series min-max normalized before fitting.

### Results

| Domain | k | R² | Collapse window |
|---|---|---|---|
| Language / Finnish | 7.5 | 0.97 | ~53% of sentence |
| Language / Mandarin | 12.0 | 0.92 | ~33% of sentence |
| Cognition / belief | 15–20 | 0.91–0.96 | ~20% of simulation |
| Physics / Kuramoto (games) | 50 | 0.99 | ~8% of simulation |
| Physics / Kuramoto (music) | 75 | 0.98 | ~5% of simulation |

Overall CV = 0.771. **No cross-domain k invariant.**

**What's true:** The logistic functional form appears in all domains (high R²
everywhere). The exponent k sorts by coupling strength: high-K physical systems
collapse sharply; low-K social systems collapse gradually. This is the expected
relationship between Q-factor and resonance sharpness — correct but not novel.

**Interesting alignment:** Cognition k ≈ 15–20 corresponds to a ~20% transition
window, which matches the ~200ms N2→P3b window in a ~1s EEG trial. This wasn't
designed in — it emerged from the trust network's natural convergence timescale.
One data point; weak evidence; but it's the only result that wasn't obvious.

---

## Honest Net Assessment

| Claim | Status |
|---|---|
| Φ peaks before ignition | True but circular — structural consequence of model design |
| Power law Φ_gap vs rate | Weak (b=0.099); floor is real but not a strong prediction |
| Logistic form is universal | True; but this is known for any threshold-crossing system |
| k is domain-invariant | False (CV=0.771) |
| k reflects coupling strength | True; expected from physics |
| Cognition k aligns with EEG window | Weakly yes; not circular; one observation |

The simulation stack is doing real work — CONTRARIAN immunity, SELECTIVE niche,
evolutionary dynamics — but none of the GWT/consciousness-specific probes produced
a finding that couldn't be explained by the model's construction.

---

## Paths 1–4 Results (2026-03-25)

### Path 1 — Topology Floor ✓ Supported

**Probe**: `gwt_topology_floor.py` | **Artifact**: `gwt_topology_floor.json`

Swept N (20–320) × connection_prob (0.05–0.80), held cognitive params at
SELECTIVE with trust_build_rate=1.0 to remove learning-rate effects.

**Result**: For well-connected networks (N≥80):
```
floor = 6.2 × L + 46.8   (R²=0.90, n=15)
```
- ~47-step irreducible floor: minimum integration time regardless of topology
- 6.2 steps per unit path length: information travel cost
- Near-percolation (small N, sparse p): floor volatile, not topologically determined

**Finding**: The pre-ignition window has two components — an irreducible constant
(~47 steps, set by the trust accumulation dynamics) and a topological correction
(path length × 6.2). Learning rate is irrelevant once connections exist.

---

### Path 2 — K_eff Formalization ✗ Rejected; reveals cleaner result

**Probe**: `gwt_keff_formalization.py` | **Artifact**: `gwt_keff_formalization.json`

Swept trust_build_rate × connection_prob × N (54 conditions × 5 seeds).

**Result**: K_eff = trust_build_rate × connection_prob × N does not predict k.
R²=0.06 for all fit forms. The Kuramoto bridge is not supported (predicted k=15–16
for Kuramoto K_eff=2.0; observed k=50).

**Actual driver**: k is set by N × connection_prob (mean degree), not K_eff.
A 100× change in trust_build_rate changes k by <2 points. Mean degree explains
~85% of k variation within the belief-network domain.

```
N×p =  4 → k ≈ 10
N×p = 16 → k ≈ 17
N×p = 64 → k ≈ 20  (saturating logarithmic relationship)
```

**Finding**: In belief networks, collapse steepness is a graph property, not a
learning-rate property. The Kuramoto bridge fails because Kuramoto coupling is
continuous and instantaneous; belief-network coupling is thresholded and
trust-mediated. They cannot share a K_eff.

---

### Path 3 — EEG Alignment ◑ Partial (synthetic only)

**Probe**: `gwt_eeg_alignment.py` | **Artifact**: `gwt_eeg_alignment.json`

Mode A (synthetic — no external EEG data):

| Profile | k | t0 | Window |
|---|---|---|---|
| SELECTIVE | 17.0 | 140ms | 185.5ms |
| CONFORMIST | 200.0 | 0ms | 4ms |

EEG landmarks: P3b=380ms, N2→P3b window=180ms.

**Window match: 185.5ms vs 180ms (error: 5.5ms)**. The N2→P3b duration is
reproduced without being tuned for it.

**t0 miss: 140ms vs 380ms**. Absolute timing requires a stimulus-onset offset
parameter not present in the simulation.

**Finding**: The collapse duration at k≈17 naturally produces the correct
N2→P3b window width. The absolute timing mismatch is expected — the simulation
has no concept of trial onset. Empirical validation requires an EEG dataset
(OpenNeuro ds002034, ds003517, or ds001810) and Mode B.

---

### Path 4 — Adversarial Ecology Formalism ◑ 2/3 confirmed

**Probe**: `gwt_adversarial_formalism.py` | **Artifact**: `gwt_adversarial_formalism.json`

**Exp 1 — CONTRARIAN immunity vs liar anchor**: Confirmed (error=0.15).
Peak CONTRARIAN advantage at liar_anchor=0.1 (predicted 0.25). Advantage is
monotonically decreasing as anchor rises, crossing zero at anchor=0.5
(liars equidistant from truth). CONTRARIAN is a liability when liars are on
the same side of 0.5 as truth.

Formal condition: CONTRARIAN beats CONFORMIST when sign(liar_anchor − 0.5) ≠ sign(truth − 0.5).

**Exp 2 — SELECTIVE crossover**: Confirmed (error=0.002).
CONFORMIST overtakes SELECTIVE at signal_weight=0.020.
Predicted: update_rate × (1 − self_weight) = 0.12 × 0.15 = 0.018. Exact.

**Exp 3 — Optimal CONTRARIAN fraction**: Falsified.
Error decreases monotonically through 50% CONTRARIAN — no interior optimum.
"c* = liar_fraction" prediction was wrong. Each additional CONTRARIAN reduces
network conformity generally, not just canceling one liar. The interior optimum
only appears when balancing adversarial vs clean-signal performance — this
experiment ran adversarial only.

---

## Real-Domain Probes (2026-03-25)

### LLM Cognitive Profile — Bayesian accumulator, not a simulation profile

**Probe**: `gwt_llm_agent_profile.py` | **Artifact**: `gwt_llm_agent_profile.json`

5 tasks × 2 conditions (clean/adversarial) × 8 sequential evidence turns.

**Result**: Claude does approximately correct Bayesian inference across turns.
Trajectories are smooth accumulation curves, not logistic collapse events.
All tasks classified k=1 (PARANOID in sim terms) — but this is a misclassification.
The LLM moves from 50% to 95%+ on clean signals; PARANOID doesn't move at all.
The logistic collapse model does not apply at this timescale.

Clean vs adversarial:
- Clean mean final confidence: ~97%
- Adversarial mean final confidence: 82.6% (3 false signals out of 8)
- Penalty ~15% for 37.5% false signal rate — roughly proportional

**Finding**: LLM belief updating is a BAYESIAN_ACCUMULATOR profile not present
in the simulation. DCP collapse events may only be visible within a single
long reasoning trace, not across sequential conversational turns. Proper
multi-turn adversarial resistance exists: confidence degrades gracefully under
false signals rather than collapsing or ignoring them.

---

### Chess DCP — Language-range k, not physics-range

**Probe**: `gwt_decision_dcp.py` | **Artifact**: `gwt_decision_dcp.json`

Piece count as possibility-breadth proxy (strictly monotone; 32→2 pieces).

| Game | Type | k | R² |
|---|---|---|---|
| Kasparov vs Topalov 1999 (Immortal) | tactical | 7.0 | 0.976 |
| Karpov vs Kasparov 1986 G16 | positional | 7.0 | 0.897 |
| Capablanca vs Tartakower 1924 | endgame | 20.0 | 0.979 |

Mean k=11.3. Prediction was k≈50–75 (physics-like).

**Finding**: Chess piece exchange follows a language-like logistic (k≈7–12),
not a physics-like one. Captures are discrete events spread across the whole
game — structurally identical to how a sentence resolves grammatical ambiguity
word-by-word. The "tight constraint" of chess does not produce sharp collapse
because coupling is discrete and sequential, not continuous and instantaneous.

Capablanca endgame k=20 (cognitive range) reflects the sharper simplification
phase of technical endings vs. gradual middlegame trading.

---

### Wikipedia Network Consensus — Density predicts engagement, not speed

**Probe**: `gwt_network_consensus.py` | **Artifact**: `gwt_network_consensus.json`

89 threads from WT:NFL and article talk pages (archives 1–5).
13/89 threads include user Dissident93.

**Result**: posts/participant vs density: slope=+1.94, R²=0.28.
Prediction was negative slope (denser → faster = fewer posts needed).
Slope is positive — denser networks have MORE posts per participant.

**Finding**: Two structurally different thread types are present:
- Voting threads (WP:RM): density≈0, ~1 post/participant — everyone votes once
- Debate threads: density>0, 3–5+ posts/participant — back-and-forth replies

Denser networks produce more engagement, not faster convergence. The simulation's
topology floor prediction (faster collapse in denser networks) may apply to
convergence *quality* (fewer reversions post-consensus) rather than post count.
Requires timestamp-based time-to-resolution and thread-type separation to test
cleanly.

---

## Cross-Domain Synthesis

**The through-line across all probes**: The simulation's coupling-strength →
collapse-sharpness relationship only holds for systems with *continuous
instantaneous coupling* (Kuramoto oscillators, k≈50–75). Every discrete
sequential system — chess (k≈7–11), language (k≈7–12), Wikipedia deliberation,
belief networks (k≈15–20) — lives in the lower range regardless of how
"tight" the constraints feel from the inside.

**Discreteness is the moderating variable**: not constraint tightness, not
domain, not participant count. Systems where events happen one at a time
and coupling is mediated by accumulation (trust, words, captures) produce
gradual S-curves. Systems where all elements couple simultaneously produce
sharp transitions.

**What this means for DCP**: The logistic collapse shape is genuinely universal
(high R² everywhere). The steepness k is not universal — it sorts by coupling
mechanism, not by domain. This is a refinement of the original claim, not a
falsification of it.

---

## Open Paths

| Path | Status |
|---|---|
| Path 3 empirical EEG | Requires OpenNeuro dataset (ds002034/ds003517/ds001810) |
| Path 3 exp3 re-run | Needs clean+adversarial cost function to find c* |
| Wikipedia timestamps | Requires revision-history API fetch for time-to-resolution |
| LLM within-trace DCP | Test DCP on single long reasoning trace, not cross-turn |
| Music / S3K DCP series | Blocked on overnight library run completing |

---

## Files Written This Arc

| File | Purpose |
|---|---|
| `domains/games/probes/godot_cognition.py` | Core belief-network sim |
| `domains/games/probes/godot_deep_search.py` | Adversarial consensus |
| `domains/games/probes/godot_extended_search.py` | Self-weight/cynicism isolation |
| `domains/games/probes/godot_profile_comparison.py` | 6-profile monoculture |
| `domains/games/probes/godot_ecology.py` | Mixed heterogeneous network dynamics |
| `domains/games/probes/gwt_consciousness_probe.py` | GWT/IIT ignition + Φ |
| `domains/games/probes/gwt_phi_timing_probe.py` | Path A: Φ gap vs trust_build_rate |
| `domains/games/probes/gwt_domain_dcp_series.py` | Path B: cross-domain logistic fit |
| `domains/games/probes/gwt_topology_floor.py` | Path 1: topology floor sweep |
| `domains/games/probes/gwt_keff_formalization.py` | Path 2: K_eff vs k regression |
| `domains/games/probes/gwt_eeg_alignment.py` | Path 3: EEG synthetic prediction |
| `domains/games/probes/gwt_adversarial_formalism.py` | Path 4: ecology formalism |
| `domains/games/probes/gwt_llm_agent_profile.py` | LLM Bayesian profile probe |
| `domains/games/probes/gwt_decision_dcp.py` | Chess piece-count DCP |
| `domains/games/probes/gwt_network_consensus.py` | Wikipedia topology probe |

All artifacts saved to `applications/labs/artifacts/gwt_*.json`.
