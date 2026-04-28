"""
faiss_index.py — FAISS vector index with scipy KDTree fallback
==============================================================
Abstracts over faiss-cpu (preferred) and scipy.spatial.cKDTree (fallback).
When neither is installed, returns [] from query().

API
---
build_index(track_ids: list[str], vectors: list | np.ndarray,
            index_path: Path | None = None) -> VectorIndex
    Build and optionally persist an index.

load_index(index_path: Path) -> VectorIndex
    Load a persisted index.

class VectorIndex:
    .query(vec, k: int = 10) -> list[tuple[str, float]]
        Returns [(track_id, distance), …] sorted by ascending distance.
    .save(path: Path) -> None
    .size -> int
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _HAS_NP = False

try:
    import faiss as _faiss
    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False

try:
    from scipy.spatial import cKDTree as _cKDTree
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


# ---------------------------------------------------------------------------
# VectorIndex
# ---------------------------------------------------------------------------

class VectorIndex:
    """Unified wrapper around faiss or scipy KDTree."""

    def __init__(
        self,
        track_ids: list[str],
        vectors: Any,          # np.ndarray or list[list[float]]
        backend: str = "auto",
    ) -> None:
        self._ids = list(track_ids)
        self._backend: str
        self._index: Any = None
        self._mat: Any = None  # for scipy fallback

        if _HAS_NP:
            import numpy as np
            mat = np.array(vectors, dtype=np.float32)
        else:
            mat = vectors

        if backend == "auto":
            if _HAS_FAISS and _HAS_NP:
                backend = "faiss"
            elif _HAS_SCIPY and _HAS_NP:
                backend = "scipy"
            else:
                backend = "none"

        self._backend = backend

        if self._backend == "faiss" and _HAS_FAISS and _HAS_NP:
            import numpy as np
            dim = mat.shape[1] if hasattr(mat, "shape") else len(mat[0])
            idx = _faiss.IndexFlatL2(dim)
            idx.add(mat)                          # type: ignore[arg-type]
            self._index = idx
        elif self._backend == "scipy" and _HAS_SCIPY and _HAS_NP:
            self._index = _cKDTree(mat)
            self._mat   = mat
        else:
            self._mat = mat  # linear scan fallback

    # ------------------------------------------------------------------

    def query(self, vec: Any, k: int = 10) -> list[tuple[str, float]]:
        """Return [(track_id, distance), …] (k nearest neighbours)."""
        if not self._ids:
            return []

        k = min(k, len(self._ids))

        if self._backend == "faiss" and self._index is not None and _HAS_NP:
            import numpy as np
            q = np.array([vec], dtype=np.float32)
            distances, indices = self._index.search(q, k)
            return [
                (self._ids[int(i)], float(d))
                for d, i in zip(distances[0], indices[0])
                if 0 <= i < len(self._ids)
            ]

        if self._backend == "scipy" and self._index is not None and _HAS_NP:
            import numpy as np
            q = np.array(vec, dtype=np.float32)
            distances, indices = self._index.query(q, k=k)
            if not hasattr(distances, "__iter__"):
                distances = [distances]
                indices   = [indices]
            return [
                (self._ids[int(i)], float(d))
                for d, i in zip(distances, indices)
                if 0 <= i < len(self._ids)
            ]

        # Linear scan fallback
        if _HAS_NP and self._mat is not None:
            import numpy as np
            q   = np.array(vec, dtype=np.float32)
            mat = np.array(self._mat, dtype=np.float32)
            dists = np.sum((mat - q) ** 2, axis=1)
            idxs  = np.argsort(dists)[:k]
            return [(self._ids[int(i)], float(dists[i])) for i in idxs]

        return []

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ids":     self._ids,
            "backend": self._backend,
        }
        if self._backend == "faiss" and self._index is not None and _HAS_FAISS:
            faiss_path = path.with_suffix(".faiss")
            _faiss.write_index(self._index, str(faiss_path))
            data["faiss_path"] = str(faiss_path)
            path.write_text(json.dumps(data))
        else:
            with open(path, "wb") as f:
                pickle.dump({"ids": self._ids, "mat": self._mat, "backend": self._backend}, f)

    @property
    def size(self) -> int:
        return len(self._ids)


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def build_index(
    track_ids: list[str],
    vectors: Any,
    index_path: Path | None = None,
    backend: str = "auto",
) -> VectorIndex:
    idx = VectorIndex(track_ids, vectors, backend=backend)
    if index_path is not None:
        idx.save(index_path)
    return idx


def load_index(index_path: Path) -> VectorIndex:
    """Load a persisted index.  Returns empty index on any error."""
    try:
        # Try pickle first
        with open(index_path, "rb") as f:
            data = pickle.load(f)
        return VectorIndex(data["ids"], data["mat"], backend=data.get("backend", "auto"))
    except Exception:
        pass

    try:
        # JSON + faiss sidecar
        meta = json.loads(index_path.read_text())
        faiss_path = Path(meta["faiss_path"])
        if _HAS_FAISS and faiss_path.exists():
            idx_obj = _faiss.read_index(str(faiss_path))
            vi = VectorIndex.__new__(VectorIndex)
            vi._ids     = meta["ids"]
            vi._backend = "faiss"
            vi._index   = idx_obj
            vi._mat     = None
            return vi
    except Exception:
        pass

    return VectorIndex([], [], backend="none")
