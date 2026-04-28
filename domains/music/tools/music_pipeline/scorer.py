"""
domains/music/model/attribution/scorer.py
=====================================
Attribution scorer: builds composer fingerprints from artifact library,
scores S3K tracks, and produces a ranked attribution table.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from model.domains.music.attribution.fingerprint import (
    ComposerFingerprint,
    _extract_vector,
    FEATURE_NAMES,
)

_SKIP_ARTISTS = {"", "unknown", "various", "sega sound team", "sega", "sega cs r&d"}
_STRIP_HASH   = re.compile(r'_[0-9a-f]{5,}$')


class AttributionScorer:
    """
    Loads composer fingerprints from artifacts and scores track analyses.
    """

    def __init__(self, artifacts_dir: Path | None = None):
        self._root      = Path(__file__).resolve().parent.parent.parent.parent
        self._artifacts = artifacts_dir or self._root / "artifacts" / "analysis"
        self.fingerprints:  dict[str, ComposerFingerprint] = {}
        self._lib_index:    dict[str, str] = {}   # entity_id → artist
        self._source_index: dict[str, str] = {}   # source_path_lower → artist

    # ------------------------------------------------------------------
    # Library index — resolves artist from entity_id or source path
    # ------------------------------------------------------------------

    def _build_lib_index(self) -> None:
        """Scan the music library and build entity_id → artist and source → artist maps."""
        lib = self._root / "codex" / "library" / "music" / "album"
        s3k = "sonic_3_knuckles"
        for jf in lib.rglob("*.json"):
            if jf.name == "album.json" or s3k in str(jf):
                continue
            try:
                obj    = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
                meta   = obj.get("metadata", {})
                artist = meta.get("artist", "").strip()
                if not artist or artist.lower() in _SKIP_ARTISTS:
                    continue
                eid = obj.get("id", "")
                src = meta.get("source", "")
                if eid:
                    self._lib_index[eid] = artist
                    # Also index the last dot-segment (short slug used in artifact entity_id)
                    short = eid.split(".")[-1]
                    if short:
                        self._lib_index[short] = artist
                if src:
                    self._source_index[src.lower()] = artist
            except Exception:
                pass

    def _resolve_artist(self, artifact: dict) -> str:
        """Best-effort artist resolution for a loaded artifact dict."""
        analysis = artifact.get("analysis", {})

        # 1. Direct embed (new artifacts written after _run_single was fixed)
        artist = analysis.get("library_artist", "").strip()
        if artist and artist.lower() not in _SKIP_ARTISTS:
            return artist

        # 2. Library index by entity_id
        eid = artifact.get("entity_id", "")
        artist = self._lib_index.get(eid, "")
        if not artist:
            short = eid.split(".")[-1]
            clean = _STRIP_HASH.sub("", short)
            artist = self._lib_index.get(short, "") or self._lib_index.get(clean, "")
        if artist and artist.lower() not in _SKIP_ARTISTS:
            return artist

        # 3. Library index by source path
        src = artifact.get("source", "").lower()
        artist = self._source_index.get(src, "")
        return artist if artist.lower() not in _SKIP_ARTISTS else ""

    # ------------------------------------------------------------------
    # Fingerprint loading
    # ------------------------------------------------------------------

    def load_composer_artifacts(self, composers: list[str] | None = None) -> dict[str, int]:
        """
        Scan artifacts/analysis/, resolve each to a composer, and build fingerprints.
        Returns {composer_name: track_count}.
        """
        self._build_lib_index()
        s3k_slug = "sonic_3_knuckles"
        composer_analyses: dict[str, list[dict]] = {}

        for af in self._artifacts.glob("*.json"):
            try:
                artifact = json.loads(af.read_text(encoding="utf-8"))
                eid = artifact.get("entity_id", "")

                # Skip S3K tracks
                if s3k_slug in eid or s3k_slug in af.stem:
                    continue

                composer = self._resolve_artist(artifact)
                if not composer:
                    continue
                if composers and not any(c.lower() in composer.lower() for c in composers):
                    continue

                composer_analyses.setdefault(composer, []).append(artifact)
            except Exception:
                pass

        counts = {}
        for composer, analyses in composer_analyses.items():
            fp = ComposerFingerprint.from_analyses(composer, analyses)
            if fp.track_count > 0:
                self.fingerprints[composer] = fp
                counts[composer] = fp.track_count

        return counts

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_track(self, artifact: dict) -> list[dict]:
        """
        Score a single track artifact against all loaded fingerprints.
        Returns [{composer, similarity, weighted_score, confidence_weight}] sorted descending.
        """
        analysis = artifact.get("analysis", artifact)
        vec = _extract_vector({"analysis": analysis})
        if vec is None:
            return []

        results = []
        for composer, fp in self.fingerprints.items():
            sim = fp.similarity(vec)
            wt  = fp.confidence_weight()
            results.append({
                "composer":          composer,
                "similarity":        round(sim, 4),
                "confidence_weight": round(wt, 4),
                "weighted_score":    round(sim * wt, 4),
                "track_count":       fp.track_count,
                "dcp_qualified":     fp.dcp_qualified,
            })

        results.sort(key=lambda x: x["weighted_score"], reverse=True)
        return results

    def score_all_s3k(self) -> dict[str, Any]:
        """
        Loads all (deduplicated) S3K track artifacts and scores each.
        Returns attribution dict keyed by track stem.
        """
        s3k_dir = self._root / "codex" / "library" / "music" / "album" / "sonic_3_knuckles"
        results  = {}
        seen_src = set()

        for jf in sorted(s3k_dir.glob("*.json")):
            if jf.name == "album.json":
                continue
            try:
                track_obj = json.loads(jf.read_text(encoding="utf-8"))
                src = track_obj.get("metadata", {}).get("source", "")
                if src in seen_src:
                    continue
                seen_src.add(src)

                eid   = track_obj.get("id", "")
                short = eid.split(".")[-1] if "." in eid else jf.stem
                clean = _STRIP_HASH.sub("", short)

                # Try multiple artifact filename patterns
                candidates = [
                    self._artifacts / f"track_{short}.json",
                    self._artifacts / f"track_{clean}.json",
                    self._artifacts / f"{eid.replace(':','_').replace('.','_')}.json",
                    # also old run-format
                    self._artifacts / f"music_track_sonic_3_knuckles_{short}.json",
                ]
                artifact_f = next((p for p in candidates if p.exists()), None)
                if artifact_f is None:
                    continue

                artifact = json.loads(artifact_f.read_text(encoding="utf-8"))
                ranking  = self.score_track(artifact)
                if not ranking:
                    continue

                name = track_obj.get("name", "") or track_obj.get("title", "") or jf.stem
                results[jf.stem] = {
                    "track_name":   name,
                    "track_id":     eid,
                    "ranking":      ranking[:5],
                    "top_composer": ranking[0]["composer"],
                    "top_score":    ranking[0]["weighted_score"],
                }
            except Exception:
                pass

        return results

    def summary(self) -> dict:
        return {
            c: {"track_count": fp.track_count, "dcp_qualified": fp.dcp_qualified,
                "confidence_weight": fp.confidence_weight()}
            for c, fp in sorted(self.fingerprints.items())
        }

