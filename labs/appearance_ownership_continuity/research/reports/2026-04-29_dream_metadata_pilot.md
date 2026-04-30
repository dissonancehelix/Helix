# DREAM Metadata Pilot

## Scope

This pilot uses the local DREAM registry metadata only. It joins dataset-level metadata to awakening-level records, ranks candidate subsets, and chooses the smallest next package to inspect later. No raw EEG, MEG, PSG, or linked dataset packages were downloaded.

## Local Files Used

- `labs/appearance_ownership_continuity/research/data_index/dream_database/Datasets.csv`
- `labs/appearance_ownership_continuity/research/data_index/dream_database/Data records.csv`
- `labs/appearance_ownership_continuity/research/data_index/dream_database/People.csv`

Counts:

- Dataset rows: 23
- Unique dataset Set IDs: 20
- Data record rows: 3191
- People rows: 20

## Join Integrity

- Join key: normalized `Set ID`.
- Dataset IDs represented in records: 20
- Unique dataset IDs represented in `Datasets.csv`: 20
- Record rows without dataset metadata: 0
- Dataset IDs with no records: 0

The join is adequate for a metadata pilot. It does not prove that the linked raw packages are currently available or small enough for immediate download.

## Per-Dataset Label Matrix

| Set ID | Common name | Total | Experience | No experience | Without recall | No exp/without recall | Unknown | Usable contrast | Uncertain ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Zhang & Wamsley 2019 | 308 | 238 | 70 | 0 | 0 | 0 | 308 | 0.00 |
| 2 | Oudiette_N1Data | 246 | 214 | 18 | 14 | 0 | 0 | 232 | 0.06 |
| 3 | LODE | 190 | 118 | 58 | 14 | 0 | 0 | 176 | 0.07 |
| 4 | TWC_USA | 33 | 27 | 5 | 1 | 0 | 0 | 32 | 0.03 |
| 5 | Dream Database from Donders | 7 | 7 | 0 | 0 | 0 | 0 | 7 | 0.00 |
| 6 | REM_Turku | 134 | 123 | 3 | 8 | 0 | 0 | 126 | 0.06 |
| 7 | ChildrenDreaming | 30 | 13 | 17 | 0 | 0 | 0 | 30 | 0.00 |
| 8 | SCANDataset | 85 | 63 | 15 | 7 | 0 | 0 | 78 | 0.08 |
| 9 | Multiple awakenings | 456 | 314 | 121 | 0 | 21 | 0 | 435 | 0.05 |
| 10 | Sleep Talking | 22 | 11 | 10 | 1 | 0 | 0 | 21 | 0.05 |
| 11 | Dream_YoungAdults | 65 | 40 | 25 | 0 | 0 | 0 | 65 | 0.00 |
| 12 | Older adults | 40 | 18 | 22 | 0 | 0 | 0 | 40 | 0.00 |
| 13 | Tononi Serial Awakenings | 809 | 344 | 309 | 156 | 0 | 0 | 653 | 0.19 |
| 14 | Brain Institute - Federal University of Ri | 41 | 25 | 16 | 0 | 0 | 0 | 41 | 0.00 |
| 15 | Noreika_Motor_tDCS | 49 | 49 | 0 | 0 | 0 | 0 | 49 | 0.00 |
| 16 | DATA1 | 324 | 107 | 118 | 63 | 34 | 2 | 225 | 0.31 |
| 17 | Aamodt_evening_sleep | 158 | 116 | 15 | 27 | 0 | 0 | 131 | 0.17 |
| 18 | Aamodt_morning_sleep | 97 | 60 | 14 | 21 | 0 | 2 | 74 | 0.24 |
| 19 | Kumral et al., 2023 | 66 | 42 | 24 | 0 | 0 | 0 | 66 | 0.00 |
| 20 | MEG Kyushu | 31 | 24 | 0 | 4 | 0 | 3 | 24 | 0.23 |

## Access/Restriction Matrix

