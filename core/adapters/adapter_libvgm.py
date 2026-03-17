"""
adapter_libvgm.py — Helix adapter for libvgm (ValleyBell/libvgm)
=================================================================
Wraps the libvgm ctypes bridge at:
    substrates/music/measurement_synthesis/libvgm_bridge.py

Purpose:
    Render VGM/VGZ files through the libvgm emulator and extract
    chip register-write events as a structured ControlSequence.

Input:
    file_path (str | Path)  — path to .vgm or .vgz file
    sample_rate (int)       — sample rate for emulation (default: 44100)

Output (dict — ControlSequence schema):
    {
        "format":          "vgm" | "vgz",
        "chip_target":     str,        # primary chip detected
        "event_count":     int,
        "timing_data":     list[float],  # event timestamps (seconds)
        "register_writes": list[dict],   # {chip, channel, register, value, time}
        "sample_rate":     int,
        "source_path":     str,
        "adapter":         "libvgm",
        "bridge_mode":     "emulated" | "fallback",
    }

Adapter rules:
    • Does NOT import from core/operators/, core/semantics/, or core/compiler/.
    • Normalizes inputs before calling the bridge.
    • Returns structured dicts only.
    • Raises AdapterError on unrecoverable failures.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    """Raised when an adapter cannot process its input."""


class Adapter:
    """
    Adapter wrapping libvgm_bridge for VGM/VGZ emulation.

    Correct call path:
        HIL → INGEST_TRACK operator → Adapter → libvgm_bridge
    """
    toolkit = "libvgm"
    substrate = "music"

    # Supported input extensions
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".vgm", ".vgz"})

    def supports(self, file_path: str | Path) -> bool:
        """Return True if this adapter handles the given file format."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Render a VGM/VGZ file and return a ControlSequence dict.

        Args:
            payload: Dict containing 'file_path' and 'sample_rate'.

        Returns:
            ControlSequence dict compatible with Atlas schema.

        Raises:
            AdapterError: if file does not exist or format is unsupported.
        """
        file_path = payload.get("file_path")
        sample_rate = payload.get("sample_rate", 44100)
        
        path = self._normalize_path(file_path)
        fmt  = path.suffix.lower().lstrip(".")

        try:
            from substrates.music.measurement_synthesis.libvgm_bridge import (
                LibvgmBridge,
            )
            bridge = LibvgmBridge()
            events = bridge.render(path, sample_rate=sample_rate)
            bridge_mode = "emulated" if bridge.is_available() else "fallback"
        except ImportError as exc:
            raise AdapterError(f"libvgm_bridge not available: {exc}") from exc
        except Exception as exc:
            raise AdapterError(f"libvgm render failed for {path}: {exc}") from exc

        return self.normalize(events, path, fmt, sample_rate, bridge_mode)

    def is_available(self) -> bool:
        """Return True if the underlying bridge is importable."""
        try:
            from substrates.music.measurement_synthesis.libvgm_bridge import LibvgmBridge  # noqa
            return True
        except ImportError:
            return False

    # ── Private helpers ────────────────────────────────────────────────────

    def _normalize_path(self, file_path: str | Path) -> Path:
        path = Path(file_path)
        if not path.exists():
            raise AdapterError(f"File not found: {path}")
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise AdapterError(
                f"Unsupported format {path.suffix!r}. "
                f"LibvgmAdapter handles: {sorted(self.SUPPORTED_EXTENSIONS)}"
            )
        return path

    def normalize(
        self,
        events: list[Any],
        path: Path,
        fmt: str,
        sample_rate: int,
        bridge_mode: str,
    ) -> dict[str, Any]:
        """Convert raw ChipEvent list into ControlSequence dict."""
        register_writes: list[dict] = []
        timing_data:     list[float] = []
        chip_targets:    set[str]    = set()

        for ev in events:
            chip = getattr(ev, "chip", "unknown")
            chip_targets.add(str(chip))
            t = float(getattr(ev, "time", 0.0))
            timing_data.append(t)
            register_writes.append({
                "chip":      str(chip),
                "channel":   getattr(ev, "channel",  0),
                "operator":  getattr(ev, "operator", None),
                "register":  getattr(ev, "register", None),
                "value":     getattr(ev, "value",    None),
                "time":      t,
            })

        return {
            "format":          fmt,
            "chip_target":     ", ".join(sorted(chip_targets)) or "unknown",
            "event_count":     len(events),
            "timing_data":     timing_data[:1000],  # cap for serialization
            "register_writes": register_writes,
            "sample_rate":     sample_rate,
            "source_path":     str(path),
            "adapter":         "libvgm",
            "bridge_mode":     bridge_mode,
        }
