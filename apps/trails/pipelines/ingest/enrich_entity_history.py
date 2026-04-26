"""
enrich_entity_history.py
Phase 21 — Full Entity History Enrichment (Batched)

STORAGE PHILOSOPHY
──────────────────
The substrate stores structured data, not formatted prose.
  - entity_registry.notes  → JSON blob: all structured fields + per-game history
  - chunk_registry          → flat clean text derived from structured data (for FTS)
  - Export scripts          → produce wiki / markdown / JSONL from the structured layer

Nothing stored here looks like a Wikipedia article.
Wiki formatting is an export concern handled downstream.

What gets extracted per entity:
  - metadata: age, birthDate, nationality, affiliation, relatives, VA, etc.
  - history[]:  [{game (EN title), media_id, band, text}, ...]
  - appearance: physical description (clean prose)
  - personality: traits / character notes (clean prose)
  - background: for factions/locations (clean prose)
  - lead: the entity's defining one-line role statement

chunk_registry gets one flat text chunk per data type, searchable via FTS5.
All Japanese shorthand (Ao, Sen IV, Hajimari, Kuro) is resolved to EN display titles.
Japanese content lives only in entity_registry.japanese_name / aliases.

Usage:
    python enrich_entity_history.py [--type TYPE] [--batch N] [--dry-run]

    --type    : filter by entity_type (character, faction, location, quest, item)
    --batch   : entities per run (default 150)
    --dry-run : print stats without writing

Lifecycle: raw → normalized after enrichment.
Run repeatedly until "Still raw: 0".
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT        = Path(__file__).parent.parent.parent
DB_PATH     = ROOT / 'retrieval' / 'index' / 'trails.db'
MIRROR_PATH = ROOT / 'corpus' / 'wiki' / 'en_wiki_full_mirror.json'
SOURCE_ID   = 'wiki:en_full_mirror_v2'

# ── Game template → (media_id, spoiler_band, english_display_title) ───────────
# Keys = Fandom wiki shorthand inside {{g|...}}.
# "Ao", "Sen IV", "Hajimari", "Kuro" are JP shorthands — never used in output.
GAME_MAP = {
    'fc':                        ('sky_fc',    10, 'Trails in the Sky FC'),
    'sora fc':                   ('sky_fc',    10, 'Trails in the Sky FC'),
    'sora 1st':                  ('sky_fc',    10, 'Trails in the Sky the 1st'),
    'sky fc':                    ('sky_fc',    10, 'Trails in the Sky FC'),
    'sc':                        ('sky_sc',    12, 'Trails in the Sky SC'),
    'sora sc':                   ('sky_sc',    12, 'Trails in the Sky SC'),
    'sky sc':                    ('sky_sc',    12, 'Trails in the Sky SC'),
    '3rd':                       ('sky_3rd',   14, 'Trails in the Sky the 3rd'),
    'the 3rd':                   ('sky_3rd',   14, 'Trails in the Sky the 3rd'),
    'sora 3rd':                  ('sky_3rd',   14, 'Trails in the Sky the 3rd'),
    'zero':                      ('zero',      20, 'Trails from Zero'),
    'ao':                        ('azure',     22, 'Trails to Azure'),
    'azure':                     ('azure',     22, 'Trails to Azure'),
    'sen':                       ('cs1',       40, 'Trails of Cold Steel'),
    'sen i':                     ('cs1',       40, 'Trails of Cold Steel'),
    'cold steel':                ('cs1',       40, 'Trails of Cold Steel'),
    'cold steel i':              ('cs1',       40, 'Trails of Cold Steel'),
    'sen ii':                    ('cs2',       42, 'Trails of Cold Steel II'),
    'cold steel ii':             ('cs2',       42, 'Trails of Cold Steel II'),
    'sen iii':                   ('cs3',       50, 'Trails of Cold Steel III'),
    'cold steel iii':            ('cs3',       50, 'Trails of Cold Steel III'),
    'sen iv':                    ('cs4',       55, 'Trails of Cold Steel IV'),
    'cold steel iv':             ('cs4',       55, 'Trails of Cold Steel IV'),
    'hajimari':                  ('reverie',   65, 'Trails into Reverie'),
    'reverie':                   ('reverie',   65, 'Trails into Reverie'),
    'kuro':                      ('daybreak',  70, 'Trails Through Daybreak'),
    'kuro i':                    ('daybreak',  70, 'Trails Through Daybreak'),
    'daybreak':                  ('daybreak',  70, 'Trails Through Daybreak'),
    'kuro ii':                   ('daybreak2', 75, 'Trails Through Daybreak II'),
    'daybreak ii':               ('daybreak2', 75, 'Trails Through Daybreak II'),
    'kai':                       ('kai',       100, 'Trails Beyond the Horizon'),
    'akatsuki':                  ('akatsuki',  20, 'Akatsuki no Kiseki'),
    'nayuta':                    ('nayuta',    10, 'The Legend of Nayuta: Boundless Trails'),
}

# Infobox field extraction map: (output_key, [candidate_field_names])
INFOBOX_FIELDS = [
    ('age',          ['age']),
    ('birth_date',   ['birthDate', 'birth_date', 'birthdate']),
    ('birth_place',  ['birthPlace', 'birth_place', 'birthplace']),
    ('nationality',  ['nationality']),
    ('affiliation',  ['affilliation', 'affiliation', 'organization']),
    ('occupation',   ['occupation', 'job']),
    ('relatives',    ['relatives', 'family']),
    ('status',       ['status']),
    ('gender',       ['gender']),
    ('height',       ['height']),
    ('weapon',       ['weapon']),
    ('voice_jp',     ['seiyuu']),
    ('voice_en',     ['voiceactor', 'voice_actor']),
    ('likes',        ['likes']),
    ('dislikes',     ['dislikes']),
    ('hobbies',      ['hobbies']),
    # Faction / location
    ('founder',      ['founder']),
    ('founded',      ['foundingDate', 'founded', 'founding_date']),
    ('location',     ['location', 'country', 'region']),
    ('capital',      ['capital']),
    ('leadership',   ['key_people', 'leader', 'head', 'president']),
    # Quest
    ('game',         ['game']),
    ('quest_type',   ['type']),
    ('quest_length', ['length']),
    ('rewards',      ['rewards']),
]


# ── Wikitext utilities ────────────────────────────────────────────────────────
def resolve_game_key(raw: str) -> tuple[str | None, int, str]:
    key = raw.strip().lower()
    if key in GAME_MAP:
        return GAME_MAP[key]
    best = (None, 0, '')
    for keyword, val in GAME_MAP.items():
        if keyword in key and val[1] > best[1]:
            best = val
    return best


def extract_infobox_raw(wikitext: str) -> str:
    """Return the full {{Infobox ...}} block (handles nested braces)."""
    for pat in (r'\{\{[Ii]nfobox', r'\{\{[Ii]nfoquest', r'\{\{[Ii]nfobook',
                r'\{\{[Ii]nfobox[ _][Oo]rgani', r'\{\{[Ii]nfobox[ _][Cc]ity'):
        m = re.search(pat, wikitext)
        if m:
            break
    else:
        return ''
    start, depth, i = m.start(), 0, m.start()
    while i < len(wikitext):
        if wikitext[i:i+2] == '{{':
            depth += 1; i += 2
        elif wikitext[i:i+2] == '}}':
            depth -= 1; i += 2
            if depth == 0:
                return wikitext[start:i]
        else:
            i += 1
    return wikitext[start:]


def clean_value(val: str) -> str:
    """Strip all markup from an infobox field value."""
    # Spoiler spans — keep the text
    val = re.sub(r'<span[^>]*class[^>]*spoiler[^>]*>(.*?)</span>', r'\1',
                 val, flags=re.DOTALL | re.IGNORECASE)
    val = re.sub(r'<[^>]+>', '', val)
    for _ in range(6):
        val = re.sub(r'\{\{[^{}|]*\|([^{}]*)\}\}', r'\1', val)
        val = re.sub(r'\{\{[^{}]*\}\}', '', val)
    val = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', val)
    val = re.sub(r'\[https?://\S+\s+([^\]]+)\]', r'\1', val)
    val = re.sub(r'\[https?://\S+\]', '', val)
    val = re.sub(r'\s+', ' ', val).strip(' *,\n')
    return val


def parse_infobox_field(infobox: str, field_keys: list[str]) -> str | None:
    for key in field_keys:
        m = re.search(
            rf'^\s*\|{key}\s*=\s*(.+?)(?=\n\s*\||\n\s*\}}\}}|\Z)',
            infobox, re.MULTILINE | re.DOTALL | re.IGNORECASE
        )
        if m:
            val = clean_value(m.group(1))
            if val:
                return val
    return None


def extract_metadata(wikitext: str) -> dict:
    infobox = extract_infobox_raw(wikitext)
    meta = {}
    for out_key, field_keys in INFOBOX_FIELDS:
        val = parse_infobox_field(infobox, field_keys)
        if val:
            meta[out_key] = val
    return meta


def clean_prose(text: str) -> str:
    """Strip all wiki/html markup from a prose block. Returns plain text."""
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r'<ref[^/]*/>', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<span[^>]*class[^>]*spoiler[^>]*>(.*?)</span>', r'\1',
               t, flags=re.DOTALL | re.IGNORECASE)
    for tag in ('gallery', 'tabber', 'div', 'table', 'blockquote', 'poem'):
        t = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', t,
                   flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r'<[^>]+>', '', t)
    for _ in range(8):
        n = re.sub(r'\{\{[^{}]*\}\}', '', t)
        if n == t:
            break
        t = n
    t = re.sub(r'\{\{.*', '', t)
    t = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', t)
    t = re.sub(r'\[https?://\S+\s+([^\]]+)\]', r'\1', t)
    t = re.sub(r'\[https?://\S+\]', '', t)
    lines = []
    for line in t.split('\n'):
        s = line.strip()
        if not s or s.startswith(('==', '*', ':', ';', '|', '!', '{|', '|-', '|}')):
            continue
        lines.append(s)
    return re.sub(r'\s+', ' ', ' '.join(lines)).strip()


def extract_per_game_history(wikitext: str) -> list[dict]:
    """
    Parse the Introduction section into per-game history entries.
    Returns list of structured dicts:
      {game, media_id, band, text}
    where game is always the English display title.
    """
    results = []
    intro_m = re.search(r'===\s*Introduction\s*===', wikitext, re.IGNORECASE)
    if not intro_m:
        return results

    post    = wikitext[intro_m.end():]
    end_m   = re.search(r'\n==\s+[^=]', post)
    block   = post[:end_m.start()] if end_m else post[:6000]

    # Split by ==== {{g|...}} ==== game headers
    pattern = re.compile(r'====\s*\{\{g\|([^}|]+).*?\}\}\s*====', re.IGNORECASE)
    parts   = pattern.split(block)

    i = 1
    while i + 1 < len(parts):
        game_raw = parts[i].strip()
        section  = parts[i + 1]
        i += 2

        media_id, band, en_title = resolve_game_key(game_raw)
        if not media_id:
            continue

        prose = clean_prose(re.sub(r'\|-\|[^=]+=\s*', '', section))
        if len(prose) > 40:
            results.append({
                'game':     en_title,     # Always English display title
                'media_id': media_id,
                'band':     band,
                'text':     prose,
            })

    # Tabber fallback
    if not results:
        for m in re.finditer(
            r'\|-\|([^=\n]+)=\s*(.*?)(?=\|-\||</tabber>|\Z)', block, re.DOTALL
        ):
            media_id, band, en_title = resolve_game_key(m.group(1).strip())
            prose = clean_prose(m.group(2))
            if media_id and len(prose) > 40:
                results.append({'game': en_title, 'media_id': media_id,
                                'band': band, 'text': prose})
    return results


def extract_named_section(wikitext: str, *names: str) -> str:
    """Extract clean prose from the first matching named section."""
    for name in names:
        m = re.search(rf'===?\s*{re.escape(name)}\s*===?', wikitext, re.IGNORECASE)
        if not m:
            continue
        post  = wikitext[m.end():]
        end   = re.search(r'\n===?\s+[^=]', post)
        block = post[:end.start()] if end else post[:3000]
        prose = clean_prose(block)
        if len(prose) > 30:
            return prose
    return ''


def extract_lead(wikitext: str) -> str:
    """Extract the entity's defining lead sentence (after the infobox)."""
    infobox = extract_infobox_raw(wikitext)
    rest    = wikitext[len(infobox):] if infobox else wikitext
    rest    = re.sub(r'\{\{Q\|.*?\}\}', '', rest, flags=re.DOTALL)
    for line in rest.split('\n'):
        s = line.strip()
        if s.startswith("'''") and len(s) > 30:
            return clean_prose(s)
    for line in rest.split('\n'):
        s = clean_prose(line)
        if len(s) > 50 and not s.startswith('='):
            return s
    return ''


