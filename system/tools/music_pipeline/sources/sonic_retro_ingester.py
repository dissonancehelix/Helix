"""
sonic_retro_ingester.py — Sonic Retro HTML Ingester
====================================================
Parses local Sonic Retro HTML files (saved from Desktop/temp) into
ComposerNode, TrackNode, and Relationship objects for the ComposerGraph.

Supported files:
  Sonic the Hedgehog 3_Development_Music - Sonic Retro.htm
    → Full per-zone track attribution tables + staff list

API
---
ingest_s3k_html(path, graph) -> SonicRetroIngestResult
ingest_s3k_default(graph)   -> SonicRetroIngestResult  (uses Desktop/temp path)
"""

from __future__ import annotations

import html.parser
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from model.domains.music.atlas_integration.composer_schema import (
    ComposerNode, GameNode, Relationship, SoundTeamNode, TrackNode,
)
from model.domains.music.atlas_integration.composer_graph import (
    ComposerGraph, cid, gid, tid, tmid,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default path
# ---------------------------------------------------------------------------

S3K_HTML_PATH = Path("C:/Users/dissonance/Desktop/temp") / \
    "Sonic the Hedgehog 3_Development_Music - Sonic Retro.htm"

# ---------------------------------------------------------------------------
# Known track ID → (slug, title, game_section) mapping
# ---------------------------------------------------------------------------

S3K_TRACK_IDS: dict[str, tuple[str, str]] = {
    "01": ("s3k_01", "Angel Island Zone Act 1"),
    "02": ("s3k_02", "Angel Island Zone Act 2"),
    "03": ("s3k_03", "Hydrocity Zone Act 1"),
    "04": ("s3k_04", "Hydrocity Zone Act 2"),
    "05": ("s3k_05", "Marble Garden Zone Act 1"),
    "06": ("s3k_06", "Marble Garden Zone Act 2"),
    "07": ("s3k_07", "Carnival Night Zone Act 1"),
    "08": ("s3k_08", "Carnival Night Zone Act 2"),
    "09": ("s3k_09", "Flying Battery Zone Act 1"),
    "0A": ("s3k_0a", "Flying Battery Zone Act 2"),
    "0B": ("s3k_0b", "IceCap Zone Act 1"),
    "0C": ("s3k_0c", "IceCap Zone Act 2"),
    "0D": ("s3k_0d", "Launch Base Zone Act 1"),
    "0E": ("s3k_0e", "Launch Base Zone Act 2"),
    "0F": ("s3k_0f", "Mushroom Hill Zone Act 1"),
    "10": ("s3k_10", "Mushroom Hill Zone Act 2"),
    "11": ("s3k_11", "Sandopolis Zone Act 1"),
    "12": ("s3k_12", "Sandopolis Zone Act 2"),
    "13": ("s3k_13", "Lava Reef Zone Act 1"),
    "14": ("s3k_14", "Hidden Palace Zone / Lava Reef Act 2"),
    "15": ("s3k_15", "Sky Sanctuary Zone"),
    "16": ("s3k_16", "Death Egg Zone Act 1"),
    "17": ("s3k_17", "Death Egg Zone Act 2"),
    "18": ("s3k_18", "Boss 1"),
    "19": ("s3k_19", "Boss 2"),
    "1A": ("s3k_1a", "The Doomsday Zone"),
    "1B": ("s3k_1b", "Bonus Stage - Magnetic Orbs"),
    "1C": ("s3k_1c", "Special Stage - Blue Spheres"),
    "1D": ("s3k_1d", "Bonus Stage - Slot Machine"),
    "1E": ("s3k_1e", "Bonus Stage - Gumball Machine"),
    "1F": ("s3k_1f", "Knuckles Appears"),
    "20": ("s3k_20", "2P vs. - Azure Lake"),
    "21": ("s3k_21", "2P vs. - Balloon Park"),
    "22": ("s3k_22", "2P vs. - Desert Palace"),
    "23": ("s3k_23", "2P vs. - Chrome Gadget"),
    "24": ("s3k_24", "2P vs. - Endless Mine"),
    "25": ("s3k_25", "Title Screen"),
    "26": ("s3k_26", "Staff Roll"),
    "27": ("s3k_27", "Game Over"),
    "28": ("s3k_28", "Continue"),
    "29": ("s3k_29", "Stage Clear - Act Passed"),
    "2A": ("s3k_2a", "1UP - Extra Life"),
    "2B": ("s3k_2b", "Chaos Emerald"),
    "2C": ("s3k_2c", "Power Up - Invincibility"),
    "2D": ("s3k_2d", "2P Menu - Player Select"),
    "2E": ("s3k_2e", "Unused Song / Boss 1 (S3 version)"),
    "2F": ("s3k_2f", "Menu - Data Select"),
    "30": ("s3k_30", "Final Eggman"),
    "31": ("s3k_31", "Drowning"),
    "32": ("s3k_32", "All Clear - Victory"),
}

# ---------------------------------------------------------------------------
# Name → composer_id slug mapping  (canonical)
# ---------------------------------------------------------------------------

NAME_TO_SLUG: dict[str, str] = {
    # Sega Sound Team
    "masayuki nagao":         "masayuki_nagao",
    "tatsuyuki maeda":        "tatsuyuki_maeda",
    "jun senoue":             "jun_senoue",
    "yoshiaki kashima":       "yoshiaki_kashima",
    "sachio ogawa":           "sachio_ogawa",
    "masaru setsumaru":       "masaru_setsumaru",
    "tomonori sawada":        "tomonori_sawada",
    "yukifumi makino":        "yukifumi_makino",
    "tokuhiko uwabo":         "tokuhiko_uwabo",
    'tokuhiko "bo" uwabo':    "tokuhiko_uwabo",
    # Cube Corp
    "miyoko takaoka":         "miyoko_takaoka",
    "masanori hikichi":       "masanori_hikichi",
    # Jackson's Sound Team
    "michael jackson":        "michael_jackson",
    "brad buxer":             "brad_buxer",
    "bobby brooks":           "bobby_brooks",
    "robert green brooks":    "bobby_brooks",
    'robert green "bobby" brooks': "bobby_brooks",
    "darryl ross":            "darryl_ross",
    "geoff grace":            "geoff_grace",
    "doug grigsby iii":       "doug_grigsby_iii",
    "cirocco jones":          "cirocco_jones",
    'c. cirocco "scirocco" jones': "cirocco_jones",
    # Non-team composers
    "bruce connole":          "bruce_connole",
    "howard drossin":         "howard_drossin",
    # Others
    "masanori nakayama":      "masanori_nakayama",
}


def _name_to_slug(name: str) -> str | None:
    """Fuzzy name → slug lookup."""
    clean = name.strip().lower()
    # Remove citation brackets like [54]
    clean = re.sub(r"\s*\[\d+\]", "", clean)
    # Remove parenthetical roles like (Uncredited)
    clean = re.sub(r"\s*\([^)]+\)", "", clean)
    clean = clean.strip()
    return NAME_TO_SLUG.get(clean)


# ---------------------------------------------------------------------------
# Minimal stdlib HTML table extractor
# ---------------------------------------------------------------------------

class _TableExtractor(html.parser.HTMLParser):
    """Extracts all tables as list[list[list[str]]]."""

    def __init__(self) -> None:
        super().__init__()
        self.tables:    list[list[list[str]]] = []
        self._table:    list[list[str]] | None = None
        self._row:      list[str] | None = None
        self._cell:     list[str] | None = None
        self._in_ref:   bool = False   # inside [n] citation span
        self._nesting:  int = 0        # table nesting depth (skip nested)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_dict = dict(attrs)
        if tag == "table":
            self._nesting += 1
            if self._nesting == 1:
                self._table = []
                self.tables.append(self._table)
        elif tag == "tr" and self._nesting == 1 and self._table is not None:
            self._row = []
            self._table.append(self._row)
        elif tag in ("td", "th") and self._nesting == 1 and self._row is not None:
            self._cell = []
            self._row.append(self._cell)
        elif tag == "sup":
            self._in_ref = True  # skip superscript citation text

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._nesting -= 1
            if self._nesting == 0:
                self._table = None
        elif tag == "tr":
            self._row = None
        elif tag in ("td", "th"):
            self._cell = None
        elif tag == "sup":
            self._in_ref = False

    def handle_data(self, data: str) -> None:
        if self._in_ref:
            return
        if self._cell is not None:
            clean = data.replace("\xa0", " ").strip()
            if clean:
                self._cell.append(clean)


def _cell_text(cell: list[str]) -> str:
    return " ".join(cell).strip()


def _extract_tables(html_text: str) -> list[list[list[str]]]:
    ex = _TableExtractor()
    ex.feed(html_text)
    return ex.tables


# ---------------------------------------------------------------------------
# Credit string parser
# ---------------------------------------------------------------------------

_REF_RE = re.compile(r"\[\d+\]")
_CREDIT_PARTS_RE = re.compile(
    r"(Composition and Arrangement|Composition|Arrangement|Programming)\s*[:\u00a0 ]+([^•]+?)(?=\s*(?:Composition|Arrangement|Programming|•|$))",
    re.IGNORECASE,
)


def _parse_credits(credit_str: str) -> dict[str, list[str]]:
    """
    Parse credit string into role → [name, ...] mapping.
    Returns {} if all unknown (???).
    """
    cleaned = _REF_RE.sub("", credit_str).strip()
    if not cleaned or "???" in cleaned or cleaned == "???":
        return {}

    result: dict[str, list[str]] = {}
    for m in _CREDIT_PARTS_RE.finditer(cleaned):
        role_key = m.group(1).lower().replace(" and ", "_and_")
        name_part = m.group(2).strip()
        if "???" in name_part or not name_part:
            continue
        # Split multiple names by " & " or " , "
        names = [n.strip() for n in re.split(r"\s*[&,]\s*", name_part) if n.strip()]
        if role_key == "composition_and_arrangement":
            result.setdefault("composition", []).extend(names)
            result.setdefault("arrangement", []).extend(names)
        else:
            result.setdefault(role_key, []).extend(names)

    return result


# ---------------------------------------------------------------------------
# Track table parser
# ---------------------------------------------------------------------------

def _parse_track_table(zone_name: str, rows: list[list[list[str]]]) -> list[dict]:
    """
    Parse a zone track table (rows from the extractor).
    Returns list of raw attribution dicts.
    """
    results = []
    for row in rows:
        cells = [_cell_text(c) for c in row]
        if len(cells) < 4:
            continue
        # Columns: [thumbnail?], ID, Version(s), Team, Credit(s)
        # First cell may be empty (image) or the ID itself
        # Detect by checking which cell looks like a hex ID
        track_id = None
        credit_str = ""
        team_str = ""
        versions_str = ""

        # Try to find the hex ID column
        for i, cell in enumerate(cells):
            if re.match(r'^[0-9A-Fa-f]{2}$', cell.strip()):
                track_id = cell.strip().upper()
                if i + 1 < len(cells): versions_str = cells[i + 1]
                if i + 2 < len(cells): team_str     = cells[i + 2]
                if i + 3 < len(cells): credit_str   = cells[i + 3]
                break

        if not track_id:
            continue

        credits = _parse_credits(credit_str)
        results.append({
            "track_id_hex": track_id,
            "zone":         zone_name,
            "versions":     versions_str,
            "team":         team_str,
            "credit_raw":   credit_str,
            "credits":      credits,
        })

    return results


# ---------------------------------------------------------------------------
# Staff table parser
# ---------------------------------------------------------------------------

_UNCREDITED_RE = re.compile(r"\s*\(uncredited\)", re.IGNORECASE)
_ROLE_SPLIT_RE = re.compile(r"\s*[,&]\s*|(?:\s+&\s+)")


def _parse_staff_table(rows: list[list[list[str]]]) -> list[dict]:
    """
    Parse the staff table → list of staff dicts.
    Columns: Name, Group, Role, Description, Statement(s)
    """
    staff = []
    for row in rows:
        cells = [_cell_text(c) for c in row]
        if len(cells) < 3:
            continue
        raw_name = cells[0]
        group    = cells[1] if len(cells) > 1 else ""
        role     = cells[2] if len(cells) > 2 else ""
        desc     = cells[3] if len(cells) > 3 else ""

        # Skip header row
        if raw_name.lower() in ("name", ""):
            continue

        uncredited = bool(_UNCREDITED_RE.search(raw_name))
        name_clean = _REF_RE.sub("", raw_name)
        name_clean = _UNCREDITED_RE.sub("", name_clean).strip()

        # Extract quoted nickname (e.g., "Bo", "Milpo", "Scirocco")
        nickname_m = re.search(r'"([^"]+)"', name_clean)
        nickname = nickname_m.group(1) if nickname_m else None

        # Extract plain name without quotes / brackets
        plain_name = re.sub(r'"[^"]*"\s*', "", name_clean).strip()
        # Remove trailing citation bracket remnants
        plain_name = _REF_RE.sub("", plain_name).strip()

        staff.append({
            "name_raw":    name_clean,
            "plain_name":  plain_name,
            "nickname":    nickname,
            "uncredited":  uncredited,
            "group":       group.strip(),
            "role":        role.strip(),
            "description": desc.strip(),
        })

    return staff


# ---------------------------------------------------------------------------
# ComposerNode builder from staff record
# ---------------------------------------------------------------------------

_GROUP_TO_STUDIO: dict[str, str] = {
    "Sega Sound Team":        "Sega",
    "Sega Sound Team / Opus Corp": "Opus Corp",
    "Cube Corp":              "Cube Corp",
    "Jackson's Sound Team":  "MJJ Productions",
    "Sega Technical Institute": "Sega Technical Institute",
    "Unlimited Sound Project": "Unlimited Sound Project",
    "Studio Who":             "Studio Who",
    "None":                   "",
}

_GROUP_TO_TEAM: dict[str, str | None] = {
    "Sega Sound Team":        "sega_sound_team_1994",
    "Jackson's Sound Team":  "jacksons_sound_team_1993",
    "Cube Corp":              "cube_corp_1993",
}


def _staff_to_composer_node(staff: dict) -> ComposerNode:
    """Build a ComposerNode from a parsed staff record."""
    name    = staff["plain_name"]
    slug    = _name_to_slug(name) or _auto_slug(name)
    group   = staff["group"]
    studio  = _GROUP_TO_STUDIO.get(group, group or "")
    team_id = _GROUP_TO_TEAM.get(group)
    roles   = [r.strip() for r in re.split(r",\s*|&\s*|;\s*", staff["role"]) if r.strip()]
    aliases = []
    if staff["nickname"]:
        aliases.append(staff["nickname"])

    node = ComposerNode(
        composer_id=slug,
        full_name=name,
        aliases=aliases,
        studios=[studio] if studio else [],
        sound_teams=[team_id] if team_id else [],
        bio_summary=staff["description"] or None,
        style_traits={
            "source_roles": roles,
            "group": group,
            "uncredited": staff["uncredited"],
            "source": "sonic_retro_html",
        },
    )
    return node


def _auto_slug(name: str) -> str:
    """Generate a slug from a name (fallback when not in NAME_TO_SLUG)."""
    s = name.lower().strip()
    s = re.sub(r'"[^"]*"', "", s)         # remove nicknames
    s = re.sub(r"\([^)]*\)", "", s)       # remove parentheticals
    s = re.sub(r"[^a-z0-9\s]", "", s)    # strip punctuation
    s = re.sub(r"\s+", "_", s.strip())   # spaces → underscores
    return s


# ---------------------------------------------------------------------------
# Full ingest result
# ---------------------------------------------------------------------------

@dataclass
class SonicRetroIngestResult:
    composers_added:   int = 0
    composers_updated: int = 0
    tracks_added:      int = 0
    relationships_added: int = 0
    errors:            list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"SonicRetroIngestResult("
            f"composers={self.composers_added}+{self.composers_updated}, "
            f"tracks={self.tracks_added}, "
            f"rels={self.relationships_added}, "
            f"errors={len(self.errors)})"
        )


