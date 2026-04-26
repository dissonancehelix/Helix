"""
Template family dossiers — knowledge about related template ecosystems.

A dossier captures what an experienced editor knows about a template family:
not just parameter names, but conventions, fragile zones, recurring breakage,
and the policies that govern their use.

Dossiers are static knowledge + can be extended by the operator.

Priority families (from Dissident93's edit history):
  - NFL infobox/stat ecosystem
  - Video game infobox/navbox ecosystem
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DossierParam:
    name: str
    aliases: list[str]
    description: str
    fragile: bool = False          # known to cause breakage if mishandled
    deprecated: bool = False


@dataclass
class TemplateFamilyDossier:
    family_id: str
    family_name: str
    description: str
    member_templates: list[str]     # canonical template names in this family
    common_params: list[DossierParam]
    fragile_zones: list[str]        # descriptions of known risky areas
    breakage_patterns: list[str]    # things that commonly go wrong
    style_conventions: list[str]    # editorial expectations
    relevant_policies: list[str]    # WP:NFL, MOS:VG, etc.
    transclusion_contexts: list[str]  # where these templates typically appear
    notes: list[str] = field(default_factory=list)

    def covers(self, template_name: str) -> bool:
        """Return True if this template is in the family."""
        name = template_name.removeprefix("Template:").lower()
        return any(m.lower() in name or name in m.lower() for m in self.member_templates)

    def display(self) -> str:
        lines = [
            f"=== {self.family_name} ===",
            self.description,
            "",
            f"Members ({len(self.member_templates)}): {', '.join(self.member_templates[:8])}",
            "",
            "Fragile zones:",
        ]
        for z in self.fragile_zones:
            lines.append(f"  ! {z}")
        lines.append("")
        lines.append("Style conventions:")
        for s in self.style_conventions:
            lines.append(f"  · {s}")
        lines.append("")
        lines.append(f"Policies: {', '.join(self.relevant_policies)}")
        if self.notes:
            lines.append("")
            for n in self.notes:
                lines.append(f"Note: {n}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "family_id": self.family_id,
            "family_name": self.family_name,
            "description": self.description,
            "member_templates": self.member_templates,
            "common_params": [
                {
                    "name": p.name, "aliases": p.aliases,
                    "description": p.description,
                    "fragile": p.fragile, "deprecated": p.deprecated,
                }
                for p in self.common_params
            ],
            "fragile_zones": self.fragile_zones,
            "breakage_patterns": self.breakage_patterns,
            "style_conventions": self.style_conventions,
            "relevant_policies": self.relevant_policies,
            "transclusion_contexts": self.transclusion_contexts,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# NFL dossier
# ---------------------------------------------------------------------------

_NFL_DOSSIER = TemplateFamilyDossier(
    family_id="nfl",
    family_name="NFL infobox and statistics ecosystem",
    description=(
        "Templates used on NFL player, team, draft, and season articles. "
        "High edit volume in Dissident93's history. "
        "BLP applies to all living player articles."
    ),
    member_templates=[
        "Infobox NFL player",
        "Infobox NFL biography",
        "NFL player stats",
        "NFL draft",
        "NFL season",
        "NFL team",
        "Infobox NFL official",
        "NFL game",
        "NFL coach",
    ],
    common_params=[
        DossierParam("name",          [],              "Player full name"),
        DossierParam("position",      ["pos"],         "Playing position — use official abbreviations (QB, WR, etc.)"),
        DossierParam("birth_date",    ["birthdate"],   "Use {{birth date}} template", fragile=True),
        DossierParam("birth_place",   ["birthplace"],  "City, State"),
        DossierParam("death_date",    ["deathdate"],   "Use {{death date and age}}", fragile=True),
        DossierParam("height",        ["height_in"],   "Use {{height}} template"),
        DossierParam("weight",        ["weight_lbs"],  "Use {{convert}} or numeric only"),
        DossierParam("college",       [],              "College attended — wikilink"),
        DossierParam("draft_year",    [],              "Year of NFL draft"),
        DossierParam("draft_round",   [],              "Round selected"),
        DossierParam("draft_pick",    [],              "Overall pick number"),
        DossierParam("teams",         [],              "Chronological team list with years", fragile=True),
        DossierParam("status",        [],              '"active", "retired", "free agent"'),
        DossierParam("number",        ["jersey"],      "Jersey number(s)", fragile=True),
        DossierParam("pfr",           [],              "Pro Football Reference ID"),
        DossierParam("stats_column",  [],              "Deprecated — use stat row params instead", deprecated=True),
    ],
    fragile_zones=[
        "|teams= format: each team on its own line with {{NFL link}} and year range. "
        "Incorrect format causes malformed infobox rows.",
        "|number= accepts pipe-separated values for multiple jersey numbers. "
        "Plain comma separation breaks the template.",
        "Birth/death date templates must be nested correctly — bare dates cause lint errors.",
        "Draft section is hidden when draft_year is absent — guard with #if if any sub-param is present.",
        "Stats template expects season-indexed rows; out-of-order rows silently corrupt totals.",
    ],
    breakage_patterns=[
        "Removing |status= on active players — infobox shows 'undetermined'.",
        "Using plain text for teams instead of {{NFL link}} — breaks standardized formatting.",
        "Adding |pfr= with wrong ID — links to wrong player on Pro Football Reference.",
        "Using full year ranges like '2020–2022' in teams — template expects separate from/to params.",
        "Bare birth_date without {{birth date}} — renders unformatted and breaks age calculation.",
    ],
    style_conventions=[
        "Positions: use official NFL abbreviations (QB, RB, WR, TE, OT, OG, C, DE, DT, LB, CB, S, K, P).",
        "College: link to article, not university website.",
        "Draft: always include round, pick, and year if player was drafted.",
        "Teams: listed chronologically; include all teams even if brief stints.",
        "BLP: contract values and salary require inline citation from reliable source.",
        "WP:NFL: player must have appeared in at least one regular-season or postseason NFL game for notability.",
        "Stats: cite NFL.com or Pro Football Reference as primary sources.",
    ],
    relevant_policies=["WP:NFL", "WP:BLP", "WP:V", "WP:RS"],
    transclusion_contexts=[
        "NFL player biography articles",
        "NFL coach articles",
        "NFL official/referee articles",
    ],
)


# ---------------------------------------------------------------------------
# Video game dossier
# ---------------------------------------------------------------------------

_VG_DOSSIER = TemplateFamilyDossier(
    family_id="vg",
    family_name="Video game infobox and navbox ecosystem",
    description=(
        "Templates used on video game, game developer, and game series articles. "
        "High edit volume in Dissident93's history (Dota 2, FromSoftware, Persona 5). "
        "MOS:VG governs formatting conventions."
    ),
    member_templates=[
        "Infobox video game",
        "Infobox video game series",
        "Infobox video game developer",
        "Video game reviews",
        "Video game release",
        "Navbox video game",
    ],
    common_params=[
        DossierParam("title",         [],              "Game title — must match article title"),
        DossierParam("image",         ["image_size"],  "Cover art filename (no File: prefix)", fragile=True),
        DossierParam("caption",       [],              "Image caption — include alt text"),
        DossierParam("developer",     [],              "Developer(s) — wikilink"),
        DossierParam("publisher",     [],              "Publisher(s) — wikilink"),
        DossierParam("director",      [],              "Game director(s)"),
        DossierParam("designer",      [],              "Game designer(s)"),
        DossierParam("composer",      [],              "Music composer(s) — wikilink"),
        DossierParam("series",        [],              "Game series — wikilink"),
        DossierParam("engine",        [],              "Game engine name"),
        DossierParam("platforms",     [],              "Platform list — use {{unbulleted list}}", fragile=True),
        DossierParam("released",      [],              "Release dates — use {{Video game release}}", fragile=True),
        DossierParam("genre",         [],              "Genre(s) — from standardized VG genre list"),
        DossierParam("modes",         [],              '"Single-player", "Multiplayer", etc.'),
        DossierParam("arcade_system", [],              "Arcade board — only for arcade games"),
    ],
    fragile_zones=[
        "|platforms= expects {{unbulleted list}} or wikilinked platform names. "
        "Plain comma lists render inconsistently across skins.",
        "|released= expects {{Video game release}} template for multi-region dates. "
        "Plain text dates lose region labeling.",
        "|image= must be bare filename (no File:, Image: prefix). "
        "Including prefix causes broken image display.",
        "Review aggregator scores in {{Video game reviews}} — MC/OC IDs must be exact.",
        "Genre values must use standardized MOS:VG terms — avoid invented genre names.",
    ],
    breakage_patterns=[
        "Using 'video game' where MOS:VG says 'game' — article tone inconsistency.",
        "Platform list without {{unbulleted list}} — breaks alignment in infobox.",
        "Release date as plain text — loses region context and breaks sorting.",
        "image= with File: prefix — broken image.",
        "Metacritic score without |mc_link= — unverifiable citation.",
        "Using 'characters' section header where 'Cast' or 'Plot' is MOS-preferred.",
    ],
    style_conventions=[
        "Titles: italicize game titles in prose (''Title'') and use {{italic title}} in article.",
        "Platforms: use standardized abbreviations (PS5, Xbox Series X/S, PC, NS).",
        "Developers: link on first mention; do not repeat links.",
        "Genre: use MOS:VG genre taxonomy — 'action-adventure', 'role-playing', etc.",
        "Gameplay section before Plot section (MOS:VG ordering).",
        "Avoid peacock terms ('groundbreaking', 'revolutionary') without citation.",
        "VGM composers: wikilink on first mention; use full name consistently.",
        "MOS:VG: avoid 'The player must...' framing — prefer 'Players...'.",
    ],
    relevant_policies=["MOS:VG", "WP:VG/GL", "WP:GNG", "WP:V", "WP:RS"],
    transclusion_contexts=[
        "Video game articles",
        "Game series articles",
        "Game developer articles",
    ],
)


# ---------------------------------------------------------------------------
# BLP general dossier (cross-cutting)
# ---------------------------------------------------------------------------

_BLP_DOSSIER = TemplateFamilyDossier(
    family_id="blp",
    family_name="BLP-sensitive article templates",
    description=(
        "Templates used in biographies of living persons. "
        "BLP policy supersedes most other editorial considerations. "
        "Applies to NFL player articles, composer articles, and any living person."
    ),
    member_templates=[
        "Infobox person",
        "Infobox NFL player",
        "Infobox musician",
        "Infobox video game developer",
        "Birth date",
        "Death date and age",
        "Birth date and age",
    ],
    common_params=[
        DossierParam("birth_date",  [],          "Must use {{birth date}} — required inline citation", fragile=True),
        DossierParam("death_date",  [],          "Must use {{death date and age}}", fragile=True),
        DossierParam("nationality", [],          "Sensitive — requires reliable sourcing"),
        DossierParam("spouse",      [],          "BLP-sensitive — only include if publicly documented"),
        DossierParam("children",    [],          "BLP-sensitive — omit unless subject has made public"),
        DossierParam("net_worth",   [],          "Highly contested — avoid or cite very carefully", fragile=True),
    ],
    fragile_zones=[
        "Any negative or contentious claim about a living person requires inline citation.",
        "Net worth, salary, contract figures — use only if cited from reliable, independent source.",
        "Ethnicity, religion, sexuality — include only if publicly stated by subject.",
        "Medical conditions — never include without exceptional sourcing.",
        "Criminal/legal history — must be reliably sourced; avoid WP:UNDUE weight.",
    ],
    breakage_patterns=[
        "Adding contested claim without citation — BLP violation, will be reverted.",
        "Copying salary info from non-reliable source (blogs, fan sites).",
        "Using Wikipedia itself as a source for BLP facts.",
        "Adding birth city/country from genealogy sites — not accepted as RS.",
        "Restoring previously reverted BLP content without new sourcing.",
    ],
    style_conventions=[
        "When in doubt, omit. BLP errs toward privacy, not completeness.",
        "Living person's political/religious views: only if publicly stated.",
        "Promotional language about living persons is a BLP concern.",
        "Use past tense for historical facts; present tense for current status.",
        "Do not include unverified information even if 'probably true'.",
    ],
    relevant_policies=["WP:BLP", "WP:V", "WP:RS", "WP:UNDUE", "WP:BLPNAME"],
    transclusion_contexts=[
        "Any article about a living person",
        "NFL player biography articles",
        "VGM composer articles",
    ],
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DOSSIER_REGISTRY: dict[str, TemplateFamilyDossier] = {
    d.family_id: d for d in [_NFL_DOSSIER, _VG_DOSSIER, _BLP_DOSSIER]
}


def get_dossier(family_id: str) -> TemplateFamilyDossier | None:
    return DOSSIER_REGISTRY.get(family_id)


def find_dossiers_for_template(template_name: str) -> list[TemplateFamilyDossier]:
    """Return all dossiers that claim this template as a member."""
    return [d for d in DOSSIER_REGISTRY.values() if d.covers(template_name)]
