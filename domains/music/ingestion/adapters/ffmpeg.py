import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

class FFmpegAdapter:
    """
    Wrapper for ffprobe to extract technical metadata from audio files.
    """
    def __init__(self, binary_path: str = "ffprobe"):
        self.binary_path = binary_path
        self._available = shutil.which(binary_path) is not None
    
    def is_available(self) -> bool:
        return self._available
    
    def get_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        if not self._available:
            return None
            
        try:
            cmd = [
                self.binary_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Error running ffprobe on {file_path}: {e}")
        
        return None

    def extract_audio_features(self, file_path: str, output_path: str):
        """
        Stub for future Essentia/Librosa integration.
        """
        # TODO: Implement feature extraction (BPM, Key, Spectral features)
        pass
