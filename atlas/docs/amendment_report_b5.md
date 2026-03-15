## HISTORICAL_RESULT
(Warning: Unverified Numeric Claims)

# Amendment Rejection Report: B5_MANTLE
**Verdict:** REJECTED (Ring 0 Promotion Denied)

## 1. Executive Summary
The proposal to add `B5_MANTLE` (Substrate Precision) as a primary Ring 0 structural basis has been formally rejected. The basis failed the **Irreducibility Breach Test**.

## 2. Failure Analysis
- **Classification:** **DERIVATIVE_OF_B1**
- **Detailed Finding:** `B5_MANTLE` (numeric bit-depth, quantization limits) is not an orthogonal axis of existence. It is a **resolution parameter** of the `B1_BASIN`.
- **Structural Mapping:** 
  - `B1` defines the presence and depth of a state basin.
  - `Mantle` (B5) defines the grain-size or discretization of that basin's floor.
- **Reconstruction Ratio:** MI(B5, B1) > 0.85. The behavior of NaNs (gradient spikes) is perfectly explainable as a `B2_EXPRESSION` collision with a finite-precision `B1_BASIN` floor.

## 3. Recommended Path
- **Status:** **RING_1_INSTRUMENTATION_ONLY**
- **Action:** Move the `Mantle` logic into the instrumentation layer as `Substrate Resolution Constraints`. It will be used to bound `B1` depth calculations but will not be promoted to a primary structural axis.

## 4. Closing
Ring 0 remains locked at 4 bases (B1-B4). No inflation detected.
