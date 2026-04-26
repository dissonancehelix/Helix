"""
Stage 7 — Feature fusion
=========================
Combines chip, symbolic, MIR, and theory features into a unified
64-dimensional feature vector per track.

Also builds:
  - FAISS / KDTree similarity index over all track vectors
  - Gaussian composer fingerprints (mean + covariance per composer)
  - Probabilistic composer attribution scores

Delegates to MasterPipeline stages 9–12:
  9  feature_vec   — assemble 64-dim vector
  10 faiss         — build similarity index
  11 composer_fp   — compute composer Gaussian fingerprints
  12 attributions  — probabilistic attribution per track
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine.kernel.runtime.orchestration.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> None:
    """Stage 7: feature vector assembly, FAISS index, composer profiles."""
    pipeline._delegate_to_legacy([9, 10, 11, 12])
