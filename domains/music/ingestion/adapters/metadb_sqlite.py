import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class MetadbSqliteReader:
    """
    Reader for foobar2000's metadb.sqlite or a canonical export thereof.
    Expected schema matches the Helix Music Lab megaprompt requirements.
    """
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.db_path.exists():
            print(f"Warning: metadb.sqlite not found at {self.db_path}")
            return []

        results = []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # We assume a 'tracks' or 'library' table exists. 
            # If not, we try to detect typical metadb.sqlite layouts.
            # For the purpose of Helix, we prioritize a flattened table if available.
            
            table_name = "tracks" # Default expectation
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            except sqlite3.OperationalError:
                # Try discovery
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                if "library" in tables:
                    table_name = "library"
                elif tables:
                    table_name = tables[0]
                else:
                    return []

            cursor.execute(f"SELECT * FROM {table_name}")
            for row in cursor.fetchall():
                results.append(dict(row))
            
            conn.close()
        except Exception as e:
            print(f"Error reading metadb.sqlite: {e}")
        
        return results

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw record from metadb.sqlite into Helix structured track objects.
        """
        # Mapping rules from megaprompt:
        # ARTIST → Primary composer
        # ALBUM ARTIST → Soundtrack release artist
        # FEATURING → Additional contributors
        # SOUND TEAM → Composer collective or studio team
        # FRANCHISE → Game series grouping
        # PLATFORM → Hardware platform
        # SOUND CHIP → Hardware synthesis chip

        mapped = {
            "title":        raw_record.get("TITLE", raw_record.get("title")),
            "artist":       raw_record.get("ARTIST", raw_record.get("artist")),
            "album":        raw_record.get("ALBUM", raw_record.get("album")),
            "date":         raw_record.get("DATE", raw_record.get("date")),
            "genre":        raw_record.get("GENRE", raw_record.get("genre")),
            "featuring":    raw_record.get("FEATURING", raw_record.get("featuring")),
            "album_artist": raw_record.get("ALBUM ARTIST", raw_record.get("album_artist")),
            "sound_team":   raw_record.get("SOUND TEAM", raw_record.get("sound_team")),
            "franchise":    raw_record.get("FRANCHISE", raw_record.get("franchise")),
            "track_number": raw_record.get("TRACKNUMBER", raw_record.get("track_number")),
            "total_tracks": raw_record.get("TOTALTRACKS", raw_record.get("total_tracks")),
            "disc_number":  raw_record.get("DISCNUMBER", raw_record.get("disc_number")),
            "total_discs":  raw_record.get("TOTALDISCS", raw_record.get("total_discs")),
            "comment":      raw_record.get("COMMENT", raw_record.get("comment")),
            "platform":     raw_record.get("PLATFORM", raw_record.get("platform")),
            "sound_chip":   raw_record.get("SOUND CHIP", raw_record.get("sound_chip")),
            "file_path":    raw_record.get("path", raw_record.get("file_path"))
        }

        # Handle specific Helix interpretation rules
        # (Though we keep the keys mapped as requested, 
        # the architecture doc defines their meaning)
        
        return {k: v for k, v in mapped.items() if v is not None}
