import sqlite3
import struct
import json
import os
from pathlib import Path

# Helix Root
HELIX_ROOT = Path("C:/Users/dissonance/Desktop/Helix")
LIB_ROOT = HELIX_ROOT / "codex/library/music"
EXTERNAL_TAGS_DB = Path(r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2\external-tags.db")
PROJECTION_POLICY = HELIX_ROOT / "domains/music/model/ingestion/normalization/projection_policy.json"
GENRE_POLICY = HELIX_ROOT / "domains/music/model/ingestion/normalization/genre_surface_policy.json"

def encode_fb2k_meta(tags: dict) -> bytes:
    """Encode a dictionary of tags into a foobar2000 external-tags.db binary blob."""
    # tags format: { "key": ["val1", "val2"] }
    # Binary: [UI32 count] [[UI32 keylen][key][UI32 vallen][val]]...
    
    # Flatten multi-value tags if they aren't already lists
    processed_tags = []
    for k, v in tags.items():
        if isinstance(v, list):
            for val in v:
                processed_tags.append((k, str(val)))
        else:
            processed_tags.append((k, str(v)))
            
    data = bytearray()
    data.extend(struct.pack('<I', len(processed_tags)))
    
    for k, v in processed_tags:
        k_bytes = k.encode('utf-8')
        data.extend(struct.pack('<I', len(k_bytes)))
        data.extend(k_bytes)
        
        v_bytes = v.encode('utf-8')
        data.extend(struct.pack('<I', len(v_bytes)))
        data.extend(v_bytes)
        
    return bytes(data)

def decode_fb2k_meta(data: bytes) -> dict:
    """Minimal decoder to merge existing tags."""
    if not data or len(data) < 4: return {}
    tags = {}
    pos = 0
    try:
        field_count = struct.unpack_from('<I', data, 0)[0]
        pos = 4
        # Handle the '12-byte header' offset seen in foobaradapter
        if field_count > 1000 or field_count == 0:
            if len(data) > 12:
                field_count = struct.unpack_from('<I', data, 8)[0]
                pos = 12
        
        for _ in range(field_count):
            if pos + 4 > len(data): break
            nlen = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            name = data[pos:pos+nlen].decode('utf-8').lower()
            pos += nlen
            vlen = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            val = data[pos:pos+vlen].decode('utf-8')
            pos += vlen
            
            if name not in tags: tags[name] = []
            tags[name].append(val)
    except: pass
    return tags

def get_surface_genre(raw_genre, genre_policy):
    if not raw_genre: return None
    raw_genre = raw_genre.lower()
    for surface, patterns in genre_policy["mappings"].items():
        if any(p.lower() in raw_genre for p in patterns):
            return surface
    return genre_policy.get("default", "Other")

def run_projection():
    print("Helix Foobar Projector v1.0")
    
    with open(PROJECTION_POLICY, "r") as f:
        policy = json.load(f)["projection_policy"]
    with open(GENRE_POLICY, "r") as f:
        genre_policy = json.load(f)["genre_surface_policy"]
        
    whitelist = {item["fb2k_field"]: item["helix_field"] for item in policy["whitelisted_fields"]}
    
    print(f"Connecting to {EXTERNAL_TAGS_DB}...")
    conn = sqlite3.connect(str(EXTERNAL_TAGS_DB))
    cur = conn.cursor()
    
    count = 0
    updated = 0
    
    print(f"Scanning library in {LIB_ROOT}...")
    
    # Iterate over all tracks in Helix Library
    for root, _, files in os.walk(str(LIB_ROOT)):
        for fname in files:
            if not fname.endswith(".json") or fname.startswith("."): continue
            
            with open(Path(root) / fname, "r", encoding="utf-8") as f:
                track = json.load(f)
            
            # Skip non-track entities (e.g. album.json, artist entity)
            if track.get("type") != "Track":
                continue
                
            count += 1
            source_path = track.get("metadata", {}).get("source")
            if not source_path:
                print(f"  Warning: No source path for track {track.get('id', fname)}")
                continue
                
            # foobar uses file://C:\Path format in this DB
            fb2k_path = "file://" + str(source_path)
            
            # Fetch current meta from DB
            cur.execute("SELECT meta FROM tags WHERE path = ?", (fb2k_path,))
            row = cur.fetchone()
            if not row:
                # Optional: log if path is not in DB if we expect it to be
                continue
            
            existing_tags = decode_fb2k_meta(row[0])
            new_tags = existing_tags.copy()
            
            changed = False
            for fb_field, helix_path in whitelist.items():
                # Extract value from Helix track JSON
                val = track
                try:
                    for part in helix_path.split("."):
                        val = val.get(part, {})
                    if val == {}: val = None
                except: val = None
                
                # Special handling for Genre Surface
                if fb_field == "GENRE":
                    val = get_surface_genre(val, genre_policy)
                
                if val:
                    # Helix internal k:v -> Foobar k:v
                    # Foobar expects a list of values
                    val_list = [str(val)] if not isinstance(val, list) else [str(v) for v in val]
                    if new_tags.get(fb_field.lower()) != val_list:
                        new_tags[fb_field.lower()] = val_list
                        changed = True
            
            if changed:
                new_blob = encode_fb2k_meta(new_tags)
                cur.execute("UPDATE tags SET meta = ? WHERE path = ?", (new_blob, fb2k_path))
                updated += 1
            
            if count % 1000 == 0:
                print(f"  Processed {count} files... ({updated} updated in DB)")
                conn.commit()
    
    conn.commit()
    conn.close()
    print(f"Finished Projection. Path Count: {count}, Updated: {updated}")

if __name__ == "__main__":
    run_projection()

