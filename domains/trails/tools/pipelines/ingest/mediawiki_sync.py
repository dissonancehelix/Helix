"""
mediawiki_sync.py
Zemurian Index — MediaWiki Incremental Sync Pipeline

Checks registered MediaWiki sources for pages changed since last fetch.
Fetches updated content, routes through the page classifier, and writes
raw updates into chunk_registry.

Protection rules:
  - Entities with lifecycle state 'curated' or 'export_ready' are NOT
    overwritten. Source changes are stored as chunk_type='raw_bio_update'
    with a note flagging curator review.
  - Entities at 'raw' or 'normalized' lifecycle state: raw_bio chunk is
    updated in place.
  - source_registry.last_fetched_at is updated on successful completion.

Supported source modes:
  recentchanges  — polls the MediaWiki recentchanges API to find all pages
                   edited since last_fetched_at (used for Kiseki Fandom wiki)
  specific_pages — checks revision timestamps for a fixed set of pages and
                   re-fetches only those that have changed (used for JA Wikipedia)

Usage:
  python mediawiki_sync.py                              # sync all configured sources
  python mediawiki_sync.py --source wiki:kiseki_fandom  # sync one source
  python mediawiki_sync.py --dry-run                    # report what would change, no writes
  python mediawiki_sync.py --lookback-days 30           # override default lookback window
  python mediawiki_sync.py --full                       # ignore last_fetched_at, sync all pages
"""

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Import shared parsing utilities from parse_full_mirror ────────────────────
# These handle page classification, wikitext cleaning, spoiler band detection,
# and the GAME_MAP. No need to duplicate them here.
sys.path.insert(0, str(Path(__file__).parent))
from parse_full_mirror import (
    classify_page,
    clean_wikitext,
    slugify,
    extract_debut_game,
    extract_japanese_name,
    detect_spoiler_band,
)

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / 'retrieval' / 'index' / 'trails.db'

USER_AGENT  = 'ZemurianIndexBot/1.0 (Zemurian Index; kiseki lore atlas; contact via project)'
BATCH_SIZE  = 50    # MediaWiki max titles per query for unregistered bots
DELAY_EN    = 0.5   # seconds between requests to Fandom
DELAY_JA    = 1.0   # seconds between requests to JA Wikipedia (stricter limits)

