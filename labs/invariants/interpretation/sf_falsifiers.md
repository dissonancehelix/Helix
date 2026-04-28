## HISTORICAL_RESULT
(Warning: Unverified Numeric Claims)

# SF Overlay Falsifiers
**Helix CE-OS Falsification Suite**

## Falsification of Attachability
The SF coordinates are invalidated if any of the following occur:

1. **SF1 False Negative:** An intervention with SF1 > 1.0 (delayed feedback) successfully stabilizes a runaway system in a controlled physical trial.
2. **SF4 False Positive:** An intervention with SF4 > 1.0 (fast controller) fails to damp a disturbance despite perfect observability (SF2) and protocol-level enforcement (SF3).
3. **Ghost Stabilization:** A system is stabilized by a factor that remains "UNOBSERVABLE" (SF2) across ≥ 3 measurement layers, indicating a hidden structural basis exists that Helix has not yet mapped.

## Promotion Blockers
- Any stabilizer failing SF1 or SF4 is permanently barred from promotion to the **Intervention Registry**.
- Any stabilizer requiring "CENTRAL" enforcement (SF3) without a defined "GOVERNANCE_DOMAIN" is marked as **STRUCTURALLY_CORRECT_BUT_STATIC**.
