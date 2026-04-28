"""
resolution.py — Phase 12: Conservative Alias Graph and Candidate Resolution.

Logical layers:
  A. Candidate Generation (Generates local <-> external pairs)
  B. Evidence Model (Multi-signal structured scoring)
  C. Acceptance Engine (Tiered filtering and Contradiction Gates)
  D. Manual Review Queue (Persistence of ambiguous cases)
  E. Curated Subset Logic (Handling track-count mismatches)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from .metadata_adapter import TrackMeta
from .alias_graph import AliasSet, AliasGraph


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    """Structured evidence for a candidate match."""
    alias_match: str = "none"           # "exact" | "normalized" | "fuzzy" | "none"
    artist_match: bool = False
    composer_match: bool = False
    year_proximity: bool = False        # +/- 2 years
    platform_match: bool = False
    track_count_overlap: float = 0.0    # ratio of local tracks found in external set
    external_id_match: bool = False     # e.g. existing VGMdb ID match
    franchise_overlap: bool = False
    source: str = ""                    # e.g. "VGMdb", "MusicBrainz"

    def score(self) -> float:
        """Heuristic score for internal ranking (0.0 - 1.0)."""
        points = 0.0
        if self.alias_match == "exact": points += 0.5
        elif self.alias_match == "normalized": points += 0.3
        
        if self.artist_match: points += 0.2
        if self.platform_match: points += 0.1
        if self.year_proximity: points += 0.1
        if self.track_count_overlap > 0.8: points += 0.1
        
        return min(1.0, points)


@dataclass
class Contradiction:
    """Structured contradictions that block auto-acceptance."""
    franchise_mismatch: bool = False
    composer_mismatch: bool = False
    year_mismatch: bool = False         # > 5 years difference (not counting remakes)
    platform_mismatch: bool = False
    competing_candidate_id: Optional[str] = None
    low_overlap: bool = False           # track count mismatch too severe to be curated subset
    
    def any(self) -> bool:
        return any([
            self.franchise_mismatch,
            self.composer_mismatch,
            self.year_mismatch,
            self.platform_mismatch,
            self.competing_candidate_id is not None,
            self.low_overlap
        ])


@dataclass
class Candidate:
    """A generated match candidate between a local record and an external entity."""
    local_id: str                       # typically the album name or folder path
    external_id: str                    # external service ID (e.g. VGMdb album ID)
    entity_type: str                    # "release" | "artist" | "game"
    
    tier: str = "TIER_D"                # A, B, C, D
    evidence: Evidence = field(default_factory=Evidence)
    contradictions: Contradiction = field(default_factory=Contradiction)
    
    match_category: str = "PARTIAL_UNCERTAIN" # FULL_MATCH | CURATED_SUBSET_MATCH | PARTIAL_UNCERTAIN | CONTRADICTED
    provenance: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "local_id": self.local_id,
            "external_id": self.external_id,
            "entity_type": self.entity_type,
            "tier": self.tier,
            "match_category": self.match_category,
            "evidence": self.evidence.__dict__,
            "contradictions": self.contradictions.__dict__,
            "provenance": self.provenance,
            "timestamp": self.timestamp
        }


# ---------------------------------------------------------------------------
# Acceptance Engine
# ---------------------------------------------------------------------------

class AcceptanceEngine:
    """
    Tiered acceptance logic for candidates.
    Hard rule: MISSING IS BETTER THAN WRONG.
    """
    
    def evaluate(self, candidate: Candidate) -> str:
        """Assign an acceptance tier based on evidence and contradictions."""
        ev = candidate.evidence
        co = candidate.contradictions
        
        # Rule 1: Contradictions always block auto-accept
        if co.any():
            candidate.tier = "TIER_D"
            candidate.match_category = "CONTRADICTED"
            return "TIER_D"
        
        # Rule 2: Title similarity alone is not TIER_A
        if ev.alias_match in ("exact", "normalized") and not (ev.artist_match or ev.platform_match or ev.year_proximity):
            candidate.tier = "TIER_B" # Needs review
            return "TIER_B"
            
        # TIER A: Auto-Accept
        # Strong multi-signal support, no contradictions
        if ev.alias_match == "exact" and (ev.artist_match or ev.platform_match) and ev.track_count_overlap > 0.5:
            candidate.tier = "TIER_A"
            candidate.match_category = "FULL_MATCH" if ev.track_count_overlap > 0.9 else "CURATED_SUBSET_MATCH"
            return "TIER_A"
            
        # TIER B: Review-Preferred
        # Good but not definitive
        if ev.alias_match in ("exact", "normalized") or (ev.artist_match and ev.platform_match):
            candidate.tier = "TIER_B"
            return "TIER_B"
            
        # TIER C: Ambiguous
        if ev.score() > 0.3:
            candidate.tier = "TIER_C"
            return "TIER_C"
            
        # Default D
        candidate.tier = "TIER_D"
        return "TIER_D"


# ---------------------------------------------------------------------------
# Candidate Generation
# ---------------------------------------------------------------------------

class CandidateGenerator:
    """
    Generates candidates from local metadata and external adapters.
    Conservatively seeds the alias graph and crosswalks.
    """
    
    def __init__(self, metadata: MetadataAdapter, alias_graph: AliasGraph):
        self._meta = metadata
        self._aliases = alias_graph
        self.engine = AcceptanceEngine()

    def generate_all(self) -> Dict[str, List[Candidate]]:
        """
        Scan full library and generate candidates for each distinct album/release.
        Returns a map of local_id -> List[Candidate].
        """
        # Step 1: Group library by album
        lib = self._meta.library()
        by_album: Dict[str, List[TrackMeta]] = {}
        for track in lib:
            album = track.album or "Unknown Album"
            if album not in by_album:
                by_album[album] = []
            by_album[album].append(track)
            
        results = {}
        for album_name, tracks in by_album.items():
            results[album_name] = self.generate_for_release(album_name, tracks)
            
        return results

    def generate_for_release(self, album_name: str, tracks: List[TrackMeta]) -> List[Candidate]:
        """Generate candidates for one local absolute release grouping."""
        candidates = []
        
        # 1. Base local context
        local_artists = {t.display_artist for t in tracks if t.display_artist}
        local_platforms = {t.platform.lower() for t in tracks if t.platform}
        local_years = {t.year for t in tracks if t.year and t.year.isdigit()}
        local_track_count = len(tracks)

        # 2. Generate search slugs
        from .ingestion.ign_artwork_downloader import _slug_candidates
        slugs = _slug_candidates(album_name)

        # 3. Simulate/Perform external search (VGMdb primary)
        # Note: In production, this would call vgmdb_ingester.search_album()
        # For this execution, we use the evidence model against simulated hits.
        # We also check the AliasGraph for known remappings.
        
        for slug in slugs:
            # Check AliasGraph for mapping
            alias_set = self._aliases.lookup(slug, entity_type="release")
            if alias_set:
                evidence = Evidence(
                    alias_match="exact",
                    external_id_match=True,
                    source="AliasGraph"
                )
                c = Candidate(
                    local_id=album_name,
                    external_id=alias_set.vgmdb_id or alias_set.canonical,
                    entity_type="release",
                    evidence=evidence,
                    provenance=f"AliasGraph hit for {slug}"
                )
                self.engine.evaluate(c)
                candidates.append(c)

        # 4. Strategy: Track title overlap (Partial/Curated subset detection)
        # If we have external tracklists (not yet in Phase 12 scope for bulk),
        # we would compare track sets. For now, we rely on Release+Artist+Platform.
        
        return candidates


# ---------------------------------------------------------------------------
# Manual Review Queue
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]
REVIEW_QUEUE_PATH = ROOT / "data" / "derived" / "atlas_staging" / "music" / "review_queue.json"

class ReviewQueue:
    """Manages candidates needing human judgment."""
    
    def __init__(self, path: Path = REVIEW_QUEUE_PATH):
        self.path = path
        self.queue: List[Candidate] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Handle dict-based persistence
                    self.queue = []
                    for c_dict in data.get("queue", []):
                        ev = Evidence(**c_dict.pop("evidence"))
                        co = Contradiction(**c_dict.pop("contradictions"))
                        c = Candidate(evidence=ev, contradictions=co, **c_dict)
                        self.queue.append(c)
            except Exception as e:
                print(f"Failed to load review queue: {e}")
                self.queue = []

    def add(self, candidate: Candidate):
        if candidate.tier in ("TIER_B", "TIER_C"):
            if not any(c.local_id == candidate.local_id and c.external_id == candidate.external_id for c in self.queue):
                self.queue.append(candidate)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "count": len(self.queue),
            "queue": [c.to_dict() for c in self.queue]
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Review queue saved: {self.path}")
