from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid

@dataclass
class SourceRecord:
    source_type: str  # 'foobar', 'spotify', 'youtube', 'file'
    source_id: str    # URI, file path, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrackIdentity:
    track_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    canonical_title: Optional[str] = None
    canonical_artist: Optional[str] = None
    canonical_composer: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    duration_ms: Optional[int] = None
    format_type: Optional[str] = None  # 'FLAC', 'VGZ', etc.
    platform: Optional[str] = None     # 'Genesis', 'SNES', etc.
    
    # Helix specific
    taste_weight: float = 1.0
    is_love: bool = False
    listen_count: int = 0
    
    # Source linking
    source_records: List[SourceRecord] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    
    # Extracted data references (artifact paths)
    feature_artifact_path: Optional[str] = None
    event_stream_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "canonical_title": self.canonical_title,
            "canonical_artist": self.canonical_artist,
            "canonical_composer": self.canonical_composer,
            "album": self.album,
            "year": self.year,
            "duration_ms": self.duration_ms,
            "format_type": self.format_type,
            "platform": self.platform,
            "taste_weight": self.taste_weight,
            "is_love": self.is_love,
            "listen_count": self.listen_count,
            "source_records": [vars(s) for s in self.source_records],
            "file_paths": self.file_paths,
            "feature_artifact_path": self.feature_artifact_path,
            "event_stream_path": self.event_stream_path
        }

@dataclass
class ArtistIdentity:
    artist_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: str = "artist"  # 'artist', 'composer', 'arranger'
    style_fingerprint: Dict[str, Any] = field(default_factory=dict)
    linked_tracks: List[str] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return vars(self)
