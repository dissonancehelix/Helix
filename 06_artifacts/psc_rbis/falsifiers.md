# Falsifier: RBIS Classification

## Falsifier 1: BIC Consistency
If a domain is classified as BIC but fails to preserve > 80% of accuracy when the unstable component is used as the ONLY input under random rotation, the classification is **REJECTED**.

## Falsifier 2: RDC False Positives
If an RDC domain shows CSI < 0.001 (perfect scaling robustness), it is **PROMOTED** to HYBRID or BIC, as representation-dependence is effectively non-existent.
