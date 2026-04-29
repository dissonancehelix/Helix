"""
ingest_en_wikipedia.py
Phase 21 — English Wikipedia Ingestion

Fetches, caches, and ingests two Wikipedia articles written by the project author:
  - Trails_(series)        → arc-level lore chunks + series overview
  - List_of_Trails_media   → media_registry enrichment (dates, platforms, JP titles, publishers)

Trust tier: 0 (author-written Wikipedia articles, treated as primary editorial source)

Also adds two missing media entries:
  - sky_1st_chapter  (Trails in the Sky 1st Chapter — 3D remake, Sept 2025)
  - sky_2nd_chapter  (Trails in the Sky 2nd Chapter — 2026)
"""

import json
import re
import sqlite3
import time
import urllib.request
import urllib.parse
from pathlib import Path

ROOT      = Path(__file__).parent.parent.parent
DB_PATH   = ROOT / 'retrieval' / 'index' / 'trails.db'
CACHE_DIR = ROOT / 'corpus' / 'wiki'

WIKIPEDIA_API = 'https://en.wikipedia.org/w/api.php'

PAGES = [
    {
        'source_id':   'wiki:en_wikipedia_series',
        'page_title':  'Trails_(series)',
        'display':     'Trails (series) — English Wikipedia',
        'cache_file':  'en_wikipedia_series.json',
        'trust_tier':  0,
        'spoiler_band': 75,
    },
    {
        'source_id':   'wiki:en_wikipedia_media',
        'page_title':  'List_of_Trails_media',
        'display':     'List of Trails media — English Wikipedia',
        'cache_file':  'en_wikipedia_media.json',
        'trust_tier':  0,
        'spoiler_band': 75,
    },
]

# media_id → known data for cross-referencing
MEDIA_TITLE_MAP = {
    'Trails in the Sky':           'sky_fc',
    'Trails in the Sky SC':        'sky_sc',
    'Trails in the Sky the 3rd':   'sky_3rd',
    'Trails from Zero':            'zero',
    'Trails to Azure':             'azure',
    'Trails of Cold Steel':        'cs1',
    'Trails of Cold Steel II':     'cs2',
    'Trails of Cold Steel III':    'cs3',
    'Trails of Cold Steel IV':     'cs4',
    'Trails into Reverie':         'reverie',
    'Trails Through Daybreak':     'daybreak',
    'Trails Through Daybreak II':  'daybreak2',
    'Trails Beyond the Horizon':   'kai',
    'Trails in the Sky 1st Chapter': 'sky_1st_chapter',
    'Trails in the Sky 2nd Chapter': 'sky_2nd_chapter',
    'The Legend of Nayuta: Boundless Trails': 'nayuta',
    'Trails at Sunrise':           'akatsuki',
}

# JP title mapping from notes field in List_of_Trails_media
JP_TITLE_MAP = {
    'sky_fc':    ('Eiyū Densetsu VI: Sora no Kiseki',            '英雄伝説VI 空の軌跡'),
    'sky_sc':    ('Eiyū Densetsu VI: Sora no Kiseki SC',         '英雄伝説VI 空の軌跡SC'),
    'sky_3rd':   ('Eiyū Densetsu: Sora no Kiseki the 3rd',       '英雄伝説 空の軌跡 the 3rd'),
    'zero':      ('The Legend of Heroes: Zero no Kiseki',         '英雄伝説 零の軌跡'),
    'azure':     ('The Legend of Heroes: Ao no Kiseki',           '英雄伝説 碧の軌跡'),
    'cs1':       ('The Legend of Heroes: Sen no Kiseki',          '英雄伝説 閃の軌跡'),
    'cs2':       ('The Legend of Heroes: Sen no Kiseki II',       '英雄伝説 閃の軌跡II'),
    'cs3':       ('The Legend of Heroes: Sen no Kiseki III',      '英雄伝説 閃の軌跡III'),
    'cs4':       ('The Legend of Heroes: Sen no Kiseki IV',       '英雄伝説 閃の軌跡IV'),
    'reverie':   ('The Legend of Heroes: Hajimari no Kiseki',     '英雄伝説 創の軌跡'),
    'daybreak':  ('The Legend of Heroes: Kuro no Kiseki',         '英雄伝説 黎の軌跡'),
    'daybreak2': ('The Legend of Heroes: Kuro no Kiseki II',      '英雄伝説 黎の軌跡II'),
    'kai':       ('The Legend of Heroes: Kai no Kiseki',          '英雄伝説 界の軌跡'),
    'nayuta':    ('Nayuta no Kiseki',                             'ナユタの軌跡'),
    'akatsuki':  ('Akatsuki no Kiseki',                           '暁の軌跡'),
}


