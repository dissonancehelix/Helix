"""
signal_record.py — SignalRecord: unified per-track listening evidence record.

One SignalRecord per track in the library.

Source model (Phase 6, revised 2026-03-29):
  Playcount 2003        → LOCAL_PLAYCOUNT, LOCAL_LOVED
  Last.fm JSON/Sync     → LASTFM_PLAYCOUNT, LASTFM_FIRST_PLAYED, LASTFM_LAST_PLAYED
  ListenBrainz          → LISTENBRAINZ_LISTEN_COUNT, LB_FIRST_LISTEN, LB_LAST_LISTEN
  Beefweb               → runtime interface only, not a data source

Enhanced Playback Statistics is NOT in scope — tested and dropped.
It adds only Last.fm-derived timestamps already covered by the Last.fm sources.

Missing source data is represented as None — never imputed.
Derived fields are computed by signal_fuser.py via playcount_reconciler.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ── Playcount Split State ─────────────────────────────────────────────────────

SPLIT_SYNCHRONIZED   = "synchronized"       # counts within ±15%
SPLIT_LOCAL_AHEAD    = "local_ahead"         # local > external by margin
SPLIT_LASTFM_AHEAD   = "lastfm_ahead"        # Last.fm > local by margin
SPLIT_LOCAL_ONLY     = "local_only"          # no external data, local > 0
SPLIT_LASTFM_ONLY    = "lastfm_only"         # local = 0/None, Last.fm > 0
SPLIT_BOTH_ZERO      = "both_zero"           # no plays anywhere
SPLIT_DIVERGENT      = "divergent"           # > 50% relative discrepancy
SPLIT_UNRESOLVABLE   = "unresolvable"        # conflicting, no winner

SPLIT_STATES = frozenset({
    SPLIT_SYNCHRONIZED, SPLIT_LOCAL_AHEAD, SPLIT_LASTFM_AHEAD,
    SPLIT_LOCAL_ONLY, SPLIT_LASTFM_ONLY, SPLIT_BOTH_ZERO,
    SPLIT_DIVERGENT, SPLIT_UNRESOLVABLE,
})


# ── Timeline Completeness ─────────────────────────────────────────────────────

COMPLETENESS_FULL       = "full"          # multi-source with timestamps
COMPLETENESS_HIGH       = "high"          # one external source with full timeline
COMPLETENESS_PARTIAL    = "partial"       # one external source, sparse timeline
COMPLETENESS_COUNT_ONLY = "count_only"    # counts known, no timestamps
COMPLETENESS_NONE       = "none"          # no signal at all


# ── SignalRecord ──────────────────────────────────────────────────────────────

@dataclass
class SignalRecord:
    """
    Unified per-track listening signal record.
    track_id must match the codex entity ID: music.track:<slug>
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    track_id:   str
    artist_key: str
    title_key:  str
    album_key:  str

    # ── Raw: Playcount 2003 ───────────────────────────────────────────────────
    local_playcount:    Optional[int]  = None
    local_loved:        Optional[bool] = None
    local_first_played: Optional[int]  = None   # 2003_first_played (Unix ms)
    local_last_played:  Optional[int]  = None   # 2003_last_played (Unix ms)
    local_added:        Optional[int]  = None   # 2003_added (Unix ms)

    # ── Raw: Last.fm (JSON history + Playcount Sync) ──────────────────────────
    lastfm_playcount:    Optional[int] = None
    lastfm_first_played: Optional[int] = None   # Unix ms
    lastfm_last_played:  Optional[int] = None   # Unix ms

    # ── Raw: ListenBrainz ─────────────────────────────────────────────────────
    listenbrainz_listen_count: Optional[int] = None
    listenbrainz_first_listen: Optional[int] = None  # Unix ms
    listenbrainz_last_listen:  Optional[int] = None  # Unix ms

    # ── Derived ───────────────────────────────────────────────────────────────
    lifetime_signal_score:             Optional[float] = None  # 0–100
    historical_confidence:             Optional[float] = None  # 0–1
    playcount_split_state:             Optional[str]   = None
    active_rotation_score:             Optional[float] = None  # 0–1
    local_only_signal:                 bool = False
    lastfm_only_signal:                bool = False
    timeline_completeness:             Optional[str]   = None
    priority_reconciliation_candidate: bool = False

    # ── Source coverage ───────────────────────────────────────────────────────
    has_local_playcount:     bool = False
    has_lastfm_data:         bool = False
    has_listenbrainz_data:   bool = False

    def total_evidence_plays(self) -> int:
        """Best available total play count across all sources."""
        return max(
            self.local_playcount              or 0,
            self.lastfm_playcount             or 0,
            self.listenbrainz_listen_count    or 0,
        )

    def earliest_known_play(self) -> Optional[int]:
        candidates = [
            self.local_first_played,
            self.lastfm_first_played,
            self.listenbrainz_first_listen,
        ]
        valid = [c for c in candidates if c]
        return min(valid) if valid else None

    def latest_known_play(self) -> Optional[int]:
        candidates = [
            self.local_last_played,
            self.lastfm_last_played,
            self.listenbrainz_last_listen,
        ]
        valid = [c for c in candidates if c]
        return max(valid) if valid else None

    def to_dict(self) -> dict:
        return {
            "track_id":    self.track_id,
            "artist_key":  self.artist_key,
            "title_key":   self.title_key,
            "album_key":   self.album_key,
            # Raw
            "local_playcount":              self.local_playcount,
            "local_loved":                  self.local_loved,
            "local_first_played":           self.local_first_played,
            "local_last_played":            self.local_last_played,
            "local_added":                  self.local_added,
            "lastfm_playcount":             self.lastfm_playcount,
            "lastfm_first_played":          self.lastfm_first_played,
            "lastfm_last_played":           self.lastfm_last_played,
            "listenbrainz_listen_count":    self.listenbrainz_listen_count,
            "listenbrainz_first_listen":    self.listenbrainz_first_listen,
            "listenbrainz_last_listen":     self.listenbrainz_last_listen,
            # Derived
            "lifetime_signal_score":            self.lifetime_signal_score,
            "historical_confidence":            self.historical_confidence,
            "playcount_split_state":            self.playcount_split_state,
            "active_rotation_score":            self.active_rotation_score,
            "local_only_signal":                self.local_only_signal,
            "lastfm_only_signal":               self.lastfm_only_signal,
            "timeline_completeness":            self.timeline_completeness,
            "priority_reconciliation_candidate": self.priority_reconciliation_candidate,
            # Coverage
            "has_local_playcount":   self.has_local_playcount,
            "has_lastfm_data":       self.has_lastfm_data,
            "has_listenbrainz_data": self.has_listenbrainz_data,
            "total_evidence_plays":  self.total_evidence_plays(),
            "earliest_known_play":   self.earliest_known_play(),
            "latest_known_play":     self.latest_known_play(),
        }
