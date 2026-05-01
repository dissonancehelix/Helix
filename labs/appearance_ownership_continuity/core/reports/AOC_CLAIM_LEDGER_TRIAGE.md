# AOC Claim Ledger Triage

## 0. Triage Metadata

- **task id:** `AOC_CLAIM_LEDGER_TRIAGE`
- **mode:** curatorial compression with DCP-I safeguards
- **status:** triage report, not canon
- **source reports read:** `A_SPLIT_A1_COGITATE_FIELD_ACCESS.md`; `A_SPLIT_A2_OWNERSHIP_ABSENT.md`; `A_SPLIT_A3_TEMPORAL_FLOW_MINIMAL_SELF.md`; `A_SPLIT_A4_INTERRUPTION_REENTRY.md`; `A_SPLIT_A4_DREAM_REENTRY_METADATA.md`; `A_SPLIT_A4_PROPOFOL_DERIVATIVE_TIMELINE.md`; `A_SPLIT_A5_MEMORY_RESIDUE_NOT_CONTINUITY.md`; `A_SPLIT_A5_BRANCHING_IDENTITY.md`; `A_SPLIT_A5_SLEEP_REENTRY_OWNER.md`; `A_SPLIT_A5_UPLOAD_COPY_NEGATIVE_CONTROL.md`; `A_SPLIT_A0_HARD_GAP_AUDIT.md`
- **ledgers inspected:** `labs/appearance_ownership_continuity/core/CLAIM_LEDGER.yaml`; `labs/appearance_ownership_continuity/core/TEST_REGISTRY.yaml`
- **files intentionally not edited:** `CLAIM_LEDGER.yaml`; `TEST_REGISTRY.yaml`; theory files

## 1. Purpose

The first A-Split report arc repeatedly recommended candidate claims, but those recommendations remain scattered across report endings. This triage report consolidates them, groups duplicates, identifies tensions, assigns maturity labels, and recommends ledger actions without automatically promoting anything into canon.

The governing rule here is subtractive but careful: merge true duplicates, keep meaningfully distinct false-positive protections separate, and do not let repeated wording harden into theory just because it has been said often.

## 2. Current Claim Ledger Snapshot

Current `CLAIM_LEDGER.yaml` snapshot:

- top-level schema fields: `version`, `status`, `parent_theory`, `scope`, `owner_location`, `promotion_state`, `claims`
- each claim currently uses at least: `id`, `claim`, `status`, `type`, `owner_location`, `promotion_state`
- most claims also include: `depends_on`, `strengthens_if`, `weakens_if`, `relevant_tests`, `relevant_theories`, `notes`
- newer A-Split harness claims additionally use: `owner`, `rationale`, `falsifier`

Current claim ID families:

- `OCH-C001` through `OCH-C011`
- `A_SPLIT_REQUIRED`
- `A0_UNRESOLVED`
- `OWNERSHIP_NOT_REPORT`
- `CONTINUITY_NOT_MEMORY`
- `FIELD_NOT_OWNER`

Current statuses present:

- `anchored`
- `plausible`
- `open`
- `provisional`

Schema constraints and cautions:

- no claim should be marked as closed or final
- newer entries should preserve existing mixed-schema tolerance rather than forcing a full ledger rewrite in this pass
- the ledger already tolerates both `owner_location` alone and `owner` plus `owner_location`
- no missing `status` field was found in current claims

## 3. Claim Extraction Table

