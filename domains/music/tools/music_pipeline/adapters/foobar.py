import os
import json
import sqlite3
import struct
from pathlib import Path
from typing import List, Optional, Set

try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC as FLAC_TAG
    from mutagen.oggopus import OggOpus
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from domains.music.tools.music_pipeline.normalization.track_identity import TrackIdentity, SourceRecord
except ImportError:
    from domains.music.tools.music_pipeline.normalization.track_identity import TrackIdentity, SourceRecord

COMMON_AUDIO_EXTENSIONS = {'.mp3', '.flac', '.opus', '.aac', '.wav', '.ogg'}
EMULATED_EXTENSIONS = {
    '.vgm', '.vgz', '.nsf', '.nsfe', '.spc', '.gbs', '.hes', '.kss', '.ay', '.sap', 
    '.sid', '.gym', '.psf', '.psf2', '.usf', '.dsf', '.ssf', '.ncsf', '.adp', '.mid'
}

FOOBAR_APPDATA = Path(r"C:\Users\dissonance\AppData\Roaming\foobar2000-v2")
EXTERNAL_TAGS_DB = FOOBAR_APPDATA / "external-tags.db"

def decode_fb2k_meta(data: bytes) -> dict:
    """Decode foobar2000 external-tags.db binary metadata blob."""
    if not data:
        return {}
    
    tags = {}
    pos = 0
    try:
        if len(data) < 4:
            return {}
            
        field_count = struct.unpack_from('<I', data, 0)[0]
        pos = 4
        
        # Heuristic: Check if name_len at pos 4 is reasonable. 
        # If not, try pos 12 (skipping 8-byte header).
        if field_count > 0 and field_count <= 1000:
            if len(data) > 8:
                name_len = struct.unpack_from('<I', data, 4)[0]
                if name_len == 0 or name_len > 1000:
                    # Likely a header at 4..11.
                    if len(data) > 16:
                        # Re-read field count at 8 if 0..3 was a flag? 
                        # Or keep field count from 0 and skip 8 bytes.
                        pos = 12
        else:
            # Traditional retry logic
            if len(data) > 12:
                field_count = struct.unpack_from('<I', data, 8)[0]
                pos = 12

        if field_count == 0 or field_count > 1000:
            return {}
        
        for _ in range(min(field_count, 500)):
            if pos + 4 > len(data): break
            name_len = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            
            if name_len == 0 or name_len > 1000 or pos + name_len > len(data): break
            try:
                name = data[pos:pos+name_len].decode('utf-8', errors='replace').lower()
            except Exception:
                break
            pos += name_len
            
            if pos + 4 > len(data): break
            val_len = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            
            if val_len > 100000 or pos + val_len > len(data): break
            try:
                value = data[pos:pos+val_len].decode('utf-8', errors='replace')
            except Exception:
                value = data[pos:pos+val_len].hex()
            pos += val_len
            
            if name in tags:
                if isinstance(tags[name], list):
                    tags[name].append(value)
                else:
                    tags[name] = [tags[name], value]
            else:
                tags[name] = value
    except Exception:
        pass
    
    return tags


def encode_fb2k_meta(tags: dict) -> bytes:
    """Encode a dictionary of tags into the foobar2000 external-tags.db binary format."""
    if not tags:
        return b""
    
    # Filter out empty keys/values
    clean_tags = {str(k): v for k, v in tags.items() if k and v is not None}
    field_count = len(clean_tags)
    
    # 4 bytes for count (little endian)
    # Plus 8 bytes padding which foobar often uses for larger tables
    # but based on decode logic, 4 bytes for field_count is the minimum.
    # foobar often uses a 12-byte header: [0, 0, field_count]
    # Let's match the 12-byte header seen in decode:
    header = struct.pack('<III', 0, 0, field_count)
    blob = [header]
    
    for name, value in clean_tags.items():
        # Name
        name_bytes = name.encode('utf-8')
        blob.append(struct.pack('<I', len(name_bytes)))
        blob.append(name_bytes)
        
        # Value (handle lists)
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        else:
            value = str(value)
            
        val_bytes = value.encode('utf-8')
        blob.append(struct.pack('<I', len(val_bytes)))
        blob.append(val_bytes)
        
    return b"".join(blob)


