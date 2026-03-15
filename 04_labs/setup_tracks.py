import os
import shutil
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
FORGE_DIR = ROOT / '04_labs'
RESEARCH_DIR = FORGE_DIR / 'research'

def setup_dirs():
    for track in ['pgp', 'atp', 'oig']:
        d = RESEARCH_DIR / track
        for sub in ['experiments', 'metrics', 'verdicts']:
            (d / sub).mkdir(parents=True, exist_ok=True)
            
    artifacts = ROOT / '07_artifacts'
    for track in ['pgp', 'atp', 'oig']:
        (artifacts / track).mkdir(parents=True, exist_ok=True)
    
    (artifacts / '_cross_track').mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    setup_dirs()
    print("Directories set up.")
