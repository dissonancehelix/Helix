"""
ingest_titd_dialogue.py
Phase 22 — TrailsInTheDatabase.com Dialogue Ingestion

Fetches official English (+ Japanese parallel) script lines from:
  https://trailsinthedatabase.com/api/script/search/?p={page}&q={query}

Strategy: search by character display name for every character entity.
Stores results as chunk_type='dialogue' with full bilingual metadata.

Each chunk stores:
  - English line (primary text_content for FTS)
  - Japanese line in notes JSON
  - Speaker name (EN + JP)
  - Game title (English), media_id, spoiler_band
  - Scene file + row number for provenance

Resumable: tracks ingested characters in lifecycle_registry
  (state = 'dialogue_ingested'). Run again to continue from where it left off.

Usage:
    python ingest_titd_dialogue.py [--batch N] [--dry-run] [--search TERM]

    --batch    : characters per session (default 50, to stay polite)
    --dry-run  : show what would be fetched without writing
    --search   : fetch a single search term instead of iterating characters

Rate limit: 1 second between API pages. Be a good citizen.
"""

import argparse
import hashlib
import json
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / 'retrieval' / 'index' / 'trails.db'

TITD_SEARCH = 'https://trailsinthedatabase.com/api/script/search/?p={page}&q={query}'
SOURCE_ID   = 'titd:en_script_v1'

# TITD game ID → (media_id, spoiler_band, english_title)
GAME_MAP = {
    1:  ('sky_fc',    10, 'Trails in the Sky'),
    2:  ('sky_sc',    12, 'Trails in the Sky SC'),
    3:  ('sky_3rd',   14, 'Trails in the Sky the 3rd'),
    4:  ('zero',      20, 'Trails from Zero'),
    5:  ('azure',     22, 'Trails to Azure'),
    6:  ('cs1',       40, 'Trails of Cold Steel'),
    7:  ('cs2',       42, 'Trails of Cold Steel II'),
    8:  ('cs3',       50, 'Trails of Cold Steel III'),
    9:  ('cs4',       55, 'Trails of Cold Steel IV'),
    10: ('reverie',   65, 'Trails into Reverie'),
    11: ('daybreak',  70, 'Trails Through Daybreak'),
}

HEADERS = {'User-Agent': 'HelixTrailsBot/1.0 (kiseki lore substrate; respectful crawler)'}


def clean_html(text: str) -> str:
    text = re.sub(r'<br\s*/?>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\x0f', '').replace('\x00', '')
    return re.sub(r'\s+', ' ', text).strip()


def chunk_id_for(entity_id: str, game_id: int, fname: str, row: int) -> str:
    key = f"{entity_id}:{game_id}:{fname}:{row}"
    h   = hashlib.md5(key.encode()).hexdigest()[:12]
    return f"dialogue:{h}"


def fetch_page(query: str, page: int) -> list[dict]:
    url = TITD_SEARCH.format(page=page, query=urllib.parse.quote(query))
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode('utf-8'))
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"    [WARN] Page {page} fetch error: {e}")
        return []


