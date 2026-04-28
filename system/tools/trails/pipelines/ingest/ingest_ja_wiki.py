#!/usr/bin/env python3
"""
JA Wikipedia ingestion pipeline.

Parses corpus/wiki/ja_wikipedia_characters.json wikitext into chunk_registry.

Structure: ; {{Vanc|JA Name}} followed by :-prefixed content lines.
Maps JA name → entity_id via aliases table + name similarity fallback.
Stores chunks with language='ja', source_id='ja_wikipedia', chunk_type='background'.
"""
import sqlite3, json, re, unicodedata
from pathlib import Path

BASE    = Path('C:/Users/dissonance/Desktop/Trails')
DB      = str(BASE / 'retrieval/index/trails.db')
CORPUS  = BASE / 'corpus/wiki'

conn = sqlite3.connect(DB)
c = conn.cursor()

# -----------------------------------------------------------------------
# Build lookup: JA name → entity_id
# Primary: extract JA names from existing chunk text ('''EN Name''' (JA名))
# Secondary: aliases table + english display names
# -----------------------------------------------------------------------
JA_PARENS = re.compile(r"'''[^']+'''.*?\(([^)]{2,40})\)")
KATAKANA   = re.compile(r'[\u30A0-\u30FF]')

name_to_eid = {}

# From chunk text — most reliable source
c.execute("""
    SELECT linked_entity_ids, text_content
    FROM chunk_registry
    WHERE chunk_type='background' AND language='en' AND text_content IS NOT NULL
""")
for ids_json, text in c.fetchall():
    if not text:
        continue
    try:
        eids = json.loads(ids_json)
    except:
        continue
    m = JA_PARENS.search(text[:400])
    if m:
        ja_name = m.group(1).strip()
        if KATAKANA.search(ja_name) and len(ja_name) > 1:
            for eid in eids:
                name_to_eid[ja_name] = eid

print(f"JA names from chunk text: {len(name_to_eid)}")

# From aliases table
c.execute("SELECT entity_id, alias FROM aliases WHERE alias IS NOT NULL")
for eid, alias in c.fetchall():
    if alias:
        name_to_eid.setdefault(alias.strip(), eid)

# From english display names (for EN fallback)
c.execute("SELECT entity_id, english_display_name FROM entity_registry WHERE english_display_name IS NOT NULL")
for eid, name in c.fetchall():
    if name:
        name_to_eid.setdefault(name.strip().lower(), eid)

# -----------------------------------------------------------------------
# Parse JA Wikipedia wikitext
# -----------------------------------------------------------------------
def strip_wikitext(text):
    """Strip wiki markup from text for clean storage."""
    # Remove templates {{...}}
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    # Remove [[link|text]] → text, [[link]] → link
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    # Remove ''bold''/'''italic'''
    text = re.sub(r"'{2,3}", '', text)
    # Remove <ref...>...</ref>
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^/]*/>', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text.strip())
    return text

def extract_ja_name(header):
    """Extract JA character name from ;-header, handling Vanc template."""
    # {{Vanc|Name}} or {{Vanc|Name|...}}
    m = re.search(r'\{\{Vanc\|([^|}]+)', header)
    if m:
        return m.group(1).strip()
    # Plain ;Name
    return re.sub(r'[;:\s]+', '', header).strip()

# Parse character blocks from wikitext
def parse_character_blocks(wikitext):
    """
    Extract ;CharName → :content blocks.
    Returns list of (ja_name, raw_content, section_header)
    """
    blocks = []
    lines = wikitext.split('\n')
    i = 0
    current_h2 = ''
    current_h3 = ''

    while i < len(lines):
        line = lines[i]

        # Track section headers
        m = re.match(r'^(={2,4})\s*(.+?)\s*\1', line)
        if m:
            level = len(m.group(1))
            name = m.group(2)
            if level == 2:
                current_h2 = name
            elif level == 3:
                current_h3 = name
            i += 1
            continue

        # Character entry: starts with ;
        if line.startswith(';') and line.strip() != ';':
            # Collect all following : lines
            ja_name = extract_ja_name(line[1:].strip())
            content_lines = []
            i += 1
            while i < len(lines) and (lines[i].startswith(':') or lines[i].strip() == ''):
                content_lines.append(lines[i])
                i += 1

            raw_content = '\n'.join(content_lines).strip()
            if raw_content and len(raw_content) > 50:
                section = f"{current_h2} / {current_h3}".strip(' /')
                blocks.append((ja_name, raw_content, section))
            continue

        i += 1

    return blocks

