# data/archives/

Local archive bay for original source dumps.

Raw datasets are not Helix working structure. They should be zipped or otherwise packaged here, then extracted into Helix-shaped records under `data/normalized/`, `data/derived/`, `data/legacy/`, `model/map/`, or the relevant domain README.

Tracked files in this folder should stay small: archive manifests, notes, and restore instructions. Bulky archives are local-only and ignored by Git.

Current local archive set:
- `raw_datasets/games_2026-04-28.zip`
- `raw_datasets/images_2026-04-28.zip`
- `raw_datasets/migration_2026-04-28.zip`
- `raw_datasets/reddit_2026-04-28.zip`
- `raw_datasets/scrobbles_2026-04-28.zip`
- `raw_datasets/trails_2026-04-28.zip`
- `raw_datasets/twitter_2026-04-28.zip`
- `raw_datasets/visual_corpus_2026-04-28.zip`
- `raw_datasets/wikipedia_2026-04-28.zip`

If a tool needs original files, restore the needed archive into a local ignored extraction area and then promote the usable facts into Helix-shaped outputs. Do not recreate `data/raw/` as a permanent workspace.
