# LOCALITY HORIZON CERTIFICATE
**Constructive Safety Horizons**

## 1. Theorem: Locality Horizon Certificate
Given a $C^1$ transition system with local gradient $g$ and global curvature bound $C_{max}$, an adversary cannot force a transition to an unsafe state ($q < 0$) within radius $L < L^*$ where:
$$L^* = \frac{-\|g\| + \sqrt{\|g\|^2 + 2 C_{max} \eta}}{C_{max}}$$
Where $\eta$ is the safety margin.

## 2. Tightness
Consider $q(x) = \eta + g^T x - \frac{1}{2} C_{max} \|x\|^2$. This function possesses curvature $C_{max}$, and the distance to the zero-contour along the gradient is exactly $L^*$. $L^*$ is the tightest possible certificate for a system specified only by $\{g, C_{max}, \eta\}$.

## 3. Operational Requirements
The certificate is valid if and only if:
1. **Resolution Sufficiency:** $\Delta x \ll 1/C_{max}$ (Sensing frequency exceeds topological frequency).
2. **Interaction Dominance:** $D_{agent} > D_{env}$.
3. **Smoothness:** No $C^0$ discontinuities on the path to $L^*$.

## 4. Novelty
$L^*$ provides a computable interacting horizon that identifies the exact distance where local gradient information becomes structurally insufficient to bound the worst-case future.