# ---------------------------------------------------------------------------
# Main ingest function
# ---------------------------------------------------------------------------

def ingest_s3k_html(
    path: Path,
    graph: ComposerGraph,
    game_id: str = "sonic_3_and_knuckles",
) -> SonicRetroIngestResult:
    """
    Parse a Sonic Retro S3K music development HTML page and populate `graph`.

    Adds:
    - ComposerNode for every staff member
    - SoundTeamNode for Jackson/Cube/Sega teams (if not already present)
    - TrackNode for every track with known attribution
    - Relationships: wrote, arranged, part_of, member_of, collaborated_with
    """
    result = SonicRetroIngestResult()

    if not path.exists():
        result.errors.append(f"File not found: {path}")
        log.warning("sonic_retro_ingester: file not found: %s", path)
        return result

    html_text = path.read_text(encoding="utf-8", errors="replace")
    tables = _extract_tables(html_text)
    log.info("sonic_retro_ingester: extracted %d tables from %s", len(tables), path.name)

    # --- Ensure game node exists ---
    if not graph._games.get(game_id):
        from model.domains.music.atlas_integration.composer_schema import S3K_GAME
        graph.add_game(S3K_GAME)

    # --- Pass 1: find and parse staff table ---
    staff_list: list[dict] = []
    for t in tables:
        if not t or not t[0]:
            continue
        h = [_cell_text(c) for c in t[0]]
        if "Name" in h and "Role" in h:
            staff_list = _parse_staff_table(t[1:])
            log.info("sonic_retro_ingester: found staff table with %d entries", len(staff_list))
            break

    # Build extra sound teams
    _ensure_extra_teams(graph)

    # Add all staff as ComposerNodes
    composer_slugs_by_group: dict[str, list[str]] = {}
    for staff in staff_list:
        try:
            node = _staff_to_composer_node(staff)
            existing = graph.get_composer(node.composer_id)
            if existing:
                result.composers_updated += 1
            else:
                result.composers_added += 1
            graph.add_composer(node)

            # Track member → team relationship
            group = staff["group"]
            team_id = _GROUP_TO_TEAM.get(group)
            if team_id:
                graph.relate(
                    cid(node.composer_id), "member_of", tmid(team_id),
                    confidence=0.95, source_name="sonic_retro_html",
                )
                result.relationships_added += 1
                composer_slugs_by_group.setdefault(group, []).append(node.composer_id)

            # worked_on game relationship
            # Only add worked_on for composers (not coordinators, directors, etc.)
            roles_lower = staff["role"].lower()
            is_composer = any(r in roles_lower for r in ("composer", "arranger", "sound"))
            if is_composer:
                graph.relate(
                    cid(node.composer_id), "worked_on", gid(game_id),
                    confidence=0.9, source_name="sonic_retro_html",
                )
                result.relationships_added += 1

        except Exception as exc:
            result.errors.append(f"staff {staff.get('plain_name', '?')}: {exc}")

    # Add collaborated_with edges within each sound team group
    for group, members in composer_slugs_by_group.items():
        for i, c1 in enumerate(members):
            for c2 in members[i + 1:]:
                graph.relate(
                    cid(c1), "collaborated_with", cid(c2),
                    confidence=0.85, source_name="sonic_retro_html",
                    notes=f"Co-worked on S3K ({group})",
                )
                result.relationships_added += 1

    # --- Pass 2: find and parse track attribution tables ---
    for t in tables:
        if not t or not t[0]:
            continue
        h = [_cell_text(c) for c in t[0]]
        if "ID" not in h or "Credit(s)" not in h:
            continue

        zone_name = h[0].strip() if h[0] else "Unknown Zone"
        raw_tracks = _parse_track_table(zone_name, t[1:])

        for raw in raw_tracks:
            track_id_hex = raw["track_id_hex"]
            if track_id_hex not in S3K_TRACK_IDS:
                continue

            track_slug, track_title = S3K_TRACK_IDS[track_id_hex]
            credits = raw["credits"]

            # Upsert track node
            existing_track = graph.get_track(track_slug)
            if not existing_track:
                track_node = TrackNode(
                    track_id=track_slug,
                    title=track_title,
                    game_id=game_id,
                    platform="Sega Genesis / Mega Drive",
                    external_ids={"sonic_retro_id": track_id_hex},
                )
                graph.add_track(track_node)
                result.tracks_added += 1

                # part_of relationship
                graph.relate(
                    tid(track_slug), "part_of", gid(game_id),
                    confidence=1.0, source_name="sonic_retro_html",
                )
                result.relationships_added += 1

            # Attribution relationships from credits
            for role, names in credits.items():
                for name in names:
                    slug = _name_to_slug(name)
                    if not slug:
                        slug = _auto_slug(name)
                        log.debug("sonic_retro_ingester: auto-slug '%s' → '%s'", name, slug)

                    # Ensure composer node exists (minimal stub if not yet in staff table)
                    if not graph.get_composer(slug):
                        stub = ComposerNode(
                            composer_id=slug,
                            full_name=name.strip(),
                            style_traits={"source": "sonic_retro_html_credits"},
                        )
                        graph.add_composer(stub)
                        result.composers_added += 1

                    relation = "wrote" if "composition" in role else "attributed_to"
                    graph.relate(
                        cid(slug), relation, tid(track_slug),
                        confidence=0.9, source_name="sonic_retro_html",
                        notes=f"{role.title()}: {raw['credit_raw'][:80]}",
                    )
                    result.relationships_added += 1

    log.info("sonic_retro_ingester: %s", result)
    return result


