import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'
EXPORT_PATH = Path(__file__).parent.parent.parent / 'export' / 'registry_export.jsonl'

def export_backbone_jsonl():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(EXPORT_PATH, 'w', encoding='utf-8') as f:
        # 1. Export Entities (with full relational nodes)
        print("Exporting Relational Entity Graph to JSONL...")
        cursor.execute("SELECT * FROM entity_registry")
        for ent in cursor.fetchall():
            record = dict(ent)
            record['record_type'] = 'entity'
            
            # Sub-query for Appearances
            cursor.execute('''
                SELECT m.english_title, a.appearance_type, a.debut_flag
                FROM appearance_registry a
                JOIN media_registry m ON a.media_id = m.media_id
                WHERE a.entity_id = ?
            ''', (record['entity_id'],))
            record['appearances'] = [dict(a) for a in cursor.fetchall()]

            # Sub-query for Relationships (VA, Factions, etc)
            cursor.execute('''
                SELECT r.relationship_type, e.english_display_name as target_name, r.object_id as target_id
                FROM relationship_registry r
                JOIN entity_registry e ON r.object_id = e.entity_id
                WHERE r.subject_entity_id = ?
            ''', (record['entity_id'],))
            record['relationships'] = [dict(r) for r in cursor.fetchall()]

            # Sub-query for Curated Bio
            cursor.execute('''
                SELECT text_content, spoiler_band 
                FROM chunk_registry 
                WHERE chunk_id = ? AND chunk_type = 'curated_bio'
            ''', (f"curated:{record['entity_id']}",))
            bio = cursor.fetchone()
            if bio:
                record['curated_bio'] = bio['text_content']
                record['spoiler_band'] = bio['spoiler_band']
            
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # 2. Export Media Metadata
        print("Exporting Media Metadata to JSONL...")
        cursor.execute("SELECT * FROM media_registry")
        for med in cursor.fetchall():
            record = dict(med)
            record['record_type'] = 'media'
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    conn.close()
    print(f"[SUCCESS] Digital Registry Export complete: {EXPORT_PATH}")

if __name__ == "__main__":
    export_backbone_jsonl()