| Source report | Claim ID / phrase | Layer | Recommendation type | Near-exact wording | Notes |
| --- | --- | --- | --- | --- | --- |
| A1 | `A1_FIELD_NOT_ACCESS` | A1 | candidate | A1 field is not access | Narrow A1 guardrail |
| A1 | `CONTENT_MARKER_NOT_APPEARANCE` | A1 | candidate | content marker is not appearance | Protects decoding/sustained-activity shortcut |
| A1 | `ACCESS_NOT_APPEARANCE` | A1/A0 | strengthened | access is not appearance | Overlaps A0 proxy block |
| A1 | `REPORT_NOT_APPEARANCE` | A1/A0 | strengthened | report is not appearance | Repeats across A4 |
| A1 | `FIELD_MARKERS_NOT_OWNER` | A1/A2 | strengthened | field markers are not owner | Distinct from field-not-owner |
| A1 | `A0_UNRESOLVED` | A0 | strengthened | A0 remains unresolved | Repeats widely |
| A1 | `THEORY_SUPPORT_NOT_AOC_CONFIRMATION` | meta | candidate | theory support is not AOC confirmation | Repo hygiene guardrail |
| A2 | `OWNERSHIP_NOT_REPORT` | A2 | strengthened | ownership is not report | Already in ledger |
| A2 | `FIELD_NOT_OWNER` | A1/A2 | strengthened | field is not owner | Already in ledger |
| A2 | `A0_UNRESOLVED` | A0 | strengthened | A0 remains unresolved | Repeats widely |
| A2 | `SELF_MODEL_NOT_A` | A2/A0 | candidate | self-model is not A | Important false-positive block |
| A2 | `AGENCY_NOT_OWNERSHIP` | A2 | candidate | agency is not ownership | Distinct from report guardrail |
| A2 | `OWNERSHIP_NONUNITARY` | A2 | candidate | ownership is nonunitary | Structural claim, not just guardrail |
| A3 | `TEMPORAL_FLOW_NOT_MEMORY` | A3/A5 | candidate | temporal flow is not memory | Narrow A3 guardrail |
| A3 | `TEMPORAL_CODING_NOT_LIVED_DURATION` | A3 | candidate | temporal coding is not lived duration | Important anti-shortcut claim |
| A3 | `FLOW_NOT_NO_SELF` | A3/A2 | candidate | flow is not no-self | False-positive guardrail |
| A3 | `MINIMAL_SELF_NOT_A0` | A3/A0 | candidate | minimal self is not A0 | Prevents smuggled solution |
| A3 | `A3_CANDIDATE_CONTINUITY_CHANNEL` | A3/A5 | candidate | A3 is a continuity candidate | Positive but guarded |
| A3 | `OCH_NEEDS_TEMPORAL_MARKER` | A3/A5 | candidate | OCH needs a temporal marker | High circularity risk |
| A4 interruption | `A0_UNRESOLVED` | A0 | strengthened | A0 unresolved | Repeats widely |
| A4 interruption | `OWNERSHIP_NOT_REPORT` | A2/A4 | constrained / strengthened | ownership is not report | Already in ledger |
| A4 interruption | `REPORT_NOT_APPEARANCE` | A4/A0 | candidate | report is not appearance | Strong repeated cluster |
| A4 interruption | `RESPONSIVENESS_NOT_CONSCIOUSNESS` | A4 | candidate | responsiveness is not consciousness | Strong empirical/negative-control guardrail |
| A4 interruption | `REENTRY_NOT_MEMORY_ONLY` | A4/A5 | candidate | re-entry is not memory only | Bridges A4 and A5 |
| A4 interruption | `FIELD_MARKERS_NOT_OWNER` | A1/A2/A4 | candidate | field markers are not owner | Repeats A1 form |
| A4 DREAM | `REPORT_NOT_APPEARANCE` | A4/A0 | candidate / strengthened | report is not appearance | Repeats |
| A4 DREAM | `REENTRY_NOT_MEMORY_ONLY` | A4/A5 | constrained | re-entry not memory only | Supports but does not close |
| A4 DREAM | `A0_UNRESOLVED` | A0 | strengthened | A0 unresolved | Repeats |
| A4 DREAM | `OWNERSHIP_NOT_REPORT` | A2/A4 | indirectly strengthened | ownership not report | Repeats |
| A4 DREAM | `DREAM_REPORT_IS_RESIDUE` | A4 | candidate | dream report is residue | Narrow dataset-specific guardrail |
| A4 DREAM | `NO_RECALL_NOT_NO_EXPERIENCE` | A4 | candidate | no recall is not no experience | Narrow dataset-specific guardrail |
| A4 propofol | `RESPONSIVENESS_NOT_CONSCIOUSNESS` | A4 | candidate / strengthened | responsiveness is not consciousness | Repeats |
| A4 propofol | `REENTRY_NOT_MEMORY_ONLY` | A4/A5 | candidate | re-entry is not memory only | Repeats |
| A4 propofol | `REPORT_NOT_APPEARANCE` | A4/A0 | candidate | report is not appearance | Repeats |
| A4 propofol | `FIELD_MARKERS_NOT_OWNER` | A1/A2/A4 | candidate | field markers are not owner | Repeats |
| A5 memory | `CONTINUITY_NOT_MEMORY` | A5 | strengthened | continuity is not memory | Already in ledger |
| A5 memory | `REPORT_RESIDUE_NOT_CONTINUITY` | A5/A4 | candidate | report residue is not continuity | Strong repeated cluster |
| A5 memory | `PATTERN_NOT_OWNER` | A5 | candidate | pattern is not owner | Strong repeated cluster |
| A5 memory | `BRANCHING_THREATENS_SINGULAR_CONTINUITY` | A5 | strengthened | branching threatens singular continuity | Strong repeated cluster |
| A5 memory | `OCH_REQUIRES_NONBRANCHING_OWNED_STREAM` | A5 | candidate | OCH requires non-branching owned stream | High circularity risk |
| A5 memory | `A0_UNRESOLVED` | A0 | indirectly strengthened | A0 unresolved | Repeats |
| A5 branching | `BRANCHING_THREATENS_SINGULAR_CONTINUITY` | A5 | strengthened | branching threatens singular continuity | Repeats |
| A5 branching | `PATTERN_NOT_OWNER` | A5 | candidate | pattern is not owner | Repeats |
| A5 branching | `CONTINUITY_NOT_MEMORY` | A5 | strengthened | continuity not memory | Repeats |
| A5 branching | `OCH_REQUIRES_NONBRANCHING_OWNED_STREAM` | A5 | candidate | OCH requires non-branching owned stream | Repeats |
| A5 branching | `NONBRANCHING_NOT_SUFFICIENT` | A5 | candidate | non-branching is not sufficient | Important counter-guardrail |
| A5 branching | `SUCCESSOR_SYMMETRY_UNRESOLVED` | A5 | candidate | successor symmetry unresolved | Distinct branch-specific tension |
| A5 sleep | `REENTRY_STRONGER_THAN_COPYING` | A5/A4 | candidate | re-entry stronger than copying | Useful but narrow |
| A5 sleep | `NONBRANCHING_NOT_SUFFICIENT` | A5 | strengthened | non-branching not sufficient | Repeats |
| A5 sleep | `BIOLOGICAL_CONTINUITY_NOT_OWNER_PROOF` | A5 | candidate | biological continuity not owner proof | Distinct guardrail |
| A5 sleep | `REENTRY_PRAGMATICALLY_PRESERVED_THEORETICALLY_UNDERDETERMINED` | A5/A4 | candidate | re-entry pragmatically preserved, theoretically underdetermined | Useful synthesis claim |
| A5 sleep | `CONTINUITY_NOT_MEMORY` | A5 | strengthened | continuity not memory | Repeats |
| A5 sleep | `REPORT_RESIDUE_NOT_CONTINUITY` | A5/A4 | strengthened | report residue not continuity | Repeats |
| A5 upload | `LLM_REPORT_NOT_OWNER` | A5/A2 | strengthened / candidate | LLM report not owner | Narrow AI guardrail |
| A5 upload | `PERSONA_NOT_CONTINUITY` | A5 | candidate | persona not continuity | Distinct from memory store |
| A5 upload | `MEMORY_STORE_NOT_SELF` | A5 | candidate | memory store not self | Distinct archive/backup guardrail |
| A5 upload | `COPYABILITY_THREATENS_SINGULAR_CONTINUITY` | A5 | candidate | copyability threatens singular continuity | Related but not identical to branching |
| A5 upload | `PATTERN_NOT_OWNER` | A5 | strengthened | pattern not owner | Repeats |
| A5 upload | `FUTURE_AI_CONSCIOUSNESS_UNRESOLVED` | meta/A0 | candidate | future AI consciousness unresolved | Keep separate from current negative controls |
| A0 audit | `A0_UNRESOLVED` | A0 | strengthened | A0 unresolved | Repeats |
| A0 audit | `PROXY_REJECTION_NOT_EXPLANATION` | A0/meta | candidate | proxy rejection is not explanation | Important methodological guardrail |
| A0 audit | `A0_NOT_REPORT_ACCESS_INTEGRATION_MEMORY` | A0 | candidate | A0 not report/access/integration/memory | Compression claim, maybe too packed |
| A0 audit | `BRIDGE_REQUIRED_FOR_A0` | A0 | candidate | bridge required for A0 | Positive pressure, still open |
| A0 audit | `NO_BRIDGE_NOT_VICTORY` | A0/meta | candidate | no-bridge is not victory | Strong guardrail |

