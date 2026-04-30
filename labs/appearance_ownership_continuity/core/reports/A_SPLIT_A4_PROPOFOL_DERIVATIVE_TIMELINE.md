# A-Split Pilot Report: A4 Propofol Derivative Timeline

## 0. Test Metadata

- **Test ID:** `A_SPLIT_A4_PROPOFOL_DERIVATIVE_TIMELINE`
- **Mode:** DCP-I / investigative compression
- **Target layer:** A4 interruption / re-entry
- **Dataset:** ds006623 / Michigan Human Anesthesia fMRI Dataset-1
- **Data level:** derivative/control only
- **Status:** pilot report, evidence only, not canon
- **Files read:** `Participant_Info.csv`; `LOR_ROR_Timing.csv`; local `Propofol_Infusion/*.1D` traces; local `Squeeze_Force/*.1D` traces; `Squeeze_Force/Instruction_Timing/*.1D`; ds006623 dataset note and derivative intake report; AOC dataset ledger; A4 interruption/re-entry report.
- **Derived files used:** `subject_phase_inventory.csv`; `representative_trace_summary.csv`; `timeline_summary.json`.
- **Files intentionally not used:** raw fMRI, preprocessed fMRI, XCP-D outputs, fMRIPrep outputs, FreeSurfer outputs, MRIQC outputs, raw imaging event analysis, and imaging-derived connectivity markers.

## 1. Claim Under Pressure

Claim being tested:

> Responsiveness, sedation phase, task timing, and behavioral traces are separable channels in interruption/re-entry analysis.

Stronger claims not assumed:

- Responsiveness is not consciousness.
- Unresponsiveness is not unconsciousness.
- Hand squeeze is not raw A.
- Task timing is not ownership.
- Propofol concentration is not field presence.

This pilot asks whether the local derivative/control files can produce disciplined A4 timing channels before any larger imaging analysis is warranted.

## 2. Local File Inventory

Local root:

`labs/appearance_ownership_continuity/research/data_index/ds006623_derivatives/`

| File class | Local examples | Classification | Used in this pilot |
| --- | --- | --- | --- |
| participant/anesthetic metadata | `derivatives/Participant_Info.csv`, `Participant_Info.xlsx` | participant/anesthetic metadata | yes, CSV |
| LOR/ROR timing | `derivatives/LOR_ROR_Timing.csv`, `.xlsx` | participant phase timing | yes, CSV |
| propofol trace | `derivatives/Propofol_Infusion/sub-*/sub-*_allrun_ESC.1D`, `*_PLAS.1D`, run/task/rest traces | drug/dose channel | yes, compact summaries |
| squeeze-force trace | `derivatives/Squeeze_Force/sub-*/sub-*_allrun.1D`, `task1`-`task4` traces | motor response channel | yes, compact summaries |
| stimulus / instruction timing | `derivatives/Squeeze_Force/Instruction_Timing/Ideal_*` | instruction/task channel | yes, compact summaries |
| PDFs | propofol and squeeze plots | derivative visualization | inventoried only |
| imaging derivative | fMRIPrep, XCP-D, FreeSurfer, MRIQC style payloads | imaging derivative - do not use | not present in local pilot scope / not used |
| unknown / needs review | none identified in the derivative/control folders used here | needs review | no |

Local derivative/control inventory from prior intake:

- 26 subject IDs represented in propofol/squeeze traces.
- 27 readable rows in `Participant_Info.csv`; 26 subject rows used after excluding blank/header spacer rows.
- 26 readable rows in `LOR_ROR_Timing.csv`.
- 364 propofol `.1D` traces plus exposed PDFs.
- 150 squeeze-force `.1D` traces plus exposed PDFs.
- 20 instruction timing files.

## 3. Participant / Phase Table

The derived inventory file is:

`labs/appearance_ownership_continuity/research/derived/ds006623_timeline/subject_phase_inventory.csv`

Compact summary:

| Field | Result |
| --- | --- |
| participant rows used | 26 |
| LOR/ROR rows | 26 |
| subjects with propofol allrun trace | 26 |
| subjects with squeeze allrun trace | 26 |
| subjects with stimulus timing available | 26 via shared instruction timing files |
| subjects with missing/ambiguous ROR | 6 |

Representative subject rows:

