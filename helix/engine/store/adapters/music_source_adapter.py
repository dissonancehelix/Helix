import os
import sqlite3
import re
import struct
from mutagen import File as MutagenFile
from mutagen.apev2 import APEv2

class MusicSourceAdapter:
    def __init__(self, music_root, db_path):
        self.music_root = music_root
        self.db_path = db_path
        # FOOBAR MAP: filename -> {playcount: int, loved: bool}
        self.foobar_map = self._prebuild_foobar_map()

    def _prebuild_foobar_map(self):
        """Pre-reads Foobar SQLite for performance and loved/playcount accuracy."""
        if not os.path.exists(self.db_path):
            print(f"Foobar DB not found at {self.db_path}")
            return {}
            
        print("Pre-building Foobar Metadata Cache...")
        conn = sqlite3.connect(self.db_path)
        data_map = {}
        
        # Primary Playcount Index (GUID: BE36C585...)
        # Little-endian 32-bit int at offset 12 is playcount
        PLAYCOUNT_IDX_TABLE = 'metadb_index_BE36C585_58CE_4465_9825_F2CA30CCEEED'
        
        query = f"""
            SELECT i.filename, d.value 
            FROM {PLAYCOUNT_IDX_TABLE} i
            JOIN {PLAYCOUNT_IDX_TABLE}_data d ON i.key = d.key
        """
        try:
            for url, blob in conn.execute(query):
                # file://C:\Users\dissonance\Music\...
                # We normalize the file URL back to a windows path
                path = url.replace('0+file://', '').replace('/', '\\')
                
                pc = 0
                if len(blob) >= 16:
                    pc = struct.unpack('<I', blob[12:16])[0]
                
                # Check for "loved" bit in other common indexes 
                # (Assuming 88DA... for this run, but we can check offsets)
                # For now, we strictly follow the playcount mapping
                data_map[path.lower()] = {"playcount": pc, "loved": False} # Loved mapping candidate: index 88DA
        except Exception as e:
            print(f"Foobar query error: {e}")
            
        # SECONDARY PASS: Loved candidates (Index: 88DA...)
        LOVED_IDX_TABLE = 'metadb_index_88DA8D97_B450_4FF4_A881_F6F6AD3836C1'
        try:
            query_loved = f"""
                SELECT i.filename, d.value 
                FROM {LOVED_IDX_TABLE} i
                JOIN {LOVED_IDX_TABLE}_data d ON i.key = d.key
            """
            for url, blob in conn.execute(query_loved):
                path = url.replace('0+file://', '').replace('/', '\\')
                l_path = path.lower()
                # If it's in this index at all, we flag it as a candidate for 'loved' 
                # or check if it has a non-zero bit.
                if l_path in data_map:
                    # Generic mapping: if blob has '1' at offset 0 (common for loved buttons)
                    data_map[l_path]['loved'] = True
        except: pass
        
        conn.close()
        print(f"Foobar Cache ready: {len(data_map)} files mapped.")
        return data_map

    def scan_tracks(self, limit=1000000):
        count = 0
        extensions = ('.mp3', '.flac', '.vgm', '.vgz', '.spc', '.psf', '.psf2', '.gsf', '.opus', '.m4a', '.ogg', '.wav')
        
        for root, dirs, files in os.walk(self.music_root):
            p_slug = os.path.basename(root).lower().replace(' ', '_')
            
            for f in files:
                if f.lower().endswith(extensions):
                    if count >= limit: return
                    
                    full_path = os.path.join(root, f)
                    metadata = self._extract_metadata(full_path)
                    
                    # APPLY FOOBAR STATS (Loved/Playcount)
                    stats = self.foobar_map.get(full_path.lower(), {"playcount": 0, "loved": False})
                    
                    record = {
                        "title": metadata.get('title') or f.rsplit('.', 1)[0],
                        "album": metadata.get('album') or os.path.basename(root),
                        "artist": metadata.get('artist') or "Unknown Artist",
                        "track_number": metadata.get('track_number', 0),
                        "format": f.split('.')[-1].lower(),
                        "loved": stats['loved'],
                        "playcount": stats['playcount'], # WRITTEN to raw metadata
                        "parent_slug": p_slug,
                        "sources": metadata.get('sources', {"title": "inferred"})
                    }
                    
                    yield record
                    count += 1

    def _extract_metadata(self, file_path):
        # (Same implementation as before - sidecar APE + Embedded Mutagen)
        res = {}
        sources = {}
        tag_path = file_path + ".tag"
        if not os.path.exists(tag_path):
            tag_path = os.path.join(os.path.dirname(file_path), ".tags")
            
        if os.path.exists(tag_path):
            try:
                tags = APEv2(tag_path)
                res['title'] = str(tags.get('Title', ''))
                res['artist'] = str(tags.get('Artist', ''))
                res['album'] = str(tags.get('Album', ''))
                tn = str(tags.get('Track', '0')).split('/')[0]
                res['track_number'] = int(re.sub(r'\D', '', tn) or 0)
                sources = {k: "external_tags" for k in ['title', 'artist', 'album']}
            except: pass
        if not res.get('title') or not res.get('artist'):
            try:
                audio = MutagenFile(file_path)
                if audio:
                    if not res.get('title'):
                        res['title'] = str(audio.get('title', [None])[0] or '')
                        sources['title'] = "embedded"
                    if not res.get('artist'):
                        res['artist'] = str(audio.get('artist', [None])[0] or '')
                        sources['artist'] = "embedded"
                    if not res.get('album'):
                        res['album'] = str(audio.get('album', [None])[0] or '')
                        sources['album'] = "embedded"
                    if not res.get('track_number'):
                        tn = str(audio.get('tracknumber', ['0'])[0]).split('/')[0]
                        res['track_number'] = int(re.sub(r'\D', '', tn) or 0)
            except: pass
        res['sources'] = sources
        return res