def ingest_results(rows: list[dict], entity_id: str, cursor,
                   dry_run: bool) -> dict[str, int]:
    counts = {'inserted': 0, 'skipped': 0, 'band100': 0}
    for row in rows:
        game_id = row.get('gameId')
        if game_id not in GAME_MAP:
            counts['skipped'] += 1
            continue

        media_id, band, en_title = GAME_MAP[game_id]
        en_text  = clean_html(row.get('engHtmlText') or row.get('engSearchText') or '')
        jp_text  = clean_html(row.get('jpnHtmlText') or row.get('jpnSearchText') or '')
        en_spkr  = clean_html(row.get('engChrName') or '')
        jp_spkr  = clean_html(row.get('jpnChrName') or '')
        fname    = row.get('fname', '')
        scene    = row.get('scene') or ''
        line_row = row.get('row', 0)

        if not en_text or len(en_text) < 5:
            counts['skipped'] += 1
            continue

        if band == 100:
            counts['band100'] += 1
            # Still store Band 100 — it's gated at retrieval time

        cid  = chunk_id_for(entity_id, game_id, fname, line_row)
        # Build notes JSON with bilingual + provenance data
        meta = {
            'speaker_en': en_spkr,
            'speaker_jp': jp_spkr,
            'jp_text':    jp_text,
            'game':       en_title,
            'media_id':   media_id,
            'scene':      scene,
            'file':       fname,
            'row':        line_row,
        }
        # Text stored for FTS: "Speaker: line" — clean, no markup
        if en_spkr:
            fts_text = f"{en_spkr}: {en_text}"
        else:
            fts_text = en_text

        if not dry_run:
            cursor.execute('''
                INSERT OR IGNORE INTO chunk_registry (
                    chunk_id, source_id, media_id, linked_entity_ids,
                    text_content, language, chunk_type, spoiler_band
                ) VALUES (?, ?, ?, ?, ?, 'en', 'dialogue', ?)
            ''', (
                cid, SOURCE_ID, media_id,
                json.dumps([entity_id]),
                fts_text, band
            ))
            # Store bilingual metadata in a parallel JP chunk
            if jp_text and len(jp_text) > 3:
                jp_cid = f"dialogue_jp:{cid[9:]}"
                cursor.execute('''
                    INSERT OR IGNORE INTO chunk_registry (
                        chunk_id, source_id, media_id, linked_entity_ids,
                        text_content, language, chunk_type, spoiler_band
                    ) VALUES (?, ?, ?, ?, ?, 'ja', 'dialogue', ?)
                ''', (
                    jp_cid, SOURCE_ID, media_id,
                    json.dumps([entity_id]),
                    f"{jp_spkr}: {jp_text}" if jp_spkr else jp_text,
                    band
                ))
            counts['inserted'] += 1
        else:
            counts['inserted'] += 1

    return counts


def ingest_character(entity_id: str, display_name: str, cursor,
                     dry_run: bool, max_pages: int = 5) -> dict:
    """Fetch and ingest all dialogue pages for one character."""
    totals = {'inserted': 0, 'skipped': 0, 'band100': 0, 'pages': 0}

    # Search by first name only if multi-word (avoids zero results for "Estelle Bright")
    # but also try full name
    search_terms = [display_name]
    parts = display_name.split()
    if len(parts) > 1 and len(parts[0]) > 2:
        search_terms.append(parts[0])

    for term in search_terms:
        for page in range(1, max_pages + 1):
            rows = fetch_page(term, page)
            if not rows:
                break
            c = ingest_results(rows, entity_id, cursor, dry_run)
            totals['inserted'] += c['inserted']
            totals['skipped']  += c['skipped']
            totals['band100']  += c['band100']
            totals['pages']    += 1
            if len(rows) < 100:
                break  # Last page
            time.sleep(1)

        # If first term got results, skip first-name fallback
        if totals['inserted'] > 0:
            break
        time.sleep(0.5)

    # Mark as dialogue_ingested in lifecycle
    if not dry_run and totals['inserted'] > 0:
        cursor.execute('''
            INSERT OR REPLACE INTO lifecycle_registry
            (object_id, state, reviewer_notes)
            VALUES (?, 'dialogue_ingested', 'TITD Phase 22: dialogue chunks added')
        ''', (entity_id,))

    return totals


