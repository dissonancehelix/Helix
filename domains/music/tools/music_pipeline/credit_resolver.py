"""
credit_resolver.py — Parse ARTIST + FEATURING tag strings into ParticipantSets.

Handles the messy reality of VGM crediting:
  - Solo: "Masayuki Nagao"
  - Multi (null-separated): "Masayuki Nagao\x00Masanori Hikichi"
  - Featuring: ARTIST="Darren Korb", FEATURING="Ashley Barrett"
  - Inline feat: "Darren Korb feat. Ashley Barrett"
  - Separators: "&", "+", " and ", " vs. ", "/", ","

Output is a ParticipantSet: typed list of CreditedParticipant with roles,
confidence, and resolution state.

Resolution logic:
  1. Parse raw strings into name tokens
  2. Normalize each name (lowercase, strip, collapse whitespace)
  3. Look up in codex atlas to resolve to entity_id
  4. Assign ResolutionState and confidence

Codex lookup is best-effort: if the artist is not in the codex, the
participant is UNRESOLVED but still carries their credited_form.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .ambiguity import ConfidenceRecord, ProvenanceSource, ResolutionState


# ── Separators for inline multi-artist strings ────────────────────────────────

# Null byte is Foobar2000's native multi-value separator
_NULL_SEP     = "\x00"

# Inline featuring patterns (capture the featured name)
_FEAT_PATTERNS = [
    re.compile(r"\s+feat\.?\s+", re.IGNORECASE),
    re.compile(r"\s+ft\.?\s+",   re.IGNORECASE),
    re.compile(r"\s+featuring\s+", re.IGNORECASE),
]

# Other joining separators — only used when null-sep is absent
_JOIN_PATTERNS = [
    re.compile(r"\s*&\s*"),
    re.compile(r"\s*\+\s*"),
    re.compile(r"\s+and\s+", re.IGNORECASE),
    re.compile(r"\s+vs\.?\s+", re.IGNORECASE),
]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class CreditedParticipant:
    """A single credited entity from a track's tag strings."""

    credited_form:     str                   # raw string as it appears in tags
    normalized_key:    str                   # lowercased, stripped
    role:              str                   # "role:composer" | "role:featured" | ...
    entity_id:         Optional[str]         # resolved codex id, or None
    confidence_record: ConfidenceRecord

    def to_dict(self) -> dict:
        return {
            "credited_form":     self.credited_form,
            "normalized_key":    self.normalized_key,
            "role":              self.role,
            "entity_id":         self.entity_id,
            "confidence_record": self.confidence_record.to_dict(),
        }


@dataclass
class ParticipantSet:
    """
    All credited participants for a single track.

    primary     — composers/primary credits (from ARTIST tag)
    featured    — featured guests (from FEATURING tag or inline feat.)
    attribution_type — solo | multi | inferred
    """
    primary:          list[CreditedParticipant] = field(default_factory=list)
    featured:         list[CreditedParticipant] = field(default_factory=list)
    attribution_type: str = "solo"   # solo | multi | inferred

    def all_participants(self) -> list[CreditedParticipant]:
        return self.primary + self.featured

    def to_dict(self) -> dict:
        return {
            "attribution_type": self.attribution_type,
            "primary":  [p.to_dict() for p in self.primary],
            "featured": [p.to_dict() for p in self.featured],
        }


# ── Normalization ─────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """Normalize a name string for key matching."""
    return re.sub(r"\s+", " ", s.strip().lower())


# ── Codex index (lazy-loaded) ──────────────────────────────────────────────────

_codex_index: Optional[dict[str, str]] = None  # normalized_key -> entity_id

def _load_codex_index() -> dict[str, str]:
    """
    Build a flat lookup: normalized name/alias → entity_id from codex atlas.
    Loads lazily on first call.
    """
    global _codex_index
    if _codex_index is not None:
        return _codex_index

    import json
    index: dict[str, str] = {}
    atlas_dir = _REPO_ROOT / "codex" / "atlas" / "music" / "artists"

    if not atlas_dir.exists():
        _codex_index = index
        return index

    for json_file in atlas_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        entity_id = data.get("entity_id", "")
        label     = data.get("label", "")
        aliases   = data.get("aliases", [])
        if not entity_id:
            continue

        if label:
            index[_norm(label)] = entity_id
        for alias in aliases:
            if alias:
                index[_norm(alias)] = entity_id

    _codex_index = index
    return index


