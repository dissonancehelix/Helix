# ds004902 Sleep Deprivation EEG Intake

## Source

- **OpenNeuro ID:** `ds004902`
- **DOI:** `10.18112/openneuro.ds004902.v1.0.8`
- **Title:** A Resting-state EEG Dataset for Sleep Deprivation
- **OpenNeuro:** https://openneuro.org/datasets/ds004902
- **Local metadata path:** `labs/temporal_ownership/research/data_index/ds004902_metadata/`

## Metadata Obtained

Metadata-only files were fetched through the OpenNeuro GraphQL file listing and S3 file URLs:

| File | Local size | Role |
| --- | ---: | --- |
| `dataset_description.json` | 600 bytes | BIDS title, DOI, authors, license, keywords. |
| `participants.tsv` | 12,014 bytes | 71 participant rows with questionnaire and sampling fields. |
| `participants.json` | 4,693 bytes | Column descriptions for participant table. |
| `README` | 3,373 bytes | Dataset orientation. |

No EEG signal files were downloaded.

## Dataset Facts

- Total dataset size: about 8.3 GB
- Subjects: 71
- Recordings: 218
- Channels: 61
- EEGDash can filter/stream by subject, so a one-subject pilot should be possible later without fetching the full dataset.

Participant table columns include:

`participant_id`, `Gender`, `Age`, session order, EEG sampling timestamps, PVT measures, PANAS positive/negative affect, ATQ, SAI, SSS, KSS, sleep diary fields, EQ, Buss-Perry, and PSQI fields.

## Recommended First Pilot

Do not download the full dataset.

First approved pilot should be:

1. `sub-01` only.
2. One recording only.
3. Metadata plus one resting EEG file if needed.
4. Use EEGDash/OpenNeuro filtering if available.

Initial role: fatigue/state degradation and temporal-control pressure, not direct consciousness proof.

## Relevance To TOM / ICT / DCP / LIP / EIP

- **TOM:** tests temporal stability under fatigue and sleep-pressure degradation.
- **ICT:** can pressure whether degraded vigilance affects self-continuity proxies, but does not directly test appearance-from-within.
- **DCP:** fatigue can alter transition thresholds and decision/attention compression.
- **LIP:** local behavior during fatigue may be insufficient to infer internal state.
- **EIP:** sleep deprivation and recovery leave measurable residue in affect, vigilance, and task performance.

## Limitations

- This is not a direct consciousness dataset.
- Resting EEG and questionnaires are indirect pressure channels.
- Full raw download is intentionally deferred.
- Metadata alone cannot support claim promotion.
