"""
run_log.py — Phase 4 run tracking and auditability.

Every Phase 4 invocation produces a run record with:
- stable run_id (timestamp + short random suffix)
- timing
- source record counts
- match/validation/refresh candidate counts
- outputs written
- warnings/errors

Logs are written to artifacts/runs/<run_id>/run_log.json.
"""

from __future__ import annotations

import json
import random
import string
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_FOOBAR_ROOT = Path(__file__).resolve().parents[3] / "domains" / "music" / "tools" / "foobar"
_RUNS_DIR = _FOOBAR_ROOT / "artifacts" / "runs"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _short_id(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


class RunLog:
    """
    Tracks a single Phase 4 execution.

    Usage:
        log = RunLog()
        log.start()
        log.record("source_counts", {"library": 122000, "lastfm": 201368})
        log.warn("metadb.sqlite not found, fell back to filesystem scan")
        log.finish()
        log.write()
    """

    def __init__(self, run_id: str | None = None, label: str = "phase4"):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.run_id = run_id or f"{label}_{ts}_{_short_id()}"
        self.label = label
        self.run_dir = _RUNS_DIR / self.run_id
        self._data: dict[str, Any] = {
            "run_id":     self.run_id,
            "label":      label,
            "started_at": None,
            "finished_at": None,
            "duration_sec": None,
            "status": "started",
            "source_counts": {},
            "match_counts": {},
            "validation_counts": {},
            "refresh_counts": {},
            "corpus_counts": {},
            "outputs_written": [],
            "warnings": [],
            "errors": [],
            "metadata": {},
        }
        self._start_ts: float = 0.0

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------

    def start(self) -> "RunLog":
        self._start_ts = time.monotonic()
        self._data["started_at"] = _now_iso()
        print(f"[run:{self.run_id}] Phase 4 started")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return self

    def finish(self, status: str = "complete") -> "RunLog":
        elapsed = time.monotonic() - self._start_ts
        self._data["finished_at"] = _now_iso()
        self._data["duration_sec"] = round(elapsed, 2)
        self._data["status"] = status
        print(f"[run:{self.run_id}] Finished in {elapsed:.1f}s — status: {status}")
        return self

    def error(self, msg: str) -> "RunLog":
        self._data["errors"].append({"ts": _now_iso(), "msg": msg})
        print(f"[run:{self.run_id}] ERROR: {msg}")
        return self

    def warn(self, msg: str) -> "RunLog":
        self._data["warnings"].append({"ts": _now_iso(), "msg": msg})
        print(f"[run:{self.run_id}] WARN: {msg}")
        return self

    # -----------------------------------------------------------------------
    # Count tracking
    # -----------------------------------------------------------------------

    def record(self, category: str, counts: dict) -> "RunLog":
        """Record counts into a named category."""
        existing = self._data.get(category)
        if isinstance(existing, dict):
            existing.update(counts)
        else:
            self._data[category] = counts
        return self

    def add_output(self, path: Path | str) -> "RunLog":
        self._data["outputs_written"].append(str(path))
        return self

    def set_meta(self, key: str, value: Any) -> "RunLog":
        self._data["metadata"][key] = value
        return self

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def write(self) -> Path:
        """Write the run log to run_dir/run_log.json."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / "run_log.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, default=str)
        print(f"[run:{self.run_id}] Log written → {path}")
        return path

    def artifact_path(self, filename: str) -> Path:
        """Return a path inside the run directory for an artifact."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return self.run_dir / filename

    def write_artifact(self, filename: str, data: Any, *, indent: int = 2) -> Path:
        """Write a JSON artifact to the run directory."""
        path = self.artifact_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=str)
        self.add_output(path)
        return path

    @property
    def data(self) -> dict:
        return self._data
