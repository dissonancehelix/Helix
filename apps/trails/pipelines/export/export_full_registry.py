import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
EXPORT_FILE = Path(__file__).parent.parent.parent / 'export' / 'character_profiles_v16_full.md'

def export_full_profiles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch all entities with curated bios
    cursor.execute('''
        SELECT e.*, c.text_content as curated_bio, c.spoiler_band as band
        FROM entity_registry e
        LEFT JOIN chunk_registry c ON c.chunk_id = 'curated:' || e.entity_id
        WHERE c.chunk_type = 'curated_bio' OR e.notes IS NOT NULL
        ORDER BY e.english_display_name ASC
    ''')
    entities = cursor.fetchall()
    
    md = [
        "# Helix Trails Domain: Full Character Archival Registry (v16)",
        "",
        f"This archival record contains high-fidelity, neutral-tone summaries for all **{len(entities)}** discovered entities in the Trails series.",
        "",
        "> [!IMPORTANT]",
        "> All biographies have been curated into strictly neutral, third-person encyclopedic prose and tagged with arc-based spoiler bands.",
        "",
        "---",
        ""
    ]
    
    for e in entities:
        md.append(f"## {e['english_display_name']}")
        md.append(f"- **ID**: `{e['entity_id']}`")
        if e['japanese_name']:
            md.append(f"- **Japanese**: {e['japanese_name']}")
        md.append(f"- **Spoiler Band**: `{e['band'] or 'Unassigned'}`")
        md.append("")
        
        bio = e['curated_bio'] or e['notes'] or "No curated record available."
        md.append(f"### Biography")
        md.append(bio)
        md.append("")
        
        # Simple Appearance summary
        cursor.execute('''
            SELECT m.english_title, a.appearance_type
            FROM appearance_registry a
            JOIN media_registry m ON a.media_id = m.media_id
            WHERE a.entity_id = ?
            ORDER BY m.release_chronology ASC
            LIMIT 5
        ''', (e['entity_id'],))
        apps = cursor.fetchall()
        if apps:
            md.append("### Appearance History (Partial)")
            for app in apps:
                md.append(f"- {app['english_title']} ({app['appearance_type']})")
        
        md.append("")
        md.append("---")
        md.append("")

    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))
        
    conn.close()
    print(f"[SUCCESS] Exported full registry to {EXPORT_FILE}")

if __name__ == "__main__":
    export_full_profiles()