## 5. Deduplication / Merge Map

### Cluster: report / access / appearance

- **canonical proposed ID:** `REPORT_NOT_APPEARANCE`
- **aliases / merged phrases:** `ACCESS_NOT_APPEARANCE`; report is not appearance; access/report is not appearance
- **supporting reports:** A1, A4 interruption, A4 DREAM, A4 propofol
- **merge safety:** partial merge only
- **meaning preserved:** keep `REPORT_NOT_APPEARANCE` as canonical and keep `ACCESS_NOT_APPEARANCE` as a linked alias or sibling

Why merge is only partly safe:
`report` and `access` travel together in several reports, but they do not protect the exact same shortcut. `report` blocks output collapse; `access` blocks broader GNWT-style availability collapse.

### Cluster: content / field markers / appearance

- **canonical proposed ID:** `CONTENT_MARKER_NOT_APPEARANCE`
- **aliases / merged phrases:** content decoding not appearance; sustained activity not appearance; marker is not appearance
- **supporting reports:** A1
- **merge safety:** safe within A1 marker language
- **meaning preserved:** content-marker family remains distinct from report/access family

### Cluster: field / ownership distinction

- **canonical proposed ID:** `FIELD_NOT_OWNER`
- **aliases / merged phrases:** fielded appearance is not owner; field unity not owner
- **supporting reports:** A2
- **merge safety:** safe
- **meaning preserved:** preserves the A1 versus A2 separation

### Cluster: field markers / ownership distinction

- **canonical proposed ID:** `FIELD_MARKERS_NOT_OWNER`
- **aliases / merged phrases:** integration or field markers are not owner
- **supporting reports:** A1, A4 interruption, A4 propofol
- **merge safety:** unsafe to merge into `FIELD_NOT_OWNER`
- **meaning preserved:** `FIELD_NOT_OWNER` is ontological separation; `FIELD_MARKERS_NOT_OWNER` is methodological marker caution