| Set ID | Common name | Direct URL | Restricted/request | Data URL | Restriction note |
| --- | --- | --- | --- | --- | --- |
| 13 | Tononi Serial Awakenings | yes | no | https://doi.org/10.26180/23306054.v3 | #N/A |
| 9 | Multiple awakenings | yes | no | https://doi.org/10.6084/m9.figshare.22086266 | #N/A |
| 1 | Zhang & Wamsley 2019 | yes | no | https://doi.org/10.6084/m9.figshare.22226692 | #N/A |
| 2 | Oudiette_N1Data | yes | no | https://doi.org/10.6084/m9.figshare.22210684 | #N/A |
| 16 | DATA1 | yes | no | https://doi.org/10.6084/m9.figshare.24058740.v1 | #N/A |
| 3 | LODE | yes | no | https://doi.org/10.6084/m9.figshare.22147085.v1 | #N/A |
| 17 | Aamodt_evening_sleep | yes | no | https://doi.org/10.6084/m9.figshare.22085597.v1 | #N/A |
| 6 | REM_Turku | yes | no | https://doi.org/10.6084/m9.figshare.23274596.v2 | #N/A |
| 18 | Aamodt_morning_sleep | yes | no | https://doi.org/10.6084/m9.figshare.22085627.v1 | #N/A |
| 19 | Kumral et al., 2023 | yes | no | https://doi.org/10.60493/31mg4-mfq53 | #N/A |
| 11 | Dream_YoungAdults | yes | no | https://doi.org/10.6084/m9.figshare.14899506 | #N/A |
| 15 | Noreika_Motor_tDCS | yes | no | https://doi.org/10.6084/m9.figshare.24058848.v1 | #N/A |
| 14 | Brain Institute - Federal University o | yes | no | https://doi.org/10.26180/23904699.v1 | #N/A |
| 12 | Older adults | yes | no | https://doi.org/10.6084/m9.figshare.14500563 | #N/A |
| 4 | TWC_USA | yes | no | https://doi.org/10.6084/m9.figshare.22106123 | #N/A |
| 7 | ChildrenDreaming | yes | no | https://doi.org/10.6084/m9.figshare.22220701 | #N/A |
| 20 | MEG Kyushu | yes | no | https://doi.org/10.6084/m9.figshare.27116590.v1 | #N/A |
| 10 | Sleep Talking | yes | no | https://doi.org/10.6084/m9.figshare.16950856 | #N/A |
| 5 | Dream Database from Donders | yes | no | https://doi.org/10.6084/m9.figshare.21388722 | #N/A |
| 8 | SCANDataset | no | yes | #N/A | Anyone who applies will be granted access to the dataset. The data's s... |

## Ranked Candidate Subsets

Ranking favored direct URL availability, usable `Experience` / `No experience` contrast, low uncertain burden, and likely small future inspection cost. It is a triage ranking, not a claim about consciousness.

| Rank | Set ID | Common name | Usable | Exp | No exp | Uncertain ratio | Direct URL | Restricted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 13 | Tononi Serial Awakenings | 653 | 344 | 309 | 0.19 | yes | no |
| 2 | 9 | Multiple awakenings | 435 | 314 | 121 | 0.05 | yes | no |
| 3 | 1 | Zhang & Wamsley 2019 | 308 | 238 | 70 | 0.00 | yes | no |
| 4 | 2 | Oudiette_N1Data | 232 | 214 | 18 | 0.06 | yes | no |
| 5 | 3 | LODE | 176 | 118 | 58 | 0.07 | yes | no |
| 6 | 6 | REM_Turku | 126 | 123 | 3 | 0.06 | yes | no |
| 7 | 19 | Kumral et al., 2023 | 66 | 42 | 24 | 0.00 | yes | no |
| 8 | 11 | Dream_YoungAdults | 65 | 40 | 25 | 0.00 | yes | no |

## Best Next DREAM Package To Inspect

**Best next package:** `Set ID 13` -- Tononi Serial Awakenings.

Why this is the next inspection target:

- direct URL available: yes
- restricted/request flag: no
- usable contrast count: 653 (`Experience` 344 + `No experience` 309)
- uncertain burden: 156 / 809 (19.28%)
- data URL: https://doi.org/10.26180/23306054.v3

Backup candidates:

- `Set ID 9` -- Multiple awakenings: usable 435, uncertain ratio 4.61%, direct URL yes, restricted no.
- `Set ID 1` -- Zhang & Wamsley 2019: usable 308, uncertain ratio 0.00%, direct URL yes, restricted no.
- `Set ID 2` -- Oudiette_N1Data: usable 232, uncertain ratio 5.69%, direct URL yes, restricted no.

## AOC/OCH/DCP/LIP/EIP Pressure

DREAM can pressure:

- report vs experience,
- delayed report as residue,
- sleep/waking re-entry,
- interruption boundary,
- **LIP:** local report labels are insufficient to reconstruct the full dream field,
- **EIP:** report is irreversible residue after the experience,
- **DCP:** awakening/report transition compresses experience into communicable residue.

DREAM gives AOC useful pressure because the labels already separate direct experience reports, no-experience reports, recall failure, and unknown/mixed cases. That lets the research program test whether report categories are clean enough to guide later signal analysis without pretending they are the experience itself.

## What This Does Not Prove

DREAM does not prove:

- appearance-from-within,
- ownership,
- self-continuity,
- AOC/OCH,
- that `No experience` means absence of experience.

## False Positives

- Treating `Experience` as the full dream field.
- Treating `No experience` as proven absence.
- Treating `Without recall` as useless.
- Treating metadata cleanliness as consciousness evidence.
- Treating dream report as the dream field itself.

## Next Raw/Signal Step

Inspect the linked package for `Set ID 13` without downloading the full raw archive first. The next safe move is to check package size, file manifest, license/access status, and whether a tiny metadata or one-subject subset can be selected before any signal data comes down.

## Compression

DREAM is useful because awakening turns a private sleep field into residue. The residue can pressure report/experience distinctions, but it is not the field.
