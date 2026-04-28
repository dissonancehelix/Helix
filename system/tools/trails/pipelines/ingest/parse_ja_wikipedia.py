"""
parse_ja_wikipedia.py
Phase 20 — Japanese Wikipedia Ingestion

Fetches and parses the three Japanese Wikipedia Kiseki pages registered in source_registry:
  1. 英雄伝説 軌跡シリーズ          — Main series overview (media metadata, studio notes)
  2. 英雄伝説 軌跡シリーズの登場人物  — Character list (JP names, roles, game mapping)
  3. 英雄伝説 軌跡シリーズの年表     — Series timeline / chronology

What this does:
  - Backfills japanese_name on existing entity_registry rows where it's NULL
  - Inserts Japanese-name aliases
  - Stores raw page content as chunks for retrieval
  - Does NOT create new entities — only enriches existing ones

Trust tier: 1 (Wikipedia — higher than Fandom fan wiki at tier 2)
"""

import json
import re
import sqlite3
import time
import urllib.request
import urllib.parse
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / 'retrieval' / 'index' / 'trails.db'
CACHE_DIR = ROOT / 'corpus' / 'wiki'

WIKIPEDIA_API = 'https://ja.wikipedia.org/w/api.php'

SOURCES = [
    {
        'source_id': 'wiki:ja_wikipedia_series',
        'page_title': '英雄伝説 軌跡シリーズ',
        'cache_file': 'ja_wikipedia_series.json',
        'chunk_type': 'series_overview',
        'spoiler_band': 0,
    },
    {
        'source_id': 'wiki:ja_wikipedia_characters',
        'page_title': '英雄伝説 軌跡シリーズの登場人物',
        'cache_file': 'ja_wikipedia_characters.json',
        'chunk_type': 'character_list',
        'spoiler_band': 75,  # Contains Daybreak II content
    },
    {
        'source_id': 'wiki:ja_wikipedia_timeline',
        'page_title': '英雄伝説 軌跡シリーズの年表',
        'cache_file': 'ja_wikipedia_timeline.json',
        'chunk_type': 'timeline',
        'spoiler_band': 75,
    },
]


# ── Wikipedia API fetch ───────────────────────────────────────────────────────
def fetch_wikitext(page_title: str) -> str | None:
    params = urllib.parse.urlencode({
        'action': 'query',
        'titles': page_title,
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main',
        'format': 'json',
        'formatversion': '2',
    })
    url = f"{WIKIPEDIA_API}?{params}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'HelixTrailsBot/1.0 (research project; kiseki lore substrate)'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', [])
            if pages:
                page = pages[0]
                if 'missing' in page:
                    print(f"  [WARN] Page not found: {page_title}")
                    return None
                return page.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
    except Exception as e:
        print(f"  [ERROR] Fetch failed for '{page_title}': {e}")
        return None


# ── Name extraction from JP character list ────────────────────────────────────
def extract_ja_name_pairs(wikitext: str) -> list[tuple[str, str]]:
    """
    Finds patterns like:
      == エステル・ブライト ==  (section header = JP name)
      ===エステル・ブライト（Estelle Bright）===

    Or table rows:
      | エステル・ブライト || Estelle Bright

    Returns list of (en_name, ja_name) tuples.
    """
    pairs = []

    # Pattern 1: Japanese name (English Name) in parentheses
    # e.g. エステル・ブライト（エステル・ブライト、Estelle Bright）
    for m in re.finditer(
        r'([\u3000-\u9fff\uff00-\uffef\u3040-\u30ff・ー]+)'   # JP name
        r'[（(【]'
        r'(?:[^）)】]*?)'                                       # optional kana/note
        r'([A-Z][a-zA-Z\s\-\'\.]+)'                           # English Name
        r'[）)】]',
        wikitext
    ):
        ja = m.group(1).strip('・ー \t')
        en = m.group(2).strip()
        if len(ja) >= 2 and len(en) >= 3:
            pairs.append((en, ja))

    # Pattern 2: Table cells — | JP || EN
    for m in re.finditer(
        r'\|\s*([\u3040-\u30ff\u4e00-\u9fff]+[^\|]*?)\s*\|\|\s*([A-Z][a-zA-Z\s\-\'\.]{2,40})',
        wikitext
    ):
        ja = m.group(1).strip()
        en = m.group(2).strip()
        if len(ja) >= 2 and len(en) >= 3 and en[0].isupper():
            pairs.append((en, ja))

    # Deduplicate
    seen = set()
    result = []
    for en, ja in pairs:
        key = en.lower()
        if key not in seen:
            seen.add(key)
            result.append((en, ja))
    return result


def extract_timeline_chunks(wikitext: str, source_id: str, spoiler_band: int) -> list[dict]:
    """
    Splits the timeline wikitext by year/section into retrievable chunks.
    Each chunk covers one year or era block.
    """
    chunks = []
    sections = re.split(r'==+\s*(.+?)\s*==+', wikitext)

    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        body = sections[i + 1].strip() if i + 1 < len(sections) else ''

        # Clean body
        body = re.sub(r'\{\{[^}]+\}\}', '', body)
        body = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', body)
        body = re.sub(r'<[^>]+>', '', body)
        body = re.sub(r'\s+', ' ', body).strip()

        if len(body) > 50:
            chunks.append({
                'chunk_id': f"jatime:{re.sub(r'[^a-z0-9]', '_', header.lower())[:40]}",
                'source_id': source_id,
                'text_content': f"[{header}] {body[:3000]}",
                'language': 'ja',
                'chunk_type': 'timeline',
                'spoiler_band': spoiler_band,
            })
    return chunks


