"""
parse_full_mirror.py
Phase 20 — Full Wiki Clone Router & Parser

Reads en_wiki_full_mirror.json (6,007 pages of raw wikitext) and routes each page
into the correct registry in trails.db. This is a one-time seeding pass; the
corpus file is temporary scaffolding and will be deleted once parsing is complete.

Routing logic:
  - Redirects        → alias map (resolved to target entity)
  - Infobox character → entity_registry (character)
  - Infobox organisation / military unit → entity_registry (faction)
  - Infobox city / nation / region / road / ruins → entity_registry (location)
  - InfoQuest        → entity_registry (quest concept) + chunk
  - InfoBook         → entity_registry (item/document) + chunk
  - Infobox machine  → entity_registry (item)
  - Infobox album / song → entity_registry (item/music)
  - Infobox event    → entity_registry (event)
  - Infobox game     → SKIP (already in media_registry)
  - Nav / parent tab only → SKIP (navigation scaffolding)
  - Unrecognised     → entity_registry (concept) with raw chunk

All inserts use INSERT OR IGNORE for entity_registry (preserves existing 529 chars).
All chunks use INSERT OR REPLACE (refresh raw content from full mirror).
Redirects are stored in a JSON sidecar for the alias resolver to consume.
"""

import json
import re
import sqlite3
from pathlib import Path
from collections import defaultdict

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent.parent
DB_PATH     = ROOT / 'retrieval' / 'index' / 'trails.db'
MIRROR_PATH = ROOT / 'corpus' / 'wiki' / 'en_wiki_full_mirror.json'
REDIRECT_SIDECAR = ROOT / 'corpus' / 'wiki' / 'redirect_map.json'

SOURCE_ID   = 'wiki:en_full_mirror_v2'
SOURCE_TITLE = 'Kiseki Fandom Wiki — Full Clone (6007 pages)'
SOURCE_URL   = 'https://kiseki.fandom.com/wiki/Main_Page'

# ── Game keyword → (media_id, spoiler_band) ───────────────────────────────────
# Keys are Fandom wiki shorthand. Tuple is (media_id, spoiler_band).
# All display text always uses the full English title from media_registry.
# "Ao", "Sen IV", "Hajimari", "Kuro" etc. are JP shorthand — never used in output.
GAME_MAP = {
    # Sky arc
    'fc':                        ('sky_fc',    10),
    'sora fc':                   ('sky_fc',    10),
    'sora 1st':                  ('sky_fc',    10),
    'sky fc':                    ('sky_fc',    10),
    'trails in the sky fc':      ('sky_fc',    10),
    'sc':                        ('sky_sc',    12),
    'sora sc':                   ('sky_sc',    12),
    'sky sc':                    ('sky_sc',    12),
    'trails in the sky sc':      ('sky_sc',    12),
    '3rd':                       ('sky_3rd',   14),
    'the 3rd':                   ('sky_3rd',   14),
    'sora 3rd':                  ('sky_3rd',   14),
    'sky 3rd':                   ('sky_3rd',   14),
    'trails in the sky the 3rd': ('sky_3rd',   14),
    # Crossbell arc — "Zero" and "Ao" resolve to English titles
    'zero':                      ('zero',      20),
    'zero no kiseki':            ('zero',      20),
    'trails from zero':          ('zero',      20),
    'ao':                        ('azure',     22),
    'azure':                     ('azure',     22),
    'ao no kiseki':              ('azure',     22),
    'trails to azure':           ('azure',     22),
    # Erebonia arc — "Sen I–IV" resolves to Cold Steel English titles
    'sen':                       ('cs1',       40),
    'sen i':                     ('cs1',       40),
    'cold steel':                ('cs1',       40),
    'cold steel i':              ('cs1',       40),
    'trails of cold steel':      ('cs1',       40),
    'sen ii':                    ('cs2',       42),
    'cold steel ii':             ('cs2',       42),
    'sen iii':                   ('cs3',       50),
    'cold steel iii':            ('cs3',       50),
    'sen iv':                    ('cs4',       55),
    'cold steel iv':             ('cs4',       55),
    # Reverie — "Hajimari" resolves to English title
    'hajimari':                  ('reverie',   65),
    'reverie':                   ('reverie',   65),
    'into reverie':              ('reverie',   65),
    'trails into reverie':       ('reverie',   65),
    # Calvard arc — "Kuro I/II" resolves to Daybreak English titles
    'kuro':                      ('daybreak',  70),
    'kuro i':                    ('daybreak',  70),
    'daybreak':                  ('daybreak',  70),
    'daybreak i':                ('daybreak',  70),
    'trails through daybreak':   ('daybreak',  70),
    'kuro ii':                   ('daybreak2', 75),
    'daybreak ii':               ('daybreak2', 75),
    'trails through daybreak ii':('daybreak2', 75),
    # Frontier
    'kai':                       ('kai',       100),
    'beyond the horizon':        ('kai',       100),
    'trails beyond the horizon': ('kai',       100),
    # Spinoffs
    'nayuta':                    ('nayuta',    10),
    'akatsuki':                  ('akatsuki',  20),
}

