import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class MetadbSqliteReader:
    """
    [DEPRECATED - PHASE 7]
    Due to the Phase 7 Bridge Contract Refinement, Helix MUST NOT use foobar's private 
    metadb.sqlite as an integration contract. 
    
    The live foobar-facing custom metadata plane is now:
    C:\\Users\\dissonance\\AppData\\Roaming\\foobar2000-v2\\external-tags.db
    
    Use ingestion.adapters.foobar.FoobarAdapter instead.
    """
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    def read_all(self) -> List[Dict[str, Any]]:
        print("WARNING: metadb.sqlite is NOT an integration contract. Bypassing read.")
        print("Use external-tags.db and the FoobarAdapter for live tag fetching.")
        return []

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        return {}
