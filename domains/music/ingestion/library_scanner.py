"""
Stage 1 — Library ingestion
============================
Scans the configured library roots, discovers all audio files, and
inserts track metadata records into the SQLite DB.

Delegates to MasterPipeline stages:
  1 (scan)   — walk filesystem, build file list
  2 (ingest) — write track records to DB with basic metadata
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domains.music.pipeline import MusicSubstratePipeline


def run(pipeline: "MusicSubstratePipeline") -> None:
    """Run library scan and DB ingestion (legacy stages 1 + 2)."""
    pipeline._delegate_to_legacy([1, 2])
