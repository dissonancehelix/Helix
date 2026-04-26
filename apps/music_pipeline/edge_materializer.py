"""
edge_materializer.py — Materialize APPEARED_ON and FEATURED_ON relationship edges.

For each track in the library:
  - Parse ARTIST credits → APPEARED_ON edges (artist → track)
  - Parse FEATURING credits → FEATURED_ON edges (artist → track)
  - Resolve each credit to entity_id via codex atlas

Output is a list of EdgeRecord objects.

These are written to:
  artifacts/music/phase6/contributor_edge_materialization.json

They are NOT written to the atlas directly.
Promotion is a manual operator step.

Edge deduplication:
  Edges with identical (source_entity_id, relationship, target_track_id)
  are merged. Confidence is the max of all contributing evidence.

Signal enrichment:
  If a signal registry is provided, edges for tracks in active rotation
  (active_rotation_score > 0.2) or loved tracks are flagged.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from domains.music.semantic.credit_resolver import (
    resolve_credits, _lookup_entity, _norm,
)
from domains.music.semantic.ambiguity import ResolutionState
from domains.music.signals.signal_record import SignalRecord


# ── Edge record ───────────────────────────────────────────────────────────────

@dataclass
class EdgeRecord:
    """
    A single resolved relationship edge.

    source_entity_id → relationship → target_track_id

    For APPEARED_ON:   artist/composer → APPEARED_ON → track
    For FEATURED_ON:   artist → FEATURED_ON → track
    """
    source_entity_id:  str        # resolved entity_id (or stub id)
    source_key:        str        # normalized artist key
    credited_form:     str        # raw tag string
    relationship:      str        # "APPEARED_ON" | "FEATURED_ON"
    target_track_id:   str        # music.track:<slug>
    resolution_state:  str        # from ResolutionState
    confidence:        float      # 0.0–1.0
    source:            str        # "foobar_tags"

    # Signal flags (from signal registry)
    track_is_loved:    bool = False
    track_in_rotation: bool = False   # active_rotation_score > 0.2
    track_signal_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "source_entity_id":  self.source_entity_id,
            "source_key":        self.source_key,
            "credited_form":     self.credited_form,
            "relationship":      self.relationship,
            "target_track_id":   self.target_track_id,
            "resolution_state":  self.resolution_state,
            "confidence":        self.confidence,
            "source":            self.source,
            "track_is_loved":    self.track_is_loved,
            "track_in_rotation": self.track_in_rotation,
            "track_signal_score": self.track_signal_score,
        }


# ── Stub ID generator ─────────────────────────────────────────────────────────

_SLUG_RE = re.compile(r"[^\w]+")


def _make_stub_entity_id(normalized_key: str, entity_type: str = "artist") -> str:
    slug = _SLUG_RE.sub("_", normalized_key.strip()).strip("_")
    return f"music.{entity_type}:{slug}"


# ── Edge materializer ─────────────────────────────────────────────────────────

class EdgeMaterializer:
    """
    Builds APPEARED_ON and FEATURED_ON edge records from the field index.

    Uses by_artist and by_featuring indexes as the primary source.
    Individual track credit strings are not re-parsed at this stage
    (that would require reading 170k+ library JSONs).

    Edge derivation:
      by_artist[artist_key] → list of track_ids
        → each becomes an APPEARED_ON edge

      by_featuring[artist_key] → list of track_ids
        → each becomes a FEATURED_ON edge

    The field index artist_keys may be multi-valued (null-byte separated).
    Each sub-key gets its own edge to the same tracks.
    """

    def __init__(
        self,
        field_index: dict,
        signal_registry: Optional[dict[str, SignalRecord]] = None,
        by_loved: Optional[set[str]] = None,
    ) -> None:
        self._field_index = field_index
        self._signal_reg  = signal_registry or {}
        self._loved       = by_loved or set()

    def _enrich_edge(self, edge: EdgeRecord) -> None:
        """Add signal enrichment fields to an edge in-place."""
        sig = self._signal_reg.get(edge.target_track_id)
        edge.track_is_loved    = edge.target_track_id in self._loved
        edge.track_in_rotation = bool(sig and (sig.active_rotation_score or 0) > 0.2)
        edge.track_signal_score = (sig.lifetime_signal_score or 0.0) if sig else 0.0

    def run(self) -> list[EdgeRecord]:
        """
        Build all edge records from the field index.
        Returns deduplicated list.
        """
        by_artist    = self._field_index.get("by_artist", {})
        by_featuring = self._field_index.get("by_featuring", {})

        edges: dict[tuple, EdgeRecord] = {}  # (source_id, rel, target) → edge

        # ── APPEARED_ON edges (from by_artist) ────────────────────────────────
        for artist_key, track_ids in by_artist.items():
            sub_keys = [k.strip() for k in artist_key.split("\x00") if k.strip()]
            for sk in sub_keys:
                entity_id, state, conf = _lookup_entity(sk)
                if not entity_id:
                    entity_id = _make_stub_entity_id(sk, "artist")

                for tid in track_ids:
                    edge_key = (entity_id, "APPEARED_ON", tid)
                    if edge_key not in edges:
                        edge = EdgeRecord(
                            source_entity_id=entity_id,
                            source_key=sk,
                            credited_form=sk,  # normalized approximation
                            relationship="APPEARED_ON",
                            target_track_id=tid,
                            resolution_state=state.value,
                            confidence=conf,
                            source="foobar_tags",
                        )
                        self._enrich_edge(edge)
                        edges[edge_key] = edge
                    else:
                        # Update confidence to max
                        edges[edge_key].confidence = max(edges[edge_key].confidence, conf)

        # ── FEATURED_ON edges (from by_featuring) ─────────────────────────────
        for feat_key, track_ids in by_featuring.items():
            entity_id, state, conf = _lookup_entity(feat_key)
            if not entity_id:
                entity_id = _make_stub_entity_id(feat_key, "artist")

            for tid in track_ids:
                edge_key = (entity_id, "FEATURED_ON", tid)
                if edge_key not in edges:
                    edge = EdgeRecord(
                        source_entity_id=entity_id,
                        source_key=feat_key,
                        credited_form=feat_key,
                        relationship="FEATURED_ON",
                        target_track_id=tid,
                        resolution_state=state.value,
                        confidence=conf,
                        source="foobar_tags",
                    )
                    self._enrich_edge(edge)
                    edges[edge_key] = edge

        result = list(edges.values())

        # Sort: FEATURED_ON first, then by confidence desc
        rel_order = {"FEATURED_ON": 0, "APPEARED_ON": 1}
        result.sort(key=lambda e: (rel_order.get(e.relationship, 9), -e.confidence))

        return result

    def summary(self, edges: list[EdgeRecord]) -> dict:
        appeared_on  = [e for e in edges if e.relationship == "APPEARED_ON"]
        featured_on  = [e for e in edges if e.relationship == "FEATURED_ON"]
        resolved     = [e for e in edges if e.resolution_state == ResolutionState.RESOLVED.value]
        unresolved   = [e for e in edges if e.resolution_state == ResolutionState.UNRESOLVED.value]
        loved_edges  = [e for e in edges if e.track_is_loved]
        rotation_edges = [e for e in edges if e.track_in_rotation]
        return {
            "total_edges":       len(edges),
            "appeared_on_edges": len(appeared_on),
            "featured_on_edges": len(featured_on),
            "resolved_sources":  len(resolved),
            "unresolved_sources": len(unresolved),
            "edges_to_loved_tracks":    len(loved_edges),
            "edges_to_active_rotation": len(rotation_edges),
            "unique_source_entities": len({e.source_entity_id for e in edges}),
            "unique_target_tracks":   len({e.target_track_id for e in edges}),
        }
