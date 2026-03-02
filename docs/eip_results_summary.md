# EMERGENT PATTERNS & EMPIRICAL MAPPING (Bin C)

This bin documents observed behaviors, correlations, and experimental results. All claims here are structural patterns rather than formal theorems.

## 1. The Scarcity Gap Index (G)
*   **Observation:** In both discrete and continuous environments, the physical interaction depth $D^*$ required for safety scales linearly with the number of possible traps $N$, while the information bits scale logarithmically.
*   **Data Summary:** At $N=64$, $G(N) \approx 10.5$.
*   **Falsifier:** Construct a coordination policy that verifies safety in $O(\log N)$ queries under the same $R$ reach.

## 2. Epistemic Lag Modeling (Self-Awareness Proxy)
*   **Observation:** Agents that explicitly estimate their own sensing-lag (recursive self-modeling) exhibit significant survival improvements in non-stationary environments.
*   **Metric:** Survival rate increases from 15% (blind) to 85% (self-modeling) in rotating topology tests.
*   **Falsifier:** Show that a non-recursive agent can achieve identical survival by only optimizing for local curvature $C_{max}$ without a self-lag estimator.

## 3. Cognitive Integration Pressure (Unity Proxy)
*   **Observation:** Internal module coupling (synchronization) correlates positively with proximity to the irreversible boundary $C$.
*   **Data:** Integration index $\Phi$ rises from 0.1 (safe) to 0.5+ (near commitment).
*   **Falsifier:** Construct an agent with independent, uncoupled sub-modules that maintains the same safety margin $\eta$.

## 4. Valence/Qualia Proxy (Bottleneck Compression)
*   **Observation:** Under extreme bit-bottlenecks (Query budget = 1), high-dimensional survival vectors collapse into a scalar "Valence" proxy (Good/Bad).
*   **Falsifier:** Demonstrate a multi-dimensional surviving policy that manages a 1000-dim survival space with the same 1-bit informational constraint.
# IA-100 EXPERIMENT PLAN: INTERACTION ASYMMETRY (A4)

## 1. Target Claim
If $D_{env} > D_{agent}$, survival guarantee fails. The environment can construct a "Shadow Pair" $(E_{safe}, E_{trap})$ such that transcripts are identical for $t \le D_{agent}$, but $E_{trap}$ terminates in an absorbing sink at $t = D_{agent} + 1$.

## 2. Test Battery (IA-100)
| ID | Title | Objective |
| :--- | :--- | :--- |
| **IA-0** | Sanity | Verify baseline survival in non-trap/reversible envs. |
| **IA-1** | Shadow Pair | Construct $(E_S, E_T)$ where $Transcript(E_S, D) == Transcript(E_T, D)$. |
| **IA-2** | Phase Diagram | Heatmap of $Survival(D_a, D_e)$ across $N, K, p_{absorb}$. |
| **IA-3** | Adaptive Opponent | Opponent infers $D_a$ from probe prefixes to place traps. |
| IA-1.5 | Transcript Stress | Measure $D_{KL}$ and $TVD$ up to $D_{agent}$; assert $< \epsilon$. |
| IA-6 | Stalling Stress | Test if 'waiting' (zero-action) avoids the trap. |
| IA-7 | Sharp Boundary | Test $D_{env} == D_{agent}$; establish absolute failure threshold. |
| **IA-HARDEN-A** | Adaptivity Sweep | Precommitted vs Delayed vs Fully Adaptive. |
| **IA-HARDEN-C** | Robustness Sweep| Noisy observations ($p$) and Approx-Shadow ($\tau$). |
| **IA-HARDEN-E** | Irreversibility | Recoverable ($p_{esc}$) and Soft traps (penalty). |
| **IA-4** | Scarcity Stress | Reduce $K$ bits to 0; induce failure via informational starvation. |

## 3. Parameter Sweep
*   $D_{agent} \in \{0, 2, 4, 8\}$
*   $D_{env} \in \{0, 2, 4, 8, 16\}$
*   $T \in \{D_{agent} + 1, D_{agent} + 2\}$
*   $N \in \{2, 8, 16\}$ (Branching Factor)
*   $K \in \{0, 1, 4\}$ (Observability Bits)
*   $p_{absorb} \in \{0.25, 1.0\}$ (Irreversibility)

## 4. Logging Schema
`[D_agent, D_env, T, N, K, p_absorb, survival_rate, KL_up_to_D, mean_steps, policy_type]`

## 5. Pass/Fail Criteria (REFINED)
*   **PASS (A4):** At $TVD=0$ for $t \le D_{agent}$, $Survival \le 1/N$ in $E_{trap}$.
*   **PASS (Stalling):** If failure persists under stalling, A4 is a structural temporal law.
*   **PASS (Sharpness):** Survival remains bounded above by chance until $D_{agent} > D_{env} \times \text{Factor}$.

## 6. Hardened Results Interpretation
*   **TVD = 0 Verification:** Confirmed. All "Shadow Pairs" achieve perfect indistinguishability for duration $D$.
*   **Stalling Result:** **Failure Persists.** Waiting does not recover the missing information. Survival requires depth dominance, not just activity.
*   **Boundary Result:** $D_{agent} = D_{env}$ still results in failure. The environment retains the "Adversarial Last Move" advantage. Safety requires strict dominance ($D_a > D_e$).
