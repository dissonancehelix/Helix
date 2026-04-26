"""
build_composer_entities.py — Build/update composer entity files from live data
==============================================================================

Reads:
  - codex/library/music/.field_index.json     → library_artist_keys, track_ids,
                                                 by_sound_team for org seeding
  - domains/music/artifacts/analysis/s3k_composer_fingerprints.json → style_signature
  - codex/atlas/music/artists/*.json          → existing entities (preserved on update)

Writes:
  - codex/atlas/music/artists/<slug>.json       one file per composer
  - codex/atlas/music/soundteams/<slug>.json    one file per sound team org
  - codex/atlas/entities/registry.json          HSL EntityResolver registry

Schema is Wikidata-influenced:
  - Every entity has a stable ID (music.composer:<slug>, music.soundteam:<slug>)
  - Relationships are typed with confidence (MEMBER_OF, COMPOSED)
  - library block caches hw_seq_track_ids so ANALYZE COMPOSER bypasses album walk
  - by_sound_team index is seeded from the %Sound Team% Foobar tag field

Run:
    python codex/atlas/music/build_composer_entities.py
    python codex/atlas/music/build_composer_entities.py --composers "Miyoko Takaoka"
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)

FIELD_INDEX    = ROOT / "codex" / "library" / "music" / ".field_index.json"
FINGERPRINTS   = ROOT / "domains" / "language" / "artifacts" / "analysis" / "s3k_composer_fingerprints.json"
ARTISTS_DIR    = ROOT / "codex" / "atlas" / "music" / "artists"
SOUNDTEAMS_DIR = ROOT / "codex" / "atlas" / "music" / "soundteams"
REGISTRY_PATH  = ROOT / "codex" / "atlas" / "entities" / "registry.json"

FORMAT_CATEGORY = {
    "vgm": "hardware_log", "vgz": "hardware_log", "spc": "hardware_log",
    "nsf": "hardware_log", "nsfe": "hardware_log", "gbs": "hardware_log",
    "hes": "hardware_log", "gym": "hardware_log", "s98": "hardware_log",
    "psf": "sequence", "psf2": "sequence", "dsf": "sequence",
    "ssf": "sequence", "usf": "sequence", "gsf": "sequence",
    "ncsf": "sequence", "mid": "sequence",
    "mini2sf": "sequence", "miniusf": "sequence",
    "minincsf": "sequence", "minigsf": "sequence", "minipsf": "sequence",
    "mp3": "audio", "flac": "audio", "opus": "audio", "ogg": "audio",
    "m4a": "audio", "aac": "audio", "wav": "audio", "wma": "audio",
}

# ---------------------------------------------------------------------------
# Composer seed data
# ---------------------------------------------------------------------------
COMPOSER_SEED: dict[str, dict] = {
    "Tatsuyuki Maeda": {
        "slug": "tatsuyuki_maeda",
        "aliases": ["Johnny Maeda", "Ryunosuke"],
        "description": "Sega Sound Team composer; primary Sonic 3D Blast composer",
        "affiliations": [{"org": "music.soundteam:sega_sound_team", "role": "composer"}],
    },
    "Sachio Ogawa": {
        "slug": "sachio_ogawa",
        "aliases": [],
        "description": "Sega composer; early Mega Drive and Master System era",
        "affiliations": [{"org": "music.soundteam:sega_sound_team", "role": "composer"}],
    },
    "Tomonori Sawada": {
        "slug": "tomonori_sawada",
        "aliases": [],
        "description": "Sega composer; collaborated with Sachio Ogawa",
        "affiliations": [{"org": "music.soundteam:sega_sound_team", "role": "composer"}],
    },
    "Masaru Setsumaru": {
        "slug": "masaru_setsumaru",
        "aliases": [],
        "description": "Sega Sound Team; programmer/arranger on Sonic 3 & Knuckles",
        "affiliations": [{"org": "music.soundteam:sega_sound_team", "role": "programmer_arranger"}],
    },
    "Jun Senoue": {
        "slug": "jun_senoue",
        "aliases": [],
        "description": "Sega Sound Team; composer on S3K bonus stages, later Sonic Adventure series",
        "affiliations": [{"org": "music.soundteam:sega_sound_team", "role": "composer"}],
    },
    "Masayuki Nagao": {
        "slug": "masayuki_nagao",
        "aliases": ["N.GEE"],
        "description": "Sega Sound Team; produced/arranged half of S3K, composer on Sonic Game Gear titles",
        "affiliations": [{"org": "music.soundteam:sega_sound_team", "role": "composer_producer"}],
    },
    "Yoshiaki Kashima": {
        "slug": "yoshiaki_kashima",
        "aliases": [],
        "description": "Sega Sound Team; programmer/composer; Blue Spheres confirmed",
        "affiliations": [{"org": "music.soundteam:sega_sound_team", "role": "programmer_composer"}],
    },
    "Masanori Hikichi": {
        "slug": "masanori_hikichi",
        "aliases": [],
        "description": "Cube Corp composer; sequenced S3K SMPS data; composed Gley Lancer, Terranigma",
        "affiliations": [{"org": "music.soundteam:cube_corp", "role": "composer_sequencer"}],
    },
    "Miyoko Takaoka": {
        "slug": "miyoko_takaoka",
        "aliases": ["Takaoka"],
        "description": "Cube Corp composer; confirmed Marble Garden Zone; Terranigma, America Oudan Ultra Quiz",
        "affiliations": [{"org": "music.soundteam:cube_corp", "role": "composer"}],
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    s = str(text).lower().strip()
    s = re.sub(r"['\u2019\u2018`]", "", s)
    s = re.sub(r"[\s\-\/;,:\.&!?\(\)\[\]\{\}]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_") or "unknown"


def load_field_index() -> dict:
    with open(FIELD_INDEX, encoding="utf-8") as f:
        return json.load(f)


def load_fingerprints() -> dict[str, dict]:
    if not FINGERPRINTS.exists():
        return {}
    with open(FINGERPRINTS, encoding="utf-8") as f:
        d = json.load(f)
    return {c["composer"]: c for c in d.get("composers", [])}


def collect_library_data(name: str, idx: dict) -> dict:
    by_artist  = idx.get("by_artist", {})
    source_map = idx.get("source_map", {})
    by_fmt     = idx.get("by_fmt_cat", {})
    hw_seq_ids = set(by_fmt.get("hardware_log", [])) | set(by_fmt.get("sequence", []))

    needle = name.lower()
    matching_keys: list[str] = []
    all_ids: set[str] = set()
    for artist_key, tids in by_artist.items():
        if needle in artist_key:
            matching_keys.append(artist_key)
            all_ids.update(tids)

    hw_seq = sorted(all_ids & hw_seq_ids)

    platform_counts: dict[str, int] = {}
    for t_id in hw_seq:
        src = source_map.get(t_id, "")
        ext = Path(src).suffix.lstrip(".").lower() if src else ""
        platform = "spc" if ext == "spc" else "vgm_vgz" if ext in ("vgm", "vgz") else ext or "?"
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    return {
        "artist_keys":      sorted(matching_keys),
        "track_count":      len(all_ids),
        "hw_seq_count":     len(hw_seq),
        "audio_count":      len(all_ids) - len(hw_seq),
        "hw_seq_track_ids": hw_seq,
        "platform_counts":  platform_counts,
    }


def collect_sound_team_data(team_slug: str, idx: dict) -> dict:
    """Collect track IDs for a sound team from the by_sound_team index."""
    by_sound_team = idx.get("by_sound_team", {})
    source_map    = idx.get("source_map", {})
    by_fmt        = idx.get("by_fmt_cat", {})
    hw_seq_ids    = set(by_fmt.get("hardware_log", [])) | set(by_fmt.get("sequence", []))

    needle = team_slug.lower().replace("_", " ")
    matching_keys: list[str] = []
    all_ids: set[str] = set()
    for team_key, tids in by_sound_team.items():
        if needle in team_key or team_key in needle:
            matching_keys.append(team_key)
            all_ids.update(tids)

    hw_seq = sorted(all_ids & hw_seq_ids)

    platform_counts: dict[str, int] = {}
    for t_id in hw_seq:
        src = source_map.get(t_id, "")
        ext = Path(src).suffix.lstrip(".").lower() if src else ""
        platform = "spc" if ext == "spc" else "vgm_vgz" if ext in ("vgm", "vgz") else ext or "?"
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    return {
        "sound_team_keys": sorted(matching_keys),
        "track_count":     len(all_ids),
        "hw_seq_count":    len(hw_seq),
        "platform_counts": platform_counts,
        "hw_seq_track_ids": hw_seq,
    }


def style_signature_from_fingerprint(fp: dict) -> dict:
    SKIP = {"composer", "track_count", "progression_fingerprint", "melodic_contour",
            "dynamic_arc", "fm_patch_catalog", "spc_brr_catalog"}
    return {k: v for k, v in fp.items() if k not in SKIP and not isinstance(v, list)}


def build_composer_entity(name: str, seed: dict, lib: dict, fp: dict | None) -> dict:
    entity: dict = {
        "entity_id":    f"music.composer:{seed['slug']}",
        "entity_type":  "COMPOSER",
        "label":        name,
        "aliases":      seed.get("aliases", []),
        "description":  seed.get("description", ""),
        "affiliations": seed.get("affiliations", []),
        "library": {
            "artist_keys":      lib["artist_keys"],
            "track_count":      lib["track_count"],
            "hw_seq_count":     lib["hw_seq_count"],
            "audio_count":      lib["audio_count"],
            "platform_counts":  lib["platform_counts"],
            "hw_seq_track_ids": lib["hw_seq_track_ids"],
        },
    }
    if fp:
        entity["style_signature"] = style_signature_from_fingerprint(fp)
        entity["style_signature"]["calibration_track_count"] = fp.get("track_count", 0)
        entity["style_signature"]["source"] = FINGERPRINTS.relative_to(ROOT).as_posix()
    return entity


def build_soundteam_entity(slug: str, name: str, description: str, lib: dict) -> dict:
    return {
        "entity_id":   f"music.soundteam:{slug}",
        "entity_type": "SOUNDTEAM",
        "label":       name,
        "aliases":     [],
        "description": description,
        "library": {
            "sound_team_keys":  lib["sound_team_keys"],
            "track_count":      lib["track_count"],
            "hw_seq_count":     lib["hw_seq_count"],
            "platform_counts":  lib["platform_counts"],
            "hw_seq_track_ids": lib["hw_seq_track_ids"],
        },
    }


# ---------------------------------------------------------------------------
# Registry writer
# ---------------------------------------------------------------------------

SOUNDTEAM_SEED = {
    "sega_sound_team": {
        "name": "Sega Sound Team",
        "description": "Sega internal music division; Mega Drive / Game Gear era",
    },
    "cube_corp": {
        "name": "Cube Corp",
        "description": "External contractor for Sega; composed and sequenced Sonic 3 & Knuckles tracks",
    },
}


def build_registry(composer_entities: list[dict], soundteam_entities: list[dict]) -> dict:
    """Build registry.json entries from built entity dicts."""
    entries = []

    for e in composer_entities:
        slug = e["entity_id"].split(":")[-1]
        relationships = [
            {"relation": "MEMBER_OF", "target_id": aff["org"], "confidence": 1.0}
            for aff in e.get("affiliations", [])
        ]
        entries.append({
            "id":            e["entity_id"],
            "type":          "Composer",
            "name":          e["label"],
            "label":         e["label"],
            "description":   e.get("description", ""),
            "metadata": {
                "aliases":          e.get("aliases", []),
                "hw_seq_count":     e.get("library", {}).get("hw_seq_count", 0),
                "platform_counts":  e.get("library", {}).get("platform_counts", {}),
                "scale_mode":       e.get("style_signature", {}).get("scale_mode", ""),
                "source":           "build_composer_entities.py",
                "source_stage":     "entity_build",
                "source_artifact":  f"codex/atlas/music/artists/{slug}.json",
                "extraction_method": "field_index_query",
            },
            "external_ids":  {},
            "relationships": relationships,
        })

    for e in soundteam_entities:
        slug = e["entity_id"].split(":")[-1]
        entries.append({
            "id":          e["entity_id"],
            "type":        "SoundTeam",
            "name":        e["label"],
            "label":       e["label"],
            "description": e.get("description", ""),
            "metadata": {
                "hw_seq_count":    e.get("library", {}).get("hw_seq_count", 0),
                "platform_counts": e.get("library", {}).get("platform_counts", {}),
                "source":          "build_composer_entities.py",
                "source_stage":    "entity_build",
                "source_artifact": f"codex/atlas/music/soundteams/{slug}.json",
                "extraction_method": "field_index_query",
            },
            "external_ids":  {},
            "relationships": [],
        })

    return {
        "_meta": {"entity_count": len(entries)},
        "entities": entries,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(target_names: list[str] | None = None) -> None:
    print("Loading field index...")
    idx = load_field_index()
    print(f"  {len(idx.get('source_map',{})):,} tracks in source_map")
    st_count = len(idx.get("by_sound_team", {}))
    print(f"  {st_count} sound team keys in index{' (run --stage index to populate)' if st_count == 0 else ''}")

    print("Loading fingerprints...")
    fps = load_fingerprints()
    print(f"  {len(fps)} composer fingerprints")

    ARTISTS_DIR.mkdir(parents=True, exist_ok=True)
    SOUNDTEAMS_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ── Composers ──────────────────────────────────────────────────────────
    names = target_names or list(COMPOSER_SEED.keys())
    composer_entities: list[dict] = []
    for name in names:
        seed = COMPOSER_SEED.get(name)
        if not seed:
            print(f"  SKIP: {name} — not in seed table")
            continue
        lib    = collect_library_data(name, idx)
        fp     = fps.get(name)
        entity = build_composer_entity(name, seed, lib, fp)
        composer_entities.append(entity)

        out_path = ARTISTS_DIR / f"{seed['slug']}.json"
        out_path.write_text(json.dumps(entity, indent=2, ensure_ascii=False), encoding="utf-8")

        mode_note = f"  mode={entity['style_signature']['scale_mode']}" if fp else ""
        print(f"  {name}: {lib['hw_seq_count']} hw/seq {lib['platform_counts']}{mode_note}")

    # ── Sound teams ────────────────────────────────────────────────────────
    soundteam_entities: list[dict] = []
    for slug, seed in SOUNDTEAM_SEED.items():
        lib    = collect_sound_team_data(slug, idx)
        entity = build_soundteam_entity(slug, seed["name"], seed["description"], lib)
        soundteam_entities.append(entity)

        out_path = SOUNDTEAMS_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(entity, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {seed['name']}: {lib['hw_seq_count']} hw/seq via sound_team tag")

    # ── Registry ───────────────────────────────────────────────────────────
    registry = build_registry(composer_entities, soundteam_entities)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  registry.json: {registry['_meta']['entity_count']} entities → {REGISTRY_PATH}")
    print(f"Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build composer/soundteam entity files and registry")
    parser.add_argument("--composers", nargs="+", metavar="NAME",
                        help="Composer names to build (default: all 9 S3K composers)")
    args = parser.parse_args()
    main(args.composers)
