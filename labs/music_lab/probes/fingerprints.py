from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class AudioFingerprint:
    tempo_bpm: float = 0.0
    key_estimate: str = "Unknown"
    mode: str = "Unknown"
    energy: float = 0.0
    danceability: float = 0.0
    spectral_centroid_mean: float = 0.0
    rhythmic_entropy: float = 0.0
    
    # Raw vector for similarity calculations
    feature_vector: List[float] = field(default_factory=list)

def extract_signal_features(file_path: str) -> AudioFingerprint:
    """
    Primary probe for renderable audio.
    Will eventually use Essentia/Librosa.
    """
    # Placeholder for measurement logic
    return AudioFingerprint()

@dataclass
class ChipFingerprint:
    """
    For emulated music (VGM, SID, SPC, etc.)
    """
    channel_count: int = 0
    channel_activity: Dict[int, float] = field(default_factory=dict)
    register_write_density: float = 0.0
    patch_uniqueness_score: float = 0.0
    bass_channel_bias: float = 0.0  # e.g. tendency to put bass on channel 2
    fm_feedback_habits: List[float] = field(default_factory=list)

def extract_chip_features(event_stream_path: str) -> ChipFingerprint:
    """
    Primary probe for instruction-level music.
    Analyzes register writes and timing.
    """
    return ChipFingerprint()
