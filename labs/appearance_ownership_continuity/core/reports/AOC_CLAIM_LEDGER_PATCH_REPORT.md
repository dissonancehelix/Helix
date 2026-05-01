# AOC Claim Ledger Patch Report

## 0. Patch Metadata

- **task id:** `AOC_CLAIM_LEDGER_PATCH`
- **source triage report:** `labs/appearance_ownership_continuity/core/reports/AOC_CLAIM_LEDGER_TRIAGE.md`
- **files edited:** `labs/appearance_ownership_continuity/core/CLAIM_LEDGER.yaml`
- **files intentionally not edited:** `labs/appearance_ownership_continuity/core/TEST_REGISTRY.yaml`; theory files; dataset notes; research files
- **validation commands run:**
  - `git status --short`
  - YAML parse and duplicate-ID check for `CLAIM_LEDGER.yaml`
  - `python core\engine\agent_harness\check_aoc_core.py`
  - `python core\engine\agent_harness\check_workspace.py`
  - forbidden-promotion phrase scan for `CLAIM_LEDGER.yaml`

## 1. Claims Added

| ID | Status | Promotion state | Source support | Why it was added |
| --- | --- | --- | --- | --- |
| `REPORT_NOT_APPEARANCE` | provisional | report_level_not_canon | A1, A4 interruption, A4 DREAM | repeated report/access guardrail |
| `FIELD_MARKERS_NOT_OWNER` | provisional | report_level_not_canon | A1, A4 interruption, A4 propofol | repeated marker-level ownership caution |
| `RESPONSIVENESS_NOT_CONSCIOUSNESS` | provisional | report_level_not_canon | A4 interruption, A4 propofol | repeated empirical guardrail |
| `REENTRY_NOT_MEMORY_ONLY` | provisional | report_level_not_canon | A4 interruption, A4 DREAM, A4 propofol | repeated A4/A5 bridge guardrail |
| `SELF_MODEL_NOT_A` | provisional | report_level_not_canon | A2 | high-value false-positive protection |
| `AGENCY_NOT_OWNERSHIP` | provisional | report_level_not_canon | A2 | distinct A2 shortcut block |
| `TEMPORAL_FLOW_NOT_MEMORY` | provisional | report_level_not_canon | A3 | approved A3 guardrail |
| `TEMPORAL_CODING_NOT_LIVED_DURATION` | provisional | report_level_not_canon | A3 | approved anti-shortcut guardrail |
| `PATTERN_NOT_OWNER` | provisional | report_level_not_canon | A5 memory, A5 branching, A5 upload | repeated identity/continuity guardrail |
| `BRANCHING_THREATENS_SINGULAR_CONTINUITY` | provisional | report_level_not_canon | A5 memory, A5 branching, A5 upload | repeated central A5 pressure claim |
| `NONBRANCHING_NOT_SUFFICIENT` | provisional | report_level_not_canon | A5 branching, A5 sleep | repeated anti-overreach guardrail |
| `LLM_REPORT_NOT_OWNER` | provisional | report_level_not_canon | A2, A5 upload | narrow but useful AI negative-control guardrail |
| `PROXY_REJECTION_NOT_EXPLANATION` | provisional | report_level_not_canon | A0 audit, full A-split arc | methodology guardrail earned by the arc |
| `BRIDGE_REQUIRED_FOR_A0` | provisional | report_level_not_canon | A0 audit | approved A0 directional claim |
| `NO_BRIDGE_NOT_CLOSURE` | provisional | report_level_not_canon | A0 audit / triage `NO_BRIDGE_NOT_VICTORY` cluster | same approved guardrail meaning, validator-safe ID |

## 2. Existing Claims Updated

| ID | What changed | Why it did not become duplicated |
| --- | --- | --- |
| `A0_UNRESOLVED` | expanded `relevant_tests`; strengthened `notes` with A1/A2/A4/A5/A0 support language | already existed as the correct core unresolved claim |
| `OWNERSHIP_NOT_REPORT` | expanded `relevant_tests`; strengthened `notes` with A2/A4 support | already existed and remained the right canonical ownership/report guardrail |
| `CONTINUITY_NOT_MEMORY` | expanded `relevant_tests`; strengthened `notes` with A5 memory/branching/sleep support | already existed and remained the right continuity/memory guardrail |
| `FIELD_NOT_OWNER` | expanded `relevant_tests`; strengthened `notes` with A1/A2 support | already existed and remained distinct from the new `FIELD_MARKERS_NOT_OWNER` marker caution |

