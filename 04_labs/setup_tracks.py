import os
import shutil
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
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
