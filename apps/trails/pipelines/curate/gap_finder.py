import sqlite3
import os
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path('retrieval/index/trails.db')

class RegistryAuditor:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def run_audit(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Total Coverage Stats
        cursor.execute("SELECT COUNT(*) FROM entities")
        total_entities = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT e.entity_id) 
            FROM entities e 
            JOIN chunks c ON (c.text_content LIKE '%' || e.display_name || '%')
            WHERE c.trust_tier = 0
        """)
        entities_with_official_bio = cursor.fetchone()[0]
        
        print(f"--- REGISTRY AUDIT ---")
        print(f"Total Skeleton Entities: {total_entities}")
        print(f"Entities with Tier 0 (Official) Coverage: {entities_with_official_bio}")
        print(f"Coverage Gap: {total_entities - entities_with_official_bio} characters")
        print("-" * 30)
        
        # 2. Identify the 'Gaps'
        cursor.execute("""
            SELECT entity_id, display_name FROM entities 
            WHERE entity_id NOT IN (
                SELECT DISTINCT e.entity_id 
                FROM entities e 
                JOIN chunks c ON (c.text_content LIKE '%' || e.display_name || '%')
                WHERE c.trust_tier = 0
            )
            LIMIT 20
        """)
        gaps = cursor.fetchall()
        print("Sample Coverage Gaps (Characters missing official bios):")
        for g in gaps:
            print(f" - {g[1]} ({g[0]})")
            
        conn.close()

if __name__ == "__main__":
    auditor = RegistryAuditor()
    auditor.run_audit()
