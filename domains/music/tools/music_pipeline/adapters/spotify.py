import csv
from pathlib import Path
from typing import List
from domains.music.tools.music_pipeline.normalization.track_identity import TrackIdentity, SourceRecord

class SpotifyAdapter:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
    
    def ingest(self) -> List[TrackIdentity]:
        if not self.csv_path.exists():
            return []
        
        tracks = []
        with open(self.csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map Spotify CSV to TrackIdentity
                track = TrackIdentity(
                    canonical_title=row.get('Track Name'),
                    canonical_artist=row.get('Artist Name(s)'),
                    album=row.get('Album Name'),
                    duration_ms=int(row.get('Duration (ms)', 0)) if row.get('Duration (ms)') else None,
                    # Spotify-specific metadata in source record
                    source_records=[SourceRecord(
                        source_type='spotify',
                        source_id=row.get('Track URI', ''),
                        metadata={
                            "popularity": row.get('Popularity'),
                            "genres": row.get('Genres'),
                            "energy": row.get('Energy'),
                            "tempo": row.get('Tempo'),
                            "valence": row.get('Valence')
                        }
                    )]
                )
                
                # If energy is high or popularity is high, we might adjust weight? 
                # (Just placeholder for logic)
                
                tracks.append(track)
        
        return tracks

if __name__ == "__main__":
    # Test ingestion
    adapter = SpotifyAdapter("spotify.csv")
    tracks = adapter.ingest()
    print(f"Ingested {len(tracks)} tracks from Spotify.")
    if tracks:
        print(f"Sample: {tracks[0].canonical_title} by {tracks[0].canonical_artist}")