def fetch_wikitext(page_title: str) -> str | None:
    params = urllib.parse.urlencode({
        'action': 'query', 'titles': page_title,
        'prop': 'revisions', 'rvprop': 'content',
        'rvslots': 'main', 'format': 'json', 'formatversion': '2',
    })
    req = urllib.request.Request(
        f"{WIKIPEDIA_API}?{params}",
        headers={'User-Agent': 'HelixTrailsBot/1.0 (kiseki lore substrate)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
        page = data['query']['pages'][0]
        if 'missing' in page:
            return None
        return page['revisions'][0]['slots']['main']['content']
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def clean(text: str) -> str:
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r'<ref[^/]*/>', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<[^>]+>', '', t)
    for _ in range(6):
        n = re.sub(r'\{\{[^{}]*\}\}', '', t)
        if n == t: break
        t = n
    t = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', t)
    t = re.sub(r'\[https?://\S+\s+([^\]]+)\]', r'\1', t)
    t = re.sub(r'\[https?://\S+\]', '', t)
    return re.sub(r'\s+', ' ', t).strip()


# ── Series article → arc lore chunks ─────────────────────────────────────────
def ingest_series_article(wikitext: str, source_id: str, cursor):
    """Extract arc-level narrative sections as high-trust lore chunks."""
    chunks_added = 0

    # Store full cleaned text
    full_clean = clean(wikitext)
    cursor.execute('''
        INSERT OR REPLACE INTO chunk_registry
        (chunk_id, source_id, text_content, language, chunk_type, spoiler_band)
        VALUES ('en_wiki_series_full', ?, ?, 'en', 'series_overview', 20)
    ''', (source_id, full_clean[:8000]))
    chunks_added += 1

    # Extract named sections
    sections = re.split(r'(={2,4}[^=\n]+={2,4})', wikitext)
    i = 1
    while i + 1 < len(sections):
        header_raw = sections[i].strip('= \n')
        body       = sections[i + 1]
        i += 2

        # Strip anchors from header: {{anchor|...}}Name → Name
        header = re.sub(r'\{\{anchor\|[^}]+\}\}', '', header_raw).strip()
        header = clean(header)

        body_clean = clean(body)
        if len(body_clean) < 80:
            continue

        # Determine spoiler band from header content
        band = 20
        hl = header.lower()
        if 'calvard' in hl or 'daybreak' in hl:
            band = 70
        elif 'erebonia' in hl or 'cold steel' in hl or 'reverie' in hl:
            band = 40
        elif 'crossbell' in hl or 'zero' in hl or 'azure' in hl:
            band = 20
        elif 'liberl' in hl or 'sky' in hl:
            band = 10

        slug = re.sub(r'[^a-z0-9]', '_', header.lower())[:50]
        chunk_id = f"en_wiki_series:{slug}"

        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry
            (chunk_id, source_id, text_content, language, chunk_type, spoiler_band)
            VALUES (?, ?, ?, 'en', 'series_lore', ?)
        ''', (chunk_id, source_id, f"[{header}] {body_clean[:4000]}", band))
        chunks_added += 1

    return chunks_added


# ── Media list → media_registry enrichment ───────────────────────────────────
def parse_media_items(wikitext: str) -> list[dict]:
    """
    Parse {{Video game titles/item}} blocks from the media list article.
    Returns list of structured media dicts.
    """
    items = []
    # Match each item block
    pattern = re.compile(
        r'\{\{Video game titles/item\s*\|(.+?)\}\}(?=\s*\{\{Video game titles/item|\s*\}\})',
        re.DOTALL
    )
    for m in pattern.finditer(wikitext):
        block = m.group(1)
        item = {}

        def field(key):
            fm = re.search(rf'^\s*\|\s*{key}\s*=\s*(.+?)(?=\n\s*\||\Z)',
                           block, re.MULTILINE | re.DOTALL)
            if fm:
                return clean(fm.group(1).strip())
            return None

        title      = field('title')
        article    = field('article')
        notes_raw  = field('notes')
        date_raw   = re.search(r'\|\s*date\s*=\s*(.+?)(?=\n\s*\||\Z)', block,
                               re.MULTILINE | re.DOTALL)
        release_raw = re.search(r'\|\s*release\s*=\s*(.+?)(?=\n\s*\||\Z)', block,
                                re.MULTILINE | re.DOTALL)

        if not title:
            continue

        # Dates: extract JP and WW/NA dates
        date_str = clean(date_raw.group(1)) if date_raw else ''
        jp_m  = re.search(r'JP\|([^|}]+)', date_raw.group(1) if date_raw else '')
        na_m  = re.search(r'(?:NA|WW)\|([^|}]+)', date_raw.group(1) if date_raw else '')
        jp_date = jp_m.group(1).strip() if jp_m else ''
        en_date = na_m.group(1).strip() if na_m else ''

        # Platforms
        platforms = []
        if release_raw:
            platforms = re.findall(r'(\d{4})\s*[–-]\s*([^\n|{}]+)', release_raw.group(1))
            platforms = [f"{y}: {p.strip()}" for y, p in platforms]

        item = {
            'title':      title,
            'article':    article,
            'jp_date':    jp_date,
            'en_date':    en_date,
            'platforms':  ' | '.join(platforms[:6]),
            'notes':      notes_raw or '',
            'media_id':   MEDIA_TITLE_MAP.get(title),
        }
        items.append(item)

    return items


def ingest_media_list(wikitext: str, source_id: str, cursor):
    """Update media_registry with enriched data from the media list."""
    items = parse_media_items(wikitext)
    updated = 0
    added   = 0

    # Add missing media entries first
    new_entries = [
        {
            'media_id':          'sky_1st_chapter',
            'media_type':        'main_game',
            'english_title':     'Trails in the Sky 1st Chapter',
            'japanese_title':    '空の軌跡 1st Chapter',
            'publisher':         'GungHo (NA) / Clear River Games (EU)',
            'release_date_jp':   'September 19, 2025',
            'release_date_en':   'September 19, 2025',
            'release_chronology': 14,
            'internal_chronology': 'Liberl arc',
            'spoiler_band':      10,
            'is_main_series':    1,
            'canonical_notes':   '3D remake of Trails in the Sky FC using Daybreak engine. First simultaneous worldwide release in series history.',
        },
        {
            'media_id':          'sky_2nd_chapter',
            'media_type':        'main_game',
            'english_title':     'Trails in the Sky 2nd Chapter',
            'japanese_title':    '空の軌跡 2nd Chapter',
            'publisher':         'GungHo (NA) / Clear River Games (EU)',
            'release_date_jp':   '2026',
            'release_date_en':   '2026',
            'release_chronology': 15,
            'internal_chronology': 'Liberl arc',
            'spoiler_band':      12,
            'is_main_series':    1,
            'canonical_notes':   '3D remake of Trails in the Sky SC.',
        },
    ]
    for e in new_entries:
        cursor.execute('''
            INSERT OR IGNORE INTO media_registry (
                media_id, media_type, english_title, japanese_title,
                publisher, release_date_jp, release_date_en,
                release_chronology, internal_chronology,
                spoiler_band, is_main_series, canonical_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            e['media_id'], e['media_type'], e['english_title'], e['japanese_title'],
            e['publisher'], e['release_date_jp'], e['release_date_en'],
            e['release_chronology'], e['internal_chronology'],
            e['spoiler_band'], e['is_main_series'], e['canonical_notes'],
        ))
        if cursor.rowcount:
            added += 1
            print(f"  + Added: {e['english_title']}")

    # Update existing entries from parsed items
    for item in items:
        mid = item['media_id']
        if not mid:
            continue

        # Extract publisher from notes
        publisher = None
        if 'Xseed Games' in item['notes']:
            publisher = 'XSEED Games'
        elif 'NIS America' in item['notes']:
            publisher = 'NIS America'
        elif 'GungHo' in item['notes']:
            publisher = 'GungHo Online Entertainment'

        # Extract arc from notes
        arc_m = re.search(r'(Liberl|Crossbell|Erebonia|Calvard)\s+arc', item['notes'])
        arc = arc_m.group(0) if arc_m else None

        # Apply JP title from our authoritative map
        jp_romaji, jp_kanji = JP_TITLE_MAP.get(mid, (None, None))

        # Build update
        updates = {}
        if item['jp_date']:
            updates['release_date_jp'] = item['jp_date']
        if item['en_date']:
            updates['release_date_en'] = item['en_date']
        if publisher:
            updates['publisher'] = publisher
        if arc:
            updates['internal_chronology'] = arc
        if jp_kanji:
            updates['japanese_title'] = jp_kanji
        if item['platforms']:
            updates['canonical_notes'] = item['platforms']

        if updates:
            set_clause = ', '.join(f'{k} = ?' for k in updates)
            cursor.execute(
                f'UPDATE media_registry SET {set_clause} WHERE media_id = ?',
                list(updates.values()) + [mid]
            )
            if cursor.rowcount:
                updated += 1

    # Also store the full media list as a chunk
    full_clean = clean(wikitext)
    cursor.execute('''
        INSERT OR REPLACE INTO chunk_registry
        (chunk_id, source_id, text_content, language, chunk_type, spoiler_band)
        VALUES ('en_wiki_media_full', ?, ?, 'en', 'media_catalog', 75)
    ''', (source_id, full_clean[:8000]))

    return updated, added


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for page in PAGES:
        sid        = page['source_id']
        title      = page['page_title']
        cache_path = CACHE_DIR / page['cache_file']
        display    = page['display']

        print(f"\n── {display}")

        # Register source
        cursor.execute('''
            INSERT OR REPLACE INTO source_registry (
                source_id, title, source_class, language,
                origin_url, trust_tier, ingestion_status, parse_status, spoiler_band, notes
            ) VALUES (?, ?, 'wikipedia_en', 'en', ?, ?, 'complete', 'in_progress', ?, ?)
        ''', (
            sid, display,
            f"https://en.wikipedia.org/wiki/{title}",
            page['trust_tier'], page['spoiler_band'],
            'Author-written Wikipedia article. Trust tier 0 — treated as primary editorial source.',
        ))

        # Load or fetch wikitext
        if cache_path.exists():
            with open(cache_path, encoding='utf-8') as f:
                wikitext = json.load(f).get('wikitext', '')
            print(f"  Loaded from cache ({len(wikitext):,} chars)")
        else:
            print(f"  Fetching from Wikipedia API...")
            wikitext = fetch_wikitext(title)
            time.sleep(1)
            if not wikitext:
                print(f"  [SKIP] Could not fetch.")
                continue
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({'title': title, 'wikitext': wikitext}, f,
                          ensure_ascii=False, indent=2)
            print(f"  Cached → {cache_path.name} ({len(wikitext):,} chars)")

        # Ingest
        if 'series' in sid:
            n = ingest_series_article(wikitext, sid, cursor)
            print(f"  Series lore chunks: {n}")

        elif 'media' in sid:
            updated, added = ingest_media_list(wikitext, sid, cursor)
            print(f"  Media entries updated: {updated}, added: {added}")

        cursor.execute(
            "UPDATE source_registry SET parse_status = 'complete' WHERE source_id = ?",
            (sid,)
        )

    conn.commit()

    # Print updated media registry
    print("\n── Media Registry (updated)")
    cur2 = conn.cursor()
    cur2.execute('''
        SELECT english_title, japanese_title, release_date_jp, release_date_en,
               publisher, spoiler_band
        FROM media_registry
        WHERE media_type IN ('main_game')
        ORDER BY release_chronology
    ''')
    for r in cur2.fetchall():
        print(f"  [{r[5]:>3}] {r[0]}")
        print(f"        JP: {r[2]}  EN: {r[3]}  Publisher: {r[4]}")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    run()
