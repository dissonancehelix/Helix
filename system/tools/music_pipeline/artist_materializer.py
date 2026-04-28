"""
artist_materializer.py — Materialize Artist entity stubs from resolved credits.

For every unique artist key in the field index:
  1. Try to resolve to a known Composer entity in the codex atlas
  2. If resolved → emit a reference record (entity already exists)
  3. If unresolved → emit an Artist stub that can be promoted to the atlas
  4. Enrich stubs with signal data (total plays, loved tracks, corpus size)

Output: list of ArtistMaterializationRecord

These are NOT written directly to the atlas.
They are written to artifacts/music/phase6/artist_entity_materialization.json
for operator review and optional manual promotion.

Entity ID format for stubs: music.artist:<normalized_slug>
(Different from Composer: music.composer:<slug>)
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from model.domains.music.semantic.credit_resolver import (
    _load_codex_index, _norm, _lookup_entity,
)
from model.domains.music.semantic.ambiguity import ResolutionState
from system.tools.music_pipeline.signal_record import SignalRecord


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ArtistMaterializationRecord:
    """
    A single artist entity materialization candidate.

    status:
      existing_composer   — already a Composer in the codex atlas
      resolved_artist     — no codex Composer but credit_resolver found a match
      stub_candidate      — unresolved; needs manual review or creation
    """
    credited_form:   str                   # most common raw tag string
    normalized_key:  str                   # lowercase normalized key
    entity_id:       Optional[str]         # resolved entity_id, or generated stub id
    entity_type:     str                   # "Composer" | "Artist"
    status:          str                   # existing_composer | resolved_artist | stub_candidate
    resolution_state: str                  # from ResolutionState
    confidence:      float                 # 0.0–1.0

    # Signal enrichment
    track_count:         int   = 0
    loved_track_count:   int   = 0
    total_evidence_plays: int  = 0
    lifetime_signal_score: float = 0.0
    featured_track_count: int  = 0

    # Track IDs (sample, not full list)
    sample_track_ids: list[str] = field(default_factory=list)
    credited_forms:   list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "credited_form":    self.credited_form,
            "normalized_key":   self.normalized_key,
            "entity_id":        self.entity_id,
            "entity_type":      self.entity_type,
            "status":           self.status,
            "resolution_state": self.resolution_state,
            "confidence":       self.confidence,
            "track_count":      self.track_count,
            "loved_track_count": self.loved_track_count,
            "total_evidence_plays": self.total_evidence_plays,
            "lifetime_signal_score": self.lifetime_signal_score,
            "featured_track_count": self.featured_track_count,
            "sample_track_ids": self.sample_track_ids[:20],
            "credited_forms":   self.credited_forms,
        }


# ── Slug generator ─────────────────────────────────────────────────────────────

_SLUG_RE = re.compile(r"[^\w]+")


def _make_stub_id(normalized_key: str) -> str:
    slug = _SLUG_RE.sub("_", normalized_key.strip()).strip("_")
    return f"music.artist:{slug}"


# ── Materializer ──────────────────────────────────────────────────────────────

class ArtistMaterializer:
    """
    Builds ArtistMaterializationRecord for every unique artist key
    in the field index.

    signal_registry is optional — if provided, tracks are enriched
    with lifetime signal scores and evidence play counts.
    """

    def __init__(
        self,
        field_index: dict,
        signal_registry: Optional[dict[str, SignalRecord]] = None,
        by_loved: Optional[set[str]] = None,
    ) -> None:
        self._field_index    = field_index
        self._signal_reg     = signal_registry or {}
        self._loved          = by_loved or set()
        self._codex_index    = None  # lazy

    def _get_codex_index(self) -> dict[str, str]:
        if self._codex_index is None:
            self._codex_index = _load_codex_index()
        return self._codex_index

    def run(self) -> list[ArtistMaterializationRecord]:
        """
        Run materialization for all artist keys in the field index.
        Returns sorted list: existing composers first, then stubs.
        """
        by_artist    = self._field_index.get("by_artist", {})
        by_featuring = self._field_index.get("by_featuring", {})
        codex        = self._get_codex_index()

        # Collect all unique artist keys (primary + featured)
        all_keys: dict[str, set[str]] = {}  # normalized_key → set of track_ids

        for key, tids in by_artist.items():
            # Handle null-byte multi-artist keys
            sub_keys = [k.strip() for k in key.split("\x00") if k.strip()]
            for sk in sub_keys:
                if sk not in all_keys:
                    all_keys[sk] = set()
                all_keys[sk].update(tids)

        # Featured artists
        for key in by_featuring:
            if key not in all_keys:
                all_keys[key] = set(by_featuring[key])

        records: list[ArtistMaterializationRecord] = []

        for norm_key, track_ids in all_keys.items():
            if not norm_key:
                continue

            # Resolve via codex
            entity_id, state, confidence = _lookup_entity(norm_key)

            # Determine entity type and status
            if entity_id and entity_id.startswith("music.composer:"):
                status      = "existing_composer"
                entity_type = "Composer"
            elif entity_id:
                status      = "resolved_artist"
                entity_type = "Artist"
            else:
                status      = "stub_candidate"
                entity_type = "Artist"
                entity_id   = _make_stub_id(norm_key)

            # Determine most common credited form
            # We only have the normalized key here; use it as credited_form
            # (credit_resolver would give us the raw form, but that requires
            # a full library scan — this is a fast path using the field index)
            credited_form = norm_key  # best approximation without full scan

            # Signal enrichment
            total_plays   = 0
            loved_count   = 0
            max_lifetime  = 0.0
            for tid in track_ids:
                sig = self._signal_reg.get(tid)
                if sig:
                    total_plays  += sig.total_evidence_plays()
                    max_lifetime  = max(max_lifetime, sig.lifetime_signal_score or 0.0)
                if tid in self._loved:
                    loved_count += 1

            feat_count = len(by_featuring.get(norm_key, []))

            rec = ArtistMaterializationRecord(
                credited_form=credited_form,
                normalized_key=norm_key,
                entity_id=entity_id,
                entity_type=entity_type,
                status=status,
                resolution_state=state.value,
                confidence=confidence,
                track_count=len(track_ids),
                loved_track_count=loved_count,
                total_evidence_plays=total_plays,
                lifetime_signal_score=round(max_lifetime, 2),
                featured_track_count=feat_count,
                sample_track_ids=sorted(track_ids)[:20],
                credited_forms=[credited_form],
            )
            records.append(rec)

        # Sort: existing_composer first, then by track count descending
        _status_order = {"existing_composer": 0, "resolved_artist": 1, "stub_candidate": 2}
        records.sort(key=lambda r: (_status_order.get(r.status, 3), -r.track_count))

        return records

    def summary(self, records: list[ArtistMaterializationRecord]) -> dict:
        existing   = [r for r in records if r.status == "existing_composer"]
        resolved   = [r for r in records if r.status == "resolved_artist"]
        stubs      = [r for r in records if r.status == "stub_candidate"]
        return {
            "total_artist_keys":          len(records),
            "existing_composers":         len(existing),
            "resolved_artists":           len(resolved),
            "stub_candidates":            len(stubs),
            "stubs_with_loved_tracks":    sum(1 for r in stubs if r.loved_track_count > 0),
            "stubs_with_high_plays":      sum(1 for r in stubs if r.total_evidence_plays >= 20),
            "stubs_needing_creation":     sum(1 for r in stubs if r.track_count >= 3),
        }

