# DREAM Database Intake

## Source

- **Dataset:** The DREAM database
- **DOI:** `10.26180/22133105`
- **Landing page:** https://doi.org/10.26180/22133105
- **Repository page:** https://bridges.monash.edu/articles/dataset/The_DREAM_database/22133105
- **License:** CC BY 4.0
- **Local index path:** `labs/appearance_ownership_continuity/research/data_index/dream_database/`

## Files Obtained

Small metadata package only:

| File | Local size | Role |
| --- | ---: | --- |
| `Datasets.csv` | 170,822 bytes | Registry of accepted DREAM datasets and access URLs. |
| `Data records.csv` | 357,539 bytes | Record-level awakening / experience metadata. |
| `People.csv` | 1,685 bytes | Contributor key table for dataset contacts. |

No raw EEG, MEG, PSG, audio, video, or full dataset payloads were downloaded.

## Table Summaries

### Datasets

- Rows: 23
- Columns include: `Key ID`, `Set ID`, `Amendment`, `Date entered`, `Common name`, `Full name`, `Corresponding contributor ID`, `Data URL`, `Data restriction note`.
- Entries with a `Data URL`: 20
- Entries without a direct `Data URL`: 3
- Apparent request-based entry: `SCANDataset`, with a restriction note indicating access requires application/contact.

Potential open-access candidates listed by `Data URL` include:

- `Zhang & Wamsley 2019` — https://doi.org/10.6084/m9.figshare.22226692
- `Oudiette_N1Data` — https://doi.org/10.6084/m9.figshare.22210684
- `LODE` / `The Language of Dreams` — https://doi.org/10.6084/m9.figshare.22147085.v1
- `TWC_USA` — https://doi.org/10.6084/m9.figshare.22106123
- `REM_Turku` — https://doi.org/10.6084/m9.figshare.23274596.v2
- `Tononi Serial Awakenings` — https://doi.org/10.26180/23306054.v3

### Data Records

- Rows: 3,191
- Columns include: `Key ID`, `Set ID`, `Amendment`, `Filename`, `Case ID`, `Subject ID`, `Experience`, `Treatment group`, and sleep-stage / timing metadata fields.
- Experience label counts:
  - `Experience`: 1,953
  - `No experience`: 860
  - `Without recall`: 316
  - `No experience or without recall`: 55
  - `Unknown`: 7

### People

- Rows: 20
- Columns include: `Key ID`, `Date entered`, `Given name(s)`, `Surname`, `Aliases`, `Email`, `Country`, `Date confirmed`.
- This table is used only as an access/contact lookup. It should not be treated as evidence for AOC.

## Access Notes

The DREAM registry is useful because it separates dataset discovery from raw signal download. The `Data URL` field points to underlying datasets; the registry itself does not contain raw recordings.

Smallest plausible next step:

1. Inspect the open figshare package metadata for `Zhang & Wamsley 2019`, `Oudiette_N1Data`, and `LODE`.
2. Select the smallest package that includes dream-report labels plus a minimal EEG/PSG subset.
3. Create an analysis plan before downloading any raw signal files.

Do not download the full DREAM-linked ecosystem at once.

## Relevance To AOC / OCH / DCP / LIP / EIP

- **AOC:** pressure-tests time, report, sleep interruption, and re-entry.
- **OCH:** distinguishes possible experience, delayed report, ownership, and memory-filtered residue.
- **DCP:** sleep/waking and awakening reports provide transition boundaries.
- **LIP:** immediate local evidence is incomplete because experience is often reconstructed after waking.
- **EIP:** dream report is residue; it changes the epistemic state after the experience and cannot fully restore the prior state.

## First Tiny Analysis Proposal

Use `Data records.csv` only:

1. Count experience labels by dataset and sleep stage.
2. Identify datasets with the cleanest `Experience` / `No experience` contrast.
3. Cross-check which of those datasets have open `Data URL` values.
4. Select one minimal raw-data candidate for a future pilot.

This would pressure report-vs-experience and interruption/re-entry claims without touching large raw files.

## Limitations

- Registry metadata is not raw consciousness evidence.
- Dream reports are delayed, memory-filtered, and language-shaped.
- `Experience` labels do not by themselves prove ownership or appearance-from-within.
- Dataset access varies; the registry points outward to packages with different formats and restrictions.
