"""
Ingest nation/region pages, additional lore, and JA Wikipedia series article.
Run: python scripts/ingestion/ingest_nations_lore.py
"""
import urllib.request, json, urllib.parse, re, time, sqlite3

DB = 'retrieval/index/trails.db'
KISEKI_BASE = 'https://kiseki.fandom.com/api.php'
JA_BASE = 'https://ja.wikipedia.org/w/api.php'
UA = 'TrailsAtlasBot/1.0'


def fetch_wikitext(base, title):
    params = urllib.parse.urlencode({
        'action': 'query', 'titles': title,
        'prop': 'revisions', 'rvprop': 'content',
        'rvslots': 'main', 'redirects': True, 'format': 'json'
    })
    req = urllib.request.Request(f'{base}?{params}', headers={'User-Agent': UA})
    resp = urllib.request.urlopen(req, timeout=20)
    data = json.loads(resp.read())
    page = next(iter(data['query']['pages'].values()))
    if 'missing' in page:
        return None
    slots = page.get('revisions', [{}])[0].get('slots', {})
    return slots.get('main', {}).get('*', '')


def fetch_extract(base, title):
    params = urllib.parse.urlencode({
        'action': 'query', 'titles': title,
        'prop': 'extracts', 'explaintext': True,
        'redirects': True, 'format': 'json'
    })
    req = urllib.request.Request(f'{base}?{params}', headers={'User-Agent': UA})
    resp = urllib.request.urlopen(req, timeout=20)
    data = json.loads(resp.read())
    page = next(iter(data['query']['pages'].values()))
    if 'missing' in page:
        return None
    return page.get('extract', '')