| Subject | Participant info | Propofol trace | Squeeze trace | Stimulus timing | LOR task2 TR | ROR task3 TR | Notes |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `sub-02` | yes | yes | yes | yes | 1160 | 673 | clean complete case |
| `sub-14` | yes | yes | yes | yes | 898 | N/A | ROR missing/ambiguous |
| `sub-29` | yes | yes | yes | yes | 1835 | N/A | ROR missing/ambiguous; squeeze task4 file is empty |

This table is a channel inventory. It does not interpret phase timing as experience.

## 4. Timeline Construction

The derived trace summary file is:

`labs/appearance_ownership_continuity/research/derived/ds006623_timeline/representative_trace_summary.csv`

Representative subjects:

1. `sub-02`: clean complete case with LOR and ROR timing plus allrun propofol and squeeze traces.
2. `sub-14`: missing/ambiguous ROR case with available propofol and squeeze traces.
3. `sub-29`: missing/ambiguous ROR case with shortened allrun squeeze trace and empty task4 squeeze trace.

### `sub-02` Clean Complete Case

| Channel | Window / trace | Samples | Key summary | Phase markers |
| --- | --- | ---: | --- | --- |
| propofol ESC allrun | `sub-02_allrun_ESC.1D` | 8370 | nonzero from index 1943 to 8369; max 2.8734 | LOR task2 TR 1160; ROR task3 TR 673 |
| propofol PLAS allrun | `sub-02_allrun_PLAS.1D` | 8370 | nonzero from index 1943 to 8369; max 3.1991 | same phase markers |
| squeeze allrun | `sub-02_allrun.1D` | 6830 | force trace present across all samples; min -9.03, max 11.7 | same phase markers |
| squeeze task4 | `sub-02_task4.1D` | 1145 | task-specific force trace present | post-LOR/ROR relation requires protocol alignment |
| instruction squeeze allrun | `Ideal_allrun_squeeze.1D` | 6830 | nonzero design intervals from index 96 to 6823 | task channel only |

`sub-02` is the best first timeline candidate because all summary channels are present and LOR/ROR are both listed.

### `sub-14` Missing ROR Case

| Channel | Window / trace | Samples | Key summary | Phase markers |
| --- | --- | ---: | --- | --- |
| propofol ESC allrun | `sub-14_allrun_ESC.1D` | 8370 | nonzero from index 1946 to 8369; max 1.9835 | LOR task2 TR 898; ROR N/A |
| propofol PLAS allrun | `sub-14_allrun_PLAS.1D` | 8370 | nonzero from index 1946 to 8369; max 2.1832 | ROR unavailable |
| squeeze allrun | `sub-14_allrun.1D` | 6830 | force trace present; min -3.183, max 8.368 | re-entry phase unresolved |
| squeeze task4 | `sub-14_task4.1D` | 1145 | trace present | cannot anchor recovery to ROR |
| instruction squeeze allrun | shared timing file | 6830 | design intervals present | task channel only |

`sub-14` is useful as an ambiguity control. It has usable traces, but a missing ROR prevents clean re-entry labeling.

### `sub-29` Missing / Ambiguous Trace Case

| Channel | Window / trace | Samples | Key summary | Phase markers |
| --- | --- | ---: | --- | --- |
| propofol ESC allrun | `sub-29_allrun_ESC.1D` | 8370 | nonzero from index 1952 to 8369; max 5.1983 | LOR task2 TR 1835; ROR N/A |
| propofol PLAS allrun | `sub-29_allrun_PLAS.1D` | 8370 | nonzero from index 1952 to 8369; max 5.2483 | ROR unavailable |
| squeeze allrun | `sub-29_allrun.1D` | 5072 | shorter force trace present; min -11.23, max 11.47 | re-entry phase unresolved |
| squeeze task4 | `sub-29_task4.1D` | 0 | empty file | missing task trace |
| instruction squeeze allrun | shared timing file | 6830 | design intervals present | task channel only |

`sub-29` is useful as a missingness control. It shows why derived timelines need explicit channel completeness flags before any interpretation.

## 5. Channel Separation

| Channel | Local proxy | Available? | What it says | What it does not say |
| --- | --- | --- | --- | --- |
| drug/dose channel | propofol ESC/PLAS `.1D`, participant dosage notes, LOR ESC | yes | sedation/dose trace and pharmacological phase context | whether appearance is present |
| instruction/task channel | `Instruction_Timing/Ideal_*` files | yes | when task prompts/design intervals occur | whether task is experienced or owned |
| motor response channel | squeeze-force traces | yes | whether force output changes during task windows | whether response is conscious |
| report/access channel | ordinary verbal report during deep phases | no direct channel in this pilot | absent or not represented in local derivative tables | absence of report is not absence of appearance |
| inferred consciousness channel | none directly available | not directly available | must remain a later interpretive layer | cannot be read from dose, task, or squeeze alone |
| ownership channel | none directly available | not directly available | OCH/A2 remains unmeasured here | cannot be inferred from force or timing |