def _lookup_entity(normalized_key: str) -> tuple[Optional[str], ResolutionState, float]:
    """
    Look up a normalized key in the codex.
    Returns (entity_id or None, resolution_state, confidence).
    """
    idx = _load_codex_index()
    if normalized_key in idx:
        return idx[normalized_key], ResolutionState.RESOLVED, 0.95

    # Try partial match — first token (last name or first name) exact
    tokens = normalized_key.split()
    if len(tokens) > 1:
        for key, eid in idx.items():
            key_tokens = set(key.split())
            if set(tokens) & key_tokens:
                overlap = len(set(tokens) & key_tokens) / len(set(tokens) | key_tokens)
                if overlap >= 0.6:
                    return eid, ResolutionState.LIKELY_RESOLVED, 0.70

    return None, ResolutionState.UNRESOLVED, 0.10


# ── Parsing helpers ───────────────────────────────────────────────────────────

def _split_primary(artist_raw: str) -> list[str]:
    """
    Split a raw ARTIST tag string into individual credited names.

    Priority:
      1. Null-byte separator (Foobar multi-value)
      2. Inline featuring — extract left side as primary, right as featured hint
         (callers handle the right side separately)
      3. Join separators (&, +, and, vs)
      4. Single value
    """
    if _NULL_SEP in artist_raw:
        return [p.strip() for p in artist_raw.split(_NULL_SEP) if p.strip()]

    for pat in _FEAT_PATTERNS:
        if pat.search(artist_raw):
            parts = pat.split(artist_raw, maxsplit=1)
            # Return only the primary side here; featured side is a hint
            return [parts[0].strip()] if parts[0].strip() else []

    for pat in _JOIN_PATTERNS:
        if pat.search(artist_raw):
            return [p.strip() for p in pat.split(artist_raw) if p.strip()]

    return [artist_raw.strip()] if artist_raw.strip() else []


def _extract_inline_featured(artist_raw: str) -> list[str]:
    """
    If artist_raw contains an inline feat. pattern, return the featured name(s).
    """
    for pat in _FEAT_PATTERNS:
        m = pat.search(artist_raw)
        if m:
            featured_raw = artist_raw[m.end():]
            return [p.strip() for p in re.split(r"[,;&+]", featured_raw) if p.strip()]
    return []


def _split_featuring(featuring_raw: str) -> list[str]:
    """
    Split a FEATURING tag value into individual featured artist names.
    Foobar uses null-byte, semicolon, newline, or comma as separator.
    """
    for sep in (_NULL_SEP, "\n", ";", ","):
        if sep in featuring_raw:
            return [p.strip() for p in featuring_raw.split(sep) if p.strip()]
    return [featuring_raw.strip()] if featuring_raw.strip() else []


# ── Main resolver ─────────────────────────────────────────────────────────────

def resolve_credits(
    artist_raw: str,
    featuring_raw: str = "",
) -> ParticipantSet:
    """
    Parse ARTIST + FEATURING tag strings into a ParticipantSet.

    artist_raw    — value of the ARTIST tag field
    featuring_raw — value of the FEATURING tag field (may be empty)

    Returns a fully-populated ParticipantSet with resolution state
    and confidence records for each participant.
    """
    primary_names  = _split_primary(artist_raw)
    featured_names = list(_split_featuring(featuring_raw)) if featuring_raw.strip() else []

    # Supplement with inline feat. if no FEATURING tag
    if not featured_names:
        featured_names = _extract_inline_featured(artist_raw)

    def _make_participant(name: str, role: str) -> CreditedParticipant:
        key = _norm(name)
        entity_id, state, conf = _lookup_entity(key)
        prov = [ProvenanceSource.FOOBAR_TAGS]
        if entity_id:
            prov.append(ProvenanceSource.CODEX)
        return CreditedParticipant(
            credited_form=name,
            normalized_key=key,
            role=role,
            entity_id=entity_id,
            confidence_record=ConfidenceRecord(
                resolution_state=state,
                confidence=conf,
                provenance=prov,
                credited_forms=[name],
            ),
        )

    primaries  = [_make_participant(n, "role:composer") for n in primary_names]
    featureds  = [_make_participant(n, "role:featured") for n in featured_names]

    if len(primaries) > 1:
        attribution_type = "multi"
    elif not primaries:
        attribution_type = "inferred"
    else:
        attribution_type = "solo"

    return ParticipantSet(
        primary=primaries,
        featured=featureds,
        attribution_type=attribution_type,
    )
