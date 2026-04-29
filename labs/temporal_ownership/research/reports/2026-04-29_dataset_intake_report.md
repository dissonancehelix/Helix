# 2026-04-29 Dataset Intake Report

## Scope

This intake performed a small-first pass for Temporal Ownership research.

Goal:

- obtain only lightweight metadata where safe,
- write dataset notes,
- avoid huge raw downloads,
- identify the next smallest useful pilot,
- promote no claims.

## What Was Obtained

### DREAM Database

Obtained the public registry metadata package from `10.26180/22133105`:

- `Datasets.csv`
- `Data records.csv`
- `People.csv`

Local path:

`labs/temporal_ownership/research/data_index/dream_database/`

Total local size is about 530 KB.

### ds004902 Sleep Deprivation EEG

Obtained metadata only:

- `dataset_description.json`
- `participants.tsv`
- `participants.json`
- `README`

Local path:

`labs/temporal_ownership/research/data_index/ds004902_metadata/`

Total local size is about 21 KB.

## What Was Not Obtained

Not downloaded:

- full DREAM-linked raw datasets,
- full ds004902 EEG payload,
- COGITATE raw fMRI / M-EEG / iEEG data,
- ds006623 raw or preprocessed fMRI,
- large derivatives,
- tool caches.

## Dataset Sizes And Access

| Dataset | Current local intake | Full / expected size | Access stance |
| --- | ---: | ---: | --- |
| DREAM registry | about 530 KB | registry package about 482.59 KB listed on repository page; local CSV sum differs slightly after file download | open registry, mixed underlying datasets |
| ds004902 | about 21 KB metadata | about 8.3 GB full dataset | OpenNeuro; one-subject pilot later |
| COGITATE | no files | large multimodal release | docs/variable map first |
| ds006623 | no files | full fMRI large | derivative-only pilot later |

## Access Blockers

- DREAM links outward to many datasets with different formats and access rules.
- `SCANDataset` appears request-based in the DREAM table.
- ds004902 full EEG is large; use EEGDash/OpenNeuro filtering later.
- COGITATE raw data should wait for a specific variable map.
- ds006623 imaging should wait; small derivative files are the safe first target.

## Next Smallest Safe Download

Priority order:

1. Inspect DREAM `Data URL` packages for size and fields without downloading bulk.
2. Choose the smallest DREAM open package with experience labels plus EEG/PSG.
3. If DREAM pilot is awkward, run ds004902 `sub-01` one-recording pilot by filtered access.
4. For anesthesia, fetch only `Participant_Info.xlsx`, propofol profiles, and squeeze-force traces if they are small.
5. Keep COGITATE at design/variable-map level until a sharper analysis question exists.

## Claim Pressure Potential

- **DREAM:** report vs experience, delayed report, sleep/waking re-entry, memory residue.
- **ds004902:** fatigue, temporal control degradation, state stability.
- **ds006623:** interruption/re-entry, covert responsiveness, control coupling under anesthesia.
- **COGITATE:** access/report/binding/theory comparison.

## No Claims Promoted

This intake does not strengthen, weaken, promote, or demote any TOM/ICT/DCP/LIP/EIP claim by itself.

Best compression:

> Metadata chooses the next pressure point; it does not become evidence of ownership.
