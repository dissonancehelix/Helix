import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
EXPORT_FILE = Path(__file__).parent.parent.parent / 'export' / 'media_catalog.md'

def export_catalog_v5():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch Media joined with Game Metadata
    cursor.execute('''
        SELECT m.*, g.arc, g.platform_info 
        FROM media_registry m 
        LEFT JOIN games_registry g ON m.media_id = g.media_id 
        ORDER BY m.is_main_series DESC, m.release_chronology ASC
    ''')
    media_items = cursor.fetchall()
    
    md = [
        "# Helix Trails Domain: Transmedia Catalog (v5)",
        "",
        "This catalog provides an encyclopedic overview of the Trails (Kiseki) media universe, tracked as separate registries for games, anime, and other transmedia adaptations.",
        "",
        "## Main Series (Game Backbone)",
        "| Arc | Title | JP Release | EN Release | Platforms |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    
    for m in media_items:
        if m['is_main_series']:
            md.append(f"| {m['arc'] or 'N/A'} | **{m['english_title']}** | {m['release_date_jp']} | {m['release_date_en'] or 'TBA'} | {m['platform_info'] or 'N/A'} |")
            
    md.append("")
    md.append("## Transmedia (Anime, Manga, Drama CDs)")
    md.append("| Type | Title | JP Release | Publisher |",)
    md.append("| :--- | :--- | :--- | :--- |")
    
    for m in media_items:
        if not m['is_main_series']:
            md.append(f"| {m['media_type'].capitalize()} | {m['english_title']} | {m['release_date_jp']} | {m['publisher']} |")

    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))
        
    conn.close()
    print(f"Exported Transmedia Catalog to {EXPORT_FILE}")

if __name__ == "__main__":
    export_catalog_v5()
