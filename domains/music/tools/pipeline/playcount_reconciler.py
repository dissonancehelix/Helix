"""
playcount_reconciler.py — PLAYCOUNT_SPLIT_STATE classification.

Classifies the relationship between LOCAL_PLAYCOUNT (Playcount 2003)
and LASTFM_PLAYCOUNT (Last.fm scrobbles) per track.

The two counts are independent:
  - Local: continuous from Foobar (offline play, non-scrobbled content)
  - Last.fm: history from 2012; gaps before that; some tracks never scrobble
  - Divergence is expected and meaningful, not a data error

Split state vocabulary:
  synchronized     counts within ±15% of each other
  local_ahead      local significantly higher than Last.fm
  lastfm_ahead     Last.fm significantly higher than local
  local_only       Last.fm absent, local > 0
  lastfm_only      local absent, Last.fm > 0
  both_zero        no plays recorded anywhere
  divergent        > 50% relative discrepancy, source unclear
  unresolvable     conflicting signals with no clear explanation

Timeline completeness:
  full          multi-source with timestamps (local + Last.fm)
  high          last.fm has first/last timestamps
  partial        local timestamps only (2003_first_played / 2003_last_played)
  count_only     counts known, no timestamps
  none           no signal at all
"""
from __future__ import annotations

from typing import Optional

from .signal_record import (
    SignalRecord,
    SPLIT_SYNCHRONIZED, SPLIT_LOCAL_AHEAD, SPLIT_LASTFM_AHEAD,
    SPLIT_LOCAL_ONLY, SPLIT_LASTFM_ONLY, SPLIT_BOTH_ZERO,
    SPLIT_DIVERGENT, SPLIT_UNRESOLVABLE,
    COMPLETENESS_FULL, COMPLETENESS_HIGH,
    COMPLETENESS_COUNT_ONLY, COMPLETENESS_NONE,
)

_SYNC_THRESHOLD  = 0.15   # within 15% = synchronized
_MINOR_THRESHOLD = 0.30   # within 30% = minor divergence
_DIVERGE_THRESHOLD = 0.50 # beyond 50% = divergent

_PRIORITY_MIN_PLAYS   = 5
_PRIORITY_SPLIT_DELTA = 10


def classify_split_state(
    local_playcount: Optional[int],
    lastfm_playcount: Optional[int],
) -> str:
    lc = local_playcount  if local_playcount  is not None else 0
    fc = lastfm_playcount if lastfm_playcount is not None else 0

    if lc == 0 and fc == 0:
        return SPLIT_BOTH_ZERO
    if lc > 0 and fc == 0:
        return SPLIT_LOCAL_ONLY
    if lc == 0 and fc > 0:
        return SPLIT_LASTFM_ONLY

    higher = max(lc, fc)
    rel    = (higher - min(lc, fc)) / higher

    if rel <= _SYNC_THRESHOLD:
        return SPLIT_SYNCHRONIZED
    elif rel <= _DIVERGE_THRESHOLD:
        return SPLIT_LOCAL_AHEAD if lc > fc else SPLIT_LASTFM_AHEAD
    else:
        return SPLIT_DIVERGENT if (lc > fc * 2 or fc > lc * 2) else SPLIT_UNRESOLVABLE


def classify_timeline_completeness(record: SignalRecord) -> str:
    has_local_ts = bool(record.local_first_played or record.local_last_played)
    has_lfm_ts   = bool(record.lastfm_first_played or record.lastfm_last_played)
    has_lb_ts    = bool(record.listenbrainz_first_listen or record.listenbrainz_last_listen)

    ts_sources = sum([has_local_ts, has_lfm_ts, has_lb_ts])
    has_counts = bool(
        (record.local_playcount and record.local_playcount > 0)
        or (record.lastfm_playcount and record.lastfm_playcount > 0)
        or (record.listenbrainz_listen_count and record.listenbrainz_listen_count > 0)
    )

    if ts_sources >= 2:
        return COMPLETENESS_FULL
    elif ts_sources == 1:
        return COMPLETENESS_HIGH
    elif has_counts:
        return COMPLETENESS_COUNT_ONLY
    else:
        return COMPLETENESS_NONE


def is_priority_reconciliation_candidate(record: SignalRecord) -> bool:
    state = record.playcount_split_state
    lc = record.local_playcount or 0
    fc = record.lastfm_playcount or 0

    if state in (SPLIT_DIVERGENT, SPLIT_UNRESOLVABLE):
        return True
    if state == SPLIT_LOCAL_ONLY and lc >= _PRIORITY_MIN_PLAYS:
        return True
    if state == SPLIT_LASTFM_ONLY and fc >= _PRIORITY_MIN_PLAYS:
        return True
    if state in (SPLIT_LOCAL_AHEAD, SPLIT_LASTFM_AHEAD):
        if abs(lc - fc) >= _PRIORITY_SPLIT_DELTA and (lc + fc) >= _PRIORITY_MIN_PLAYS:
            return True
    return False


def apply_reconciliation(record: SignalRecord) -> None:
    """Compute and set all reconciliation-derived fields in place."""
    record.playcount_split_state = classify_split_state(
        record.local_playcount, record.lastfm_playcount
    )
    record.timeline_completeness = classify_timeline_completeness(record)
    record.priority_reconciliation_candidate = is_priority_reconciliation_candidate(record)

    record.local_only_signal  = record.playcount_split_state == SPLIT_LOCAL_ONLY
    record.lastfm_only_signal = record.playcount_split_state == SPLIT_LASTFM_ONLY

    record.has_local_playcount   = record.local_playcount is not None
    record.has_lastfm_data       = bool(record.lastfm_playcount or record.lastfm_first_played)
    record.has_listenbrainz_data = bool(record.listenbrainz_listen_count)