### Cluster: ownership / report distinction

- **canonical proposed ID:** `OWNERSHIP_NOT_REPORT`
- **aliases / merged phrases:** ownership not reportability; mineness not report
- **supporting reports:** A2, A4 interruption, A4 DREAM
- **merge safety:** safe
- **meaning preserved:** already an existing ledger claim; clearly repeated pressure

### Cluster: agency / ownership distinction

- **canonical proposed ID:** `AGENCY_NOT_OWNERSHIP`
- **aliases / merged phrases:** agency without ownership pressure
- **supporting reports:** A2
- **merge safety:** safe
- **meaning preserved:** protects a different false positive than `OWNERSHIP_NOT_REPORT`

### Cluster: self-model / appearance distinction

- **canonical proposed ID:** `SELF_MODEL_NOT_A`
- **aliases / merged phrases:** self-model without A
- **supporting reports:** A2
- **merge safety:** safe
- **meaning preserved:** distinct AI and HOT guardrail

### Cluster: responsiveness / consciousness distinction

- **canonical proposed ID:** `RESPONSIVENESS_NOT_CONSCIOUSNESS`
- **aliases / merged phrases:** hand squeeze not consciousness; motor response not consciousness
- **supporting reports:** A4 interruption, A4 propofol
- **merge safety:** safe
- **meaning preserved:** important empirical guardrail

### Cluster: dream-report residue

- **canonical proposed ID:** `DREAM_REPORT_IS_RESIDUE`
- **aliases / merged phrases:** dream report is residue; awakening report is not dream field
- **supporting reports:** A4 DREAM
- **merge safety:** safe
- **meaning preserved:** keep narrow and dataset-specific

### Cluster: no-recall caution

- **canonical proposed ID:** `NO_RECALL_NOT_NO_EXPERIENCE`
- **aliases / merged phrases:** without recall is not no experience
- **supporting reports:** A4 DREAM
- **merge safety:** safe
- **meaning preserved:** protects a distinct sleep-report false positive

### Cluster: re-entry versus memory

- **canonical proposed ID:** `REENTRY_NOT_MEMORY_ONLY`
- **aliases / merged phrases:** re-entry not memory only
- **supporting reports:** A4 interruption, A4 DREAM, A4 propofol
- **merge safety:** safe
- **meaning preserved:** bridges A4 and A5 without collapsing into full identity claim

### Cluster: continuity / memory distinction

- **canonical proposed ID:** `CONTINUITY_NOT_MEMORY`
- **aliases / merged phrases:** memory supports continuity but is not continuity
- **supporting reports:** A5 memory, A5 branching, A5 sleep
- **merge safety:** safe
- **meaning preserved:** already an existing ledger claim; repeatedly reinforced

### Cluster: report residue / continuity distinction

- **canonical proposed ID:** `REPORT_RESIDUE_NOT_CONTINUITY`
- **aliases / merged phrases:** report after interruption is not same-self continuity
- **supporting reports:** A5 memory, A5 sleep
- **merge safety:** safe
- **meaning preserved:** distinct from `REPORT_NOT_APPEARANCE`

### Cluster: pattern / owner distinction

- **canonical proposed ID:** `PATTERN_NOT_OWNER`
- **aliases / merged phrases:** copied pattern is not owner
- **supporting reports:** A5 memory, A5 branching, A5 upload
- **merge safety:** safe
- **meaning preserved:** distinct from continuity-memory issues

### Cluster: branching / copyability pressure

- **canonical proposed ID:** `BRANCHING_THREATENS_SINGULAR_CONTINUITY`
- **aliases / merged phrases:** copyability threatens singular continuity
- **supporting reports:** A5 memory, A5 branching, A5 upload
- **merge safety:** unsafe as a full merge
- **meaning preserved:** keep `BRANCHING_THREATENS_SINGULAR_CONTINUITY` as canonical; keep `COPYABILITY_THREATENS_SINGULAR_CONTINUITY` as A5 artificial-system alias or subclaim

Why merge is only partly safe:
branching is the general identity stressor; copyability is the artificial/operational negative-control expression of the same issue.

### Cluster: non-branching guardrails

- **canonical proposed ID:** `NONBRANCHING_NOT_SUFFICIENT`
- **aliases / merged phrases:** non-branching is a guardrail, not proof
- **supporting reports:** A5 branching, A5 sleep
- **merge safety:** safe
- **meaning preserved:** key anti-overreach guardrail

### Cluster: temporal-flow guardrails

- **canonical proposed ID:** `TEMPORAL_FLOW_NOT_MEMORY`
- **aliases / merged phrases:** active lived succession is not memory residue
- **supporting reports:** A3
- **merge safety:** safe
- **meaning preserved:** keep distinct from `CONTINUITY_NOT_MEMORY`

### Cluster: temporal-coding guardrails

