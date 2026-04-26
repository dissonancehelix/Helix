#!/usr/bin/env python3
"""
Trails Database — Bulk Cargo population from trails.db.
Reads from retrieval/index/trails.db and directly INSERTs into cargo__ tables.

Entity mapping:
  entity_type='character'          → cargo__Character (583)
  entity_type='faction'            → cargo__Faction (116)
  entity_type='location'           → cargo__Location (50)
  entity_type='staff'              → cargo__Staff (179)
  entity_type in (concept,quest,   → cargo__Entity (4222)
                  item,main_game,
                  spin_off,anime,
                  manga,drama_cd)
  media_registry                   → cargo__MediaEntry (30)
  appearance_registry              → cargo__Appearance (6182)
  source_registry                  → cargo__SourceRecord (37)
"""

import sqlite3
import subprocess
import sys

TRAILS_DB = "C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db"
DB_USER = "wiki_user"
DB_PASS = "trailsdb2026"
DB_NAME = "trails_wiki"
BATCH_SIZE = 200

# ---------------------------------------------------------------------------
# SQL helpers — stdin pipe to mariadb handles Unicode correctly
# ---------------------------------------------------------------------------

def sql(query):
    """Execute SQL via stdin pipe (handles Unicode; no sudo needed)."""
    result = subprocess.run(
        ["bash", "-c", f"mariadb -u {DB_USER} -p{DB_PASS} {DB_NAME}"],
        input=query, capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        print(f"  SQL ERROR (rc={result.returncode}): {result.stderr[:200]}", file=sys.stderr)
    return result.stdout.strip()

def sql_batch(statements):
    """Run a batch of SQL statements via a single connection."""
    sql("\n".join(statements))

def esc(v):
    if v is None:
        return "NULL"
    s = str(v).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{s}'"

def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# ---------------------------------------------------------------------------
# Populate cargo__Character
# ---------------------------------------------------------------------------

def populate_characters(conn):
    print("Populating cargo__Character...")
    sql("TRUNCATE TABLE cargo__Character;")
    c = conn.cursor()
    c.execute("""
        SELECT entity_id, english_display_name, japanese_name, aliases
        FROM entity_registry
        WHERE entity_type = 'character'
        ORDER BY entity_id
    """)
    rows = c.fetchall()

    # Get spoiler_band from appearance_registry (min spoiler_band per entity = earliest game)
    sb_map = {}
    c.execute("""
        SELECT entity_id, MIN(spoiler_band)
        FROM appearance_registry
        GROUP BY entity_id
    """)
    for eid, sb in c.fetchall():
        sb_map[eid] = sb

    # Get arc_first_appearance from media_registry via appearance_registry
    arc_map = {}
    c.execute("""
        SELECT a.entity_id, m.internal_chronology
        FROM appearance_registry a
        JOIN media_registry m ON a.media_id = m.media_id
        WHERE a.debut_flag = 1
    """)
    for eid, arc in c.fetchall():
        if eid not in arc_map and arc:
            arc_map[eid] = arc

    stmts = []
    for entity_id, name_en, name_ja, aliases in rows:
        sb = sb_map.get(entity_id, 20)
        arc = arc_map.get(entity_id, None)
        stmt = (
            f"INSERT IGNORE INTO cargo__Character (_pageName, _pageTitle, _pageNamespace, entity_id, name_en, name_ja, aliases, arc_first_appearance, spoiler_band) "
            f"VALUES ({esc(entity_id)}, {esc(entity_id)}, 0, {esc(entity_id)}, {esc(name_en)}, {esc(name_ja)}, {esc(aliases)}, {esc(arc)}, {sb});"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} characters")


# ---------------------------------------------------------------------------
# Populate cargo__MediaEntry
# ---------------------------------------------------------------------------

def populate_media(conn):
    print("Populating cargo__MediaEntry...")
    sql("TRUNCATE TABLE cargo__MediaEntry;")
    c = conn.cursor()
    c.execute("""
        SELECT media_id, media_type, english_title, japanese_title,
               internal_chronology, release_date_jp, publisher,
               is_main_series, spoiler_band
        FROM media_registry
        ORDER BY release_chronology
    """)
    rows = c.fetchall()

    stmts = []
    for media_id, media_type, title_en, title_ja, arc, release_date, publisher, is_main, sb in rows:
        # Extract year from release_date (e.g. "June 24, 2004" → 2004)
        release_year = None
        if release_date:
            import re
            m = re.search(r'\b(19|20)\d{2}\b', release_date)
            if m:
                release_year = int(m.group(0))
        stmt = (
            f"INSERT IGNORE INTO cargo__MediaEntry (_pageName, _pageTitle, _pageNamespace, media_id, title_en, title_ja, media_type, arc, release_year, developer, publisher, spoiler_band) "
            f"VALUES ({esc(media_id)}, {esc(media_id)}, 0, {esc(media_id)}, {esc(title_en)}, {esc(title_ja)}, {esc(media_type)}, {esc(arc)}, "
            f"{'NULL' if release_year is None else release_year}, {'NULL'}, {esc(publisher)}, {sb});"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} media entries")


# ---------------------------------------------------------------------------
# Populate cargo__Appearance
# ---------------------------------------------------------------------------

def populate_appearances(conn):
    print("Populating cargo__Appearance...")
    sql("TRUNCATE TABLE cargo__Appearance;")
    c = conn.cursor()
    c.execute("""
        SELECT entity_id, media_id, appearance_type, spoiler_band
        FROM appearance_registry
        ORDER BY appearance_id
    """)
    rows = c.fetchall()

    stmts = []
    for entity_id, media_id, appearance_type, sb in rows:
        stmt = (
            f"INSERT IGNORE INTO cargo__Appearance (_pageName, _pageTitle, _pageNamespace, entity_id, media_id, role, spoiler_band) "
            f"VALUES ({esc(entity_id)}, {esc(entity_id)}, 0, {esc(entity_id)}, {esc(media_id)}, {esc(appearance_type)}, {sb or 20});"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} appearances")


# ---------------------------------------------------------------------------
# Populate cargo__SourceRecord
# ---------------------------------------------------------------------------

def populate_sources(conn):
    print("Populating cargo__SourceRecord...")
    sql("TRUNCATE TABLE cargo__SourceRecord;")
    c = conn.cursor()
    c.execute("""
        SELECT source_id, origin_url, trust_tier, language, source_class, last_fetched_at
        FROM source_registry
        ORDER BY source_id
    """)
    rows = c.fetchall()

    stmts = []
    for source_id, url, trust_tier, lang, source_class, fetched_at in rows:
        stmt = (
            f"INSERT IGNORE INTO cargo__SourceRecord (_pageName, _pageTitle, _pageNamespace, source_id, source_url, trust_tier, language, source_type, last_fetched_at) "
            f"VALUES ({esc(source_id)}, {esc(source_id)}, 0, {esc(source_id)}, {esc(url)}, {trust_tier or 2}, {esc(lang)}, {esc(source_class)}, {esc(fetched_at)});"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} sources")


# ---------------------------------------------------------------------------
# Populate cargo__Faction
# ---------------------------------------------------------------------------

def populate_factions(conn):
    print("Populating cargo__Faction...")
    sql("TRUNCATE TABLE cargo__Faction;")
    c = conn.cursor()
    c.execute("""
        SELECT entity_id, english_display_name, japanese_name
        FROM entity_registry
        WHERE entity_type = 'faction'
        ORDER BY entity_id
    """)
    rows = c.fetchall()

    # Spoiler band from appearance_registry
    sb_map = {}
    c.execute("SELECT entity_id, MIN(spoiler_band) FROM appearance_registry GROUP BY entity_id")
    for eid, sb in c.fetchall():
        sb_map[eid] = sb

    stmts = []
    for entity_id, name_en, name_ja in rows:
        sb = sb_map.get(entity_id, 20)
        stmt = (
            f"INSERT IGNORE INTO cargo__Faction (_pageName, _pageTitle, _pageNamespace, entity_id, name_en, name_ja, spoiler_band) "
            f"VALUES ({esc(entity_id)}, {esc(entity_id)}, 0, {esc(entity_id)}, {esc(name_en)}, {esc(name_ja)}, {sb});"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} factions")


# ---------------------------------------------------------------------------
# Populate cargo__Location
# ---------------------------------------------------------------------------

def populate_locations(conn):
    print("Populating cargo__Location...")
    sql("TRUNCATE TABLE cargo__Location;")
    c = conn.cursor()
    c.execute("""
        SELECT entity_id, english_display_name, japanese_name
        FROM entity_registry
        WHERE entity_type = 'location'
        ORDER BY entity_id
    """)
    rows = c.fetchall()

    sb_map = {}
    c.execute("SELECT entity_id, MIN(spoiler_band) FROM appearance_registry GROUP BY entity_id")
    for eid, sb in c.fetchall():
        sb_map[eid] = sb

    stmts = []
    for entity_id, name_en, name_ja in rows:
        sb = sb_map.get(entity_id, 20)
        stmt = (
            f"INSERT IGNORE INTO cargo__Location (_pageName, _pageTitle, _pageNamespace, entity_id, name_en, name_ja, spoiler_band) "
            f"VALUES ({esc(entity_id)}, {esc(entity_id)}, 0, {esc(entity_id)}, {esc(name_en)}, {esc(name_ja)}, {sb});"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} locations")


# ---------------------------------------------------------------------------
# Populate cargo__Staff
# ---------------------------------------------------------------------------

def populate_staff(conn):
    print("Populating cargo__Staff...")
    sql("TRUNCATE TABLE cargo__Staff;")
    c = conn.cursor()
    c.execute("""
        SELECT entity_id, english_display_name, japanese_name
        FROM entity_registry
        WHERE entity_type = 'staff'
        ORDER BY entity_id
    """)
    rows = c.fetchall()

    stmts = []
    for entity_id, name_en, name_ja in rows:
        stmt = (
            f"INSERT IGNORE INTO cargo__Staff (_pageName, _pageTitle, _pageNamespace, entity_id, name_en, name_ja, spoiler_band) "
            f"VALUES ({esc(entity_id)}, {esc(entity_id)}, 0, {esc(entity_id)}, {esc(name_en)}, {esc(name_ja)}, 0);"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} staff")


# ---------------------------------------------------------------------------
# Populate cargo__Entity (catch-all: concept, quest, item, + media sub-types)
# ---------------------------------------------------------------------------

CATCHALL_TYPES = ('concept', 'quest', 'item', 'main_game', 'spin_off', 'anime', 'manga', 'drama_cd')

def populate_entities(conn):
    print("Populating cargo__Entity (concept/quest/item/media-types)...")
    sql("TRUNCATE TABLE cargo__Entity;")
    c = conn.cursor()

    placeholders = ",".join(f"'{t}'" for t in CATCHALL_TYPES)
    c.execute(f"""
        SELECT entity_id, entity_type, english_display_name, japanese_name
        FROM entity_registry
        WHERE entity_type IN ({placeholders})
        ORDER BY entity_type, entity_id
    """)
    rows = c.fetchall()

    sb_map = {}
    c.execute("SELECT entity_id, MIN(spoiler_band) FROM appearance_registry GROUP BY entity_id")
    for eid, sb in c.fetchall():
        sb_map[eid] = sb

    stmts = []
    for entity_id, entity_type, name_en, name_ja in rows:
        sb = sb_map.get(entity_id, 20)
        stmt = (
            f"INSERT IGNORE INTO cargo__Entity (_pageName, _pageTitle, _pageNamespace, entity_id, entity_type, name_en, name_ja, spoiler_band) "
            f"VALUES ({esc(entity_id)}, {esc(entity_id)}, 0, {esc(entity_id)}, {esc(entity_type)}, {esc(name_en)}, {esc(name_ja)}, {sb});"
        )
        stmts.append(stmt)

    for batch in chunked(stmts, BATCH_SIZE):
        sql_batch(batch)

    print(f"  inserted: {len(rows)} entities")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify():
    print("\n=== Verification ===")
    tables = [
        ("Character",   "entity_id"),
        ("Faction",     "entity_id"),
        ("Location",    "entity_id"),
        ("Staff",       "entity_id"),
        ("Entity",      "entity_id"),
        ("MediaEntry",  "media_id"),
        ("Appearance",  "entity_id"),
        ("SourceRecord","source_id"),
    ]
    total = 0
    for tbl, _ in tables:
        out = sql(f"SELECT COUNT(*) FROM cargo__{tbl};")
        count_lines = [l for l in out.split("\n") if l.strip() and "COUNT" not in l]
        n = int(count_lines[0]) if count_lines else 0
        total += n
        print(f"  cargo__{tbl}: {n:,} rows")
    print(f"  TOTAL: {total:,} rows across all Cargo tables")


if __name__ == "__main__":
    conn = sqlite3.connect(TRAILS_DB)

    populate_characters(conn)
    populate_media(conn)
    populate_appearances(conn)
    populate_sources(conn)
    populate_factions(conn)
    populate_locations(conn)
    populate_staff(conn)
    populate_entities(conn)

    conn.close()
    verify()