# ── Source configuration ───────────────────────────────────────────────────────
# Keyed by source_id as registered in source_registry.
SOURCE_CONFIGS = {
    'wiki:kiseki_fandom': {
        'api_url':              'https://kiseki.fandom.com/api.php',
        'language':             'en',
        'trust_tier':           2,
        'request_delay':        DELAY_EN,
        'mode':                 'recentchanges',
        'namespace':            0,          # Main namespace only
        'default_lookback_days': 7,
    },
    'wiki:ja_wikipedia_series': {
        'api_url':              'https://ja.wikipedia.org/w/api.php',
        'language':             'ja',
        'trust_tier':           1,
        'request_delay':        DELAY_JA,
        'mode':                 'specific_pages',
        'handler':              'ja_aggregate',   # aggregate page, not individual entity
        'chunk_type':           'series_overview',
        'spoiler_band':         0,
        'pages':                ['英雄伝説 軌跡シリーズ'],
        'default_lookback_days': 30,
    },
    'wiki:ja_wikipedia_characters': {
        'api_url':              'https://ja.wikipedia.org/w/api.php',
        'language':             'ja',
        'trust_tier':           1,
        'request_delay':        DELAY_JA,
        'mode':                 'specific_pages',
        'handler':              'ja_aggregate',
        'chunk_type':           'character_list',  # triggers JP name backfill
        'spoiler_band':         75,
        'pages':                ['英雄伝説 軌跡シリーズの登場人物'],
        'default_lookback_days': 30,
    },
    'wiki:ja_wikipedia_timeline': {
        'api_url':              'https://ja.wikipedia.org/w/api.php',
        'language':             'ja',
        'trust_tier':           1,
        'request_delay':        DELAY_JA,
        'mode':                 'specific_pages',
        'handler':              'ja_aggregate',
        'chunk_type':           'timeline',        # triggers year-chunked storage
        'spoiler_band':         75,
        'pages':                ['英雄伝説 軌跡シリーズの年表'],
        'default_lookback_days': 30,
    },
}


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_sync_columns(conn: sqlite3.Connection):
    """Add last_fetched_at and last_rev_id to source_registry if absent.
    Creates sync_log if it doesn't exist. Safe to call every run."""
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(source_registry)')
    existing = {row[1] for row in cur.fetchall()}

    if 'last_fetched_at' not in existing:
        cur.execute('ALTER TABLE source_registry ADD COLUMN last_fetched_at TEXT')
    if 'last_rev_id' not in existing:
        cur.execute('ALTER TABLE source_registry ADD COLUMN last_rev_id INTEGER')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS sync_log (
            run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id       TEXT NOT NULL,
            started_at      TEXT NOT NULL,
            completed_at    TEXT,
            pages_checked   INTEGER DEFAULT 0,
            pages_new       INTEGER DEFAULT 0,
            pages_updated   INTEGER DEFAULT 0,
            pages_curated   INTEGER DEFAULT 0,
            pages_skipped   INTEGER DEFAULT 0,
            errors          INTEGER DEFAULT 0,
            dry_run         INTEGER DEFAULT 0,
            notes           TEXT
        )
    ''')
    conn.commit()


def get_last_fetched(conn: sqlite3.Connection, source_id: str) -> str | None:
    row = conn.execute(
        'SELECT last_fetched_at FROM source_registry WHERE source_id = ?',
        (source_id,)
    ).fetchone()
    return row['last_fetched_at'] if row else None


def set_last_fetched(conn: sqlite3.Connection, source_id: str, timestamp: str):
    conn.execute(
        'UPDATE source_registry SET last_fetched_at = ? WHERE source_id = ?',
        (timestamp, source_id)
    )
    conn.commit()


def is_curated(conn: sqlite3.Connection, entity_id: str) -> bool:
    """Returns True if the entity has a lifecycle state of curated or export_ready."""
    row = conn.execute(
        "SELECT state FROM lifecycle_registry WHERE object_id = ?",
        (entity_id,)
    ).fetchone()
    return row is not None and row['state'] in ('curated', 'export_ready')


def entity_exists(conn: sqlite3.Connection, entity_id: str) -> bool:
    return conn.execute(
        'SELECT 1 FROM entity_registry WHERE entity_id = ?', (entity_id,)
    ).fetchone() is not None


def start_sync_log(conn: sqlite3.Connection, source_id: str, dry_run: bool) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        '''INSERT INTO sync_log (source_id, started_at, dry_run)
           VALUES (?, ?, ?)''',
        (source_id, now, int(dry_run))
    )
    conn.commit()
    return cur.lastrowid


def finish_sync_log(conn: sqlite3.Connection, run_id: int, counts: dict, notes: str = None):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute('''
        UPDATE sync_log SET
            completed_at  = ?,
            pages_checked = ?,
            pages_new     = ?,
            pages_updated = ?,
            pages_curated = ?,
            pages_skipped = ?,
            errors        = ?,
            notes         = ?
        WHERE run_id = ?
    ''', (
        now,
        counts.get('checked', 0),
        counts.get('new', 0),
        counts.get('updated', 0),
        counts.get('curated_flagged', 0),
        counts.get('skipped', 0),
        counts.get('errors', 0),
        notes,
        run_id,
    ))
    conn.commit()


# ── MediaWiki API client ───────────────────────────────────────────────────────

def api_get(api_url: str, params: dict, delay: float = 0.5) -> dict | None:
    """Single GET request to a MediaWiki API endpoint. Returns parsed JSON or None."""
    params['format'] = 'json'
    params['formatversion'] = '2'
    # Use quote_via=quote with safe='|' so pipe-separated multi-value fields
    # (titles, rvprop, rcprop, etc.) are not percent-encoded as %7C.
    # MediaWiki's API requires literal | as a value separator.
    url = f"{api_url}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe='|')}"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            time.sleep(delay)
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f'  [HTTP {e.code}] {url[:80]}')
        time.sleep(delay * 4)  # back off on error
        return None
    except Exception as e:
        print(f'  [ERROR] {e}')
        time.sleep(delay * 2)
        return None


def get_recent_changes(
    api_url: str,
    since: str,
    namespace: int = 0,
    delay: float = DELAY_EN,
) -> list[dict]:
    """
    Returns a deduplicated list of {title, timestamp, revid} for all pages
    in the given namespace edited since `since` (ISO 8601 UTC string).
    Follows API continuation automatically.
    """
    changed: dict[str, dict] = {}  # title → latest entry (dedup by title)
    continue_params: dict = {}

    while True:
        params = {
            'action':    'query',
            'list':      'recentchanges',
            'rcstart':   since,
            'rcdir':     'newer',           # oldest-to-newest from our start point
            'rclimit':   500,
            'rcprop':    'title|timestamp|ids',
            'rctype':    'edit|new',
            'rcnamespace': namespace,
            **continue_params,
        }
        data = api_get(api_url, params, delay)
        if not data:
            break

        for entry in data.get('query', {}).get('recentchanges', []):
            title = entry.get('title', '')
            if not title:
                continue
            # Keep only the most recent revision for each title
            existing = changed.get(title)
            if not existing or entry['timestamp'] > existing['timestamp']:
                changed[title] = {
                    'title':     title,
                    'timestamp': entry['timestamp'],
                    'revid':     entry.get('revid'),
                }

        # Pagination
        if 'continue' in data:
            continue_params = data['continue']
        else:
            break

    return list(changed.values())


def get_page_revision_timestamp(
    api_url: str,
    title: str,
    delay: float = DELAY_JA,
) -> tuple[str | None, int | None]:
    """Returns (ISO timestamp, revid) of the current revision of a page, or (None, None)."""
    data = api_get(api_url, {
        'action': 'query',
        'titles': title,
        'prop':   'revisions',
        'rvprop': 'ids|timestamp',
        'rvlimit': 1,
    }, delay)
    if not data:
        return None, None
    pages = data.get('query', {}).get('pages', [])
    if not pages or 'missing' in pages[0]:
        return None, None
    revs = pages[0].get('revisions', [])
    if not revs:
        return None, None
    return revs[0].get('timestamp'), revs[0].get('revid')


def fetch_pages_batch(
    api_url: str,
    titles: list[str],
    delay: float = DELAY_EN,
) -> dict[str, dict]:
    """
    Batch-fetch wikitext content for up to BATCH_SIZE pages per request.
    Returns {title: {content, timestamp, revid}}.
    """
    results: dict[str, dict] = {}

    for i in range(0, len(titles), BATCH_SIZE):
        batch = titles[i : i + BATCH_SIZE]
        data = api_get(api_url, {
            'action':  'query',
            'titles':  '|'.join(batch),
            'prop':    'revisions',
            'rvprop':  'content|timestamp|ids',
            'rvslots': 'main',
            # rvlimit omitted: not permitted when querying multiple pages simultaneously
        }, delay)
        if not data:
            continue

        for page in data.get('query', {}).get('pages', []):
            if 'missing' in page:
                continue
            title = page.get('title', '')
            revs  = page.get('revisions', [])
            if not revs:
                continue
            rev     = revs[0]
            content = rev.get('slots', {}).get('main', {}).get('content', '')
            results[title] = {
                'content':   content,
                'timestamp': rev.get('timestamp'),
                'revid':     rev.get('revid'),
            }

    return results


# ── Page ingestion ────────────────────────────────────────────────────────────

def ingest_page(
    conn: sqlite3.Connection,
    title: str,
    page_data: dict,
    source_id: str,
    language: str,
    dry_run: bool,
) -> str:
    """
    Classify and ingest a single page. Returns one of:
      'new'            — entity created, raw chunk written
      'updated'        — existing non-curated entity chunk refreshed
      'curated_flagged'— entity is curated; change stored as raw_bio_update for review
      'skipped'        — redirect, nav page, or too short
      'error'          — exception during processing
    """
    wikitext  = page_data.get('content', '')
    timestamp = page_data.get('timestamp', '')
    revid     = page_data.get('revid')

    if not wikitext or len(wikitext) < 30:
        return 'skipped'

    try:
        cls = classify_page(title, wikitext)
    except Exception as e:
        print(f'  [CLASSIFY ERROR] {title}: {e}')
        return 'error'

    if cls['skip']:
        return 'skipped'

    if cls['is_redirect']:
        # Redirects: update alias only, don't create a chunk
        target = cls.get('redirect_target')
        if target and not dry_run:
            _update_redirect_alias(conn, title, target)
        return 'skipped'

    entity_type = cls['entity_type']
    id_prefix   = cls['id_prefix']
    entity_id   = f"{id_prefix}{slugify(title)}"

    ja_name               = extract_japanese_name(title, wikitext)
    debut_media, debut_band = extract_debut_game(wikitext)
    spoiler_band          = detect_spoiler_band(wikitext, debut_band) or 20
    raw_prose             = clean_wikitext(wikitext)

    if not raw_prose or len(raw_prose) < 30:
        return 'skipped'

    if dry_run:
        existing = entity_exists(conn, entity_id)
        curated  = is_curated(conn, entity_id) if existing else False
        if curated:
            return 'curated_flagged'
        return 'updated' if existing else 'new'

    cur = conn.cursor()

    # ── Entity registry (INSERT OR IGNORE — never overwrite display name) ─────
    existing = entity_exists(conn, entity_id)
    if not existing:
        cur.execute('''
            INSERT OR IGNORE INTO entity_registry (
                entity_id, entity_type, english_display_name, japanese_name
            ) VALUES (?, ?, ?, ?)
        ''', (entity_id, entity_type, title, ja_name))
        outcome = 'new'
    else:
        # Backfill japanese_name if still missing
        if ja_name:
            cur.execute('''
                UPDATE entity_registry
                SET japanese_name = ?
                WHERE entity_id = ? AND (japanese_name IS NULL OR japanese_name = '')
            ''', (ja_name, entity_id))
        outcome = 'updated'

    # ── Chunk handling — protect curated entries ──────────────────────────────
    if is_curated(conn, entity_id):
        # Store the source update separately so the curator can review it
        update_chunk_id = f"raw_update:{entity_id}:{revid or timestamp[:10]}"
        cur.execute('''
            INSERT OR REPLACE INTO chunk_registry (
                chunk_id, source_id, linked_entity_ids,
                text_content, language, chunk_type, spoiler_band
            ) VALUES (?, ?, ?, ?, ?, 'raw_bio_update', ?)
        ''', (
            update_chunk_id, source_id,
            json.dumps([entity_id]),
            raw_prose, language, spoiler_band
        ))
        outcome = 'curated_flagged'
    else:
        chunk_id = f"raw:{entity_id}"
        cur.execute('''
            INSERT OR REPLACE INTO chunk_registry (
                chunk_id, source_id, linked_entity_ids,
                text_content, language, chunk_type, spoiler_band
            ) VALUES (?, ?, ?, ?, ?, 'raw_bio', ?)
        ''', (
            chunk_id, source_id,
            json.dumps([entity_id]),
            raw_prose, language, spoiler_band
        ))

        # Lifecycle: set to raw if brand new, leave existing state alone
        if not existing:
            cur.execute('''
                INSERT OR IGNORE INTO lifecycle_registry (object_id, state, reviewer_notes)
                VALUES (?, 'raw', ?)
            ''', (entity_id, f'Synced from {source_id} at {timestamp}'))

    # ── Appearance link ───────────────────────────────────────────────────────
    if debut_media and not existing:
        row = cur.execute(
            'SELECT 1 FROM media_registry WHERE media_id = ?', (debut_media,)
        ).fetchone()
        if row:
            cur.execute('''
                INSERT OR IGNORE INTO appearance_registry (
                    entity_id, media_id, appearance_type, debut_flag, spoiler_band, source_id
                ) VALUES (?, ?, 'main', 1, ?, ?)
            ''', (entity_id, debut_media, spoiler_band, source_id))

    conn.commit()
    return outcome


def _update_redirect_alias(conn: sqlite3.Connection, redirect_title: str, target_title: str):
    """Resolve a redirect as an alias on the target entity."""
    target_slug = slugify(target_title)
    row = conn.execute('''
        SELECT entity_id, aliases FROM entity_registry
        WHERE english_display_name = ? OR entity_id LIKE ?
        LIMIT 1
    ''', (target_title, f'%{target_slug}%')).fetchone()

    if not row:
        return

    entity_id  = row['entity_id']
    try:
        aliases = json.loads(row['aliases']) if row['aliases'] else []
    except (json.JSONDecodeError, TypeError):
        aliases = []

    if redirect_title not in aliases:
        aliases.append(redirect_title)
        conn.execute(
            'UPDATE entity_registry SET aliases = ? WHERE entity_id = ?',
            (json.dumps(aliases), entity_id)
        )
        conn.commit()


# ── Source sync orchestrators ─────────────────────────────────────────────────

def sync_recentchanges(
    conn: sqlite3.Connection,
    source_id: str,
    config: dict,
    since: str,
    dry_run: bool,
) -> dict:
    """Sync a source using the recentchanges API (Fandom wiki)."""
    api_url   = config['api_url']
    language  = config['language']
    namespace = config.get('namespace', 0)
    delay     = config['request_delay']

    counts = {'checked': 0, 'new': 0, 'updated': 0,
              'curated_flagged': 0, 'skipped': 0, 'errors': 0}

    print(f'  Fetching recent changes since {since} ...')
    changed = get_recent_changes(api_url, since, namespace, delay)
    print(f'  Found {len(changed)} changed pages')

    if not changed:
        return counts

    titles = [p['title'] for p in changed]
    counts['checked'] = len(titles)

    print(f'  Fetching content in batches of {BATCH_SIZE} ...')
    pages = fetch_pages_batch(api_url, titles, delay)
    print(f'  Retrieved {len(pages)} pages')

    for title, page_data in pages.items():
        result = ingest_page(conn, title, page_data, source_id, language, dry_run)
        counts[result] = counts.get(result, 0) + 1

        if result == 'curated_flagged':
            print(f'  [REVIEW] {title} (curated entry — update stored as raw_bio_update)')
        elif result == 'error':
            print(f'  [ERROR]  {title}')

    return counts


def _extract_ja_name_pairs(wikitext: str) -> list[tuple[str, str]]:
    """Extract (en_name, ja_name) pairs from a JA Wikipedia character list page."""
    pairs = []
    # Pattern: JP name（English Name）
    for m in re.finditer(
        r'([\u3000-\u9fff\uff00-\uffef\u3040-\u30ff・ー]+)'
        r'[（(【](?:[^）)】]*?)'
        r'([A-Z][a-zA-Z\s\-\'\.]+)'
        r'[）)】]',
        wikitext
    ):
        ja = m.group(1).strip('・ー \t')
        en = m.group(2).strip()
        if len(ja) >= 2 and len(en) >= 3:
            pairs.append((en, ja))
    # Pattern: table cell | JP || EN
    for m in re.finditer(
        r'\|\s*([\u3040-\u30ff\u4e00-\u9fff]+[^\|]*?)\s*\|\|\s*([A-Z][a-zA-Z\s\-\'\.]{2,40})',
        wikitext
    ):
        ja = m.group(1).strip()
        en = m.group(2).strip()
        if len(ja) >= 2 and len(en) >= 3 and en[0].isupper():
            pairs.append((en, ja))
    # Deduplicate by EN name
    seen, result = set(), []
    for en, ja in pairs:
        if en.lower() not in seen:
            seen.add(en.lower())
            result.append((en, ja))
    return result


def _extract_timeline_chunks(wikitext: str, source_id: str, spoiler_band: int) -> list[dict]:
    """Split a JA Wikipedia timeline page into year/section chunks."""
    chunks = []
    sections = re.split(r'==+\s*(.+?)\s*==+', wikitext)
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        body   = sections[i + 1].strip() if i + 1 < len(sections) else ''
        body   = re.sub(r'\{\{[^}]+\}\}', '', body)
        body   = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', body)
        body   = re.sub(r'<[^>]+>', '', body)
        body   = re.sub(r'\s+', ' ', body).strip()
        if len(body) > 50:
            safe_header = re.sub(r'[^a-z0-9]', '_', header.lower())[:40]
            chunks.append({
                'chunk_id':    f"jatime:{safe_header}",
                'source_id':   source_id,
                'text_content': f"[{header}] {body[:3000]}",
                'language':    'ja',
                'chunk_type':  'timeline',
                'spoiler_band': spoiler_band,
            })
    return chunks


def ingest_ja_aggregate_page(
    conn: sqlite3.Connection,
    title: str,
    page_data: dict,
    source_id: str,
    chunk_type: str,
    spoiler_band: int,
    dry_run: bool,
) -> str:
    """
    Ingest a JA Wikipedia aggregate page (series overview, character list, timeline).

    These are NOT individual entities. They are stored as Japanese substrate chunks
    and used to backfill entity_registry.japanese_name where possible.
    No new entity_registry rows are created.

    Returns 'updated' on success, 'skipped' if too short, 'error' on failure.
    """
    wikitext  = page_data.get('content', '')
    timestamp = page_data.get('timestamp', '')

    if not wikitext or len(wikitext) < 100:
        return 'skipped'

    # Clean the wikitext for storage
    clean = re.sub(r'\{\{[^}]+\}\}', '', wikitext)
    clean = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', clean)
    clean = re.sub(r'<[^>]+>', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if dry_run:
        name_pairs = _extract_ja_name_pairs(wikitext) if chunk_type == 'character_list' else []
        print(f'  [DRY RUN] Would store JA chunk for: {title}')
        if name_pairs:
            print(f'            Would backfill JP names for up to {len(name_pairs)} characters')
        return 'updated'

    cur = conn.cursor()

    # Store the full page as a JA substrate chunk
    full_chunk_id = f"raw:{source_id.replace(':', '_')}_full"
    cur.execute('''
        INSERT OR REPLACE INTO chunk_registry (
            chunk_id, source_id, text_content, language, chunk_type, spoiler_band
        ) VALUES (?, ?, ?, 'ja', ?, ?)
    ''', (full_chunk_id, source_id, clean[:8000], chunk_type, spoiler_band))

    # Character list: extract JP name pairs and backfill entity_registry.japanese_name
    if chunk_type == 'character_list':
        pairs = _extract_ja_name_pairs(wikitext)
        backfilled = 0
        for en_name, ja_name in pairs:
            row = cur.execute('''
                SELECT entity_id, japanese_name, aliases FROM entity_registry
                WHERE lower(english_display_name) = lower(?) AND entity_type = 'character'
                LIMIT 1
            ''', (en_name,)).fetchone()
            if row:
                eid = row['entity_id']
                if not row['japanese_name']:
                    cur.execute(
                        'UPDATE entity_registry SET japanese_name = ? WHERE entity_id = ?',
                        (ja_name, eid)
                    )
                    backfilled += 1
                try:
                    aliases = json.loads(row['aliases']) if row['aliases'] else []
                except (json.JSONDecodeError, TypeError):
                    aliases = []
                if ja_name not in aliases:
                    aliases.append(ja_name)
                    cur.execute(
                        'UPDATE entity_registry SET aliases = ? WHERE entity_id = ?',
                        (json.dumps(aliases, ensure_ascii=False), eid)
                    )
        print(f'  JP names backfilled: {backfilled} / {len(pairs)} pairs found')

    # Timeline: split into year chunks
    if chunk_type == 'timeline':
        year_chunks = _extract_timeline_chunks(wikitext, source_id, spoiler_band)
        for tc in year_chunks:
            cur.execute('''
                INSERT OR REPLACE INTO chunk_registry (
                    chunk_id, source_id, text_content, language, chunk_type, spoiler_band
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (tc['chunk_id'], tc['source_id'], tc['text_content'],
                  tc['language'], tc['chunk_type'], tc['spoiler_band']))
        print(f'  Timeline chunks stored: {len(year_chunks)}')

    # Mark source as updated
    cur.execute(
        "UPDATE source_registry SET ingestion_status = 'complete', parse_status = 'complete' WHERE source_id = ?",
        (source_id,)
    )
    conn.commit()
    return 'updated'


