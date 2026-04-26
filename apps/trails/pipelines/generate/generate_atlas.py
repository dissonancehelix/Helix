#!/usr/bin/env python3
"""
Atlas generation pipeline.

For each entity, gathers all chunks from chunk_registry,
sends to Claude API, and stores the synthesized Atlas document
in entity_summary.summary + advances lifecycle_registry state.

Usage:
    python generate_atlas.py                  # process all entities missing summaries
    python generate_atlas.py --entity char:estelle_bright  # single entity
    python generate_atlas.py --type character --limit 10   # batch by type
    python generate_atlas.py --dry-run        # show prompt without calling API

Requirements:
    ANTHROPIC_API_KEY environment variable
    pip install anthropic
"""
import sqlite3, sys, json, os, re, time
import argparse
from datetime import datetime, timezone
from pathlib import Path

DB = 'C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'

# Chunk type priority for ordering context (most important first)
CHUNK_PRIORITY = {
    'lead': 0, 'background': 1, 'history': 2, 'personality': 3,
    'appearance': 4, 'dialogue': 5, 'lore': 6, 'timeline': 7,
}

# Section labels for the Atlas prompt
SECTION_LABELS = {
    'lead':        'Overview',
    'background':  'Background',
    'history':     'History',
    'personality': 'Personality',
    'appearance':  'Appearance',
    'dialogue':    'Dialogue / Notable Quotes',
    'lore':        'Lore',
    'timeline':    'Timeline',
}

SYSTEM_PROMPT = """\
You are a Zemurian Index curator. Your task is to synthesize source chunks into a \
single comprehensive, authoritative Atlas entry for a Trails series entity.

Rules:
- Write in compressed encyclopedic prose — load-bearing sentences, no filler
- Present tense for identity/role; past tense for completed events
- Use XSEED/NISA localized names exclusively
- Organize by: Overview → Background → History (chronological by arc) → Personality → Appearance → Lore
- Omit sections with no source content
- Suppress details beyond spoiler_band threshold (keep to band 0 content unless instructed otherwise)
- Do not invent details not in the source chunks
- Do not use wiki markup; write clean prose
- Keep the entry focused on the entity itself, not on game mechanics unless the entity IS a mechanic

Output format:
== Overview ==
[1-3 sentences: who/what this entity is and why it matters]

== Background ==
[Origin, context, pre-story information]

== History ==
=== [Arc name] ===
[Events during that arc, one subsection per game]

== Personality ==
[For characters: traits, disposition, relationships]

== Appearance ==
[Physical description if meaningful]

== Lore ==
[World-building context, thematic significance, meta information]

Omit any section that has no meaningful source content. Do not add a section just to have it.\
"""

def get_entity_chunks(c, entity_id, max_chars=12000):
    """Gather and order chunks for an entity.

    For JA chunks: uses translated_content when available (produced by
    scripts/translation/translate_ja_chunks.py), falling back to raw
    text_content. Untranslated JA chunks are skipped — raw Japanese is
    opaque to the EN synthesis prompt.
    """
    c.execute("""
        SELECT chunk_id, chunk_type, language, spoiler_band, text_content,
               translated_content
        FROM chunk_registry
        WHERE linked_entity_ids LIKE ?
        ORDER BY spoiler_band, chunk_type
    """, (f'%{entity_id}%',))
    rows = c.fetchall()

    # Deduplicate by content (some chunks may be near-identical)
    seen_texts = set()
    chunks = []
    for chunk_id, ctype, lang, band, text, translated in rows:
        # For JA chunks: use translation if available, skip if not
        if lang == 'ja':
            if not translated or not translated.strip():
                continue  # skip untranslated JA — raw text is opaque to EN prompt
            effective_text = translated
            effective_lang = 'ja_translated'
        else:
            if not text or len(text) < 20:
                continue
            effective_text = text
            effective_lang = lang or 'en'

        sig = effective_text[:200]
        if sig in seen_texts:
            continue
        seen_texts.add(sig)
        chunks.append((chunk_id, ctype or 'background', effective_lang, band or 0, effective_text))

    # Sort: spoiler_band first, then chunk type priority, then EN before JA_translated
    chunks.sort(key=lambda r: (
        r[3],
        CHUNK_PRIORITY.get(r[1], 99),
        0 if r[2] == 'en' else 1
    ))

    # Build context string, respecting max_chars
    sections = {}
    total = 0
    for chunk_id, ctype, lang, band, text in chunks:
        label = SECTION_LABELS.get(ctype, ctype.title())
        if lang == 'ja_translated':
            label = f"[JA Wikipedia] {label}"
        if label not in sections:
            sections[label] = []
        sections[label].append(text)
        total += len(text)
        if total >= max_chars:
            break

    return sections, len(chunks)