def clean_wikitext(text):
    text = re.sub(r'<gallery[^>]*>.*?</gallery>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<ref[^>]*/>', '', text)
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'\{\|.*?\|\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\[\[(?:[^|\]]+\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\{\{furi\|([^|]+)\|[^}]+\}\}', r'\1', text)
    text = re.sub(r'\{\{g\|([^}]+)\}\}', r'(\1)', text)
    text = re.sub(r'\{\{[^{}]{0,200}\}\}', '', text)
    text = re.sub(r"'''(.+?)'''", r'\1', text)
    text = re.sub(r"''(.+?)''", r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'^[|!{].*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_sections(text):
    pattern = re.compile(r'\n(={2,4})\s*(.+?)\s*\1\n', re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections = []
    intro_end = matches[0].start() if matches else len(text)
    intro = text[:intro_end].strip()
    if intro:
        sections.append(('intro', intro))
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content and len(content) > 80:
            sections.append((title, content))
    return sections


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower())[:40].strip('_')


# Nation and additional lore pages
KISEKI_PAGES = [
    # (wiki_title, source_id, primary_media_ids, spoiler_band, chunk_type, extra_entity_ids)
    ('Erebonia', 'wiki:en_nations_v1', ['cs1', 'cs2', 'cs3', 'cs4'], 2, 'lore', ['loc:heimdallr']),
    ('Calvard', 'wiki:en_nations_v1', ['daybreak', 'daybreak2', 'horizon'], 2, 'lore', []),
    ('Crossbell', 'wiki:en_nations_v1', ['zero', 'azure'], 2, 'lore', ['loc:crossbell_city']),
    ('Liberl', 'wiki:en_nations_v1', ['sky_fc', 'sky_sc', 'sky_3rd'], 2, 'lore', []),
    ('North Ambria', 'wiki:en_nations_v1', ['cs1', 'cs2', 'cs3', 'cs4'], 1, 'lore', []),
    ('Zemuria', 'wiki:en_nations_v1', [], 1, 'lore', ['loc:zemuria']),
    ('Remiferia', 'wiki:en_nations_v1', [], 1, 'lore', []),
    ('Arteria', 'wiki:en_nations_v1', [], 1, 'lore', []),
    ('Ored', 'wiki:en_nations_v1', ['daybreak', 'daybreak2'], 1, 'lore', ['loc:ored']),
    ('Leman', 'wiki:en_nations_v1', [], 1, 'lore', []),
    ('Glorious', 'wiki:en_lore_v1', ['sky_fc', 'sky_sc', 'sky_3rd'], 2, 'lore', []),
    ('Gospel', 'wiki:en_lore_v1', ['sky_fc', 'sky_sc'], 2, 'lore', []),
    ('Aidios', 'wiki:en_lore_v1', [], 1, 'lore', ['concept:aidios']),
]

JA_EXTRA_ARTICLES = [
    # (wiki_title, source_id, media_ids, language)
    ('英雄伝説 軌跡シリーズ', 'wikipedia:ja_series', [], 'ja'),
    ('イースvs.空の軌跡 オルタナティブ・サーガ', 'wikipedia:ja', ['ys_vs_trails'], 'ja'),
    ('英雄伝説 創の軌跡', 'wikipedia:ja', ['reverie'], 'ja'),
]


def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    total = 0

    print('=== Kiseki wiki: Nation + Lore pages ===')
    for title, source_id, media_ids, band, chunk_type, entities in KISEKI_PAGES:
        print(f'  Fetching: {title}...', end=' ', flush=True)
        try:
            wikitext = fetch_wikitext(KISEKI_BASE, title)
            if not wikitext:
                print('NOT FOUND')
                continue
            cleaned = clean_wikitext(wikitext)
            sections = split_sections(cleaned)
            inserted = 0
            for sec_title, content in sections:
                slug = slugify(sec_title) if sec_title != 'intro' else 'intro'
                chunk_id = f'nation:{slugify(title)}:{slug}'
                linked = json.dumps(
                    [f'media:{m}' for m in media_ids] + entities
                )
                c.execute(
                    'INSERT OR REPLACE INTO chunk_registry '
                    '(chunk_id,source_id,media_id,linked_entity_ids,text_content,language,spoiler_band,chunk_type) '
                    'VALUES (?,?,?,?,?,?,?,?)',
                    (chunk_id, source_id, media_ids[0] if media_ids else None,
                     linked, content, 'en', band, chunk_type)
                )
                inserted += 1
            total += inserted
            print(f'{inserted} sections ({len(cleaned):,} chars)')
        except Exception as e:
            print(f'ERROR: {e}')
        time.sleep(0.4)

    print()
    print('=== JA Wikipedia: extra articles ===')
    for title, source_id, media_ids, lang in JA_EXTRA_ARTICLES:
        print(f'  Fetching: {title}...', end=' ', flush=True)
        try:
            text = fetch_extract(JA_BASE, title)
            if not text:
                print('NOT FOUND')
                continue
            sections = split_sections(text)
            inserted = 0
            for sec_title, content in sections:
                if len(content) < 100:
                    continue
                slug = slugify(sec_title) if sec_title != 'intro' else 'intro'
                title_slug = slugify(title)
                chunk_id = f'wikipedia:{lang}:{title_slug}:{slug}'
                linked = json.dumps([f'media:{m}' for m in media_ids]) if media_ids else '[]'
                c.execute(
                    'INSERT OR REPLACE INTO chunk_registry '
                    '(chunk_id,source_id,media_id,linked_entity_ids,text_content,language,spoiler_band,chunk_type) '
                    'VALUES (?,?,?,?,?,?,?,?)',
                    (chunk_id, source_id, media_ids[0] if media_ids else None,
                     linked, content[:4000], lang, 1, 'lore')
                )
                inserted += 1
            total += inserted
            print(f'{inserted} sections ({len(text):,} chars)')
        except Exception as e:
            print(f'ERROR: {e}')
        time.sleep(0.5)

    conn.commit()
    c.execute('SELECT COUNT(*) FROM chunk_registry')
    print(f'\nInserted: {total} new chunks | DB total: {c.fetchone()[0]:,}')
    conn.close()


if __name__ == '__main__':
    main()
