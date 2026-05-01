# AOC Ownership Nonunitary Candidate Patch Report

## 0. Patch Metadata
- task id: AOC_OWNERSHIP_NONUNITARY_CANDIDATE_PATCH
- mode: curatorial compression with DCP-I safeguards
- files edited:
  - labs/appearance_ownership_continuity/core/CLAIM_LEDGER.yaml
  - labs/appearance_ownership_continuity/core/reports/AOC_OWNERSHIP_NONUNITARY_CANDIDATE_PATCH.md
- files intentionally not edited:
  - labs/appearance_ownership_continuity/core/TEST_REGISTRY.yaml
  - theory files
  - unrelated claims in CLAIM_LEDGER.yaml
- source reports read:
  - labs/appearance_ownership_continuity/core/reports/AOC_A2_AGENCY_AUTHORSHIP_DISSOCIATION.md
  - labs/appearance_ownership_continuity/core/reports/AOC_A2_RUBBER_HAND_MEASURE_DISSOCIATION.md
  - labs/appearance_ownership_continuity/core/reports/AOC_A2_DEPERSONALIZATION_MINENESS_PRESSURE.md
  - labs/appearance_ownership_continuity/core/reports/AOC_A2_OWNERSHIP_NONUNITARY_LEVEL2_DESIGN.md
  - labs/appearance_ownership_continuity/core/reports/AOC_A2_OWNERSHIP_NONUNITARY_RETEST.md
  - labs/appearance_ownership_continuity/core/reports/AOC_MINIMAL_SELF_LEVEL2_PATHFINDER.md
  - labs/appearance_ownership_continuity/core/reports/AOC_MINIMAL_SELF_VS_SELF_MODEL_MATRIX.md
  - labs/appearance_ownership_continuity/core/reports/AOC_MINIMAL_SELF_OPERATIONALIZATION.md
- validation commands run:
  - git status --short
  - YAML parse check for CLAIM_LEDGER.yaml
  - existing AOC/core validation
  - forbidden phrase scan in CLAIM_LEDGER.yaml and patch report

## 1. Patch Purpose
`OWNERSHIP_NONUNITARY` is being added only as a provisional candidate because the three-family threshold has been met. This patch does not promote the claim to canon and does not treat ownership nonunitarity as proof of minimal self or A0.

## 2. Claim Added
- id: OWNERSHIP_NONUNITARY
- claim text: "Ownership appears partially nonunitary under dissociation pressure: body ownership, agency/authorship, self-modeling, reportable ownership judgment, and thin mineness may vary semi-independently."
- status: provisional
- type: operational
- promotion_state: report_level_not_canon
- human_review_required: true
- rationale: "Three independent pressure families separate ownership channels in different ways: depersonalization/derealization preserves report and perception while altering mineness and self-world intimacy; rubber-hand/body-illusion cases separate ownership judgment from proprioceptive and body-position measures; agency/authorship dissociation separates action authorship and control from ownership texture."
- falsifier: "The apparent dissociations reduce cleanly to a single dominant channel such as self-model disturbance, body-model/embodiment remapping, agency/control disruption, report artifact, or valence/arousal, with no semi-independent ownership structure remaining across case families."
- depends_on: [OWNERSHIP_NOT_REPORT, SELF_MODEL_NOT_A, AGENCY_NOT_OWNERSHIP, FIELD_NOT_OWNER, PROXY_REJECTION_NOT_EXPLANATION]
- relevant_tests: [A_SPLIT_A2_OWNERSHIP_ABSENT, AOC_MINIMAL_SELF_OPERATIONALIZATION, AOC_MINIMAL_SELF_VS_SELF_MODEL_MATRIX, AOC_MINIMAL_SELF_LEVEL2_PATHFINDER, AOC_A2_OWNERSHIP_NONUNITARY_RETEST, AOC_A2_OWNERSHIP_NONUNITARY_LEVEL2_DESIGN, AOC_A2_DEPERSONALIZATION_MINENESS_PRESSURE, AOC_A2_RUBBER_HAND_MEASURE_DISSOCIATION, AOC_A2_AGENCY_AUTHORSHIP_DISSOCIATION]
- relevant_theories: [minimal_self, self_model_theory, embodied_enactive, predictive_processing, valence_stakes, no_bridge_restraint]
- notes: "Pressure-supported candidate, not a mechanism. Thin mineness remains underoperationalized. Supports ownership-layer decomposition, not A0 closure."

## 3. Evidence Basis

### Depersonalization / Derealization
- what it pressures: report-preserved but ownership-altered experience, self-world intimacy, affective estrangement, and thin mineness.
- what it supports: ownership texture can change while perception and report persist.
- what it cannot prove: minimal self, ownership nonunitarity as mechanism, or A0 closure.