# ── Infobox template → entity classification ──────────────────────────────────
def classify_page(title: str, wikitext: str) -> dict:
    """
    Returns a dict with:
        skip:        bool — True if this page should not be ingested
        is_redirect: bool
        redirect_target: str | None
        entity_type: str
        id_prefix:   str
    """
    text_lower = wikitext.strip().lower()

    # Redirect
    if text_lower.startswith('#redirect'):
        m = re.match(r'#redirect\s*\[\[([^\]]+)\]\]', wikitext.strip(), re.IGNORECASE)
        target = m.group(1).split('|')[0].strip() if m else None
        return {'skip': False, 'is_redirect': True, 'redirect_target': target,
                'entity_type': None, 'id_prefix': None}

    # Pure navigation templates with no content
    nav_only = re.match(r'^\s*\{\{(nav |parent tab|clr|refnest|see also|main\b)', text_lower)
    if nav_only and len(wikitext) < 500:
        return {'skip': True, 'is_redirect': False, 'redirect_target': None,
                'entity_type': None, 'id_prefix': None}

    # Game infobox — already in media_registry
    if re.search(r'\{\{[Ii]nfobox[ _]game', wikitext):
        return {'skip': True, 'is_redirect': False, 'redirect_target': None,
                'entity_type': None, 'id_prefix': None}

    # Character
    if re.search(r'\{\{[Ii]nfobox[ _][Cc]haracter', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'character', 'id_prefix': 'char:'}

    # Organisation / military unit → faction
    if re.search(r'\{\{[Ii]nfobox[ _][Oo]rgani', wikitext) or \
       re.search(r'\{\{[Ii]nfobox[ _][Mm]ilitary[ _][Uu]nit', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'faction', 'id_prefix': 'faction:'}

    # City / Nation / Region / Road / Ruins → location
    if re.search(r'\{\{[Ii]nfobox[ _][Cc]ity', wikitext) or \
       re.search(r'\{\{[Ii]nfobox[ _][Nn]ation', wikitext) or \
       re.search(r'\{\{[Ii]nforegion', wikitext) or \
       re.search(r'\{\{[Ii]nforoad', wikitext) or \
       re.search(r'\{\{[Ii]nforuins', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'location', 'id_prefix': 'loc:'}

    # Quest
    if re.search(r'\{\{[Ii]nfo[Qq]uest', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'quest', 'id_prefix': 'quest:'}

    # Book / in-game document
    if re.search(r'\{\{[Ii]nfo[Bb]ook', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'item', 'id_prefix': 'item:'}

    # Machine / Weapon / Orbment → item
    if re.search(r'\{\{[Ii]nfobox[ _][Mm]achine', wikitext) or \
       re.search(r'\{\{[Ii]nfoorbment', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'item', 'id_prefix': 'item:'}

    # Album / Song → item (music)
    if re.search(r'\{\{[Ii]nfoalbum', wikitext) or \
       re.search(r'\{\{[Ii]nfobox[ _][Ss]ong', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'item', 'id_prefix': 'item:'}

    # Event
    if re.search(r'\{\{[Ii]nfoevent', wikitext) or \
       re.search(r'\{\{[Ii]nfobox[ _][Mm]ilitary[ _][Cc]onflict', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'event', 'id_prefix': 'event:'}

    # Publication (strategy guides, in-world books)
    if re.search(r'\{\{[Ii]nfobox[ _][Pp]ublication', wikitext):
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'item', 'id_prefix': 'item:'}

    # Anything with substantial prose but no known infobox → concept
    if len(wikitext) > 300:
        return {'skip': False, 'is_redirect': False, 'redirect_target': None,
                'entity_type': 'concept', 'id_prefix': 'concept:'}

    # Too short / pure navigation scaffolding → skip
    return {'skip': True, 'is_redirect': False, 'redirect_target': None,
            'entity_type': None, 'id_prefix': None}


