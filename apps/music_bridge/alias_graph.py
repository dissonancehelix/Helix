"""
alias_graph.py — Phase 12: Alias Graph, Crosswalks, and External Identity.

Purpose:
  Complete the external identity graph so Helix can reliably match tracks,
  artists, and releases across systems with different naming conventions.

Priority order (from helix_music_local_handoff.md):
  1. Artist / composer aliases
  2. Soundtrack / release aliases
  3. Game / franchise aliases
  4. Track-title aliases

Sources targeted:
  - MusicBrainz (canonical artist/release IDs)
  - Wikidata (cross-system entity linking)
  - Wikipedia (game/franchise metadata)
  - VGMdb (VGM-specific soundtrack/game identity)
  - Spotify (crosswalk for retrieval)
  - Local Helix entities (existing codex)

Key problem this solves:
  Japanese / romaji / English naming is currently unanchored.
  Spotify retrieval is brittle without stable artist+release identity.
  One-off missing tracks can be found through graph context instead of
  fragile search strings.

Status: SCAFFOLD — types and structure defined.
        Implement source fetchers in Phase 12 proper after bridge is stable.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
ALIAS_STORE_PATH = HELIX_ROOT / "codex/atlas/entities/alias_graph.json"


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------

@dataclass
class AliasSet:
    """
    All known names for one entity (artist, release, game, or track).
    The canonical name is the preferred display form.
    """
    entity_type: str            # "artist" | "release" | "game" | "track" | "franchise"
    canonical: str              # preferred name
    aliases: list[str] = field(default_factory=list)     # alternate names
    japanese: Optional[str] = None   # Japanese script form
    romaji: Optional[str] = None     # Romanized form
    english: Optional[str] = None    # English localization

    # External IDs — populated by source fetchers
    musicbrainz_id: Optional[str] = None   # MBID
    wikidata_id: Optional[str] = None      # Q-number
    vgmdb_id: Optional[str] = None         # VGMdb numeric ID
    spotify_id: Optional[str] = None       # Spotify URI

    def all_names(self) -> list[str]:
        """All known name variants, deduplicated."""
        seen = set()
        result = []
        for n in [self.canonical] + self.aliases + [
            self.japanese, self.romaji, self.english
        ]:
            if n and n not in seen:
                seen.add(n)
                result.append(n)
        return result

    def matches(self, query: str) -> bool:
        """Return True if query matches any known name (case-insensitive)."""
        q = query.lower().strip()
        return any(n.lower().strip() == q for n in self.all_names())


@dataclass
class Evidence:
    """Multi-signal evidence container for a candidate match."""
    alias_match: str = "none"           # "exact" | "normalized" | "fuzzy" | "none"
    artist_match: bool = False
    composer_match: bool = False
    year_proximity: bool = False        # +/- 2 years
    platform_match: bool = False
    track_count_overlap: float = 0.0    # 0.0-1.0 overlap ratio
    external_id_match: bool = False
    franchise_overlap: bool = False
    source_provenance: list[str] = field(default_factory=list)

    def summary(self) -> str:
        signals = []
        if self.alias_match != "none": signals.append(f"alias:{self.alias_match}")
        if self.artist_match: signals.append("artist_match")
        if self.platform_match: signals.append("platform_match")
        if self.track_count_overlap > 0: signals.append(f"tracks:{self.track_count_overlap:.2f}")
        return " + ".join(signals)


@dataclass
class Contradiction:
    """Contradiction gates that block auto-acceptance (Tier A)."""
    franchise_mismatch: bool = False
    composer_mismatch: bool = False
    year_mismatch: bool = False         # > 5 years (excluding remasters)
    platform_mismatch: bool = False
    competing_candidate_id: Optional[str] = None
    low_overlap: bool = False           # track overlap is too low for curated subset

    def any(self) -> bool:
        return any([self.franchise_mismatch, self.composer_mismatch, 
                    self.year_mismatch, self.platform_mismatch, 
                    self.competing_candidate_id, self.low_overlap])

    def describe(self) -> str:
        flags = [k for k, v in self.__dict__.items() if v]
        return ", ".join(flags) if flags else "none"


@dataclass
class Candidate:
    """
    Candidate link between a local entity and an external record.
    Must be tiered before acceptance.
    """
    local_id: str
    external_id: str
    entity_type: str
    
    tier: str = "TIER_D"                # A (Auto), B (Review-Preferred), C (Ambiguous), D (Reject)
    evidence: Evidence = field(default_factory=Evidence)
    contradictions: Contradiction = field(default_factory=Contradiction)
    
    match_category: str = "PARTIAL_UNCERTAIN"  # FULL | CURATED_SUBSET | PARTIAL | CONTRADICTED
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


@dataclass
class Crosswalk:
    """
    A resolved identity link between a Helix entity and an external service.
    Used for Spotify retrieval, MusicBrainz enrichment, etc.
    """
    helix_id: str               # Internal Helix entity ID
    entity_type: str
    canonical_name: str
    service: str                # "spotify" | "musicbrainz" | "vgmdb" | "wikidata"
    external_id: str
    confidence: float           # 0.0–1.0
    verified: bool = False


# ---------------------------------------------------------------------------
# Alias store (simple JSON-backed for Phase 12)
# ---------------------------------------------------------------------------

class AliasGraph:
    """
    In-memory alias graph backed by a JSON store.

    Phase 12 implementation plan:
      1. Seed from existing Helix codex entities (composers, games)
      2. Enrich artist aliases from MusicBrainz artist search
      3. Enrich release aliases from VGMdb soundtrack entries
      4. Link game/franchise aliases via Wikidata
      5. Build Spotify crosswalk for retrieval (artist + album ID pairs)
      6. Persist to codex/atlas/entities/alias_graph.json
      7. Expose lookup API used by PlaycountRecoveryEngine and retrieval
    """

    def __init__(self):
        self._entities: dict[str, AliasSet] = {}   # canonical → AliasSet
        self._crosswalks: list[Crosswalk] = []

    def add(self, alias_set: AliasSet) -> None:
        self._entities[alias_set.canonical] = alias_set

    def lookup(self, query: str, entity_type: str = None) -> Optional[AliasSet]:
        """Find the AliasSet that matches query, optionally filtered by type."""
        for alias_set in self._entities.values():
            if entity_type and alias_set.entity_type != entity_type:
                continue
            if alias_set.matches(query):
                return alias_set
        return None

    def resolve_to_canonical(self, query: str, entity_type: str = None) -> Optional[str]:
        """Return the canonical name for a query string, or None if unknown."""
        result = self.lookup(query, entity_type)
        return result.canonical if result else None

    def add_crosswalk(self, crosswalk: Crosswalk) -> None:
        self._crosswalks.append(crosswalk)

    def crosswalks_for(self, helix_id: str) -> list[Crosswalk]:
        return [c for c in self._crosswalks if c.helix_id == helix_id]

    def materialize_candidate(self, candidate: Candidate) -> bool:
        """
        Promote a Tier A candidate to the persistent alias graph or crosswalks.
        Returns True if materialized.
        """
        if candidate.tier != "TIER_A":
            return False

        # Add crosswalk for the external identity
        cx = Crosswalk(
            helix_id=candidate.local_id,
            entity_type=candidate.entity_type,
            canonical_name=candidate.local_id,
            service=candidate.provenance.split()[0].replace("hit", "").strip(),
            external_id=candidate.external_id,
            confidence=0.98 if candidate.match_category == "FULL_MATCH" else 0.85,
            verified=True
        )
        self.add_crosswalk(cx)
        
        # Update/Create AliasSet if needed
        existing = self.lookup(candidate.local_id, entity_type=candidate.entity_type)
        if not existing:
            a = AliasSet(
                entity_type=candidate.entity_type,
                canonical=candidate.local_id,
                vgmdb_id=candidate.external_id if "VGMdb" in candidate.provenance else None
            )
            self.add(a)
        elif "VGMdb" in candidate.provenance and not existing.vgmdb_id:
            existing.vgmdb_id = candidate.external_id
            
        return True

    def save(self, path: Path = ALIAS_STORE_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "entities": [
                {
                    "entity_type": a.entity_type,
                    "canonical": a.canonical,
                    "aliases": a.aliases,
                    "japanese": a.japanese,
                    "romaji": a.romaji,
                    "english": a.english,
                    "musicbrainz_id": a.musicbrainz_id,
                    "wikidata_id": a.wikidata_id,
                    "vgmdb_id": a.vgmdb_id,
                    "spotify_id": a.spotify_id,
                }
                for a in self._entities.values()
            ],
            "crosswalks": [
                {
                    "helix_id": c.helix_id,
                    "entity_type": c.entity_type,
                    "canonical_name": c.canonical_name,
                    "service": c.service,
                    "external_id": c.external_id,
                    "confidence": c.confidence,
                    "verified": c.verified,
                }
                for c in self._crosswalks
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Log to codex index metadata too?

    def load(self, path: Path = ALIAS_STORE_PATH) -> None:
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for e in data.get("entities", []):
            self._entities[e["canonical"]] = AliasSet(**e)
        for c in data.get("crosswalks", []):
            self._crosswalks.append(Crosswalk(**c))

    @property
    def entity_count(self) -> int:
        return len(self._entities)

    @property
    def crosswalk_count(self) -> int:
        return len(self._crosswalks)


# ---------------------------------------------------------------------------
# Source seeders (Phase 12 — stubbed)
# ---------------------------------------------------------------------------

def seed_from_codex(graph: AliasGraph) -> int:
    """
    Seed the alias graph from existing Helix codex artist JSON files.
    Returns number of entities added.
    """
    # Check both artist and soundteam dirs
    roots = [
        HELIX_ROOT / "codex/atlas/music/artists",
        HELIX_ROOT / "codex/atlas/music/soundteams"
    ]
    count = 0
    for root in roots:
        if not root.exists():
            continue
        for f in root.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                # Match various naming conventions used in the repo
                canonical = data.get("label") or data.get("name") or data.get("canonical_name")
                if not canonical:
                    # Try to derive from entity_id: music.composer:jun_senoue -> Jun Senoue (fallback)
                    eid = data.get("entity_id", "")
                    if ":" in eid:
                        canonical = eid.split(":")[-1].replace("_", " ").title()
                    else:
                        continue
                
                e_type_raw = data.get("entity_type", "artist").lower()
                e_type = "artist"
                if "composer" in e_type_raw: e_type = "artist"
                elif "soundteam" in e_type_raw: e_type = "artist"
                elif "game" in e_type_raw: e_type = "game"
                
                aliases = data.get("aliases", [])
                # Also check for 'library.artist_keys' as aliases
                if "library" in data and "artist_keys" in data["library"]:
                    aliases = list(set(aliases + data["library"]["artist_keys"]))

                a = AliasSet(
                    entity_type=e_type,
                    canonical=canonical,
                    aliases=aliases,
                    japanese=data.get("japanese_name"),
                    romaji=data.get("romaji_name"),
                    english=data.get("english_name"),
                    musicbrainz_id=data.get("external_ids", {}).get("musicbrainz"),
                    wikidata_id=data.get("external_ids", {}).get("wikidata"),
                    vgmdb_id=data.get("external_ids", {}).get("vgmdb"),
                    spotify_id=data.get("external_ids", {}).get("spotify"),
                )
                graph.add(a)
                count += 1
            except Exception:
                pass
    return count


def enrich_from_musicbrainz(graph: AliasGraph, entity_type: str = "artist") -> int:
    """
    Phase 12: Enrich entities with MusicBrainz IDs and alias lists.
    SCAFFOLD — implement in Phase 12 proper.
    """
    # TODO: for each entity in graph without musicbrainz_id:
    #   query https://musicbrainz.org/ws/2/{entity_type}/?query={name}&fmt=json
    #   match by name similarity
    #   set musicbrainz_id, add aliases from MB aliases list
    return 0


def build_spotify_crosswalks(graph: AliasGraph) -> int:
    """
    Phase 12: Build Spotify crosswalk for artists/releases.
    SCAFFOLD — implement in Phase 12 proper.
    """
    # TODO: for each artist entity in graph:
    #   query Spotify search API: /v1/search?q={name}&type=artist
    #   match by name + genre similarity
    #   store Crosswalk(helix_id, "artist", canonical, "spotify", spotify_id, confidence)
    return 0


if __name__ == "__main__":
    graph = AliasGraph()
    n = seed_from_codex(graph)
    print(f"Phase 12 scaffold — seeded {n} entities from codex")
    print(f"Alias graph: {graph.entity_count} entities, {graph.crosswalk_count} crosswalks")
    print("(Full enrichment pending Phase 12)")
