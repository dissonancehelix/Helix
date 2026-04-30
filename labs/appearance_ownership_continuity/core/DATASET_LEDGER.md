# AOC Dataset And Empirical Pressure Ledger

**Status:** canonical empirical pressure index for the AOC core harness  
**Scope:** dataset/contact inventory only; no claim promotion  
**Use:** future A-Split reports should cite this ledger when invoking empirical pressure sources

This ledger locks the currently identified empirical pressure map. It is not a broad literature review and does not claim any dataset solves appearance-from-within. Each source can pressure a layer, contrast class, or false positive; none can directly close A0.

## Inventory Summary

| ID | Source / paradigm | Local status | External status | Target A-Split layer(s) | First use |
| --- | --- | --- | --- | --- | --- |
| `cogitate_iit_gnwt_2025` | COGITATE adversarial collaboration | referenced | public dataset / docs | A1, access/report | theory-comparison pressure |
| `dream_database_2025` | DREAM database | available | public metadata / linked datasets | A4 | dream report and re-entry pressure |
| `ds006623_anesthesia` | Michigan Human Anesthesia fMRI Dataset-1 | available | public dataset | A4 | derivative-only interruption/re-entry pilot |
| `ds004902_sleep_deprivation` | Resting-state EEG Sleep Deprivation | available | public dataset | arousal, vigilance, indirect A4 | metadata / one-subject pilot spec |
| `body_ownership_paradigms` | rubber-hand, full-body, out-of-body-style manipulation | referenced | paradigm / literature | A2 | ownership/mineness pressure |
| `alien_limb_literature` | alien limb / alien hand | referenced | literature | A2 | ownership vs agency pressure |
| `depersonalization_derealization` | depersonalization / derealization | referenced | clinical / phenomenological literature | A2 | mineness and self-world boundary pressure |
| `no_report_paradigms` | no-report paradigms | referenced | paradigm / literature | A0, A1, A4 | access/report vs appearance pressure |

## `cogitate_iit_gnwt_2025`

- **Source / paradigm name:** COGITATE adversarial collaboration / IIT vs GNWT.
- **Local status:** referenced. Local docs/design link material exists; raw multimodal data was not downloaded.
- **External status:** public dataset / staged release depending modality.
- **Target A-Split layer(s):** A1 fielded appearance; access/report distinction; neighboring A0 pressure only.
- **Pressures which claims:** `OCH-C007`, `OCH-C008`, `OCH-C009`, `A_SPLIT_REQUIRED`, `A0_UNRESOLVED`.
- **What it can test:** whether task relevance, content duration, category/orientation, and modality signatures separate access/report pressure from binding/integration pressure.
- **What it cannot test:** raw A0 directly, ownership/mineness, same-self continuity, or OCH as selfhood.
- **Recommended first analysis:** docs-only variable map: task relevance -> GNWT/access pressure; sustained content/duration -> IIT/RPT/A1 pressure; report/behavior -> residue/access pressure.
- **Likely report IDs:** `A_SPLIT_A1_FIELD_ACCESS_COGITATE`, `T-COMP-001`, future A0/A1 bridge reports.
- **Local path:** `labs/appearance_ownership_continuity/research/data_index/cogitate_docs/`; `labs/appearance_ownership_continuity/research/dataset_notes/cogitate_docs.md`; `labs/appearance_ownership_continuity/research/reports/2026-04-29_cogitate_design_variable_map.md`.
- **Citation / source note:** COGITATE data docs and 2025 Nature adversarial collaboration paper. Use as theory-comparison pressure, not raw A solution.

## `dream_database_2025`

- **Source / paradigm name:** DREAM database.
- **Local status:** available. Registry metadata is local.
- **External status:** public metadata package with linked datasets; linked raw datasets vary by access and size.
- **Target A-Split layer(s):** A4 interruption/re-entry; sleep consciousness; delayed report; A0/A2 only indirectly.
- **Pressures which claims:** `OCH-C003`, `A_SPLIT_REQUIRED`, `A0_UNRESOLVED`, `OWNERSHIP_NOT_REPORT`.
- **What it can test:** dream/no-dream/mentation report labels, delayed report as residue, sleep-stage re-entry pressure, and uncertainty burden in retrospective experience labels.
- **What it cannot test:** direct access to the dream field, proof of ownership, proof of raw appearance, or full self-continuity.
- **Recommended first analysis:** metadata-only label matrix by dataset and sleep stage; rank open subsets by usable Experience / No experience contrast and low uncertain burden.
- **Likely report IDs:** `A_SPLIT_A4_DREAM_REENTRY`, `A_SPLIT_A4_INTERRUPTION_REENTRY`, future dream/anesthesia comparison.
- **Local path:** `labs/appearance_ownership_continuity/research/data_index/dream_database/`; `labs/appearance_ownership_continuity/research/dataset_notes/dream_database.md`; `labs/appearance_ownership_continuity/research/reports/2026-04-29_dream_metadata_pilot.md`.
- **Citation / source note:** DREAM database DOI `10.26180/22133105`. Retrospective report is not direct access to the dream field.

