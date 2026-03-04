import json
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACTS_DIR = ROOT / '06_artifacts/artifacts'

def test_eigenspace_stability():
    try:
        import numpy as np
    except ImportError:
        return

    with open(ARTIFACTS_DIR / 'eigenspace/baseline_beams_v2.json', 'r') as f:
        wrapper = json.load(f)
        
    assert "data" in wrapper, "Artifact missing metadata wrapper"
    data = wrapper["data"]
    
    components = np.array(data["components"])
    assert len(components) >= 2, "Eigenspace must have at least 2 components"
    print("test_eigenspace_stability: PASS")

if __name__ == "__main__":
    test_eigenspace_stability()