def sync_specific_pages(
    conn: sqlite3.Connection,
    source_id: str,
    config: dict,
    since: str,
    dry_run: bool,
) -> dict:
    """Sync a fixed set of pages by checking their current revision timestamp."""
    api_url   = config['api_url']
    language  = config['language']
    delay     = config['request_delay']
    handler   = config.get('handler', 'default')
    pages_to_check = config.get('pages', [])

    counts = {'checked': 0, 'new': 0, 'updated': 0,
              'curated_flagged': 0, 'skipped': 0, 'errors': 0}

    for page_title in pages_to_check:
        counts['checked'] += 1
        print(f'  Checking: {page_title}')

        rev_ts, revid = get_page_revision_timestamp(api_url, page_title, delay)
        if not rev_ts:
            print(f'  [WARN] Could not get revision info for: {page_title}')
            counts['errors'] += 1
            continue

        if rev_ts <= since:
            print(f'  No change since {since[:10]} (current rev: {rev_ts[:10]})')
            counts['skipped'] += 1
            continue

        print(f'  Changed: {since[:10]} → {rev_ts[:10]} — fetching content ...')
        pages = fetch_pages_batch(api_url, [page_title], delay)
        if page_title not in pages:
            print(f'  [ERROR] Failed to fetch: {page_title}')
            counts['errors'] += 1
            continue

        page_data = pages[page_title]

        if handler == 'ja_aggregate':
            result = ingest_ja_aggregate_page(
                conn, page_title, page_data,
                source_id,
                chunk_type=config.get('chunk_type', 'series_overview'),
                spoiler_band=config.get('spoiler_band', 0),
                dry_run=dry_run,
            )
        else:
            result = ingest_page(conn, page_title, page_data, source_id, language, dry_run)

        counts[result] = counts.get(result, 0) + 1

        if result == 'curated_flagged':
            print(f'  [REVIEW] {page_title} — curated, update stored for review')

    return counts