def ingest_s3k_default(graph: ComposerGraph) -> SonicRetroIngestResult:
    """Ingest using the default Desktop/temp path."""
    return ingest_s3k_html(S3K_HTML_PATH, graph)


# ---------------------------------------------------------------------------
# Extra sound teams not in composer_schema seed
# ---------------------------------------------------------------------------

def _ensure_extra_teams(graph: ComposerGraph) -> None:
    """Add Jackson/Cube/STI teams if not already present."""
    extra_teams = [
        SoundTeamNode(
            team_id="jacksons_sound_team_1993",
            name="Jackson's Sound Team (1993)",
            company="MJJ Productions",
            members=[
                "michael_jackson", "brad_buxer", "bobby_brooks",
                "darryl_ross", "geoff_grace", "doug_grigsby_iii", "cirocco_jones",
            ],
            active_years="1993",
        ),
        SoundTeamNode(
            team_id="cube_corp_1993",
            name="Cube Corp (1993)",
            company="Cube Corp",
            members=["miyoko_takaoka", "masanori_hikichi"],
            active_years="1993",
        ),
        SoundTeamNode(
            team_id="sti_sound_1993",
            name="Sega Technical Institute Sound",
            company="Sega Technical Institute",
            members=["howard_drossin"],
            active_years="1993",
        ),
    ]
    for team in extra_teams:
        if not graph._teams.get(team.team_id):
            graph.add_team(team)
            log.debug("sonic_retro_ingester: added team %s", team.team_id)


