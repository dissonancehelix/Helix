# 2026-04-29 Dataset Availability Audit

## Scope

This audit inspected the local Temporal Ownership research folder without downloading new raw datasets.

Inspected:

- `labs/temporal_ownership/research/`
- `labs/temporal_ownership/research/data_index/`
- `labs/temporal_ownership/research/dataset_notes/`
- `labs/temporal_ownership/research/reports/`

No claims are promoted by this audit.

## Files And Folders Found

### Research Root

| Path | Status |
| --- | --- |
| `ANALYSIS_LANES.md` | present |
| `DATASETS.yaml` | present |
| `LITERATURE.yaml` | present |
| `NOTES.md` | present |
| `README.md` | present |
| `ROADMAP.md` | present |
| `data_index/` | present |
| `dataset_notes/` | present |
| `reports/` | present |

### Data Index

| Dataset | Files present | Size / scope |
| --- | --- | --- |
| DREAM database | `Datasets.csv`, `Data records.csv`, `People.csv` | registry metadata only; about 530 KB total |
| ds004902 sleep deprivation EEG | `dataset_description.json`, `participants.tsv`, `participants.json`, `README` | top-level BIDS/OpenNeuro metadata only; about 21 KB total |
| ds006623 anesthesia fMRI | none in `data_index/` | note only |
| COGITATE | none in `data_index/` | note only |

## Dataset / Metadata Present

### DREAM Database

Local path:

`labs/temporal_ownership/research/data_index/dream_database/`

Readable tables:

| File | Rows | Columns discovered |
| --- | ---: | --- |
| `Datasets.csv` | 23 | `Key ID`, `Set ID`, `Amendment`, `Date entered`, `Common name`, `Full name`, `Corresponding contributor ID`, `Data URL`, `Data restriction note` |
| `Data records.csv` | 3,191 | `Key ID`, `Set ID`, `Amendment`, `Filename`, `Case ID`, `Subject ID`, `Experience`, `Treatment group`, plus sleep-stage/timing metadata fields |
| `People.csv` | 20 | `Key ID`, `Date entered`, `Given name(s)`, `Surname`, `Aliases`, `Email`, `Country`, `Date confirmed` |

Experience counts from `Data records.csv`:

| Experience label | Count |
| --- | ---: |
| `Experience` | 1,953 |
| `No experience` | 860 |
| `Without recall` | 316 |
| `No experience or without recall` | 55 |
| `Unknown` | 7 |

Access signals from `Datasets.csv`:

- Total rows: 23
- Rows with direct `Data URL`: 20
- Rows without direct `Data URL`: 3
- Request-based/restricted note visible for `SCANDataset`

Open-looking candidates listed in the registry include:

- `Zhang & Wamsley 2019` — `https://doi.org/10.6084/m9.figshare.22226692`
- `Oudiette_N1Data` — `https://doi.org/10.6084/m9.figshare.22210684`
- `LODE / The Language of Dreams` — `https://doi.org/10.6084/m9.figshare.22147085.v1`
- `TWC_USA` — `https://doi.org/10.6084/m9.figshare.22106123`
- `REM_Turku` — `https://doi.org/10.6084/m9.figshare.23274596.v2`
- `Multiple awakenings` — `https://doi.org/10.6084/m9.figshare.22086266`

Smallest plausible future EEG/PSG pilot:

1. Use `Data records.csv` only to rank DREAM sets by count of usable `Experience` / `No experience` labels.
2. Inspect package metadata for the open-looking candidates without downloading raw payloads.
3. Choose the smallest open package that has clear dream-report labels and a minimal signal subset.

### ds004902 Sleep Deprivation EEG

Local path:

`labs/temporal_ownership/research/data_index/ds004902_metadata/`

Files:

| File | Scope |
| --- | --- |
| `dataset_description.json` | BIDS/OpenNeuro title, DOI, authors, license, keywords |
| `participants.tsv` | 71 participant rows |
| `participants.json` | participant-column descriptions |
| `README` | dataset orientation |

Dataset description:

- Title: `A Resting-state EEG Dataset for Sleep Deprivation`
- DOI: `doi:10.18112/openneuro.ds004902.v1.0.8`
- Keywords: sleep deprivation, resting-state EEG, mood, sleepiness
- Dataset type: raw

Participant table:

- Rows: 71
- Columns include participant ID, gender, age, session order, EEG sampling timestamps, PVT fields, PANAS positive/negative affect, ATQ, SAI, SSS, KSS, sleep diary fields, EQ, Buss-Perry, and PSQI fields.

One-subject pilot feasibility:

- Locally feasible at metadata level.
- Raw one-subject EEG is not local.
- Future raw pilot should fetch only one subject / one recording if approved.

## Dataset / Metadata Not Found

### ds006623 Anesthesia fMRI

Not found locally:

- `Participant_Info.xlsx`
- propofol infusion profiles
- squeeze-force traces
- raw or preprocessed fMRI

Available locally:

- docs-only note: `dataset_notes/ds006623_anesthesia.md`

Derivative-only pilot feasibility:

- Not locally feasible yet because derivative files are not present.
- Feasible next step would be a small derivative-file fetch only, not fMRI.

### COGITATE

Not found locally:

- COGITATE raw fMRI / M-EEG / iEEG
- local task files
- local data-release documentation payload

Available locally:

- docs-only note: `dataset_notes/cogitate_docs.md`

Variable-map feasibility:

- Feasible from existing note and public design facts only.
- Not an empirical data analysis until local docs/data are added.

## Smallest Next Usable Empirical Target

Chosen smallest target:

```text
DREAM metadata/open-subset pilot
```

Reason:

- DREAM metadata is actually local and readable.
- It directly pressures report vs experience and sleep/waking re-entry.
- It requires no raw EEG/MEG/PSG download yet.
- It can identify the smallest open candidate before any signal analysis.

## Access Blockers

- DREAM underlying datasets vary by package and access rules.
- `SCANDataset` appears request-based.
- ds004902 full raw EEG is about 8.3 GB and is not local.
- ds006623 derivative files are not local.
- COGITATE local docs/raw data are not present.

## No Claims Promoted

This audit only establishes availability and next-step feasibility. It does not promote TOM, ICT, DCP, LIP, EIP, DCP-C, DCP-I, or any A-bridge claim.
