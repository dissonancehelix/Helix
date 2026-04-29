import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

def run_demos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- HELIX PHASE 3 RETRIEVAL DEMO ---")

    # Pattern A: All media a character appears in
    char_name = "Estelle Bright"
    print(f"\n[QUERY] Full appearance history for: {char_name}")
    cursor.execute('''
        SELECT m.english_title, m.media_type, a.appearance_type, a.debut_flag
        FROM appearance_registry a
        JOIN entity_registry e ON a.entity_id = e.entity_id
        JOIN media_registry m ON a.media_id = m.media_id
        WHERE e.english_display_name = ?
        ORDER BY m.release_chronology ASC
    ''', (char_name,))
    for row in cursor.fetchall():
        debut_tag = " [DEBUT]" if row['debut_flag'] else ""
        print(f" - {row['english_title']} ({row['media_type']}){debut_tag}")

    # Pattern B: All staff linked to a media item
    game_title = "Trails in the Sky FC"
    print(f"\n[QUERY] Project Credits for: {game_title}")
    cursor.execute('''
        SELECT e.english_display_name, r.relationship_type
        FROM relationship_registry r
        JOIN entity_registry e ON r.subject_entity_id = e.entity_id
        JOIN media_registry m ON r.object_id = m.media_id
        WHERE m.english_title = ?
    ''', (game_title,))
    for row in cursor.fetchall():
        print(f" - {row['english_display_name']} ({row['relationship_type']})")

    # Pattern C: Spoiler-Safe Faction Appearance Check
    print(f"\n[QUERY] Faction Presences (Spoiler Band <= 20)")
    # (Simulated for core cast presence)
    cursor.execute('''
        SELECT e.english_display_name, m.english_title
        FROM appearance_registry a
        JOIN entity_registry e ON a.entity_id = e.entity_id
        JOIN media_registry m ON a.media_id = m.media_id
        WHERE m.spoiler_band <= 20
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f" - {row['english_display_name']} appears in {row['english_title']}")

    conn.close()

if __name__ == "__main__":
    run_demos()
