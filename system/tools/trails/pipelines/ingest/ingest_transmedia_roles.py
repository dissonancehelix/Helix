import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

# High-Fidelity Role Mapping (Top Cast across Transmedia)
role_data = [
    # Estelle Bright
    {"char": "char:estelle_bright", "media": "sky_fc", "role": "Protagonist", "debut": 1},
    {"char": "char:estelle_bright", "media": "sky_sc", "role": "Protagonist", "debut": 0},
    {"char": "char:estelle_bright", "media": "sky_3rd", "role": "Supporting", "debut": 0},
    {"char": "char:estelle_bright", "media": "zero", "role": "Supporting", "debut": 0},
    {"char": "char:estelle_bright", "media": "azure", "role": "Cameo", "debut": 0},
    {"char": "char:estelle_bright", "media": "cs4", "role": "Supporting", "debut": 0},
    {"char": "char:estelle_bright", "media": "reverie", "role": "Supporting", "debut": 0},
    {"char": "char:estelle_bright", "media": "sky_ova", "role": "Protagonist", "debut": 0},
    {"char": "char:estelle_bright", "media": "manga_ring", "role": "Protagonist", "debut": 0},

    # Leonhardt (Loewe) - Gap characters bridged to Transmedia
    {"char": "char:leonhardt", "media": "sky_fc", "role": "Antagonist", "debut": 1},
    {"char": "char:leonhardt", "media": "sky_sc", "role": "Antagonist", "debut": 0},
    {"char": "char:leonhardt", "media": "manga_loewe", "role": "Protagonist", "debut": 0},
    {"char": "char:leonhardt", "media": "sky_ova", "role": "Antagonist", "debut": 0},

    # Rean Schwarzer
    {"char": "char:rean_schwarzer", "media": "cs1", "role": "Protagonist", "debut": 1},
    {"char": "char:rean_schwarzer", "media": "cs2", "role": "Protagonist", "debut": 0},
    {"char": "char:rean_schwarzer", "media": "cs3", "role": "Protagonist", "debut": 0},
    {"char": "char:rean_schwarzer", "media": "cs4", "role": "Protagonist", "debut": 0},
    {"char": "char:rean_schwarzer", "media": "reverie", "role": "Protagonist", "debut": 0},
    {"char": "char:rean_schwarzer", "media": "northern_war", "role": "Supporting", "debut": 0},
    {"char": "char:rean_schwarzer", "media": "daybreak", "role": "Cameo", "debut": 0},
]

def ingest_transmedia_roles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Ingesting High-Fidelity Transmedia Roles (Phase 4)...")
    
    for r in role_data:
        # First ensure the entity exists in the registry
        # (This handles the Leonhardt/Loewe gap bridging)
        cursor.execute('''
            INSERT OR IGNORE INTO entity_registry (entity_id, entity_type, english_display_name)
            VALUES (?, 'character', ?)
        ''', (r["char"], r["char"].split(':')[-1].replace('_', ' ').title()))

        # Now update/insert the appearance role
        cursor.execute('''
            INSERT OR REPLACE INTO appearance_registry (
                entity_id, media_id, appearance_type, debut_flag
            ) VALUES (?, ?, ?, ?)
        ''', (r["char"], r["media"], r["role"], r["debut"]))

    conn.commit()
    conn.close()
    print(f"Transmedia mapping complete for {len(role_data)} character scenarios.")

if __name__ == "__main__":
    ingest_transmedia_roles()
