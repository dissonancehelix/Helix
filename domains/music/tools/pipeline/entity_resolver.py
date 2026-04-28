"""
entity_resolver.py — Cross-source entity resolution for Phase 4.

Matches records across trace sources into EntityGroups with
confidence-scored match classifications.

This is fuzzy key matching — not acoustic fingerprinting or
MusicBrainz deep lookup. Confidence scores reflect string
similarity and multi-source corroboration, not ground truth.

Match classes (descending confidence):
  exact_match           artist+album+title all match exactly (normalized)
  strong_match          artist+title match, album differs or absent
  likely_match          artist matches, title fuzzy or partial
  alias_match_candidate artist/title tokens partially overlap
  ambiguous_match       multiple partial matches across different records
  no_match              no signal overlap found
  conflict_requires_review  sources disagree on important fields
"""

from __future__ import annotations

import hashlib
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .staging import StagedRecord, SourceSnapshot, norm_key


# ---------------------------------------------------------------------------
# Match class constants and confidence thresholds
# ---------------------------------------------------------------------------

MATCH_EXACT   = "exact_match"
MATCH_STRONG  = "strong_match"
MATCH_LIKELY  = "likely_match"
MATCH_ALIAS   = "alias_match_candidate"
MATCH_AMBIG   = "ambiguous_match"
MATCH_NONE    = "no_match"
MATCH_CONFLICT = "conflict_requires_review"

_CONFIDENCE = {
    MATCH_EXACT:    1.00,
    MATCH_STRONG:   0.85,
    MATCH_LIKELY:   0.65,
    MATCH_ALIAS:    0.45,
    MATCH_AMBIG:    0.30,
    MATCH_NONE:     0.00,
    MATCH_CONFLICT: 0.20,
}

# Source authority order (higher index = more authoritative for metadata)
SOURCE_AUTHORITY = ["lastfm", "spotify", "codex", "library", "foobar_runtime"]


# ---------------------------------------------------------------------------
# EntityGroup
# ---------------------------------------------------------------------------

@dataclass
class EntityGroup:
    """
    A resolved entity across one or more trace sources.

    `primary` is the record from the most authoritative source.
    `all_records` maps source → record.
    """

    entity_id:       str        # stable hash of best key tuple
    match_class:     str        # one of MATCH_* constants
    confidence:      float      # 0.0 → 1.0
    sources_matched: list[str]  # which sources contributed records
    primary:         StagedRecord
    all_records:     dict[str, StagedRecord]   # source -> record
    match_signals:   list[str]   # human-readable match evidence
    field_conflicts: list[dict]  # {field, sources, values} where sources disagree
    scrobble_count:  int = 0    # total Last.fm plays if available
    spotify_popularity: int | None = None

    def to_dict(self) -> dict:
        return {
            "entity_id":       self.entity_id,
            "match_class":     self.match_class,
            "confidence":      self.confidence,
            "sources_matched": self.sources_matched,
            "scrobble_count":  self.scrobble_count,
            "spotify_popularity": self.spotify_popularity,
            "match_signals":   self.match_signals,
            "field_conflicts": self.field_conflicts,
            "primary": {
                "source":     self.primary.source,
                "source_id":  self.primary.source_id,
                "title_raw":  self.primary.title_raw,
                "artist_raw": self.primary.artist_raw,
                "album_raw":  self.primary.album_raw,
                "platform":   self.primary.platform,
                "franchise":  self.primary.franchise,
                "sound_chip": self.primary.sound_chip,
                "sound_team": self.primary.sound_team,
                "loved":      self.primary.loved,
                "track_number": self.primary.track_number,
            },
            "sources": {
                src: {
                    "title_raw":  r.title_raw,
                    "artist_raw": r.artist_raw,
                    "album_raw":  r.album_raw,
                    "source_id":  r.source_id,
                    "scrobble_count": r.scrobble_count,
                }
                for src, r in self.all_records.items()
            },
        }


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------

def _build_index(records: list[StagedRecord]) -> tuple[
    dict[tuple, StagedRecord],   # exact: (artist_key, album_key, title_key) -> record
    dict[tuple, list[StagedRecord]],  # artist+title: (artist_key, title_key) -> [records]
    dict[str, list[StagedRecord]],    # artist only: artist_key -> [records]
]:
    exact_idx: dict[tuple, StagedRecord] = {}
    at_idx: dict[tuple, list[StagedRecord]] = defaultdict(list)
    a_idx: dict[str, list[StagedRecord]] = defaultdict(list)

    for r in records:
        key3 = (r.artist_key, r.album_key, r.title_key)
        key2 = (r.artist_key, r.title_key)
        if r.artist_key or r.title_key:
            exact_idx[key3] = r         # last-write wins on exact duplicate
            if key2[0] or key2[1]:
                at_idx[key2].append(r)
            if r.artist_key:
                a_idx[r.artist_key].append(r)

    return exact_idx, dict(at_idx), dict(a_idx)


