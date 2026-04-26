# atlas/embeddings/music/albums/

Album-level Substrate Capability Vector aggregations.

Each file: `{album_slug}.json`
Schema: `core/models/substrate/schema/substrate_schema.json`

Album embeddings are duration-weighted means of all track embeddings in the album.
They are computed after all track embeddings for the album are available.

Files will be populated when album entities are reparsed.

