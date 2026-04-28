# CCS Domain Adapters

This directory contains pure-translation layers that map domain-specific raw data (observables) into established **CCS Signals**.

## Architecture

- **`spotify.py`**: Implementation for mapping Spotify audio features (Energy, Danceability, etc.) to CCS signals.
- **`music/`**: Deep structural signal definitions and mapping rules for the music domain (Symbolic, Causal, and Perceptual layers).

## Separation of Concerns

Adapters are responsible for:
1. Normalizing raw data (e.g., 0-100 values to [0, 1]).
2. Applying domain-specific structural proxies.
3. Grouping raw features into the 6 CCS axes.

They **do not** modify the core CCS specification.