# ── Main run ──────────────────────────────────────────────────────────────────
def run():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_name_backfills = 0
    total_chunks_added = 0

    for src in SOURCES:
        source_id  = src['source_id']
        page_title = src['page_title']
        cache_path = CACHE_DIR / src['cache_file']
        chunk_type = src['chunk_type']
        band       = src['spoiler_band']

        print(f"\nProcessing: {page_title}")
        print(f"  Source: {source_id}")

        # Load from cache or fetch
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                wikitext = json.load(f).get('wikitext', '')
            print(f"  Loaded from cache: {cache_path.name}")
        else:
            print(f"  Fetching from Wikipedia API...")
            wikitext = fetch_wikitext(page_title)
            time.sleep(1)  # polite
            if not wikitext:
                print(f"  [SKIP] Could not fetch content.")
                continue
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({'title': page_title, 'wikitext': wikitext}, f,
                          ensure_ascii=False, indent=2)
            print(f"  Cached → {cache_path.name} ({len(wikitext):,} chars)")

        # ── Update source status ─────────────────────────────────────────────
        cursor.execute('''
            UPDATE source_registry
            SET ingestion_status = 'complete', parse_status = 'in_progress'
            WHERE source_id = ?
        ''', (source_id,))

        # ── Store full page as a single retrievable chunk ────────────────────
        clean = re.sub(r'\{\{[^}]+\}\}', '', wikitext)
        clean = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', clean)
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        full_chunk_id = f"raw:{source_id.replace(':', '_')}_full"
        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry (
                chunk_id, source_id, text_content, language, chunk_type, spoiler_band
            ) VALUES (?, ?, ?, 'ja', ?, ?)
        ''', (full_chunk_id, source_id, clean[:8000], chunk_type, band))
        total_chunks_added += 1

        # ── Character name page: backfill japanese_name ──────────────────────
        if chunk_type == 'character_list':
            pairs = extract_ja_name_pairs(wikitext)
            print(f"  Found {len(pairs)} EN→JP name pairs")

            backfilled = 0
            for en_name, ja_name in pairs:
                # Try exact match first
                cursor.execute('''
                    SELECT entity_id, japanese_name, aliases
                    FROM entity_registry
                    WHERE english_display_name = ? AND entity_type = 'character'
                ''', (en_name,))
                row = cursor.fetchone()

                # Fuzzy: try case-insensitive
                if not row:
                    cursor.execute('''
                        SELECT entity_id, japanese_name, aliases
                        FROM entity_registry
                        WHERE lower(english_display_name) = lower(?) AND entity_type = 'character'
                    ''', (en_name,))
                    row = cursor.fetchone()

                if row:
                    eid, current_ja, aliases_json = row
                    # Backfill if empty
                    if not current_ja:
                        cursor.execute(
                            'UPDATE entity_registry SET japanese_name = ? WHERE entity_id = ?',
                            (ja_name, eid)
                        )
                        backfilled += 1

                    # Add to aliases if not already present
                    try:
                        aliases = json.loads(aliases_json) if aliases_json else []
                    except (json.JSONDecodeError, TypeError):
                        aliases = []
                    if ja_name not in aliases:
                        aliases.append(ja_name)
                        cursor.execute(
                            'UPDATE entity_registry SET aliases = ? WHERE entity_id = ?',
                            (json.dumps(aliases, ensure_ascii=False), eid)
                        )

            print(f"  Backfilled japanese_name on {backfilled} characters")
            total_name_backfills += backfilled

        # ── Timeline page: split into year chunks ────────────────────────────
        if chunk_type == 'timeline':
            timeline_chunks = extract_timeline_chunks(wikitext, source_id, band)
            for tc in timeline_chunks:
                cursor.execute('''
                    INSERT OR REPLACE INTO chunk_registry (
                        chunk_id, source_id, text_content,
                        language, chunk_type, spoiler_band
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    tc['chunk_id'], tc['source_id'], tc['text_content'],
                    tc['language'], tc['chunk_type'], tc['spoiler_band']
                ))
            total_chunks_added += len(timeline_chunks)
            print(f"  Inserted {len(timeline_chunks)} timeline chunks")

        # ── Mark source parse complete ───────────────────────────────────────
        cursor.execute(
            "UPDATE source_registry SET parse_status = 'complete' WHERE source_id = ?",
            (source_id,)
        )

    conn.commit()
    conn.close()

    print()
    print("=" * 50)
    print("  JA Wikipedia Parse Complete")
    print(f"  JP name backfills : {total_name_backfills}")
    print(f"  Chunks added      : {total_chunks_added}")
    print("=" * 50)


if __name__ == '__main__':
    run()
