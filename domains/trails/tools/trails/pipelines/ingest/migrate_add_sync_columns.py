"""
migrate_add_sync_columns.py
Zemurian Index — One-shot DB migration for the MediaWiki sync pipeline.

Adds:
  source_registry.last_fetched_at  TEXT  — ISO 8601 UTC timestamp of last successful sync
  source_registry.last_rev_id      INTEGER — MediaWiki revision ID at last fetch (optional,
                                             used to detect single-page changes efficiently)

Creates:
  sync_log — per-run audit table for the mediawiki_sync pipeline

Safe to re-run: uses ALTER TABLE only if the column doesn't already exist,
and CREATE TABLE IF NOT EXISTS for sync_log.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'


def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f'PRAGMA table_info({table})')
    return any(row[1] == column for row in cursor.fetchall())


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── source_registry: last_fetched_at ─────────────────────────────────────
    if not column_exists(cur, 'source_registry', 'last_fetched_at'):
        cur.execute('ALTER TABLE source_registry ADD COLUMN last_fetched_at TEXT')
        print('Added column: source_registry.last_fetched_at')
    else:
        print('Column already exists: source_registry.last_fetched_at')

    # ── source_registry: last_rev_id ─────────────────────────────────────────
    if not column_exists(cur, 'source_registry', 'last_rev_id'):
        cur.execute('ALTER TABLE source_registry ADD COLUMN last_rev_id INTEGER')
        print('Added column: source_registry.last_rev_id')
    else:
        print('Column already exists: source_registry.last_rev_id')

    # ── sync_log table ───────────────────────────────────────────────────────
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sync_log (
            run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id         TEXT NOT NULL,
            started_at        TEXT NOT NULL,
            completed_at      TEXT,
            pages_checked     INTEGER DEFAULT 0,
            pages_new         INTEGER DEFAULT 0,
            pages_updated     INTEGER DEFAULT 0,
            pages_curated     INTEGER DEFAULT 0,  -- curated entries flagged for review
            pages_skipped     INTEGER DEFAULT 0,
            errors            INTEGER DEFAULT 0,
            dry_run           INTEGER DEFAULT 0,
            notes             TEXT,
            FOREIGN KEY(source_id) REFERENCES source_registry(source_id)
        )
    ''')
    print('Table ready: sync_log')

    conn.commit()
    conn.close()
    print('\nMigration complete.')


if __name__ == '__main__':
    run()
