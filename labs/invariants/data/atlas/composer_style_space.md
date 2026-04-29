# MODEL: COMPOSER STYLE SPACE

**Type**: Model  
**Status**: Exploratory  
**Origin**: Helix Music Lab  
**Domain Coverage**: Comprehensive Music Library (VGM and General Audio)  

## Mechanism

The Composer Style Space is a high-dimensional embedding where each point represents the musical fingerprint of a composer. This space is constructed by aggregating **TrackStyleVectors** belonging to that composer.

### Transformation Pipeline:
1. **Extraction**: Compute 64-dimensional feature vectors per track using `feature_extractor.py`.
2. **Aggregation**: `ComposerStyleVector = mean(track_vectors)`.
3. **Projection**: Dimensionality reduction (PCA/UMAP) to visualize stylistic clusters.

## Predictions

- Composers from the same "Sound Team" (e.g., Sega Sound Team) will exhibit closer proximity in style space than those from different teams.
- "Style Drifts" can be observed chronologically for a single composer as they migrate between platforms (e.g., FM synthesis to PCM/Redbook).

## Evidence

- Initial clustering on Sonic the Hedgehog 3 & Knuckles shows clear separation between the MJ/Buxer funk-influenced tracks and the Senoue/Drossin arcade-style tracks.

## Linked Experiments

- [composer_style_space](file:///c:/Users/dissonance/Desktop/Helix/labs/music_lab/experiments/composer_style_space.py)
- [composer_similarity_graph](file:///c:/Users/dissonance/Desktop/Helix/labs/music_lab/experiments/composer_similarity_graph.py)

## Artifacts

- `artifacts/music_lab/composer_vectors.json`
- `artifacts/music_lab/composer_similarity.graphml`
