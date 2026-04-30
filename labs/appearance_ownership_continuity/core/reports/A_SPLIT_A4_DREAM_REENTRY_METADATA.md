# A-Split Pilot Report: A4 DREAM Re-entry Metadata

## 0. Test Metadata

- **Test id:** `A_SPLIT_A4_DREAM_REENTRY_METADATA`
- **Mode:** DCP-I / investigative compression
- **Target layer:** A4 interruption / re-entry
- **Dataset:** DREAM database
- **Data level:** metadata only
- **Status:** pilot report, evidence only, not canon
- **Files read:**
  - `labs/appearance_ownership_continuity/research/data_index/dream_database/Datasets.csv`
  - `labs/appearance_ownership_continuity/research/data_index/dream_database/Data records.csv`
  - `labs/appearance_ownership_continuity/research/data_index/dream_database/People.csv`
  - `labs/appearance_ownership_continuity/research/dataset_notes/dream_database.md`
  - `labs/appearance_ownership_continuity/research/reports/2026-04-29_dream_metadata_pilot.md`
  - `labs/appearance_ownership_continuity/core/reports/A_SPLIT_A4_INTERRUPTION_REENTRY.md`
  - `labs/appearance_ownership_continuity/core/reports/A_SPLIT_A4_PROPOFOL_DERIVATIVE_TIMELINE.md`
- **Files intentionally not used:** raw EEG, raw MEG, EDF/EDF+ signal packages, linked raw dataset payloads, participant-level raw PSG.

Small derived tables used by this report:

- `labs/appearance_ownership_continuity/research/derived/dream_reentry_metadata/dream_label_matrix.csv`
- `labs/appearance_ownership_continuity/research/derived/dream_reentry_metadata/dream_candidate_ranking.csv`
- `labs/appearance_ownership_continuity/research/derived/dream_reentry_metadata/dream_schema_map.json`
- `labs/appearance_ownership_continuity/research/derived/dream_reentry_metadata/dream_reentry_summary.json`

## 1. Claim Under Pressure

Dream re-entry metadata can separate original sleep-state, later report residue, recall quality, uncertainty burden, and sleep-stage context without giving direct access to the dream field.

Stronger claims not assumed:

- dream report is not the dream field
- no recall is not no experience
- no-experience report is not transparent absence
- EEG-predictable labels are not raw A
- awakening report is not ownership evidence by itself

## 2. Local DREAM File Inventory

| File | Size | Classification | Use here |
| --- | ---: | --- | --- |
| `Datasets.csv` | 170,822 bytes | dataset registry / access metadata / linked raw dataset pointer | dataset names, URLs, restrictions, response form, summary proportions |
| `Data records.csv` | 357,539 bytes | records table / report classification / sleep-stage metadata / signal availability metadata | Set-level label counts, last sleep stage, sample/channel availability, subject/file fields |
| `People.csv` | 1,685 bytes | contributor table | source context only |

No raw signal files were present or used. `Data URL` values are treated as linked package pointers, not local evidence.

## 3. Metadata Schema Map

Available fields relevant to A4:

| Channel | Local fields |
| --- | --- |
| dataset / Set ID | `Datasets.csv:Set ID`, `Data records.csv:Set ID` |
| participant / subject ID | `Data records.csv:Subject ID` |
| awakening / record ID | `Data records.csv:Key ID`, `Case ID`, `Filename` |
| sleep stage before awakening | `Data records.csv:Last sleep stage` |
| report classification | `Data records.csv:Experience` |
| recall status | `Experience` values: `Without recall`, `No experience or without recall`, `Unknown` |
| uncertainty / unknown labels | `Without recall`, `No experience or without recall`, `Unknown` |
| dataset access status | `Data URL`, `Accessibility`, `Data restriction note` |
| signal availability metadata | `EEG sample rate`, `Number of EEG channels`, `Has EOG`, `Has EMG`, `Has ECG`, `Has more data` |
| linked package status | `Datasets.csv:Data URL` |

The key structural advantage is that each awakening record carries both a mentation label and a `Last sleep stage` value. That lets A4 separate sleep-state context from report residue before any raw signal analysis.

## 4. Label Matrix

The registry contains 23 dataset rows, 20 unique dataset Set IDs, and 3,191 record rows. All record Set IDs join to dataset metadata.

