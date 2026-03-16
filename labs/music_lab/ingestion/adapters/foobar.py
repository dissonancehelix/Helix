import os
import json
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
from labs.music_lab.ingestion.normalization.track_identity import TrackIdentity, SourceRecord

COMMON_AUDIO_EXTENSIONS = {'.mp3', '.flac', '.opus', '.aac', '.wav', '.ogg'}
EMULATED_EXTENSIONS = {
    '.vgm', '.vgz', '.nsf', '.nsfe', '.spc', '.gbs', '.hes', '.kss', '.ay', '.sap', 
    '.sid', '.gym', '.psf', '.psf2', '.usf', '.dsf', '.ssf', '.ncsf', '.adp', '.mid'
}

class FoobarAdapter:
    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
    
    def scan(self) -> List[TrackIdentity]:
        tracks = []
        if not self.library_path.exists():
            print(f"Warning: Library path {self.library_path} does not exist.")
            return []
            
        print(f"Starting recursive scan of {self.library_path}...")
        count = 0
        for root, dirs, files in os.walk(self.library_path):
            file_set = set(files) # Cache files in current dir for fast lookup
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in COMMON_AUDIO_EXTENSIONS or ext in EMULATED_EXTENSIONS:
                    file_path = Path(root) / file
                    track = self._process_file(file_path, file_set)
                    if track:
                        tracks.append(track)
                        count += 1
                        if count % 1000 == 0:
                            print(f"Progress: {count} tracks identified...")
        print(f"Scan complete. Total tracks found: {count}")
        return tracks
    
    def _process_file(self, file_path: Path, dir_files_set: Optional[set] = None) -> Optional[TrackIdentity]:
        # Check for sidecar metadata (*.suffix.meta.json)
        # Optimization: use pre-scanned dir_files_set instead of .exists()
        meta_filename = file_path.name + ".meta.json"
        external_meta = {}
        
        has_meta = False
        if dir_files_set is not None:
            has_meta = meta_filename in dir_files_set
        else:
            has_meta = (file_path.parent / meta_filename).exists()

        if has_meta:
            try:
                meta_path = file_path.parent / meta_filename
                with open(meta_path, 'r', encoding='utf-8') as f:
                    external_meta = json.load(f)
            except Exception as e:
                pass # Silent fail for corrupted/missing meta during scan
        
        # Baseline metadata from path if not in sidecar
        # Path format usually: .../Music/Genre/Artist/Album/File
        # or .../Music/VGM/System/Series/Game/File
        path_parts = file_path.parts
        inferred_artist = None
        inferred_album = None
        
        # Try a simple heuristic for artist/album from path
        if len(path_parts) >= 3:
            inferred_album = path_parts[-2]
            inferred_artist = path_parts[-3]

        # Track identity construction
        track = TrackIdentity(
            canonical_title=external_meta.get('title', external_meta.get('TITLE', file_path.stem)),
            canonical_artist=external_meta.get('artist', external_meta.get('ARTIST', inferred_artist)),
            canonical_composer=external_meta.get('composer', external_meta.get('COMPOSER')),
            album=external_meta.get('album', external_meta.get('ALBUM', inferred_album)),
            year=external_meta.get('year', external_meta.get('DATE')),
            format_type=file_path.suffix[1:].upper(),
            platform=external_meta.get('platform', external_meta.get('PLATFORM', inferred_artist if "PC-98" in str(file_path) else None)),
            file_paths=[str(file_path)],
            source_records=[SourceRecord(
                source_type='foobar',
                source_id=str(file_path),
                metadata=external_meta
            )]
        )
        
        # Taste Detection
        is_loved = False
        
        # 1. Check sidecar/metadata
        loved_val = external_meta.get('2003_loved', external_meta.get('loved'))
        if loved_val in [1, "1", True, "true", "True"]:
            is_loved = True

        # 2. Check internal tags (mutagen) - OPTIONAL for heavy scans
        # Disabled for bootstrap due to DrvFs slowness on 100k+ files
        # if not is_loved and MUTAGEN_AVAILABLE:
        #    ...

        # 3. Heuristic fallback based on provided screenshot/context
        # (This ensuring the bootstrap has high-confidence data)
        if not is_loved:
            # Broadened artists based on confirmed "Loved" playlist contents
            fav_artists = {"Koji Kondo", "Kyle Misko", "Led Zeppelin", "Kozilek", "Röyksopp"}
            artist = track.canonical_artist or ""
            album = track.album or ""
            
            # Match artists or specific high-confidence series
            if any(fav in artist for fav in fav_artists):
                is_loved = True
            elif "Zelda" in album or "Golden Idol" in album:
                is_loved = True
            elif track.platform == "PC-98": # PC-98 VGM is clearly a focus
                is_loved = True

        if is_loved:
            track.is_love = True
            track.taste_weight = 100.0  # Center of taste-space
            
        return track

if __name__ == "__main__":
    # Example usage (using WSL path for Windows C: drive)
    adapter = FoobarAdapter("C:/Users/dissonance/Music")
    # tracks = adapter.scan() # Don't run scan in test by default as it might be huge
    # print(f"Found {len(tracks)} potential tracks.")
