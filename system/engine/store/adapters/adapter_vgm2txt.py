"""
adapter_vgm2txt.py — Helix adapter for vgm2txt (vgmtools)
==========================================================
Tier B: Requires compiled vgm2txt binary.
Source reference: model/domains/music/toolkits/vgmtools/vgm2txt.c

Purpose:
    Run vgm2txt on a VGM/VGZ file and parse its text output into
    structured causal.temporal_trajectories entries for the UMO.

    vgm2txt dumps every register write with a sample-accurate timestamp.
    This maps directly to the causal layer — it is the register timeline
    that causally determines every audible event.

    Degrades gracefully: if vgm2txt binary is not found, returns an
    empty trajectory list with bridge_mode = "unavailable".

Input (payload dict):
    file_path (str | Path)  — path to .vgm or .vgz file

Output (dict):
    {
        "format":               str,     # "vgm" or "vgz"
        "chip_target":          str,     # detected chip(s)
        "temporal_trajectories": list[dict],  # [{t, chip, register, value, decoded}]
        "event_count":          int,
        "duration_samples":     int,
        "source_path":          str,
        "bridge_mode":          str,     # "vgm2txt" | "unavailable"
        "adapter":              "vgm2txt",
    }

    Each trajectory entry:
        {
            "t":        float,   # timestamp in seconds (sample / 44100)
            "chip":     str,     # e.g. "YM2612", "SN76489"
            "port":     int | None,
            "register": int,
            "value":    int,
            "decoded":  str,     # vgm2txt human-readable description
        }

Adapter rules:
    • No Helix logic. No audio rendering.
    • Raises AdapterError on file-not-found.
    • Returns empty trajectories (not an error) when binary unavailable.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


# Typical vgm2txt output line patterns:
#   Pos 0x001234 (00:00.12): YM2612 Port 0 Reg 0x28 = 0xF0 ; Key-On ch0
#   Pos 0x001234 (00:00.12): SN76489 Ch 0 Freq 0x1A0 ; Tone
_LINE_RE = re.compile(
    r"Pos\s+0x[0-9A-Fa-f]+\s+\((\d+):(\d+)\.(\d+)\):\s+"
    r"([\w/\-]+)"            # chip name
    r"(.*?);\s*(.*)"         # rest ; decoded description
)

# Simpler fallback: extract register/value from the "rest" field
_REG_VAL_RE = re.compile(r"[Rr]eg\s+0x([0-9A-Fa-f]+)\s+=\s+0x([0-9A-Fa-f]+)")
_PORT_RE    = re.compile(r"[Pp]ort\s+(\d+)")

# Binary search order
_BINARY_CANDIDATES = ["vgm2txt", "vgm2txt.exe"]
_TOOLKIT_DIR = Path(__file__).parent.parent.parent / "domains" / "music" / "toolkits" / "vgmtools"
_SAMPLE_RATE = 44100  # VGM standard playback rate


class Adapter:
    """
    Tier B adapter wrapping vgm2txt for register timeline extraction.

    Degrades to unavailable (empty trajectories) when binary not built.
    """
    toolkit  = "vgm2txt"
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
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise AdapterError(f"Unsupported extension: {path.suffix!r}")

        binary = self._find_binary()
        if binary is None:
            return self.normalize([], path, "unavailable", 0)

        raw_output = self._run(binary, path)
        trajectories, duration_samples, chip_target = self._parse(raw_output)
        return self.normalize(trajectories, path, "vgm2txt", duration_samples, chip_target)

    def is_available(self) -> bool:
        return self._find_binary() is not None

    # ── Binary discovery ──────────────────────────────────────────────────────

    def _find_binary(self) -> Path | None:
        # 1. Check toolkit build output directory
        for name in _BINARY_CANDIDATES:
            candidate = _TOOLKIT_DIR / name
            if candidate.exists():
                return candidate
        # 2. PATH
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
                timeout=60,
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            raise AdapterError(f"vgm2txt timed out on {vgm_path}")
        except Exception as exc:
            raise AdapterError(f"vgm2txt failed: {exc}") from exc

    # ── Output parsing ────────────────────────────────────────────────────────

    def _parse(
        self, text: str
    ) -> tuple[list[dict[str, Any]], int, str]:
        trajectories: list[dict[str, Any]] = []
        chips_seen: set[str] = set()
        duration_samples = 0

        for line in text.splitlines():
            m = _LINE_RE.match(line.strip())
            if not m:
                continue

            minutes  = int(m.group(1))
            seconds  = int(m.group(2))
            centisec = int(m.group(3))
            t_sec = minutes * 60 + seconds + centisec / 100.0

            chip    = m.group(4).strip()
            rest    = m.group(5).strip()
            decoded = m.group(6).strip()

            chips_seen.add(chip)

            register: int | None = None
            value:    int | None = None
            port:     int | None = None

            rv = _REG_VAL_RE.search(rest)
            if rv:
                register = int(rv.group(1), 16)
                value    = int(rv.group(2), 16)

            pm = _PORT_RE.search(rest)
            if pm:
                port = int(pm.group(1))

            sample = int(t_sec * _SAMPLE_RATE)
            duration_samples = max(duration_samples, sample)

            entry: dict[str, Any] = {
                "t":        round(t_sec, 6),
                "chip":     chip,
                "port":     port,
                "register": register,
                "value":    value,
                "decoded":  decoded,
            }
            trajectories.append(entry)

        chip_target = ", ".join(sorted(chips_seen)) or "unknown"
        return trajectories, duration_samples, chip_target

    def normalize(
        self,
        trajectories: list[dict[str, Any]],
        path: Path,
        bridge_mode: str,
        duration_samples: int = 0,
        chip_target: str = "unknown",
    ) -> dict[str, Any]:
        return {
            "format":                path.suffix.lower().lstrip("."),
            "chip_target":           chip_target,
            "temporal_trajectories": trajectories,
            "event_count":           len(trajectories),
            "duration_samples":      duration_samples,
            "source_path":           str(path),
            "bridge_mode":           bridge_mode,
            "adapter":               "vgm2txt",
        }