class FoobarAdapter:
    """
    Adapter reading from foobar2000-v2 external-tags.db 
    This is the live foobar-facing custom metadata plane for Phase 7+.
    """
    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
    
    def scan(self) -> List[TrackIdentity]:
        tracks = []
        if not EXTERNAL_TAGS_DB.exists():
            print(f"Warning: external-tags.db not found at {EXTERNAL_TAGS_DB}")
            return []
            
        print(f"Reading from centralized external-tags.db plane: {EXTERNAL_TAGS_DB}...")
        try:
            conn = sqlite3.connect(str(EXTERNAL_TAGS_DB))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Fetch local library files mapped in DB
            cur.execute("SELECT path, meta FROM tags WHERE path LIKE 'file://%'")
            count = 0
            
            for row in cur.fetchall():
                path_uri = row['path']
                # Translate file://///... -> normal path
                file_path_str = path_uri.replace('file://', '')
                while file_path_str.startswith('/'):
                    file_path_str = file_path_str[1:]
                    
                file_path = Path(file_path_str)
                external_meta = decode_fb2k_meta(row['meta'])
                
                track = self._process_record(file_path, external_meta)
                if track:
                    tracks.append(track)
                    count += 1
                    if count % 5000 == 0:
                        print(f"Processed {count} entries from external-tags.db...")
            conn.close()
            print(f"Scan complete. Mapped {count} entries into track identities.")
        except Exception as e:
            print(f"Error scanning external-tags.db: {e}")
            
        return tracks
    
    def _process_record(self, file_path: Path, external_meta: dict) -> Optional[TrackIdentity]:
        # Fallback strings from path 
        path_parts = file_path.parts
        inferred_artist = path_parts[-3] if len(path_parts) >= 3 else None
        inferred_album = path_parts[-2] if len(path_parts) >= 3 else None
        
        # Canonical metadata logic mapped from foobar external tags
        # Foobar's 'featuring' or 'featured_on' logic
        featuring = external_meta.get('featuring', external_meta.get('featured', external_meta.get('featured_on')))
        featuring_artists = []
        if featuring:
            if isinstance(featuring, list):
                featuring_artists = featuring
            elif isinstance(featuring, str):
                featuring_artists = [f.strip() for f in featuring.replace('feat.', '').replace('ft.', '').split(',') if f.strip()]
        
        track = TrackIdentity(
            canonical_title=external_meta.get('title', file_path.stem),
            canonical_artist=external_meta.get('artist', inferred_artist),
            canonical_composer=external_meta.get('composer'),
            album=external_meta.get('album', inferred_album),
            year=external_meta.get('date', external_meta.get('year')),
            format_type=file_path.suffix[1:].upper(),
            platform=external_meta.get('platform', inferred_artist if "PC-98" in str(file_path) else None),
            featuring_artists=featuring_artists,
            file_paths=[str(file_path)],
            source_records=[SourceRecord(
                source_type='foobar_external_tags_db',
                source_id=str(file_path),
                metadata=external_meta
            )]
        )
        
        # Taste / visibility logic
        is_loved = False
        loved_val = external_meta.get('2003_loved', external_meta.get('loved'))
        if loved_val in [1, "1", True, "true", "True", "loved"]:
            is_loved = True
            
        # Bootstrap heuristic
        if not is_loved:
            fav_artists = {"Koji Kondo", "Kyle Misko", "Led Zeppelin", "Kozilek", "Röyksopp"}
            artist = str(track.canonical_artist or "")
            album = str(track.album or "")
            
            if any(fav in artist for fav in fav_artists):
                is_loved = True
            elif "Zelda" in album or "Golden Idol" in album:
                is_loved = True
            elif track.platform == "PC-98": 
                is_loved = True

        if is_loved:
            track.is_love = True
            track.taste_weight = 100.0  
            
        return track

if __name__ == "__main__":
    adapter = FoobarAdapter("C:/Users/dissonance/Music")

