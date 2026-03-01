# SCARCITY GAP PROOF
**Query Complexity of Environment Family $E_N$**

## 1. Proposition
For a class of environments $E_N$ with $N$ possible branching paths, identifying a safe corridor requires $O(\log_2 N)$ bits of information, but **guaranteeing survival** in the presence of absorbing sinks requires linear interaction depth $D \sim \Omega(N)$.

## 2. Environment Family $E_N$
- **Setup:** $N$ corridors. $N-1$ corridors contain an irreversible sink $C$ at depth $d+1$. Exactly one corridor $c^*$ is safe.
- **Prefix:** $\forall c \in E_N, t \le d \implies$ observation transcripts are identical.
- **Goal:** Identify $c^*$ without entering $C$.

## 3. Deterministic Bound
- **Adversary:** For any agent $A$ performing $k < N-1$ queries, the adversary assigns $c^*$ to an unqueried branch.
- **Lower Bound:** $D^* \ge N-1$.

## 4. Randomized Bound ($1-\delta$ Success)
- **Adversary:** Selects $c^*$ uniformly at random.
- **Success Condition:** Termination in $c^*$ with probability $\ge 1-\delta$.
- **Lower Bound:** The agent must query $\Omega(N \log 1/\delta)$ paths to suppress the probability of hitting an absorbing sink before finding the exit.

## 5. Conclusion
Interaction cost is exponentially higher than informational cost in irreversible systems. The "Bits vs Work" gap diverges linearly with $N$.
