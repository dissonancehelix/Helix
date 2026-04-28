# Domain: Music

This is a Structured Knowledge Surface. It represents a formal, modeled reality of music semantics, structural analysis, and ingestion schemas.

**Constraints:**
- This is not an application.
- This is not a research lab.
- This directory contains normalized models, shared schemas, and semantic definitions.
- Any tool built to process music data belongs in `system/tools/`.
- Any experiment testing music structural invariants belongs in `labs/`.

## Foobar / Local Music Atlas

See [model/domains/music/foobar/README.md](foobar/README.md).

Foobar is the operator's interactive archive surface. It supports the music domain by preserving metadata, playback history, loved tracks, radio intake, VGM hardware context, and return paths into albums/artists/composers. The bridge between foobar and Helix lives at [system/tools/music_bridge/](../../system/tools/music_bridge/) and is read-only in Phase 2.

