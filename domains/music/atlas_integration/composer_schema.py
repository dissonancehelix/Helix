"""
composer_schema.py — Composer Knowledge Graph Schema
=====================================================
Canonical data model for composers, tracks, games, and sound teams.
All external data sources normalize into these structures.

Design:
- Dataclasses are the in-memory representation
- All fields are optional (None = unknown)
- `external_ids` maps source name → source ID for cross-referencing
- `confidence` on relationships: 1.0 = authoritative, 0.6 = inferred, 0.3 = speculative

Relationships encoded as simple dicts so the graph is JSON-serializable:
    {
      "source": "composer:masayuki_nagao",
      "relation": "wrote",
      "target": "track:s3k_02",
      "confidence": 1.0,
      "source_name": "sonic_retro"
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Node types
# ---------------------------------------------------------------------------

@dataclass
class ComposerNode:
    """A composer or sound designer."""
    composer_id:    str              # slug, e.g. "masayuki_nagao"
    full_name:      str
    aliases:        list[str]        = field(default_factory=list)
    nationality:    str | None       = None
    birth_year:     int | None       = None
    death_year:     int | None       = None
    years_active:   str | None       = None   # e.g. "1989–present"
    instruments:    list[str]        = field(default_factory=list)
    studios:        list[str]        = field(default_factory=list)   # companies
    sound_teams:    list[str]        = field(default_factory=list)   # e.g. "Sega Sound Team"

    # External IDs for cross-referencing
    external_ids:   dict[str, str]   = field(default_factory=dict)
    # Keys: "wikipedia", "wikidata", "vgmdb", "vgmpf", "lastfm", "spotify", "musicbrainz"

    # Biography
    bio_summary:    str | None       = None   # 2–3 sentence summary
    bio_url:        str | None       = None   # canonical Wikipedia/Wikidata URL

    # Helix analysis data (filled by linker.py)
    fingerprint_vector:   list[float] | None  = None
    cluster_memberships:  list[str]   = field(default_factory=list)
    representative_tracks: list[str]  = field(default_factory=list)

    # Stylistic profile (computed from analysis)
    style_traits:   dict[str, Any]   = field(default_factory=dict)
    # e.g. {"dominant_key": "minor", "tempo_range": [100,160], "preferred_alg": 4}

    def to_dict(self) -> dict[str, Any]:
        return {
            "composer_id":    self.composer_id,
            "full_name":      self.full_name,
            "aliases":        self.aliases,
            "nationality":    self.nationality,
            "birth_year":     self.birth_year,
            "years_active":   self.years_active,
            "instruments":    self.instruments,
            "studios":        self.studios,
            "sound_teams":    self.sound_teams,
            "external_ids":   self.external_ids,
            "bio_summary":    self.bio_summary,
            "bio_url":        self.bio_url,
            "fingerprint_vector": (
                [round(x, 4) for x in self.fingerprint_vector]
                if self.fingerprint_vector else None
            ),
            "cluster_memberships":   self.cluster_memberships,
            "representative_tracks": self.representative_tracks,
            "style_traits":          self.style_traits,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ComposerNode":
        return cls(
            composer_id=d["composer_id"],
            full_name=d["full_name"],
            aliases=d.get("aliases", []),
            nationality=d.get("nationality"),
            birth_year=d.get("birth_year"),
            death_year=d.get("death_year"),
            years_active=d.get("years_active"),
            instruments=d.get("instruments", []),
            studios=d.get("studios", []),
            sound_teams=d.get("sound_teams", []),
            external_ids=d.get("external_ids", {}),
            bio_summary=d.get("bio_summary"),
            bio_url=d.get("bio_url"),
            fingerprint_vector=d.get("fingerprint_vector"),
            cluster_memberships=d.get("cluster_memberships", []),
            representative_tracks=d.get("representative_tracks", []),
            style_traits=d.get("style_traits", {}),
        )


@dataclass
class TrackNode:
    """A VGM track."""
    track_id:       str              # e.g. "s3k_02"
    title:          str | None       = None
    game_id:        str | None       = None
    platform:       str | None       = None
    duration_sec:   float | None     = None
    file_path:      str | None       = None
    chip:           str | None       = None  # "YM2612+SN76489"
    track_number:   int | None       = None
    composers:      list[str]        = field(default_factory=list)   # composer_ids
    attribution_confidence: float    = 1.0
    external_ids:   dict[str, str]   = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id":     self.track_id,
            "title":        self.title,
            "game_id":      self.game_id,
            "platform":     self.platform,
            "duration_sec": self.duration_sec,
            "chip":         self.chip,
            "track_number": self.track_number,
            "composers":    self.composers,
            "attribution_confidence": self.attribution_confidence,
            "external_ids": self.external_ids,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TrackNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class GameNode:
    """A video game."""
    game_id:        str
    title:          str
    platform:       str | None       = None
    year:           int | None       = None
    developer:      str | None       = None
    publisher:      str | None       = None
    composers:      list[str]        = field(default_factory=list)   # composer_ids
    sound_team:     str | None       = None
    external_ids:   dict[str, str]   = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_id":    self.game_id,
            "title":      self.title,
            "platform":   self.platform,
            "year":       self.year,
            "developer":  self.developer,
            "publisher":  self.publisher,
            "composers":  self.composers,
            "sound_team": self.sound_team,
            "external_ids": self.external_ids,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SoundTeamNode:
    """A studio sound team (e.g. Sega AM3 Sound Team)."""
    team_id:     str
    name:        str
    company:     str | None = None
    members:     list[str] = field(default_factory=list)   # composer_ids
    active_years: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "team_id":     self.team_id,
            "name":        self.name,
            "company":     self.company,
            "members":     self.members,
            "active_years": self.active_years,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SoundTeamNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Relationship
# ---------------------------------------------------------------------------

VALID_RELATIONS = {
    # Composer → X
    "wrote",              # composer → track
    "arranged",           # composer → track
    "worked_on",          # composer → game
    "member_of",          # composer → sound_team
    "worked_at",          # composer → studio
    "influenced_by",      # composer → composer
    "collaborated_with",  # composer → composer  (symmetric)
    # Track → X
    "part_of",            # track → game
    "appears_in",         # track → game  (alias for part_of with soundtrack context)
    "released_on",        # track → soundtrack
    "uses_sound_driver",  # track/game → sound_driver
    "attributed_to",      # track → composer  (attribution result, may be inferred)
    # Game → X
    "runs_on",            # game → platform
    "published_by",       # game → studio
    "developed_by",       # game → studio
    # Soundtrack → X
    "documents",          # soundtrack → game
    "released_by",        # soundtrack → studio
    # New relationships
    "has_style_profile",  # artist -> artist_style_vector
    "uses_motif",         # artist/track -> motif
    "uses_chip",          # track/platform/sound_driver -> sound_chip
    "contains_track",     # album -> track
    "characterizes",      # artist_style_vector -> artist
    "appears_in_track",   # motif/musical_pattern -> track
    "pattern_used_by",    # musical_pattern -> artist
    "driver_supports",    # sound_driver -> sound_chip
    "driver_used_in",     # sound_driver -> game/track
    # Listener -> X
    "listened_to",        # listener -> track
    "has_taste_profile",  # listener -> listener_taste_vector
    # ListenerTasteVector -> X
    "taste_affinity",     # listener_taste_vector -> motif / artist / track
    # Motif Evolution Graph -> X
    "has_transformation", # motif -> motif_relationship
    "transformation_of",  # motif_relationship -> motif
    "observed_in",        # motif_relationship -> track
    "has_lineage",        # artist -> motif_lineage
    "uses_motif",         # artist -> motif
}


@dataclass
class Relationship:
    source:      str             # node ID with type prefix, e.g. "composer:masayuki_nagao"
    relation:    str             # one of VALID_RELATIONS
    target:      str             # node ID
    confidence:  float   = 1.0  # 0–1
    source_name: str     = ""   # provenance: "sonic_retro", "vgmdb", "helix_analysis", etc.
    notes:       str     = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source":      self.source,
            "relation":    self.relation,
            "target":      self.target,
            "confidence":  round(self.confidence, 3),
            "source_name": self.source_name,
            "notes":       self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Relationship":
        return cls(
            source=d["source"],
            relation=d["relation"],
            target=d["target"],
            confidence=d.get("confidence", 1.0),
            source_name=d.get("source_name", ""),
            notes=d.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Canonical S3K seed data (ground truth from Sonic Retro / known attribution)
# ---------------------------------------------------------------------------

S3K_GAME = GameNode(
    game_id="sonic_3_and_knuckles",
    title="Sonic 3 & Knuckles",
    platform="Sega Genesis / Mega Drive",
    year=1994,
    developer="Sonic Team / Sega",
    publisher="Sega",
    composers=[
        "masayuki_nagao", "tatsuyuki_maeda", "jun_senoue",
        "yoshiaki_kashima", "brad_buxer", "darryl_ross",
        "bobby_brooks", "cirocco_jones", "doug_grigsby_iii", "geoff_grace",
    ],
    sound_team="sega_sound_team_1994",
    external_ids={
        "vgmdb":     "359",
        "wikipedia": "Sonic_3_%26_Knuckles",
    },
)

SEED_COMPOSERS: list[ComposerNode] = [
    ComposerNode(
        composer_id="masayuki_nagao",
        full_name="Masayuki Nagao",
        aliases=["マサユキ・ナガオ"],
        nationality="Japanese",
        studios=["Sega", "Sonic Team"],
        sound_teams=["sega_sound_team_1994"],
        external_ids={
            "vgmdb":    "15",
            "vgmpf":    "Masayuki_Nagao",
            "wikidata": "Q14934873",
        },
        style_traits={
            "signature": "Minor-key melodic writing, stepwise bass lines, high rhythmic density",
            "preferred_chip": "YM2612",
        },
    ),
    ComposerNode(
        composer_id="tatsuyuki_maeda",
        full_name="Tatsuyuki Maeda",
        aliases=["マエダ・タツユキ"],
        nationality="Japanese",
        studios=["Sega"],
        sound_teams=["sega_sound_team_1994"],
        external_ids={
            "vgmdb":    "298",
            "vgmpf":    "Tatsuyuki_Maeda",
        },
        style_traits={
            "signature": "Driving rock-influenced rhythms, modal harmonic language, prominent bass",
        },
    ),
    ComposerNode(
        composer_id="jun_senoue",
        full_name="Jun Senoue",
        aliases=["瀬上純"],
        nationality="Japanese",
        studios=["Sega", "Hardline Records"],
        sound_teams=["sega_sound_team_1994", "crush_40"],
        external_ids={
            "vgmdb":    "29",
            "wikipedia": "Jun_Senoue",
            "wikidata":  "Q4175052",
            "lastfm":    "Jun Senoue",
        },
    ),
    ComposerNode(
        composer_id="yoshiaki_kashima",
        full_name="Yoshiaki Kashima",
        aliases=["鹿島由明"],
        nationality="Japanese",
        studios=["Sega"],
        sound_teams=["sega_sound_team_1994"],
        external_ids={
            "vgmdb": "516",
        },
        style_traits={
            "notes": "Special Stage music recycled from SegaSonic Bros.",
        },
    ),
    ComposerNode(
        composer_id="brad_buxer",
        full_name="Brad Buxer",
        nationality="American",
        studios=["MJJ Productions"],
        external_ids={
            "wikipedia": "Brad_Buxer",
            "wikidata":  "Q4957085",
        },
        style_traits={
            "signature": "IceCap Zone Act 1 (based on 'Hard Times' by The Jetzons)",
            "notes": "Michael Jackson associate; contributed to Sonic 3",
        },
    ),
    ComposerNode(
        composer_id="darryl_ross",
        full_name="Darryl Ross",
        nationality="American",
        studios=["MJJ Productions"],
        style_traits={"notes": "Michael Jackson associate; Sonic 3 contributor"},
    ),
    ComposerNode(
        composer_id="bobby_brooks",
        full_name="Bobby Brooks",
        nationality="American",
        studios=["MJJ Productions"],
    ),
    ComposerNode(
        composer_id="cirocco_jones",
        full_name="Cirocco Jones",
        nationality="American",
        studios=["MJJ Productions"],
    ),
    ComposerNode(
        composer_id="doug_grigsby_iii",
        full_name="Doug Grigsby III",
        nationality="American",
        studios=["MJJ Productions"],
    ),
    ComposerNode(
        composer_id="geoff_grace",
        full_name="Geoff Grace",
        nationality="American",
        studios=["MJJ Productions"],
    ),
]

SEED_SOUND_TEAMS: list[SoundTeamNode] = [
    SoundTeamNode(
        team_id="sega_sound_team_1994",
        name="Sega Sound Team (1993–1994)",
        company="Sega",
        members=["masayuki_nagao", "tatsuyuki_maeda", "jun_senoue", "yoshiaki_kashima"],
        active_years="1993–1994",
    ),
]


# ---------------------------------------------------------------------------
# Extended entity types
# ---------------------------------------------------------------------------

@dataclass
class SoundtrackNode:
    """An official soundtrack release (album / OST)."""
    soundtrack_id:  str
    title:          str
    game_id:        str | None       = None
    year:           int | None       = None
    label:          str | None       = None   # record label
    catalog_number: str | None       = None
    disc_count:     int | None       = None
    track_count:    int | None       = None
    format:         str | None       = None   # "CD", "Digital", "Vinyl"
    composers:      list[str]        = field(default_factory=list)
    external_ids:   dict[str, str]   = field(default_factory=dict)
    # Keys: "vgmdb", "musicbrainz", "discogs", "spotify_album"

    def to_dict(self) -> dict[str, Any]:
        return {
            "soundtrack_id":  self.soundtrack_id,
            "title":          self.title,
            "game_id":        self.game_id,
            "year":           self.year,
            "label":          self.label,
            "catalog_number": self.catalog_number,
            "disc_count":     self.disc_count,
            "track_count":    self.track_count,
            "format":         self.format,
            "composers":      self.composers,
            "external_ids":   self.external_ids,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SoundtrackNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class StudioNode:
    """A game development or music studio."""
    studio_id:      str
    name:           str
    country:        str | None       = None
    founded_year:   int | None       = None
    dissolved_year: int | None       = None
    parent_company: str | None       = None
    studio_type:    str | None       = None  # "developer", "publisher", "sound_house"
    notable_series: list[str]        = field(default_factory=list)
    external_ids:   dict[str, str]   = field(default_factory=dict)
    # Keys: "wikidata", "wikipedia", "musicbrainz_label"

    def to_dict(self) -> dict[str, Any]:
        return {
            "studio_id":      self.studio_id,
            "name":           self.name,
            "country":        self.country,
            "founded_year":   self.founded_year,
            "dissolved_year": self.dissolved_year,
            "parent_company": self.parent_company,
            "studio_type":    self.studio_type,
            "notable_series": self.notable_series,
            "external_ids":   self.external_ids,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StudioNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class PlatformNode:
    """A hardware platform / console."""
    platform_id:    str
    name:           str
    manufacturer:   str | None       = None
    release_year:   int | None       = None
    cpu:            str | None       = None
    sound_chips:    list[str]        = field(default_factory=list)  # e.g. ["YM2612", "SN76489"]
    external_ids:   dict[str, str]   = field(default_factory=dict)
    # Keys: "wikidata", "wikipedia"

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_id":   self.platform_id,
            "name":          self.name,
            "manufacturer":  self.manufacturer,
            "release_year":  self.release_year,
            "cpu":           self.cpu,
            "sound_chips":   self.sound_chips,
            "external_ids":  self.external_ids,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PlatformNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SoundDriverNode:
    """A sound driver / sound engine used in a game or on a platform."""
    driver_id:      str
    name:           str
    platform:       str | None       = None   # platform_id
    developer:      str | None       = None
    games_using:    list[str]        = field(default_factory=list)  # game_ids
    chips:          list[str]        = field(default_factory=list)  # supported chips
    features:       list[str]        = field(default_factory=list)  # capabilities
    notes:          str | None       = None
    external_ids:   dict[str, str]   = field(default_factory=dict)
    # Keys: "vgmpf", "sega_retro", "github"

    def to_dict(self) -> dict[str, Any]:
        return {
            "driver_id":   self.driver_id,
            "name":        self.name,
            "platform":    self.platform,
            "developer":   self.developer,
            "games_using": self.games_using,
            "chips":       self.chips,
            "features":    self.features,
            "notes":       self.notes,
            "external_ids": self.external_ids,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SoundDriverNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Machine Learned / Analytical Types
# ---------------------------------------------------------------------------

@dataclass
class SoundChipNode:
    """A sound chip specification."""
    chip_id:          str
    name:             str
    manufacturer:     str | None       = None
    release_year:     int | None       = None
    synthesis_type:   str | None       = None
    channel_count:    int | None       = None
    operator_count:   int | None       = None
    clock_rate:       int | None       = None
    algorithm_count:  int | None       = None
    voice_limit:      int | None       = None
    register_layout:  dict[str, Any]   = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SoundChipNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MotifNode:
    """A recurring musical motif."""
    motif_id:         str
    interval_pattern: list[int]      = field(default_factory=list)
    rhythmic_pattern: list[float]    = field(default_factory=list)
    motif_length:     int | None     = None
    tonal_context:    str | None     = None

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MotifNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MotifRelationshipNode:
    """A transformation relationship between two motifs."""
    relationship_id:          str
    source_motif:             str
    target_motif:             str
    relationship_type:        str
    similarity_score:         float
    transformation_description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MotifRelationshipNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MotifLineageNode:
    """An evolutionary path of motif transformation."""
    lineage_id:     str
    motif_sequence: list[str] = field(default_factory=list)
    lineage_length: int | None = None
    occurrence_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MotifLineageNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MusicalPatternNode:
    """A broader structural musical pattern."""
    pattern_id:       str
    pattern_type:     str | None     = None
    structure:        list[str]      = field(default_factory=list)
    harmonic_context: str | None     = None
    tempo_context:    str | None     = None

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MusicalPatternNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ArtistStyleVectorNode:
    """A learned stylistic fingerprint of an artist."""
    vector_id:                       str
    melodic_interval_distribution:   dict[str, float] = field(default_factory=dict)
    rhythmic_signature_distribution: dict[str, float] = field(default_factory=dict)
    harmonic_profile:                dict[str, float] = field(default_factory=dict)
    motif_clusters:                  list[str]        = field(default_factory=list)
    spectral_profile:                dict[str, float] = field(default_factory=dict)
    dynamic_profile:                 dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ArtistStyleVectorNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ListenerNode:
    """A user or listener profile."""
    listener_id:        str
    name:               str | None       = None
    library_size:       int | None       = None
    analysis_timestamp: str | None       = None

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ListenerNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ListenerTasteVectorNode:
    """A learned stylistic preference vector of a listener."""
    vector_id:                       str
    melodic_interval_distribution:   dict[str, float] = field(default_factory=dict)
    rhythmic_density_profile:        dict[str, float] = field(default_factory=dict)
    syncopation_preference:          float | None     = None
    harmonic_tension_profile:        dict[str, float] = field(default_factory=dict)
    motif_family_distribution:       dict[str, float] = field(default_factory=dict)
    spectral_energy_profile:         dict[str, float] = field(default_factory=dict)
    dynamic_profile:                 dict[str, float] = field(default_factory=dict)
    structural_preference_profile:   dict[str, float] = field(default_factory=dict)
    # Derived metrics
    motif_cluster_affinity:          float | None     = None
    entropy_preference:              float | None     = None
    spectral_centroid_bias:          float | None     = None
    rhythmic_complexity_bias:        float | None     = None
    lineage_affinity:                float | None     = None
    motif_variation_preference:      float | None     = None

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ListenerTasteVectorNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

# ---------------------------------------------------------------------------
# S3K seed: platform + sound driver
# ---------------------------------------------------------------------------

S3K_PLATFORM = PlatformNode(
    platform_id="sega_genesis",
    name="Sega Genesis / Mega Drive",
    manufacturer="Sega",
    release_year=1988,
    cpu="Motorola 68000 + Zilog Z80",
    sound_chips=["YM2612", "SN76489"],
    external_ids={
        "wikidata":  "Q152763",
        "wikipedia": "Mega_Drive",
    },
)

S3K_SOUND_DRIVER = SoundDriverNode(
    driver_id="smps_z80_s3k",
    name="SMPS Z80 (Sonic 3 & Knuckles variant)",
    platform="sega_genesis",
    developer="Yoshiaki Kashima / Sega Sound Team",
    games_using=["sonic_3_and_knuckles"],
    chips=["YM2612", "SN76489"],
    features=[
        "DAC sample playback",
        "FM synthesis (6 channels)",
        "PSG (4 channels)",
        "PCM drums",
        "loop support with offset",
    ],
    notes="Custom variant of SMPS written for S3K by Yoshiaki 'Milpo' Kashima.",
    external_ids={
        "vgmpf":      "SMPS",
        "sega_retro": "SMPS",
        "github":     "andlabs/s2-sound-driver",
    },
)

S3K_STUDIO_SEGA = StudioNode(
    studio_id="sega",
    name="Sega",
    country="Japan",
    founded_year=1965,
    studio_type="developer_publisher",
    notable_series=["Sonic", "Streets of Rage", "Phantasy Star"],
    external_ids={
        "wikidata":  "Q122741",
        "wikipedia": "Sega",
    },
)

S3K_SOUNDTRACK = SoundtrackNode(
    soundtrack_id="s3k_ost",
    title="Sonic the Hedgehog 3 Original Soundtrack",
    game_id="sonic_3_and_knuckles",
    year=1994,
    label="Sega",
    format="CD",
    composers=[
        "masayuki_nagao", "tatsuyuki_maeda", "jun_senoue",
        "yoshiaki_kashima", "brad_buxer",
    ],
    external_ids={
        "vgmdb": "359",
    },
)
