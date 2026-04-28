"""
decode_external_tags.py — Decode foobar2000 external-tags.db binary meta format.

Foobar2000 external-tags.db uses a compact binary format for the meta BLOB.
This script attempts to decode it.
"""
import sqlite3
import struct
import json
from pathlib import Path

EXTERNAL_TAGS_DB = Path(r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\external-tags.db")

def decode_fb2k_meta(data: bytes) -> dict:
    """
    Attempt to decode foobar2000's compact tag format from external-tags.db.
    
    The format appears to be:
    - 4 bytes: number of fields (little-endian uint32)
    - [timestamp: 8 bytes little-endian int64 (Windows FILETIME?)]
    - Then for each field:
      - 4 bytes: field name length
      - N bytes: field name (UTF-8 or ASCII)
      - 4 bytes: value length
      - N bytes: value (UTF-8)
    
    This is an empirical decode attempt.
    """
    if not data:
        return {}
    
    tags = {}
    pos = 0
    
    try:
        # Try reading as: count (4 bytes LE), then fields
        if len(data) < 4:
            return {"_raw_hex": data.hex()[:200]}
        
        # First 4 bytes: field count
        field_count = struct.unpack_from('<I', data, 0)[0]
        pos = 4
        
        # Skip 8 bytes (possible timestamp)
        if field_count > 1000 or field_count == 0:
            # The count might be a timestamp marker, skip 8 bytes
            if len(data) > 12:
                field_count = struct.unpack_from('<I', data, 8)[0]
                pos = 12
        
        for _ in range(min(field_count, 500)):
            if pos + 4 > len(data):
                break
            
            # Field name length
            name_len = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            
            if name_len == 0 or name_len > 1000 or pos + name_len > len(data):
                break
            
            # Field name
            try:
                name = data[pos:pos + name_len].decode('utf-8', errors='replace')
            except Exception:
                break
            pos += name_len
            
            if pos + 4 > len(data):
                break
            
            # Value length
            val_len = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            
            if val_len > 100000 or pos + val_len > len(data):
                break
            
            # Value
            try:
                value = data[pos:pos + val_len].decode('utf-8', errors='replace')
            except Exception:
                value = data[pos:pos + val_len].hex()
            pos += val_len
            
            if name in tags:
                if isinstance(tags[name], list):
                    tags[name].append(value)
                else:
                    tags[name] = [tags[name], value]
            else:
                tags[name] = value
    
    except Exception as e:
        tags['_decode_error'] = str(e)
    
    return tags


def main():
    conn = sqlite3.connect(str(EXTERNAL_TAGS_DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get full column info
    cur.execute("PRAGMA table_info([tags])")
    cols = [(r['name'], r['type']) for r in cur.fetchall()]
    print("tags columns:", cols)

    cur.execute("SELECT COUNT(*) FROM [tags]")
    total = cur.fetchone()[0]
    print(f"Total rows: {total}")

    # Sample raw rows - local music files only  
    cur.execute("SELECT * FROM [tags] WHERE path LIKE 'C:%' OR path LIKE 'c:%' LIMIT 5")
    rows = cur.fetchall()
    
    print(f"\nSample local file rows: {len(rows)}")
    
    for i, row in enumerate(rows[:3]):
        d = dict(row)
        path = d.get('path', '')
        meta_blob = d.get('meta', b'')
        
        if isinstance(meta_blob, bytes):
            decoded = decode_fb2k_meta(meta_blob)
        else:
            decoded = {"raw": str(meta_blob)[:500]}
        
        print(f"\n--- Row {i+1} ---")
        print(f"Path: {path[:200]}")
        print(f"Meta blob length: {len(meta_blob) if isinstance(meta_blob, bytes) else 'N/A'}")
        print(f"Meta blob hex (first 128 bytes): {meta_blob[:128].hex() if isinstance(meta_blob, bytes) else 'N/A'}")
        print(f"Decoded: {json.dumps(decoded, indent=2, default=str)[:1500]}")

    # Also check how many local vs stream paths
    cur.execute("SELECT COUNT(*) FROM [tags] WHERE path LIKE 'C:%' OR path LIKE 'c:%'")
    local = cur.fetchone()[0]
    print(f"\nLocal file rows (C:): {local}")
    
    cur.execute("SELECT COUNT(*) FROM [tags] WHERE path LIKE 'http%'")
    streams = cur.fetchone()[0]
    print(f"Stream rows (http): {streams}")
    
    cur.execute("SELECT DISTINCT substr(path, 1, 3) as prefix FROM [tags] LIMIT 20")
    prefixes = [r[0] for r in cur.fetchall()]
    print(f"Path prefixes: {prefixes}")
    
    conn.close()

if __name__ == "__main__":
    main()
