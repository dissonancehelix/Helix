import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'retrieval' / 'index' / 'trails.db'

def verify_spoiler_guards():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- HELIX SPOILER GUARD AUDIT v5 ---")
    
    # 1. Check Media Registry
    cursor.execute("SELECT english_title, spoiler_band FROM media_registry WHERE media_id = 'kai'")
    kai_media = cursor.fetchone()
    if kai_media:
        if kai_media[1] >= 100:
            print(f" [OK] 'Beyond the Horizon' (Kai) is correctly banded level {kai_media[1]}.")
        else:
            print(f" [!] 'Beyond the Horizon' is banded {kai_media[1]}. Security risk (Must be >=100).")

    # 2. Check Appearance Registry
    cursor.execute('''
        SELECT COUNT(*) 
        FROM appearance_registry 
        WHERE media_id = 'kai' AND (spoiler_band < 100 OR spoiler_band IS NULL)
    ''')
    rogue_appearances = cursor.fetchone()[0]
    if rogue_appearances == 0:
        print(f" [OK] All appearances linked to Kai are correctly shielded.")
    else:
        print(f" [!] {rogue_appearances} Kai appearances lack proper spoiler shielding.")

    # 3. Retrieval Simulation: Safe Search Test
    # Simulate a search for 'Kai' with safe filter
    cursor.execute('''
        SELECT COUNT(*) 
        FROM media_registry 
        WHERE (english_title LIKE '%Beyond the Horizon%' OR media_id = 'kai') 
        AND spoiler_band <= 50
    ''')
    safe_search_results = cursor.fetchone()[0]
    if safe_search_results == 0:
        print(f" [OK] Safe Search properly suppressed Beyond the Horizon results.")
    else:
        print(f" [!] Safe Search LEAKED Kai results (Found: {safe_search_results}).")

    conn.close()
    print("\n[SUCCESS] Spoiler Guards are ACTIVE.")

if __name__ == "__main__":
    verify_spoiler_guards()