# ── Build structured record ───────────────────────────────────────────────────
def build_structured_record(entity_id: str, entity_type: str,
                            display_name: str, wikitext: str) -> dict:
    """
    Build a fully structured dict for this entity.
    No wiki formatting. No prose templates. Just data.
    """
    record = {
        'entity_id':   entity_id,
        'type':        entity_type,
        'name':        display_name,
    }

    # Infobox metadata
    meta = extract_metadata(wikitext)
    if meta:
        record['metadata'] = meta

    # Lead sentence
    lead = extract_lead(wikitext)
    if lead:
        record['lead'] = lead

    # Per-game history (characters)
    if entity_type == 'character':
        history = extract_per_game_history(wikitext)
        if history:
            record['history'] = history

    # Appearance / personality (characters, staff)
    if entity_type in ('character', 'staff'):
        app = extract_named_section(wikitext, 'Appearance')
        if app:
            record['appearance'] = app
        per = extract_named_section(wikitext, 'Personality')
        if per:
            record['personality'] = per

    # Background (factions, locations, events, concepts)
    if entity_type in ('faction', 'location', 'event', 'concept'):
        bg = extract_named_section(wikitext, 'Background', 'Description',
                                   'Overview', 'History', 'Profile')
        if bg:
            record['background'] = bg

    # Quest structure
    if entity_type == 'quest':
        meta_q = extract_metadata(wikitext)
        record['metadata'] = meta_q  # game, type, length, rewards

    return record


