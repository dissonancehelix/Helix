import os
import sys
import json
import hashlib
import argparse
import re
from collections import defaultdict

# ==============================================================================
# HELIX MUSIC LIBRARY - PRODUCTION INGESTION RUNTIME V8 (WARP SPEED)
# ==============================================================================

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'compiler'))
from library_compiler import SlugPolicy, IDAuthority, WriteAuthority, TemplateFactory

class IngestionManager:
    def __init__(self, lib_root):
        self.writer = WriteAuthority(lib_root)
        self.id_auth = IDAuthority(self.writer.manifest)
        # IN-MEMORY COUNTERS FOR WARP-SPEED AGGREGATION
        self._album_stats = defaultdict(lambda: {"track_count": 0, "loved_count": 0, "artists": set()})
        self._artist_stats = defaultdict(lambda: {"track_count": 0, "loved_count": 0})
        self._artist_albums = defaultdict(set) # Map artist -> {album_ids}
        self._lib_root = lib_root

    def ingest_record(self, raw):
        # 1. Normalize Artists
        raw_art = str(raw.get('artist', 'Unknown Artist'))
        # Robust Splitting: / , ; (Removed 'and' and '&' to preserve bands like 'The Bird and the Bee')
        artists = [a.strip() for a in re.split(r'[,;/]', raw_art)]
        artists = [a for a in artists if a]
        a_ids = [self.id_auth.artist_id(a) for a in artists]
        a_slugs = [SlugPolicy.generate(a) for a in artists]
        
        # 2. Build Artists (Minimal metadata first)
        for a_name, aid in zip(artists, a_ids):
            art_e = TemplateFactory.artist({"id": aid, "name": a_name})
            self.writer.write_entity(art_e, hashlib.sha256(json.dumps(art_e['metadata'], sort_keys=True).encode()).hexdigest())
            
        # 3. Build Album ID (slug-stable coalescence)
        alb_name = raw.get('album', 'Unknown Album')
        p_slug = raw.get('parent_slug', 'unknown_folder')
        
        # KEY CHANGE: The album identity is now tied ONLY to the album slug. 
        # This prevents splitting multi-composer soundtracks into separate folders.
        alb_meta_stable = { 
            "album_slug": SlugPolicy.generate(alb_name)
        }
        alb_stable_hash = hashlib.sha256(json.dumps(alb_meta_stable, sort_keys=True).encode()).hexdigest()
        
        alb_id = self.id_auth.get_album_id(alb_name, alb_stable_hash, artist_slug=a_slugs[0])
        
        alb_e = TemplateFactory.album({
            "id": alb_id, "name": alb_name, "album_artist": artists[0],
            "artist_credits_raw": raw_art, "artist_ids": a_ids
        })
        self.writer.write_entity(alb_e, alb_stable_hash)
        
        # 4. Build Track
        title = raw.get('title', 'Unknown Track')
        t_slug = SlugPolicy.generate(title)
        alb_id_slug = ".".join(alb_id.split('.')[2:])
        
        loved = bool(raw.get('loved', False))
        
        t_meta_track = { 
            "title": title, "album_id": alb_id, "track_number": int(raw.get('track_number', 0)),
            "format": raw.get('format', 'unknown'), "library_state": {"loved": loved}
        }
        t_hash = hashlib.sha256(json.dumps(t_meta_track, sort_keys=True).encode()).hexdigest()
        
        tid = self.id_auth.get_track_id(alb_id_slug, t_slug, t_hash, track_number=raw.get('track_number'))
        
        ext = str(raw.get('format', 'unknown')).lower()
        cat = "sampling"
        if ext in ['vgm', 'vgz', 'spc', 'nsf', 'gsf', 'psf', 'psf2']: cat = "hardware_log"
        elif ext in ['mp3', 'flac', 'opus', 'wav', 'm4a', 'ogg']: cat = "waveform"
        
        track_entity = TemplateFactory.track({
            "id": tid, "title": title, "album": alb_name, "album_id": alb_id,
            "artist_credits_raw": raw_art, "artist_ids": a_ids,
            "track_number": raw.get('track_number', 0),
            "format": ext, "format_category": cat,
            "loved": loved
        }, raw.get('sources', {"title": "foobar_db", "artist": "foobar_db"}))
        
        self.writer.write_entity(track_entity, t_hash)

        # UPDATING COUNTERS (STREAMING AGGREGATION)
        self._album_stats[alb_id]["track_count"] += 1
        if loved: self._album_stats[alb_id]["loved_count"] += 1
        self._album_stats[alb_id]["artists"].update(a_ids)
        
        for aid in a_ids:
            self._artist_stats[aid]["track_count"] += 1
            if loved: self._artist_stats[aid]["loved_count"] += 1
            self._artist_albums[aid].add(alb_id)

    def finalize(self):
        print("Finalizing. Streaming aggregation updates...")
        self.writer.save_manifest()
        
        # WRITE AGGREGATES TO ALBUMS
        for alb_id, stats in self._album_stats.items():
            alb_slug = ".".join(alb_id.split('.')[2:])
            path = os.path.join(self._lib_root, 'album', alb_slug, "album.json")
            if os.path.exists(path):
                with open(path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    data['metadata']['track_count'] = stats['track_count']
                    data['metadata']['loved_track_count'] = stats['loved_count']
                    data['metadata']['artist_ids'] = sorted(list(stats['artists']))
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()

        # WRITE AGGREGATES TO ARTISTS
        for art_id, stats in self._artist_stats.items():
            art_slug = art_id.split('.')[-1]
            path = os.path.join(self._lib_root, 'artist', f"{art_slug}.json")
            if os.path.exists(path):
                with open(path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    data['metadata']['track_count'] = stats['track_count']
                    data['metadata']['loved_track_count'] = stats['loved_count']
                    
                    # Populating Relationships
                    data['relationships'] = []
                    for alb_id in sorted(list(self._artist_albums.get(art_id, []))):
                         data['relationships'].append({
                             "target": alb_id,
                             "type": "contributed_to"
                         })
                         
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
        print("Substrate aggregation complete.")
