# Epistemic Irreversibility Principle (EIP)
**The Formal Theory of Survival under Informational Scarcity.**

## 1. FORMAL STATEMENT
The **Epistemic Irreversibility Principle (EIP)** states that for any agent with finite epistemic capacity ($r$), in an environment containing irreversible terminal sinks ($C$), there exists a hard informational horizon beyond which survival cannot be guaranteed without interactive state expansion (Rollout). In such systems, epistemic uncertainty does not scale as expected regret, but as binary terminal failure.

## 2. MINIMAL KERNEL (AXIOMS)
The kernel applies to localized, resource-constrained agents interacting with irreversible landscapes.
- **A1: Finite Epistemic Capacity ($r < \infty$):** Sensing and local data are strictly bounded.
- **A2: Irreversibility ($C$):** Existence of state-loss transitions from which recovery is impossible within the agent's energy budget $E$.
- **A3: Informational Reach ($R$):** The environment possesses a perturbation/reaction reach $R$ such that $R > r$.
- **A4: Interaction Depth ($D$):** Survival in adaptive environments requires agent simulation depth ($D_a$) to strictly dominate environmental reaction depth ($D_e$), i.e., $D_a > D_e$.

## 3. MINIMAL INEVITABILITY THEOREM
A survival guarantee ($P_s = 1$) is impossible if:
1.  **Absorbing Sinks:** A terminal set $\mathcal{C}$ is reachable.
2.  **Indistinguishability:** There exist partitions of the world-state $\{\omega_1, \omega_2\}$ that generate identical observation transcripts for all actions $a_{1:D}$, where $\omega_1$ terminates in $\mathcal{C}$.

**Result:** In the presence of absorbing sinks, informational scarcity ($R > r$) converts "error probability" into "deterministic failure."

## 4. REDUCTION MAP
| Framework | Relation | Condition |
| :--- | :--- | :--- |
| **Decision Tree LB** | Equivalent | Static scarcity regime ($R > r$). |
| **Best-Arm ID** | Strictly Stronger | EIP adds absorbing sinks; sub-optimal learning is lethal. |
| **Viability Theory** | Generalization | Extends viability kernels to truncated observability and discrete budgets. |
| **Minimax Search** | Reframing | Proof that depth mismatch ($D_e \ge D_a$) leads to terminal collapse. |
| **POMDP Reachability** | Special Case | EIP models the subset of POMDPs with irreversible failure sinks. |

## 5. FAILURE CONDITIONS
The EIP reduces to analogy or fails in:
- **$C^0$ Discontinuity:** Step-functions break Taylor-based curvature bounds ($C_{max}$).
- **Global Observability ($r \to \infty$):** Incompleteness vanishes.
- **Infinite Energy ($E \to \infty$):** Dimensional collapse becomes an optional optimization.
- **Reversibility:** If $C$ is recoverable, failure collapses back to standard regret scaling.

## 6. VERIFIED RESULTS SUMMARY
- **Scarcity Gap (EN):** Confirmed linear interaction cost $\Omega(N)$ vs logarithmic information cost $\log_2(N)$ for $N$ branches.
- **Interaction Asymmetry:** Validated that $D_e \ge D_a$ produces survival $P_s = 0$ in reactive shadow-pair tests.
- **Dimensional Collapse:** Verified $k_{eff} \to 1$ as a necessary energy-minimizing response to approaching irreversible boundaries.
- **Locality Horizon ($L^*$):** Derived and stress-tested as the tightest possible certificate for local safety.

## 7. OPEN PROBLEMS
- **Recursive Trust Calibration:** Distinguishing lethal curvature from adversarial sensor noise.
- **Non-Stationary Coupling:** Scaling $C_{max}$ in multi-agent environments where terrain is a function of the observer's step.
- **Tightness in High Dimensions:** Lower-bounding $k_{eff}$ on dense averaging paths.
