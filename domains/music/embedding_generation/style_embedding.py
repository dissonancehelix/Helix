"""
Stage 8 — Style space embedding
=================================
Projects 64-dim feature vectors into a 2D/3D style space using
UMAP (primary) or PCA (fallback).

The style space reveals clusters of compositional similarity across
composers, games, and sound chips — enabling visualisation of the
entire music library's stylistic topology.

Delegates to MasterPipeline stage 18 (style_space).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domains.music.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> None:
    """Stage 8: UMAP/PCA style space projection (legacy stage 18)."""
    pipeline._delegate_to_legacy([18])
