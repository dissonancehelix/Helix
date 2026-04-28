"""
translate_ja_chunks.py
======================
Translate all Japanese chunks in chunk_registry into English using the
Claude API, storing results in the translated_content column.

Translations use official XSEED/NISA localization terminology as the
anchor vocabulary, making the JA Wikipedia content (which is 4-10x
denser than EN Wikipedia per game) usable by English LLMs.

Usage:
    python scripts/translation/translate_ja_chunks.py [options]

Options:
    --dry-run          Print the prompt for the first chunk, no API calls
    --limit N          Translate at most N chunks this run
    --source-id SRC    Only translate chunks from this source_id
    --quality          Use claude-opus-4-6 instead of haiku (slower, higher quality)
    --rerun            Re-translate chunks that already have translated_content

Requires:
    ANTHROPIC_API_KEY environment variable

Run the schema migration first if you haven't:
    python scripts/translation/migrate_add_translated_content.py
"""

import argparse
import os
import sqlite3
import sys
import time

DB = "C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db"

MODEL_DEFAULT = "claude-haiku-4-5"
MODEL_QUALITY  = "claude-opus-4-6"

RATE_LIMIT_DELAY = 0.3   # seconds between API calls
MAX_ERRORS       = 5     # stop after this many consecutive errors

# ---------------------------------------------------------------------------
# Terminology glossary injected into the system prompt.
# Maps JA terms/romanizations → official EN localizations.
# Covers cases where a naive translation would produce wrong terminology.
# ---------------------------------------------------------------------------
TERMINOLOGY = """
Key terminology (always use the English column, never the Japanese/romaji):

Japanese / Romaji              → Official English (XSEED/NISA)
--------------------------------------------------------------
遊撃士 / Yuugekishi            → Bracer
遊撃士協会 / Bracers Assoc.    → Bracer Guild
結社 / Kessha                  → Ouroboros
執行者 / Shikkousha            → Enforcer
使徒 / Shito                   → Anguis (for the Thirteen Factories leaders)
星杯騎士団 / Seihai Kishidan   → Gralsritter
教会 / Kyoukai (Septian)       → Septian Church
七の至宝 / Nana no Shihou      → Sept-Terrion
導力 / Orbal Force / Kohdou    → Orbal Energy / orbment
導力器 / Orbal Device          → orbment
ARCUS / アークス               → ARCUS
鉄機隊 / Tekkitai              → Stahlritter
鉄騎隊 / Tekkitai (CS)         → Eisenritter
猟兵 / Ryouhei                 → Jaeger
帝国 / Teikoku                 → Erebonian Empire
王国 / Oukoku (Liberl)         → Kingdom of Liberl
クロスベル / Kurosuberu        → Crossbell
カルバード / Karubādo           → Calvard
ゼムリア / Zemuria              → Zemuria
閃の軌跡 / Sen no Kiseki       → Trails of Cold Steel
空の軌跡 / Sora no Kiseki      → Trails in the Sky
零の軌跡 / Zero no Kiseki      → Trails from Zero
碧の軌跡 / Ao no Kiseki        → Trails to Azure
創の軌跡 / Hajimari no Kiseki  → Trails into Reverie
黎の軌跡 / Kuro no Kiseki      → Trails through Daybreak
界の軌跡 / Kai no Kiseki       → Trails beyond the Horizon
暁の軌跡 / Akatsuki no Kiseki  → Akatsuki no Kiseki (mobile, no EN release)
"""

SYSTEM_PROMPT = f"""You are a specialist translator for Nihon Falcom's Kiseki (Trails) series.
Translate the following Japanese text into English for use in a reference database.

{TERMINOLOGY}

Translation rules:
- Apply the terminology table above consistently throughout your translation.
- For character names: use the official XSEED/NISA romanization where known. \
If unsure of the official EN name, preserve the katakana romanized as-is.
- Keep the encyclopedic, neutral tone of the source. Do not editorialize.
- Translate completely — do not summarize, condense, or omit any content.
- Preserve formatting cues: semicolons used as list markers, colon-indented \
details, parenthetical notes.
- If a term has no confirmed EN equivalent and is not in the terminology table, \
write it in romaji and append [JA] to flag it for review.
- Output only the translated text. No preamble, no commentary, no notes."""


def parse_args():
    p = argparse.ArgumentParser(description="Translate JA chunks in chunk_registry to English.")
    p.add_argument("--dry-run",   action="store_true", help="Print prompt for first chunk, no API calls")
    p.add_argument("--limit",     type=int, default=None, metavar="N", help="Translate at most N chunks")
    p.add_argument("--source-id", default=None, metavar="SRC", help="Only chunks from this source_id")
    p.add_argument("--quality",   action="store_true", help=f"Use {MODEL_QUALITY} instead of haiku")
    p.add_argument("--rerun",     action="store_true", help="Re-translate already-translated chunks")
    return p.parse_args()