# ---------------------------------------------------------------------------
# Field conflict detector
# ---------------------------------------------------------------------------

def _detect_conflicts(records: dict[str, StagedRecord]) -> list[dict]:
    """Detect disagreements between sources on important metadata fields."""
    COMPARE_FIELDS = ["platform", "sound_chip", "sound_team", "franchise",
                      "album_raw", "album_artist"]
    conflicts = []
    for f in COMPARE_FIELDS:
        vals = {src: getattr(r, f, None) for src, r in records.items()
                if getattr(r, f, None)}
        unique_vals = set(v.lower().strip() if v else "" for v in vals.values())
        unique_vals.discard("")
        if len(unique_vals) > 1:
            conflicts.append({
                "field":   f,
                "values":  {src: val for src, val in vals.items()},
            })
    return conflicts


# ---------------------------------------------------------------------------
# Per-record match scorer
# ---------------------------------------------------------------------------

def _score_match(
    primary: StagedRecord,
    candidate: StagedRecord,
) -> tuple[str, float, list[str]]:
    """
    Return (match_class, confidence, signals) for a candidate vs. primary.
    Only the string keys (not raw strings) are used for matching.
    """
    signals = []
    ak_match  = primary.artist_key and primary.artist_key == candidate.artist_key
    alk_match = primary.album_key  and primary.album_key  == candidate.album_key
    tk_match  = primary.title_key  and primary.title_key  == candidate.title_key

    if ak_match:
        signals.append("artist_key_exact")
    if alk_match:
        signals.append("album_key_exact")
    if tk_match:
        signals.append("title_key_exact")

    # Exact 3-key match
    if ak_match and alk_match and tk_match:
        return MATCH_EXACT, _CONFIDENCE[MATCH_EXACT], signals

    # Artist + title match, album differs or absent (common for compilations)
    if ak_match and tk_match:
        signals.append("album_mismatch_or_absent")
        return MATCH_STRONG, _CONFIDENCE[MATCH_STRONG], signals

    # MBID match (Last.fm albumId — reliable when present)
    if (primary.mbid and candidate.mbid
            and primary.mbid == candidate.mbid
            and primary.mbid != ""):
        signals.append("mbid_match")
        if tk_match:
            return MATCH_EXACT, _CONFIDENCE[MATCH_EXACT], signals
        return MATCH_STRONG, _CONFIDENCE[MATCH_STRONG], signals

    # Artist + partial title match (token overlap > 0.6)
    if ak_match:
        pt = _token_overlap(primary.title_key, candidate.title_key)
        if pt >= 0.6:
            signals.append(f"title_token_overlap={pt:.2f}")
            return MATCH_LIKELY, _CONFIDENCE[MATCH_LIKELY], signals
        signals.append("artist_key_only")
        return MATCH_ALIAS, _CONFIDENCE[MATCH_ALIAS], signals

    # Artist partial match + title
    pa = _token_overlap(primary.artist_key, candidate.artist_key)
    if pa >= 0.5 and tk_match:
        signals.append(f"artist_token_overlap={pa:.2f}+title_exact")
        return MATCH_ALIAS, _CONFIDENCE[MATCH_ALIAS], signals

    return MATCH_NONE, 0.0, signals


def _token_overlap(a: str, b: str) -> float:
    """Token-based Jaccard similarity for two normalized strings."""
    if not a or not b:
        return 0.0
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------

