import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

class SourceManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)

    def register_source(self, source_id, title, source_class, language, **kwargs):
        """
        Registers a source in the master catalog.
        """
        cursor = self.conn.cursor()
        
        # Default metadata
        data = {
            'source_id': source_id,
            'title': title,
            'source_class': source_class,
            'language': language,
            'origin_url': kwargs.get('origin_url'),
            'local_path': kwargs.get('local_path'),
            'trust_tier': kwargs.get('trust_tier', 1),
            'spoiler_band': kwargs.get('spoiler_band'),
            'notes': kwargs.get('notes')
        }
        
        cursor.execute('''
            INSERT OR REPLACE INTO source_registry (
                source_id, title, source_class, language, origin_url, local_path, trust_tier, spoiler_band, notes
            ) VALUES (:source_id, :title, :source_class, :language, :origin_url, :local_path, :trust_tier, :spoiler_band, :notes)
        ''', data)
        
        self.conn.commit()
        print(f"Registered Source: {source_id} ({title}) [Tier {data['trust_tier']}]")

    def update_status(self, source_id, **kwargs):
        cursor = self.conn.cursor()
        updates = []
        params = {'source_id': source_id}
        
        for key in ['ingestion_status', 'parse_status', 'normalization_status', 'export_status']:
            if key in kwargs:
                updates.append(f"{key} = :{key}")
                params[key] = kwargs[key]
        
        if updates:
            sql = f"UPDATE source_registry SET {', '.join(updates)} WHERE source_id = :source_id"
            cursor.execute(sql, params)
            self.conn.commit()

    def list_sources(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT source_id, title, source_class, trust_tier, ingestion_status FROM source_registry")
        return cursor.fetchall()

if __name__ == "__main__":
    manager = SourceManager()
    
    # Register Initial Tier 0/1 Sources
    manager.register_source(
        "official:nisa_daybreak_bios", 
        "NIS America Daybreak Character Bios", 
        "official_web", 
        "en", 
        origin_url="https://thelegendofheroes.com/daybreak/characters",
        trust_tier=0,
        spoiler_band="Calvard"
    )
    
    manager.register_source(
        "official:falcom_kuro_bios", 
        "Falcom Kuro no Kiseki Character Bios", 
        "official_web", 
        "ja", 
        origin_url="https://www.falcom.co.jp/kuro/character/",
        trust_tier=0,
        spoiler_band="Calvard"
    )

    manager.register_source(
        "official:falcom_kai_bios", 
        "Falcom Kai no Kiseki Character Bios", 
        "official_web", 
        "ja", 
        origin_url="https://www.falcom.co.jp/kai/character/",
        trust_tier=0,
        spoiler_band="Kai" # SPOILER FRONTIER
    )
    
    manager.register_source(
        "wiki:kiseki_fandom", 
        "Kiseki Fandom Wiki", 
        "fan_wiki", 
        "en", 
        origin_url="https://kiseki.fandom.com/",
        trust_tier=2
    )

    manager.register_source(
        "wiki:ja_wikipedia_chars", 
        "Japanese Wikipedia Character List", 
        "wikipedia_ja", 
        "ja", 
        local_path="corpus/wiki/ja_wiki_characters.html",
        trust_tier=1
    )
