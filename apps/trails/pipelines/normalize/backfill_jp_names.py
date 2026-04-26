"""
backfill_jp_names.py
Phase 21 — Japanese Name Backfill

Sources (in priority order):
  1. raw_bio chunks  — re-scan the lead sentence pattern: '''Name''' (JP)
     Already in chunk_registry, no mirror needed.
  2. JA Wikipedia Vanc entries — 439 {{Vanc|JP_NAME}} section headers.
     Match against entities that already have JP names to build a bootstrap
     lookup, then use phonetic/alias matching for the rest.
  3. entity.notes.metadata.voice_jp — seiyuu field often contains furigana
     readings embedded in parentheses that can confirm katakana readings.

After backfill also updates aliases JSON to include the JP name.
"""

import json
import re
import sqlite3
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / 'retrieval' / 'index' / 'trails.db'
JA_CHAR_CACHE = ROOT / 'corpus' / 'wiki' / 'ja_wikipedia_characters.json'


def extract_jp_from_lead(text: str) -> str | None:
    """
    Find (JP) in the first bold-name lead pattern.
    Matches: '''Name''' (エステル・ブライト) or '''Name''' (エステル・ブライト, Romaji)
    """
    m = re.search(r"'''[^']+'''\s*\(([^)]+)\)", text[:800])
    if not m:
        return None
    paren = m.group(1)
    # Extract CJK / kana block — that's the JP name
    cjk = re.findall(r'[\u3000-\u9fff\uff00-\uffef\u3040-\u30ff・ー＝]+', paren)
    if cjk:
        candidate = cjk[0].strip('・ー ')
        if len(candidate) >= 2:
            return candidate
    return None


def extract_jp_from_vanc_page(wikitext: str) -> list[str]:
    """Extract all JP names from {{Vanc|JP_NAME}} entries."""
    return re.findall(r'\{\{Vanc\|([^}]+)\}\}', wikitext)


