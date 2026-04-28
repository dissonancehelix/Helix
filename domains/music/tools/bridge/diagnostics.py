"""
diagnostics.py — Bridge health check and contract verification.

Run directly to verify both planes are operational:
  python -m domains.music.tools.bridge.diagnostics

Or import and call:
  from domains.music.tools.bridge.diagnostics import run_diagnostics
  report = run_diagnostics()
  print(report.render())
"""
from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .bridge import HelixBridge
from .metadata_adapter import EXTERNAL_TAGS_DB


@dataclass
class DiagnosticsReport:
    # Metadata plane
    db_path: str
    db_exists: bool
    db_track_count: int
    db_read_ok: bool
    db_sample_title: str
    db_read_ms: float

    # Runtime plane
    beefweb_reachable: bool
    beefweb_url: str
    playback_state: str
    runtime_read_ms: float

    # Identity resolution
    now_playing_title: Optional[str]
    now_playing_resolved: Optional[bool]
    resolution_ms: Optional[float]

    # Overall
    warnings: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.db_exists and self.db_read_ok

    def render(self) -> str:
        lines = [
            "=" * 60,
            "  Helix Music Bridge — Diagnostics",
            "=" * 60,
            "",
            "[ Metadata Plane — external-tags.db ]",
            f"  path        : {self.db_path}",
            f"  exists      : {'YES' if self.db_exists else 'NO — not found'}",
        ]
        if self.db_exists:
            lines += [
                f"  readable    : {'YES' if self.db_read_ok else 'NO — read failed'}",
                f"  tracks      : {self.db_track_count:,}",
                f"  read time   : {self.db_read_ms:.0f} ms",
            ]
            if self.db_sample_title:
                lines.append(f"  sample      : \"{self.db_sample_title}\"")

        lines += [
            "",
            "[ Runtime Plane — Beefweb ]",
            f"  endpoint    : {self.beefweb_url}",
            f"  reachable   : {'YES' if self.beefweb_reachable else 'NO — Foobar not running?'}",
        ]
        if self.beefweb_reachable:
            lines += [
                f"  playback    : {self.playback_state}",
                f"  read time   : {self.runtime_read_ms:.0f} ms",
            ]

        if self.now_playing_title:
            resolved_str = "resolved" if self.now_playing_resolved else "UNRESOLVED (not in metadata plane)"
            lines += [
                "",
                "[ Identity Resolution ]",
                f"  now playing : \"{self.now_playing_title}\"",
                f"  status      : {resolved_str}",
                f"  resolve ms  : {self.resolution_ms:.0f} ms",
            ]

        if self.warnings:
            lines += ["", "[ Warnings ]"]
            for w in self.warnings:
                lines.append(f"  ! {w}")

        lines += [
            "",
            f"  Overall: {'OK' if self.healthy else 'DEGRADED'}",
            "=" * 60,
        ]
        return "\n".join(lines)


def run_diagnostics(
    beefweb_url: str = "http://localhost:8880",
    beefweb_username: str = None,
    beefweb_password: str = None,
) -> DiagnosticsReport:
    warnings = []

    # --- Metadata plane ---
    db_path = str(EXTERNAL_TAGS_DB)
    db_exists = EXTERNAL_TAGS_DB.exists()
    db_read_ok = False
    db_track_count = 0
    db_sample_title = ""
    db_read_ms = 0.0

    if db_exists:
        t0 = time.monotonic()
        try:
            import sqlite3
            con = sqlite3.connect(db_path)
            db_track_count = con.execute(
                "SELECT COUNT(*) FROM tags WHERE path LIKE 'file://%'"
            ).fetchone()[0]
            # Grab one sample row to verify decode works
            row = con.execute(
                "SELECT path, meta FROM tags WHERE path LIKE 'file://%' LIMIT 1"
            ).fetchone()
            con.close()
            db_read_ok = True
            db_read_ms = (time.monotonic() - t0) * 1000

            if row:
                from .metadata_adapter import _row_to_meta
                sample = _row_to_meta(row[0], row[1])
                if sample:
                    db_sample_title = sample.title
        except Exception as e:
            warnings.append(f"external-tags.db read error: {e}")
    else:
        warnings.append(f"external-tags.db not found at: {db_path}")

    # --- Runtime plane ---
    t1 = time.monotonic()
    bridge = HelixBridge(beefweb_url=beefweb_url)
    runtime_state = bridge.runtime.state()
    runtime_read_ms = (time.monotonic() - t1) * 1000
    beefweb_reachable = runtime_state.is_live
    playback_state = runtime_state.playback_state

    if not beefweb_reachable:
        warnings.append("Beefweb not reachable — is Foobar2000 running with Beefweb enabled?")

    # --- Identity resolution (only if something is playing) ---
    now_playing_title = None
    now_playing_resolved = None
    resolution_ms = None

    if runtime_state.track:
        t2 = time.monotonic()
        resolved = bridge.get_now_playing()
        resolution_ms = (time.monotonic() - t2) * 1000
        if resolved:
            now_playing_title = resolved.title
            now_playing_resolved = resolved.resolved
            if not resolved.resolved:
                warnings.append(
                    f"Now-playing track not found in external-tags.db: {runtime_state.track.file_path}"
                )

    if db_track_count == 0 and db_exists:
        warnings.append("external-tags.db exists but contains no file:// entries — has foobar been indexed?")

    return DiagnosticsReport(
        db_path=db_path,
        db_exists=db_exists,
        db_track_count=db_track_count,
        db_read_ok=db_read_ok,
        db_sample_title=db_sample_title,
        db_read_ms=db_read_ms,
        beefweb_reachable=beefweb_reachable,
        beefweb_url=beefweb_url,
        playback_state=playback_state,
        runtime_read_ms=runtime_read_ms,
        now_playing_title=now_playing_title,
        now_playing_resolved=now_playing_resolved,
        resolution_ms=resolution_ms,
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only music bridge diagnostics.")
    parser.add_argument("--beefweb-url", default="http://localhost:8880")
    args = parser.parse_args()
    report = run_diagnostics(beefweb_url=args.beefweb_url)
    print(report.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

