# MATHEMATICAL COMPRESSION: INTERACTIVE TRAP GAMES

## 1. Formal Definitions
- **Game $\mathcal{G}$:** A tuple $(X, A, \Omega, \mathcal{T}, \mathcal{O}, \mathcal{C})$
- **States $X$:** Contains a terminal set of absorbing sinks $\mathcal{C} \subset X$.
- **Actions $A$:** Agent choice space.
- **Adversary $\Omega$:** Family of transition/observation mappings.
- **Transitions $\mathcal{T}(x, a, \omega) \to x'$:** State transition function.
- **Observations $\mathcal{O}(x) \to o$:** Mapping from state to observation space with budget $K$.
- **Absorbing Sink:** $\forall a, \omega: \mathcal{T}(c, a, \omega) = c$.

## 2. Minimal Kernel (Inevitability Conditions)
1. **Strict Absorbing Sinks:** $P(\text{recovery} | x \in \mathcal{C}) = 0$.
2. **Epistemic Indistinguishability:** $\Omega_{indist} \subseteq \Omega$ generates identical transcripts for $t \le d$.
3. **Adversarial Winner:** Environment selects $\omega^* \in \Omega_{indist}$ post-policy commitment.

## 3. Theorem Compression
- **Scarcity:** $P_s \le 1/N$ for query budget $k < N-1$.
- **Interaction Depth:** If $D_{env} > D_{agent}$, there exists an adaptive reaction $\omega_{t+k}$ placing $x \in \mathcal{C}$ at $D_{agent}+1$.
- **Observation Masking:** If $\mathcal{O}(c^*) = \mathcal{O}(c \in \mathcal{C})$, identification is impossible.

## 4. Counterexample Regimes
The theorems collapse to regret scaling if:
1. **Recoverability:** Exit from $C$ is possible.
2. **Static Environment:** $D_{env} = 0$.
3. **Hint Channel:** Information $H \ge \log_2 N$ provided.
