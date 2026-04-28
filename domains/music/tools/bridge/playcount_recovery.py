"""
playcount_recovery.py — Phase 11: Playcount Recovery and HELIX_IMPORT_* fields.

Purpose:
  Remap old listening history onto current local tracks.
  Recover continuity lost by title normalization and translation changes.
  Project import fields into foobar via external-tags.db for review.

Output fields (projected into foobar metadata plane as HELIX_IMPORT_*):
  HELIX_IMPORT_PLAYCOUNT      — best-available historical play count
  HELIX_IMPORT_FIRST_PLAYED   — earliest known play (ISO timestamp)
  HELIX_IMPORT_LAST_PLAYED    — most recent known play (ISO timestamp)
  HELIX_IMPORT_LOVED          — loved state (1 / 0)
  HELIX_IMPORT_SOURCE         — which source provided this data
  HELIX_IMPORT_CONFIDENCE     — confidence in the match (0.0–1.0)

Policy rules (from helix_music_local_handoff.md):
  - Do NOT revert good titles to legacy names just to preserve stats.
  - Local tracks are curated — no naive 1:1 reliance on public tracklists.
  - Deleted short tracks / commercials / voice lines are expected gaps.
  - Stats should survive title improvements.

Status: SCAFFOLD — structure and types defined, matching logic stubbed.
        Implement matching in Phase 11 proper after bridge is verified.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
IMPORT_REPORT_PATH = HELIX_ROOT / "domains/music/model/reports/playcount_recovery_report.json"

# Fields projected into foobar via external-tags.db
IMPORT_FIELDS = [
    "HELIX_IMPORT_PLAYCOUNT",
    "HELIX_IMPORT_FIRST_PLAYED",
    "HELIX_IMPORT_LAST_PLAYED",
    "HELIX_IMPORT_LOVED",
    "HELIX_IMPORT_SOURCE",
    "HELIX_IMPORT_CONFIDENCE",
]


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------

@dataclass
class ImportRecord:
    """
    A resolved playcount import for one track.
    Produced by the recovery engine; projected into foobar as HELIX_IMPORT_* tags.
    """
    file_path: str
    playcount: int
    first_played: Optional[str]     # ISO 8601 or foobar timestamp string
    last_played: Optional[str]
    loved: bool
    source: str                     # "local_2003" | "lastfm" | "listenbrainz" | "fused"
    confidence: float               # 0.0–1.0
    match_method: str               # "exact_path" | "title_artist" | "fuzzy" | "manual"
    notes: str = ""

    def to_foobar_fields(self) -> dict:
        """Return the dict of HELIX_IMPORT_* fields ready for external-tags.db write."""
        return {
            "HELIX_IMPORT_PLAYCOUNT":   str(self.playcount),
            "HELIX_IMPORT_FIRST_PLAYED": self.first_played or "",
            "HELIX_IMPORT_LAST_PLAYED":  self.last_played or "",
            "HELIX_IMPORT_LOVED":        "1" if self.loved else "0",
            "HELIX_IMPORT_SOURCE":       self.source,
            "HELIX_IMPORT_CONFIDENCE":   f"{self.confidence:.2f}",
        }


@dataclass
class RecoveryReport:
    """Summary of a playcount recovery pass."""
    run_at: str
    total_library_tracks: int
    matched: int
    unmatched: int
    high_confidence: int        # confidence >= 0.85
    low_confidence: int         # confidence < 0.50
    priority_review: list[str]  # file paths needing manual review
    records: list[ImportRecord] = field(default_factory=list)

    def save(self, path: Path = IMPORT_REPORT_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "run_at": self.run_at,
            "stats": {
                "total": self.total_library_tracks,
                "matched": self.matched,
                "unmatched": self.unmatched,
                "high_confidence": self.high_confidence,
                "low_confidence": self.low_confidence,
            },
            "priority_review": self.priority_review,
            "records": [
                {
                    "file_path": r.file_path,
                    "playcount": r.playcount,
                    "first_played": r.first_played,
                    "last_played": r.last_played,
                    "loved": r.loved,
                    "source": r.source,
                    "confidence": r.confidence,
                    "match_method": r.match_method,
                    "notes": r.notes,
                }
                for r in self.records
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Recovery report saved: {path}")


# ---------------------------------------------------------------------------
# Recovery engine (Phase 11 — to be implemented)
# ---------------------------------------------------------------------------

class PlaycountRecoveryEngine:
    """
    Matches library tracks to historical play data and produces ImportRecords.

    Phase 11 implementation plan:
      1. Load signal sources (Playcount 2003 JSON, Last.fm JSON, ListenBrainz)
         via domains.music.signals.signal_sources
      2. Load library via bridge.metadata.library()
      3. For each library track:
         a. Exact path match against Playcount 2003 index
         b. Title + artist match against Last.fm scrobble index
         c. Fuzzy title match for tracks renamed since scrobbling
      4. Fuse matched signals into ImportRecord (use SignalFuser logic)
      5. Flag low-confidence and divergent matches for priority review
      6. Write HELIX_IMPORT_* fields via foobar_projector (Phase 14 writeback)
         or export to report for manual review first

    Key constraint: SPC/VGM track titles in library may differ from what
    Last.fm scrobbled (e.g. "Marble Zone" vs "Sonic the Hedgehog - Marble Zone").
    Use normalized key matching (strip game prefix, lowercase, strip punctuation).
    """

    def __init__(self):
        # Lazy imports — signal sources are optional dependencies
        self._sources_loaded = False

    def _ensure_sources(self):
        if self._sources_loaded:
            return
        try:
            from domains.music.tools.pipeline.signal_sources import (
                PlaycountSource, LastFmSignalSource
            )
            from domains.music.tools.bridge.bridge import HelixBridge
            self._playcount_source = PlaycountSource()
            self._lastfm_source = LastFmSignalSource()
            self._bridge = HelixBridge()
            self._sources_loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load signal sources: {e}") from e

    def run(self, dry_run: bool = True) -> RecoveryReport:
        """
        Run the playcount recovery pass.

        dry_run=True  — build report but do not write to external-tags.db
        dry_run=False — project HELIX_IMPORT_* fields (Phase 14 writeback gate)
        """
        # SCAFFOLD: full implementation in Phase 11
        # For now, return a report skeleton so the structure is exercisable.
        return RecoveryReport(
            run_at=datetime.now(timezone.utc).isoformat(),
            total_library_tracks=0,
            matched=0,
            unmatched=0,
            high_confidence=0,
            low_confidence=0,
            priority_review=[],
            records=[],
        )


# ---------------------------------------------------------------------------
# Normalize helpers (shared with Phase 12 alias work)
# ---------------------------------------------------------------------------

def normalize_key(s: str) -> str:
    """
    Canonical matching key for title/artist strings.
    Strips game-prefix patterns, punctuation, articles, and collapses whitespace.
    E.g. "Sonic the Hedgehog - Marble Zone" → "marble zone"
    """
    import re
    s = s.lower()
    # Strip common game-prefix patterns like "Game Name - Track Title"
    if " - " in s:
        s = s.split(" - ", 1)[-1]
    # Strip articles
    s = re.sub(r"^(the|a|an)\s+", "", s)
    # Strip punctuation
    s = re.sub(r"[^\w\s]", " ", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


if __name__ == "__main__":
    engine = PlaycountRecoveryEngine()
    report = engine.run(dry_run=True)
    print(f"Phase 11 scaffold — {report.total_library_tracks} tracks, {report.matched} matched")
    print("(Full implementation pending Phase 11)")