# ── Main ──────────────────────────────────────────────────────────────────────
def run(batch: int, dry_run: bool, single_search: str | None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Register source
    c.execute('''
        INSERT OR IGNORE INTO source_registry (
            source_id, title, source_class, language,
            origin_url, trust_tier, ingestion_status, parse_status, spoiler_band, notes
        ) VALUES (?, ?, 'official_script', 'en',
                  'https://trailsinthedatabase.com', 0,
                  'in_progress', 'in_progress', 0,
                  'Official EN+JP script database covering all 11 released games. ~547K total lines. Trust tier 0 — official localised text.')
    ''', (SOURCE_ID,))

    # ── Single search mode ────────────────────────────────────────────────────
    if single_search:
        print(f"Single search: '{single_search}'")
        rows = fetch_page(single_search, 1)
        print(f"Results: {len(rows)}")
        for r in rows[:5]:
            mid, band, title = GAME_MAP.get(r.get('gameId'), (None, 0, '?'))
            spkr = clean_html(r.get('engChrName', ''))
            text = clean_html(r.get('engSearchText', ''))[:100]
            print(f"  [{title}] {spkr}: {text}")
        conn.close()
        return

    # ── Character iteration mode ──────────────────────────────────────────────
    # Only characters not yet dialogue_ingested
    c.execute('''
        SELECT e.entity_id, e.english_display_name
        FROM entity_registry e
        LEFT JOIN lifecycle_registry l ON e.entity_id = l.object_id
                                      AND l.state = 'dialogue_ingested'
        WHERE e.entity_type = 'character'
          AND l.object_id IS NULL
        ORDER BY e.english_display_name
        LIMIT ?
    ''', (batch,))
    characters = c.fetchall()

    if not characters:
        print("All characters have been dialogue-ingested.")
        conn.close()
        return

    # Count remaining
    c.execute('''
        SELECT COUNT(*) FROM entity_registry e
        LEFT JOIN lifecycle_registry l ON e.entity_id = l.object_id
                                      AND l.state = 'dialogue_ingested'
        WHERE e.entity_type = 'character' AND l.object_id IS NULL
    ''')
    remaining_total = c.fetchone()[0]

    print(f"Ingesting dialogue for {len(characters)} characters"
          f" ({remaining_total} remaining total)"
          f"{'  [DRY RUN]' if dry_run else ''}")
    print()

    session = {'chars': 0, 'lines': 0, 'pages': 0, 'band100': 0}

    for row in characters:
        eid  = row['entity_id']
        name = row['english_display_name']
        print(f"  {name:<30}", end='', flush=True)

        totals = ingest_character(eid, name, c, dry_run)

        band100_suffix = f", {totals['band100']} kai" if totals['band100'] else ""
        print(f"{totals['inserted']:>4} lines  "
              f"({totals['pages']} pages"
              f"{band100_suffix})")

        session['chars']   += 1
        session['lines']   += totals['inserted']
        session['pages']   += totals['pages']
        session['band100'] += totals['band100']

        if not dry_run:
            conn.commit()

    # Update source status
    if not dry_run:
        c.execute(
            "UPDATE source_registry SET ingestion_status = 'partial' WHERE source_id = ?",
            (SOURCE_ID,)
        )
        conn.commit()

    conn.close()

    # Remaining after this session
    conn2 = sqlite3.connect(DB_PATH)
    still_left = conn2.execute('''
        SELECT COUNT(*) FROM entity_registry e
        LEFT JOIN lifecycle_registry l ON e.entity_id = l.object_id
                                      AND l.state = 'dialogue_ingested'
        WHERE e.entity_type = 'character' AND l.object_id IS NULL
    ''').fetchone()[0]
    conn2.close()

    print()
    print("=" * 55)
    print(f"  Characters processed : {session['chars']:>4}")
    print(f"  Dialogue lines added : {session['lines']:>6,}")
    print(f"  API pages fetched    : {session['pages']:>4}")
    print(f"  Band 100 lines       : {session['band100']:>4}")
    print(f"  Characters remaining : {still_left:>4}")
    if still_left:
        print(f"\n  Run again to continue.")
    else:
        print(f"\n  All characters ingested.")
    print("=" * 55)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch',   type=int, default=50,
                        help='Characters per session (default 50)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--search',  default=None,
                        help='Test a single search term')
    args = parser.parse_args()
    run(args.batch, args.dry_run, args.search)
