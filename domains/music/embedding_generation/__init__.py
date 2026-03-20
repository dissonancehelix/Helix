"""
domains.music.models — Feature vector and style space modules.

Stages:
  7  feature_fusion    — build 64-dim feature vectors, FAISS index, composer profiles
  8  style_embedding   — UMAP/PCA style space projection
"""
from .feature_fusion  import run as feature_fusion
from .style_embedding import run as style_embedding

__all__ = ["feature_fusion", "style_embedding"]
