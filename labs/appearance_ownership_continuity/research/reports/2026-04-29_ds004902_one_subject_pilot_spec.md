# ds004902 One-Subject Pilot Spec

## Scope

Preparation only. This report uses existing local metadata under `labs/appearance_ownership_continuity/research/data_index/ds004902_metadata/`. No raw EEG was downloaded.

## Exact Subject / Session Selection Rule

Select the first subject with both normal-sleep and sleep-deprivation EEG timestamps available, then download only that subject's smallest usable raw EEG files after explicit approval.

Current metadata-selected pilot subject: `sub-01`.

Selection fields:

- Session order: `NS->SD`
- NS eyes-open time: `8:57:52`
- SD eyes-open time: `8:18:28`
- NS eyes-closed time: `9:04:40`
- SD eyes-closed time: `8:25:34`

## Normal Sleep vs Sleep Deprivation Contrast

Use within-subject contrast only:

- one normal sleep recording,
- one sleep-deprivation recording,
- eyes-open and eyes-closed if both are locally available and small enough.

## Metadata Variables

- **sleepiness:** KSS_NS, KSS_SD, SSS_NS, SSS_SD
- **mood:** PANAS_P_NS, PANAS_P_SD, PANAS_N_NS, PANAS_N_SD
- **PVT:** PVT_item1_NS, PVT_item2_NS, PVT_item3_NS, PVT_item1_SD, PVT_item2_SD, PVT_item3_SD
- **session_order:** SessionOrder
- **EEG_timing:** EEG_SamplingTime_Open_NS, EEG_SamplingTime_Closed_NS, EEG_SamplingTime_Open_SD, EEG_SamplingTime_Closed_SD

## Minimal Future EEG Analysis

After explicit approval:

1. Fetch one subject only.
2. Use one NS recording and one SD recording.
3. Prefer eyes-open plus eyes-closed if available.
4. Compute only basic spectral features: delta, theta, alpha, beta power and simple ratios.
5. Pair spectral features with KSS/SSS, PANAS, PVT, and session order metadata.

## AOC Pressure

This pilot can pressure:

- fatigue,
- state degradation,
- temporal stability,
- report/control reliability,
- whether degraded state affects attention/control proxies without being mistaken for direct consciousness evidence.

## No Claim Promotion

This is a pilot specification only. It does not promote AOC, OCH, DCP, LIP, or EIP claims.
