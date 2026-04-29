import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

# Spoiler Band Mapping (Arc-based)
ARC_BANDS = {
    "sky_fc": 10, "sky_sc": 10, "sky_3rd": 15,
    "zero": 20, "azure": 25,
    "cs1": 40, "cs2": 45, "cs3": 50, "cs4": 55,
    "reverie": 60,
    "daybreak": 70, "daybreak_2": 75,
    "kai": 100
}

def run_auto_banding():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Executing Automated Spoiler Banding Pass (v16)...")
    
    # 1. Update Appearance Registry Bands from Media Registry
    # (Propagate existing media bands)
    cursor.execute('''
        UPDATE appearance_registry 
        SET spoiler_band = (
            SELECT spoiler_band FROM media_registry 
            WHERE media_registry.media_id = appearance_registry.media_id
        )
    ''')
    
    # 2. Update Chunk Registry Bands from Appearance Registry (Debut)
    # Target curated biographies
    cursor.execute('''
        UPDATE chunk_registry 
        SET spoiler_band = (
            SELECT a.spoiler_band 
            FROM appearance_registry a
            WHERE a.entity_id = REPLACE(chunk_registry.chunk_id, 'curated:char:', '')
            AND a.debut_flag = 1
            LIMIT 1
        )
        WHERE chunk_type = 'curated_bio'
    ''')
    
    # 3. Handle Special Cases (Kai Lock)
    # Ensure anything linked to 'kai' is strictly 100
    cursor.execute('''
        UPDATE chunk_registry 
        SET spoiler_band = 100 
        WHERE chunk_id IN (
            SELECT 'curated:char:' || entity_id 
            FROM appearance_registry 
            WHERE media_id = 'kai'
        )
    ''')

    conn.commit()
    conn.close()
    print("[SUCCESS] Spoiler Bands propagated for the 500+ character backbone.")

if __name__ == "__main__":
    run_auto_banding()