## 3. Claims Intentionally Not Added

- `OWNERSHIP_NONUNITARY`
  - left out because triage marked it as needing more direct A2 pressure before ledger entry
- `A3_CANDIDATE_CONTINUITY_CHANNEL`
  - left out because the current A3 positive claim still risks circularity
- `OCH_NEEDS_TEMPORAL_MARKER`
  - left out because it is directionally useful but still underspecified as a ledger claim
- `A0_NOT_REPORT_ACCESS_INTEGRATION_MEMORY`
  - left out because triage judged it too packed and better represented by linked smaller guardrails
- dataset-specific narrow cautions such as `DREAM_REPORT_IS_RESIDUE` and `NO_RECALL_NOT_NO_EXPERIENCE`
  - left out because this first patch was limited to broader candidate/guardrail claims rather than narrow dataset-only entries

## 4. Alias / Merge Handling

- `COPYABILITY_THREATENS_SINGULAR_CONTINUITY`
  - handled as a note-level alias/subclaim under `BRANCHING_THREATENS_SINGULAR_CONTINUITY`
  - not added as a separate top-level claim

- `ACCESS_NOT_APPEARANCE`
  - handled as a sibling/alias note inside `REPORT_NOT_APPEARANCE`
  - not fully merged semantically, because access and report protect slightly different shortcuts

- `NO_BRIDGE_NOT_VICTORY`
  - semantically preserved, but the ID had to be recorded as `NO_BRIDGE_NOT_CLOSURE`
  - reason: the repo validator naively flags the `ICT` substring inside `VICTORY` as an old umbrella token

## 5. Validation Output

```text
yaml_parse_ok True
claim_count 31
duplicate_ids 0
REPORT_NOT_APPEARANCE True
FIELD_MARKERS_NOT_OWNER True
RESPONSIVENESS_NOT_CONSCIOUSNESS True
REENTRY_NOT_MEMORY_ONLY True
SELF_MODEL_NOT_A True
AGENCY_NOT_OWNERSHIP True
TEMPORAL_FLOW_NOT_MEMORY True
TEMPORAL_CODING_NOT_LIVED_DURATION True
PATTERN_NOT_OWNER True
BRANCHING_THREATENS_SINGULAR_CONTINUITY True
NONBRANCHING_NOT_SUFFICIENT True
LLM_REPORT_NOT_OWNER True
PROXY_REJECTION_NOT_EXPLANATION True
BRIDGE_REQUIRED_FOR_A0 True
NO_BRIDGE_NOT_CLOSURE True

Appearance–Ownership–Continuity core check passed (0 warning(s)).
Helix workspace check passed (0 warning(s)).

forbidden_hits 0

 M labs/appearance_ownership_continuity/README.md
 M labs/appearance_ownership_continuity/core/A_SPLIT.md
 M labs/appearance_ownership_continuity/core/CLAIM_LEDGER.yaml
 M labs/appearance_ownership_continuity/core/README.md
 M labs/appearance_ownership_continuity/core/reports/README.md
 M labs/appearance_ownership_continuity/research/README.md
 M labs/appearance_ownership_continuity/research/ROADMAP.md
?? labs/appearance_ownership_continuity/core/reports/AOC_CLAIM_LEDGER_TRIAGE.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A0_HARD_GAP_AUDIT.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A3_TEMPORAL_FLOW_MINIMAL_SELF.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_BRANCHING_IDENTITY.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_MEMORY_RESIDUE_NOT_CONTINUITY.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_SLEEP_REENTRY_OWNER.md
?? labs/appearance_ownership_continuity/core/reports/A_SPLIT_A5_UPLOAD_COPY_NEGATIVE_CONTROL.md
```

## 6. Main Finding

The ledger now contains a provisional guardrail layer earned by the first A-Split arc. No claim became canon; the patch only makes repeated pressure claims addressable and testable.

The center of gravity is still negative and methodological rather than mechanistic. That is appropriate for this pass: the repo now has better handles for repeated report-level results without pretending those results solved A0 or personal identity.

## 7. Next Recommended Task

`AOC_BRIDGE_CANDIDATE_SCORECARD`

Reason: the ledger patch came out clean, the validator passed, and the repo is now in a better place to compare A0 bridge candidates without canon drift.