- **canonical proposed ID:** `TEMPORAL_CODING_NOT_LIVED_DURATION`
- **aliases / merged phrases:** time coding is not lived duration
- **supporting reports:** A3
- **merge safety:** safe
- **meaning preserved:** distinct mechanistic caution

### Cluster: flow / no-self guardrail

- **canonical proposed ID:** `FLOW_NOT_NO_SELF`
- **aliases / merged phrases:** reduced reflection is not absent self
- **supporting reports:** A3
- **merge safety:** safe
- **meaning preserved:** distinct phenomenology caution

### Cluster: A0 unresolved

- **canonical proposed ID:** `A0_UNRESOLVED`
- **aliases / merged phrases:** raw A unresolved; A0 remains open
- **supporting reports:** A1, A2, A4 interruption, A4 DREAM, A5 memory, A0 audit
- **merge safety:** safe
- **meaning preserved:** already in ledger and heavily repeated

### Cluster: proxy-rejection guardrails

- **canonical proposed ID:** `PROXY_REJECTION_NOT_EXPLANATION`
- **aliases / merged phrases:** negative controls are not mechanisms; subtraction is not explanation
- **supporting reports:** A0 audit, implicitly all A-split reports
- **merge safety:** safe
- **meaning preserved:** methodological guardrail

### Cluster: no-bridge guardrails

- **canonical proposed ID:** `NO_BRIDGE_NOT_VICTORY`
- **aliases / merged phrases:** no-bridge stance is not explanation
- **supporting reports:** A0 audit
- **merge safety:** safe
- **meaning preserved:** protects against mystery-by-definition drift

## 5. Maturity Scoring

| Canonical claim | Maturity | Why |
| --- | --- | --- |
| `A0_UNRESOLVED` | `unresolved_core` | repeated across many reports and already present in ledger |
| `OWNERSHIP_NOT_REPORT` | `strong_guardrail` | repeated, cross-case, already in ledger |
| `CONTINUITY_NOT_MEMORY` | `strong_guardrail` | repeated, central to A5, already in ledger |
| `FIELD_NOT_OWNER` | `strong_guardrail` | central A1/A2 separation, already in ledger |
| `REPORT_NOT_APPEARANCE` | `repeated_pressure` | repeated across A1 and A4, but not yet in ledger |
| `ACCESS_NOT_APPEARANCE` | `observed_once` | important but only directly named once |
| `CONTENT_MARKER_NOT_APPEARANCE` | `observed_once` | strong A1-specific guardrail, but currently single-source |
| `FIELD_MARKERS_NOT_OWNER` | `repeated_pressure` | repeated marker-level caution across A1/A4 |
| `RESPONSIVENESS_NOT_CONSCIOUSNESS` | `repeated_pressure` | empirical pressure from A4 interruption and propofol |
| `REENTRY_NOT_MEMORY_ONLY` | `repeated_pressure` | repeated A4/A5 bridge caution |
| `DREAM_REPORT_IS_RESIDUE` | `observed_once` | narrow but useful dataset-specific guardrail |
| `NO_RECALL_NOT_NO_EXPERIENCE` | `observed_once` | narrow but important sleep-study caution |
| `SELF_MODEL_NOT_A` | `observed_once` | important but not yet repeated enough |
| `AGENCY_NOT_OWNERSHIP` | `observed_once` | distinct A2 guardrail; needs follow-up |
| `OWNERSHIP_NONUNITARY` | `observed_once` | structural claim, not yet pressure-tested enough |
| `TEMPORAL_FLOW_NOT_MEMORY` | `observed_once` | useful A3 distinction, not yet repeated |
| `TEMPORAL_CODING_NOT_LIVED_DURATION` | `observed_once` | important mechanistic guardrail, single-source |
| `FLOW_NOT_NO_SELF` | `observed_once` | single-source but useful false-positive block |
| `MINIMAL_SELF_NOT_A0` | `observed_once` | single-source anti-smuggling guardrail |
| `A3_CANDIDATE_CONTINUITY_CHANNEL` | `conflict_or_needs_split` | positive candidate with circularity risk |
| `OCH_NEEDS_TEMPORAL_MARKER` | `conflict_or_needs_split` | useful direction but operationally underspecified |
| `PATTERN_NOT_OWNER` | `repeated_pressure` | repeated across A5 memory/branching/upload |
| `BRANCHING_THREATENS_SINGULAR_CONTINUITY` | `candidate_core` | repeated, structurally central, but still thought-experiment heavy |
| `COPYABILITY_THREATENS_SINGULAR_CONTINUITY` | `repeated_pressure` | strong negative-control version of branching, but likely alias/subclaim |
| `NONBRANCHING_NOT_SUFFICIENT` | `strong_guardrail` | repeated anti-overreach guardrail |
| `SUCCESSOR_SYMMETRY_UNRESOLVED` | `observed_once` | precise branch-case tension; likely worth preserving |
| `BIOLOGICAL_CONTINUITY_NOT_OWNER_PROOF` | `observed_once` | important but currently sleep-reentry specific |
| `REENTRY_STRONGER_THAN_COPYING` | `observed_once` | useful comparative claim, still narrow |
| `REENTRY_PRAGMATICALLY_PRESERVED_THEORETICALLY_UNDERDETERMINED` | `repeated_pressure` | strong synthesis compression, but still report-level |
| `LLM_REPORT_NOT_OWNER` | `observed_once` | important AI-specific guardrail |
| `PERSONA_NOT_CONTINUITY` | `observed_once` | AI/archive-specific caution |
| `MEMORY_STORE_NOT_SELF` | `observed_once` | archive/backup-specific caution |
| `FUTURE_AI_CONSCIOUSNESS_UNRESOLVED` | `strong_guardrail` | critical restraint claim, though not yet repeated often |
| `PROXY_REJECTION_NOT_EXPLANATION` | `strong_guardrail` | needed methodological brake after full A-split arc |
| `A0_NOT_REPORT_ACCESS_INTEGRATION_MEMORY` | `conflict_or_needs_split` | useful compression, but too packed for clean ledger entry |
| `BRIDGE_REQUIRED_FOR_A0` | `candidate_core` | central A0 direction, but still abstract |
| `NO_BRIDGE_NOT_VICTORY` | `strong_guardrail` | crucial against mystery-by-definition drift |
| `THEORY_SUPPORT_NOT_AOC_CONFIRMATION` | `observed_once` | meta-hygiene claim, useful but narrow |

