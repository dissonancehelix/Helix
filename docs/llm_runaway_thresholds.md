# LLM Runaway Thresholds
**Helix CE-OS Stability Audit**

## 1. The B4 Inflation Threshold
Helix identifies a critical runaway point where the **Symbolic Depth (B4)** of the model outruns the **Coordination Capacity (B3)** of the attention layers to synchronize them.

- **Detected Threshold:** **B4 = 27** (Relative scale factor).
- **Mechanism:** Beyond this depth, gradient signal-to-noise ratio (SNR) drops exponentially. The increase in referential logic (B4) is no longer balanced by multi-head coordination (B3).
- **Outcome:** **Symbolic Runaway**. The model generates high-depth logic that is no longer grounded in the training manifold's B1 basins.

## 2. Emergent Capability Jumps
Helix predicts that "emergence" is not a phase change in intelligence, but a **Topological Re-routing**. 
When B2 expression capacity is sufficiently high, the system finds a "wormhole" between previously disconnected B1 basins, allowing for a sudden leap in predictive accuracy (B3 synchronization across distant manifold domains).

## 3. Critical Ratio
**Stability Rule:** B4 / B3_capacity MUST BE < 1.0.
If the ratio exceeds 1.0, the model enters a **Delusional State** (high internal coherence, zero external grounding).
