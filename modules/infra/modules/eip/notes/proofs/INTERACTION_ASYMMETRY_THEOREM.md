# INTERACTION DEPTH ASYMMETRY
**Formalization of Axiom A4**

## 1. Theorem: Indistinguishable Reactive Traps
If $D_{agent} < D_{env}$, there exists an environment class where all observation traces for any probe of depth $D_{agent}$ are safe, but all reachable paths terminate in failure at $t = D_{agent} + 1$.

## 2. Construction: The Adaptive Shadow
- **World 1 (Safe):** A static corridor of length $2D$.
- **World 2 (Reactive Trap):** Appears static for $t \le D_{agent}$. The environment responds to the agent's first action $a_1$ by placing an irreversible sink $C$ at $D_{agent} + 1$.
- **Adversary:** Reaction policy $\Pi_{env}$ has depth $D_{env}$. It places the trap beyond the agent's lookahead horizon.

## 3. Proof
- The agent simulates up to $D_{agent}$. The reactive trap at $D_{agent} + 1$ is outside its sensing/query horizon.
- For any probe $a_{1:D}$, observations $o_{1:D}$ are identical in both worlds.
- The agent cannot distinguish between a static safe world and a reactive lethal world.
- Failure is inevitable if the adversary matches the agent's plan with a deeper reaction trap.

## 4. Operational Result
Survival requires $D_{agent} \ge \text{Adversary\_Reach} \times \text{Reaction\_Frequency}$. This establishes simulation depth as a primary structural constraint for safety.