## 6. Promotion Guardrails

| Claim cluster | Recommended action | Why |
| --- | --- | --- |
| `A0_UNRESOLVED` | `mark_strengthened_but_not_canon` | already present; repeated across reports |
| `OWNERSHIP_NOT_REPORT` | `mark_strengthened_but_not_canon` | already present; repeated A2/A4 support |
| `CONTINUITY_NOT_MEMORY` | `mark_strengthened_but_not_canon` | already present; strong repeated A5 support |
| `FIELD_NOT_OWNER` | `mark_strengthened_but_not_canon` | already present; useful A1/A2 separation |
| `REPORT_NOT_APPEARANCE` | `add_as_candidate` | repeated, cross-report, high-value guardrail |
| `ACCESS_NOT_APPEARANCE` | `leave_unpromoted` | important but not repeated enough yet |
| `CONTENT_MARKER_NOT_APPEARANCE` | `add_as_candidate` | single-source but important A1 guardrail |
| `FIELD_MARKERS_NOT_OWNER` | `add_as_candidate` | repeated marker-level caution |
| `RESPONSIVENESS_NOT_CONSCIOUSNESS` | `add_as_candidate` | repeated and empirically pressured |
| `REENTRY_NOT_MEMORY_ONLY` | `add_as_candidate` | repeated and useful A4/A5 bridge guardrail |
| `DREAM_REPORT_IS_RESIDUE` | `keep_as_guardrail` | narrow dataset-specific claim, useful but not general canon |
| `NO_RECALL_NOT_NO_EXPERIENCE` | `keep_as_guardrail` | same as above |
| `SELF_MODEL_NOT_A` | `add_as_candidate` | high-value false-positive protection |
| `AGENCY_NOT_OWNERSHIP` | `add_as_candidate` | distinct and worth preserving |
| `OWNERSHIP_NONUNITARY` | `needs_more_test` | plausible, but too structural for one report |
| `TEMPORAL_FLOW_NOT_MEMORY` | `add_as_candidate` | useful A3 guardrail |
| `TEMPORAL_CODING_NOT_LIVED_DURATION` | `add_as_candidate` | useful mechanistic guardrail |
| `FLOW_NOT_NO_SELF` | `keep_as_guardrail` | valuable but still local to A3 framing |
| `MINIMAL_SELF_NOT_A0` | `keep_as_guardrail` | anti-smuggling protection, not yet broad claim |
| `A3_CANDIDATE_CONTINUITY_CHANNEL` | `needs_more_test` | positive mechanism candidate with circularity risk |
| `OCH_NEEDS_TEMPORAL_MARKER` | `needs_more_test` | promising but underspecified |
| `PATTERN_NOT_OWNER` | `add_as_candidate` | repeated across multiple A5 reports |
| `BRANCHING_THREATENS_SINGULAR_CONTINUITY` | `add_as_candidate` | strong candidate-core result, but still human review required |
| `COPYABILITY_THREATENS_SINGULAR_CONTINUITY` | `merge_aliases` | keep as branch/AI alias under branching cluster |
| `NONBRANCHING_NOT_SUFFICIENT` | `add_as_candidate` | strong repeated anti-overreach guardrail |
| `SUCCESSOR_SYMMETRY_UNRESOLVED` | `keep_as_guardrail` | precise branch-case caution |
| `BIOLOGICAL_CONTINUITY_NOT_OWNER_PROOF` | `keep_as_guardrail` | useful but still narrow |
| `REENTRY_STRONGER_THAN_COPYING` | `keep_as_guardrail` | useful compression, but not ledger-core yet |
| `REENTRY_PRAGMATICALLY_PRESERVED_THEORETICALLY_UNDERDETERMINED` | `mark_strengthened_but_not_canon` | strong synthesis, but still human-review territory |
| `LLM_REPORT_NOT_OWNER` | `add_as_candidate` | strong operational guardrail |
| `PERSONA_NOT_CONTINUITY` | `keep_as_guardrail` | useful negative-control refinement |
| `MEMORY_STORE_NOT_SELF` | `keep_as_guardrail` | useful archive/backup refinement |
| `FUTURE_AI_CONSCIOUSNESS_UNRESOLVED` | `keep_as_guardrail` | important restraint claim |
| `PROXY_REJECTION_NOT_EXPLANATION` | `add_as_candidate` | high-value methodological protection |
| `A0_NOT_REPORT_ACCESS_INTEGRATION_MEMORY` | `split_claim` | too compressed; better represented by linked claims |
| `BRIDGE_REQUIRED_FOR_A0` | `add_as_candidate` | central A0 direction, but human review required |
| `NO_BRIDGE_NOT_VICTORY` | `add_as_candidate` | high-value anti-stall guardrail |
| `THEORY_SUPPORT_NOT_AOC_CONFIRMATION` | `keep_as_guardrail` | meta-hygiene, lower urgency |

