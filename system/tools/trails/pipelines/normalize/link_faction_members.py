"""
link_faction_members.py
Phase 21 — Faction Member Relationship Builder

Walks every entity's notes.metadata.affiliation field and fuzzy-matches
the value against faction entities in entity_registry, then inserts
relationship_registry entries of type 'member_of'.

Also handles multi-affiliation strings like:
  "Bracer Guild * Erebonian Army" → two separate member_of links

Source: system:phase21_faction_linker (derived from wiki infobox data)
"""

import json
import re
import sqlite3
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / 'retrieval' / 'index' / 'trails.db'
SOURCE_ID = 'system:phase21_faction_linker'


def slugify(s: str) -> str:
    return re.sub(r'[\s-]+', '_', re.sub(r'[^\w\s-]', '', s.lower())).strip('_')


def normalize(s: str) -> str:
    return re.sub(r'\s+', ' ', s.lower().strip())


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Register source
    c.execute('''
        INSERT OR IGNORE INTO source_registry (
            source_id, title, source_class, language,
            trust_tier, ingestion_status, parse_status, spoiler_band
        ) VALUES (?, 'Phase 21 Faction Member Linker', 'system', 'en', 1, 'complete', 'complete', 0)
    ''', (SOURCE_ID,))

    # ── Build faction lookup ─────────────────────────────────────────────────
    # {normalised_name: entity_id}  for all factions
    c.execute('''
        SELECT entity_id, english_display_name, aliases
        FROM entity_registry
        WHERE entity_type = 'faction'
    ''')
    faction_index = {}
    for row in c.fetchall():
        faction_index[normalize(row['english_display_name'])] = row['entity_id']
        try:
            for alias in json.loads(row['aliases'] or '[]'):
                faction_index[normalize(alias)] = row['entity_id']
        except (json.JSONDecodeError, TypeError):
            pass

    # Partial match index: {word: [entity_id, ...]} for single-word lookups
    word_index = {}
    for name, eid in faction_index.items():
        for word in name.split():
            if len(word) > 4:
                word_index.setdefault(word, set()).add(eid)

    def find_faction(raw_affiliation: str) -> list[str]:
        """
        Try to find faction entity_ids for a raw affiliation string.
        Handles multi-value strings split by * or newlines.
        """
        results = []
        # Split on * (wiki list separator) or newlines
        parts = re.split(r'[\*\n]+', raw_affiliation)
        for part in parts:
            part = part.strip(' *,()')
            # Strip parenthetical qualifiers like "(formerly)", "(informally)"
            part = re.sub(r'\([^)]+\)', '', part).strip()
            if not part or len(part) < 3:
                continue

            norm = normalize(part)

            # Exact match
            if norm in faction_index:
                eid = faction_index[norm]
                if eid not in results:
                    results.append(eid)
                continue

            # Prefix match
            for fname, feid in faction_index.items():
                if fname.startswith(norm) or norm.startswith(fname):
                    if feid not in results:
                        results.append(feid)
                    break

            # Word overlap match (at least 2 significant words in common)
            words = [w for w in norm.split() if len(w) > 4]
            candidates = {}
            for word in words:
                for feid in word_index.get(word, set()):
                    candidates[feid] = candidates.get(feid, 0) + 1
            best = [(score, feid) for feid, score in candidates.items() if score >= 1]
            best.sort(reverse=True)
            if best:
                feid = best[0][1]
                if feid not in results:
                    results.append(feid)

        return results

    # ── Walk all entities with affiliation metadata ──────────────────────────
    c.execute('''
        SELECT entity_id, entity_type, notes
        FROM entity_registry
        WHERE notes IS NOT NULL AND notes NOT IN ('{}', 'null', '')
          AND entity_type NOT IN ('faction', 'main_game', 'spin_off', 'anime', 'manga', 'drama_cd')
    ''')
    entities = c.fetchall()
    print(f"Scanning {len(entities):,} entities for affiliation data...")

    linked      = 0
    already     = 0
    no_match    = 0
    multi_links = 0

    for row in entities:
        try:
            notes = json.loads(row['notes'])
        except (json.JSONDecodeError, TypeError):
            continue

        affil = notes.get('metadata', {}).get('affiliation', '')
        if not affil:
            continue

        faction_ids = find_faction(affil)
        if not faction_ids:
            no_match += 1
            continue

        for fid in faction_ids:
            # Check if relationship already exists
            c.execute('''
                SELECT 1 FROM relationship_registry
                WHERE subject_entity_id = ? AND object_id = ? AND relationship_type = 'member_of'
            ''', (row['entity_id'], fid))
            if c.fetchone():
                already += 1
                continue

            c.execute('''
                INSERT INTO relationship_registry
                (subject_entity_id, object_id, relationship_type, source_id, notes)
                VALUES (?, ?, 'member_of', ?, 'Phase 21: derived from infobox affiliation field')
            ''', (row['entity_id'], fid, SOURCE_ID))
            linked += 1

        if len(faction_ids) > 1:
            multi_links += 1

    conn.commit()

    # ── Verify top factions by member count ──────────────────────────────────
    print("\nTop factions by member count:")
    c.execute('''
        SELECT e.english_display_name, COUNT(*) as members
        FROM relationship_registry r
        JOIN entity_registry e ON r.object_id = e.entity_id
        WHERE r.relationship_type = 'member_of'
        GROUP BY r.object_id
        ORDER BY members DESC
        LIMIT 20
    ''')
    for row in c.fetchall():
        print(f"  {row['members']:>4}  {row['english_display_name']}")

    conn.close()

    print()
    print("=" * 50)
    print(f"  New member_of links   : {linked:,}")
    print(f"  Already existed       : {already:,}")
    print(f"  Multi-faction members : {multi_links:,}")
    print(f"  Affiliation not matched: {no_match:,}")
    print("=" * 50)


if __name__ == '__main__':
    run()
