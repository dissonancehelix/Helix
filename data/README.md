# data/

Evidence and artifacts live here.

- `archives/` is the local archive bay for original source dumps. Archives are evidence preservation, not Helix working structure.
- `normalized/` is cleaned or projected evidence that can be regenerated or audited back to raw inputs.
- `derived/` is generated output: indexes, atlas artifacts, pipeline products, caches, and reviewable machine output.
- `legacy/` preserves compact extracted understanding and provenance notes from older structures.

Interpretation belongs in `model/`. Machinery belongs in `system/`. Reports belong in `reports/`.

Raw source material should be extracted and mapped into Helix-shaped records. Keep the original dumps as local archives under `data/archives/`; do not use `data/raw/` as a standing folder.
