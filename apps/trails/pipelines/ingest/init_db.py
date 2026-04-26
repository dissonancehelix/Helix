import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def init_db():
    # Ensure directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- 1. MEDIA_REGISTRY (Umbrella table for all media objects) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_registry (
            media_id TEXT PRIMARY KEY,
            media_type TEXT NOT NULL, -- main_game, spin_off, anime, manga, drama_cd, etc.
            english_title TEXT NOT NULL,
            japanese_title TEXT NOT NULL,
            aliases TEXT,             -- JSON list
            publisher TEXT,           -- /distributor
            release_date_jp TEXT,
            release_date_en TEXT,
            internal_chronology TEXT, -- Timeline metadata
            release_chronology INTEGER,
            spoiler_band INTEGER DEFAULT 10, -- Normalized progression band
            is_main_series BOOLEAN DEFAULT 0,
            canonical_notes TEXT
        )
    ''')

    # --- 2. GAMES (Subtype table / compatibility view) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games_registry (
            media_id TEXT PRIMARY KEY,
            platform_info TEXT,
            arc TEXT,
            release_order INTEGER,
            internal_order INTEGER,
            localization_metadata TEXT,
            FOREIGN KEY(media_id) REFERENCES media_registry(media_id)
        )
    ''')

    # --- 3. ENTITY_REGISTRY (Backbone) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entity_registry (
            entity_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL, -- character, place, faction, staff, concept, etc.
            english_display_name TEXT NOT NULL,
            japanese_name TEXT,
            aliases TEXT,             -- JSON list
            notes TEXT
        )
    ''')

    # --- 4. SOURCE_REGISTRY (Provenance Tracker) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_registry (
            source_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source_class TEXT NOT NULL, -- official_web, official_script, fan_wiki, wikipedia_ja, etc.
            language TEXT NOT NULL,
            origin_url TEXT,
            local_path TEXT,
            trust_tier INTEGER DEFAULT 1, -- 0 (Official) to 3 (Speculative)
            ingestion_status TEXT DEFAULT 'pending',
            parse_status TEXT DEFAULT 'pending',
            normalization_status TEXT DEFAULT 'pending',
            export_status TEXT DEFAULT 'pending',
            spoiler_band INTEGER DEFAULT 0,
            notes TEXT
        )
    ''')

    # --- 5. APPEARANCE_REGISTRY (Cross-media mapping layer) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appearance_registry (
            appearance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            media_id TEXT NOT NULL,
            appearance_type TEXT, -- main, support, cameo
            debut_flag BOOLEAN DEFAULT 0,
            canonical_weight INTEGER DEFAULT 100,
            spoiler_band INTEGER,
            source_id TEXT,
            notes TEXT,
            FOREIGN KEY(entity_id) REFERENCES entity_registry(entity_id),
            FOREIGN KEY(media_id) REFERENCES media_registry(media_id),
            FOREIGN KEY(source_id) REFERENCES source_registry(source_id)
        )
    ''')

    # --- 6. RELATIONSHIP_REGISTRY (Staff-media and entity-entity links) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationship_registry (
            relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_entity_id TEXT NOT NULL,
            object_id TEXT NOT NULL, -- entity_id or media_id
            relationship_type TEXT NOT NULL, -- director, writer, member_of, related_to
            source_id TEXT,
            notes TEXT,
            FOREIGN KEY(subject_entity_id) REFERENCES entity_registry(entity_id),
            FOREIGN KEY(source_id) REFERENCES source_registry(source_id)
        )
    ''')

    # --- 7. CHUNK_REGISTRY (Parsed retrieval chunks) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunk_registry (
            chunk_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            media_id TEXT,            -- optional
            linked_entity_ids TEXT,   -- JSON list
            text_content TEXT NOT NULL,
            language TEXT NOT NULL,
            spoiler_band INTEGER,
            chunk_type TEXT,          -- bio, dialogue, historical_fact, dev_note
            FOREIGN KEY(source_id) REFERENCES source_registry(source_id)
        )
    ''')

    # --- 8. LIFECYCLE_REGISTRY (Editorial-state tracking) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lifecycle_registry (
            object_id TEXT PRIMARY KEY, -- chunk_id, entity_id, or archive_id
            state TEXT NOT NULL,        -- raw, parsed, normalized, summarized, reviewed, export_ready
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewer_notes TEXT
        )
    ''')

    # --- FTS5 Virtual Table for Search ---
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            text_content, chunk_id UNINDEXED
        )
    ''')

    # Triggers for FTS consistency
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunk_registry BEGIN
      INSERT INTO chunks_fts(rowid, text_content, chunk_id) VALUES (new.rowid, new.text_content, new.chunk_id);
    END;
    ''')
    
    conn.commit()
    conn.close()
    print(f"Helix Trails Domain: v5 Transmedia Schema initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
