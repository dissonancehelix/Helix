"""
composer_graph.py — Composer Knowledge Graph
=============================================
In-memory graph of composers, tracks, games, and sound teams.
Backed by dicts for JSON serialization; optional networkx overlay
for graph algorithms (centrality, community detection, shortest path).

Relationship model
------------------
All relationships are typed and directional:

  composer:X  --wrote-->           track:Y
  composer:X  --worked_on-->       game:Y
  composer:X  --member_of-->       team:Y
  composer:X  --influenced_by-->   composer:Y
  composer:X  --collaborated_with--> composer:Y   (symmetric)
  track:X     --part_of-->         game:Y
  track:X     --attributed_to-->   composer:Y     (analysis result)

Graph uses typed node IDs: "composer:slug", "track:slug", "game:slug", "team:slug"

API
---
graph = ComposerGraph()
graph.add_composer(node)
graph.add_track(node)
graph.add_relationship(rel)
graph.composers_for_track(track_id) -> list[ComposerNode]
graph.tracks_for_composer(composer_id) -> list[TrackNode]
graph.collaborators(composer_id) -> list[ComposerNode]
graph.to_dict() -> dict
graph.from_dict(d) -> None   (loads into existing graph)
graph.save(path)
graph.load(path)
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from labs.music_lab.knowledge.composer_schema import (
    ComposerNode, GameNode, Relationship, SoundTeamNode, TrackNode,
    SoundtrackNode, StudioNode, PlatformNode, SoundDriverNode,
    SEED_COMPOSERS, SEED_SOUND_TEAMS, S3K_GAME,
    S3K_PLATFORM, S3K_SOUND_DRIVER, S3K_STUDIO_SEGA, S3K_SOUNDTRACK,
)

log = logging.getLogger(__name__)

# Optional networkx
try:
    import networkx as _nx
    _HAS_NETWORKX = True
except ImportError:
    _nx = None  # type: ignore
    _HAS_NETWORKX = False


# ---------------------------------------------------------------------------
# Prefixed node ID helpers
# ---------------------------------------------------------------------------

def cid(slug: str)   -> str: return f"composer:{slug}"
def tid(slug: str)   -> str: return f"track:{slug}"
def gid(slug: str)   -> str: return f"game:{slug}"
def tmid(slug: str)  -> str: return f"team:{slug}"
def stid(slug: str)  -> str: return f"soundtrack:{slug}"
def sdid(slug: str)  -> str: return f"studio:{slug}"
def plid(slug: str)  -> str: return f"platform:{slug}"
def drid(slug: str)  -> str: return f"driver:{slug}"


# ---------------------------------------------------------------------------
# ComposerGraph
# ---------------------------------------------------------------------------

class ComposerGraph:
    """
    In-memory knowledge graph for VGM composer metadata.
    """

    def __init__(self) -> None:
        # Node stores keyed by slug (without prefix)
        self._composers:   dict[str, ComposerNode]    = {}
        self._tracks:      dict[str, TrackNode]       = {}
        self._games:       dict[str, GameNode]        = {}
        self._teams:       dict[str, SoundTeamNode]   = {}
        self._soundtracks: dict[str, SoundtrackNode]  = {}
        self._studios:     dict[str, StudioNode]      = {}
        self._platforms:   dict[str, PlatformNode]    = {}
        self._drivers:     dict[str, SoundDriverNode] = {}

        # Relationship list
        self._rels:        list[Relationship]        = []

        # Adjacency indexes: source → list[Relationship]
        self._out_edges:   dict[str, list[Relationship]] = defaultdict(list)
        # target → list[Relationship]
        self._in_edges:    dict[str, list[Relationship]] = defaultdict(list)

    # -----------------------------------------------------------------------
    # Node insertion
    # -----------------------------------------------------------------------

    def add_composer(self, node: ComposerNode) -> None:
        key = cid(node.composer_id)
        existing = self._composers.get(node.composer_id)
        if existing:
            _merge_composer(existing, node)
        else:
            self._composers[node.composer_id] = node

    def add_track(self, node: TrackNode) -> None:
        self._tracks[node.track_id] = node

    def add_game(self, node: GameNode) -> None:
        self._games[node.game_id] = node

    def add_team(self, node: SoundTeamNode) -> None:
        self._teams[node.team_id] = node

    def add_soundtrack(self, node: SoundtrackNode) -> None:
        self._soundtracks[node.soundtrack_id] = node

    def add_studio(self, node: StudioNode) -> None:
        self._studios[node.studio_id] = node

    def add_platform(self, node: PlatformNode) -> None:
        self._platforms[node.platform_id] = node

    def add_driver(self, node: SoundDriverNode) -> None:
        self._drivers[node.driver_id] = node

    # -----------------------------------------------------------------------
    # Getters for new types
    # -----------------------------------------------------------------------

    def get_soundtrack(self, soundtrack_id: str) -> SoundtrackNode | None:
        return self._soundtracks.get(soundtrack_id)

    def get_studio(self, studio_id: str) -> StudioNode | None:
        return self._studios.get(studio_id)

    def get_platform(self, platform_id: str) -> PlatformNode | None:
        return self._platforms.get(platform_id)

    def get_driver(self, driver_id: str) -> SoundDriverNode | None:
        return self._drivers.get(driver_id)

    def all_studios(self) -> list[StudioNode]:
        return list(self._studios.values())

    def all_platforms(self) -> list[PlatformNode]:
        return list(self._platforms.values())

    def all_drivers(self) -> list[SoundDriverNode]:
        return list(self._drivers.values())

    def all_soundtracks(self) -> list[SoundtrackNode]:
        return list(self._soundtracks.values())

    # -----------------------------------------------------------------------
    # Relationship insertion
    # -----------------------------------------------------------------------

    def add_relationship(self, rel: Relationship) -> None:
        self._rels.append(rel)
        self._out_edges[rel.source].append(rel)
        self._in_edges[rel.target].append(rel)

    def relate(
        self,
        source: str,
        relation: str,
        target: str,
        confidence: float = 1.0,
        source_name: str = "",
        notes: str = "",
    ) -> None:
        """Convenience wrapper."""
        self.add_relationship(Relationship(
            source=source, relation=relation, target=target,
            confidence=confidence, source_name=source_name, notes=notes,
        ))

    # -----------------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------------

    def get_composer(self, composer_id: str) -> ComposerNode | None:
        return self._composers.get(composer_id)

    def get_track(self, track_id: str) -> TrackNode | None:
        return self._tracks.get(track_id)

    def get_game(self, game_id: str) -> GameNode | None:
        return self._games.get(game_id)

    def composers_for_track(self, track_id: str) -> list[ComposerNode]:
        """All composers with a 'wrote' or 'attributed_to' edge to this track."""
        results: list[ComposerNode] = []
        for rel in self._in_edges.get(tid(track_id), []):
            if rel.relation in ("wrote", "attributed_to"):
                c_id = rel.source.removeprefix("composer:")
                if c_id in self._composers:
                    results.append(self._composers[c_id])
        return results

    def tracks_for_composer(self, composer_id: str) -> list[TrackNode]:
        """All tracks written by a composer (via 'wrote' edges)."""
        results: list[TrackNode] = []
        for rel in self._out_edges.get(cid(composer_id), []):
            if rel.relation == "wrote":
                t_id = rel.target.removeprefix("track:")
                if t_id in self._tracks:
                    results.append(self._tracks[t_id])
        return results

    def games_for_composer(self, composer_id: str) -> list[GameNode]:
        results: list[GameNode] = []
        for rel in self._out_edges.get(cid(composer_id), []):
            if rel.relation == "worked_on":
                g_id = rel.target.removeprefix("game:")
                if g_id in self._games:
                    results.append(self._games[g_id])
        return results

    def collaborators(self, composer_id: str) -> list[tuple[ComposerNode, float]]:
        """
        Composers who collaborated with composer_id on the same game.
        Returns [(composer, shared_game_count)] sorted descending.
        """
        my_games = {g.game_id for g in self.games_for_composer(composer_id)}
        collab_count: dict[str, int] = defaultdict(int)

        for c_id, c_node in self._composers.items():
            if c_id == composer_id:
                continue
            their_games = {g.game_id for g in self.games_for_composer(c_id)}
            shared = len(my_games & their_games)
            if shared:
                collab_count[c_id] = shared

        result = [
            (self._composers[c_id], count)
            for c_id, count in collab_count.items()
        ]
        result.sort(key=lambda x: -x[1])
        return result

    def influenced_by(self, composer_id: str) -> list[ComposerNode]:
        results = []
        for rel in self._out_edges.get(cid(composer_id), []):
            if rel.relation == "influenced_by":
                inf_id = rel.target.removeprefix("composer:")
                if inf_id in self._composers:
                    results.append(self._composers[inf_id])
        return results

    def all_composers(self) -> list[ComposerNode]:
        return list(self._composers.values())

    def all_tracks(self) -> list[TrackNode]:
        return list(self._tracks.values())

    def all_games(self) -> list[GameNode]:
        return list(self._games.values())

    def all_teams(self) -> list[SoundTeamNode]:
        return list(self._teams.values())

    def all_relationships(self) -> list[Relationship]:
        return list(self._rels)

    def relationship_count(self) -> int:
        return len(self._rels)

    def relationships_between(
        self,
        source_id: str,
        target_id: str,
    ) -> list[Relationship]:
        return [r for r in self._rels if r.source == source_id and r.target == target_id]

    # -----------------------------------------------------------------------
    # Style profile queries
    # -----------------------------------------------------------------------

    def composer_style_report(self, composer_id: str) -> dict[str, Any]:
        """
        Compile a style profile for a composer from graph data + analysis.
        """
        c = self._composers.get(composer_id)
        if not c:
            return {}

        tracks = self.tracks_for_composer(composer_id)
        games  = self.games_for_composer(composer_id)
        collabs = self.collaborators(composer_id)

        return {
            "composer_id":    composer_id,
            "full_name":      c.full_name,
            "aliases":        c.aliases,
            "nationality":    c.nationality,
            "years_active":   c.years_active,
            "studios":        c.studios,
            "sound_teams":    c.sound_teams,
            "bio_summary":    c.bio_summary,
            "external_ids":   c.external_ids,
            "track_count":    len(tracks),
            "track_ids":      [t.track_id for t in tracks],
            "game_count":     len(games),
            "game_titles":    [g.title for g in games],
            "collaborators":  [
                {"composer": col.full_name, "shared_games": n}
                for col, n in collabs[:5]
            ],
            "style_traits":   c.style_traits,
            "fingerprint_available": c.fingerprint_vector is not None,
            "cluster_memberships":   c.cluster_memberships,
            "representative_tracks": c.representative_tracks,
        }

    # -----------------------------------------------------------------------
    # networkx graph export
    # -----------------------------------------------------------------------

    def to_networkx(self) -> Any:
        """Export as a directed networkx graph. Returns None if networkx unavailable."""
        if not _HAS_NETWORKX:
            return None

        G = _nx.DiGraph()

        for c in self._composers.values():
            G.add_node(cid(c.composer_id),  type="composer",   label=c.full_name)
        for t in self._tracks.values():
            G.add_node(tid(t.track_id),     type="track",      label=t.title or t.track_id)
        for g in self._games.values():
            G.add_node(gid(g.game_id),      type="game",       label=g.title)
        for tm in self._teams.values():
            G.add_node(tmid(tm.team_id),    type="team",       label=tm.name)
        for s in self._soundtracks.values():
            G.add_node(stid(s.soundtrack_id), type="soundtrack", label=s.title)
        for st in self._studios.values():
            G.add_node(sdid(st.studio_id),  type="studio",     label=st.name)
        for p in self._platforms.values():
            G.add_node(plid(p.platform_id), type="platform",   label=p.name)
        for d in self._drivers.values():
            G.add_node(drid(d.driver_id),   type="driver",     label=d.name)

        for rel in self._rels:
            G.add_edge(
                rel.source, rel.target,
                relation=rel.relation,
                confidence=rel.confidence,
                source_name=rel.source_name,
            )

        return G

    def graph_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "composers":     len(self._composers),
            "tracks":        len(self._tracks),
            "games":         len(self._games),
            "teams":         len(self._teams),
            "soundtracks":   len(self._soundtracks),
            "studios":       len(self._studios),
            "platforms":     len(self._platforms),
            "drivers":       len(self._drivers),
            "relationships": len(self._rels),
        }

        if _HAS_NETWORKX:
            G = self.to_networkx()
            if G:
                stats["networkx_nodes"]     = G.number_of_nodes()
                stats["networkx_edges"]     = G.number_of_edges()
                stats["weakly_connected"]   = _nx.number_weakly_connected_components(G)
                # Betweenness centrality of composer nodes
                try:
                    bc = _nx.betweenness_centrality(G)
                    composer_bc = {
                        k.removeprefix("composer:"): round(v, 4)
                        for k, v in bc.items()
                        if k.startswith("composer:")
                    }
                    stats["top_central_composers"] = sorted(
                        composer_bc.items(), key=lambda x: -x[1]
                    )[:5]
                except Exception:
                    pass

        return stats

    # -----------------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "composers":     [c.to_dict()  for c  in self._composers.values()],
            "tracks":        [t.to_dict()  for t  in self._tracks.values()],
            "games":         [g.to_dict()  for g  in self._games.values()],
            "teams":         [tm.to_dict() for tm in self._teams.values()],
            "soundtracks":   [s.to_dict()  for s  in self._soundtracks.values()],
            "studios":       [st.to_dict() for st in self._studios.values()],
            "platforms":     [p.to_dict()  for p  in self._platforms.values()],
            "drivers":       [d.to_dict()  for d  in self._drivers.values()],
            "relationships": [r.to_dict()  for r  in self._rels],
        }

    def from_dict(self, d: dict[str, Any]) -> None:
        for item in d.get("composers", []):
            self.add_composer(ComposerNode.from_dict(item))
        for item in d.get("tracks", []):
            self.add_track(TrackNode.from_dict(item))
        for item in d.get("games", []):
            self.add_game(GameNode.from_dict(item))
        for item in d.get("teams", []):
            self.add_team(SoundTeamNode.from_dict(item))
        for item in d.get("soundtracks", []):
            self.add_soundtrack(SoundtrackNode.from_dict(item))
        for item in d.get("studios", []):
            self.add_studio(StudioNode.from_dict(item))
        for item in d.get("platforms", []):
            self.add_platform(PlatformNode.from_dict(item))
        for item in d.get("drivers", []):
            self.add_driver(SoundDriverNode.from_dict(item))
        for item in d.get("relationships", []):
            self.add_relationship(Relationship.from_dict(item))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        log.info("composer_graph: saved to %s (%d composers, %d rels)",
                 path, len(self._composers), len(self._rels))

    def load(self, path: Path) -> None:
        if not path.exists():
            log.debug("composer_graph: no graph file at %s", path)
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self.from_dict(data)
        log.info("composer_graph: loaded from %s (%d composers, %d rels)",
                 path, len(self._composers), len(self._rels))

    # -----------------------------------------------------------------------
    # Seed with S3K ground truth
    # -----------------------------------------------------------------------

    def seed_s3k(self) -> None:
        """
        Populate graph with S3K seed data from composer_schema.py.
        Called once on first use; idempotent.
        """
        # Game node
        self.add_game(S3K_GAME)

        # Sound teams
        for team in SEED_SOUND_TEAMS:
            self.add_team(team)
            for member_id in team.members:
                self.relate(
                    cid(member_id), "member_of", tmid(team.team_id),
                    confidence=1.0, source_name="sonic_retro",
                )

        # Composers + worked_on
        for composer in SEED_COMPOSERS:
            self.add_composer(composer)
            self.relate(
                cid(composer.composer_id), "worked_on", gid(S3K_GAME.game_id),
                confidence=1.0 if composer.composer_id in [
                    "masayuki_nagao", "tatsuyuki_maeda", "jun_senoue", "yoshiaki_kashima"
                ] else 0.8,
                source_name="sonic_retro",
            )

        # Collaborations (all composers who worked on S3K collaborated with each other)
        s3k_composers = S3K_GAME.composers
        for i, c1 in enumerate(s3k_composers):
            for c2 in s3k_composers[i + 1:]:
                self.relate(
                    cid(c1), "collaborated_with", cid(c2),
                    confidence=0.9, source_name="sonic_retro",
                    notes="Co-composed Sonic 3 & Knuckles (1994)",
                )

        # Platform + sound driver + studio + soundtrack
        self.add_platform(S3K_PLATFORM)
        self.add_driver(S3K_SOUND_DRIVER)
        self.add_studio(S3K_STUDIO_SEGA)
        self.add_soundtrack(S3K_SOUNDTRACK)

        # Game → platform / studio relationships
        self.relate(
            gid(S3K_GAME.game_id), "runs_on", plid(S3K_PLATFORM.platform_id),
            confidence=1.0, source_name="seed",
        )
        self.relate(
            gid(S3K_GAME.game_id), "developed_by", sdid(S3K_STUDIO_SEGA.studio_id),
            confidence=1.0, source_name="seed",
        )
        self.relate(
            gid(S3K_GAME.game_id), "published_by", sdid(S3K_STUDIO_SEGA.studio_id),
            confidence=1.0, source_name="seed",
        )
        self.relate(
            gid(S3K_GAME.game_id), "uses_sound_driver", drid(S3K_SOUND_DRIVER.driver_id),
            confidence=1.0, source_name="seed",
        )

        # Soundtrack → game
        self.relate(
            stid(S3K_SOUNDTRACK.soundtrack_id), "documents", gid(S3K_GAME.game_id),
            confidence=1.0, source_name="seed",
        )

        # Composers → worked_at → Sega studio
        sega_composers = ["masayuki_nagao", "tatsuyuki_maeda", "jun_senoue", "yoshiaki_kashima"]
        for c_id in sega_composers:
            self.relate(
                cid(c_id), "worked_at", sdid(S3K_STUDIO_SEGA.studio_id),
                confidence=1.0, source_name="seed",
            )


# ---------------------------------------------------------------------------
# Singleton graph accessor
# ---------------------------------------------------------------------------

_GRAPH: ComposerGraph | None = None


def get_graph(seed: bool = True, graph_path: Path | None = None) -> ComposerGraph:
    """
    Return the singleton ComposerGraph.
    Loads from disk if graph_path exists; seeds S3K data if empty.
    """
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = ComposerGraph()
        if graph_path and graph_path.exists():
            _GRAPH.load(graph_path)
        if seed and len(_GRAPH._composers) == 0:
            _GRAPH.seed_s3k()
    return _GRAPH


def reset_graph() -> None:
    global _GRAPH
    _GRAPH = None


# ---------------------------------------------------------------------------
# Merge helper
# ---------------------------------------------------------------------------

def _merge_composer(existing: ComposerNode, incoming: ComposerNode) -> None:
    """Merge incoming data into existing node, preserving non-None values."""
    for field_name in [
        "nationality", "birth_year", "death_year", "years_active",
        "bio_summary", "bio_url",
    ]:
        if getattr(existing, field_name) is None:
            val = getattr(incoming, field_name, None)
            if val is not None:
                setattr(existing, field_name, val)

    for list_field in ["aliases", "instruments", "studios", "sound_teams",
                        "cluster_memberships", "representative_tracks"]:
        existing_list = getattr(existing, list_field, [])
        incoming_list = getattr(incoming, list_field, [])
        merged = list(dict.fromkeys(existing_list + incoming_list))
        setattr(existing, list_field, merged)

    existing.external_ids.update(incoming.external_ids)
    existing.style_traits.update(incoming.style_traits)

    if incoming.fingerprint_vector is not None:
        existing.fingerprint_vector = incoming.fingerprint_vector
