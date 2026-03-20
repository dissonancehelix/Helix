"""
domains.music.ingest — Library ingestion and metadata normalization.

Stages:
  1  library_ingestion      — scan filesystem, ingest track records into DB
  2  metadata_normalization — chip register parse + APEv2/.tag sidecar processing
"""
from .library_scanner    import run as scan
from .metadata_normalizer import run as normalize

__all__ = ["scan", "normalize"]
