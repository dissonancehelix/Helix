"""
Stage 5 — MIR audio analysis
==============================
Extracts Music Information Retrieval (MIR) features from audio files.

For rendered formats (MP3, FLAC, OGG, etc.) this uses librosa to extract:
  - Tempo and beat strength
  - Spectral centroid and rolloff
  - Zero-crossing rate, RMS energy
  - MFCC coefficients (13-dimensional)
  - Chroma features (12-dimensional)

For chip/emulated formats (VGM, SPC, NSF, etc.) a chip-proxy MIR
is computed from the symbolic score's pitch and timing data when
full audio rendering is unavailable.

Delegates to MasterPipeline stage 8 (mir).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domains.music.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> None:
    """Stage 5: MIR audio feature extraction (legacy stage 8)."""
    pipeline._delegate_to_legacy([8])
