"""
adapter_vgm_cnt.py — Helix adapter for vgm_cnt (vgmtools)
==========================================================
Tier B: Requires compiled vgm_cnt binary.
Source reference: domains/music/toolkits/vgmtools/vgm_cnt.c

Purpose:
    Run vgm_cnt on a VGM/VGZ file and parse its per-chip command
    frequency statistics into a structured channel_usage dict for
    the UMO causal layer.

    vgm_cnt counts register writes per chip, key-on/off transitions
    per channel, and volume state changes — producing a fast structural
    summary without a full register timeline.

    Degrades gracefully: returns empty stats if binary not available.

Input (payload dict):
    file_path (str | Path)

Output (dict):
    {
        "chip_command_counts": dict,   # chip_name -> total register writes
        "channel_stats":       dict,   # chip -> {ch -> {key_ons, key_offs, vol_changes}}
        "active_chips":        list,   # chips with nonzero write counts
        "source_path":         str,
        "bridge_mode":         str,    # "vgm_cnt" | "unavailable"
        "adapter":             "vgm_cnt",
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


_BINARY_CANDIDATES = ["vgm_cnt", "vgm_cnt.exe"]
_TOOLKIT_DIR = Path(__file__).parent.parent.parent / "substrates" / "music" / "toolkits" / "vgmtools"

# vgm_cnt output patterns (approximate — format varies by version):
#   YM2612:  1234 writes
#   SN76489:  456 writes
#   YM2612 Ch0: 12 key-ons, 12 key-offs
_CHIP_WRITES_RE  = re.compile(r"^([\w/]+):\s+(\d+)\s+writes?", re.IGNORECASE)
_CHAN_KEYON_RE   = re.compile(r"^([\w/]+)\s+Ch(\d+):\s+(\d+)\s+key.?on", re.IGNORECASE)


class Adapter:
    """
    Tier B adapter wrapping vgm_cnt for per-chip command frequency analysis.
    """
    toolkit  = "vgm_cnt"
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
            return self.normalize({}, {}, path, "unavailable")

        raw_output = self._run(binary, path)
        chip_counts, channel_stats = self._parse(raw_output)
        return self.normalize(chip_counts, channel_stats, path, "vgm_cnt")

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
            raise AdapterError(f"vgm_cnt timed out on {vgm_path}")
        except Exception as exc:
            raise AdapterError(f"vgm_cnt failed: {exc}") from exc

    def _parse(
        self, text: str
    ) -> tuple[dict[str, int], dict[str, dict]]:
        chip_counts: dict[str, int] = {}
        channel_stats: dict[str, dict] = {}

        for line in text.splitlines():
            line = line.strip()

            m = _CHIP_WRITES_RE.match(line)
            if m:
                chip_counts[m.group(1)] = int(m.group(2))
                continue

            m = _CHAN_KEYON_RE.match(line)
            if m:
                chip = m.group(1)
                ch   = int(m.group(2))
                kons = int(m.group(3))
                if chip not in channel_stats:
                    channel_stats[chip] = {}
                channel_stats[chip][str(ch)] = {"key_ons": kons}

        return chip_counts, channel_stats

    def normalize(
        self,
        chip_counts: dict[str, int],
        channel_stats: dict[str, dict],
        path: Path,
        bridge_mode: str,
    ) -> dict[str, Any]:
        active = [chip for chip, count in chip_counts.items() if count > 0]
        return {
            "chip_command_counts": chip_counts,
            "channel_stats":       channel_stats,
            "active_chips":        active,
            "source_path":         str(path),
            "bridge_mode":         bridge_mode,
            "adapter":             "vgm_cnt",
        }