No cluster here should be recommended for automatic canon promotion. Even the strongest ones should be treated as `human-review required`.

## 7. Contradictions / Tensions

| Tension | Why it matters | Best handling |
| --- | --- | --- |
| A3 temporal flow is a better continuity candidate, but not A0 | prevents smuggling continuity language into appearance | future test plus guardrail |
| non-branching is a strong guardrail, but not sufficient | blocks cheap identity solutions | candidate claim plus guardrail |
| biological/dynamical continuity strengthens sleep re-entry, but does not prove ownership | preserves ordinary life intuitions without overpromotion | guardrail |
| no-bridge stance protects against false bridges, but is not explanation | avoids mystery-by-definition drift | candidate methodological claim |
| proxy rejection sharpens A0, but can become explanation theater | the whole A-split arc risks stopping at subtraction | candidate methodological claim |
| field is not owner, but field markers are also not owner | ontological distinction and marker caution are related but not identical | keep split |
| branching threatens singular continuity, but copyability is only one expression of that threat | protects general theory and AI-specific negative controls | merge by alias, not full collapse |
| report is not appearance, but report residue is also not continuity | same word family, different target layers | keep split |

None of these currently requires an anomaly entry. They read more like guardrails and future-test seams than hard contradictions.

## 8. Proposed Ledger Patch Plan

Do not apply this patch plan without explicit instruction.

### Claims to add as candidates

- `REPORT_NOT_APPEARANCE`
- `FIELD_MARKERS_NOT_OWNER`
- `RESPONSIVENESS_NOT_CONSCIOUSNESS`
- `REENTRY_NOT_MEMORY_ONLY`
- `SELF_MODEL_NOT_A`
- `AGENCY_NOT_OWNERSHIP`
- `TEMPORAL_FLOW_NOT_MEMORY`
- `TEMPORAL_CODING_NOT_LIVED_DURATION`
- `PATTERN_NOT_OWNER`
- `BRANCHING_THREATENS_SINGULAR_CONTINUITY`
- `NONBRANCHING_NOT_SUFFICIENT`
- `LLM_REPORT_NOT_OWNER`
- `PROXY_REJECTION_NOT_EXPLANATION`
- `BRIDGE_REQUIRED_FOR_A0`
- `NO_BRIDGE_NOT_VICTORY`

### Claims to merge or alias

- `COPYABILITY_THREATENS_SINGULAR_CONTINUITY` -> alias/subclaim under `BRANCHING_THREATENS_SINGULAR_CONTINUITY`
- `ACCESS_NOT_APPEARANCE` -> alias or sibling to `REPORT_NOT_APPEARANCE`, not full merge

### Claims to split or leave out

- split `A0_NOT_REPORT_ACCESS_INTEGRATION_MEMORY` into linked guardrails rather than one oversized claim
- leave `OWNERSHIP_NONUNITARY` out until another dedicated A2 pass supports it
- leave `A3_CANDIDATE_CONTINUITY_CHANNEL` and `OCH_NEEDS_TEMPORAL_MARKER` out until another A3/A5 pass reduces circularity
- keep `DREAM_REPORT_IS_RESIDUE`, `NO_RECALL_NOT_NO_EXPERIENCE`, `PERSONA_NOT_CONTINUITY`, and `MEMORY_STORE_NOT_SELF` report-level unless a dataset or AI-specific section is added to the ledger

### Fields needed for new entries

- `id`
- `claim`
- `status: provisional`
- `type`
- `owner_location`
- `promotion_state: report_level_not_canon`
- `rationale`
- `falsifier`
- `depends_on`
- `relevant_tests`
- `relevant_theories`
- `notes`

