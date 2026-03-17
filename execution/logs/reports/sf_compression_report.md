## HISTORICAL_RESULT
(Warning: Unverified Numeric Claims)

# SF Compression Report
**Instrument State:** IRREDUCIBLE

## 1. Objective
A formal attempt was made to reduce the 4-dimensional Stabilization Feasibility overlay (SF1–SF4) into a 2-dimensional model comprising:
- **T (Temporal Dominance)**: Fusion of Latency and Time Constants.
- **A (Control Accessibility)**: Fusion of Observability and Enforcement.

## 2. Comparison Metrics
A regression test was performed against 7 validated intervention domains to measure classification agreement between the 4D plurality and the 2D compressed model.

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| **Classification Agreement** | 57.14% | ≥ 90.0% | **FAIL** |
| **False Positive Delta** | 0.0% | ≤ 10.0% | PASS |
| **Information Retention** | Low | High | **FAIL** |

## 3. Analysis of Failure
The 2D model failed to distinguish between **PARTIALLY_ATTACHABLE** and **NON_ATTACHABLE** states in 42.8% of cases. 
- **Decoupling**: SF1 (Latency) and SF4 (Time Constant) represent different physical failure modes. A system can have high controller speed (SF4) but fatal feedback delay (SF1). Collapsing them into `T` leads to catastrophic misclassification of "ghost stabilizers."
- **Observability vs Enforcement**: A state being "GLOBAL" (SF2) but requiring "CENTRAL" authority (SF3) creates a unique coordination friction that a binary "Accessibility" `A` bit cannot capture.

## 4. Orthogonality Check
Independence tests confirm that while SF1 and SF4 both deal with time, their impact on the stability basin is orthogonal. One bounds the *start* of the intervention, the other bounds the *sustained control* of the disturbance.

## 5. Final Verdict
**SF_IRREDUCIBLE**

The Stabilization Feasibility overlay must retain its 4-dimensional plurality. The attempt to compress into 2 primitives results in unacceptable predictive loss.

**Action:** Maintain SF1–SF4 as the canonical feasibility coordinates.
