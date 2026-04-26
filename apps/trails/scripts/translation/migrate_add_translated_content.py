"""
One-time migration: add translated_content column to chunk_registry.
Safe to re-run — skips if column already exists.

Usage:
    python scripts/translation/migrate_add_translated_content.py
"""
import sqlite3

DB = "C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db"


def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Check if column already exists
    c.execute("PRAGMA table_info(chunk_registry)")
    cols = {row[1] for row in c.fetchall()}

    if "translated_content" in cols:
        print("Column 'translated_content' already exists — nothing to do.")
        conn.close()
        return

    print("Adding 'translated_content TEXT' to chunk_registry...")
    c.execute("ALTER TABLE chunk_registry ADD COLUMN translated_content TEXT")
    conn.commit()

    c.execute("SELECT COUNT(*) FROM chunk_registry WHERE language = 'ja'")
    ja_count = c.fetchone()[0]
    print(f"Done. {ja_count:,} JA chunks are now eligible for translation.")
    conn.close()


if __name__ == "__main__":
    main()
