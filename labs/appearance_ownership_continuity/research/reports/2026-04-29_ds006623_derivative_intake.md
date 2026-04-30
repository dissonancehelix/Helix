# ds006623 Derivative Intake

## Scope

Derivative-only intake for OpenNeuro `ds006623` / Michigan Human Anesthesia fMRI Dataset-1. This run fetched small control and trace files only. No raw or preprocessed imaging files were downloaded.

## Local Files Fetched

- `dataset_description.json` (2,221 bytes; fetched)
- `README.md` (1,538 bytes; fetched)
- `CHANGES` (105 bytes; fetched)
- `derivatives/Participant_Info.csv` (2,046 bytes; fetched)
- `derivatives/Participant_Info.xlsx` (11,160 bytes; fetched)
- `derivatives/LOR_ROR_Timing.csv` (502 bytes; fetched)
- `derivatives/LOR_ROR_Timing.xlsx` (11,831 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_Propofol_Infusion.pdf` (77,852 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_allrun_ESC.1D` (52,176 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_allrun_PLAS.1D` (52,233 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_rest1_ESC.1D` (1,540 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_rest1_PLAS.1D` (1,540 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_rest2_ESC.1D` (6,032 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_rest2_PLAS.1D` (6,034 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task1_ESC.1D` (2,290 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task1_PLAS.1D` (2,290 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task2_ESC.1D` (16,191 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task2_PLAS.1D` (16,167 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task3_ESC.1D` (17,131 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task3_PLAS.1D` (17,209 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task4_ESC.1D` (8,992 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-02/sub-02_task4_PLAS.1D` (8,993 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_Propofol_Infusion.pdf` (74,316 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_allrun_ESC.1D` (52,246 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_allrun_PLAS.1D` (52,283 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_rest1_ESC.1D` (1,540 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_rest1_PLAS.1D` (1,540 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_rest2_ESC.1D` (6,106 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_rest2_PLAS.1D` (6,094 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task1_ESC.1D` (2,290 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task1_PLAS.1D` (2,290 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task2_ESC.1D` (16,192 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task2_PLAS.1D` (16,141 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task3_ESC.1D` (17,117 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task3_PLAS.1D` (17,181 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task4_ESC.1D` (9,001 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-03/sub-03_task4_PLAS.1D` (9,037 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-04/sub-04_Propofol_Infusion.pdf` (78,096 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-04/sub-04_allrun_ESC.1D` (52,167 bytes; fetched)
- `derivatives/Propofol_Infusion/sub-04/sub-04_allrun_PLAS.1D` (52,272 bytes; fetched)
- ... 533 additional small derivative/control files

Failed fetches:

- none

## Participant Count

- Readable participant rows from `Participant_Info.csv`: 27
- Subject IDs represented in propofol/squeeze traces: 26

## Dose / Propofol Variables

Local propofol files include 364 `.1D` traces under `Propofol_Infusion/`.

Observed file pattern:

- `*_ESC.1D`
- `*_PLAS.1D`
- run/task/rest partitions such as `allrun`, `rest1`, `rest2`, and `task1` through `task4`

These are suitable for a later derivative-only timeline pilot.

## Squeeze-Force Variables

Local squeeze-force files include 150 `.1D` traces under `Squeeze_Force/`.

Observed file pattern:

- subject-level `*_allrun.1D`
- `*_task1.1D` through `*_task4.1D`
- `Instruction_Timing/Ideal_*` timing/design traces for action, navigation, squeeze, and tennis conditions

## Task Timing Variables

Readable derivative timing files:

- `derivatives/LOR_ROR_Timing.csv`: 26 rows
- `derivatives/Squeeze_Force/Instruction_Timing/*.1D`: instruction/design timing traces

## Candidate Re-Entry Markers

- responsiveness loss,
- responsiveness recovery,
- propofol concentration changes,
- rest/task block boundaries,
- force trace changes,
- instruction timing versus actual squeeze response.

## No Claims Promoted

This is an intake report only. It provides files for later pressure tests and does not promote AOC/OCH/DCP/LIP/EIP claims.
