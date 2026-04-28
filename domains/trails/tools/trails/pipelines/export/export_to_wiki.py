"""
export_to_wiki.py
Phase 21 — Structured JSON → Wiki / Markdown Export

Converts the structured JSON stored in entity_registry.notes back into
formatted output. The JSON is the source of truth; this script is purely
a renderer.

Supported formats:
  --format wiki      MediaWiki markup (for Fandom-style wiki import)
  --format markdown  Standard Markdown (for docs, GitHub, registry site)
  --format jsonl     One JSON object per line (for RAG / registry ingestion)

Usage:
    python export_to_wiki.py --type character --format markdown --out export/characters.md
    python export_to_wiki.py --entity char:estelle_bright --format wiki
    python export_to_wiki.py --type faction --format jsonl --out export/factions.jsonl
    python export_to_wiki.py --format jsonl --out export/full_registry.jsonl

Spoiler safety: defaults to band < 100 (excludes Kai content).
Use --unsafe to include Band 100.
"""

import argparse
import json
import sqlite3
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / 'retrieval' / 'index' / 'trails.db'


# ── Renderers ─────────────────────────────────────────────────────────────────
def render_markdown(entity: dict, record: dict) -> str:
    lines = []

    # Header
    name = entity['english_display_name']
    ja   = entity.get('japanese_name') or ''
    lines.append(f"## {name}")
    if ja:
        lines.append(f"*{ja}*\n")

    # Lead
    if record.get('lead'):
        lines.append(record['lead'])
        lines.append('')

    # Metadata table
    meta = record.get('metadata', {})
    if meta:
        lines.append('### Profile')
        lines.append('')
        lines.append('| Field | Value |')
        lines.append('|---|---|')
        label_map = {
            'age': 'Age', 'birth_date': 'Birth Date', 'birth_place': 'Birth Place',
            'nationality': 'Nationality', 'affiliation': 'Affiliation',
            'occupation': 'Occupation', 'gender': 'Gender', 'height': 'Height',
            'status': 'Status', 'weapon': 'Weapon', 'voice_jp': 'Voice (JP)',
            'voice_en': 'Voice (EN)', 'relatives': 'Relatives',
            'likes': 'Likes', 'dislikes': 'Dislikes', 'hobbies': 'Hobbies',
            'founder': 'Founder', 'founded': 'Founded', 'location': 'Location',
            'capital': 'Capital', 'leadership': 'Leadership',
            'game': 'Game', 'quest_type': 'Type', 'quest_length': 'Length',
            'rewards': 'Rewards',
        }
        for key, label in label_map.items():
            if meta.get(key):
                val = meta[key].replace('\n', ' ').replace('|', '\\|')
                lines.append(f'| {label} | {val} |')
        lines.append('')

    # Appearance
    if record.get('appearance'):
        lines.append('### Appearance')
        lines.append('')
        lines.append(record['appearance'])
        lines.append('')

    # Personality
    if record.get('personality'):
        lines.append('### Personality')
        lines.append('')
        lines.append(record['personality'])
        lines.append('')

    # Background (factions/locations)
    if record.get('background'):
        lines.append('### Background')
        lines.append('')
        lines.append(record['background'])
        lines.append('')

    # Per-game history
    history = record.get('history', [])
    if history:
        lines.append('### History')
        lines.append('')
        for entry in history:
            lines.append(f"**{entry['game']}**")
            lines.append('')
            lines.append(entry['text'])
            lines.append('')

    # Appearances
    appearances = entity.get('appearances', [])
    if appearances:
        lines.append('### Appearances')
        lines.append('')
        lines.append('| Title | Type | Debut |')
        lines.append('|---|---|---|')
        for app in appearances:
            debut = '★' if app.get('debut_flag') else ''
            lines.append(f"| {app['english_title']} | {app.get('appearance_type', '')} | {debut} |")
        lines.append('')

    lines.append('---')
    return '\n'.join(lines)


def render_wiki(entity: dict, record: dict) -> str:
    """MediaWiki markup format."""
    lines = []
    name = entity['english_display_name']
    ja   = entity.get('japanese_name') or ''

    # Lead
    lead = record.get('lead', f"{name} is a character in the Trails series.")
    if ja:
        # Bold name + JP in parentheses on first mention
        lead = lead.replace(f"'''{name}'''", f"'''{name}''' ({ja})", 1)
        if f"'''{name}'''" not in lead:
            lead = f"'''{name}''' ({ja}) — {lead}"
    lines.append(lead)
    lines.append('')

    # Metadata as infobox
    meta = record.get('metadata', {})
    if meta:
        lines.append('{{Infobox character')
        field_map = {
            'age': 'age', 'birth_date': 'birthDate', 'birth_place': 'birthPlace',
            'nationality': 'nationality', 'affiliation': 'affilliation',
            'occupation': 'occupation', 'gender': 'gender', 'height': 'height',
            'status': 'status', 'weapon': 'weapon', 'voice_jp': 'seiyuu',
            'voice_en': 'voiceactor', 'relatives': 'relatives',
        }
        for our_key, wiki_key in field_map.items():
            if meta.get(our_key):
                lines.append(f'|{wiki_key} = {meta[our_key]}')
        lines.append('}}')
        lines.append('')

    # Appearance section
    if record.get('appearance'):
        lines.append('== Appearance ==')
        lines.append(record['appearance'])
        lines.append('')

    # Personality section
    if record.get('personality'):
        lines.append('== Personality ==')
        lines.append(record['personality'])
        lines.append('')

    # Background (factions/locations)
    if record.get('background'):
        lines.append('== Background ==')
        lines.append(record['background'])
        lines.append('')

    # History section (per-game)
    history = record.get('history', [])
    if history:
        lines.append('== History ==')
        lines.append('')
        for entry in history:
            lines.append(f"=== {entry['game']} ===")
            lines.append(entry['text'])
            lines.append('')

    return '\n'.join(lines)