| Set | Dataset | Total | Exp | No exp | Without recall | No exp / without recall | Unknown | Usable contrast | Uncertainty ratio | Sleep-stage coverage | Direct URL | Restricted/request |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Zhang & Wamsley 2019 | 308 | 238 | 70 | 0 | 0 | 0 | 308 | 0.0000 | 1.0000 | yes | no |
| 2 | Oudiette_N1Data | 246 | 214 | 18 | 14 | 0 | 0 | 232 | 0.0569 | 1.0000 | yes | no |
| 3 | LODE | 190 | 118 | 58 | 14 | 0 | 0 | 176 | 0.0737 | 1.0000 | yes | no |
| 9 | Multiple awakenings | 456 | 314 | 121 | 0 | 21 | 0 | 435 | 0.0461 | 1.0000 | yes | no |
| 13 | Tononi Serial Awakenings | 809 | 344 | 309 | 156 | 0 | 0 | 653 | 0.1928 | 1.0000 | yes | no |
| 16 | DATA1 | 324 | 107 | 118 | 63 | 34 | 2 | 225 | 0.3056 | 1.0000 | yes | no |

Other usable but smaller datasets include `Dream_YoungAdults`, `Older adults`, `ChildrenDreaming`, `Kumral et al., 2023`, `Sleep Talking`, `REM_Turku`, `Aamodt_evening_sleep`, and `Aamodt_morning_sleep`.

Normalization used:

- `Experience` and `No experience` form the usable contrast count.
- `Without recall`, `No experience or without recall`, and `Unknown` form the uncertainty burden.
- `Last sleep stage` is treated as sleep-state context, not as appearance evidence.

## 5. Candidate Dataset Ranking

Metadata-only ranking criteria:

- enough records
- clear `Experience` / `No experience` contrast
- low `Unknown` / recall-uncertainty burden
- sleep-stage labels available
- open or easy access
- standard EEG/PSG suitability
- no raw download needed yet

| Rank | Set | Dataset | Usable contrast | Uncertainty ratio | Why it ranks |
| ---: | ---: | --- | ---: | ---: | --- |
| 1 | 13 | Tononi Serial Awakenings | 653 | 0.1928 | largest usable contrast, direct URL, unrestricted, full sleep-stage metadata |
| 2 | 9 | Multiple awakenings | 435 | 0.0461 | large contrast, low uncertainty, direct URL, unrestricted |
| 3 | 1 | Zhang & Wamsley 2019 | 308 | 0.0000 | clean contrast, direct URL, unrestricted, strong metadata |
| 4 | 16 | DATA1 | 225 | 0.3056 | substantial contrast but high uncertainty burden |
| 5 | 3 | LODE | 176 | 0.0737 | moderate contrast, low uncertainty, direct URL |
| 6 | 2 | Oudiette_N1Data | 232 | 0.0569 | strong experience side, weaker no-experience contrast |

Top candidate for future raw/signal inspection remains `Tononi Serial Awakenings`, with a caution: its uncertainty burden is meaningful, not noise to erase. Best backups are `Multiple awakenings`, `Zhang & Wamsley 2019`, and `LODE`.

## 6. Re-entry Interpretation

The metadata separates these channels:

- **Sleep-state channel:** `Last sleep stage`, dataset-level REM/N1/N2/W proportions.
- **Awakening/re-entry channel:** each record is an awakening-linked report event, with `Time of awakening` and file/case identifiers.
- **Report-residue channel:** `Experience` label records what became communicable after re-entry.
- **Recall channel:** `Without recall` and `No experience or without recall` mark residue ambiguity.
- **Uncertainty channel:** uncertain labels are preserved as pressure, not discarded as inconvenience.
- **EEG/signal channel:** metadata says signals exist, but this run uses no raw signal.
- **Inferred appearance channel:** not directly available.
- **Ownership channel:** not directly available.

DCP-I reads this as a compression surface: sleep-state and possible experience are compressed through awakening into report residue. LIP applies because local labels are insufficient to reconstruct the original field. EIP applies because the later report is an irreversible residue of the transition, not a restoration of the prior state.

## 7. A4 Pressure

DREAM metadata can pressure:

- report residue
- delayed recall
- dream/no-dream labeling
- sleep-stage context
- uncertainty burden
- re-entry after sleep

DREAM metadata cannot directly pressure:

- A0 raw appearance
- A2 ownership/mineness
- A1 field unity
- A5 same-self identity
- the original dream field itself