# ── Wikitext utilities ────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s[:80]


def resolve_g_template(wikitext: str) -> tuple[str | None, int]:
    """
    Extract the first {{g|GameName}} reference and return (media_id, spoiler_band).
    Falls back to scanning for game keywords in plain text.
    """
    matches = re.findall(r'\{\{g\|([^|}]+)', wikitext, re.IGNORECASE)
    best_band = 0
    best_media = None
    for raw in matches:
        key = raw.strip().lower()
        for keyword, (mid, band) in GAME_MAP.items():
            if keyword in key or key in keyword:
                if band > best_band:
                    best_band = band
                    best_media = mid
                break
    if best_media:
        return best_media, best_band

    # Fallback: plain text scan
    wt_lower = wikitext.lower()
    for keyword, (mid, band) in GAME_MAP.items():
        if keyword in wt_lower:
            if band > best_band:
                best_band = band
                best_media = mid
    return best_media, best_band


def extract_debut_game(wikitext: str) -> tuple[str | None, int]:
    """
    Prefer the first |firstAppear / |first_appearance / |game infobox field.
    """
    # Try infobox field for debut/first
    for field in ('firstAppear', 'first_appearance', 'first', 'game'):
        m = re.search(rf'\|{field}\s*=\s*(.*?)(?:\n\||\n\n|\Z)', wikitext, re.DOTALL | re.IGNORECASE)
        if m:
            snippet = m.group(1)
            # Only use the FIRST line of multi-value fields (i.e. debut, not full list)
            first_line = snippet.split('\n')[0]
            # If it starts with *, grab the first bullet
            if first_line.strip().startswith('*'):
                first_line = first_line.strip().lstrip('*').strip()
            media_id, band = resolve_g_template(first_line)
            if media_id:
                return media_id, band

    # Full-wikitext fallback
    return resolve_g_template(wikitext)


def extract_infobox_value(wikitext: str, *keys: str) -> str | None:
    for key in keys:
        m = re.search(rf'\|{key}\s*=\s*([^\n|}}]+)', wikitext, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Strip wikilinks and HTML
            val = re.sub(r'\[\[([^|\]]+\|)?([^\]]+)\]\]', r'\2', val)
            val = re.sub(r'<[^>]+>', '', val)
            val = re.sub(r'\{\{[^}]+\}\}', '', val)
            val = val.strip(' *,')
            if val:
                return val
    return None


def extract_japanese_name(title: str, wikitext: str) -> str | None:
    """
    Try the infobox |kanji field first, then the bold-with-parenthesis lead pattern:
    '''Name''' (日本語) or '''Name''' (かな, Romaji)
    """
    kanji = extract_infobox_value(wikitext, 'kanji', 'japanese', 'ja_name')
    if kanji:
        return kanji

    # Lead sentence pattern
    m = re.search(
        r"'''[^']+'''\s*\(([^)]+)\)",
        wikitext[:2000]
    )
    if m:
        paren = m.group(1)
        # Keep only CJK / kana portion
        cjk = re.findall(r'[\u3000-\u9fff\uf900-\ufaff]+', paren)
        if cjk:
            return cjk[0]
    return None


# ── Wikitext → clean prose ────────────────────────────────────────────────────
def clean_wikitext(wikitext: str, max_paragraphs: int = 3) -> str:
    text = wikitext

    # Remove <ref>...</ref> blocks
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<ref[^/]*/>', '', text, flags=re.IGNORECASE)

    # Remove block-level HTML (gallery, tabber, div, table)
    for tag in ('gallery', 'tabber', 'div', 'table', 'blockquote', 'poem',
                'timeline', 'imagemap'):
        text = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', text,
                      flags=re.DOTALL | re.IGNORECASE)

    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Strip nested {{ }} templates iteratively
    for _ in range(8):
        new = re.sub(r'\{\{[^{}]*\}\}', '', text)
        if new == text:
            break
        text = new

    # Remove leftover {{ or }} fragments
    text = re.sub(r'\{\{.*', '', text)
    text = re.sub(r'\}\}.*', '', text)

    # Resolve [[Link|Text]] and [[Link]]
    text = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', text)

    # Remove external links [url text]
    text = re.sub(r'\[https?://\S+\s+([^\]]+)\]', r'\1', text)
    text = re.sub(r'\[https?://\S+\]', '', text)

    # Strip wiki markup lines (headers, bullets, indents, table rows)
    lines = text.split('\n')
    prose = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('==', '*', ':', ';', '|', '!', '{|', '|-', '|}')):
            continue
        if stripped.startswith("'''") and len(stripped) < 40:
            continue  # Likely a bold section header
        prose.append(stripped)

    # Merge into paragraphs (blank-line separated in original)
    result = ' '.join(prose)

    # Normalise whitespace
    result = re.sub(r'\s{2,}', ' ', result).strip()

    # Truncate to approximate paragraph count (sentence boundary)
    sentences = re.split(r'(?<=[.!?])\s+', result)
    kept = []
    para_count = 0
    for s in sentences:
        kept.append(s)
        if s.endswith('.') or s.endswith('!') or s.endswith('?'):
            para_count += 1
        if para_count >= max_paragraphs * 4:  # ~4 sentences per para
            break

    return ' '.join(kept)[:4000]  # Hard cap at 4000 chars