def build_prompt(entity_id, entity_type, display_name, sections, appearances):
    """Build the user prompt with entity context."""
    lines = [
        f"Entity: {display_name}",
        f"ID: {entity_id}",
        f"Type: {entity_type}",
    ]
    if appearances:
        lines.append(f"Appears in: {', '.join(appearances)}")
    lines.append("")
    lines.append("Source chunks:")
    lines.append("---")

    for label, texts in sections.items():
        lines.append(f"\n[{label}]")
        for text in texts:
            lines.append(text[:3000])  # cap individual chunk size

    lines.append("---")
    lines.append("\nWrite the Atlas entry for this entity.")
    return '\n'.join(lines)

def generate_atlas_entry(client, entity_id, entity_type, display_name, sections, appearances, dry_run=False):
    """Call Claude API to generate Atlas entry."""
    prompt = build_prompt(entity_id, entity_type, display_name, sections, appearances)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"PROMPT FOR: {display_name} ({entity_id})")
        print('='*60)
        print(prompt[:2000])
        print("... [truncated]" if len(prompt) > 2000 else "")
        return "[DRY RUN — no API call]"

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--entity', help='Process a single entity_id')
    parser.add_argument('--type', help='Process all entities of this type')
    parser.add_argument('--limit', type=int, default=None, help='Max entities to process')
    parser.add_argument('--dry-run', action='store_true', help='Show prompt, skip API call')
    parser.add_argument('--min-completeness', type=int, default=40,
                        help='Only process entities with completeness >= N (default 40)')
    args = parser.parse_args()

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Setup Anthropic client
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key and not args.dry_run:
        print("ERROR: ANTHROPIC_API_KEY not set. Use --dry-run to test without API.")
        sys.exit(1)

    client = None
    if not args.dry_run:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

    # Select entities to process
    if args.entity:
        c.execute("""
            SELECT e.entity_id, e.entity_type, e.english_display_name, s.completeness
            FROM entity_registry e
            LEFT JOIN entity_summary s ON s.entity_id = e.entity_id
            WHERE e.entity_id = ?
        """, (args.entity,))
    else:
        type_filter = f"AND e.entity_type = '{args.type}'" if args.type else ""
        c.execute(f"""
            SELECT e.entity_id, e.entity_type, e.english_display_name, COALESCE(s.completeness, 0)
            FROM entity_registry e
            LEFT JOIN entity_summary s ON s.entity_id = e.entity_id
            WHERE (s.summary IS NULL OR s.summary = '')
              AND COALESCE(s.completeness, 0) >= {args.min_completeness}
              {type_filter}
            ORDER BY COALESCE(s.completeness, 0) DESC, e.entity_type
            {f'LIMIT {args.limit}' if args.limit else ''}
        """)

    entities = c.fetchall()
    print(f"Entities to process: {len(entities)}")

    # Load appearance map
    c.execute("SELECT entity_id, game_id FROM entity_appearances")
    appearances_map = {}
    for eid, gid in c.fetchall():
        appearances_map.setdefault(eid, []).append(gid)

    processed = 0
    errors = 0

    for entity_id, entity_type, display_name, completeness in entities:
        print(f"\n[{processed+1}/{len(entities)}] {display_name} ({entity_id}) — completeness={completeness}")

        sections, chunk_count = get_entity_chunks(c, entity_id)
        if not sections:
            print(f"  No chunks — skipping")
            continue

        appearances = appearances_map.get(entity_id, [])
        print(f"  {chunk_count} chunks, {len(sections)} section types, {len(appearances)} appearances")

        try:
            atlas_text = generate_atlas_entry(
                client, entity_id, entity_type, display_name,
                sections, appearances, dry_run=args.dry_run
            )

            if not args.dry_run:
                # Store in entity_summary
                now = datetime.now(timezone.utc).isoformat()
                c.execute("""
                    INSERT INTO entity_summary (entity_id, summary, completeness, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(entity_id) DO UPDATE SET
                        summary=excluded.summary,
                        updated_at=excluded.updated_at
                """, (entity_id, atlas_text, completeness, now))

                # Advance lifecycle_registry if present
                c.execute("""
                    UPDATE lifecycle_registry SET status='normalized', updated_at=?
                    WHERE object_id=? AND status='raw'
                """, (now, entity_id))

                conn.commit()
                print(f"  Stored ({len(atlas_text)} chars)")
                time.sleep(0.5)  # rate limit courtesy
            else:
                print(f"  [dry-run] Would store {len(atlas_text)} chars")

            processed += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1
            if errors > 5:
                print("Too many errors, stopping.")
                break

    print(f"\nDone. Processed: {processed}, Errors: {errors}")

    if not args.dry_run and processed > 0:
        c.execute("SELECT COUNT(*) FROM entity_summary WHERE summary IS NOT NULL AND summary != ''")
        print(f"Total entities with Atlas entries: {c.fetchone()[0]}")

    conn.close()

if __name__ == '__main__':
    main()
