"""
Music Domain DCP Hook — model/domains/music/analysis/dcp.py
======================================================
Translates music structural features into DCP events (schema: dcp_event_v2).

The music DCP interpretation reads the library's structural signals and maps
them onto the five DCP component proxies plus the two v2 fields:
  - collapse_morphology  (CollapseMorphology enum value)
  - constraint_class     ('internal' | 'external' | 'mixed')

CANONICAL COLLAPSE EVENT IN MUSIC: the LOOP-SEAM
  The moment a developing structural trajectory returns to a prior state.
  In VGM this is a literal driver-enforced loop point.
  In composed music it is the phrase/section-level return event.

Morphology heuristic (metadata-level, provisional):
  CIRCULAR           — default for VGM tracks (driver enforces literal loop)
  TRANSFORMATIVE     — high energy + high instrumentalness (structural shift at seam)
  DISSOLUTIVE        — low instrumentalness + low energy (texture thins at seam)
  DEFERRED_SUSPENDED — low danceability + low energy (seam doesn't land cleanly)

Constraint class heuristic:
  VGM / hardware format → 'mixed'  (internal composition + external SMPS/hardware limits)
  Non-VGM instrumental  → 'internal'
  Spotify/commercial    → 'internal' (default; no hardware constraint signal)

Layer relationships:
  model/domains/music/analysis/loop_seam.py          → loop-seam probe (candidacy ranking)
  model/domains/music/analysis/dcp.py    ← THIS FILE → DCP event emission (dcp_event_v2)
  core/invariants/dcp/event.py                 → canonical event schema
  core/invariants/dcp/metrics.py               → metric functions
  system/engine/compute/invariants/dcp/morphology.py            → CollapseMorphology enum + profiles

Limitation notes embedded throughout.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists()
)
sys.path.insert(0, str(ROOT))

from core.invariants.dcp.event import DCPEvent
from core.invariants.dcp.metrics import compute_dcp_score
from core.invariants.dcp.morphology import CollapseMorphology


# ─── Component mapping notes ──────────────────────────────────────────────────
#
# possibility_space_proxy:
#   Breadth of harmonic/structural futures before the collapse.
#   Proxy: energy × (1 − speechiness)
#   High energy + low speechiness → richer structural vocabulary.
#   Limitation: indirect proxy; real harmonic breadth requires audio.
#
# constraint_proxy:
#   Structural constraint acting on the possibility space.
#   Proxy: 1 − liveness  (low liveness = high production constraint)
#   For VGM: additionally boosted by hardware channel/driver constraint.
#   Limitation: liveness ≠ structural constraint. Plausible correlation only.
#
# tension_proxy:
#   Pre-collapse unresolved competition.
#   Proxy: (1 − valence) × energy
#   Low valence + high energy = unresolved emotional/structural tension.
#   Limitation: emotional tension ≠ structural tension. Metadata approximation.
#
# collapse_proxy:
#   Sharpness of the compression event.
#   CANNOT BE ESTIMATED FROM SPOTIFY METADATA.
#   Returns None — qualification_status will reflect INCOMPLETE/UNCONFIRMED.
#   For VGM library tracks: also None (requires audio-level loop-seam detection).
#
# post_collapse_narrowing:
#   Reduction in trajectory diversity after the seam.
#   Proxy: instrumentalness × 0.5 + (1 − valence) × 0.5
#   Limitation: significant approximation. Low confidence.
#
# collapse_morphology (v2):
#   Assigned heuristically from metadata. See _classify_morphology() below.
#   VGM tracks default to CIRCULAR — the driver loop IS the circular return.
#   Provisional; audio-level verification required.
#
# constraint_class (v2):
#   VGM/hardware tracks → 'mixed' (composition + hardware channel limits + SMPS loop)
#   Non-VGM instrumental → 'internal'
#   Default → 'internal'


# ─── VGM format indicators ────────────────────────────────────────────────────
# Track formats that imply hardware/driver external constraint
VGM_FORMATS = frozenset({
    "vgm", "vgz", "gym", "nsf", "nsfe", "spc", "psf", "psf2",
    "ssf", "dsf", "gsf", "usf", "miniusf", "2sf", "mini2sf",
    "xsf", "minixsf", "qsf", "miniqsf", "snsf", "minisnsf",
    "s98", "hes", "kss", "ay", "gbs", "sgc", "vgp",
})

# Known S3K sound chip constraint notes
S3K_CONSTRAINT_NOTE = (
    "S3K: SMPS Z80 driver enforces loop point (external constraint). "
    "YM2612 FM (6ch) + SN76489 PSG (4ch) hardware limits (external). "
    "Composer's harmonic/rhythmic structure (internal). → constraint_class=mixed"
)


def _is_vgm_track(domain_metadata: dict[str, Any]) -> bool:
    """Return True if the track is a VGM/hardware-log format."""
    fmt = str(domain_metadata.get("format", "")).lower().rstrip(".")
    return fmt in VGM_FORMATS


def _classify_morphology(
    energy: float,
    valence: float,
    instrumentalness: float,
    danceability: float,
    is_vgm: bool,
) -> str:
    """
    Heuristic morphology assignment from Spotify metadata features.

    Rules (provisional, uncalibrated — override with audio-level detection):
      VGM track               → CIRCULAR by default (driver loop is a literal return)
        exception: high energy + high instrumentalness → TRANSFORMATIVE
                   (e.g. a VGM track where the loop seam introduces a structural shift)
      Non-VGM:
        high energy + high instrumentalness → TRANSFORMATIVE
        low energy + low instrumentalness   → DISSOLUTIVE
        low danceability + low energy       → DEFERRED_SUSPENDED
        default                             → CIRCULAR

    These rules are intentionally conservative. The dominant case for VGM is
    CIRCULAR — the loop point IS the circular return. Only flag TRANSFORMATIVE
    when the track has strong structural vocabulary AND high energy, suggesting
    the seam lands on a genuinely different structural state.
    """
    if is_vgm:
        # VGM default: CIRCULAR (literal driver loop)
        if energy >= 0.70 and instrumentalness >= 0.75:
            return CollapseMorphology.TRANSFORMATIVE.value
        return CollapseMorphology.CIRCULAR.value
    else:
        if energy >= 0.65 and instrumentalness >= 0.60:
            return CollapseMorphology.TRANSFORMATIVE.value
        if energy < 0.35 and instrumentalness < 0.35:
            return CollapseMorphology.DISSOLUTIVE.value
        if danceability < 0.35 and energy < 0.40:
            return CollapseMorphology.DEFERRED_SUSPENDED.value
        return CollapseMorphology.CIRCULAR.value


def _classify_constraint(
    is_vgm: bool,
    instrumentalness: float,
    liveness: float,
) -> str:
    """
    Heuristic constraint class from track metadata.

      VGM formats: 'mixed' — driver-enforced loop (external) + composition (internal)
      Non-VGM, highly produced (low liveness): 'internal'
      Default: 'internal'
    """
    if is_vgm:
        return "mixed"
    return "internal"


def extract_dcp_event_from_spotify(
    track: dict[str, Any],
    source_artifact: str = "spotify_library",
) -> DCPEvent:
    """
    Emit a music-domain DCP event (dcp_event_v2) from a single Spotify/library
    track record.

    Populates:
      - All five DCP component proxies (collapse_proxy is None — requires audio)
      - collapse_morphology  (heuristic from metadata; provisional)
      - constraint_class     (heuristic from format + metadata)

    Args:
        track: a single record from the Spotify/library JSON
               (fields: Track Name, Artist Name(s), Energy, Valence,
                Instrumentalness, Liveness, Danceability, Acousticness,
                Speechiness, Tempo, format [optional])
        source_artifact: artifact identifier for provenance

    Returns:
        DCPEvent (schema: dcp_event_v2)
          qualification_status → INCOMPLETE (collapse_proxy=None; morphology set)
    """
    def _get(key: str, default: float = 0.0) -> float:
        v = track.get(key)
        try:
            return float(v) if v is not None else default
        except (TypeError, ValueError):
            return default

    energy           = _get("Energy")
    valence          = _get("Valence")
    instrumentalness = _get("Instrumentalness")
    liveness         = _get("Liveness")
    speechiness      = _get("Speechiness")
    acousticness     = _get("Acousticness")
    danceability     = _get("Danceability")
    tempo            = _get("Tempo", 120.0)

    # Detect VGM/hardware format
    domain_meta_for_format = {"format": track.get("format", track.get("Format", ""))}
    is_vgm = _is_vgm_track(domain_meta_for_format)

    # ── Possibility space ────────────────────────────────────────────────────
    possibility_space = float(min(1.0, max(0.0,
        energy * (1.0 - 0.5 * speechiness)
    )))

    # ── Constraint proxy ─────────────────────────────────────────────────────
    # VGM tracks: boost constraint slightly to reflect hardware channel limits
    # on top of production constraint (1 - liveness).
    base_constraint = float(min(1.0, max(0.0, 1.0 - liveness)))
    constraint = float(min(1.0, base_constraint + (0.10 if is_vgm else 0.0)))

    # ── Tension proxy ────────────────────────────────────────────────────────
    tension = float(min(1.0, max(0.0, (1.0 - valence) * energy)))

    # ── Collapse proxy ───────────────────────────────────────────────────────
    # CANNOT BE MEASURED FROM METADATA.
    # Returning None is the honest choice. Audio-level loop-seam detection required.
    collapse: Optional[float] = None

    # ── Post-collapse narrowing ──────────────────────────────────────────────
    post_narrowing = float(min(1.0, max(0.0,
        instrumentalness * 0.5 + (1.0 - valence) * 0.5
    )))

    # ── v2 fields ────────────────────────────────────────────────────────────
    morphology = _classify_morphology(
        energy=energy,
        valence=valence,
        instrumentalness=instrumentalness,
        danceability=danceability,
        is_vgm=is_vgm,
    )

    constraint_class = _classify_constraint(
        is_vgm=is_vgm,
        instrumentalness=instrumentalness,
        liveness=liveness,
    )

    # ── Composite score ───────────────────────────────────────────────────────
    dcp_score = compute_dcp_score(
        possibility_space=possibility_space,
        constraint=constraint,
        tension=tension,
        collapse=collapse,
        post_narrowing=post_narrowing,
    )

    # Confidence: capped at 0.45 (collapse is absent); morphology now populated
    # so cap is slightly higher than before (+0.05 for partial v2 completeness)
    confidence = float(min(0.50, dcp_score * 0.55))

    track_name  = track.get("Track Name", "unknown")
    artist_name = track.get("Artist Name(s)", "unknown")
    track_uri   = track.get("Track URI", "")

    event_id = (
        f"music.dcp.spotify.{track_uri.split(':')[-1]}"
        if track_uri else
        f"music.dcp.{track_name[:20].replace(' ', '_').lower()}"
    )

    # Build constraint note
    constraint_note = (
        S3K_CONSTRAINT_NOTE
        if is_vgm and "sonic" in (track.get("Album", "") or "").lower()
        else (
            f"VGM format ({domain_meta_for_format['format']}): "
            "driver loop (external) + composition (internal) → mixed"
            if is_vgm else
            "Non-VGM: production constraint only → internal"
        )
    )

    return DCPEvent(
        source_domain     = "music",
        source_artifact   = source_artifact,
        event_id          = event_id,
        possibility_space_proxy  = possibility_space,
        constraint_proxy         = constraint,
        tension_proxy            = tension,
        collapse_proxy           = collapse,          # None — requires audio
        post_collapse_narrowing  = post_narrowing,
        collapse_morphology      = morphology,        # v2: heuristic, provisional
        constraint_class         = constraint_class,  # v2: 'mixed' | 'internal'
        confidence               = confidence,
        calibration_status       = "provisional",
        notes=(
            f"Track: '{track_name}' by {artist_name}. "
            f"Metadata-level proxy only. collapse_proxy=None "
            f"(requires audio-level loop-seam detection). "
            f"collapse_morphology='{morphology}' (heuristic — not audio-verified). "
            f"{constraint_note}. "
            f"See model/domains/music/analysis/loop_seam.py for candidacy scoring."
        ),
        domain_metadata={
            "track_name":        track_name,
            "artist":            artist_name,
            "track_uri":         track_uri,
            "format":            domain_meta_for_format["format"],
            "is_vgm":            is_vgm,
            "energy":            energy,
            "valence":           valence,
            "instrumentalness":  instrumentalness,
            "liveness":          liveness,
            "danceability":      danceability,
            "acousticness":      acousticness,
            "speechiness":       speechiness,
            "tempo":             tempo,
            "dcp_composite":     round(dcp_score, 4),
        },
    )


def extract_dcp_event_from_library_track(
    track_json: dict[str, Any],
    source_artifact: str = "helix_library",
) -> DCPEvent:
    """
    Emit a DCP event from a Helix library track JSON
    (codex/library/music/album/<album>/<track>.json).

    Library tracks have richer format metadata (format, format_category)
    compared to Spotify records, enabling more precise constraint classification.

    Args:
        track_json: parsed contents of a library track JSON file
        source_artifact: provenance identifier

    Returns:
        DCPEvent (schema: dcp_event_v2)
    """
    meta = track_json.get("metadata", {})
    analysis = track_json.get("analysis", {})

    # Remap library fields to Spotify-compatible keys for reuse
    spotify_compat: dict[str, Any] = {
        "Track Name":      meta.get("title", meta.get("name", track_json.get("name", "unknown"))),
        "Artist Name(s)":  meta.get("artist", "unknown"),
        "Album":           meta.get("album", ""),
        "format":          meta.get("format", ""),
        # Audio features would come from a prior analysis run if available
        "Energy":          analysis.get("energy", 0.70),        # VGM default: assume energetic
        "Valence":         analysis.get("valence", 0.50),
        "Instrumentalness": analysis.get("instrumentalness",
                                meta.get("format_category") == "hardware_log" and 1.0 or 0.85),
        "Liveness":        analysis.get("liveness", 0.05),      # VGM: always produced
        "Danceability":    analysis.get("danceability", 0.60),
        "Speechiness":     analysis.get("speechiness", 0.03),
        "Acousticness":    analysis.get("acousticness", 0.05),
        "Tempo":           analysis.get("tempo", 140.0),
        "Track URI":       track_json.get("id", ""),
    }

    event = extract_dcp_event_from_spotify(spotify_compat, source_artifact)

    # Upgrade event_id to use library track ID format
    track_id = track_json.get("id", "")
    if track_id:
        object.__setattr__ if hasattr(event, "__slots__") else None
        # DCPEvent is a dataclass — reassign event_id via standard attribute
        event = DCPEvent(
            **{
                **event.to_dict(),
                "event_id": f"music.dcp.library.{track_id}",
                # Remove computed field from to_dict
            }
        )

    return event