The useful result is not that DREAM identifies appearance. The useful result is that DREAM keeps report, recall, uncertainty, sleep stage, and future signal analysis from collapsing into one channel.

## 8. False-Positive Battery

| Shortcut | Result | How this report avoids overclaiming |
| --- | --- | --- |
| dream report mistaken for original dream field | blocked | report is treated as residue after awakening |
| no recall mistaken for no experience | blocked | `Without recall` remains an uncertainty burden |
| no-experience report mistaken for transparent absence | blocked | `No experience` is a report label, not direct absence |
| label cleanliness mistaken for consciousness evidence | blocked | clean labels only improve contrast selection |
| sleep stage mistaken for appearance | blocked | sleep stage is context, not A0 |
| EEG-predictable label mistaken for raw A | blocked | no EEG analysis was run; future EEG would still be marker pressure |
| awakening narrative mistaken for continuity preservation | blocked | narrative residue is separated from owned continuity |
| metadata availability mistaken for support of the framework | blocked | metadata supports dataset selection, not claim promotion |

## 9. Comparison To Propofol Pilot

The propofol pilot and DREAM pilot are complementary A4 pressure sources.

| Source | Main channels | Main guardrail |
| --- | --- | --- |
| ds006623 propofol pilot | dose, task timing, motor response, LOR/ROR phase | responsiveness is not consciousness |
| DREAM metadata pilot | sleep stage, report residue, recall, uncertainty | report residue is not the original field |

Propofol pressures the shortcut where response becomes consciousness. DREAM pressures the shortcut where later report becomes the dream field. Together they sharpen A4 as interruption/re-entry rather than as one generic altered-state bucket.

## 10. Escalation Decision

Decision: **one-subset raw package warranted later**.

No escalation to a full DREAM raw download is warranted. Metadata already identifies candidate subsets and the next marker-level question. The smallest useful future escalation would inspect one high-value package, preferably:

1. `Tononi Serial Awakenings` if the goal is maximum usable contrast.
2. `Multiple awakenings` if the goal is lower uncertainty burden.
3. `Zhang & Wamsley 2019` if the goal is clean contrast and manageable scope.

Future marker-level question:

> Do pre-awakening EEG features differ reliably between `Experience`, `No experience`, and `Without recall` labels within one high-quality subset?

## 11. Main Finding

DREAM metadata can organize re-entry/report-residue pressure and identify candidate subsets, but it cannot directly access the dream field. Its value is making report, recall, uncertainty, sleep stage, and future signal analysis separable.

The conservative A4 result: interruption/re-entry is not a single channel. Sleep-state context, awakening, recall, later report, and uncertainty each need their own lane before any stronger interpretation is allowed.

## 12. Claim Ledger Recommendations

Do not edit `CLAIM_LEDGER.yaml` from this report alone. Recommended pressure only:

- `REPORT_NOT_APPEARANCE`: candidate claim; strengthened by DREAM as residue structure.
- `REENTRY_NOT_MEMORY_ONLY`: constrained; DREAM shows report/re-entry structure but not ownership continuity.
- `A0_UNRESOLVED`: strengthened; metadata cannot reach raw appearance.
- `OWNERSHIP_NOT_REPORT`: indirectly strengthened; no ownership channel exists in the metadata.
- `DREAM_REPORT_IS_RESIDUE`: candidate claim.
- `NO_RECALL_NOT_NO_EXPERIENCE`: candidate claim.

## 13. Next Tests

Recommended next test: `A_SPLIT_A1_COGITATE_FIELD_ACCESS`.

Reason: A4 now has two disciplined pilot anchors:

- propofol derivative/control timeline for dose, task, motor response, and re-entry channels
- DREAM metadata for sleep stage, report residue, recall, and uncertainty channels

Before drilling deeper into a single DREAM raw subset, the next better pressure move is to test A1/access separation through COGITATE design variables.

## 14. Verdict

- **What got stronger:** A4 needs channel separation: sleep state, awakening, report residue, recall, uncertainty, and future signal markers cannot be treated as one thing.
- **What got weaker:** any shortcut from later report to original field.
- **What remains open:** whether dream reports preserve enough structure to pressure A0, A1, or A2 beyond residue and re-entry.
- **What should be tested next:** A1 field/access separation using COGITATE as a design-variable pressure source.

Compression:

> DREAM does not hand over the dream field; it hands over the residue map after waking.
