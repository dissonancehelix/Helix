import json
from pathlib import Path

ROOT = Path('c:/Users/dissonance/Desktop/Helix')
ARTIFACTS_DIR = ROOT / '07_artifacts/artifacts'

def test_obstruction_rank():
    with open(ARTIFACTS_DIR / 'obstruction/obstruction_spectrum.json', 'r') as f:
        wrapper = json.load(f)
        
    assert "data" in wrapper, "Artifact missing metadata wrapper"
    data = wrapper["data"]

    var_exp = data.get("variance_explained", [])
    if len(var_exp) > 0:
        top_variance = var_exp[0]
        assert top_variance >= 0.35, f"Top obstruction beam explains {top_variance*100:.1f}%, expected >= 35%"
    print("test_obstruction_rank: PASS")

if __name__ == "__main__":
    test_obstruction_rank()
