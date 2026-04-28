"""
Helix Music Lab — Track Database
==================================
SQLite interface for the 122k-track Helix music archive.

All writes include provenance_version, tier, extraction_ts, and confidence.
Feature vector schema version (config.FEATURE_VECTOR_VERSION) is stored with
every vector row; mismatched vectors are detected and can be recomputed.

Usage:
    from model.domains.music.atlas_integration.track_db import TrackDB
    db = TrackDB()
    db.insert_track({"file_path": "...", "title": "...", ...})
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from domains.music.tools.pipeline.config import DB_PATH, FEATURE_VECTOR_VERSION, FEATURE_VECTOR_DIM

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _track_id(file_path: str) -> str:
    return hashlib.sha1(file_path.encode()).hexdigest()


class TrackDB:
    """
    SQLite-backed store for the Helix music archive.

    Thread-safety: each call opens a short-lived connection via contextmanager.
    For bulk inserts, use the batch_* methods which hold a single connection.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        sql = SCHEMA_PATH.read_text()
        with self._conn() as conn:
            conn.executescript(sql)
            # Phase 15: Staged Actions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS staged_actions (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    metadata_json TEXT, -- JSON payload of the action
                    context_json TEXT,  -- Context (NP, Browse, etc.)
                    rationale TEXT,
                    confidence REAL,
                    staged_ts TEXT,
                    applied_ts TEXT     -- NULL if not yet applied
                )
            """)

    # ------------------------------------------------------------------
    # Track CRUD
    # ------------------------------------------------------------------

    def insert_track(self, rec: dict[str, Any]) -> str:
        """Insert or update a track record. Returns track_id (sha1 hex)."""
        path = rec.get("file_path", "")
        tid  = _track_id(path)
        ts   = _now()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO tracks (
                    id, helix_id, file_path, file_name, title, artist, album,
                    album_artist, date, genre, featuring, sound_team,
                    franchise, track_number, disc_number, platform,
                    sound_chip, comment, format, duration_sec, file_size,
                    play_count, rating, loved, ingested_ts
                ) VALUES (
                    :id, :helix_id, :file_path, :file_name, :title, :artist, :album,
                    :album_artist, :date, :genre, :featuring, :sound_team,
                    :franchise, :track_number, :disc_number, :platform,
                    :sound_chip, :comment, :format, :duration_sec, :file_size,
                    :play_count, :rating, :loved, :ingested_ts
                ) ON CONFLICT(file_path) DO UPDATE SET
                    helix_id     = COALESCE(excluded.helix_id, helix_id),
                    title        = excluded.title,
                    artist       = excluded.artist,
                    album        = excluded.album,
                    platform     = excluded.platform,
                    sound_chip   = excluded.sound_chip,
                    loved        = excluded.loved,
                    rating       = excluded.rating,
                    ingested_ts  = excluded.ingested_ts
            """, {
                "id":           tid,
                "helix_id":     rec.get("id") or rec.get("helix_id"),
                "file_path":    path,
                "file_name":    rec.get("file_name") or Path(path).name,
                "title":        rec.get("title"),
                "artist":       rec.get("artist"),
                "album":        rec.get("album"),
                "album_artist": rec.get("album_artist"),
                "date":         rec.get("date"),
                "genre":        rec.get("genre"),
                "featuring":    rec.get("featuring"),
                "sound_team":   rec.get("sound_team"),
                "franchise":    rec.get("franchise"),
                "track_number": rec.get("track_number"),
                "disc_number":  rec.get("disc_number"),
                "platform":     rec.get("platform"),
                "sound_chip":   rec.get("sound_chip"),
                "comment":      rec.get("comment"),
                "format":       rec.get("format"),
                "duration_sec": rec.get("duration", 0),
                "file_size":    rec.get("file_size", 0),
                "play_count":   rec.get("play_count", 0),
                "rating":       rec.get("rating", 0),
                "loved":        int(bool(rec.get("loved", False))),
                "ingested_ts":  ts,
            })
        return tid

    def get_track(self, track_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM tracks WHERE id = ?", (track_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_track_by_helix_id(self, helix_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM tracks WHERE helix_id = ?", (helix_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_track_by_path(self, file_path: str) -> dict | None:
        tid = _track_id(file_path)
        return self.get_track(tid)

    def track_count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]

    def get_tracks_by_tier(self, max_tier: int) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tracks WHERE max_tier >= ?", (max_tier,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_tracks_with_features(self, max_tier: int = 1) -> list[dict]:
        """Fetch tracks joined with all available feature tables."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT 
                    t.*, 
                    c.keyon_density, c.pitch_center, c.pitch_range as chip_pitch_range,
                    th.key_estimate, th.mode, th.tempo_bpm as theory_bpm, thr.tempo_bpm as audio_bpm
                FROM tracks t
                LEFT JOIN chip_features c ON t.id = c.track_id
                LEFT JOIN theory_features th ON t.id = th.track_id
                LEFT JOIN audio_features thr ON t.id = thr.track_id
                WHERE t.max_tier >= ?
            """, (max_tier,)).fetchall()
        
        results = []
        for r in rows:
            d = dict(r)
            # Reconstruct nested feature dicts for pipeline compatibility
            d["chip_features"] = {
                "keyon_density": d.get("keyon_density"),
                "pitch_center":  d.get("pitch_center"),
                "pitch_range":   d.get("chip_pitch_range")
            }
            d["theory_features"] = {
                "key_estimate": d.get("key_estimate"),
                "mode":         d.get("mode"),
                "tempo_bpm":    d.get("theory_bpm")
            }
            d["audio_features"] = {
                "tempo_bpm":    d.get("audio_bpm")
            }
            results.append(d)
        return results

    def get_unanalyzed(self, tier: int) -> list[dict]:
        """Return tracks that have not yet reached *tier*."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tracks WHERE max_tier < ?", (tier,)
            ).fetchall()
        return [dict(r) for r in rows]

    def set_tier(self, track_id: str, tier: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE tracks SET max_tier = MAX(max_tier, ?) WHERE id = ?",
                (tier, track_id)
            )

    # ------------------------------------------------------------------
    # Feature upserts
    # ------------------------------------------------------------------

    def upsert_chip_features(self, track_id: str, feat: dict,
                              tier: int = 1, confidence: float = 0.6,
                              provenance: str = "chip_features:1.0") -> None:
        ts = _now()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO chip_features (
                    track_id, keyon_density, rhythmic_entropy, pitch_center,
                    pitch_range, pitch_entropy, psg_to_fm_ratio, ams_fms_usage,
                    silence_ratio, tl_mean_op1, tl_mean_op2,
                    algorithm_dist, channel_activity,
                    spc_active_voices, spc_echo_enabled, spc_sample_count,
                    nsf_expansion_chips, sid_chip_model, sid_waveform_dist,
                    provenance_version, tier, confidence, extraction_ts
                ) VALUES (
                    :track_id, :keyon_density, :rhythmic_entropy, :pitch_center,
                    :pitch_range, :pitch_entropy, :psg_to_fm_ratio, :ams_fms_usage,
                    :silence_ratio, :tl_mean_op1, :tl_mean_op2,
                    :algorithm_dist, :channel_activity,
                    :spc_active_voices, :spc_echo_enabled, :spc_sample_count,
                    :nsf_expansion_chips, :sid_chip_model, :sid_waveform_dist,
                    :prov, :tier, :conf, :ts
                ) ON CONFLICT(track_id) DO UPDATE SET
                    keyon_density     = excluded.keyon_density,
                    rhythmic_entropy  = excluded.rhythmic_entropy,
                    tier              = excluded.tier,
                    confidence        = excluded.confidence,
                    extraction_ts     = excluded.extraction_ts
            """, {
                "track_id":           track_id,
                "keyon_density":      feat.get("keyon_density"),
                "rhythmic_entropy":   feat.get("rhythmic_entropy"),
                "pitch_center":       feat.get("pitch_center"),
                "pitch_range":        feat.get("pitch_range"),
                "pitch_entropy":      feat.get("pitch_entropy"),
                "psg_to_fm_ratio":    feat.get("psg_to_fm_ratio"),
                "ams_fms_usage":      feat.get("ams_fms_usage"),
                "silence_ratio":      feat.get("silence_ratio"),
                "tl_mean_op1":        feat.get("tl_mean_op1"),
                "tl_mean_op2":        feat.get("tl_mean_op2"),
                "algorithm_dist":     json.dumps(feat.get("algorithm_dist", {})),
                "channel_activity":   json.dumps(feat.get("channel_activity", {})),
                "spc_active_voices":  feat.get("spc_active_voices"),
                "spc_echo_enabled":   feat.get("spc_echo_enabled"),
                "spc_sample_count":   feat.get("spc_sample_count"),
                "nsf_expansion_chips": json.dumps(feat.get("nsf_expansion_chips", [])),
                "sid_chip_model":     feat.get("sid_chip_model"),
                "sid_waveform_dist":  json.dumps(feat.get("sid_waveform_dist", {})),
                "prov": provenance, "tier": tier, "conf": confidence, "ts": ts,
            })
        self.set_tier(track_id, tier)

    def upsert_symbolic_features(self, track_id: str, feat: dict,
                                  tier: int = 3, confidence: float = 1.0) -> None:
        ts = _now()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO symbolic_features (
                    track_id, note_count, unique_pitches, pitch_range,
                    avg_duration_sec, keyon_events, keyoff_events, orphan_keyons,
                    provenance_version, tier, confidence, extraction_ts
                ) VALUES (
                    :tid, :nc, :up, :pr, :ad, :ko, :kf, :ok,
                    'symbolic_features:1.0', :tier, :conf, :ts
                ) ON CONFLICT(track_id) DO UPDATE SET
                    note_count = excluded.note_count,
                    unique_pitches = excluded.unique_pitches,
                    tier = excluded.tier, extraction_ts = excluded.extraction_ts
            """, {
                "tid": track_id, "tier": tier, "conf": confidence, "ts": ts,
                "nc": feat.get("note_count"), "up": feat.get("unique_pitches"),
                "pr": feat.get("pitch_range"), "ad": feat.get("avg_duration_sec"),
                "ko": feat.get("keyon_events"), "kf": feat.get("keyoff_events"),
                "ok": feat.get("orphan_keyons"),
            })
        self.set_tier(track_id, tier)

    def upsert_theory_features(self, track_id: str, feat: dict,
                                tier: int = 3, confidence: float = 0.6) -> None:
        ts = _now()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO theory_features (
                    track_id, key_estimate, key_confidence, mode,
                    tempo_bpm, beat_regularity, syncopation_index,
                    motif_count, top_motif_freq, harmonic_density,
                    provenance_version, tier, confidence, extraction_ts
                ) VALUES (
                    :tid, :ke, :kc, :mode, :bpm, :br, :si, :mc, :tmf, :hd,
                    'theory_features:1.0', :tier, :conf, :ts
                ) ON CONFLICT(track_id) DO UPDATE SET
                    key_estimate = excluded.key_estimate,
                    tempo_bpm = excluded.tempo_bpm,
                    tier = excluded.tier, extraction_ts = excluded.extraction_ts
            """, {
                "tid": track_id, "tier": tier, "conf": confidence, "ts": ts,
                "ke": feat.get("key_estimate"), "kc": feat.get("key_confidence"),
                "mode": feat.get("mode"), "bpm": feat.get("tempo_bpm"),
                "br": feat.get("beat_regularity"), "si": feat.get("syncopation_index"),
                "mc": feat.get("motif_count"), "tmf": feat.get("top_motif_freq"),
                "hd": feat.get("harmonic_density"),
            })
        self.set_tier(track_id, tier)

    def upsert_audio_features(self, track_id: str, feat: dict,
                               tier: int = 4, confidence: float = 1.0) -> None:
        ts = _now()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO audio_features (
                    track_id, tempo_bpm, beat_strength, spectral_centroid,
                    spectral_rolloff, zcr, rms_mean, mfcc_json, chroma_json,
                    provenance_version, tier, confidence, extraction_ts
                ) VALUES (
                    :tid, :bpm, :bs, :sc, :sr, :zcr, :rms, :mfcc, :chroma,
                    'audio_features:1.0', :tier, :conf, :ts
                ) ON CONFLICT(track_id) DO UPDATE SET
                    tempo_bpm = excluded.tempo_bpm,
                    tier = excluded.tier, extraction_ts = excluded.extraction_ts
            """, {
                "tid": track_id, "tier": tier, "conf": confidence, "ts": ts,
                "bpm": feat.get("tempo_bpm"), "bs": feat.get("beat_strength"),
                "sc": feat.get("spectral_centroid"), "sr": feat.get("spectral_rolloff"),
                "zcr": feat.get("zcr"), "rms": feat.get("rms_mean"),
                "mfcc": json.dumps(feat.get("mfcc", [])),
                "chroma": json.dumps(feat.get("chroma", [])),
            })
        self.set_tier(track_id, tier)

    # ------------------------------------------------------------------
    # Feature vectors
    # ------------------------------------------------------------------

    def save_feature_vector(self, track_id: str, vector: np.ndarray,
                             tier: int = 4, confidence: float = 1.0) -> None:
        assert vector.shape == (FEATURE_VECTOR_DIM,), \
            f"Expected dim {FEATURE_VECTOR_DIM}, got {vector.shape}"
        blob = vector.astype(np.float32).tobytes()
        ts   = _now()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO feature_vectors (
                    track_id, schema_version, vector_dim, vector_blob,
                    tier, confidence, provenance_version, extraction_ts
                ) VALUES (?, ?, ?, ?, ?, ?, 'feature_vector:1.0', ?)
                ON CONFLICT(track_id) DO UPDATE SET
                    schema_version = excluded.schema_version,
                    vector_blob    = excluded.vector_blob,
                    tier           = excluded.tier,
                    extraction_ts  = excluded.extraction_ts
            """, (track_id, FEATURE_VECTOR_VERSION, FEATURE_VECTOR_DIM,
                  blob, tier, confidence, ts))

    def load_all_vectors(self, schema_version: str = FEATURE_VECTOR_VERSION
                         ) -> tuple[list[str], np.ndarray]:
        """Return (track_ids, vectors) for all rows matching schema_version."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT track_id, vector_blob FROM feature_vectors WHERE schema_version = ?",
                (schema_version,)
            ).fetchall()
        if not rows:
            return [], np.empty((0, FEATURE_VECTOR_DIM), dtype=np.float32)
        ids     = [r[0] for r in rows]
        vectors = np.stack([
            np.frombuffer(r[1], dtype=np.float32) for r in rows
        ])
        return ids, vectors

    # ------------------------------------------------------------------
    # Attribution
    # ------------------------------------------------------------------

    def upsert_attribution(self, track_id: str, attributions: list[dict],
                            method: str = "bayesian_gaussian",
                            tier: int = 1, confidence: float = 0.6) -> None:
        ts = _now()
        with self._conn() as conn:
            conn.execute("DELETE FROM attributions WHERE track_id = ?", (track_id,))
            for i, attr in enumerate(attributions):
                conn.execute("""
                    INSERT INTO attributions (
                        track_id, composer_name, probability, rank,
                        method, confidence, tier, provenance_version, extraction_ts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'attribution:1.0', ?)
                """, (track_id, attr["composer"], attr["probability"],
                      i + 1, method, confidence, tier, ts))

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def composer_tracks(self, composer_name: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT t.* FROM tracks t
                JOIN attributions a ON t.id = a.track_id
                WHERE a.composer_name = ? AND a.rank = 1
            """, (composer_name,)).fetchall()
        return [dict(r) for r in rows]

    def loved_tracks(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tracks WHERE loved = 1"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_chip_features(self, track_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM chip_features WHERE track_id = ?", (track_id,)
            ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Semantic Tags (Phase 13)
    # ------------------------------------------------------------------

    def upsert_semantic_tags(self, track_id: str, tags: list[str], 
                              tier: int = 1, confidence: float = 1.0) -> None:
        ts = _now()
        with self._conn() as conn:
            # We don't delete existing tags, we just ensure these are present.
            # To replace all tags, a separate clear() would be needed.
            for tag in tags:
                conn.execute("""
                    INSERT INTO semantic_tags (
                        track_id, tag_name, confidence, tier, extraction_ts
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(track_id, tag_name) DO UPDATE SET
                        confidence    = excluded.confidence,
                        extraction_ts = excluded.extraction_ts
                """, (track_id, tag, confidence, tier, ts))

    def get_semantic_tags(self, track_id: str) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT tag_name FROM semantic_tags WHERE track_id = ?", (track_id,)
            ).fetchall()
        return [r[0] for r in rows]

    def get_tracks_by_tag(self, tag_name: str) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT track_id FROM semantic_tags WHERE tag_name = ?", (tag_name,)
            ).fetchall()
        return [r[0] for r in rows]

    def stats(self) -> dict:
        with self._conn() as conn:
            total     = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
            by_format = dict(conn.execute(
                "SELECT format, COUNT(*) FROM tracks GROUP BY format"
            ).fetchall())
            loved     = conn.execute(
                "SELECT COUNT(*) FROM tracks WHERE loved=1"
            ).fetchone()[0]
            vectorized = conn.execute(
                "SELECT COUNT(*) FROM feature_vectors WHERE schema_version=?",
                (FEATURE_VECTOR_VERSION,)
            ).fetchone()[0]
        return {
            "total_tracks": total,
            "by_format":    by_format,
            "loved_tracks": loved,
            "vectorized":   vectorized,
            "vector_schema": FEATURE_VECTOR_VERSION,
        }

    # ------------------------------------------------------------------
    # Bulk helpers
    # ------------------------------------------------------------------

    def populate_from_records(self, records: list[dict]) -> int:
        """Bulk-insert a list of track record dicts. Returns inserted count."""
        n = 0
        for rec in records:
            try:
                self.insert_track(rec)
                n += 1
            except Exception as e:
                print(f"  DB warn: {e} — {rec.get('file_path', '?')[:60]}")
        return n