def render_jsonl(entity: dict, record: dict) -> str:
    """Single-line JSON object for JSONL registry export."""
    out = {
        'entity_id':    entity['entity_id'],
        'type':         entity['entity_type'],
        'name':         entity['english_display_name'],
        'japanese_name': entity.get('japanese_name'),
        'aliases':      _parse_json_field(entity.get('aliases')),
        'lead':         record.get('lead'),
        'metadata':     record.get('metadata', {}),
        'appearance':   record.get('appearance'),
        'personality':  record.get('personality'),
        'background':   record.get('background'),
        'history':      record.get('history', []),
        'appearances':  entity.get('appearances', []),
    }
    # Drop None values for cleanliness
    out = {k: v for k, v in out.items() if v is not None and v != [] and v != {}}
    return json.dumps(out, ensure_ascii=False)


def _parse_json_field(val):
    if not val:
        return []
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []


# ── DB fetch helpers ──────────────────────────────────────────────────────────
def fetch_entities(cursor, entity_type: str | None, entity_id: str | None,
                   safe: bool) -> list[dict]:
    query = '''
        SELECT e.entity_id, e.entity_type, e.english_display_name,
               e.japanese_name, e.aliases, e.notes
        FROM entity_registry e
        WHERE 1=1
    '''
    params = []
    if entity_id:
        query += ' AND e.entity_id = ?'
        params.append(entity_id)
    if entity_type:
        query += ' AND e.entity_type = ?'
        params.append(entity_type)
    query += ' ORDER BY e.entity_type, e.english_display_name'
    cursor.execute(query, params)
    rows = cursor.fetchall()

    entities = []
    for row in rows:
        entity = dict(row)
        # Parse notes → record
        record = {}
        if entity.get('notes'):
            try:
                record = json.loads(entity['notes'])
            except (json.JSONDecodeError, TypeError):
                record = {}

        # Filter history by spoiler band
        if safe and record.get('history'):
            record['history'] = [h for h in record['history'] if h.get('band', 0) < 100]

        # Fetch appearances
        cursor.execute('''
            SELECT m.english_title, a.appearance_type, a.debut_flag, a.spoiler_band
            FROM appearance_registry a
            JOIN media_registry m ON a.media_id = m.media_id
            WHERE a.entity_id = ?
            ORDER BY m.release_chronology
        ''', (entity['entity_id'],))
        apps = cursor.fetchall()
        if safe:
            apps = [a for a in apps if (a['spoiler_band'] or 0) < 100]
        entity['appearances'] = [dict(a) for a in apps]
        entity['_record'] = record
        entities.append(entity)

    return entities


# ── Main ──────────────────────────────────────────────────────────────────────
def run(entity_type: str | None, entity_id: str | None,
        fmt: str, out_path: str | None, safe: bool):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    entities = fetch_entities(cursor, entity_type, entity_id, safe)
    conn.close()

    if not entities:
        print('No entities found matching those filters.')
        return

    print(f"Rendering {len(entities)} entities as {fmt.upper()}"
          f"{'  [SAFE — Kai excluded]' if safe else '  [FULL — includes Kai]'}")

    output_lines = []

    if fmt == 'markdown':
        if not entity_id:
            output_lines.append(f"# Helix Trails Domain Export\n")
        for e in entities:
            output_lines.append(render_markdown(e, e['_record']))

    elif fmt == 'wiki':
        for e in entities:
            output_lines.append(f"<!-- {e['entity_id']} -->")
            output_lines.append(render_wiki(e, e['_record']))
            output_lines.append('')

    elif fmt == 'jsonl':
        for e in entities:
            output_lines.append(render_jsonl(e, e['_record']))

    result = '\n'.join(output_lines)

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(result, encoding='utf-8')
        print(f"Written → {out_path}  ({len(result):,} chars)")
    else:
        print(result[:4000])
        if len(result) > 4000:
            print(f'\n... [{len(result) - 4000:,} chars truncated — use --out to write full output]')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--type',   dest='entity_type', default=None,
                        help='Filter by entity_type')
    parser.add_argument('--entity', dest='entity_id',   default=None,
                        help='Export a single entity by ID')
    parser.add_argument('--format', dest='fmt', default='markdown',
                        choices=['markdown', 'wiki', 'jsonl'])
    parser.add_argument('--out',    default=None,
                        help='Output file path (prints to console if omitted)')
    parser.add_argument('--unsafe', action='store_true',
                        help='Include Band 100 (Kai) content')
    args = parser.parse_args()
    run(args.entity_type, args.entity_id, args.fmt,
        args.out, safe=not args.unsafe)