def get_chunks(conn, source_id=None, rerun=False, limit=None):
    """Fetch JA chunks to translate, highest-value sources first."""
    conditions = ["language = 'ja'"]
    params = []

    if not rerun:
        conditions.append("(translated_content IS NULL OR translated_content = '')")

    if source_id:
        conditions.append("source_id = ?")
        params.append(source_id)

    where = " AND ".join(conditions)

    # Priority: ja_chars (character descriptions) → wikipedia:ja (game articles)
    # → ja_wikipedia (misc) → everything else
    query = f"""
        SELECT chunk_id, text_content, source_id, linked_entity_ids
        FROM chunk_registry
        WHERE {where}
        ORDER BY
          CASE source_id
            WHEN 'wikipedia:ja_chars' THEN 1
            WHEN 'wikipedia:ja'       THEN 2
            WHEN 'ja_wikipedia'       THEN 3
            WHEN 'ja_wikipedia_series'   THEN 4
            WHEN 'ja_wikipedia_timeline' THEN 5
            ELSE 6
          END,
          chunk_id
        {'LIMIT ' + str(limit) if limit else ''}
    """
    c = conn.cursor()
    c.execute(query, params)
    return c.fetchall()


def translate_chunk(client, model, text_content, dry_run=False):
    """Call Claude to translate a single chunk. Returns translated string."""
    if dry_run:
        print("\n" + "=" * 60)
        print("SYSTEM PROMPT (truncated):")
        print(SYSTEM_PROMPT[:400] + "...")
        print("\nUSER MESSAGE (first 500 chars of source):")
        print(text_content[:500])
        print("=" * 60)
        return "[DRY RUN]"

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text_content}],
    )
    return response.content[0].text


def main():
    args = parse_args()
    model = MODEL_QUALITY if args.quality else MODEL_DEFAULT

    # Verify schema migration has been run
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("PRAGMA table_info(chunk_registry)")
    cols = {row[1] for row in c.fetchall()}
    if "translated_content" not in cols:
        print("ERROR: 'translated_content' column missing.")
        print("Run: python scripts/translation/migrate_add_translated_content.py")
        conn.close()
        sys.exit(1)

    # Set up API client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: ANTHROPIC_API_KEY not set. Use --dry-run to test without API.")
        conn.close()
        sys.exit(1)

    client = None
    if not args.dry_run:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

    # Fetch chunks
    chunks = get_chunks(conn, source_id=args.source_id, rerun=args.rerun, limit=args.limit)
    print(f"Model: {model}")
    print(f"Chunks to translate: {len(chunks)}")
    if args.source_id:
        print(f"Source filter: {args.source_id}")
    if args.dry_run:
        print("Mode: DRY RUN\n")

    if not chunks:
        print("Nothing to translate.")
        conn.close()
        return

    translated = 0
    errors = 0
    consecutive_errors = 0

    for chunk_id, text_content, source_id, linked_entity_ids in chunks:
        if not text_content or not text_content.strip():
            continue

        try:
            result = translate_chunk(client, model, text_content, dry_run=args.dry_run)

            if args.dry_run:
                # Only show one chunk in dry-run mode
                break

            c.execute(
                "UPDATE chunk_registry SET translated_content = ? WHERE chunk_id = ?",
                (result, chunk_id)
            )
            conn.commit()

            translated += 1
            consecutive_errors = 0

            source_tag = f"[{source_id}]"
            print(f"  ✓ {chunk_id} {source_tag} ({len(text_content)}→{len(result)} chars)")

            time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            errors += 1
            consecutive_errors += 1
            print(f"  ✗ {chunk_id}: {e}")

            if consecutive_errors >= MAX_ERRORS:
                print(f"\nStopped after {MAX_ERRORS} consecutive errors.")
                break

            time.sleep(1.0)  # back off on error

    conn.close()

    if not args.dry_run:
        print(f"\nDone. Translated: {translated}  Errors: {errors}")
        # Show how many remain
        conn2 = sqlite3.connect(DB)
        c2 = conn2.cursor()
        c2.execute("SELECT COUNT(*) FROM chunk_registry WHERE language='ja' AND (translated_content IS NULL OR translated_content='')")
        remaining = c2.fetchone()[0]
        conn2.close()
        print(f"Remaining untranslated JA chunks: {remaining:,}")


if __name__ == "__main__":
    main()
