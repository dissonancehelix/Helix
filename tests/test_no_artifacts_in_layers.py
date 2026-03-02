import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYERS_DIR = ROOT / 'layers'

def test_no_artifacts():
    leaks = []
    # Search for JSON or MD files in layers/
    for p in LAYERS_DIR.rglob('*'):
        if p.suffix in ['.json', '.md']:
            # Ignore some known non-artifact files if any (none expected)
            leaks.append(str(p.relative_to(ROOT)))
            
    if leaks:
        print("Artifact Leaks Detected in Layers:")
        for l in leaks:
            print(f"  - {l}")
        return False
        
    print("Artifact Containment Check Passed.")
    return True

if __name__ == "__main__":
    if not test_no_artifacts():
        sys.exit(1)
    sys.exit(0)
