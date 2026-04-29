# ds006623 Anesthesia Intake

## Source

- **OpenNeuro ID:** `ds006623`
- **DOI:** `10.18112/openneuro.ds006623.v1.0.0`
- **Title:** Open fMRI resource for covert consciousness under anesthesia
- **OpenNeuro:** https://openneuro.org/datasets/ds006623
- **Scientific Data article:** https://www.nature.com/articles/s41597-025-06442-2

## Scope

Docs-only note. No full raw or preprocessed fMRI files were downloaded.

## Dataset Facts

- 26 healthy volunteers
- graded propofol sedation
- resting-state fMRI
- task fMRI
- tennis/navigation/hand-squeeze mental imagery tasks
- motor response hand squeeze

Useful derivative or small-first targets for a later approved pilot:

- `Participant_Info.xlsx`
- propofol infusion profiles
- squeeze-force traces
- task timing / behavioral response derivatives

## First TOM Use

Use as an interruption/re-entry and control-coupling pressure source:

1. Start with paper, OpenNeuro metadata, and small derivative files only.
2. Identify sedation levels, responsiveness states, and imagery/motor response markers.
3. Ask whether control coupling and re-entry degrade gradually or split from report/responsiveness.

## Relevance To TOM / ICT / DCP / LIP / EIP

- **TOM:** directly pressures interruption, re-entry, responsiveness, and temporal state transitions.
- **ICT:** relevant to covert consciousness and ownership-without-normal-report questions.
- **DCP:** sedation/recovery can be modeled as thresholded transition pressure.
- **LIP:** behavioral unresponsiveness is locally incomplete evidence.
- **EIP:** recovery reports and physiological traces are residue after altered state transitions.

## Limitations

- Responsiveness and consciousness can dissociate.
- Task performance is not identical to appearance-from-within.
- fMRI connectivity or imagery signatures should pressure claims, not promote them automatically.
- Full imaging download is deferred.