### Rubber-Hand / Body-Illusion Dissociation
- what it pressures: ownership judgment versus proprioceptive/body-position measures, plus local limb ownership versus global ownership.
- what it supports: ownership is not a single unified measure; drift and ownership can split.
- what it cannot prove: thin mineness, A0, or a complete embodiment explanation.

### Agency / Authorship Dissociation
- what it pressures: action authorship, motor control, report, and ownership texture.
- what it supports: agency/control and ownership can fracture apart, and body ownership can persist when authorship is disturbed.
- what it cannot prove: that agency loss is minimal self loss, or that agency disruption alone explains ownership.

## 4. Why This Is Not Canon
- thin mineness is still underoperationalized
- the dissociation map is not a mechanism
- proxy rejection is not explanation
- A2 progress is not A0 closure
- rival theories remain live

## 5. Claims Intentionally Not Added
- MINIMAL_SELF_SOLVES_A0
- DEPERSONALIZATION_PROVES_MINIMAL_SELF
- RUBBER_HAND_PROVES_OWNERSHIP_NONUNITARY
- AGENCY_LOSS_PROVES_MINIMAL_SELF
- OWNERSHIP_NONUNITARY_SOLVES_A0

## 6. Validation Output
Validation output:
```text
git status --short
 M labs/appearance_ownership_continuity/README.md
 M labs/appearance_ownership_continuity/core/A_SPLIT.md
 M labs/appearance_ownership_continuity/core/CLAIM_LEDGER.yaml
 M labs/appearance_ownership_continuity/core/README.md
 M labs/appearance_ownership_continuity/core/reports/README.md
 M labs/appearance_ownership_continuity/research/README.md
 M labs/appearance_ownership_continuity/research/ROADMAP.md
?? labs/appearance_ownership_continuity/core/reports/AOC_A0_BRIDGE_DISCRIMINATION_MATRIX.md
?? labs/appearance_ownership_continuity/core/reports/AOC_A2_AGENCY_AUTHORSHIP_DISSOCIATION.md
?? labs/appearance_ownership_continuity/core/reports/AOC_A2_DEPERSONALIZATION_MINENESS_PRESSURE.md
?? labs/appearance_ownership_continuity/core/reports/AOC_A2_OWNERSHIP_NONUNITARY_LEVEL2_DESIGN.md
?? labs/appearance_ownership_continuity/core/reports/AOC_A2_OWNERSHIP_NONUNITARY_RETEST.md
?? labs/appearance_ownership_continuity/core/reports/AOC_A2_RUBBER_HAND_MEASURE_DISSOCIATION.md
?? labs/appearance_ownership_continuity/core/reports/AOC_BRIDGE_CANDIDATE_SCORECARD.md
?? labs/appearance_ownership_continuity/core/reports/AOC_CLAIM_LEDGER_PATCH_REPORT.md
?? labs/appearance_ownership_continuity/core/reports/AOC_CLAIM_LEDGER_TRIAGE.md
?? labs/appearance_ownership_continuity/core/reports/AOC_IIT_BRIDGE_PRESSURE.md
?? labs/appearance_ownership_continuity/core/reports/AOC_MINIMAL_SELF_LEVEL2_PATHFINDER.md
?? labs/appearance_ownership_continuity/core/reports/AOC_MINIMAL_SELF_OPERATIONALIZATION.md
?? labs/appearance_ownership_continuity/core/reports/AOC_MINIMAL_SELF_VS_SELF_MODEL_MATRIX.md
?? labs/appearance_ownership_continuity/core/reports/AOC_OWNERSHIP_NONUNITARY_CANDIDATE_PATCH.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A0_HARD_GAP_AUDIT.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A3_FLOW_FALSE_POSITIVE_BATTERY.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A3_TEMPORAL_FLOW_MINIMAL_SELF.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_BRANCHING_IDENTITY.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_MEMORY_RESIDUE_NOT_CONTINUITY.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_SLEEP_REENTRY_OWNER.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_UPLOAD_COPY_NEGATIVE_CONTROL.md
---
5486
---
yaml_parse_ok True
---
Appearance–Ownership–Continuity core check passed (0 warning(s)).
---
Helix workspace check passed (0 warning(s)).
```

## 7. Main Finding
The ledger now contains `OWNERSHIP_NONUNITARY` as a provisional, human-review-required candidate claim. This formalizes a multi-family pressure result without promoting it to canon or mechanism.

## 8. Next Recommended Task
- AOC_VALENCE_STAKES_BRIDGE_PRESSURE
