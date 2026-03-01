# INTERACTIVE GAME MODEL
**Axiom Translation to Decision Theory**

## 1. Environment Setup
An environment $E$ is a tuple $(X, A, \mathcal{W}, F, G, C)$ where:
- $X$: State space.
- $A$: Agent action space.
- $\mathcal{W}$: Adversary weight space.
- $F(x, a, w) \to x'$: Transition function.
- $G(x) \to o$: Observation function.
- $C \subset X$: Irreversible failure set (Terminal Sink).

## 2. Axiom Translation
- **A1:** Observation constraint $|o_t| \le K$ bits or $I(x_t; o_t) \le K$.
- **A2:** Reachability: if $x_t \in C$, then $x_{t+k} \in C$ for all $k > 0$ relative to budget $E$.
- **A3:** Adversary budget $R$: $\text{diam}(\{F(x, a, w) : w \in \mathcal{W}\}) \le R$.
- **A4:** Agent policy depth $D_a$ vs Environment adaptive response $D_e$.

## 3. The Game of Survival
1. Adversary chooses configuration $w^* \in \mathcal{W}$ and hidden state $s \in X$, consistent with $o_0$.
2. For $t = 1 \dots D$:
   - Agent chooses $a_t$.
   - Environment transitions to $x_{t+1}$ and reveals $o_{t+1}$.
3. **Win Condition:** Agent survives if $x_t \notin C$ for all $t$.
4. **Veto:** If $x_t \in C$, the game terminates in failure.

## 4. Relationship to Known Models
- **Partial Observability:** $G(x_t)$ maps to POMDP kernels.
- **Active Learning:** Querying $a_t$ is a member of the Best-Arm Identification family.
- **Adversarial Bandits:** Environment choice is a worst-case selection over the indistinguishability class.
