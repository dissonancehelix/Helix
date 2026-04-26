import os
import json
import re
import hashlib
import shutil

class SlugPolicy:
    @staticmethod
    def generate(text):
        if not text: return "unknown"
        s = str(text).lower().strip()
        s = re.sub(r'[\s\-\/;,:\.]+', '_', s)
        s = re.sub(r'[^a-z0-9_]', '', s)
        s = re.sub(r'_+', '_', s)
        return s.strip('_')

class IDAuthority:
    def __init__(self, manifest):
        self.manifest = manifest

    def artist_id(self, name):
        return f"music.artist.{SlugPolicy.generate(name)}"

    def get_album_id(self, name, data_hash, artist_slug=None, parent_slug=None):
        base_slug = SlugPolicy.generate(name)
        eid = f"music.album.{base_slug}"
        
        # ESCALATION TIER 1: Base Name
        if eid in self.manifest['ids'] and self.manifest['ids'][eid] == data_hash: return eid
        
        # ESCALATION TIER 2: Artist Qualified
        if eid in self.manifest['ids']:
            eid = f"music.album.{base_slug}.{artist_slug or 'unknown'}"
            if eid in self.manifest['ids'] and self.manifest['ids'][eid] == data_hash: return eid
            
        # ESCALATION TIER 3: Parent Folder Qualified (Disambiguate 'Disc 1' / 'Unknown Artist')
        if eid in self.manifest['ids']:
            eid = f"music.album.{base_slug}.{parent_slug or artist_slug or 'gen'}"
            if eid in self.manifest['ids'] and self.manifest['ids'][eid] == data_hash: return eid
            
        # ESCALATION TIER 4: Hash Qualified (Final Safety)
        if eid in self.manifest['ids']:
            eid = f"music.album.{base_slug}.{data_hash[:8]}"
            
        return eid

    def get_track_id(self, album_slug, track_slug, data_hash, track_number=None):
        eid = f"music.track.{album_slug}.{track_slug}"
        if eid in self.manifest['ids'] and self.manifest['ids'][eid] == data_hash: return eid
        
        if eid in self.manifest['ids']:
            tn = str(track_number).zfill(2) if track_number else "x"
            eid = f"music.track.{album_slug}.{tn}_{track_slug}"
            if eid in self.manifest['ids'] and self.manifest['ids'][eid] == data_hash: return eid
            
        # Final safety
        if eid in self.manifest['ids']:
            eid = f"music.track.{album_slug}.{track_slug}_{data_hash[:6]}"
            
        return eid

class WriteAuthority:
    def __init__(self, lib_root):
        self.lib_root = lib_root
        self.artist_dir = os.path.join(lib_root, 'artist')
        self.album_dir = os.path.join(lib_root, 'album')
        self.manifest_path = os.path.join(lib_root, ".compiler_manifest.json")
        self.manifest = self._load_manifest()
        self._write_count = 0

    def _load_manifest(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r') as f: return json.load(f)
        return {"ids": {}, "paths": {}}

    def write_entity(self, entity, data_hash):
        eid = entity['id']
        etype = entity['type']
        
        if etype == "Artist":
            slug = SlugPolicy.generate(entity['name'])
            path = os.path.join(self.artist_dir, f"{slug}.json")
        elif etype == "Album":
            alb_slug = ".".join(eid.split('.')[2:])
            path = os.path.join(self.album_dir, alb_slug, "album.json")
        elif etype == "Track":
            alb_id = entity['metadata']['album_id']
            alb_id_slug = ".".join(alb_id.split('.')[2:])
            t_slug = SlugPolicy.generate(entity['name'])
            tn = str(entity['metadata'].get('track_number', 0)).zfill(2)
            path = os.path.join(self.album_dir, alb_id_slug, f"{tn}_{t_slug}.json")
        else:
            raise ValueError(f"Unknown type: {etype}")

        if eid in self.manifest['ids'] and self.manifest['ids'][eid] == data_hash:
            return True
        
        # Hard fail only if we hit identical IDs with different hashes after all escalations
        if eid in self.manifest['ids'] and etype == "Track":
             # Tracks should be unique after escalation. 
             # For Albums/Artists, we allow updates (merging).
             pass

        # PRESERVE ANALYSIS
        existing_analysis = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    existing_analysis = old_data.get('analysis', {})
            except: pass
        
        if existing_analysis:
            entity['analysis'] = existing_analysis

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(entity, f, indent=2)
            
        self.manifest['ids'][eid] = data_hash
        self.manifest['paths'][path] = eid
        
        self._write_count += 1
        if self._write_count % 5000 == 0: self.save_manifest()
        return True

    def save_manifest(self):
        with open(self.manifest_path, 'w') as f: json.dump(self.manifest, f, indent=2)

class TemplateFactory:
    @staticmethod
    def track(data, sources):
        return {
            "id": data['id'], "type": "Track", "name": data['title'],
            "metadata": {
                "title": data['title'], "album": data['album'], "album_id": data['album_id'],
                "artist_credits_raw": data['artist_credits_raw'], "artist_ids": data['artist_ids'],
                "track_number": int(data['track_number']), "format": data['format'], "format_category": data['format_category'],
                "library_state": { "loved": bool(data['loved']) },
                "metadata_sources": sources
            },
            "analysis": {}, "relationships": []
        }

    @staticmethod
    def album(data):
        return {
            "id": data['id'], "type": "Album", "name": data['name'],
            "metadata": {
                "album": data['name'], "album_artist": data['album_artist'],
                "artist_credits_raw": data['artist_credits_raw'], "artist_ids": data['artist_ids'],
                "track_count": 0, "loved_track_count": 0
            },
            "analysis": {}, "relationships": []
        }

    @staticmethod
    def artist(data):
        return {
            "id": data['id'], "type": "Artist", "name": data['name'],
            "metadata": { "canonical_name": data['name'], "track_count": 0, "loved_track_count": 0 },
            "analysis": {}, "relationships": []
        }
