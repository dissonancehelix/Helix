"""
adapter_vgmstream.py — Helix adapter for vgmstream
====================================================
Wraps the vgmstream CLI decoding path used as fallback inside:
    domains/music/model/measurement_synthesis/gme_bridge.py

Purpose:
    Decode broad game audio formats that neither libvgm nor gme handles
    (FLAC, MP3, OGG, OPUS, WAV, M4A, APE, WV, and many proprietary formats)
    and extract an amplitude-envelope proxy as a ControlSequence.

Input:
    file_path (str | Path)  — audio file path
    sample_rate (int)       — target decoding sample rate (default: 44100)

Output (dict — ControlSequence schema):
    {
        "format":           str,
        "chip_target":      "pcm",     # rendered audio, no register-level data
        "event_count":      int,
        "timing_data":      list[float],
        "register_writes":  list[dict],  # amplitude envelope proxy events
        "sample_rate":      int,
        "source_path":      str,
        "adapter":          "vgmstream",
        "bridge_mode":      "vgmstream" | "unavailable",
    }

Adapter rules:
    • No Helix logic.
    • Returns unavailable ControlSequence if vgmstream binary missing.
    • Amplitude envelope proxy: synthetic "volume" events from WAV PCM.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AdapterError(Exception):
    pass


class Adapter:
    """
    Adapter wrapping the vgmstream CLI decode path.

    Correct call path:
        HIL → INGEST_TRACK operator → Adapter → vgmstream CLI → WAV → envelope
    """
    toolkit = "vgmstream"
    substrate = "music"

    # Audio formats vgmstream can decode
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
        ".flac", ".mp3", ".ogg", ".wav", ".m4a", ".opus", ".ape", ".wv",
        ".2sf", ".ncsf", ".usf", ".gsf",
        ".psf", ".psf2", ".ssf", ".dsf", ".s98",
        ".minipsf", ".minipsf2",
    })

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Decode an audio file via vgmstream and extract an amplitude envelope proxy.
        """
        file_path = payload.get("file_path")
        sample_rate = payload.get("sample_rate", 44100)
        
        path = Path(file_path)
        ext  = path.suffix.lower()

        try:
            from domains.music.measurement_synthesis.gme_bridge import GmeBridge
            bridge = GmeBridge()
            events = bridge.render(path, sample_rate=sample_rate)
            mode   = "vgmstream"
        except ImportError:
            events = []
            mode   = "unavailable"
        except Exception as exc:
            raise AdapterError(f"vgmstream decode failed for {path}: {exc}") from exc

        return self.normalize(events, path, ext, sample_rate, mode)

    def normalize(
        self,
        events: list[Any],
        path: Path,
        ext: str,
        sample_rate: int,
        mode: str,
    ) -> dict[str, Any]:
        return {
            "format":          ext.lstrip("."),
            "chip_target":     "pcm",
            "event_count":     len(events),
            "timing_data":     [float(getattr(e, "time", 0.0)) for e in events][:1000],
            "register_writes": [
                {
                    "chip":     "pcm",
                    "channel":  getattr(e, "channel", 0),
                    "register": "amplitude",
                    "value":    getattr(e, "value", None),
                    "time":     float(getattr(e, "time", 0.0)),
                }
                for e in events
            ],
            "sample_rate":  sample_rate,
            "source_path":  str(path),
            "adapter":      "vgmstream",
            "bridge_mode":  mode,
        }

    def is_available(self) -> bool:
        try:
            from domains.music.measurement_synthesis.gme_bridge import GmeBridge
            b = GmeBridge()
            return b.is_available()
        except ImportError:
            return False

