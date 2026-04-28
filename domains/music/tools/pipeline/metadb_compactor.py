"""
metadb_compactor.py — Safely compact foobar2000 metadb.sqlite
"""
import sqlite3
import shutil
import time
from pathlib import Path
import json

FOOBAR_APPDATA = Path(r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2")
METADB_SQLITE = FOOBAR_APPDATA / "metadb.sqlite"
REPORTS_DIR = Path(__file__).parent / "reports"

def is_foobar_running():
    import psutil
    for p in psutil.process_iter(['name']):
        if p.info['name'] and 'foobar2000' in p.info['name'].lower():
            return True
    return False

def compact_metadb():
    if not METADB_SQLITE.exists():
        return {"error": f"Not found: {METADB_SQLITE}"}

    original_size = METADB_SQLITE.stat().st_size
    backup_path = FOOBAR_APPDATA / f"metadb.sqlite.bak.{int(time.time())}"
    compact_path = FOOBAR_APPDATA / "metadb_compacted.sqlite"

    result = {
        "original_path": str(METADB_SQLITE),
        "original_size_mb": original_size / (1024*1024),
        "compacted_path": str(compact_path),
        "status": "pending"
    }

    try:
        # Create compact version using VACUUM INTO (safe fallback from python directly executing on LIVE db)
        # Even if foobar is running, vacuum into might work, but it's safer if closed.
        conn = sqlite3.connect(f"file:{METADB_SQLITE}?mode=ro", uri=True)
        
        if compact_path.exists():
            compact_path.unlink()
            
        conn.execute(f"VACUUM INTO '{compact_path}'")
        conn.close()
        
        # Verify integrity of new file
        compact_conn = sqlite3.connect(compact_path)
        cur = compact_conn.cursor()
        cur.execute("PRAGMA integrity_check")
        integrity = cur.fetchone()[0]
        compact_conn.close()
        
        compact_size = compact_path.stat().st_size
        result["compacted_size_mb"] = compact_size / (1024*1024)
        result["savings_mb"] = result["original_size_mb"] - result["compacted_size_mb"]
        result["integrity_check"] = integrity
        
        if integrity == "ok":
            result["status"] = "success_ready_for_swap"
            result["instructions"] = (
                "The compacted database is ready. To complete the swap safely:\n"
                "1. Close foobar2000 entirely.\n"
                f"2. Rename or move original: {METADB_SQLITE}\n"
                f"3. Rename compacted to original name: {compact_path} -> metadb.sqlite\n"
                "4. Restart foobar2000 and verify functionality."
            )
        else:
            result["status"] = "failed_integrity_check"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        
    return result

if __name__ == "__main__":
    report = compact_metadb()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "metadb_compaction_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
