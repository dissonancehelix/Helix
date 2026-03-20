from typing import List, Dict, Any
from domains.music.ingestion.adapters.spotify import SpotifyAdapter
from domains.music.ingestion.adapters.foobar import FoobarAdapter
from domains.music.ingestion.normalization.track_identity import TrackIdentity

class MusicLab:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dataset: List[TrackIdentity] = []
        
    def full_ingest(self):
        """
        Ingest from all configured sources and merge.
        """
        # 1. Spotify
        print("Ingesting Spotify...")
        spotify = SpotifyAdapter(self.config.get('spotify_csv', 'spotify.csv'))
        spotify_tracks = spotify.ingest()
        self.dataset.extend(spotify_tracks)
        
        # 2. Foobar / Local
        print("Ingesting Foobar/Local Library...")
        foobar = FoobarAdapter(self.config.get('library_path', 'C:/Users/dissonance/Music'))
        # local_tracks = foobar.scan() # Scoped to single files or small subsets in Phase 1
        # self.dataset.extend(local_tracks)
        
        # 3. Canonicalization / Deduplication
        self.canonicalize()
        
        print(f"Ingestion complete. Total canonical tracks: {len(self.dataset)}")

    def canonicalize(self):
        """
        Merge duplicate tracks across sources.
        """
        # TODO: Implement deduplication logic based on fuzzy title/artist matching
        pass
    
    def get_recommendations(self, weight_love: bool = True) -> List[TrackIdentity]:
        """
        Personal discovery: Find unlistened tracks near my taste fingerprint.
        """
        # TODO: Implement similarity ranking
        return []

    def export_dataset(self, path: str):
        """
        Save the current state to a Parquet or JSON artifact.
        """
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.dataset], f, indent=2)

if __name__ == "__main__":
    # Basic bootstrap
    lab_config = {
        "spotify_csv": "spotify.csv",
        "library_path": "C:/Users/dissonance/Music"
    }
    lab = MusicLab(lab_config)
    lab.full_ingest()
    # lab.export_dataset("artifacts/music_dataset.json")
