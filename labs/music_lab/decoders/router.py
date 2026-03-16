from pathlib import Path
from typing import Dict, Any, Optional
import os

class FormatRouter:
    """
    Routes files to the appropriate decoder based on extension.
    """
    
    EXT_MAP = {
        '.VGM': 'libvgm',
        '.VGZ': 'libvgm',
        '.SPC': 'gme',
        '.NSF': 'gme',
        '.GBS': 'gme',
        '.HES': 'gme',
        '.KSS': 'gme',
        '.2SF': 'vgmstream',
        '.NCSF': 'vgmstream',
        '.USF': 'vgmstream',
        '.GSF': 'vgmstream',
        '.PSF': 'vgmstream',
        '.PSF2': 'vgmstream',
        '.SSF': 'vgmstream',
        '.DSF': 'vgmstream',
    }

    def __init__(self):
        # We'll initialize decoder instances here later
        pass

    def get_decoder_type(self, file_path: str) -> Optional[str]:
        ext = Path(file_path).suffix.upper()
        return self.EXT_MAP.get(ext)

    def route(self, file_path: str):
        decoder_type = self.get_decoder_type(file_path)
        if not decoder_type:
            # Fallback to vgmstream if generic?
            return "vgmstream"
        return decoder_type
