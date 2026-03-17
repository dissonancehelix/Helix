"""
composer_store.py — Persistent Store for the Composer Knowledge Graph
=====================================================================
Provides JSON + optional SQLite persistence for ComposerGraph.

JSON store:  data/composer_graph.json  — full graph snapshot
SQLite store: data/helix_music.db      — structured tables for queries

The JSON store is the primary format: fast load/save, diff-friendly.
SQLite is a secondary index rebuilt from JSON for relational queries.

API
---
store = ComposerStore(data_dir)
store.save(graph)          → write graph to JSON (+ optional SQLite)
store.load() -> graph      → load from JSON
store.rebuild_db(graph)    → rebuild SQLite from graph
store.query_tracks(composer_id=...) -> list[dict]
store.query_composer(name=...) -> list[dict]
store.search_any(text) -> list[dict]
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from substrates.music.atlas_integration.composer_graph import ComposerGraph, get_graph, reset_graph
from substrates.music.atlas_integration.composer_schema import (
    ComposerNode, TrackNode, GameNode, SoundTeamNode, Relationship,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"
_GRAPH_JSON       = "composer_graph.json"
_DB_NAME          = "helix_music.db"


# ---------------------------------------------------------------------------
# ComposerStore
# ---------------------------------------------------------------------------

class ComposerStore:
    """
    Manages persistence of the ComposerGraph to disk.

    Parameters
    ----------
    data_dir : Path
        Directory for JSON and SQLite files. Created if absent.
    use_sqlite : bool
        Whether to maintain a SQLite index alongside JSON.
        Default True if sqlite3 available (always is in stdlib).
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        use_sqlite: bool = True,
    ) -> None:
        self.data_dir   = (data_dir or _DEFAULT_DATA_DIR).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.json_path  = self.data_dir / _GRAPH_JSON
        self.db_path    = self.data_dir / _DB_NAME
        self.use_sqlite = use_sqlite

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------

    def save(self, graph: ComposerGraph) -> None:
        """Write graph to JSON and optionally rebuild SQLite index."""
        data = graph.to_dict()
        data["_meta"] = {
            "saved_at":       _now_iso(),
            "composers":      len(graph._composers),
            "tracks":         len(graph._tracks),
            "games":          len(graph._games),
            "teams":          len(graph._teams),
            "relationships":  len(graph._rels),
        }
        self.json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(
            "composer_store: saved to %s (%d composers, %d tracks, %d rels)",
            self.json_path, len(graph._composers), len(graph._tracks), len(graph._rels),
        )

        if self.use_sqlite:
            try:
                self.rebuild_db(graph)
            except Exception as exc:
                log.warning("composer_store: SQLite rebuild failed: %s", exc)

    # -----------------------------------------------------------------------
    # Load
    # -----------------------------------------------------------------------

    def load(self, seed_if_empty: bool = True) -> ComposerGraph:
        """
        Load ComposerGraph from JSON.
        Returns a fresh seeded graph if no JSON file found and seed_if_empty=True.
        """
        reset_graph()
        graph = ComposerGraph()

        if self.json_path.exists():
            try:
                data = json.loads(self.json_path.read_text(encoding="utf-8"))
                data.pop("_meta", None)   # strip meta before from_dict
                graph.from_dict(data)
                log.info(
                    "composer_store: loaded from %s (%d composers, %d rels)",
                    self.json_path, len(graph._composers), len(graph._rels),
                )
            except Exception as exc:
                log.error("composer_store: load failed: %s", exc)
        elif seed_if_empty:
            graph.seed_s3k()
            log.info("composer_store: no JSON found; seeded with S3K data")

        return graph

    # -----------------------------------------------------------------------
    # SQLite
    # -----------------------------------------------------------------------

    def rebuild_db(self, graph: ComposerGraph) -> None:
        """Rebuild all SQLite tables from graph."""
        with sqlite3.connect(str(self.db_path)) as con:
            _create_schema(con)
            _populate_composers(con, graph)
            _populate_tracks(con, graph)
            _populate_games(con, graph)
            _populate_teams(con, graph)
            _populate_relationships(con, graph)
            con.commit()
        log.info(
            "composer_store: SQLite rebuilt at %s (%d composers, %d tracks)",
            self.db_path, len(graph._composers), len(graph._tracks),
        )

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        return con

    # -----------------------------------------------------------------------
    # Query API
    # -----------------------------------------------------------------------

    def query_tracks(
        self,
        composer_id: str | None = None,
        game_id:     str | None = None,
        relation:    str = "wrote",
    ) -> list[dict[str, Any]]:
        """
        Return tracks for a composer (via relationships table).

        Parameters
        ----------
        composer_id : str, optional
            Filter by composer slug.
        game_id : str, optional
            Filter by game.
        relation : str
            Relationship type to follow (default: "wrote").
        """
        if not self.db_path.exists():
            return []

        with self._con() as con:
            if composer_id:
                rows = con.execute(
                    """
                    SELECT t.*, r.confidence, r.source_name
                    FROM tracks t
                    JOIN relationships r ON r.target = 'track:' || t.track_id
                    WHERE r.source = 'composer:' || ?
                      AND r.relation = ?
                    ORDER BY t.track_number
                    """,
                    (composer_id, relation),
                ).fetchall()
            elif game_id:
                rows = con.execute(
                    "SELECT * FROM tracks WHERE game_id = ? ORDER BY track_number",
                    (game_id,),
                ).fetchall()
            else:
                rows = con.execute("SELECT * FROM tracks ORDER BY game_id, track_number").fetchall()

            return [dict(r) for r in rows]

    def query_composer(
        self,
        composer_id: str | None = None,
        name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Look up a composer by ID or fuzzy name search."""
        if not self.db_path.exists():
            return []

        with self._con() as con:
            if composer_id:
                rows = con.execute(
                    "SELECT * FROM composers WHERE composer_id = ?",
                    (composer_id,),
                ).fetchall()
            elif name:
                pattern = f"%{name.lower()}%"
                rows = con.execute(
                    "SELECT * FROM composers WHERE LOWER(full_name) LIKE ? OR LOWER(aliases) LIKE ?",
                    (pattern, pattern),
                ).fetchall()
            else:
                rows = con.execute("SELECT * FROM composers").fetchall()

            return [dict(r) for r in rows]

    def query_relationships(
        self,
        source_prefix: str | None = None,
        relation:      str | None = None,
        target_prefix: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Query the relationships table with optional filters."""
        if not self.db_path.exists():
            return []

        clauses = ["confidence >= ?"]
        params: list[Any] = [min_confidence]

        if source_prefix:
            clauses.append("source LIKE ?")
            params.append(f"{source_prefix}%")
        if relation:
            clauses.append("relation = ?")
            params.append(relation)
        if target_prefix:
            clauses.append("target LIKE ?")
            params.append(f"{target_prefix}%")

        sql = f"SELECT * FROM relationships WHERE {' AND '.join(clauses)} ORDER BY confidence DESC"

        with self._con() as con:
            rows = con.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def search_any(self, text: str) -> list[dict[str, Any]]:
        """Full-text search across composers, tracks, and games."""
        if not self.db_path.exists():
            return []

        pattern = f"%{text.lower()}%"
        results: list[dict] = []

        with self._con() as con:
            for row in con.execute(
                """
                SELECT 'composer' as entity_type, composer_id as id, full_name as label
                FROM composers WHERE LOWER(full_name) LIKE ? OR LOWER(aliases) LIKE ?
                """,
                (pattern, pattern),
            ).fetchall():
                results.append(dict(row))

            for row in con.execute(
                """
                SELECT 'track' as entity_type, track_id as id, title as label
                FROM tracks WHERE LOWER(title) LIKE ?
                """,
                (pattern,),
            ).fetchall():
                results.append(dict(row))

            for row in con.execute(
                """
                SELECT 'game' as entity_type, game_id as id, title as label
                FROM games WHERE LOWER(title) LIKE ?
                """,
                (pattern,),
            ).fetchall():
                results.append(dict(row))

        return results

    # -----------------------------------------------------------------------
    # Convenience
    # -----------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Return store stats (JSON file metadata + SQLite row counts if available)."""
        s: dict[str, Any] = {
            "json_exists":  self.json_path.exists(),
            "json_path":    str(self.json_path),
            "db_exists":    self.db_path.exists(),
            "db_path":      str(self.db_path),
        }
        if self.json_path.exists():
            try:
                meta = json.loads(self.json_path.read_text())
                s["json_meta"] = meta.get("_meta", {})
            except Exception:
                pass
        if self.db_path.exists():
            with self._con() as con:
                for table in ("composers", "tracks", "games", "teams", "relationships"):
                    try:
                        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                        s[f"db_{table}"] = count
                    except Exception:
                        s[f"db_{table}"] = "?"
        return s


# ---------------------------------------------------------------------------
# SQLite schema helpers
# ---------------------------------------------------------------------------

def _create_schema(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE TABLE IF NOT EXISTS composers (
            composer_id     TEXT PRIMARY KEY,
            full_name       TEXT NOT NULL,
            aliases         TEXT,
            nationality     TEXT,
            birth_year      INTEGER,
            years_active    TEXT,
            studios         TEXT,
            sound_teams     TEXT,
            bio_summary     TEXT,
            bio_url         TEXT,
            style_traits    TEXT,
            external_ids    TEXT,
            updated_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS tracks (
            track_id        TEXT PRIMARY KEY,
            title           TEXT,
            game_id         TEXT,
            platform        TEXT,
            duration_sec    REAL,
            chip            TEXT,
            track_number    INTEGER,
            composers       TEXT,
            attribution_confidence REAL DEFAULT 1.0,
            external_ids    TEXT
        );

        CREATE TABLE IF NOT EXISTS games (
            game_id         TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            platform        TEXT,
            year            INTEGER,
            developer       TEXT,
            publisher       TEXT,
            composers       TEXT,
            sound_team      TEXT,
            external_ids    TEXT
        );

        CREATE TABLE IF NOT EXISTS teams (
            team_id         TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            company         TEXT,
            members         TEXT,
            active_years    TEXT
        );

        CREATE TABLE IF NOT EXISTS relationships (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source          TEXT NOT NULL,
            relation        TEXT NOT NULL,
            target          TEXT NOT NULL,
            confidence      REAL DEFAULT 1.0,
            source_name     TEXT,
            notes           TEXT,
            UNIQUE(source, relation, target)
        );

        CREATE INDEX IF NOT EXISTS idx_rel_source   ON relationships(source);
        CREATE INDEX IF NOT EXISTS idx_rel_target   ON relationships(target);
        CREATE INDEX IF NOT EXISTS idx_rel_relation ON relationships(relation);
        CREATE INDEX IF NOT EXISTS idx_tracks_game  ON tracks(game_id);
        CREATE INDEX IF NOT EXISTS idx_comp_name    ON composers(full_name);
    """)


def _j(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _populate_composers(con: sqlite3.Connection, graph: ComposerGraph) -> None:
    con.execute("DELETE FROM composers")
    ts = _now_iso()
    rows = [
        (
            c.composer_id, c.full_name, _j(c.aliases), c.nationality,
            c.birth_year, c.years_active, _j(c.studios), _j(c.sound_teams),
            c.bio_summary, c.bio_url, _j(c.style_traits), _j(c.external_ids), ts,
        )
        for c in graph._composers.values()
    ]
    con.executemany(
        """
        INSERT OR REPLACE INTO composers
        (composer_id, full_name, aliases, nationality, birth_year, years_active,
         studios, sound_teams, bio_summary, bio_url, style_traits, external_ids, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )


def _populate_tracks(con: sqlite3.Connection, graph: ComposerGraph) -> None:
    con.execute("DELETE FROM tracks")
    rows = [
        (
            t.track_id, t.title, t.game_id, t.platform, t.duration_sec,
            t.chip, t.track_number, _j(t.composers), t.attribution_confidence,
            _j(t.external_ids),
        )
        for t in graph._tracks.values()
    ]
    con.executemany(
        """
        INSERT OR REPLACE INTO tracks
        (track_id, title, game_id, platform, duration_sec, chip, track_number,
         composers, attribution_confidence, external_ids)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )


def _populate_games(con: sqlite3.Connection, graph: ComposerGraph) -> None:
    con.execute("DELETE FROM games")
    rows = [
        (
            g.game_id, g.title, g.platform, g.year, g.developer, g.publisher,
            _j(g.composers), g.sound_team, _j(g.external_ids),
        )
        for g in graph._games.values()
    ]
    con.executemany(
        """
        INSERT OR REPLACE INTO games
        (game_id, title, platform, year, developer, publisher, composers, sound_team, external_ids)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )


def _populate_teams(con: sqlite3.Connection, graph: ComposerGraph) -> None:
    con.execute("DELETE FROM teams")
    rows = [
        (tm.team_id, tm.name, tm.company, _j(tm.members), tm.active_years)
        for tm in graph._teams.values()
    ]
    con.executemany(
        "INSERT OR REPLACE INTO teams (team_id, name, company, members, active_years) VALUES (?,?,?,?,?)",
        rows,
    )


def _populate_relationships(con: sqlite3.Connection, graph: ComposerGraph) -> None:
    con.execute("DELETE FROM relationships")
    rows = [
        (r.source, r.relation, r.target, r.confidence, r.source_name, r.notes)
        for r in graph._rels
    ]
    con.executemany(
        """
        INSERT OR IGNORE INTO relationships
        (source, relation, target, confidence, source_name, notes)
        VALUES (?,?,?,?,?,?)
        """,
        rows,
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
