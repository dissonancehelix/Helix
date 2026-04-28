import os
import json

class LibraryAggregator:
    """Recomputes aggregate fields AND MERGES ARTIST COLLECTIONS post-ingestion."""
    def __init__(self, lib_root):
        self.lib_root = lib_root
        self.artist_dir = os.path.join(lib_root, 'artist')
        self.album_dir = os.path.join(lib_root, 'album')

    def recompute_all(self):
        # 1. Gather all tracks once for performance at 122k+ scale
        all_tracks = []
        for alb_slug in os.listdir(self.album_dir):
            container = os.path.join(self.album_dir, alb_slug)
            if os.path.isdir(container):
                for f in os.listdir(container):
                    if f.endswith('.json') and f != 'album.json':
                        try:
                            with open(os.path.join(container, f), 'r', encoding='utf-8') as tf:
                                all_tracks.append(json.load(tf))
                        except: pass
        
        # 2. Recompute for Albums
        for alb_slug in os.listdir(self.album_dir):
            container = os.path.join(self.album_dir, alb_slug)
            alb_json = os.path.join(container, "album.json")
            if os.path.exists(alb_json):
                with open(alb_json, 'r', encoding='utf-8') as f:
                    alb = json.load(f)
                
                # Fetch tracks for this concrete album ID
                alb_tracks = [t for t in all_tracks if t['metadata'].get('album_id') == alb['id']]
                
                # MERGE ARTISTS: Collect every artist ID appearing in any track
                merged_aids = set()
                for t in alb_tracks:
                    merged_aids.update(t['metadata'].get('artist_ids', []))
                
                alb['metadata']['artist_ids'] = sorted(list(merged_aids))
                alb['metadata']['track_count'] = len(alb_tracks)
                alb['metadata']['loved_track_count'] = len([t for t in alb_tracks if t['metadata']['library_state'].get('loved')])
                
                with open(alb_json, 'w', encoding='utf-8') as f:
                    json.dump(alb, f, indent=2)

        # 3. Recompute for Artists (track counts only)
        for f in os.listdir(self.artist_dir):
            if f.endswith('.json'):
                path = os.path.join(self.artist_dir, f)
                with open(path, 'r', encoding='utf-8') as artf:
                    art = json.load(artf)
                
                art_tracks = [t for t in all_tracks if art['id'] in t['metadata'].get('artist_ids', [])]
                art['metadata']['track_count'] = len(art_tracks)
                art['metadata']['loved_track_count'] = len([t for t in art_tracks if t['metadata']['library_state'].get('loved')])
                
                # Cleanup playcount if residual
                if 'library_state' in art['metadata']: del art['metadata']['library_state']
                
                with open(path, 'w', encoding='utf-8') as artf:
                    json.dump(art, artf, indent=2)

        print(f"Aggregation complete. Merged artists for all multi-composer albums.")
