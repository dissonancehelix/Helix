# KERNEL SPECIFICATION
**Epistemic Irreversibility Principle (EIP)**

## 1. Minimal Kernel Axioms
These axioms define the fundamental limits of localized agents in interactive environments.

*   **A1: Epistemic Capacity ($r$):** The limit of local observational data. Any state beyond this budget is epistemically indistinguishable from any other state consistent with the local history.
*   **A2: Resource Scarcity ($E$):** Survival costs are non-zero. A transition to state $x'$ is "irreversible" if the recovery cost exceeds the resource budget $E$.
*   **A3: Informational Reach ($R$):** The diameter of the set of reachable states $x_{t+1}$ over all admissible environment weights $w_t \in \mathcal{W}$ per decision cycle.
*   **A4: Interaction Depth ($D$):** Survival in adaptive environments requires the agent's simulation depth $D_a$ to strictly dominate the environment's reaction depth $D_e$ ($D_a > D_e$).

## 2. Fundamental Theorems

### Theorem K0: The Scarcity Inevitability
If $R > r$ and $E < \text{RecoveryCost}$, local inference is mathematically insufficient to guarantee safety. Success requires interaction depth $D_a$ to cover the exhaustive reach of the threat family.

### The Scarcity Gap Bound
For an environment family $E_N$ with $N$ branches (1 safe, $N-1$ absorbing traps):
- **Information:** Naming the safe branch requires $\log_2(N)$ bits.
- **Interaction:** Guaranteeing survival requires linear interaction depth $D \ge N-1$.
**The Scarcity Gap:** $G(N) = D / \log_2(N)$ quantifiers the work-to-information divergence.

## 3. Jurisdiction
The EIP applies strictly to:
1. Bounded agents ($E < \infty, r < \infty$).
2. Time-asymmetric (irreversible) systems.
3. Landscapes with measurable regularity ($C^1$ smoothness necessity for $L^*$).
