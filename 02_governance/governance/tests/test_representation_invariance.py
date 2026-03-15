import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'helix.py').exists())
ARTIFACTS_DIR = ROOT / '07_artifacts/artifacts'

def test_representation_invariance():
    with open(ARTIFACTS_DIR / 'invariance/invariance_suite.json', 'r') as f:
        wrapper = json.load(f)
        
    assert "data" in wrapper, "Artifact missing metadata wrapper"
    data = wrapper["data"]

    assert data.get("max_drift", 1.0) < 0.2, "Ontology permutation did not collapse beams sufficiently"
    print("test_representation_invariance: PASS")

if __name__ == "__main__":
    test_representation_invariance()