# ── Main sync entry point ─────────────────────────────────────────────────────

def sync_source(
    conn: sqlite3.Connection,
    source_id: str,
    config: dict,
    dry_run: bool,
    force_lookback_days: int | None = None,
    full: bool = False,
):
    print(f'\n{"="*60}')
    print(f'  Source: {source_id}')
    print(f'  Mode:   {config["mode"]}  |  Dry run: {dry_run}')
    print(f'{"="*60}')

    # Determine the `since` timestamp
    if full:
        # Full resync: go back far enough to catch everything
        since = '2010-01-01T00:00:00Z'
        print(f'  Full resync mode — since {since}')
    else:
        last_fetched = get_last_fetched(conn, source_id)
        if last_fetched:
            since = last_fetched
            print(f'  Last fetched: {last_fetched}')
        else:
            days = force_lookback_days or config['default_lookback_days']
            since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
            print(f'  First sync — looking back {days} days (since {since})')

    run_id = start_sync_log(conn, source_id, dry_run)
    now    = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        mode = config['mode']
        if mode == 'recentchanges':
            counts = sync_recentchanges(conn, source_id, config, since, dry_run)
        elif mode == 'specific_pages':
            counts = sync_specific_pages(conn, source_id, config, since, dry_run)
        else:
            print(f'  [ERROR] Unknown mode: {mode}')
            counts = {'errors': 1}

        # Update last_fetched_at to now (only on real runs)
        if not dry_run:
            set_last_fetched(conn, source_id, now)

        finish_sync_log(conn, run_id, counts)

        # Summary
        print()
        print(f'  checked        : {counts.get("checked", 0):>5}')
        print(f'  new entities   : {counts.get("new", 0):>5}')
        print(f'  updated        : {counts.get("updated", 0):>5}')
        print(f'  curated/review : {counts.get("curated_flagged", 0):>5}')
        print(f'  skipped        : {counts.get("skipped", 0):>5}')
        print(f'  errors         : {counts.get("errors", 0):>5}')
        if dry_run:
            print('  [DRY RUN — no writes committed]')
        else:
            print(f'  last_fetched_at updated → {now}')

    except Exception as e:
        print(f'  [FATAL] {e}')
        finish_sync_log(conn, run_id, {}, notes=str(e))
        raise


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='Zemurian Index — MediaWiki incremental sync pipeline'
    )
    p.add_argument(
        '--source', metavar='SOURCE_ID',
        help='Sync only this source (e.g. wiki:kiseki_fandom). Default: all configured sources.'
    )
    p.add_argument(
        '--dry-run', action='store_true',
        help='Report what would be fetched and written without committing any changes.'
    )
    p.add_argument(
        '--lookback-days', type=int, metavar='N',
        help='Override default lookback window for sources with no last_fetched_at.'
    )
    p.add_argument(
        '--full', action='store_true',
        help='Ignore last_fetched_at and sync all pages (effectively a full re-ingest).'
    )
    p.add_argument(
        '--list-sources', action='store_true',
        help='Print configured sources and their last_fetched_at timestamps, then exit.'
    )
    return p


