# ds006623 Anesthesia Intake

## Source

- **OpenNeuro ID:** `ds006623`
- **DOI:** `10.18112/openneuro.ds006623.v1.0.0`
- **Title:** Michigan Human Anesthesia fMRI Dataset-1 / open fMRI resource for covert consciousness under anesthesia
- **OpenNeuro:** https://openneuro.org/datasets/ds006623
- **Scientific Data article:** https://www.nature.com/articles/s41597-025-06442-2

## Scope

Derivative-only intake. No anatomical scans, functional scans, fmriprep, xcp_d, freesurfer, mriqc, or other imaging payloads were downloaded.

## Local Files Fetched

Stored under `labs/appearance_ownership_continuity/research/data_index/ds006623_derivatives/`:

- top-level docs: `dataset_description.json`, `README.md`, `CHANGES`
- participant/control metadata: `derivatives/Participant_Info.csv`, `derivatives/Participant_Info.xlsx`, `derivatives/LOR_ROR_Timing.csv`, `derivatives/LOR_ROR_Timing.xlsx`
- propofol traces: 364 `.1D` files plus small PDFs when exposed
- squeeze-force and instruction-timing traces: 150 `.1D` files plus small PDFs when exposed

Total files selected/fetched or already present: 573.
Failed fetches: 0.

## Missing Files

- `participants.tsv` and `participants.json` were not present as top-level OpenNeuro files in the exposed snapshot.
- Full imaging derivatives were intentionally skipped.
- Raw task event files were not fetched unless included in the derivative/control paths above.

## Derivative-Only Pilot Feasibility

Feasible. The local intake has participant/control metadata and trace files for 26 subject IDs: sub-02, sub-03, sub-04, sub-05, sub-06, sub-07, sub-11, sub-12, sub-13, sub-14, sub-15, sub-16....

Participant rows readable from `Participant_Info.csv`: 27.
LOR/ROR timing rows readable from `LOR_ROR_Timing.csv`: 26.

## Interruption/Re-Entry Relevance

This dataset can define sedation/recovery windows before imaging analysis by combining participant rows, LOR/ROR timing, propofol concentration traces, and squeeze-force responsiveness traces.

## Control-Coupling Relevance

Squeeze-force traces and instruction timing can pressure control-coupling questions without requiring fMRI first. They can help define responsiveness loss, responsiveness recovery, task blocks, and force trace changes.

## What To Fetch Next

Next smallest safe step: parse `Participant_Info.csv`, `LOR_ROR_Timing.csv`, one subject's propofol `.1D` traces, and one subject's squeeze `.1D` traces into a derivative-only timeline. Do not fetch imaging until that timeline is useful.

## No Claim Promotion

This intake creates empirical pressure material only. It does not promote AOC, OCH, DCP, LIP, or EIP claims.