## `ds006623_anesthesia`

- **Source / paradigm name:** OpenNeuro `ds006623` / Michigan Human Anesthesia fMRI Dataset-1.
- **Local status:** available. Small derivative/control files are local; imaging was intentionally not downloaded.
- **External status:** public dataset.
- **Target A-Split layer(s):** A4 interruption/re-entry; covert cognition; responsiveness vs consciousness.
- **Pressures which claims:** `OCH-C003`, `A_SPLIT_REQUIRED`, `A0_UNRESOLVED`, `OCH-C007`.
- **What it can test:** propofol loss/recovery windows, imagery-task timing, hand-squeeze responsiveness, derivative control-coupling markers, and sedation/re-entry timeline construction.
- **What it cannot test:** task activity as raw A, responsiveness as consciousness, or unresponsiveness as absence.
- **Recommended first analysis:** derivative-only timeline using Participant_Info, LOR/ROR timing, one subject's propofol traces, and one subject's squeeze-force traces.
- **Likely report IDs:** `A_SPLIT_A4_PROPOFOL_REENTRY`, `A_SPLIT_A4_INTERRUPTION_REENTRY`, future anesthesia/DREAM comparison.
- **Local path:** `labs/appearance_ownership_continuity/research/data_index/ds006623_derivatives/`; `labs/appearance_ownership_continuity/research/dataset_notes/ds006623_anesthesia.md`; `labs/appearance_ownership_continuity/research/reports/2026-04-29_ds006623_derivative_intake.md`.
- **Citation / source note:** OpenNeuro `ds006623`, DOI `10.18112/openneuro.ds006623.v1.0.0`; Scientific Data article noted in the dataset note.

## `ds004902_sleep_deprivation`

- **Source / paradigm name:** Resting-state EEG Sleep Deprivation.
- **Local status:** available. Top-level metadata is local; no raw EEG was downloaded.
- **External status:** public dataset.
- **Target A-Split layer(s):** arousal, vigilance, homeostatic pressure, indirect A4 context.
- **Pressures which claims:** `OCH-C010`, `A_SPLIT_REQUIRED`, `A0_UNRESOLVED` as indirect constraint only.
- **What it can test:** fatigue/arousal degradation, questionnaire/PVT/KSS/SSS/PANAS context, vigilance as a constraint on temporal stability and report/control reliability.
- **What it cannot test:** loss of consciousness, raw A, ownership/mineness, or sleep interruption/re-entry directly.
- **Recommended first analysis:** one-subject pilot spec only: compare normal-sleep vs sleep-deprivation metadata and, if approved later, one EEG recording per condition with basic spectral features.
- **Likely report IDs:** `A_SPLIT_AROUSAL_DS004902_CONTEXT`, future arousal/vigilance constraint report.
- **Local path:** `labs/appearance_ownership_continuity/research/data_index/ds004902_metadata/`; `labs/appearance_ownership_continuity/research/dataset_notes/ds004902_sleep_deprivation_eeg.md`; `labs/appearance_ownership_continuity/research/reports/2026-04-29_ds004902_one_subject_pilot_spec.md`.
- **Citation / source note:** OpenNeuro `ds004902`, DOI `10.18112/openneuro.ds004902.v1.0.8`.

## `body_ownership_paradigms`