The pilot therefore succeeds as a channel separator: dose, task design, motor output, and phase timing are locally separable. The two channels AOC most cares about, appearance and ownership, are not directly available.

## 6. A4 Pressure

The derivative timeline can pressure:

- response loss,
- response recovery,
- re-entry windows,
- task-following possibility,
- report/response insufficiency,
- missingness and ambiguity handling before larger analysis.

It cannot pressure directly:

- raw A0,
- owned mineness A2,
- field unity A1,
- same-self identity A5,
- conscious experience itself.

The useful A4 object is not "subject conscious/unconscious." The useful object is a multi-channel transition record:

```text
drug trace
task timing
motor response
LOR/ROR marker
missingness flag
interpretive caution
```

## 7. False-Positive Battery

| Check | Vulnerable shortcut | Result | How this report avoids overclaiming |
| --- | --- | --- | --- |
| dose mistaken for unconsciousness | high propofol or phase label becomes absence of A | blocked | dose is a drug channel only |
| hand squeeze mistaken for consciousness | motor trace becomes conscious task following | blocked | squeeze is motor response channel only |
| no squeeze mistaken for no consciousness | absent/empty response becomes absence of appearance | blocked | missing motor output is not absence of A |
| task window mistaken for task experience | instruction timing becomes experience | blocked | timing is design context only |
| re-entry timing mistaken for ownership continuity | ROR becomes same-owner return | blocked | ROR is responsiveness/recovery marker, not OCH continuity |
| derivative cleanliness mistaken for theory support | clean table becomes AOC support | blocked | derived tables support future pressure tests, not claim promotion |

## 8. Escalation Decision

Decision: **one-subject derivative expansion**.

Labels:

- **No escalation:** not chosen, because `sub-02` has enough complete structure to justify one more derivative-only pass.
- **One-subject derivative expansion:** chosen. Expand `sub-02` into a task-aligned derivative timeline using all task/rest propofol traces, squeeze traces, and instruction timing files.
- **One-subject imaging derivative warranted later:** possible later, only after the derivative timeline names a marker-level question.
- **Full imaging not yet warranted:** current decision.
- **Full imaging warranted:** not warranted.

The pilot identifies a useful marker-level question that can still be answered without imaging:

> During known task windows around LOR/ROR, do squeeze-force traces show separable response loss/recovery relative to propofol trace changes?

That question should be answered before any imaging escalation.

## 9. Main Finding

Derivative/control files can define interruption/re-entry windows and separate sedation, task, and motor-response channels. They do not identify consciousness or ownership directly, but they create a disciplined timeline for later marker-level testing.

Most conservative result:

> ds006623 derivative files are useful because they prevent the channels from collapsing into one another before theory interpretation begins.

## 10. Claim Ledger Recommendations

Do not edit `CLAIM_LEDGER.yaml` from this pilot alone.

Recommended pressure only:

- `RESPONSIVENESS_NOT_CONSCIOUSNESS`: candidate new claim; strengthened by channel separation.
- `REENTRY_NOT_MEMORY_ONLY`: candidate new claim; not directly tested, but timeline structure prepares the terrain.
- `REPORT_NOT_APPEARANCE`: candidate new claim; indirectly supported because report is not the active channel here.
- `FIELD_MARKERS_NOT_OWNER`: candidate new claim; keep for later imaging/field-marker work.

## 11. Next Tests

Recommended next test:

> `A_SPLIT_A4_DREAM_REENTRY_METADATA`

Reason: this pilot found useful timeline structure in ds006623, but the immediate complementary pressure source is DREAM. DREAM can test the other side of A4: report residue after sleep rather than motor/dose traces during anesthesia. Running DREAM next keeps A4 balanced before returning to a deeper `sub-02` derivative expansion.

Alternate later test:

> `A_SPLIT_A4_PROPOFOL_SUB02_DERIVATIVE_ALIGNMENT`

Use only if the next pass wants a tighter task-aligned anesthesia timeline.

Best compression:

> The derivative timeline gives channels, not consciousness; its value is that the channels stop pretending to be one thing.
