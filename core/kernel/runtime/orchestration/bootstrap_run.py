import os
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from domains.music.ingestion.adapters.foobar import FoobarAdapter
from domains.music.ingestion.adapters.spotify import SpotifyAdapter
from domains.music.ingestion.normalization.track_identity import TrackIdentity, SourceRecord

# Paths — resolved dynamically so the repo works from any location
BASE_DIR = Path(__file__).resolve().parents[3]  # .../Helix/
ARTIFACTS_DIR = BASE_DIR / "artifacts/music_lab"
INITIAL_SCAN_DIR = ARTIFACTS_DIR / "initial_scan"
PROBE_RUN_DIR = ARTIFACTS_DIR / "probe_run_v1"
TASTE_MODEL_DIR = ARTIFACTS_DIR / "taste_model_v1"
DISCOVERY_DIR = ARTIFACTS_DIR / "discovery_v1"

class MusicLabBootstrap:
    def __init__(self, library_path: str, spotify_csv: str):
        self.library_path = library_path
        self.spotify_csv = spotify_csv
        self.dataset: List[TrackIdentity] = []
        
    def run(self):
        print(f"--- Starting Helix Music Lab Bootstrap [{datetime.datetime.now()}] ---")
        
        # 1. Ingestion
        self.step_1_ingest()
        
        # 2. Normalization & Indexing
        self.step_2_normalize()
        
        # 3. First Probe Pass (Scaffolded)
        self.step_3_probe()
        
        # 4. Taste Model
        self.step_4_taste()
        
        # 5. Discovery
        self.step_5_discovery()
        
        print("--- Bootstrap Run Complete ---")

    def step_1_ingest(self):
        print("Step 1: Ingesting Library Data...")
        
        # Spotify
        if os.path.exists(self.spotify_csv):
            print(f"Ingesting Spotify from {self.spotify_csv}...")
            spotify = SpotifyAdapter(self.spotify_csv)
            self.dataset.extend(spotify.ingest())
        
        # Foobar (Scaffolded scan - for real run we'd walk the tree)
        print(f"Scanning Foobar Library at {self.library_path}...")
        foobar = FoobarAdapter(self.library_path)
        # We'll simulate a scan results for the demo if the path is empty,
        # but in a real run this would walk the library path.
        local_tracks = foobar.scan()
        self.dataset.extend(local_tracks)
        
        print(f"Total tracks ingested: {len(self.dataset)}")

    def step_2_normalize(self):
        print("Step 2: Normalizing Identities...")
        
        # Deduplication logic
        seen: Dict[str, TrackIdentity] = {}
        unique_tracks = []
        
        for track in self.dataset:
            # Simple key: Title + Artist (normalized)
            title = (track.canonical_title or "").strip().lower()
            artist = (track.canonical_artist or "").strip().lower()
            key = f"{title}|{artist}"
            
            if not title: continue # Skip junk
            
            if key in seen:
                # Merge records
                existing = seen[key]
                existing.source_records.extend(track.source_records)
                existing.file_paths.extend(track.file_paths)
                # Keep the best metadata
                if not existing.canonical_composer: existing.canonical_composer = track.canonical_composer
                if not existing.album: existing.album = track.album
                # Combine love status
                if track.is_love:
                    existing.is_love = True
                    existing.taste_weight = max(existing.taste_weight, track.taste_weight)
            else:
                seen[key] = track
                unique_tracks.append(track)
        
        self.dataset = unique_tracks
        print(f"Unique tracks after normalization: {len(self.dataset)}")
        
        # Save artifacts
        os.makedirs(INITIAL_SCAN_DIR, exist_ok=True)
        dataset_path = INITIAL_SCAN_DIR / "track_index.json"
        with open(dataset_path, "w", encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.dataset], f, indent=2)
            
        print(f"Saved track index to {dataset_path}")

    def step_3_probe(self):
        print("Step 3: Running First Probe Pass (Measurement Scaffolding)...")
        # In a real run, this would invoke ffprobe/libvgm on file_paths
        # Saving placeholder distribution
        os.makedirs(PROBE_RUN_DIR, exist_ok=True)
        
        format_dist = {}
        for t in self.dataset:
            fmt = t.format_type or "UNKNOWN"
            format_dist[fmt] = format_dist.get(fmt, 0) + 1
            
        dist_path = PROBE_RUN_DIR / "format_distribution.json"
        with open(dist_path, "w") as f:
            json.dump(format_dist, f, indent=2)
        print(f"Format distribution preserved in {dist_path}")

    def step_4_taste(self):
        print("Step 4: Building Taste Model...")
        love_tracks = [t for t in self.dataset if t.is_love]
        print(f"Identified {len(love_tracks)} 'loved' tracks (weight: 100.0)")
        
        taste_model = {
            "center_weight": 100.0,
            "loved_count": len(love_tracks),
            "common_artists": self._best_of(love_tracks, "canonical_artist"),
            "common_albums": self._best_of(love_tracks, "album"),
            "common_composers": self._best_of(love_tracks, "canonical_composer")
        }
        
        os.makedirs(TASTE_MODEL_DIR, exist_ok=True)
        taste_path = TASTE_MODEL_DIR / "taste_fingerprint.json"
        with open(taste_path, "w") as f:
            json.dump(taste_model, f, indent=2)
        print(f"Taste fingerprint generated at {taste_path}")

    def step_5_discovery(self):
        print("Step 5: Initial Discovery Run...")
        # Placeholder for similarity discovery
        discovery = {
            "top_matches": [],
            "status": "Awaiting full feature extraction for vector similarity."
        }
        os.makedirs(DISCOVERY_DIR, exist_ok=True)
        disc_path = DISCOVERY_DIR / "discovery_summary.json"
        with open(disc_path, "w") as f:
            json.dump(discovery, f, indent=2)

    def _best_of(self, tracks: List[TrackIdentity], field: str) -> Dict[str, int]:
        counts = {}
        for t in tracks:
            val = getattr(t, field)
            if val:
                counts[val] = counts.get(val, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])

if __name__ == "__main__":
    # Bootstrap setup — paths work on both Windows (MINGW64) and WSL
    import sys
    if sys.platform == "win32" or __import__("os").environ.get("MSYSTEM", "").startswith("MINGW"):
        LAB_ROOT    = "C:/Users/dissonance/Music"
        SPOTIFY_CSV = str(BASE_DIR / "spotify.csv")
    else:
        LAB_ROOT    = "/mnt/c/Users/dissonance/Music"
        SPOTIFY_CSV = str(BASE_DIR / "spotify.csv")
    
    bootstrap = MusicLabBootstrap(LAB_ROOT, SPOTIFY_CSV)
    bootstrap.run()
