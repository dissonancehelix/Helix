"""
Wikipedia ingestion script for Trails series.
Fetches EN and JA Wikipedia articles for all main Trails games,
splits them into section-level chunks, and stores them in chunk_registry.
Also populates entity_summary for media: entities from the article intro.

Usage:
    python scripts/ingestion/ingest_wikipedia.py [--dry-run] [--lang en|ja|both]
"""

import sqlite3
import json
import re
import sys
import uuid
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timezone

DB_PATH = "retrieval/index/trails.db"
EN_BASE = "https://en.wikipedia.org/w/api.php"
JA_BASE = "https://ja.wikipedia.org/w/api.php"
UA = "TrailsAtlasBot/1.0 (trails-atlas research)"

# ===========================================================================
# Game article map
# EN: short title used for API lookup (redirects are followed)
# JA: exact JA Wikipedia article title
# media_ids: which DB media_ids this article covers
# ===========================================================================
EN_ARTICLES = [
    {
        "media_ids": ["sky_fc"],
        "title": "The Legend of Heroes: Trails in the Sky",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["sky_sc"],
        "title": "The Legend of Heroes: Trails in the Sky SC",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["sky_3rd"],
        "title": "The Legend of Heroes: Trails in the Sky the 3rd",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["zero"],
        "title": "Trails from Zero",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["azure"],
        "title": "Trails to Azure",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["cs1"],
        "title": "The Legend of Heroes: Trails of Cold Steel",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["cs2"],
        "title": "The Legend of Heroes: Trails of Cold Steel II",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["cs3"],
        "title": "The Legend of Heroes: Trails of Cold Steel III",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["cs4"],
        "title": "The Legend of Heroes: Trails of Cold Steel IV",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["reverie"],
        "title": "Trails into Reverie",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["daybreak"],
        "title": "Trails Through Daybreak",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["daybreak2"],
        "title": "Trails Through Daybreak 2",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["kai"],
        "title": "Trails Beyond the Horizon",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["nayuta"],
        "title": "The Legend of Nayuta: Boundless Trails",
        "spoiler_band": 2,
    },
]

JA_ARTICLES = [
    {
        "media_ids": ["sky_fc", "sky_sc", "sky_3rd"],
        "title": "英雄伝説VI 空の軌跡",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["zero", "azure"],
        "title": "英雄伝説VII",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["cs1", "cs2", "cs3", "cs4"],
        "title": "英雄伝説 閃の軌跡",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["reverie"],
        "title": "英雄伝説 創の軌跡",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["daybreak", "daybreak2"],
        "title": "英雄伝説 黎の軌跡",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["kai"],
        "title": "英雄伝説 界の軌跡 -Farewell, O Zemuria-",
        "spoiler_band": 2,
    },
    {
        "media_ids": ["akatsuki"],
        "title": "英雄伝説 暁の軌跡",
        "spoiler_band": 1,
    },
    {
        "media_ids": ["nayuta"],
        "title": "那由多の軌跡",
        "spoiler_band": 2,
    },
]

# Section title → chunk_type mapping
SECTION_TYPE_MAP = {
    # EN section names
    "gameplay": "gameplay",
    "plot": "plot",
    "story": "plot",
    "synopsis": "plot",
    "characters": "characters",
    "development": "development",
    "reception": "reception",
    "music": "development",
    "soundtrack": "development",
    "localization": "development",
    "release": "release",
    "legacy": "reception",
    "sales": "reception",
    # JA section names
    "ゲームシステム": "gameplay",
    "システム": "gameplay",
    "ストーリー": "plot",
    "あらすじ": "plot",
    "登場人物": "characters",
    "開発": "development",
    "評価": "reception",
    "売上": "reception",
    "音楽": "development",
    "リリース": "release",
}


def api_request(base, params):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{base}?{qs}", headers={"User-Agent": UA})
    resp = urllib.request.urlopen(req, timeout=20)
    return json.loads(resp.read())


def fetch_article_sections(base, title):
    """Returns list of (section_title, text) tuples. First item is ('intro', intro_text)."""
    # Get full plain-text extract with section markers
    data = api_request(base, {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "redirects": True,
        "format": "json",
    })
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    if page.get("missing") is not None:
        return None, None

    # Get the resolved title after redirect
    redirects = data["query"].get("redirects", [])
    resolved_title = redirects[-1]["to"] if redirects else title

    text = page.get("extract", "")
    if not text:
        return resolved_title, []

    # Split into sections by == markers
    # Plain text from API uses \n== Section ==\n
    section_pattern = re.compile(r'\n(={2,4})\s*(.+?)\s*\1\n', re.MULTILINE)
    sections = []

    # Find all section boundaries
    matches = list(section_pattern.finditer(text))

    # Intro text (before first section)
    intro_end = matches[0].start() if matches else len(text)
    intro_text = text[:intro_end].strip()
    if intro_text:
        sections.append(("intro", intro_text))

    # Remaining sections
    for i, m in enumerate(matches):
        section_title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        if section_text:
            sections.append((section_title, section_text))

    return resolved_title, sections