def derive_spoiler_band(record: dict) -> int:
    """Derive the entity's spoiler band from its history entries."""
    band = 10
    for entry in record.get('history', []):
        band = max(band, entry.get('band', 10))
    # Fallback: check metadata game field
    meta_game = record.get('metadata', {}).get('game', '')
    if meta_game:
        _, b, _ = resolve_game_key(meta_game)
        band = max(band, b)
    return band if band > 0 else 20


# ── Write structured record to DB ─────────────────────────────────────────────
def write_to_db(record: dict, cursor, dry_run: bool) -> dict:
    entity_id   = record['entity_id']
    entity_type = record['type']
    band        = derive_spoiler_band(record)
    summary     = {'history_entries': 0, 'chunks': 0}

    if dry_run:
        summary['history_entries'] = len(record.get('history', []))
        summary['chunks'] = sum(1 for k in ('lead', 'appearance', 'personality', 'background')
                                if k in record)
        return summary

    # ── Store structured data in entity_registry.notes ───────────────────────
    # Merge with any existing notes (don't overwrite keys from earlier passes)
    existing_row = cursor.execute(
        'SELECT notes FROM entity_registry WHERE entity_id = ?', (entity_id,)
    ).fetchone()
    existing = {}
    if existing_row and existing_row[0]:
        try:
            existing = json.loads(existing_row[0])
        except (json.JSONDecodeError, TypeError):
            existing = {}

    # New data takes precedence (richer)
    merged = {**existing}
    if 'metadata' in record:
        merged['metadata'] = {**existing.get('metadata', {}), **record['metadata']}
    for k in ('lead', 'appearance', 'personality', 'background', 'history'):
        if k in record:
            merged[k] = record[k]

    cursor.execute(
        'UPDATE entity_registry SET notes = ? WHERE entity_id = ?',
        (json.dumps(merged, ensure_ascii=False), entity_id)
    )

    # ── Write FTS-searchable text chunks ─────────────────────────────────────
    linked = json.dumps([entity_id])

    # Lead chunk
    if record.get('lead'):
        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry
            (chunk_id, source_id, linked_entity_ids, text_content,
             language, chunk_type, spoiler_band)
            VALUES (?, ?, ?, ?, 'en', 'lead', ?)
        ''', (f"lead:{entity_id}", SOURCE_ID, linked, record['lead'], band))
        summary['chunks'] += 1

    # Per-game history chunks (one per game entry)
    for entry in record.get('history', []):
        chunk_id = f"history:{entity_id}:{entry['media_id']}"
        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry
            (chunk_id, source_id, linked_entity_ids, text_content,
             language, chunk_type, spoiler_band, media_id)
            VALUES (?, ?, ?, ?, 'en', 'history', ?, ?)
        ''', (chunk_id, SOURCE_ID, linked,
              entry['text'],           # clean prose, no headers
              entry['band'],
              entry['media_id']))
        summary['history_entries'] += 1
        summary['chunks'] += 1

    # Appearance chunk
    if record.get('appearance'):
        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry
            (chunk_id, source_id, linked_entity_ids, text_content,
             language, chunk_type, spoiler_band)
            VALUES (?, ?, ?, ?, 'en', 'appearance', ?)
        ''', (f"appearance:{entity_id}", SOURCE_ID, linked,
              record['appearance'][:2000], band))
        summary['chunks'] += 1

    # Personality chunk
    if record.get('personality'):
        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry
            (chunk_id, source_id, linked_entity_ids, text_content,
             language, chunk_type, spoiler_band)
            VALUES (?, ?, ?, ?, 'en', 'personality', ?)
        ''', (f"personality:{entity_id}", SOURCE_ID, linked,
              record['personality'][:2000], band))
        summary['chunks'] += 1

    # Background chunk (factions/locations/concepts)
    if record.get('background'):
        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry
            (chunk_id, source_id, linked_entity_ids, text_content,
             language, chunk_type, spoiler_band)
            VALUES (?, ?, ?, ?, 'en', 'background', ?)
        ''', (f"background:{entity_id}", SOURCE_ID, linked,
              record['background'][:3000], band))
        summary['chunks'] += 1

    # ── Promote lifecycle ─────────────────────────────────────────────────────
    cursor.execute('''
        INSERT OR REPLACE INTO lifecycle_registry
        (object_id, state, reviewer_notes)
        VALUES (?, 'normalized', 'Phase 21: structured history enrichment')
    ''', (entity_id,))

    return summary


# ── Main ──────────────────────────────────────────────────────────────────────
def run(entity_type_filter: str | None, batch_size: int, dry_run: bool):
    if not MIRROR_PATH.exists():
        print(f"[ERROR] Mirror not found at {MIRROR_PATH}")
        print("  Enrichment requires the raw mirror. Do not delete it yet.")
        return

    with open(MIRROR_PATH, 'r', encoding='utf-8') as f:
        mirror = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Pick entities still in 'raw' state
    query = '''
        SELECT e.entity_id, e.entity_type, e.english_display_name
        FROM entity_registry e
        LEFT JOIN lifecycle_registry l ON e.entity_id = l.object_id
        WHERE (l.state = 'raw' OR l.state IS NULL)
    '''
    params = []
    if entity_type_filter:
        query += ' AND e.entity_type = ?'
        params.append(entity_type_filter)
    query += f' ORDER BY e.entity_type, e.english_display_name LIMIT {batch_size}'

    cursor.execute(query, params)
    entities = cursor.fetchall()

    if not entities:
        print("All entities are normalized. Nothing to do.")
        conn.close()
        return

    print(f"Enriching {len(entities)} entities  [batch={batch_size}"
          f"{', type=' + entity_type_filter if entity_type_filter else ''}]"
          f"{'  [DRY RUN]' if dry_run else ''}")

    from collections import Counter
    type_dist = Counter(e['entity_type'] for e in entities)
    for t, c in type_dist.most_common():
        print(f"  {t}: {c}")
    print()

    totals = {'enriched': 0, 'no_wikitext': 0, 'history_entries': 0, 'chunks': 0}

    for row in entities:
        eid   = row['entity_id']
        etype = row['entity_type']
        name  = row['english_display_name']

        wikitext = mirror.get(name, '')
        if not wikitext:
            totals['no_wikitext'] += 1
            if not dry_run:
                cursor.execute('''
                    INSERT OR REPLACE INTO lifecycle_registry
                    (object_id, state, reviewer_notes)
                    VALUES (?, 'normalized', 'Phase 21: not in mirror (pre-existing entity)')
                ''', (eid,))
            continue

        record  = build_structured_record(eid, etype, name, wikitext)
        summary = write_to_db(record, cursor, dry_run)
        totals['enriched']         += 1
        totals['history_entries']  += summary['history_entries']
        totals['chunks']           += summary['chunks']

    if not dry_run:
        conn.commit()

    # Remaining count
    remaining_q = '''
        SELECT COUNT(*) FROM entity_registry e
        LEFT JOIN lifecycle_registry l ON e.entity_id = l.object_id
        WHERE (l.state = 'raw' OR l.state IS NULL)
    '''
    if entity_type_filter:
        remaining_q += f" AND e.entity_type = '{entity_type_filter}'"
    remaining = conn.execute(remaining_q).fetchone()[0]
    conn.close()

    print("=" * 55)
    print(f"  Enriched             : {totals['enriched']:>5,}")
    print(f"  No wikitext (skip)   : {totals['no_wikitext']:>5,}")
    print(f"  Per-game history     : {totals['history_entries']:>5,}")
    print(f"  Chunks written       : {totals['chunks']:>5,}")
    print(f"  Still raw            : {remaining:>5,}")
    if remaining > 0:
        print(f"\n  Run again to continue the next batch.")
    else:
        print(f"\n  All entities normalized.")
    print("=" * 55)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--type',    dest='entity_type', default=None)
    parser.add_argument('--batch',   type=int, default=150)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(args.entity_type, args.batch, args.dry_run)
