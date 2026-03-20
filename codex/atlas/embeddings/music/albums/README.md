# codex/atlas/embeddings/music/albums/

Album-level CCS aggregations.

Each file: `{album_slug}.json`
Schema: `core/models/ccs/schema/ccs_schema.json`

Album embeddings are duration-weighted means of all track embeddings in the album.
They are computed after all track embeddings for the album are available.

Files will be populated when album entities are reparsed.
