import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
EXPORT_FILE = Path(__file__).parent.parent.parent / 'export' / 'character_profiles_v4.md'

def export_character_profiles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch all entities with notes (curated bios)
    cursor.execute("SELECT * FROM entity_registry WHERE notes IS NOT NULL")
    entities = cursor.fetchall()
    
    md = [
        "# Helix Trails Domain: Character Profiles (v4)",
        "",
        "This record consolidates character biographies and their full transmedia history across the Trails universe.",
        ""
    ]
    
    for e in entities:
        md.append(f"## {e['english_display_name']}")
        md.append(f"**Entity ID**: `{e['entity_id']}`")
        md.append("")
        md.append("### Biography (Neutral Tone)")
        md.append(e['notes'])
        md.append("")
        
        # Fetch Appearances
        md.append("### Transmedia History")
        md.append("| Media | Type | Role | Debut |",)
        md.append("| :--- | :--- | :--- | :--- |")
        
        cursor.execute('''
            SELECT m.english_title, m.media_type, a.appearance_type, a.debut_flag
            FROM appearance_registry a
            JOIN media_registry m ON a.media_id = m.media_id
            WHERE a.entity_id = ?
            ORDER BY m.release_chronology ASC
        ''', (e['entity_id'],))
        
        for a in cursor.fetchall():
            debut_tag = "✓" if a['debut_flag'] else ""
            md.append(f"| {a['english_title']} | {a['media_type'].capitalize()} | {a['appearance_type']} | {debut_tag} |")
        
        md.append("")
        md.append("---")
        md.append("")

    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))
        
    conn.close()
    print(f"Exported Character Profiles to {EXPORT_FILE}")

if __name__ == "__main__":
    export_character_profiles()
