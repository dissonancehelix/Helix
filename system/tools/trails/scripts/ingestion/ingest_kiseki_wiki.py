"""
ingest_kiseki_wiki.py
=====================
Ingests content from the Kiseki fandom wiki (kiseki.fandom.com) and the JA Wikipedia
character list into the Trails SQLite database (chunk_registry table).

Usage:
    python scripts/ingestion/ingest_kiseki_wiki.py [options]

Options:
    --dry-run       Print what would be inserted without writing to DB
    --target        game_story | char_story | lore | ja_chars | all (default: all)
    --limit N       Only process first N pages (for testing)
"""

import argparse
import json
import re
import sqlite3
import time
import unicodedata
from typing import Optional
from urllib.parse import urlencode, quote

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = r"C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db"

KISEKI_API = "https://kiseki.fandom.com/api.php"
JA_WIKI_API = "https://ja.wikipedia.org/w/api.php"

HEADERS = {"User-Agent": "TrailsAtlasBot/1.0"}

REQUEST_DELAY = 0.3  # seconds between API calls

# Game story pages: (media_id, wiki_page_title)
GAME_STORY_PAGES = [
    ("sky_fc",    "The Legend of Heroes: Trails in the Sky FC/Story"),
    ("sky_sc",    "The Legend of Heroes: Trails in the Sky SC/Story"),
    ("sky_3rd",   "The Legend of Heroes: Trails in the Sky The 3rd/Story"),
    ("zero",      "The Legend of Heroes: Trails from Zero/Story"),
    ("azure",     "The Legend of Heroes: Trails to Azure/Story"),
    ("cs1",       "The Legend of Heroes: Trails of Cold Steel/Story"),
    ("cs2",       "The Legend of Heroes: Trails of Cold Steel II/Story"),
    ("cs3",       "The Legend of Heroes: Trails of Cold Steel III/Story"),
    ("cs4",       "The Legend of Heroes: Trails of Cold Steel IV/Story"),
    ("reverie",   "The Legend of Heroes: Trails into Reverie/Story"),
    ("daybreak",  "The Legend of Heroes: Trails through Daybreak/Story"),
    ("daybreak2", "The Legend of Heroes: Trails through Daybreak II/Story"),
    ("horizon",   "The Legend of Heroes: Trails beyond the Horizon/Story"),
    ("akatsuki",  "The Legend of Heroes: Akatsuki no Kiseki/Story"),
]

# Lore pages: (concept_slug, entity_id_or_None, wiki_page_title)
LORE_PAGES = [
    ("concept:bracer_guild",         "faction:bracer_guild",    "Bracer Guild"),
    ("concept:sept_terrion",         None,                      "Sept-Terrion"),
    ("concept:septian_church",       "faction:septian_church",  "Septian Church"),
    ("concept:jaeger",               None,                      "Jaeger"),
    ("concept:divine_knight",        None,                      "Divine Knight"),
    ("concept:ouroboros",            "faction:ouroboros",       "Ouroboros"),
    ("concept:spirit_shrines",       None,                      "Spirit Shrines"),
    ("concept:salt_pale",            None,                      "Salt Pale"),
    ("concept:gnomes",               "faction:gnomes",          "Gnomes"),
    ("concept:tactical_orbment",     None,                      "Tactical Orbment"),
    ("concept:great_collapse",       None,                      "Great Collapse"),
    ("concept:black_records",        None,                      "Black Records"),
    ("concept:stigma",               None,                      "Stigma"),
    ("concept:aureole",              None,                      "Aureole"),
    ("concept:recluse_cube",         None,                      "Recluse Cube"),
    ("concept:great_one",            None,                      "Great One"),
    ("concept:tetracyclic_towers",   None,                      "Tetracyclic Towers"),
    ("concept:phantasmal_blaze_plan", None,                     "Phantasmal Blaze Plan"),
    ("concept:arcus",                None,                      "ARCUS"),
]

# Title prefixes that appear in entity display names but not in wiki page titles.
# Used by lookup_character_entity to strip prefixes before matching.
TITLE_PREFIXES = [
    "professor ", "prof. ", "dr. ", "doctor ", "captain ", "capt. ",
    "colonel ", "general ", "major ", "admiral ", "commander ",
    "baron ", "count ", "duke ", "archbishop ", "bishop ",
    "father ", "mother ", "sister ", "brother ",
    "director ", "chief ", "inspector ", "detective ",
    "back alley doctor ",
]

