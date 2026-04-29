import sqlite3
import json
from pathlib import Path

class TrailsSearch:
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
        else:
            self.db_path = Path(db_path)
            
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search_entities(self, query, arc=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = '''
            SELECT * FROM entity_registry 
            WHERE (english_display_name LIKE ? OR japanese_name LIKE ? OR aliases LIKE ?)
        '''
        params = [f'%{query}%', f'%{query}%', f'%{query}%']
        
        if arc:
            sql += " AND aliases LIKE ?"
            params.append(f"%arc:{arc}%")
            
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_appearance_history(self, entity_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.english_title, m.media_type, a.appearance_type, a.debut_flag, m.release_chronology
            FROM appearance_registry a
            JOIN media_registry m ON a.media_id = m.media_id
            WHERE a.entity_id = ?
            ORDER BY m.release_chronology ASC
        ''', (entity_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_voice_actors(self, entity_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.english_display_name as name, r.relationship_type as role
            FROM relationship_registry r
            JOIN entity_registry e ON r.object_id = e.entity_id
            WHERE r.subject_entity_id = ? AND r.relationship_type LIKE 'voiced_by%'
        ''', (entity_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def search_by_talent(self, va_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e_char.english_display_name, r.relationship_type
            FROM relationship_registry r
            JOIN entity_registry e_char ON r.subject_entity_id = e_char.entity_id
            JOIN entity_registry e_va ON r.object_id = e_va.entity_id
            WHERE e_va.english_display_name LIKE ?
        ''', (f'%{va_name}%',))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_registry_record(self, entity_id, safe_mode=True):
        """Returns a high-fidelity record including Bio + Appearances + Talent."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM entity_registry WHERE entity_id = ?", (entity_id,))
        entity = cursor.fetchone()
        if not entity: return None
        
        record = dict(entity)
        
        # Bio
        max_band = 50 if safe_mode else 100
        cursor.execute('''
            SELECT text_content 
            FROM chunk_registry 
            WHERE chunk_id = ? AND spoiler_band <= ?
        ''', (f"curated:{entity_id}", max_band))
        bio = cursor.fetchone()
        record['bio'] = bio[0] if bio else "No safe biography available."
        
        # Appearances & Talent
        record['appearances'] = self.get_appearance_history(entity_id)
        record['talent'] = self.get_voice_actors(entity_id)
        
        conn.close()
        return record

    def search_chunks_fts(self, query, safe_mode=True):
        """Performs lexical search on the FTS5 virtual table."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        max_band = 50 if safe_mode else 100
        
        cursor.execute('''
            SELECT f.text_content, f.chunk_id, c.spoiler_band, c.chunk_type
            FROM chunks_fts f
            JOIN chunk_registry c ON f.chunk_id = c.chunk_id
            WHERE chunks_fts MATCH ? AND c.spoiler_band <= ?
            ORDER BY rank
        ''', (query, max_band))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

if __name__ == "__main__":
    # Self-test
    ts = TrailsSearch()
    print("Testing TrailsSearch Utility...")
    estelle = ts.get_registry_record("char:estelle_bright", safe_mode=True)
    if estelle:
        print(f"Found Registry Record for: {estelle['english_display_name']}")
        print(f"Bio: {estelle['bio'][:100]}...")
    else:
        print("Record not found.")