def section_to_chunk_type(section_title):
    normalized = section_title.lower().strip()
    for key, chunk_type in SECTION_TYPE_MAP.items():
        if key in normalized:
            return chunk_type
    return "lore"


def make_chunk_id(source_id, media_id, section_title):
    slug = re.sub(r'[^a-z0-9_]', '_', (section_title or 'intro').lower())[:30]
    lang = source_id.split(':')[-1] if ':' in source_id else source_id
    return f"wikipedia:{lang}:{media_id}:{slug}"


def insert_chunks(conn, sections, source_id, media_ids, language, spoiler_band, dry_run):
    c = conn.cursor()
    inserted = 0
    skipped = 0

    for section_title, text in sections:
        # Skip very short sections (likely just headers with no content)
        if len(text) < 50:
            continue

        chunk_type = section_to_chunk_type(section_title)

        for media_id in media_ids:
            chunk_id = make_chunk_id(media_id, source_id, section_title)
            linked = json.dumps([f"media:{media_id}"])

            if not dry_run:
                try:
                    c.execute(
                        """INSERT OR REPLACE INTO chunk_registry
                           (chunk_id, source_id, media_id, linked_entity_ids, text_content, language, spoiler_band, chunk_type)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (chunk_id, source_id, media_id, linked, text, language, spoiler_band, chunk_type)
                    )
                    inserted += 1
                except Exception as e:
                    print(f"  ERROR inserting {chunk_id}: {e}")
                    skipped += 1
            else:
                print(f"  [DRY] Would insert: {chunk_id} ({chunk_type}, {len(text)} chars)")
                inserted += 1

    return inserted, skipped


def update_entity_summary(conn, media_ids, intro_text, wikipedia_title, language, dry_run):
    """Update entity_summary with intro text as the summary for each media entity."""
    c = conn.cursor()

    for media_id in media_ids:
        entity_id = f"media:{media_id}"

        # Check if entity exists
        c.execute("SELECT entity_id FROM entity_registry WHERE entity_id=?", (entity_id,))
        if not c.fetchone():
            continue

        # Only update if this is the EN article or if no EN summary exists yet
        if not dry_run:
            # Check current summary
            c.execute("SELECT summary, completeness FROM entity_summary WHERE entity_id=?", (entity_id,))
            row = c.fetchone()

            if row is None:
                # Insert new
                c.execute(
                    "INSERT INTO entity_summary (entity_id, summary, completeness, updated_at) VALUES (?, ?, ?, ?)",
                    (entity_id, intro_text[:2000], 50, datetime.now(timezone.utc).isoformat())
                )
                print(f"  Created summary for {entity_id} from {wikipedia_title} ({language})")
            elif language == "en" and (row[0] is None or row[1] < 50):
                # Update with EN content if better
                c.execute(
                    "UPDATE entity_summary SET summary=?, completeness=?, updated_at=? WHERE entity_id=?",
                    (intro_text[:2000], 60, datetime.now(timezone.utc).isoformat(), entity_id)
                )
                print(f"  Updated summary for {entity_id} from {wikipedia_title}")
        else:
            print(f"  [DRY] Would update summary for {entity_id} ({len(intro_text)} chars from {wikipedia_title})")


def process_article(conn, base, article, language, dry_run):
    title = article["title"]
    media_ids = article["media_ids"]
    spoiler_band = article["spoiler_band"]
    source_id = f"wikipedia:{language}"

    print(f"\nFetching [{language.upper()}] {title}...")
    resolved_title, sections = fetch_article_sections(base, title)

    if sections is None:
        print(f"  NOT FOUND: {title}")
        return 0, 0

    print(f"  → {resolved_title}: {len(sections)} sections, {sum(len(t) for _, t in sections)} chars total")

    # Find intro text for entity_summary
    intro_text = ""
    for sec_title, text in sections:
        if sec_title == "intro":
            intro_text = text
            break

    if intro_text and language == "en":
        update_entity_summary(conn, media_ids, intro_text, resolved_title, language, dry_run)

    inserted, skipped = insert_chunks(conn, sections, source_id, media_ids, language, spoiler_band, dry_run)
    print(f"  Inserted: {inserted}, Skipped: {skipped}")
    return inserted, skipped


def main():
    parser = argparse.ArgumentParser(description="Ingest Wikipedia articles for Trails games")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--lang", choices=["en", "ja", "both"], default="both", help="Which language to ingest")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    total_inserted = 0
    total_skipped = 0

    try:
        if args.lang in ("en", "both"):
            print("\n=== Ingesting EN Wikipedia articles ===")
            for article in EN_ARTICLES:
                ins, skp = process_article(conn, EN_BASE, article, "en", args.dry_run)
                total_inserted += ins
                total_skipped += skp

        if args.lang in ("ja", "both"):
            print("\n=== Ingesting JA Wikipedia articles ===")
            for article in JA_ARTICLES:
                ins, skp = process_article(conn, JA_BASE, article, "ja", args.dry_run)
                total_inserted += ins
                total_skipped += skp

        if not args.dry_run:
            conn.commit()
            print(f"\n✓ Committed. Total inserted: {total_inserted}, skipped: {total_skipped}")
        else:
            print(f"\n[DRY RUN] Would insert: {total_inserted} chunks")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