# Static alias map: wiki page title → entity_id.
# Add entries here for any wiki title that can't be resolved automatically.
WIKI_NAME_ALIASES: dict[str, str] = {
    # Examples of mantle/title entities where wiki title ≠ display name
    # "Grimcat" resolves automatically via comma-suffix stripping now,
    # but keep this pattern available for future one-offs.
}

# Maps {{g|Abbrev}} template values to (full name display, media_id)
GAME_TEMPLATE_MAP = {
    "Sky FC":        ("Trails in the Sky FC",     "sky_fc"),
    "Sora FC":       ("Trails in the Sky FC",     "sky_fc"),
    "Sky SC":        ("Trails in the Sky SC",     "sky_sc"),
    "Sora SC":       ("Trails in the Sky SC",     "sky_sc"),
    "Sky 3rd":       ("Trails in the Sky the 3rd","sky_3rd"),
    "Sora 3rd":      ("Trails in the Sky the 3rd","sky_3rd"),
    "Sky":           ("Trails in the Sky FC",     "sky_fc"),
    "Zero":          ("Trails from Zero",         "zero"),
    "Azure":         ("Trails to Azure",          "azure"),
    "Ao":            ("Trails to Azure",          "azure"),
    "Sen I":         ("Trails of Cold Steel",     "cs1"),
    "Sen 1":         ("Trails of Cold Steel",     "cs1"),
    "Cold Steel":    ("Trails of Cold Steel",     "cs1"),
    "Sen II":        ("Trails of Cold Steel II",  "cs2"),
    "Sen 2":         ("Trails of Cold Steel II",  "cs2"),
    "Cold Steel II": ("Trails of Cold Steel II",  "cs2"),
    "Sen III":       ("Trails of Cold Steel III", "cs3"),
    "Sen 3":         ("Trails of Cold Steel III", "cs3"),
    "Cold Steel III":("Trails of Cold Steel III", "cs3"),
    "Sen IV":        ("Trails of Cold Steel IV",  "cs4"),
    "Sen 4":         ("Trails of Cold Steel IV",  "cs4"),
    "Cold Steel IV": ("Trails of Cold Steel IV",  "cs4"),
    "Hajimari":      ("Trails into Reverie",      "reverie"),
    "Reverie":       ("Trails into Reverie",      "reverie"),
    "Kuro":          ("Trails through Daybreak",  "daybreak"),
    "Daybreak":      ("Trails through Daybreak",  "daybreak"),
    "Kuro II":       ("Trails through Daybreak II","daybreak2"),
    "Daybreak II":   ("Trails through Daybreak II","daybreak2"),
    "Kai":           ("Trails beyond the Horizon","horizon"),
    "Horizon":       ("Trails beyond the Horizon","horizon"),
    "Akatsuki":      ("Akatsuki no Kiseki",       "akatsuki"),
}

# JA Wikipedia section title keywords → media_id
JA_SECTION_MEDIA_MAP = [
    ("空の軌跡FC",     "sky_fc"),
    ("空の軌跡SC",     "sky_sc"),
    ("空の軌跡 the 3rd", "sky_3rd"),
    ("空の軌跡",       "sky_fc"),
    ("零の軌跡",       "zero"),
    ("碧の軌跡",       "azure"),
    ("閃の軌跡I",      "cs1"),
    ("閃の軌跡Ⅰ",     "cs1"),
    ("閃の軌跡II",     "cs2"),
    ("閃の軌跡Ⅱ",     "cs2"),
    ("閃の軌跡III",    "cs3"),
    ("閃の軌跡Ⅲ",     "cs3"),
    ("閃の軌跡IV",     "cs4"),
    ("閃の軌跡Ⅳ",     "cs4"),
    ("閃の軌跡",       "cs1"),
    ("黎の軌跡II",     "daybreak2"),
    ("黎の軌跡Ⅱ",     "daybreak2"),
    ("黎の軌跡",       "daybreak"),
    ("創の軌跡",       "reverie"),
    ("界の軌跡",       "horizon"),
    ("暁の軌跡",       "akatsuki"),
]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """
    Convert arbitrary text to a URL/ID-safe slug.
    Lowercases, removes accents, replaces spaces and special chars with underscores.
    """
    # Normalize unicode (NFD strips accent marks)
    text = unicodedata.normalize("NFD", text)
    # Keep only ASCII after normalization
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Replace anything that isn't alphanumeric or underscore with underscore
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text or "unknown"


