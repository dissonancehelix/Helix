import sqlite3
import re
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')

# I will provide the neutral rewrites as a curator model
curated_bios = [
    {
        "entity_id": "char:van_arkride",
        "neutral_bio": "Van Arkride is a Spriggan based in the Old Town district of Edith, the capital of the Calvard Republic. Operating from the Arkride Solutions Office, he handles tasks ranging from detective work to negotiations that fall outside the jurisdiction of official authorities like the police or Bracer Guild. Known for his pragmatism and extensive network within both the surface and underworld, he is often characterized by his distinctive blue-streaked black hair and a personal code of ethics that dictates his professional conduct."
    },
    {
        "entity_id": "char:estelle_bright",
        "neutral_bio": "Estelle Bright is a Senior Bracer of the Liberl Kingdom's Bracer Guild. She is the daughter of Cassius Bright and the adoptive sister of Joshua Bright. Her career began during the Orbal Phenomenon in Liberl, eventually leading her to play a central role in resolving the Liberl Ark incident. Professionally, she is recognized for her proficiency with a ceremonial staff and her leadership during multinational crises, including the Great Twilight in Erebonia."
    },
    {
        "entity_id": "char:joshua_bright",
        "neutral_bio": "Joshua Bright is a Senior Bracer and the adoptive son of Cassius Bright. Originally born in the Erebonian Empire, he was later recruited into the secret society Ouroboros as Enforcer No. XIII, 'The Black Fang,' before defecting and finding refuge in the Liberl Kingdom. He is a specialist in dual-blade combat and stealth operations, often working alongside Estelle Bright to resolve high-stakes international incidents."
    },
    {
        "entity_id": "char:agnes_claudel",
        "neutral_bio": "Agnès Claudel is a student at the Aramis High School in Edith and a client-turned-assistant at the Arkride Solutions Office. She is the great-granddaughter of the renowned scientist C. Epstein. Her involvement in the Calvard arc began when she sought Van Arkride's assistance in retrieving the 'Genesis' orbal orbs, artifacts left behind by her great-grandfather that possess unique and potentially world-altering properties."
    }
]

def curate_tone():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    source_id = "curation:wikipedia_style_v1"
    
    # Register the curation source
    cursor.execute('''
        INSERT OR REPLACE INTO source_registry (source_id, title, source_class, language, trust_tier, quality_tone)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (source_id, "Helix Curation Layer (Wikipedia Mode)", "curation", "en", 0, "encyclopedic"))

    for bio in curated_bios:
        chunk_id = f"chk_curated_{bio['entity_id'].split(':')[-1]}"
        
        # Ingest the neutral summary
        cursor.execute('''
            INSERT OR REPLACE INTO chunks (chunk_id, source_id, text_content, language, trust_tier, quality_tone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chunk_id, source_id, bio['neutral_bio'], "en", 0, "encyclopedic"))

        # Mark the entity as curated
        cursor.execute('''
            UPDATE entities SET creation_status = 'curated'
            WHERE entity_id = ?
        ''', (bio['entity_id'],))

    conn.commit()
    conn.close()
    print(f"Successfully curated {len(curated_bios)} entities into Wikipedia-style neutrality.")

if __name__ == "__main__":
    curate_tone()
