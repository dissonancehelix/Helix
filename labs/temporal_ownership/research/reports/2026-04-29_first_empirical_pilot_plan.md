# 2026-04-29 First Empirical Pilot Plan

## Chosen Dataset

```text
DREAM database metadata / open-subset pilot
```

Local material exists under:

`labs/temporal_ownership/research/data_index/dream_database/`

Files:

- `Datasets.csv`
- `Data records.csv`
- `People.csv`

No raw EEG, MEG, PSG, or full linked dataset package is required for this pilot.

## Why This Is The Smallest Useful Empirical Move

DREAM is the smallest useful move because:

- metadata is already local,
- tables are readable,
- report categories are available,
- open/restricted dataset URLs can be inspected,
- the pilot can pressure report vs experience and sleep/waking re-entry before raw signal analysis.

This is a metadata pilot, not a consciousness proof.

## TOM / ICT / DCP / LIP / EIP Question

Question:

> Do DREAM report classifications separate cleanly enough to pressure report vs experience and sleep re-entry?

TOM pressure:

- report class,
- sleep/waking transition,
- delayed residue,
- re-entry after interruption.

ICT pressure:

- experience can be reported after the fact,
- no immediate report does not equal no experience,
- delayed report is not the full field.

DCP pressure:

- awakening is a transition boundary where experience becomes report/residue.

LIP pressure:

- local report labels are insufficient to infer the full dream field.

EIP pressure:

- dream reports are irreversible epistemic residue after the experience.

## Required Files

Required and already local:

- `Datasets.csv`
- `Data records.csv`

Optional:

- `People.csv` only if an access/contact route is needed; not needed for first analysis.

## Variables / Features

From `Data records.csv`:

- `Set ID`
- `Filename`
- `Case ID`
- `Subject ID`
- `Experience`
- sleep-stage / timing metadata fields if populated
- treatment/group fields if populated

From `Datasets.csv`:

- `Set ID`
- `Common name`
- `Full name`
- `Data URL`
- `Data restriction note`

Derived features:

- experience-label counts by dataset,
- usable contrast score: `Experience` + `No experience` counts,
- uncertain-label burden: `Without recall`, `No experience or without recall`, `Unknown`,
- access class: direct URL / no URL / request-based,
- candidate pilot rank.

## Exact Planned Analysis

1. Load `Datasets.csv` and `Data records.csv`.
2. Normalize `Set ID` and join records to dataset metadata.
3. Count `Experience` labels by dataset.
4. Count uncertain/no-recall labels by dataset.
5. Mark datasets with direct `Data URL`.
6. Mark request-based or missing URL datasets.
7. Rank datasets by:
   - direct access URL,
   - high count of `Experience` and `No experience`,
   - low unknown/no-recall burden,
   - likely small package size after metadata inspection.
8. Produce a candidate subset table.
9. Recommend exactly one open package for a future raw/signal pilot.

## Expected Output

Planned output:

```text
labs/temporal_ownership/research/reports/YYYY-MM-DD_dream_metadata_pilot.md
```

Expected contents:

- per-dataset report-label counts,
- open/restricted candidate list,
- smallest recommended raw/signal subset,
- TOM pressure interpretation,
- no claim promotion.

## Strengthening Pattern

The model is strengthened only modestly if:

- report labels separate into meaningful contrast classes,
- some datasets provide clean `Experience` vs `No experience` contrasts,
- sleep-stage/timing fields support interruption/re-entry framing,
- open subset candidates exist for later signal analysis.

## Weakening Pattern

The plan weakens if:

- labels are too inconsistent for report/experience pressure,
- dataset metadata cannot be joined reliably,
- open candidates lack useful report classes,
- the registry cannot identify a small pilot without downloading large packages.

## Ambiguous Pattern

Ambiguous results:

- many `Without recall` labels,
- mixed labels without sleep-stage context,
- direct URLs but unclear package sizes,
- good report labels but request-based access.

## False Positives

- Treating `Experience` label as full experience.
- Treating `No experience` as proven absence.
- Treating delayed report as the dream field itself.
- Treating metadata cleanliness as empirical support for TOM.

## False Negatives

- Discarding useful datasets because labels are messy.
- Treating `Without recall` as useless rather than theoretically important.
- Rejecting DREAM because it cannot solve A directly.

## Resource Cost

Expected cost:

- low compute,
- no raw downloads,
- no heavy analysis,
- no imaging/signal processing,
- CSV-only.

## No Claims Promoted

This pilot plan promotes no TOM, ICT, DCP, LIP, EIP, A-bridge, DCP-C, or DCP-I claim.

Best compression:

> DREAM metadata is the first pressure point because report residue is already visible before signals are touched.