# ---------------------------------------------------------------------------
# Known attribution notes (from Sonic Retro research)
# ---------------------------------------------------------------------------

KNOWN_ATTRIBUTION_NOTES: dict[str, str] = {
    "s3k_0b": (
        "IceCap Zone Act 1: Based on 'Hard Times' by The Jetzons "
        "(Bruce Connole & Brad Buxer, ~1982). "
        "Arrangement attributed to Brad Buxer for S3K version."
    ),
    "s3k_0c": "IceCap Zone Act 2: Arrangement attributed to Brad Buxer / Jackson team.",
    "s3k_04": "Hydrocity Zone Act 2: Arrangement by Masayuki Nagao (Sega/Opus Corp).",
    "s3k_26": (
        "Staff Roll: Brad Buxer composition; contains Michael Jackson's beatboxing "
        "samples, later reused in 'Stranger In Moscow'."
    ),
    "s3k_1c": "Special Stage - Blue Spheres: Yoshiaki Kashima. Recycled from SegaSonic Bros.",
    "s3k_2f": "Data Select Menu: Programming and arrangement by Masaru Setsumaru.",
    "s3k_15": "Sky Sanctuary Zone: Arrangement by Masaru Setsumaru (Cube/Sega).",
    "s3k_19": "Boss 2: Composition and arrangement by Masanori Hikichi (Cube Corp).",
}