# ── Spoiler band from content ─────────────────────────────────────────────────
def detect_spoiler_band(wikitext: str, debut_band: int) -> int:
    """
    Start from debut_band and scan for later game references.
    A character mentioned in Kai content gets band 100 even if they debuted in Sky.
    """
    _, max_band = resolve_g_template(wikitext)
    return max(debut_band, max_band) if max_band else debut_band


# ── Main ingestion pass ───────────────────────────────────────────────────────
def run():
    if not MIRROR_PATH.exists():
        print(f"[ERROR] Mirror not found: {MIRROR_PATH}")
        return

    with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
        mirror = json.load(f)

    print(f"Loaded {len(mirror):,} pages from mirror.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Register source ──────────────────────────────────────────────────────
    cursor.execute('''
        INSERT OR REPLACE INTO source_registry (
            source_id, title, source_class, language,
            origin_url, local_path, trust_tier,
            ingestion_status, parse_status, spoiler_band, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        SOURCE_ID, SOURCE_TITLE, 'fan_wiki', 'en',
        SOURCE_URL,
        str(MIRROR_PATH.relative_to(ROOT)),
        2,   # trust_tier: fan wiki
        'complete', 'in_progress', 0,
        'Full 6007-page MediaWiki wikitext clone via generator=allpages. Temporary seed — delete after parse.'
    ))

    # ── Counters ─────────────────────────────────────────────────────────────
    counts = defaultdict(int)
    redirect_map = {}   # redirect_title → canonical_target_title
    skipped_titles = []

    # ── Process pages ────────────────────────────────────────────────────────
    for title, wikitext in mirror.items():
        if not wikitext:
            counts['empty'] += 1
            continue

        cls = classify_page(title, wikitext)

        # ── Redirect ────────────────────────────────────────────────────────
        if cls['is_redirect']:
            if cls['redirect_target']:
                redirect_map[title] = cls['redirect_target']
            counts['redirect'] += 1
            continue

        # ── Skip ────────────────────────────────────────────────────────────
        if cls['skip']:
            skipped_titles.append(title)
            counts['skipped'] += 1
            continue

        entity_type = cls['entity_type']
        id_prefix   = cls['id_prefix']

        # ── Build entity_id ──────────────────────────────────────────────────
        entity_id = f"{id_prefix}{slugify(title)}"

        # ── Extract metadata ─────────────────────────────────────────────────
        ja_name      = extract_japanese_name(title, wikitext)
        debut_media, debut_band = extract_debut_game(wikitext)
        spoiler_band = detect_spoiler_band(wikitext, debut_band)

        # Default band: quests/books default to their game band; else 20
        if spoiler_band == 0:
            spoiler_band = 20

        # ── Entity registry (INSERT OR IGNORE — preserve existing data) ──────
        cursor.execute('''
            INSERT OR IGNORE INTO entity_registry (
                entity_id, entity_type, english_display_name, japanese_name
            ) VALUES (?, ?, ?, ?)
        ''', (entity_id, entity_type, title, ja_name))

        # ── Raw text chunk ────────────────────────────────────────────────────
        raw_prose = clean_wikitext(wikitext)
        if raw_prose and len(raw_prose) > 30:
            chunk_id = f"raw:{entity_id}"
            cursor.execute('''
                INSERT OR REPLACE INTO chunk_registry (
                    chunk_id, source_id, linked_entity_ids,
                    text_content, language, chunk_type, spoiler_band
                ) VALUES (?, ?, ?, ?, 'en', 'raw_bio', ?)
            ''', (
                chunk_id, SOURCE_ID,
                json.dumps([entity_id]),
                raw_prose, spoiler_band
            ))

            # Lifecycle: mark as raw
            cursor.execute('''
                INSERT OR IGNORE INTO lifecycle_registry (object_id, state, reviewer_notes)
                VALUES (?, 'raw', 'Ingested from en_wiki_full_mirror.json Phase 20')
            ''', (entity_id,))

        # ── Debut appearance ─────────────────────────────────────────────────
        if debut_media:
            # Only link to media that exists in media_registry
            cursor.execute('SELECT 1 FROM media_registry WHERE media_id = ?', (debut_media,))
            if cursor.fetchone():
                cursor.execute('''
                    INSERT OR IGNORE INTO appearance_registry (
                        entity_id, media_id, appearance_type, debut_flag,
                        spoiler_band, source_id
                    ) VALUES (?, ?, 'main', 1, ?, ?)
                ''', (entity_id, debut_media, spoiler_band, SOURCE_ID))

        counts[entity_type] += 1

    # ── Resolve redirects as aliases ─────────────────────────────────────────
    alias_count = 0
    for redirect_title, target_title in redirect_map.items():
        # Find entity whose display name matches the target
        target_slug = slugify(target_title)
        cursor.execute('''
            SELECT entity_id, aliases FROM entity_registry
            WHERE english_display_name = ? OR entity_id LIKE ?
            LIMIT 1
        ''', (target_title, f'%{target_slug}%'))
        row = cursor.fetchone()
        if row:
            eid, aliases_json = row
            try:
                aliases = json.loads(aliases_json) if aliases_json else []
            except (json.JSONDecodeError, TypeError):
                aliases = []
            if redirect_title not in aliases:
                aliases.append(redirect_title)
                cursor.execute(
                    'UPDATE entity_registry SET aliases = ? WHERE entity_id = ?',
                    (json.dumps(aliases), eid)
                )
                alias_count += 1

    # ── Save redirect sidecar ────────────────────────────────────────────────
    with open(REDIRECT_SIDECAR, 'w', encoding='utf-8') as f:
        json.dump(redirect_map, f, ensure_ascii=False, indent=2)
    print(f"Redirect map saved → {REDIRECT_SIDECAR.name} ({len(redirect_map):,} entries)")

    # ── Update source parse status ───────────────────────────────────────────
    cursor.execute(
        "UPDATE source_registry SET parse_status = 'complete' WHERE source_id = ?",
        (SOURCE_ID,)
    )

    conn.commit()
    conn.close()

    # ── Summary ──────────────────────────────────────────────────────────────
    print()
    print("=" * 55)
    print("  Phase 20 — Full Mirror Parse Complete")
    print("=" * 55)
    print(f"  character  : {counts['character']:>5,}")
    print(f"  faction    : {counts['faction']:>5,}")
    print(f"  location   : {counts['location']:>5,}")
    print(f"  quest      : {counts['quest']:>5,}")
    print(f"  item       : {counts['item']:>5,}")
    print(f"  event      : {counts['event']:>5,}")
    print(f"  concept    : {counts['concept']:>5,}")
    print(f"  redirect   : {counts['redirect']:>5,}  (→ aliases)")
    print(f"  skipped    : {counts['skipped']:>5,}  (nav/game pages)")
    print(f"  empty      : {counts['empty']:>5,}")
    print(f"  aliases resolved : {alias_count:>4,}")
    print(f"  total processed  : {sum(counts.values()):>4,} / {len(mirror):,}")
    print("=" * 55)


if __name__ == '__main__':
    run()