def fetch_wikitext(api_url: str, page_title: str) -> Optional[str]:
    """
    Fetch the raw wikitext for a page via the MediaWiki API.
    Retries once on failure. Returns None if the page is missing or errored.
    """
    params = {
        "action":   "query",
        "prop":     "revisions",
        "titles":   page_title,
        "rvprop":   "content",
        "rvslots":  "main",
        "format":   "json",
    }

    for attempt in range(2):
        try:
            resp = requests.get(api_url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    print(f"  [SKIP] Page not found: {page_title!r}")
                    return None
                revisions = page_data.get("revisions", [])
                if not revisions:
                    print(f"  [SKIP] No revisions for: {page_title!r}")
                    return None
                slot = revisions[0].get("slots", {}).get("main", {})
                return slot.get("*", "")
            return None
        except requests.RequestException as e:
            if attempt == 0:
                print(f"  [WARN] HTTP error fetching {page_title!r}: {e}. Retrying...")
                time.sleep(1.0)
            else:
                print(f"  [ERROR] Failed to fetch {page_title!r}: {e}. Skipping.")
                return None
    return None


def clean_wikitext(text: str) -> str:
    """
    Strip wikitext markup and return clean prose.

    Steps:
      1. Remove <gallery>...</gallery> blocks
      2. Remove <ref>...</ref> and self-closing <ref ... />
      3. Convert [[Target|Display]] → "Display"
      4. Convert [[Target]] → "Target"
      5. Convert {{g|GameAbbrev}} → "(Full Game Name)"
      6. Convert {{furi|kanji|reading}} → "kanji"
      7. Remove {{SpoilerSection|...}} tags
      8. Remove other {{ }} template lines/blocks
      9. Convert '''text''' → text and ''text'' → text
     10. Remove remaining HTML tags
     11. Remove pure wikimarkup lines (|, !, {|, |})
     12. Collapse multiple blank lines
    """
    # 1. Remove gallery blocks (multiline)
    text = re.sub(r"<gallery[^>]*>.*?</gallery>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Remove ref tags (block and self-closing)
    text = re.sub(r"<ref[^>]*/\s*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # 3 & 4. Convert wiki links
    # [[Target|Display]] → Display
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    # [[Target]] → Target
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

    # 5. Convert {{g|Abbrev}} → (Full Game Name)
    def expand_game_template(m):
        abbrev = m.group(1).strip()
        if abbrev in GAME_TEMPLATE_MAP:
            full_name, _ = GAME_TEMPLATE_MAP[abbrev]
            return f"({full_name})"
        return f"({abbrev})"

    text = re.sub(r"\{\{g\|([^}]+)\}\}", expand_game_template, text, flags=re.IGNORECASE)

    # 6. Convert {{furi|kanji|reading}} → kanji
    text = re.sub(r"\{\{furi\|([^|}]+)\|[^}]*\}\}", r"\1", text, flags=re.IGNORECASE)

    # 7. Remove SpoilerSection template tags (keep surrounding content)
    text = re.sub(r"\{\{SpoilerSection[^}]*\}\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{EndSpoiler[^}]*\}\}", "", text, flags=re.IGNORECASE)

    # 8. Remove other template blocks.
    # Strategy A: single-line templates {{...}}
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Strategy B: multi-line templates — remove lines that look like template guts
    # (lines starting with | or lines that are just {{ or }})
    # We do a second pass after other cleaning below.

    # 9. Convert bold/italic wiki markup
    text = re.sub(r"'''([^']+)'''", r"\1", text)
    text = re.sub(r"''([^']+)''", r"\1", text)

    # 10. Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # 11. Remove pure wikimarkup lines
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        # Skip table markup lines
        if stripped.startswith("|") or stripped.startswith("!") or \
                stripped.startswith("{|") or stripped.startswith("|}"):
            continue
        # Skip leftover template lines (opener/closer)
        if stripped.startswith("{{") or stripped.startswith("}}"):
            continue
        # Skip lines that are just a template parameter (| param = value)
        if re.match(r"^\|[^|]", stripped):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # 12. Collapse multiple blank lines to one
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def split_into_sections(wikitext: str) -> list[tuple[str, str]]:
    """
    Parse wikitext into (section_title, section_content) pairs.
    Handles == H2 ==, === H3 ===, and ==== H4 ==== headings.
    Returns a list of (title, content) — the intro (before any heading)
    is returned with title '' if non-empty.
    """
    # Split on any heading level (== ... ==)
    heading_pattern = re.compile(r"^(={2,4})\s*(.+?)\s*\1\s*$", re.MULTILINE)
    sections = []
    last_end = 0
    last_title = ""

    for m in heading_pattern.finditer(wikitext):
        content = wikitext[last_end:m.start()].strip()
        if content or last_title:
            sections.append((last_title, content))
        last_title = m.group(2).strip()
        last_end = m.end()

    # Remaining content after last heading
    content = wikitext[last_end:].strip()
    if content or last_title:
        sections.append((last_title, content))

    return sections


def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    """
    Split text into chunks of at most max_chars, splitting on paragraph boundaries.
    """
    if len(text) <= max_chars:
        return [text] if text.strip() else []

    paragraphs = re.split(r"\n\n+", text)
    chunks = []
    current = ""

    for para in paragraphs:
        if not para.strip():
            continue
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            # If a single paragraph itself is too long, split on sentence boundaries
            if len(para) > max_chars:
                sentences = re.split(r"(?<=[。！？.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_chars:
                        current = (current + " " + sent).strip() if current else sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def lookup_character_entity(conn: sqlite3.Connection, char_name: str) -> Optional[str]:
    """
    Attempt to find a character entity_id by english_display_name.

    Resolution order:
      1. Static alias map (WIKI_NAME_ALIASES) — for known one-offs
      2. Exact match on english_display_name
      3. Case-insensitive exact match
      4. Strip parenthetical suffix from wiki name, e.g. "Ada (Nayuta)" → "Ada"
      5. Scan all character entities and try:
         a. Strip a title prefix from the *entity* name, compare to wiki name
            e.g. entity="Professor Latoya Hamilton" → "Latoya Hamilton" == wiki name
         b. Strip comma-and-everything-after from the *entity* name, compare to wiki name
            e.g. entity="Grimcat, Cat of the Illusory Night" → "Grimcat" == wiki name
    """
    cur = conn.cursor()

    # 1. Static alias map
    if char_name in WIKI_NAME_ALIASES:
        return WIKI_NAME_ALIASES[char_name]

    # 2. Exact match
    cur.execute(
        "SELECT entity_id FROM entity_registry WHERE entity_type='character' AND english_display_name=?",
        (char_name,)
    )
    row = cur.fetchone()
    if row:
        return row["entity_id"]

    # 3. Case-insensitive exact match
    cur.execute(
        "SELECT entity_id FROM entity_registry WHERE entity_type='character' AND LOWER(english_display_name)=LOWER(?)",
        (char_name,)
    )
    row = cur.fetchone()
    if row:
        return row["entity_id"]

    # 4. Strip parenthetical suffix from wiki name: "Ada (Nayuta)" → "Ada"
    base_name = re.sub(r"\s*\([^)]+\)\s*$", "", char_name).strip()
    if base_name != char_name:
        cur.execute(
            "SELECT entity_id FROM entity_registry WHERE entity_type='character' AND LOWER(english_display_name)=LOWER(?)",
            (base_name,)
        )
        row = cur.fetchone()
        if row:
            return row["entity_id"]

    # 5. Scan all character entities for prefix/suffix structural mismatches
    cur.execute(
        "SELECT entity_id, english_display_name FROM entity_registry WHERE entity_type='character'"
    )
    all_chars = cur.fetchall()
    wiki_lower = char_name.lower()

    for row in all_chars:
        eid = row["entity_id"]
        display = (row["english_display_name"] or "").lower()

        # 5a. Strip title prefix from entity display name
        stripped = display
        for prefix in TITLE_PREFIXES:
            if display.startswith(prefix):
                stripped = display[len(prefix):]
                break
        if stripped == wiki_lower:
            return eid

        # 5b. Strip ", <anything>" suffix from entity display name
        #     e.g. "grimcat, cat of the illusory night" → "grimcat"
        comma_base = display.split(",")[0].strip()
        if comma_base != display and comma_base == wiki_lower:
            return eid

    return None


def lookup_entity_by_id(conn: sqlite3.Connection, entity_id: str) -> Optional[str]:
    """Check whether a given entity_id exists in entity_registry."""
    cur = conn.cursor()
    cur.execute("SELECT entity_id FROM entity_registry WHERE entity_id=?", (entity_id,))
    row = cur.fetchone()
    return row["entity_id"] if row else None


def insert_chunk(
    conn: sqlite3.Connection,
    dry_run: bool,
    chunk_id: str,
    source_id: str,
    media_id: Optional[str],
    linked_entity_ids: list,
    text_content: str,
    language: str,
    spoiler_band: int,
    chunk_type: str,
) -> None:
    """Insert (or replace) a single chunk into chunk_registry."""
    if not text_content.strip():
        return  # Skip empty chunks

    linked_json = json.dumps(linked_entity_ids)

    if dry_run:
        print(
            f"  [DRY-RUN] chunk_id={chunk_id!r} source={source_id!r} "
            f"media={media_id!r} lang={language} band={spoiler_band} "
            f"type={chunk_type} len={len(text_content)} "
            f"entities={linked_entity_ids}"
        )
        return

    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO chunk_registry
            (chunk_id, source_id, media_id, linked_entity_ids, text_content, language, spoiler_band, chunk_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (chunk_id, source_id, media_id, linked_json, text_content, language, spoiler_band, chunk_type),
    )


# ---------------------------------------------------------------------------
# Target 1: Game Story Pages
# ---------------------------------------------------------------------------

def ingest_game_story(conn: sqlite3.Connection, dry_run: bool, limit: Optional[int]) -> None:
    """
    Fetch story-page wikitext for each game and insert per-section chunks.
    source_id = 'wiki:en_story_v1', language = 'en', spoiler_band = 3, chunk_type = 'plot'
    """
    print("\n=== Game Story Pages ===")
    pages = GAME_STORY_PAGES[:limit] if limit else GAME_STORY_PAGES

    for media_id, page_title in pages:
        print(f"  Fetching: {page_title}")
        wikitext = fetch_wikitext(KISEKI_API, page_title)
        time.sleep(REQUEST_DELAY)

        if wikitext is None:
            continue

        sections = split_into_sections(wikitext)
        inserted = 0

        for section_title, section_content in sections:
            clean = clean_wikitext(section_content)
            if not clean.strip():
                continue

            slug = slugify(section_title) if section_title else "intro"
            chunk_id = f"story:{media_id}:{slug}"
            linked = [f"media:{media_id}"]

            insert_chunk(
                conn, dry_run,
                chunk_id=chunk_id,
                source_id="wiki:en_story_v1",
                media_id=media_id,
                linked_entity_ids=linked,
                text_content=clean,
                language="en",
                spoiler_band=3,
                chunk_type="plot",
            )
            inserted += 1

        print(f"    → {inserted} section(s) inserted for {media_id}")

    if not dry_run:
        conn.commit()


# ---------------------------------------------------------------------------
# Target 2: Character Story Pages
# ---------------------------------------------------------------------------

def search_char_story_pages(limit: Optional[int]) -> list[dict]:
    """
    Query the Kiseki wiki search API for pages ending in /Story that are NOT
    game story pages and have size > 3000 bytes.
    Returns a list of {title, size} dicts.
    """
    print("  Searching for character /Story pages...")
    params = {
        "action":    "query",
        "list":      "search",
        "srsearch":  "intitle:/Story",
        "srlimit":   "200",
        "srprop":    "size",
        "format":    "json",
    }

    try:
        resp = requests.get(KISEKI_API, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] Search API failed: {e}")
        return []

    time.sleep(REQUEST_DELAY)

    results = data.get("query", {}).get("search", [])
    filtered = []
    for item in results:
        title = item.get("title", "")
        size = item.get("size", 0)

        # Must end with /Story
        if not title.endswith("/Story"):
            continue
        # Must NOT be a game-level story page
        if "The Legend of Heroes" in title:
            continue
        if "Akatsuki no Kiseki" in title:
            continue
        # Must be large enough to be substantive
        if size <= 3000:
            continue

        filtered.append({"title": title, "size": size})

    print(f"  Found {len(filtered)} character story pages after filtering.")
    if limit:
        filtered = filtered[:limit]
    return filtered


def detect_game_from_section(section_title: str) -> Optional[str]:
    """
    Try to detect which media_id a character-story section belongs to by matching
    game template abbreviations or display names in the heading text.
    E.g. "== {{g|Sen I}} ==" or a plain heading like "Sen IV".
    We sort candidates by length descending so that more specific keys (e.g.
    "Sen IV", "Cold Steel IV") are checked before shorter ones ("Sen I", "Sky").
    """
    title_lower = section_title.lower()
    # Sort keys longest-first so more specific matches win over substrings
    sorted_abbrevs = sorted(GAME_TEMPLATE_MAP.keys(), key=len, reverse=True)
    for abbrev in sorted_abbrevs:
        _, media_id = GAME_TEMPLATE_MAP[abbrev]
        # Use word-boundary-aware matching to avoid "Sen I" matching "Sen II"
        # Escape the abbreviation for regex use and require non-alphanumeric boundary
        pattern = r"(?<![a-z0-9])" + re.escape(abbrev.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, title_lower):
            return media_id
    return None


def ingest_char_story(conn: sqlite3.Connection, dry_run: bool, limit: Optional[int]) -> None:
    """
    Fetch character story pages and insert per-section chunks.
    source_id = 'wiki:en_char_story_v1', language = 'en', spoiler_band = 2, chunk_type = 'story'
    """
    print("\n=== Character Story Pages ===")
    pages = search_char_story_pages(limit)

    for page_info in pages:
        page_title = page_info["title"]
        char_name = page_title.replace("/Story", "").strip()
        print(f"  Fetching: {page_title}")

        wikitext = fetch_wikitext(KISEKI_API, page_title)
        time.sleep(REQUEST_DELAY)

        if wikitext is None:
            continue

        # Look up entity
        entity_id = lookup_character_entity(conn, char_name)
        base_linked = [entity_id] if entity_id else []

        char_slug = slugify(char_name)
        sections = split_into_sections(wikitext)
        inserted = 0

        for section_title, section_content in sections:
            # Detect which game this section covers (from raw heading before cleaning)
            section_media_id = detect_game_from_section(section_title)

            clean = clean_wikitext(section_content)
            if not clean.strip():
                continue

            section_slug = slugify(section_title) if section_title else "intro"
            chunk_id = f"char_story:{char_slug}:{section_slug}"

            insert_chunk(
                conn, dry_run,
                chunk_id=chunk_id,
                source_id="wiki:en_char_story_v1",
                media_id=section_media_id,
                linked_entity_ids=base_linked,
                text_content=clean,
                language="en",
                spoiler_band=2,
                chunk_type="story",
            )
            inserted += 1

        if entity_id:
            print(f"    → {inserted} section(s) for {char_name!r} [{entity_id}]")
        else:
            print(f"    → {inserted} section(s) for {char_name!r} [no entity match]")

    if not dry_run:
        conn.commit()


# ---------------------------------------------------------------------------
# Target 3: Lore Pages
# ---------------------------------------------------------------------------

def ingest_lore(conn: sqlite3.Connection, dry_run: bool, limit: Optional[int]) -> None:
    """
    Fetch major lore pages and insert per-section chunks.
    source_id = 'wiki:en_lore_v1', language = 'en', spoiler_band = 2, chunk_type = 'lore'
    """
    print("\n=== Lore Pages ===")
    pages = LORE_PAGES[:limit] if limit else LORE_PAGES

    for concept_id, entity_id, page_title in pages:
        print(f"  Fetching: {page_title}")
        wikitext = fetch_wikitext(KISEKI_API, page_title)
        time.sleep(REQUEST_DELAY)

        if wikitext is None:
            continue

        # Determine linked entity ids
        if entity_id:
            # Verify it exists
            resolved = lookup_entity_by_id(conn, entity_id)
            linked = [entity_id] if resolved else []
        else:
            # Try looking up by the concept_id as an entity
            resolved = lookup_entity_by_id(conn, concept_id)
            linked = [concept_id] if resolved else []

        concept_slug = concept_id.split(":")[-1]  # e.g. "bracer_guild"
        sections = split_into_sections(wikitext)
        inserted = 0

        for section_title, section_content in sections:
            clean = clean_wikitext(section_content)
            if not clean.strip():
                continue

            section_slug = slugify(section_title) if section_title else "intro"
            chunk_id = f"lore:{concept_slug}:{section_slug}"

            insert_chunk(
                conn, dry_run,
                chunk_id=chunk_id,
                source_id="wiki:en_lore_v1",
                media_id=None,
                linked_entity_ids=linked,
                text_content=clean,
                language="en",
                spoiler_band=2,
                chunk_type="lore",
            )
            inserted += 1

        print(f"    → {inserted} section(s) for {concept_id}")

    if not dry_run:
        conn.commit()


# ---------------------------------------------------------------------------
# Target 4: JA Wikipedia Character List
# ---------------------------------------------------------------------------

def detect_ja_media_id(section_title: str) -> Optional[str]:
    """
    Given a JA Wikipedia section heading, return the matching media_id or None.
    Checks JA_SECTION_MEDIA_MAP in order (more specific first).
    """
    for keyword, media_id in JA_SECTION_MEDIA_MAP:
        if keyword in section_title:
            return media_id
    # Also try Latin abbreviations in JA sections (sometimes mixed)
    for abbrev, (_, media_id) in GAME_TEMPLATE_MAP.items():
        if abbrev in section_title:
            return media_id
    return None


def ingest_ja_chars(conn: sqlite3.Connection, dry_run: bool, limit: Optional[int]) -> None:
    """
    Fetch the JA Wikipedia character list article and insert per-subsection chunks.
    The article is ~1.28MB so we split aggressively.
    source_id = 'wikipedia:ja_chars', language = 'ja', spoiler_band = 2, chunk_type = 'characters'
    """
    print("\n=== JA Wikipedia Character List ===")
    article_title = "英雄伝説 軌跡シリーズの登場人物"
    print(f"  Fetching: {article_title}")

    wikitext = fetch_wikitext(JA_WIKI_API, article_title)
    time.sleep(REQUEST_DELAY)

    if wikitext is None:
        print("  [ERROR] Could not fetch JA Wikipedia article.")
        return

    print(f"  Raw wikitext length: {len(wikitext):,} chars")

    # We split at the === subsection level for JA content as it's very long
    # Use split_into_sections which handles all heading levels
    sections = split_into_sections(wikitext)
    print(f"  Found {len(sections)} section(s) before limit")

    if limit:
        sections = sections[:limit]

    # Track current game context across sections (inherit from last named heading)
    current_media_id: Optional[str] = None
    inserted = 0

    for section_title, section_content in sections:
        # Update media context from heading
        detected = detect_ja_media_id(section_title)
        if detected:
            current_media_id = detected

        clean = clean_wikitext(section_content)
        if not clean.strip():
            continue

        # Use slugify on the ASCII transliteration — for JA text, just use
        # a hex fingerprint of the title to keep chunk_ids stable and unique
        if section_title:
            # Try ASCII slugify first; fall back to a hex digest of the title
            slug_attempt = slugify(section_title)
            if slug_attempt == "unknown" or not slug_attempt:
                import hashlib
                slug_attempt = hashlib.md5(section_title.encode("utf-8")).hexdigest()[:12]
            section_slug = slug_attempt
        else:
            section_slug = "intro"

        # Split large sections into sub-chunks
        sub_chunks = chunk_text(clean, max_chars=3000)
        for idx, sub in enumerate(sub_chunks):
            suffix = f"_{idx}" if len(sub_chunks) > 1 else ""
            chunk_id = f"ja_chars:{section_slug}{suffix}"

            insert_chunk(
                conn, dry_run,
                chunk_id=chunk_id,
                source_id="wikipedia:ja_chars",
                media_id=current_media_id,
                linked_entity_ids=[],
                text_content=sub,
                language="ja",
                spoiler_band=2,
                chunk_type="characters",
            )
            inserted += 1

    print(f"  → {inserted} chunk(s) inserted for JA character list")

    if not dry_run:
        conn.commit()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest Kiseki wiki and JA Wikipedia content into the Trails database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be inserted without writing to DB.",
    )
    parser.add_argument(
        "--target",
        choices=["game_story", "char_story", "lore", "ja_chars", "all"],
        default="all",
        help="Which ingestion target to run (default: all).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Only process first N pages (useful for testing).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.dry_run:
        print("*** DRY-RUN MODE — no database writes will occur ***\n")

    conn = get_db_connection()

    try:
        target = args.target
        limit = args.limit

        if target in ("game_story", "all"):
            ingest_game_story(conn, dry_run=args.dry_run, limit=limit)

        if target in ("char_story", "all"):
            ingest_char_story(conn, dry_run=args.dry_run, limit=limit)

        if target in ("lore", "all"):
            ingest_lore(conn, dry_run=args.dry_run, limit=limit)

        if target in ("ja_chars", "all"):
            ingest_ja_chars(conn, dry_run=args.dry_run, limit=limit)

        if not args.dry_run:
            conn.commit()
            print("\nAll commits complete.")
        else:
            print("\nDry-run complete. No changes were written.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
