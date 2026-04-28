import sqlite3
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')

staff_data = [
    {"id": "staff:toshihiro_kondo", "name": "Toshihiro Kondo", "ja": "近藤季洋", "role": "President / Producer / Director"},
    {"id": "staff:hisayoshi_takeiri", "name": "Hisayoshi Takeiri", "ja": "竹入久喜", "role": "Lead Scenario Writer"},
    {"id": "staff:takayuki_kusano", "name": "Takayuki Kusano", "ja": "草野孝之", "role": "Director"},
    {"id": "staff:hayato_sonoda", "name": "Hayato Sonoda", "ja": "園田隼人", "role": "Composer (jdk)"},
    {"id": "staff:takahiro_unisuga", "name": "Takahiro Unisuga", "ja": "宇仁菅孝宏", "role": "Composer (jdk)"},
    {"id": "staff:yukihiro_jindo", "name": "Yukihiro Jindo", "ja": "神藤由東大", "role": "Composer / Arranger (jdk)"},
]

# Mapping staff to key arcs/games (Simplified for first pass)
staff_relationships = [
    ("staff:toshihiro_kondo", "game:sky_fc", "Director"),
    ("staff:toshihiro_kondo", "game:sky_sc", "Director"),
    ("staff:hisayoshi_takeiri", "game:sky_fc", "Scenario"),
    ("staff:hisayoshi_takeiri", "game:daybreak1", "Scenario"),
    ("staff:takayuki_kusano", "game:cs1", "Director"),
    ("staff:takayuki_kusano", "game:daybreak1", "Director"),
]

def ingest_staff():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Register source
    cursor.execute('''
        INSERT OR REPLACE INTO source_registry (source_id, title, source_class, language, trust_tier)
        VALUES (?, ?, ?, ?, ?)
    ''', ("metadata:staff_credits", "Official Development Credits", "metadata_staff", "multi", 0))

    for s in staff_data:
        # Register in entities
        cursor.execute('''
            INSERT OR REPLACE INTO entities (entity_id, type, display_name, japanese_name, trust_tier, creation_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (s["id"], 'staff', s["name"], s["ja"], 0, 'verified'))
        
        # Add descriptive chunk (Registry style)
        chunk_id = f"chk_staff_{s['id'].split(':')[-1]}"
        text = f"Staff Profile - {s['name']} ({s['ja']})\nRole: {s['role']}\nA key member of the Nihon Falcom development team responsible for the Trails (Kiseki) series."
        
        cursor.execute('''
            INSERT OR REPLACE INTO chunks (chunk_id, source_id, text_content, language, trust_tier, quality_tone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chunk_id, "metadata:staff_credits", text, 'en', 0, 'encyclopedic'))

    for r in staff_relationships:
        cursor.execute('''
            INSERT OR REPLACE INTO entity_relationships (source_id, target_id, relationship_type)
            VALUES (?, ?, ?)
        ''', (r[0], r[1], r[2]))

    conn.commit()
    conn.close()
    print(f"Successfully ingested {len(staff_data)} staff members and {len(staff_relationships)} relationships.")

if __name__ == "__main__":
    ingest_staff()
