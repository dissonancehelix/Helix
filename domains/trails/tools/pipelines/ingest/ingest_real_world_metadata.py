import sqlite3
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')

games_data = [
    # Liberl Arc
    {"id": "sky_fc", "en": "Trails in the Sky (FC)", "ja": "空の軌跡 FC", "jp_rel": "2004-06-24", "en_rel": "2011-03-29", "platforms": "PC, PSP, PS3, PSV", "arc": "Sky", "order": 1},
    {"id": "sky_sc", "en": "Trails in the Sky SC", "ja": "空の軌跡 SC", "jp_rel": "2006-03-09", "en_rel": "2015-10-29", "platforms": "PC, PSP, PS3, PSV", "arc": "Sky", "order": 2},
    {"id": "sky_3rd", "en": "Trails in the Sky the 3rd", "ja": "空の軌跡 the 3rd", "jp_rel": "2007-06-28", "en_rel": "2017-05-03", "platforms": "PC, PSP, PS3, PSV", "arc": "Sky", "order": 3},
    
    # Crossbell Arc
    {"id": "zero", "en": "Trails from Zero", "ja": "零の軌跡", "jp_rel": "2010-09-30", "en_rel": "2022-09-27", "platforms": "PC, PSP, PSV, PS4, Switch", "arc": "Crossbell", "order": 4},
    {"id": "azure", "en": "Trails to Azure", "ja": "碧の軌跡", "jp_rel": "2011-09-29", "en_rel": "2023-03-14", "platforms": "PC, PSP, PSV, PS4, Switch", "arc": "Crossbell", "order": 5},
    
    # Erebonia Arc
    {"id": "cs1", "en": "Trails of Cold Steel I", "ja": "閃の軌跡", "jp_rel": "2013-09-26", "en_rel": "2015-12-22", "platforms": "PC, PS3, PSV, PS4", "arc": "Erebonia", "order": 6},
    {"id": "cs2", "en": "Trails of Cold Steel II", "ja": "閃の軌跡 II", "jp_rel": "2014-09-25", "en_rel": "2016-09-06", "platforms": "PC, PS3, PSV, PS4", "arc": "Erebonia", "order": 7},
    {"id": "cs3", "en": "Trails of Cold Steel III", "ja": "閃の軌跡 III", "jp_rel": "2017-09-28", "en_rel": "2019-10-22", "platforms": "PC, PS4, Switch", "arc": "Erebonia", "order": 8},
    {"id": "cs4", "en": "Trails of Cold Steel IV", "ja": "閃の軌跡 IV", "jp_rel": "2018-09-27", "en_rel": "2020-10-27", "platforms": "PC, PS4, Switch", "arc": "Erebonia", "order": 9},
    {"id": "reverie", "en": "Trails into Reverie", "ja": "創の軌跡", "jp_rel": "2020-08-27", "en_rel": "2023-07-07", "platforms": "PC, PS4, PS5, Switch", "arc": "Erebonia", "order": 10},
    
    # Calvard Arc
    {"id": "daybreak1", "en": "Trails Through Daybreak", "ja": "黎の軌跡", "jp_rel": "2021-09-30", "en_rel": "2024-07-05", "platforms": "PC, PS4, PS5, Switch", "arc": "Calvard", "order": 11},
    {"id": "daybreak2", "en": "Trails Through Daybreak II", "ja": "黎の軌跡 II", "jp_rel": "2022-09-29", "en_rel": "2025-02-14", "platforms": "PC, PS4, PS5, Switch", "arc": "Calvard", "order": 12},
    {"id": "kai", "en": "Trails Beyond the Horizon", "ja": "界の軌跡", "jp_rel": "2024-09-26", "en_rel": "2026-01-15", "platforms": "PS4, PS5", "arc": "Calvard", "order": 13},
]

def ingest_metadata():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Register metadata source
    cursor.execute('''
        INSERT OR REPLACE INTO source_registry (source_id, title, source_class, language, trust_tier)
        VALUES (?, ?, ?, ?, ?)
    ''', ("metadata:series_chronology", "Official Trails Series Chronology", "metadata_series", "multi", 0))

    for g in games_data:
        cursor.execute('''
            INSERT OR REPLACE INTO games (game_id, title_en, title_ja, release_date_jp, release_date_en, platforms, arc, chronological_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (g["id"], g["en"], g["ja"], g["jp_rel"], g["en_rel"], g["platforms"], g["arc"], g["order"]))
        
        # Also register game as an entity
        cursor.execute('''
            INSERT OR REPLACE INTO entities (entity_id, type, display_name, japanese_name, trust_tier, creation_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (f"game:{g['id']}", 'game', g['en'], g['ja'], 0, 'verified'))

    conn.commit()
    conn.close()
    print(f"Successfully ingested {len(games_data)} series entries into the substrate.")

if __name__ == "__main__":
    ingest_metadata()