def resolve_entities(
    snapshots: dict[str, SourceSnapshot],
    *,
    primary_source: str = "foobar_runtime",
) -> list[EntityGroup]:
    """
    Resolve entities across all snapshots.

    Uses `primary_source` records as anchors.
    Matches records from other sources to each anchor.

    Returns a list of EntityGroups — one per primary record
    (plus unmatched non-primary records as no_match groups).
    """
    groups: list[EntityGroup] = []

    primary_snap = snapshots.get(primary_source)
    if not primary_snap or not primary_snap.records:
        # Fallback: if primary source absent, use codex
        primary_snap = snapshots.get("codex")
    if not primary_snap or not primary_snap.records:
        return groups

    primary_records = primary_snap.records
    print(f"[resolver] Anchor source: {primary_snap.source} "
          f"({len(primary_records):,} records)")

    # Build indices for each non-primary source
    source_indices: dict[str, tuple] = {}
    for src, snap in snapshots.items():
        if src == primary_source or not snap.records:
            continue
        ei, ati, ai = _build_index(snap.records)
        source_indices[src] = (ei, ati, ai)
        print(f"[resolver] Indexed {src}: {len(ei):,} unique tracks")

    # Track which non-primary records were matched
    matched_ids: dict[str, set[str]] = {src: set() for src in source_indices}

    for primary_rec in primary_records:
        all_records: dict[str, StagedRecord] = {primary_source: primary_rec}
        match_signals: list[str] = []
        best_class = MATCH_NONE
        best_conf  = 0.0

        for src, (ei, ati, ai) in source_indices.items():
            # Try exact 3-key match first
            key3 = primary_rec.entity_key
            key2 = (primary_rec.artist_key, primary_rec.title_key)

            candidate = ei.get(key3)
            if candidate:
                mc, conf, sigs = _score_match(primary_rec, candidate)
                match_signals.extend([f"{src}:{s}" for s in sigs])
                if conf > best_conf:
                    best_class, best_conf = mc, conf
                all_records[src] = candidate
                matched_ids[src].add(candidate.source_id)
                continue

            # Try artist+title match
            at_candidates = ati.get(key2, [])
            if len(at_candidates) == 1:
                mc, conf, sigs = _score_match(primary_rec, at_candidates[0])
                if conf >= 0.65:
                    match_signals.extend([f"{src}:{s}" for s in sigs])
                    if conf > best_conf:
                        best_class, best_conf = mc, conf
                    all_records[src] = at_candidates[0]
                    matched_ids[src].add(at_candidates[0].source_id)
            elif len(at_candidates) > 1:
                # Multiple artist+title matches — ambiguous
                if src not in all_records:
                    match_signals.append(f"{src}:ambiguous_{len(at_candidates)}_at_matches")
                    if best_conf < _CONFIDENCE[MATCH_AMBIG]:
                        best_class, best_conf = MATCH_AMBIG, _CONFIDENCE[MATCH_AMBIG]

        # Determine final match class
        sources_matched = list(all_records.keys())
        if len(sources_matched) == 1:
            best_class = MATCH_NONE
            best_conf  = 0.0

        # Check for field conflicts across matched records
        conflicts = _detect_conflicts(all_records)
        if conflicts and best_class in (MATCH_EXACT, MATCH_STRONG):
            # Significant disagreement — downgrade to conflict
            if len(conflicts) > 2:
                best_class = MATCH_CONFLICT
                best_conf  = _CONFIDENCE[MATCH_CONFLICT]

        # Pick primary from most authoritative matched source
        best_primary = _pick_primary(all_records)

        # Pull scrobble count from Last.fm record if present
        lfm_rec = all_records.get("lastfm")
        scrobble_count = lfm_rec.scrobble_count if lfm_rec else 0

        spo_rec = all_records.get("spotify")
        spotify_pop = spo_rec.spotify_popularity if spo_rec else None

        groups.append(EntityGroup(
            entity_id       = primary_rec.stable_id(),
            match_class     = best_class,
            confidence      = best_conf,
            sources_matched = sources_matched,
            primary         = best_primary,
            all_records     = all_records,
            match_signals   = match_signals,
            field_conflicts = conflicts,
            scrobble_count  = scrobble_count or 0,
            spotify_popularity = spotify_pop,
        ))

    # Add Last.fm-only records that were never matched
    lfm_snap = snapshots.get("lastfm")
    if lfm_snap:
        (lfm_ei, _, _) = source_indices.get("lastfm", ({}, {}, {}))
        lfm_unmatched_ids = set(r.source_id for r in lfm_snap.records) - matched_ids.get("lastfm", set())
        lfm_unmatched = [r for r in lfm_snap.records
                         if r.source_id in lfm_unmatched_ids]
        print(f"[resolver] {len(lfm_unmatched):,} Last.fm-only records (no library match)")
        for rec in lfm_unmatched:
            groups.append(EntityGroup(
                entity_id       = rec.stable_id(),
                match_class     = MATCH_NONE,
                confidence      = 0.0,
                sources_matched = ["lastfm"],
                primary         = rec,
                all_records     = {"lastfm": rec},
                match_signals   = ["lastfm_only"],
                field_conflicts = [],
                scrobble_count  = rec.scrobble_count or 0,
            ))

    print(f"[resolver] Resolved {len(groups):,} entity groups")
    return groups


def _pick_primary(all_records: dict[str, StagedRecord]) -> StagedRecord:
    """
    Pick the most authoritative record as primary.
    Priority: foobar_runtime > codex > library > spotify > lastfm
    """
    for src in ["foobar_runtime", "codex", "library", "spotify", "lastfm"]:
        if src in all_records:
            return all_records[src]
    return next(iter(all_records.values()))


# ---------------------------------------------------------------------------
# Summary helper
# ---------------------------------------------------------------------------

def summarize_resolution(groups: list[EntityGroup]) -> dict:
    counts: dict[str, int] = defaultdict(int)
    source_combos: dict[str, int] = defaultdict(int)
    for g in groups:
        counts[g.match_class] += 1
        combo = "+".join(sorted(g.sources_matched))
        source_combos[combo] += 1
    return {
        "total_groups": len(groups),
        "by_match_class": dict(sorted(counts.items(), key=lambda x: -x[1])),
        "by_source_combo": dict(sorted(source_combos.items(), key=lambda x: -x[1])),
        "multi_source_count": sum(1 for g in groups if len(g.sources_matched) > 1),
        "single_source_count": sum(1 for g in groups if len(g.sources_matched) == 1),
        "high_confidence_count": sum(1 for g in groups if g.confidence >= 0.85),
    }
