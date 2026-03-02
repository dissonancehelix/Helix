# MINIMAL INEVITABILITY THEOREM

## 1. Theorem Statement
A survival guarantee is impossible if and only if a terminal absorbing sink $\mathcal{C}$ is reachable for all surviving action sequences whose observation prefixes are identical to at least one terminal sequence.

## 2. Minimal Assumptions
1.  **Absorbing Sink:** There exists a state $c \in \mathcal{C}$ such that $P(\text{recovery} | c) = 0$.
2.  **Epistemic Equivalence:** There exist at least two configurations $(\omega_1, \omega_2)$ generating identical observation transcripts up to depth $D_{agent}$, where for any action $a$, at least one configuration terminates in $\mathcal{C}$.

## 3. Proof Sketch
Since $\omega_1$ and $\omega_2$ are indistinguishable for $t \le D_{agent}$, the agent must commit to a single action sequence $a_{1:D}$. If $\omega_1 \to \mathcal{C}$ and $\omega_2 \to \text{Safe}$, the adversary can select $\omega^* = \omega_1$. Because $c \in \mathcal{C}$ is absorbing, the agent cannot exit the sink once entered.

## 4. Reduction Analysis
| Framework | Relation | Condition |
| :--- | :--- | :--- |
| **Decision Tree LB** | Equivalent | When Absorption and Scarcity are both present. |
| **Best-Arm ID** | Strictly Stronger | Adds terminal failure constraint; learning is not free. |
| **Minimax Depth** | Reframing | Maps search horizon to terminal safety bounds. |
| **POMDP Reachability** | Special Case | Models the subset of POMDPs with irreversible sinks. |