# -----------------------------------------------------------------------
# Ingest characters file
# -----------------------------------------------------------------------
with open(CORPUS / 'ja_wikipedia_characters.json', encoding='utf-8') as f:
    char_data = json.load(f)

blocks = parse_character_blocks(char_data['wikitext'])
print(f"Parsed {len(blocks)} character blocks from JA Wikipedia")

# Clear existing JA Wikipedia chunks (re-ingest cleanly)
c.execute("DELETE FROM chunk_registry WHERE source_id='ja_wikipedia'")
conn.commit()
print(f"Cleared old JA Wikipedia chunks")
existing_chunk_ids = set()

# Map blocks to entity_ids
matched = 0
unmatched = []
chunks_to_insert = []

for ja_name, raw_content, section in blocks:
    # Multi-character entries use 、to separate names
    ja_names = [n.strip() for n in ja_name.split('、') if n.strip()]

    # Try to resolve each name to entity_ids
    resolved_eids = []
    for name in ja_names:
        eid = name_to_eid.get(name) or name_to_eid.get(name.lower())
        # Try without middle-dot separators
        if not eid:
            normalized = name.replace('・', '').replace(' ', '')
            eid = name_to_eid.get(normalized)
        if eid:
            resolved_eids.append(eid)

    if not resolved_eids:
        unmatched.append(ja_name)
        continue

    # Clean the content
    clean = strip_wikitext(raw_content)
    if len(clean) < 30:
        continue

    # Create one chunk per resolved entity_id (shared content for multi-char entries)
    for eid in resolved_eids:
        chunk_id = f"ja_wiki:{eid}"
        if chunk_id in existing_chunk_ids:
            suffix = 1
            while f"{chunk_id}_{suffix}" in existing_chunk_ids:
                suffix += 1
            chunk_id = f"{chunk_id}_{suffix}"

        existing_chunk_ids.add(chunk_id)
        chunks_to_insert.append((
            chunk_id,
            'ja_wikipedia',
            None,
            json.dumps([eid]),
            clean,
            'ja',
            0,
            'background',
        ))
    matched += len(resolved_eids)

print(f"\nMatched:   {matched}")
print(f"Unmatched: {len(unmatched)}")
print(f"Unmatched sample: {unmatched[:20]}")

# Insert chunks
c.executemany("""
    INSERT OR IGNORE INTO chunk_registry
    (chunk_id, source_id, media_id, linked_entity_ids, text_content, language, spoiler_band, chunk_type)
    VALUES (?,?,?,?,?,?,?,?)
""", chunks_to_insert)
conn.commit()
print(f"\nInserted {c.rowcount} JA Wikipedia chunks")

# -----------------------------------------------------------------------
# Also ingest series + timeline files
# -----------------------------------------------------------------------
for fname, source_id, chunk_type in [
    ('ja_wikipedia_series.json',   'ja_wikipedia_series',   'lore'),
    ('ja_wikipedia_timeline.json', 'ja_wikipedia_timeline', 'timeline'),
    ('en_wikipedia_series.json',   'en_wikipedia_series',   'lore'),
    ('en_wikipedia_media.json',    'en_wikipedia_media',    'lore'),
]:
    fpath = CORPUS / fname
    if not fpath.exists():
        continue
    with open(fpath, encoding='utf-8') as f:
        fdata = json.load(f)

    title    = fdata.get('title', fname)
    wikitext = fdata.get('wikitext', '')
    if not wikitext:
        continue

    clean = strip_wikitext(wikitext)
    # Split into 2000-char chunks
    chunks_added = 0
    for i, start in enumerate(range(0, len(clean), 2000)):
        text_chunk = clean[start:start+2000].strip()
        if len(text_chunk) < 100:
            continue
        chunk_id = f"{source_id}:chunk_{i}"
        if chunk_id in existing_chunk_ids:
            continue
        c.execute("""
            INSERT OR IGNORE INTO chunk_registry
            (chunk_id, source_id, media_id, linked_entity_ids, text_content, language, spoiler_band, chunk_type)
            VALUES (?,?,?,?,?,?,?,?)
        """, (chunk_id, source_id, None, json.dumps([]), text_chunk, 'ja' if fname.startswith('ja_') else 'en', 0, chunk_type))
        chunks_added += 1

    conn.commit()
    print(f"{fname}: {chunks_added} chunks added")

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
c.execute("SELECT COUNT(*) FROM chunk_registry WHERE language='ja'")
print(f"\nTotal JA chunks in registry: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM chunk_registry")
print(f"Total chunks: {c.fetchone()[0]}")

conn.close()
print("Done.")
