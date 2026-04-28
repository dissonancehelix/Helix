"""
candidate_engine.py — Phase 12: Conservative Candidate Generation and Evidence Scoring.

This engine matches local curated library albums against external authoritative sources (VGMdb, MusicBrainz).
It implements multi-signal evidence scoring and strict contradiction gates to ensure 
that "Missing is Better Than Wrong".
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from .metadata_adapter import MetadataAdapter, TrackMeta
from .alias_graph import AliasGraph, AliasSet, Candidate, Evidence, Contradiction
from system.tools.music_pipeline.sources.vgmdb_ingester import fetch_album

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Acceptance Policy
# ---------------------------------------------------------------------------

class AcceptancePolicy:
    """
    Conservatively assigns Tiers to Candidates.
    Updated in Phase 12.5 with audit-backed threshold tightening.
    """
    
    # Titles that carry no authority on their own
    RISKY_TITLES = {
        "best selection", "selections", "best of", "greatest hits", 
        "soundtrack", "original soundtrack", "disk 1", "cd 1", "disc 1",
        "music", "background music", "bgm", "unknown"
    }
    
    @staticmethod
    def evaluate(candidate: Candidate) -> str:
        ev = candidate.evidence
        co = candidate.contradictions
        
        # Rule 1: Contradictions always block auto-accept (Tier D)
        if co.any():
            candidate.tier = "TIER_D"
            candidate.match_category = "CONTRADICTED"
            return "TIER_D"

        # Rule 2: Generic Title Gate
        # Titles like "Best Selection" should NEVER be Tier A without extreme evidence
        is_generic = candidate.local_id.lower().strip() in AcceptancePolicy.RISKY_TITLES
        
        # TIER A: Auto-Accept (High confidence, multi-signal)
        # Requirements:
        # - Exact/Normalized Alias match
        # - AND (Artist match OR Platform match)
        # - AND (Year Proximity OR ID match)
        # - AND NOT Generic Title
        # - AND High track overlap (>0.8)
        if ev.alias_match in ("exact", "normalized") and not is_generic:
            if (ev.artist_match or ev.platform_match) and (ev.year_proximity or ev.external_id_match):
                if ev.track_count_overlap > 0.8: # Tightened from 0.6
                    candidate.tier = "TIER_A"
                    candidate.match_category = "FULL_MATCH" if ev.track_count_overlap > 0.9 else "CURATED_SUBSET_MATCH"
                    return "TIER_A"

        # TIER B: Review-Preferred
        # Good match but some risk (Generic title with evidence, 
        # or moderate overlap, or folder-derived metadata)
        if ev.alias_match in ("exact", "normalized") or (ev.artist_match and ev.track_count_overlap > 0.4):
            candidate.tier = "TIER_B"
            candidate.match_category = "PARTIAL_UNCERTAIN"
            return "TIER_B"

        # TIER C: Ambiguous
        if ev.alias_match != "none" or ev.score() > 0.2:
            candidate.tier = "TIER_C"
            return "TIER_C"

        # TIER D: Reject
        candidate.tier = "TIER_D"
        return "TIER_D"


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class CandidateGenerationEngine:
    """
    Generates candidates for local releases.
    Integrates VGMdb search and local AliasGraph checks.
    """
    
    def __init__(self, metadata: MetadataAdapter, alias_graph: AliasGraph):
        self._meta = metadata
        self._aliases = alias_graph
        self.policy = AcceptancePolicy()

    def generate_all(self) -> List[Candidate]:
        """Runs the candidate generation pass over the full library."""
        lib = self._meta.library()
        by_album = self._group_by_album(lib)
        
        candidates = []
        for album_name, tracks in by_album.items():
            candidates.extend(self.generate_for_album(album_name, tracks))
            
        return candidates

    def _group_by_album(self, tracks: List[TrackMeta]) -> Dict[str, List[TrackMeta]]:
        groups = {}
        for t in tracks:
            album = t.album
            if not album or album.lower() in ("unknown album", "none", ""):
                # Fallback: parent folder name
                path = Path(t.file_path)
                parent = path.parent
                if parent.name.lower() in ("disc 1", "disc 2", "disc 3", "cd1", "cd2", "front", "scans"):
                    parent = parent.parent
                album = parent.name if parent else "Unknown Album"
            
            if album not in groups: groups[album] = []
            groups[album].append(t)
        return groups

    def generate_for_album(self, album_name: str, tracks: List[TrackMeta]) -> List[Candidate]:
        """Generates tiered candidates for a single local album group."""
        local_artists = {t.display_artist.lower() for t in tracks if t.display_artist}
        local_platforms = {t.platform.lower() for t in tracks if t.platform}
        local_years = {int(t.year) for t in tracks if t.year and t.year.isdigit()}
        local_count = len(tracks)

        candidates = []
        
        # 1. Alias Graph Seed Check
        alias_set = self._aliases.lookup(album_name, entity_type="release")
        if alias_set:
            ev = Evidence(
                alias_match="exact",
                external_id_match=True,
                source_provenance=["HelixAliasGraph"]
            )
            # Use data from alias set to fill evidence
            if alias_set.vgmdb_id:
                # In real usage, we might fetch the album to verify metadata
                pass
            
            c = Candidate(
                local_id=album_name,
                external_id=alias_set.vgmdb_id or alias_set.canonical,
                entity_type="release",
                evidence=ev,
                provenance="Seeded via Helix Alias Graph"
            )
            self.policy.evaluate(c)
            candidates.append(c)

        # 2. External Search (Strategy: Normalized Title match)
        # For Phase 12, we implement the search logic pattern but keep it conservative.
        # Logic to be implemented: call VGMdb search, for each result build Candidate.
        
        # Placeholder for VGMdb candidate logic (Phase 12 simulation)
        # ...
        
        return candidates

    def build_candidate_from_vgmdb(self, local_album: str, local_tracks: List[TrackMeta], vgmdb_album: dict) -> Candidate:
        """
        Calculates evidence and contradictions between a local group and a VGMdb result.
        """
        # 1. Title matching
        alias_type = "none"
        ext_title = vgmdb_album.get("title", "").lower()
        if local_album.lower() == ext_title:
            alias_type = "exact"
        elif self._normalize(local_album) == self._normalize(ext_title):
            alias_type = "normalized"
            
        # 2. Artist matching
        ext_artists = {a.lower() for a in vgmdb_album.get("composers", []) + vgmdb_album.get("performers", [])}
        local_artists = {t.display_artist.lower() for t in local_tracks if t.display_artist}
        artist_match = bool(local_artists & ext_artists)
        
        # 3. Year proximity
        year_match = False
        ext_year = vgmdb_album.get("year")
        local_years = {int(t.year) for t in local_tracks if t.year and t.year.isdigit()}
        if ext_year and local_years:
            if any(abs(ext_year - ly) <= 2 for ly in local_years):
                year_match = True
        
        # 4. Platform matching
        # ... Logic for platform normalization matching ...
        
        # 5. Track count overlap
        ext_count = len(vgmdb_album.get("track_list", []))
        overlap = 0.0
        if ext_count > 0:
            overlap = min(len(local_tracks) / ext_count, 1.0)

        ev = Evidence(
            alias_match=alias_type,
            artist_match=artist_match,
            year_proximity=year_match,
            track_count_overlap=overlap,
            source_provenance=["VGMdb"]
        )
        
        co = Contradiction()
        if ext_year and local_years and all(abs(ext_year - ly) > 5 for ly in local_years):
            co.year_mismatch = True
            
        c = Candidate(
            local_id=local_album,
            external_id=vgmdb_album["vgmdb_id"],
            entity_type="release",
            evidence=ev,
            contradictions=co,
            provenance="VGMdb Search Match"
        )
        
        self.policy.evaluate(c)
        return c

    def _normalize(self, s: str) -> str:
        from .playcount_recovery import normalize_key
        return normalize_key(s)
