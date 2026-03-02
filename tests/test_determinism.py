import os
import sys
import json
import hashlib
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
sys.path.append(str(ROOT))

from infra.io import persistence as m_io; from infra.platform import environment as m_env

def hash_artifacts():
    hashes = {}
    for p in m.ART_DIR.rglob('*.json'):
        if p.name == 'run_manifest.json' or 'archive' in p.parts: continue
        payload = p.read_bytes()
        hashes[p.name] = hashlib.sha256(payload).hexdigest()
    return hashes

def test_determinism():
    os.environ['HELIX_BOOTSTRAP_SEED'] = '42'
    
    # 1st run
    m.execute_all()
    hashes1 = hash_artifacts()
    
    # 2nd run
    m.execute_all()
    hashes2 = hash_artifacts()
    
    for k in hashes1:
        assert hashes1[k] == hashes2[k], f"Determinism failure in artifact {k}"
        
    print("test_determinism: PASS")

if __name__ == "__main__":
    test_determinism()
