# Profile Theory Lab

`labs/profile_theory/` turns `DISSONANCE.md` into a prediction engine.

This lab is not canon. It tests whether profile claims predict future evidence
better than weaker explanations such as generic complexity preference,
nostalgia, completionism, or novelty seeking.

## Method

Each claim must record:

- claim
- mechanism
- predictions
- positive evidence
- negative controls
- blocking gates
- falsifier
- status
- update rule

Rules:

- Do not treat a pattern as global unless it has at least three independent
  evidence doors.
- Every claim needs negative controls.
- Every false positive must produce either a blocking gate or a revision.
- Preserve uncertainty.
- Do not overhype.

## Files

- `CLAIMS.md` — active testable claims.
- `EVIDENCE_LEDGER.md` — compact evidence index and controls.
- `runs/2026-04-28.md` — first run: Resolution-Increasing Depth versus
  "likes complexity."
