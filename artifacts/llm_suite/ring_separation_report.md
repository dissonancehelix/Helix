# Ring Separation Report
**Regime:** Substrate-Level Controls vs. Behavioral Wrappers

## 1. Ring-0 Controls (Substrate Mathematics)
Interventions that directly manipulate the **B1-B4 manifold** during the training update cycle (`RING 0`).

| Intervention | Mechanism | Attachment | Stability Effect |
|--------------|-----------|------------|------------------|
| **Adam Optimizer** | Momentum/Variance bias correction | **ROBUST** | Maintains local basin commitment (B1). |
| **Gradient Clipping** | Threshold-based norm bounding | **PHYSICAL** | Prevents B2_EXPRESSION blowup (NaNs). |
| **LayerNorm** | Distributional shifting | **IMMUTABLE** | Prevents B3_COORDINATION collapse. |
| **Weight Decay** | Regularization penalty | **ATTACHED** | Prevents overfitting (B1-B4 rigidity). |

## 2. Ring-3 Controls (Behavioral / Symbolic Wrappers)
Interventions that rely on **B4 symbolic depth** manipulation post-training or in the sampling phase (`RING 3`).

| Intervention | Mechanism | Attachment | Stability Effect |
|--------------|-----------|------------|------------------|
| **Prompt Engineering** | Contextual instruction injection | **DETACHABLE** | Does not modify B1-B2 manifold structure. |
| **Output Filters** | String-matching / Classification | **LAYERED** | Blocks symptoms of collapse (Mode Collapse) but does not prevent it. |
| **Instruction Tuning**| Fine-tuning dataset biasing | **PARTIAL** | Shift in B1 basins but easily re-routed by new context (Leaky). |

## 3. Analysis
Helix establishes a clear boundary between **Stable Structural Intervention** (Ring-0) and **Meta-Instructional Intervention** (Ring-3). 

Ring-0 interventions satisfy **SF1-SF4** with maximum margins (SF4 >> 1.0). 
Ring-3 interventions are **Detachable**; they act as a "Babel-layer" (ECC/Parity) that can be stripped from the model without destroying the underlying structural bases.

**Verdict: RING SEPARATION PROVEN.**
Substrate controls prevent **NaN COLLAPSE**; Behavioral controls prevent **SOCIAL COLLAPSE**. They are incompensatable.
