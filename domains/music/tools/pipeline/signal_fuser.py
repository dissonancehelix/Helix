"""
signal_fuser.py — Core signal fusion engine for Phase 6 Part A.

Loads all available signal sources and produces one SignalRecord
per track in the library, keyed by track_id.

Fusion strategy:
  1. Load Playcount 2003 export by file path → track_id via source_map
  2. Load Last.fm index (artist+album+title key match)
  3. Load ListenBrainz index if available (same key match)
  4. Merge loved state: field_index by_loved (m3u8) OR 2003_loved
  5. Apply reconciler: split state, timeline completeness, priority flag
  6. Compute LIFETIME_SIGNAL_SCORE and ACTIVE_ROTATION_SCORE

LIFETIME_SIGNAL_SCORE (0–100):
  Weighted combination:
    local_playcount   × 0.45  (direct operator measurement)
    lastfm_playcount  × 0.40  (external behavioral history)
    listenbrainz      × 0.15  (secondary corroboration)
  Normalized so the 99th-percentile track = 100.

ACTIVE_ROTATION_SCORE (0–1):
  Recency-weighted: last-played within 6 months → ×3.0, within 12 months → ×2.0,
  older → ×1.0. Normalized to 50 weighted plays = 1.0.

HISTORICAL_CONFIDENCE (0–1):
  Based on timeline completeness + number of corroborating sources.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]

from .signal_record import (
    SignalRecord,
    COMPLETENESS_FULL, COMPLETENESS_HIGH,
    COMPLETENESS_PARTIAL, COMPLETENESS_COUNT_ONLY, COMPLETENESS_NONE,
)
from .signal_sources import PlaycountSource, LastFmSignalSource, ListenBrainzSource
from .playcount_reconciler import apply_reconciliation

_FIELD_INDEX_PATH = _REPO_ROOT / "codex" / "library" / "music" / ".field_index.json"

_6_MONTHS_MS  = 183 * 24 * 3600 * 1000
_12_MONTHS_MS = 365 * 24 * 3600 * 1000


def _now_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def _confidence(completeness: str, source_count: int) -> float:
    base = {
        COMPLETENESS_FULL:       0.90,
        COMPLETENESS_HIGH:       0.75,
        COMPLETENESS_PARTIAL:    0.55,
        COMPLETENESS_COUNT_ONLY: 0.35,
        COMPLETENESS_NONE:       0.05,
    }.get(completeness, 0.05)
    if source_count >= 3:
        return min(1.0, base + 0.08)
    if source_count == 2:
        return min(1.0, base + 0.04)
    return base


def _active_rotation_score(
    local_last_played:  Optional[int],
    lastfm_last_played: Optional[int],
    lb_last_listen:     Optional[int],
    local_playcount:    Optional[int],
    lastfm_playcount:   Optional[int],
    now_ms: int,
) -> float:
    """
    Recency-weighted play score. Uses last-played timestamps plus total counts
    to produce a 0–1 score indicating how active this track is right now.
    """
    last_ts = max(filter(None, [local_last_played, lastfm_last_played, lb_last_listen] or [0]), default=0)
    if last_ts == 0:
        return 0.0

    age = now_ms - last_ts
    if age < 0:
        age = 0

    # Recency weight based on last-play age
    if age < _6_MONTHS_MS:
        recency_w = 3.0
    elif age < _12_MONTHS_MS:
        recency_w = 2.0
    else:
        recency_w = 1.0

    # Play volume weight (log-scale to avoid extreme outliers dominating)
    total = (local_playcount or 0) + (lastfm_playcount or 0)
    import math
    volume_w = math.log1p(total) / math.log1p(300)  # normalize: 300 plays ≈ 1.0

    return min(1.0, recency_w * volume_w)


class SignalFuser:
    """
    Main Phase 6 signal fusion engine.

    Usage:
        fuser    = SignalFuser()
        registry = fuser.run(verbose=True)
        # registry: dict[track_id → SignalRecord]
    """

    def __init__(self, field_index_path: Path = _FIELD_INDEX_PATH) -> None:
        self._fi_path = field_index_path

    def run(self, *, verbose: bool = False) -> dict[str, SignalRecord]:
        t0 = time.time()

        # ── 1. Load field index ───────────────────────────────────────────────
        if not self._fi_path.exists():
            raise FileNotFoundError(f"Field index not found: {self._fi_path}")

        if verbose:
            print("[signal_fuser] Loading field index...")
        fi = json.loads(self._fi_path.read_text(encoding="utf-8"))

        source_map  = fi.get("source_map", {})   # track_id → file_path
        by_artist   = fi.get("by_artist", {})
        by_loved    = set(fi.get("by_loved", []))

        if verbose:
            print(f"[signal_fuser] {len(source_map):,} tracks in index")

        # Build reverse source map: normalized_file_path → track_id
        path_to_tid: dict[str, str] = {
            v.replace("\\", "/").lower(): k
            for k, v in source_map.items()
        }

        # Build artist key map: track_id → artist_key
        tid_to_artist: dict[str, str] = {}
        for ak, tids in by_artist.items():
            for tid in tids:
                if tid not in tid_to_artist:
                    tid_to_artist[tid] = ak

        # ── 2. Load Playcount 2003 ────────────────────────────────────────────
        pc_source = PlaycountSource()
        if verbose:
            total_pc = pc_source.total_entries()
            print(f"[signal_fuser] Playcount 2003: {total_pc:,} entries "
                  f"({pc_source.loved_count():,} loved)")

        # Build track_id → pc_signal using file path matching
        pc_by_tid: dict[str, dict] = {}
        for norm_path, sig in pc_source.iter_all():
            tid = path_to_tid.get(norm_path)
            if tid:
                pc_by_tid[tid] = sig

        if verbose:
            print(f"[signal_fuser] Playcount 2003 matched to {len(pc_by_tid):,} track_ids")

        # ── 3. Load Last.fm ───────────────────────────────────────────────────
        lfm = LastFmSignalSource()
        if verbose:
            print(f"[signal_fuser] Last.fm: {lfm.total_scrobbles():,} scrobbles → "
                  f"{lfm.unique_track_count():,} unique tracks")
        lfm._build()

        # ── 4. Load ListenBrainz (best-effort) ────────────────────────────────
        lb = ListenBrainzSource()
        if verbose:
            print(f"[signal_fuser] ListenBrainz: {'available' if lb.is_available() else 'not available'}")
        lb._build()

        # ── 5. Build registry ─────────────────────────────────────────────────
        registry: dict[str, SignalRecord] = {}
        now_ms = _now_ms()

        for tid, file_path in source_map.items():
            artist_key = tid_to_artist.get(tid, "")

            # Derive album/title keys from track_id slug
            # Format: music.track.<album_slug>.<title_slug>
            parts      = tid.split(".", 3)
            album_key  = parts[2] if len(parts) > 2 else ""
            title_key  = parts[3] if len(parts) > 3 else ""

            rec = SignalRecord(
                track_id=tid,
                artist_key=artist_key,
                title_key=title_key,
                album_key=album_key,
            )

            # Loved from field index (m3u8 source — always loaded)
            rec.local_loved = tid in by_loved

            # ── Playcount 2003 ────────────────────────────────────────────────
            pc = pc_by_tid.get(tid)
            if pc:
                rec.local_playcount    = pc.get("local_playcount")
                rec.local_first_played = pc.get("local_first_played")
                rec.local_last_played  = pc.get("local_last_played")
                rec.local_added        = pc.get("local_added")
                # 2003_loved is authoritative for loved; merge with m3u8
                if pc.get("local_loved"):
                    rec.local_loved = True

            # ── Last.fm ───────────────────────────────────────────────────────
            # Multi-artist keys: try each sub-key
            sub_keys = [k.strip() for k in artist_key.split("\x00") if k.strip()] or [artist_key]
            lfm_data = None
            for ak in sub_keys:
                lfm_data = lfm.get(ak, album_key, title_key)
                if lfm_data:
                    break

            if lfm_data:
                rec.lastfm_playcount    = lfm_data["lastfm_playcount"]
                rec.lastfm_first_played = lfm_data["lastfm_first_played"]
                rec.lastfm_last_played  = lfm_data["lastfm_last_played"]

            # ── ListenBrainz ──────────────────────────────────────────────────
            lb_data = None
            for ak in sub_keys:
                lb_data = lb.get(ak, album_key, title_key)
                if lb_data:
                    break

            if lb_data:
                rec.listenbrainz_listen_count = lb_data["listenbrainz_listen_count"]
                rec.listenbrainz_first_listen = lb_data["listenbrainz_first_listen"]
                rec.listenbrainz_last_listen  = lb_data["listenbrainz_last_listen"]

            # ── Reconciliation ────────────────────────────────────────────────
            apply_reconciliation(rec)

            # ── ACTIVE_ROTATION_SCORE ─────────────────────────────────────────
            rec.active_rotation_score = _active_rotation_score(
                rec.local_last_played, rec.lastfm_last_played,
                rec.listenbrainz_last_listen,
                rec.local_playcount, rec.lastfm_playcount,
                now_ms,
            )

            # ── HISTORICAL_CONFIDENCE ─────────────────────────────────────────
            source_count = sum([
                rec.has_local_playcount,
                rec.has_lastfm_data,
                rec.has_listenbrainz_data,
            ])
            rec.historical_confidence = _confidence(
                rec.timeline_completeness or COMPLETENESS_NONE, source_count
            )

            # Store raw signal for later normalization
            rec._raw_signal = (
                (rec.local_playcount         or 0) * 0.45
                + (rec.lastfm_playcount      or 0) * 0.40
                + (rec.listenbrainz_listen_count or 0) * 0.15
            )

            registry[tid] = rec

        # ── 6. Normalize LIFETIME_SIGNAL_SCORE ────────────────────────────────
        raw_scores = sorted(
            [r._raw_signal for r in registry.values() if r._raw_signal > 0],
            reverse=True,
        )
        if raw_scores:
            p99_idx = max(0, int(len(raw_scores) * 0.01) - 1)
            p99     = max(raw_scores[p99_idx], 1.0)
            for rec in registry.values():
                rec.lifetime_signal_score = round(
                    min(100.0, (rec._raw_signal / p99) * 100.0), 2
                )
                del rec._raw_signal

        elapsed = time.time() - t0
        if verbose:
            n_local  = sum(1 for r in registry.values() if r.has_local_playcount)
            n_lfm    = sum(1 for r in registry.values() if r.has_lastfm_data)
            n_lb     = sum(1 for r in registry.values() if r.has_listenbrainz_data)
            n_loved  = sum(1 for r in registry.values() if r.local_loved)
            print(f"[signal_fuser] Built {len(registry):,} records in {elapsed:.1f}s")
            print(f"  local_playcount:  {n_local:,}")
            print(f"  last.fm matched:  {n_lfm:,}")
            print(f"  listenbrainz:     {n_lb:,}")
            print(f"  loved:            {n_loved:,}")

        return registry
