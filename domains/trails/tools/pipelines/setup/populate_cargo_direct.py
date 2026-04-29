#!/usr/bin/env python3
"""
Trails Database — Direct Cargo table population.
Bypasses MediaWiki hook mechanism and writes directly to cargo__ tables.
Use this when Cargo's PageSaveComplete hook fails to commit (MW 1.41 + Cargo 3.4.x compat issue).

Data is read from wiki page definitions (hardcoded here for the vertical slice).
When scaling to bulk, read from trails.db entity_registry and appearance_registry.
"""

import subprocess
import json

SUDO_PASS = "Helix"

def sql(query):
    """Run a SQL query against trails_wiki via sudo mariadb."""
    result = subprocess.run(
        ["bash", "-c", f"echo '{SUDO_PASS}' | sudo -S mariadb trails_wiki -e \"{query}\" 2>/dev/null"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def sql_file(filepath):
    result = subprocess.run(
        ["bash", "-c", f"echo '{SUDO_PASS}' | sudo -S bash -c 'mariadb trails_wiki < {filepath}' 2>/dev/null"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Get page IDs from wiki for known pages
# ---------------------------------------------------------------------------

def get_page_id(page_title):
    title_escaped = page_title.replace(" ", "_").replace("'", "\\'")
    out = sql(f"SELECT page_id FROM page WHERE page_title='{title_escaped}' AND page_namespace=0 LIMIT 1;")
    lines = [l for l in out.split("\n") if l.strip() and l.strip() != "page_id"]
    return int(lines[0]) if lines else None


# ---------------------------------------------------------------------------
# Data to insert
# ---------------------------------------------------------------------------

CHARACTERS = [
    {
        "entity_id": "char:estelle_bright",
        "name_en": "Estelle Bright",
        "name_ja": "エステル・ブライト",
        "aliases": "",
        "arc_first_appearance": "Sky",
        "spoiler_band": 14,
        "voice_jp": "Kanae Itō",
        "voice_en": "Brittney Karbowski",
        "page_title": "Estelle Bright",
    }
]

APPEARANCES = [
    {"entity_id": "char:estelle_bright", "media_id": "media:trails_sky_fc",        "role": "protagonist", "spoiler_band": 10, "page_title": "Estelle Bright"},
    {"entity_id": "char:estelle_bright", "media_id": "media:trails_sky_sc",        "role": "protagonist", "spoiler_band": 12, "page_title": "Estelle Bright"},
    {"entity_id": "char:estelle_bright", "media_id": "media:trails_sky_3rd",       "role": "supporting",  "spoiler_band": 14, "page_title": "Estelle Bright"},
    {"entity_id": "char:estelle_bright", "media_id": "media:trails_from_zero",     "role": "supporting",  "spoiler_band": 20, "page_title": "Estelle Bright"},
    {"entity_id": "char:estelle_bright", "media_id": "media:trails_to_azure",      "role": "supporting",  "spoiler_band": 22, "page_title": "Estelle Bright"},
    {"entity_id": "char:estelle_bright", "media_id": "media:trails_into_reverie",  "role": "supporting",  "spoiler_band": 65, "page_title": "Estelle Bright"},
]

MEDIA_ENTRIES = [
    {
        "media_id": "media:trails_sky_fc",
        "title_en": "Trails in the Sky FC",
        "title_ja": "英雄伝説 空の軌跡 FC",
        "media_type": "game",
        "arc": "Sky",
        "release_year": 2004,
        "platform": "PC|PSP|PS3|Vita",
        "developer": "Nihon Falcom",
        "publisher": "XSEED Games",
        "spoiler_band": 10,
        "page_title": "Trails in the Sky FC",
    }
]

SOURCE_RECORDS = [
    {"source_id": "wiki:kiseki_fandom",          "source_url": "https://kiseki.fandom.com",                          "trust_tier": 2, "language": "en", "source_type": "wiki", "page_title": "Trails Database:Sources"},
    {"source_id": "wiki:ja_wikipedia_series",    "source_url": "https://ja.wikipedia.org/wiki/英雄伝説_軌跡シリーズ", "trust_tier": 1, "language": "ja", "source_type": "wiki", "page_title": "Trails Database:Sources"},
    {"source_id": "wiki:ja_wikipedia_characters","source_url": "https://ja.wikipedia.org/wiki/英雄伝説_軌跡シリーズの登場人物", "trust_tier": 1, "language": "ja", "source_type": "wiki", "page_title": "Trails Database:Sources"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(v):
    """Escape a string value for SQL."""
    if v is None:
        return "NULL"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"

def get_page_namespace(title):
    """Return namespace int for a page title (namespace:title format)."""
    if ":" in title:
        prefix = title.split(":")[0]
        ns_map = {"Template": 10, "Module": 828, "Form": 104, "Draft": 102, "Metadata": 100, "Trails Database": 4}
        return ns_map.get(prefix, 0)
    return 0

def resolve_page_id(title):
    """Look up page_id from MariaDB."""
    ns = get_page_namespace(title)
    if ":" in title and ns != 0:
        page_name = title.split(":", 1)[1]
    else:
        page_name = title
    page_name_escaped = page_name.replace("_", " ").replace("'", "\\'")
    out = sql(f"SELECT page_id FROM page WHERE page_title='{page_name_escaped.replace(' ', '_')}' AND page_namespace={ns} LIMIT 1;")
    lines = [l for l in out.split("\n") if l.strip() and l.strip() != "page_id"]
    if lines:
        return int(lines[0]), ns, page_name.replace(" ", "_")
    return None, ns, page_name.replace(" ", "_")


# ---------------------------------------------------------------------------
# Insert functions
# ---------------------------------------------------------------------------

def populate_characters():
    print("Populating cargo__Character...")
    sql("TRUNCATE TABLE cargo__Character;")
    for c in CHARACTERS:
        page_id, ns, pname = resolve_page_id(c["page_title"])
        row = (
            f"INSERT INTO cargo__Character "
            f"(_pageID, _pageName, _pageTitle, _pageNamespace, "
            f"entity_id, name_en, name_ja, aliases, arc_first_appearance, spoiler_band, voice_jp, voice_en) "
            f"VALUES ({page_id or 'NULL'}, {esc(pname)}, {esc(pname)}, {ns}, "
            f"{esc(c['entity_id'])}, {esc(c['name_en'])}, {esc(c['name_ja'])}, "
            f"{esc(c['aliases'])}, {esc(c['arc_first_appearance'])}, {c['spoiler_band']}, "
            f"{esc(c['voice_jp'])}, {esc(c['voice_en'])});"
        )
        sql(row)
        print(f"  inserted: {c['entity_id']}")


def populate_appearances():
    print("Populating cargo__Appearance...")
    sql("TRUNCATE TABLE cargo__Appearance;")
    for a in APPEARANCES:
        page_id, ns, pname = resolve_page_id(a["page_title"])
        row = (
            f"INSERT INTO cargo__Appearance "
            f"(_pageID, _pageName, _pageTitle, _pageNamespace, "
            f"entity_id, media_id, role, spoiler_band) "
            f"VALUES ({page_id or 'NULL'}, {esc(pname)}, {esc(pname)}, {ns}, "
            f"{esc(a['entity_id'])}, {esc(a['media_id'])}, {esc(a['role'])}, {a['spoiler_band']});"
        )
        sql(row)
        print(f"  inserted: {a['entity_id']} → {a['media_id']}")


def populate_media():
    print("Populating cargo__MediaEntry...")
    sql("TRUNCATE TABLE cargo__MediaEntry;")
    for m in MEDIA_ENTRIES:
        page_id, ns, pname = resolve_page_id(m["page_title"])
        row = (
            f"INSERT INTO cargo__MediaEntry "
            f"(_pageID, _pageName, _pageTitle, _pageNamespace, "
            f"media_id, title_en, title_ja, media_type, arc, release_year, platform, developer, publisher, spoiler_band) "
            f"VALUES ({page_id or 'NULL'}, {esc(pname)}, {esc(pname)}, {ns}, "
            f"{esc(m['media_id'])}, {esc(m['title_en'])}, {esc(m['title_ja'])}, {esc(m['media_type'])}, "
            f"{esc(m['arc'])}, {m['release_year']}, {esc(m['platform'])}, {esc(m['developer'])}, "
            f"{esc(m['publisher'])}, {m['spoiler_band']});"
        )
        sql(row)
        print(f"  inserted: {m['media_id']}")


def populate_sources():
    print("Populating cargo__SourceRecord...")
    sql("TRUNCATE TABLE cargo__SourceRecord;")
    for s in SOURCE_RECORDS:
        page_id, ns, pname = resolve_page_id(s["page_title"])
        row = (
            f"INSERT INTO cargo__SourceRecord "
            f"(_pageID, _pageName, _pageTitle, _pageNamespace, "
            f"source_id, source_url, trust_tier, language, source_type, last_fetched_at) "
            f"VALUES ({page_id or 'NULL'}, {esc(pname)}, {esc(pname)}, {ns}, "
            f"{esc(s['source_id'])}, {esc(s['source_url'])}, {s['trust_tier']}, "
            f"{esc(s['language'])}, {esc(s['source_type'])}, NULL);"
        )
        sql(row)
        print(f"  inserted: {s['source_id']}")


def verify():
    print("\nVerification:")
    for tbl, field in [("Character","entity_id"), ("Appearance","entity_id"), ("MediaEntry","media_id"), ("SourceRecord","source_id")]:
        out = sql(f"SELECT COUNT(*) FROM cargo__{tbl};")
        count = [l for l in out.split("\n") if l.strip() and "COUNT" not in l]
        print(f"  cargo__{tbl}: {count[0] if count else '?'} rows")


if __name__ == "__main__":
    populate_characters()
    populate_appearances()
    populate_media()
    populate_sources()
    verify()