def list_sources(conn: sqlite3.Connection):
    print('\nConfigured sync sources:\n')
    for source_id, config in SOURCE_CONFIGS.items():
        last = get_last_fetched(conn, source_id)
        mode = config['mode']
        print(f'  {source_id}')
        print(f'    mode         : {mode}')
        print(f'    api_url      : {config["api_url"]}')
        print(f'    last_fetched : {last or "(never)"}')
        print()


def main():
    args = build_arg_parser().parse_args()

    conn = get_db()
    ensure_sync_columns(conn)

    if args.list_sources:
        list_sources(conn)
        conn.close()
        return

    sources_to_sync = {}
    if args.source:
        if args.source not in SOURCE_CONFIGS:
            print(f'[ERROR] Unknown source: {args.source}')
            print(f'Available: {", ".join(SOURCE_CONFIGS)}')
            sys.exit(1)
        sources_to_sync[args.source] = SOURCE_CONFIGS[args.source]
    else:
        sources_to_sync = SOURCE_CONFIGS

    for source_id, config in sources_to_sync.items():
        sync_source(
            conn,
            source_id,
            config,
            dry_run=args.dry_run,
            force_lookback_days=args.lookback_days,
            full=args.full,
        )

    conn.close()
    print('\nSync complete.')


if __name__ == '__main__':
    main()