### Proposed status pattern

- repeated guardrails already in ledger: keep current status, update notes or support only
- new repeated high-value claims: `status: provisional`
- unresolved A0 claims: `status: provisional`
- methodology-only guardrails: `status: provisional`

### YAML proposal snippets

```yaml
- id: REPORT_NOT_APPEARANCE
  claim: "Reportability is not identical to appearance-from-within."
  status: provisional
  type: operational
  owner_location: labs/appearance_ownership_continuity/core/A_SPLIT.md
  promotion_state: report_level_not_canon
  rationale: "A1 and A4 reports repeatedly show that report is residue or access-output rather than the target itself."
  falsifier: "Reportability fully predicts appearance across no-report, dream, anesthesia, and altered-report cases with no residue."
```

```yaml
- id: RESPONSIVENESS_NOT_CONSCIOUSNESS
  claim: "Responsiveness is not identical to consciousness."
  status: provisional
  type: operational
  owner_location: labs/appearance_ownership_continuity/core/A_SPLIT.md
  promotion_state: report_level_not_canon
  rationale: "A4 interruption and propofol pilot reports separate dose, motor response, and possible appearance."
  falsifier: "Responsiveness or its absence cleanly predicts consciousness across interruption and covert-cognition cases."
```

```yaml
- id: PROXY_REJECTION_NOT_EXPLANATION
  claim: "Rejecting a proxy is not the same as explaining appearance-from-within."
  status: provisional
  type: philosophical
  owner_location: labs/appearance_ownership_continuity/core/A_SPLIT.md
  promotion_state: report_level_not_canon
  rationale: "The A-split arc improved localization and guardrails, but not a positive mechanism of A0."
  falsifier: "Proxy rejection alone yields a mechanism or bridge that explains A0 rather than only protecting it from substitutes."
```

## 9. Proposed Test Registry Patch Plan

Recommended additions or updates for `TEST_REGISTRY.yaml`:

- `A_SPLIT_A3_FLOW_FALSE_POSITIVE_BATTERY`
- `A_SPLIT_A4_PROPOFOL_SUB02_DERIVATIVE_ALIGNMENT`
- `A_SPLIT_A1_COGITATE_MARKER_QUESTION_PLANNING`
- `AOC_AUTONOMOUS_TEST_LOOP_DESIGN`
- `AOC_BRIDGE_CANDIDATE_SCORECARD`

Recommended emphasis:

- use `A_SPLIT_A3_FLOW_FALSE_POSITIVE_BATTERY` to test whether A3 claims stay clear of circularity
- use `A_SPLIT_A4_PROPOFOL_SUB02_DERIVATIVE_ALIGNMENT` to deepen the strongest local empirical A4 channel
- use `A_SPLIT_A1_COGITATE_MARKER_QUESTION_PLANNING` to convert A1 caution into a concrete marker-question plan
- use `AOC_AUTONOMOUS_TEST_LOOP_DESIGN` to keep the framework from turning into a static taxonomy
- use `AOC_BRIDGE_CANDIDATE_SCORECARD` to compare A0 bridge candidates without premature promotion

## 10. Main Finding

The first A-Split arc produced a coherent set of negative and guardrail claims. The highest-confidence results are proxy rejections, not positive mechanisms. A0 remains unresolved; the next repository step is ledger hygiene, not theory expansion.

The most stable triage result is this: the repo is ready for a broader candidate-claim layer, but not for a canon pass. Several claims are repeated enough to deserve provisional ledger entry, while others still function better as report-only cautions or future-test prompts.

## 11. Verdict

- **what is ready for candidate ledger entry:** repeated guardrails such as `REPORT_NOT_APPEARANCE`, `RESPONSIVENESS_NOT_CONSCIOUSNESS`, `REENTRY_NOT_MEMORY_ONLY`, `PATTERN_NOT_OWNER`, `BRANCHING_THREATENS_SINGULAR_CONTINUITY`, `NONBRANCHING_NOT_SUFFICIENT`, `PROXY_REJECTION_NOT_EXPLANATION`, and `NO_BRIDGE_NOT_VICTORY`
- **what must remain report-only:** dataset-specific cautions like `DREAM_REPORT_IS_RESIDUE` and `NO_RECALL_NOT_NO_EXPERIENCE`, plus narrow AI/archive refinements unless a dedicated subsection is created
- **what needs another test:** `OWNERSHIP_NONUNITARY`, `A3_CANDIDATE_CONTINUITY_CHANNEL`, `OCH_NEEDS_TEMPORAL_MARKER`, and any oversized A0 compression claims
- **what should be tested next:** `AOC_BRIDGE_CANDIDATE_SCORECARD` if the goal is A0 progress, or `A_SPLIT_A4_PROPOFOL_SUB02_DERIVATIVE_ALIGNMENT` if the goal is the next smallest empirical move

Compression:

> The first A-Split arc earned a guardrail layer before it earned a mechanism layer.
