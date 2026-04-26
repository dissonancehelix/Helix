"""
adapter_vgm_stat.py — Helix adapter for vgm_stat (vgmtools)
============================================================
Tier B: Requires compiled vgm_stat binary.
Source reference: domains/music/toolkits/vgmtools/vgm_stat.c

Purpose:
    Run vgm_stat on a VGM/VGZ file and parse its temporal statistics
    and GD3 metadata into a structured output usable for:
      - metadata.recorded population (GD3 fields, secondary to .tag)
      - temporal analysis (total length, loop point, loop length)

    Degrades gracefully: returns empty stats if binary not available.

Input (payload dict):
    file_path (str | Path)

Output (dict):
    {
        "duration_sec":    float,      # total play length in seconds
        "loop_start_sec":  float,      # loop start point in seconds (0 if no loop)
        "loop_length_sec": float,      # loop section length in seconds (0 if no loop)
        "has_loop":        bool,
        "gd3": {
            "title":    str,
            "game":     str,
            "system":   str,
            "author":   str,
            "date":     str,
            "creator":  str,
            "notes":    str,
        } | None,
        "source_path":  str,
        "bridge_mode":  str,           # "vgm_stat" | "unavailable"
        "adapter":      "vgm_stat",
    }
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


_BINARY_CANDIDATES = ["vgm_stat", "vgm_stat.exe"]
_TOOLKIT_DIR = Path(__file__).parent.parent.parent / "domains" / "music" / "toolkits" / "vgmtools"

# vgm_stat output format (approximate):
#   Length:    00:03:42.15  (13335 samples)
#   Loop:      00:01:23.00  (3630 samples)
#   Title:     Mystic Cave Zone
#   Author:    Masato Nakamura
_DURATION_RE = re.compile(r"Length\s*:\s*(\d+):(\d+):(\d+)\.(\d+)", re.IGNORECASE)
_LOOP_RE     = re.compile(r"Loop\s*:\s*(\d+):(\d+):(\d+)\.(\d+)", re.IGNORECASE)
_FIELD_RE    = re.compile(r"^(Title|Game|System|Author|Date|Creator|Notes)\s*:\s*(.+)$", re.IGNORECASE)

_GD3_FIELD_MAP = {
    "title":   "title",
    "game":    "game",
    "system":  "system",
    "author":  "author",
    "date":    "date",
    "creator": "creator",
    "notes":   "notes",
}


def _ts_to_sec(h: str, m: str, s: str, cs: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0


class Adapter:
    """
    Tier B adapter wrapping vgm_stat for temporal statistics extraction.
    """
    toolkit  = "vgm_stat"
    substrate = "music"

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".vgm", ".vgz"})

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        file_path = payload.get("file_path")
        if not file_path:
            raise AdapterError("Payload must contain 'file_path'")
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")

        binary = self._find_binary()
        if binary is None:
            return self.normalize(0.0, 0.0, 0.0, None, path, "unavailable")

        raw_output = self._run(binary, path)
        duration, loop_start, loop_length, gd3 = self._parse(raw_output)
        return self.normalize(duration, loop_start, loop_length, gd3, path, "vgm_stat")

    def is_available(self) -> bool:
        return self._find_binary() is not None

    def _find_binary(self) -> Path | None:
        for name in _BINARY_CANDIDATES:
            candidate = _TOOLKIT_DIR / name
            if candidate.exists():
                return candidate
        for name in _BINARY_CANDIDATES:
            found = shutil.which(name)
            if found:
                return Path(found)
        return None

    def _run(self, binary: Path, vgm_path: Path) -> str:
        try:
            result = subprocess.run(
                [str(binary), str(vgm_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            raise AdapterError(f"vgm_stat timed out on {vgm_path}")
        except Exception as exc:
            raise AdapterError(f"vgm_stat failed: {exc}") from exc

    def _parse(
        self, text: str
    ) -> tuple[float, float, float, dict[str, str] | None]:
        duration    = 0.0
        loop_start  = 0.0
        loop_length = 0.0
        gd3_fields: dict[str, str] = {}

        for line in text.splitlines():
            line = line.strip()

            m = _DURATION_RE.search(line)
            if m:
                duration = _ts_to_sec(*m.groups())
                continue

            m = _LOOP_RE.search(line)
            if m:
                loop_length = _ts_to_sec(*m.groups())
                continue

            m = _FIELD_RE.match(line)
            if m:
                key = m.group(1).lower()
                val = m.group(2).strip()
                if key in _GD3_FIELD_MAP and val:
                    gd3_fields[_GD3_FIELD_MAP[key]] = val

        # If we have a loop length but no duration, loop_start is ambiguous
        if loop_length and duration:
            loop_start = max(0.0, duration - loop_length)

        gd3 = gd3_fields if gd3_fields else None
        return duration, loop_start, loop_length, gd3

    def normalize(
        self,
        duration: float,
        loop_start: float,
        loop_length: float,
        gd3: dict[str, str] | None,
        path: Path,
        bridge_mode: str,
    ) -> dict[str, Any]:
        return {
            "duration_sec":    round(duration, 3),
            "loop_start_sec":  round(loop_start, 3),
            "loop_length_sec": round(loop_length, 3),
            "has_loop":        loop_length > 0,
            "gd3":             gd3,
            "source_path":     str(path),
            "bridge_mode":     bridge_mode,
            "adapter":         "vgm_stat",
        }
