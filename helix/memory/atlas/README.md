# Atlas System

The Atlas contains **specific entities and relationships** and represents **instantiated structure (posteriors)**.

## Mental Model
> "Library defines what can be true. Atlas records what appears to be true."

## Content
- **Entities**: Artists, albums, tracks, games, franchises.
- **Analysis**: Embeddings (Substrate Capability Vector vectors), style profiles, invariants discovered by Helix.
- **Relationships**: Graph-level connections (e.g., Artist → COMPOSER_OF → Track).

## Rules
- **Write Target**: This is the primary destination for Helix analysis pipelines.
- **No Priors**: General hardware knowledge belongs in the Library.
- **Validated Results**: Only semantically validated entities should exist here.

## Data Flow
Library → Helix → Atlas
