"""
taste_vector.py — Operator taste centroid builder
==================================================
Scans two sources of "loved" tracks:
  1. Foobar2000 library — tracks tagged with the `2003_loved` field
  2. C:/Users/dissonance/Desktop/temp — files in the operator's temp favourites folder

Loads each track's feature vector from the DB, applies taste weights
(from config.TASTE_WEIGHT), and computes a weighted centroid.

IMPORTANT: Taste weights and confidence weights are NEVER mixed.
  - Taste weights control how strongly each track contributes to the centroid.
  - Confidence weights (used by recommender) control reliability of vectors.

API
---
build(db: TrackDB, index: VectorIndex | None = None) -> TasteVector
    Scan sources, weight, compute centroid.  Save to config.TASTE_PATH.

TasteVector:
    .centroid: list[float]        # 64-dim weighted centroid
    .loved_ids: list[str]         # track_ids that contributed
    .save(path) / .load(path)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from labs.music_lab.config import (
    TASTE_WEIGHT, TASTE_PATH, TEMP_DIR, FOOBAR_LOVED_FIELD,
    FEATURE_VECTOR_DIM, FEATURE_VECTOR_VERSION,
)

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False

try:
    import mutagen as _mutagen
    _HAS_MUTAGEN = True
except ImportError:
    _HAS_MUTAGEN = False


# ---------------------------------------------------------------------------
# TasteVector
# ---------------------------------------------------------------------------

@dataclass
class TasteVector:
    centroid:   list[float]
    loved_ids:  list[str]        = field(default_factory=list)
    weights:    list[float]      = field(default_factory=list)
    source_counts: dict[str, int] = field(default_factory=dict)
    schema_version: str          = FEATURE_VECTOR_VERSION

    def save(self, path: Path | None = None) -> None:
        p = path or TASTE_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": self.schema_version,
            "centroid":       self.centroid,
            "loved_ids":      self.loved_ids,
            "weights":        self.weights,
            "source_counts":  self.source_counts,
        }
        p.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path | None = None) -> "TasteVector":
        p = path or TASTE_PATH
        if not p.exists():
            return cls(centroid=[0.0] * FEATURE_VECTOR_DIM)
        try:
            data = json.loads(p.read_text())
            return cls(
                centroid=data.get("centroid", [0.0] * FEATURE_VECTOR_DIM),
                loved_ids=data.get("loved_ids", []),
                weights=data.get("weights", []),
                source_counts=data.get("source_counts", {}),
                schema_version=data.get("schema_version", FEATURE_VECTOR_VERSION),
            )
        except Exception:
            return cls(centroid=[0.0] * FEATURE_VECTOR_DIM)


# ---------------------------------------------------------------------------
# Source scanners
# ---------------------------------------------------------------------------

_AUDIO_EXTS = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac", ".wma",
               ".ape", ".wv", ".opus", ".vgm", ".vgz", ".spc", ".nsf",
               ".nsfe", ".sid", ".gym"}


def _is_loved_foobar(path: Path) -> bool:
    """Check if a file has the 2003_loved tag set (non-empty/non-zero)."""
    if not _HAS_MUTAGEN:
        return False
    try:
        import mutagen
        tags = mutagen.File(str(path), easy=True)
        if tags is None:
            return False
        # Check exact field name (ID3, APEv2, VorbisComment all handled by easy=True)
        for key in [FOOBAR_LOVED_FIELD, f":{FOOBAR_LOVED_FIELD}:",
                    FOOBAR_LOVED_FIELD.upper(), f"txxx:{FOOBAR_LOVED_FIELD}"]:
            val = tags.get(key)
            if val:
                v = str(val[0]).strip()
                if v not in ("", "0", "false", "False"):
                    return True
        # Also check raw tags for TXXX frames (ID3)
        if hasattr(tags, "tags") and tags.tags:
            for k, v in tags.tags.items():
                if FOOBAR_LOVED_FIELD.lower() in str(k).lower():
                    sv = str(v)
                    if sv not in ("", "0", "false", "False"):
                        return True
    except Exception:
        pass
    return False


def scan_foobar_loved(library_root: Path) -> list[Path]:
    """Scan music library for files tagged with FOOBAR_LOVED_FIELD."""
    loved: list[Path] = []
    if not library_root.exists():
        return loved
    for path in library_root.rglob("*"):
        if path.suffix.lower() in _AUDIO_EXTS and path.is_file():
            if _is_loved_foobar(path):
                loved.append(path)
    return loved


def scan_temp_dir(temp_dir: Path = TEMP_DIR) -> list[Path]:
    """Return all audio/music files in the temp favourites dir."""
    if not temp_dir.exists():
        return []
    return [p for p in temp_dir.rglob("*")
            if p.suffix.lower() in _AUDIO_EXTS and p.is_file()]


# ---------------------------------------------------------------------------
# Centroid builder
# ---------------------------------------------------------------------------

def _weighted_centroid(vectors: list[list[float]], weights: list[float]) -> list[float]:
    """Compute a weighted mean vector."""
    if not vectors:
        return [0.0] * FEATURE_VECTOR_DIM
    dim = len(vectors[0])
    total_w = sum(weights)
    if total_w == 0:
        return [0.0] * dim

    centroid = [0.0] * dim
    for vec, w in zip(vectors, weights):
        for i in range(min(dim, len(vec))):
            centroid[i] += vec[i] * w
    return [c / total_w for c in centroid]


def build(db: Any, library_root: Path | None = None) -> TasteVector:
    """
    Build operator taste centroid from Foobar loved tracks + temp dir.

    db: TrackDB instance (used to look up feature vectors by path)
    library_root: override for music library scan (defaults to config.LIBRARY_ROOT)
    """
    from labs.music_lab.config import LIBRARY_ROOT

    if library_root is None:
        library_root = LIBRARY_ROOT

    loved_vectors: list[list[float]] = []
    loved_ids:     list[str]         = []
    weights:       list[float]       = []
    source_counts: dict[str, int]    = {"foobar_loved": 0, "desktop_temp": 0}

    # Foobar loved tracks
    print("[taste_vector] Scanning Foobar loved tracks …")
    foobar_paths = scan_foobar_loved(library_root)
    source_counts["foobar_loved"] = len(foobar_paths)
    for path in foobar_paths:
        vec = _load_vector_for_path(db, path)
        if vec is not None:
            loved_vectors.append(vec)
            loved_ids.append(_path_id(path))
            weights.append(TASTE_WEIGHT["loved_foobar"])

    # Desktop temp favourites
    print("[taste_vector] Scanning Desktop/temp …")
    temp_paths = scan_temp_dir()
    source_counts["desktop_temp"] = len(temp_paths)
    for path in temp_paths:
        # Avoid double-counting if also in Foobar library
        pid = _path_id(path)
        if pid not in loved_ids:
            vec = _load_vector_for_path(db, path)
            if vec is not None:
                loved_vectors.append(vec)
                loved_ids.append(pid)
                weights.append(TASTE_WEIGHT["desktop_temp"])

    centroid = _weighted_centroid(loved_vectors, weights)

    taste = TasteVector(
        centroid=centroid,
        loved_ids=loved_ids,
        weights=weights,
        source_counts=source_counts,
    )
    taste.save()
    print(f"[taste_vector] Centroid built from {len(loved_ids)} tracks "
          f"(foobar={source_counts['foobar_loved']}, "
          f"temp={source_counts['desktop_temp']})")
    return taste


def _path_id(path: Path) -> str:
    import hashlib
    return hashlib.sha1(str(path).encode()).hexdigest()


def _load_vector_for_path(db: Any, path: Path) -> list[float] | None:
    """Try to load the feature vector for a given file path from the DB."""
    try:
        track_id = _path_id(path)
        ids, mat = db.load_all_vectors(FEATURE_VECTOR_VERSION)
        if track_id in ids:
            idx = ids.index(track_id)
            if _HAS_NP:
                import numpy as np
                return mat[idx].tolist()
            return list(mat[idx])
    except Exception:
        pass
    return None