- **Source / paradigm name:** rubber-hand illusion, full-body illusion, out-of-body-style body ownership manipulation.
- **Local status:** referenced.
- **External status:** paradigm / literature.
- **Target A-Split layer(s):** A2 ownership/mineness.
- **Pressures which claims:** `OWNERSHIP_NOT_REPORT`, `FIELD_NOT_OWNER`, `OCH-C006`, `OCH-C010`.
- **What it can test:** dissociation among body schema, visual/tactile integration, mineness, boundary, agency/control coupling, and report.
- **What it cannot test:** raw A0 structure, same-self identity preservation, or ownership of thoughts/memories by itself.
- **Recommended first analysis:** literature-pressure case matrix comparing rubber-hand, full-body, and out-of-body-style manipulations against ownership, agency, and report dimensions.
- **Likely report IDs:** `A_SPLIT_A2_OWNERSHIP_ABSENT`, `A_SPLIT_A2_BODY_OWNERSHIP_WITHOUT_IDENTITY`, `T-EMB-001`.
- **Local path:** none yet beyond core reports and empirical contacts.
- **Citation / source note:** Use as A2 paradigm family. Body ownership alteration does not prove raw A structure.

## `alien_limb_literature`

- **Source / paradigm name:** alien limb / alien hand literature.
- **Local status:** referenced.
- **External status:** paper-only / clinical literature.
- **Target A-Split layer(s):** A2 ownership vs agency.
- **Pressures which claims:** `OWNERSHIP_NOT_REPORT`, `OCH-C006`, candidate `AGENCY_NOT_OWNERSHIP`.
- **What it can test:** dissociation between movement, authorship, agency attribution, bodily mineness, and report.
- **What it cannot test:** raw appearance, total ownership absence, or identity preservation.
- **Recommended first analysis:** A2 literature-pressure comparison against agency illusions and body ownership paradigms.
- **Likely report IDs:** `A_SPLIT_A2_OWNERSHIP_ABSENT`, `A_SPLIT_A2_AGENCY_WITHOUT_OWNERSHIP`.
- **Local path:** none yet beyond core reports and empirical contacts.
- **Citation / source note:** Agency disruption is not automatically ownership absence.

## `depersonalization_derealization`

- **Source / paradigm name:** depersonalization / derealization literature.
- **Local status:** referenced.
- **External status:** clinical / phenomenological literature.
- **Target A-Split layer(s):** A2 mineness; self-world ownership; A4 when interruption/re-entry or state transitions matter.
- **Pressures which claims:** `FIELD_NOT_OWNER`, `OWNERSHIP_NOT_REPORT`, `OCH-C001`, `OCH-C006`.
- **What it can test:** preservation of perception/report with altered mineness, reality-feel, affective ownership, and self-world boundary.
- **What it cannot test:** zero ownership, raw A absence/presence by itself, or a single mechanism for all ownership channels.
- **Recommended first analysis:** A2 case matrix separating appearance, affect, body ownership, thought ownership, report, and continuity.
- **Likely report IDs:** `A_SPLIT_A2_OWNERSHIP_ABSENT`, future boundary/mineness report.
- **Local path:** none yet beyond core reports and empirical contacts.
- **Citation / source note:** Reports are clinical/phenomenological; do not overread them as zero ownership.

## `no_report_paradigms`

- **Source / paradigm name:** no-report paradigms.
- **Local status:** referenced.
- **External status:** paradigm / literature.
- **Target A-Split layer(s):** access/report vs appearance; A0/A1/A4 pressure.
- **Pressures which claims:** `OCH-C003`, `A_SPLIT_REQUIRED`, `A0_UNRESOLVED`, `OCH-C009`.
- **What it can test:** whether neural/behavioral proxy markers differ when explicit report is removed or minimized.
- **What it cannot test:** raw A directly, ownership/mineness, or same-self continuity without further evidence.
- **Recommended first analysis:** theory-pressure report comparing report-present and no-report interpretations across GNWT/HOT/RPT/IIT/AOC.
- **Likely report IDs:** `A_SPLIT_A4_NO_REPORT_ACCESS_SPLIT`, `T-A-001`, `T-OWN-001`.
- **Local path:** none yet beyond core reports and empirical contacts.
- **Citation / source note:** Protects against GNWT/HOT overcollapse, but proxy markers still require interpretation.

## Standing Guardrails

- Metadata cleanliness is not consciousness evidence.
- Retrospective report is residue, not the original field.
- Responsiveness is not identical to consciousness.
- Integration is not identical to ownership.
- Arousal/vigilance constraints are not raw A tests.
- Clinical report is not zero-ownership proof.
- No empirical source listed here promotes claims automatically.