def normalize_jp(s: str) -> str:
    """Strip punctuation for fuzzy matching."""
    return re.sub(r'[・＝=\s]', '', s).strip()


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ── Pass 1: Scan raw_bio chunks for lead sentence JP name ────────────────
    print("Pass 1: Scanning raw_bio chunks for '''Name''' (JP) pattern...")

    c.execute('''
        SELECT e.entity_id, e.english_display_name, e.japanese_name, e.aliases,
               cr.text_content
        FROM entity_registry e
        JOIN chunk_registry cr ON cr.chunk_id = 'raw:' || e.entity_id
        WHERE e.entity_type IN ('character', 'faction', 'location', 'item')
          AND (e.japanese_name IS NULL OR e.japanese_name = '')
          AND cr.chunk_type = 'raw_bio'
    ''')
    rows = c.fetchall()
    print(f"  Entities missing JP name with raw_bio: {len(rows)}")

    pass1_count = 0
    for row in rows:
        jp = extract_jp_from_lead(row['text_content'])
        if jp:
            try:
                aliases = json.loads(row['aliases']) if row['aliases'] else []
            except (json.JSONDecodeError, TypeError):
                aliases = []
            if jp not in aliases:
                aliases.append(jp)
            c.execute(
                'UPDATE entity_registry SET japanese_name = ?, aliases = ? WHERE entity_id = ?',
                (jp, json.dumps(aliases, ensure_ascii=False), row['entity_id'])
            )
            pass1_count += 1

    print(f"  Backfilled from raw_bio: {pass1_count}")

    # ── Pass 2: Also scan lead chunks (better cleaned text) ─────────────────
    print("Pass 2: Scanning lead chunks...")
    c.execute('''
        SELECT e.entity_id, e.english_display_name, e.japanese_name, e.aliases,
               cr.text_content
        FROM entity_registry e
        JOIN chunk_registry cr ON cr.chunk_id = 'lead:' || e.entity_id
        WHERE e.entity_type IN ('character', 'faction', 'location')
          AND (e.japanese_name IS NULL OR e.japanese_name = '')
    ''')
    rows2 = c.fetchall()

    pass2_count = 0
    for row in rows2:
        # Lead chunks are cleaned, so look for parenthesised JP inline
        m = re.search(r'\(([^\)]{2,20})\)', row['text_content'][:400])
        if m:
            paren = m.group(1)
            cjk = re.findall(r'[\u3000-\u9fff\u3040-\u30ff・ー]+', paren)
            if cjk and len(cjk[0]) >= 2:
                jp = cjk[0].strip('・ー ')
                try:
                    aliases = json.loads(row['aliases']) if row['aliases'] else []
                except (json.JSONDecodeError, TypeError):
                    aliases = []
                if jp not in aliases:
                    aliases.append(jp)
                c.execute(
                    'UPDATE entity_registry SET japanese_name = ?, aliases = ? WHERE entity_id = ?',
                    (jp, json.dumps(aliases, ensure_ascii=False), row['entity_id'])
                )
                pass2_count += 1

    print(f"  Backfilled from lead chunks: {pass2_count}")

    # ── Pass 3: JA Wikipedia Vanc bootstrap ──────────────────────────────────
    print("Pass 3: JA Wikipedia Vanc cross-reference...")
    vanc_names = []
    if JA_CHAR_CACHE.exists():
        with open(JA_CHAR_CACHE, encoding='utf-8') as f:
            wt = json.load(f).get('wikitext', '')
        vanc_names = extract_jp_from_vanc_page(wt)
        print(f"  {len(vanc_names)} Vanc entries found")

    # Build normalised JP → entity_id map from what we already have
    c.execute('''
        SELECT entity_id, japanese_name FROM entity_registry
        WHERE japanese_name IS NOT NULL AND japanese_name != ''
    ''')
    existing_jp = {normalize_jp(r['japanese_name']): r['entity_id']
                   for r in c.fetchall()}

    # For Vanc names not yet matched, check if they're in entity aliases
    c.execute('''
        SELECT entity_id, aliases FROM entity_registry
        WHERE aliases IS NOT NULL AND aliases != '[]'
    ''')
    alias_map = {}
    for row in c.fetchall():
        try:
            for alias in json.loads(row['aliases']):
                nk = normalize_jp(alias)
                if nk:
                    alias_map[nk] = row['entity_id']
        except (json.JSONDecodeError, TypeError):
            pass

    # Vanc names that still have no match → try to find entity by normalized match
    unmatched_vanc = []
    for vname in vanc_names:
        nk = normalize_jp(vname)
        if nk not in existing_jp and nk not in alias_map:
            unmatched_vanc.append(vname)

    print(f"  Vanc names already mapped: {len(vanc_names) - len(unmatched_vanc)}")
    print(f"  Vanc names unmatched: {len(unmatched_vanc)}")

    # ── Pass 4: Backfill from entity notes seiyuu field ─────────────────────
    print("Pass 4: Scanning metadata for katakana in voice/affiliation fields...")
    c.execute('''
        SELECT entity_id, japanese_name, aliases, notes
        FROM entity_registry
        WHERE (japanese_name IS NULL OR japanese_name = '')
          AND notes IS NOT NULL AND notes != '{}'
    ''')
    pass4_count = 0
    for row in c.fetchall():
        try:
            notes = json.loads(row['notes'])
        except (json.JSONDecodeError, TypeError):
            continue
        meta = notes.get('metadata', {})
        # Sometimes the affiliation or occupation contains the JP name in parens
        for field_val in (meta.get('affiliation', ''), meta.get('occupation', ''),
                          notes.get('lead', '')):
            if not field_val:
                continue
            cjk = re.findall(r'[\u4e00-\u9fff\u3040-\u30ff・ー]{3,}', field_val)
            if cjk:
                jp = cjk[0].strip('・ー ')
                if len(jp) >= 2:
                    try:
                        aliases = json.loads(row['aliases']) if row['aliases'] else []
                    except (json.JSONDecodeError, TypeError):
                        aliases = []
                    if jp not in aliases:
                        aliases.append(jp)
                    c.execute(
                        'UPDATE entity_registry SET japanese_name = ?, aliases = ? WHERE entity_id = ?',
                        (jp, json.dumps(aliases, ensure_ascii=False), row['entity_id'])
                    )
                    pass4_count += 1
                    break

    print(f"  Backfilled from metadata fields: {pass4_count}")

    conn.commit()

    # ── Final count ──────────────────────────────────────────────────────────
    c.execute('SELECT COUNT(*) FROM entity_registry WHERE entity_type="character"')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM entity_registry WHERE entity_type="character" AND japanese_name IS NOT NULL AND japanese_name != ""')
    with_jp = c.fetchone()[0]
    conn.close()

    total_added = pass1_count + pass2_count + pass4_count
    print()
    print("=" * 50)
    print(f"  Total JP names added  : {total_added}")
    print(f"  Characters with JP    : {with_jp} / {total}  ({with_jp*100//total}%)")
    print("=" * 50)


if __name__ == '__main__':
    run()
