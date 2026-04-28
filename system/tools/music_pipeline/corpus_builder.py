"""
corpus_builder.py — Active corpus generation from fused trace signals.

Produces operator-facing derived corpora based on actual listening
signals, library state, validation results, and project requirements.

Corpora are derived from real signal combinations — not arbitrary
folder or tag slicing. A corpus represents a meaningful research
or maintenance set that the operator currently cares about.

Generated corpora:
  active_listening     albums/tracks with strong Last.fm signal
  high_signal_missing  high-play tracks absent from library
  priority_cleanup     high-signal tracks with current metadata gaps
  vgm_corpus           all VGM/SPC-format records with status
  franchise_corpus     per-franchise breakdowns
  s3k_corpus           Sonic 3 & Knuckles specific project view
  general_cleanup      all records needing metadata attention
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .entity_resolver import (
    EntityGroup, MATCH_NONE, MATCH_CONFLICT, MATCH_AMBIG,
)
from .validator import ValidationResult, PASS, REVIEW
from .refresh_planner import RefreshCandidate, ACTION_ADD_NEW, ACTION_REVIEW

# Thresholds
HIGH_SIGNAL_PLAYS = 5
PRIORITY_PLAYS    = 20
S3K_FRANCHISE_KEY = "sonic"   # normalized key fragment


# ---------------------------------------------------------------------------
# CorpusEntry
# ---------------------------------------------------------------------------

@dataclass
class CorpusEntry:
    entity_id:         str
    title:             str
    artist:            str
    album:             str
    corpus_tags:       list[str]   # which corpora this belongs to
    scrobble_count:    int
    match_class:       str
    has_library_source: bool
    has_codex_record:  bool
    validation_status: str
    refresh_action:    str
    platform:          str = ""
    franchise:         str = ""
    sound_chip:        str = ""
    sound_team:        str = ""
    loved:             bool | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Corpus builders
# ---------------------------------------------------------------------------

def build_corpora(
    groups: list[EntityGroup],
    validation_results: list[ValidationResult],
    candidates: list[RefreshCandidate],
) -> dict[str, list[CorpusEntry]]:
    """
    Build all active corpora from fused trace data.
    Returns {corpus_name: [CorpusEntry]}.
    """
    val_map: dict[str, ValidationResult] = {r.entity_id: r for r in validation_results}
    plan_map: dict[str, RefreshCandidate] = {c.entity_id: c for c in candidates}

    corpora: dict[str, list[CorpusEntry]] = defaultdict(list)

    # Keyed sets to avoid duplicate entity_ids per corpus
    added: dict[str, set[str]] = defaultdict(set)

    for group in groups:
        p = group.primary
        val = val_map.get(group.entity_id)
        cand = plan_map.get(group.entity_id)

        val_status     = val.status if val else REVIEW
        refresh_action = cand.action if cand else ACTION_REVIEW
        has_library    = any(s in group.sources_matched
                             for s in ("foobar_runtime", "library"))
        has_codex      = "codex" in group.sources_matched

        corpus_tags: list[str] = []
        plays = group.scrobble_count or 0

        entry = CorpusEntry(
            entity_id          = group.entity_id,
            title              = p.title_raw,
            artist             = p.artist_raw,
            album              = p.album_raw,
            corpus_tags        = corpus_tags,
            scrobble_count     = plays,
            match_class        = group.match_class,
            has_library_source = has_library,
            has_codex_record   = has_codex,
            validation_status  = val_status,
            refresh_action     = refresh_action,
            platform           = p.platform or "",
            franchise          = p.franchise or "",
            sound_chip         = p.sound_chip or "",
            sound_team         = p.sound_team or "",
            loved              = p.loved,
        )

        # ── active_listening ──────────────────────────────────────────────
        if plays >= HIGH_SIGNAL_PLAYS:
            corpus_tags.append("active_listening")
            _add(corpora, added, "active_listening", entry)

        # ── high_signal_missing ───────────────────────────────────────────
        if plays >= HIGH_SIGNAL_PLAYS and not has_library:
            corpus_tags.append("high_signal_missing")
            _add(corpora, added, "high_signal_missing", entry)

        # ── priority_cleanup ─────────────────────────────────────────────
        if plays >= PRIORITY_PLAYS and has_library:
            # Check for metadata gaps
            has_custom_gap = (
                not p.sound_team and not p.platform and not p.franchise
                and (p.genre or "").lower() in ("", "vgm", "game")
            )
            if has_custom_gap or val_status == REVIEW:
                corpus_tags.append("priority_cleanup")
                _add(corpora, added, "priority_cleanup", entry)

        # ── vgm_corpus ────────────────────────────────────────────────────
        is_vgm = (
            bool(p.platform) or bool(p.sound_chip)
            or (p.genre or "").lower() in ("vgm", "game music", "chiptune", "game")
        )
        if is_vgm:
            corpus_tags.append("vgm_corpus")
            _add(corpora, added, "vgm_corpus", entry)

        # ── s3k_corpus ────────────────────────────────────────────────────
        franchise_key = (p.franchise or "").lower()
        album_key = group.primary.album_key
        is_s3k = (
            S3K_FRANCHISE_KEY in franchise_key
            or "sonic" in album_key
            or "s3k" in album_key.replace(" ", "")
            or "sonic 3" in album_key
        )
        if is_s3k:
            corpus_tags.append("s3k_corpus")
            _add(corpora, added, "s3k_corpus", entry)

        # ── franchise_corpus ──────────────────────────────────────────────
        if p.franchise:
            fname = _franchise_safe(p.franchise)
            corpus_tags.append(f"franchise:{fname}")
            _add(corpora, added, f"franchise:{fname}", entry)

        # ── general_cleanup ───────────────────────────────────────────────
        if val_status in (REVIEW,) or refresh_action == ACTION_REVIEW:
            corpus_tags.append("general_cleanup")
            _add(corpora, added, "general_cleanup", entry)

        # ── priority_ingest ───────────────────────────────────────────────
        if not has_codex and has_library and val_status == PASS:
            corpus_tags.append("priority_ingest")
            _add(corpora, added, "priority_ingest", entry)

    # Sort each corpus by play count descending
    for name in corpora:
        corpora[name].sort(key=lambda e: -e.scrobble_count)

    print("[corpus_builder] Corpora generated:")
    for name, entries in sorted(corpora.items()):
        print(f"  {name:35s}: {len(entries):,} entries")

    return dict(corpora)


def _add(
    corpora: dict[str, list[CorpusEntry]],
    added: dict[str, set[str]],
    name: str,
    entry: CorpusEntry,
) -> None:
    if entry.entity_id not in added[name]:
        corpora[name].append(entry)
        added[name].add(entry.entity_id)


def _franchise_safe(s: str) -> str:
    """Remove characters unsafe for dict keys/filenames."""
    import re
    return re.sub(r"[^\w\-]", "_", s.lower().strip())[:32]


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def corpus_to_dict(
    name: str,
    entries: list[CorpusEntry],
    snapshot_id: str,
) -> dict:
    return {
        "corpus_name":   name,
        "snapshot_id":   snapshot_id,
        "count":         len(entries),
        "entries":       [e.to_dict() for e in entries],
    }


def build_corpus_index(
    corpora: dict[str, list[CorpusEntry]],
) -> dict:
    """Summary manifest listing all generated corpora."""
    return {
        "total_corpora": len(corpora),
        "corpora": {
            name: {
                "count": len(entries),
                "top_played_artist": entries[0].artist if entries else None,
            }
            for name, entries in corpora.items()
        },
    }
