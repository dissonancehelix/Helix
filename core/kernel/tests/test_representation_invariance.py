import json
from pathlib import Path
from core.paths import REPO_ROOT, ATLAS_ROOT, ARTIFACTS_ROOT, LAB_DATASETS_ROOT, EXPERIMENTS_ROOT

ROOT = REPO_ROOT
ARTIFACTS_DIR = ROOT / 'execution/artifacts'

def test_representation_invariance():
    with open(ARTIFACTS_DIR / 'invariance/invariance_suite.json', 'r') as f:
        wrapper = json.load(f)
        
    assert "data" in wrapper, "Artifact missing metadata wrapper"
    data = wrapper["data"]

    assert data.get("max_drift", 1.0) < 0.2, "Ontology permutation did not collapse beams sufficiently"
    print("test_representation_invariance: PASS")

if __name__ == "__main__":
    test_representation_invariance()
